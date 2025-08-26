#!/usr/bin/env python3
"""
CLI Tool Evaluation Harness

Main entry point for evaluating CLI tools with Docker isolation,
secure token handling, and comprehensive metrics collection.
"""

import argparse
import json
import sys
import time
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Import our evaluator
from lib.evaluator import CLIEvaluator


def validate_environment():
    """Validate the environment and provide helpful feedback."""
    issues = []

    # Check if Docker is available
    try:
        import subprocess

        result = subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
        docker_available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        docker_available = False

    if not docker_available:
        issues.append("Docker not available")

    # Check if scenarios directory exists
    if not Path("scenarios").exists():
        issues.append("scenarios/ directory not found")

    # Check if cli_installers directory exists
    if not Path("cli_installers").exists():
        issues.append("cli_installers/ directory not found")

    return issues, docker_available


def print_usage_examples():
    """Print usage examples for different scenarios."""
    print(
        """
🎯 USAGE EXAMPLES:

# API Key Authentication (automated)
python run_eval.py scenarios/baseline_task.yaml \\
  --cli-tool claude \\
  --auth apikey \\
  --api-key "your-claude-api-key"

# OAuth Authentication (interactive)
python run_eval.py scenarios/baseline_task.yaml \\
  --cli-tool claude \\
  --auth oauth

# Test with Qwen using API key
python run_eval.py scenarios/baseline_task.yaml \\
  --cli-tool qwen \\
  --auth apikey \\
  --api-key "sk-your-openai-api-key"

# Test with Gemini using OAuth (interactive)
python run_eval.py scenarios/baseline_task.yaml \\
  --cli-tool gemini \\
  --auth oauth

# One-time test (cleanup container after)
python run_eval.py scenarios/baseline_task.yaml \\
  --cli-tool claude \\
  --auth apikey \\
  --api-key "your-api-key" \\
  --tear-down

# Save as baseline for comparison
python run_eval.py scenarios/baseline_task.yaml \\
  --cli-tool claude \\
  --auth oauth \\
  --save-baseline

# Verbose mode (real-time output)
python run_eval.py scenarios/baseline_task.yaml \\
  --cli-tool claude \\
  --auth apikey \\
  --api-key "your-api-key" \\
  --verbose

🔧 DOCKER MANAGEMENT:

# Build Docker images
python docker_build.py

# Clean up containers (stop only)
python docker_cleanup.py

# Full cleanup (remove everything)
python docker_cleanup.py --purge

🔐 SECURITY NOTES:

• API keys are never stored in files, logs, or containers
• Use environment variables for API keys in CI/CD:
  export CLAUDE_API_KEY="your-api-key"
  python run_eval.py scenarios/baseline_task.yaml --cli-tool claude --auth apikey

• OAuth credentials persist in container volumes for reuse
• Containers are reused by default for efficiency
• Use --tear-down for one-time tests or sensitive environments
"""
    )


def save_report(report: Dict[str, Any]) -> Path:
    """Save evaluation report to disk."""
    # Ensure reports directory exists
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    # Generate report filename
    timestamp = report.get("timestamp", "unknown")
    report_path = reports_dir / f"run_{timestamp}.json"

    # Sanitize report before saving (security check)
    sanitized_report = sanitize_report(report)

    # Save report
    with open(report_path, "w") as f:
        json.dump(sanitized_report, f, indent=2, default=str)

    return report_path


