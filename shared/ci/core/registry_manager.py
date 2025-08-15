#!/usr/bin/env python3
"""
Registry Manager for Continuous Improvement Framework (REFACTORED)

This is a refactored version demonstrating the use of new base utilities
to eliminate code duplication patterns. Part of AI-Assisted Workflows.
"""

import json
import pickle
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

import numpy as np

# Import base utilities (eliminates duplication)
from ..base import (
    CIConfigModule,
    ConfigFactory,
    RegistryConfig,
    timed_operation,
    PerformanceTracker,
    FileSystemUtils,
    atomic_write,
)

# Import Symbol from analyzers
try:
    from ..analyzers.symbol_extractor import Symbol
except ImportError:
    # Fallback for direct execution
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "analyzers"))
    from symbol_extractor import Symbol


class RegistryStatus(Enum):
    """Status of registry operations."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CORRUPTED = "corrupted"
    MISSING = "missing"


@dataclass
class RegistryStats:
    """Statistics for registry performance."""

    total_symbols: int
    unique_symbols: int
    duplicate_count: int
    last_updated: str
    registry_size_bytes: int
    index_size_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RefactoredRegistryManager(CIConfigModule):
    """Refactored Registry Manager using base utilities to eliminate duplication."""

    def __init__(self, project_root: str = "."):
        super().__init__("registry_manager", project_root)

        # Load configuration using base utilities
        self.config = self._load_registry_config()

        # Setup paths using base utilities
        self.registry_dir = self.get_config_path("")
        self.index_file = self.registry_dir / "registry_index.json"
        self.symbols_file = self.registry_dir / "symbols.pkl"
        self.embeddings_file = self.registry_dir / "embeddings.npy"

        # Performance tracking
        self.performance_tracker = PerformanceTracker()

        # Create necessary directories
        FileSystemUtils.ensure_directory(self.registry_dir)

        # Initialize if needed
        self._ensure_registry_initialized()

    def _load_registry_config(self) -> RegistryConfig:
        """Load registry configuration using config factory."""
        try:
            return ConfigFactory.create_from_file(
                "registry", self.get_config_path("registry_config.json")
            )
        except Exception:
            # Create default config if none exists
            config = ConfigFactory.create("registry")
            self.save_config("registry_config.json", config.to_dict())
            return config

    def _ensure_registry_initialized(self) -> None:
        """Ensure registry is properly initialized."""
        if not self.index_file.exists():
            self._create_empty_registry()

    @timed_operation("create_empty_registry")
    def _create_empty_registry(self) -> None:
        """Create empty registry structure using base utilities."""
        initial_index = {
            "version": "1.0",
            "created_at": time.time(),
            "last_updated": time.time(),
            "symbol_count": 0,
            "files_processed": [],
            "checksums": {},
        }

        # Use atomic write from base utilities
        with atomic_write(self.index_file) as f:
            json.dump(initial_index, f, indent=2)

        # Create empty arrays
        empty_symbols = []
        empty_embeddings = np.array([])

        with atomic_write(self.symbols_file, encoding=None) as f:
            pickle.dump(empty_symbols, f)

        np.save(self.embeddings_file, empty_embeddings)

        self.log_operation("registry_initialized")

    @timed_operation("load_registry_index")
    def load_index(self) -> Dict[str, Any]:
        """Load registry index using base utilities."""
        try:
            content = FileSystemUtils.safe_read_text(self.index_file)
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Use centralized error handling
            self.CIErrorHandler.config_error(
                f"Registry index is corrupted: {e}", self.index_file
            )

    @timed_operation("save_registry_index")
    def save_index(self, index: Dict[str, Any]) -> None:
        """Save registry index using base utilities."""
        index["last_updated"] = time.time()

        # Use atomic write for consistency
        with atomic_write(self.index_file) as f:
            json.dump(index, f, indent=2)

        self.log_operation("index_saved", {"symbols": index.get("symbol_count", 0)})

    @timed_operation("load_symbols")
    def load_symbols(self) -> List[Symbol]:
        """Load symbols from registry."""
        if not self.symbols_file.exists():
            return []

        try:
            with open(self.symbols_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            self.log_operation("symbol_load_error", {"error": str(e)})
            return []

    @timed_operation("save_symbols")
    def save_symbols(self, symbols: List[Symbol]) -> None:
        """Save symbols to registry using atomic operations."""
        with atomic_write(self.symbols_file, encoding=None) as f:
            pickle.dump(symbols, f)

        self.log_operation("symbols_saved", {"count": len(symbols)})

    @timed_operation("load_embeddings")
    def load_embeddings(self) -> np.ndarray:
        """Load embeddings from registry."""
        if not self.embeddings_file.exists():
            return np.array([])

        try:
            return np.load(self.embeddings_file)
        except Exception as e:
            self.log_operation("embedding_load_error", {"error": str(e)})
            return np.array([])

    @timed_operation("save_embeddings")
    def save_embeddings(self, embeddings: np.ndarray) -> None:
        """Save embeddings to registry."""
        np.save(self.embeddings_file, embeddings)
        self.log_operation("embeddings_saved", {"shape": embeddings.shape})

    def add_symbols(
        self, symbols: List[Symbol], embeddings: Optional[np.ndarray] = None
    ) -> None:
        """Add symbols to registry with performance tracking."""
        with self.performance_tracker.time_operation("add_symbols_batch") as timing:
            # Load existing data
            index = self.load_index()
            existing_symbols = self.load_symbols()
            existing_embeddings = self.load_embeddings()

            # Add new symbols
            existing_symbols.extend(symbols)

            if embeddings is not None:
                if existing_embeddings.size == 0:
                    combined_embeddings = embeddings
                else:
                    combined_embeddings = np.vstack([existing_embeddings, embeddings])
            else:
                combined_embeddings = existing_embeddings

            # Update index
            index["symbol_count"] = len(existing_symbols)

            # Save everything atomically
            self.save_symbols(existing_symbols)
            self.save_embeddings(combined_embeddings)
            self.save_index(index)

            timing.metadata["symbols_added"] = len(symbols)

    def get_registry_stats(self) -> RegistryStats:
        """Get registry statistics using base utilities."""
        index = self.load_index()
        symbols = self.load_symbols()

        # Calculate sizes safely
        registry_size = 0
        index_size = 0

        try:
            if self.symbols_file.exists():
                registry_size = self.symbols_file.stat().st_size
            if self.index_file.exists():
                index_size = self.index_file.stat().st_size
        except OSError:
            pass

        # Count unique symbols (by signature)
        unique_signatures = set()
        for symbol in symbols:
            signature = f"{symbol.name}:{symbol.symbol_type}:{symbol.file_path}"
            unique_signatures.add(signature)

        return RegistryStats(
            total_symbols=len(symbols),
            unique_symbols=len(unique_signatures),
            duplicate_count=len(symbols) - len(unique_signatures),
            last_updated=index.get("last_updated", 0),
            registry_size_bytes=registry_size,
            index_size_bytes=index_size,
        )

    def get_status(self) -> RegistryStatus:
        """Get registry health status."""
        try:
            if not self.index_file.exists():
                return RegistryStatus.MISSING

            index = self.load_index()

            # Basic validation
            if not isinstance(index.get("symbol_count"), int):
                return RegistryStatus.CORRUPTED

            if index.get("symbol_count", 0) == 0:
                return RegistryStatus.HEALTHY  # Empty but valid

            # Check if symbols file exists when count > 0
            if not self.symbols_file.exists():
                return RegistryStatus.DEGRADED

            return RegistryStatus.HEALTHY

        except Exception:
            return RegistryStatus.CORRUPTED

    def cleanup_registry(self, max_age_days: int = 30) -> int:
        """Clean up old registry entries."""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

        index = self.load_index()
        if index.get("last_updated", time.time()) > cutoff_time:
            return 0  # Registry is recent

        # For this example, we'll just clean temp files
        temp_files = FileSystemUtils.find_files(
            self.registry_dir, patterns=["*.tmp", "*.backup", "*.temp"]
        )

        removed_count = 0
        for temp_file in temp_files:
            try:
                temp_file.unlink()
                removed_count += 1
            except OSError:
                pass

        self.log_operation("registry_cleaned", {"files_removed": removed_count})
        return removed_count

    def generate_performance_report(self) -> str:
        """Generate performance report using timing utilities."""
        from ..base.timing_utils import create_performance_report

        report = create_performance_report(self.performance_tracker, "summary")

        stats = self.get_registry_stats()
        status = self.get_status()

        full_report = [
            "Registry Manager Performance Report",
            "=" * 40,
            f"Status: {status.value}",
            f"Total Symbols: {stats.total_symbols}",
            f"Unique Symbols: {stats.unique_symbols}",
            f"Registry Size: {stats.registry_size_bytes:,} bytes",
            "",
            "Performance Metrics:",
            report,
        ]

        return "\n".join(full_report)


def main():
    """CLI interface using base utilities."""
    from ..base.cli_utils import create_standard_cli, run_cli_tool

    cli = create_standard_cli(
        "registry-manager",
        "Manage symbol registry for continuous improvement",
        version="2.0.0",
    )

    cli.parser.add_argument(
        "command",
        choices=["status", "stats", "cleanup", "performance"],
        help="Command to execute",
    )

    def main_function(args):
        manager = RefactoredRegistryManager(str(args.project_root))

        if args.command == "status":
            status = manager.get_status()
            return {"registry_status": status.value}

        elif args.command == "stats":
            stats = manager.get_registry_stats()
            return stats.to_dict()

        elif args.command == "cleanup":
            removed_count = manager.cleanup_registry()
            return {"files_removed": removed_count}

        elif args.command == "performance":
            report = manager.generate_performance_report()
            print(report)
            return None

    return run_cli_tool(cli, main_function)


if __name__ == "__main__":
    exit(main())
