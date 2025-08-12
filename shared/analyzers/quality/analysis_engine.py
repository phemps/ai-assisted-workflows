#!/usr/bin/env python3
"""
Complete Analysis Engine Orchestrator
======================================

PURPOSE: Unified interface for comprehensive code quality analysis,
combining duplicate detection, pattern classification, and result aggregation.
Part of the analyzers/quality suite for orchestrated multi-analysis workflows.

APPROACH:
- Orchestrates multiple analysis components in a unified workflow
- Combines duplicate detection, pattern classification, and result aggregation
- Provides comprehensive reporting and statistical analysis
- Integrates with the BaseAnalyzer infrastructure for consistency

DEPENDENCIES:
- code_duplication_analyzer for duplicate detection
- pattern_classifier for code pattern analysis
- result_aggregator for analysis result consolidation

USE CASES:
- Complete codebase quality assessment
- Multi-dimensional code analysis reporting
- Orchestrated quality gate analysis in CI/CD
- Comprehensive quality metrics collection

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements orchestration-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns
"""

import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

# Import base analyzer infrastructure
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared.core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
except ImportError as e:
    print(f"Error importing base analyzer: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from .code_duplication_analyzer import CompositeDuplicateDetector, CodeBlock
    from .pattern_classifier import CompositePatternClassifier
    from .result_aggregator import (
        AnalysisAggregator,
        ComprehensiveAnalysisReport,
        Priority,
        AnalysisType,
    )
except ImportError:
    # Handle direct script execution
    from code_duplication_analyzer import CompositeDuplicateDetector, CodeBlock
    from pattern_classifier import CompositePatternClassifier
    from result_aggregator import (
        AnalysisAggregator,
        ComprehensiveAnalysisReport,
        Priority,
        AnalysisType,
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisEngine(BaseAnalyzer):
    """Complete code quality analysis engine extending BaseAnalyzer infrastructure."""

    def __init__(
        self,
        config: Optional[AnalyzerConfig] = None,
        enable_duplicate_detection: bool = True,
        enable_pattern_classification: bool = True,
        min_duplicate_lines: int = 5,
        min_confidence: float = 0.5,
    ):
        """
        Initialize the analysis engine.

        Args:
            config: BaseAnalyzer configuration
            enable_duplicate_detection: Enable duplicate code detection
            enable_pattern_classification: Enable pattern classification
            min_duplicate_lines: Minimum lines for duplicate detection
            min_confidence: Minimum confidence threshold for reporting
        """
        # Create quality analysis-specific configuration
        quality_config = config or AnalyzerConfig(
            code_extensions={
                ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".java",
                ".cs",
                ".php",
                ".rb",
                ".go",
                ".rs",
                ".cpp",
                ".c",
                ".h",
                ".hpp",
                ".swift",
                ".kt",
                ".scala",
                ".dart",
                ".vue",
            },
            skip_patterns={
                "node_modules",
                ".git",
                "__pycache__",
                ".pytest_cache",
                "venv",
                "env",
                ".venv",
                "dist",
                "build",
                ".next",
                "coverage",
                ".nyc_output",
                "target",
                "vendor",
                "migrations",
                "test",
                "tests",
                "__tests__",
                "spec",
                "specs",
            },
        )

        # Initialize base analyzer
        super().__init__("quality", quality_config)

        # Initialize analysis-specific attributes
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

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Implement orchestrated analysis logic for target path.

        Args:
            target_path: Path to analyze (single file - BaseAnalyzer handles directory iteration)

        Returns:
            List of analysis findings from all enabled analyzers
        """
        target = Path(target_path)

        if target.is_file() and target.suffix == ".py":
            try:
                relative_path = str(target.relative_to(Path.cwd()))
            except ValueError:
                relative_path = str(target)

            return self._analyze_file_comprehensive(str(target), relative_path)

        return []

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """
        Get orchestrated analysis engine-specific metadata.

        Returns:
            Dictionary with analyzer-specific metadata
        """
        return {
            "analysis_type": "quality_orchestration",
            "orchestrated_components": {
                "duplicate_detection": self.enable_duplicate_detection,
                "pattern_classification": self.enable_pattern_classification,
                "result_aggregation": "always_enabled",
            },
            "thresholds": {
                "min_duplicate_lines": self.min_duplicate_lines,
                "min_confidence": self.min_confidence,
            },
            "supported_languages": [
                "Python",
                "JavaScript",
                "TypeScript",
                "Java",
                "C#",
                "PHP",
                "Ruby",
                "Go",
                "Rust",
                "C++",
                "C",
                "Swift",
                "Kotlin",
                "Scala",
                "Dart",
                "Vue",
            ],
            "dependencies": [
                "code_duplication_analyzer",
                "pattern_classifier",
                "result_aggregator",
            ],
            "use_cases": [
                "Complete codebase quality assessment",
                "Multi-dimensional code analysis reporting",
                "Orchestrated quality gate analysis in CI/CD",
                "Comprehensive quality metrics collection",
            ],
        }

    def _analyze_file_comprehensive(
        self, file_path: str, relative_path: str
    ) -> List[Dict[str, Any]]:
        """Analyze a single file with comprehensive quality analysis."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.strip():
                return []

            findings = []

            # Pattern classification analysis
            if self.enable_pattern_classification:
                try:
                    pattern_matches = self.pattern_classifier.classify_patterns(
                        content, relative_path
                    )
                    # Convert pattern matches to findings format
                    for pattern in pattern_matches:
                        findings.append(
                            {
                                "type": "pattern_classification",
                                "severity": self._get_pattern_severity(pattern),
                                "message": f"Pattern detected: {pattern.get('pattern_type', 'unknown')}",
                                "file_path": relative_path,
                                "line_number": pattern.get("line_number", 1),
                                "metadata": pattern,
                            }
                        )
                    logger.debug(
                        f"Found {len(pattern_matches)} patterns in {relative_path}"
                    )
                except Exception as e:
                    logger.error(
                        f"Pattern classification failed for {relative_path}: {e}"
                    )
                    findings.append(
                        {
                            "type": "analysis_error",
                            "severity": "low",
                            "message": f"Pattern classification failed: {str(e)}",
                            "file_path": relative_path,
                            "line_number": 1,
                            "metadata": {"error_type": type(e).__name__},
                        }
                    )

            # Add file analysis completion info
            findings.append(
                {
                    "type": "orchestrated_analysis",
                    "severity": "info",
                    "message": "File analyzed with orchestrated quality engine",
                    "file_path": relative_path,
                    "line_number": 1,
                    "metadata": {
                        "total_lines": len(content.splitlines()),
                        "analyzers_enabled": {
                            "duplicate_detection": self.enable_duplicate_detection,
                            "pattern_classification": self.enable_pattern_classification,
                        },
                        "findings_count": len(
                            [
                                f
                                for f in findings
                                if f["type"] != "orchestrated_analysis"
                            ]
                        ),
                    },
                }
            )

            return findings

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return [
                {
                    "type": "analysis_error",
                    "severity": "low",
                    "message": f"Failed to analyze file: {str(e)}",
                    "file_path": relative_path,
                    "line_number": 1,
                    "metadata": {"error_type": type(e).__name__},
                }
            ]

    def _get_pattern_severity(self, pattern: Dict[str, Any]) -> str:
        """Determine severity level for pattern findings."""
        # Map pattern types to severity levels
        pattern_type = pattern.get("pattern_type", "").lower()
        confidence = pattern.get("confidence", 0.5)

        # High severity patterns
        if any(critical in pattern_type for critical in ["security", "error", "bug"]):
            return "high"
        # Medium severity patterns
        elif confidence > 0.8 or any(
            medium in pattern_type for medium in ["performance", "maintainability"]
        ):
            return "medium"
        # Low severity patterns
        else:
            return "low"

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


# Legacy function for backward compatibility
def analyze_code_quality(
    target_path: str,
    output_format: str = "json",
    enable_duplicate_detection: bool = True,
    enable_pattern_classification: bool = True,
    min_duplicate_lines: int = 5,
    min_confidence: float = 0.5,
) -> Dict[str, Any]:
    """
    Legacy function wrapper for backward compatibility.

    Args:
        target_path: Path to analyze
        output_format: Output format (json, console, summary)
        enable_duplicate_detection: Enable duplicate code detection
        enable_pattern_classification: Enable pattern classification
        min_duplicate_lines: Minimum lines for duplicate detection
        min_confidence: Minimum confidence threshold for reporting

    Returns:
        Analysis results
    """
    try:
        config = AnalyzerConfig(target_path=target_path, output_format=output_format)

        analyzer = AnalysisEngine(
            config=config,
            enable_duplicate_detection=enable_duplicate_detection,
            enable_pattern_classification=enable_pattern_classification,
            min_duplicate_lines=min_duplicate_lines,
            min_confidence=min_confidence,
        )

        # Use BaseAnalyzer's analyze for full directory analysis
        results = analyzer.analyze()

        # Convert AnalysisResult to dict for backward compatibility
        return {
            "success": results.success if hasattr(results, "success") else True,
            "findings": [
                finding.__dict__ if hasattr(finding, "__dict__") else finding
                for finding in (
                    results.findings if hasattr(results, "findings") else []
                )
            ],
            "metadata": results.metadata if hasattr(results, "metadata") else {},
            "execution_time": results.execution_time
            if hasattr(results, "execution_time")
            else 0,
        }

    except Exception as e:
        logger.error(f"Error in legacy quality analysis: {e}")
        return {"success": False, "error": str(e), "findings": []}


def main():
    """Main function for command-line usage."""
    analyzer = AnalysisEngine()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
