from __future__ import annotations
from typing import List, Dict, Tuple

try:
    from .models import TaskPlan
except Exception:  # pragma: no cover
    from models import TaskPlan


class GateFailure(Exception):
    pass


def gate_l0_schema(plan: TaskPlan) -> List[str]:
    issues: List[str] = []
    if not plan.project or not plan.files:
        issues.append("missing project or files")
    if not plan.project.stack_profile:
        issues.append("missing stack_profile")
    return issues


def gate_l1_integrity(plan: TaskPlan) -> List[str]:
    issues: List[str] = []
    # duplicate function ids
    seen: Dict[str, str] = {}
    for pf in plan.files:
        if not pf.path or "/" not in pf.path and "." not in pf.path:
            issues.append(f"suspicious path: {pf.path}")
        for fn in pf.functions:
            if fn.id in seen:
                issues.append(
                    f"duplicate function id: {fn.id} in {pf.path} and {seen[fn.id]}"
                )
            else:
                seen[fn.id] = pf.path
            # basic signature check
            if fn.signature is None or fn.signature.params is None:
                issues.append(f"missing signature for {fn.id}")
    return issues


def gate_l3_traceability(plan: TaskPlan) -> List[str]:
    issues: List[str] = []
    # ensure functions mapped in traceability appear in files
    all_ids = {fn.id for pf in plan.files for fn in pf.functions}
    for prd, fids in plan.traceability.items():
        for fid in fids:
            if fid not in all_ids:
                issues.append(
                    f"traceability points to missing function: {prd} -> {fid}"
                )
    return issues


def gate_l4_template_options(plan: TaskPlan) -> List[str]:
    issues: List[str] = []
    # Enforce singular primary stack label (no combined labels)
    combined = ["nextjs-workers-convex", "nextjs-convex", "nextjs-workers"]
    if any(x in plan.project.stack_profile for x in combined):
        issues.append(f"combined stack label not allowed: {plan.project.stack_profile}")

    # If options are set for api-route, require advice markers to be present in rendered content later
    # Here we can only check that options are recognized per kind; deep content checks would occur post-render.
    valid_api_opts = {"validation", "auth", "queue"}
    for pf in plan.files:
        if pf.kind == "api-route" and getattr(pf, "options", {}):
            unknown = set(pf.options.keys()) - valid_api_opts
            if unknown:
                issues.append(
                    f"api-route has unknown options: {sorted(unknown)} in {pf.path}"
                )
    return issues


def run_gates(plan: TaskPlan) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    issues += gate_l0_schema(plan)
    issues += gate_l1_integrity(plan)
    issues += gate_l3_traceability(plan)
    issues += gate_l4_template_options(plan)
    return (len(issues) == 0, issues)
