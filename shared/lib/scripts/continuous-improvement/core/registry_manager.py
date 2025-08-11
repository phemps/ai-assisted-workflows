#!/usr/bin/env python3
"""
Registry Manager for Continuous Improvement Framework

Provides file-based storage and management for symbol registry with
incremental updates and performance optimization. Part of Claude Code
Workflows - integrates with 8-agent orchestration system.
"""

import hashlib
import json
import pickle
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

import numpy as np

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))

# Import utilities and existing components
try:
    from output_formatter import ResultFormatter
    from tech_stack_detector import TechStackDetector
except ImportError as e:
    print(f"Error importing utilities: {e}", file=sys.stderr)
    sys.exit(1)

# Import Symbol from analyzers
try:
    from ..analyzers.symbol_extractor import Symbol
except ImportError:
    try:
        # Fallback for direct execution
        sys.path.insert(0, str(Path(__file__).parent.parent / "analyzers"))
        from symbol_extractor import Symbol
    except ImportError as e:
        print(f"Error importing Symbol: {e}", file=sys.stderr)
        sys.exit(1)


class RegistryStatus(Enum):
    """Status of registry operations."""

    HEALTHY = "healthy"
    STALE = "stale"
    CORRUPTED = "corrupted"
    MISSING = "missing"
    WRITE_ERROR = "write_error"
    READ_ERROR = "read_error"


