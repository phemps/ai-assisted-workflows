#!/usr/bin/env python3
"""
Slim Orchestration Bridge for Code Duplication Detection (Phase 3 Refactored)

Coordinates duplicate detection workflow by delegating to specialized modules:
- ExpertRouter: Language-specific expert agent routing
- DecisionEngine: Decision matrix and action determination
- GitHubReporter: Issue creation for manual review
- FindingProcessor: Finding aggregation and utilities

DESIGN PRINCIPLE: Slim coordinator pattern with focused module delegation.
"""

import json
import sys
import time
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup import paths and import required modules
try:
    from utils import path_resolver  # noqa: F401
    from ci.core.semantic_duplicate_detector import (
        DuplicateFinder,
        DuplicateFinderConfig,
        CISystemError,
    )

    # Import the new focused modules
    from ci.integration.expert_router import ExpertRouter
    from ci.integration.decision_engine import DecisionEngine
    from ci.integration.github_reporter import GitHubReporter
    from ci.integration.finding_processor import FindingProcessor
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


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


class OrchestrationBridge:
    """
    Slim coordinator that orchestrates duplicate detection workflow.

    Delegates specialized functions to focused modules:
    - ExpertRouter: Expert agent routing and task management
    - DecisionEngine: Decision matrix logic and action determination
    - GitHubReporter: GitHub integration for manual review
    - FindingProcessor: Finding aggregation and utility functions
    """

    def __init__(
        self,
        project_root: str = ".",
        test_mode: bool = False,
        config_path: str = None,
        verbose: bool = False,
    ):
        self.project_root = Path(project_root).resolve()
        self.test_mode = test_mode
        self.config_path = config_path
        self.verbose = verbose
        self.duplicate_finder = self._initialize_duplicate_finder(test_mode, verbose)

        # Initialize specialized modules
        self.expert_router = ExpertRouter(test_mode, verbose)
        self.decision_engine = DecisionEngine(
            str(self.project_root), test_mode, verbose
        )
        self.github_reporter = GitHubReporter(
            str(self.project_root), test_mode, verbose
        )
        self.finding_processor = FindingProcessor(str(self.project_root), verbose)

    def _initialize_duplicate_finder(
        self, test_mode: bool = False, verbose: bool = False
    ) -> DuplicateFinder:
        """Initialize duplicate finder with fail-fast behavior."""
        try:
            # Load CI configuration if available
            ci_config = self._load_ci_config()

            # Extract configuration values
            analysis_config = ci_config.get("project", {}).get("analysis", {})
            exclusions = ci_config.get("project", {}).get("exclusions", {})

            # Build exclude patterns from CI config
            exclude_patterns = []
            exclude_patterns.extend(exclusions.get("files", []))
            exclude_patterns.extend(exclusions.get("patterns", []))

            # Add directory exclusions as patterns
            for directory in exclusions.get("directories", []):
                exclude_patterns.append(f"{directory}/*")
                exclude_patterns.append(f"**/{directory}/*")

            config = DuplicateFinderConfig(
                analysis_mode=analysis_config.get("analysis_mode", "targeted"),
                enable_caching=analysis_config.get("enable_caching", True),
                batch_size=analysis_config.get("batch_size", 50),
                medium_similarity_threshold=analysis_config.get(
                    "medium_similarity_threshold", 0.75
                ),
                high_similarity_threshold=analysis_config.get(
                    "high_similarity_threshold", 0.85
                ),
                exact_duplicate_threshold=analysis_config.get(
                    "exact_duplicate_threshold", 1.0
                ),
                low_similarity_threshold=analysis_config.get(
                    "low_similarity_threshold", 0.45
                ),
                exclude_file_patterns=exclude_patterns if exclude_patterns else None,
            )
            return DuplicateFinder(
                config, self.project_root, test_mode=test_mode, verbose=verbose
            )
        except Exception as e:
            if test_mode:
                raise CISystemError(f"Cannot initialize DuplicateFinder: {e}")
            else:
                print(f"FATAL: Cannot initialize DuplicateFinder: {e}", file=sys.stderr)
                sys.exit(1)

    def _index_changed_files(self, changed_files: List[str]) -> None:
        """Index changed files in ChromaDB for improved duplicate detection."""
        try:
            from ci.core.chromadb_indexer import ChromaDBIndexer

            indexer = ChromaDBIndexer(
                project_root=str(self.project_root), test_mode=self.test_mode
            )

            print(f"🗂️ Indexing {len(changed_files)} changed files...")
            result = indexer.incremental_index(changed_files)

            if result.get("status") == "success":
                files_processed = result.get("files_processed", 0)
                symbols_indexed = result.get("symbols_indexed", 0)
                print(f"✅ Indexed {files_processed} files ({symbols_indexed} symbols)")
            elif result.get("status") == "skipped":
                print(f"⏭️ Indexing skipped: {result.get('reason', 'Unknown reason')}")
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"⚠️ Indexing failed: {error_msg}")

        except Exception as e:
            # Don't fail the entire process if indexing fails
            print(f"⚠️ Indexing error (continuing anyway): {e}")

    def _load_ci_config(self) -> Dict[str, Any]:
        """Load CI configuration from file."""
        import json

        # Determine config file path
        if self.config_path:
            config_file = Path(self.config_path)
        else:
            # Default location
            config_file = self.project_root / ".ci-registry" / "ci_config.json"

        if not config_file.exists():
            # Return default configuration if no config file found
            return {
                "project": {
                    "analysis": {
                        "analysis_mode": "targeted",
                        "enable_caching": True,
                        "batch_size": 50,
                        "medium_similarity_threshold": 0.75,
                        "high_similarity_threshold": 0.85,
                        "exact_duplicate_threshold": 1.0,
                        "low_similarity_threshold": 0.45,
                    },
                    "exclusions": {
                        "directories": [
                            "node_modules",
                            ".git",
                            "__pycache__",
                            "dist",
                            "build",
                            "target",
                        ],
                        "files": ["*.min.js", "*.bundle.js", "*.map"],
                        "patterns": [],
                    },
                }
            }

        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            if self.test_mode:
                raise CISystemError(f"Failed to load CI config from {config_file}: {e}")
            else:
                print(
                    f"Warning: Failed to load CI config from {config_file}: {e}",
                    file=sys.stderr,
                )
                print("Using default configuration", file=sys.stderr)
                return {"project": {"analysis": {}, "exclusions": {}}}

    def process_duplicates_for_github_actions(
        self, changed_files: Optional[List[str]] = None, verbose: bool = False
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
            # Step 1: Index changed files in ChromaDB if provided
            if changed_files:
                self._index_changed_files(changed_files)

            # Step 2: Analyze for duplicates
            print("🔍 Analyzing project for code duplication...")
            if changed_files:
                # Convert to Path objects and run incremental analysis
                changed_paths = [Path(f) for f in changed_files]
                analysis_result = self.duplicate_finder.incremental_analysis(
                    changed_paths, verbose=verbose
                )
            else:
                analysis_result = self.duplicate_finder.analyze_project(verbose=verbose)

            # Step 1.5: Get findings (filtering now happens at symbol extraction level)
            filtered_findings = analysis_result.findings
            findings_count = len(filtered_findings)
            print(
                f"📊 Found {findings_count} duplicate(s) after enhanced filtering at symbol extraction level"
            )

            if findings_count == 0:
                result = {
                    "status": "success",
                    "action": "no_duplicates_found",
                    "results": [],
                    "summary": {
                        "automatic_fixes": 0,
                        "github_issues": 0,
                        "skipped": 0,
                        "errors": 0,
                        "successes": 0,
                    },
                }
                # Save report even when no duplicates found
                self.finding_processor.save_analysis_report(
                    [], result.get("summary", {})
                )
                return result

            # Step 2: Aggregate findings by file pairs to reduce processing overhead
            aggregated_findings = self.finding_processor.aggregate_findings(
                filtered_findings
            )
            print(f"📦 Aggregated into {len(aggregated_findings)} finding groups")

            # Step 3: Expert agent review for aggregated findings
            if len(aggregated_findings) > 0:
                expert_results = self.expert_router.route_findings_to_experts(
                    aggregated_findings, verbose=verbose
                )
                results = expert_results
            else:
                results = []

            # Step 4: Create summary
            total_time = time.time() - time.time()  # Placeholder for timing
            summary = self.finding_processor.create_summary(results, total_time)

            result = {
                "status": "success",
                "findings_processed": findings_count,
                "summary": summary,
                "results": results,
            }

            # Step 5: Save analysis report
            self.finding_processor.save_analysis_report(
                result.get("results", []), result.get("summary", {})
            )

            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "message": "Duplicate analysis failed - see logs for details",
                "summary": {
                    "automatic_fixes": 0,
                    "github_issues": 0,
                    "skipped": 0,
                    "errors": 1,
                    "successes": 0,
                },
            }
            # Save error report as well
            self.finding_processor.save_analysis_report(
                [], error_result.get("summary", {})
            )
            return error_result


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
    parser.add_argument("--config-path", help="Path to custom CI configuration file")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include code snippets in output for debugging",
    )

    args = parser.parse_args()

    # Initialize bridge
    bridge = OrchestrationBridge(
        args.project_root, config_path=args.config_path, verbose=args.verbose
    )

    # Process duplicates
    result = bridge.process_duplicates_for_github_actions(
        args.changed_files, verbose=args.verbose
    )

    # Output results as JSON for GitHub Actions
    print(json.dumps(result, indent=2, cls=CustomJSONEncoder))

    # Exit with appropriate code
    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
