#!/usr/bin/env python3
"""
Orchestration Bridge for Code Duplication Detection
Bridges duplication detection with Claude Code todo-orchestrate workflow.
Removes duplication by directly calling existing claude commands.

DESIGN PRINCIPLE: Don't recreate existing workflows - call them.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add utils and core components to path
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "utils"))
sys.path.insert(0, str(script_dir / "continuous-improvement" / "core"))

# Import core duplication detection components - REQUIRED
try:
    from duplicate_finder import DuplicateFinder, DuplicateFinderConfig
except ImportError as e:
    print(f"FATAL: DuplicateFinder not available: {e}", file=sys.stderr)
    sys.exit(1)

# Import CTO decision logic - REQUIRED
try:
    from decision_matrix import DecisionMatrix, ActionType, DuplicationContext
except ImportError as e:
    print(f"FATAL: DecisionMatrix not available: {e}", file=sys.stderr)
    sys.exit(1)


class SimplifiedOrchestrationBridge:
    """
    Simplified bridge that delegates to existing Claude Code workflows.

    Purpose: When CTO decision logic determines a fix is needed, create a
    simple implementation plan and pass it to claude /todo-orchestrate.

    No duplication of workflow logic - just calls the existing command.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.duplicate_finder = self._initialize_duplicate_finder()
        self.decision_matrix = DecisionMatrix()

    def _initialize_duplicate_finder(self) -> DuplicateFinder:
        """Initialize duplicate finder with fail-fast behavior."""
        try:
            config = DuplicateFinderConfig(
                analysis_mode="targeted", enable_caching=True, batch_size=50
            )
            return DuplicateFinder(config, self.project_root)
        except Exception as e:
            print(f"FATAL: Cannot initialize DuplicateFinder: {e}", file=sys.stderr)
            sys.exit(1)

    def process_duplicates_for_github_actions(
        self, changed_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for GitHub Actions workflow.

        1. Run duplicate detection
        2. Use CTO decision matrix
        3. For automatic fixes: call claude /todo-orchestrate
        4. For manual review: create GitHub issue

        Args:
            changed_files: Optional list of changed files to focus analysis

        Returns:
            Processing results for GitHub Actions
        """
        try:
            # Step 1: Analyze for duplicates
            print("🔍 Analyzing project for code duplication...")
            if changed_files:
                # Convert to Path objects and run incremental analysis
                changed_paths = [Path(f) for f in changed_files]
                analysis_result = self.duplicate_finder.incremental_analysis(
                    changed_paths
                )
            else:
                analysis_result = self.duplicate_finder.analyze_project()

            findings_count = len(analysis_result.findings)
            print(f"📊 Found {findings_count} potential duplicate(s)")

            if findings_count == 0:
                return {
                    "status": "success",
                    "action": "no_duplicates_found",
                    "results": [],
                }

            # Step 2: Process each finding through CTO decision matrix
            results = []
            for finding in analysis_result.findings:
                result = self._process_single_duplicate(finding)
                results.append(result)

            # Step 3: Create summary
            summary = self._create_summary(results)

            return {
                "status": "success",
                "findings_processed": findings_count,
                "summary": summary,
                "results": results,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Duplicate analysis failed - see logs for details",
            }

    def _process_single_duplicate(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single duplicate finding through CTO decision matrix."""
        try:
            # Convert finding to DuplicationContext
            context = self._finding_to_context(finding)

            # Get CTO decision
            decision = self.decision_matrix.evaluate(context)

            if decision.action == ActionType.AUTOMATIC_FIX:
                return self._execute_automatic_fix(finding, context)
            elif decision.action == ActionType.HUMAN_REVIEW:
                return self._create_github_issue(finding, context)
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

    def _execute_automatic_fix(
        self, finding: Dict[str, Any], context: DuplicationContext
    ) -> Dict[str, Any]:
        """Execute automatic fix by calling claude /todo-orchestrate."""
        try:
            # Create simple implementation plan
            plan_text = self._create_implementation_plan(finding, context)

            # Write plan to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(plan_text)
                plan_file_path = f.name

            # Call claude with todo-orchestrate command
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
**Similarity Score**: {evidence.get('similarity_score', 0):.2%}
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
            # Build claude command
            cmd = ["claude", f"/todo-orchestrate {plan_file_path}"]

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

    def _create_github_issue(
        self, finding: Dict[str, Any], context: DuplicationContext
    ) -> Dict[str, Any]:
        """Create GitHub issue for manual review cases."""
        try:
            evidence = finding.get("evidence", {})

            # Create issue title
            title = f"Code Duplication Review: {finding.get('title', 'Duplicate Code Detected')}"

            # Create issue body
            body = f"""## Code Duplication Detected

**Similarity Score**: {evidence.get('similarity_score', 0):.2%}
**Severity**: {finding.get('severity', 'unknown').upper()}
**Files Affected**: {context.file_count}

### Description
{finding.get('description', 'Duplicate code patterns detected that require manual review.')}

### Evidence
- **Similarity Score**: {evidence.get('similarity_score', 0):.2%}
- **Confidence**: {evidence.get('confidence', 0):.2%}
- **Comparison Type**: {evidence.get('comparison_type', 'unknown')}

### Files Involved
{self._format_file_list(evidence)}

### Recommended Action
Manual review is recommended because:
- {context.cross_module_impact and "Cross-module impact detected"}
- {context.is_public_api and "Public API affected"}
- {context.test_coverage_percentage < 70 and "Low test coverage"}

### Next Steps
1. Review the duplicate code patterns
2. Determine if consolidation is appropriate
3. If consolidating, create implementation plan
4. Test thoroughly due to complexity/risk factors
"""

            # Use GitHub CLI to create issue
            result = self._create_issue_with_gh_cli(title, body)

            return {
                "action": "github_issue",
                "status": result.get("status", "unknown"),
                "finding_id": finding.get("finding_id", "unknown"),
                "issue_result": result,
            }

        except Exception as e:
            return {
                "action": "github_issue",
                "status": "error",
                "error": str(e),
                "finding_id": finding.get("finding_id", "unknown"),
            }

    def _create_issue_with_gh_cli(self, title: str, body: str) -> Dict[str, Any]:
        """Create GitHub issue using gh CLI."""
        try:
            cmd = [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                "code-duplication,technical-debt",
            ]

            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                issue_url = result.stdout.strip()
                return {
                    "status": "success",
                    "issue_url": issue_url,
                    "message": f"GitHub issue created: {issue_url}",
                }
            else:
                return {
                    "status": "failure",
                    "returncode": result.returncode,
                    "stderr": result.stderr,
                    "message": "Failed to create GitHub issue",
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Error creating GitHub issue",
            }

    def _finding_to_context(self, finding: Dict[str, Any]) -> DuplicationContext:
        """Convert finding dict to DuplicationContext for decision matrix."""
        evidence = finding.get("evidence", {})

        return DuplicationContext(
            similarity_score=evidence.get("similarity_score", 0),
            file_count=2,  # Minimum for duplicates
            total_line_count=evidence.get("total_lines", 50),
            symbol_types=evidence.get("symbol_types", ["function"]),
            cross_module_impact=evidence.get("cross_module", False),
            test_coverage_percentage=evidence.get("test_coverage", 75.0),
            cyclomatic_complexity=evidence.get("complexity", 5),
            dependency_count=evidence.get("dependencies", 3),
            is_public_api=evidence.get("is_public", False),
            has_documentation=evidence.get("documented", True),
            last_modified_days_ago=evidence.get("last_modified_days", 30),
        )

    def _create_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of processing results."""
        summary = {
            "automatic_fixes": 0,
            "github_issues": 0,
            "skipped": 0,
            "errors": 0,
            "successes": 0,
        }

        for result in results:
            action = result.get("action", "unknown")
            status = result.get("status", "unknown")

            if action == "automatic_fix":
                summary["automatic_fixes"] += 1
            elif action == "github_issue":
                summary["github_issues"] += 1
            elif action == "skipped":
                summary["skipped"] += 1
            elif action == "error":
                summary["errors"] += 1

            if status == "success":
                summary["successes"] += 1

        return summary


def main():
    """Main entry point for GitHub Actions workflow."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Simplified orchestration bridge for code duplication"
    )
    parser.add_argument(
        "--changed-files", nargs="*", help="List of changed files to analyze"
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    # Initialize bridge
    bridge = SimplifiedOrchestrationBridge(args.project_root)

    # Process duplicates
    result = bridge.process_duplicates_for_github_actions(args.changed_files)

    # Output results as JSON for GitHub Actions
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
