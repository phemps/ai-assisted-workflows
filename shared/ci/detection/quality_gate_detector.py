#!/usr/bin/env python3
"""
Quality Gate Detector for Continuous Improvement Framework (REFACTORED)

This is a refactored version demonstrating the use of new base utilities
to eliminate code duplication patterns. Part of AI-Assisted Workflows.
"""

import subprocess
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Setup import paths and import base utilities
try:
    from utils import path_resolver  # noqa: F401
    from core.base.module_base import CIAnalysisModule
    from core.base.config_factory import ConfigFactory, QualityGateConfig
    from core.base.timing_utils import timed_operation, time_operation
    from core.base.cli_utils import create_standard_cli, run_cli_tool
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class QualityGateStatus(Enum):
    """Quality gate execution status."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    NOT_AVAILABLE = "not_available"


class QualityGateDetector(CIAnalysisModule):
    """Quality Gate Detector using base utilities to eliminate duplication."""

    def __init__(self, project_root: str = "."):
        super().__init__("quality_gate_detector", project_root)

        # Load configuration using base utilities
        self.config = self._load_quality_gate_config()

        # Setup tech stack detection using base class functionality
        self.tech_detector = self.TechStackDetector()

    def _load_quality_gate_config(self) -> QualityGateConfig:
        """Load quality gate configuration using config factory."""
        try:
            return ConfigFactory.create_from_file(
                "quality_gate", self.get_config_path("quality_gate_config.json")
            )
        except Exception:
            # Create default config if none exists
            config = ConfigFactory.create("quality_gate")
            self.save_config("quality_gate_config.json", config.to_dict())
            return config

    @timed_operation("detect_available_gates")
    def detect_available_gates(self) -> Dict[str, Any]:
        """Detect available quality gates in the project."""
        gates = {
            "build": self._detect_build_commands(),
            "test": self._detect_test_commands(),
            "lint": self._detect_lint_commands(),
            "typecheck": self._detect_typecheck_commands(),
            "security": self._detect_security_commands(),
            "coverage": self._detect_coverage_commands(),
        }

        # Filter out unavailable gates
        available_gates = {
            name: config for name, config in gates.items() if config["available"]
        }

        self.log_operation("gates_detected", {"total_available": len(available_gates)})

        return {
            "detected_gates": available_gates,
            "total_available": len(available_gates),
            "tech_stack": self._get_detected_tech_stack(),
            "detection_timestamp": datetime.now().isoformat(),
        }

    def execute_quality_gates(
        self, mode: str = "production", correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute quality gates with performance tracking."""

        # Start analysis timing
        self.start_analysis()

        with time_operation("quality_gate_execution") as timing:
            # Detect available gates
            detection_result = self.detect_available_gates()
            available_gates = detection_result["detected_gates"]

            # Define gate execution order and mode requirements
            gate_order = ["lint", "typecheck", "build", "test", "coverage", "security"]

            # Use configuration for mode gates
            if mode == "prototype":
                required_gates = set(self.config.prototype_mode_gates)
            else:
                required_gates = set(self.config.production_mode_gates)

            execution_results = {}
            overall_status = QualityGateStatus.PASSED

            for gate_name in gate_order:
                if gate_name not in available_gates:
                    execution_results[gate_name] = {
                        "status": QualityGateStatus.NOT_AVAILABLE.value,
                        "message": f"{gate_name} gate not available in project",
                        "execution_time": 0,
                        "skipped": True,
                    }
                    continue

                # Skip non-required gates in current mode
                if gate_name not in required_gates:
                    execution_results[gate_name] = {
                        "status": QualityGateStatus.SKIPPED.value,
                        "message": f"Skipped in {mode} mode",
                        "execution_time": 0,
                        "skipped": True,
                    }
                    continue

                # Execute the gate
                gate_config = available_gates[gate_name]
                gate_result = self._execute_single_gate(gate_name, gate_config)
                execution_results[gate_name] = gate_result

                # Track overall status
                if gate_result["status"] == QualityGateStatus.FAILED.value:
                    overall_status = QualityGateStatus.FAILED
                elif (
                    gate_result["status"] == QualityGateStatus.ERROR.value
                    and overall_status != QualityGateStatus.FAILED
                ):
                    overall_status = QualityGateStatus.ERROR

            # Check for runtime errors in logs
            log_check_result = self._check_runtime_errors()
            execution_results["runtime_logs"] = log_check_result

            if log_check_result["has_errors"]:
                overall_status = QualityGateStatus.FAILED

            timing.metadata.update(
                {
                    "mode": mode,
                    "gates_executed": len(
                        [
                            r
                            for r in execution_results.values()
                            if not r.get("skipped", False)
                        ]
                    ),
                    "overall_status": overall_status.value,
                }
            )

        # Calculate summary statistics
        not_skipped = [
            r for r in execution_results.values() if not r.get("skipped", False)
        ]
        passed_gates = [
            r
            for r in execution_results.values()
            if r["status"] == QualityGateStatus.PASSED.value
        ]
        failed_gates = [
            r
            for r in execution_results.values()
            if r["status"] == QualityGateStatus.FAILED.value
        ]

        result = {
            "overall_status": overall_status.value,
            "mode": mode,
            "gates_executed": len(not_skipped),
            "gates_passed": len(passed_gates),
            "gates_failed": len(failed_gates),
            "execution_time": timing.duration_seconds if timing else 0,
            "results": execution_results,
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
        }

        self.log_operation(
            "quality_gates_executed",
            {
                "status": overall_status.value,
                "passed": len(passed_gates),
                "failed": len(failed_gates),
            },
        )

        return result

    @timed_operation("execute_single_gate")
    def _execute_single_gate(
        self, gate_name: str, gate_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single quality gate with timeout handling."""

        try:
            command = gate_config["command"]
            timeout = gate_config.get("timeout", self.config.timeout_seconds)

            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                status = QualityGateStatus.PASSED
                message = f"{gate_name} passed successfully"
            else:
                status = QualityGateStatus.FAILED
                message = f"{gate_name} failed with exit code {result.returncode}"

            # Truncate output using configuration
            max_lines = self.config.truncate_output_lines
            stdout = (
                "\n".join(result.stdout.split("\n")[:max_lines])
                if result.stdout
                else ""
            )
            stderr = (
                "\n".join(result.stderr.split("\n")[:max_lines])
                if result.stderr
                else ""
            )

            return {
                "status": status.value,
                "message": message,
                "exit_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "command": command,
                "skipped": False,
            }

        except subprocess.TimeoutExpired:
            return {
                "status": QualityGateStatus.ERROR.value,
                "message": f"{gate_name} timed out after {timeout}s",
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": command,
                "skipped": False,
            }
        except Exception as e:
            return {
                "status": QualityGateStatus.ERROR.value,
                "message": f"{gate_name} execution error: {str(e)}",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command,
                "skipped": False,
            }

    def _detect_build_commands(self) -> Dict[str, Any]:
        """Detect build commands for different tech stacks."""
        build_commands = []

        # Node.js/npm projects
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                import json

                content = self.safe_file_read(package_json)
                package_data = json.loads(content)
                scripts = package_data.get("scripts", {})

                if "build" in scripts:
                    build_commands.append("npm run build")
                elif "compile" in scripts:
                    build_commands.append("npm run compile")
            except Exception:
                pass

        # Python projects
        python_project_files = [
            self.project_root / "setup.py",
            self.project_root / "pyproject.toml",
        ]
        if any(f.exists() for f in python_project_files):
            build_commands.append("python -m py_compile .")

        # Rust projects
        if (self.project_root / "Cargo.toml").exists():
            build_commands.append("cargo build")

        # Go projects
        if (self.project_root / "go.mod").exists():
            build_commands.append("go build ./...")

        return {
            "available": len(build_commands) > 0,
            "command": build_commands[0] if build_commands else None,
            "alternatives": build_commands[1:] if len(build_commands) > 1 else [],
            "timeout": 600,  # 10 minutes for builds
        }

    def _detect_test_commands(self) -> Dict[str, Any]:
        """Detect test commands for different tech stacks."""
        test_commands = []

        # Node.js projects
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                import json

                content = self.safe_file_read(package_json)
                package_data = json.loads(content)
                scripts = package_data.get("scripts", {})

                if "test" in scripts:
                    test_commands.append("npm test")
                elif "test:unit" in scripts:
                    test_commands.append("npm run test:unit")
            except Exception:
                pass

        # Python projects (simplified detection)
        if (self.project_root / "pytest.ini").exists():
            test_commands.append("pytest")
        elif any(self.project_root.glob("test*.py")):
            test_commands.append("python -m pytest")

        return {
            "available": len(test_commands) > 0,
            "command": test_commands[0] if test_commands else None,
            "alternatives": test_commands[1:] if len(test_commands) > 1 else [],
            "timeout": self.config.timeout_seconds,
        }

    def _detect_lint_commands(self) -> Dict[str, Any]:
        """Detect lint commands for different tech stacks."""
        # Simplified implementation - full version would be similar to original
        return {"available": False, "command": None, "alternatives": [], "timeout": 120}

    def _detect_typecheck_commands(self) -> Dict[str, Any]:
        """Detect typecheck commands."""
        # Simplified implementation - full version would be similar to original
        return {"available": False, "command": None, "alternatives": [], "timeout": 180}

    def _detect_security_commands(self) -> Dict[str, Any]:
        """Detect security scanning commands."""
        # Simplified implementation - full version would be similar to original
        return {"available": False, "command": None, "alternatives": [], "timeout": 120}

    def _detect_coverage_commands(self) -> Dict[str, Any]:
        """Detect test coverage commands."""
        # Simplified implementation - full version would be similar to original
        return {"available": False, "command": None, "alternatives": [], "timeout": 300}

    def _check_runtime_errors(self) -> Dict[str, Any]:
        """Check for runtime errors in development logs."""
        log_files = [
            self.project_root / "dev.log",
            self.project_root / ".claude" / "dev.log",
            self.project_root / "logs" / "development.log",
        ]

        errors_found = []

        for log_file in log_files:
            if log_file.exists():
                try:
                    content = self.safe_file_read(log_file)
                    lines = content.split("\n")[-100:]  # Last 100 lines

                    error_keywords = ["error:", "exception:", "traceback", "fatal:"]
                    for i, line in enumerate(lines):
                        line_has_error = any(
                            keyword in line.lower() for keyword in error_keywords
                        )
                        if line_has_error:
                            message = line.strip()[:200]
                            errors_found.append(
                                {
                                    "file": str(log_file),
                                    "line_number": len(lines) - i,
                                    "message": message,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                except Exception:
                    pass

        return {
            "has_errors": len(errors_found) > 0,
            "error_count": len(errors_found),
            "errors": errors_found[:10],  # Limit to 10 most recent
            "log_files_checked": [str(f) for f in log_files if f.exists()],
        }

    def _get_detected_tech_stack(self) -> List[str]:
        """Get detected tech stack information."""
        return self.tech_detector.detect_tech_stack(str(self.project_root))


def main():
    """CLI interface using base utilities."""
    cli = create_standard_cli(
        "quality-gate-detector",
        "Detect and execute quality gates for CI integration",
        version="2.0.0",
        add_execution_args=True,
    )

    cli.parser.add_argument(
        "command",
        choices=["detect", "execute", "check-logs"],
        help="Command to execute",
    )

    cli.parser.add_argument(
        "--mode",
        choices=["production", "prototype"],
        default="production",
        help="Execution mode (default: production)",
    )

    cli.parser.add_argument("--correlation-id", help="Correlation ID for tracking")

    def main_function(args):
        detector = QualityGateDetector(str(args.project_root))

        if args.command == "detect":
            return detector.detect_available_gates()

        elif args.command == "execute":
            return detector.execute_quality_gates(
                mode=args.mode, correlation_id=args.correlation_id
            )

        elif args.command == "check-logs":
            return detector._check_runtime_errors()

    return run_cli_tool(cli, main_function)


if __name__ == "__main__":
    exit(main())
