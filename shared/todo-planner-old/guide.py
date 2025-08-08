from __future__ import annotations
from typing import Dict, List

try:
    from .models import TaskPlan
except Exception:  # pragma: no cover
    from models import TaskPlan


def build_implementation_guide(plan: TaskPlan) -> Dict:
    # Simple ordering: functions without calls first; then others
    indegree = {fn.id: 0 for pf in plan.files for fn in pf.functions}
    for pf in plan.files:
        for fn in pf.functions:
            for callee in fn.calls:
                if callee in indegree:
                    indegree[fn.id] = indegree.get(fn.id, 0) + 1
    ordered = sorted(indegree.items(), key=lambda kv: kv[1])
    fill_queue: List[Dict] = []
    for fid, _ in ordered:
        # locate function
        for pf in plan.files:
            for fn in pf.functions:
                if fn.id == fid:
                    fill_queue.append(
                        {
                            "function_id": fid,
                            "file": pf.path,
                            "name": fn.name,
                            "requirements": fn.requirements,
                            "notes": ["Implement body per TODOs in stub."],
                        }
                    )
                    break
    guide = {
        "project": plan.project.__dict__,
        "fill_queue": fill_queue,
        "notes": [
            "Implement functions in dependency order (low indegree first).",
            "Keep re-renders safe — bodies are protected by KEEP markers.",
        ],
    }
    return guide
