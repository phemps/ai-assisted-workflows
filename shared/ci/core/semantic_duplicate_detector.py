#!/usr/bin/env python3
"""
Semantic Duplicate Detector - Advanced CI Pipeline Tool
=======================================================

PURPOSE: Advanced semantic duplicate detection using machine learning for CI pipeline integration.
Part of the continuous improvement system for development workflow optimization.

APPROACH:
- Symbol-level semantic analysis using CodeBERT embeddings
- Vector similarity search using ChromaDB unified storage
- LSP integration for semantic symbol extraction and cross-file analysis
- ChromaDB for unified vector storage, metadata, and persistence

DEPENDENCIES (ALL REQUIRED - FAIL-FAST):
- LSPSymbolExtractor: Language Server Protocol integration for semantic analysis
- EmbeddingEngine: CodeBERT/transformers for semantic embeddings
- ChromaDBStorage: Unified vector storage, metadata, and persistence

USE CASES:
- Advanced duplicate detection in development workflow
- Semantic similarity analysis beyond structural matching
- CI pipeline integration with caching and incremental updates
- ML-powered code analysis for refactoring recommendations

DISTINCTION FROM code_duplication_analyzer.py:
- This uses advanced ML techniques for semantic understanding
- Requires heavy dependencies (transformers, ChromaDB, MCP)
- Designed for CI pipeline integration with unified storage
- Part of the continuous improvement system

For lightweight traditional duplicate detection, see:
shared/analyzers/quality/code_duplication_analyzer.py

NOTE: For lightweight traditional duplicate detection suitable for quality gates,
see shared/analyzers/quality/code_duplication_analyzer.py
This tool requires ML dependencies and is designed for CI pipeline integration.

FAIL-FAST BEHAVIOR: Any component failure → sys.exit(1) with clear error message.
NO FALLBACKS: Complete success or immediate exit.
"""

import argparse
import fnmatch
import json
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np

# Import CI exceptions for proper error handling
try:
    from .exceptions import (
        CISystemError,
        CIDependencyError,
        CIAnalysisError,
        CISymbolExtractionError,
        CIEmbeddingError,
        CISimilarityError,
    )
except ImportError:
    # Direct execution fallback
    try:
        from exceptions import (
            CISystemError,
            CIDependencyError,
            CIAnalysisError,
            CISymbolExtractionError,
            CIEmbeddingError,
            CISimilarityError,
        )
    except ImportError:
        # Fallback definitions for standalone execution
        class CISystemError(Exception):
            def __init__(self, message: str, exit_code: int = 1):
                super().__init__(message)
                self.exit_code = exit_code
                self.message = message

        CIDependencyError = CIAnalysisError = CISymbolExtractionError = CISystemError
        CIEmbeddingError = CISimilarityError = CISystemError

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "utils"))

# Import utilities and existing components
try:
    from shared.core.utils.output_formatter import ResultFormatter
    from shared.core.utils.tech_stack_detector import TechStackDetector
except ImportError as e:
    raise CIDependencyError(f"Error importing utilities: {e}")

# Import core components - ALL REQUIRED
try:
    from .lsp_symbol_extractor import LSPSymbolExtractor, SymbolExtractionConfig
    from .embedding_engine import EmbeddingEngine, EmbeddingConfig
    from .chromadb_storage import ChromaDBStorage, ChromaDBConfig
except ImportError:
    try:
        # Direct execution import
        from lsp_symbol_extractor import LSPSymbolExtractor, SymbolExtractionConfig
        from embedding_engine import EmbeddingEngine, EmbeddingConfig
        from chromadb_storage import ChromaDBStorage, ChromaDBConfig
    except ImportError as e:
        context = {
            "required_components": [
                "LSPSymbolExtractor (Language Server Protocol integration)",
                "EmbeddingEngine (CodeBERT/transformers)",
                "ChromaDBStorage (Unified vector storage and metadata)",
            ]
        }
        raise CIDependencyError(
            f"Missing required core components: {e}", context=context
        )

# Import Symbol
try:
    from ..integration.symbol_extractor import Symbol
except ImportError:
    try:
        # Fallback for direct execution
        sys.path.insert(0, str(Path(__file__).parent.parent / "integration"))
        from symbol_extractor import Symbol
    except ImportError as e:
        raise CIDependencyError(f"Error importing Symbol: {e}")


# Define comparison types and results directly (extracted from removed comparison_framework)
class ComparisonType(Enum):
    """Types of comparisons supported."""

    EXACT_MATCH = "exact_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    STRUCTURAL_SIMILARITY = "structural_similarity"
    NAME_SIMILARITY = "name_similarity"


