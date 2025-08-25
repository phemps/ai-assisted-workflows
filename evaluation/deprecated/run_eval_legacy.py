#!/usr/bin/env python3
"""
CLI Tool Evaluation Harness

External test harness that wraps CLI tools to collect performance metrics
without modifying the existing tool workflows.
"""

import json
import subprocess
import time
import yaml
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def get_default_flags(cli_tool: str) -> str:
    """Get default flags for specific CLI tools"""
    defaults = {
        "claude": "-p --add-dir {workspace} --permission-mode bypassPermissions",
        "gpt": "--workspace {workspace}",
        "openai": "--workspace {workspace}",
        "custom-tool": "{workspace}",
        "default": "",  # No flags for unknown tools
    }
    return defaults.get(cli_tool, defaults["default"])


class CLIEvaluator:
    """Test harness for evaluating CLI tool performance"""

    def __init__(
        self,
        scenario_path: str,
        cli_tool: str = "claude",
        prompt: str = "/todo-orchestrate",
        flags: str = None,
        verbose: bool = False,
    ):
        self.scenario_path = Path(scenario_path)
        self.cli_tool = cli_tool
        self.prompt = prompt
        self.flags = flags if flags is not None else get_default_flags(cli_tool)
        self.verbose = verbose
        self.scenario = self.load_scenario()
        self.start_time = None
        self.end_time = None
        self.metrics = {
            "K1_failed_tools": 0,
            "K2_quality_reruns": 0,
            "K9_token_spend": 0,
            "K11_runtime_seconds": 0,
            "raw_data": {
                "tool_calls": [],
                "state_transitions": [],
                "token_events": [],
                "errors": [],
            },
        }

    def load_scenario(self) -> Dict[str, Any]:
        """Load test scenario configuration"""
        if not self.scenario_path.exists():
            raise FileNotFoundError(f"Scenario file not found: {self.scenario_path}")

        with open(self.scenario_path, "r") as f:
            return yaml.safe_load(f)

    def run_test(
        self, save_baseline: bool = False, compare: bool = False
    ) -> Dict[str, Any]:
        """Execute the test scenario and collect metrics"""
        print(f"🧪 Running evaluation: {self.scenario['id']}")
        print(f"📄 Plan file: {self.scenario['plan_file']}")

        # Setup monitoring
        self.start_time = time.time()

        # Prepare log capture
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("reports")
        log_dir.mkdir(exist_ok=True)

        # Create isolated test workspace
        test_workspace = Path(f"workspaces/run_{timestamp}")
        test_workspace.mkdir(parents=True, exist_ok=True)
        self.test_workspace = str(test_workspace)

        # Execute CLI tool
        plan_path = Path("scenarios") / self.scenario["plan_file"]
        if not plan_path.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_path}")

        # Store plan path for reporting
        self.plan_path_executed = str(plan_path)

        # Build the command array with proper token replacement
        cmd = [self.cli_tool]

        # Handle the -p flag specially for claude (it needs the prompt combined)
        if "-p" in self.flags:
            # Claude-style command: claude -p "prompt plan_file" --other-flags
            full_prompt = f"{self.prompt} {plan_path}"
            cmd.extend(["-p", full_prompt])

            # Add remaining flags (excluding -p) with token replacement
            flag_parts = self.flags.split()
            skip_next = False
            for part in flag_parts:
                if skip_next:
                    skip_next = False
                    continue
                if part == "-p":
                    skip_next = True  # Skip the next part if it's a -p argument
                    continue
                # Apply token replacement to this flag part
                processed_part = part.replace("{workspace}", str(test_workspace))
                processed_part = processed_part.replace("{plan_file}", str(plan_path))
                cmd.append(processed_part)
        else:
            # Other CLI tools - add flags with token replacement, then prompt and plan
            flag_parts = self.flags.split()
            for part in flag_parts:
                processed_part = part.replace("{workspace}", str(test_workspace))
                processed_part = processed_part.replace("{plan_file}", str(plan_path))
                cmd.append(processed_part)
            cmd.extend([self.prompt, str(plan_path)])

        print(f"⚡ Executing: {' '.join(cmd)}")
        print(f"📁 Workspace: {test_workspace}")

        try:
            # Run CLI command with output capture in isolated workspace
            if self.verbose:
                print("📺 Verbose mode: streaming output...")
                result = subprocess.run(
                    cmd,
                    cwd=str(test_workspace),  # Execute in isolated directory
                    text=True,
                    timeout=self.scenario.get("max_duration_minutes", 30) * 60,
                )
                # In verbose mode, output goes to terminal, we need to capture separately
                self.raw_output = (
                    f"Process completed with exit code: {result.returncode}"
                )
                self.raw_errors = ""
            else:
                result = subprocess.run(
                    cmd,
                    cwd=str(test_workspace),  # Execute in isolated directory
                    capture_output=True,
                    text=True,
                    timeout=self.scenario.get("max_duration_minutes", 30) * 60,
                )
                # Store raw output for parsing
                self.raw_output = result.stdout
                self.raw_errors = result.stderr

            self.end_time = time.time()
            self.exit_code = result.returncode

        except subprocess.TimeoutExpired:
            self.end_time = time.time()
            print("⏰ Test timed out")
            self.raw_output = ""
            self.raw_errors = "Test timed out"
            self.exit_code = 124  # Timeout exit code

        # Parse metrics from output
        self.parse_metrics()

        # Generate report
        report = self.generate_report(timestamp)

        if save_baseline:
            self.save_baseline(report)
            print("💾 Baseline saved")

        if compare:
            self.compare_with_baseline(report)

        # Handle workspace cleanup
        self.handle_workspace_cleanup()

        return report

    def handle_workspace_cleanup(self):
        """Clean up test workspace based on scenario configuration"""
        cleanup_workspace = self.scenario.get("cleanup_workspace", False)

        if cleanup_workspace and hasattr(self, "test_workspace"):
            try:
                shutil.rmtree(self.test_workspace)
                print(f"🧹 Cleaned up workspace: {self.test_workspace}")
            except Exception as e:
                print(f"⚠️  Failed to clean up workspace {self.test_workspace}: {e}")
        elif hasattr(self, "test_workspace"):
            print(f"💾 Workspace preserved: {self.test_workspace}")

    def parse_metrics(self):
        """Extract KPIs from CLI tool output and logs"""

        # K11: Runtime (easy one first)
        if self.start_time and self.end_time:
            self.metrics["K11_runtime_seconds"] = round(
                self.end_time - self.start_time, 2
            )

        # Parse stdout and stderr for patterns
        full_output = f"{self.raw_output}\n{self.raw_errors}"

        # K1: Failed Tool Calls
        # Look for common failure patterns
        tool_failure_patterns = [
            r"Tool execution failed",
            r'"error":\s*true',
            r"Command not found",
            r"Permission denied",
            r"No such file or directory",
            r"Exit code: [1-9]\d*",  # Non-zero exit codes
            r"Error: .*",
            r"Failed to .*",
        ]

        failed_tools = 0
        for pattern in tool_failure_patterns:
            matches = re.findall(pattern, full_output, re.IGNORECASE)
            failed_tools += len(matches)
            if matches:
                self.metrics["raw_data"]["tool_calls"].extend(matches)

        self.metrics["K1_failed_tools"] = failed_tools

        # K2: Quality Gate Reruns
        # Look for state transitions indicating quality issues
        quality_rerun_patterns = [
            r"quality_review.*in_progress",
            r"testing.*in_progress",
            r"Rerunning quality checks",
            r"Quality gate failed.*retrying",
            r"Re-attempting.*quality",
        ]

        reruns = 0
        for pattern in quality_rerun_patterns:
            matches = re.findall(pattern, full_output, re.IGNORECASE)
            reruns += len(matches)
            if matches:
                self.metrics["raw_data"]["state_transitions"].extend(matches)

        self.metrics["K2_quality_reruns"] = reruns

        # K9: Token Spend
        # Look for token usage patterns in output
        token_patterns = [
            r"tokens?[:\s]*(\d+)",
            r"usage[:\s]*(\d+)",
            r"cost[:\s]*\$?(\d+\.?\d*)",
        ]

        total_tokens = 0
        for pattern in token_patterns:
            matches = re.findall(pattern, full_output, re.IGNORECASE)
            for match in matches:
                try:
                    tokens = int(float(match))  # Handle both int and float strings
                    total_tokens += tokens
                    self.metrics["raw_data"]["token_events"].append(tokens)
                except ValueError:
                    continue

        self.metrics["K9_token_spend"] = total_tokens

        # Store any errors found
        error_patterns = [r"ERROR:.*", r"CRITICAL:.*", r"Exception.*"]

        for pattern in error_patterns:
            matches = re.findall(pattern, full_output, re.IGNORECASE)
            self.metrics["raw_data"]["errors"].extend(matches)

    def generate_report(self, timestamp: str) -> Dict[str, Any]:
        """Generate evaluation report"""
        return {
            "scenario_id": self.scenario["id"],
            "timestamp": timestamp,
            "cli_tool": self.cli_tool,
            "prompt": self.prompt,
            "plan_file": getattr(self, "plan_path_executed", "unknown"),
            "workspace": getattr(self, "test_workspace", "unknown"),
            "exit_code": getattr(self, "exit_code", -1),
            "kpis": {
                "K1_failed_tools": self.metrics["K1_failed_tools"],
                "K2_quality_reruns": self.metrics["K2_quality_reruns"],
                "K9_token_spend": self.metrics["K9_token_spend"],
                "K11_runtime_seconds": self.metrics["K11_runtime_seconds"],
            },
            "raw_data": self.metrics["raw_data"],
            "scenario": self.scenario,
        }

    def save_report(self, report: Dict[str, Any]) -> str:
        """Save report to disk"""
        report_path = Path(f"reports/run_{report['timestamp']}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        return str(report_path)

    def save_baseline(self, report: Dict[str, Any]):
        """Save report as baseline for comparison"""
        baseline_path = Path("reports/baseline.json")
        with open(baseline_path, "w") as f:
            json.dump(report, f, indent=2)

    def compare_with_baseline(self, current_report: Dict[str, Any]):
        """Compare current run with baseline"""
        baseline_path = Path("reports/baseline.json")

        if not baseline_path.exists():
            print("⚠️  No baseline found. Run with --save-baseline first.")
            return

        with open(baseline_path, "r") as f:
            baseline = json.load(f)

        # Check for configuration mismatch
        baseline_tool = baseline.get("cli_tool", "unknown")
        baseline_prompt = baseline.get("prompt", "unknown")

        print("\n" + "=" * 50)
        print("📊 EVALUATION RESULTS")
        print("=" * 50)
        print(f"CLI Tool: {current_report['cli_tool']}")
        print(f"Prompt: {current_report['prompt']}")
        print(f"Plan File: {current_report['plan_file']}")
        print(f"Workspace: {current_report['workspace']}")
        print(f"Scenario: {current_report['scenario_id']}")

        if (
            baseline_tool != current_report["cli_tool"]
            or baseline_prompt != current_report["prompt"]
        ):
            print("\n⚠️  Configuration mismatch:")
            print(f"   Baseline: {baseline_tool} {baseline_prompt}")
            print(
                f"   Current:  {current_report['cli_tool']} {current_report['prompt']}"
            )
            print("   Comparison may not be meaningful")

        print()

        current_kpis = current_report["kpis"]
        baseline_kpis = baseline["kpis"]

        improvements = 0
        regressions = 0

        for kpi_name in current_kpis:
            current_val = current_kpis[kpi_name]
            baseline_val = baseline_kpis.get(kpi_name, 0)

            if baseline_val == 0:
                change_pct = "N/A"
                status = "➖"
            else:
                change_pct = ((current_val - baseline_val) / baseline_val) * 100

                # For these KPIs, lower is better
                if kpi_name in [
                    "K1_failed_tools",
                    "K2_quality_reruns",
                    "K11_runtime_seconds",
                ]:
                    if change_pct < 0:
                        status = "✅"
                        improvements += 1
                    elif change_pct > 0:
                        status = "❌"
                        regressions += 1
                    else:
                        status = "➖"
                else:  # For token spend, depends on context but usually lower is better
                    if change_pct < 0:
                        status = "✅"
                        improvements += 1
                    elif change_pct > 0:
                        status = "❌"
                        regressions += 1
                    else:
                        status = "➖"

            print(
                f"{kpi_name}: {baseline_val} → {current_val} ({change_pct:+.1f}%) {status}"
            )

        print(f"\nOverall: {improvements} improvements, {regressions} regressions")

        # Save comparison report
        comparison = {
            "timestamp": current_report["timestamp"],
            "baseline_timestamp": baseline.get("timestamp", "unknown"),
            "improvements": improvements,
            "regressions": regressions,
            "kpi_comparisons": {},
        }

        for kpi_name in current_kpis:
            comparison["kpi_comparisons"][kpi_name] = {
                "baseline": baseline_kpis.get(kpi_name, 0),
                "current": current_kpis[kpi_name],
                "change_percent": change_pct
                if isinstance(change_pct, str)
                else f"{change_pct:+.1f}%",
            }

        comparison_path = f"reports/comparison_{current_report['timestamp']}.json"
        with open(comparison_path, "w") as f:
            json.dump(comparison, f, indent=2)

        print(f"📄 Detailed comparison saved to: {comparison_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CLI Tool Evaluation Harness")
    parser.add_argument("scenario", help="Path to scenario YAML file")
    parser.add_argument(
        "--cli-tool",
        default="claude",
        help="CLI tool to test (e.g., claude, gpt, etc.)",
    )
    parser.add_argument(
        "--prompt",
        default="/todo-orchestrate",
        help="Prompt/command to pass to the CLI tool",
    )
    parser.add_argument(
        "--flags",
        default=None,
        help="Additional CLI flags (use {workspace} and {plan_file} as tokens). If not specified, uses tool-specific defaults.",
    )
    parser.add_argument(
        "--save-baseline", action="store_true", help="Save results as baseline"
    )
    parser.add_argument("--compare", action="store_true", help="Compare with baseline")
    parser.add_argument(
        "--verbose", action="store_true", help="Show real-time CLI tool output"
    )

    args = parser.parse_args()

    evaluator = CLIEvaluator(
        args.scenario,
        cli_tool=args.cli_tool,
        prompt=args.prompt,
        flags=args.flags,
        verbose=args.verbose,
    )
    report = evaluator.run_test(save_baseline=args.save_baseline, compare=args.compare)

    # Always save the report
    report_path = evaluator.save_report(report)
    print(f"📄 Report saved to: {report_path}")


if __name__ == "__main__":
    main()
