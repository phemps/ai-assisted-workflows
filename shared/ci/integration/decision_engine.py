#!/usr/bin/env python3
"""
Decision Engine Module for Orchestration Bridge Refactoring (Phase 3)

Handles decision matrix logic, context creation, and action determination.
Extracted from orchestration_bridge.py lines 963-1261.

Part of AI-Assisted Workflows - Phase 3: Breaking up God Class
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Setup import paths
try:
    from utils import path_resolver  # noqa: F401
    from ci.workflows.decision_matrix import (
        DecisionMatrix,
        ActionType,
        DuplicationContext,
    )
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class DecisionEngine:
    """Decision matrix integration and action determination."""

    def __init__(
        self, project_root: str = ".", test_mode: bool = False, verbose: bool = False
    ):
        """
        Initialize decision engine.

        Args:
            project_root: Root directory of the project
            test_mode: Enable test mode with simulated responses
            verbose: Enable verbose logging
        """
        self.project_root = Path(project_root).resolve()
        self.test_mode = test_mode
        self.verbose = verbose
        self.decision_matrix = DecisionMatrix()

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
        try:
            # Convert finding to DuplicationContext
            duplication_context = self.create_context_from_finding(finding)

            # Get CTO decision
            decision = self.decision_matrix.evaluate(duplication_context)

            if decision.action == ActionType.AUTOMATIC_FIX:
                return self.execute_automatic_fix(finding, duplication_context)
            elif decision.action == ActionType.HUMAN_REVIEW:
                from ci.integration.github_reporter import GitHubReporter

                github_reporter = GitHubReporter(
                    self.project_root, self.test_mode, self.verbose
                )
                return github_reporter.create_issue_for_finding(
                    finding, duplication_context
                )
            else:  # SKIP
                return {
                    "action": "skipped",
                    "reason": decision.justification,
                    "finding_id": finding.get("finding_id", "unknown"),
                }

        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "finding_id": finding.get("finding_id", "unknown"),
            }

    def create_context_from_finding(
        self, finding: Dict[str, Any]
    ) -> DuplicationContext:
        """
        Convert finding to DuplicationContext for decision matrix.

        Args:
            finding: Duplicate finding to convert

        Returns:
            DuplicationContext object for decision matrix
        """
        evidence = finding.get("evidence", {})

        return DuplicationContext(
            similarity_score=evidence.get("similarity_score", 0),
            file_count=2,  # Minimum for duplicates
            total_line_count=evidence.get("total_lines", 50),
            symbol_types=evidence.get("symbol_types", ["function"]),
            cross_module_impact=evidence.get("cross_module", False),
            test_coverage_percentage=evidence.get(
                "test_coverage", 85.0
            ),  # Higher default for auto-fix eligibility
            cyclomatic_complexity=evidence.get(
                "complexity", 3
            ),  # Lower complexity for simple functions
            dependency_count=evidence.get(
                "dependencies", 1
            ),  # Fewer dependencies for simple functions
            is_public_api=evidence.get("is_public", False),
            has_documentation=evidence.get("documented", True),
            last_modified_days_ago=evidence.get(
                "last_modified_days", 60
            ),  # Older = more stable
        )

    def execute_automatic_fix(
        self, finding: Dict[str, Any], context: Optional[DuplicationContext] = None
    ) -> Dict[str, Any]:
        """
        Execute automatic fix for duplicate if decision matrix recommends it.

        Args:
            finding: Finding with auto-fix decision
            context: Optional DuplicationContext

        Returns:
            Finding with execution result
        """
        try:
            # Create context if not provided
            if context is None:
                context = self.create_context_from_finding(finding)

            # Create simple implementation plan
            plan_text = self._create_implementation_plan(finding, context)

            # Write plan to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(plan_text)
                plan_file_path = f.name

            # Call claude with todo-orchestrate command
            if self.verbose:
                print(
                    f"🤖 Executing automatic fix via claude /todo-orchestrate for {finding.get('title', 'duplicate')}"
                )

            result = self._call_claude_todo_orchestrate(plan_file_path)

            # Clean up temporary file
            Path(plan_file_path).unlink(missing_ok=True)

            return {
                "action": "automatic_fix",
                "status": result.get("status", "unknown"),
                "finding_id": finding.get("finding_id", "unknown"),
                "orchestration_result": result,
            }

        except Exception as e:
            return {
                "action": "automatic_fix",
                "status": "error",
                "error": str(e),
                "finding_id": finding.get("finding_id", "unknown"),
            }

    def _create_implementation_plan(
        self, finding: Dict[str, Any], context: DuplicationContext
    ) -> str:
        """Create a simple implementation plan for todo-orchestrate."""
        evidence = finding.get("evidence", {})

        return f"""# Code Duplication Refactoring Plan

## Overview
**Finding**: {finding.get('title', 'Code Duplication Detected')}
**Similarity Score**: {evidence.get('similarity_score', 0):.0%}
**Files Affected**: {context.file_count}
**Priority**: {"High" if context.similarity_score > 0.8 else "Medium"}

## Description
{finding.get('description', 'Duplicate code patterns detected that should be consolidated.')}

## Implementation Tasks

### Phase 1: Analysis and Planning
- [ ] Use Serena to identify all instances of the duplicate code pattern
- [ ] Analyze dependencies and usage patterns
- [ ] Determine optimal refactoring approach (extract method, create shared utility, etc.)

### Phase 2: Refactoring Implementation
- [ ] Create shared component/function to consolidate duplicate code
- [ ] Update all affected files to use the shared implementation
- [ ] Ensure consistent parameter passing and return values

### Phase 3: Validation
- [ ] Run all existing tests to ensure no regressions
- [ ] Add tests for the new shared component if needed
- [ ] Verify code still functions as expected

## Files to Review
{self._format_file_list(evidence)}

## Acceptance Criteria
- [ ] All duplicate code consolidated into shared component
- [ ] No functional changes to existing behavior
- [ ] All tests passing
- [ ] Code quality gates satisfied

## Quality Gates
- All existing tests must pass
- No linting errors
- Code coverage maintained or improved
"""

    def _format_file_list(self, evidence: Dict[str, Any]) -> str:
        """Format file list from evidence."""
        files = []
        if "original_symbol" in evidence:
            files.append(f"- {evidence['original_symbol'].get('file', 'unknown')}")
        if "duplicate_symbol" in evidence:
            files.append(f"- {evidence['duplicate_symbol'].get('file', 'unknown')}")
        return (
            "\n".join(files) if files else "- Files will be identified during analysis"
        )

    def _call_claude_todo_orchestrate(self, plan_file_path: str) -> Dict[str, Any]:
        """Call claude with the todo-orchestrate command."""
        try:
            # In test mode, simulate the call
            if self.test_mode:
                return {
                    "status": "simulated_success",
                    "stdout": "Simulated todo-orchestrate execution completed",
                    "message": "Simulated todo-orchestrate completed successfully",
                }

            # Build claude command
            cmd = ["claude", f"/todo-orchestrate {plan_file_path}"]

            if self.verbose:
                print(f"Executing: {' '.join(cmd)}")

            # Execute command with timeout
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "stdout": result.stdout,
                    "message": "todo-orchestrate completed successfully",
                }
            else:
                return {
                    "status": "failure",
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "message": "todo-orchestrate failed",
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "message": "todo-orchestrate timed out after 5 minutes",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to execute todo-orchestrate",
            }
