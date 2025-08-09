#!/usr/bin/env python3
"""
Add a file with function stubs to the skeleton manifest.
This script adds files and their function specifications to the manifest.
"""
import argparse
import json
import sys
from typing import Dict, List, Optional


def load_manifest(manifest_path: str) -> Dict:
    """Load skeleton manifest from JSON file."""
    try:
        with open(manifest_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Could not load manifest: {e}")


def save_manifest(manifest: Dict, manifest_path: str) -> None:
    """Save skeleton manifest to JSON file."""
    try:
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
    except Exception as e:
        raise Exception(f"Could not save manifest: {e}")


def parse_function_spec(func_spec: Dict) -> Dict:
    """Parse and validate a function specification."""
    required_fields = ["name", "description", "return_type"]

    for field in required_fields:
        if field not in func_spec:
            raise ValueError(f"Function specification missing required field: {field}")

    return {
        "id": f"{func_spec['name']}_{''.join(func_spec.get('params', [])[:2])}",  # Simple ID generation
        "name": func_spec["name"],
        "description": func_spec["description"],
        "signature": {
            "params": func_spec.get("params", []),
            "return_type": func_spec["return_type"],
            "async": func_spec.get("async", False),
        },
        "prd_references": func_spec.get("prd_references", []),
        "dependencies": func_spec.get("dependencies", []),
        "options": func_spec.get("options", {}),
    }


def determine_file_kind(file_path: str, stack_profile: str) -> str:
    """Determine file kind based on path and stack profile."""
    path_lower = file_path.lower()

    # API routes
    if "api/" in path_lower or "route" in path_lower:
        return "api-route"

    # Pages/components (frontend)
    if "page" in path_lower or "component" in path_lower:
        if "next" in stack_profile:
            return "page"
        else:
            return "component"

    # Services
    if "service" in path_lower:
        return "service"

    # Middleware
    if "middleware" in path_lower:
        return "middleware"

    # Database/schema
    if "schema" in path_lower or "db" in path_lower or "database" in path_lower:
        return "schema"

    # Auth
    if "auth" in path_lower:
        return "auth"

    # Utils
    if "util" in path_lower or "helper" in path_lower:
        return "utils"

    # Default
    return "module"


def infer_function_purpose(name: str, description: str) -> str:
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

    # Storage purposes
    elif any(word in combined for word in ["upload", "store", "save"]) and any(
        w in combined for w in ["file", "artifact", "asset"]
    ):
        return "file_storage"
    elif any(word in combined for word in ["delete", "remove"]) and any(
        w in combined for w in ["file", "artifact"]
    ):
        return "file_deletion"

    # Scheduling purposes
    elif any(word in combined for word in ["schedule", "queue"]) and "scan" in combined:
        return "scan_scheduling"

    # Generic CRUD operations
    elif any(word in combined for word in ["create", "insert", "add"]):
        return "data_creation"
    elif any(word in combined for word in ["update", "modify", "edit"]):
        return "data_update"
    elif any(word in combined for word in ["delete", "remove", "destroy"]):
        return "data_deletion"
    elif any(word in combined for word in ["get", "fetch", "retrieve", "find"]):
        return "data_retrieval"
    elif any(word in combined for word in ["list", "all", "many"]):
        return "data_listing"

    return f"unknown_{name.lower()}"


def get_existing_functions_by_purpose(manifest: Dict, project_dir) -> Dict[str, Dict]:
    """Get all existing functions grouped by their inferred purpose."""
    purposes = {}

    # Check manifest files
    for file_info in manifest.get("files", []):
        for func in file_info.get("functions", []):
            purpose = infer_function_purpose(
                func.get("name", ""), func.get("description", "")
            )
            if purpose not in purposes:
                purposes[purpose] = {
                    "name": func.get("name"),
                    "file": file_info.get("path"),
                    "description": func.get("description", ""),
                }

    # Also scan existing files if project structure map exists
    map_path = project_dir / "complete_project_map.json"
    if map_path.exists():
        # Add functions from existing files (would need to parse actual files for this)
        pass
        # For now, just use what's in the manifest

    return purposes


def get_correct_file_path(manifest: Dict, file_path: str, file_kind: str) -> str:
    """Get the correct file path based on project structure map."""
    from pathlib import Path

    project_dir = Path(manifest.get("metadata", {}).get("project_directory", "."))
    structure_map_path = project_dir / "project_structure_map.json"

    if structure_map_path.exists():
        with open(structure_map_path) as f:
            structure_map = json.load(f)

        placement_rules = structure_map.get("file_placement_rules", {})

        # Determine the base path from the file kind
        if file_kind in placement_rules:
            base_path = placement_rules[file_kind]
            # Extract just the filename from the provided path
            file_name = Path(file_path).name
            # For routes, preserve subdirectory structure
            if file_kind == "api-route" and "/" in file_path:
                # Keep subdirectory structure for API routes
                parts = file_path.split("/")
                if "api" in parts:
                    idx = parts.index("api")
                    subpath = "/".join(parts[idx + 1 :])
                    return f"{base_path}/{subpath}"
            elif file_kind == "page" and "[" in file_path:
                # Keep dynamic route structure for pages
                parts = file_path.split("/")
                if len(parts) > 1:
                    return f"{base_path}/{'/'.join(parts[-2:])}"
            return f"{base_path}/{file_name}"

    return file_path


def add_file(
    manifest: Dict,
    file_path: str,
    functions: List[Dict],
    module_name: Optional[str] = None,
    file_kind: Optional[str] = None,
    options: Dict = None,
) -> Dict:
    """Add or update a file in the manifest."""

    # Determine file kind if not provided
    if file_kind is None:
        stack_profile = manifest.get("project", {}).get("stack_profile", "")
        file_kind = determine_file_kind(file_path, stack_profile)

    # Get the correct file path based on structure map
    corrected_path = get_correct_file_path(manifest, file_path, file_kind)
    if corrected_path != file_path:
        print(f"📍 Corrected path: {file_path} → {corrected_path}")
        file_path = corrected_path

    # Check for functional duplicates in existing functions
    from pathlib import Path

    project_dir = Path(manifest.get("metadata", {}).get("project_directory", "."))
    existing_functions = get_existing_functions_by_purpose(manifest, project_dir)
    for func_spec in functions:
        func_purpose = infer_function_purpose(
            func_spec.get("name", ""), func_spec.get("description", "")
        )
        if func_purpose in existing_functions:
            existing = existing_functions[func_purpose]
            print(
                f"⚠️  Function '{func_spec['name']}' may duplicate existing function '{existing['name']}' in {existing['file']}"
            )
            print(f"    Both handle: {func_purpose}")

    # Parse function specifications
    parsed_functions = []
    for func_spec in functions:
        try:
            parsed_func = parse_function_spec(func_spec)
            parsed_functions.append(parsed_func)
        except Exception as e:
            raise Exception(
                f"Invalid function specification for {func_spec.get('name', 'unknown')}: {e}"
            )

    # Find existing file or create new one
    existing_file = None
    for i, file_info in enumerate(manifest.get("files", [])):
        if file_info["path"] == file_path:
            existing_file = i
            break

    new_file = {
        "path": file_path,
        "kind": file_kind,
        "module": module_name,
        "functions": parsed_functions,
        "options": options or {},
    }

    if existing_file is not None:
        # Update existing file
        manifest["files"][existing_file] = new_file
        action = "updated"
    else:
        # Add new file
        if "files" not in manifest:
            manifest["files"] = []
        manifest["files"].append(new_file)
        action = "added"

    # Update traceability mapping
    if "traceability" not in manifest:
        manifest["traceability"] = {}

    for func in parsed_functions:
        for prd_ref in func.get("prd_references", []):
            if prd_ref not in manifest["traceability"]:
                manifest["traceability"][prd_ref] = []
            if func["id"] not in manifest["traceability"][prd_ref]:
                manifest["traceability"][prd_ref].append(func["id"])

    return manifest, action, len(parsed_functions)


def main():
    parser = argparse.ArgumentParser(
        description="Add file with functions to skeleton manifest"
    )
    parser.add_argument(
        "--manifest", required=True, help="Path to skeleton manifest JSON"
    )
    parser.add_argument(
        "--path", required=True, help="File path relative to project root"
    )
    parser.add_argument(
        "--functions", required=True, help="JSON string with function specifications"
    )
    parser.add_argument("--module", help="Module this file belongs to")
    parser.add_argument("--kind", help="File kind (api-route, page, service, etc.)")
    parser.add_argument("--options", help="JSON string with file options")
    parser.add_argument(
        "--output", help="Path to write updated manifest (default: update in place)"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        # Parse function specifications
        try:
            functions = json.loads(args.functions)
            if not isinstance(functions, list):
                functions = [functions]  # Single function
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in functions parameter: {e}", file=sys.stderr)
            return 1

        # Parse options if provided
        options = {}
        if args.options:
            try:
                options = json.loads(args.options)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in options parameter: {e}", file=sys.stderr)
                return 1

        # Load manifest
        manifest = load_manifest(args.manifest)

        if args.verbose:
            print(
                f"📄 Loaded manifest with {len(manifest.get('files', []))} existing files"
            )

        # Add/update file
        updated_manifest, action, func_count = add_file(
            manifest, args.path, functions, args.module, args.kind, options
        )

        # Save manifest
        output_path = args.output or args.manifest
        save_manifest(updated_manifest, output_path)

        if args.verbose:
            print(f"✅ File '{args.path}' {action}")
            print(f"🔧 Functions: {func_count}")
            if args.kind:
                print(f"📁 Kind: {args.kind}")
            if args.module:
                print(f"📦 Module: {args.module}")
            if options:
                print(f"⚙️  Options: {options}")
            print(f"💾 Saved to: {output_path}")
        else:
            print(f"✅ {action.title()} file: {args.path} ({func_count} functions)")

        # Output summary
        total_files = len(updated_manifest.get("files", []))
        total_functions = sum(
            len(f.get("functions", [])) for f in updated_manifest.get("files", [])
        )
        if args.verbose:
            print(f"📊 Total files: {total_files}")
            print(f"🔧 Total functions: {total_functions}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
