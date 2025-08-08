from __future__ import annotations
from typing import Dict, List, Tuple
import re

# Very light placeholder normalization. In a real integration, parse PRD/Design to extract entities/routes/APIs.


def _parse_requirements(lines: List[str]) -> Tuple[Dict[str, str], List[str]]:
    reqs: Dict[str, str] = {}
    ordered: List[str] = []
    pat = re.compile(r"\b(PRD-[\w.\-]+)\b[:\s-]*(.*)$", re.IGNORECASE)
    for raw in lines:
        line = raw.strip().lstrip("- ")
        m = pat.search(line)
        if m:
            rid = m.group(1).upper()
            title = (m.group(2) or "").strip()
            if rid not in reqs:
                reqs[rid] = title
                ordered.append(rid)
    return reqs, ordered


def normalize_inputs(prd_text: str, design_text: str | None) -> Dict:
    context: Dict = {
        "product_vision": None,
        "problem_statement": None,
        "tech_stack": None,
        "constraints": None,
        "requirements": {},  # id -> title
        "requirements_order": [],
        "notes": [],
    }
    # Heuristics (placeholder): look for headings
    lines = prd_text.splitlines()
    for line in lines:
        low = line.strip().lower()
        if low.startswith("vision:"):
            context["product_vision"] = line.split(":", 1)[1].strip()
        elif low.startswith("problem:"):
            context["problem_statement"] = line.split(":", 1)[1].strip()
        elif low.startswith("stack:"):
            context["tech_stack"] = line.split(":", 1)[1].strip()
        elif low.startswith("constraints:"):
            context["constraints"] = line.split(":", 1)[1].strip()

    # Requirements list (lines that include PRD-*)
    reqs, order = _parse_requirements(lines)
    context["requirements"] = reqs
    context["requirements_order"] = order
    if design_text:
        context["notes"].append("design_attached")
    return context
