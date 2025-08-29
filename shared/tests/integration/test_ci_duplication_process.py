#!/usr/bin/env python3
"""
CI Duplication Process Integration Test
========================================

This test provides a comprehensive overview of how the orchestration_bridge.py
duplicate detection system works, along with a simple test harness to run it
against any project.

WORKFLOW OVERVIEW:
==================

The orchestration bridge performs semantic duplicate detection through these steps:

1. PROJECT INITIALIZATION
   - Accepts --project-root parameter (defaults to current directory)
   - Creates/uses .ci-registry/ directory at project root
   - Initializes ChromaDB vector database at .ci-registry/chromadb/

2. CODEBASE SCANNING
   - Uses DuplicateFinder to scan all source files
   - Extracts code symbols using Language Server Protocol (LSP)
   - Supports 10+ languages (Python, TypeScript, Java, Go, Rust, etc.)
   - Filters out test files and third-party code

3. SEMANTIC ANALYSIS
   - Generates CodeBERT embeddings for each code symbol
   - Stores embeddings in ChromaDB for similarity search
   - Groups similar code by semantic meaning (not just text matching)
   - Applies similarity thresholds (exact: 1.0, high: 0.8, medium: 0.6)

4. FALSE POSITIVE FILTERING
   The system applies multiple filters to reduce false positives:

   a) Symbol Reference Detection
      - Identifies imports, type annotations, function calls
      - Distinguishes references from actual implementations
      - Filters out normal usage patterns

   b) LSP Symbol Analysis
      - Uses symbol kinds (Variable, Property, Field, Parameter, etc.)
      - Excludes reference-type symbols that aren't actual duplicates
      - Focuses on implementation symbols (Method, Function, Class)

   c) Implementation Content Check
      - Verifies symbols contain actual code logic
      - Filters out empty declarations and interfaces
      - Requires minimum implementation complexity

   d) Language-Specific Patterns
      - Recognizes framework boilerplate (Django models, React components)
      - Filters constructor patterns and standard methods
      - Handles language-specific idioms

   e) Context-Aware Thresholds
      - Adjusts similarity requirements based on symbol type
      - Higher thresholds for simple patterns
      - Lower thresholds for complex implementations

5. EXPERT AGENT ROUTING
   For remaining duplicates, the system routes to specialized agents:

   - Python duplicates → python-expert agent
   - TypeScript/JavaScript → typescript-expert agent
   - Complex multi-language → codebase-expert agent
   - Infrastructure code → terraform-gcp-expert agent

   Each expert agent:
   - Analyzes the duplicate for refactoring potential
   - Generates specific recommendations
   - Returns structured JSON response
   - May fail if analysis is too complex

6. DECISION MATRIX
   The DecisionMatrix determines action based on:

   - Duplicate complexity and file count
   - Language and framework considerations
   - Project-specific quality gates
   - CI configuration settings

   Possible decisions:
   - auto_fix: Simple duplicates that can be automatically refactored
   - create_issue: Complex duplicates requiring human review
   - ignore: Acceptable patterns or false positives
   - escalate: Critical issues requiring immediate attention

7. OUTPUT GENERATION
   The system produces:

   - Summary statistics (files scanned, duplicates found, etc.)
   - Detailed duplicate groups with evidence
   - Expert agent recommendations
   - Decision matrix actions
   - Quality improvement suggestions

CHROMADB STORAGE:
=================

Each project maintains its own isolated ChromaDB database:
- Location: <project_root>/.ci-registry/chromadb/
- Collections: code_symbols, duplicate_groups
- Persistence: SQLite backend with vector indices
- Isolation: No cross-project contamination

The database stores:
- Code symbol embeddings
- File paths and line numbers
- Symbol metadata (type, language, complexity)
- Duplicate group relationships
- Historical analysis results

USAGE:
======

Run against current project:
  python test_ci_duplication_process.py

Run against specific project:
  python test_ci_duplication_process.py --project-root /path/to/project

With verbose output:
  python test_ci_duplication_process.py --verbose

Limit file scanning:
  python test_ci_duplication_process.py --max-files 100

COMMON ISSUES:
==============

1. Import Errors
   - Ensure PYTHONPATH includes shared/utils and shared directories
   - Check that all dependencies are installed (chromadb, transformers, etc.)

2. Expert Agent Failures
   - Agents may timeout on very large duplicate groups
   - Network issues can cause agent communication failures
   - Complex code may exceed agent analysis capabilities

3. False Positives
   - Despite filtering, some patterns may still be flagged
   - Adjust thresholds in .ci-registry/ci_config.json
   - Add custom patterns to language-specific filters

4. Performance
   - Large codebases may take significant time to analyze
   - Use --max-files to limit scope for testing
   - ChromaDB indexing is one-time cost per project
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any
import argparse

# Setup import paths and import utilities
try:
    from utils.path_resolver import get_ci_dir
    from core.utils.cross_platform import CommandExecutor
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print("Ensure PYTHONPATH includes the shared directory", file=sys.stderr)
    sys.exit(1)


def run_orchestration_bridge(
    project_root: Path, config_path: str = None, verbose: bool = False
) -> Dict[str, Any]:
    """
    Run the orchestration bridge duplicate detection process.

    Args:
        project_root: Root directory of project to analyze
        config_path: Optional path to custom CI configuration file
        verbose: Enable verbose output

    Returns:
        Dictionary containing analysis results and any errors
    """

    print(f"🔍 Running duplicate detection on: {project_root}")

    # Find the orchestration bridge script
    bridge_script = get_ci_dir("integration") / "orchestration_bridge.py"

    if not bridge_script.exists():
        return {
            "error": f"Orchestration bridge not found at {bridge_script}",
            "success": False,
        }

    # Build command arguments
    args = ["--project-root", str(project_root)]

    if config_path:
        args.extend(["--config-path", config_path])

    if verbose:
        print(f"  Script: {bridge_script}")
        print(f"  Args: {args}")

    start_time = time.time()

    # Execute the orchestration bridge
    returncode, stdout, stderr = CommandExecutor.run_python_script(
        str(bridge_script), args
    )

    execution_time = time.time() - start_time

    # Parse results
    if returncode == 0 and stdout:
        try:
            # The orchestration bridge outputs progress messages before JSON
            # Find the JSON part (starts with '{' and ends with '}')
            lines = stdout.strip().split("\n")
            json_lines = []
            found_json_start = False
            brace_count = 0

            for line in lines:
                if not found_json_start and line.strip().startswith("{"):
                    found_json_start = True

                if found_json_start:
                    json_lines.append(line)
                    brace_count += line.count("{") - line.count("}")
                    if brace_count == 0:
                        break

            if json_lines:
                json_str = "\n".join(json_lines)
                results = json.loads(json_str)
                results["execution_time"] = execution_time
                results["success"] = True
                return results
            else:
                return {
                    "error": "No JSON output found in response",
                    "stdout": stdout[:500],
                    "stderr": stderr,
                    "success": False,
                    "execution_time": execution_time,
                }
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse JSON output: {e}",
                "stdout": stdout[:500],
                "stderr": stderr,
                "success": False,
                "execution_time": execution_time,
            }
    else:
        return {
            "error": "Orchestration bridge execution failed",
            "returncode": returncode,
            "stderr": stderr,
            "stdout": stdout[:500] if stdout else None,
            "success": False,
            "execution_time": execution_time,
        }


def analyze_results(results: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze and summarize the orchestration bridge results.

    Args:
        results: Raw results from orchestration bridge
        verbose: Enable detailed output

    Returns:
        Analysis summary with key metrics
    """

    if not results.get("success"):
        return {
            "status": "failed",
            "error": results.get("error", "Unknown error"),
            "execution_time": results.get("execution_time", 0),
        }

    summary = {
        "status": "success",
        "execution_time": results.get("execution_time", 0),
        "files_scanned": results.get("summary", {}).get("files_scanned", 0),
        "symbols_extracted": results.get("summary", {}).get("symbols_extracted", 0),
        "duplicate_groups": len(results.get("duplicates", [])),
        "total_duplicates": 0,
        "expert_agent_calls": 0,
        "failed_agent_calls": 0,
        "decisions": {"auto_fix": 0, "create_issue": 0, "ignore": 0, "escalate": 0},
    }

    # Count duplicates and analyze expert agent calls
    for group in results.get("duplicates", []):
        summary["total_duplicates"] += len(group.get("duplicates", []))

        # Check for expert agent analysis
        if "expert_analysis" in group:
            summary["expert_agent_calls"] += 1
            if group["expert_analysis"].get("error"):
                summary["failed_agent_calls"] += 1

        # Count decision types
        decision = group.get("decision", {}).get("action", "unknown")
        if decision in summary["decisions"]:
            summary["decisions"][decision] += 1

    # Add false positive filtering stats if available
    if "filtering_stats" in results:
        summary["filtering_stats"] = results["filtering_stats"]

    return summary


