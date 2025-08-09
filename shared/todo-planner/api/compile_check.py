#!/usr/bin/env python3
"""
Run compile, lint, and typecheck quality gates on a project.
Detects package manager and available scripts from package.json.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def detect_package_manager(project_dir: Path) -> str:
    """Detect which package manager is used."""
    # Check for bun lockfiles (both variants)
    if (project_dir / "bun.lockb").exists() or (project_dir / "bun.lock").exists():
        return "bun"
    elif (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    elif (project_dir / "yarn.lock").exists():
        return "yarn"
    elif (project_dir / "package-lock.json").exists():
        return "npm"
    # Check for bunfig.toml as another indicator
    elif (project_dir / "bunfig.toml").exists():
        return "bun"
    else:
        return "npm"  # Default


def get_available_scripts(project_dir: Path) -> Dict[str, str]:
    """Read available scripts from package.json."""
    package_json = project_dir / "package.json"
    if not package_json.exists():
        return {}

    try:
        with open(package_json) as f:
            data = json.load(f)
        return data.get("scripts", {})
    except Exception:
        return {}


def run_command(
    cmd: List[str], project_dir: Path, timeout: int = 60
) -> Tuple[bool, str, str]:
    """Run a command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=project_dir, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def install_dependencies(
    project_dir: Path, package_manager: str
) -> Tuple[bool, str, str]:
    """Install project dependencies."""
    install_commands = {
        "npm": ["npm", "install"],
        "yarn": ["yarn", "install"],
        "pnpm": ["pnpm", "install"],
        "bun": ["bun", "install"],
    }

    cmd = install_commands.get(package_manager, install_commands["npm"])
    print(f"Installing dependencies with {package_manager}...")

    return run_command(cmd, project_dir, timeout=300)  # 5 min timeout for installs


def check_quality_gates(project_dir: Path) -> Dict:
    """Run all available quality checks."""
    project_path = Path(project_dir)

    # Detect package manager and scripts
    package_manager = detect_package_manager(project_path)
    available_scripts = get_available_scripts(project_path)

    # Install dependencies first if node_modules doesn't exist
    if not (project_path / "node_modules").exists():
        success, stdout, stderr = install_dependencies(project_path, package_manager)
        if not success:
            return {
                "project_dir": str(project_path),
                "package_manager": package_manager,
                "available_scripts": available_scripts,
                "checks": {},
                "overall_status": "failed",
                "summary": "Dependency installation failed",
                "install_error": {"stdout": stdout, "stderr": stderr},
            }
        print("✅ Dependencies installed successfully")

    # Define command patterns for different package managers
    pm_commands = {
        "npm": lambda script: ["npm", "run", script],
        "yarn": lambda script: ["yarn", script],
        "pnpm": lambda script: ["pnpm", script],
        "bun": lambda script: ["bun", "run", script],
    }

    cmd_builder = pm_commands.get(package_manager, pm_commands["npm"])

    results = {
        "project_dir": str(project_path),
        "package_manager": package_manager,
        "available_scripts": available_scripts,
        "checks": {},
    }

    # Define quality gate checks in priority order
    quality_gates = [
        ("build", "Build compilation", 120),  # 2 min timeout for builds
        ("typecheck", "TypeScript type checking", 60),
        ("type-check", "TypeScript type checking", 60),  # Alternative name
        ("lint", "Code linting", 60),
        ("format:check", "Format checking", 30),
        ("format-check", "Format checking", 30),  # Alternative name
    ]

    # Run each available quality gate
    for script_name, description, timeout in quality_gates:
        if script_name in available_scripts:
            print(f"Running {description}...")

            cmd = cmd_builder(script_name)
            success, stdout, stderr = run_command(cmd, project_path, timeout)

            results["checks"][script_name] = {
                "description": description,
                "command": " ".join(cmd),
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
            }

            status = "✅" if success else "❌"
            print(f"{status} {description}: {'PASSED' if success else 'FAILED'}")

            if not success and stderr:
                print(f"   Error: {stderr[:200]}...")
        else:
            print(f"⏭️  {description}: Script '{script_name}' not available")

    # Calculate overall status
    checks = results["checks"]
    if not checks:
        results["overall_status"] = "no_checks"
        results["summary"] = "No quality gate scripts found"
    else:
        passed = sum(1 for check in checks.values() if check["success"])
        total = len(checks)
        all_passed = passed == total

        results["overall_status"] = "passed" if all_passed else "failed"
        results["summary"] = f"{passed}/{total} quality gates passed"

    return results


def detect_project_type(project_dir: Path) -> Dict[str, bool]:
    """Detect project characteristics for better error reporting."""
    characteristics = {
        "has_typescript": False,
        "has_eslint": False,
        "has_prettier": False,
        "has_tests": False,
    }

    # Check for TypeScript
    if (project_dir / "tsconfig.json").exists():
        characteristics["has_typescript"] = True

    # Check for ESLint
    eslint_configs = [
        ".eslintrc.js",
        ".eslintrc.json",
        ".eslintrc.yml",
        ".eslintrc.yaml",
        "eslint.config.js",
    ]
    if any((project_dir / config).exists() for config in eslint_configs):
        characteristics["has_eslint"] = True

    # Check for Prettier
    prettier_configs = [
        ".prettierrc",
        ".prettierrc.json",
        ".prettierrc.js",
        ".prettierrc.yml",
        ".prettierrc.yaml",
        "prettier.config.js",
    ]
    if any((project_dir / config).exists() for config in prettier_configs):
        characteristics["has_prettier"] = True

    # Check for tests
    test_dirs = ["test", "tests", "__tests__", "spec"]
    if any((project_dir / test_dir).exists() for test_dir in test_dirs):
        characteristics["has_tests"] = True

    return characteristics


def main():
    parser = argparse.ArgumentParser(description="Run project quality gates")
    parser.add_argument(
        "--project-dir", required=True, help="Path to project directory"
    )
    parser.add_argument("--output", help="Path to write results JSON")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    project_dir = Path(args.project_dir)

    if not project_dir.exists():
        print(f"❌ Project directory does not exist: {project_dir}", file=sys.stderr)
        return 1

    if not (project_dir / "package.json").exists():
        print(f"❌ No package.json found in: {project_dir}", file=sys.stderr)
        return 1

    # Run quality checks
    results = check_quality_gates(project_dir)

    # Add project characteristics if verbose
    if args.verbose:
        results["project_characteristics"] = detect_project_type(project_dir)

    # Output results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
    elif args.verbose:
        print("\n" + "=" * 50)
        print("QUALITY GATE RESULTS")
        print("=" * 50)
        print(json.dumps(results, indent=2))
    else:
        print(f"\n📊 {results['summary']}")
        if results["overall_status"] == "failed":
            print("\n❌ Quality gates failed. Run with --verbose for details.")

    # Return exit code
    if results["overall_status"] == "passed":
        return 0
    elif results["overall_status"] == "no_checks":
        print("⚠️  No quality gates configured - assuming success")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
