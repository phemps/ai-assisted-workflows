#!/usr/bin/env python3
"""
Orchestration Bridge for Continuous Improvement
Integrates CI workflow with the 8-agent orchestration system.
Part of Claude Code Workflows.
"""

import json
import sys
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add utils and framework to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))
sys.path.insert(0, str(script_dir / "continuous-improvement" / "framework"))

try:
    from output_formatter import AnalysisResult
    from ci_framework import CIFramework, CIPhase, CIMetricType
except ImportError as e:
    print(f"Error importing dependencies: {e}", file=sys.stderr)
    sys.exit(1)


class MessageType(Enum):
    """Message types for agent communication."""

    CI_ANALYSIS_REQUEST = "CI_ANALYSIS_REQUEST"
    CI_RECOMMENDATION = "CI_RECOMMENDATION"
    CI_METRICS_REPORT = "CI_METRICS_REPORT"
    CI_IMPROVEMENT_TASK = "CI_IMPROVEMENT_TASK"
    CI_STATUS_UPDATE = "CI_STATUS_UPDATE"


class OrchestrationBridge:
    """Bridge between CI framework and build-orchestrator agent system."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.ci_framework = CIFramework(project_root)
        self.agent_name = "continuous-improvement"

    def create_message(
        self,
        message_type: MessageType,
        to_agent: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create standardized message for agent communication."""
        return {
            "messageId": str(uuid.uuid4()),
            "correlationId": correlation_id or str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "from": self.agent_name,
            "to": to_agent,
            "type": message_type.value,
            "version": "1.0",
            "payload": payload,
        }

    def request_ci_analysis(self, correlation_id: str) -> Dict[str, Any]:
        """Request CI analysis from build-orchestrator."""
        payload = {
            "analysisType": "CONTINUOUS_IMPROVEMENT",
            "scope": "PROJECT_WIDE",
            "requestedBy": self.agent_name,
            "context": {
                "projectRoot": str(self.project_root),
                "analysisPhase": CIPhase.ANALYZE.value,
                "metricsAvailable": self._check_metrics_availability(),
            },
        }

        return self.create_message(
            MessageType.CI_ANALYSIS_REQUEST,
            "build-orchestrator",
            payload,
            correlation_id,
        )

    def create_ci_task_message(
        self, recommendation: Dict[str, Any], correlation_id: str
    ) -> Dict[str, Any]:
        """Create CI improvement task message for build-orchestrator."""
        task_id = f"CI-{int(time.time() * 1000)}"

        payload = {
            "taskId": task_id,
            "title": f"CI Improvement: {recommendation['category']}",
            "description": recommendation["description"],
            "phase": 1,  # CI tasks are phase 1 - foundational
            "dependencies": [],
            "context": {
                "ciRecommendation": recommendation,
                "priority": recommendation["priority"],
                "category": recommendation["category"],
                "automationLevel": self._determine_automation_level(recommendation),
                "requiredAgents": self._determine_required_agents(recommendation),
            },
        }

        return self.create_message(
            MessageType.CI_IMPROVEMENT_TASK,
            "build-orchestrator",
            payload,
            correlation_id,
        )

    def create_metrics_report(
        self, metrics_data: List[Dict[str, Any]], correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create metrics report for quality-monitor integration."""
        payload = {
            "reportType": "CI_METRICS",
            "timestamp": datetime.now().isoformat(),
            "metricsCount": len(metrics_data),
            "metrics": metrics_data,
            "trends": self._analyze_metrics_trends(metrics_data),
            "qualityGateImpact": self._assess_quality_gate_impact(metrics_data),
        }

        return self.create_message(
            MessageType.CI_METRICS_REPORT, "quality-monitor", payload, correlation_id
        )

    def process_orchestrator_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process response from build-orchestrator."""
        message_type = message.get("type")
        payload = message.get("payload", {})
        correlation_id = message.get("correlationId")

        response = {
            "status": "processed",
            "correlation_id": correlation_id,
            "actions": [],
        }

        if message_type == "TASK_ASSIGNMENT":
            # CI improvement task assigned
            task_id = payload.get("taskId")
            response["actions"].append(
                {
                    "type": "TASK_RECEIVED",
                    "taskId": task_id,
                    "next_step": "begin_implementation",
                }
            )

            # Record task assignment in CI framework
            self.ci_framework.record_metric(
                CIMetricType.QUALITY_GATE,
                CIPhase.IMPLEMENT,
                1.0,
                metadata={
                    "task_id": task_id,
                    "category": payload.get("context", {}).get("category"),
                    "priority": payload.get("context", {}).get("priority"),
                },
                correlation_id=correlation_id,
                agent_source="build-orchestrator",
            )

        elif message_type == "VALIDATION_REQUEST":
            # Orchestrator requesting validation of CI approach
            response["actions"].append(
                {
                    "type": "VALIDATION_REQUESTED",
                    "subject": payload.get("subject"),
                    "next_step": "perform_ci_validation",
                }
            )

        return response

    def generate_ci_recommendations(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate CI recommendations based on analysis results."""
        recommendations = []

        # Analyze findings for CI opportunities
        for finding in analysis_result.findings:
            if finding.severity.value in ["critical", "high"]:
                # High-impact findings become CI recommendations
                priority = "high" if finding.severity.value == "critical" else "medium"
                description = f"Address {finding.title}: " f"{finding.description}"

                rec_data = {
                    "category": "quality_improvement",
                    "priority": priority,
                    "description": description,
                    "metadata": {
                        "finding_id": finding.finding_id,
                        "file_path": finding.file_path,
                        "original_recommendation": finding.recommendation,
                        "evidence": finding.evidence,
                    },
                }

                rec_id = self.ci_framework.create_recommendation(
                    category=rec_data["category"],
                    priority=rec_data["priority"],
                    description=rec_data["description"],
                    metadata=rec_data["metadata"],
                )

                rec_data["id"] = rec_id
                recommendations.append(rec_data)

        # Add trend-based recommendations
        trend_recs = self._generate_trend_recommendations()
        recommendations.extend(trend_recs)

        return recommendations

    def _check_metrics_availability(self) -> Dict[str, Any]:
        """Check what CI metrics are available."""
        recent_metrics = self.ci_framework.get_metrics(
            since=datetime.now().replace(hour=0, minute=0, second=0)
        )

        metrics_by_type = {}
        for metric in recent_metrics:
            metric_type = metric["metric_type"]
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = 0
            metrics_by_type[metric_type] += 1

        return {
            "totalMetrics": len(recent_metrics),
            "metricTypes": list(metrics_by_type.keys()),
            "metricCounts": metrics_by_type,
            "hasRecentData": len(recent_metrics) > 0,
        }

    def _determine_automation_level(self, recommendation: Dict[str, Any]) -> str:
        """Determine automation level for CI recommendation."""
        category = recommendation.get("category", "")
        priority = recommendation.get("priority", "")

        # High-priority quality improvements can be automated
        automated_categories = ["quality_improvement", "build_optimization"]
        if category in automated_categories and priority == "high":
            return "FULL_AUTO"
        elif category in ["testing", "linting"]:
            return "SEMI_AUTO"
        else:
            return "MANUAL"

    def _determine_required_agents(self, recommendation: Dict[str, Any]) -> List[str]:
        """Determine which agents are required for CI recommendation."""
        category = recommendation.get("category", "")

        agent_mapping = {
            "quality_improvement": ["quality-monitor", "fullstack-developer"],
            "build_optimization": ["fullstack-developer", "git-manager"],
            "testing": ["quality-monitor", "fullstack-developer"],
            "documentation": ["documenter", "fullstack-developer"],
            "security": ["quality-monitor", "fullstack-developer"],
        }

        return agent_mapping.get(category, ["fullstack-developer"])

    def _analyze_metrics_trends(
        self, metrics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze trends in metrics data."""
        if not metrics_data:
            return {"trend": "no_data"}

        # Group by metric type
        metrics_by_type = {}
        for metric in metrics_data:
            metric_type = metric["metric_type"]
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(metric["value"])

        trends = {}
        for metric_type, values in metrics_by_type.items():
            if len(values) >= 2:
                recent_avg = sum(values[: len(values) // 2]) / (len(values) // 2)
                older_avg = sum(values[len(values) // 2 :]) / (
                    len(values) - len(values) // 2
                )

                if recent_avg > older_avg * 1.1:
                    trends[metric_type] = "improving"
                elif recent_avg < older_avg * 0.9:
                    trends[metric_type] = "declining"
                else:
                    trends[metric_type] = "stable"
            else:
                trends[metric_type] = "insufficient_data"

        return trends

    def _assess_quality_gate_impact(
        self, metrics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess impact of metrics on quality gates."""
        quality_metrics = [
            m
            for m in metrics_data
            if m["metric_type"] in ["quality_gate", "test_coverage", "build_time"]
        ]

        if not quality_metrics:
            return {"impact": "no_quality_data"}

        # < 80% success
        failing_gates = [m for m in quality_metrics if m["value"] < 0.8]

        gate_threshold = len(quality_metrics) * 0.3
        impact = "high" if len(failing_gates) > gate_threshold else "low"

        return {
            "totalQualityMetrics": len(quality_metrics),
            "failingGates": len(failing_gates),
            "impact": impact,
            "recommendAction": len(failing_gates) > 0,
        }

    def _generate_trend_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on metric trends."""
        recommendations = []

        # Analyze trends for each metric type
        for metric_type in CIMetricType:
            trend_analysis = self.ci_framework.analyze_trends(metric_type)

            is_declining = trend_analysis.get("trend") == "declining"
            has_enough_data = trend_analysis.get("metrics_count", 0) > 3

            if is_declining and has_enough_data:
                description = (
                    f"Declining trend detected in " f"{metric_type.value} metrics"
                )

                rec_data = {
                    "category": "performance_optimization",
                    "priority": "medium",
                    "description": description,
                    "metadata": {
                        "trend_analysis": trend_analysis,
                        "metric_type": metric_type.value,
                        "generated_by": "trend_analysis",
                    },
                }

                rec_id = self.ci_framework.create_recommendation(
                    category=rec_data["category"],
                    priority=rec_data["priority"],
                    description=rec_data["description"],
                    metadata=rec_data["metadata"],
                )

                rec_data["id"] = rec_id
                recommendations.append(rec_data)

        return recommendations


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CI Orchestration Bridge - Agent System Integration"
    )
    parser.add_argument(
        "command", choices=["test-message", "analyze", "recommendations"]
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--correlation-id", help="Correlation ID for message tracking")

    args = parser.parse_args()

    bridge = OrchestrationBridge(args.project_root)
    correlation_id = args.correlation_id or str(uuid.uuid4())

    if args.command == "test-message":
        # Test message creation
        message = bridge.request_ci_analysis(correlation_id)
        print("Test message created:")
        print(json.dumps(message, indent=2))

    elif args.command == "analyze":
        # Generate CI analysis report
        result = bridge.ci_framework.generate_ci_report()
        recommendations = bridge.generate_ci_recommendations(result)

        print("CI Analysis Results:")
        print(result.to_json())
        print(f"\nGenerated {len(recommendations)} recommendations")

    elif args.command == "recommendations":
        # Show pending recommendations
        recs = bridge.ci_framework.get_recommendations()
        print(f"Pending CI Recommendations: {len(recs)}")
        print(json.dumps(recs, indent=2))


if __name__ == "__main__":
    main()
