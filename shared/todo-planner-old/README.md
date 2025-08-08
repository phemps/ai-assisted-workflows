# Task Planning Workflow (Stub-First Skeleton Planner)

A token-efficient, PRD-driven planning workflow that converts an existing PRD (e.g., from plan-ux-prd.md) and supporting docs into a deterministic, file-level implementation skeleton using Jinja templates. It preserves PRPs-agentic-eng strengths (explicit project map, cross-file call graph, zero-duplication) while generating stubs instead of full function bodies.

## What it does

- Validates input context readiness (product vision, problem statement, tech stack, constraints)
- Normalizes PRD + design docs into a TaskPlan manifest
- Synthesizes a deterministic project tree with files, exports, and function contracts
- Renders language/framework-specific stubs via Jinja templates
- Outputs an Implementation Guide and a fill queue for downstream implementation

## Readiness gate (start-of-workflow)

1. Validate minimum context:
   - Product vision
   - Problem statement
   - Tech stack (stack profile)
   - Constraints (security, compliance, performance, deployment)
2. If missing, the planner emits a list of questions for you to answer first.
3. If still incomplete, optional search fallback can be used (requires user verification of findings). This repository does not perform network calls by default.

## Structure

- cli.py — entrypoint to run checks, plan, and render
- validate.py — readiness/threshold checks and question generation
- normalize.py — PRD/design doc normalization
- synthesize.py — TaskPlan manifest synthesis
- render.py — Jinja-based renderer for skeleton files
- models.py — data models for the manifest
- templates/ — Jinja templates per stack profile
- examples/ — small example PRD/design docs
- plan-implementation-skeleton.md — hybrid prompt-orchestrated workflow for conversational use (recommended)

## Minimal usage

- Check readiness only (no rendering):
  - python cli.py --prd examples/prd.md --design examples/design.md --stack nextjs-app-router --check-readiness
- Dry-run planning (no files written):
  - python cli.py --prd examples/prd.md --design examples/design.md --stack nextjs-app-router --dry-run
- Render skeleton (requires Jinja2 installed):
  - python cli.py --prd examples/prd.md --design examples/design.md --stack nextjs-app-router --out-dir /tmp/my-skeleton

## Outputs

- TaskPlan manifest (YAML)
- Rendered file skeletons (stubs only, with TODOs and PRD traceability)
- Implementation Guide (ordered fill queue, dependencies, and clarifications)

## Templates

Profiles are composable:

- Primary app profile (e.g., nextjs-app-router)
- Supplemental profiles for infra/services (cloudflare-workers, convex, cloudflare-r2, analytics-posthog, nodejs)
  - First matched template per kind wins based on profile order

Extend by adding templates under templates/<profile>/<kind>.jinja and listing the profile in ProjectSettings.profiles.

## Idempotency and safety

- Files include KEEP/BEGIN-IMPL/END-IMPL markers to protect hand-written bodies.
- Re-runs do not overwrite bodies by default; use --dry-run to preview.

## Notes

- This module avoids network access. Any search fallback must be performed manually and verified by the user.
- For conversational, hybrid operation, follow the steps in plan-implementation-skeleton.md (collect readiness context, then delegate to scripts).
