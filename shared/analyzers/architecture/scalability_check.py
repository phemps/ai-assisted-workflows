#!/usr/bin/env python3
"""
Scalability Analysis Analyzer - Code Scalability Assessment
==========================================================

PURPOSE: Analyzes code for potential scalability bottlenecks and architectural constraints.
Part of the shared/analyzers/architecture suite using BaseAnalyzer infrastructure.

APPROACH:
- Database scalability patterns (N+1 queries, missing indexes, unbounded result sets)
- Performance bottleneck detection (synchronous I/O, nested loops, inefficient algorithms)
- Concurrency issue identification (thread safety, blocking operations, resource contention)
- Architecture scalability analysis (tight coupling, hardcoded config, SRP violations)
- Python AST analysis for algorithmic complexity detection

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements scalability-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns
"""

import re
import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import base analyzer (package root must be on PYTHONPATH)
from core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig


class ScalabilityAnalyzer(BaseAnalyzer):
    """Analyzes code for scalability bottlenecks and architectural constraints."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        # Create scalability-specific configuration
        scalability_config = config or AnalyzerConfig(
            code_extensions={
                ".py",
                ".js",
                ".jsx",
                ".ts",
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
            },
            skip_patterns={
                "node_modules",
                ".git",
                "__pycache__",
                ".pytest_cache",
                "build",
                "dist",
                ".next",
                ".nuxt",
                "coverage",
                "venv",
                "env",
                ".env",
                "vendor",
                "logs",
                "target",
                ".vscode",
                ".idea",
                "*.min.js",
                "*.bundle.js",
                "*.test.*",
                "*/tests/*",
            },
        )

        # Initialize base analyzer
        super().__init__("architecture", scalability_config)

        # Initialize scalability pattern definitions
        self._init_scalability_patterns()

    def _init_scalability_patterns(self):
        """Initialize all scalability pattern definitions."""
        # Database scalability patterns (more specific)
        self.db_patterns = {
            "n_plus_one": {
                "indicators": [
                    # Only flag when loops explicitly contain database operations
                    r"for\s+\w+\s+in\s+.*\.all\(\).*:\s*\n.*\.(get|find|query|execute)\(",
                    r"for\s+\w+\s+in\s+.*:\s*\n.*\s+.*\.(get|find|query)\(.*\w+\.id",
                    r"forEach\([^}]*=>\s*[^}]*\.(get|find|query)\(.*\w+\.id",
                    r"map\([^}]*=>\s*[^}]*\.(get|find|query)\(",
                ],
                "severity": "high",
                "description": "Potential N+1 query problem",
            },
            "missing_indexes": {
                "indicators": [
                    # Only flag SQL queries without checking for existing indexes
                    r"SELECT.*FROM\s+\w+\s+WHERE\s+\w+\s*=.*(?!.*INDEX|.*INDEXED)",
                    r"ORDER\s+BY\s+\w+.*(?!.*INDEX)",
                    # Only flag ORM queries that look like they need indexing
                    r"\.filter\(\w+__exact\s*=|\.filter\(\w+\s*=.*\)\.order_by\(",
                ],
                "severity": "medium",
                "description": "Query without explicit index consideration",
            },
            "large_result_sets": {
                "indicators": [
                    # Only flag queries explicitly getting all records without limits
                    r"SELECT\s+\*\s+FROM\s+\w+(?!.*LIMIT|.*WHERE|.*TOP)",
                    r"\.all\(\)(?!.*\[:|\[:\d+\])",  # .all() without slicing
                    r"fetchall\(\)(?!.*WHERE)",  # fetchall without WHERE
                    r"find\(\{\}\)(?!.*limit|.*skip)",  # MongoDB find all without limits
                ],
                "severity": "medium",
                "description": "Potentially unbounded result set",
            },
            "no_pagination": {
                "indicators": [
                    # Only flag queries that should have pagination
                    r"SELECT.*FROM.*users.*(?!.*LIMIT|.*OFFSET)",
                    r"SELECT.*FROM.*orders.*(?!.*LIMIT|.*OFFSET)",
                    r"SELECT.*FROM.*products.*(?!.*LIMIT|.*OFFSET)",
                    r"find\(\)\.count\(\)\s*>\s*1000",  # Large counts without pagination
                ],
                "severity": "medium",
                "description": "Query without pagination",
            },
        }

        # Performance bottleneck patterns
        self.performance_patterns = {
            "synchronous_io": {
                "indicators": [
                    r"requests\.get\(",
                    r"urllib\.request\.",
                    r"httplib\.",
                    r'open\(.*[\'"]r[\'"]',
                    r"sleep\(",
                    r"time\.sleep\(",
                ],
                "severity": "high",
                "description": "Synchronous I/O operation",
            },
            "nested_loops": {
                "indicators": [
                    r"for\s+.*:\s*\n.*for\s+.*:\s*\n.*for\s+",  # Triple nested
                    r"while\s+.*:\s*\n.*while\s+.*:\s*\n.*while\s+",
                ],
                "severity": "high",
                "description": "Deep nested loops (O(n³) or worse)",
            },
            "inefficient_algorithms": {
                "indicators": [
                    r"\.sort\(\).*\.sort\(\)",  # Multiple sorts
                    r"in\s+range\(len\(",  # Inefficient iteration
                    r"list\(.*\)\[0\]",  # Inefficient first element access
                ],
                "severity": "medium",
                "description": "Potentially inefficient algorithm",
            },
            "memory_leaks": {
                "indicators": [
                    r"global\s+\w+.*=.*\[\]",  # Global collections
                    r"while\s+True:.*append\(",  # Unbounded growth
                    r"cache\s*=\s*\{\}",  # Unbounded cache
                ],
                "severity": "high",
                "description": "Potential memory leak",
            },
        }

        # Concurrency and scaling patterns
        self.concurrency_patterns = {
            "thread_safety": {
                "indicators": [
                    r"global\s+\w+",
                    r"class\s+\w+.*:\s*\n.*\w+\s*=\s*\[\]",  # Shared mutable state
                    r"threading\.Thread",
                    r"multiprocessing\.",
                ],
                "severity": "high",
                "description": "Potential thread safety issue",
            },
            "blocking_operations": {
                "indicators": [
                    r"\.join\(\)",
                    r"\.wait\(\)",
                    r"input\(\)",
                    r"raw_input\(\)",
                    r"time\.sleep\(",
                ],
                "severity": "medium",
                "description": "Blocking operation that may affect scalability",
            },
            "resource_contention": {
                "indicators": [
                    r"lock\s*=\s*",
                    r"Lock\(\)",
                    r"RLock\(\)",
                    r"Semaphore\(",
                    r"mutex",
                ],
                "severity": "medium",
                "description": "Resource locking that may limit scalability",
            },
        }

        # Architecture scalability patterns (refined to reduce false positives)
        self.architecture_patterns = {
            "tight_coupling": {
                "indicators": [
                    # Only flag when there are multiple deep imports in same file indicating tight coupling
                    r"(?:import|from)\s+\w+\.\w+\.\w+\.\w+.*\n(?:.*\n){0,5}(?:import|from)\s+\w+\.\w+\.\w+\.\w+",
                    # Deep method chaining with mutations (indicates tight coupling)
                    r"\w+\.\w+\.\w+\.\w+\.\w+\(",
                    # Direct access to internal properties across modules
                    r"\w+\.\w+\._\w+\.\w+\(",
                ],
                "severity": "medium",
                "description": "Tight coupling that may hinder scaling",
            },
            "hardcoded_config": {
                "indicators": [
                    # More specific hardcoded config patterns
                    r'host\s*=\s*[\'"](?:localhost|127\.0\.0\.1)[\'"]',
                    r"port\s*=\s*(?:3000|8080|5432|3306)(?!\s*\+|\s*\*)",  # Common hardcoded ports
                    r'password\s*=\s*[\'"][^\'"]{6,}[\'"]',  # Actual passwords, not empty
                    r'(?:DATABASE_|DB_)URL\s*=\s*[\'"](?:postgres|mysql|mongodb)://[^\'\"]*[\'"]',
                    r'api_key\s*=\s*[\'"][a-zA-Z0-9]{20,}[\'"]',  # Actual API keys
                ],
                "severity": "high",
                "description": "Hardcoded configuration limits scalability",
            },
            "single_responsibility": {
                "indicators": [
                    # Only flag extremely large classes/methods that clearly violate SRP
                    r"class\s+\w+.*:\s*(?:\n.*){100,}",  # Very large classes (100+ lines)
                    r"def\s+\w+.*:\s*(?:\n.*){50,}",  # Large methods (50+ lines)
                    r"def\s+\w+.*(?:and|or).*(?:and|or).*\(",  # Method names with multiple conjunctions
                ],
                "severity": "medium",
                "description": "Violation of single responsibility principle",
            },
        }

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "Scalability Analysis Analyzer",
            "version": "2.0.0",
            "description": "Analyzes code for potential scalability bottlenecks and architectural constraints",
            "category": "architecture",
            "priority": "high",
            "capabilities": [
                "Database scalability patterns (N+1 queries, missing indexes)",
                "Performance bottleneck detection (synchronous I/O, nested loops)",
                "Concurrency issue identification (thread safety, resource contention)",
                "Architecture scalability analysis (coupling, configuration)",
                "Python AST analysis for algorithmic complexity",
                "Multi-language scalability pattern recognition",
                "Scalability scoring and prioritized recommendations",
            ],
            "supported_formats": list(self.config.code_extensions),
            "pattern_categories": {
                "database_patterns": len(self.db_patterns),
                "performance_patterns": len(self.performance_patterns),
                "concurrency_patterns": len(self.concurrency_patterns),
                "architecture_patterns": len(self.architecture_patterns),
            },
        }

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file for scalability bottlenecks.

        Args:
            target_path: Path to file to analyze

        Returns:
            List of findings with standardized structure
        """
        all_findings = []
        file_path = Path(target_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            # Check database scalability patterns
            findings = self._check_scalability_patterns(
                content, lines, str(file_path), self.db_patterns, "database"
            )
            all_findings.extend(findings)

            # Check performance patterns
            findings = self._check_scalability_patterns(
                content, lines, str(file_path), self.performance_patterns, "performance"
            )
            all_findings.extend(findings)

            # Check concurrency patterns
            findings = self._check_scalability_patterns(
                content, lines, str(file_path), self.concurrency_patterns, "concurrency"
            )
            all_findings.extend(findings)

            # Check architecture patterns
            findings = self._check_scalability_patterns(
                content,
                lines,
                str(file_path),
                self.architecture_patterns,
                "architecture",
            )
            all_findings.extend(findings)

            # Additional Python complexity analysis
            if file_path.suffix == ".py":
                complexity_findings = self._analyze_python_complexity(
                    content, lines, str(file_path)
                )
                all_findings.extend(complexity_findings)

        except Exception as e:
            all_findings.append(
                {
                    "title": "File Analysis Error",
                    "description": f"Could not analyze file: {str(e)}",
                    "severity": "low",
                    "file_path": str(file_path),
                    "line_number": 0,
                    "recommendation": "Check file encoding and permissions.",
                    "metadata": {"error_type": "file_read_error", "confidence": "high"},
                }
            )

        return all_findings

    def _check_scalability_patterns(
        self,
        content: str,
        lines: List[str],
        file_path: str,
        pattern_dict: Dict,
        category: str,
    ) -> List[Dict[str, Any]]:
        """Check for specific scalability patterns in file content with context validation."""
        findings = []

        # Get Lizard metrics for context
        lizard_metrics = self._get_lizard_metrics(file_path)

        for pattern_name, pattern_info in pattern_dict.items():
            for indicator in pattern_info["indicators"]:
                matches = re.finditer(indicator, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    context = (
                        lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    )

                    # Context validation - only flag if there's real complexity
                    if self._should_flag_scalability_issue(
                        pattern_name, context, lizard_metrics, content
                    ):
                        confidence = self._calculate_confidence(
                            pattern_name, context, lizard_metrics
                        )

                        findings.append(
                            {
                                "title": f"Scalability Issue: {pattern_name.replace('_', ' ').title()}",
                                "description": f"{pattern_info['description']} ({pattern_name})",
                                "severity": pattern_info["severity"],
                                "file_path": file_path,
                                "line_number": line_num,
                                "recommendation": self._get_recommendation(
                                    pattern_name, category
                                ),
                                "metadata": {
                                    "scalability_category": category,
                                    "pattern_name": pattern_name,
                                    "context": context,
                                    "confidence": confidence,
                                    "lizard_ccn": lizard_metrics.get("max_ccn", 0),
                                },
                            }
                        )

        return findings

    def _get_lizard_metrics(self, file_path: str) -> Dict[str, Any]:
        """Get Lizard complexity metrics for the file."""
        try:
            result = subprocess.run(
                ["lizard", "-C", "999", "-L", "999", "-a", "999", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse lizard output for metrics
                lines = result.stdout.strip().split("\n")
                metrics = {
                    "functions": [],
                    "avg_ccn": 0,
                    "max_ccn": 0,
                    "total_functions": 0,
                }

                for line in lines:
                    if (
                        line.strip()
                        and not line.startswith("=")
                        and not line.startswith("NLOC")
                    ):
                        parts = line.split()
                        if len(parts) >= 4 and parts[0].isdigit():
                            try:
                                ccn = int(parts[0])
                                nloc = int(parts[1])

                                metrics["functions"].append({"ccn": ccn, "nloc": nloc})
                                metrics["max_ccn"] = max(metrics["max_ccn"], ccn)
                                metrics["total_functions"] += 1
                            except (ValueError, IndexError):
                                continue

                if metrics["total_functions"] > 0:
                    metrics["avg_ccn"] = (
                        sum(f["ccn"] for f in metrics["functions"])
                        / metrics["total_functions"]
                    )

                return metrics

        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ):
            pass

        return {"functions": [], "avg_ccn": 0, "max_ccn": 0, "total_functions": 0}

    def _should_flag_scalability_issue(
        self, pattern_name: str, context: str, lizard_metrics: Dict, content: str
    ) -> bool:
        """Determine if a scalability issue should be flagged based on context."""

        # Skip if in test files, specs, or configuration files
        context_lower = context.lower()
        if any(
            marker in context_lower
            for marker in ["test", "spec", "mock", "fixture", "stub", "config", "setup"]
        ):
            return False

        # Only flag database patterns if they're in complex functions with real database usage
        if pattern_name in [
            "n_plus_one",
            "missing_indexes",
            "large_result_sets",
            "no_pagination",
        ]:
            # Require higher complexity AND evidence of actual database usage
            has_db_context = any(
                db_term in content.lower()
                for db_term in [
                    "select",
                    "insert",
                    "update",
                    "delete",
                    "query",
                    "orm",
                    "model",
                    "database",
                    "table",
                    "sequelize",
                    "mongoose",
                    "prisma",
                ]
            )
            return (
                lizard_metrics.get("max_ccn", 0) > 10
                and has_db_context
                and lizard_metrics.get("total_functions", 0) > 2
            )

        # Only flag synchronous I/O if in performance-critical context
        if pattern_name == "synchronous_io":
            # Require explicit loop context AND complex function
            has_loop = any(
                loop in context_lower for loop in ["for ", "while ", "foreach"]
            )
            return (
                has_loop
                and lizard_metrics.get("max_ccn", 0) > 12
                and "await" not in context_lower
            )  # Not if already using async

        # Only flag hardcoded config if it's in actual configuration context
        if pattern_name == "hardcoded_config":
            has_config_context = any(
                term in content.lower()
                for term in ["config", "environment", "settings", "connection"]
            )
            return lizard_metrics.get("total_functions", 0) > 3 and has_config_context

        # Only flag memory leaks in substantial, long-running code
        if pattern_name == "memory_leaks":
            return (
                lizard_metrics.get("total_functions", 0) > 5
                and lizard_metrics.get("max_ccn", 0) > 8
            )

        # Only flag tight coupling in files with significant complexity
        if pattern_name == "tight_coupling":
            return (
                lizard_metrics.get("total_functions", 0) > 4
                and lizard_metrics.get("max_ccn", 0) > 10
            )

        # Only flag thread safety in concurrent code
        if pattern_name == "thread_safety":
            has_concurrent_context = any(
                term in content.lower()
                for term in [
                    "thread",
                    "async",
                    "concurrent",
                    "parallel",
                    "multiprocess",
                ]
            )
            return lizard_metrics.get("max_ccn", 0) > 8 and has_concurrent_context

        # Default: only flag in complex, substantial files
        return (
            lizard_metrics.get("total_functions", 0) > 3
            and lizard_metrics.get("max_ccn", 0) > 8
        )

    def _calculate_confidence(
        self, pattern_name: str, context: str, lizard_metrics: Dict
    ) -> str:
        """Calculate confidence level for the finding."""
        max_ccn = lizard_metrics.get("max_ccn", 0)

        # High confidence for complex functions with scalability patterns
        if max_ccn > 15:
            return "high"
        elif max_ccn > 8:
            return "medium"
        else:
            return "low"

    def _analyze_python_complexity(
        self, content: str, lines: List[str], file_path: str
    ) -> List[Dict[str, Any]]:
        """Analyze Python-specific complexity that affects scalability."""
        findings = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Check for deeply nested loops
                if isinstance(node, (ast.For, ast.While)):
                    nesting_level = self._count_nesting_level(node, tree)
                    if nesting_level >= 3:
                        line_num = getattr(node, "lineno", 0)
                        context = (
                            lines[line_num - 1].strip()
                            if line_num <= len(lines)
                            else ""
                        )

                        findings.append(
                            {
                                "title": f"High Algorithmic Complexity (O(n^{nesting_level}))",
                                "description": f"Deeply nested loop (level {nesting_level}) - O(n^{nesting_level}) complexity",
                                "severity": "high",
                                "file_path": file_path,
                                "line_number": line_num,
                                "recommendation": "Consider algorithm optimization, caching, or breaking into smaller functions",
                                "metadata": {
                                    "scalability_category": "performance",
                                    "pattern_name": "algorithmic_complexity",
                                    "nesting_level": nesting_level,
                                    "context": context,
                                    "confidence": "high",
                                },
                            }
                        )

                # Check for large list comprehensions
                if isinstance(node, ast.ListComp):
                    if len(node.generators) > 2:  # Multiple generators
                        line_num = getattr(node, "lineno", 0)
                        context = (
                            lines[line_num - 1].strip()
                            if line_num <= len(lines)
                            else ""
                        )

                        findings.append(
                            {
                                "title": "Complex List Comprehension",
                                "description": "Complex list comprehension with multiple generators may impact performance",
                                "severity": "medium",
                                "file_path": file_path,
                                "line_number": line_num,
                                "recommendation": "Consider breaking into simpler operations or using generator expressions",
                                "metadata": {
                                    "scalability_category": "performance",
                                    "pattern_name": "complex_comprehension",
                                    "generator_count": len(node.generators),
                                    "context": context,
                                    "confidence": "medium",
                                },
                            }
                        )

        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception as e:
            findings.append(
                {
                    "title": "AST Analysis Error",
                    "description": f"AST analysis failed: {str(e)}",
                    "severity": "low",
                    "file_path": file_path,
                    "line_number": 0,
                    "recommendation": "Manual review required - file may have syntax issues",
                    "metadata": {
                        "scalability_category": "analysis",
                        "pattern_name": "ast_analysis_error",
                        "error_type": type(e).__name__,
                        "confidence": "high",
                    },
                }
            )

        return findings

    def _count_nesting_level(self, target_node, tree) -> int:
        """Count the nesting level of loops."""
        level = 0

        def count_parent_loops(node):
            nonlocal level
            for child in ast.iter_child_nodes(node):
                if child == target_node:
                    return True
                if isinstance(child, (ast.For, ast.While)):
                    level += 1
                    if count_parent_loops(child):
                        return True
                    level -= 1
                elif count_parent_loops(child):
                    return True
            return False

        count_parent_loops(tree)
        return level

    def _get_recommendation(self, pattern_name: str, category: str) -> str:
        """Get specific recommendations for scalability issues."""
        recommendations = {
            "n_plus_one": "Use eager loading, batch queries, or caching",
            "missing_indexes": "Add database indexes for frequently queried columns",
            "large_result_sets": "Implement pagination or result limiting",
            "no_pagination": "Add LIMIT clauses and pagination support",
            "synchronous_io": "Use async/await or threading for I/O operations",
            "nested_loops": "Optimize algorithm complexity or use caching",
            "inefficient_algorithms": "Review algorithm choice and data structures",
            "memory_leaks": "Implement proper cleanup and bounded collections",
            "thread_safety": "Use thread-safe data structures and proper synchronization",
            "blocking_operations": "Use non-blocking alternatives or background processing",
            "resource_contention": "Minimize lock scope and consider lock-free algorithms",
            "tight_coupling": "Implement dependency injection and interface abstraction",
            "hardcoded_config": "Use environment variables or configuration files",
            "single_responsibility": "Refactor into smaller, focused components",
        }
        return recommendations.get(pattern_name, "Review and optimize this pattern")


if __name__ == "__main__":
    raise SystemExit(0)
