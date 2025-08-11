#!/usr/bin/env python3
"""
Duplicate Detection Comparison Framework for Continuous Improvement System
Implements pluggable comparison algorithms with similarity scoring.
Part of Claude Code Workflows - integrates with 8-agent orchestration system.
"""

import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any, Set

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))

# Import utilities
try:
    from output_formatter import ResultFormatter
except ImportError as e:
    print(f"Error importing utilities: {e}", file=sys.stderr)
    sys.exit(1)

# Import Symbol from symbol_extractor
try:
    from .symbol_extractor import Symbol, SymbolType
except ImportError:
    try:
        from symbol_extractor import Symbol, SymbolType
    except ImportError as e:
        print(f"Error importing Symbol: {e}", file=sys.stderr)
        sys.exit(1)


class ComparisonType(Enum):
    """Types of comparisons supported by the framework."""

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
class SimilarityScore:
    """Represents similarity between two code symbols."""

    symbol1: Symbol
    symbol2: Symbol
    score: float  # 0.0 to 1.0 where 1.0 is identical
    comparison_type: ComparisonType
    reason: Optional[DuplicateReason] = None
    confidence: float = 1.0  # Confidence in the score (0.0 to 1.0)
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

        # Validate score range
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")

        # Validate confidence range
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


@dataclass
class ComparisonConfig:
    """Configuration for comparison algorithms following existing patterns."""

    # Thresholds
    exact_match_threshold: float = 1.0  # Must be perfect match
    high_similarity_threshold: float = 0.8  # High similarity indicator
    medium_similarity_threshold: float = 0.6  # Medium similarity indicator
    low_similarity_threshold: float = 0.3  # Minimum similarity to report

    # Symbol filtering
    include_symbol_types: Set[SymbolType] = None
    exclude_symbol_types: Set[SymbolType] = None
    min_line_length: int = 3  # Minimum lines in symbol to consider
    ignore_test_files: bool = True
    ignore_generated_files: bool = True

    # Comparison behavior
    case_sensitive_names: bool = False
    compare_across_files: bool = True
    compare_within_files: bool = True
    max_comparisons_per_run: int = 10000  # Prevent performance issues

    # Algorithm weights (sum should equal 1.0)
    name_similarity_weight: float = 0.3
    structure_similarity_weight: float = 0.4
    content_similarity_weight: float = 0.3

    def __post_init__(self):
        # Set defaults for symbol type filters
        if self.include_symbol_types is None:
            self.include_symbol_types = {
                SymbolType.FUNCTION,
                SymbolType.CLASS,
                SymbolType.METHOD,
            }

        if self.exclude_symbol_types is None:
            self.exclude_symbol_types = {SymbolType.IMPORT, SymbolType.VARIABLE}

        # Validate weights
        total_weight = (
            self.name_similarity_weight
            + self.structure_similarity_weight
            + self.content_similarity_weight
        )
        if abs(total_weight - 1.0) > 0.001:  # Allow for floating point
            raise ValueError(f"Algorithm weights must sum to 1.0, got {total_weight}")


@dataclass
class ComparisonResult:
    """Extended AnalysisResult for comparison findings, compatible with existing patterns."""

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

    def to_analysis_result(self) -> Any:
        """Convert to standard AnalysisResult format."""
        # Import here to avoid circular imports
        try:
            from output_formatter import AnalysisResult, ResultFormatter
        except ImportError:
            # Fallback for testing - just return self
            return self

        # Create an AnalysisResult with proper format
        result = AnalysisResult(
            analysis_type="architecture",  # Map to existing enum type
            script_name="duplicate_detector.py",
            target_path=self.metadata.get("project_root", "."),
        )

        # Convert findings to proper Finding objects
        for finding_data in self.findings:
            finding = ResultFormatter.create_finding(
                finding_id=finding_data.get("finding_id", ""),
                title=finding_data.get("title", ""),
                description=finding_data.get("description", ""),
                severity=finding_data.get("severity", "info"),
                file_path=finding_data.get("file_path"),
                line_number=finding_data.get("line_number"),
                recommendation=None,  # Could be added later
                evidence=finding_data.get("evidence", {}),
            )
            result.add_finding(finding)

        # Set metadata
        result.metadata.update(self.metadata)

        return result


