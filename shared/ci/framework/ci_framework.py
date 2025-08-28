#!/usr/bin/env python3
"""
Continuous Improvement Framework Core
Part of AI-Assisted Workflows - integrates with 8-agent orchestration system.
"""

import json
import sys
import sqlite3
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Use smart imports for module access
try:
    from smart_imports import (
        import_output_formatter,
        import_tech_stack_detector,
        import_symbol_extractor,
    )
except ImportError as e:
    print(f"Error importing smart imports: {e}", file=sys.stderr)
    sys.exit(1)

# Import utilities
try:
    output_formatter_module = import_output_formatter()
    AnalysisResult = output_formatter_module.AnalysisResult
    ResultFormatter = output_formatter_module.ResultFormatter

    tech_stack_module = import_tech_stack_detector()
    TechStackDetector = tech_stack_module.TechStackDetector

    symbol_extractor_module = import_symbol_extractor()
    SymbolExtractor = symbol_extractor_module.SymbolExtractor
except ImportError as e:
    print(f"Error importing utilities: {e}", file=sys.stderr)
    sys.exit(1)


class CIPhase(Enum):
    """Continuous improvement phases."""

    COLLECT = "collect"
    ANALYZE = "analyze"
    RECOMMEND = "recommend"
    IMPLEMENT = "implement"
    VERIFY = "verify"


class CIMetricType(Enum):
    """Types of CI metrics."""

    QUALITY_GATE = "quality_gate"
    BUILD_TIME = "build_time"
    TEST_COVERAGE = "test_coverage"
    DEPLOYMENT = "deployment"
    ERROR_RATE = "error_rate"
    PERFORMANCE = "performance"


