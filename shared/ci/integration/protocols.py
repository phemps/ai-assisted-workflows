#!/usr/bin/env python3
"""
Protocol Interfaces for Orchestration Bridge Refactoring (Phase 3)

Defines clear contracts between modules using Python Protocols for type safety,
testability, and dependency injection. These protocols establish the boundaries
between the refactored modules from the god class orchestration_bridge.py.

Part of AI-Assisted Workflows - Phase 3: Breaking up God Class
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class ExpertRouterProtocol(Protocol):
    """Protocol for expert agent routing and task management."""

    @abstractmethod
    def route_findings_to_experts(
        self, aggregated_findings: List[Dict[str, Any]], verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Route findings to appropriate expert agents based on language and complexity.

        Args:
            aggregated_findings: List of duplicate findings grouped by pairs
            verbose: Enable verbose logging

        Returns:
            List of findings with expert review results
        """
        ...

    @abstractmethod
    def detect_primary_language(self, findings: List[Dict[str, Any]]) -> str:
        """
        Detect the primary programming language from findings.

        Args:
            findings: List of duplicate findings

        Returns:
            Primary language detected (e.g., "python", "typescript", "mixed")
        """
        ...


class DecisionEngineProtocol(Protocol):
    """Protocol for decision matrix integration and action determination."""

    @abstractmethod
    def process_single_finding(
        self, finding: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process single finding through decision matrix to determine action.

        Args:
            finding: Individual duplicate finding
            context: Optional context for decision making

        Returns:
            Finding with decision result and recommended action
        """
        ...

    @abstractmethod
    def create_context_from_finding(self, finding: Dict[str, Any]) -> Any:
        """
        Convert finding to DuplicationContext for decision matrix.

        Args:
            finding: Duplicate finding to convert

        Returns:
            DuplicationContext object for decision matrix
        """
        ...

    @abstractmethod
    def execute_automatic_fix(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute automatic fix for duplicate if decision matrix recommends it.

        Args:
            finding: Finding with auto-fix decision

        Returns:
            Finding with execution result
        """
        ...


class GitHubReporterProtocol(Protocol):
    """Protocol for GitHub Actions integration and issue creation."""

    @abstractmethod
    def create_issue_for_finding(
        self, finding: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """
        Create GitHub issue for findings requiring manual review.

        Args:
            finding: Finding requiring manual review
            context: Additional context for issue creation

        Returns:
            Finding with GitHub issue creation result
        """
        ...

    @abstractmethod
    def format_issue_content(
        self, finding: Dict[str, Any], code_snippets: str = ""
    ) -> Dict[str, str]:
        """
        Format issue title and body for GitHub issue creation.

        Args:
            finding: Finding to format
            code_snippets: Optional code snippets to include

        Returns:
            Dictionary with 'title' and 'body' keys
        """
        ...


class FindingProcessorProtocol(Protocol):
    """Protocol for finding aggregation and utility functions."""

    @abstractmethod
    def aggregate_findings(
        self, findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Group findings by duplicate pairs for processing.

        Args:
            findings: Raw duplicate findings

        Returns:
            Aggregated findings grouped by duplicate pairs
        """
        ...

    @abstractmethod
    def create_summary(
        self, findings: List[Dict[str, Any]], total_time: float
    ) -> Dict[str, Any]:
        """
        Create summary of duplicate detection analysis.

        Args:
            findings: List of processed findings
            total_time: Total processing time in seconds

        Returns:
            Summary with statistics and metadata
        """
        ...

    @abstractmethod
    def create_code_snippets_section(self, finding: Dict[str, Any]) -> str:
        """
        Generate code snippets section for findings with file content.

        Args:
            finding: Finding to generate snippets for

        Returns:
            Formatted code snippets as markdown string
        """
        ...

    @abstractmethod
    def save_analysis_report(
        self,
        findings: List[Dict[str, Any]],
        summary: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> bool:
        """
        Save complete analysis report to file.

        Args:
            findings: List of processed findings
            summary: Analysis summary
            output_path: Optional custom output path

        Returns:
            True if save successful, False otherwise
        """
        ...


class OrchestratorConfigProtocol(Protocol):
    """Protocol for orchestrator configuration management."""

    @abstractmethod
    def load_ci_config(self) -> Dict[str, Any]:
        """
        Load CI configuration from .ci-registry/ci_config.json.

        Returns:
            Configuration dictionary with project settings
        """
        ...

    @abstractmethod
    def initialize_duplicate_finder(
        self, test_mode: bool = False, verbose: bool = False
    ) -> Any:
        """
        Initialize DuplicateFinder with CI configuration.

        Args:
            test_mode: Enable test mode
            verbose: Enable verbose logging

        Returns:
            Configured DuplicateFinder instance
        """
        ...


# Type aliases for common data structures
FindingDict = Dict[str, Any]
SummaryDict = Dict[str, Any]
ConfigDict = Dict[str, Any]
ExpertResult = Dict[str, Any]
DecisionResult = Dict[str, Any]
GitHubResult = Dict[str, Any]
