#!/usr/bin/env python3
"""
GitHub Actions Workflow Monitor for Continuous Improvement
Part of the AI-Assisted Workflows system - Phase 3 implementation.

Monitors GitHub workflow executions, collects metrics, and coordinates
with the CTO orchestrator for continuous improvement cycles.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
import hashlib
import subprocess

# Setup import paths and import utilities
try:
    from utils import path_resolver  # noqa: F401
    from core.utils.output_formatter import ResultFormatter, AnalysisResult
    from core.utils.tech_stack_detector import TechStackDetector
    from core.utils.cross_platform import PlatformDetector
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class GitHubWorkflowMonitor:
    """Monitor and coordinate GitHub Actions workflow executions."""

    def __init__(self):
        self.platform_detector = PlatformDetector()
        self.tech_detector = TechStackDetector()

        # Registry configuration
        self.registry_file = ".github/workflow-registry.json"
        self.cache_key_prefix = "claude-workflows-v1"

        # Workflow integration points
        self.workflow_triggers = {
            "continuous_improvement": {
                "event_type": "continuous-improvement-cycle",
                "schedule": "0 2 * * 1",  # Weekly at 2 AM Monday
                "description": "Trigger continuous improvement analysis cycle",
            },
            "quality_degradation": {
                "event_type": "quality-degradation-detected",
                "schedule": None,  # Event-driven only
                "description": "Trigger when quality metrics degrade",
            },
            "cto_escalation": {
                "event_type": "cto-escalation-required",
                "schedule": None,  # Event-driven only
                "description": "Escalate to CTO orchestrator for critical issues",
            },
        }

    def initialize_registry(self) -> Dict[str, Any]:
        """Initialize the workflow registry with baseline metrics."""
        registry = {
            "version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "repository_info": self._get_repository_info(),
            "baseline_metrics": {},
            "improvement_cycles": [],
            "cto_escalations": [],
            "workflow_executions": [],
        }

        # Save initial registry
        self._save_registry(registry)
        return registry

    def load_registry(self) -> Dict[str, Any]:
        """Load existing workflow registry or create new one."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    registry = json.load(f)
                    registry["updated_at"] = datetime.now(timezone.utc).isoformat()
                    return registry
            except (json.JSONDecodeError, KeyError):
                print(
                    "Warning: Invalid registry file, creating new one", file=sys.stderr
                )

        return self.initialize_registry()

    def _save_registry(self, registry: Dict[str, Any]) -> None:
        """Save registry to file with proper formatting."""
        registry["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Ensure .github directory exists
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)

        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

    def _get_repository_info(self) -> Dict[str, Any]:
        """Get basic repository information."""
        info = {
            "working_directory": os.getcwd(),
            "detected_tech_stacks": [],
            "git_info": {},
        }

        # Detect tech stacks
        try:
            info["detected_tech_stacks"] = self.tech_detector.detect_tech_stack(".")
        except Exception:
            pass

        # Get git information
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            info["git_info"]["current_branch"] = result.stdout.strip()

            # Get remote origin
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            info["git_info"]["origin_url"] = result.stdout.strip()

        except subprocess.CalledProcessError:
            pass

        return info

    def collect_workflow_metrics(self) -> Dict[str, Any]:
        """Collect current workflow execution metrics."""
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
            "workflow_name": os.environ.get("GITHUB_WORKFLOW"),
            "trigger_event": os.environ.get("GITHUB_EVENT_NAME"),
            "actor": os.environ.get("GITHUB_ACTOR"),
            "ref": os.environ.get("GITHUB_REF"),
            "sha": os.environ.get("GITHUB_SHA"),
            "repository": os.environ.get("GITHUB_REPOSITORY"),
            "analysis_results": {},
            "quality_scores": {},
            "performance_metrics": {},
            "execution_summary": {},
        }

        # Collect analysis artifacts if they exist
        artifacts_dir = Path(".")
        for artifact_file in [
            "analysis_report.json",
            "performance_profile.log",
            "security_scan_results.txt",
            "code_complexity_metrics.csv",
        ]:
            artifact_path = artifacts_dir / artifact_file
            if artifact_path.exists():
                metrics["analysis_results"][artifact_file] = {
                    "exists": True,
                    "size_bytes": artifact_path.stat().st_size,
                    "modified_time": artifact_path.stat().st_mtime,
                }

                # Extract key metrics from JSON files
                if artifact_file.endswith(".json"):
                    try:
                        with open(artifact_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            metrics["analysis_results"][artifact_file][
                                "summary"
                            ] = self._extract_analysis_summary(data)
                    except (json.JSONDecodeError, Exception):
                        pass

        return metrics

    def _extract_analysis_summary(
        self, analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract key metrics from analysis results."""
        summary = {
            "total_findings": 0,
            "severity_breakdown": {},
            "categories": {},
            "files_analyzed": 0,
        }

        try:
            # Handle different analysis result formats
            if "findings" in analysis_data:
                findings = analysis_data["findings"]
                summary["total_findings"] = len(findings)

                # Count by severity
                for finding in findings:
                    severity = finding.get("severity", "unknown")
                    summary["severity_breakdown"][severity] = (
                        summary["severity_breakdown"].get(severity, 0) + 1
                    )

                # Count by category if available
                for finding in findings:
                    category = finding.get("metadata", {}).get("category", "unknown")
                    summary["categories"][category] = (
                        summary["categories"].get(category, 0) + 1
                    )

            # Extract metadata if available
            if "metadata" in analysis_data:
                metadata = analysis_data["metadata"]
                summary["files_analyzed"] = metadata.get("files_scanned", 0)

        except (KeyError, TypeError, AttributeError):
            pass

        return summary

    def calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score from metrics."""
        score = 100.0  # Start with perfect score

        try:
            # Analyze findings from each analysis type
            for artifact_name, artifact_data in metrics.get(
                "analysis_results", {}
            ).items():
                if "summary" in artifact_data:
                    summary = artifact_data["summary"]

                    # Deduct points based on severity
                    severity_breakdown = summary.get("severity_breakdown", {})
                    score -= severity_breakdown.get("critical", 0) * 10
                    score -= severity_breakdown.get("high", 0) * 5
                    score -= severity_breakdown.get("medium", 0) * 2
                    score -= severity_breakdown.get("low", 0) * 0.5

            # Ensure score doesn't go below 0
            score = max(0.0, score)

        except (KeyError, TypeError, AttributeError):
            # If calculation fails, return neutral score
            score = 50.0

        return round(score, 2)

    def detect_quality_degradation(
        self, current_metrics: Dict[str, Any], registry: Dict[str, Any]
    ) -> bool:
        """Detect if code quality has significantly degraded."""
        current_score = self.calculate_quality_score(current_metrics)

        # Compare with recent executions
        recent_executions = registry.get("workflow_executions", [])[-5:]  # Last 5 runs
        if not recent_executions:
            return False

        # Calculate average of recent scores
        recent_scores = []
        for execution in recent_executions:
            if "quality_score" in execution:
                recent_scores.append(execution["quality_score"])

        if not recent_scores:
            return False

        avg_recent_score = sum(recent_scores) / len(recent_scores)

        # Consider degradation if current score is 20% lower than recent average
        degradation_threshold = avg_recent_score * 0.8

        return current_score < degradation_threshold

    def should_escalate_to_cto(
        self, metrics: Dict[str, Any], registry: Dict[str, Any]
    ) -> bool:
        """Determine if issues should be escalated to CTO orchestrator."""
        current_score = self.calculate_quality_score(metrics)

        # Escalate if score is critically low
        if current_score < 30.0:
            return True

        # Check for consecutive failures
        recent_executions = registry.get("workflow_executions", [])[-3:]  # Last 3 runs
        consecutive_failures = 0

        for execution in recent_executions:
            execution_score = execution.get("quality_score", 100.0)
            if execution_score < 50.0:
                consecutive_failures += 1
            else:
                break

        # Escalate after 3 consecutive poor scores
        if consecutive_failures >= 2 and current_score < 50.0:
            return True

        return False

    def trigger_repository_dispatch(
        self, event_type: str, payload: Dict[str, Any]
    ) -> bool:
        """Trigger repository dispatch event for workflow coordination."""
        if not os.environ.get("GITHUB_TOKEN"):
            print(
                "Warning: GITHUB_TOKEN not available, cannot trigger dispatch",
                file=sys.stderr,
            )
            return False

        repository = os.environ.get("GITHUB_REPOSITORY")
        if not repository:
            print("Warning: GITHUB_REPOSITORY not available", file=sys.stderr)
            return False

        try:
            import requests

            headers = {
                "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            dispatch_payload = {"event_type": event_type, "client_payload": payload}

            url = f"https://api.github.com/repos/{repository}/dispatches"
            response = requests.post(
                url, headers=headers, json=dispatch_payload, timeout=30
            )

            if response.status_code == 204:
                print(f"Successfully triggered {event_type} dispatch event")
                return True
            else:
                print(
                    f"Failed to trigger dispatch: {response.status_code} {response.text}",
                    file=sys.stderr,
                )
                return False

        except ImportError:
            print(
                "Warning: requests library not available for dispatch", file=sys.stderr
            )
            return False
        except Exception as e:
            print(f"Error triggering dispatch: {e}", file=sys.stderr)
            return False

    def generate_cache_key(self, suffix: str = "") -> str:
        """Generate cache key for GitHub Actions cache."""
        # Include repository info and current date for cache versioning
        repo_hash = hashlib.md5(
            os.environ.get("GITHUB_REPOSITORY", "unknown").encode()
        ).hexdigest()[:8]

        date_key = datetime.now().strftime("%Y-%m-%d")

        if suffix:
            return f"{self.cache_key_prefix}-{repo_hash}-{date_key}-{suffix}"
        else:
            return f"{self.cache_key_prefix}-{repo_hash}-{date_key}"

    def run_monitoring_cycle(self) -> AnalysisResult:
        """Execute complete monitoring cycle."""
        start_time = time.time()
        result = ResultFormatter.create_monitoring_result(
            "github_monitor.py", "GitHub Actions Workflow"
        )

        try:
            # Load registry
            registry = self.load_registry()

            # Collect current metrics
            current_metrics = self.collect_workflow_metrics()
            current_metrics["quality_score"] = self.calculate_quality_score(
                current_metrics
            )
            current_metrics["cache_key"] = self.generate_cache_key("monitoring")

            # Record execution in registry
            registry["workflow_executions"].append(current_metrics)

            # Keep only last 50 executions to prevent unbounded growth
            registry["workflow_executions"] = registry["workflow_executions"][-50:]

            # Check for quality degradation
            quality_degraded = self.detect_quality_degradation(
                current_metrics, registry
            )
            if quality_degraded:
                finding = ResultFormatter.create_finding(
                    "QUAL001",
                    "Quality Degradation Detected",
                    f"Quality score {current_metrics['quality_score']} is significantly lower than recent average",
                    "high",
                    self.registry_file,
                    1,
                    "Review recent changes and run targeted analysis",
                    {"score": current_metrics["quality_score"]},
                )
                result.add_finding(finding)

                # Trigger quality degradation dispatch
                self.trigger_repository_dispatch(
                    "quality-degradation-detected",
                    {
                        "quality_score": current_metrics["quality_score"],
                        "workflow_run_id": current_metrics["workflow_run_id"],
                        "timestamp": current_metrics["timestamp"],
                    },
                )

            # Check for CTO escalation
            should_escalate = self.should_escalate_to_cto(current_metrics, registry)
            if should_escalate:
                finding = ResultFormatter.create_finding(
                    "ESC001",
                    "CTO Escalation Required",
                    f"Critical quality issues detected, score: {current_metrics['quality_score']}",
                    "critical",
                    self.registry_file,
                    1,
                    "Manual intervention required - escalating to CTO orchestrator",
                    {"score": current_metrics["quality_score"]},
                )
                result.add_finding(finding)

                # Record escalation
                escalation_record = {
                    "timestamp": current_metrics["timestamp"],
                    "quality_score": current_metrics["quality_score"],
                    "workflow_run_id": current_metrics["workflow_run_id"],
                    "reason": "critical_quality_issues",
                }
                registry["cto_escalations"].append(escalation_record)

                # Trigger CTO escalation dispatch
                self.trigger_repository_dispatch(
                    "cto-escalation-required", escalation_record
                )

            # Update baseline metrics periodically
            if len(registry["workflow_executions"]) % 10 == 0:  # Every 10 runs
                registry["baseline_metrics"] = self._calculate_baseline_metrics(
                    registry
                )

            # Save updated registry
            self._save_registry(registry)

            # Set success metadata
            result.metadata = {
                "quality_score": current_metrics["quality_score"],
                "executions_tracked": len(registry["workflow_executions"]),
                "quality_degraded": quality_degraded,
                "cto_escalation": should_escalate,
                "cache_key": current_metrics["cache_key"],
            }

        except Exception as e:
            result.set_error(f"Monitoring cycle failed: {str(e)}")

        result.set_execution_time(start_time)
        return result

    def _calculate_baseline_metrics(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate baseline metrics from historical data."""
        executions = registry.get("workflow_executions", [])
        if not executions:
            return {}

        scores = [
            e.get("quality_score", 50.0) for e in executions if "quality_score" in e
        ]

        baseline = {
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "sample_size": len(scores),
            "average_quality_score": sum(scores) / len(scores) if scores else 50.0,
            "min_quality_score": min(scores) if scores else 0.0,
            "max_quality_score": max(scores) if scores else 100.0,
        }

        return baseline


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor GitHub Actions workflows for continuous improvement"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "console"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    monitor = GitHubWorkflowMonitor()
    result = monitor.run_monitoring_cycle()

    # Output based on format choice
    if args.output_format == "console":
        print(ResultFormatter.format_console_output(result))
    else:  # json (default)
        print(result.to_json())


if __name__ == "__main__":
    main()
