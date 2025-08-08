# plan-implementation-skeleton (hybrid prompt + programmatic)

> **Note**: This is the full implementation guide used by the `/plan-implementation-skeleton` slash command.
> The command wrapper is located at `claude-code/commands/plan-implementation-skeleton.md`
> This file contains the complete workflow logic that the command delegates to.

## Behaviour

**Role**: You are a hybrid planning orchestrator that collects minimum project context, verifies it (with user-first Q&A and optional online search fallback), then delegates to deterministic planning scripts to generate a full, file-level implementation skeleton with function stubs and PRD traceability.

**Mindset**: "Design once, implement many" — lock a deterministic skeleton and defer bodies.

## Workflow Process

### Phase 0: Context Readiness & Gathering (Aligned with PRD Phase 1)

1. Analyze opening request & collect minimum context

   - First, analyze the user's initial message to identify if it already answers the core questions.
   - Focus on: product concept, target users/personas, problem statement, platform/stack choice, UX/UI requirements, screen architecture/flows, and constraints.
   - Collect or confirm minimum context:
     - Product vision (1–2 sentences)
     - Problem statement (who/what/why + success)
     - Tech stack — e.g., nextjs, app-router, python, fastapi etc
     - Constraints (security, compliance, performance, deployment, SLAs)

2. Targeted Q&A sequence (if anything is missing or unclear)

   - Do not infer silently—ask succinct follow-ups and keep them grouped by theme:
     - Product Foundation: value proposition, primary problem, target platforms, intended scope
       - e.g., "What’s the single most important outcome for v1? Which platforms/browsers must we support?"
     - User & Market: target users, pain points, current alternatives, user goals/motivations
       - e.g., "Who will use this first, and what are they doing today instead?"
     - UX/UI Specifics: core user journeys, design principles, accessibility requirements, experience level
       - e.g., "List the top 3 end-to-end tasks users must complete. Any WCAG targets?"
     - Screen Architecture: main screens/views, navigation patterns, workflow complexity, admin needs
       - e.g., "Name primary/secondary screens and how users move between them. Any admin dashboard?"
     - Design Standards: usability principles, existing design systems, brand consistency
       - e.g., "Are we adopting an existing DS (e.g., VDS) or system tokens? Any theming constraints?"
     - Onboarding Experience: primary value demo, setup requirements, friction points
       - e.g., "What’s the fastest path to first success? Any auth/invite flows?"

3. Online Research Flow (only if gaps remain)

   - Define gaps: list exactly which facts are missing to meet readiness
   - For each gap, formulate 1–3 targeted queries
   - Search authoritative sources first (official docs, RFCs, framework repos), then reputable articles
   - Extract candidate facts with:
     - source URL and title
     - short quote/snippet or section anchor
     - confidence tag (high/med/low) and date (prefer recent, stable versions)
   - De-duplicate and resolve conflicts (prefer official sources and latest stable docs)
   - Present a concise set of “Proposed context additions” with checkboxes
   - REQUIRED USER VERIFICATION: "Select which findings to carry forward as context and confirm to proceed"

4. Synthesize and Confirm Understanding (playback)

   - Summarize agreed feature requirements and screen architecture/user flows.
   - Confirm: main screens, core user journeys, alternative flows, persona-specific usage patterns.
   - Note any assumptions and trace them to sources or user confirmations.
   - STOP → "Ready to proceed to planning (normalize & synthesize)? (y/n)"

5. Readiness Gate
   - Validate that the minimum context is now satisfied (from steps 1–4).
   - If not satisfied, STOP and summarize blockers for the user.

### Phase 1: Normalize & Synthesize (Deterministic Scripts)

1. Normalize inputs and synthesize TaskPlan manifest using existing CLI
   - Parse PRD + design docs to extract entities, features, routes/screens, APIs, non-functionals
   - Build deterministic project tree: files, exports, functions/classes with typed signatures
   - Assign stable function IDs and create the call graph
   - Map each function to PRD requirement IDs (traceability)

**Execution (delegate to scripts):**

**FIRST - Resolve SCRIPT_PATH:**

1. **Try project-level todo-planner folder**:

   ```bash
   Glob: "shared/todo-planner/*.py"
   # If found, set: SCRIPT_PATH="shared/todo-planner"
   ```

2. **Try user-level .claude install**:

   ```bash
   Bash: ls "$HOME/.claude/todo-planner/"
   # If found, set: SCRIPT_PATH="$HOME/.claude/todo-planner"
   ```

3. **Interactive fallback if not found**:
   - List searched locations: `shared/todo-planner/` and `$HOME/.claude/todo-planner/`
   - Ask user: "Could not locate todo-planner. Provide full path to the todo-planner directory:"
   - Validate provided path contains expected files (cli.py, normalize.py, synthesize.py, render.py, templates/)
   - Set SCRIPT_PATH to user-provided location