class ComparisonAlgorithm(ABC):
    """Abstract base class for pluggable comparison algorithms."""

    def __init__(self, config: ComparisonConfig):
        self.config = config

    @abstractmethod
    def compare_symbols(self, symbols: List[Symbol]) -> List[SimilarityScore]:
        """
        Compare symbols and return similarity scores.

        Args:
            symbols: List of symbols to compare

        Returns:
            List of similarity scores for symbol pairs
        """
        pass

    @abstractmethod
    def configure(self, **kwargs) -> None:
        """
        Configure algorithm-specific parameters.

        Args:
            **kwargs: Algorithm-specific configuration parameters
        """
        pass

    @property
    @abstractmethod
    def algorithm_name(self) -> str:
        """Return the name of this algorithm."""
        pass

    @property
    @abstractmethod
    def supported_comparison_types(self) -> List[ComparisonType]:
        """Return the comparison types this algorithm supports."""
        pass

    def _should_compare_symbols(self, symbol1: Symbol, symbol2: Symbol) -> bool:
        """Check if two symbols should be compared based on configuration."""
        # Don't compare symbol with itself
        if (
            symbol1.file_path == symbol2.file_path
            and symbol1.line_number == symbol2.line_number
        ):
            return False

        # Check symbol type inclusion/exclusion
        for symbol in [symbol1, symbol2]:
            if (
                self.config.include_symbol_types
                and symbol.symbol_type not in self.config.include_symbol_types
            ):
                return False

            if (
                self.config.exclude_symbol_types
                and symbol.symbol_type in self.config.exclude_symbol_types
            ):
                return False

        # Check file comparison settings
        same_file = symbol1.file_path == symbol2.file_path
        if same_file and not self.config.compare_within_files:
            return False
        if not same_file and not self.config.compare_across_files:
            return False

        # Check minimum line length (use line_content as proxy)
        for symbol in [symbol1, symbol2]:
            if len(symbol.line_content.strip()) < self.config.min_line_length:
                return False

        # Check test file filtering
        if self.config.ignore_test_files:
            for symbol in [symbol1, symbol2]:
                file_path = symbol.file_path.lower()
                if (
                    "test_" in file_path
                    or "_test" in file_path
                    or "/test/" in file_path
                    or "spec_" in file_path
                ):
                    return False

        return True

    def _filter_symbols(self, symbols: List[Symbol]) -> List[Symbol]:
        """Filter symbols based on configuration before comparison."""
        filtered = []

        for symbol in symbols:
            # Check symbol type filters
            if (
                self.config.include_symbol_types
                and symbol.symbol_type not in self.config.include_symbol_types
            ):
                continue

            if (
                self.config.exclude_symbol_types
                and symbol.symbol_type in self.config.exclude_symbol_types
            ):
                continue

            # Check minimum line length
            if len(symbol.line_content.strip()) < self.config.min_line_length:
                continue

            # Check test file filtering
            if self.config.ignore_test_files:
                file_path = symbol.file_path.lower()
                if (
                    "test_" in file_path
                    or "_test" in file_path
                    or "/test/" in file_path
                    or "spec_" in file_path
                ):
                    continue

            # Check generated file filtering
            if self.config.ignore_generated_files:
                file_path = symbol.file_path.lower()
                if (
                    "generated" in file_path
                    or ".gen." in file_path
                    or "autogenerated" in file_path
                ):
                    continue

            filtered.append(symbol)

        return filtered


