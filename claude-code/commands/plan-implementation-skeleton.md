# plan-implementation-skeleton v0.2

**Mindset**: "Foundation first, then scaffold" — Create working project base with better-t-stack, add business logic skeletons.

## Behavior

Hybrid planning orchestrator that creates a PRD, uses better-t-stack for the foundation, then progressively builds implementation skeletons with function stubs and requirement traceability.

## Workflow Process

### Phase 0: Script Path Resolution

**FIRST - Resolve SCRIPT_PATH:**

1. **Try project-level todo-planner**:

   ```bash
   Glob: "shared/todo-planner/api/*.py"
   # If found, set: SCRIPT_PATH="shared/todo-planner/api"
   ```

2. **Try user-level .claude install**:

   ```bash
   Bash: ls "$HOME/.claude/todo-planner/api/"
   # If found, set: SCRIPT_PATH="$HOME/.claude/todo-planner/api"
   ```

3. **Interactive fallback**:
   - Ask user: "Could not locate todo-planner. Provide path:"
   - Validate path contains: create_bts_project.py, compile_check.py, init_skeleton.py

### Phase 1: PRD Creation & Stack Selection

1. **Analyze opening request** - Extract provided context
2. **Create PRD with better-t-stack options**:
   - Map user requirements to available better-t-stack choices
   - Present detected stack: "nextjs + hono + sqlite + drizzle + better-auth"
3. **Get user confirmation** on tech stack
4. **Save PRD and create better-t-stack config JSON**

**⚠️ REQUIRED USER CONFIRMATION**: "Proceed with this tech stack? (y/n)"

### Phase 2: Foundation Project Creation

```bash
# Create better-t-stack project
python [SCRIPT_PATH]/create_bts_project.py \
  --name [PROJECT_NAME] \
  --config bts_config.json \
  --output bts_result.json

# Verify base project quality
python [SCRIPT_PATH]/compile_check.py \
  --project-dir ./[PROJECT_NAME] \
  --output quality_check.json
```

**⚠️ REQUIRED USER CONFIRMATION**: "Base project created and verified. Proceed to skeleton? (y/n)"

### Phase 3: Skeleton Generation

```bash
# Initialize skeleton manifest
python [SCRIPT_PATH]/init_skeleton.py \
  --project-dir ./[PROJECT_NAME] \
  --prd prd_[PROJECT]_[TIMESTAMP].md \
  --output ./[PROJECT_NAME]/skeleton_manifest.json \
  --verbose

# Add modules and files progressively based on PRD
python [SCRIPT_PATH]/add_module.py \
  --manifest ./[PROJECT_NAME]/skeleton_manifest.json \
  --name auth \
  --description "Authentication and authorization" \
  --exports "AuthConfig,authMiddleware,getUser"

python [SCRIPT_PATH]/add_file.py \
  --manifest ./[PROJECT_NAME]/skeleton_manifest.json \
  --path "app/api/auth/login/route.ts" \
  --kind api-route \
  --functions '[{"name":"POST","description":"User login","return_type":"NextResponse","prd_references":["FR001"]}]'

# Render all skeleton files
python [SCRIPT_PATH]/render_skeleton.py \
  --manifest ./[PROJECT_NAME]/skeleton_manifest.json \
  --project-dir ./[PROJECT_NAME] \
  --stub-level 2
```

### Phase 4: Final Validation & Tasks

```bash
# Final quality check
python [SCRIPT_PATH]/compile_check.py \
  --project-dir ./[PROJECT_NAME] \
  --verbose

# Generate implementation tasks
python [SCRIPT_PATH]/generate_tasks.py \
  --manifest ./[PROJECT_NAME]/skeleton_manifest.json \
  --output ./[PROJECT_NAME]/IMPLEMENTATION_TASKS.md
```

Present final summary:

- ✅ Project ready: ./[PROJECT_NAME]/
- 📋 Tasks: IMPLEMENTATION_TASKS.md
- 🏗️ Foundation: better-t-stack + skeleton stubs

## Key Features

- **Working foundation**: better-t-stack creates compilable project
- **Quality gates**: Validation at each phase
- **Stub-level 2**: Pseudocode implementations
- **Template-aware**: Adapts to detected tech stack
- **Progressive building**: Add complexity incrementally
- **Implementation guide**: Priority-ordered task checklist

$ARGUMENTS
