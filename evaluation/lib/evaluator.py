#!/usr/bin/env python3
"""
CLI Evaluator - Main Orchestrator

Clean, focused orchestrator that coordinates Docker, authentication,
execution, and metrics collection for CLI tool evaluation.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from .docker_manager import DockerManager
from .auth_manager import AuthManager
from .execution_engine import ExecutionEngine, CLIInstallationManager
from .metrics_parser import MetricsParser, ReportGenerator


class CLIEvaluator:
    """Main orchestrator for CLI tool evaluation."""

    def __init__(
        self,
        scenario_path: str,
        cli_tool: str,
        prompt: str = "/todo-orchestrate",
        auth_mode: str = "apikey",
        api_key: Optional[str] = None,
        tear_down: bool = False,
        verbose: bool = False,
    ):
        # Load scenario configuration
        self.scenario = self._load_scenario(scenario_path)
        self.cli_tool = cli_tool
        self.prompt = prompt
        self.auth_mode = auth_mode
        self.api_key = api_key
        self.tear_down = tear_down
        self.verbose = verbose

        # Initialize components
        self.docker_manager = DockerManager(cli_tool, self.scenario)
        self.auth_manager = AuthManager(cli_tool, self.docker_manager.container_name)
        self.execution_engine = ExecutionEngine(
            cli_tool, self.docker_manager, auth_mode
        )
        self.installation_manager = CLIInstallationManager(self.docker_manager)
        self.metrics_parser = MetricsParser()

    def _load_scenario(self, scenario_path: str) -> Dict[str, Any]:
        """Load scenario configuration from YAML file."""
        scenario_file = Path(scenario_path)
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

        with open(scenario_file, "r") as f:
            return yaml.safe_load(f)

    def run_test(
        self, save_baseline: bool = False, compare: bool = False
    ) -> Dict[str, Any]:
        """Execute complete CLI evaluation test."""
        print(f"🐳 CLI Evaluation System - {self.cli_tool.upper()}")
        print(f"📄 Scenario: {self.scenario['id']}")
        print("-" * 50)

        # Check Docker availability
        if not self.docker_manager.check_docker_available():
            raise RuntimeError("Docker is not available or not running")

        # Phase 1: Container Setup (NOT TIMED)
        self._setup_container()

        # Phase 2: CLI Installation (NOT TIMED)
        self._install_cli()

        # Phase 3: Authentication (NOT TIMED)
        self._handle_authentication()

        # Phase 4: Execute Test (TIMED)
        self._execute_test()

        # Phase 5: Parse Metrics & Generate Report
        report = self._generate_report()

        # Phase 6: Cleanup
        self._cleanup()

        # Handle baseline and comparison
        if save_baseline:
            self._save_baseline(report)

        if compare:
            comparison = ReportGenerator.compare_with_baseline(report)
            print("📊 Baseline Comparison:")
            self._display_comparison(comparison)

        print(f"📊 Test completed in {self.metrics_parser._calculate_runtime():.2f}s")
        print(f"🎯 Exit code: {self.metrics_parser.exit_code}")

        return report

    def _setup_container(self):
        """Set up Docker container."""
        if not self.docker_manager.ensure_container_ready(self.auth_mode):
            raise RuntimeError("Failed to set up Docker container")

    def _install_cli(self):
        """Install CLI tool if needed."""
        if not self.installation_manager.is_cli_installed(self.cli_tool):
            if not self.installation_manager.install_cli(
                self.cli_tool, self.auth_mode, self.api_key
            ):
                raise RuntimeError(f"Failed to install {self.cli_tool}")
        else:
            print(f"✅ {self.cli_tool} already installed")

    def _handle_authentication(self):
        """Handle authentication based on mode."""
        if not self.auth_manager.authenticate(self.auth_mode, self.api_key):
            raise RuntimeError(f"Authentication failed for {self.cli_tool}")

    def _execute_test(self):
        """Execute the timed test portion."""
        print("⚡ Starting timed execution...")

        self.metrics_parser.start_timing()

        try:
            result = self.execution_engine.execute_test(
                self.prompt, self.scenario, self.api_key, self.verbose
            )
            self.metrics_parser.set_exit_code(result.returncode)
            self.metrics_parser.raw_output = result.stdout + result.stderr

        finally:
            self.metrics_parser.end_timing()

        return result

    def _generate_report(self) -> Dict[str, Any]:
        """Generate evaluation report."""
        return self.metrics_parser.generate_report(
            scenario_id=self.scenario["id"],
            cli_tool=self.cli_tool,
            prompt=self.prompt,
            plan_file=self.scenario["plan_file"],
            container_name=self.docker_manager.container_name,
            docker_image=self.docker_manager.docker_image,
        )

    def _cleanup(self):
        """Clean up resources."""
        self.docker_manager.cleanup(self.tear_down)

    def _save_baseline(self, report: Dict[str, Any]):
        """Save report as baseline."""
        baseline_path = Path("reports/baseline.json")
        baseline_path.parent.mkdir(exist_ok=True)

        import json

        with open(baseline_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"💾 Baseline saved: {baseline_path}")

    def _display_comparison(self, comparison: Dict[str, Any]):
        """Display baseline comparison results."""
        if "error" in comparison:
            print(f"❌ Comparison failed: {comparison['error']}")
            return

        comp_data = comparison.get("comparison", {})
        for kpi, data in comp_data.items():
            current = data["current"]
            baseline = data["baseline"]
            change = data["change"]
            change_pct = data["change_percent"]

            if change == 0:
                status = "→"
            elif change > 0:
                status = (
                    "↑" if "failure" in kpi.lower() or "error" in kpi.lower() else "↗"
                )
            else:
                status = (
                    "↓" if "failure" in kpi.lower() or "error" in kpi.lower() else "↘"
                )

            print(
                f"  {kpi}: {current} {status} {baseline} ({change:+.1f}, {change_pct:+.1f}%)"
            )


# Utility functions for backward compatibility during migration
def validate_environment():
    """Validate evaluation environment."""
    import subprocess

    issues = []

    # Check Docker
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
        docker_available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        docker_available = False

    if not docker_available:
        issues.append("Docker not available")

    # Check directories
    if not Path("scenarios").exists():
        issues.append("scenarios/ directory not found")

    if not Path("cli_installers").exists():
        issues.append("cli_installers/ directory not found")

    return issues, docker_available