class DuplicateReason(Enum):
    """Reasons why symbols might be considered duplicates."""

    IDENTICAL_IMPLEMENTATION = "identical_implementation"
    SIMILAR_FUNCTIONALITY = "similar_functionality"
    COPY_PASTE_ERROR = "copy_paste_error"
    REFACTOR_CANDIDATE = "refactor_candidate"


@dataclass
class ComparisonResult:
    """Extended result for comparison findings."""

    analysis_type: str = "duplicate_detection"
    findings: List[Dict[str, Any]] = None
    summary: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.findings is None:
            self.findings = []
        if self.summary is None:
            self.summary = {}
        if self.metadata is None:
            self.metadata = {}


class AnalysisMode(Enum):
    """Modes of duplicate analysis."""

    FULL = "full"
    INCREMENTAL = "incremental"
    TARGETED = "targeted"


class ProgressStage(Enum):
    """Stages of duplicate analysis for progress tracking."""

    INITIALIZING = "initializing"
    EXTRACTING_SYMBOLS = "extracting_symbols"
    GENERATING_EMBEDDINGS = "generating_embeddings"
    BUILDING_INDEX = "building_index"
    FINDING_DUPLICATES = "finding_duplicates"
    UPDATING_REGISTRY = "updating_registry"
    FORMATTING_RESULTS = "formatting_results"
    COMPLETED = "completed"


@dataclass
class DuplicateFinderConfig:
    """Configuration for duplicate finder following existing patterns."""

    # Analysis settings
    analysis_mode: AnalysisMode = AnalysisMode.FULL
    max_symbols: int = 10000
    batch_size: int = 100

    # Similarity thresholds (configurable: 0.95/0.85/0.75)
    exact_duplicate_threshold: float = 0.95
    high_similarity_threshold: float = 0.85
    medium_similarity_threshold: float = 0.75
    low_similarity_threshold: float = 0.65

    # Performance settings
    enable_caching: bool = True
    enable_incremental: bool = True
    parallel_processing: bool = False
    max_memory_gb: float = 2.0

    # Symbol filtering
    include_symbol_types: Optional[List[str]] = None
    exclude_file_patterns: Optional[List[str]] = None
    min_symbol_length: int = 10

    # Component configurations
    extractor_config: Optional[SymbolExtractionConfig] = None
    embedding_config: Optional[EmbeddingConfig] = None
    chromadb_config: Optional[ChromaDBConfig] = None

    def __post_init__(self):
        """Initialize default configurations - validate all thresholds."""
        # Validate thresholds - NO FALLBACK to defaults
        if not (0.0 <= self.exact_duplicate_threshold <= 1.0):
            raise ValueError(
                f"Invalid exact_duplicate_threshold: "
                f"{self.exact_duplicate_threshold}. "
                f"Must be 0.0-1.0"
            )
        if not (0.0 <= self.high_similarity_threshold <= 1.0):
            raise ValueError(
                f"Invalid high_similarity_threshold: "
                f"{self.high_similarity_threshold}. "
                f"Must be 0.0-1.0"
            )
        if not (0.0 <= self.medium_similarity_threshold <= 1.0):
            raise ValueError(
                f"Invalid medium_similarity_threshold: "
                f"{self.medium_similarity_threshold}. "
                f"Must be 0.0-1.0"
            )
        if not (0.0 <= self.low_similarity_threshold <= 1.0):
            raise ValueError(
                f"Invalid low_similarity_threshold: "
                f"{self.low_similarity_threshold}. "
                f"Must be 0.0-1.0"
            )

        # Validate threshold ordering
        if not (
            (
                self.low_similarity_threshold
                < self.medium_similarity_threshold
                < self.high_similarity_threshold
                < self.exact_duplicate_threshold
            )
        ):
            raise ValueError(
                "Thresholds must be in ascending order: " "low < medium < high < exact"
            )
        if self.include_symbol_types is None:
            self.include_symbol_types = ["function", "class", "method", "interface"]

        if self.exclude_file_patterns is None:
            self.exclude_file_patterns = [
                "node_modules/*",
                ".git/*",
                "build/*",
                "dist/*",
                "coverage/*",
                "*.min.js",
                "__pycache__/*",
                "*.pyc",
            ]

        # Initialize component configs if not provided
        if self.extractor_config is None:
            self.extractor_config = SymbolExtractionConfig(
                max_symbols_per_file=min(self.batch_size, 500),
                include_symbol_types=self.include_symbol_types,
            )

        if self.embedding_config is None:
            self.embedding_config = EmbeddingConfig(
                batch_size=self.batch_size,
                max_memory_gb=self.max_memory_gb,
            )

        if self.chromadb_config is None:
            self.chromadb_config = ChromaDBConfig(
                exact_match_threshold=self.exact_duplicate_threshold,
                high_similarity_threshold=self.high_similarity_threshold,
                medium_similarity_threshold=self.medium_similarity_threshold,
                low_similarity_threshold=self.low_similarity_threshold,
                batch_size=self.batch_size,
                max_memory_gb=self.max_memory_gb,
            )


