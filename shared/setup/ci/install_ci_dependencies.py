#!/usr/bin/env python3
"""
install_ci_dependencies.py v1.0

Cross-platform installer for continuous improvement dependencies: MCP, CodeBERT, Faiss, transformers.
Checks for package presence, asks user consent, and installs using pip with fail-fast behavior.
Follows the exact pattern from dev-monitoring setup.
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, shell=False, capture_output=True):
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd, capture_output=capture_output, text=True, shell=shell
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def check_python_package(package_name):
    """Check if a Python package is installed."""
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pip", "show", package_name]
    )
    return success


def check_serena_mcp():
    """Check if Serena MCP is available."""
    # Check if uvx is available
    success, _, _ = run_command(["which", "uvx"])
    if not success:
        return False

    # Check if serena can be accessed via uvx
    success, _, _ = run_command(
        ["uvx", "--from", "git+https://github.com/oraios/serena", "serena", "--version"]
    )
    return success


def get_user_consent(missing_packages, missing_tools):
    """Ask user for consent to install missing packages and tools."""
    print("\nContinuous Improvement System Dependencies:")

    if missing_packages:
        print(f"Missing Python packages: {', '.join(missing_packages)}")

    if missing_tools:
        print(f"Missing tools: {', '.join(missing_tools)}")

    print("\nThese are required for:")
    print("  - Code duplication detection using ML embeddings")
    print("  - Vector similarity search for performance")
    print("  - Codebase analysis and symbol extraction")
    print("  - Integration with Claude Code agent system")

    while True:
        response = input("\nWould you like to install them? (y/n): ").lower().strip()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def install_python_packages(packages):
    """Install Python packages using pip."""
    print(f"Installing Python packages: {', '.join(packages)}")

    # Create requirements content
    requirements = [
        "numpy<2.0.0",  # Numerical operations - pin to avoid OpenTelemetry conflicts
        "opentelemetry-api==1.27.0",  # OpenTelemetry API - pinned version for ChromaDB compatibility
        "opentelemetry-sdk==1.27.0",  # OpenTelemetry SDK - pinned version for ChromaDB compatibility
        "opentelemetry-exporter-otlp-proto-grpc==1.27.0",  # OpenTelemetry OTLP exporter - pinned version
        "chromadb>=0.4.0",  # Vector database for embeddings
        "faiss-cpu>=1.7.0",  # Vector similarity search
        "transformers>=4.21.0",  # CodeBERT embeddings
        "torch>=1.12.0",  # PyTorch for transformers
        "scipy>=1.7.0",  # Scientific computing
        "scikit-learn>=1.0.0",  # Machine learning utilities
        "sentence-transformers>=2.2.0",  # Semantic embeddings
        "tokenizers>=0.13.0",  # Fast tokenization
        "datasets>=2.0.0",  # Dataset utilities
    ]

    failed_packages = []

    for requirement in requirements:
        package_name = requirement.split(">=")[0].split("==")[0]
        if package_name in packages:
            print(f"  Installing {requirement}...")
            success, stdout, stderr = run_command(
                [sys.executable, "-m", "pip", "install", requirement]
            )

            if success:
                print(f"    ✓ {package_name} installed successfully")
            else:
                print(f"    ✗ Failed to install {package_name}: {stderr}")
                failed_packages.append(package_name)

    return failed_packages


def setup_serena_mcp():
    """Setup Serena MCP server integration."""
    print("Setting up Serena MCP server...")

    # Check if uvx is available first
    success, _, _ = run_command(["which", "uvx"])
    if not success:
        print("  Installing uvx (Python package executor)...")
        success, stdout, stderr = run_command(
            [sys.executable, "-m", "pip", "install", "uvx"]
        )
        if not success:
            return False, f"Failed to install uvx: {stderr}"

    # Test serena availability
    print("  Testing Serena MCP availability...")
    success, stdout, stderr = run_command(
        [
            "uvx",
            "--from",
            "git+https://github.com/oraios/serena",
            "serena",
            "--version",
        ],
        capture_output=True,
    )

    if success:
        print(f"    ✓ Serena MCP available: {stdout}")
        return True, "Serena MCP ready for integration"
    else:
        return False, f"Serena MCP test failed: {stderr}"


def create_requirements_file():
    """Create requirements.txt for continuous improvement."""
    requirements_dir = Path(__file__).parent
    requirements_file = requirements_dir / "requirements.txt"

    requirements_content = """# Continuous Improvement Framework Dependencies
