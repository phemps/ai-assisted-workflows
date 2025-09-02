#!/usr/bin/env python3
"""
Finding Processor Module for Orchestration Bridge Refactoring (Phase 3)

Handles finding aggregation, summary creation, and utility functions.
Extracted from orchestration_bridge.py lines 147-230, 1262-1344.

Part of AI-Assisted Workflows - Phase 3: Breaking up God Class
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup import paths
try:
    from utils import path_resolver  # noqa: F401
    from ci.integration.orchestration_bridge import (
        CustomJSONEncoder,
    )  # Import from original
except ImportError:
    try:
        from utils import path_resolver  # noqa: F401

        # Define CustomJSONEncoder locally if import fails
        import numpy as np

        class CustomJSONEncoder(json.JSONEncoder):
            """Custom JSON encoder that handles numpy types and other non-serializable objects."""

            def default(self, obj):
                if isinstance(obj, (np.integer, np.int32, np.int64)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float32, np.float64)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, Path):
                    return str(obj)
                elif hasattr(obj, "__dict__"):
                    return obj.__dict__
                return super().default(obj)

    except ImportError as e:
        print(f"Import error: {e}", file=sys.stderr)
        sys.exit(1)


class FindingProcessor:
    """Finding aggregation and utility functions."""

    def __init__(self, project_root: str = ".", verbose: bool = False):
        """
        Initialize finding processor.

        Args:
            project_root: Root directory of the project
            verbose: Enable verbose logging
        """
        self.project_root = Path(project_root).resolve()
        self.verbose = verbose

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
        # Group findings by the pair of files involved
        file_pairs = defaultdict(list)

        for finding in findings:
            evidence = finding.get("evidence", {})
            orig = evidence.get("original_symbol", {})
            dup = evidence.get("duplicate_symbol", {})

            orig_file = orig.get("file", "")
            dup_file = dup.get("file", "")

            # Create a consistent pair key (sorted to avoid duplicates)
            if orig_file and dup_file:
                file_pair = tuple(sorted([orig_file, dup_file]))
                file_pairs[file_pair].append(finding)

        # Create aggregated findings for each file pair
        aggregated = []

        for file_pair, pair_findings in file_pairs.items():
            if len(pair_findings) < 1:  # Skip if no duplicates
                continue

            # Calculate aggregate metrics
            total_similarity = sum(
                f.get("evidence", {}).get("similarity_score", 0) for f in pair_findings
            )
            avg_similarity = total_similarity / len(pair_findings)

            # Get symbol types involved
            symbol_types = set()
            duplicate_symbols = []

            for finding in pair_findings:
                evidence = finding.get("evidence", {})
                orig = evidence.get("original_symbol", {})
                dup = evidence.get("duplicate_symbol", {})

                symbol_types.add(orig.get("type", "unknown"))
                symbol_types.add(dup.get("type", "unknown"))

                duplicate_symbols.append(
                    {
                        "original": orig.get("name", ""),
                        "duplicate": dup.get("name", ""),
                        "similarity": evidence.get("similarity_score", 0),
                    }
                )

            # Create aggregated finding
            aggregated_finding = {
                "finding_id": f"aggregated_{len(aggregated):03d}",
                "title": f"Multiple duplicates between {Path(file_pair[0]).name} and {Path(file_pair[1]).name}",
                "description": f"Found {len(pair_findings)} duplicate patterns between files with average similarity {avg_similarity:.2f}",
                "severity": "high" if avg_similarity >= 0.85 else "medium",
                "evidence": {
                    "file_pair": file_pair,
                    "duplicate_count": len(pair_findings),
                    "average_similarity": avg_similarity,
                    "symbol_types": list(symbol_types),
                    "duplicate_symbols": duplicate_symbols,
                    "individual_findings": pair_findings,
                },
            }

            aggregated.append(aggregated_finding)

        # Sort by severity and duplicate count
        aggregated.sort(
            key=lambda x: (
                x["evidence"]["average_similarity"],
                x["evidence"]["duplicate_count"],
            ),
            reverse=True,
        )

        return aggregated

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
        summary = {
            "expert_reviews": 0,
            "automatic_fixes": 0,
            "github_issues": 0,
            "skipped": 0,
            "errors": 0,
            "successes": 0,
            "agents_used": set(),
            "total_processing_time": total_time,
            "total_findings": len(findings),
        }

        for result in findings:
            action = result.get("action", "unknown")
            status = result.get("status", "unknown")
            agent = result.get("agent", "")

            if action == "expert_review":
                summary["expert_reviews"] += 1
                if agent:
                    summary["agents_used"].add(agent)
            elif action == "automatic_fix":
                summary["automatic_fixes"] += 1
            elif action == "github_issue":
                summary["github_issues"] += 1
            elif action == "skipped":
                summary["skipped"] += 1
            elif action in ["error", "expert_review_error"]:
                summary["errors"] += 1

            if status in ["success", "completed", "simulated_success"]:
                summary["successes"] += 1

        # Convert set to list for JSON serialization
        summary["agents_used"] = list(summary["agents_used"])
        return summary

    def create_code_snippets_section(self, finding: Dict[str, Any]) -> str:
        """
        Generate code snippets section for findings with file content.

        Args:
            finding: Finding to generate snippets for

        Returns:
            Formatted code snippets as markdown string
        """
        evidence = finding.get("evidence", {})
        individual_findings = evidence.get("individual_findings", [])
        file_pair = evidence.get("file_pair", [])

        if not file_pair or len(file_pair) < 2:
            return ""

        snippets_info = []
        snippet_count = 0
        max_snippets = 10  # Limit per finding

        file1_name = Path(file_pair[0]).name
        file2_name = Path(file_pair[1]).name

        snippets_info.append(f"\n### Code Snippets: {file1_name} ↔ {file2_name}")

        # Show first few actual code snippets from individual findings
        for idx, individual in enumerate(
            individual_findings[:5]
        ):  # Max 5 per file pair
            if snippet_count >= max_snippets:
                break

            evidence = individual.get("evidence", {})
            orig_symbol = evidence.get("original_symbol", {})
            dup_symbol = evidence.get("duplicate_symbol", {})

            orig_content = orig_symbol.get("content", "")
            dup_content = dup_symbol.get("content", "")
            orig_line = orig_symbol.get("line", "")
            dup_line = dup_symbol.get("line", "")
            similarity = evidence.get("similarity_score", 0)

            if orig_content and dup_content:
                snippets_info.append(
                    f"""
