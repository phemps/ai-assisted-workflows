#!/usr/bin/env python3
"""
Generate IMPLEMENTATION_TASKS.md file from skeleton manifest.
This creates an actionable checklist for implementing the skeleton functions.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List


def detect_package_manager(project_dir: Path) -> str:
    """Detect which package manager is used in the project."""
    # Check for lock files to determine package manager
    if (project_dir / "bun.lockb").exists() or (project_dir / "bun.lock").exists():
        return "bun"
    elif (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    elif (project_dir / "yarn.lock").exists():
        return "yarn"
    elif (project_dir / "package-lock.json").exists():
        return "npm"
    elif (project_dir / "bunfig.toml").exists():
        return "bun"
    else:
        return "npm"  # Default


def get_package_manager_commands(package_manager: str) -> Dict[str, str]:
    """Get the appropriate commands for the detected package manager."""
    commands = {
        "npm": {
            "build": "npm run build",
            "typecheck": "npm run typecheck",
            "lint": "npm run lint",
            "install": "npm install",
        },
        "pnpm": {
            "build": "pnpm build",
            "typecheck": "pnpm typecheck",
            "lint": "pnpm lint",
            "install": "pnpm install",
        },
        "yarn": {
            "build": "yarn build",
            "typecheck": "yarn typecheck",
            "lint": "yarn lint",
            "install": "yarn install",
        },
        "bun": {
            "build": "bun run build",
            "typecheck": "bun run typecheck",
            "lint": "bun run lint",
            "install": "bun install",
        },
    }
    return commands.get(package_manager, commands["npm"])


def load_manifest(manifest_path: str) -> Dict:
    """Load skeleton manifest from JSON file."""
    try:
        with open(manifest_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Could not load manifest: {e}")


def analyze_dependencies(manifest: Dict) -> Dict[str, List[str]]:
    """Analyze function dependencies to determine implementation order."""
    dependencies = {}

    for file_spec in manifest.get("files", []):
        for func in file_spec.get("functions", []):
            func_id = func["id"]
            func_deps = func.get("dependencies", [])
            dependencies[func_id] = func_deps

    return dependencies


def topological_sort(dependencies: Dict[str, List[str]]) -> List[str]:
    """Sort functions by dependency order using topological sort."""
    # Simple topological sort implementation
    visited = set()
    temp_visited = set()
    result = []

    def visit(func_id: str):
        if func_id in temp_visited:
            # Circular dependency - just add to result
            return
        if func_id in visited:
            return

        temp_visited.add(func_id)

        for dep in dependencies.get(func_id, []):
            if dep in dependencies:  # Only visit if dependency exists
                visit(dep)

        temp_visited.remove(func_id)
        visited.add(func_id)
        result.append(func_id)

    for func_id in dependencies.keys():
        if func_id not in visited:
            visit(func_id)

    return result


def group_by_priority(
    manifest: Dict, ordered_functions: List[str]
) -> Dict[str, List[Dict]]:
    """Group functions by implementation priority."""

    # Create function lookup
    func_lookup = {}
    for file_spec in manifest.get("files", []):
        for func in file_spec.get("functions", []):
            func_lookup[func["id"]] = {
                **func,
                "file_path": file_spec["path"],
                "file_kind": file_spec.get("kind", "module"),
            }

    # Categorize by priority
    priority_groups = {
        "Phase 1 - Core Infrastructure": [],
        "Phase 2 - Business Logic": [],
        "Phase 3 - Features & Endpoints": [],
        "Phase 4 - Utilities & Helpers": [],
    }

    for func_id in ordered_functions:
        if func_id not in func_lookup:
            continue

        func = func_lookup[func_id]
        func_name = func["name"].lower()
        file_kind = func["file_kind"]

        # Determine priority based on function characteristics
        if any(
            keyword in func_name
            for keyword in ["init", "setup", "config", "database", "schema"]
        ):
            priority_groups["Phase 1 - Core Infrastructure"].append(func)
        elif file_kind == "api-route" or "api" in func["file_path"]:
            priority_groups["Phase 3 - Features & Endpoints"].append(func)
        elif any(
            keyword in func_name
            for keyword in ["create", "update", "delete", "get", "find"]
        ):
            priority_groups["Phase 2 - Business Logic"].append(func)
        else:
            priority_groups["Phase 4 - Utilities & Helpers"].append(func)

    return priority_groups


def generate_tasks_markdown(manifest: Dict, project_dir: Path = None) -> str:
    """Generate the complete IMPLEMENTATION_TASKS.md content."""

    project_name = manifest.get("project", {}).get("name", "Project")
    stack_profile = manifest.get("project", {}).get("stack_profile", "unknown")

    # Detect package manager if project directory provided
    if project_dir:
        package_manager = detect_package_manager(project_dir)
        pm_commands = get_package_manager_commands(package_manager)
    else:
        package_manager = "npm"
        pm_commands = get_package_manager_commands("npm")

    # Analyze dependencies and get implementation order
    dependencies = analyze_dependencies(manifest)
    ordered_functions = topological_sort(dependencies)

    # Group by priority
    priority_groups = group_by_priority(manifest, ordered_functions)

    # Count statistics
    total_files = len(manifest.get("files", []))
    total_functions = sum(
        len(f.get("functions", [])) for f in manifest.get("files", [])
    )
    total_modules = len(manifest.get("modules", []))

    # Build markdown content
    md_content = f"""# Implementation Tasks for {project_name}

