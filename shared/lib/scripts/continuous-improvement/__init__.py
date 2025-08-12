#!/usr/bin/env python3
"""
Continuous Improvement Framework Initialization
Part of Claude Code Workflows - PHASE1-002 Implementation.

This module provides the foundational continuous improvement framework
that integrates with the existing 8-agent orchestration system.
"""

import sys
from pathlib import Path

# Framework components
from .detection.quality_gate_detector import QualityGateDetector, QualityGateStatus
from .framework.ci_framework import CIFramework, CIPhase, CIMetricType
from .integration.orchestration_bridge import SimplifiedOrchestrationBridge
from .metrics.ci_metrics_collector import (
    BuildMetrics,
    CIMetricsCollector,
    PerformanceMetrics,
    QualityMetrics,
    TestMetrics,
)

# Ensure proper imports are available
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir / "utils"))

# Version and metadata
__version__ = "1.0.0"
__author__ = "Claude Code Workflows"
__description__ = (
    "Continuous Improvement Framework integrated " "with 8-agent orchestration"
)

# Core exports
__all__ = [
    # Core Framework
    "CIFramework",
    "CIPhase",
    "CIMetricType",
    # Orchestration Integration (Simplified)
    "SimplifiedOrchestrationBridge",
    # Quality Gate Detection
    "QualityGateDetector",
    "QualityGateStatus",
    # Metrics Collection
    "CIMetricsCollector",
    "BuildMetrics",
    "TestMetrics",
    "QualityMetrics",
    "PerformanceMetrics",
]


def initialize_ci_framework(project_root: str = ".") -> CIFramework:
    """
    Initialize the CI framework for a project.

    Args:
        project_root: Path to the project root directory

    Returns:
        Initialized CIFramework instance
    """
    return CIFramework(project_root)


def create_orchestration_bridge(
    project_root: str = ".",
) -> SimplifiedOrchestrationBridge:
    """
    Create a simplified orchestration bridge for agent system integration.

    Args:
        project_root: Path to the project root directory

    Returns:
        SimplifiedOrchestrationBridge instance
    """
    return SimplifiedOrchestrationBridge(project_root)


def setup_quality_gate_detection(project_root: str = ".") -> QualityGateDetector:
    """
    Set up quality gate detection for the project.

    Args:
        project_root: Path to the project root directory

    Returns:
        QualityGateDetector instance
    """
    return QualityGateDetector(project_root)


def create_metrics_collector(project_root: str = ".") -> CIMetricsCollector:
    """
    Create a metrics collector for the project.

    Args:
        project_root: Path to the project root directory

    Returns:
        CIMetricsCollector instance
    """
    return CIMetricsCollector(project_root)


# Integration status and info
INTEGRATION_INFO = {
    "status": "PHASE1-002 Foundation Implemented",
    "version": __version__,
    "components": [
        "CI Framework Core",
        "Orchestration Bridge",
        "Quality Gate Detection",
        "Metrics Collection",
    ],
    "agent_integration": {
        "build-orchestrator": "Task assignment and workflow coordination",
        "quality-monitor": "Dynamic quality gate detection and execution",
        "git-manager": "Commit orchestration integration",
        "fullstack-developer": "Implementation execution",
    },
    "next_phases": [
        "PHASE2: Advanced Analytics and ML-based Recommendations",
        "PHASE3: Automated Improvement Implementation",
        "PHASE4: Multi-project CI Optimization",
    ],
}