def print_report(summary: Dict[str, Any], verbose: bool = False):
    """
    Print a formatted report of the analysis results.

    Args:
        summary: Analysis summary from analyze_results
        verbose: Enable detailed output
    """

    print("\n" + "=" * 60)
    print("CI DUPLICATION DETECTION REPORT")
    print("=" * 60)

    if summary["status"] == "failed":
        print(f"❌ Analysis Failed: {summary['error']}")
        print(f"   Execution time: {summary['execution_time']:.2f}s")
        return

    print("\n📊 Summary Statistics:")
    print(f"   Files scanned:        {summary['files_scanned']:,}")
    print(f"   Symbols extracted:    {summary['symbols_extracted']:,}")
    print(f"   Duplicate groups:     {summary['duplicate_groups']}")
    print(f"   Total duplicates:     {summary['total_duplicates']}")
    print(f"   Execution time:       {summary['execution_time']:.2f}s")

    if summary["expert_agent_calls"] > 0:
        print("\n🤖 Expert Agent Analysis:")
        print(f"   Total calls:          {summary['expert_agent_calls']}")
        print(f"   Failed calls:         {summary['failed_agent_calls']}")
        success_rate = (
            1 - summary["failed_agent_calls"] / summary["expert_agent_calls"]
        ) * 100
        print(f"   Success rate:         {success_rate:.1f}%")

    print("\n📋 Decision Matrix Actions:")
    for action, count in summary["decisions"].items():
        if count > 0:
            print(f"   {action:15}     {count}")

    if "filtering_stats" in summary and verbose:
        print("\n🔍 False Positive Filtering:")
        stats = summary["filtering_stats"]
        print(f"   Symbol references:    {stats.get('symbol_references', 0)}")
        print(f"   Boilerplate patterns: {stats.get('boilerplate', 0)}")
        print(f"   Low complexity:       {stats.get('low_complexity', 0)}")
        print(f"   Total filtered:       {stats.get('total_filtered', 0)}")

    print("\n" + "=" * 60)


def main():
    """Main entry point for the CI duplication process test."""

    parser = argparse.ArgumentParser(
        description="Test CI Duplication Detection Process",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current directory
  python test_ci_duplication_process.py

  # Analyze specific project
  python test_ci_duplication_process.py --project-root /path/to/project

  # Use custom configuration
  python test_ci_duplication_process.py --config-path /path/to/config.json --verbose
        """,
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of project to analyze (default: current directory)",
    )

    parser.add_argument("--config-path", help="Path to custom CI configuration file")

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed statistics",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON results instead of formatted report",
    )

    args = parser.parse_args()

    # Validate project root
    if not args.project_root.exists():
        print(f"❌ Error: Project root does not exist: {args.project_root}")
        sys.exit(1)

    # Run the orchestration bridge
    results = run_orchestration_bridge(
        args.project_root, config_path=args.config_path, verbose=args.verbose
    )

    if args.json:
        # Output raw JSON results
        print(json.dumps(results, indent=2))
    else:
        # Analyze and print formatted report
        summary = analyze_results(results, verbose=args.verbose)
        print_report(summary, verbose=args.verbose)

    # Exit with appropriate code
    sys.exit(0 if results.get("success") else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🚫 Analysis interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
