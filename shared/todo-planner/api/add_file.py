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
        if "nextjs" in stack_profile:
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
