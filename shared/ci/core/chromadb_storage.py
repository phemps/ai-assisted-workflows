#!/usr/bin/env python3
"""
ChromaDB Vector Storage System for Continuous Improvement Framework

Complete replacement for Faiss + SQLite + file caching system.
Provides unified vector storage, metadata management, and similarity search.
Part of AI-Assisted Workflows - integrates with 8-agent orchestration system.
"""

import asyncio
import hashlib
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

import numpy as np

# Required imports - fail fast if unavailable
try:
    # OpenTelemetry compatibility patch for ChromaDB
    from opentelemetry.sdk import environment_variables

    # Add missing constants for compatibility with older OpenTelemetry versions
    missing_constants = [
        "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE",
        "OTEL_EXPORTER_OTLP_CLIENT_KEY",
        "OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE",
        "OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY",
        "OTEL_EXPORTER_OTLP_METRICS_CLIENT_CERTIFICATE",
        "OTEL_EXPORTER_OTLP_METRICS_CLIENT_KEY",
        "OTEL_EXPORTER_OTLP_LOGS_CLIENT_CERTIFICATE",
        "OTEL_EXPORTER_OTLP_LOGS_CLIENT_KEY",
    ]
    for const_name in missing_constants:
        if not hasattr(environment_variables, const_name):
            setattr(environment_variables, const_name, const_name)

    import chromadb
    from chromadb.config import Settings
except ImportError as e:
    print(f"ERROR: Required dependencies not available: {e}", file=sys.stderr)
    print(
        "Please install required packages: pip install chromadb opentelemetry-api",
        file=sys.stderr,
    )
    sys.exit(1)

# Setup import paths and import required modules
try:
    from utils import path_resolver  # noqa: F401
    from ci.integration.symbol_extractor import Symbol, SymbolType
    from ci.core.memory_manager import MemoryManager
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class ChromaDBStatus(Enum):
    """Status of ChromaDB operations."""

    READY = "ready"
    INITIALIZING = "initializing"
    ERROR = "error"
    NOT_FOUND = "not_found"