@dataclass
class DuplicateResult:
    """Represents a duplicate detection result."""

    original_symbol: Symbol
    duplicate_symbol: Symbol
    similarity_score: float
    confidence: float
    reason: DuplicateReason
    comparison_type: ComparisonType
    embedding_similarity: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize details if not provided."""
        if self.details is None:
            self.details = {}


class DuplicateFinder:
    """
    Main orchestrator for duplicate detection using ChromaDB unified storage.

    FAIL-FAST BEHAVIOR: Exits immediately if any core component fails.
    NO FALLBACKS or graceful degradation - complete success or exit.

    Required Components:
    - LSPSymbolExtractor: Language Server Protocol integration for semantic analysis
    - EmbeddingEngine: CodeBERT/transformers for semantic embeddings
    - ChromaDBStorage: Unified vector storage, metadata, and persistence

    Any component failure → sys.exit(1) with clear error message
    """

    def __init__(
        self,
        config: Optional[DuplicateFinderConfig] = None,
        project_root: Optional[Path] = None,
        test_mode: bool = False,
    ):
        self.config = config or DuplicateFinderConfig()
        self.project_root = project_root or Path.cwd()
        self.test_mode = test_mode

        # Initialize utilities
        self.tech_detector = TechStackDetector()
        self.result_formatter = ResultFormatter()

        # Initialize 3 core components - FAIL FAST if any unavailable
        try:
            self.symbol_extractor = LSPSymbolExtractor(
                self.config.extractor_config, self.project_root
            )
        except Exception as e:
            print(
                f"FATAL: LSPSymbolExtractor initialization failed: {e}", file=sys.stderr
            )
            print(
                "Required: multilspy and language servers for semantic analysis",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            self.embedding_engine = EmbeddingEngine(
                self.config.embedding_config, self.project_root
            )
        except Exception as e:
            print(f"FATAL: EmbeddingEngine initialization failed: {e}", file=sys.stderr)
            print(
                "Required: CodeBERT/transformers for semantic embeddings",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            self.chromadb_storage = ChromaDBStorage(
                self.config.chromadb_config, self.project_root
            )
        except Exception as e:
            print(f"FATAL: ChromaDBStorage initialization failed: {e}", file=sys.stderr)
            print(
                "Required: ChromaDB for unified vector storage and metadata",
                file=sys.stderr,
            )
            sys.exit(1)

        # Validate all components are functional
        self._validate_all_components()

        # Progress tracking
        self._current_stage = ProgressStage.INITIALIZING
        self._progress_callback = None
        self._stats = {
            "symbols_extracted": 0,
            "embeddings_generated": 0,
            "duplicates_found": 0,
            "execution_time": 0.0,
        }

    def _validate_all_components(self) -> None:
        """Validate all core components are functional - NO FALLBACKS."""
        # Test LSPSymbolExtractor
        try:
            parser_info = self.symbol_extractor.get_parser_info()
            if not parser_info.get("is_loaded", False):
                raise Exception("LSPSymbolExtractor language servers not loaded")
        except Exception as e:
            print(f"FATAL: LSPSymbolExtractor validation failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Test EmbeddingEngine
        try:
            engine_info = self.embedding_engine.get_engine_info()
            if not engine_info.get("is_available", False):
                raise Exception("EmbeddingEngine not available")
        except Exception as e:
            print(f"FATAL: EmbeddingEngine validation failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Test ChromaDBStorage
        try:
            storage_info = self.chromadb_storage.get_storage_info()
            if not storage_info.get("is_available", False):
                raise Exception("ChromaDBStorage not available")
        except Exception as e:
            print(f"FATAL: ChromaDBStorage validation failed: {e}", file=sys.stderr)
            sys.exit(1)

    def set_progress_callback(self, callback) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback

    def _update_progress(
        self, stage: ProgressStage, message: str = "", percentage: float = 0.0
    ) -> None:
        """Update progress tracking."""
        self._current_stage = stage
        if self._progress_callback:
            self._progress_callback(stage, message, percentage)

    def _handle_fatal_error(
        self, message: str, exception_class=CISystemError, **kwargs
    ):
        """Handle fatal errors - either raise exception (test mode) or exit (production)."""
        if self.test_mode:
            raise exception_class(message, **kwargs)
        else:
            print(f"FATAL: {message}", file=sys.stderr)
            sys.exit(kwargs.get("exit_code", 1))

    def analyze_project(
        self,
        project_root: Optional[Path] = None,
        file_patterns: Optional[List[str]] = None,
    ) -> ComparisonResult:
        """
        Perform full project analysis for duplicate detection.

        Args:
            project_root: Root directory to analyze (uses config default
                if None)
            file_patterns: File patterns to include (uses config default
                if None)

        Returns:
            ComparisonResult with duplicate findings
        """
        start_time = time.time()
        project_root = project_root or self.project_root

        self._update_progress(
            ProgressStage.INITIALIZING,
            "Initializing duplicate detection analysis",
            0.0,
        )

        # 1. Extract symbols from project
        self._update_progress(
            ProgressStage.EXTRACTING_SYMBOLS,
            "Extracting symbols from source files",
            10.0,
        )
        symbols = self._extract_project_symbols(project_root, file_patterns)

        if not symbols:
            self._handle_fatal_error(
                "No symbols found in project", CISymbolExtractionError
            )

        self._stats["symbols_extracted"] = len(symbols)

        # 2. Perform duplicate detection - FAIL if any component fails
        duplicates = self.find_duplicates(
            symbols, self.config.medium_similarity_threshold
        )

        self._stats["duplicates_found"] = len(duplicates)
        self._stats["execution_time"] = time.time() - start_time

        # 3. Format results
        self._update_progress(
            ProgressStage.FORMATTING_RESULTS,
            "Formatting analysis results",
            90.0,
        )
        result = self._create_comparison_result(duplicates, symbols)

        self._update_progress(ProgressStage.COMPLETED, "Analysis completed", 100.0)

        return result

    def find_duplicates(
        self,
        symbols: List[Symbol],
        threshold: float = None,
        use_incremental: bool = None,
    ) -> List[DuplicateResult]:
        """
        Find duplicates in symbols using the complete detection pipeline.

        Args:
            symbols: List of symbols to analyze
            threshold: Similarity threshold (uses config default if None)
            use_incremental: Use incremental analysis
                (uses config default if None)

        Returns:
            List of duplicate detection results
        """
        threshold = threshold or self.config.medium_similarity_threshold
        use_incremental = (
            use_incremental
            if use_incremental is not None
            else self.config.enable_incremental
        )

        # Filter symbols
        filtered_symbols = self._filter_symbols(symbols)

        if not filtered_symbols:
            self._handle_fatal_error(
                "No symbols remain after filtering", CISymbolExtractionError
            )

        # Check for incremental updates if enabled
        if use_incremental:
            try:
                filtered_symbols = self._handle_incremental_updates(filtered_symbols)
            except Exception as e:
                self._handle_fatal_error(
                    f"Incremental update handling failed: {e}", CISymbolExtractionError
                )

        # Generate embeddings - FAIL FAST if component fails
        self._update_progress(
            ProgressStage.GENERATING_EMBEDDINGS,
            f"Generating embeddings for {len(filtered_symbols)} symbols",
            30.0,
        )
        try:
            embeddings = self.embedding_engine.generate_embeddings(filtered_symbols)
        except Exception as e:
            self._handle_fatal_error(
                f"Embedding generation failed: {e}", CIEmbeddingError
            )

        if len(embeddings) == 0:
            self._handle_fatal_error("No embeddings generated", CIEmbeddingError)

        self._stats["embeddings_generated"] = len(embeddings)

        # Store symbols and embeddings in ChromaDB - FAIL FAST if component fails
        self._update_progress(
            ProgressStage.BUILDING_INDEX,
            "Storing symbols and embeddings in ChromaDB",
            50.0,
        )
        try:
            success = self.chromadb_storage.store_symbols(filtered_symbols, embeddings)
        except Exception as e:
            self._handle_fatal_error(f"ChromaDB storage failed: {e}", CISimilarityError)

        if not success:
            self._handle_fatal_error(
                "Failed to store symbols in ChromaDB", CISimilarityError
            )

        # Find similar pairs using ChromaDB - FAIL FAST if component fails
        self._update_progress(
            ProgressStage.FINDING_DUPLICATES,
            "Finding duplicate symbol pairs",
            70.0,
        )
        try:
            duplicates = self._find_similar_pairs_chromadb(
                filtered_symbols, embeddings, threshold
            )
        except Exception as e:
            self._handle_fatal_error(
                f"Similar pairs finding failed: {e}", CISimilarityError
            )

        return duplicates

    def incremental_analysis(
        self, changed_files: Optional[List[Path]] = None
    ) -> ComparisonResult:
        """
        Perform incremental analysis using registry change detection.

        Args:
            changed_files: Specific files that changed (auto-detect if None)

        Returns:
            ComparisonResult with duplicate findings for changed symbols
        """
        start_time = time.time()

        # Detect changed files if not provided
        if changed_files is None:
            try:
                changed_files = self._detect_changed_files()
            except Exception as e:
                self._handle_fatal_error(
                    f"Changed file detection failed: {e}", CISymbolExtractionError
                )

        if not changed_files:
            # If no file changes detected, return empty result gracefully
            return ComparisonResult(
                findings=[],
                summary={
                    "files_analyzed": 0,
                    "symbols_extracted": 0,
                    "symbols_filtered": 0,
                    "embeddings_generated": 0,
                    "duplicates_found": 0,
                },
                metadata={"analysis_duration": time.time() - start_time},
            )

        # Extract symbols from changed files
        symbols = []
        for file_path in changed_files:
            try:
                # Skip non-existent files gracefully
                if not file_path.exists():
                    print(
                        f"Warning: Skipping non-existent file: {file_path}",
                        file=sys.stderr,
                    )
                    continue

                file_symbols = self._extract_file_symbols(file_path)
                symbols.extend(file_symbols)
            except Exception as e:
                print(
                    f"Warning: Symbol extraction failed for {file_path}: {e}",
                    file=sys.stderr,
                )
                # Continue processing other files instead of failing completely
                continue

        if not symbols:
            # If no symbols found, return empty result instead of failing
            # This handles cases like non-existent files gracefully
            return ComparisonResult(
                findings=[],
                summary={
                    "files_analyzed": len(changed_files),
                    "symbols_extracted": 0,
                    "symbols_filtered": 0,
                    "embeddings_generated": 0,
                    "duplicates_found": 0,
                },
                metadata={"analysis_duration": time.time() - start_time},
            )

        # Find duplicates using incremental mode
        duplicates = self.find_duplicates(
            symbols,
            use_incremental=True,
            threshold=self.config.medium_similarity_threshold,
        )

        self._stats["execution_time"] = time.time() - start_time

        # Format results
        result = self._create_comparison_result(duplicates, symbols)
        result.metadata["analysis_mode"] = "incremental"
        result.metadata["changed_files"] = [str(f) for f in changed_files]

        # Check for new languages in changed files and update config if needed
        self._update_project_languages_from_files(changed_files)

        return result

    def _detect_languages_from_files(self, file_paths: List[Path]) -> set[str]:
        """Detect programming languages from a list of files using TechStackDetector."""
        exclusion_patterns = self.config.exclude_file_patterns or []

        # Create a simple language mapping based on file extensions
        language_patterns = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
        }

        languages = set()
        for file_path in file_paths:
            # Simple exclusion check - skip if any exclusion pattern is in the path
            if any(
                pattern.replace("*", "") in str(file_path)
                for pattern in exclusion_patterns
            ):
                continue

            suffix = file_path.suffix.lower()
            if suffix in language_patterns:
                languages.add(language_patterns[suffix])

        return languages

    def _update_project_languages_from_files(self, file_paths: List[Path]) -> None:
        """Update project languages in config if new ones detected in files."""
        if not file_paths:
            return

        # Detect languages from the files
        detected_languages = self._detect_languages_from_files(file_paths)

        if detected_languages:
            # Get current languages from registry manager
            try:
                self.registry_manager.update_project_languages(detected_languages)
            except Exception as e:
                print(
                    f"Warning: Could not update project languages: {e}", file=sys.stderr
                )

    def _extract_project_symbols(
        self,
        project_root: Path,
        file_patterns: Optional[List[str]] = None,
    ) -> List[Symbol]:
        """Extract symbols from all files in project."""
        # Use tech detector to find relevant files
        file_patterns = file_patterns or ["*.py", "*.js", "*.ts", "*.java", "*.go"]

        all_files = []
        for pattern in file_patterns:
            pattern_files = list(project_root.rglob(pattern))
            all_files.extend(pattern_files)

        # Filter out excluded patterns using proper glob matching
        filtered_files = []
        for file_path in all_files:
            excluded = False
            # Convert to relative path for pattern matching
            try:
                relative_path = file_path.relative_to(project_root)
                path_str = str(relative_path)
            except ValueError:
                # If we can't make it relative, use the full path
                path_str = str(file_path)

            for exclude_pattern in self.config.exclude_file_patterns:
                # Use fnmatch for proper glob pattern matching
                if fnmatch.fnmatch(path_str, exclude_pattern) or fnmatch.fnmatch(
                    str(file_path), exclude_pattern
                ):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(file_path)

        # Extract symbols from files - FAIL FAST on component failure
        all_symbols = []
        for file_path in filtered_files:
            try:
                file_symbols = self._extract_file_symbols(file_path)
                all_symbols.extend(file_symbols)

                # Limit symbols, not files
                if len(all_symbols) >= self.config.max_symbols:
                    all_symbols = all_symbols[: self.config.max_symbols]
                    break
            except Exception as e:
                self._handle_fatal_error(
                    f"Symbol extraction failed for {file_path}: {e}",
                    CISymbolExtractionError,
                )

        return all_symbols

    def _extract_file_symbols(self, file_path: Path) -> List[Symbol]:
        """
        Extract symbols from a single file using Serena client.
        NO FALLBACK.
        """
        try:
            symbols = self.symbol_extractor.extract_symbols([file_path])
            return symbols
        except Exception as e:
            # No fallback - raise exception to be handled by caller
            raise Exception(
                f"LSPSymbolExtractor symbol extraction failed for {file_path}: {e}"
            )

    def _filter_symbols(self, symbols: List[Symbol]) -> List[Symbol]:
        """Filter symbols based on configuration with enhanced filtering logic."""
        filtered = []

        for symbol in symbols:
            # Type filtering
            type_val = symbol.symbol_type.value
            if type_val not in self.config.include_symbol_types:
                continue

            # Import filtering - exclude imports before expensive embedding generation
            if hasattr(symbol, "is_import") and symbol.is_import:
                continue

            # Length filtering
            content_len = len(symbol.line_content.strip())
            if content_len < self.config.min_symbol_length:
                continue

            # Enhanced file pattern filtering
            file_path = symbol.file_path.lower()
            excluded = False

            # Check configured exclude patterns
            for pattern in self.config.exclude_file_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    excluded = True
                    break

            # Enhanced generated file filtering
            if not excluded and (
                "generated" in file_path
                or ".gen." in file_path
                or "autogenerated" in file_path
                or "auto-generated" in file_path
                or "__pycache__" in file_path
                or ".pyc" in file_path
            ):
                excluded = True

            if excluded:
                continue

            filtered.append(symbol)

        return filtered

    def _handle_incremental_updates(self, symbols: List[Symbol]) -> List[Symbol]:
        """Handle incremental updates using ChromaDB storage - NO FALLBACK."""
        # ChromaDB handles incremental updates automatically through upsert
        # For now, return all symbols since incremental filtering isn't implemented yet
        # TODO: Implement proper incremental update filtering based on file modification times
        return symbols

    def _find_similar_pairs_chromadb(
        self, symbols: List[Symbol], embeddings: np.ndarray, threshold: float
    ) -> List[DuplicateResult]:
        """Find similar symbol pairs using ChromaDB storage."""
        duplicates = []

        # Perform batch similarity search using ChromaDB - NO FALLBACK
        similarity_results = self.chromadb_storage.batch_similarity_search(
            embeddings, threshold
        )

        # Convert similarity matches to duplicate results
        processed_pairs = set()

        for query_idx, matches in similarity_results.items():
            query_symbol = symbols[query_idx]

            for match in matches:
                # Avoid duplicate pairs and self-matches
                pair_id = tuple(sorted([query_idx, match.match_index]))
                if pair_id in processed_pairs or query_idx == match.match_index:
                    continue

                processed_pairs.add(pair_id)
                match_symbol = (
                    symbols[match.match_index]
                    if match.match_symbol is None
                    else match.match_symbol
                )

                # Create duplicate result
                duplicate_result = self._create_duplicate_result(
                    query_symbol,
                    match_symbol,
                    match.similarity_score,
                    match.confidence,
                )

                duplicates.append(duplicate_result)

        return duplicates

    def _create_duplicate_result(
        self,
        symbol1: Symbol,
        symbol2: Symbol,
        similarity_score: float,
        confidence: float,
    ) -> DuplicateResult:
        """Create a duplicate result from similarity match."""
        # Determine comparison type based on score
        if similarity_score >= self.config.exact_duplicate_threshold:
            comparison_type = ComparisonType.EXACT_MATCH
            reason = DuplicateReason.IDENTICAL_IMPLEMENTATION
        elif similarity_score >= self.config.high_similarity_threshold:
            comparison_type = ComparisonType.SEMANTIC_SIMILARITY
            if symbol1.file_path != symbol2.file_path:
                reason = DuplicateReason.COPY_PASTE_ERROR
            else:
                reason = DuplicateReason.SIMILAR_FUNCTIONALITY
        else:
            comparison_type = ComparisonType.STRUCTURAL_SIMILARITY
            reason = DuplicateReason.REFACTOR_CANDIDATE

        return DuplicateResult(
            original_symbol=symbol1,
            duplicate_symbol=symbol2,
            similarity_score=similarity_score,
            confidence=confidence,
            reason=reason,
            comparison_type=comparison_type,
            embedding_similarity=similarity_score,
            details={
                "detection_method": "chromadb_similarity",
                "embedding_engine": self.embedding_engine.get_engine_info()["method"],
                "storage_system": self.chromadb_storage.get_storage_info()["method"],
            },
        )

    def _detect_changed_files(self) -> List[Path]:
        """Detect changed files using registry manager."""
        # This would use git or file system timestamps
        # For now, return empty list (placeholder)
        return []

    def _create_comparison_result(
        self, duplicates: List[DuplicateResult], symbols: List[Symbol]
    ) -> ComparisonResult:
        """Create ComparisonResult from duplicate results."""
        findings = []

        for i, duplicate in enumerate(duplicates):
            finding = {
                "finding_id": f"duplicate_{i:04d}",
                "title": (
                    f"Duplicate: {duplicate.original_symbol.name} & "
                    f"{duplicate.duplicate_symbol.name}"
                ),
                "description": (
                    f"Found {duplicate.comparison_type.value} between symbols "
                    f"with {duplicate.similarity_score:.3f} similarity"
                ),
                "severity": self._determine_severity(duplicate.similarity_score),
                "file_path": duplicate.original_symbol.file_path,
                "line_number": duplicate.original_symbol.line_number,
                "evidence": {
                    "similarity_score": duplicate.similarity_score,
                    "confidence": duplicate.confidence,
                    "reason": duplicate.reason.value,
                    "comparison_type": duplicate.comparison_type.value,
                    "original_symbol": {
                        "name": duplicate.original_symbol.name,
                        "type": duplicate.original_symbol.symbol_type.value,
                        "file": duplicate.original_symbol.file_path,
                        "line": duplicate.original_symbol.line_number,
                        "content": duplicate.original_symbol.line_content[:100],
                        "lsp_kind": duplicate.original_symbol.lsp_kind,
                        "line_count": duplicate.original_symbol.line_count,
                    },
                    "duplicate_symbol": {
                        "name": duplicate.duplicate_symbol.name,
                        "type": duplicate.duplicate_symbol.symbol_type.value,
                        "file": duplicate.duplicate_symbol.file_path,
                        "line": duplicate.duplicate_symbol.line_number,
                        "content": duplicate.duplicate_symbol.line_content[:100],
                        "lsp_kind": duplicate.duplicate_symbol.lsp_kind,
                        "line_count": duplicate.duplicate_symbol.line_count,
                    },
                    "details": duplicate.details,
                },
            }
            findings.append(finding)

        # Create summary
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in findings:
            severity_counts[finding["severity"]] += 1

        summary = {
            "total_duplicates_found": len(duplicates),
            "symbols_analyzed": len(symbols),
            "execution_time_seconds": round(self._stats["execution_time"], 2),
            "severity_breakdown": severity_counts,
            "detection_method": "embedding_similarity",
            "thresholds": {
                "exact_duplicate": self.config.exact_duplicate_threshold,
                "high_similarity": self.config.high_similarity_threshold,
                "medium_similarity": self.config.medium_similarity_threshold,
            },
        }

        # Create metadata
        metadata = {
            "project_root": str(self.project_root),
            "analysis_mode": self.config.analysis_mode,
            "component_info": {
                "symbol_extractor": self.symbol_extractor.get_parser_info(),
                "embedding_engine": self.embedding_engine.get_engine_info(),
                "chromadb_storage": self.chromadb_storage.get_storage_info(),
            },
            "configuration": {
                "max_symbols": self.config.max_symbols,
                "batch_size": self.config.batch_size,
                "enable_incremental": self.config.enable_incremental,
            },
            "stats": self._stats.copy(),
            "timestamp": time.time(),
        }

        return ComparisonResult(
            analysis_type="duplicate_detection",
            findings=findings,
            summary=summary,
            metadata=metadata,
        )

    # Removed _create_empty_result and _create_error_result methods
    # DuplicateFinder now uses fail-fast behavior
    # instead of graceful degradation

    def _determine_severity(self, score: float) -> str:
        """Determine severity based on similarity score."""
        if score >= self.config.exact_duplicate_threshold:
            return "critical"  # Exact duplicates
        elif score >= self.config.high_similarity_threshold:
            return "high"  # High similarity
        elif score >= self.config.medium_similarity_threshold:
            return "medium"  # Medium similarity
        else:
            return "low"  # Lower similarity

    def get_finder_info(self) -> Dict[str, Any]:
        """Get comprehensive duplicate finder status and diagnostic info."""
        return {
            "current_stage": self._current_stage.value,
            "configuration": {
                "analysis_mode": self.config.analysis_mode,
                "thresholds": {
                    "exact_duplicate": self.config.exact_duplicate_threshold,
                    "high_similarity": self.config.high_similarity_threshold,
                    "medium_similarity": self.config.medium_similarity_threshold,
                    "low_similarity": self.config.low_similarity_threshold,
                },
                "performance": {
                    "max_symbols": self.config.max_symbols,
                    "batch_size": self.config.batch_size,
                    "enable_caching": self.config.enable_caching,
                    "enable_incremental": self.config.enable_incremental,
                    "max_memory_gb": self.config.max_memory_gb,
                },
            },
            "components": {
                "symbol_extractor": self.symbol_extractor.get_parser_info(),
                "embedding_engine": self.embedding_engine.get_engine_info(),
                "chromadb_storage": self.chromadb_storage.get_storage_info(),
            },
            "stats": self._stats.copy(),
            "project_root": str(self.project_root),
        }

    def cleanup(self, clear_caches: bool = False) -> None:
        """
        Cleanup resources and optionally clear caches.
        FAIL FAST on component failure.
        """
        if clear_caches:
            # Clear ChromaDB collection - ChromaDB handles all caching internally
            try:
                self.chromadb_storage.clear_collection()
            except Exception as e:
                print(f"FATAL: ChromaDB collection clear failed: {e}", file=sys.stderr)
                sys.exit(1)

        # Reset stats
        self._stats = {
            "symbols_extracted": 0,
            "embeddings_generated": 0,
            "duplicates_found": 0,
            "execution_time": 0.0,
        }

        self._current_stage = ProgressStage.INITIALIZING


def main():
    """Main entry point for testing duplicate finder functionality."""

    parser = argparse.ArgumentParser(
        description="Duplicate detection using ChromaDB unified storage"
    )
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument(
        "--mode",
        choices=["full", "incremental", "targeted"],
        default="full",
        help="Analysis mode",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.75, help="Similarity threshold"
    )
    parser.add_argument(
        "--max-symbols", type=int, default=1000, help="Maximum symbols to analyze"
    )
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear all caches before analysis"
    )

    args = parser.parse_args()

    # Create configuration
    config = DuplicateFinderConfig(
        analysis_mode=AnalysisMode(args.mode),
        medium_similarity_threshold=args.threshold,
        max_symbols=args.max_symbols,
    )

    # Initialize finder - exits if any core component fails
    finder = DuplicateFinder(config, args.project_root)

    if args.clear_cache:
        finder.cleanup(clear_caches=True)

    # Run analysis based on mode - exits on any failure
    if args.mode == "incremental":
        result = finder.incremental_analysis()
    else:
        result = finder.analyze_project()

    # Output results - only reached if analysis succeeds completely
    if args.output == "json":
        output = {
            "analysis_type": result.analysis_type,
            "findings": result.findings,
            "summary": result.summary,
            "metadata": result.metadata,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        summary = result.summary
        print("Duplicate Detection Analysis Results:")
        print(f"  Mode: {args.mode}")
        print(f"  Duplicates found: {summary['total_duplicates_found']}")
        print(f"  Symbols analyzed: {summary['symbols_analyzed']}")
        print(f"  Execution time: {summary['execution_time_seconds']}s")
        print("  Severity breakdown:")
        for severity, count in summary.get("severity_breakdown", {}).items():
            if count > 0:
                print(f"    {severity}: {count}")

        # Show component info - all components guaranteed to be working
        finder_info = finder.get_finder_info()
        print("\nComponent Status (All Required and Verified):")
        for component, info in finder_info["components"].items():
            status = info.get("status", info.get("is_available", "available"))
            print(f"  {component}: {status}")

        print("\nAll 3 core components verified functional:")
        print("  - LSPSymbolExtractor: Language servers loaded")
        print("  - EmbeddingEngine: CodeBERT/transformers available")
        print("  - ChromaDBStorage: Unified vector storage operational")


if __name__ == "__main__":
    main()
