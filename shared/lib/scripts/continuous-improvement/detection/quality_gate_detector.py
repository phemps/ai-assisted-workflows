#!/usr/bin/env python3
"""
Quality Gate Detection for Continuous Improvement
Integrates with quality-monitor agent for dynamic quality gate detection.
Part of Claude Code Workflows.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add utils and framework to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))
sys.path.insert(0, str(script_dir / "continuous-improvement" / "framework"))

try:
    from tech_stack_detector import TechStackDetector
    from ci_framework import CIFramework, CIMetricType, CIPhase
except ImportError as e:
    print(f"Error importing dependencies: {e}", file=sys.stderr)
    sys.exit(1)


class QualityGateStatus(Enum):
    """Quality gate execution status."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    NOT_AVAILABLE = "not_available"


class QualityGateDetector:
    """Detect and execute quality gates for CI integration."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.tech_detector = TechStackDetector()
        self.ci_framework = CIFramework(project_root)

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

        return {
            "detected_gates": available_gates,
            "total_available": len(available_gates),
            "tech_stack": self._get_detected_tech_stack(),
            "detection_timestamp": datetime.now().isoformat(),
        }

    def execute_quality_gates(
        self, mode: str = "production", correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute quality gates based on mode (production/prototype)."""
        start_time = time.time()

        # Detect available gates
        detection_result = self.detect_available_gates()
        available_gates = detection_result["detected_gates"]

        # Define gate execution order and mode requirements
        gate_order = ["lint", "typecheck", "build", "test", "coverage", "security"]
        # Prototype mode gates
        prototype_gates = {"lint", "typecheck", "build"}

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

            # Skip non-essential gates in prototype mode
            if mode == "prototype" and gate_name not in prototype_gates:
                execution_results[gate_name] = {
                    "status": QualityGateStatus.SKIPPED.value,
                    "message": "Skipped in prototype mode",
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

            # Record metrics
            gate_success = gate_result["status"] == QualityGateStatus.PASSED.value
            self.ci_framework.record_metric(
                CIMetricType.QUALITY_GATE,
                CIPhase.VERIFY,
                1.0 if gate_success else 0.0,
                metadata={
                    "gate_name": gate_name,
                    "status": gate_result["status"],
                    "execution_time": gate_result["execution_time"],
                    "mode": mode,
                },
                correlation_id=correlation_id,
                agent_source="quality-monitor",
            )

        # Check for runtime errors in logs
        log_check_result = self._check_runtime_errors()
        execution_results["runtime_logs"] = log_check_result

        if log_check_result["has_errors"]:
            overall_status = QualityGateStatus.FAILED

        total_execution_time = time.time() - start_time

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

        return {
            "overall_status": overall_status.value,
            "mode": mode,
            "gates_executed": len(not_skipped),
            "gates_passed": len(passed_gates),
            "gates_failed": len(failed_gates),
            "execution_time": round(total_execution_time, 3),
            "results": execution_results,
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _execute_single_gate(
        self, gate_name: str, gate_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single quality gate."""
        start_time = time.time()

        try:
            command = gate_config["command"]
            timeout = gate_config.get("timeout", 300)  # 5 minute default

            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                status = QualityGateStatus.PASSED
                message = f"{gate_name} passed successfully"
            else:
                status = QualityGateStatus.FAILED
                message = f"{gate_name} failed with exit code " f"{result.returncode}"

            # Truncate output
            stdout = result.stdout[:1000] if result.stdout else ""
            stderr = result.stderr[:1000] if result.stderr else ""

            return {
                "status": status.value,
                "message": message,
                "execution_time": round(execution_time, 3),
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
                "execution_time": timeout,
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
                "execution_time": time.time() - start_time,
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
        if (self.project_root / "package.json").exists():
            package_json_path = self.project_root / "package.json"
            try:
                with open(package_json_path) as f:
                    package_data = json.load(f)
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
            "alternatives": (build_commands[1:] if len(build_commands) > 1 else []),
            "timeout": 600,  # 10 minutes for builds
        }

    def _detect_test_commands(self) -> Dict[str, Any]:
        """Detect test commands for different tech stacks."""
        test_commands = []

        # Node.js projects
        if (self.project_root / "package.json").exists():
            try:
                with open(self.project_root / "package.json") as f:
                    package_data = json.load(f)
                    scripts = package_data.get("scripts", {})

                if "test" in scripts:
                    test_commands.append("npm test")
                elif "test:unit" in scripts:
                    test_commands.append("npm run test:unit")
            except Exception:
                pass

        # Python projects
        pytest_indicators = [
            (self.project_root / "pytest.ini").exists(),
            any(self.project_root.glob("test*.py")),
            any(self.project_root.glob("**/test_*.py")),
        ]

        if pytest_indicators[0] or pytest_indicators[1]:
            test_commands.append("pytest")
        elif pytest_indicators[2]:
            test_commands.append("python -m pytest")

        # Rust projects
        if (self.project_root / "Cargo.toml").exists():
            test_commands.append("cargo test")

        # Go projects
        if (self.project_root / "go.mod").exists():
            test_commands.append("go test ./...")

        return {
            "available": len(test_commands) > 0,
            "command": test_commands[0] if test_commands else None,
            "alternatives": (test_commands[1:] if len(test_commands) > 1 else []),
            "timeout": 300,
        }

    def _detect_lint_commands(self) -> Dict[str, Any]:
        """Detect lint commands for different tech stacks."""
        lint_commands = []

        # Node.js projects
        if (self.project_root / "package.json").exists():
            try:
                with open(self.project_root / "package.json") as f:
                    package_data = json.load(f)
                    scripts = package_data.get("scripts", {})

                if "lint" in scripts:
                    lint_commands.append("npm run lint")
                elif "eslint" in scripts:
                    lint_commands.append("npm run eslint")
            except Exception:
                pass

        # Python projects
        python_lint_indicators = [
            (self.project_root / ".flake8").exists(),
            (self.project_root / "setup.cfg").exists(),
            any(self.project_root.glob("**/*.py")),
        ]

        if python_lint_indicators[0] or python_lint_indicators[1]:
            lint_commands.append("flake8 .")
        elif python_lint_indicators[2]:
            lint_commands.append("python -m flake8 .")

        # Rust projects
        if (self.project_root / "Cargo.toml").exists():
            lint_commands.append("cargo clippy")

        return {
            "available": len(lint_commands) > 0,
            "command": lint_commands[0] if lint_commands else None,
            "alternatives": (lint_commands[1:] if len(lint_commands) > 1 else []),
            "timeout": 120,
        }

    def _detect_typecheck_commands(self) -> Dict[str, Any]:
        """Detect type checking commands."""
        typecheck_commands = []

        # TypeScript projects
        if (self.project_root / "tsconfig.json").exists():
            if (self.project_root / "package.json").exists():
                try:
                    with open(self.project_root / "package.json") as f:
                        package_data = json.load(f)
                        scripts = package_data.get("scripts", {})

                    if "typecheck" in scripts:
                        typecheck_commands.append("npm run typecheck")
                    elif "type-check" in scripts:
                        typecheck_commands.append("npm run type-check")
                    else:
                        typecheck_commands.append("npx tsc --noEmit")
                except Exception:
                    typecheck_commands.append("npx tsc --noEmit")
            else:
                typecheck_commands.append("npx tsc --noEmit")

        # Python with mypy
        python_has_files = any(self.project_root.glob("**/*.py"))
        mypy_config_exists = (self.project_root / "mypy.ini").exists()
        if python_has_files and mypy_config_exists:
            typecheck_commands.append("mypy .")

        return {
            "available": len(typecheck_commands) > 0,
            "command": typecheck_commands[0] if typecheck_commands else None,
            "alternatives": (
                typecheck_commands[1:] if len(typecheck_commands) > 1 else []
            ),
            "timeout": 180,
        }

    def _detect_security_commands(self) -> Dict[str, Any]:
        """Detect security scanning commands."""
        security_commands = []

        # Node.js projects
        if (self.project_root / "package.json").exists():
            security_commands.append("npm audit")

        # Python projects
        if any(self.project_root.glob("**/*.py")):
            security_commands.append("bandit -r .")

        return {
            "available": len(security_commands) > 0,
            "command": security_commands[0] if security_commands else None,
            "alternatives": (
                security_commands[1:] if len(security_commands) > 1 else []
            ),
            "timeout": 120,
        }

    def _detect_coverage_commands(self) -> Dict[str, Any]:
        """Detect test coverage commands."""
        coverage_commands = []

        # Node.js projects
        if (self.project_root / "package.json").exists():
            try:
                with open(self.project_root / "package.json") as f:
                    package_data = json.load(f)
                    scripts = package_data.get("scripts", {})

                if "test:coverage" in scripts:
                    coverage_commands.append("npm run test:coverage")
                elif "coverage" in scripts:
                    coverage_commands.append("npm run coverage")
            except Exception:
                pass

        # Python projects
        if any(self.project_root.glob("**/*.py")):
            coverage_commands.append("pytest --cov=.")

        return {
            "available": len(coverage_commands) > 0,
            "command": coverage_commands[0] if coverage_commands else None,
            "alternatives": (
                coverage_commands[1:] if len(coverage_commands) > 1 else []
            ),
            "timeout": 300,
        }

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
                    with open(log_file, "r") as f:
                        # Check last 100 lines
                        lines = f.readlines()[-100:]

                    error_keywords = ["error:", "exception:", "traceback", "fatal:"]
                    for i, line in enumerate(lines):
                        line_has_error = any(
                            keyword in line.lower() for keyword in error_keywords
                        )
                        if line_has_error:
                            # Truncate long messages
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
        stack = []

        if (self.project_root / "package.json").exists():
            stack.append("nodejs")
        if any(self.project_root.glob("**/*.py")):
            stack.append("python")
        if (self.project_root / "Cargo.toml").exists():
            stack.append("rust")
        if (self.project_root / "go.mod").exists():
            stack.append("go")
        if (self.project_root / "tsconfig.json").exists():
            stack.append("typescript")

        return stack


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Quality Gate Detection for CI Integration"
    )
    parser.add_argument("command", choices=["detect", "execute", "check-logs"])
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument(
        "--mode", choices=["production", "prototype"], default="production"
    )
    parser.add_argument("--correlation-id", help="Correlation ID for tracking")

    args = parser.parse_args()

    detector = QualityGateDetector(args.project_root)

    if args.command == "detect":
        result = detector.detect_available_gates()
        print("Available Quality Gates:")
        print(json.dumps(result, indent=2))

    elif args.command == "execute":
        result = detector.execute_quality_gates(
            mode=args.mode, correlation_id=args.correlation_id
        )
        print("Quality Gate Execution Results:")
        print(json.dumps(result, indent=2))

    elif args.command == "check-logs":
        result = detector._check_runtime_errors()
        print("Runtime Error Check:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
