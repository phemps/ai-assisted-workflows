#!/usr/bin/env python3
"""
Initialize skeleton manifest from PRD and existing better-t-stack project.
This creates the foundation for progressive skeleton building.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from models import (
        ProjectSettings,
        TaskPlan,
        Module,
    )
except ImportError as e:
    print(f"❌ Import error: {e}", file=sys.stderr)
    print("Ensure you're running from the correct directory", file=sys.stderr)
    sys.exit(1)


def detect_project_stack(project_dir: Path) -> Dict[str, Optional[str]]:
    """Detect tech stack from better-t-stack project structure and config files."""
    stack_info = {
        "web_frontend": None,
        "backend": None,
        "database": None,
        "orm": None,
        "auth": None,
        "runtime": None,
        "package_manager": None,
    }

    # First check if we have a structure map
    structure_map_path = project_dir / "project_structure_map.json"
    if structure_map_path.exists():
        with open(structure_map_path) as f:
            structure_map = json.load(f)
            # Use the structure map to guide detection
            for pkg_name, pkg_info in structure_map.get("packages", {}).items():
                if pkg_info["type"] == "nextjs":
                    stack_info["web_frontend"] = "next"
                elif pkg_info["type"] == "convex":
                    stack_info["backend"] = "convex"

    # Check monorepo packages
    for possible_path in [
        project_dir / "apps" / "web" / "package.json",
        project_dir / "packages" / "backend" / "package.json",
        project_dir / "package.json",
    ]:
        if possible_path.exists():
            try:
                with open(possible_path) as f:
                    package_data = json.load(f)

                deps = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }
            except Exception:
                continue

            # Detect web frontend
            if "next" in deps:
                stack_info["web_frontend"] = "next"
            elif "@tanstack/react-router" in deps:
                stack_info["web_frontend"] = "tanstack-router"
            elif "react-router-dom" in deps:
                stack_info["web_frontend"] = "react-router"
            elif "svelte" in deps:
                stack_info["web_frontend"] = "svelte"
            elif "@solidjs/router" in deps:
                stack_info["web_frontend"] = "solid"

            # Detect backend
            if "hono" in deps:
                stack_info["backend"] = "hono"
            elif "elysia" in deps:
                stack_info["backend"] = "elysia"
            elif "express" in deps:
                stack_info["backend"] = "express"
            elif "fastify" in deps:
                stack_info["backend"] = "fastify"

            # Detect ORM
            if "drizzle-orm" in deps:
                stack_info["orm"] = "drizzle"
            elif "prisma" in deps:
                stack_info["orm"] = "prisma"
            elif "mongoose" in deps:
                stack_info["orm"] = "mongoose"

            # Detect auth
            if "better-auth" in deps:
                stack_info["auth"] = "better-auth"

            # Detect runtime from scripts or lock files
            if "bun" in package_data.get("scripts", {}).get("dev", ""):
                stack_info["runtime"] = "bun"
            elif (project_dir / "bun.lockb").exists():
                stack_info["runtime"] = "bun"
            else:
                stack_info["runtime"] = "nodejs"

    # Detect package manager
    if (project_dir / "bun.lockb").exists():
        stack_info["package_manager"] = "bun"
    elif (project_dir / "pnpm-lock.yaml").exists():
        stack_info["package_manager"] = "pnpm"
    elif (project_dir / "yarn.lock").exists():
        stack_info["package_manager"] = "yarn"
    else:
        stack_info["package_manager"] = "npm"

    return stack_info


def create_initial_modules(features: List[Dict], stack_info: Dict) -> List[Module]:
    """Create initial module structure based on features and stack."""
    modules = []

    # Core modules based on stack
    if stack_info.get("auth"):
        modules.append(
            Module(
                name="auth",
                purpose="Authentication and authorization",
                depends_on=[],
            )
        )

    if stack_info.get("orm"):
        modules.append(
            Module(
                name="database",
                purpose="Database layer and schema",
                depends_on=[],
            )
        )

    # Feature-based modules (simplified for now)
    feature_modules = set()
    for feature in features:
        # Extract potential module names from feature descriptions
        # This is a simple heuristic - could be enhanced with better NLP
        words = feature["title"].lower().split()
        if "user" in words:
            feature_modules.add("user")
        elif "api" in words:
            feature_modules.add("api")
        elif "admin" in words:
            feature_modules.add("admin")

    # Add feature modules
    for module_name in feature_modules:
        modules.append(
            Module(
                name=module_name,
                purpose=f"{module_name.title()} related functionality",
                depends_on=["database"] if stack_info.get("orm") else [],
            )
        )

    return modules


def init_skeleton(
    project_dir: Path, features: List[Dict], modules: List[Dict] = None
) -> TaskPlan:
    """Initialize skeleton manifest from project and LLM-parsed features."""

    # Detect project stack
    stack_info = detect_project_stack(project_dir)

    # Use provided modules or create from features
    if modules:
        initial_modules = [
            Module(
                name=m["name"], purpose=m["purpose"], depends_on=m.get("depends_on", [])
            )
            for m in modules
        ]
    else:
        initial_modules = create_initial_modules(features, stack_info)

    # Create project settings
    project_name = project_dir.name

    project = ProjectSettings(
        name=project_name,
        language="typescript",  # Default assumption for better-t-stack
        package_manager=stack_info.get("package_manager"),
        web_frontend=stack_info.get("web_frontend"),
        backend=stack_info.get("backend"),
        orm=stack_info.get("orm"),
        runtime=stack_info.get("runtime"),
        auth=stack_info.get("auth"),
        # Legacy field for backwards compatibility
        stack_profile=f"{stack_info.get('web_frontend', 'unknown')}-{stack_info.get('backend', '')}"
        if stack_info.get("backend")
        else stack_info.get("web_frontend", "unknown"),
    )

    # Create initial task plan
    task_plan = TaskPlan(
        project=project,
        modules=initial_modules,
        files=[],  # Will be added progressively
        traceability={feature["id"]: [] for feature in features},
    )

    return task_plan


def main():
    parser = argparse.ArgumentParser(description="Initialize skeleton manifest")
    parser.add_argument(
        "--project-dir", required=True, help="Path to better-t-stack project directory"
    )
    parser.add_argument(
        "--features", required=True, help="JSON string with features array"
    )
    parser.add_argument("--modules", help="JSON string with modules array (optional)")
    parser.add_argument(
        "--output", required=True, help="Path to write skeleton manifest JSON"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    project_dir = Path(args.project_dir)

    try:
        features = json.loads(args.features)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid features JSON: {e}", file=sys.stderr)
        return 1

    modules = None
    if args.modules:
        try:
            modules = json.loads(args.modules)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid modules JSON: {e}", file=sys.stderr)
            return 1

    # Validate inputs
    if not project_dir.exists():
        print(f"❌ Project directory does not exist: {project_dir}", file=sys.stderr)
        return 1

    if not features:
        print("❌ Features array cannot be empty", file=sys.stderr)
        return 1

    if not (project_dir / "package.json").exists():
        print("❌ No package.json found in project directory", file=sys.stderr)
        return 1

    try:
        # Initialize skeleton
        if args.verbose:
            print(f"🏗️  Initializing skeleton for project: {project_dir.name}")
            print(f"📊 Processing {len(features)} features")

        task_plan = init_skeleton(project_dir, features, modules)

        # Convert to dict for JSON serialization
        output_data = {
            "project": {
                "name": task_plan.project.name,
                "language": task_plan.project.language,
                "package_manager": task_plan.project.package_manager,
                "web_frontend": task_plan.project.web_frontend,
                "backend": task_plan.project.backend,
                "orm": task_plan.project.orm,
                "runtime": task_plan.project.runtime,
                "auth": task_plan.project.auth,
                # Legacy field for compatibility
                "stack_profile": task_plan.project.stack_profile,
            },
            "modules": [
                {
                    "name": module.name,
                    "purpose": module.purpose,
                    "depends_on": module.depends_on,
                }
                for module in task_plan.modules
            ],
            "files": [],
            "traceability": task_plan.traceability,
            "metadata": {
                "project_directory": str(project_dir),
                "version": "1.0",
                "features_count": len(features),
            },
        }

        # Write output
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        if args.verbose:
            print(f"✅ Skeleton manifest written to: {args.output}")
            print(f"📊 Initialized with {len(task_plan.modules)} modules")
            print(f"🎯 Tracking {len(task_plan.traceability)} requirements")
        else:
            print(f"✅ Skeleton initialized: {args.output}")

        return 0

    except Exception as e:
        print(f"❌ Error initializing skeleton: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
