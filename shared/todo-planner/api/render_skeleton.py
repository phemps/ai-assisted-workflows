#!/usr/bin/env python3
"""
Render skeleton code files from manifest using Jinja templates.
This script generates the actual stub code files based on the skeleton manifest.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("❌ Jinja2 not installed. Run: pip install jinja2", file=sys.stderr)
    sys.exit(1)


def load_manifest(manifest_path: str) -> Dict:
    """Load skeleton manifest from JSON file."""
    try:
        with open(manifest_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Could not load manifest: {e}")


def get_template_path(
    templates_dir: Path, manifest: Dict, file_path: str, file_kind: str
) -> Optional[Path]:
    """Find the appropriate template for a file kind based on tech stack.

    Priority order:
    1. Check backend-specific template if file is in backend path
    2. Check frontend-specific template if file is in frontend path
    3. Check ORM-specific template for database files
    4. No generic fallbacks - templates must be technology-specific
    """

    project = manifest.get("project", {})

    # Determine which tech stack applies based on file path
    tech_stacks = []

    # Backend files (convex, backend packages)
    if any(marker in file_path.lower() for marker in ["/convex/", "/backend/"]):
        if project.get("backend"):
            tech_stacks.append(project["backend"])

    # Frontend files (pages, components, API routes in Next.js app router)
    elif any(
        marker in file_path.lower()
        for marker in ["/app/", "/pages/", "/components/", "/src/"]
    ):
        if project.get("web_frontend"):
            tech_stacks.append(project["web_frontend"])

    # Special case: Next.js API routes are frontend-stack specific
    if "/app/api/" in file_path.lower() or "/pages/api/" in file_path.lower():
        if project.get("web_frontend"):
            # Ensure frontend stack is first for API routes
            if project["web_frontend"] not in tech_stacks:
                tech_stacks.insert(0, project["web_frontend"])

    # ORM files (schemas, migrations, etc.)
    if "schema" in file_kind or "migration" in file_kind:
        if project.get("orm"):
            tech_stacks.append(project["orm"])

    # Auth files
    if "auth" in file_kind or "auth" in file_path.lower():
        if project.get("auth"):
            tech_stacks.append(project["auth"])

    # Map better-t-stack names to our template directories
    stack_to_template_dir = {
        "workers": "cloudflare",  # Cloudflare Workers runtime
        # Add more mappings as needed
    }

    # Try to find template in priority order
    for stack in tech_stacks:
        # Check if we need to map the stack name to a different template directory
        template_dir = stack_to_template_dir.get(stack, stack)
        template_path = templates_dir / template_dir / f"{file_kind}.jinja"
        if template_path.exists():
            return template_path

    # No fallbacks - templates must be technology-specific
    return None


def render_function_stub(func_spec: Dict, stub_level: int = 2) -> str:
    """Generate function stub code based on specification and stub level."""

    func_name = func_spec["name"]
    signature = func_spec.get("signature", {})
    params = signature.get("params", [])
    return_type = signature.get("return_type", "void")
    is_async = signature.get("async", False)
    description = func_spec.get("description", "")
    prd_refs = func_spec.get("prd_references", [])

    # Build parameter string
    param_str = ", ".join(params) if params else ""

    # Build function signature
    async_keyword = "async " if is_async else ""

    # Generate stub content based on level
    if stub_level == 0:
        # Level 0: Signatures only
        return f"{async_keyword}function {func_name}({param_str}): {return_type} {{}}"

    elif stub_level == 1:
        # Level 1: Signatures + TODO comments + minimal implementation
        todo_comment = (
            f"// TODO: {', '.join(prd_refs)} - {description}"
            if prd_refs
            else f"// TODO: {description}"
        )

        if return_type == "void":
            implementation = "// Implementation needed"
        elif return_type.startswith("Promise"):
            implementation = f'throw new Error("{func_name} not implemented");'
        elif return_type == "boolean":
            implementation = "return false; // Placeholder"
        elif return_type in ["string", "String"]:
            implementation = 'return ""; // Placeholder'
        elif return_type in ["number", "Number"]:
            implementation = "return 0; // Placeholder"
        else:
            implementation = f'throw new Error("{func_name} not implemented");'

        return f"""export {async_keyword}function {func_name}({param_str}): {return_type} {{
  {todo_comment}
  {implementation}
}}"""

    else:  # Level 2: Signatures + pseudocode
        todo_comment = (
            f"// TODO: {', '.join(prd_refs)} - {description}"
            if prd_refs
            else f"// TODO: {description}"
        )

        # Generate more sophisticated pseudocode
        first_param = params[0].split(":")[0].strip() if params else None

        if "auth" in func_name.lower() or "login" in func_name.lower():
            pseudocode = f"""// Validate input parameters
  if (!{first_param or 'email'}) {{
    throw new Error("Invalid input");
  }}

  // Perform authentication logic
  const user = await authenticateUser({first_param or 'email'});
  return user;"""

        elif "create" in func_name.lower():
            pseudocode = f"""// Validate input data
  if (!{first_param or 'data'}) {{
    throw new Error("Invalid input data");
  }}

  // Create new entity
  const newEntity = await database.create({first_param or 'data'});
  return newEntity;"""

        elif "get" in func_name.lower() or "find" in func_name.lower():
            pseudocode = f"""// Validate input parameters
  if (!{first_param or 'id'}) {{
    throw new Error("Invalid identifier");
  }}

  // Retrieve entity from database
  const entity = await database.findById({first_param or 'id'});
  if (!entity) {{
    throw new Error("Entity not found");
  }}
  return entity;"""

        elif return_type == "boolean":
            pseudocode = f"""// Validate input parameters
  if (!{first_param}) {{
    return false;
  }}

  // Perform validation logic
  const isValid = await validateEntity({first_param});
  return isValid;"""

        else:
            # Generic pseudocode
            pseudocode = f"""// Process input parameters
  const result = await processRequest({{ {first_param or 'data'} }});

  // Return processed result
  return result;"""

        return f"""export {async_keyword}function {func_name}({param_str}): {return_type} {{
  {todo_comment}

  {pseudocode}
}}"""


def render_file(file_spec: Dict, template_path: Path, stub_level: int) -> str:
    """Render a complete file using its template and function specifications."""

    try:
        # Load template
        env = Environment(loader=FileSystemLoader(template_path.parent))
        template = env.get_template(template_path.name)

        # Prepare template context
        functions = []
        for func_spec in file_spec.get("functions", []):
            func_context = {
                "name": func_spec["name"],
                "description": func_spec.get("description", ""),
                "signature": func_spec.get("signature", {}),
                "prd_references": func_spec.get("prd_references", []),
                "stub_code": render_function_stub(func_spec, stub_level),
            }
            functions.append(func_context)

        # Template context
        context = {
            "file": file_spec,
            "functions": functions,
            "options": file_spec.get("options", {}),
            "stub_level": stub_level,
        }

        # Render template
        rendered = template.render(context)
        return rendered

    except Exception as e:
        # No fallback rendering - template failures are now errors
        raise Exception(f"Template rendering failed for {file_spec['path']}: {e}")


def render_skeleton(
    manifest: Dict, project_dir: Path, templates_dir: Path, stub_level: int = 2
) -> Dict:
    """Render all skeleton files from manifest."""

    results = {"files_created": 0, "files_updated": 0, "files_failed": 0, "errors": []}

    for file_spec in manifest.get("files", []):
        file_path = project_dir / file_spec["path"]
        file_kind = file_spec.get("kind", "module")

        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Find template using new logic
            template_path = get_template_path(
                templates_dir, manifest, file_spec["path"], file_kind
            )

            if not template_path:
                # No template found - this is now an error
                project = manifest.get("project", {})
                tech_stacks = [
                    project.get(k)
                    for k in ["web_frontend", "backend", "orm", "auth"]
                    if project.get(k)
                ]
                error_msg = f"No template found for {file_kind} in stacks {tech_stacks}"
                results["files_failed"] += 1
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}", file=sys.stderr)
                continue

            # Render using template
            content = render_file(file_spec, template_path, stub_level)

            # Check if file exists
            existed = file_path.exists()

            # Write file (always overwrite for now - could add merge logic later)
            with open(file_path, "w") as f:
                f.write(content)

            if existed:
                results["files_updated"] += 1
                print(f"📝 Updated: {file_spec['path']}")
            else:
                results["files_created"] += 1
                print(f"✨ Created: {file_spec['path']}")

        except Exception as e:
            results["files_failed"] += 1
            error_msg = f"Failed to render {file_spec['path']}: {e}"
            results["errors"].append(error_msg)
            print(f"❌ {error_msg}", file=sys.stderr)

    return results


def main():
    parser = argparse.ArgumentParser(description="Render skeleton files from manifest")
    parser.add_argument(
        "--manifest", required=True, help="Path to skeleton manifest JSON"
    )
    parser.add_argument(
        "--project-dir", required=True, help="Project directory to render files into"
    )
    parser.add_argument(
        "--templates-dir", help="Templates directory (default: relative to script)"
    )
    parser.add_argument(
        "--stub-level", type=int, choices=[0, 1, 2], default=2, help="Stub detail level"
    )
    parser.add_argument("--output", help="Path to write render results JSON")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        # Resolve paths
        project_dir = Path(args.project_dir)
        if not project_dir.exists():
            print(f"❌ Project directory does not exist: {project_dir}", file=sys.stderr)
            return 1

        # Find templates directory
        if args.templates_dir:
            templates_dir = Path(args.templates_dir)
        else:
            # Default to templates in parent directory
            script_dir = Path(__file__).parent.parent
            templates_dir = script_dir / "templates"

        if not templates_dir.exists():
            print(
                f"❌ Templates directory does not exist: {templates_dir}",
                file=sys.stderr,
            )
            return 1

        # Load manifest
        manifest = load_manifest(args.manifest)

        if args.verbose:
            files_count = len(manifest.get("files", []))
            print(f"🏗️  Rendering {files_count} files at stub level {args.stub_level}")
            print(f"📁 Project: {project_dir}")
            print(f"🎨 Templates: {templates_dir}")

        # Render skeleton
        results = render_skeleton(manifest, project_dir, templates_dir, args.stub_level)

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

        # Summary
        print("\n📊 Render Results:")
        print(f"✨ Created: {results['files_created']} files")
        print(f"📝 Updated: {results['files_updated']} files")
        if results["files_failed"] > 0:
            print(f"❌ Failed: {results['files_failed']} files")

        if results["errors"] and args.verbose:
            print("\n❌ Errors:")
            for error in results["errors"]:
                print(f"  - {error}")

        # Return appropriate exit code
        return 0 if results["files_failed"] == 0 else 1

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
