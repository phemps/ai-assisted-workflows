#!/usr/bin/env python3
"""
Bottleneck Performance Analyzer - Performance Bottleneck Detection and Analysis
================================================================================

PURPOSE: Analyzes code for CPU/memory performance bottlenecks and resource usage patterns.
Part of the shared/analyzers/performance suite using BaseAnalyzer infrastructure.

APPROACH:
- CPU bottleneck detection (inefficient loops, blocking operations)
- Memory bottleneck analysis (leaks, large object creation)
- Algorithm complexity analysis (O(n²) patterns)
- Database bottleneck detection (N+1 queries)
- Concurrency bottleneck identification (race conditions, deadlocks)
- Python-specific performance patterns

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements performance-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns
"""

import re
import sys
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


class BottleneckAnalyzer(BaseAnalyzer):
    """Analyzes performance bottlenecks and resource usage patterns."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        # Create performance-specific configuration
        performance_config = config or AnalyzerConfig(
            code_extensions={
                ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".java",
                ".cs",
                ".cpp",
                ".c",
                ".h",
                ".hpp",
                ".go",
                ".rs",
                ".php",
                ".rb",
                ".swift",
                ".kt",
                ".scala",
                ".sql",
                ".vue",
                ".svelte",
                ".dart",
                ".clj",
                ".fs",
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
                "*.min.js",
                "*.min.css",
                "*.bundle.js",
                "*.chunk.js",
                ".d.ts",
            },
        )

        # Initialize base analyzer
        super().__init__("performance", performance_config)

        # Initialize bottleneck patterns
        self._init_cpu_patterns()
        self._init_memory_patterns()
        self._init_algorithm_patterns()
        self._init_database_patterns()
        self._init_concurrency_patterns()

        # Compile patterns for performance
        self._compiled_patterns = {}
        self._compile_all_patterns()

    def _init_cpu_patterns(self):
        """Initialize CPU bottleneck patterns."""
        self.cpu_patterns = {
            "inefficient_loops": {
                "indicators": [
                    r"for\s+.*in\s+range\(len\(",
                    r"while\s+.*:\s*\n.*for\s+.*:",
                    r"for\s+.*:\s*\n.*for\s+.*:\s*\n.*for\s+.*:",  # Triple nested loops
                    r"forEach\(.*forEach\(.*forEach\(",
                    r"map\(.*map\(.*map\(",
                ],
                "severity": "high",
                "description": "Inefficient nested loops causing CPU bottlenecks",
            },
            "redundant_computations": {
                "indicators": [
                    r"for\s+.*:\s*\n.*len\(",
                    r"while\s+.*len\(",
                    r"sort\(.*\).*sort\(",
                    r"reverse\(.*\).*reverse\(",
                    r"Math\.(sin|cos|tan|sqrt)\(.*\).*Math\.(sin|cos|tan|sqrt)\(",
                ],
                "severity": "medium",
                "description": "Redundant computations in loops",
            },
            "expensive_operations_in_loops": {
                "indicators": [
                    r"for\s+.*:\s*\n.*re\.compile\(",
                    r"while\s+.*:\s*\n.*datetime\.now\(",
                    r"for\s+.*:\s*\n.*json\.loads\(",
                    r"forEach\(.*new\s+Date\(",
                    r"map\(.*JSON\.parse\(",
                ],
                "severity": "high",
                "description": "Expensive operations inside loops",
            },
            "blocking_io_operations": {
                "indicators": [
                    r"requests\.get\((?!.*async)",
                    r"urllib\.request\.urlopen\(",
                    r'open\(.*[\'"]r[\'"].*\)(?!.*async)',
                    r"file\.read\(\)(?!.*async)",
                    r"fetch\(.*\)(?!.*\.then|await)",
                ],
                "severity": "high",
                "description": "Blocking I/O operations on main thread",
            },
        }

    def _init_memory_patterns(self):
        """Initialize memory bottleneck patterns."""
        self.memory_patterns = {
            "memory_leaks": {
                "indicators": [
                    r"global\s+\w+\s*=\s*\[\]",
                    r"cache\s*=\s*\{\}",
                    r"setInterval\(.*(?!.*clearInterval)",
                    r"addEventListener\(.*(?!.*removeEventListener)",
                    r"new\s+.*Observer\(.*(?!.*disconnect)",
                ],
                "severity": "critical",
                "description": "Potential memory leaks from uncleaned resources",
            },
            "large_object_creation": {
                "indicators": [
                    r"new\s+Array\(\s*\d{6,}\s*\)",
                    r"\[\s*\]\s*\*\s*\d{6,}",
                    r"Buffer\.alloc\(\s*\d{6,}\s*\)",
                    r"new\s+.*\(\s*\d{6,}\s*\)",
                    r"range\(\s*\d{6,}\s*\)",
                ],
                "severity": "medium",
                "description": "Large object creation that may cause memory pressure",
            },
            "inefficient_data_structures": {
                "indicators": [
                    r"for\s+.*in\s+.*:\s*\n.*list\.append\(",
                    r"while\s+.*:\s*\n.*dict\[.*\]\s*=",
                    r"for\s+.*:\s*\n.*array\.push\(",
                    r"forEach\(.*array\.push\(",
                    r"map\(.*\{\.\.\.",
                ],
                "severity": "medium",
                "description": "Inefficient data structure usage",
            },
            "string_concatenation_loops": {
                "indicators": [
                    r'for\s+.*:\s*\n.*\+\s*[\'"]',
                    r'while\s+.*:\s*\n.*\+=\s*[\'"]',
                    r"forEach\(.*\+=.*string",
                    r'map\(.*\+.*[\'"`]',
                ],
                "severity": "medium",
                "description": "String concatenation in loops causing memory allocations",
            },
        }

    def _init_algorithm_patterns(self):
        """Initialize algorithm complexity patterns."""
        self.algorithm_patterns = {
            "quadratic_complexity": {
                "indicators": [
                    r"for\s+.*:\s*\n.*for\s+.*:\s*\n.*if\s+.*==",
                    r"forEach\(.*forEach\(",
                    r"for\s+.*in\s+.*:\s*\n.*for\s+.*in\s+.*:",
                    r"while\s+.*:\s*\n.*while\s+.*:",
                ],
                "severity": "high",
                "description": "O(n²) algorithm complexity",
            },
            "inefficient_search": {
                "indicators": [
                    r"for\s+.*in\s+.*:\s*\n.*if\s+.*==.*break",
                    r"while\s+.*:\s*\n.*if\s+.*==.*return",
                    r"indexOf\(.*\)\s*!==\s*-1",
                    r"includes\(.*\)",
                ],
                "severity": "medium",
                "description": "Inefficient linear search where better alternatives exist",
            },
            "repeated_sorting": {
                "indicators": [
                    r"for\s+.*:\s*\n.*sort\(",
                    r"while\s+.*:\s*\n.*sort\(",
                    r"forEach\(.*sort\(",
                    r"map\(.*sort\(",
                ],
                "severity": "medium",
                "description": "Repeated sorting operations",
            },
        }

    def _init_database_patterns(self):
        """Initialize database bottleneck patterns."""
        self.database_patterns = {
            "n_plus_one_queries": {
                "indicators": [
                    r"for\s+.*:\s*\n.*\.get\(",
                    r"for\s+.*:\s*\n.*\.find\(",
                    r"forEach\(.*\.query\(",
                    r"map\(.*\.execute\(",
                    r"for\s+.*:\s*\n.*SELECT",
                ],
                "severity": "critical",
                "description": "N+1 query problem",
            },
            "missing_pagination": {
                "indicators": [
                    r"\.all\(\)",
                    r"SELECT\s+\*\s+FROM.*(?!LIMIT)",
                    r"find\(\{\}\)(?!\.limit)",
                    r"query\(.*\)(?!\.limit)",
                ],
                "severity": "medium",
                "description": "Queries without pagination",
            },
            "inefficient_queries": {
                "indicators": [
                    r"SELECT\s+\*\s+FROM",
                    r'WHERE.*LIKE\s+[\'"]%.*%[\'"]',
                    r"ORDER\s+BY.*(?!.*INDEX)",
                    r"JOIN.*(?!.*INDEX)",
                ],
                "severity": "medium",
                "description": "Potentially inefficient database queries",
            },
        }

    def _init_concurrency_patterns(self):
        """Initialize concurrency bottleneck patterns."""
        self.concurrency_patterns = {
            "race_conditions": {
                "indicators": [
                    r"global\s+\w+\s*=.*(?!.*lock)",
                    r"shared.*variable.*(?!.*mutex)",
                    r"counter\s*\+=.*(?!.*atomic)",
                    r"threading.*(?!.*Lock)",
                ],
                "severity": "high",
                "description": "Potential race conditions in concurrent code",
            },
            "deadlock_risk": {
                "indicators": [
                    r"lock.*lock",
                    r"acquire.*acquire",
                    r"synchronized.*synchronized",
                    r"mutex.*mutex",
                ],
                "severity": "high",
                "description": "Potential deadlock from multiple locks",
            },
            "thread_pool_exhaustion": {
                "indicators": [
                    r"ThreadPoolExecutor\(.*\d+.*\)",
                    r"thread.*pool.*size.*\d+",
                    r"concurrent\.futures.*max_workers=\d+",
                    r"asyncio.*Semaphore\(\d+\)",
                ],
                "severity": "medium",
                "description": "Fixed thread pool sizes that may cause exhaustion",
            },
        }

    def _compile_all_patterns(self):
        """Compile all regex patterns for performance."""
        pattern_groups = [
            self.cpu_patterns,
            self.memory_patterns,
            self.algorithm_patterns,
            self.database_patterns,
            self.concurrency_patterns,
        ]

        for patterns in pattern_groups:
            for bottleneck_type, config in patterns.items():
                self._compiled_patterns[bottleneck_type] = [
                    re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                    for pattern in config["indicators"]
                ]

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "Bottleneck Performance Analyzer",
            "version": "2.0.0",
            "description": "Analyzes performance bottlenecks and resource usage patterns",
            "category": "performance",
            "priority": "high",
            "capabilities": [
                "CPU bottleneck detection",
                "Memory leak analysis",
                "Algorithm complexity analysis",
                "Database N+1 query detection",
                "Concurrency issue detection",
                "Python AST analysis",
                "Resource usage pattern analysis",
                "Performance score calculation",
            ],
            "supported_formats": list(self.config.code_extensions),
            "patterns_checked": len(self._compiled_patterns),
        }

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file for performance bottlenecks.

        Args:
            target_path: Path to file to analyze

        Returns:
            List of findings with standardized structure
        """
        all_findings = []
        file_path = Path(target_path)

        # Skip files that are too large
        if file_path.stat().st_size > 2 * 1024 * 1024:  # Skip files > 2MB
            return all_findings

        findings = self._scan_file_for_bottlenecks(file_path)

        # Convert to standardized finding format
        for finding in findings:
            # Create detailed title
            title = f"{finding['description']} ({finding['bottleneck_type'].replace('_', ' ').title()})"

            # Create comprehensive description
            description = (
                f"{finding['description']} detected in {file_path.name} at line {finding['line_number']}. "
                f"Category: {finding['category'].replace('_', ' ').title()}. "
                f"This performance bottleneck could impact {finding['performance_impact'].replace('_', ' ')} and overall system performance."
            )

            standardized = {
                "title": title,
                "description": description,
                "severity": finding["severity"],
                "file_path": finding["file_path"],
                "line_number": finding["line_number"],
                "recommendation": finding["recommendation"],
                "metadata": {
                    "bottleneck_type": finding["bottleneck_type"],
                    "category": finding["category"],
                    "performance_impact": finding["performance_impact"],
                    "line_content": finding["context"],
                    "confidence": "high",
                },
            }
            all_findings.append(standardized)

        return all_findings

    def _scan_file_for_bottlenecks(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze performance bottlenecks in a single file."""
        findings = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            # Check all bottleneck patterns
            pattern_groups = [
                ("cpu", self.cpu_patterns, "cpu_performance"),
                ("memory", self.memory_patterns, "memory_usage"),
                ("algorithm", self.algorithm_patterns, "algorithm_efficiency"),
                ("database", self.database_patterns, "database_performance"),
                ("concurrency", self.concurrency_patterns, "concurrency_performance"),
            ]

            for category, patterns, performance_impact in pattern_groups:
                for bottleneck_type, config in patterns.items():
                    compiled_patterns = self._compiled_patterns.get(bottleneck_type, [])

                    for pattern in compiled_patterns:
                        for match in pattern.finditer(content):
                            # Calculate line number
                            line_number = content[: match.start()].count("\n") + 1

                            # Get the matched line
                            line_content = (
                                lines[line_number - 1].strip()
                                if line_number <= len(lines)
                                else ""
                            )

                            # Skip false positives
                            if self._is_false_positive(
                                line_content, bottleneck_type, category
                            ):
                                continue

                            findings.append(
                                {
                                    "file_path": str(file_path),
                                    "line_number": line_number,
                                    "bottleneck_type": bottleneck_type,
                                    "severity": config["severity"],
                                    "description": config["description"],
                                    "recommendation": self._get_bottleneck_recommendation(
                                        bottleneck_type
                                    ),
                                    "context": line_content[
                                        :150
                                    ],  # Truncate long lines
                                    "category": category,
                                    "performance_impact": performance_impact,
                                }
                            )

            # Additional Python-specific analysis
            if str(file_path).endswith(".py"):
                findings.extend(
                    self._analyze_python_bottlenecks(content, lines, str(file_path))
                )

        except Exception as e:
            # Log but continue - file might be binary or inaccessible
            if self.verbose:
                print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)

        return findings

    def _is_false_positive(
        self, line_content: str, bottleneck_type: str, category: str
    ) -> bool:
        """Check if a detected bottleneck is likely a false positive."""
        line_lower = line_content.lower()

        # Skip comments
        comment_indicators = ["//", "#", "/*", "*", "<!--", "'''", '"""']
        for indicator in comment_indicators:
            if line_content.strip().startswith(indicator):
                return True

        # Skip test/example code
        if any(
            word in line_lower
            for word in ["test", "example", "sample", "demo", "mock", "fixture"]
        ):
            return True

        # Skip documentation
        if any(
            word in line_lower
            for word in ["@param", "@return", "docstring", "@example"]
        ):
            return True

        # Category-specific false positive checks
        if category == "cpu" and any(
            word in line_lower for word in ["async", "await", "thread", "pool"]
        ):
            return True  # Already optimized

        if category == "memory" and any(
            word in line_lower for word in ["cleanup", "dispose", "close", "free"]
        ):
            return True  # Has cleanup

        if category == "database" and any(
            word in line_lower for word in ["batch", "bulk", "limit", "pagination"]
        ):
            return True  # Already optimized

        return False

    def _analyze_python_bottlenecks(
        self, content: str, lines: List[str], file_path: str
    ) -> List[Dict[str, Any]]:
        """Analyze Python-specific performance bottlenecks."""
        findings = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Check for global variables in loops
                if isinstance(node, (ast.For, ast.While)):
                    loop_line = getattr(node, "lineno", 0)
                    for child in ast.walk(node):
                        if isinstance(child, ast.Global):
                            findings.append(
                                {
                                    "file_path": file_path,
                                    "line_number": loop_line,
                                    "bottleneck_type": "python_global_in_loop",
                                    "severity": "medium",
                                    "description": "Global variable access in loop may impact performance",
                                    "recommendation": self._get_bottleneck_recommendation(
                                        "python_global_in_loop"
                                    ),
                                    "context": (
                                        lines[loop_line - 1].strip()
                                        if loop_line <= len(lines)
                                        else ""
                                    ),
                                    "category": "python",
                                    "performance_impact": "cpu_performance",
                                }
                            )

                # Check for list comprehensions with side effects
                if isinstance(node, ast.ListComp):
                    for generator in node.generators:
                        for if_clause in generator.ifs:
                            if isinstance(if_clause, ast.Call):
                                line_num = getattr(node, "lineno", 0)
                                findings.append(
                                    {
                                        "file_path": file_path,
                                        "line_number": line_num,
                                        "bottleneck_type": "python_complex_comprehension",
                                        "severity": "low",
                                        "description": "Complex list comprehension may impact performance",
                                        "recommendation": self._get_bottleneck_recommendation(
                                            "python_complex_comprehension"
                                        ),
                                        "context": (
                                            lines[line_num - 1].strip()
                                            if line_num <= len(lines)
                                            else ""
                                        ),
                                        "category": "python",
                                        "performance_impact": "cpu_performance",
                                    }
                                )

        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception as e:
            if self.verbose:
                print(
                    f"Warning: Python AST analysis failed for {file_path}: {e}",
                    file=sys.stderr,
                )

        return findings

    def _get_bottleneck_recommendation(self, bottleneck_type: str) -> str:
        """Get specific recommendations for performance bottlenecks."""
        recommendations = {
            "cpu_inefficient_loops": "Optimize nested loops with better algorithms or caching",
            "cpu_redundant_computations": "Cache expensive computations outside loops",
            "cpu_expensive_operations_in_loops": "Move expensive operations outside loops",
            "cpu_blocking_io_operations": "Use async/await or threading for I/O operations",
            "memory_memory_leaks": "Implement proper cleanup of resources and event listeners",
            "memory_large_object_creation": "Use streaming or chunked processing for large data",
            "memory_inefficient_data_structures": "Use appropriate data structures (sets, deques, etc.)",
            "memory_string_concatenation_loops": "Use join() or StringBuilder for string concatenation",
            "algorithm_quadratic_complexity": "Replace with O(n log n) or O(n) algorithms",
            "algorithm_inefficient_search": "Use hash tables, binary search, or indexed lookups",
            "algorithm_repeated_sorting": "Sort once and maintain order, or use appropriate data structures",
            "database_n_plus_one_queries": "Use eager loading, joins, or batch queries",
            "database_missing_pagination": "Implement LIMIT/OFFSET or cursor-based pagination",
            "database_inefficient_queries": "Add indexes, optimize WHERE clauses, avoid SELECT *",
            "concurrency_race_conditions": "Use locks, atomic operations, or thread-safe data structures",
            "concurrency_deadlock_risk": "Implement lock ordering or use lock-free algorithms",
            "concurrency_thread_pool_exhaustion": "Use dynamic thread pools or rate limiting",
            "python_global_in_loop": "Use local variables or pass globals as parameters",
            "python_complex_comprehension": "Break complex comprehensions into simpler operations",
        }
        return recommendations.get(
            bottleneck_type, "Review code for performance optimization opportunities"
        )


def main():
    """Main entry point for command-line usage."""
    analyzer = BottleneckAnalyzer()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