class ChangeType(Enum):
    """Types of file changes for incremental updates."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class RegistryEntry:
    """Represents a registry entry with symbol and metadata."""

    symbol: Symbol
    embedding: Optional[np.ndarray] = None
    similarity_metadata: Optional[Dict[str, Any]] = None
    file_hash: str = ""
    last_updated: float = 0.0
    embedding_method: str = "unknown"
    similarity_method: str = "unknown"

    def __post_init__(self):
        """Initialize timestamps and hashes."""
        if self.last_updated == 0.0:
            self.last_updated = time.time()

        # Generate file hash if not provided
        if not self.file_hash and self.symbol.file_path:
            try:
                file_path = Path(self.symbol.file_path)
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    self.file_hash = hashlib.md5(content.encode()).hexdigest()
            except Exception:
                self.file_hash = "unknown"


@dataclass
class RegistryConfig:
    """Configuration for registry manager following existing patterns."""

    # Storage settings
    registry_dir: str = ".claude/cache/registry"
    compression_enabled: bool = True
    backup_count: int = 3

    # Performance settings
    batch_size: int = 100
    max_memory_gb: float = 1.0
    enable_indexing: bool = True

    # Cache and TTL settings
    cache_ttl_hours: int = 168  # 1 week
    stale_threshold_hours: int = 24
    cleanup_interval_hours: int = 6

    # File tracking
    track_file_changes: bool = True
    hash_chunk_size: int = 8192
    include_file_patterns: Optional[List[str]] = None
    exclude_file_patterns: Optional[List[str]] = None

    # Incremental update settings
    force_update_threshold: float = 0.8  # Force update if 80% changed
    batch_update_size: int = 50

    def __post_init__(self):
        """Initialize default patterns."""
        if self.include_file_patterns is None:
            self.include_file_patterns = [
                "*.py",
                "*.js",
                "*.ts",
                "*.java",
                "*.cpp",
                "*.h",
                "*.go",
                "*.rs",
                "*.php",
                "*.rb",
            ]

        if self.exclude_file_patterns is None:
            self.exclude_file_patterns = [
                "*.pyc",
                "*/node_modules/*",
                "*/.git/*",
                "*/test/*",
                "*_test.py",
                "*.spec.*",
            ]


class RegistryManager:
    """
    File-based registry storage and management for symbols, embeddings,
    and similarity data with comprehensive caching and incremental updates.
    """

    def __init__(
        self,
        config: Optional[RegistryConfig] = None,
        project_root: Optional[Path] = None,
    ):
        self.config = config or RegistryConfig()
        self.project_root = project_root or Path.cwd()

        # Initialize components
        self.tech_detector = TechStackDetector()
        self.result_formatter = ResultFormatter()

        # Storage paths
        self.registry_dir = self.project_root / self.config.registry_dir
        self.symbols_dir = self.registry_dir / "symbols"
        self.metadata_dir = self.registry_dir / "metadata"
        self.index_file = self.registry_dir / "index.json"

        # Create directories
        for dir_path in [
            self.registry_dir,
            self.symbols_dir,
            self.metadata_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Cache and tracking
        self._registry_cache: Dict[str, RegistryEntry] = {}
        self._file_hashes: Dict[str, str] = {}
        self._index_data: Dict[str, Any] = {}

        # Performance tracking
        self._operation_times = {"read": [], "write": [], "update": []}
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}

        # Load existing data
        self._load_index()
        self._load_file_hashes()

    def _load_index(self) -> None:
        """Load registry index from disk."""
        try:
            if self.index_file.exists():
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self._index_data = json.load(f)
            else:
                self._index_data = {
                    "created_at": time.time(),
                    "last_updated": time.time(),
                    "symbols_count": 0,
                    "files_tracked": {},
                    "version": "1.0",
                }
        except Exception as e:
            print(f"Index load error: {e}", file=sys.stderr)
            self._index_data = {}

    def _save_index(self) -> None:
        """Save registry index to disk."""
        try:
            self._index_data["last_updated"] = time.time()
            self._index_data["symbols_count"] = len(self._registry_cache)

            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self._index_data, f, indent=2)
        except Exception as e:
            print(f"Index save error: {e}", file=sys.stderr)

    def _load_file_hashes(self) -> None:
        """Load tracked file hashes for change detection."""
        try:
            hash_file = self.metadata_dir / "file_hashes.json"
            if hash_file.exists():
                with open(hash_file, "r", encoding="utf-8") as f:
                    self._file_hashes = json.load(f)
        except Exception as e:
            print(f"File hash load error: {e}", file=sys.stderr)
            self._file_hashes = {}

    def _save_file_hashes(self) -> None:
        """Save tracked file hashes to disk."""
        try:
            hash_file = self.metadata_dir / "file_hashes.json"
            with open(hash_file, "w", encoding="utf-8") as f:
                json.dump(self._file_hashes, f, indent=2)
        except Exception as e:
            print(f"File hash save error: {e}", file=sys.stderr)

    def _get_entry_key(self, file_path: str, symbol_name: str) -> str:
        """Generate unique key for registry entry."""
        # Use project-relative path for portability
        try:
            rel_path = Path(file_path).relative_to(self.project_root)
            normalized_path = str(rel_path).replace("\\", "/")
        except ValueError:
            # Fallback for absolute paths outside project
            normalized_path = str(Path(file_path).as_posix())

        key_data = f"{normalized_path}::{symbol_name}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_file_hash(self, file_path: Path) -> str:
        """Get content hash for file change detection."""
        try:
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(self.config.hash_chunk_size), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return "error"

    def register_symbol(
        self,
        symbol: Symbol,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register a symbol with optional embedding and metadata.

        Args:
            symbol: Symbol to register
            embedding: Optional embedding vector
            metadata: Optional similarity/analysis metadata

        Returns:
            True if registration successful, False otherwise
        """
        start_time = time.time()

        try:
            # Create registry entry
            entry = RegistryEntry(
                symbol=symbol,
                embedding=embedding,
                similarity_metadata=metadata or {},
                last_updated=time.time(),
            )

            # Update file hash if tracking enabled
            if self.config.track_file_changes and symbol.file_path:
                file_path = Path(symbol.file_path)
                if file_path.exists():
                    entry.file_hash = self._get_file_hash(file_path)
                    self._file_hashes[str(file_path)] = entry.file_hash

            # Store in cache and persist to disk
            entry_key = self._get_entry_key(symbol.file_path, symbol.name)
            self._registry_cache[entry_key] = entry

            # Persist entry
            success = self._persist_entry(entry_key, entry)

            if success:
                # Update index
                file_key = str(Path(symbol.file_path))
                if file_key not in self._index_data.get("files_tracked", {}):
                    self._index_data.setdefault("files_tracked", {})[file_key] = {
                        "symbols": [],
                        "last_updated": time.time(),
                    }

                if (
                    symbol.name
                    not in self._index_data["files_tracked"][file_key]["symbols"]
                ):
                    self._index_data["files_tracked"][file_key]["symbols"].append(
                        symbol.name
                    )

                self._save_index()

                # Track performance
                execution_time = time.time() - start_time
                self._operation_times["write"].append(execution_time)

            return success

        except Exception as e:
            print(f"Symbol registration error: {e}", file=sys.stderr)
            return False

    def _persist_entry(self, entry_key: str, entry: RegistryEntry) -> bool:
        """Persist registry entry to disk."""
        try:
            entry_file = self.symbols_dir / f"{entry_key}.pkl"

            # Prepare data for serialization
            entry_data = {
                "symbol": asdict(entry.symbol),
                "embedding": entry.embedding,
                "similarity_metadata": entry.similarity_metadata,
                "file_hash": entry.file_hash,
                "last_updated": entry.last_updated,
                "embedding_method": entry.embedding_method,
                "similarity_method": entry.similarity_method,
            }

            with open(entry_file, "wb") as f:
                pickle.dump(entry_data, f)

            return True

        except Exception as e:
            print(f"Entry persist error: {e}", file=sys.stderr)
            return False

    def get_symbol(self, file_path: str, symbol_name: str) -> Optional[RegistryEntry]:
        """
        Retrieve symbol registry entry.

        Args:
            file_path: Path to source file
            symbol_name: Name of symbol to retrieve

        Returns:
            RegistryEntry if found, None otherwise
        """
        start_time = time.time()
        entry_key = self._get_entry_key(file_path, symbol_name)

        # Check cache first
        if entry_key in self._registry_cache:
            self._cache_stats["hits"] += 1
            return self._registry_cache[entry_key]

        # Load from disk
        try:
            entry = self._load_entry(entry_key)
            if entry:
                self._registry_cache[entry_key] = entry
                self._cache_stats["hits"] += 1
            else:
                self._cache_stats["misses"] += 1

            # Track performance
            execution_time = time.time() - start_time
            self._operation_times["read"].append(execution_time)

            return entry

        except Exception as e:
            self._cache_stats["errors"] += 1
            print(f"Symbol retrieval error: {e}", file=sys.stderr)
            return None

    def _load_entry(self, entry_key: str) -> Optional[RegistryEntry]:
        """Load registry entry from disk."""
        try:
            entry_file = self.symbols_dir / f"{entry_key}.pkl"

            if not entry_file.exists():
                return None

            with open(entry_file, "rb") as f:
                entry_data = pickle.load(f)

            # Reconstruct Symbol object
            from ..analyzers.symbol_extractor import Symbol, SymbolType

            symbol_data = entry_data["symbol"]
            symbol = Symbol(
                name=symbol_data["name"],
                symbol_type=SymbolType(symbol_data["symbol_type"]),
                file_path=symbol_data["file_path"],
                line_number=symbol_data["line_number"],
                line_content=symbol_data["line_content"],
                scope=symbol_data["scope"],
                visibility=symbol_data.get("visibility"),
                parameters=symbol_data.get("parameters"),
                return_type=symbol_data.get("return_type"),
                complexity=symbol_data.get("complexity"),
                dependencies=symbol_data.get("dependencies"),
            )

            entry = RegistryEntry(
                symbol=symbol,
                embedding=entry_data.get("embedding"),
                similarity_metadata=entry_data.get("similarity_metadata", {}),
                file_hash=entry_data.get("file_hash", ""),
                last_updated=entry_data.get("last_updated", time.time()),
                embedding_method=entry_data.get("embedding_method", "unknown"),
                similarity_method=entry_data.get("similarity_method", "unknown"),
            )

            return entry

        except Exception as e:
            print(f"Entry load error for {entry_key}: {e}", file=sys.stderr)
            return None

    def update_symbols(self, symbols: List[Symbol]) -> Dict[str, bool]:
        """
        Perform incremental update of symbols based on file changes.

        Args:
            symbols: List of symbols to update

        Returns:
            Dictionary mapping symbol keys to update success status
        """
        start_time = time.time()
        results = {}
        updated_count = 0

        try:
            # Group symbols by file for efficient processing
            symbols_by_file: Dict[str, List[Symbol]] = {}
            for symbol in symbols:
                file_key = str(Path(symbol.file_path))
                symbols_by_file.setdefault(file_key, []).append(symbol)

            # Process each file
            for file_path, file_symbols in symbols_by_file.items():
                file_change_type = self._detect_file_changes(Path(file_path))

                # Skip unchanged files unless force update needed
                if file_change_type == ChangeType.UNCHANGED:
                    for symbol in file_symbols:
                        entry_key = self._get_entry_key(symbol.file_path, symbol.name)
                        results[entry_key] = True  # No update needed
                    continue

                # Process symbols in batches
                for i in range(0, len(file_symbols), self.config.batch_update_size):
                    batch = file_symbols[i : i + self.config.batch_update_size]

                    for symbol in batch:
                        entry_key = self._get_entry_key(symbol.file_path, symbol.name)

                        # Check if update needed
                        existing_entry = self.get_symbol(symbol.file_path, symbol.name)

                        if self._should_update_symbol(existing_entry, symbol):
                            # Preserve existing embedding and metadata
                            embedding = (
                                existing_entry.embedding if existing_entry else None
                            )
                            metadata = (
                                existing_entry.similarity_metadata
                                if existing_entry
                                else {}
                            )

                            success = self.register_symbol(symbol, embedding, metadata)
                            results[entry_key] = success

                            if success:
                                updated_count += 1
                        else:
                            results[entry_key] = True  # No update needed

            # Track performance
            execution_time = time.time() - start_time
            self._operation_times["update"].append(execution_time)

            print(
                f"Updated {updated_count}/{len(symbols)} symbols "
                f"in {execution_time:.3f}s",
                file=sys.stderr,
            )

            return results

        except Exception as e:
            print(f"Symbols update error: {e}", file=sys.stderr)
            return {self._get_entry_key(s.file_path, s.name): False for s in symbols}

    def _detect_file_changes(self, file_path: Path) -> ChangeType:
        """Detect changes in file for incremental updates."""
        if not self.config.track_file_changes:
            return ChangeType.UNCHANGED

        try:
            file_key = str(file_path)

            if not file_path.exists():
                return ChangeType.DELETED

            current_hash = self._get_file_hash(file_path)
            previous_hash = self._file_hashes.get(file_key)

            if previous_hash is None:
                return ChangeType.ADDED

            if current_hash != previous_hash:
                return ChangeType.MODIFIED

            return ChangeType.UNCHANGED

        except Exception:
            return ChangeType.MODIFIED  # Safe fallback

    def _should_update_symbol(
        self, existing: Optional[RegistryEntry], new_symbol: Symbol
    ) -> bool:
        """Determine if symbol should be updated."""
        if existing is None:
            return True

        # Check if symbol data has changed
        content_changed = existing.symbol.line_content != new_symbol.line_content
        line_changed = existing.symbol.line_number != new_symbol.line_number
        if content_changed or line_changed:
            return True

        # Check if entry is stale
        age_hours = (time.time() - existing.last_updated) / 3600
        if age_hours > self.config.stale_threshold_hours:
            return True

        return False

    def cleanup_stale_entries(self, older_than_hours: Optional[int] = None) -> int:
        """
        Clean up stale registry entries.

        Args:
            older_than_hours: Remove entries older than this
                (uses config default if None)

        Returns:
            Number of entries cleaned up
        """
        older_than_hours = older_than_hours or self.config.cache_ttl_hours
        cutoff_time = time.time() - (older_than_hours * 3600)
        cleaned_count = 0

        try:
            # Find stale cache entries
            stale_keys = []
            for key, entry in self._registry_cache.items():
                if entry.last_updated < cutoff_time:
                    stale_keys.append(key)

            # Remove from cache
            for key in stale_keys:
                del self._registry_cache[key]
                cleaned_count += 1

            # Clean up disk files
            for entry_file in self.symbols_dir.glob("*.pkl"):
                try:
                    file_age = entry_file.stat().st_mtime
                    if file_age < cutoff_time:
                        entry_file.unlink()
                        cleaned_count += 1
                except Exception:
                    continue

            # Update index
            self._save_index()
            self._save_file_hashes()

            print(f"Cleaned up {cleaned_count} stale entries", file=sys.stderr)

            return cleaned_count

        except Exception as e:
            print(f"Cleanup error: {e}", file=sys.stderr)
            return 0

    def _calculate_avg_time(self, operation_type: str) -> float:
        """Calculate average time for operation type."""
        times = self._operation_times.get(operation_type, [])
        return sum(times) / max(len(times), 1)

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics and health info."""
        return {
            "status": self._get_registry_status(),
            "cache_stats": self._cache_stats.copy(),
            "storage_info": {
                "registry_dir": str(self.registry_dir),
                "symbols_cached": len(self._registry_cache),
                "files_tracked": len(self._file_hashes),
                "index_exists": self.index_file.exists(),
            },
            "performance": {
                "avg_read_time": self._calculate_avg_time("read"),
                "avg_write_time": self._calculate_avg_time("write"),
                "avg_update_time": self._calculate_avg_time("update"),
                "total_operations": sum(
                    len(times) for times in self._operation_times.values()
                ),
            },
            "config": {
                "cache_ttl_hours": self.config.cache_ttl_hours,
                "track_file_changes": self.config.track_file_changes,
                "batch_size": self.config.batch_size,
                "compression_enabled": self.config.compression_enabled,
            },
            "index_data": self._index_data.copy(),
        }

    def _get_registry_status(self) -> RegistryStatus:
        """Determine overall registry health status."""
        try:
            if not self.registry_dir.exists():
                return RegistryStatus.MISSING

            if not self.index_file.exists():
                return RegistryStatus.CORRUPTED

            # Check for stale data
            if self._index_data:
                last_updated = self._index_data.get("last_updated", 0)
                age_hours = (time.time() - last_updated) / 3600
                if age_hours > self.config.stale_threshold_hours:
                    return RegistryStatus.STALE

            return RegistryStatus.HEALTHY

        except Exception:
            return RegistryStatus.CORRUPTED


def main():
    """Main entry point for testing registry manager functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Test registry manager")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--cleanup", action="store_true", help="Clean up stale entries")
    parser.add_argument("--stats", action="store_true", help="Show registry statistics")
    parser.add_argument(
        "--output",
        choices=["json", "summary"],
        default="summary",
        help="Output format",
    )

    args = parser.parse_args()

    # Initialize registry manager
    config = RegistryConfig()
    manager = RegistryManager(config, args.project_root)

    if args.cleanup:
        cleaned = manager.cleanup_stale_entries()
        print(f"Cleaned up {cleaned} stale entries")
        return

    # Show statistics
    stats = manager.get_registry_stats()

    if args.output == "json":
        print(json.dumps(stats, indent=2, default=str))
    else:
        print("Registry Manager Status:")
        status_value = (
            stats["status"].value
            if hasattr(stats["status"], "value")
            else stats["status"]
        )
        print(f"  Status: {status_value}")
        print(f"  Symbols cached: {stats['storage_info']['symbols_cached']}")
        print(f"  Files tracked: {stats['storage_info']['files_tracked']}")
        print(f"  Cache hits: {stats['cache_stats']['hits']}")
        print(f"  Cache misses: {stats['cache_stats']['misses']}")
        print(f"  Total operations: {stats['performance']['total_operations']}")

        if stats["index_data"]:
            index_data = stats["index_data"]
            print("\nIndex Information:")
            print(f"  Created: {time.ctime(index_data.get('created_at', 0))}")
            print(
                f"  Last updated: " f"{time.ctime(index_data.get('last_updated', 0))}"
            )
            print(f"  Version: {index_data.get('version', 'unknown')}")


if __name__ == "__main__":
    main()
