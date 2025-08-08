from __future__ import annotations
import argparse
import sys
import json
from pathlib import Path
from typing import Optional

try:
    # Running as a module: python -m shared.todo-planner.cli
    from .normalize import normalize_inputs
    from .validate import check_readiness
    from .synthesize import synthesize_task_plan

    _PKG = True
except Exception:  # pragma: no cover
    # Running as a script directly
    from normalize import normalize_inputs
    from validate import check_readiness
    from synthesize import synthesize_task_plan

    _PKG = False


def read_text(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        print(f"Missing file: {path}", file=sys.stderr)
        return None
    return p.read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stub-first implementation skeleton planner"
    )
    ap.add_argument(
        "--prd",
        required=True,
        help="Path to PRD markdown file (self-contained with design info)",
    )
    ap.add_argument("--stack", required=False, help="Override stack profile detection")
    ap.add_argument(
        "--out-dir", required=False, help="Directory to render skeleton files"
    )
    ap.add_argument(
        "--templates",
        required=False,
        default=str(Path(__file__).parent / "templates"),
        help="Templates root directory",
    )
    ap.add_argument("--dry-run", action="store_true", help="Plan only, no file writes")
    ap.add_argument(
        "--check-readiness", action="store_true", help="Check readiness and exit"
    )
    ap.add_argument(
        "--stub-level",
        type=int,
        default=1,
        choices=[0, 1, 2],
        help="Stub verbosity level",
    )
    ap.add_argument(
        "--gates",
        action="store_true",
        help="Run planning quality gates and print results",
    )
    ap.add_argument(
        "--emit-guide", required=False, help="Path to write Implementation Guide JSON"
    )
    ap.add_argument(
        "--emit-manifest",
        required=False,
        help="Path to write synthesized TaskPlan manifest JSON",
    )

    args = ap.parse_args()

    prd_text = read_text(args.prd)
    if prd_text is None:
        return 2

    # PRD now contains all design information
    context = normalize_inputs(prd_text, None)
    if args.stack:
        context["tech_stack"] = args.stack

    report = check_readiness(context)
    if args.check_readiness:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "missing": report.missing,
                    "questions": report.questions,
                },
                indent=2,
            )
        )
        return 0 if report.ok else 1

    if not report.ok:
        print("Readiness check failed. Please answer questions:")
        for q in report.questions:
            print(f"- {q}")
        return 1

    plan = synthesize_task_plan(context)

    # Optional: run planning gates
    if args.gates:
        if _PKG:
            from .gates import run_gates
        else:
            from gates import run_gates
        ok, issues = run_gates(plan)
        print(json.dumps({"gates_ok": ok, "issues": issues}, indent=2))

    if args.dry_run or not args.out_dir:
        print(
            json.dumps(
                {
                    "project": plan.project.__dict__,
                    "files": [f.path for f in plan.files],
                    "functions": [fn.id for pf in plan.files for fn in pf.functions],
                },
                indent=2,
            )
        )
        if args.emit_guide:
            if _PKG:
                from .guide import build_implementation_guide
            else:
                from guide import build_implementation_guide
            guide = build_implementation_guide(plan)
            Path(args.emit_guide).write_text(
                json.dumps(guide, indent=2), encoding="utf-8"
            )
            print(f"Wrote Implementation Guide to {args.emit_guide}")
        if args.emit_manifest:
            # Serialize plan to JSON (basic dataclass expansion)
            manifest = {
                "project": plan.project.__dict__,
                "modules": [m.__dict__ for m in plan.modules],
                "files": [
                    {
                        "path": pf.path,
                        "kind": pf.kind,
                        "exports": pf.exports,
                        "functions": [
                            {
                                "id": fn.id,
                                "name": fn.name,
                                "signature": {
                                    "params": fn.signature.params,
                                    "returns": fn.signature.returns,
                                    "async_fn": fn.signature.async_fn,
                                    "throws": fn.signature.throws,
                                },
                                "description": fn.description,
                                "requirements": fn.requirements,
                                "calls": fn.calls,
                            }
                            for fn in pf.functions
                        ],
                    }
                    for pf in plan.files
                ],
                "call_graph": plan.call_graph,
                "dependencies": plan.dependencies,
                "test_plan": plan.test_plan,
                "traceability": plan.traceability,
            }
            Path(args.emit_manifest).write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )
            print(f"Wrote TaskPlan manifest to {args.emit_manifest}")
        return 0

    # Render
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Lazy import render to avoid jinja2 requirement during dry-run
    if _PKG:
        from .render import render_plan
    else:
        from render import render_plan
    render_plan(plan, args.templates, str(out_dir), stub_level=args.stub_level)
    if args.emit_guide:
        if _PKG:
            from .guide import build_implementation_guide
        else:
            from guide import build_implementation_guide
        guide = build_implementation_guide(plan)
        Path(args.emit_guide).write_text(json.dumps(guide, indent=2), encoding="utf-8")
        print(f"Wrote Implementation Guide to {args.emit_guide}")
    if args.emit_manifest:
        manifest = {
            "project": plan.project.__dict__,
            "modules": [m.__dict__ for m in plan.modules],
            "files": [
                {
                    "path": pf.path,
                    "kind": pf.kind,
                    "exports": pf.exports,
                    "functions": [
                        {
                            "id": fn.id,
                            "name": fn.name,
                            "signature": {
                                "params": fn.signature.params,
                                "returns": fn.signature.returns,
                                "async_fn": fn.signature.async_fn,
                                "throws": fn.signature.throws,
                            },
                            "description": fn.description,
                            "requirements": fn.requirements,
                            "calls": fn.calls,
                        }
                        for fn in pf.functions
                    ],
                }
                for pf in plan.files
            ],
            "call_graph": plan.call_graph,
            "dependencies": plan.dependencies,
            "test_plan": plan.test_plan,
            "traceability": plan.traceability,
        }
        Path(args.emit_manifest).write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        print(f"Wrote TaskPlan manifest to {args.emit_manifest}")
    print(f"Rendered skeleton to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
