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
    from ci.workflows.decision_matrix import (
        DecisionMatrix,
        ActionType,
        DuplicationContext,
    )
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
    Bridge that orchestrates duplicate detection and remediation workflows.

    Purpose: When CTO decision logic determines a fix is needed, create a
    simple implementation plan and pass it to claude /todo-orchestrate.

    No duplication of workflow logic - just calls the existing command.
    """

    def __init__(
        self, project_root: str = ".", test_mode: bool = False, config_path: str = None
    ):
        self.project_root = Path(project_root).resolve()
        self.test_mode = test_mode
        self.config_path = config_path
        self.duplicate_finder = self._initialize_duplicate_finder(test_mode)
        self.decision_matrix = DecisionMatrix()

    def _initialize_duplicate_finder(self, test_mode: bool = False) -> DuplicateFinder:
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
            return DuplicateFinder(config, self.project_root, test_mode=test_mode)
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

    def _filter_meaningful_duplicates(
        self, findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhanced filtering using LSP kinds and language-specific patterns."""

        # Import tech stack detector for language patterns
        try:
            from utils import path_resolver  # noqa: F401
            from core.utils.tech_stack_detector import TechStackDetector

            detector = TechStackDetector()
        except ImportError:
            detector = None

        meaningful_findings = []

        for finding in findings:
            evidence = finding.get("evidence", {})
            orig = evidence.get("original_symbol", {})
            dup = evidence.get("duplicate_symbol", {})

            # 1. USE LSP KIND for semantic filtering (not string matching!)
            orig_kind = orig.get("lsp_kind", 0)
            dup_kind = dup.get("lsp_kind", 0)
            similarity = evidence.get("similarity_score", 0)

            # Skip imports (LSP kind 2 = MODULE)
            if orig_kind == 2 or dup_kind == 2:
                continue

            # Skip constants (LSP kind 14 = CONSTANT, 22 = ENUM_MEMBER)
            if orig_kind in [14, 22] or dup_kind in [14, 22]:
                continue

            # Skip constructors unless exact match (LSP kind 9 = CONSTRUCTOR)
            if (orig_kind == 9 or dup_kind == 9) and similarity < 0.95:
                continue

            orig_name = orig.get("name", "")
            dup_name = dup.get("name", "")
            orig_file = orig.get("file", "")
            dup_file = dup.get("file", "")

            # 2. Get language-specific patterns if available
            if detector and orig_file:
                language = self._detect_language_from_file(orig_file)
                boilerplate_patterns = set()

                # Load boilerplate patterns for this language
                for stack_id, config in detector.tech_stacks.items():
                    if (
                        language in config.primary_languages
                        and config.boilerplate_patterns
                    ):
                        boilerplate_patterns.update(config.boilerplate_patterns)

                # 3. Check against language-specific patterns using fnmatch
                if boilerplate_patterns:
                    import fnmatch

                    is_boilerplate = False
                    for pattern in boilerplate_patterns:
                        if fnmatch.fnmatch(orig_name, pattern) or fnmatch.fnmatch(
                            dup_name, pattern
                        ):
                            # Boilerplate detected - only flag if very high similarity
                            if similarity < 0.90:
                                is_boilerplate = True
                                break

                    if is_boilerplate:
                        continue

            # 4. Skip PROPERTY kinds (LSP kind 7) unless high similarity
            # Properties/getters/setters are often similar by design
            if (orig_kind == 7 or dup_kind == 7) and similarity < 0.90:
                continue

            # 5. Skip very short duplicates unless exact match
            # Only filter if we have reliable line count data AND it's not just function signatures
            orig_lines = orig.get("line_count")
            dup_lines = dup.get("line_count")
            if (
                orig_lines
                and dup_lines
                and orig_lines < 3
                and dup_lines < 3
                and similarity < 1.0
                and
                # Don't filter functions based on line count - LSP often only returns signature
                orig_kind not in [12, 6]
                and dup_kind not in [12, 6]
            ):  # 12=FUNCTION, 6=METHOD
                continue

            # 6. Skip single-character names (likely parameters)
            if len(orig_name) <= 1 or len(dup_name) <= 1:
                continue

            # 7. Skip if names are too generic
            generic_names = {"i", "j", "k", "x", "y", "z", "n", "m", "e", "f", "v"}
            if orig_name.lower() in generic_names or dup_name.lower() in generic_names:
                continue

            # 8. Only include cross-file duplicates (more meaningful)
            if orig_file and dup_file and orig_file != dup_file:
                meaningful_findings.append(finding)

        return meaningful_findings

    def _aggregate_findings(
        self, findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Group findings by duplicate pairs to create consolidated refactoring tasks."""
        from collections import defaultdict

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

    def _expert_review_duplicates(
        self, aggregated_findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Pass aggregated findings to expert agents for language-specific review.
        Batch all findings by language to give experts full context.
        """
        from collections import defaultdict

        # Group findings by language FIRST
        findings_by_language = defaultdict(list)

        for finding in aggregated_findings:
            try:
                evidence = finding.get("evidence", {})
                file_pair = evidence.get("file_pair", [])
                primary_language = self._detect_primary_language(file_pair)
                findings_by_language[primary_language].append(finding)
            except Exception:
                # Handle errors gracefully - add to unknown language group
                findings_by_language["unknown"].append(finding)

        results = []

        # Process each language group with a SINGLE expert call
        for language, language_findings in findings_by_language.items():
            try:
                if language == "python" and language_findings:
                    result = self._python_expert_review_batch(language_findings)
                elif language in ["javascript", "typescript"] and language_findings:
                    result = self._typescript_expert_review_batch(language_findings)
                else:
                    # Fallback to CTO for unknown languages
                    result = self._cto_expert_review_batch(language_findings)

                results.append(result)

            except Exception as e:
                # Handle errors gracefully
                error_result = {
                    "action": "expert_review_error",
                    "status": "error",
                    "error": str(e),
                    "language": language,
                    "findings_count": len(language_findings),
                    "message": f"Expert batch review failed for {language}: {e}",
                }
                results.append(error_result)

        return results

    def _detect_primary_language(self, file_pair: List[str]) -> str:
        """Detect the primary programming language from file extensions."""
        if not file_pair:
            return "unknown"

        extensions = [Path(f).suffix.lower() for f in file_pair]

        # Count language occurrences
        language_count = {}
        for ext in extensions:
            if ext in [".py", ".pyx"]:
                language_count["python"] = language_count.get("python", 0) + 1
            elif ext in [".js", ".jsx"]:
                language_count["javascript"] = language_count.get("javascript", 0) + 1
            elif ext in [".ts", ".tsx"]:
                language_count["typescript"] = language_count.get("typescript", 0) + 1
            elif ext in [".rs"]:
                language_count["rust"] = language_count.get("rust", 0) + 1
            elif ext in [".go"]:
                language_count["go"] = language_count.get("go", 0) + 1

        # Return most common language, or "unknown" if none detected
        if language_count:
            return max(language_count, key=language_count.get)
        return "unknown"

    def _detect_language_from_file(self, file_path: str) -> str:
        """Detect programming language from a single file path."""
        if not file_path:
            return "unknown"

        ext = Path(file_path).suffix.lower()

        if ext in [".py", ".pyx"]:
            return "python"
        elif ext in [".js", ".jsx"]:
            return "javascript"
        elif ext in [".ts", ".tsx"]:
            return "typescript"
        elif ext in [".rs"]:
            return "rust"
        elif ext in [".go"]:
            return "go"
        elif ext in [".java"]:
            return "java"
        elif ext in [".cs"]:
            return "csharp"
        elif ext in [".cpp", ".cc", ".cxx", ".c"]:
            return "cpp"
        elif ext in [".rb"]:
            return "ruby"
        elif ext in [".php"]:
            return "php"
        elif ext in [".swift"]:
            return "swift"
        elif ext in [".kt"]:
            return "kotlin"

        return "unknown"

    def _python_expert_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Pass aggregated Python duplicates to python-expert agent."""
        try:
            print(
                f"🐍 Passing {context['duplicate_count']} duplicates to python-expert..."
            )

            # Create comprehensive task description for the expert agent
            task_description = self._create_expert_task_description(
                context, "python-expert"
            )

            # Call the expert agent through Task tool
            result = self._call_expert_agent("python-expert", task_description, context)

            return {
                "action": "expert_review",
                "agent": "python-expert",
                "status": result.get("status", "completed"),
                "finding_id": context["finding"].get("finding_id", "unknown"),
                "language": "python",
                "expert_result": result,
            }

        except Exception as e:
            return {
                "action": "expert_review",
                "agent": "python-expert",
                "status": "error",
                "error": str(e),
                "finding_id": context["finding"].get("finding_id", "unknown"),
            }

    def _typescript_expert_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Pass aggregated TypeScript/JavaScript duplicates to typescript-expert agent."""
        try:
            print(
                f"📜 Passing {context['duplicate_count']} duplicates to typescript-expert..."
            )

            task_description = self._create_expert_task_description(
                context, "typescript-expert"
            )
            result = self._call_expert_agent(
                "typescript-expert", task_description, context
            )

            return {
                "action": "expert_review",
                "agent": "typescript-expert",
                "status": result.get("status", "completed"),
                "finding_id": context["finding"].get("finding_id", "unknown"),
                "language": context["language"],
                "expert_result": result,
            }

        except Exception as e:
            return {
                "action": "expert_review",
                "agent": "typescript-expert",
                "status": "error",
                "error": str(e),
                "finding_id": context["finding"].get("finding_id", "unknown"),
            }

    def _cto_expert_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Pass complex or unknown language duplicates to CTO agent."""
        try:
            print(
                f"👔 Escalating {context['duplicate_count']} duplicates to CTO for complex review..."
            )

            task_description = self._create_expert_task_description(context, "cto")
            result = self._call_expert_agent("cto", task_description, context)

            return {
                "action": "expert_review",
                "agent": "cto",
                "status": result.get("status", "completed"),
                "finding_id": context["finding"].get("finding_id", "unknown"),
                "language": context["language"],
                "expert_result": result,
            }

        except Exception as e:
            return {
                "action": "expert_review",
                "agent": "cto",
                "status": "error",
                "error": str(e),
                "finding_id": context["finding"].get("finding_id", "unknown"),
            }

    def _python_expert_review_batch(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Pass all Python duplicates to python-expert in one batch."""
        try:
            total_duplicates = sum(
                f.get("evidence", {}).get("duplicate_count", 0) for f in findings
            )
            print(
                f"🐍 Passing {total_duplicates} duplicates across {len(findings)} file pairs to python-expert..."
            )

            # Create batch context
            batch_context = {
                "findings": findings,
                "total_file_pairs": len(findings),
                "total_duplicates": total_duplicates,
                "language": "python",
            }

            # Create comprehensive batch task description
            task_description = self._create_expert_batch_task_description(
                batch_context, "python-expert"
            )
            result = self._call_expert_agent(
                "python-expert", task_description, batch_context
            )

            return {
                "action": "expert_review",
                "agent": "python-expert",
                "status": result.get("status", "completed"),
                "language": "python",
                "findings_count": len(findings),
                "total_duplicates": total_duplicates,
                "expert_result": result,
            }

        except Exception as e:
            return {
                "action": "expert_review",
                "agent": "python-expert",
                "status": "error",
                "error": str(e),
                "language": "python",
                "findings_count": len(findings),
            }

    def _typescript_expert_review_batch(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Pass all TypeScript/JavaScript duplicates to typescript-expert in one batch."""
        try:
            total_duplicates = sum(
                f.get("evidence", {}).get("duplicate_count", 0) for f in findings
            )
            print(
                f"📜 Passing {total_duplicates} duplicates across {len(findings)} file pairs to typescript-expert..."
            )

            batch_context = {
                "findings": findings,
                "total_file_pairs": len(findings),
                "total_duplicates": total_duplicates,
                "language": "typescript",
            }

            task_description = self._create_expert_batch_task_description(
                batch_context, "typescript-expert"
            )
            result = self._call_expert_agent(
                "typescript-expert", task_description, batch_context
            )

            return {
                "action": "expert_review",
                "agent": "typescript-expert",
                "status": result.get("status", "completed"),
                "language": "typescript",
                "findings_count": len(findings),
                "total_duplicates": total_duplicates,
                "expert_result": result,
            }

        except Exception as e:
            return {
                "action": "expert_review",
                "agent": "typescript-expert",
                "status": "error",
                "error": str(e),
                "language": "typescript",
                "findings_count": len(findings),
            }

    def _cto_expert_review_batch(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Pass complex or unknown language duplicates to CTO agent in one batch."""
        try:
            total_duplicates = sum(
                f.get("evidence", {}).get("duplicate_count", 0) for f in findings
            )
            print(
                f"👔 Escalating {total_duplicates} duplicates across {len(findings)} file pairs to CTO for complex review..."
            )

            batch_context = {
                "findings": findings,
                "total_file_pairs": len(findings),
                "total_duplicates": total_duplicates,
                "language": "unknown",
            }

            task_description = self._create_expert_batch_task_description(
                batch_context, "cto"
            )
            result = self._call_expert_agent("cto", task_description, batch_context)

            return {
                "action": "expert_review",
                "agent": "cto",
                "status": result.get("status", "completed"),
                "language": "unknown",
                "findings_count": len(findings),
                "total_duplicates": total_duplicates,
                "expert_result": result,
            }

        except Exception as e:
            return {
                "action": "expert_review",
                "agent": "cto",
                "status": "error",
                "error": str(e),
                "language": "unknown",
                "findings_count": len(findings),
            }

    def _create_expert_task_description(
        self, context: Dict[str, Any], agent_type: str
    ) -> str:
        """Create detailed task description for expert agents."""
        finding = context["finding"]
        evidence = finding.get("evidence", {})
        duplicate_symbols = evidence.get("duplicate_symbols", [])

        # Format duplicate symbols information
        symbols_info = "\n".join(
            [
                f"- {sym['original']} ↔ {sym['duplicate']} (similarity: {sym['similarity']:.2f})"
                for sym in duplicate_symbols[:10]  # Limit to first 10 for readability
            ]
        )

        if len(duplicate_symbols) > 10:
            symbols_info += f"\n... and {len(duplicate_symbols) - 10} more duplicates"

        file_pair = context["file_pair"]

        return f"""# Code Duplication Review and Planning Task

## Context
You are reviewing code duplication findings from our continuous improvement system. Your role is to:
1. Analyze the aggregated duplicate patterns
2. Create a comprehensive refactoring plan
3. Decide whether to proceed with automatic refactoring or escalate to human review

## Duplication Details

**File Pair**: {Path(file_pair[0]).name} ↔ {Path(file_pair[1]).name}
**Total Duplicates Found**: {context['duplicate_count']}
**Average Similarity**: {context['average_similarity']:.2f}
**Language**: {context['language']}

### Duplicate Patterns Identified:
{symbols_info}

## Task Requirements

1. **Analysis Phase**:
   - Use Serena tools to examine both files and understand the duplicate patterns
   - Assess the complexity and risk of consolidating these duplicates
   - Consider dependencies, test coverage, and architectural impact

2. **Decision Phase**:
   - If duplicates are simple and low-risk: Create implementation plan for automatic refactoring
   - If duplicates are complex or high-risk: Create detailed issue for human review
   - Consider the decision matrix criteria: similarity, complexity, test coverage, API impact

3. **Action Phase**:
   - For automatic refactoring: Use /todo-orchestrate with your implementation plan
   - For human review: Create detailed GitHub issue with your analysis

## Success Criteria
- Thorough analysis of all duplicate patterns in the file pair
- Clear decision on refactoring approach based on risk assessment
- Either completed refactoring or well-documented issue for human review

Please proceed with the analysis and take appropriate action based on your assessment.
"""

    def _create_expert_batch_task_description(
        self, batch_context: Dict[str, Any], agent_type: str
    ) -> str:
        """Create detailed task description for batch expert review."""
        findings = batch_context["findings"]
        total_file_pairs = batch_context["total_file_pairs"]
        total_duplicates = batch_context["total_duplicates"]
        language = batch_context["language"]

        # Extract file pairs and summary info
        file_pairs_info = []
        all_duplicate_symbols = []

        for finding in findings:
            evidence = finding.get("evidence", {})
            file_pair = evidence.get("file_pair", [])
            duplicate_count = evidence.get("duplicate_count", 0)
            avg_similarity = evidence.get("average_similarity", 0)
            duplicate_symbols = evidence.get("duplicate_symbols", [])

            if file_pair:
                file_pairs_info.append(
                    f"- **{Path(file_pair[0]).name} ↔ {Path(file_pair[1]).name}**: {duplicate_count} duplicates (avg similarity: {avg_similarity:.2f})"
                )

            all_duplicate_symbols.extend(duplicate_symbols)

        # Format first 15 duplicate symbols for readability
        symbols_info = "\n".join(
            [
                f"- {sym['original']} ↔ {sym['duplicate']} (similarity: {sym['similarity']:.2f})"
                for sym in all_duplicate_symbols[:15]
            ]
        )

        if len(all_duplicate_symbols) > 15:
            symbols_info += f"\n... and {len(all_duplicate_symbols) - 15} more duplicates across all file pairs"

        return f"""# Comprehensive Code Duplication Review and Refactoring Strategy

## Context
You are conducting a comprehensive review of code duplication findings across multiple file pairs in a {language} codebase. Your role is to:
1. Analyze all duplicate patterns holistically
2. Create a unified refactoring strategy that addresses the entire scope
3. Decide on the best approach for coordinated refactoring across all affected files

## Batch Duplication Overview

**Language**: {language}
**Total File Pairs**: {total_file_pairs}
**Total Duplicates Found**: {total_duplicates}

### File Pairs Analyzed:
{chr(10).join(file_pairs_info)}

### Sample Duplicate Patterns (across all pairs):
{symbols_info}

## Comprehensive Analysis Requirements

1. **Holistic Pattern Analysis**:
   - Identify common themes and patterns across all file pairs
   - Look for architectural issues that span multiple files
   - Assess whether duplicates suggest missing abstractions or shared utilities

2. **Unified Refactoring Strategy**:
   - Consider refactoring all related duplicates together rather than piecemeal
   - Identify opportunities for shared libraries, base classes, or utility functions
   - Plan the sequence of refactoring to minimize conflicts

3. **Risk Assessment**:
   - Evaluate the overall complexity and impact of coordinated refactoring
   - Consider dependencies, test coverage, and API impacts across all files
   - Assess whether batch refactoring is safer than individual file fixes

4. **Strategic Decision**:
   - **For coordinated automatic refactoring**: Use /todo-orchestrate with comprehensive implementation plan
   - **For complex architectural changes**: Create detailed GitHub issue with full analysis and recommendations

## Success Criteria
- Comprehensive analysis covering all {total_file_pairs} file pairs
- Clear strategic approach that considers interdependencies
- Either completed coordinated refactoring or well-documented architectural improvement plan

## Additional Context
This batch review allows you to see the full scope of duplication patterns, enabling better architectural decisions than reviewing files individually.

Please proceed with the holistic analysis and create an appropriate refactoring strategy.
"""

    def _call_expert_agent(
        self, agent_type: str, task_description: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call expert agent using Claude Code Task tool (simulated for now)."""
        try:
            # In test mode, simulate expert agent response
            if self.test_mode:
                return {
                    "status": "simulated_success",
                    "agent": agent_type,
                    "message": f"Simulated {agent_type} review completed",
                    "action_taken": "simulated_analysis",
                    "recommendation": "Proceed with automatic refactoring"
                    if context.get("average_similarity", 0) > 0.8
                    else "Escalate to human review",
                }

            # In real mode, this would call the Task tool with the specified agent
            # For now, return a placeholder that indicates the system is working
            return {
                "status": "agent_call_required",
                "agent": agent_type,
                "task_description": task_description,
                "message": f"Task prepared for {agent_type} - agent integration pending",
                "context_summary": {
                    "duplicates": context["duplicate_count"],
                    "similarity": context["average_similarity"],
                    "files": context["file_pair"],
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to call {agent_type} agent",
            }

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
            # Step 1: Index changed files in ChromaDB if provided
            if changed_files:
                self._index_changed_files(changed_files)

            # Step 2: Analyze for duplicates
            print("🔍 Analyzing project for code duplication...")
            if changed_files:
                # Convert to Path objects and run incremental analysis
                changed_paths = [Path(f) for f in changed_files]
                analysis_result = self.duplicate_finder.incremental_analysis(
                    changed_paths
                )
            else:
                analysis_result = self.duplicate_finder.analyze_project()

            # Step 1.5: Filter out meaningless duplicates (imports, built-ins)
            filtered_findings = self._filter_meaningful_duplicates(
                analysis_result.findings
            )
            findings_count = len(filtered_findings)
            print(
                f"📊 Found {findings_count} meaningful duplicate(s) (filtered from {len(analysis_result.findings)} total)"
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
                self._save_analysis_report(result)
                return result

            # Step 2: Aggregate findings by file pairs to reduce processing overhead
            aggregated_findings = self._aggregate_findings(filtered_findings)
            print(f"📦 Aggregated into {len(aggregated_findings)} finding groups")

            # Step 3: Expert agent review for aggregated findings
            if len(aggregated_findings) > 0:
                expert_results = self._expert_review_duplicates(aggregated_findings)
                results = expert_results
            else:
                results = []

            # Step 4: Create summary
            summary = self._create_summary(results)

            result = {
                "status": "success",
                "findings_processed": findings_count,
                "summary": summary,
                "results": results,
            }

            # Step 5: Save analysis report
            self._save_analysis_report(result)

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
            self._save_analysis_report(error_result)
            return error_result

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

**Similarity Score**: {evidence.get('similarity_score', 0):.0%}
**Severity**: {finding.get('severity', 'unknown').upper()}
**Files Affected**: {context.file_count}

### Description
{finding.get('description', 'Duplicate code patterns detected that require manual review.')}

### Evidence
- **Similarity Score**: {evidence.get('similarity_score', 0):.0%}
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

    def _create_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of processing results."""
        summary = {
            "expert_reviews": 0,
            "automatic_fixes": 0,
            "github_issues": 0,
            "skipped": 0,
            "errors": 0,
            "successes": 0,
            "agents_used": set(),
        }

        for result in results:
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

    def _save_analysis_report(self, result: Dict[str, Any]) -> None:
        """Save analysis results to reports directory for GitHub Actions artifact upload."""
        try:
            # Create reports directory
            reports_dir = Path(self.project_root) / ".ci-registry" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Create comprehensive report
            report_data = {
                "timestamp": time.time(),
                "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "status": result.get("status", "unknown"),
                "findings": result.get("results", []),
                "summary": result.get("summary", {}),
                "config": {
                    "similarity_threshold": 0.85,  # TODO: Get from actual config
                    "project_root": str(self.project_root),
                    "analysis_mode": "github_actions",
                },
                "metadata": {
                    "analysis_type": "duplicate_detection",
                    "workflow_trigger": "github_actions",
                    "findings_processed": result.get("findings_processed", 0),
                    "action": result.get("action", "analysis_completed"),
                },
            }

            # Save latest analysis report
            report_file = reports_dir / "latest-analysis.json"
            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=2, cls=CustomJSONEncoder)

            print(
                f"✅ Analysis report saved to {report_file.relative_to(self.project_root)}"
            )

            # Also save timestamped report for history
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
            historical_file = reports_dir / f"analysis_{timestamp}.json"
            with open(historical_file, "w") as f:
                json.dump(report_data, f, indent=2, cls=CustomJSONEncoder)

        except Exception as e:
            print(f"⚠️  Warning: Could not save analysis report: {e}", file=sys.stderr)
            # Don't fail the entire process if report saving fails


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

    args = parser.parse_args()

    # Initialize bridge
    bridge = OrchestrationBridge(args.project_root, config_path=args.config_path)

    # Process duplicates
    result = bridge.process_duplicates_for_github_actions(args.changed_files)

    # Output results as JSON for GitHub Actions
    print(json.dumps(result, indent=2, cls=CustomJSONEncoder))

    # Exit with appropriate code
    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
