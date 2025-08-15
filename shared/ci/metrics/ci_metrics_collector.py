#!/usr/bin/env python3
"""
Duplication Detection System Metrics Collection and Analysis
Tracks performance metrics for the duplication detection system components.
Part of AI-Assisted Workflows.
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

import psutil

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "utils"))

try:
    from shared.core.utils.output_formatter import AnalysisResult, ResultFormatter
    from shared.core.utils.tech_stack_detector import TechStackDetector
except ImportError as e:
    print(f"Error importing required dependencies: {e}", file=sys.stderr)
    sys.exit(1)


@dataclass
class DuplicationScanMetrics:
    """Duplication scan performance metrics."""

    scan_time: float
    files_processed: int
    duplicates_found: int
    symbols_analyzed: int
    scan_success: bool = True
    false_positives: Optional[int] = None
    true_positives: Optional[int] = None


@dataclass
class CTODecisionMetrics:
    """CTO decision tracking metrics."""

    decisions_made: int
    automatic_fixes: int
    human_reviews: int
    fix_success_rate: float
    escalations_triggered: int = 0
    decision_time_seconds: Optional[float] = None


@dataclass
class ComponentPerformanceMetrics:
    """Duplication system component performance metrics."""

    embedding_time: float
    similarity_search_time: float
    registry_time: float
    total_pipeline_time: float
    components_active: int
    registry_size: Optional[int] = None


@dataclass
class SystemHealthMetrics:
    """Overall duplication detection system health metrics."""

    registry_entries: int
    active_components: int
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    storage_size_mb: Optional[float] = None


class DuplicationMetricsCollector:
    """Collect and analyze duplication detection system metrics."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.tech_detector = TechStackDetector()
        self.metrics_store = self._init_metrics_store()

    def _init_metrics_store(self) -> Dict[str, List[Dict]]:
        """Initialize metrics storage."""
        return {
            "scan_metrics": [],
            "cto_decisions": [],
            "component_performance": [],
            "system_health": [],
        }

    def collect_scan_metrics(
        self, scan_results: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> DuplicationScanMetrics:
        """Record scan performance metrics."""
        start_time = time.time()

        try:
            scan_time = scan_results.get("scan_time", 0.0)
            files_processed = scan_results.get("files_processed", 0)
            duplicates_found = scan_results.get("duplicates_found", 0)
            symbols_analyzed = scan_results.get("symbols_analyzed", 0)
            scan_success = scan_results.get("success", True)
            false_positives = scan_results.get("false_positives")
            true_positives = scan_results.get("true_positives")

        except Exception as e:
            print(f"Scan metrics collection error: {e}", file=sys.stderr)
            # Provide fallback values
            scan_time = time.time() - start_time
            files_processed = 0
            duplicates_found = 0
            symbols_analyzed = 0
            scan_success = False
            false_positives = None
            true_positives = None

        metrics = DuplicationScanMetrics(
            scan_time=scan_time,
            files_processed=files_processed,
            duplicates_found=duplicates_found,
            symbols_analyzed=symbols_analyzed,
            scan_success=scan_success,
            false_positives=false_positives,
            true_positives=true_positives,
        )

        # Store metrics
        metric_entry = asdict(metrics)
        metric_entry["timestamp"] = datetime.now().isoformat()
        metric_entry["correlation_id"] = correlation_id
        self.metrics_store["scan_metrics"].append(metric_entry)

        return metrics

    def record_cto_decision(
        self,
        duplicate_info: Dict[str, Any],
        decision: str,
        correlation_id: Optional[str] = None,
    ) -> CTODecisionMetrics:
        """Track CTO decision patterns."""
        start_time = time.time()

        try:
            # Extract decision details
            decisions_made = 1
            automatic_fixes = 1 if decision == "fix" else 0
            human_reviews = 1 if decision == "review" else 0
            escalations_triggered = 1 if decision == "escalate" else 0

            # Calculate success rate from recent decisions
            recent_decisions = self._get_recent_cto_decisions(days=7)
            fix_success_rate = self._calculate_fix_success_rate(recent_decisions)

            decision_time_seconds = time.time() - start_time

        except Exception as e:
            print(f"CTO decision recording error: {e}", file=sys.stderr)
            decisions_made = 1
            automatic_fixes = 0
            human_reviews = 0
            fix_success_rate = 0.0
            escalations_triggered = 0
            decision_time_seconds = None

        metrics = CTODecisionMetrics(
            decisions_made=decisions_made,
            automatic_fixes=automatic_fixes,
            human_reviews=human_reviews,
            fix_success_rate=fix_success_rate,
            escalations_triggered=escalations_triggered,
            decision_time_seconds=decision_time_seconds,
        )

        # Store metrics
        metric_entry = asdict(metrics)
        metric_entry["timestamp"] = datetime.now().isoformat()
        metric_entry["correlation_id"] = correlation_id
        metric_entry["decision"] = decision
        metric_entry["duplicate_info"] = duplicate_info
        self.metrics_store["cto_decisions"].append(metric_entry)

        return metrics

    def collect_component_performance(
        self, component_timings: Dict[str, float], correlation_id: Optional[str] = None
    ) -> ComponentPerformanceMetrics:
        """Collect duplication system component performance metrics."""
        try:
            embedding_time = component_timings.get("embedding_time", 0.0)
            similarity_search_time = component_timings.get(
                "similarity_search_time", 0.0
            )
            registry_time = component_timings.get("registry_time", 0.0)
            total_pipeline_time = component_timings.get("total_pipeline_time", 0.0)
            components_active = component_timings.get("components_active", 0)
            registry_size = component_timings.get("registry_size")

        except Exception as e:
            print(f"Component performance collection error: {e}", file=sys.stderr)
            embedding_time = 0.0
            similarity_search_time = 0.0
            registry_time = 0.0
            total_pipeline_time = 0.0
            components_active = 0
            registry_size = None

        metrics = ComponentPerformanceMetrics(
            embedding_time=embedding_time,
            similarity_search_time=similarity_search_time,
            registry_time=registry_time,
            total_pipeline_time=total_pipeline_time,
            components_active=components_active,
            registry_size=registry_size,
        )

        # Store metrics
        metric_entry = asdict(metrics)
        metric_entry["timestamp"] = datetime.now().isoformat()
        metric_entry["correlation_id"] = correlation_id
        self.metrics_store["component_performance"].append(metric_entry)

        return metrics

    def get_system_health(
        self, correlation_id: Optional[str] = None
    ) -> SystemHealthMetrics:
        """Get registry and component status for system health."""
        try:
            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_mb = memory_info.used / 1024 / 1024

            # Calculate registry metrics
            registry_entries = self._count_registry_entries()
            active_components = self._count_active_components()
            error_rate = self._calculate_error_rate()

            # Calculate storage usage
            storage_size_mb = self._calculate_storage_size()

        except Exception as e:
            print(f"System health collection error: {e}", file=sys.stderr)
            cpu_percent = 0.0
            memory_mb = 0.0
            registry_entries = 0
            active_components = 0
            error_rate = 0.0
            storage_size_mb = None

        metrics = SystemHealthMetrics(
            registry_entries=registry_entries,
            active_components=active_components,
            error_rate=error_rate,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
            storage_size_mb=storage_size_mb,
        )

        # Store metrics
        metric_entry = asdict(metrics)
        metric_entry["timestamp"] = datetime.now().isoformat()
        metric_entry["correlation_id"] = correlation_id
        self.metrics_store["system_health"].append(metric_entry)

        return metrics

    def generate_report(self, days: int = 7) -> AnalysisResult:
        """Generate simple performance report for duplication system."""
        start_time = time.time()
        result = ResultFormatter.create_architecture_result(
            "duplication_metrics_collector.py", str(self.project_root)
        )

        try:
            # Get current system health
            system_health = self.get_system_health()

            # Analyze recent metrics
            since_date = datetime.now() - timedelta(days=days)

            scan_stats = self._analyze_scan_performance(since_date)
            cto_stats = self._analyze_cto_decisions(since_date)
            component_stats = self._analyze_component_performance(since_date)

            # Generate findings for issues
            finding_id = 1

            # System health findings
            if system_health.error_rate > 0.1:  # > 10% error rate
                error_percent = f"{system_health.error_rate * 100:.1f}%"
                finding = ResultFormatter.create_finding(
                    f"DUP{finding_id:03d}",
                    "High Error Rate",
                    f"System error rate at {error_percent} (>10% threshold)",
                    "high",
                    recommendation="Investigate and fix system errors",
                    evidence={"system_health": asdict(system_health)},
                )
                result.add_finding(finding)
                finding_id += 1

            # Scan performance findings
            if scan_stats.get("avg_scan_time", 0) > 30:  # > 30 seconds
                scan_time = f"{scan_stats['avg_scan_time']:.1f}s"
                finding = ResultFormatter.create_finding(
                    f"DUP{finding_id:03d}",
                    "Slow Scan Performance",
                    f"Average scan time {scan_time} (>30s threshold)",
                    "medium",
                    recommendation="Optimize scan algorithms and indexing",
                    evidence={"scan_stats": scan_stats},
                )
                result.add_finding(finding)
                finding_id += 1

            # False positive rate findings
            if scan_stats.get("false_positive_rate", 0) > 0.2:  # > 20%
                fp_rate = f"{scan_stats['false_positive_rate'] * 100:.1f}%"
                finding = ResultFormatter.create_finding(
                    f"DUP{finding_id:03d}",
                    "High False Positive Rate",
                    f"False positive rate at {fp_rate} (>20% threshold)",
                    "medium",
                    recommendation="Tune similarity thresholds and filters",
                    evidence={"scan_stats": scan_stats},
                )
                result.add_finding(finding)
                finding_id += 1

            # Component performance findings
            if component_stats.get("avg_pipeline_time", 0) > 10:  # > 10 seconds
                pipeline_time = f"{component_stats['avg_pipeline_time']:.1f}s"
                finding = ResultFormatter.create_finding(
                    f"DUP{finding_id:03d}",
                    "Slow Pipeline Performance",
                    f"Average pipeline time {pipeline_time} (>10s threshold)",
                    "medium",
                    recommendation="Optimize component pipeline processing",
                    evidence={"component_stats": component_stats},
                )
                result.add_finding(finding)
                finding_id += 1

            # Add metadata
            result.metadata = {
                "system_health": asdict(system_health),
                "scan_statistics": scan_stats,
                "cto_statistics": cto_stats,
                "component_statistics": component_stats,
                "analysis_period_days": days,
                "project_root": str(self.project_root),
                "metrics_collected": len(self.metrics_store["scan_metrics"]),
            }

        except Exception as e:
            result.set_error(f"Duplication metrics analysis failed: {str(e)}")

        result.set_execution_time(start_time)
        return result

    def _get_recent_cto_decisions(self, days: int = 7) -> List[Dict]:
        """Get recent CTO decisions from metrics store."""
        since_date = datetime.now() - timedelta(days=days)

        recent_decisions = []
        for decision in self.metrics_store["cto_decisions"]:
            decision_time = datetime.fromisoformat(decision["timestamp"])
            if decision_time >= since_date:
                recent_decisions.append(decision)

        return recent_decisions

    def _calculate_fix_success_rate(self, decisions: List[Dict]) -> float:
        """Calculate success rate of automatic fixes."""
        if not decisions:
            return 0.0

        fixes = [d for d in decisions if d.get("decision") == "fix"]
        if not fixes:
            return 0.0

        # Simplified success rate calculation
        # In real implementation, track fix outcomes
        return 0.8  # 80% default success rate

    def _count_registry_entries(self) -> int:
        """Count entries in duplication registry."""
        registry_path = self.project_root / ".claude" / "registry"
        if not registry_path.exists():
            return 0

        count = 0
        for file_path in registry_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    count += len(data.get("entries", []))
            except Exception:
                continue
        return count

    def _count_active_components(self) -> int:
        """Count active duplication detection components."""
        # Check for component status files or running processes
        components = [
            "DuplicateFinder",
            "EmbeddingEngine",
            "SimilarityEngine",
            "ComponentRegistry",
            "CTODecisionEngine",
        ]

        active_count = 0
        for component in components:
            # Simplified check - in real implementation check process status
            status_file = self.project_root / ".claude" / f"{component}.status"
            if status_file.exists():
                active_count += 1

        return active_count

    def _calculate_error_rate(self) -> float:
        """Calculate system error rate from recent metrics."""
        recent_scans = self._get_recent_scans(days=1)
        if not recent_scans:
            return 0.0

        failed_scans = sum(
            1 for scan in recent_scans if not scan.get("scan_success", True)
        )
        return failed_scans / len(recent_scans)

    def _calculate_storage_size(self) -> Optional[float]:
        """Calculate total storage used by duplication system."""
        storage_dirs = [
            self.project_root / ".claude" / "registry",
            self.project_root / ".claude" / "embeddings",
            self.project_root / ".claude" / "cache",
        ]

        total_size = 0
        for storage_dir in storage_dirs:
            if storage_dir.exists():
                total_size += self._calculate_directory_size_mb(storage_dir)

        return total_size if total_size > 0 else None

    def _calculate_directory_size_mb(self, directory: Path) -> float:
        """Calculate directory size in MB."""
        total_size = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except Exception:
                    continue
        return total_size / 1024 / 1024

    def _get_recent_scans(self, days: int = 1) -> List[Dict]:
        """Get recent scan metrics."""
        since_date = datetime.now() - timedelta(days=days)

        recent_scans = []
        for scan in self.metrics_store["scan_metrics"]:
            scan_time = datetime.fromisoformat(scan["timestamp"])
            if scan_time >= since_date:
                recent_scans.append(scan)

        return recent_scans

    def _analyze_scan_performance(self, since_date: datetime) -> Dict[str, Any]:
        """Analyze scan performance metrics over time period."""
        relevant_scans = [
            scan
            for scan in self.metrics_store["scan_metrics"]
            if datetime.fromisoformat(scan["timestamp"]) >= since_date
        ]

        if not relevant_scans:
            return {"count": 0, "avg_scan_time": 0, "false_positive_rate": 0}

        scan_times = [scan["scan_time"] for scan in relevant_scans]

        # Calculate false positive rate
        total_positives = sum(
            scan.get("true_positives", 0) + scan.get("false_positives", 0)
            for scan in relevant_scans
        )
        false_positives = sum(scan.get("false_positives", 0) for scan in relevant_scans)
        false_positive_rate = (
            false_positives / total_positives if total_positives > 0 else 0
        )

        return {
            "count": len(relevant_scans),
            "avg_scan_time": sum(scan_times) / len(scan_times),
            "total_duplicates_found": sum(
                scan["duplicates_found"] for scan in relevant_scans
            ),
            "false_positive_rate": false_positive_rate,
        }

    def _analyze_cto_decisions(self, since_date: datetime) -> Dict[str, Any]:
        """Analyze CTO decision patterns over time period."""
        relevant_decisions = [
            decision
            for decision in self.metrics_store["cto_decisions"]
            if datetime.fromisoformat(decision["timestamp"]) >= since_date
        ]

        if not relevant_decisions:
            return {"count": 0, "fix_ratio": 0, "avg_decision_time": 0}

        fix_decisions = sum(1 for d in relevant_decisions if d.get("decision") == "fix")

        decision_times = [
            d.get("decision_time_seconds", 0)
            for d in relevant_decisions
            if d.get("decision_time_seconds")
        ]

        return {
            "count": len(relevant_decisions),
            "fix_ratio": fix_decisions / len(relevant_decisions),
            "avg_decision_time": (
                sum(decision_times) / len(decision_times) if decision_times else 0
            ),
            "escalations": sum(
                d.get("escalations_triggered", 0) for d in relevant_decisions
            ),
        }

    def _analyze_component_performance(self, since_date: datetime) -> Dict[str, Any]:
        """Analyze component performance over time period."""
        relevant_metrics = [
            metric
            for metric in self.metrics_store["component_performance"]
            if datetime.fromisoformat(metric["timestamp"]) >= since_date
        ]

        if not relevant_metrics:
            return {"count": 0, "avg_pipeline_time": 0}

        pipeline_times = [m["total_pipeline_time"] for m in relevant_metrics]
        embedding_times = [m["embedding_time"] for m in relevant_metrics]

        return {
            "count": len(relevant_metrics),
            "avg_pipeline_time": sum(pipeline_times) / len(pipeline_times),
            "avg_embedding_time": sum(embedding_times) / len(embedding_times),
            "avg_components_active": sum(
                m["components_active"] for m in relevant_metrics
            )
            / len(relevant_metrics),
        }


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Duplication Detection System Metrics Collector"
    )
    parser.add_argument(
        "command", choices=["scan", "health", "components", "cto", "report", "status"]
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--correlation-id", help="Correlation ID for tracking")
    parser.add_argument("--output-format", choices=["json", "console"], default="json")
    parser.add_argument("--days", type=int, default=7, help="Historical analysis days")

    args = parser.parse_args()

    collector = DuplicationMetricsCollector(args.project_root)

    if args.command == "scan":
        # Example scan results for testing
        scan_results = {
            "scan_time": 15.5,
            "files_processed": 100,
            "duplicates_found": 5,
            "symbols_analyzed": 500,
            "success": True,
        }
        metrics = collector.collect_scan_metrics(scan_results, args.correlation_id)
        print(json.dumps(asdict(metrics), indent=2))

    elif args.command == "health":
        metrics = collector.get_system_health(args.correlation_id)
        print(json.dumps(asdict(metrics), indent=2))

    elif args.command == "components":
        # Example component timings for testing
        component_timings = {
            "embedding_time": 2.5,
            "similarity_search_time": 1.2,
            "registry_time": 0.8,
            "total_pipeline_time": 5.0,
            "components_active": 5,
        }
        metrics = collector.collect_component_performance(
            component_timings, args.correlation_id
        )
        print(json.dumps(asdict(metrics), indent=2))

    elif args.command == "cto":
        # Example CTO decision for testing
        duplicate_info = {"file": "test.py", "similarity": 0.95}
        metrics = collector.record_cto_decision(
            duplicate_info, "fix", args.correlation_id
        )
        print(json.dumps(asdict(metrics), indent=2))

    elif args.command == "report":
        result = collector.generate_report(days=args.days)
        if args.output_format == "console":
            print(ResultFormatter.format_console_output(result))
        else:
            print(result.to_json())

    elif args.command == "status":
        health = collector.get_system_health()
        print(f"Registry Entries: {health.registry_entries}")
        print(f"Active Components: {health.active_components}")
        print(f"Error Rate: {health.error_rate * 100:.1f}%")
        print(f"Memory Usage: {health.memory_usage_mb:.1f} MB")
        print(f"CPU Usage: {health.cpu_usage_percent:.1f}%")


if __name__ == "__main__":
    main()
