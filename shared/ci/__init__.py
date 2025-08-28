#!/usr/bin/env python3
"""
Continuous Improvement Framework Initialization
Part of AI-Assisted Workflows - PHASE1-002 Implementation.

This module provides the foundational continuous improvement framework
that integrates with the existing 8-agent orchestration system.
"""


# Framework components
from .detection.quality_gate_detector import QualityGateDetector, QualityGateStatus
from .framework.ci_framework import CIFramework, CIPhase, CIMetricType
from .integration.orchestration_bridge import OrchestrationBridge
from .metrics.ci_metrics_collector import (
    DuplicationScanMetrics,
    DuplicationMetricsCollector,
    ComponentPerformanceMetrics,
    SystemHealthMetrics,
    CTODecisionMetrics,
)

# Ensure proper imports are available
# Use smart imports for module access

# Version and metadata
__version__ = "1.0.0"
__author__ = "AI-Assisted Workflows"
__description__ = (
    "Continuous Improvement Framework integrated " "with 8-agent orchestration"
)

# Core exports
__all__ = [
    # Core Framework
    "CIFramework",
    "CIPhase",
    "CIMetricType",
    # Orchestration Integration
    "OrchestrationBridge",
    # Quality Gate Detection
    "QualityGateDetector",
    "QualityGateStatus",
    # Metrics Collection
    "DuplicationMetricsCollector",
    "DuplicationScanMetrics",
    "CTODecisionMetrics",
    "ComponentPerformanceMetrics",
    "SystemHealthMetrics",
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
    test_mode: bool = False,
    config_path: str = None,
) -> OrchestrationBridge:
    """
    Create an orchestration bridge for agent system integration.

    Args:
        project_root: Path to the project root directory
        test_mode: Whether to run in test mode
        config_path: Optional path to custom CI configuration

    Returns:
        OrchestrationBridge instance
    """
    return OrchestrationBridge(
        project_root, test_mode=test_mode, config_path=config_path
    )


def setup_quality_gate_detection(project_root: str = ".") -> QualityGateDetector:
    """
    Set up quality gate detection for the project.

    Args:
        project_root: Path to the project root directory

    Returns:
        QualityGateDetector instance
    """
    return QualityGateDetector(project_root)


def create_metrics_collector(project_root: str = ".") -> DuplicationMetricsCollector:
    """
    Create a metrics collector for the project.

    Args:
        project_root: Path to the project root directory

    Returns:
        DuplicationMetricsCollector instance
    """
    return DuplicationMetricsCollector(project_root)


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
