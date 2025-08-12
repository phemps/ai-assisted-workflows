#!/usr/bin/env python3
"""
CLI Utilities for Continuous Improvement Framework
Eliminates duplication of CLI argument parsing patterns.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from .error_handler import CIErrorHandler


class CLIBase:
    """Base class for CLI interfaces with common argument patterns."""

    def __init__(self, description: str, version: Optional[str] = None):
        self.description = description
        self.version = version
        self.parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._setup_common_arguments()

    def _setup_common_arguments(self):
        """Setup common arguments used across CI modules."""
        # Project and path arguments
        self.parser.add_argument(
            "--project-root",
            type=Path,
            default=Path.cwd(),
            help="Project root directory (default: current directory)",
        )

        # Output format arguments
        self.parser.add_argument(
            "--output-format",
            choices=["json", "console", "summary"],
            default="json",
            help="Output format (default: json)",
        )

        self.parser.add_argument(
            "--output-file", type=Path, help="Output file path (default: stdout)"
        )

        # Logging and verbosity
        self.parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help="Increase verbosity (can be used multiple times)",
        )

        self.parser.add_argument(
            "--quiet", "-q", action="store_true", help="Suppress non-error output"
        )

        # Configuration
        self.parser.add_argument(
            "--config-file", type=Path, help="Configuration file path"
        )

        # Version
        if self.version:
            self.parser.add_argument(
                "--version", action="version", version=f"%(prog)s {self.version}"
            )

    def add_threshold_arguments(self):
        """Add threshold-related arguments."""
        threshold_group = self.parser.add_argument_group("threshold options")

        threshold_group.add_argument(
            "--exact-threshold",
            type=float,
            default=0.95,
            help="Exact duplicate threshold (0.0-1.0, default: 0.95)",
        )

        threshold_group.add_argument(
            "--near-threshold",
            type=float,
            default=0.85,
            help="Near duplicate threshold (0.0-1.0, default: 0.85)",
        )

        threshold_group.add_argument(
            "--similar-threshold",
            type=float,
            default=0.75,
            help="Similar pattern threshold (0.0-1.0, default: 0.75)",
        )

    def add_detection_arguments(self):
        """Add detection-specific arguments."""
        detection_group = self.parser.add_argument_group("detection options")

        detection_group.add_argument(
            "--file-extensions",
            nargs="+",
            default=[".py", ".js", ".ts", ".java"],
            help="File extensions to analyze (default: .py .js .ts .java)",
        )

        detection_group.add_argument(
            "--exclude-patterns",
            nargs="+",
            default=["test_*", "*_test.py", "*.spec.py"],
            help="File patterns to exclude",
        )

        detection_group.add_argument(
            "--min-lines",
            type=int,
            default=5,
            help="Minimum lines for duplication detection (default: 5)",
        )

        detection_group.add_argument(
            "--ignore-test-files",
            action="store_true",
            default=True,
            help="Ignore test files (default: True)",
        )

    def add_analysis_arguments(self):
        """Add analysis-specific arguments."""
        analysis_group = self.parser.add_argument_group("analysis options")

        analysis_group.add_argument(
            "--analysis-type",
            choices=["security", "performance", "quality", "architecture", "all"],
            default="all",
            help="Type of analysis to perform (default: all)",
        )

        analysis_group.add_argument(
            "--max-findings",
            type=int,
            default=100,
            help="Maximum number of findings to report (default: 100)",
        )

        analysis_group.add_argument(
            "--severity-filter",
            choices=["low", "medium", "high", "critical"],
            help="Filter findings by minimum severity",
        )

    def add_execution_arguments(self):
        """Add execution control arguments."""
        execution_group = self.parser.add_argument_group("execution options")

        execution_group.add_argument(
            "--timeout",
            type=int,
            default=300,
            help="Operation timeout in seconds (default: 300)",
        )

        execution_group.add_argument(
            "--parallel", action="store_true", help="Enable parallel processing"
        )

        execution_group.add_argument(
            "--max-workers",
            type=int,
            default=4,
            help="Maximum worker processes/threads (default: 4)",
        )

        execution_group.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without executing",
        )

    def add_serena_arguments(self):
        """Add Serena MCP related arguments."""
        serena_group = self.parser.add_argument_group("Serena MCP options")

        serena_group.add_argument(
            "--use-serena",
            action="store_true",
            default=True,
            help="Use Serena MCP for analysis (default: True)",
        )

        serena_group.add_argument(
            "--no-serena",
            action="store_true",
            help="Skip Serena MCP, use fallback methods",
        )

        serena_group.add_argument(
            "--serena-timeout",
            type=int,
            default=30,
            help="Serena MCP timeout in seconds (default: 30)",
        )

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse arguments with validation."""
        parsed_args = self.parser.parse_args(args)
        self._validate_arguments(parsed_args)
        return parsed_args

    def _validate_arguments(self, args: argparse.Namespace):
        """Validate parsed arguments."""
        # Validate thresholds if present
        for threshold_attr in [
            "exact_threshold",
            "near_threshold",
            "similar_threshold",
        ]:
            if hasattr(args, threshold_attr):
                value = getattr(args, threshold_attr)
                if not (0.0 <= value <= 1.0):
                    CIErrorHandler.validation_error(
                        threshold_attr.replace("_", " "),
                        value,
                        "number between 0.0 and 1.0",
                    )

        # Validate project root exists
        if hasattr(args, "project_root") and not args.project_root.exists():
            CIErrorHandler.validation_error(
                "project_root", args.project_root, "existing directory path"
            )

        # Validate timeout
        if hasattr(args, "timeout") and args.timeout <= 0:
            CIErrorHandler.validation_error("timeout", args.timeout, "positive integer")

        # Validate max workers
        if hasattr(args, "max_workers") and args.max_workers <= 0:
            CIErrorHandler.validation_error(
                "max_workers", args.max_workers, "positive integer"
            )

        # Validate min lines
        if hasattr(args, "min_lines") and args.min_lines <= 0:
            CIErrorHandler.validation_error(
                "min_lines", args.min_lines, "positive integer"
            )

        # Handle no-serena flag
        if hasattr(args, "no_serena") and args.no_serena:
            args.use_serena = False


