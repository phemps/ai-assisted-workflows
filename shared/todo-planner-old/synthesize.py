from __future__ import annotations
from typing import Dict, List, DefaultDict
from collections import defaultdict

try:
    from .models import (
        TaskPlan,
        ProjectSettings,
        Module,
        PlannedFile,
        PlannedFunction,
        FunctionSignature,
    )
except Exception:  # pragma: no cover
    from models import (
        TaskPlan,
        ProjectSettings,
        Module,
        PlannedFile,
        PlannedFunction,
        FunctionSignature,
    )

# Composable synthesizer that produces a stub-first plan based on PRD context.


def synthesize_task_plan(context: Dict) -> TaskPlan:
    stack = (context.get("tech_stack") or "").strip().lower()
    # Primary profile: default to Next.js app unless FastAPI is explicitly requested
    if "fastapi" in stack:
        profile = "python-fastapi"
        language = "python"
    else:
        profile = "nextjs-app-router"
        language = "typescript"

    # Supplemental profiles based on keywords
    profiles: List[str] = []
    # Supplemental profiles are additive and do not form combined stack labels
    if any(k in stack for k in ["cloudflare", "workers"]):
        profiles.append("cloudflare-workers")
        profiles.append("cloudflare-r2")
    if "convex" in stack:
        profiles.append("convex")
    if "posthog" in stack or "analytics" in stack:
        profiles.append("analytics-posthog")
    # Do not include generic node runner profile by default; add only when required

    project = ProjectSettings(
        name=context.get("project_name") or "sample-project",
        stack_profile=profile,
        language=language,
        package_manager="npm" if language == "typescript" else None,
        profiles=profiles,
    )

    modules = [
        Module(name="core", purpose="Core domain and services"),
        Module(name="api", purpose="HTTP endpoints/controllers", depends_on=["core"]),
    ]

    # Prefer parsed requirements; fall back to PRD-1.0 as a generic anchor
    prd_ids = list((context.get("requirements") or {}).keys()) or ["PRD-1.0"]
    prd_anchor = prd_ids[0]

    files: List[PlannedFile] = []

    if profile == "nextjs-app-router":
        # UI shell
        files.append(
            PlannedFile(path="app/page.tsx", kind="page", exports=[], functions=[])
        )
        # API endpoint and service for submitting scans
        files.append(
            PlannedFile(
                path="app/api/scan/route.ts",
                kind="api-route",
                exports=[{"name": "POST", "type": "handler"}],
                functions=[
                    PlannedFunction(
                        id="api.scan.post",
                        name="POST",
                        signature=FunctionSignature(
                            params=[{"name": "req", "type": "Request"}],
                            returns="Promise<Response>",
                            async_fn=True,
                        ),
                        description="Submit scan job; enforce quotas; enqueue Cloudflare Queue",
                        requirements=[prd_anchor],
                        calls=["svc.scan.enqueue"],
                    )
                ],
                options={},
            )
        )
        files.append(
            PlannedFile(
                path="services/scan/enqueue.ts",
                kind="service",
                exports=[{"name": "enqueueScan", "type": "function"}],
                functions=[
                    PlannedFunction(
                        id="svc.scan.enqueue",
                        name="enqueueScan",
                        signature=FunctionSignature(
                            params=[{"name": "input", "type": "{ url: string }"}],
                            returns="Promise<void>",
                            async_fn=True,
                        ),
                        description="Enqueue scan job to Cloudflare Queue",
                        requirements=[prd_anchor],
                        calls=["worker.queue.send"],
                    )
                ],
                options={},
            )
        )

        # Supplemental: Cloudflare Workers consumer
        if "cloudflare-workers" in profiles:
            files.append(
                PlannedFile(
                    path="worker/queue-consumer.ts",
                    kind="worker-consumer",
                    exports=[{"name": "default", "type": "handler"}],
                    functions=[],
                    options={},
                )
            )
        # Supplemental: Convex function to record results
        if "convex" in profiles:
            files.append(
                PlannedFile(
                    path="convex/scan.ts",
                    kind="convex-function",
                    exports=[{"name": "recordScan", "type": "function"}],
                    functions=[
                        PlannedFunction(
                            id="db.scan.record",
                            name="recordScan",
                            signature=FunctionSignature(
                                params=[
                                    {
                                        "name": "input",
                                        "type": "{ url: string, score: number }",
                                    }
                                ],
                                returns="Promise<void>",
                                async_fn=True,
                            ),
                            description="Persist Scan/Score results to Convex",
                            requirements=[prd_anchor],
                            calls=[],
                        )
                    ],
                    options={},
                )
            )
    # No default node script scaffolding; planners may add explicit node-script files when needed
    else:  # python-fastapi
        files.append(
            PlannedFile(path="app/main.py", kind="router", exports=[], functions=[])
        )
        files.append(
            PlannedFile(
                path="app/services/user_service.py",
                kind="service",
                exports=[{"name": "create_user", "type": "function"}],
                functions=[
                    PlannedFunction(
                        id="svc.user.create",
                        name="create_user",
                        signature=FunctionSignature(
                            params=[{"name": "input", "type": "CreateUserInput"}],
                            returns="User",
                            async_fn=False,
                        ),
                        description="Create user with validation and welcome flow",
                        requirements=[prd_anchor],
                        calls=["repo.user.insert", "svc.notifications.enqueue_welcome"],
                    )
                ],
            )
        )

    # Build call graph from explicit calls in functions
    call_graph: List[Dict[str, str]] = []
    for pf in files:
        for fn in pf.functions:
            for callee in fn.calls:
                call_graph.append(
                    {"from": fn.id, "to": callee, "reason": "declared call"}
                )

    # Dependencies
    dependencies = {
        "runtime": ["fastapi"] if profile == "python-fastapi" else ["next"],
        "dev": ["pytest"] if profile == "python-fastapi" else ["jest"],
    }

    # Dynamic traceability: map each PRD id to functions that reference it
    trace: DefaultDict[str, List[str]] = defaultdict(list)
    for pf in files:
        for fn in pf.functions:
            for rid in fn.requirements:
                if fn.id not in trace[rid]:
                    trace[rid].append(fn.id)
    # Ensure at least the anchor exists in the dict
    if prd_anchor not in trace:
        trace[prd_anchor] = []

    plan = TaskPlan(
        project=project,
        modules=modules,
        files=files,
        call_graph=call_graph,
        dependencies=dependencies,
        test_plan={"unit": [fn.id for pf in files for fn in pf.functions][:1]},
        traceability=dict(trace),
    )
    return plan
