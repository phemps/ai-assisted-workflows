#!/usr/bin/env python3
"""
Create a new project using better-t-stack CLI with specified technologies.
This script handles the initial project scaffolding before skeleton generation.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def build_bts_command(name: str, config: Dict) -> List[str]:
    """Build the npx create-better-t-stack command from config."""
    cmd = ["npx", "create-better-t-stack@latest", name]

    # Map config to better-t-stack flags
    if config.get("web_frontend"):
        cmd.extend(["--web", config["web_frontend"]])

    if config.get("native_frontend"):
        cmd.extend(["--native", config["native_frontend"]])

    if config.get("backend"):
        cmd.extend(["--backend", config["backend"]])

    if config.get("runtime"):
        cmd.extend(["--runtime", config["runtime"]])

    if config.get("database"):
        cmd.extend(["--database", config["database"]])

    if config.get("orm"):
        cmd.extend(["--orm", config["orm"]])

    if config.get("database_setup"):
        cmd.extend(["--database-setup", config["database_setup"]])

    if config.get("deploy"):
        cmd.extend(["--deploy", config["deploy"]])

    if config.get("auth"):
        cmd.extend(["--auth", config["auth"]])

    # Handle addons (multiple values)
    if config.get("addons"):
        for addon in config["addons"]:
            cmd.extend(["--addon", addon])

    return cmd


def detect_package_manager(project_dir: Path) -> str:
    """Detect which package manager was used by better-t-stack."""
    # Check for lock files to determine package manager
    if (project_dir / "bun.lockb").exists():
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
            return {
                "success": False,
                "error": f"better-t-stack creation failed: {result.stderr}",
                "command": " ".join(cmd),
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

        # Install dependencies
        if not install_dependencies(project_dir, package_manager):
            return {
                "success": False,
                "error": "Dependency installation failed",
                "project_dir": str(project_dir),
                "package_manager": package_manager,
            }

        # Return success info
        return {
            "success": True,
            "project_dir": str(project_dir),
            "package_manager": package_manager,
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
        "--target-dir", help="Target directory (default: current directory)"
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

    # Create project
    result = create_project(args.name, config, args.target_dir)

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
