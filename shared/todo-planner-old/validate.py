from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict

MIN_FIELDS = [
    "product_vision",
    "problem_statement",
    "tech_stack",
    "constraints",
]


@dataclass
class ReadinessReport:
    ok: bool
    missing: List[str]
    questions: List[str]


def check_readiness(context: Dict) -> ReadinessReport:
    missing = [k for k in MIN_FIELDS if not context.get(k)]
    questions: List[str] = []
    if "product_vision" in missing:
        questions.append("What's the concise product vision (1-2 sentences)?")
    if "problem_statement" in missing:
        questions.append(
            "What problem are we solving and for whom? What does success look like?"
        )
    if "tech_stack" in missing:
        questions.append(
            "Which stack profile are we targeting (e.g., nextjs-app-router, python-fastapi)? Any versions?"
        )
    if "constraints" in missing:
        questions.append(
            "List constraints: security/compliance/perf/deployment/SLAs and must-not-violates."
        )

    return ReadinessReport(
        ok=len(missing) == 0,
        missing=missing,
        questions=questions,
    )
