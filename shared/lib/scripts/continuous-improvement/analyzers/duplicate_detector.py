#!/usr/bin/env python3
"""
Duplicate Detection Integration Script
Combines SymbolExtractor with ComparisonFramework for end-to-end duplicate detection.
Part of Claude Code Workflows - TASK-010 implementation.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))

# Import analysis components (after path setup)
from symbol_extractor import SymbolExtractor  # noqa: E402
from comparison_framework import ComparisonFramework, ComparisonConfig  # noqa: E402

# Import standard result formatter for consistency (after path setup)
try:
    from output_formatter import AnalysisResult
except ImportError:
    # Fallback - define a minimal compatible structure
    class AnalysisResult:
        def __init__(self, analysis_type, findings=None, summary=None, metadata=None):
            self.analysis_type = analysis_type
            self.findings = findings or []
            self.summary = summary or {}
            self.metadata = metadata or {}


class DuplicateDetector:
    """Integrated duplicate detection using symbol extraction and comparison."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[ComparisonConfig] = None,
    ):
        self.project_root = project_root or Path.cwd()
        self.config = config or ComparisonConfig()
        self.symbol_extractor = SymbolExtractor(self.project_root)
        self.comparison_framework = ComparisonFramework(self.config, self.project_root)

    def detect_duplicates(self, algorithm_name: str = "basic_similarity"):
        """
        End-to-end duplicate detection process.

        Args:
            algorithm_name: Comparison algorithm to use

        Returns:
            ComparisonResult with duplicate detection findings
        """
        # Step 1: Extract symbols from project
        print("Extracting symbols from project...", file=sys.stderr)
        symbol_result = self.symbol_extractor.extract_symbols(use_serena=False)

        # Step 2: Convert findings to Symbol objects (extract from the results)
        symbols = []
        for finding in symbol_result.findings:
            evidence = finding.get("evidence", {})
            if evidence:
                from symbol_extractor import Symbol, SymbolType

                # Map string to enum
                symbol_type_str = evidence.get("symbol_type", "function")
                try:
                    symbol_type = SymbolType(symbol_type_str)
                except ValueError:
                    symbol_type = SymbolType.FUNCTION  # Default fallback

                symbol = Symbol(
                    name=evidence.get("name", "unknown"),
                    symbol_type=symbol_type,
                    file_path=finding.get("file_path", ""),
                    line_number=finding.get("line_number", 0),
                    line_content=evidence.get("line_content", ""),
                    scope=evidence.get("scope", "unknown"),
                    visibility=evidence.get("visibility"),
                    parameters=evidence.get("parameters"),
                    return_type=evidence.get("return_type"),
                )
                symbols.append(symbol)

        print(f"Extracted {len(symbols)} symbols", file=sys.stderr)

        # Step 3: Compare symbols for duplicates
        print("Analyzing symbols for duplicates...", file=sys.stderr)
        comparison_result = self.comparison_framework.compare_symbols(
            symbols, algorithm_name
        )

        duplicates_found = comparison_result.summary["total_duplicates_found"]
        print(f"Found {duplicates_found} potential duplicates", file=sys.stderr)

        return comparison_result


def main():
    """Main entry point for integrated duplicate detection."""
    parser = argparse.ArgumentParser(
        description="Integrated duplicate detection using symbol extraction"
        " and comparison"
    )
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument(
        "--algorithm", default="basic_similarity", help="Comparison algorithm"
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

    # Run detection
    detector = DuplicateDetector(args.project_root, config)
    result = detector.detect_duplicates(args.algorithm)

    # Output results
    if args.output == "json":
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
        print("\n=== DUPLICATE DETECTION RESULTS ===")
        print(f"Duplicates found: {summary['total_duplicates_found']}")
        print(f"Symbols analyzed: {summary['symbols_analyzed']}")
        print(f"Algorithm used: {summary['algorithm_used']}")
        print(f"Execution time: {summary['execution_time_seconds']}s")

        if summary["severity_breakdown"]:
            print("\nSeverity breakdown:")
            for severity, count in summary["severity_breakdown"].items():
                if count > 0:
                    print(f"  {severity.upper()}: {count}")

        if result.findings:
            print("\nTop findings:")
            for i, finding in enumerate(result.findings[:5]):  # Show top 5
                evidence = finding["evidence"]
                symbol1 = evidence["symbol1"]
                symbol2 = evidence["symbol2"]
                print(f"  {i+1}. {finding['title']}")
                print(f"     Similarity: {evidence['similarity_score']:.2f}")
                file1 = symbol1["file"]
                line1 = symbol1["line"]
                file2 = symbol2["file"]
                line2 = symbol2["line"]
                print(f"     Files: {file1}:{line1} & {file2}:{line2}")


if __name__ == "__main__":
    main()
