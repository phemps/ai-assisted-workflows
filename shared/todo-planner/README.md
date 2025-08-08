# Todo Planner - API-Driven Skeleton Generator

Skeleton generation system using jinja templaes an API-like approach with better-t-stack foundation.

## What's Included

### 🏗️ **Better-T-Stack Foundation**

- Creates working projects with real dependencies
- Compiles and runs from day 1
- Supports multiple tech stacks (Next.js, Hono, Drizzle, etc.)

### 🔧 **API Scripts Architecture**

- Individual Python scripts for each operation
- Progressive building with error recovery
- No temp files - works in target directories

### 📋 **Enhanced Output**

- Stub-level 2: Pseudocode implementations
- Priority-ordered implementation tasks
- PRD requirement traceability

## Architecture

```
todo-planner/
├── api/                          # API-like scripts
│   ├── create_bts_project.py     # Create better-t-stack project
│   ├── compile_check.py          # Quality gates (build, lint, typecheck)
│   ├── init_skeleton.py          # Initialize skeleton from PRD + project
│   ├── add_module.py             # Add modules to manifest
│   ├── add_file.py               # Add files with functions
│   ├── render_skeleton.py        # Generate code using Jinja templates
│   └── generate_tasks.py         # Create implementation checklist
└── templates/                    # Jinja templates by tech stack
    ├── nextjs/
    ├── hono/
    └── common/
```

## Usage

### Initiate

Use the `/plan-implementation-skeleton` slash command for full LLM-orchestrated workflow.

### How it works (pipeline)

**Inputs:**

- PRD markdown (self-contained with tech stack and design info)
- Better-t-stack technology choices

**Steps:**

1. **Stack Selection:** LLM extracts requirements from PRD and maps to better-t-stack options
2. **Foundation Creation:** `create_bts_project.py` creates working project with real dependencies
3. **Quality Gate 1:** `compile_check.py` verifies base project compiles, typechecks, and lints
4. **Skeleton Init:** `init_skeleton.py` creates manifest from PRD + detected project structure
5. **Progressive Building:** `add_module.py` and `add_file.py` add business logic structure
6. **Render:** `render_skeleton.py` generates stub code using stack-aware Jinja templates
7. **Quality Gate 2:** `compile_check.py` validates skeleton still compiles
8. **Task Generation:** `generate_tasks.py` creates priority-ordered implementation checklist

**Outputs:**

- Working better-t-stack project
- Skeleton code with stub-level 2 pseudocode
- Implementation task list with PRD traceability
- Project manifest tracking all functions and dependencies

## Supported Tech Stacks

Based on better-t-stack options:

- **Web Frontend**: nextjs, tanstack-router, react-router, svelte, solid
- **Backend**: hono, nextjs, elysia, express, fastify, convex
- **Runtime**: bun, nodejs, cloudflare-workers
- **Database**: sqlite, postgresql, mysql, mongodb
- **ORM**: drizzle, prisma, mongoose
- **Auth**: better-auth

### Command Line (Individual Scripts)

```bash
# Create better-t-stack project
python api/create_bts_project.py --name MyApp --config stack_config.json

# Initialize skeleton
python api/init_skeleton.py --project-dir ./MyApp --prd prd.md --output manifest.json

# Add modules and files
python api/add_module.py --manifest manifest.json --name auth --exports "login,logout"
python api/add_file.py --manifest manifest.json --path "app/api/login/route.ts" --kind api-route

# Render and validate
python api/render_skeleton.py --manifest manifest.json --project-dir ./MyApp
python api/compile_check.py --project-dir ./MyApp
python api/generate_tasks.py --manifest manifest.json
```

## Templates

Templates are organized by tech stack and automatically selected based on:

1. Project's better-t-stack configuration
2. File kind (api-route, page, service, etc.)
3. Fallback to common templates

Templates live under `templates/` and are selected by detected stack:

**Template selection:**

1. Try stack-specific template (e.g., nextjs/api-route.jinja)
2. Try common template (common/api-route.jinja)

**Stub levels:**

- Level 0: Signatures only (will fail compile)
- Level 1: Signatures + TODO + minimal returns
- Level 2: Signatures + pseudocode (default)

## Quality Gates

Each phase includes validation:

- **Build**: Project compiles successfully
- **TypeCheck**: TypeScript types are valid
- **Lint**: Code style checks (may warn on stub implementations)

## Output Structure

```
./
├── prd_MyApp_20250108.md         # Complete PRD
├── MyApp/                        # Project directory
│   ├── [better-t-stack files]   # Base project structure
│   ├── [generated skeleton]     # Business logic stubs
│   ├── skeleton_manifest.json   # Project metadata
│   └── IMPLEMENTATION_TASKS.md  # Priority-ordered checklist
```

## Development

### Adding New Templates

1. Create template directory: `templates/[stack]/`
2. Add Jinja templates: `templates/[stack]/[kind].jinja`
3. Templates automatically detected by `render_skeleton.py`

### Adding New Stacks

1. Update better-t-stack options in prompt
2. Add stack-specific templates
3. Update `init_skeleton.py` stack detection

## Requirements

- Python 3.8+
- Jinja2 (for template rendering)
- Node.js (for better-t-stack)
- Internet connection (for better-t-stack creation)

---

_Part of the AI Assisted Workflows project_
