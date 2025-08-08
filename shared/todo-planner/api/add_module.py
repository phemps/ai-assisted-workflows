#!/usr/bin/env python3
"""
Add a module to the skeleton manifest.
This script adds or updates modules in the progressive skeleton building process.
"""
import argparse
import json
import sys
from typing import Dict, List


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


def add_module(
    manifest: Dict,
    name: str,
    description: str,
    exports: List[str],
    dependencies: List[str],
) -> Dict:
    """Add or update a module in the manifest."""

    # Find existing module or create new one
    existing_module = None
    for i, module in enumerate(manifest.get("modules", [])):
        if module["name"] == name:
            existing_module = i
            break

    new_module = {
        "name": name,
        "description": description,
        "exports": exports,
        "dependencies": dependencies,
    }

    if existing_module is not None:
        # Update existing module
        manifest["modules"][existing_module] = new_module
        action = "updated"
    else:
        # Add new module
        if "modules" not in manifest:
            manifest["modules"] = []
        manifest["modules"].append(new_module)
        action = "added"

    return manifest, action


def validate_dependencies(
    manifest: Dict, module_name: str, dependencies: List[str]
) -> List[str]:
    """Validate that all dependencies exist in the manifest."""
    existing_modules = {module["name"] for module in manifest.get("modules", [])}
    missing_deps = []

    for dep in dependencies:
        if dep != module_name and dep not in existing_modules:
            missing_deps.append(dep)

    return missing_deps


def main():
    parser = argparse.ArgumentParser(description="Add module to skeleton manifest")
    parser.add_argument(
        "--manifest", required=True, help="Path to skeleton manifest JSON"
    )
    parser.add_argument("--name", required=True, help="Module name")
    parser.add_argument("--description", required=True, help="Module description")
    parser.add_argument(
        "--exports", required=True, help="Comma-separated list of module exports"
    )
    parser.add_argument(
        "--dependencies", help="Comma-separated list of module dependencies"
    )
    parser.add_argument(
        "--output", help="Path to write updated manifest (default: update in place)"
    )
    parser.add_argument(
        "--validate-deps", action="store_true", help="Validate dependencies exist"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Parse inputs
    exports = [export.strip() for export in args.exports.split(",") if export.strip()]
    dependencies = []
    if args.dependencies:
        dependencies = [
            dep.strip() for dep in args.dependencies.split(",") if dep.strip()
        ]

    try:
        # Load manifest
        manifest = load_manifest(args.manifest)

        if args.verbose:
            print(
                f"📄 Loaded manifest with {len(manifest.get('modules', []))} existing modules"
            )

        # Validate dependencies if requested
        if args.validate_deps:
            missing_deps = validate_dependencies(manifest, args.name, dependencies)
            if missing_deps:
                print(
                    f"❌ Missing dependencies: {', '.join(missing_deps)}",
                    file=sys.stderr,
                )
                print("Available modules:", file=sys.stderr)
                for module in manifest.get("modules", []):
                    print(f"  - {module['name']}", file=sys.stderr)
                return 1

        # Add/update module
        updated_manifest, action = add_module(
            manifest, args.name, args.description, exports, dependencies
        )

        # Save manifest
        output_path = args.output or args.manifest
        save_manifest(updated_manifest, output_path)

        if args.verbose:
            print(f"✅ Module '{args.name}' {action}")
            print(f"📦 Exports: {', '.join(exports)}")
            if dependencies:
                print(f"🔗 Dependencies: {', '.join(dependencies)}")
            print(f"💾 Saved to: {output_path}")
        else:
            print(f"✅ {action.title()} module: {args.name}")

        # Output summary
        total_modules = len(updated_manifest.get("modules", []))
        if args.verbose:
            print(f"📊 Total modules: {total_modules}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
