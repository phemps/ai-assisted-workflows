#!/usr/bin/env python3
"""
Create a new project using better-t-stack CLI with specified technologies.
This script handles the initial project scaffolding before skeleton generation.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def build_bts_command(name: str, config: Dict) -> List[str]:
    """Build the create-better-t-stack command from config using appropriate package manager."""
    # Use the specified package manager to run create-better-t-stack
    package_manager = config.get("package_manager", "npm")

    if package_manager == "bun":
        cmd = ["bunx", "create-better-t-stack@latest", name, "--yes"]
    elif package_manager == "pnpm":
        cmd = ["pnpx", "create-better-t-stack@latest", name, "--yes"]
    elif package_manager == "yarn":
        cmd = ["yarn", "create", "better-t-stack", name, "--yes"]
    else:  # npm or fallback
        cmd = ["npx", "create-better-t-stack@latest", name, "--yes"]

    # Apply compatibility rules for different backends

    # Apply compatibility validation using our reference
    try:
        from .better_t_stack_reference import validate_config

        # Check for known incompatibilities
        is_valid, errors = validate_config(config)
        if not is_valid:
            print("⚠️  Configuration validation warnings:")
            for error in errors:
                print(f"   - {error}")
        # Continue anyway - let better-t-stack handle the actual validation

    except ImportError:
        print("ℹ️  Skipping advanced compatibility validation")

    # Let better-t-stack handle its own compatibility rules
    # Remove the previous hardcoded Convex restrictions

    # Map config to better-t-stack flags (CORRECTED based on actual CLI)
    # NOTE: Some combinations are incompatible (e.g., convex backend auto-sets many options)
    # The compatibility rules above handle these automatically

    # Frontend options (--frontend flag)
    if config.get("web_frontend"):
        cmd.extend(["--frontend", config["web_frontend"]])
        # Valid options: tanstack-router, react-router, tanstack-start, next, nuxt, svelte, solid

    # Native Frontend options
    if config.get("native_frontend"):
        cmd.extend(["--frontend", config["native_frontend"]])
        # Options: native-nativewind, native-unistyles

    # Backend options
    if config.get("backend"):
        cmd.extend(["--backend", config["backend"]])
        # Options: hono, nextjs, elysia, express, fastify, convex

    # Runtime options
    if config.get("runtime"):
        cmd.extend(["--runtime", config["runtime"]])
        # Options: bun, nodejs, workers (for Cloudflare Workers)

    # Database options
    if config.get("database"):
        cmd.extend(["--database", config["database"]])
        # Options: sqlite, postgresql, mysql, mongodb

    # ORM options
    if config.get("orm"):
        cmd.extend(["--orm", config["orm"]])
        # Options: drizzle, prisma, mongoose

    # Database Setup options
    if config.get("db_setup"):
        cmd.extend(["--db-setup", config["db_setup"]])
        # Options: turso, cloudflare-d1, neon-postgres, prisma-postgresql, supabase, mongodb-atlas, docker, basic-setup

    # Web Deploy options
    if config.get("web_deploy"):
        cmd.extend(["--web-deploy", config["web_deploy"]])
        # Options: cloudflare-workers

    # API options
    if config.get("api"):
        cmd.extend(["--api", config["api"]])
        # Options: trpc, orpc

    # Package Manager
    if config.get("package_manager"):
        cmd.extend(["--package-manager", config["package_manager"]])
        # Options: npm, yarn, pnpm, bun

    # Auth (boolean flag)
    if config.get("auth"):
        if config["auth"] == "clerk" or config["auth"] is True:
            cmd.append("--auth")
        # Note: better-t-stack doesn't have --auth clerk, just --auth boolean

    # Analytics is not directly supported by better-t-stack CLI
    # It would need to be added manually after project creation

    return cmd


def detect_package_manager(project_dir: Path) -> str:
    """Detect which package manager was used by better-t-stack."""
    # Check for lock files to determine package manager
    # Note: bun can create either bun.lock or bun.lockb
    if (project_dir / "bun.lockb").exists() or (project_dir / "bun.lock").exists():
        return "bun"
    elif (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    elif (project_dir / "yarn.lock").exists():
        return "yarn"
    elif (project_dir / "package-lock.json").exists():
        return "npm"
    else:
        # Default to npm if no lock file found
        return "npm"


def setup_formatter(project_dir: Path, formatter: str) -> bool:
    """Set up code formatter configuration in the project."""
    try:
        # Path to shared formatter configs
        config_dir = Path(__file__).parent.parent.parent / "config" / "formatter"

        if formatter == "biome":
            source_config = config_dir / "biome.json"
            target_config = project_dir / "biome.json"
            if source_config.exists():
                shutil.copy2(source_config, target_config)
                print("✅ Biome formatter configured")
                return True
        elif formatter == "ruff":
            source_config = config_dir / "ruff.toml"
            target_config = project_dir / "ruff.toml"
            if source_config.exists():
                shutil.copy2(source_config, target_config)
                print("✅ Ruff formatter configured")
                return True
        elif formatter == "prettier":
            # Create a basic prettier config
            prettier_config = {
                "semi": True,
                "trailingComma": "es5",
                "singleQuote": False,
                "tabWidth": 2,
                "useTabs": False,
            }
            with open(project_dir / ".prettierrc.json", "w") as f:
                json.dump(prettier_config, f, indent=2)
            print("✅ Prettier formatter configured")
            return True
        else:
            print(f"⚠️  Unknown formatter: {formatter}")
            return False

    except Exception as e:
        print(f"❌ Error setting up formatter: {e}")
        return False


def install_dependencies(project_dir: Path, package_manager: str) -> bool:
    """Install dependencies using detected package manager."""
    install_commands = {
        "npm": ["npm", "install"],
        "yarn": ["yarn", "install"],
        "pnpm": ["pnpm", "install"],
        "bun": ["bun", "install"],
    }

    cmd = install_commands.get(package_manager, ["npm", "install"])

    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            print("❌ Dependency installation failed:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False

        print(f"✅ Dependencies installed using {package_manager}")
        return True

    except subprocess.TimeoutExpired:
        print("❌ Dependency installation timed out", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error during dependency installation: {e}", file=sys.stderr)
        return False


def create_project(name: str, config: Dict, target_dir: Optional[str] = None) -> Dict:
    """Create better-t-stack project and return result info."""

    # Build command
    cmd = build_bts_command(name, config)

    # Determine working directory
    work_dir = Path(target_dir) if target_dir else Path.cwd()
    project_dir = work_dir / name

    print(f"Creating project: {' '.join(cmd)}")
    print(f"Working directory: {work_dir}")

    try:
        # Run better-t-stack creation
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout
        )

        if result.returncode != 0:
            error_msg = "CRITICAL: better-t-stack creation failed"
            print(f"❌ {error_msg}", file=sys.stderr)
            print(f"Command: {' '.join(cmd)}", file=sys.stderr)
            print(f"STDOUT: {result.stdout}", file=sys.stderr)
            print(f"STDERR: {result.stderr}", file=sys.stderr)
            return {
                "success": False,
                "error": error_msg,
                "command": " ".join(cmd),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "escalate_to_user": True,
            }

        # Verify project was created
        if not project_dir.exists():
            return {
                "success": False,
                "error": f"Project directory {project_dir} was not created",
                "command": " ".join(cmd),
            }

        # Detect package manager
        package_manager = detect_package_manager(project_dir)

        # Set up formatter if specified
        if config.get("formatter"):
            if not setup_formatter(project_dir, config["formatter"]):
                print("⚠️  Formatter setup failed, continuing with project creation")

        # Install dependencies with STRICT package manager checking
        detected_pm = detect_package_manager(project_dir)
        requested_pm = config.get("package_manager", "npm")

        # CRITICAL: If user specified a package manager, it MUST be used
        if requested_pm != "npm" and detected_pm != requested_pm:
            return {
                "success": False,
                "error": f"CRITICAL: Requested package manager '{requested_pm}' was not used. Project created with '{detected_pm}'. This indicates better-t-stack configuration failed.",
                "project_dir": str(project_dir),
                "requested_package_manager": requested_pm,
                "detected_package_manager": detected_pm,
                "escalate_to_user": True,
            }

        if not install_dependencies(project_dir, detected_pm):
            return {
                "success": False,
                "error": f"CRITICAL: Dependency installation failed with {detected_pm}. Cannot proceed with broken project.",
                "project_dir": str(project_dir),
                "package_manager": detected_pm,
                "escalate_to_user": True,
            }

        # Return success info
        return {
            "success": True,
            "project_dir": str(project_dir),
            "package_manager": package_manager,
            "formatter": config.get("formatter"),
            "config": config,
            "command": " ".join(cmd),
            "stdout": result.stdout,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Project creation timed out",
            "command": " ".join(cmd),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "command": " ".join(cmd),
        }


def main():
    parser = argparse.ArgumentParser(description="Create better-t-stack project")
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument(
        "--config", required=True, help="Path to JSON config file with stack choices"
    )
    parser.add_argument(
        "--target-path",
        required=True,
        help="Target directory path where project will be created",
    )
    parser.add_argument("--output", help="Path to write result JSON")

    args = parser.parse_args()

    # Read config
    try:
        with open(args.config, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error reading config file: {e}", file=sys.stderr)
        return 1

    # Validate target path exists
    target_path = Path(args.target_path)
    if not target_path.exists():
        print(f"❌ Target path does not exist: {target_path}", file=sys.stderr)
        return 1

    if not target_path.is_dir():
        print(f"❌ Target path is not a directory: {target_path}", file=sys.stderr)
        return 1

    # Create project
    result = create_project(args.name, config, str(target_path))

    # Output result
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

    # Return appropriate exit code
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
