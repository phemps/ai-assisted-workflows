#!/usr/bin/env python3
"""
GitHub Reporter Module for Orchestration Bridge Refactoring (Phase 3)

Handles GitHub Actions integration and issue creation for manual review cases.
Extracted from orchestration_bridge.py lines 1088-1234.

Part of AI-Assisted Workflows - Phase 3: Breaking up God Class
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

# Setup import paths
try:
    from utils import path_resolver  # noqa: F401
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class GitHubReporter:
    """GitHub Actions integration and issue creation."""

    def __init__(
        self, project_root: str = ".", test_mode: bool = False, verbose: bool = False
    ):
        """
        Initialize GitHub reporter.

        Args:
            project_root: Root directory of the project
            test_mode: Enable test mode with simulated GitHub API calls
            verbose: Enable verbose logging
        """
        self.project_root = Path(project_root).resolve()
        self.test_mode = test_mode
        self.verbose = verbose

    def create_issue_for_finding(
        self, finding: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """
        Create GitHub issue for findings requiring manual review.

        Args:
            finding: Finding requiring manual review
            context: DuplicationContext or other context for issue creation

        Returns:
            Finding with GitHub issue creation result
        """
        try:
            evidence = finding.get("evidence", {})

            # Create issue content
            issue_content = self.format_issue_content(finding, evidence, context)
            title = issue_content["title"]
            body = issue_content["body"]

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

    def format_issue_content(
        self,
        finding: Dict[str, Any],
        evidence: Dict[str, Any] = None,
        context: Any = None,
        code_snippets: str = "",
    ) -> Dict[str, str]:
        """
        Format issue title and body for GitHub issue creation.

        Args:
            finding: Finding to format
            evidence: Evidence data from finding
            context: DuplicationContext or other context
            code_snippets: Optional code snippets to include

        Returns:
            Dictionary with 'title' and 'body' keys
        """
        if evidence is None:
            evidence = finding.get("evidence", {})

        # Create issue title
        title = f"Code Duplication Review: {finding.get('title', 'Duplicate Code Detected')}"

        # Build reason list for manual review
        manual_review_reasons = []
        if hasattr(context, "cross_module_impact") and context.cross_module_impact:
            manual_review_reasons.append("Cross-module impact detected")
        if hasattr(context, "is_public_api") and context.is_public_api:
            manual_review_reasons.append("Public API affected")
        if (
            hasattr(context, "test_coverage_percentage")
            and context.test_coverage_percentage < 70
        ):
            manual_review_reasons.append("Low test coverage")
        if (
            hasattr(context, "cyclomatic_complexity")
            and context.cyclomatic_complexity > 5
        ):
            manual_review_reasons.append("High complexity")
        if hasattr(context, "similarity_score") and context.similarity_score < 0.8:
            manual_review_reasons.append("Moderate similarity requiring analysis")

        # If no specific reasons, add default
        if not manual_review_reasons:
            manual_review_reasons.append("Complexity requires human judgment")

        # Create issue body
        body = f"""## Code Duplication Detected

**Similarity Score**: {evidence.get('similarity_score', 0):.0%}
**Severity**: {finding.get('severity', 'unknown').upper()}
**Files Affected**: {getattr(context, 'file_count', 2) if context else 2}

### Description
{finding.get('description', 'Duplicate code patterns detected that require manual review.')}

### Evidence
- **Similarity Score**: {evidence.get('similarity_score', 0):.0%}
- **Confidence**: {evidence.get('confidence', 0):.2f}
- **Comparison Type**: {evidence.get('comparison_type', 'unknown')}

### Files Involved
{self._format_file_list(evidence)}

### Recommended Action
Manual review is recommended because:
{chr(10).join(f'- {reason}' for reason in manual_review_reasons)}

### Next Steps
1. Review the duplicate code patterns
2. Determine if consolidation is appropriate
3. If consolidating, create implementation plan
4. Test thoroughly due to complexity/risk factors

{code_snippets}

---
*This issue was automatically created by the AI-Assisted Workflows continuous improvement system.*
"""

        return {"title": title, "body": body}

    def _create_issue_with_gh_cli(self, title: str, body: str) -> Dict[str, Any]:
        """Create GitHub issue using gh CLI."""
        try:
            # In test mode, simulate the GitHub CLI call
            if self.test_mode:
                return {
                    "status": "simulated_success",
                    "issue_url": "https://github.com/test/repo/issues/123",
                    "message": "Simulated GitHub issue creation completed",
                }

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

            if self.verbose:
                print(f"Creating GitHub issue: {title}")

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

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "message": "GitHub issue creation timed out",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Error creating GitHub issue",
            }

    def _format_file_list(self, evidence: Dict[str, Any]) -> str:
        """Format file list from evidence."""
        files = []

        # Handle different evidence formats
        if "file_pair" in evidence:
            file_pair = evidence["file_pair"]
            for i, file_path in enumerate(file_pair):
                files.append(f"- File {i+1}: `{file_path}`")
        elif "original_symbol" in evidence:
            files.append(
                f"- Original: `{evidence['original_symbol'].get('file', 'unknown')}`"
            )
        if "duplicate_symbol" in evidence:
            files.append(
                f"- Duplicate: `{evidence['duplicate_symbol'].get('file', 'unknown')}`"
            )

        # Handle multiple duplicates
        if "duplicate_symbols" in evidence:
            duplicate_symbols = evidence["duplicate_symbols"]
            unique_files = set()
            for symbol in duplicate_symbols:
                if "file" in symbol:
                    unique_files.add(symbol["file"])

            for file_path in sorted(unique_files):
                files.append(f"- `{file_path}`")

        return (
            "\n".join(files) if files else "- Files will be identified during analysis"
        )
