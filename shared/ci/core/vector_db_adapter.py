#!/usr/bin/env python3
"""
Vector Database Adapter Interface for CI Monitoring System

Provides pluggable storage backends for semantic embeddings and similarity search.
Enables switching between file-based (Faiss) and cloud vector database solutions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

# Setup import paths and import Symbol
try:
    from utils import path_resolver  # noqa: F401
    from ci.integration.symbol_extractor import Symbol
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class StorageBackend(Enum):
    """Available storage backend types."""

    FILE_BASED = "file_based"
    CHROMA_DB = "chroma_db"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    PINECONE = "pinecone"


@dataclass
class VectorSearchResult:
    """Result from vector similarity search."""

    symbol_id: str
    symbol: Symbol
    similarity_score: float
    distance: float
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VectorDBConfig:
    """Base configuration for vector database backends."""

    backend_type: StorageBackend
    collection_name: str = "code_symbols"
    embedding_dimension: int = 768  # CodeBERT default
    similarity_metric: str = "cosine"

    # Performance settings
    batch_size: int = 100
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600

    # Connection settings (backend-specific)
    connection_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.connection_params is None:
            self.connection_params = {}


@dataclass
class ChromaDBConfig(VectorDBConfig):
    """Configuration for ChromaDB backend."""

    backend_type: StorageBackend = StorageBackend.CHROMA_DB
    persist_directory: Optional[Path] = None
    host: Optional[str] = None
    port: Optional[int] = None

    def __post_init__(self):
        super().__post_init__()
        if self.persist_directory is None:
            self.persist_directory = Path.cwd() / ".ci-registry" / "chromadb"


@dataclass
class FileBasedConfig(VectorDBConfig):
    """Configuration for file-based (Faiss) backend."""

    backend_type: StorageBackend = StorageBackend.FILE_BASED
    index_type: str = "IndexFlatIP"  # Inner product for cosine similarity
    storage_directory: Optional[Path] = None

    def __post_init__(self):
        super().__post_init__()
        if self.storage_directory is None:
            self.storage_directory = Path.cwd() / ".ci-registry" / "faiss"


class VectorDBAdapter(ABC):
    """Abstract base class for vector database adapters.

    Provides a unified interface for different vector storage backends,
    enabling seamless switching between file-based and cloud solutions.
    """

    def __init__(self, config: VectorDBConfig):
        self.config = config
        self._is_initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the vector database connection.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, embedding_dim: int) -> bool:
        """Create a new collection for storing embeddings.

        Args:
            collection_name: Name of the collection
            embedding_dim: Dimension of embeddings to store

        Returns:
            True if collection created successfully, False otherwise
        """
        pass

    @abstractmethod
    def store_embeddings(
        self,
        symbols: List[Symbol],
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Store symbol embeddings in the database.

        Args:
            symbols: List of symbols to store
            embeddings: Corresponding embeddings array
            metadata: Optional metadata for each symbol

        Returns:
            True if storage successful, False otherwise
        """
        pass

    @abstractmethod
    def similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Perform similarity search for a query embedding.

        Args:
            query_embedding: Query vector to search for
            top_k: Maximum number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters

        Returns:
            List of search results ordered by similarity
        """
        pass

    @abstractmethod
    def batch_similarity_search(
        self,
        query_embeddings: np.ndarray,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[int, List[VectorSearchResult]]:
        """Perform batch similarity search for multiple queries.

        Args:
            query_embeddings: Array of query vectors
            top_k: Maximum results per query
            threshold: Minimum similarity threshold
            filters: Optional metadata filters

        Returns:
            Dictionary mapping query indices to search results
        """
        pass

    @abstractmethod
    def get_embeddings(
        self, symbol_ids: List[str]
    ) -> Dict[str, Tuple[Symbol, np.ndarray]]:
        """Retrieve embeddings for specific symbols.

        Args:
            symbol_ids: List of symbol IDs to retrieve

        Returns:
            Dictionary mapping symbol IDs to (symbol, embedding) tuples
        """
        pass

    @abstractmethod
    def delete_embeddings(self, symbol_ids: List[str]) -> bool:
        """Delete embeddings for specific symbols.

        Args:
            symbol_ids: List of symbol IDs to delete

        Returns:
            True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    def update_embeddings(
        self,
        symbol_ids: List[str],
        symbols: List[Symbol],
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Update existing embeddings.

        Args:
            symbol_ids: IDs of symbols to update
            symbols: Updated symbol objects
            embeddings: Updated embeddings
            metadata: Updated metadata

        Returns:
            True if update successful, False otherwise
        """
        pass

    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        pass

    @abstractmethod
    def clear_collection(self) -> bool:
        """Clear all data from the collection.

        Returns:
            True if clearing successful, False otherwise
        """
        pass

    @abstractmethod
    def close(self):
        """Close the database connection and cleanup resources."""
        pass

    # Utility methods

    def is_initialized(self) -> bool:
        """Check if adapter is initialized."""
        return self._is_initialized

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the backend."""
        return {
            "backend_type": self.config.backend_type.value,
            "collection_name": self.config.collection_name,
            "embedding_dimension": self.config.embedding_dimension,
            "similarity_metric": self.config.similarity_metric,
            "is_initialized": self._is_initialized,
            "config": self.config.__dict__,
        }

    def _generate_symbol_id(self, symbol: Symbol) -> str:
        """Generate a unique ID for a symbol."""
        import hashlib

        content = f"{symbol.file_path}:{symbol.name}:{symbol.line_number}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _extract_metadata(self, symbol: Symbol) -> Dict[str, Any]:
        """Extract searchable metadata from a symbol."""
        return {
            "file_path": str(symbol.file_path),
            "symbol_name": symbol.name,
            "symbol_type": symbol.symbol_type.value,
            "line_number": symbol.line_number,
            "language": getattr(symbol, "language", "unknown"),
            "content_length": len(symbol.line_content),
            "timestamp": symbol.created_at if hasattr(symbol, "created_at") else None,
        }


def create_vector_db_adapter(config: VectorDBConfig) -> VectorDBAdapter:
    """Factory function to create vector DB adapters based on configuration.

    Args:
        config: Vector database configuration

    Returns:
        Configured vector database adapter

    Raises:
        ValueError: If backend type is not supported
    """
    if config.backend_type == StorageBackend.FILE_BASED:
        from .faiss_backend import FaissBackend

        return FaissBackend(config)
    elif config.backend_type == StorageBackend.CHROMA_DB:
        from .chromadb_backend import ChromaDBBackend

        return ChromaDBBackend(config)
    else:
        raise ValueError(f"Unsupported backend type: {config.backend_type}")
