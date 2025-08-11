#!/usr/bin/env python3
"""
CI Metrics Collection and Analysis
Collects, stores, and analyzes continuous improvement metrics.
Part of Claude Code Workflows.
"""

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

import psutil

# Add utils and framework to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))
sys.path.insert(0, str(script_dir / "continuous-improvement" / "framework"))

try:
    from output_formatter import AnalysisResult, ResultFormatter
    from tech_stack_detector import TechStackDetector
    from ci_framework import CIFramework, CIMetricType, CIPhase
except ImportError as e:
    print(f"Error importing dependencies: {e}", file=sys.stderr)
    sys.exit(1)


@dataclass
class BuildMetrics:
    """Build performance metrics."""

    build_time: float
    build_success: bool
    build_size_mb: Optional[float] = None
    dependencies_count: Optional[int] = None
    changed_files: Optional[int] = None


@dataclass
class TestMetrics:
    """Test execution metrics."""

    test_time: float
    tests_total: int
    tests_passed: int
    tests_failed: int
    coverage_percent: Optional[float] = None


@dataclass
class QualityMetrics:
    """Code quality metrics."""

    lint_errors: int
    lint_warnings: int
    type_errors: int
    complexity_score: Optional[float] = None
    maintainability_index: Optional[float] = None


@dataclass
class PerformanceMetrics:
    """System performance metrics during CI."""

    cpu_percent: float
    memory_mb: float
    disk_io_mb: Optional[float] = None
    network_io_mb: Optional[float] = None


