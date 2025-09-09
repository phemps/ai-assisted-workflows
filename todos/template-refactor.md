# Plan: Move from Claude‑Specific Prompts to Base Workflows + Tool Adapters

This plan outlines how to transition from “Claude‑specific prompts” to a system of base workflows and pluggable tool adapters, starting with Claude Code and OpenCode. The approach aligns with your current path resolver, install model, and command/agent conventions.

---

## What I Found

- **Claude‑specific layout with install + merge semantics**
  - `claude-code/install.sh` manages `.claude/` install, merges global rules into `claude.md`, and copies `shared/` as `scripts/` for runtime invocation.
  - Commands, agents, rules, and templates are Claude‑formatted markdown prompts under `claude-code/`.
- **Script invocation is standardized and must remain unchanged**
  - Commands call analyzers via module entrypoints with `PYTHONPATH` set to scripts root.
  - Single CLI entrypoint for analyzers: `shared/core/cli/run_analyzer.py`.
- **Current workflows encode Claude‑specific formatting details** (e.g., sectioning, `$ARGUMENTS` token) directly in the markdown.
- **Global rules** are appended to the installed `claude.md` from `claude-code/rules/global.claude.rules.md`.

---

## Proposal Overview

- **Add a base, tool‑agnostic workflow spec**, grouped by type (commands, agents, rules, templates).
- **Introduce a CLI** that:
  - Validates base files against a schema.
  - Translates/exports them via pluggable adapters (Claude Code first, OpenCode second).
  - Installs the exported output exactly where the tool expects it.
- **Do not change shared/ scripts or their import/runner behaviors**; base workflows continue to call them identically.

---

## Base Layout

```
workflows/
    commands/*.yaml      # normalized spec; no Claude formatting
    agents/*.yaml
    rules/*.md           # keep content as markdown, add front‑matter header for metadata
    templates/*.md       # optional front‑matter metadata
```

- Keep `claude-code/` as the current installed/exported representation until migration is complete.

---

## Base Workflow Spec

### Commands

**Goals:** Capture intent/steps/arguments once, avoid tool formatting, keep script calls intact.

**Minimal schema:**

```yaml
kind: command
name: analyze-security
version: 1.0.0
title: Analyze Security
description: Run security analyzers on the codebase.
behavior: Automated security analysis
phases:
    - name: Initial Analysis
        steps:
            - include: resolve_scripts_root
            - shell:
                    - PYTHONPATH="${SCRIPTS_ROOT}" python -c "import core.base; print('env OK')"
            - analyzer:
                    key: security:semgrep
                    target: "."
            - analyzer:
                    key: security:detect_secrets
                    target: "."
            - confirm:
                    message: "Automated security analysis complete. Proceed with gap assessment? (y/n)"
arguments:
    # schema for user arguments
vars:
    # environment variables to surface
metadata:
    tags: [security, analysis]
```

- **Shared partials (DRY):** e.g., `partials/resolve_scripts_root.yaml`, `partials/quality_gates.yaml`.

### Agents

```yaml
kind: agent
name: python-expert
version: 1.0.0
role: Python code expert
system_prompt: >
  You are a Python expert...
capabilities:
  - planning
  - code-changes
  - analysis
constraints:
  - no fallback modes
  - must validate quality gates
tools:
  - security:semgrep
```

### Rules and Templates

- Keep content as Markdown but add basic YAML front‑matter:

```markdown
---
kind: rule
name: python-security
version: 1.0.0
tags: [python, security]
---

# Rule Content Here
```

---

## Tool Adapter Architecture

- CLI builds an in‑memory AST from base YAML/Markdown.
- **Adapters** receive normalized AST and render to outputs:
  - **Claude Code adapter:** renders markdown with headings, codeblocks, `$ARGUMENTS` footer, merges global rules into `claude.md`.
  - **OpenCode adapter:** renders to that tool’s expected structure and syntax.
- **Adapters** are Python classes with a small interface:
  - `render_command(ast) -> FileBundle`
  - `render_agent(ast) -> FileBundle`
  - `render_rule(ast) -> FileBundle`
  - `render_template(ast) -> FileBundle`
- Use **Jinja2** for templates, **Pydantic** for schema validation, and **Click** for CLI.

---

## Claude Code Adapter

- Output layout mirrors `claude-code/` today.
- Rendering rules:
  - Map phases to `### Phase N: ...`
  - Map shell arrays to triple‑backtick blocks (`bash`)
  - Map analyzer steps to `python -m core.cli.run_analyzer` lines (preserve `PYTHONPATH`)
  - Keep confirmation gates as explicit “REQUIRED USER CONFIRMATION” blocks
  - Append `$ARGUMENTS` at end of command files where defined
- For rules: drop front‑matter, keep content; inject header when merging into `claude.md`.

**Install:**

- Option A: CLI exports to `build/claude-code/` then calls existing `claude-code/install.sh`.
- Option B: CLI performs the same copy logic as `install.sh` directly.

---

## OpenCode Adapter

- Need to confirm OpenCode’s expected file format and install semantics.
- Once spec is known, implement file emission using the same AST.
- Preserve shell/analyzer invocation surface so `shared/` scripts function identically.

---

## CLI Design

**Command:** `aiwf`

- `aiwf validate` — Schema‑validate base workflows and check shell/analyzer references.
- `aiwf export --tool claude-code --out build/claude-code` — Produce tool‑specific files.
- `aiwf install --tool claude-code --dest <path>` — Export + install (replicates install.sh copy/merge semantics).
- `aiwf list-tools` — Show installed adapters.
- `aiwf new <kind> <name>` — Scaffold base files using templates.

**Libraries:** Click (CLI), Pydantic (schema), Jinja2 (rendering), ruamel.yaml (YAML), Rich (output).

**Config:**

- `workflows/config.yaml` — defaults (version, tags, export filters)
- `tools/adapters/*.yaml` — adapter metadata if needed

---

## Install/Deploy Behavior

- Scripts remain unchanged and are called exactly as today.
- Analyzer calls stay via `python -m core.cli.run_analyzer`.
- For Claude Code: keep `claude-code/install.sh` as is; new CLI can call it after export or handle copies directly.
- For future tools: CLI performs install logic per adapter.

---

## Migration Plan

**Phase 1 (non‑breaking):**

- Create `workflows/` with a few high‑value base commands and 2–3 agents.
- Build `aiwf` with validate/export for Claude Code.
- Export into `build/claude-code/` and confirm diffs match current files’ behavior.

**Phase 2:**

- Migrate remaining commands/agents/rules/templates into base format.
- Add “partials” for shared blocks.

**Phase 3:**

- Implement OpenCode adapter once spec is confirmed.
- Add adapter contract tests (golden file diffs).

---

## Why This Fits Your Constraints

- Keeps `shared/` intact and preserves analyzer invocation semantics.
- Removes Claude‑specific formatting from source and centralizes translation in adapters.
- Uses established libraries.
- Single‑responsibility boundaries: base spec, adapters, CLI, and existing scripts.
- No fallbacks; each adapter must fully implement its tool’s format and install behavior.

---

## Open Questions

- OpenCode spec: file format, folder conventions, and install method?
- Should the new CLI call `claude-code/install.sh` or replace its copy logic?
- Any immediate commands/agents to prioritize for the first base set?

---

If desired, I can draft the base spec for `analyze-security` and `python-expert` plus a minimal `aiwf` CLI skeleton (export + validate) to make this concrete and ready to iterate.
