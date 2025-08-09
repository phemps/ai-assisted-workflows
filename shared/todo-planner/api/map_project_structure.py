#!/usr/bin/env python3
"""
Map project structure to understand where files should be placed.
This should be run immediately after better-t-stack project creation.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


def detect_monorepo_structure(project_dir: Path) -> Dict:
    """Detect and map monorepo/project structure."""
    structure_map = {
        "type": "unknown",
        "root": str(project_dir),
        "packages": {},
        "file_placement_rules": {},
        "existing_files": {},
        "planned_files": {},
        "file_registry": [],
    }

    # Check if it's a monorepo
    if (project_dir / "apps").exists() or (project_dir / "packages").exists():
        structure_map["type"] = "monorepo"

        # Map apps directory
        apps_dir = project_dir / "apps"
        if apps_dir.exists():
            for app in apps_dir.iterdir():
                if app.is_dir():
                    app_type = detect_app_type(app)
                    structure_map["packages"][app.name] = {
                        "path": str(app.relative_to(project_dir)),
                        "type": app_type,
                        "src_dir": find_src_dir(app),
                    }

        # Map packages directory
        packages_dir = project_dir / "packages"
        if packages_dir.exists():
            for pkg in packages_dir.iterdir():
                if pkg.is_dir():
                    pkg_type = detect_package_type(pkg)
                    structure_map["packages"][pkg.name] = {
                        "path": str(pkg.relative_to(project_dir)),
                        "type": pkg_type,
                        "src_dir": find_src_dir(pkg),
                    }

    else:
        # Single package project
        structure_map["type"] = "single"
        structure_map["packages"]["main"] = {
            "path": ".",
            "type": detect_app_type(project_dir),
            "src_dir": find_src_dir(project_dir),
        }

    # Define file placement rules based on structure
    structure_map["file_placement_rules"] = generate_placement_rules(structure_map)

    # Inventory all existing files
    structure_map["existing_files"] = inventory_existing_files(project_dir)

    # Create file registry for tracking
    structure_map["file_registry"] = create_file_registry(structure_map)

    # Extract functional purposes from existing files
    structure_map["functional_map"] = extract_functional_purposes(project_dir)

    return structure_map


def detect_app_type(app_dir: Path) -> str:
    """Detect the type of application."""
    if (app_dir / "next.config.js").exists() or (app_dir / "next.config.ts").exists():
        return "nextjs"
    elif (app_dir / "vite.config.js").exists() or (app_dir / "vite.config.ts").exists():
        return "vite"
    elif (app_dir / "remix.config.js").exists():
        return "remix"
    elif (app_dir / "nuxt.config.js").exists() or (app_dir / "nuxt.config.ts").exists():
        return "nuxt"
    elif (app_dir / "package.json").exists():
        # Check package.json for hints
        try:
            with open(app_dir / "package.json") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "next" in deps:
                    return "nextjs"
                elif "react" in deps:
                    return "react"
                elif "vue" in deps:
                    return "vue"
                elif "svelte" in deps:
                    return "svelte"
        except Exception:
            pass
    return "unknown"


def detect_package_type(pkg_dir: Path) -> str:
    """Detect the type of package."""
    if (pkg_dir / "convex").exists():
        return "convex"
    elif (pkg_dir / "prisma").exists():
        return "prisma"
    elif pkg_dir.name == "backend":
        return "backend"
    elif pkg_dir.name == "ui":
        return "ui"
    elif pkg_dir.name == "shared":
        return "shared"
    return "library"


def find_src_dir(package_dir: Path) -> Optional[str]:
    """Find the source directory for a package."""
    # Check common source directory patterns
    for src_pattern in ["src", "lib", "source"]:
        src_dir = package_dir / src_pattern
        if src_dir.exists():
            return str(src_dir.relative_to(package_dir))

    # For Next.js apps, check for app directory
    if (package_dir / "app").exists():
        return "app"

    return None


def inventory_existing_files(project_dir: Path) -> Dict:
    """Inventory all existing source files in the project."""
    inventory = {
        "typescript": [],
        "javascript": [],
        "css": [],
        "json": [],
        "config": [],
        "total_count": 0,
    }

    # File extensions to track
    source_extensions = {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".css",
        ".scss",
        ".sass",
        ".json",
        ".jsonc",
    }

    # Directories to skip
    skip_dirs = {"node_modules", ".next", ".turbo", "dist", "build", ".git"}

    for file_path in project_dir.rglob("*"):
        # Skip if in excluded directory
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue

        if file_path.is_file() and file_path.suffix in source_extensions:
            rel_path = str(file_path.relative_to(project_dir))

            # Categorize file
            if file_path.suffix in {".ts", ".tsx"}:
                inventory["typescript"].append(
                    {
                        "path": rel_path,
                        "size": file_path.stat().st_size,
                        "purpose": determine_file_purpose(file_path),
                    }
                )
            elif file_path.suffix in {".js", ".jsx", ".mjs", ".cjs"}:
                inventory["javascript"].append(
                    {
                        "path": rel_path,
                        "size": file_path.stat().st_size,
                        "purpose": determine_file_purpose(file_path),
                    }
                )
            elif file_path.suffix in {".css", ".scss", ".sass"}:
                inventory["css"].append({"path": rel_path})
            elif file_path.suffix in {".json", ".jsonc"}:
                if file_path.name in {"package.json", "tsconfig.json", "biome.json"}:
                    inventory["config"].append(
                        {"path": rel_path, "type": file_path.name}
                    )
                else:
                    inventory["json"].append({"path": rel_path})

            inventory["total_count"] += 1

    return inventory


def determine_file_purpose(file_path: Path) -> str:
    """Determine the purpose of a file based on its path and name."""
    path_str = str(file_path).lower()
    name = file_path.stem.lower()

    if "test" in path_str or "spec" in name:
        return "test"
    elif "route" in path_str or "/api/" in path_str:
        return "api-route"
    elif "page" in name or "/app/" in path_str:
        return "page"
    elif "component" in path_str or "/components/" in path_str:
        return "component"
    elif "hook" in path_str or name.startswith("use"):
        return "hook"
    elif "util" in path_str or "helper" in path_str or "/lib/" in path_str:
        return "utility"
    elif "schema" in name:
        return "schema"
    elif "config" in name or name in {"next.config", "vite.config", "webpack.config"}:
        return "config"
    elif "/convex/" in path_str:
        # Determine the specific Convex function type based on file name
        if "schema" in name:
            return "schema"
        elif "auth" in name:
            return "auth"
        elif "action" in name:
            return "action"
        elif any(
            keyword in name for keyword in ["mutation", "update", "create", "delete"]
        ):
            return "mutation"
        elif any(keyword in name for keyword in ["query", "get", "list", "find"]):
            return "query"
        else:
            return "function"  # Generic Convex function
    elif "layout" in name:
        return "layout"
    elif "provider" in name:
        return "provider"
    else:
        return "unknown"


def create_file_registry(structure_map: Dict) -> List[Dict]:
    """Create a registry of all files with their metadata."""
    registry = []

    for category, files in structure_map["existing_files"].items():
        if category == "total_count":
            continue

        for file_info in files:
            if isinstance(file_info, dict):
                registry.append(
                    {
                        "path": file_info["path"],
                        "category": category,
                        "purpose": file_info.get("purpose", "unknown"),
                        "status": "existing",
                        "source": "better-t-stack",
                    }
                )

    return registry


def generate_placement_rules(structure_map: Dict) -> Dict:
    """Generate rules for where different file types should be placed."""
    rules = {}

    if structure_map["type"] == "monorepo":
        # Find the main web app
        web_app = None
        backend_pkg = None

        for name, info in structure_map["packages"].items():
            if info["type"] in ["nextjs", "react", "vue", "svelte", "vite"]:
                web_app = info
            elif info["type"] in ["convex", "backend"]:
                backend_pkg = info

        if web_app:
            web_path = web_app["path"]
            src_dir = web_app["src_dir"] or ""

            rules["page"] = (
                f"{web_path}/{src_dir}/app" if src_dir else f"{web_path}/app"
            )
            rules["component"] = (
                f"{web_path}/{src_dir}/components"
                if src_dir
                else f"{web_path}/components"
            )
            rules["api-route"] = (
                f"{web_path}/{src_dir}/app/api" if src_dir else f"{web_path}/app/api"
            )
            rules["lib"] = f"{web_path}/{src_dir}/lib" if src_dir else f"{web_path}/lib"
            rules["hook"] = (
                f"{web_path}/{src_dir}/hooks" if src_dir else f"{web_path}/hooks"
            )

        if backend_pkg:
            backend_path = backend_pkg["path"]
            if backend_pkg["type"] == "convex":
                # Map all Convex-related kinds to the convex directory
                for kind in ["function", "query", "mutation", "action", "auth"]:
                    rules[kind] = f"{backend_path}/convex"
                rules["schema"] = f"{backend_path}/convex"
            else:
                rules["backend-route"] = f"{backend_path}/src/routes"
                rules["service"] = f"{backend_path}/src/services"

    else:
        # Single package rules
        src_dir = structure_map["packages"]["main"]["src_dir"] or ""

        rules["page"] = f"{src_dir}/app" if src_dir else "app"
        rules["component"] = f"{src_dir}/components" if src_dir else "components"
        rules["api-route"] = f"{src_dir}/app/api" if src_dir else "app/api"
        rules["lib"] = f"{src_dir}/lib" if src_dir else "lib"
        # Map all Convex-related kinds to the convex directory
        for kind in ["function", "query", "mutation", "action", "auth"]:
            rules[kind] = "convex"
        rules["schema"] = "convex"

    return rules


def plan_files_from_requirements(structure_map: Dict, requirements: List[str]) -> Dict:
    """Plan what files should be created based on requirements."""
    planned_files = {
        "auth": [],
        "api": [],
        "pages": [],
        "components": [],
        "database": [],
        "services": [],
        "workers": [],
        "tests": [],
    }

    # Map common requirement patterns to files
    requirement_patterns = {
        "authentication": ["auth/provider", "auth/hooks", "api/auth/route"],
        "database": ["schema", "migrations", "seed"],
        "api": ["api/[endpoint]/route"],
        "scanning": ["api/scan/route", "workers/scanner"],
        "reporting": ["pages/report", "components/report-viewer"],
        "scheduling": ["api/schedule/route", "workers/scheduler"],
        "quotas": ["api/quotas/route", "lib/quota-manager"],
        "analytics": ["lib/analytics", "providers/analytics"],
        "storage": ["lib/storage", "api/storage/route"],
        "gamification": ["components/badges", "api/achievements/route"],
    }

    # Check each requirement for patterns
    for req in requirements:
        req_lower = req.lower()
        for pattern, files in requirement_patterns.items():
            if pattern in req_lower:
                for file_pattern in files:
                    if "/" in file_pattern:
                        category = file_pattern.split("/")[0]
                        if category in planned_files:
                            planned_files[category].append(
                                {
                                    "pattern": file_pattern,
                                    "requirement": req,
                                    "status": "planned",
                                }
                            )

    return planned_files


def extract_functional_purposes(project_dir: Path) -> Dict[str, List[Dict]]:
    """Extract functional purposes from existing TypeScript/JavaScript files."""
    functional_map = {}

    # Skip directories
    skip_dirs = {"node_modules", ".next", ".turbo", "dist", "build", ".git"}

    for file_path in project_dir.rglob("*.ts"):
        # Skip if in excluded directory
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue

        try:
            content = file_path.read_text()
            functions = extract_functions_from_content(content, file_path)

            for func_info in functions:
                purpose = infer_function_purpose_from_code(
                    func_info["name"], func_info.get("description", "")
                )

                if purpose not in functional_map:
                    functional_map[purpose] = []

                functional_map[purpose].append(
                    {
                        "name": func_info["name"],
                        "file": str(file_path.relative_to(project_dir)),
                        "type": func_info.get("type", "unknown"),
                        "export": func_info.get("export", False),
                    }
                )

        except Exception:
            # Skip files that can't be read or parsed
            continue

    return functional_map


def extract_functions_from_content(content: str, file_path: Path) -> List[Dict]:
    """Extract function information from TypeScript/JavaScript content."""
    functions = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()

        # Match various function patterns
        func_patterns = [
            # export const funcName =
            r"export\s+const\s+(\w+)\s*=",
            # export function funcName
            r"export\s+function\s+(\w+)\s*\(",
            # export async function funcName
            r"export\s+async\s+function\s+(\w+)\s*\(",
            # function funcName
            r"function\s+(\w+)\s*\(",
            # async function funcName
            r"async\s+function\s+(\w+)\s*\(",
            # funcName: mutation({
            r"(\w+):\s*mutation\s*\(",
            # funcName: query({
            r"(\w+):\s*query\s*\(",
        ]

        import re

        for pattern in func_patterns:
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)

                # Look for description in comments above
                description = ""
                for j in range(max(0, i - 3), i):
                    comment_line = lines[j].strip()
                    if comment_line.startswith("//") or comment_line.startswith("*"):
                        description += comment_line.lstrip("/* ") + " "

                functions.append(
                    {
                        "name": func_name,
                        "description": description.strip(),
                        "type": "mutation"
                        if "mutation" in line
                        else "query"
                        if "query" in line
                        else "function",
                        "export": "export" in line,
                    }
                )
                break

    return functions


def infer_function_purpose_from_code(name: str, description: str) -> str:
    """Infer the semantic purpose of a function from its name and description."""
    combined = f"{name} {description}".lower()

    # Authentication purposes
    if any(word in combined for word in ["signin", "login", "authenticate", "auth"]):
        return "user_authentication"
    elif any(word in combined for word in ["signup", "register", "create_user"]):
        return "user_registration"
    elif any(word in combined for word in ["signout", "logout", "sign_out"]):
        return "user_logout"
    elif any(word in combined for word in ["verify", "confirm", "validate_email"]):
        return "email_verification"

    # Scan purposes
    elif (
        any(word in combined for word in ["submit", "create", "start"])
        and "scan" in combined
    ):
        return "scan_submission"
    elif any(word in combined for word in ["get", "fetch", "retrieve"]) and any(
        w in combined for w in ["scan", "result", "report"]
    ):
        return "scan_retrieval"
    elif (
        any(word in combined for word in ["check", "validate"]) and "quota" in combined
    ):
        return "quota_checking"
    elif "status" in combined and "scan" in combined:
        return "scan_status_check"

    # Report purposes
    elif (
        any(word in combined for word in ["generate", "create", "build"])
        and "report" in combined
    ):
        return "report_generation"
    elif any(word in combined for word in ["get", "fetch"]) and "report" in combined:
        return "report_retrieval"

    return f"function_{name.lower()}"


def check_for_duplicates(structure_map: Dict) -> List[Dict]:
    """Check for potential duplicate files or overlapping functionality."""
    duplicates = []

    # Get all existing file purposes
    existing_purposes = {}
    for file_info in structure_map["file_registry"]:
        if file_info["status"] == "existing":
            purpose = file_info["purpose"]
            if purpose not in existing_purposes:
                existing_purposes[purpose] = []
            existing_purposes[purpose].append(file_info["path"])

    # Check planned files against existing
    for category, planned_list in structure_map.get("planned_files", {}).items():
        for planned in planned_list:
            pattern = planned.get("pattern", "")
            # Check if similar file already exists
            for purpose, paths in existing_purposes.items():
                if purpose in pattern or pattern in purpose:
                    duplicates.append(
                        {
                            "planned": pattern,
                            "existing": paths,
                            "type": "potential_duplicate",
                        }
                    )

    return duplicates


def main():
    parser = argparse.ArgumentParser(
        description="Map project structure for file placement"
    )
    parser.add_argument(
        "--project-dir", required=True, help="Path to project directory"
    )
    parser.add_argument("--output", help="Output file for structure map (JSON)")
    parser.add_argument(
        "--requirements", nargs="+", help="List of requirements to plan files for"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()
    project_dir = Path(args.project_dir)

    if not project_dir.exists():
        print(f"❌ Project directory not found: {project_dir}", file=sys.stderr)
        return 1

    # Map the structure
    structure_map = detect_monorepo_structure(project_dir)

    # Add planned files if requirements provided
    if args.requirements:
        structure_map["planned_files"] = plan_files_from_requirements(
            structure_map, args.requirements
        )

    # Check for duplicates
    duplicates = check_for_duplicates(structure_map)
    if duplicates:
        structure_map["potential_duplicates"] = duplicates

    # Output the map
    if args.output:
        with open(args.output, "w") as f:
            json.dump(structure_map, f, indent=2)
        print(f"✅ Structure map saved to: {args.output}")

    if args.verbose or not args.output:
        print(json.dumps(structure_map, indent=2))

    # Print summary
    print("\n📊 Project Structure Summary:")
    print(f"   Type: {structure_map['type']}")
    print(f"   Packages found: {len(structure_map['packages'])}")
    print(f"   Existing files: {structure_map['existing_files']['total_count']}")

    if structure_map["file_placement_rules"]:
        print("\n📍 File Placement Rules:")
        for file_type, path in structure_map["file_placement_rules"].items():
            print(f"   {file_type}: {path}")

    if structure_map.get("planned_files"):
        print("\n📝 Planned Files:")
        for category, files in structure_map["planned_files"].items():
            if files:
                print(f"   {category}: {len(files)} files")

    if duplicates:
        print(f"\n⚠️  Potential Duplicates Found: {len(duplicates)}")
        for dup in duplicates[:3]:  # Show first 3
            print(f"   - {dup['planned']} may overlap with {dup['existing'][0]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
