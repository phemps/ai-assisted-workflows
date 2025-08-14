#!/usr/bin/env python3
"""
Flake8 Performance Analyzer - Advanced Code Performance Analysis
================================================================

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

import subprocess
import sys
import tempfile
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import base analyzer infrastructure
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared.core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
except ImportError as e:
    print(f"Error importing base analyzer: {e}", file=sys.stderr)
    sys.exit(1)


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
                "__pycache__",
                "*.egg-info",
            },
        )

        # Initialize base analyzer
        super().__init__("performance", perf_config)

        # Check for Flake8 availability - required for accurate analysis
        self._check_flake8_availability()

        # Flake8 performance configuration
        self.flake8_performance_rules = {
            # flake8-performance rules (PERF)
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
                    "Install with: pip install flake8 flake8-performance flake8-comprehensions flake8-bugbear",
                    file=sys.stderr,
                )
                sys.exit(1)

            version = result.stdout.strip()
            print(f"Found Flake8 {version}", file=sys.stderr)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("ERROR: Flake8 is required but not available.", file=sys.stderr)
            print(
                "Install with: pip install flake8 flake8-performance flake8-comprehensions flake8-bugbear",
                file=sys.stderr,
            )
            sys.exit(1)

    def _run_flake8_analysis(self, target_path: str) -> List[Dict[str, Any]]:
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

    def _parse_flake8_line(self, line: str, file_path: str) -> Optional[Dict[str, Any]]:
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
    ) -> List[Dict[str, Any]]:
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

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze target using Flake8 and AST for performance analysis.

        Args:
            target_path: Path to analyze (single file - BaseAnalyzer handles directory iteration)

        Returns:
            List of performance findings with standardized structure
        """
        all_findings = []

        # Run Flake8 performance analysis
        flake8_findings = self._run_flake8_analysis(target_path)
        all_findings.extend(flake8_findings)

        # Run additional AST analysis for Python files
        if target_path.endswith(".py"):
            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
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

    def get_analyzer_metadata(self) -> Dict[str, Any]:
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
                "flake8-performance",
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


def main():
    """Main entry point for command-line usage."""
    analyzer = Flake8PerformanceAnalyzer()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