# OpenTelemetry dependencies - pinned versions for ChromaDB compatibility
numpy<2.0.0
opentelemetry-api==1.27.0
opentelemetry-sdk==1.27.0
opentelemetry-exporter-otlp-proto-grpc==1.27.0

# Vector similarity search and embeddings
chromadb>=0.4.0
faiss-cpu>=1.7.0
transformers>=4.21.0
torch>=1.12.0
sentence-transformers>=2.2.0
tokenizers>=0.13.0

# Scientific computing and utilities
scipy>=1.7.0
scikit-learn>=1.0.0
datasets>=2.0.0

# Additional utilities
uvx>=0.0.1  # Python package executor for MCP integration
"""

    with open(requirements_file, "w") as f:
        f.write(requirements_content)

    print(f"  ✓ Created {requirements_file}")
    return str(requirements_file)


def main():
    """Main function to check and install continuous improvement dependencies."""
    print("Checking Continuous Improvement Dependencies...")
    print("Required: MCP tools, ML packages, and code analysis utilities")

    # Define required packages and tools
    required_packages = [
        "numpy",
        "opentelemetry-api",
        "opentelemetry-sdk",
        "opentelemetry-exporter-otlp-proto-grpc",
        "chromadb",
        "faiss-cpu",
        "transformers",
        "torch",
        "scipy",
        "scikit-learn",
        "sentence-transformers",
        "tokenizers",
        "datasets",
    ]

    # Check Python packages
    missing_packages = []
    for package in required_packages:
        if not check_python_package(package):
            missing_packages.append(package)

    # Check tools
    missing_tools = []
    if not check_serena_mcp():
        missing_tools.append("serena-mcp")

    # Report status
    if not missing_packages and not missing_tools:
        print("\n✓ All continuous improvement dependencies are installed!")
        print("✓ Serena MCP integration available")
        print("✓ ML packages ready for duplicate detection")
        return 0

    # Ask for user consent
    if not get_user_consent(missing_packages, missing_tools):
        print("Installation cancelled by user.")
        print("\nNote: Continuous improvement system requires these dependencies")
        print("Run again when ready to install, or install manually:")
        print("  pip install faiss-cpu transformers torch sentence-transformers")
        return 1

    # Create requirements file
    print("\nPreparing installation...")
    requirements_file = create_requirements_file()

    # Install Python packages
    failed_packages = []
    if missing_packages:
        print("\nInstalling Python packages using pip...")
        failed_packages = install_python_packages(missing_packages)

    # Setup MCP integration
    mcp_success = True
    mcp_error = ""
    if "serena-mcp" in missing_tools:
        print("\nSetting up MCP integration...")
        mcp_success, mcp_error = setup_serena_mcp()

    # Summary
    print("\n" + "=" * 50)
    if failed_packages:
        print(f"⚠️  Failed to install packages: {', '.join(failed_packages)}")
        print("   Try installing manually with:")
        print(f"   pip install -r {requirements_file}")
        return 1

    if not mcp_success:
        print(f"⚠️  Serena MCP setup failed: {mcp_error}")
        print("   Manual setup required:")
        print("   uvx --from git+https://github.com/oraios/serena serena --version")
        return 1

    print("✓ All continuous improvement dependencies installed successfully!")
    print("\n🎉 System Ready for Continuous Improvement!")
    print("\nNext steps:")
    print("  1. Run: claude /setup-ci-monitoring")
    print("  2. Configure project-specific thresholds")
    print("  3. Initialize code registry and GitHub Actions")

    return 0


if __name__ == "__main__":
    sys.exit(main())
