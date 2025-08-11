#!/usr/bin/env python3
"""
Duplicate Finder - Main Detection Logic for Continuous Improvement Framework

FAIL-FAST ORCHESTRATOR requiring ALL 4 core components:
- SerenaClient (MCP integration)
- EmbeddingEngine (CodeBERT/transformers)
- SimilarityDetector (Faiss indexing)
- RegistryManager (SQLite storage)

NO FALLBACKS: Any component failure → sys.exit(1) with clear error message.
NO GRACEFUL DEGRADATION: Complete success or immediate exit.
NO PARTIAL RESULTS: Either full analysis or termination.

Part of Claude Code Workflows - integrates with 8-agent orchestration system.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
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

# Import core components - ALL REQUIRED
try:
    from .serena_client import SerenaClient, MCPConfig
    from .embedding_engine import EmbeddingEngine, EmbeddingConfig
    from .similarity_detector import (
        SimilarityDetector,
        SimilarityConfig,
    )
    from .registry_manager import (
        RegistryManager,
        RegistryConfig,
    )
except ImportError:
    try:
        # Direct execution import
        from serena_client import SerenaClient, MCPConfig
        from embedding_engine import EmbeddingEngine, EmbeddingConfig
        from similarity_detector import (
            SimilarityDetector,
            SimilarityConfig,
        )
        from registry_manager import (
            RegistryManager,
            RegistryConfig,
        )
    except ImportError as e:
        print(f"FATAL: Missing required core components: {e}", file=sys.stderr)
        print("DuplicateFinder requires all 4 core components:", file=sys.stderr)
        print("  - SerenaClient (MCP integration)", file=sys.stderr)
        print("  - EmbeddingEngine (CodeBERT/transformers)", file=sys.stderr)
        print("  - SimilarityDetector (Faiss indexing)", file=sys.stderr)
        print("  - RegistryManager (SQLite storage)", file=sys.stderr)
        sys.exit(1)

# Import Symbol and comparison framework
try:
    from ..analyzers.symbol_extractor import Symbol
    from ..analyzers.comparison_framework import (
        ComparisonResult,
        ComparisonType,
        DuplicateReason,
    )
except ImportError:
    try:
        # Fallback for direct execution
        sys.path.insert(0, str(Path(__file__).parent.parent / "analyzers"))
        from symbol_extractor import Symbol
        from comparison_framework import (
            ComparisonResult,
            ComparisonType,
            DuplicateReason,
        )
    except ImportError as e:
        print(f"Error importing analyzers: {e}", file=sys.stderr)
        sys.exit(1)


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
    mcp_config: Optional[MCPConfig] = None
    embedding_config: Optional[EmbeddingConfig] = None
    similarity_config: Optional[SimilarityConfig] = None
    registry_config: Optional[RegistryConfig] = None

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
                "test_*",
                "*_test.py",
                "*/test/*",
                "*.spec.*",
                "node_modules/*",
                ".git/*",
            ]

        # Initialize component configs if not provided
        if self.mcp_config is None:
            self.mcp_config = MCPConfig(
                max_symbols_per_request=min(self.batch_size, 500),
                include_symbol_types=self.include_symbol_types,
            )

        if self.embedding_config is None:
            self.embedding_config = EmbeddingConfig(
                batch_size=self.batch_size,
                enable_caching=self.enable_caching,
                max_memory_gb=self.max_memory_gb,
            )

        if self.similarity_config is None:
            self.similarity_config = SimilarityConfig(
                exact_match_threshold=self.exact_duplicate_threshold,
                high_similarity_threshold=self.high_similarity_threshold,
                medium_similarity_threshold=self.medium_similarity_threshold,
                low_similarity_threshold=self.low_similarity_threshold,
                batch_size=self.batch_size,
                enable_caching=self.enable_caching,
            )

        if self.registry_config is None:
            self.registry_config = RegistryConfig(
                batch_size=self.batch_size,
                max_memory_gb=self.max_memory_gb,
                enable_indexing=True,
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
    Main orchestrator for duplicate detection using ALL 4 core components.

    FAIL-FAST BEHAVIOR: Exits immediately if any core component fails.
    NO FALLBACKS or graceful degradation - complete success or exit.

    Required Components:
    - SerenaClient: MCP integration for symbol extraction
    - EmbeddingEngine: CodeBERT/transformers for semantic embeddings
    - SimilarityDetector: Faiss indexing for similarity search
    - RegistryManager: SQLite storage for caching and registry

    Any component failure → sys.exit(1) with clear error message
    """

    def __init__(
        self,
        config: Optional[DuplicateFinderConfig] = None,
        project_root: Optional[Path] = None,
    ):
        self.config = config or DuplicateFinderConfig()
        self.project_root = project_root or Path.cwd()

        # Initialize utilities
        self.tech_detector = TechStackDetector()
        self.result_formatter = ResultFormatter()

        # Initialize ALL 4 core components - FAIL FAST if any unavailable
        try:
            self.serena_client = SerenaClient(self.config.mcp_config, self.project_root)
        except Exception as e:
            print(f"FATAL: SerenaClient initialization failed: {e}", file=sys.stderr)
            print(
                "Required: MCP server connection for symbol extraction", file=sys.stderr
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
            self.similarity_detector = SimilarityDetector(
                self.config.similarity_config, self.project_root
            )
        except Exception as e:
            print(
                f"FATAL: SimilarityDetector initialization failed: {e}", file=sys.stderr
            )
            print("Required: Faiss for similarity indexing and search", file=sys.stderr)
            sys.exit(1)

        try:
            self.registry_manager = RegistryManager(
                self.config.registry_config, self.project_root
            )
        except Exception as e:
            print(f"FATAL: RegistryManager initialization failed: {e}", file=sys.stderr)
            print("Required: SQLite for symbol registry and caching", file=sys.stderr)
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
        # Test SerenaClient
        try:
            serena_info = self.serena_client.get_connection_info()
            if not serena_info.get("is_connected", False):
                raise Exception("SerenaClient not connected to MCP server")
        except Exception as e:
            print(f"FATAL: SerenaClient validation failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Test EmbeddingEngine
        try:
            engine_info = self.embedding_engine.get_engine_info()
            if not engine_info.get("is_available", False):
                raise Exception("EmbeddingEngine not available")
        except Exception as e:
            print(f"FATAL: EmbeddingEngine validation failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Test SimilarityDetector
        try:
            detector_info = self.similarity_detector.get_detector_info()
            if not detector_info.get("is_available", False):
                raise Exception("SimilarityDetector not available")
        except Exception as e:
            print(f"FATAL: SimilarityDetector validation failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Test RegistryManager
        try:
            registry_stats = self.registry_manager.get_registry_stats()
            if not registry_stats.get("is_available", False):
                raise Exception("RegistryManager not available")
        except Exception as e:
            print(f"FATAL: RegistryManager validation failed: {e}", file=sys.stderr)
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
            print("FATAL: No symbols found in project", file=sys.stderr)
            sys.exit(1)

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
            print("FATAL: No symbols remain after filtering", file=sys.stderr)
            sys.exit(1)

        # Check for incremental updates if enabled
        if use_incremental:
            try:
                filtered_symbols = self._handle_incremental_updates(filtered_symbols)
            except Exception as e:
                print(
                    f"FATAL: Incremental update handling failed: {e}", file=sys.stderr
                )
                sys.exit(1)

        # Generate embeddings - FAIL FAST if component fails
        self._update_progress(
            ProgressStage.GENERATING_EMBEDDINGS,
            f"Generating embeddings for {len(filtered_symbols)} symbols",
            30.0,
        )
        try:
            embeddings = self.embedding_engine.generate_embeddings(filtered_symbols)
        except Exception as e:
            print(f"FATAL: Embedding generation failed: {e}", file=sys.stderr)
            sys.exit(1)

        if len(embeddings) == 0:
            print("FATAL: No embeddings generated", file=sys.stderr)
            sys.exit(1)

        self._stats["embeddings_generated"] = len(embeddings)

        # Build similarity index - FAIL FAST if component fails
        self._update_progress(
            ProgressStage.BUILDING_INDEX,
            "Building similarity search index",
            50.0,
        )
        try:
            success = self.similarity_detector.build_index(embeddings, filtered_symbols)
        except Exception as e:
            print(f"FATAL: Similarity index building failed: {e}", file=sys.stderr)
            sys.exit(1)

        if not success:
            print("FATAL: Failed to build similarity index", file=sys.stderr)
            sys.exit(1)

        # Find similar pairs - FAIL FAST if component fails
        self._update_progress(
            ProgressStage.FINDING_DUPLICATES,
            "Finding duplicate symbol pairs",
            70.0,
        )
        try:
            duplicates = self._find_similar_pairs(
                filtered_symbols, embeddings, threshold
            )
        except Exception as e:
            print(f"FATAL: Similar pairs finding failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Update registry with results - FAIL FAST if component fails
        if self.config.enable_caching:
            self._update_progress(
                ProgressStage.UPDATING_REGISTRY,
                "Updating symbol registry",
                80.0,
            )
            try:
                self._update_registry_with_results(filtered_symbols, embeddings)
            except Exception as e:
                print(f"FATAL: Registry update failed: {e}", file=sys.stderr)
                sys.exit(1)

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
                print(f"FATAL: Changed file detection failed: {e}", file=sys.stderr)
                sys.exit(1)

        if not changed_files:
            print(
                "FATAL: No file changes detected for incremental analysis",
                file=sys.stderr,
            )
            sys.exit(1)

        # Extract symbols from changed files
        symbols = []
        for file_path in changed_files:
            try:
                file_symbols = self._extract_file_symbols(file_path)
                symbols.extend(file_symbols)
            except Exception as e:
                print(
                    f"FATAL: Symbol extraction failed for {file_path}: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)

        if not symbols:
            print("FATAL: No symbols in changed files", file=sys.stderr)
            sys.exit(1)

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

        return result

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

        # Filter out excluded patterns
        filtered_files = []
        for file_path in all_files:
            excluded = False
            for exclude_pattern in self.config.exclude_file_patterns:
                if exclude_pattern.replace("*", "") in str(file_path):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(file_path)

        # Extract symbols from files - FAIL FAST on component failure
        all_symbols = []
        for file_path in filtered_files[: self.config.max_symbols]:
            try:
                file_symbols = self._extract_file_symbols(file_path)
                all_symbols.extend(file_symbols)
            except Exception as e:
                print(
                    f"FATAL: Symbol extraction failed for {file_path}: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)

        return all_symbols

    def _extract_file_symbols(self, file_path: Path) -> List[Symbol]:
        """
        Extract symbols from a single file using Serena client.
        NO FALLBACK.
        """
        try:
            symbols = self.serena_client.extract_symbols([file_path])
            return symbols
        except Exception as e:
            # No fallback - raise exception to be handled by caller
            raise Exception(
                f"SerenaClient symbol extraction failed for {file_path}: {e}"
            )

    def _filter_symbols(self, symbols: List[Symbol]) -> List[Symbol]:
        """Filter symbols based on configuration."""
        filtered = []

        for symbol in symbols:
            # Type filtering
            type_val = symbol.symbol_type.value
            if type_val not in self.config.include_symbol_types:
                continue

            # Length filtering
            content_len = len(symbol.line_content.strip())
            if content_len < self.config.min_symbol_length:
                continue

            # File pattern filtering
            excluded = False
            for pattern in self.config.exclude_file_patterns:
                if pattern.replace("*", "") in symbol.file_path.lower():
                    excluded = True
                    break

            if excluded:
                continue

            filtered.append(symbol)

        return filtered

    def _handle_incremental_updates(self, symbols: List[Symbol]) -> List[Symbol]:
        """Handle incremental updates using registry manager - NO FALLBACK."""
        # Update symbols in registry
        update_results = self.registry_manager.update_symbols(symbols)

        # Return only symbols that needed updates
        updated_symbols = []
        for symbol in symbols:
            entry_key = self.registry_manager._get_entry_key(
                symbol.file_path, symbol.name
            )
            if update_results.get(entry_key, False):
                updated_symbols.append(symbol)

        return updated_symbols if updated_symbols else symbols

    def _find_similar_pairs(
        self, symbols: List[Symbol], embeddings: np.ndarray, threshold: float
    ) -> List[DuplicateResult]:
        """Find similar symbol pairs using similarity detector."""
        duplicates = []

        # Perform batch similarity search - NO FALLBACK
        similarity_results = self.similarity_detector.batch_similarity_search(
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
                match_symbol = symbols[match.match_index]

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
                "detection_method": "embedding_similarity",
                "embedding_engine": self.embedding_engine.get_engine_info()["method"],
                "similarity_detector": self.similarity_detector.get_detector_info()[
                    "method"
                ],
            },
        )

    def _update_registry_with_results(
        self, symbols: List[Symbol], embeddings: np.ndarray
    ) -> None:
        """Update registry with symbols and their embeddings - NO FALLBACK."""
        for i, symbol in enumerate(symbols):
            embedding = embeddings[i] if i < len(embeddings) else None
            metadata = {
                "analysis_timestamp": time.time(),
                "embedding_method": self.embedding_engine.get_engine_info()["method"],
                "similarity_method": self.similarity_detector.get_detector_info()[
                    "method"
                ],
            }

            self.registry_manager.register_symbol(symbol, embedding, metadata)

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
                    },
                    "duplicate_symbol": {
                        "name": duplicate.duplicate_symbol.name,
                        "type": duplicate.duplicate_symbol.symbol_type.value,
                        "file": duplicate.duplicate_symbol.file_path,
                        "line": duplicate.duplicate_symbol.line_number,
                        "content": duplicate.duplicate_symbol.line_content[:100],
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
            "analysis_mode": self.config.analysis_mode.value,
            "component_info": {
                "serena_client": self.serena_client.get_connection_info(),
                "embedding_engine": self.embedding_engine.get_engine_info(),
                "similarity_detector": self.similarity_detector.get_detector_info(),
                "registry_manager": self.registry_manager.get_registry_stats(),
            },
            "configuration": {
                "max_symbols": self.config.max_symbols,
                "batch_size": self.config.batch_size,
                "enable_caching": self.config.enable_caching,
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
                "analysis_mode": self.config.analysis_mode.value,
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
                "serena_client": self.serena_client.get_connection_info(),
                "embedding_engine": self.embedding_engine.get_engine_info(),
                "similarity_detector": self.similarity_detector.get_detector_info(),
                "registry_manager": self.registry_manager.get_registry_stats(),
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
            # Clear component caches - FAIL if any component fails
            try:
                self.embedding_engine.clear_cache()
            except Exception as e:
                print(
                    f"FATAL: EmbeddingEngine cache clear failed: {e}", file=sys.stderr
                )
                sys.exit(1)

            try:
                self.similarity_detector.clear_index()
            except Exception as e:
                print(
                    f"FATAL: SimilarityDetector index clear failed: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)

            try:
                self.registry_manager.cleanup_stale_entries()
            except Exception as e:
                print(f"FATAL: RegistryManager cleanup failed: {e}", file=sys.stderr)
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
        description="Duplicate detection using integrated core components"
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

        print("\nAll 4 core components verified functional:")
        print("  - SerenaClient: Connected to MCP server")
        print("  - EmbeddingEngine: CodeBERT/transformers available")
        print("  - SimilarityDetector: Faiss indexing operational")
        print("  - RegistryManager: SQLite storage accessible")


if __name__ == "__main__":
    main()