class BasicSimilarityAlgorithm(ComparisonAlgorithm):
    """Basic implementation of comparison algorithm using name and content similarity."""

    def __init__(self, config: ComparisonConfig):
        super().__init__(config)
        self._name = "basic_similarity"

    @property
    def algorithm_name(self) -> str:
        return self._name

    @property
    def supported_comparison_types(self) -> List[ComparisonType]:
        return [
            ComparisonType.EXACT_MATCH,
            ComparisonType.NAME_SIMILARITY,
            ComparisonType.STRUCTURAL_SIMILARITY,
        ]

    def configure(self, **kwargs) -> None:
        """Configure basic algorithm parameters."""
        if "name_weight" in kwargs:
            self.config.name_similarity_weight = kwargs["name_weight"]
        if "content_weight" in kwargs:
            self.config.content_similarity_weight = kwargs["content_weight"]
        if "structure_weight" in kwargs:
            self.config.structure_similarity_weight = kwargs["structure_weight"]

    def compare_symbols(self, symbols: List[Symbol]) -> List[SimilarityScore]:
        """Compare symbols using basic name and content similarity."""
        filtered_symbols = self._filter_symbols(symbols)
        similarity_scores = []
        comparisons_made = 0

        for i in range(len(filtered_symbols)):
            for j in range(i + 1, len(filtered_symbols)):
                if comparisons_made >= self.config.max_comparisons_per_run:
                    break

                symbol1 = filtered_symbols[i]
                symbol2 = filtered_symbols[j]

                if not self._should_compare_symbols(symbol1, symbol2):
                    continue

                score = self._calculate_similarity(symbol1, symbol2)

                # Only include scores above minimum threshold
                if score.score >= self.config.low_similarity_threshold:
                    similarity_scores.append(score)

                comparisons_made += 1

            if comparisons_made >= self.config.max_comparisons_per_run:
                break

        return similarity_scores

    def _calculate_similarity(
        self, symbol1: Symbol, symbol2: Symbol
    ) -> SimilarityScore:
        """Calculate similarity score between two symbols."""
        # Name similarity
        name_sim = self._calculate_name_similarity(symbol1.name, symbol2.name)

        # Content similarity (using line content as proxy)
        content_sim = self._calculate_content_similarity(
            symbol1.line_content, symbol2.line_content
        )

        # Structure similarity (based on symbol type, scope, parameters)
        structure_sim = self._calculate_structure_similarity(symbol1, symbol2)

        # Weighted combination
        overall_score = (
            name_sim * self.config.name_similarity_weight
            + content_sim * self.config.content_similarity_weight
            + structure_sim * self.config.structure_similarity_weight
        )

        # Determine comparison type and reason
        comparison_type = self._determine_comparison_type(
            name_sim, content_sim, structure_sim, overall_score
        )

        reason = self._determine_duplicate_reason(
            symbol1, symbol2, name_sim, content_sim, structure_sim, overall_score
        )

        return SimilarityScore(
            symbol1=symbol1,
            symbol2=symbol2,
            score=overall_score,
            comparison_type=comparison_type,
            reason=reason,
            confidence=min(
                1.0, min(name_sim, content_sim, structure_sim) + 0.1
            ),  # Simple confidence, capped at 1.0
            details={
                "name_similarity": name_sim,
                "content_similarity": content_sim,
                "structure_similarity": structure_sim,
                "comparison_algorithm": self.algorithm_name,
            },
        )

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names."""
        if not self.config.case_sensitive_names:
            name1 = name1.lower()
            name2 = name2.lower()

        # Exact match
        if name1 == name2:
            return 1.0

        # Simple Levenshtein-like similarity
        if not name1 or not name2:
            return 0.0

        # Jaccard similarity on character level
        set1 = set(name1)
        set2 = set(name2)
        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union) if union else 0.0

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between content strings."""
        content1 = content1.strip()
        content2 = content2.strip()

        # Exact match
        if content1 == content2:
            return 1.0

        if not content1 or not content2:
            return 0.0

        # Token-based similarity
        tokens1 = set(content1.split())
        tokens2 = set(content2.split())

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union) if union else 0.0

    def _calculate_structure_similarity(
        self, symbol1: Symbol, symbol2: Symbol
    ) -> float:
        """Calculate structural similarity between symbols."""
        similarity_score = 0.0
        checks = 0

        # Symbol type
        if symbol1.symbol_type == symbol2.symbol_type:
            similarity_score += 1.0
        checks += 1

        # Scope
        if symbol1.scope == symbol2.scope:
            similarity_score += 1.0
        checks += 1

        # Parameters (if available)
        if symbol1.parameters and symbol2.parameters:
            if len(symbol1.parameters) == len(symbol2.parameters):
                similarity_score += 1.0
            checks += 1

        # Visibility (if available)
        if symbol1.visibility and symbol2.visibility:
            if symbol1.visibility == symbol2.visibility:
                similarity_score += 1.0
            checks += 1

        return similarity_score / checks if checks > 0 else 0.0

    def _determine_comparison_type(
        self,
        name_sim: float,
        content_sim: float,
        structure_sim: float,
        overall_score: float,
    ) -> ComparisonType:
        """Determine the type of comparison based on similarity scores."""
        if overall_score >= self.config.exact_match_threshold:
            return ComparisonType.EXACT_MATCH
        elif name_sim >= 0.8:
            return ComparisonType.NAME_SIMILARITY
        elif structure_sim >= 0.8:
            return ComparisonType.STRUCTURAL_SIMILARITY
        else:
            return ComparisonType.SEMANTIC_SIMILARITY

    def _determine_duplicate_reason(
        self,
        symbol1: Symbol,
        symbol2: Symbol,
        name_sim: float,
        content_sim: float,
        structure_sim: float,
        overall_score: float,
    ) -> Optional[DuplicateReason]:
        """Determine why symbols might be duplicates."""
        if overall_score >= self.config.exact_match_threshold:
            return DuplicateReason.IDENTICAL_IMPLEMENTATION
        elif overall_score >= self.config.high_similarity_threshold:
            if symbol1.file_path != symbol2.file_path:
                return DuplicateReason.COPY_PASTE_ERROR
            else:
                return DuplicateReason.SIMILAR_FUNCTIONALITY
        elif overall_score >= self.config.medium_similarity_threshold:
            return DuplicateReason.REFACTOR_CANDIDATE

        return None


