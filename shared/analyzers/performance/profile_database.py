#!/usr/bin/env python3
"""
Database Performance Profiler - Advanced Database Query Analysis
=================================================================

PURPOSE: Specialized database performance profiler using pattern-based analysis.
Part of the shared/analyzers/performance suite using BaseProfiler infrastructure.

APPROACH:
- N+1 query pattern detection
- Slow query pattern identification
- ORM lazy loading analysis
- Advanced regex-based pattern matching for database-specific issues

EXTENDS: BaseProfiler for common profiling infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements database-specific profiling logic in profile_target()
- Uses shared timing, logging, and error handling patterns
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import base profiler infrastructure
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
try:
    from shared.core.base.profiler_base import BaseProfiler, ProfilerConfig
except ImportError as e:
    print(f"Error importing base profiler: {e}", file=sys.stderr)
    sys.exit(1)


class DatabaseProfiler(BaseProfiler):
    """Analyze database usage patterns for performance issues."""

    def __init__(self, config: Optional[ProfilerConfig] = None):
        # Create database-specific configuration
        db_config = config or ProfilerConfig(
            code_extensions={
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
            },
        )

        # Initialize base profiler
        super().__init__("database", db_config)
        # N+1 Query patterns
        self.n_plus_one_patterns = {
            "loop_query": {
                "pattern": r"for\s+\w+\s+in\s+.*?:\s*[\s\S]*?(?:\.query\(|\.get\(|\.filter\(|\.find\()",
                "severity": "high",
                "description": "Potential N+1 query in loop",
            },
            "foreach_query": {
                "pattern": r"(?:forEach|map|each)\s*\(\s*.*?(?:query|find|get|select)",
                "severity": "high",
                "description": "Potential N+1 query in iteration",
            },
            "nested_query": {
                "pattern": r"(?:\.query\(|\.find\(|\.get\()[\s\S]*?(?:\.query\(|\.find\(|\.get\()",
                "severity": "medium",
                "description": "Nested database queries detected",
            },
        }

        # Slow query patterns
        self.slow_query_patterns = {
            "missing_where": {
                "pattern": r"(?:SELECT|select)(?![^\'\"]*[\'\"]).+(?:FROM|from)\s+\w+(?![^\'\"]*[\'\"]\s*[;,)])(?!\s+(?:WHERE|where))",
                "severity": "high",
                "description": "Query without WHERE clause - potential table scan",
            },
            "select_all": {
                "pattern": r"(?:SELECT|select)\s+\*\s+(?:FROM|from)",
                "severity": "medium",
                "description": "SELECT * query - may fetch unnecessary data",
            },
            "no_limit": {
                "pattern": r"(?:SELECT|select)(?![^\'\"]*[\'\"]).+(?:FROM|from)\s+\w+(?![^\'\"]*[\'\"]\s*[;,)])(?!\s+(?:LIMIT|limit|TOP|top))",
                "severity": "medium",
                "description": "Query without LIMIT - may return large result set",
            },
            "like_prefix": {
                "pattern": r"(?:LIKE|like)\s+[\'\"]\%",
                "severity": "medium",
                "description": "LIKE query with leading wildcard - cannot use index",
            },
        }

        # ORM lazy loading patterns
        self.orm_patterns = {
            "eager_loading": {
                "pattern": r"\.include\(|\.populate\(|\.with\(|\.join\(",
                "severity": "info",
                "description": "Eager loading used - good practice",
            },
            "lazy_access": {
                "pattern": r"\w+\.\w+(?:\.\w+)*\.(?:count|length|size)\s*(?:\(\))?",
                "severity": "medium",
                "description": "Potential lazy loading access",
            },
        }

        # Database-specific initialization complete

    def profile_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Implement database-specific profiling logic.

        Args:
            target_path: Path to analyze (single file only - BaseProfiler handles directory iteration)

        Returns:
            List of database profiling findings for this specific file
        """
        # BaseProfiler calls this method for each individual file
        # So target_path should always be a single file here
        target = Path(target_path)

        if target.is_file():
            return self._scan_file_for_db_issues(target)

        return []

    def _scan_file_for_db_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Scan a single file for database performance issues.

        Args:
            file_path: Path to the file to scan

        Returns:
            List of database findings dictionaries
        """
        findings = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

                # Check N+1 patterns
                for pattern_name, pattern_info in self.n_plus_one_patterns.items():
                    findings.extend(
                        self._find_pattern_matches(
                            content,
                            lines,
                            file_path,
                            pattern_name,
                            pattern_info,
                            "N+1 Query",
                        )
                    )

                # Check slow query patterns
                for pattern_name, pattern_info in self.slow_query_patterns.items():
                    findings.extend(
                        self._find_pattern_matches(
                            content,
                            lines,
                            file_path,
                            pattern_name,
                            pattern_info,
                            "Slow Query",
                        )
                    )

                # Check ORM patterns
                for pattern_name, pattern_info in self.orm_patterns.items():
                    findings.extend(
                        self._find_pattern_matches(
                            content,
                            lines,
                            file_path,
                            pattern_name,
                            pattern_info,
                            "ORM Usage",
                        )
                    )

        except Exception as e:
            # Log error but continue scanning
            self.logger.warning(f"Error scanning {file_path}: {e}")

        return findings

    def get_profiler_metadata(self) -> Dict[str, Any]:
        """
        Get database profiler-specific metadata.

        Returns:
            Dictionary with profiler-specific metadata
        """
        return {
            "pattern_categories": {
                "n_plus_one_patterns": len(self.n_plus_one_patterns),
                "slow_query_patterns": len(self.slow_query_patterns),
                "orm_patterns": len(self.orm_patterns),
            },
            "total_patterns": (
                len(self.n_plus_one_patterns)
                + len(self.slow_query_patterns)
                + len(self.orm_patterns)
            ),
            "supported_databases": [
                "MySQL",
                "PostgreSQL",
                "SQLite",
                "MongoDB",
                "SQL Server",
                "Oracle",
                "Redis",
            ],
            "supported_orms": [
                "SQLAlchemy",
                "Django ORM",
                "Sequelize",
                "Prisma",
                "Hibernate",
                "ActiveRecord",
            ],
        }

    def _find_pattern_matches(
        self,
        content: str,
        lines: List[str],
        file_path: Path,
        pattern_name: str,
        pattern_info: Dict[str, str],
        category: str,
    ) -> List[Dict[str, Any]]:
        """Find matches for a specific pattern."""
        findings = []

        matches = re.finditer(
            pattern_info["pattern"], content, re.MULTILINE | re.IGNORECASE
        )

        for match in matches:
            # Find line number
            line_start = content[: match.start()].count("\n") + 1

            # Get context lines
            context_start = max(0, line_start - 2)
            context_end = min(len(lines), line_start + 2)
            context_lines = lines[context_start:context_end]

            finding = {
                "title": f"{category}: {pattern_name.replace('_', ' ').title()}",
                "description": pattern_info["description"],
                "severity": pattern_info["severity"],
                "file_path": str(file_path),
                "line_number": line_start,
                "recommendation": self._get_recommendation(pattern_name),
                "metadata": {
                    "category": category,
                    "pattern_type": pattern_name,
                    "line_content": (
                        lines[line_start - 1].strip()
                        if line_start <= len(lines)
                        else ""
                    ),
                    "context": "\n".join(context_lines),
                    "matched_text": match.group(0)[:100],  # Limit length
                },
            }
            findings.append(finding)

        return findings

    def _get_recommendation(self, pattern_type: str) -> str:
        """Get recommendation for specific pattern type."""
        recommendations = {
            "loop_query": "Use eager loading or batch queries to avoid N+1 problem",
            "foreach_query": "Consider bulk operations or eager loading instead",
            "nested_query": "Refactor to use joins or single query with subqueries",
            "missing_where": "Add WHERE clause to filter results and use indexes",
            "select_all": "Select only necessary columns to reduce data transfer",
            "no_limit": "Add LIMIT clause to prevent large result sets",
            "like_prefix": "Avoid leading wildcards; consider full-text search",
            "eager_loading": "Good practice - continue using eager loading",
            "lazy_access": "Consider eager loading for frequently accessed relations",
        }
        return recommendations.get(
            pattern_type, "Review query performance and optimization opportunities"
        )


def main():
    """Main function for command-line usage."""
    profiler = DatabaseProfiler()
    exit_code = profiler.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