## Project Overview

- **Stack Profile**: {stack_profile}
- **Total Modules**: {total_modules}
- **Total Files**: {total_files}
- **Total Functions**: {total_functions}

## Implementation Strategy

This project has been scaffolded with better-t-stack providing the foundation. The functions below are organized by implementation priority, with dependencies taken into account.

Each function includes:
- **Location**: File path and function name
- **Purpose**: Description from PRD requirements
- **PRD References**: Related requirement IDs
- **Dependencies**: Other functions this depends on

## Implementation Phases

"""

    # Add each priority group
    for phase_name, functions in priority_groups.items():
        if not functions:
            continue

        md_content += f"### {phase_name}\n\n"

        for func in functions:
            prd_refs = ", ".join(func.get("prd_references", []))
            prd_section = f" [{prd_refs}]" if prd_refs else ""

            dependencies_list = func.get("dependencies", [])
            deps_section = (
                f"\n  - **Dependencies**: {', '.join(dependencies_list)}"
                if dependencies_list
                else ""
            )

            md_content += f"""- [ ] **{func["file_path"]}**:`{func["name"]}()`{prd_section}
  - **Purpose**: {func.get("description", "No description")}
  - **Return Type**: {func.get("signature", {}).get("return_type", "unknown")}{deps_section}

"""

    # Add footer with helpful information
    md_content += f"""## Getting Started

1. **Start with Phase 1** - These functions set up core infrastructure
2. **Implement in order** - Dependencies are listed for each function
3. **Test as you go** - Run `{pm_commands['build']}` and `{pm_commands['typecheck']}` frequently
4. **Update this file** - Check off tasks as you complete them

## Quality Gates

Run these commands to verify your implementation:

```bash
{pm_commands['build']}      # Verify compilation
{pm_commands['typecheck']}  # Check TypeScript types
{pm_commands['lint']}       # Check code style
```

## PRD Reference

See `../prd_{project_name.lower()}_*.md` for complete requirements and context.

---

*Generated by todo-planner-v2 skeleton system*
"""

    return md_content


def main():
    parser = argparse.ArgumentParser(
        description="Generate implementation tasks from skeleton manifest"
    )
    parser.add_argument(
        "--manifest", required=True, help="Path to skeleton manifest JSON"
    )
    parser.add_argument(
        "--output",
        help="Path to write IMPLEMENTATION_TASKS.md (default: same dir as manifest)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        # Load manifest
        manifest = load_manifest(args.manifest)

        if args.verbose:
            files_count = len(manifest.get("files", []))
            functions_count = sum(
                len(f.get("functions", [])) for f in manifest.get("files", [])
            )
            print(f"📄 Processing {files_count} files with {functions_count} functions")

        # Try to detect project directory from manifest path
        manifest_path = Path(args.manifest)
        project_dir = manifest_path.parent

        # Generate tasks markdown
        tasks_content = generate_tasks_markdown(manifest, project_dir)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            manifest_path = Path(args.manifest)
            output_path = manifest_path.parent / "IMPLEMENTATION_TASKS.md"

        # Write tasks file
        with open(output_path, "w") as f:
            f.write(tasks_content)

        if args.verbose:
            print(f"✅ Generated implementation tasks: {output_path}")

            # Show summary
            lines = tasks_content.count("\n- [ ]")
            phases = tasks_content.count("### Phase")
            print(f"📊 Created {lines} tasks across {phases} phases")
        else:
            print(f"✅ Implementation tasks: {output_path}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