class ComparisonFramework:
    """Main framework for comparing symbols and detecting duplicates."""

    def __init__(self, config: ComparisonConfig = None, project_root: Path = None):
        self.config = config or ComparisonConfig()
        self.project_root = project_root or Path.cwd()
        self.algorithms: Dict[str, ComparisonAlgorithm] = {}
        self.result_formatter = ResultFormatter()

        # Register default algorithm
        self._register_default_algorithms()

    def _register_default_algorithms(self):
        """Register default comparison algorithms."""
        basic_algorithm = BasicSimilarityAlgorithm(self.config)
        self.register_algorithm(basic_algorithm)

    def register_algorithm(self, algorithm: ComparisonAlgorithm):
        """Register a comparison algorithm."""
        self.algorithms[algorithm.algorithm_name] = algorithm

    def compare_symbols(
        self, symbols: List[Symbol], algorithm_name: str = "basic_similarity"
    ) -> ComparisonResult:
        """
        Compare symbols using specified algorithm.

        Args:
            symbols: List of symbols to compare
            algorithm_name: Name of algorithm to use

        Returns:
            ComparisonResult with findings and analysis
        """
        start_time = time.time()

        if algorithm_name not in self.algorithms:
            available = ", ".join(self.algorithms.keys())
            raise ValueError(
                f"Algorithm '{algorithm_name}' not found. Available: {available}"
            )

        algorithm = self.algorithms[algorithm_name]
        similarity_scores = algorithm.compare_symbols(symbols)

        # Convert to findings format
        findings = []
        duplicate_pairs = set()

        for score in similarity_scores:
            # Create unique pair identifier to avoid duplicates
            pair_id = tuple(
                sorted(
                    [
                        f"{score.symbol1.file_path}:{score.symbol1.line_number}",
                        f"{score.symbol2.file_path}:{score.symbol2.line_number}",
                    ]
                )
            )

            if pair_id in duplicate_pairs:
                continue
            duplicate_pairs.add(pair_id)

            severity = self._determine_severity(score.score)

            finding = {
                "finding_id": f"duplicate_{len(findings):04d}",
                "title": f"Potential Duplicate: {score.symbol1.name} & {score.symbol2.name}",
                "description": f"Found {score.comparison_type.value} between symbols with {score.score:.2f} similarity",
                "severity": severity,
                "file_path": score.symbol1.file_path,
                "line_number": score.symbol1.line_number,
                "evidence": {
                    "similarity_score": score.score,
                    "comparison_type": score.comparison_type.value,
                    "duplicate_reason": score.reason.value if score.reason else None,
                    "confidence": score.confidence,
                    "symbol1": {
                        "name": score.symbol1.name,
                        "type": score.symbol1.symbol_type.value,
                        "file": score.symbol1.file_path,
                        "line": score.symbol1.line_number,
                        "content": score.symbol1.line_content[:100] + "..."
                        if len(score.symbol1.line_content) > 100
                        else score.symbol1.line_content,
                    },
                    "symbol2": {
                        "name": score.symbol2.name,
                        "type": score.symbol2.symbol_type.value,
                        "file": score.symbol2.file_path,
                        "line": score.symbol2.line_number,
                        "content": score.symbol2.line_content[:100] + "..."
                        if len(score.symbol2.line_content) > 100
                        else score.symbol2.line_content,
                    },
                    "details": score.details,
                },
            }

            findings.append(finding)

        # Create summary
        execution_time = time.time() - start_time
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in findings:
            severity_counts[finding["severity"]] += 1

        summary = {
            "total_duplicates_found": len(findings),
            "unique_symbol_pairs": len(duplicate_pairs),
            "symbols_analyzed": len(symbols),
            "algorithm_used": algorithm_name,
            "execution_time_seconds": round(execution_time, 2),
            "severity_breakdown": severity_counts,
            "configuration": {
                "high_similarity_threshold": self.config.high_similarity_threshold,
                "medium_similarity_threshold": self.config.medium_similarity_threshold,
                "low_similarity_threshold": self.config.low_similarity_threshold,
                "max_comparisons": self.config.max_comparisons_per_run,
            },
        }

        metadata = {
            "project_root": str(self.project_root),
            "comparison_framework_version": "1.0.0",
            "algorithm_name": algorithm_name,
            "supported_comparison_types": [
                ct.value for ct in algorithm.supported_comparison_types
            ],
            "timestamp": time.time(),
        }

        return ComparisonResult(
            analysis_type="duplicate_detection",
            findings=findings,
            summary=summary,
            metadata=metadata,
        )

    def _determine_severity(self, score: float) -> str:
        """Determine severity based on similarity score."""
        if score >= self.config.exact_match_threshold:
            return "critical"  # Exact duplicates
        elif score >= self.config.high_similarity_threshold:
            return "high"  # Likely duplicates
        elif score >= self.config.medium_similarity_threshold:
            return "medium"  # Possible duplicates
        else:
            return "low"  # Minor similarities

    def get_available_algorithms(self) -> List[str]:
        """Get list of available algorithm names."""
        return list(self.algorithms.keys())

    def configure_algorithm(self, algorithm_name: str, **kwargs):
        """Configure a specific algorithm."""
        if algorithm_name not in self.algorithms:
            raise ValueError(f"Algorithm '{algorithm_name}' not found")

        self.algorithms[algorithm_name].configure(**kwargs)