**Duplicate {snippet_count + 1}** (similarity: {similarity:.2f}):
```
{file1_name}:{orig_line} | {orig_content[:200]}{'...' if len(orig_content) > 200 else ''}
{file2_name}:{dup_line} | {dup_content[:200]}{'...' if len(dup_content) > 200 else ''}
```"""
                )
                snippet_count += 1

        if snippet_count == 0:
            snippets_info.append(
                "*Code snippets not available - use Serena MCP for detailed analysis*"
            )

        return "\n".join(snippets_info)

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
        try:
            # Create reports directory
            if output_path:
                reports_dir = output_path.parent
                report_file = output_path
            else:
                reports_dir = Path(self.project_root) / ".ci-registry" / "reports"
                report_file = reports_dir / "latest-analysis.json"

            reports_dir.mkdir(parents=True, exist_ok=True)

            # Create comprehensive report
            report_data = {
                "timestamp": time.time(),
                "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "status": "completed",
                "findings": findings,
                "summary": summary,
                "config": {
                    "similarity_threshold": 0.85,  # TODO: Get from actual config
                    "project_root": str(self.project_root),
                    "analysis_mode": "github_actions",
                },
                "metadata": {
                    "analysis_type": "duplicate_detection",
                    "workflow_trigger": "github_actions",
                    "findings_processed": len(findings),
                    "action": "analysis_completed",
                },
            }

            # Save main analysis report
            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=2, cls=CustomJSONEncoder)

            if self.verbose:
                print(
                    f"✅ Analysis report saved to {report_file.relative_to(self.project_root)}"
                )

            # Also save timestamped report for history if using default path
            if not output_path:
                timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
                historical_file = reports_dir / f"analysis_{timestamp}.json"
                with open(historical_file, "w") as f:
                    json.dump(report_data, f, indent=2, cls=CustomJSONEncoder)

            return True

        except Exception as e:
            if self.verbose:
                print(
                    f"⚠️  Warning: Could not save analysis report: {e}", file=sys.stderr
                )
            return False

    def format_file_list(self, evidence: Dict[str, Any]) -> str:
        """Format file list from evidence for display."""
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

    def create_findings_summary(
        self,
        aggregated_findings: List[Dict[str, Any]],
        processing_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create comprehensive summary combining findings and processing results.

        Args:
            aggregated_findings: List of aggregated duplicate findings
            processing_results: List of processing results from expert review/actions

        Returns:
            Comprehensive summary dictionary
        """
        # Basic statistics
        total_file_pairs = len(aggregated_findings)
        total_duplicates = sum(
            finding.get("evidence", {}).get("duplicate_count", 0)
            for finding in aggregated_findings
        )

        # Severity breakdown
        severity_counts = defaultdict(int)
        for finding in aggregated_findings:
            severity = finding.get("severity", "unknown")
            severity_counts[severity] += 1

        # Processing results summary
        results_summary = self.create_summary(processing_results, 0)

        return {
            "input_analysis": {
                "total_file_pairs": total_file_pairs,
                "total_duplicates": total_duplicates,
                "severity_breakdown": dict(severity_counts),
                "avg_duplicates_per_pair": total_duplicates / total_file_pairs
                if total_file_pairs > 0
                else 0,
            },
            "processing_results": results_summary,
            "recommendations": self._generate_recommendations(
                aggregated_findings, processing_results
            ),
        }

    def _generate_recommendations(
        self, findings: List[Dict[str, Any]], results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations based on findings and results."""
        recommendations = []

        if not findings:
            recommendations.append("No duplicate code detected. Keep up the good work!")
            return recommendations

        # Analyze patterns
        high_severity_count = sum(1 for f in findings if f.get("severity") == "high")

        total_duplicates = sum(
            f.get("evidence", {}).get("duplicate_count", 0) for f in findings
        )

        if high_severity_count > 0:
            recommendations.append(
                f"🔥 {high_severity_count} high-severity duplicate patterns detected. "
                "Consider prioritizing these for immediate refactoring."
            )

        if total_duplicates > 20:
            recommendations.append(
                f"📊 {total_duplicates} total duplicates found. "
                "Consider implementing shared utility modules to reduce code duplication."
            )

        # Check for successful automatic fixes
        auto_fixes = sum(1 for r in results if r.get("action") == "automatic_fix")
        if auto_fixes > 0:
            recommendations.append(
                f"✅ {auto_fixes} automatic fixes were applied successfully."
            )

        # Check for manual review items
        manual_reviews = sum(1 for r in results if r.get("action") == "github_issue")
        if manual_reviews > 0:
            recommendations.append(
                f"👀 {manual_reviews} items require manual review via GitHub issues."
            )

        return recommendations
