#!/usr/bin/env python3
"""
Standalone gate validation script for the todo-planner.
Can be called independently to validate a TaskPlan manifest.
"""
from __future__ import annotations
import argparse
import json
import sys
from typing import Dict, Any

try:
    from .gates import run_gates
    from .models import TaskPlan
    from .synthesize import synthesize_task_plan
    from .normalize import normalize_inputs
except ImportError:
    from gates import run_gates
    from models import TaskPlan
    from synthesize import synthesize_task_plan
    from normalize import normalize_inputs


def load_manifest(manifest_path: str) -> TaskPlan:
    """Load a TaskPlan from a JSON manifest file."""
    with open(manifest_path, "r") as f:
        data = json.load(f)

    # Reconstruct TaskPlan from JSON
    # This is a simplified loader - expand as needed based on actual model structure
    from types import SimpleNamespace

    def dict_to_obj(d):
        if isinstance(d, dict):
            obj = SimpleNamespace(**{k: dict_to_obj(v) for k, v in d.items()})
            return obj
        elif isinstance(d, list):
            return [dict_to_obj(item) for item in d]
        else:
            return d

    return dict_to_obj(data)


def run_gates_from_context(prd_path: str, stack: str = None) -> Dict[str, Any]:
    """Run gates from PRD (self-contained with design info)."""
    # Read input file
    with open(prd_path, "r") as f:
        prd_text = f.read()

    # Normalize and synthesize (PRD contains all design info)
    context = normalize_inputs(prd_text, None)
    if stack:
        context["tech_stack"] = stack

    plan = synthesize_task_plan(context)

    # Run gates
    ok, issues = run_gates(plan)

    return {
        "gates_passed": ok,
        "level_results": {
            "L0_schema": gate_l0_results(plan),
            "L1_integrity": gate_l1_results(plan),
            "L3_traceability": gate_l3_results(plan),
            "L4_template": gate_l4_results(plan),
        },
        "issues": issues,
        "summary": f"{'✅ All gates passed' if ok else f'❌ {len(issues)} issues found'}",
    }


def gate_l0_results(plan: TaskPlan) -> Dict[str, Any]:
    """Detailed L0 schema validation results."""
    from gates import gate_l0_schema

    issues = gate_l0_schema(plan)
    return {
        "passed": len(issues) == 0,
        "checks": {
            "has_project": bool(plan.project),
            "has_files": bool(plan.files),
            "has_stack_profile": bool(plan.project.stack_profile)
            if plan.project
            else False,
        },
        "issues": issues,
    }


def gate_l1_results(plan: TaskPlan) -> Dict[str, Any]:
    """Detailed L1 integrity validation results."""
    from gates import gate_l1_integrity

    issues = gate_l1_integrity(plan)

    # Count statistics
    total_functions = sum(len(pf.functions) for pf in plan.files)
    unique_ids = len(set(fn.id for pf in plan.files for fn in pf.functions))

    return {
        "passed": len(issues) == 0,
        "stats": {
            "total_files": len(plan.files),
            "total_functions": total_functions,
            "unique_function_ids": unique_ids,
        },
        "issues": issues,
    }


def gate_l3_results(plan: TaskPlan) -> Dict[str, Any]:
    """Detailed L3 traceability validation results."""
    from gates import gate_l3_traceability

    issues = gate_l3_traceability(plan)

    # Calculate coverage
    all_prd_ids = (
        set(plan.traceability.keys()) if hasattr(plan, "traceability") else set()
    )
    mapped_functions = set()
    if hasattr(plan, "traceability"):
        for fids in plan.traceability.values():
            mapped_functions.update(fids)

    return {
        "passed": len(issues) == 0,
        "coverage": {
            "prd_requirements": len(all_prd_ids),
            "mapped_functions": len(mapped_functions),
        },
        "issues": issues,
    }


def gate_l4_results(plan: TaskPlan) -> Dict[str, Any]:
    """Detailed L4 template options validation results."""
    from gates import gate_l4_template_options

    issues = gate_l4_template_options(plan)

    return {
        "passed": len(issues) == 0,
        "stack_profile": plan.project.stack_profile if plan.project else None,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(description="Run planning quality gates")
    parser.add_argument(
        "--prd", required=True, help="Path to PRD markdown file (self-contained)"
    )
    parser.add_argument("--stack", help="Override stack profile detection")
    parser.add_argument(
        "--manifest", help="Path to pre-generated manifest JSON (skip synthesis)"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        if args.manifest:
            # Load existing manifest
            plan = load_manifest(args.manifest)
            ok, issues = run_gates(plan)
            results = {"gates_passed": ok, "issues": issues}
        else:
            # Run from PRD
            results = run_gates_from_context(args.prd, args.stack)

        if args.output_format == "json":
            print(json.dumps(results, indent=2))
        else:
            # Text format for human reading
            print("\n🔍 Planning Quality Gates Report")
            print("=" * 50)
            print(f"\nOverall: {results['summary']}")

            if args.verbose and "level_results" in results:
                for level, data in results["level_results"].items():
                    status = "✅" if data["passed"] else "❌"
                    print(f"\n{status} {level}:")
                    if "checks" in data:
                        for check, value in data["checks"].items():
                            print(f"  - {check}: {value}")
                    if "stats" in data:
                        for stat, value in data["stats"].items():
                            print(f"  - {stat}: {value}")
                    if data["issues"]:
                        print("  Issues:")
                        for issue in data["issues"]:
                            print(f"    • {issue}")

            if results["issues"]:
                print(f"\n⚠️  Issues Found ({len(results['issues'])}):")
                for i, issue in enumerate(results["issues"], 1):
                    print(f"  {i}. {issue}")

        return 0 if results["gates_passed"] else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
