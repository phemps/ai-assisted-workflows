#!/usr/bin/env python3
"""
BaseAnalyzer - Shared Infrastructure for Analysis Tools
=======================================================

PURPOSE: Abstract base class providing common functionality for all analysis tools.
Part of the shared/analyzers/ suite - eliminates duplication across analysis categories.

ELIMINATES DUPLICATION FROM:
- Manual sys.path manipulation and import setup across 20+ analyzer files
- Individual utility imports (ResultFormatter, TechStackDetector, PlatformDetector)
- Duplicated CLI argument parsing and error handling patterns
- Repeated file scanning and filtering logic
- Inconsistent result formatting and metadata handling

PROVIDES SHARED INFRASTRUCTURE:
- Automatic import path setup and common utility access
- Standardized configuration management via AnalyzerConfig
- File scanning with configurable extensions and skip patterns
- CLI interface with consistent argument parsing
- Result formatting and error handling
- Performance timing and logging
- Abstract interface for specific analysis implementations

EXTENDS: Similar to BaseProfiler but for general analysis tools
- Uses same architectural patterns and infrastructure approach
- Supports all analysis categories: security, quality, architecture, performance, root_cause
- Abstract interface for specific analysis implementations
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field

from .module_base import CIAnalysisModule
from .cli_utils import CLIBase
from .config_factory import ConfigFactory


@dataclass
class AnalyzerConfig:
    """Standard configuration for all analyzers with validation."""

    # Core settings
    target_path: str = "."
    output_format: str = "json"
    min_severity: str = "low"
    summary_mode: bool = False

    # File filtering
    code_extensions: Set[str] = field(
        default_factory=lambda: {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".sql",
            ".prisma",
            ".kt",
            ".scala",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".swift",
            ".rs",
            ".dart",
            ".vue",
            ".jsx",
            ".tsx",
            ".xml",
            ".json",
            ".yml",
            ".yaml",
        }
    )

    skip_patterns: Set[str] = field(
        default_factory=lambda: {
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
            ".cache",
            ".tmp",
            "temp",
            "logs",
            "bin",
            "obj",
            "Debug",
            "Release",
        }
    )

    # Analysis settings
    max_files: int = 5000
    max_file_size_mb: int = 5
    batch_size: int = 50
    timeout_seconds: int = 120

    # Severity filtering
    severity_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "critical": 0.9,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.3,
        }
    )

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()

    def _validate_config(self):
        """Validate configuration values."""
        if self.max_files <= 0:
            raise ValueError("max_files must be positive")
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        valid_formats = {"json", "console", "summary"}
        if self.output_format not in valid_formats:
            raise ValueError(f"output_format must be one of: {valid_formats}")

        valid_severities = {"critical", "high", "medium", "low"}
        if self.min_severity not in valid_severities:
            raise ValueError(f"min_severity must be one of: {valid_severities}")


class BaseAnalyzer(CIAnalysisModule, ABC):
    """
    Abstract base class for all analysis tools.

    Provides common infrastructure:
    - File scanning and filtering
    - Configuration management
    - CLI interface
    - Result formatting
    - Timing and logging
    - Error handling
    """

    def __init__(self, analyzer_type: str, config: Optional[AnalyzerConfig] = None):
        super().__init__(f"{analyzer_type}_analyzer")

        self.analyzer_type = analyzer_type
        self.config = config or AnalyzerConfig()

        # Initialize common utilities (available from CIAnalysisModule)
        self.tech_detector = self.TechStackDetector()

        # Analysis tracking
        self.files_processed = 0
        self.files_skipped = 0
        self.processing_errors = 0

        self.log_operation(
            "analyzer_initialized",
            {
                "type": analyzer_type,
                "max_files": self.config.max_files,
                "extensions": len(self.config.code_extensions),
            },
        )

    @abstractmethod
    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Implement specific analysis logic for the target path.

        Args:
            target_path: Path to analyze

        Returns:
            List of analysis findings as dictionaries
        """
        pass

    @abstractmethod
    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """
        Get analyzer-specific metadata for results.

        Returns:
            Dictionary with analyzer-specific metadata
        """
        pass

    def should_scan_file(self, file_path: Path) -> bool:
        """
        Determine if file should be scanned based on configuration.

        Args:
            file_path: Path to check

        Returns:
            True if file should be scanned
        """
        # Check if file is in skip patterns
        for part in file_path.parts:
            if part in self.config.skip_patterns:
                return False

        # Check file extension
        suffix = file_path.suffix.lower()
        if suffix not in self.config.code_extensions:
            return False

        # Check file size
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                self.log_operation(
                    "file_skipped_size",
                    {"file": str(file_path), "size_mb": round(file_size_mb, 2)},
                )
                return False
        except (OSError, FileNotFoundError):
            return False

        return True

    def scan_directory(self, target_path: str) -> List[Path]:
        """
        Scan directory for files matching analyzer criteria.

        Args:
            target_path: Directory to scan

        Returns:
            List of file paths to analyze
        """
        target = Path(target_path)
        files_to_scan = []

        if target.is_file():
            if self.should_scan_file(target):
                files_to_scan.append(target)
        elif target.is_dir():
            for file_path in target.rglob("*"):
                if len(files_to_scan) >= self.config.max_files:
                    self.log_operation(
                        "max_files_reached", {"limit": self.config.max_files}
                    )
                    break

                if file_path.is_file() and self.should_scan_file(file_path):
                    files_to_scan.append(file_path)

        self.log_operation(
            "directory_scanned",
            {"target": target_path, "files_found": len(files_to_scan)},
        )

        return files_to_scan

    def process_files_batch(self, files: List[Path]) -> List[Dict[str, Any]]:
        """
        Process files in batches for memory efficiency.

        Args:
            files: List of files to process

        Returns:
            Combined findings from all files
        """
        all_findings = []

        for i in range(0, len(files), self.config.batch_size):
            batch = files[i : i + self.config.batch_size]
            batch_findings = self._process_batch(batch)
            all_findings.extend(batch_findings)

            self.log_operation(
                "batch_processed",
                {
                    "batch_number": (i // self.config.batch_size) + 1,
                    "files_in_batch": len(batch),
                    "findings": len(batch_findings),
                },
            )

        return all_findings

    def _process_batch(self, batch: List[Path]) -> List[Dict[str, Any]]:
        """Process a single batch of files."""
        batch_findings = []

        for file_path in batch:
            try:
                # Call the specific analyzer implementation
                file_findings = self.analyze_target(str(file_path))
                batch_findings.extend(file_findings)
                self.files_processed += 1

            except Exception as e:
                self.processing_errors += 1
                self.logger.warning(f"Error processing {file_path}: {e}")

        return batch_findings

    def analyze(self, target_path: Optional[str] = None) -> Any:
        """
        Main analysis entry point with full analysis pipeline.

        Args:
            target_path: Path to analyze (uses config.target_path if None)

        Returns:
            AnalysisResult object with findings and metadata
        """
        self.start_analysis()

        analyze_path = target_path or self.config.target_path
        result = self.create_result("analysis")

        try:
            # Scan for files to analyze
            files_to_analyze = self.scan_directory(analyze_path)

            if not files_to_analyze:
                result.add_info("No files found matching analyzer criteria")
                return self.complete_analysis(result)

            # Process files in batches
            all_findings = self.process_files_batch(files_to_analyze)

            # Convert findings to Finding objects
            self._add_findings_to_result(result, all_findings)

            # Add comprehensive metadata
            self._add_metadata_to_result(
                result, analyze_path, files_to_analyze, all_findings
            )

        except Exception as e:
            result.set_error(f"{self.analyzer_type} analysis failed: {str(e)}")
            self.logger.error(f"Analysis failed: {e}")

        return self.complete_analysis(result)

    def _add_findings_to_result(
        self, result: Any, findings: List[Dict[str, Any]]
    ) -> None:
        """Convert raw findings to Finding objects and add to result."""
        finding_id = 1

        for finding_data in findings:
            try:
                # Create Finding object with standard format
                finding = self.ResultFormatter.create_finding(
                    f"{self.analyzer_type.upper()}{finding_id:03d}",
                    finding_data.get("title", f"{self.analyzer_type} finding"),
                    finding_data.get("description", "Analysis issue detected"),
                    finding_data.get("severity", "medium"),
                    finding_data.get("file_path", "unknown"),
                    finding_data.get("line_number", 0),
                    finding_data.get(
                        "recommendation", f"Review {self.analyzer_type} issue"
                    ),
                    finding_data.get("metadata", {}),
                )

                result.add_finding(finding)
                finding_id += 1

            except Exception as e:
                self.logger.warning(f"Error creating finding {finding_id}: {e}")

    def _add_metadata_to_result(
        self,
        result: Any,
        target_path: str,
        files: List[Path],
        findings: List[Dict[str, Any]],
    ) -> None:
        """Add comprehensive metadata to result."""
        analyzer_metadata = self.get_analyzer_metadata()

        result.metadata = {
            "analyzer_type": self.analyzer_type,
            "target_path": target_path,
            "files_analyzed": len(files),
            "files_processed": self.files_processed,
            "files_skipped": self.files_skipped,
            "processing_errors": self.processing_errors,
            "total_findings": len(findings),
            "severity_breakdown": self._calculate_severity_breakdown(findings),
            "analyzer_config": {
                "max_files": self.config.max_files,
                "max_file_size_mb": self.config.max_file_size_mb,
                "extensions_count": len(self.config.code_extensions),
                "skip_patterns_count": len(self.config.skip_patterns),
            },
            **analyzer_metadata,
        }

    def _calculate_severity_breakdown(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate breakdown of findings by severity."""
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for finding in findings:
            severity = finding.get("severity", "medium")
            if severity in breakdown:
                breakdown[severity] += 1

        return breakdown

    def create_cli(self) -> CLIBase:
        """
        Create standard CLI interface for this analyzer.

        Returns:
            CLIBase instance with analyzer-specific arguments
        """
        cli = CLIBase(f"{self.analyzer_type.title()} Analyzer")

        # Add analyzer-specific arguments
        cli.parser.add_argument(
            "target_path",
            nargs="?",
            default=self.config.target_path,
            help="Path to analyze (default: current directory)",
        )

        cli.parser.add_argument(
            "--max-files",
            type=int,
            default=self.config.max_files,
            help=f"Maximum files to analyze (default: {self.config.max_files})",
        )

        cli.parser.add_argument(
            "--max-file-size",
            type=int,
            default=self.config.max_file_size_mb,
            help=f"Maximum file size in MB (default: {self.config.max_file_size_mb})",
        )

        cli.parser.add_argument(
            "--batch-size",
            type=int,
            default=self.config.batch_size,
            help=f"Batch size for processing (default: {self.config.batch_size})",
        )

        cli.parser.add_argument(
            "--timeout",
            type=int,
            default=self.config.timeout_seconds,
            help=f"Timeout in seconds (default: {self.config.timeout_seconds})",
        )

        # Add severity filtering and summary arguments
        cli.parser.add_argument(
            "--min-severity",
            choices=["critical", "high", "medium", "low"],
            default=self.config.min_severity,
            help=f"Minimum severity level (default: {self.config.min_severity})",
        )

        cli.parser.add_argument(
            "--summary",
            action="store_true",
            default=self.config.summary_mode,
            help="Show only top 10 critical/high severity findings",
        )

        return cli

    def run_cli(self) -> int:
        """
        Run CLI interface with standard error handling.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            cli = self.create_cli()
            args = cli.parser.parse_args()

            # Update config from CLI args
            self.config.target_path = args.target_path
            self.config.output_format = args.output_format
            self.config.max_files = args.max_files
            self.config.max_file_size_mb = args.max_file_size
            self.config.batch_size = args.batch_size
            self.config.timeout_seconds = args.timeout
            self.config.min_severity = args.min_severity
            self.config.summary_mode = args.summary

            # Run analysis
            result = self.analyze()

            # Output results
            if self.config.output_format == "console":
                print(self.ResultFormatter.format_console_output(result))
            elif self.config.output_format == "summary":
                print(
                    result.to_json(
                        summary_mode=True, min_severity=self.config.min_severity
                    )
                )
            else:  # json (default)
                print(
                    result.to_json(
                        summary_mode=self.config.summary_mode,
                        min_severity=self.config.min_severity,
                    )
                )

            return 0

        except KeyboardInterrupt:
            self.logger.info("Analysis interrupted by user")
            return 130
        except Exception as e:
            self.logger.error(f"CLI execution failed: {e}")
            return 1


def create_analyzer_config(**kwargs) -> AnalyzerConfig:
    """
    Factory function for creating AnalyzerConfig with validation.

    Args:
        **kwargs: Configuration parameters

    Returns:
        Validated AnalyzerConfig instance
    """
    return ConfigFactory.create_config("analyzer", AnalyzerConfig, **kwargs)