class CIFramework:
    """Core framework for continuous improvement integration."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.tech_detector = TechStackDetector()
        self.db_path = self.project_root / ".claude" / "ci_metrics.db"
        self._init_database()

    def _init_database(self):
        """Initialize CI metrics database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ci_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    value REAL,
                    metadata TEXT,
                    correlation_id TEXT,
                    agent_source TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ci_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    description TEXT NOT NULL,
                    implementation_status TEXT DEFAULT 'pending',
                    metadata TEXT,
                    correlation_id TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ci_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

    def record_metric(
        self,
        metric_type: CIMetricType,
        phase: CIPhase,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        agent_source: Optional[str] = None,
    ) -> str:
        """Record a CI metric with agent orchestration context."""
        timestamp = datetime.now().isoformat()
        metric_id = f"ci-metric-{int(time.time() * 1000)}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ci_metrics
                (timestamp, metric_type, phase, value, metadata,
                 correlation_id, agent_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    timestamp,
                    metric_type.value,
                    phase.value,
                    value,
                    json.dumps(metadata or {}),
                    correlation_id,
                    agent_source,
                ),
            )

        return metric_id

    def get_metrics(
        self,
        metric_type: Optional[CIMetricType] = None,
        since: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve CI metrics with filtering."""
        query = "SELECT * FROM ci_metrics WHERE 1=1"
        params = []

        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type.value)

        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())

        if correlation_id:
            query += " AND correlation_id = ?"
            params.append(correlation_id)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]

            results = []
            for row in cursor.fetchall():
                metric = dict(zip(columns, row))
                if metric["metadata"]:
                    metric["metadata"] = json.loads(metric["metadata"])
                results.append(metric)

        return results

    def create_recommendation(
        self,
        category: str,
        priority: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Create a CI improvement recommendation."""
        timestamp = datetime.now().isoformat()
        rec_id = f"ci-rec-{int(time.time() * 1000)}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ci_recommendations
                (timestamp, category, priority, description, metadata,
                 correlation_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    timestamp,
                    category,
                    priority,
                    description,
                    json.dumps(metadata or {}),
                    correlation_id,
                ),
            )

        return rec_id

    def get_recommendations(
        self,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: str = "pending",
    ) -> List[Dict[str, Any]]:
        """Get CI recommendations by criteria."""
        query = "SELECT * FROM ci_recommendations " "WHERE implementation_status = ?"
        params = [status]

        if category:
            query += " AND category = ?"
            params.append(category)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]

            results = []
            for row in cursor.fetchall():
                rec = dict(zip(columns, row))
                if rec["metadata"]:
                    rec["metadata"] = json.loads(rec["metadata"])
                results.append(rec)

        return results

    def analyze_trends(
        self, metric_type: CIMetricType, days: int = 7
    ) -> Dict[str, Any]:
        """Analyze metric trends for CI insights."""
        since = datetime.now() - timedelta(days=days)
        metrics = self.get_metrics(metric_type=metric_type, since=since)

        if not metrics:
            return {"trend": "insufficient_data", "metrics_count": 0}

        values = [m["value"] for m in metrics]

        analysis = {
            "metric_type": metric_type.value,
            "period_days": days,
            "metrics_count": len(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[0] if values else None,
            "trend": "stable",  # Basic trend analysis
        }

        # Simple trend detection
        if len(values) >= 2:
            recent_avg = sum(values[: len(values) // 2]) / (len(values) // 2)
            older_avg = sum(values[len(values) // 2 :]) / (
                len(values) - len(values) // 2
            )

            if recent_avg > older_avg * 1.1:
                analysis["trend"] = "improving"
            elif recent_avg < older_avg * 0.9:
                analysis["trend"] = "declining"

        return analysis

    def generate_ci_report(self) -> AnalysisResult:
        """Generate comprehensive CI analysis report."""
        start_time = time.time()
        result = ResultFormatter.create_architecture_result(
            "ci_framework.py", str(self.project_root)
        )

        try:
            # Collect recent metrics
            recent_metrics = self.get_metrics(since=datetime.now() - timedelta(days=7))

            # Get pending recommendations
            pending_recs = self.get_recommendations(status="pending")

            # Analyze trends for each metric type
            trend_analyses = {}
            for metric_type in CIMetricType:
                trend_analyses[metric_type.value] = self.analyze_trends(metric_type)

            # Create findings for high-priority recommendations
            finding_id = 1
            for rec in pending_recs[:10]:  # Top 10 recommendations
                severity = "high" if rec["priority"] == "critical" else "medium"

                finding = ResultFormatter.create_finding(
                    f"CI{finding_id:03d}",
                    f"CI Recommendation: {rec['category']}",
                    rec["description"],
                    severity,
                    recommendation=(
                        f"Priority: {rec['priority']} - " f"{rec['description']}"
                    ),
                    evidence={
                        "category": rec["category"],
                        "priority": rec["priority"],
                        "created_at": rec["timestamp"],
                        "correlation_id": rec["correlation_id"],
                    },
                )
                result.add_finding(finding)
                finding_id += 1

            # Add comprehensive metadata
            result.metadata = {
                "recent_metrics_count": len(recent_metrics),
                "pending_recommendations": len(pending_recs),
                "trend_analyses": trend_analyses,
                "ci_database": str(self.db_path),
                "project_root": str(self.project_root),
                "analysis_period_days": 7,
            }

        except Exception as e:
            result.set_error(f"CI analysis failed: {str(e)}")

        result.set_execution_time(start_time)
        return result

    def get_state(self, key: str) -> Optional[str]:
        """Get CI framework state value."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM ci_state WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None

    def set_state(self, key: str, value: str):
        """Set CI framework state value."""
        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ci_state (key, value, updated_at)
                VALUES (?, ?, ?)
            """,
                (key, value, timestamp),
            )

    def extract_project_symbols(self, use_serena: bool = True) -> AnalysisResult:
        """
        Extract symbols from project using integrated symbol extractor.

        Args:
            use_serena: Whether to attempt Serena MCP first (default: True)

        Returns:
            AnalysisResult containing symbol extraction findings
        """
        symbol_extractor = SymbolExtractor(self.project_root)
        result = symbol_extractor.extract_symbols(use_serena=use_serena)

        # Record symbol extraction metric
        self.record_metric(
            metric_type=CIMetricType.QUALITY_GATE,
            name="symbol_extraction_count",
            value=result.summary.get("total_symbols", 0),
            metadata={
                "files_processed": result.summary.get("files_processed", 0),
                "extraction_method": result.summary.get("extraction_method", "unknown"),
                "execution_time": result.summary.get("execution_time_seconds", 0),
            },
        )

        # Generate recommendations based on symbol analysis
        symbol_summary = result.summary.get("symbol_breakdown", {})

        # Recommend refactoring if too many functions found
        if symbol_summary.get("functions", 0) > 500:
            self.record_recommendation(
                category="code_quality",
                title="Consider function refactoring",
                description=f"Project contains {symbol_summary.get('functions')} functions. Consider breaking down large modules.",
                priority="medium",
                correlation_id=f"symbol_analysis_{int(time.time())}",
            )

        # Recommend architectural review if too many classes
        if symbol_summary.get("classes", 0) > 200:
            self.record_recommendation(
                category="architecture",
                title="Architectural complexity review",
                description=f"Project contains {symbol_summary.get('classes')} classes. Consider architectural patterns review.",
                priority="medium",
                correlation_id=f"symbol_analysis_{int(time.time())}",
            )

        return result


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Continuous Improvement Framework - Core Operations"
    )
    parser.add_argument(
        "command",
        choices=["init", "report", "metrics", "recommendations", "extract-symbols"],
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output-format", choices=["json", "console"], default="json")
    parser.add_argument("--days", type=int, default=7, help="Analysis period in days")
    parser.add_argument(
        "--no-serena", action="store_true", help="Skip Serena MCP, use AST/regex only"
    )

    args = parser.parse_args()

    framework = CIFramework(args.project_root)

    if args.command == "init":
        print("✅ CI Framework initialized")
        print(f"Database: {framework.db_path}")

    elif args.command == "report":
        result = framework.generate_ci_report()
        if args.output_format == "console":
            print(ResultFormatter.format_console_output(result))
        else:
            print(result.to_json())

    elif args.command == "metrics":
        metrics = framework.get_metrics(
            since=datetime.now() - timedelta(days=args.days)
        )
        print(json.dumps(metrics, indent=2))

    elif args.command == "recommendations":
        recs = framework.get_recommendations()
        print(json.dumps(recs, indent=2))

    elif args.command == "extract-symbols":
        result = framework.extract_project_symbols(use_serena=not args.no_serena)
        if args.output_format == "console":
            print("Symbol extraction completed:")
            print(f"  Total symbols: {result.summary.get('total_symbols', 0)}")
            print(f"  Files processed: {result.summary.get('files_processed', 0)}")
            print(f"  Method: {result.summary.get('extraction_method', 'unknown')}")
            print(f"  Time: {result.summary.get('execution_time_seconds', 0)}s")
            print("  Symbol breakdown:")
            for symbol_type, count in result.summary.get(
                "symbol_breakdown", {}
            ).items():
                print(f"    {symbol_type}: {count}")
        else:
            print(result.to_json())


if __name__ == "__main__":
    main()
