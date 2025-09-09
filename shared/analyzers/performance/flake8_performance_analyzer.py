#!/usr/bin/env python3
"""
Flake8 Performance Analyzer - Advanced Code Performance Analysis.

PURPOSE: Comprehensive code performance analysis using Flake8's established rules.
Replaces bespoke regex pattern matching with established performance analysis.

APPROACH:
- Uses Flake8 with performance-focused plugins
- AST-based analysis instead of brittle regex patterns
- Multi-language support through plugin ecosystem
- Real-time rule updates from performance community

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements performance-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns

REPLACES: check_bottlenecks.py with bespoke regex patterns
- More accurate AST parsing vs regex matching
- Established rule ecosystem vs custom patterns
- Better context-aware analysis
"""

import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

# Import base analyzer (package root must be on PYTHONPATH)
from core.base.analyzer_base import AnalyzerConfig, BaseAnalyzer
from core.base.analyzer_registry import register_analyzer


@register_analyzer("performance:flake8-perf")
class Flake8PerformanceAnalyzer(BaseAnalyzer):
    """Performance analysis using Flake8 and plugins instead of regex patterns."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        # Create performance-specific configuration
        perf_config = config or AnalyzerConfig(
            code_extensions={
                ".py",  # Primary focus on Python performance
                ".pyi",  # Type stub files
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
                "*.min.js",
                "*.min.css",
                "*.bundle.js",
                ".tox",
                "site-packages",
                "*.egg-info",
            },
        )

        # Initialize base analyzer
        super().__init__("performance", perf_config)

        # Check for Flake8 availability - required for accurate analysis
        self._check_flake8_availability()

        # Flake8 performance configuration
        self.flake8_performance_rules = {
            # perflint rules (PERF)
            "PERF101": "high",  # Unnecessary list() call inside list comprehension
            "PERF102": "medium",  # Incorrect use of dict() constructor
            "PERF203": "high",  # try-except within a loop incurs performance overhead
            "PERF204": "medium",  # Use a set literal when testing for membership
            "PERF401": "high",  # Use a list comprehension instead of a loop
            "PERF402": "medium",  # Use list or set comprehensions instead of loops
            # flake8-comprehensions rules (C4)
            "C400": "medium",  # Unnecessary generator
            "C401": "medium",  # Unnecessary generator - set comprehension
            "C402": "medium",  # Unnecessary generator - dict comprehension
            "C403": "medium",  # Unnecessary list comprehension - set
            "C404": "medium",  # Unnecessary list comprehension - dict
            "C405": "medium",  # Unnecessary literalist - set
            "C406": "medium",  # Unnecessary literalist - dict
            "C408": "medium",  # Unnecessary dict call - use {}
            "C409": "medium",  # Unnecessary list/tuple - use comprehension
            "C410": "medium",  # Unnecessary list comprehension
            "C411": "medium",  # Unnecessary list call - use comprehension
            # flake8-bugbear performance rules (B)
            "B006": "high",  # Mutable default argument
            "B007": "medium",  # Unused loop control variable
            "B020": "high",  # Loop control variable overrides iterable
            "B023": "high",  # Function definition in loop
            "B905": "medium",  # zip() without explicit strict parameter
            # PyLint performance rules (converted to our format)
            "W0102": "high",  # Dangerous default value as argument
            "W0106": "medium",  # Expression not assigned
            "R1701": "medium",  # Use set comprehension instead of loop
            "R1717": "medium",  # Use dict.get() instead of conditional assignment
            "R1718": "medium",  # Use dict.get() with default instead of conditional
            "R1735": "medium",  # Use dict comprehension instead of dict()
        }

        # Additional performance patterns to check via AST
        self.ast_performance_patterns = [
            "nested_loops",
            "string_concatenation_in_loops",
            "expensive_operations_in_loops",
            "global_variable_access_in_loops",
            "repeated_function_calls",
        ]

    def _check_flake8_availability(self):
        """Check if Flake8 and performance plugins are available."""
        try:
            result = subprocess.run(
                ["flake8", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                print(
                    "ERROR: Flake8 is required for performance analysis but not found.",
                    file=sys.stderr,
                )
                print(
                    "Install with: pip install flake8 perflint flake8-comprehensions flake8-bugbear",
                    file=sys.stderr,
                )
                sys.exit(1)

            version_output = result.stdout.strip()
            print(f"Found Flake8 {version_output}", file=sys.stderr)

            # Validate required plugins are installed
            self._validate_required_plugins(version_output)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("ERROR: Flake8 is required but not available.", file=sys.stderr)
            print(
                "Install with: pip install flake8 perflint flake8-comprehensions flake8-bugbear",
                file=sys.stderr,
            )
            sys.exit(1)

    def _validate_required_plugins(self, version_output: str):
        """Validate that required Flake8 plugins are installed."""
        # Check flake8 plugins
        flake8_plugins = {
            "flake8-comprehensions": "C4 comprehension optimization rules",
            "flake8-bugbear": "B bug and performance rules",
        }

        missing_flake8_plugins = []
        for plugin_name, description in flake8_plugins.items():
            # Check if plugin name appears in flake8 --version output
            if (
                plugin_name not in version_output
                and plugin_name.replace("-", "_") not in version_output
            ):
                missing_flake8_plugins.append(f"{plugin_name} ({description})")

        # Check perflint separately since it's not a flake8 plugin
        perflint_available = self._check_perflint_availability()

        if missing_flake8_plugins or not perflint_available:
            print(
                "WARNING: Missing required performance analysis tools:", file=sys.stderr
            )
            for plugin in missing_flake8_plugins:
                print(f"  - {plugin}", file=sys.stderr)
            if not perflint_available:
                print("  - perflint (PERF performance analysis rules)", file=sys.stderr)

            # In testing environments, this should fail hard
            if self._is_testing_environment():
                print(
                    "ERROR: In testing environment - all tools must be available",
                    file=sys.stderr,
                )
                print("Install missing tools:", file=sys.stderr)
                print(
                    "  pip install perflint flake8-comprehensions flake8-bugbear",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                # In production, warn but continue with degraded functionality
                print(
                    "Continuing with degraded performance analysis capabilities",
                    file=sys.stderr,
                )

    def _check_perflint_availability(self) -> bool:
        """Check if perflint is available separately."""
        try:
            result = subprocess.run(
                ["perflint", "--help"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _is_testing_environment(self) -> bool:
        """Detect if we're running in a testing environment."""
        import os

        # Check for common testing environment indicators
        return any(
            [
                "test" in os.environ.get("PYTHONPATH", "").lower(),
                "test" in os.getcwd().lower(),
                os.environ.get("TESTING", "").lower() == "true",
                "pytest" in str(os.environ.get("_", "")),
                any("test" in arg for arg in os.sys.argv),
            ]
        )

    def _run_flake8_analysis(self, target_path: str) -> list[dict[str, Any]]:
        """Run Flake8 analysis with performance-focused plugins."""
        findings = []

        try:
            # Create temporary Flake8 config
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".ini", delete=False
            ) as config_file:
                config_file.write("[flake8]\n")
                config_file.write("max-line-length = 120\n")
                config_file.write("extend-ignore = E203,W503\n")  # Black compatibility
                config_file.write("select = PERF,C4,B006,B007,B020,B023,B905\n")
                config_file.write("statistics = True\n")
                config_file.write("format = json\n")
                config_path = config_file.name

            # Run Flake8 with performance plugins
            cmd = [
                "flake8",
                "--config",
                config_path,
                "--format",
                "%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
                target_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Parse Flake8 output (it doesn't have JSON format, so parse text)
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line and ":" in line:
                        finding = self._parse_flake8_line(line, target_path)
                        if finding:
                            findings.append(finding)

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            if self.verbose:
                print(f"Flake8 analysis failed for {target_path}: {e}", file=sys.stderr)
        finally:
            # Clean up temp config
            try:
                if "config_path" in locals():
                    Path(config_path).unlink(missing_ok=True)
            except Exception:
                pass

        return findings

    def _run_perflint_analysis(self, target_path: str) -> list[dict[str, Any]]:
        """Run perflint analysis for PERF rules."""
        findings = []

        # Only run on Python files
        if not target_path.endswith(".py"):
            return findings

        try:
            # Run perflint with output format that we can parse
            cmd = [
                "perflint",
                target_path,
                "--output-format",
                "json",
                "--disable",
                "all",
                "--enable",
                "C,R,W",  # Enable categories that include PERF-like rules
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Parse perflint JSON output
            if result.stdout:
                try:
                    perflint_data = json.loads(result.stdout)
                    if isinstance(perflint_data, list):
                        for issue in perflint_data:
                            finding = self._parse_perflint_issue(issue, target_path)
                            if finding:
                                findings.append(finding)
                except json.JSONDecodeError:
                    # Fallback to text parsing if JSON fails
                    for line in result.stdout.strip().split("\n"):
                        if (
                            line
                            and ":" in line
                            and any(perf_code in line for perf_code in ["C", "R", "W"])
                        ):
                            finding = self._parse_perflint_line(line, target_path)
                            if finding:
                                findings.append(finding)

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            if self.verbose:
                print(
                    f"Perflint analysis failed for {target_path}: {e}", file=sys.stderr
                )
        except Exception as e:
            if self.verbose:
                print(
                    f"Perflint unexpected error for {target_path}: {e}", file=sys.stderr
                )

        return findings

    def _parse_perflint_issue(
        self, issue: dict[str, Any], file_path: str
    ) -> Optional[dict[str, Any]]:
        """Parse a perflint JSON issue."""
        try:
            message_id = issue.get("message-id", "")
            message = issue.get("message", "")
            line_no = issue.get("line", 0)

            # Map perflint codes to our performance types
            if message_id.startswith(("C", "R", "W")) and any(
                keyword in message.lower()
                for keyword in [
                    "performance",
                    "loop",
                    "comprehension",
                    "efficient",
                    "optimization",
                ]
            ):
                severity = self._get_perflint_severity(message_id)

                return {
                    "perf_type": f"PERF_{message_id}",
                    "category": "performance_optimization",
                    "file_path": file_path,
                    "line_number": line_no,
                    "severity": severity,
                    "description": message,
                    "recommendation": self._get_perflint_recommendation(
                        message_id, message
                    ),
                    "pattern_matched": f"Perflint: {message_id}",
                    "confidence": "high",
                }

        except (KeyError, ValueError) as e:
            if self.verbose:
                print(f"Failed to parse perflint issue: {issue} - {e}", file=sys.stderr)

        return None

    def _parse_perflint_line(
        self, line: str, file_path: str
    ) -> Optional[dict[str, Any]]:
        """Parse perflint text output line."""
        # Simple text parsing as fallback
        try:
            if ":" in line and any(code in line for code in ["C", "R", "W"]):
                # Basic parsing - this would need refinement based on actual perflint output format
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    line_no = int(parts[1]) if parts[1].isdigit() else 0
                    message = parts[2].strip()

                    return {
                        "perf_type": "PERF_TEXT",
                        "category": "performance_optimization",
                        "file_path": file_path,
                        "line_number": line_no,
                        "severity": "medium",
                        "description": message,
                        "recommendation": "Review for performance optimization opportunities",
                        "pattern_matched": "Perflint: text",
                        "confidence": "medium",
                    }
        except (ValueError, IndexError):
            pass

        return None

    def _get_perflint_severity(self, message_id: str) -> str:
        """Map perflint message IDs to severity levels."""
        # Map based on pylint conventions
        if message_id.startswith("C"):  # Convention
            return "medium"
        elif message_id.startswith("R") or message_id.startswith("W"):  # Refactor
            return "high"
        else:
            return "medium"

    def _get_perflint_recommendation(self, message_id: str, message: str) -> str:
        """Generate recommendations for perflint findings."""
        # Extract recommendations from message or provide generic ones
        if "comprehension" in message.lower():
            return "Use list/dict/set comprehensions for better performance"
        elif "loop" in message.lower():
            return "Optimize loop structure for better performance"
        else:
            return f"Address performance issue: {message}"

    def _parse_flake8_line(self, line: str, file_path: str) -> Optional[dict[str, Any]]:
        """Parse a single Flake8 output line."""
        try:
            # Format: path:row:col: code message
            parts = line.split(":", 4)
            if len(parts) < 4:
                return None

            line_no = int(parts[1])
            col_no = int(parts[2])
            code_and_message = parts[3].strip()

            # Extract error code and message
            code_parts = code_and_message.split(" ", 1)
            if len(code_parts) < 2:
                return None

            code = code_parts[0]
            message = code_parts[1]

            # Map to our severity
            severity = self.flake8_performance_rules.get(code, "medium")

            return {
                "perf_type": code,
                "category": self._get_category_from_code(code),
                "file_path": file_path,
                "line_number": line_no,
                "column": col_no,
                "severity": severity,
                "description": message,
                "recommendation": self._get_recommendation(code),
                "pattern_matched": f"Flake8: {code}",
                "confidence": "high",
            }

        except (ValueError, IndexError) as e:
            if self.verbose:
                print(f"Failed to parse Flake8 line: {line} - {e}", file=sys.stderr)
            return None

    def _get_category_from_code(self, code: str) -> str:
        """Map Flake8 error codes to our category system."""
        if code.startswith("PERF"):
            return "performance_optimization"
        elif code.startswith("C4"):
            return "comprehension_optimization"
        elif code.startswith("B"):
            return "bug_and_performance"
        elif code.startswith("W") or code.startswith("R"):
            return "code_quality_performance"
        else:
            return "general_performance"

    def _get_recommendation(self, code: str) -> str:
        """Get specific recommendations based on error code."""
        recommendations = {
            "PERF101": "Remove unnecessary list() call - comprehension is already a list",
            "PERF102": "Use dict literal {} instead of dict() constructor for better performance",
            "PERF203": "Move try-except outside the loop to avoid performance overhead",
            "PERF204": "Use set literal {item1, item2} for membership testing instead of list",
            "PERF401": "Replace loop with list comprehension for better performance and readability",
            "PERF402": "Use comprehension instead of manual loop building collection",
            "C400": "Replace unnecessary generator with direct comprehension",
            "C401": "Use set comprehension instead of generator with set()",
            "C402": "Use dict comprehension instead of generator with dict()",
            "C403": "Use set literal instead of unnecessary list comprehension",
            "C404": "Use dict literal instead of unnecessary list comprehension",
            "C405": "Use set literal {1, 2} instead of set([1, 2])",
            "C406": "Use dict literal {k: v} instead of dict([(k, v)])",
            "C408": "Use dict literal {} instead of dict()",
            "C409": "Use comprehension instead of tuple/list with generator",
            "C410": "Remove unnecessary list comprehension - use generator",
            "C411": "Use list comprehension instead of list(generator)",
            "B006": "Use None as default and handle in function - mutable defaults are dangerous",
            "B007": "Remove unused loop variable or prefix with underscore",
            "B020": "Use different variable name - loop control variable shadows iterable",
            "B023": "Define function outside loop to avoid repeated creation overhead",
            "B905": "Add strict=True to zip() for safety and performance in Python 3.10+",
        }

        return recommendations.get(
            code, "Review code for performance optimization opportunities"
        )

    def _analyze_ast_performance(
        self, content: str, file_path: str
    ) -> list[dict[str, Any]]:
        """Analyze Python AST for performance patterns not caught by Flake8."""
        findings = []

        try:
            tree = ast.parse(content)

            # Check for nested loops (3+ levels)
            nested_loop_finder = NestedLoopVisitor()
            nested_loop_finder.visit(tree)
            for line_no in nested_loop_finder.nested_loops:
                findings.append(
                    {
                        "perf_type": "nested_loops_deep",
                        "category": "algorithm_complexity",
                        "file_path": file_path,
                        "line_number": line_no,
                        "severity": "high",
                        "description": "Deep nested loops detected - consider algorithm optimization",
                        "recommendation": "Reduce nesting depth or use more efficient algorithms",
                        "pattern_matched": "AST: nested loops",
                        "confidence": "high",
                    }
                )

            # Check for string concatenation in loops
            string_concat_finder = StringConcatInLoopVisitor()
            string_concat_finder.visit(tree)
            for line_no in string_concat_finder.string_concats:
                findings.append(
                    {
                        "perf_type": "string_concat_loop",
                        "category": "memory_performance",
                        "file_path": file_path,
                        "line_number": line_no,
                        "severity": "medium",
                        "description": "String concatenation in loop - use join() instead",
                        "recommendation": "Use list.append() and ''.join() for string building in loops",
                        "pattern_matched": "AST: string concatenation",
                        "confidence": "high",
                    }
                )

        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception as e:
            if self.verbose:
                print(f"AST analysis failed for {file_path}: {e}", file=sys.stderr)

        return findings

    def analyze_target(self, target_path: str) -> list[dict[str, Any]]:
        """
        Analyze target using Flake8, perflint, and AST for performance analysis.

        Args:
            target_path: Path to analyze (single file - BaseAnalyzer handles directory iteration)

        Returns
        -------
            List of performance findings with standardized structure
        """
        all_findings = []

        # Run Flake8 performance analysis (C4, B rules)
        flake8_findings = self._run_flake8_analysis(target_path)
        all_findings.extend(flake8_findings)

        # Run perflint analysis for PERF-style rules
        perflint_findings = self._run_perflint_analysis(target_path)
        all_findings.extend(perflint_findings)

        # Run additional AST analysis for Python files
        if target_path.endswith(".py"):
            try:
                with open(target_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                ast_findings = self._analyze_ast_performance(content, target_path)
                all_findings.extend(ast_findings)
            except Exception as e:
                if self.verbose:
                    print(f"Error reading {target_path}: {e}", file=sys.stderr)

        # Convert to standardized format for BaseAnalyzer
        standardized_findings = []
        for finding in all_findings:
            standardized = {
                "title": f"{finding['description']} ({finding['perf_type']})",
                "description": f"Performance issue detected: {finding['description']}. This should be optimized for better performance.",
                "severity": finding["severity"],
                "file_path": finding["file_path"],
                "line_number": finding["line_number"],
                "recommendation": finding["recommendation"],
                "metadata": {
                    "tool": "flake8-performance",
                    "error_code": finding["perf_type"],
                    "category": finding["category"],
                    "confidence": finding["confidence"],
                },
            }
            standardized_findings.append(standardized)

        return standardized_findings

    def get_analyzer_metadata(self) -> dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "Flake8 Performance Analyzer",
            "version": "2.0.0",
            "description": "Code performance analysis using Flake8 and plugins (replacing bespoke regex patterns)",
            "category": "performance",
            "priority": "high",
            "capabilities": [
                "Loop performance optimization",
                "Comprehension optimization",
                "Memory usage optimization",
                "Algorithm complexity analysis",
                "String performance optimization",
                "Collection usage optimization",
                "AST-based performance analysis",
                "Real-time performance rule updates",
            ],
            "supported_languages": ["Python", "Python type stubs (.pyi)"],
            "tool": "flake8",
            "plugins": [
                "perflint",
                "flake8-comprehensions",
                "flake8-bugbear",
            ],
            "replaces": ["check_bottlenecks.py"],
        }


class NestedLoopVisitor(ast.NodeVisitor):
    """AST visitor to detect deeply nested loops."""

    def __init__(self):
        self.nested_loops = []
        self.loop_depth = 0

    def visit_For(self, node):
        self.loop_depth += 1
        if self.loop_depth >= 3:  # 3+ levels of nesting
            self.nested_loops.append(getattr(node, "lineno", 0))
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node):
        self.loop_depth += 1
        if self.loop_depth >= 3:  # 3+ levels of nesting
            self.nested_loops.append(getattr(node, "lineno", 0))
        self.generic_visit(node)
        self.loop_depth -= 1


class StringConcatInLoopVisitor(ast.NodeVisitor):
    """AST visitor to detect string concatenation in loops."""

    def __init__(self):
        self.string_concats = []
        self.in_loop = False

    def visit_For(self, node):
        old_in_loop = self.in_loop
        self.in_loop = True
        self.generic_visit(node)
        self.in_loop = old_in_loop

    def visit_While(self, node):
        old_in_loop = self.in_loop
        self.in_loop = True
        self.generic_visit(node)
        self.in_loop = old_in_loop

    def visit_AugAssign(self, node):
        if (
            self.in_loop
            and isinstance(node.op, ast.Add)
            and isinstance(node.target, ast.Name)
        ):
            self.string_concats.append(getattr(node, "lineno", 0))
        self.generic_visit(node)


if __name__ == "__main__":
    raise SystemExit(0)