def main():
    """Main entry point for duplicate detection comparison framework."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare symbols for duplicate detection using pluggable algorithms"
    )
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument(
        "--algorithm", default="basic_similarity", help="Comparison algorithm to use"
    )
    parser.add_argument(
        "--high-threshold", type=float, default=0.8, help="High similarity threshold"
    )
    parser.add_argument(
        "--medium-threshold",
        type=float,
        default=0.6,
        help="Medium similarity threshold",
    )
    parser.add_argument(
        "--low-threshold", type=float, default=0.3, help="Low similarity threshold"
    )
    parser.add_argument(
        "--output", choices=["json", "summary"], default="json", help="Output format"
    )

    args = parser.parse_args()

    # Create configuration
    config = ComparisonConfig(
        high_similarity_threshold=args.high_threshold,
        medium_similarity_threshold=args.medium_threshold,
        low_similarity_threshold=args.low_threshold,
    )

    # Initialize framework
    framework = ComparisonFramework(config, args.project_root)

    # For demo purposes, create some sample symbols (in real use, these would come from symbol_extractor)
    sample_symbols = [
        Symbol(
            name="calculate_total",
            symbol_type=SymbolType.FUNCTION,
            file_path="/demo/math_utils.py",
            line_number=10,
            line_content="def calculate_total(items): return sum(items)",
            scope="module",
        ),
        Symbol(
            name="calc_sum",
            symbol_type=SymbolType.FUNCTION,
            file_path="/demo/helper.py",
            line_number=5,
            line_content="def calc_sum(values): return sum(values)",
            scope="module",
        ),
    ]

    # Compare symbols
    result = framework.compare_symbols(sample_symbols, args.algorithm)

    # Output results
    if args.output == "json":
        # Use compatible format with existing AnalysisResult structure
        import json

        output = {
            "analysis_type": result.analysis_type,
            "findings": result.findings,
            "summary": result.summary,
            "metadata": result.metadata,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        summary = result.summary
        print("Duplicate Detection Analysis Complete:")
        print(f"  Duplicates found: {summary['total_duplicates_found']}")
        print(f"  Symbols analyzed: {summary['symbols_analyzed']}")
        print(f"  Algorithm used: {summary['algorithm_used']}")
        print(f"  Execution time: {summary['execution_time_seconds']}s")
        print("  Severity breakdown:")
        for severity, count in summary["severity_breakdown"].items():
            if count > 0:
                print(f"    {severity}: {count}")


if __name__ == "__main__":
    main()