class OutputHandler:
    """Handle output formatting and writing for CLI tools."""

    def __init__(self, format_type: str = "json", output_file: Optional[Path] = None):
        self.format_type = format_type
        self.output_file = output_file

    def output_result(self, result: Any, quiet: bool = False) -> None:
        """Output result in the specified format."""
        if quiet:
            return

        if hasattr(result, "to_json") and self.format_type == "json":
            content = result.to_json()
        elif hasattr(result, "to_dict") and self.format_type == "json":
            content = json.dumps(result.to_dict(), indent=2, default=str)
        elif isinstance(result, dict) and self.format_type == "json":
            content = json.dumps(result, indent=2, default=str)
        elif self.format_type == "console":
            content = self._format_console_output(result)
        elif self.format_type == "summary":
            content = self._format_summary_output(result)
        else:
            content = str(result)

        if self.output_file:
            try:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                self.output_file.write_text(content)
                if not quiet:
                    print(f"Output written to: {self.output_file}")
            except PermissionError as e:
                CIErrorHandler.permission_error("write output", self.output_file, e)
        else:
            print(content)

    def _format_console_output(self, result: Any) -> str:
        """Format result for console output."""
        if hasattr(result, "format_console"):
            return result.format_console()
        elif hasattr(result, "__dict__"):
            lines = []
            for key, value in result.__dict__.items():
                if key.startswith("_"):
                    continue
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        else:
            return str(result)

    def _format_summary_output(self, result: Any) -> str:
        """Format result for summary output."""
        if hasattr(result, "summary"):
            summary = result.summary
            if isinstance(summary, dict):
                lines = []
                for key, value in summary.items():
                    lines.append(f"{key}: {value}")
                return "\n".join(lines)
            else:
                return str(summary)
        elif hasattr(result, "metadata") and isinstance(result.metadata, dict):
            return self._format_dict_summary(result.metadata)
        elif isinstance(result, dict):
            return self._format_dict_summary(result)
        else:
            return str(result)

    def _format_dict_summary(self, data: Dict[str, Any]) -> str:
        """Format dictionary as summary."""
        lines = []
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                if isinstance(value, list):
                    lines.append(f"{key}: {len(value)} items")
                else:
                    lines.append(f"{key}: {len(value)} keys")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)


def create_standard_cli(
    name: str,
    description: str,
    version: Optional[str] = None,
    add_threshold_args: bool = False,
    add_detection_args: bool = False,
    add_analysis_args: bool = False,
    add_execution_args: bool = False,
    add_serena_args: bool = False,
) -> CLIBase:
    """
    Create a standard CLI with common argument groups.

    Args:
        name: CLI tool name
        description: Tool description
        version: Tool version
        add_threshold_args: Add threshold-related arguments
        add_detection_args: Add detection-specific arguments
        add_analysis_args: Add analysis-specific arguments
        add_execution_args: Add execution control arguments
        add_serena_args: Add Serena MCP arguments

    Returns:
        Configured CLI instance
    """
    cli = CLIBase(description, version)

    if add_threshold_args:
        cli.add_threshold_arguments()

    if add_detection_args:
        cli.add_detection_arguments()

    if add_analysis_args:
        cli.add_analysis_arguments()

    if add_execution_args:
        cli.add_execution_arguments()

    if add_serena_args:
        cli.add_serena_arguments()

    return cli


def run_cli_tool(
    cli: CLIBase,
    main_function: Callable[[argparse.Namespace], Any],
    args: Optional[List[str]] = None,
) -> int:
    """
    Run a CLI tool with standard error handling and output formatting.

    Args:
        cli: CLI instance
        main_function: Main function to execute with parsed args
        args: Command line arguments (default: sys.argv)

    Returns:
        Exit code (0 for success)
    """
    try:
        parsed_args = cli.parse_args(args)

        # Setup output handler
        output_handler = OutputHandler(
            format_type=parsed_args.output_format,
            output_file=getattr(parsed_args, "output_file", None),
        )

        # Run main function
        result = main_function(parsed_args)

        # Output result
        if result is not None:
            output_handler.output_result(result, parsed_args.quiet)

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        if hasattr(parsed_args, "verbose") and parsed_args.verbose > 0:
            import traceback

            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1