def sanitize_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Remove any sensitive information from report."""
    # Create a copy to avoid modifying original
    sanitized = report.copy()

    # Remove any potential sensitive keys
    sensitive_keys = [
        "api_key",
        "auth_token",
        "token",
        "password",
        "secret",
        "CLAUDE_API_KEY",
        "QWEN_API_KEY",
        "GEMINI_API_KEY",
        "CLAUDE_AUTH_TOKEN",  # Legacy
        "OPENAI_API_KEY",
        "GEMINI_AUTH_TOKEN",  # Legacy
    ]

    def remove_sensitive(obj):
        if isinstance(obj, dict):
            return {
                k: remove_sensitive(v)
                for k, v in obj.items()
                if k not in sensitive_keys
            }
        elif isinstance(obj, list):
            return [remove_sensitive(item) for item in obj]
        else:
            return obj

    return remove_sensitive(sanitized)


def main():
    parser = argparse.ArgumentParser(
        description="CLI Tool Evaluation Harness with Docker Isolation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use --examples to see usage examples",
    )

    # Core arguments
    parser.add_argument(
        "scenario",
        nargs="?",  # Make scenario optional
        help="Path to scenario YAML file",
    )
    parser.add_argument(
        "--cli-tool",
        default="claude",
        choices=list(CLIEvaluator.CLI_CONFIGS.keys()),
        help="CLI tool to test (default: claude)",
    )
    parser.add_argument(
        "--prompt",
        default="/todo-orchestrate",
        help="Prompt/command for CLI tool (default: /todo-orchestrate)",
    )

    # Authentication
    parser.add_argument(
        "--auth",
        choices=["oauth", "apikey"],
        default="apikey",
        help="Authentication method (default: apikey)",
    )
    parser.add_argument("--api-key", help="API key for authentication (never stored)")

    # Test options
    parser.add_argument(
        "--tear-down",
        action="store_true",
        help="Remove container after test (default: persist for reuse)",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save results as baseline for comparison",
    )
    parser.add_argument("--compare", action="store_true", help="Compare with baseline")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    # Help options
    parser.add_argument(
        "--examples", action="store_true", help="Show usage examples and exit"
    )
    parser.add_argument(
        "--check-env", action="store_true", help="Check environment and exit"
    )

    args = parser.parse_args()

    # Handle special options that don't require scenario
    if args.examples:
        print_usage_examples()
        return 0

    if args.check_env:
        print("🔍 Environment Check")
        print("=" * 40)
        issues, docker_available = validate_environment()

        print(f"Docker available: {'✅' if docker_available else '❌'}")
        print(f"Scenarios directory: {'✅' if Path('scenarios').exists() else '❌'}")
        print(f"CLI installers: {'✅' if Path('cli_installers').exists() else '❌'}")

        if issues:
            print("\n⚠️  Issues found:")
            for issue in issues:
                print(f"  • {issue}")
            print("\n💡 Run 'python docker_build.py' to set up Docker components")
            return 1
        else:
            print("\n✅ Environment looks good!")
            return 0

    # Validate scenario argument for normal operation
    if not args.scenario:
        print("❌ Scenario file is required for test execution")
        parser.print_help()
        return 1

    # Validate environment for normal operation
    issues, docker_available = validate_environment()

    if not docker_available:
        print("❌ Docker is not available")
        print("   • Install Docker Desktop")
        print("   • Run 'docker --version' to check installation")
        return 1

    # Load environment variables from .env file
    load_dotenv()

    # Handle authentication based on mode
    api_key = None
    if args.auth == "apikey":
        # Get API key from command line, .env file, or environment
        api_key = args.api_key
        if not api_key:
            env_vars = {
                "claude": "CLAUDE_API_KEY",
                "qwen": "QWEN_API_KEY",
                "gemini": "GEMINI_API_KEY",
            }

            env_var = env_vars.get(args.cli_tool)
            if env_var:
                api_key = os.environ.get(env_var)
                if api_key:
                    print(f"📋 Using {env_var} from .env or environment")

        # Validate API key is present for API key mode
        if not api_key:
            env_vars = {
                "claude": "CLAUDE_API_KEY",
                "qwen": "QWEN_API_KEY",
                "gemini": "GEMINI_API_KEY",
            }
            print(f"❌ No API key provided for {args.cli_tool}")
            print("\nPlease provide an API key using one of these methods:")
            print("1. Command line: --api-key 'your-api-key'")
            print(
                f"2. .env file: {env_vars.get(args.cli_tool, 'UNKNOWN')}=your-api-key"
            )
            print(
                f"3. Environment variable: export {env_vars.get(args.cli_tool, 'UNKNOWN')}=your-api-key"
            )
            return 1
    else:  # OAuth mode
        print(f"🔐 Using OAuth authentication for {args.cli_tool}")
        print("Interactive authentication will be required after CLI installation.")

    try:
        # Create CLI evaluator
        evaluator = CLIEvaluator(
            scenario_path=args.scenario,
            cli_tool=args.cli_tool,
            prompt=args.prompt,
            auth_mode=args.auth,
            api_key=api_key,
            tear_down=args.tear_down,
            verbose=args.verbose,
        )

        # Run the test
        start_time = time.time()
        report = evaluator.run_test(
            save_baseline=args.save_baseline, compare=args.compare
        )
        total_time = time.time() - start_time

        # Save report
        report_path = save_report(report)

        # Display results summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Scenario: {report.get('scenario_id', 'Unknown')}")
        print(f"CLI Tool: {report.get('cli_tool', 'Unknown')}")
        print(f"Exit Code: {report.get('exit_code', -1)}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Report: {report_path}")

        # Show KPIs if available
        kpis = report.get("kpis", {})
        if kpis:
            print("\n📈 Key Performance Indicators:")
            for kpi, value in kpis.items():
                print(f"   {kpi}: {value}")

        # Success indicator
        exit_code = report.get("exit_code", 0)
        if exit_code == 0:
            print("\n✅ Test completed successfully!")
            return 0
        else:
            print(f"\n⚠️  Test completed with exit code {exit_code}")
            return 0  # Don't fail the evaluation itself

    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
