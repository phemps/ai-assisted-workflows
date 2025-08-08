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
    from normalize import normalize_inputs
    from models import (
        ProjectSettings,
        TaskPlan,
        PlannedModule,
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

    package_json_path = project_dir / "package.json"
    if package_json_path.exists():
        try:
            with open(package_json_path) as f:
                package_data = json.load(f)

            deps = {
                **package_data.get("dependencies", {}),
                **package_data.get("devDependencies", {}),
            }

            # Detect web frontend
            if "next" in deps:
                stack_info["web_frontend"] = "nextjs"
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

        except Exception as e:
            print(f"⚠️  Warning: Could not parse package.json: {e}")

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


def extract_features_from_prd(prd_text: str) -> List[Dict]:
    """Extract features from PRD using existing normalize logic."""
    context = normalize_inputs(prd_text, None)

    features = []
    for req_id in context.get("requirements_order", []):
        req_title = context.get("requirements", {}).get(req_id, "")
        features.append(
            {
                "id": req_id,
                "title": req_title,
                "description": req_title,
                "priority": "must_have",  # Default, could be enhanced
            }
        )

    return features


def create_initial_modules(
    features: List[Dict], stack_info: Dict
) -> List[PlannedModule]:
    """Create initial module structure based on features and stack."""
    modules = []

    # Core modules based on stack
    if stack_info.get("auth"):
        modules.append(
            PlannedModule(
                name="auth",
                description="Authentication and authorization",
                exports=["AuthConfig", "authMiddleware", "getUser"],
                dependencies=[],
            )
        )

    if stack_info.get("orm"):
        modules.append(
            PlannedModule(
                name="database",
                description="Database layer and schema",
                exports=["db", "schema"],
                dependencies=[],
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
            PlannedModule(
                name=module_name,
                description=f"{module_name.title()} related functionality",
                exports=[
                    f"{module_name}Service",
                    f"create{module_name.title()}",
                    f"get{module_name.title()}",
                ],
                dependencies=["database"] if stack_info.get("orm") else [],
            )
        )

    return modules


def init_skeleton(project_dir: Path, prd_path: Path) -> TaskPlan:
    """Initialize skeleton manifest from project and PRD."""

    # Read PRD
    try:
        with open(prd_path) as f:
            prd_text = f.read()
    except Exception as e:
        raise Exception(f"Could not read PRD file: {e}")

    # Detect project stack
    stack_info = detect_project_stack(project_dir)

    # Extract features from PRD
    features = extract_features_from_prd(prd_text)

    # Create project settings
    project_name = project_dir.name
    stack_profile = stack_info.get("web_frontend", "unknown")
    if stack_info.get("backend"):
        stack_profile += f"-{stack_info['backend']}"

    project = ProjectSettings(
        name=project_name,
        description=f"Project generated from {prd_path.name}",
        stack_profile=stack_profile,
        profiles=[stack_profile],
    )

    # Create initial modules
    modules = create_initial_modules(features, stack_info)

    # Create initial task plan
    task_plan = TaskPlan(
        project=project,
        modules=modules,
        files=[],  # Will be added progressively
        traceability={feature["id"]: [] for feature in features},
    )

    return task_plan


def main():
    parser = argparse.ArgumentParser(description="Initialize skeleton manifest")
    parser.add_argument(
        "--project-dir", required=True, help="Path to better-t-stack project directory"
    )
    parser.add_argument("--prd", required=True, help="Path to PRD file")
    parser.add_argument(
        "--output", required=True, help="Path to write skeleton manifest JSON"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    prd_path = Path(args.prd)

    # Validate inputs
    if not project_dir.exists():
        print(f"❌ Project directory does not exist: {project_dir}", file=sys.stderr)
        return 1

    if not prd_path.exists():
        print(f"❌ PRD file does not exist: {prd_path}", file=sys.stderr)
        return 1

    if not (project_dir / "package.json").exists():
        print("❌ No package.json found in project directory", file=sys.stderr)
        return 1

    try:
        # Initialize skeleton
        if args.verbose:
            print(f"🏗️  Initializing skeleton for project: {project_dir.name}")
            print(f"📄 Using PRD: {prd_path}")

        task_plan = init_skeleton(project_dir, prd_path)

        # Convert to dict for JSON serialization
        output_data = {
            "project": {
                "name": task_plan.project.name,
                "description": task_plan.project.description,
                "stack_profile": task_plan.project.stack_profile,
                "profiles": task_plan.project.profiles,
            },
            "modules": [
                {
                    "name": module.name,
                    "description": module.description,
                    "exports": module.exports,
                    "dependencies": module.dependencies,
                }
                for module in task_plan.modules
            ],
            "files": [],
            "traceability": task_plan.traceability,
            "metadata": {
                "initialized_from": str(prd_path),
                "project_directory": str(project_dir),
                "version": "1.0",
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
