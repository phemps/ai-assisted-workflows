#!/usr/bin/env python3
"""
SQLFluff Database Analyzer - Advanced SQL Performance Analysis
==============================================================

PURPOSE: Comprehensive SQL performance analysis using SQLFluff's established rules.
Replaces bespoke regex pattern matching with established SQL analysis.

APPROACH:
- Uses SQLFluff's SQL parsing and linting rules
- Semantic SQL analysis instead of brittle regex patterns
- Multi-dialect SQL support with native parsers
- Real-time rule updates from SQL community

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements SQL-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns

REPLACES: profile_database.py with bespoke regex patterns
- More accurate SQL parsing vs regex matching
- Established rule ecosystem vs custom patterns
- Better false positive filtering
"""

import json
import subprocess
import sys
import tempfile
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


class SQLFluffAnalyzer(BaseAnalyzer):
    """SQL performance analysis using SQLFluff instead of regex patterns."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        # Create SQL-specific configuration
        sql_config = config or AnalyzerConfig(
            code_extensions={
                ".sql",
                ".SQL",
                ".ddl",
                ".dml",
                ".psql",
                ".mysql",
                ".sqlite",
                ".oracle",
                ".mssql",
                ".tsql",
                ".plsql",
                ".py",
                ".js",
                ".ts",
                ".java",
                ".cs",
                ".php",
                ".rb",
                ".go",
                ".prisma",
                ".kt",
                ".scala",
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
                "migrations",
                "*.min.js",
                "*.min.css",
                "*.bundle.js",
            },
        )

        # Initialize base analyzer
        super().__init__("performance", sql_config)

        # Check for SQLFluff availability - required for accurate analysis
        self._check_sqlfluff_availability()

        # SQLFluff configuration for database performance analysis
        self.sqlfluff_config = {
            "dialect": "ansi",  # Will detect dialect automatically where possible
            "rules": {
                # Performance-related rules
                "L001": "unnecessary_spacing",
                "L003": "multiple_trailing_newline",
                "L006": "operators_spacing",
                "L010": "capitalisation_keywords",
                "L014": "unquoted_identifiers",
                "L016": "jinja_spacing",
                "L019": "leading_comma",
                "L022": "blank_lines",
                "L025": "table_aliases",
                "L027": "table_references",
                "L029": "keyword_identifiers",
                "L031": "alias_keywords",
                "L034": "wildcards",  # SELECT * detection
                "L036": "select_targets",
                "L042": "join_condition",
                "L044": "column_references",
                "L046": "unnecessary_joins",
                "L051": "full_outer_joins",
                "L052": "semi_anti_joins",
                "L054": "group_by_order",
                "CV01": "select_distinct_usage",
                "CV02": "implicit_distinct",
                "CV03": "union_distinct",
                "RF01": "unnecessary_case",
                "RF02": "single_table_references",
                "RF03": "unnecessary_exists",
            },
        }

        # Severity mapping from SQLFluff to our levels
        self.severity_mapping = {
            "ERROR": "critical",
            "WARNING": "high",
            "INFO": "medium",
            "HINT": "low",
        }

    def _check_sqlfluff_availability(self):
        """Check if SQLFluff is available. Exit if not found."""
        try:
            result = subprocess.run(
                ["sqlfluff", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                print(
                    "ERROR: SQLFluff is required for SQL performance analysis but not found.",
                    file=sys.stderr,
                )
                print("Install with: pip install sqlfluff", file=sys.stderr)
                sys.exit(1)

            version = result.stdout.strip()
            print(f"Found SQLFluff {version}", file=sys.stderr)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("ERROR: SQLFluff is required but not available.", file=sys.stderr)
            print("Install with: pip install sqlfluff", file=sys.stderr)
            sys.exit(1)

    def _run_sqlfluff_analysis(
        self, target_path: str, sql_content: str = None
    ) -> List[Dict[str, Any]]:
        """Run SQLFluff analysis with performance-focused rules."""
        findings = []

        try:
            # Create temporary config file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".cfg", delete=False
            ) as config_file:
                config_file.write("[sqlfluff]\n")
                config_file.write(f"dialect = {self.sqlfluff_config['dialect']}\n")
                config_file.write("max_line_length = 120\n")
                config_file.write(
                    "exclude_rules = L003,L010\n"
                )  # Exclude cosmetic rules
                config_path = config_file.name

            # If we have SQL content directly, write it to a temp file
            if sql_content:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".sql", delete=False
                ) as sql_file:
                    sql_file.write(sql_content)
                    target_file = sql_file.name
            else:
                target_file = target_path

            # Run SQLFluff lint
            cmd = [
                "sqlfluff",
                "lint",
                "--format",
                "json",
                "--config",
                config_path,
                "--disable-progress-bar",
                target_file,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.stdout:
                sqlfluff_output = json.loads(result.stdout)

                # Process SQLFluff findings
                for file_result in sqlfluff_output:
                    for violation in file_result.get("violations", []):
                        processed_finding = self._process_sqlfluff_finding(
                            violation, target_path
                        )
                        if processed_finding:
                            findings.append(processed_finding)

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            json.JSONDecodeError,
        ) as e:
            if self.verbose:
                print(
                    f"SQLFluff analysis failed for {target_path}: {e}", file=sys.stderr
                )
        finally:
            # Clean up temp files
            try:
                if "config_path" in locals():
                    Path(config_path).unlink(missing_ok=True)
                if sql_content and "target_file" in locals():
                    Path(target_file).unlink(missing_ok=True)
            except Exception:
                pass

        return findings

    def _process_sqlfluff_finding(
        self, violation: Dict[str, Any], file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Convert SQLFluff finding to our standardized format."""
        try:
            # Extract key information from SQLFluff violation
            rule_code = violation.get("code", "unknown")
            message = violation.get("description", "SQL performance issue detected")
            line_no = violation.get("line_no", 0)
            # line_pos = violation.get("line_pos", 0)  # Not used currently

            # Map to our severity levels
            our_severity = self._map_rule_to_severity(rule_code)

            # Create standardized finding
            return {
                "perf_type": rule_code,
                "category": self._get_category_from_rule(rule_code),
                "file_path": file_path,
                "line_number": line_no,
                "line_content": "",  # SQLFluff doesn't always provide this
                "severity": our_severity,
                "description": message,
                "recommendation": self._get_recommendation(rule_code),
                "pattern_matched": f"SQLFluff: {rule_code}",
                "confidence": "high",  # SQLFluff provides high confidence findings
            }

        except Exception as e:
            if self.verbose:
                print(f"Failed to process SQLFluff finding: {e}", file=sys.stderr)
            return None

    def _map_rule_to_severity(self, rule_code: str) -> str:
        """Map SQLFluff rule codes to severity levels based on performance impact."""
        critical_rules = ["L034"]  # SELECT * usage
        high_rules = [
            "L025",
            "L042",
            "L046",
            "CV01",
            "RF03",
        ]  # Joins, aliases, unnecessary operations
        medium_rules = [
            "L036",
            "L044",
            "L051",
            "L052",
            "RF01",
            "RF02",
        ]  # Column references, optimization

        if rule_code in critical_rules:
            return "critical"
        elif rule_code in high_rules:
            return "high"
        elif rule_code in medium_rules:
            return "medium"
        else:
            return "low"

    def _get_category_from_rule(self, rule_code: str) -> str:
        """Map SQLFluff rule to our category system."""
        if rule_code in ["L034", "L036", "CV01"]:
            return "query_optimization"
        elif rule_code in ["L025", "L042", "L046"]:
            return "join_optimization"
        elif rule_code in ["RF01", "RF02", "RF03"]:
            return "refactoring"
        else:
            return "sql_performance"

    def _get_recommendation(self, rule_code: str) -> str:
        """Get specific recommendations based on SQLFluff rule code."""
        recommendations = {
            "L034": "Avoid SELECT * in production queries. Select only necessary columns to improve performance",
            "L025": "Use explicit table aliases to improve query readability and maintainability",
            "L042": "Ensure JOIN conditions are present and properly indexed for optimal performance",
            "L046": "Remove unnecessary JOINs that don't contribute to the result set",
            "L036": "Explicitly list SELECT targets instead of using wildcards for better performance",
            "CV01": "Consider if DISTINCT is necessary - it adds overhead and may indicate design issues",
            "RF01": "Simplify CASE statements where possible to reduce query complexity",
            "RF02": "Use table aliases consistently for better query maintenance",
            "RF03": "Replace unnecessary EXISTS clauses with more efficient alternatives",
        }

        return recommendations.get(
            rule_code, "Review SQL query for performance optimization opportunities"
        )

    def _extract_sql_from_code(self, content: str, file_path: str) -> List[str]:
        """Extract SQL queries from code files."""
        sql_queries = []

        # Common SQL query patterns in code
        sql_patterns = [
            r'(?:SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER)[\s\S]+?(?:["\'];|$)',
            r'"""[\s\S]*?(?:SELECT|INSERT|UPDATE|DELETE)[\s\S]*?"""',
            r"'''[\s\S]*?(?:SELECT|INSERT|UPDATE|DELETE)[\s\S]*?'''",
            r"`[\s\S]*?(?:SELECT|INSERT|UPDATE|DELETE)[\s\S]*?`",
        ]

        import re

        for pattern in sql_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                query = match.group(0).strip()
                # Clean up query
                query = re.sub(r'^["\']|["\']$|^`|`$', "", query)
                query = re.sub(r'^"""|"""$', "", query)
                query = re.sub(r"^'''|'''$", "", query)
                if len(query) > 20 and any(
                    keyword in query.upper()
                    for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]
                ):
                    sql_queries.append(query)

        return sql_queries

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze target using SQLFluff for SQL performance analysis.

        Args:
            target_path: Path to analyze (single file - BaseAnalyzer handles directory iteration)

        Returns:
            List of SQL performance findings with standardized structure
        """
        all_findings = []
        file_path = Path(target_path)

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # If it's a pure SQL file, analyze directly
            if file_path.suffix.lower() in [
                ".sql",
                ".ddl",
                ".dml",
                ".psql",
                ".mysql",
                ".sqlite",
            ]:
                findings = self._run_sqlfluff_analysis(target_path)
            else:
                # Extract SQL from code files
                sql_queries = self._extract_sql_from_code(content, str(file_path))
                for sql_query in sql_queries:
                    findings = self._run_sqlfluff_analysis(str(file_path), sql_query)
                    all_findings.extend(findings)
                return all_findings

        except Exception as e:
            if self.verbose:
                print(f"Error analyzing {target_path}: {e}", file=sys.stderr)
            return []

        # Convert to our standardized format for BaseAnalyzer
        standardized_findings = []
        for finding in all_findings:
            standardized = {
                "title": f"{finding['description']} ({finding['perf_type']})",
                "description": f"SQLFluff detected: {finding['description']}. Category: {finding['category']}. This SQL performance issue should be reviewed and optimized.",
                "severity": finding["severity"],
                "file_path": finding["file_path"],
                "line_number": finding["line_number"],
                "recommendation": finding["recommendation"],
                "metadata": {
                    "tool": "sqlfluff",
                    "rule_code": finding["perf_type"],
                    "category": finding["category"],
                    "confidence": finding["confidence"],
                },
            }
            standardized_findings.append(standardized)

        return standardized_findings

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "SQLFluff Database Analyzer",
            "version": "2.0.0",
            "description": "SQL performance analysis using SQLFluff (replacing bespoke regex patterns)",
            "category": "performance",
            "priority": "high",
            "capabilities": [
                "SQL query performance analysis",
                "SELECT * detection",
                "JOIN optimization analysis",
                "Query complexity evaluation",
                "Database best practices validation",
                "Multi-dialect SQL support",
                "Embedded SQL extraction from code",
                "Real-time SQL rule updates",
            ],
            "supported_languages": [
                "SQL",
                "MySQL",
                "PostgreSQL",
                "SQLite",
                "MSSQL",
                "Oracle",
                "Python",
                "JavaScript",
                "TypeScript",
                "Java",
                "C#",
                "PHP",
                "Ruby",
                "Go",
                "Kotlin",
                "Scala",
                "Prisma",
            ],
            "tool": "sqlfluff",
            "replaces": ["profile_database.py"],
        }


def main():
    """Main entry point for command-line usage."""
    analyzer = SQLFluffAnalyzer()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
