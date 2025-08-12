#!/usr/bin/env python3
"""
Complete Analysis Engine Orchestrator
Part of Phase 2: Analysis Engine - Main Orchestrator

This module provides a unified interface to run the complete analysis engine,
combining duplicate detection, pattern classification, and result aggregation.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from .code_duplication_analyzer import CompositeDuplicateDetector, CodeBlock
from .pattern_classifier import CompositePatternClassifier
from .result_aggregator import (
    AnalysisAggregator,
    ComprehensiveAnalysisReport,
    Priority,
    AnalysisType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Complete code quality analysis engine."""

    def __init__(
        self,
        enable_duplicate_detection: bool = True,
        enable_pattern_classification: bool = True,
        min_duplicate_lines: int = 5,
        min_confidence: float = 0.5,
    ):
        """
        Initialize the analysis engine.

        Args:
            enable_duplicate_detection: Enable duplicate code detection
            enable_pattern_classification: Enable pattern classification
            min_duplicate_lines: Minimum lines for duplicate detection
            min_confidence: Minimum confidence threshold for reporting
        """
        self.enable_duplicate_detection = enable_duplicate_detection
        self.enable_pattern_classification = enable_pattern_classification
        self.min_duplicate_lines = min_duplicate_lines
        self.min_confidence = min_confidence

        # Initialize components
        self.aggregator = AnalysisAggregator()

        if self.enable_duplicate_detection:
            self.duplicate_detector = CompositeDuplicateDetector()
            logger.info("Duplicate detection enabled")

        if self.enable_pattern_classification:
            self.pattern_classifier = CompositePatternClassifier()
            logger.info("Pattern classification enabled")

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a single Python file.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            Dictionary containing analysis results for the file
        """
        if not file_path.exists() or file_path.suffix != ".py":
            logger.warning(f"Skipping non-Python file: {file_path}")
            return {}

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return {}

        results = {
            "file_path": str(file_path),
            "duplicate_matches": [],
            "pattern_matches": [],
            "analysis_time": 0.0,
        }

        start_time = time.time()

        # Pattern classification
        if self.enable_pattern_classification:
            try:
                pattern_matches = self.pattern_classifier.classify_patterns(
                    content, str(file_path)
                )
                results["pattern_matches"] = pattern_matches
                self.aggregator.add_pattern_analysis(pattern_matches)
                logger.debug(f"Found {len(pattern_matches)} patterns in {file_path}")
            except Exception as e:
                logger.error(f"Pattern classification failed for {file_path}: {e}")

        results["analysis_time"] = time.time() - start_time
        return results

    def analyze_directory(
        self,
        directory_path: Path,
        recursive: bool = True,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze all Python files in a directory.

        Args:
            directory_path: Path to the directory to analyze
            recursive: Whether to analyze subdirectories
            include_patterns: File patterns to include (e.g., ['*.py'])
            exclude_patterns: File patterns to exclude (e.g., ['*test*', '__pycache__'])

        Returns:
            Dictionary containing aggregated analysis results
        """
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory does not exist: {directory_path}")

        # Default patterns
        if include_patterns is None:
            include_patterns = ["*.py"]
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", "*.pyc", ".git", ".venv", "venv", "env"]

        # Find Python files
        python_files = []
        for pattern in include_patterns:
            if recursive:
                files = list(directory_path.rglob(pattern))
            else:
                files = list(directory_path.glob(pattern))

            # Filter out excluded patterns
            for file_path in files:
                if not any(exclude in str(file_path) for exclude in exclude_patterns):
                    python_files.append(file_path)

        logger.info(f"Found {len(python_files)} Python files to analyze")

        # Analyze each file
        file_results = []
        all_code_blocks = []

        for file_path in python_files:
            logger.info(f"Analyzing {file_path}")

            file_result = self.analyze_file(file_path)
            if file_result:
                file_results.append(file_result)

                # Collect code blocks for duplicate detection
                if self.enable_duplicate_detection:
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        # Create blocks based on functions and classes
                        code_blocks = self._extract_code_blocks(content, str(file_path))
                        all_code_blocks.extend(code_blocks)
                    except Exception as e:
                        logger.error(
                            f"Failed to extract code blocks from {file_path}: {e}"
                        )

        # Run duplicate detection across all files
        if self.enable_duplicate_detection and all_code_blocks:
            logger.info(
                f"Running duplicate detection on {len(all_code_blocks)} code blocks"
            )
            try:
                duplicate_matches = self.duplicate_detector.detect_all_duplicates(
                    all_code_blocks
                )
                self.aggregator.add_duplicate_analysis(duplicate_matches)
                logger.info(f"Found {len(duplicate_matches)} duplicate patterns")
            except Exception as e:
                logger.error(f"Duplicate detection failed: {e}")

        # Generate analysis summary
        return {
            "directory_path": str(directory_path),
            "files_analyzed": len(file_results),
            "total_files_found": len(python_files),
            "file_results": file_results,
            "analysis_completed": True,
        }

    def _extract_code_blocks(self, content: str, file_path: str) -> List[CodeBlock]:
        """Extract logical code blocks from Python source code."""
        import ast

        code_blocks = []

        try:
            tree = ast.parse(content)
            lines = content.split("\n")

            class BlockExtractor(ast.NodeVisitor):
                def visit_FunctionDef(self, node):
                    if hasattr(node, "end_lineno") and node.end_lineno:
                        block_lines = lines[node.lineno - 1 : node.end_lineno]
                        block_content = "\n".join(block_lines)

                        if len(block_lines) >= self.min_duplicate_lines:
                            code_blocks.append(
                                CodeBlock(
                                    content=block_content,
                                    file_path=file_path,
                                    start_line=node.lineno,
                                    end_line=node.end_lineno,
                                    function_name=node.name,
                                )
                            )

                    self.generic_visit(node)

                def visit_ClassDef(self, node):
                    if hasattr(node, "end_lineno") and node.end_lineno:
                        block_lines = lines[node.lineno - 1 : node.end_lineno]
                        block_content = "\n".join(block_lines)

                        if len(block_lines) >= self.min_duplicate_lines:
                            code_blocks.append(
                                CodeBlock(
                                    content=block_content,
                                    file_path=file_path,
                                    start_line=node.lineno,
                                    end_line=node.end_lineno,
                                    class_name=node.name,
                                )
                            )

                    self.generic_visit(node)

            extractor = BlockExtractor()
            extractor.visit(tree)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")

        return code_blocks

    def generate_report(
        self,
        output_format: str = "text",
        output_file: Optional[Path] = None,
        include_low_confidence: bool = False,
    ) -> str:
        """
        Generate analysis report.

        Args:
            output_format: Output format ('text', 'json', 'csv')
            output_file: Optional file to write output to
            include_low_confidence: Include low-confidence results

        Returns:
            Generated report content
        """
        # Filter results by confidence if needed
        if not include_low_confidence:
            filtered_results = [
                r
                for r in self.aggregator.results
                if r.confidence >= self.min_confidence
            ]
            # Create a new aggregator with filtered results
            filtered_aggregator = AnalysisAggregator()
            filtered_aggregator.results = filtered_results
        else:
            filtered_aggregator = self.aggregator

        if output_format.lower() == "text":
            report_generator = ComprehensiveAnalysisReport(filtered_aggregator)
            content = report_generator.generate_detailed_report()
        elif output_format.lower() in ["json", "csv"]:
            content = filtered_aggregator.export_results(output_format)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        if output_file:
            output_file.write_text(content)
            logger.info(f"Report written to {output_file}")

        return content

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of the analysis."""
        if not self.aggregator.results:
            return {"total_issues": 0}

        project_summary = self.aggregator.generate_project_summary()

        return {
            "total_issues": len(self.aggregator.results),
            "files_analyzed": project_summary.total_files_analyzed,
            "critical_issues": len(
                self.aggregator.get_filtered_results(priority=Priority.CRITICAL)
            ),
            "high_issues": len(
                self.aggregator.get_filtered_results(priority=Priority.HIGH)
            ),
            "duplicate_issues": len(
                self.aggregator.get_filtered_results(
                    analysis_type=AnalysisType.DUPLICATE_DETECTION
                )
            ),
            "pattern_issues": len(
                self.aggregator.get_filtered_results(
                    analysis_type=AnalysisType.PATTERN_CLASSIFICATION
                )
            ),
            "avg_confidence": project_summary.avg_confidence,
            "top_problematic_files": project_summary.top_problematic_files[:5],
        }


def main():
    """Command-line interface for the analysis engine."""
    parser = argparse.ArgumentParser(description="Code Quality Analysis Engine")

    parser.add_argument(
        "path", type=str, help="Path to Python file or directory to analyze"
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Analyze directories recursively"
    )
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--min-confidence", type=float, default=0.5, help="Minimum confidence threshold"
    )
    parser.add_argument(
        "--min-duplicate-lines",
        type=int,
        default=5,
        help="Minimum lines for duplicate detection",
    )
    parser.add_argument(
        "--no-duplicates", action="store_true", help="Disable duplicate detection"
    )
    parser.add_argument(
        "--no-patterns", action="store_true", help="Disable pattern classification"
    )
    parser.add_argument(
        "--include-low-confidence",
        action="store_true",
        help="Include low-confidence results",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize analysis engine
    engine = AnalysisEngine(
        enable_duplicate_detection=not args.no_duplicates,
        enable_pattern_classification=not args.no_patterns,
        min_duplicate_lines=args.min_duplicate_lines,
        min_confidence=args.min_confidence,
    )

    # Analyze path
    analysis_path = Path(args.path)
    start_time = time.time()

    try:
        if analysis_path.is_file():
            logger.info(f"Analyzing file: {analysis_path}")
            engine.analyze_file(analysis_path)
        elif analysis_path.is_dir():
            logger.info(f"Analyzing directory: {analysis_path}")
            engine.analyze_directory(analysis_path, recursive=args.recursive)
        else:
            logger.error(f"Path does not exist: {analysis_path}")
            sys.exit(1)

        analysis_time = time.time() - start_time

        # Generate and output report
        output_file = Path(args.output) if args.output else None
        report = engine.generate_report(
            output_format=args.format,
            output_file=output_file,
            include_low_confidence=args.include_low_confidence,
        )

        # Print summary statistics
        stats = engine.get_summary_stats()
        print(f"\nAnalysis completed in {analysis_time:.2f} seconds")
        print(f"Files analyzed: {stats['files_analyzed']}")
        print(f"Total issues found: {stats['total_issues']}")
        print(f"Critical issues: {stats['critical_issues']}")
        print(f"High priority issues: {stats['high_issues']}")
        print(f"Average confidence: {stats['avg_confidence']:.1%}")

        if not args.output:
            print("\n" + "=" * 60)
            print("ANALYSIS REPORT")
            print("=" * 60)
            print(report)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
