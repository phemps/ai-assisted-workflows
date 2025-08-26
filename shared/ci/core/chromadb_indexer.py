#!/usr/bin/env python3
"""
ChromaDB Indexer for Continuous Improvement Framework

Provides centralized indexing functionality that can be used by:
- orchestration_bridge.py for analysis workflows
- chromadb_index_hook.py for real-time file indexing
- Command-line tools for manual indexing

Part of AI-Assisted Workflows - integrates with 8-agent orchestration system.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add path manipulation like other analyzers do
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class ChromaDBIndexer:
    """
    Centralized ChromaDB indexing functionality.

    Provides methods for:
    - Incremental indexing of changed files
    - Full codebase indexing
    - Background indexing for real-time updates
    - Error handling and graceful degradation
    """

    def __init__(self, project_root: str = ".", test_mode: bool = False):
        self.project_root = Path(project_root).resolve()
        self.test_mode = test_mode
        self._setup_logging()
        self._ci_registry_path = self.project_root / ".ci-registry"

    def _setup_logging(self):
        """Setup logging for indexing operations."""
        logs_dir = self.project_root / ".ci-registry" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / "chromadb_indexing.log"

        # Configure logger
        self.logger = logging.getLogger("chromadb_indexer")
        self.logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def is_ci_initialized(self) -> bool:
        """Check if CI registry is initialized."""
        config_file = self._ci_registry_path / "ci_config.json"
        return self._ci_registry_path.exists() and config_file.exists()

    def can_index(self) -> tuple[bool, str]:
        """
        Check if indexing is possible.

        Returns:
            (can_index, reason): Boolean and reason string
        """
        if not self.is_ci_initialized():
            return False, "CI registry not initialized (.ci-registry directory missing)"

        # Check if required dependencies are available
        try:
            import importlib.util

            # Check chromadb availability
            if importlib.util.find_spec("chromadb") is None:
                return False, "Required dependency not available: chromadb"

            # Check semantic_duplicate_detector availability
            if (
                importlib.util.find_spec("shared.ci.core.semantic_duplicate_detector")
                is None
            ):
                return (
                    False,
                    "Required dependency not available: semantic_duplicate_detector",
                )

            # Check embedding_engine availability
            if importlib.util.find_spec("shared.ci.core.embedding_engine") is None:
                return False, "Required dependency not available: embedding_engine"

        except ImportError as e:
            return False, f"Required dependencies not available: {e}"

        return True, "Ready for indexing"

    def index_files(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Index specific files incrementally.

        Args:
            file_paths: List of file paths to index

        Returns:
            Dictionary with indexing results
        """
        can_index, reason = self.can_index()
        if not can_index:
            self.logger.warning(f"Indexing skipped: {reason}")
            return {"status": "skipped", "reason": reason, "files_processed": 0}

        self.logger.info(f"Starting incremental indexing of {len(file_paths)} files")

        try:
            # Filter to only include existing files
            existing_files = [f for f in file_paths if f.exists()]
            if len(existing_files) != len(file_paths):
                self.logger.warning(
                    f"{len(file_paths) - len(existing_files)} files not found, "
                    f"indexing {len(existing_files)} files"
                )

            if not existing_files:
                return {
                    "status": "success",
                    "reason": "No existing files to index",
                    "files_processed": 0,
                }

            # Use existing ChromaDB storage for indexing
            from shared.ci.core.chromadb_storage import ChromaDBStorage

            storage = ChromaDBStorage(project_root=self.project_root)

            # For each file, extract symbols and update index
            total_symbols = 0
            files_processed = 0

            for file_path in existing_files:
                try:
                    symbols = self._extract_file_symbols(file_path)
                    if symbols:
                        # Store symbols in ChromaDB
                        success = self._store_symbols_batch(storage, symbols)
                        if success:
                            total_symbols += len(symbols)
                            files_processed += 1
                            self.logger.info(
                                f"Indexed {file_path}: {len(symbols)} symbols"
                            )
                        else:
                            self.logger.warning(
                                f"Failed to store symbols for {file_path}"
                            )
                    else:
                        self.logger.info(f"No symbols found in {file_path}")
                        files_processed += 1  # Still count as processed

                except Exception as e:
                    self.logger.error(f"Error indexing {file_path}: {e}")
                    continue

            self.logger.info(
                f"Indexing complete: {files_processed} files, {total_symbols} symbols"
            )

            return {
                "status": "success",
                "files_processed": files_processed,
                "symbols_indexed": total_symbols,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Indexing failed: {e}")
            return {"status": "error", "error": str(e), "files_processed": 0}

    def incremental_index(self, changed_files: List[str]) -> Dict[str, Any]:
        """
        Run incremental indexing on changed files.

        Args:
            changed_files: List of file paths as strings

        Returns:
            Dictionary with indexing results
        """
        # Convert string paths to Path objects
        file_paths = [self.project_root / f for f in changed_files if f]

        # Filter to only include supported file types
        supported_files = self._filter_supported_files(file_paths)

        if not supported_files:
            self.logger.info("No supported files to index")
            return {
                "status": "success",
                "reason": "No supported files in change list",
                "files_processed": 0,
            }

        return self.index_files(supported_files)

    def full_index(self) -> Dict[str, Any]:
        """
        Run full codebase indexing.

        Returns:
            Dictionary with indexing results
        """
        can_index, reason = self.can_index()
        if not can_index:
            self.logger.warning(f"Full indexing skipped: {reason}")
            return {"status": "skipped", "reason": reason, "files_processed": 0}

        self.logger.info("Starting full codebase indexing")

        try:
            # Use existing ChromaDB storage run_full_scan method
            from shared.ci.core.chromadb_storage import ChromaDBStorage

            storage = ChromaDBStorage(project_root=self.project_root)
            success = storage.run_full_scan()

            if success:
                self.logger.info("Full indexing completed successfully")
                return {
                    "status": "success",
                    "reason": "Full scan completed",
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                self.logger.error("Full indexing failed")
                return {
                    "status": "error",
                    "error": "Full scan failed - see logs for details",
                }

        except Exception as e:
            self.logger.error(f"Full indexing error: {e}")
            return {"status": "error", "error": str(e)}

    def _extract_file_symbols(self, file_path: Path) -> List[Any]:
        """Extract symbols from a single file."""
        try:
            # Import and use the existing symbol extraction logic
            from shared.ci.core.semantic_duplicate_detector import DuplicateFinder
            from shared.ci.core.semantic_duplicate_detector import DuplicateFinderConfig

            # Create a minimal config for single file extraction
            config = DuplicateFinderConfig()
            finder = DuplicateFinder(
                config, self.project_root, test_mode=self.test_mode
            )

            # Extract symbols from the single file
            symbols = finder._extract_file_symbols(file_path)

            return symbols

        except Exception as e:
            self.logger.error(f"Symbol extraction failed for {file_path}: {e}")
            return []

    def _store_symbols_batch(self, storage, symbols: List[Any]) -> bool:
        """Store a batch of symbols using ChromaDB storage."""
        try:
            if not symbols:
                return True

            # Import and initialize EmbeddingEngine (matches run_full_scan flow)
            from shared.ci.core.embedding_engine import EmbeddingEngine

            embedding_engine = EmbeddingEngine()

            # Generate embeddings for symbols
            embeddings = embedding_engine.generate_embeddings(symbols)

            if embeddings is None or len(embeddings) != len(symbols):
                self.logger.error("Failed to generate embeddings for symbol batch")
                return False

            # Store symbols and embeddings in ChromaDB
            success = storage.store_symbols(symbols, embeddings)
            return success

        except Exception as e:
            self.logger.error(f"Failed to store symbol batch: {e}")
            return False

    def _filter_supported_files(self, file_paths: List[Path]) -> List[Path]:
        """Filter file paths to only include supported file types."""
        supported_extensions = {
            ".py",
            ".pyx",  # Python
            ".js",
            ".jsx",
            ".ts",
            ".tsx",  # JavaScript/TypeScript
            ".java",  # Java
            ".cs",  # C#
            ".go",  # Go
            ".rs",  # Rust
            ".cpp",
            ".cc",
            ".cxx",
            ".c",
            ".hpp",
            ".h",  # C/C++
            ".rb",  # Ruby
            ".php",  # PHP
            ".swift",  # Swift
            ".kt",  # Kotlin
            ".scala",  # Scala
            ".clj",
            ".cljs",  # Clojure
        }

        supported_files = []
        for file_path in file_paths:
            if file_path.suffix.lower() in supported_extensions:
                supported_files.append(file_path)

        return supported_files

    def index_in_background(self, changed_files: List[str]) -> bool:
        """
        Start indexing in background process.

        Args:
            changed_files: List of changed file paths

        Returns:
            True if background process started successfully
        """
        try:
            import subprocess

            # Create command to run indexing
            script_path = Path(__file__)
            cmd = [
                sys.executable,
                str(script_path),
                "--project-root",
                str(self.project_root),
                "--incremental",
            ]

            # Add changed files as arguments
            if changed_files:
                cmd.extend(["--files"] + changed_files)

            # Start background process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent process
            )

            self.logger.info(
                f"Started background indexing process (PID: {process.pid})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to start background indexing: {e}")
            return False


def main():
    """Command-line interface for ChromaDB indexer."""
    import argparse

    parser = argparse.ArgumentParser(description="ChromaDB Indexer")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--full", action="store_true", help="Run full indexing")
    parser.add_argument(
        "--incremental", action="store_true", help="Run incremental indexing"
    )
    parser.add_argument("--files", nargs="*", help="Files to index (for incremental)")
    parser.add_argument("--test", action="store_true", help="Run in test mode")

    args = parser.parse_args()

    indexer = ChromaDBIndexer(args.project_root, test_mode=args.test)

    if args.full:
        result = indexer.full_index()
    elif args.incremental:
        files = args.files or []
        result = indexer.incremental_index(files)
    else:
        print("Please specify --full or --incremental")
        sys.exit(1)

    # Output result as JSON
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