class CIMetricsCollector:
    """Collect and analyze CI metrics for continuous improvement."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.ci_framework = CIFramework(project_root)
        self.tech_detector = TechStackDetector()

    def collect_build_metrics(
        self, correlation_id: Optional[str] = None
    ) -> BuildMetrics:
        """Collect build performance metrics."""
        start_time = time.time()
        build_success = False
        build_size_mb = None
        dependencies_count = None
        changed_files = None

        try:
            # Detect build command
            build_command = self._detect_build_command()
            if not build_command:
                raise ValueError("No build command detected")

            # Execute build and measure time
            result = subprocess.run(
                build_command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,
            )

            build_time = time.time() - start_time
            build_success = result.returncode == 0

            # Calculate build output size
            build_dirs = ["dist", "build", "target", ".next"]
            for build_dir in build_dirs:
                build_path = self.project_root / build_dir
                if build_path.exists():
                    build_size_mb = self._calculate_directory_size_mb(build_path)
                    break

            # Count dependencies
            dependencies_count = self._count_dependencies()

            # Count changed files (last 24 hours)
            changed_files = self._count_recent_changes()

        except Exception as e:
            build_time = time.time() - start_time
            print(f"Build metrics collection error: {e}", file=sys.stderr)

        metrics = BuildMetrics(
            build_time=build_time,
            build_success=build_success,
            build_size_mb=build_size_mb,
            dependencies_count=dependencies_count,
            changed_files=changed_files,
        )

        # Record in CI framework
        self.ci_framework.record_metric(
            CIMetricType.BUILD_TIME,
            CIPhase.IMPLEMENT,
            build_time,
            metadata=asdict(metrics),
            correlation_id=correlation_id,
            agent_source="ci-metrics-collector",
        )

        return metrics

    def collect_test_metrics(self, correlation_id: Optional[str] = None) -> TestMetrics:
        """Collect test execution metrics."""
        start_time = time.time()
        tests_total = 0
        tests_passed = 0
        tests_failed = 0
        coverage_percent = None

        try:
            # Detect test command
            test_command = self._detect_test_command()
            if not test_command:
                raise ValueError("No test command detected")

            # Execute tests with coverage if possible
            coverage_command = self._detect_coverage_command()
            if coverage_command:
                test_command = coverage_command

            result = subprocess.run(
                test_command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            test_time = time.time() - start_time

            # Parse test results from output
            test_stats = self._parse_test_output(result.stdout, result.stderr)
            tests_total = test_stats.get("total", 0)
            tests_passed = test_stats.get("passed", 0)
            tests_failed = test_stats.get("failed", 0)
            coverage_percent = test_stats.get("coverage")

        except Exception as e:
            test_time = time.time() - start_time
            print(f"Test metrics collection error: {e}", file=sys.stderr)

        metrics = TestMetrics(
            test_time=test_time,
            tests_total=tests_total,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            coverage_percent=coverage_percent,
        )

        # Record in CI framework
        success_rate = tests_passed / tests_total if tests_total > 0 else 0
        self.ci_framework.record_metric(
            CIMetricType.TEST_COVERAGE,
            CIPhase.VERIFY,
            success_rate,
            metadata=asdict(metrics),
            correlation_id=correlation_id,
            agent_source="ci-metrics-collector",
        )

        return metrics

    def collect_quality_metrics(
        self, correlation_id: Optional[str] = None
    ) -> QualityMetrics:
        """Collect code quality metrics."""
        lint_errors = 0
        lint_warnings = 0
        type_errors = 0
        complexity_score = None
        maintainability_index = None

        try:
            # Run linting
            lint_command = self._detect_lint_command()
            if lint_command:
                lint_result = subprocess.run(
                    lint_command,
                    shell=True,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                lint_stats = self._parse_lint_output(
                    lint_result.stdout, lint_result.stderr
                )
                lint_errors = lint_stats.get("errors", 0)
                lint_warnings = lint_stats.get("warnings", 0)

            # Run type checking
            typecheck_command = self._detect_typecheck_command()
            if typecheck_command:
                typecheck_result = subprocess.run(
                    typecheck_command,
                    shell=True,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )

                type_stats = self._parse_typecheck_output(
                    typecheck_result.stdout, typecheck_result.stderr
                )
                type_errors = type_stats.get("errors", 0)

            # Calculate complexity (basic implementation)
            complexity_score = self._calculate_complexity_score()

        except Exception as e:
            print(f"Quality metrics collection error: {e}", file=sys.stderr)

        metrics = QualityMetrics(
            lint_errors=lint_errors,
            lint_warnings=lint_warnings,
            type_errors=type_errors,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index,
        )

        # Record in CI framework
        quality_score = max(0, 1.0 - (lint_errors + type_errors) / 10.0)
        self.ci_framework.record_metric(
            CIMetricType.QUALITY_GATE,
            CIPhase.ANALYZE,
            quality_score,
            metadata=asdict(metrics),
            correlation_id=correlation_id,
            agent_source="ci-metrics-collector",
        )

        return metrics

    def collect_performance_metrics(
        self, duration_seconds: int = 60, correlation_id: Optional[str] = None
    ) -> PerformanceMetrics:
        """Collect system performance metrics during CI operations."""
        cpu_samples = []
        memory_samples = []

        start_time = time.time()

        try:
            # Collect samples over duration
            while time.time() - start_time < duration_seconds:
                cpu_samples.append(psutil.cpu_percent(interval=1))
                memory_info = psutil.virtual_memory()
                memory_samples.append(memory_info.used / 1024 / 1024)  # MB

                if len(cpu_samples) >= 10:  # Limit samples for quick collection
                    break

            cpu_percent = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
            memory_mb = (
                sum(memory_samples) / len(memory_samples) if memory_samples else 0
            )

        except Exception as e:
            print(f"Performance metrics collection error: {e}", file=sys.stderr)
            cpu_percent = 0
            memory_mb = 0

        metrics = PerformanceMetrics(cpu_percent=cpu_percent, memory_mb=memory_mb)

        # Record in CI framework
        self.ci_framework.record_metric(
            CIMetricType.PERFORMANCE,
            CIPhase.COLLECT,
            cpu_percent / 100.0,  # Normalize to 0-1
            metadata=asdict(metrics),
            correlation_id=correlation_id,
            agent_source="ci-metrics-collector",
        )

        return metrics

    def generate_comprehensive_report(
        self, include_history: bool = True, days_back: int = 7
    ) -> AnalysisResult:
        """Generate comprehensive CI metrics analysis report."""
        start_time = time.time()
        result = ResultFormatter.create_architecture_result(
            "ci_metrics_collector.py", str(self.project_root)
        )

        try:
            # Collect current metrics
            current_metrics = {
                "build": self.collect_build_metrics(),
                "test": self.collect_test_metrics(),
                "quality": self.collect_quality_metrics(),
                "performance": self.collect_performance_metrics(duration_seconds=10),
            }

            # Get historical data if requested
            historical_data = {}
            if include_history:
                since = datetime.now() - timedelta(days=days_back)
                for metric_type in CIMetricType:
                    historical_data[metric_type.value] = self.ci_framework.get_metrics(
                        metric_type=metric_type, since=since
                    )

            # Analyze trends
            trends = {}
            for metric_type in CIMetricType:
                trends[metric_type.value] = self.ci_framework.analyze_trends(
                    metric_type, days=days_back
                )

            # Generate findings for issues
            finding_id = 1

            # Build performance findings
            build_metrics = current_metrics["build"]
            if not build_metrics.build_success:
                finding = ResultFormatter.create_finding(
                    f"CI{finding_id:03d}",
                    "Build Failure",
                    "Current build is failing",
                    "high",
                    recommendation=(
                        "Investigate build errors and fix " "failing components"
                    ),
                    evidence={"build_metrics": asdict(build_metrics)},
                )
                result.add_finding(finding)
                finding_id += 1

            elif build_metrics.build_time > 300:  # > 5 minutes
                time_str = f"{build_metrics.build_time:.1f}s"
                finding = ResultFormatter.create_finding(
                    f"CI{finding_id:03d}",
                    "Slow Build Performance",
                    f"Build taking {time_str} (>5min threshold)",
                    "medium",
                    recommendation=(
                        "Optimize build process, consider "
                        "parallel builds or build caching"
                    ),
                    evidence={"build_metrics": asdict(build_metrics)},
                )
                result.add_finding(finding)
                finding_id += 1

            # Test coverage findings
            test_metrics = current_metrics["test"]
            if test_metrics.coverage_percent and test_metrics.coverage_percent < 70:
                coverage_str = f"{test_metrics.coverage_percent:.1f}%"
                finding = ResultFormatter.create_finding(
                    f"CI{finding_id:03d}",
                    "Low Test Coverage",
                    f"Test coverage at {coverage_str} (<70% threshold)",
                    "medium",
                    recommendation=(
                        "Increase test coverage by adding tests "
                        "for uncovered code paths"
                    ),
                    evidence={"test_metrics": asdict(test_metrics)},
                )
                result.add_finding(finding)
                finding_id += 1

            # Quality findings
            quality_metrics = current_metrics["quality"]
            total_issues = quality_metrics.lint_errors + quality_metrics.type_errors
            if total_issues > 10:
                finding = ResultFormatter.create_finding(
                    f"CI{finding_id:03d}",
                    "High Quality Issues",
                    f"{total_issues} lint/type errors detected",
                    "medium",
                    recommendation=(
                        "Address linting and type errors " "to improve code quality"
                    ),
                    evidence={"quality_metrics": asdict(quality_metrics)},
                )
                result.add_finding(finding)
                finding_id += 1

            # Add comprehensive metadata
            result.metadata = {
                "current_metrics": {k: asdict(v) for k, v in current_metrics.items()},
                "historical_metrics_count": sum(
                    len(metrics) for metrics in historical_data.values()
                ),
                "trend_analyses": trends,
                "collection_duration": days_back,
                "project_root": str(self.project_root),
            }

        except Exception as e:
            result.set_error(f"CI metrics analysis failed: {str(e)}")

        result.set_execution_time(start_time)
        return result

    def _detect_build_command(self) -> Optional[str]:
        """Detect appropriate build command."""
        if (self.project_root / "package.json").exists():
            return "npm run build"
        elif (self.project_root / "Cargo.toml").exists():
            return "cargo build"
        elif (self.project_root / "go.mod").exists():
            return "go build ./..."
        elif (self.project_root / "setup.py").exists():
            return "python setup.py build"
        return None

    def _detect_test_command(self) -> Optional[str]:
        """Detect appropriate test command."""
        if (self.project_root / "package.json").exists():
            return "npm test"
        elif any(self.project_root.glob("**/*test*.py")):
            return "pytest"
        elif (self.project_root / "Cargo.toml").exists():
            return "cargo test"
        elif (self.project_root / "go.mod").exists():
            return "go test ./..."
        return None

    def _detect_coverage_command(self) -> Optional[str]:
        """Detect coverage command."""
        if (self.project_root / "package.json").exists():
            return "npm run test -- --coverage"
        elif any(self.project_root.glob("**/*test*.py")):
            return "pytest --cov=."
        return None

    def _detect_lint_command(self) -> Optional[str]:
        """Detect lint command."""
        if (self.project_root / "package.json").exists():
            return "npm run lint"
        elif any(self.project_root.glob("**/*.py")):
            return "flake8 ."
        elif (self.project_root / "Cargo.toml").exists():
            return "cargo clippy"
        return None

    def _detect_typecheck_command(self) -> Optional[str]:
        """Detect typecheck command."""
        if (self.project_root / "tsconfig.json").exists():
            return "npx tsc --noEmit"
        elif (self.project_root / "mypy.ini").exists():
            return "mypy ."
        return None

    def _calculate_directory_size_mb(self, directory: Path) -> float:
        """Calculate directory size in MB."""
        total_size = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / 1024 / 1024

    def _count_dependencies(self) -> Optional[int]:
        """Count project dependencies."""
        if (self.project_root / "package.json").exists():
            try:
                with open(self.project_root / "package.json") as f:
                    package_data = json.load(f)
                    deps = len(package_data.get("dependencies", {}))
                    dev_deps = len(package_data.get("devDependencies", {}))
                    return deps + dev_deps
            except Exception:
                pass
        return None

    def _count_recent_changes(self) -> Optional[int]:
        """Count files changed in last 24 hours using git."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--since=24.hours.ago",
                    "--name-only",
                    "--pretty=format:",
                    "--",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                files = set(
                    line.strip() for line in result.stdout.split("\n") if line.strip()
                )
                return len(files)
        except Exception:
            pass
        return None

    def _parse_test_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse test output for metrics."""
        stats = {}

        # Simple patterns for common test frameworks
        output = stdout + stderr

        # Jest/npm test patterns
        if "tests passed" in output.lower():
            pattern = r"(\d+) passing"
            match = re.search(pattern, output)
            if match:
                stats["passed"] = int(match.group(1))
                stats["total"] = stats["passed"]

        # pytest patterns
        elif "passed" in output and "failed" in output:
            passed_match = re.search(r"(\d+) passed", output)
            failed_match = re.search(r"(\d+) failed", output)

            if passed_match:
                stats["passed"] = int(passed_match.group(1))
            if failed_match:
                stats["failed"] = int(failed_match.group(1))

            stats["total"] = stats.get("passed", 0) + stats.get("failed", 0)

        # Coverage patterns
        coverage_match = re.search(r"(\d+)%", output)
        if coverage_match:
            stats["coverage"] = float(coverage_match.group(1))

        return stats

    def _parse_lint_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse lint output for error/warning counts."""
        stats = {"errors": 0, "warnings": 0}

        output = stdout + stderr
        lines = output.lower().split("\n")

        for line in lines:
            if "error" in line and "warning" in line:
                # ESLint format: "2 errors, 3 warnings"
                error_match = re.search(r"(\d+)\s+error", line)
                warning_match = re.search(r"(\d+)\s+warning", line)

                if error_match:
                    stats["errors"] = int(error_match.group(1))
                if warning_match:
                    stats["warnings"] = int(warning_match.group(1))
                break

        return stats

    def _parse_typecheck_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse typecheck output for error counts."""
        stats = {"errors": 0}

        output = stdout + stderr

        # TypeScript: "Found N errors"
        error_match = re.search(r"Found (\d+) error", output)
        if error_match:
            stats["errors"] = int(error_match.group(1))
        else:
            # Count individual error lines
            error_lines = [
                line for line in output.split("\n") if "error" in line.lower()
            ]
            stats["errors"] = len(error_lines)

        return stats

    def _calculate_complexity_score(self) -> Optional[float]:
        """Calculate basic complexity score."""
        try:
            # Simple complexity based on file count and lines
            python_files = list(self.project_root.rglob("*.py"))
            js_files = list(self.project_root.rglob("*.js"))
            ts_files = list(self.project_root.rglob("*.ts"))
            code_files = python_files + js_files + ts_files

            if not code_files:
                return None

            total_lines = 0
            for file_path in code_files[:50]:  # Limit for performance
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        total_lines += len(f.readlines())
                except Exception:
                    continue

            # Simple complexity score: lines per file
            return total_lines / len(code_files) if code_files else None

        except Exception:
            return None


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CI Metrics Collector - Comprehensive Metrics Collection"
    )
    parser.add_argument(
        "command", choices=["build", "test", "quality", "performance", "report"]
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--correlation-id", help="Correlation ID for tracking")
    parser.add_argument("--output-format", choices=["json", "console"], default="json")
    parser.add_argument("--days", type=int, default=7, help="Historical analysis days")

    args = parser.parse_args()

    collector = CIMetricsCollector(args.project_root)

    if args.command == "build":
        metrics = collector.collect_build_metrics(args.correlation_id)
        print(json.dumps(asdict(metrics), indent=2))

    elif args.command == "test":
        metrics = collector.collect_test_metrics(args.correlation_id)
        print(json.dumps(asdict(metrics), indent=2))

    elif args.command == "quality":
        metrics = collector.collect_quality_metrics(args.correlation_id)
        print(json.dumps(asdict(metrics), indent=2))

    elif args.command == "performance":
        metrics = collector.collect_performance_metrics(
            duration_seconds=30, correlation_id=args.correlation_id
        )
        print(json.dumps(asdict(metrics), indent=2))

    elif args.command == "report":
        result = collector.generate_comprehensive_report(days_back=args.days)
        if args.output_format == "console":
            print(ResultFormatter.format_console_output(result))
        else:
            print(result.to_json())


if __name__ == "__main__":
    main()