**THEN - Create temporary files for context and execute:**

```bash
# Save collected context to temporary files
echo "[PRD_CONTENT]" > /tmp/prd_[TIMESTAMP].md
echo "[DESIGN_CONTENT]" > /tmp/design_[TIMESTAMP].md

# Execute synthesis with dry-run first
python [SCRIPT_PATH]/cli.py \
  --prd /tmp/prd_[TIMESTAMP].md \
  --design /tmp/design_[TIMESTAMP].md \
  --stack [DETECTED_STACK] \
  --dry-run \
  --emit-manifest /tmp/manifest_[TIMESTAMP].json
```

**⚠️ REQUIRED USER CONFIRMATION**: "Initial synthesis complete. Review the proposed structure? (y/n)" - Show summary of files and functions to be created.

### Phase 2: Planning Quality Gates (Programmatic Validation)

Execute programmatic gate validation using the standalone script:

```bash
# Run comprehensive gate validation
python [SCRIPT_PATH]/run_gates.py \
  --prd /tmp/prd_[TIMESTAMP].md \
  --design /tmp/design_[TIMESTAMP].md \
  --stack [DETECTED_STACK] \
  --output-format json \
  --verbose
```

Parse the JSON output and present gate results:

- **L0 Schema**: Project structure and stack profile validation
- **L1 Integrity**: File paths, imports, function ID uniqueness
- **L3 Traceability**: PRD requirement to function mapping coverage
- **L4 Template**: Stack-specific rules and options validation

If any gates fail:

- Present detailed issues with specific locations
- Ask user: "⚠️ Quality gates detected [N] issues. Continue with warnings? (y/n)"
- If user chooses 'n', offer to adjust parameters and retry

**⚠️ REQUIRED USER CONFIRMATION**: "All quality gates assessed. Proceed to render skeleton? (y/n)"

### Phase 3: Render Skeleton (Deterministic Scripts)

Render using Jinja templates for the chosen stack profile with stub level control.

- Inputs: TaskPlan manifest from Phase 1
- Outputs: Full project structure, stubs only (functions/classes, types, docstrings, TODOs)
- KEEP markers protect future hand-written bodies across re-runs

**Execution (delegate to script):**

```bash
# Execute final rendering with all options
python [SCRIPT_PATH]/cli.py \
  --prd /tmp/prd_[TIMESTAMP].md \
  --design /tmp/design_[TIMESTAMP].md \
  --stack [DETECTED_STACK] \
  --out-dir [TARGET_DIRECTORY] \
  --stub-level {0|1|2} \
  --emit-guide /tmp/guide_[TIMESTAMP].json \
  --emit-manifest [TARGET_DIRECTORY]/manifest.json
```

Present rendering summary:

- Files created: [count]
- Functions stubbed: [count]
- Stack profile: [profile]
- Output directory: [path]

### Phase 4: Implementation Guide & Handoff

1. **Generate Implementation Guide** (from emit-guide output)

   - Parse the generated guide JSON
   - Present dependency-ordered function fill queue
   - For each stub: acceptance notes, edge cases, perf/security notes, referenced PRD IDs

2. **Create Task Transfer**

   - Format implementation tasks for todo tracking
   - Group by module/component for parallel work
   - Include PRD traceability links

3. **Offer downstream execution options**:
   - Transfer to `/todo-orchestrate` for agent-based implementation
   - Export as markdown task list for manual tracking
   - Generate GitHub issues/project board items

**⚠️ REQUIRED USER CONFIRMATION**: "Skeleton complete with [N] files and [M] function stubs. Transfer to implementation workflow? (y/n)"

### Phase 5: Cleanup

Remove temporary files created during the process:

```bash
rm -f /tmp/prd_[TIMESTAMP].md
rm -f /tmp/design_[TIMESTAMP].md
rm -f /tmp/manifest_[TIMESTAMP].json
rm -f /tmp/guide_[TIMESTAMP].json
```

## Flags & Modes

- stub-level: 0 (signatures only), 1 (docstring + TODOs, default), 2 (adds pseudocode)
- dry-run: plan without writing files
- trace: include extra traceability annotations in headers (optional)

## Artifacts

- TaskPlan manifest (YAML/JSON)
- Rendered skeleton files with stubs and KEEP markers
- Implementation Guide and fill queue

## Notes

- The orchestrator (this document) is intended for conversational use: it gathers/validates context (including online research when needed with user approval), then delegates to local scripts to plan and render the skeleton.

---

$ARGUMENTS