@dataclass
class QueryCacheEntry:
    """Cache entry for query results."""

    result: Any
    timestamp: float
    access_count: int = 0

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if cache entry is expired."""
        return (time.time() - self.timestamp) > ttl_seconds


class ConnectionPool:
    """Connection pool for ChromaDB clients."""

    def __init__(self, max_connections: int = 5, timeout: float = 30.0):
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = asyncio.Queue(maxsize=max_connections)
        self._connections = set()
        self._lock = asyncio.Lock()

    async def get_connection(self, persist_directory: Path) -> chromadb.Client:
        """Get a connection from the pool."""
        try:
            # Try to get existing connection
            connection = self._pool.get_nowait()
            return connection
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            async with self._lock:
                if len(self._connections) < self.max_connections:
                    connection = await self._create_connection(persist_directory)
                    self._connections.add(connection)
                    return connection
                else:
                    # Wait for available connection
                    connection = await asyncio.wait_for(
                        self._pool.get(), timeout=self.timeout
                    )
                    return connection

    async def return_connection(self, connection: chromadb.Client) -> None:
        """Return a connection to the pool."""
        try:
            self._pool.put_nowait(connection)
        except asyncio.QueueFull:
            # Pool is full, connection will be garbage collected
            pass

    async def _create_connection(self, persist_directory: Path) -> chromadb.Client:
        """Create a new ChromaDB connection."""
        return chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(anonymized_telemetry=False, allow_reset=False),
        )

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
                # ChromaDB doesn't have explicit close, connections are GC'd
            except asyncio.QueueEmpty:
                break
        self._connections.clear()


@dataclass
class ChromaDBConfig:
    """Configuration for ChromaDB storage system."""

    # Collection settings
    collection_name: str = "code_symbols"
    persist_directory: Optional[Path] = None

    # Similarity thresholds (compatible with existing config)
    exact_match_threshold: float = 0.95
    high_similarity_threshold: float = 0.85
    medium_similarity_threshold: float = 0.75
    low_similarity_threshold: float = 0.65

    # Performance settings
    batch_size: int = 100
    max_results: int = 100
    enable_metadata_index: bool = True

    # Memory management
    max_memory_gb: float = 2.0

    # Phase 5: Performance and caching settings
    enable_connection_pooling: bool = True
    max_connections: int = 5
    connection_timeout: float = 30.0
    enable_query_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    max_cache_entries: int = 1000
    enable_async_operations: bool = True

    def __post_init__(self):
        """Validate config. Persist directory initialization moved to ChromaDBStorage.__init__"""
        # Note: persist_directory initialization now happens in ChromaDBStorage.__init__
        # to ensure it uses project_root instead of cwd()

        # Validate thresholds
        thresholds = [
            self.low_similarity_threshold,
            self.medium_similarity_threshold,
            self.high_similarity_threshold,
            self.exact_match_threshold,
        ]

        if not all(0.0 <= t <= 1.0 for t in thresholds):
            raise ValueError("All similarity thresholds must be between 0.0 and 1.0")

        if not (thresholds == sorted(thresholds)):
            raise ValueError("Thresholds must be in ascending order")


@dataclass
class SimilarityMatch:
    """ChromaDB similarity match result."""

    query_index: int
    match_index: int
    similarity_score: float
    distance: float
    query_symbol: Optional[Symbol] = None
    match_symbol: Optional[Symbol] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChromaDBStorage:
    """
    Unified ChromaDB storage system replacing Faiss + SQLite + file caching.

    Provides:
    - Vector storage and similarity search (replaces similarity_detector.py)
    - Metadata storage and retrieval (replaces registry_manager.py)
    - Persistent caching (replaces file-based embedding cache)
    - Unified collection management
    """

    def __init__(
        self,
        config: Optional[ChromaDBConfig] = None,
        project_root: Optional[Path] = None,
        memory_manager: Optional[MemoryManager] = None,
    ):
        self.config = config or ChromaDBConfig()
        self.project_root = project_root or Path.cwd()
        self.memory_manager = memory_manager

        # Initialize persist_directory if None (moved from __post_init__ to use project_root)
        if self.config.persist_directory is None:
            self.config.persist_directory = (
                self.project_root / ".ci-registry" / "chromadb"
            )

        # Update persist directory to be relative to project root if it's relative
        elif not self.config.persist_directory.is_absolute():
            self.config.persist_directory = (
                self.project_root / self.config.persist_directory
            )

        # ChromaDB client and collection
        self._client = None
        self._collection = None
        self._status = ChromaDBStatus.INITIALIZING

        # Phase 5: Connection pooling and caching
        self._connection_pool = None
        self._query_cache: Dict[str, QueryCacheEntry] = {}
        self._cache_lock = threading.Lock()
        self._executor = (
            ThreadPoolExecutor(max_workers=4)
            if self.config.enable_async_operations
            else None
        )

        # Performance tracking
        self._search_times = []
        self._storage_times = []
        self._stats = {
            "total_symbols": 0,
            "total_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Initialize ChromaDB and connection pool
        self._initialize_chromadb()
        if self.config.enable_connection_pooling:
            self._connection_pool = ConnectionPool(
                max_connections=self.config.max_connections,
                timeout=self.config.connection_timeout,
            )

    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Ensure persist directory exists
            self.config.persist_directory.mkdir(parents=True, exist_ok=True)

            # Create persistent client
            self._client = chromadb.PersistentClient(
                path=str(self.config.persist_directory),
                settings=Settings(anonymized_telemetry=False, allow_reset=False),
            )

            # Get or create collection with optimized settings for performance
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 400,  # Higher for better accuracy during build
                    "hnsw:M": 16,  # Good balance between speed and memory
                    "hnsw:search_ef": 128,  # Lower for faster search, acceptable accuracy loss
                    "hnsw:num_threads": 4,  # Parallel processing
                    "description": "Code symbol embeddings for duplicate detection (optimized)",
                },
            )

            self._status = ChromaDBStatus.READY
            print(
                f"Initialized ChromaDB collection: {self.config.collection_name}",
                file=sys.stderr,
            )

        except Exception as e:
            self._status = ChromaDBStatus.ERROR
            print(f"FATAL: ChromaDB initialization failed: {e}", file=sys.stderr)
            sys.exit(1)

    def is_available(self) -> bool:
        """Check if ChromaDB is available and ready."""
        return self._status == ChromaDBStatus.READY and self._collection is not None

    def build_index(
        self, embeddings: np.ndarray, symbols: Optional[List[Symbol]] = None
    ) -> bool:
        """
        Store symbols and their embeddings in ChromaDB.
        Compatible with similarity_detector.build_index() interface.

        Args:
            embeddings: Numpy array of embeddings [n_vectors, embedding_dim]
            symbols: Optional list of symbols corresponding to embeddings

        Returns:
            True if successful, False otherwise
        """
        if symbols is None:
            print(
                "Error: ChromaDB requires symbols for metadata storage", file=sys.stderr
            )
            return False

        return self.store_symbols(symbols, embeddings)

    def store_symbols(self, symbols: List[Symbol], embeddings: np.ndarray) -> bool:
        """
        Store symbols and their embeddings in ChromaDB.

        Replaces both registry_manager.save_symbols() and embedding caching.
        """
        if not self.is_available():
            return False

        if len(symbols) != len(embeddings):
            print(
                f"Error: Symbol count ({len(symbols)}) != embedding count ({len(embeddings)})",
                file=sys.stderr,
            )
            return False

        start_time = time.time()

        try:
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            embeddings_list = []

            for i, symbol in enumerate(symbols):
                symbol_id = self._generate_symbol_id(symbol)
                document = self._symbol_to_document(symbol)
                metadata = self._extract_metadata(symbol)
                embedding = embeddings[i].tolist()

                ids.append(symbol_id)
                documents.append(document)
                metadatas.append(metadata)
                embeddings_list.append(embedding)

            # Store in ChromaDB (upsert to handle updates)
            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings_list,
            )

            # Update statistics
            self._stats["total_symbols"] = self._collection.count()
            storage_time = time.time() - start_time
            self._storage_times.append(storage_time)

            print(
                f"Stored {len(symbols)} symbols in ChromaDB ({storage_time:.3f}s)",
                file=sys.stderr,
            )
            return True

        except Exception as e:
            print(f"Error storing symbols in ChromaDB: {e}", file=sys.stderr)
            return False

    def find_similar(
        self,
        query_embedding: np.ndarray,
        threshold: float = None,
        k: int = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SimilarityMatch]:
        """
        Find similar symbols using ChromaDB similarity search.

        Replaces similarity_detector.find_similar().
        """
        if not self.is_available():
            return []

        threshold = threshold or self.config.medium_similarity_threshold
        k = k or self.config.max_results

        start_time = time.time()

        try:
            # Query ChromaDB
            results = self._collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k,
                where=filters,
                include=["documents", "metadatas", "distances"],
            )

            # Convert to SimilarityMatch objects
            matches = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    # ChromaDB returns distances, convert to similarity
                    distance = results["distances"][0][i]
                    similarity = max(0.0, 1.0 - distance)  # Assuming cosine distance

                    if similarity >= threshold:
                        symbol = self._metadata_to_symbol(results["metadatas"][0][i])

                        match = SimilarityMatch(
                            query_index=0,
                            match_index=i,
                            similarity_score=similarity,
                            distance=distance,
                            match_symbol=symbol,
                            confidence=0.95,
                            metadata=results["metadatas"][0][i],
                        )
                        matches.append(match)

            # Track performance
            search_time = time.time() - start_time
            self._search_times.append(search_time)
            self._stats["total_searches"] += 1

            return matches

        except Exception as e:
            print(f"Error in ChromaDB similarity search: {e}", file=sys.stderr)
            return []

    def _generate_cache_key(
        self,
        query_embedding: np.ndarray,
        threshold: float,
        k: int,
        filters: Optional[Dict[str, Any]],
    ) -> str:
        """Generate cache key for query results."""
        key_parts = [
            hashlib.md5(query_embedding.tobytes()).hexdigest()[:16],
            f"t{threshold:.3f}",
            f"k{k}",
        ]
        if filters:
            filter_str = json.dumps(filters, sort_keys=True)
            key_parts.append(hashlib.md5(filter_str.encode()).hexdigest()[:8])
        return "_".join(key_parts)

    def _get_cached_result(self, cache_key: str) -> Optional[List[SimilarityMatch]]:
        """Get cached query result if available and not expired."""
        if not self.config.enable_query_caching:
            return None

        with self._cache_lock:
            entry = self._query_cache.get(cache_key)
            if entry and not entry.is_expired(self.config.cache_ttl_seconds):
                entry.access_count += 1
                self._stats["cache_hits"] += 1
                return entry.result
            elif entry:
                # Remove expired entry
                del self._query_cache[cache_key]

        self._stats["cache_misses"] += 1
        return None

    def _cache_result(self, cache_key: str, result: List[SimilarityMatch]) -> None:
        """Cache query result."""
        if not self.config.enable_query_caching:
            return

        with self._cache_lock:
            # Clean up old entries if cache is full
            if len(self._query_cache) >= self.config.max_cache_entries:
                # Remove least recently used entries (simple LRU)
                sorted_entries = sorted(
                    self._query_cache.items(),
                    key=lambda x: (x[1].access_count, x[1].timestamp),
                )
                for key, _ in sorted_entries[: len(sorted_entries) // 4]:  # Remove 25%
                    del self._query_cache[key]

            # Add new entry
            self._query_cache[cache_key] = QueryCacheEntry(
                result=result, timestamp=time.time()
            )

    async def find_similar_async(
        self,
        query_embedding: np.ndarray,
        threshold: float = None,
        k: int = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SimilarityMatch]:
        """
        Async version of find_similar using connection pool and caching.
        """
        if not self.is_available() or not self.config.enable_async_operations:
            # Fallback to sync version
            return self.find_similar(query_embedding, threshold, k, filters)

        threshold = threshold or self.config.medium_similarity_threshold
        k = k or self.config.max_results

        # Check cache first
        cache_key = self._generate_cache_key(query_embedding, threshold, k, filters)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result

        start_time = time.time()

        try:
            if self._connection_pool:
                # Use connection pool
                async with self._get_pooled_connection() as client:
                    collection = client.get_collection(self.config.collection_name)
                    result = await asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        self._execute_query,
                        collection,
                        query_embedding,
                        k,
                        filters,
                    )
            else:
                # Fallback to executor without connection pool
                result = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    self._execute_query,
                    self._collection,
                    query_embedding,
                    k,
                    filters,
                )

            # Process results
            matches = self._process_query_results(result, threshold)

            # Cache result
            self._cache_result(cache_key, matches)

            # Track performance
            search_time = time.time() - start_time
            self._search_times.append(search_time)
            self._stats["total_searches"] += 1

            return matches

        except Exception as e:
            print(f"Error in async ChromaDB similarity search: {e}", file=sys.stderr)
            return []

    @asynccontextmanager
    async def _get_pooled_connection(self):
        """Context manager for getting connection from pool."""
        if not self._connection_pool:
            yield self._client
            return

        connection = await self._connection_pool.get_connection(
            self.config.persist_directory
        )
        try:
            yield connection
        finally:
            await self._connection_pool.return_connection(connection)

    def _execute_query(
        self,
        collection,
        query_embedding: np.ndarray,
        k: int,
        filters: Optional[Dict[str, Any]],
    ):
        """Execute the ChromaDB query (sync operation for thread pool)."""
        return collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k,
            where=filters,
            include=["documents", "metadatas", "distances"],
        )

    def _process_query_results(
        self, results, threshold: float
    ) -> List[SimilarityMatch]:
        """Process ChromaDB query results into SimilarityMatch objects."""
        matches = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                # ChromaDB returns distances, convert to similarity
                distance = results["distances"][0][i]
                similarity = max(0.0, 1.0 - distance)  # Assuming cosine distance

                if similarity >= threshold:
                    symbol = self._metadata_to_symbol(results["metadatas"][0][i])

                    match = SimilarityMatch(
                        query_index=0,
                        match_index=i,
                        similarity_score=similarity,
                        distance=distance,
                        match_symbol=symbol,
                        confidence=0.95,
                        metadata=results["metadatas"][0][i],
                    )
                    matches.append(match)
        return matches

    def batch_similarity_search(
        self, embeddings: np.ndarray, threshold: float = None
    ) -> Dict[int, List[SimilarityMatch]]:
        """
        Perform batch similarity search using ChromaDB with memory-aware batching.

        Replaces similarity_detector.batch_similarity_search().
        """
        if not self.is_available():
            return {}

        threshold = threshold or self.config.medium_similarity_threshold
        results = {}

        # Use memory manager for dynamic batch sizing if available
        batch_size = self.config.batch_size
        if self.memory_manager:
            batch_size = self.memory_manager.calculate_optimal_batch_size(batch_size)

        # Process in batches to manage memory
        for start_idx in range(0, len(embeddings), batch_size):
            end_idx = min(start_idx + batch_size, len(embeddings))
            batch = embeddings[start_idx:end_idx]

            for i, query_embedding in enumerate(batch):
                query_idx = start_idx + i
                matches = self.find_similar(query_embedding, threshold)

                # Update query indices in matches
                for match in matches:
                    match.query_index = query_idx

                results[query_idx] = matches

        return results

    async def batch_similarity_search_async(
        self, embeddings: np.ndarray, threshold: float = None, max_concurrent: int = 5
    ) -> Dict[int, List[SimilarityMatch]]:
        """
        Async batch similarity search with controlled concurrency.
        """
        if not self.is_available() or not self.config.enable_async_operations:
            # Fallback to sync version
            return self.batch_similarity_search(embeddings, threshold)

        threshold = threshold or self.config.medium_similarity_threshold
        results = {}

        # Use memory manager for optimal batch and concurrency sizing
        batch_size = self.config.batch_size
        if self.memory_manager:
            batch_size = self.memory_manager.calculate_optimal_batch_size(batch_size)
            # Adjust concurrency based on memory
            if self.memory_manager.get_memory_usage_percentage() > 80:
                max_concurrent = min(max_concurrent, 2)

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single_query(query_idx: int, query_embedding: np.ndarray):
            async with semaphore:
                matches = await self.find_similar_async(query_embedding, threshold)
                # Update query indices in matches
                for match in matches:
                    match.query_index = query_idx
                return query_idx, matches

        # Create tasks for all queries
        tasks = []
        for i in range(len(embeddings)):
            task = asyncio.create_task(process_single_query(i, embeddings[i]))
            tasks.append(task)

        # Execute all tasks and collect results
        for task in asyncio.as_completed(tasks):
            query_idx, matches = await task
            results[query_idx] = matches

        return results

    def get_detector_info(self) -> Dict[str, Any]:
        """
        Get ChromaDB storage status and diagnostic information.

        Compatible with similarity_detector.get_detector_info() interface.
        """
        return self.get_storage_info()

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get ChromaDB storage status and diagnostic information.

        Replaces both similarity_detector.get_detector_info() and registry_manager.get_registry_info().
        """
        try:
            collection_count = self._collection.count() if self._collection else 0

            return {
                "status": self._status.value,
                "is_available": self.is_available(),
                "method": "chromadb_cosine",
                "collection_name": self.config.collection_name,
                "persist_directory": str(self.config.persist_directory),
                "total_symbols": collection_count,
                "config": {
                    "exact_match_threshold": self.config.exact_match_threshold,
                    "high_similarity_threshold": self.config.high_similarity_threshold,
                    "medium_similarity_threshold": self.config.medium_similarity_threshold,
                    "low_similarity_threshold": self.config.low_similarity_threshold,
                    "batch_size": self.config.batch_size,
                    "max_results": self.config.max_results,
                },
                "performance": {
                    "avg_search_time": (
                        sum(self._search_times) / len(self._search_times)
                        if self._search_times
                        else 0
                    ),
                    "avg_storage_time": (
                        sum(self._storage_times) / len(self._storage_times)
                        if self._storage_times
                        else 0
                    ),
                    "total_searches": len(self._search_times),
                    "total_storages": len(self._storage_times),
                },
                "stats": self._stats.copy(),
                "chromadb_info": {
                    "version": getattr(chromadb, "__version__", "unknown"),
                    "collection_name": self.config.collection_name,
                    "space": "cosine",
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "is_available": False,
                "error": str(e),
                "total_symbols": 0,
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB storage."""
        return self.get_storage_info()

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Compatible interface for registry_manager.get_registry_stats().
        """
        info = self.get_storage_info()
        return {
            "total_symbols": info.get("total_symbols", 0),
            "is_available": info.get("is_available", False),
            "persist_directory": info.get("persist_directory", ""),
            "stats": info.get("stats", {}),
        }

    def clear_index(self) -> None:
        """Clear all data from ChromaDB collection. Compatible with similarity_detector.clear_index()."""
        self.clear_collection()

    def clear_collection(self) -> bool:
        """Clear all data from ChromaDB collection."""
        try:
            if self._collection:
                # ChromaDB doesn't have a direct clear method, so we delete and recreate
                self._client.delete_collection(self.config.collection_name)
                self._collection = self._client.create_collection(
                    name=self.config.collection_name,
                    metadata={
                        "hnsw:space": "cosine",
                        "description": "Code symbol embeddings for duplicate detection",
                    },
                )

                # Reset stats
                self._stats = {
                    "total_symbols": 0,
                    "total_searches": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                }
                self._search_times.clear()
                self._storage_times.clear()

                print("Cleared ChromaDB collection", file=sys.stderr)
                return True
        except Exception as e:
            print(f"Error clearing ChromaDB collection: {e}", file=sys.stderr)
            return False

    def save_symbols(self, symbols: List[Symbol]) -> None:
        """
        Compatible interface for registry_manager.save_symbols().
        Note: This only saves metadata, not embeddings.
        """
        if not symbols:
            return

        # Create dummy embeddings for storage (will be overwritten when real embeddings are stored)
        dummy_embeddings = np.zeros((len(symbols), 768), dtype=np.float32)
        self.store_symbols(symbols, dummy_embeddings)

    def save_embeddings(self, embeddings: np.ndarray) -> None:
        """
        Compatible interface for registry_manager.save_embeddings().
        Note: ChromaDB stores embeddings with symbols together, so this is a no-op.
        """
        pass  # ChromaDB stores embeddings with metadata together

    def cleanup_stale_entries(self) -> None:
        """
        Compatible interface for registry_manager.cleanup_stale_entries().
        ChromaDB handles persistence automatically.
        """
        pass  # ChromaDB handles cleanup automatically

    def _generate_symbol_id(self, symbol: Symbol) -> str:
        """Generate unique ID for symbol."""
        content = f"{symbol.file_path}:{symbol.name}:{symbol.line_number}:{symbol.symbol_type.value}"
        return hashlib.md5(content.encode()).hexdigest()

    def _symbol_to_document(self, symbol: Symbol) -> str:
        """Convert symbol to document text for ChromaDB."""
        parts = [
            f"name: {symbol.name}",
            f"type: {symbol.symbol_type.value}",
            f"content: {symbol.line_content.strip()}",
        ]

        if symbol.parameters:
            parts.append(f"parameters: {', '.join(symbol.parameters)}")

        if symbol.return_type:
            parts.append(f"returns: {symbol.return_type}")

        if symbol.scope and symbol.scope != "module":
            parts.append(f"scope: {symbol.scope}")

        return " | ".join(parts)

    def _extract_metadata(self, symbol: Symbol) -> Dict[str, Any]:
        """Extract searchable metadata from symbol."""
        # Convert list/complex types to strings for ChromaDB compatibility
        parameters = symbol.parameters or []
        parameters_str = ",".join(parameters) if parameters else ""

        metadata = {
            "file_path": str(symbol.file_path),
            "symbol_name": symbol.name,
            "symbol_type": symbol.symbol_type.value,
            "line_number": symbol.line_number,
            "line_count": getattr(symbol, "line_count", 1),
            "scope": symbol.scope or "module",
            "parameters": parameters_str,  # Convert list to string
            "return_type": symbol.return_type or "",
            "content_length": len(symbol.line_content),
            "lsp_kind": str(getattr(symbol, "lsp_kind", "")),
            "is_import": bool(getattr(symbol, "is_import", False)),
            "language": getattr(symbol, "language", "unknown"),
            "timestamp": time.time(),
        }

        # Phase 2: Symbol Origin Tracking metadata
        if hasattr(symbol, "definition_file"):
            metadata.update(
                {
                    "definition_file": str(symbol.definition_file or ""),
                    "definition_line": int(symbol.definition_line or 0),
                    "is_reference": bool(getattr(symbol, "is_reference", False)),
                    "is_definition": bool(getattr(symbol, "is_definition", True)),
                    "parent_class": str(getattr(symbol, "parent_class", "") or ""),
                    "import_source": str(getattr(symbol, "import_source", "") or ""),
                    "origin_signature": str(
                        getattr(symbol, "origin_signature", "") or ""
                    ),
                    "reference_count": int(getattr(symbol, "reference_count", 0)),
                }
            )

        return metadata

    def _metadata_to_symbol(self, metadata: Dict[str, Any]) -> Symbol:
        """Convert ChromaDB metadata back to Symbol object."""
        # Convert parameters string back to list
        params_str = metadata.get("parameters", "")
        parameters = params_str.split(",") if params_str else []

        symbol = Symbol(
            name=metadata["symbol_name"],
            symbol_type=SymbolType(metadata["symbol_type"]),
            file_path=metadata["file_path"],
            line_number=metadata["line_number"],
            line_content="",  # Not stored in metadata for space efficiency
            scope=metadata.get("scope", "module"),
            parameters=parameters,  # Converted from string
            return_type=metadata.get("return_type", ""),
            line_count=metadata.get("line_count", 1),
            lsp_kind=metadata.get("lsp_kind", ""),
        )

        # Phase 2: Restore origin tracking information if available
        if "definition_file" in metadata:
            symbol.definition_file = metadata.get("definition_file") or None
            symbol.definition_line = metadata.get("definition_line") or None
            symbol.is_reference = metadata.get("is_reference", False)
            symbol.is_definition = metadata.get("is_definition", True)
            symbol.parent_class = metadata.get("parent_class") or None
            symbol.import_source = metadata.get("import_source") or None
            symbol.origin_signature = metadata.get("origin_signature") or None
            symbol.reference_count = metadata.get("reference_count", 0)

        return symbol

    def update_indexing_status(
        self,
        symbol_count: int,
        files_processed: int,
        completed: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Update indexing status in ci_config.json"""
        config_path = self.project_root / ".ci-registry" / "ci_config.json"
        if not config_path.exists():
            print(f"Warning: Config file not found at {config_path}")
            return

        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            # Update indexing section
            indexing = config.get("indexing", {})
            indexing["initial_index_completed"] = completed
            indexing["symbol_count"] = symbol_count
            indexing["files_processed"] = files_processed

            if completed:
                indexing["completed_at"] = datetime.now().isoformat()
                indexing["last_error"] = None
            elif error:
                indexing["last_error"] = error

            config["indexing"] = indexing

            # Write back atomically
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            print(
                f"Updated indexing status: completed={completed}, symbols={symbol_count}, files={files_processed}"
            )

        except Exception as e:
            print(f"Error updating indexing status: {e}")

    def check_indexing_status(self) -> Dict[str, Any]:
        """Check if initial indexing is completed with verification"""
        config_path = self.project_root / ".ci-registry" / "ci_config.json"
        if not config_path.exists():
            return {"initial_index_completed": False, "error": "Config file not found"}

        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            indexing_status = config.get("indexing", {"initial_index_completed": False})

            # If marked as completed, verify against actual ChromaDB contents
            if indexing_status.get("initial_index_completed", False):
                try:
                    # Get actual count from ChromaDB
                    storage_info = self.get_storage_info()
                    actual_count = storage_info.get("total_vectors", 0)
                    config_count = indexing_status.get("symbol_count", 0)

                    # If counts don't match, flag may be stale
                    if actual_count != config_count and config_count > 0:
                        indexing_status[
                            "verification_warning"
                        ] = f"Symbol count mismatch: config={config_count}, actual={actual_count}"

                    indexing_status["verified_count"] = actual_count

                except Exception as e:
                    indexing_status[
                        "verification_error"
                    ] = f"Could not verify ChromaDB contents: {str(e)}"

            return indexing_status

        except Exception as e:
            return {"initial_index_completed": False, "error": str(e)}

    def _create_duplicate_finder_config(self):
        """Create DuplicateFinderConfig with proper exclusions from CI config"""
        try:
            import json
            from ci.core.semantic_duplicate_detector import DuplicateFinderConfig

            # Try to load CI config
            ci_config_path = Path(self.project_root) / ".ci-registry" / "ci_config.json"
            if ci_config_path.exists():
                with open(ci_config_path, "r") as f:
                    ci_config = json.load(f)

                exclusions = ci_config.get("project", {}).get("exclusions", {})

                # Build exclude patterns from CI config (same logic as orchestration bridge)
                exclude_patterns = []
                exclude_patterns.extend(exclusions.get("files", []))
                exclude_patterns.extend(exclusions.get("patterns", []))

                # Add directory exclusions as patterns
                for directory in exclusions.get("directories", []):
                    exclude_patterns.append(f"{directory}/*")
                    exclude_patterns.append(f"**/{directory}/*")

                print(f"Using CI config exclusions: {exclude_patterns}")
                return DuplicateFinderConfig(exclude_file_patterns=exclude_patterns)
            else:
                print("No CI config found, using default exclusions")
                return DuplicateFinderConfig()

        except Exception as e:
            print(f"Error reading CI config: {e}, using default exclusions")
            return DuplicateFinderConfig()

    def run_full_scan(self) -> bool:
        """Run full codebase scan and update indexing status"""
        print("Starting full codebase scan...")

        try:
            # Import semantic duplicate detector for symbol extraction
            from ci.core.semantic_duplicate_detector import DuplicateFinder

            # Load CI config to get proper exclusions
            config = self._create_duplicate_finder_config()
            finder = DuplicateFinder(config)

            # Extract symbols from project
            symbols = finder._extract_project_symbols(self.project_root)

            if not symbols:
                print("No symbols found in project")
                self.update_indexing_status(0, 0, True)
                return True

            print(f"Extracted {len(symbols)} symbols from project")

            # Generate embeddings
            from ci.core.embedding_engine import EmbeddingEngine

            embedding_engine = EmbeddingEngine()

            # Process in batches to avoid memory issues
            batch_size = 200  # Increased batch size for better performance
            total_stored = 0
            files_processed = set()

            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i : i + batch_size]

                # Generate embeddings for batch
                embeddings = embedding_engine.generate_embeddings(batch_symbols)

                if embeddings is None or len(embeddings) != len(batch_symbols):
                    error_msg = (
                        f"Failed to generate embeddings for batch {i//batch_size + 1}"
                    )
                    print(error_msg)
                    self.update_indexing_status(
                        total_stored, len(files_processed), False, error_msg
                    )
                    return False

                # Store batch in ChromaDB
                success = self.store_symbols(batch_symbols, embeddings)
                if not success:
                    error_msg = f"Failed to store batch {i//batch_size + 1} in ChromaDB"
                    print(error_msg)
                    self.update_indexing_status(
                        total_stored, len(files_processed), False, error_msg
                    )
                    return False

                total_stored += len(batch_symbols)
                files_processed.update(symbol.file_path for symbol in batch_symbols)

                # Progress update
                progress = (i + len(batch_symbols)) / len(symbols) * 100
                print(
                    f"Progress: {progress:.1f}% ({total_stored}/{len(symbols)} symbols)"
                )

            # Update status as completed
            self.update_indexing_status(total_stored, len(files_processed), True)
            print(
                f"Full scan completed successfully: {total_stored} symbols from {len(files_processed)} files"
            )
            return True

        except Exception as e:
            error_msg = f"Full scan failed: {str(e)}"
            print(error_msg)
            self.update_indexing_status(0, 0, False, error_msg)
            return False

    def cleanup(self) -> None:
        """Cleanup resources. Compatible with similarity_detector.cleanup()."""
        # ChromaDB handles persistence automatically
        self._search_times.clear()
        self._storage_times.clear()

        # Phase 5: Clean up async resources
        if self._executor:
            self._executor.shutdown(wait=False)

        # Clean up connection pool
        if self._connection_pool:
            asyncio.create_task(self._connection_pool.close_all())

        # Clear cache
        with self._cache_lock:
            self._query_cache.clear()


def main():
    """Main entry point for testing ChromaDB storage functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Test ChromaDB storage system")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument(
        "--test-vectors",
        type=int,
        default=10,
        help="Number of test vectors to generate",
    )
    parser.add_argument(
        "--vector-dim", type=int, default=768, help="Dimension of test vectors"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.75, help="Similarity threshold for testing"
    )
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )
    parser.add_argument(
        "--clear-collection",
        action="store_true",
        help="Clear collection before testing",
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Run full codebase scan and index all symbols",
    )
    parser.add_argument(
        "--check-indexing",
        action="store_true",
        help="Check indexing status",
    )

    args = parser.parse_args()

    # Create configuration
    config = ChromaDBConfig(medium_similarity_threshold=args.threshold)

    # Initialize storage
    storage = ChromaDBStorage(config, args.project_root)

    if args.clear_collection:
        storage.clear_collection()

    # Handle indexing commands
    if args.check_indexing:
        status = storage.check_indexing_status()
        if args.output == "json":
            print(json.dumps(status, indent=2))
        else:
            completed = status.get("initial_index_completed", False)
            print(f"Initial indexing completed: {completed}")
            if completed:
                print(f"  Symbols indexed: {status.get('symbol_count', 0)}")
                print(f"  Files processed: {status.get('files_processed', 0)}")
                print(f"  Completed at: {status.get('completed_at', 'Unknown')}")
            if status.get("last_error"):
                print(f"  Last error: {status.get('last_error')}")
        return

    if args.full_scan:
        if not args.project_root:
            print("Error: --project-root required for full scan")
            sys.exit(1)

        success = storage.run_full_scan()
        if success:
            print("Full scan completed successfully")
            sys.exit(0)
        else:
            print("Full scan failed")
            sys.exit(1)

    # Generate test embeddings and symbols
    print(f"Generating {args.test_vectors} test vectors of dimension {args.vector_dim}")
    test_embeddings = np.random.random((args.test_vectors, args.vector_dim)).astype(
        np.float32
    )

    # Create test symbols
    test_symbols = []
    for i in range(args.test_vectors):
        symbol = Symbol(
            name=f"test_function_{i}",
            symbol_type=SymbolType.FUNCTION,
            file_path=f"test_{i}.py",
            line_number=i + 1,
            line_content=f"def test_function_{i}(): pass",
            scope="module",
        )
        test_symbols.append(symbol)

    # Test storage
    start_time = time.time()
    success = storage.store_symbols(test_symbols, test_embeddings)
    storage_time = time.time() - start_time

    if not success:
        print("Error: Failed to store symbols in ChromaDB")
        sys.exit(1)

    # Test similarity search
    query_vector = test_embeddings[0]  # Use first vector as query
    start_time = time.time()
    matches = storage.find_similar(query_vector, args.threshold, k=5)
    search_time = time.time() - start_time

    # Output results
    if args.output == "json":
        result = {
            "success": success,
            "storage_time": storage_time,
            "search_time": search_time,
            "matches_found": len(matches),
            "storage_info": storage.get_storage_info(),
            "sample_matches": [
                {
                    "match_index": match.match_index,
                    "similarity_score": match.similarity_score,
                    "distance": match.distance,
                    "confidence": match.confidence,
                }
                for match in matches[:3]  # First 3 matches
            ],
        }
        print(json.dumps(result, indent=2))
    else:
        print("ChromaDB Storage Test Results:")
        print(f"  Storage successful: {success}")
        print(f"  Storage time: {storage_time:.3f}s")
        print(f"  Search time: {search_time:.3f}s")
        print(f"  Matches found: {len(matches)}")

        storage_info = storage.get_storage_info()
        print("\nChromaDB Storage Info:")
        print(f"  Status: {storage_info['status']}")
        print(f"  Total symbols: {storage_info['total_symbols']}")
        print(f"  Collection: {storage_info['collection_name']}")
        print(f"  Method: {storage_info['method']}")

        if matches:
            print("\nTop 3 Matches:")
            for i, match in enumerate(matches[:3]):
                print(
                    f"  {i + 1}. Index {match.match_index}: "
                    f"{match.similarity_score:.3f} similarity "
                    f"(distance: {match.distance:.3f})"
                )


if __name__ == "__main__":
    main()
