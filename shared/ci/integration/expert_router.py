#!/usr/bin/env python3
"""
Expert Router Module for Orchestration Bridge Refactoring (Phase 3)

Handles expert agent selection, task creation, and batch processing logic.
Extracted from orchestration_bridge.py lines 231-808.

Part of AI-Assisted Workflows - Phase 3: Breaking up God Class
"""

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

# Setup import paths
try:
    from utils import path_resolver  # noqa: F401
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class ExpertRouter:
    """Expert agent routing and task management."""

    def __init__(self, test_mode: bool = False, verbose: bool = False):
        """
        Initialize expert router.

        Args:
            test_mode: Enable test mode with simulated expert responses
            verbose: Enable verbose logging
        """
        self.test_mode = test_mode
        self.verbose = verbose

    def route_findings_to_experts(
        self, aggregated_findings: List[Dict[str, Any]], verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Route findings to appropriate expert agents based on language and complexity.
        Batch all findings by language to give experts full context.
        """
        # Group findings by language FIRST
        findings_by_language = defaultdict(list)

        for finding in aggregated_findings:
            try:
                evidence = finding.get("evidence", {})
                file_pair = evidence.get("file_pair", [])
                primary_language = self.detect_primary_language(file_pair)
                findings_by_language[primary_language].append(finding)
            except Exception:
                # Handle errors gracefully - add to unknown language group
                findings_by_language["unknown"].append(finding)

        results = []

        # Process each language group with a SINGLE expert call
        for language, language_findings in findings_by_language.items():
            try:
                if language == "python" and language_findings:
                    result = self._python_expert_review_batch(
                        language_findings, verbose
                    )
                elif language in ["javascript", "typescript"] and language_findings:
                    result = self._typescript_expert_review_batch(
                        language_findings, verbose
                    )
                else:
                    # Fallback to CTO for unknown languages
                    result = self._cto_expert_review_batch(language_findings, verbose)

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

    def detect_primary_language(self, file_pair: List[str]) -> str:
        """
        Detect the primary programming language from file extensions.

        Args:
            file_pair: List of file paths to analyze

        Returns:
            Primary language detected (e.g., "python", "typescript", "mixed")
        """
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

    def _python_expert_review_batch(
        self, findings: List[Dict[str, Any]], verbose: bool = False
    ) -> Dict[str, Any]:
        """Pass all Python duplicates to python-expert in one batch."""
        try:
            total_duplicates = sum(
                f.get("evidence", {}).get("duplicate_count", 0) for f in findings
            )
            if verbose:
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
                batch_context, "python-expert", verbose
            )
            result = self._prepare_expert_review_package(
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
        self, findings: List[Dict[str, Any]], verbose: bool = False
    ) -> Dict[str, Any]:
        """Pass all TypeScript/JavaScript duplicates to typescript-expert in one batch."""
        try:
            total_duplicates = sum(
                f.get("evidence", {}).get("duplicate_count", 0) for f in findings
            )
            if verbose:
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
                batch_context, "typescript-expert", verbose
            )
            result = self._prepare_expert_review_package(
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
        self, findings: List[Dict[str, Any]], verbose: bool = False
    ) -> Dict[str, Any]:
        """Pass complex or unknown language duplicates to CTO agent in one batch."""
        try:
            total_duplicates = sum(
                f.get("evidence", {}).get("duplicate_count", 0) for f in findings
            )
            if verbose:
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
                batch_context, "cto", verbose
            )
            result = self._prepare_expert_review_package(
                "cto", task_description, batch_context
            )

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
        self, batch_context: Dict[str, Any], agent_type: str, verbose: bool = False
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
            duplicate_symbols = evidence.get("duplicate_symbols", [])

            if file_pair:
                file_pairs_info.append(
                    f"- {Path(file_pair[0]).name} ↔ {Path(file_pair[1]).name} ({duplicate_count} duplicates)"
                )
                all_duplicate_symbols.extend(duplicate_symbols)

        # Limit file pairs display to first 10 for readability
        if len(file_pairs_info) > 10:
            displayed_pairs = file_pairs_info[:10]
            displayed_pairs.append(
                f"... and {len(file_pairs_info) - 10} more file pairs"
            )
        else:
            displayed_pairs = file_pairs_info

        # Get most common duplicate patterns
        symbol_patterns = []
        if all_duplicate_symbols:
            # Group similar symbols
            symbol_names = [
                sym.get("original", "unknown") for sym in all_duplicate_symbols
            ]
            unique_symbols = list(set(symbol_names))[:15]  # Top 15 unique symbols
            symbol_patterns = [f"- {sym}" for sym in unique_symbols]

        return f"""# Batch Code Duplication Review and Planning Task

## Context
You are reviewing a comprehensive batch of code duplication findings from our continuous improvement system. This is a BATCH REVIEW covering multiple file pairs with similar patterns.

Your role is to:
1. Analyze patterns across all duplicate findings in this batch
2. Create a strategic refactoring approach for the entire batch
3. Prioritize and plan the most effective intervention strategy

## Batch Summary

**Language**: {language}
**Total File Pairs**: {total_file_pairs}
**Total Duplicates Found**: {total_duplicates}
**Average Duplicates per Pair**: {total_duplicates / total_file_pairs if total_file_pairs > 0 else 0:.1f}

### File Pairs in This Batch:
{chr(10).join(displayed_pairs)}

### Common Duplicate Patterns Identified:
{chr(10).join(symbol_patterns) if symbol_patterns else "- Pattern analysis needed"}

## Strategic Review Requirements

1. **Pattern Analysis Phase**:
   - Identify common duplication patterns across all file pairs
   - Look for systemic issues (shared base classes, common utilities, etc.)
   - Assess whether this indicates architectural issues requiring broader refactoring

2. **Batch Strategy Phase**:
   - Determine if these duplicates should be addressed individually or as a cohesive refactoring
   - Prioritize which file pairs to address first based on risk and complexity
   - Consider if a new shared module/utility would eliminate multiple duplications

3. **Implementation Planning Phase**:
   - Create a strategic implementation plan that addresses the batch holistically
   - Consider dependencies between file pairs
   - Plan the sequence of refactoring to minimize risk

4. **Action Decision Phase**:
   - For low-risk batch: Create comprehensive implementation plan for /todo-orchestrate
   - For high-risk or complex batch: Create detailed strategic analysis for human review
   - For mixed complexity: Plan phased approach with immediate low-risk fixes

## Success Criteria
- Comprehensive analysis of duplication patterns across the entire batch
- Strategic approach that maximizes refactoring benefit while minimizing risk
- Clear prioritization and sequencing of interventions
- Either a complete batch implementation plan or strategic recommendation for human review

Please proceed with the batch analysis and create an appropriate strategic response.
"""

    def _prepare_expert_review_package(
        self, agent_type: str, task_description: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare findings for LLM expert review instead of making direct Task calls."""
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

            # Handle both individual and batch context structures
            if "findings" in context:
                # Batch context
                findings_count = len(context["findings"])
                total_duplicates = context.get("total_duplicates", 0)
                language = context.get("language", "unknown")
                findings_batch = context["findings"]
            else:
                # Individual context
                findings_count = 1
                total_duplicates = context.get("duplicate_count", 0)
                language = context.get("language", "unknown")
                findings_batch = [context.get("finding", {})]

            # Return structured package for LLM review
            return {
                "status": "ready_for_expert_review",
                "action": "INVOKE_EXPERT_AGENT",
                "recommended_expert": agent_type,
                "language": language,
                "findings_count": findings_count,
                "total_duplicates": total_duplicates,
                "findings_batch": findings_batch,
                "task_description": task_description,
                "instructions": (
                    f"These {findings_count} duplicate findings require expert review. "
                    f"Please invoke the {agent_type} agent using the Task tool "
                    f"to analyze these duplicates and provide refactoring recommendations. "
                    f"The agent should receive the complete task description and context."
                ),
                "expert_context": {
                    "agent_type": agent_type,
                    "language_focus": language,
                    "complexity_level": "high"
                    if total_duplicates > 100
                    else "medium"
                    if total_duplicates > 20
                    else "low",
                    "batch_processing": findings_count > 1,
                    "priority": "high"
                    if any(
                        f.get("evidence", {}).get("average_similarity", 0) > 0.9
                        for f in findings_batch
                    )
                    else "medium",
                },
                "next_steps": [
                    f"1. Review the {findings_count} findings above",
                    f"2. Use Task tool to invoke {agent_type} agent",
                    "3. Pass the complete task_description to the agent",
                    "4. Execute the agent's recommendations",
                ],
            }

        except Exception as e:
            return {
                "status": "error",
                "agent": agent_type,
                "error": str(e),
                "message": f"Failed to prepare expert review package for {agent_type}: {e}",
            }
