from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Core data models for the TaskPlan manifest.


@dataclass
class RequirementTrace:
    id: str
    title: Optional[str] = None


@dataclass
class FunctionSignature:
    params: List[Dict[str, str]]  # [{name, type}]
    returns: Optional[str] = None
    async_fn: bool = False
    throws: List[str] = field(default_factory=list)


@dataclass
class PlannedFunction:
    id: str
    name: str
    signature: FunctionSignature
    description: str
    requirements: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)  # function-ids
    input_schema: Optional[Dict] = None
    output_schema: Optional[Dict] = None


@dataclass
class PlannedFile:
    path: str
    kind: str  # e.g., service, page, api-route, router, model
    exports: List[Dict[str, str]] = field(default_factory=list)
    functions: List[PlannedFunction] = field(default_factory=list)
    # Optional template toggles selected by the planner/LLM (e.g., { validation: 'zod' })
    options: Dict[str, str] = field(default_factory=dict)


@dataclass
class Module:
    name: str
    purpose: str
    depends_on: List[str] = field(default_factory=list)


@dataclass
class ProjectSettings:
    name: str
    language: str
    package_manager: Optional[str] = None
    # Individual tech stack components (using better-t-stack names)
    web_frontend: Optional[
        str
    ] = None  # next, tanstack-router, react-router, svelte, etc.
    backend: Optional[str] = None  # convex, hono, express, fastify, etc.
    orm: Optional[str] = None  # drizzle, prisma, mongoose
    runtime: Optional[str] = None  # bun, nodejs, workers
    auth: Optional[str] = None  # clerk, better-auth, etc.
    # Legacy field for backwards compatibility (will be deprecated)
    stack_profile: Optional[str] = None


@dataclass
class TaskPlan:
    project: ProjectSettings
    modules: List[Module]
    files: List[PlannedFile]
    call_graph: List[Dict[str, str]] = field(
        default_factory=list
    )  # [{from, to, reason}]
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # runtime/dev
    test_plan: Dict[str, List[str]] = field(default_factory=dict)
    traceability: Dict[str, List[str]] = field(
        default_factory=dict
    )  # prd_id -> [function-id]
