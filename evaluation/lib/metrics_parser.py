#!/usr/bin/env python3
"""
Metrics Parser for CLI Evaluation System

Extracts KPIs and performance metrics from CLI tool output.
"""

import re
import time
from typing import Dict, Any, List
from datetime import datetime


class MetricsParser:
    """Parses CLI output to extract key performance indicators."""

    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0
        self.exit_code: int = 0
        self.raw_output: str = ""
        self.raw_data: Dict[str, List[str]] = {
            "failed_tools": [],
            "quality_reruns": [],
            "api_failures": [],
            "retries": [],
            "rate_limits": [],
            "errors": [],
            "agent_invocations": [],
            "state_transitions": [],
        }

    def start_timing(self):
        """Start the execution timer."""
        self.start_time = time.time()

    def end_timing(self):
        """End the execution timer."""
        self.end_time = time.time()

    def set_exit_code(self, exit_code: int):
        """Set the process exit code."""
        self.exit_code = exit_code

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse CLI output and extract all KPIs."""
        self.raw_output = output
        self._extract_raw_data()

        return {
            "K1_failed_tools": self._count_failed_tools(),
            "K2_quality_reruns": self._count_quality_reruns(),
            "K3_agent_invocations": self._count_agent_invocations(),
            "K4_state_transitions": self._count_state_transitions(),
            "K9_token_spend": self._extract_token_spend(),
            "K11_runtime_seconds": self._calculate_runtime(),
            "K12_api_retry_attempts": self._count_api_retries(),
            "K13_rate_limit_events": self._count_rate_limits(),
            "K14_api_failure_rate": self._calculate_api_failure_rate(),
        }

    def _extract_raw_data(self):
        """Extract raw data using regex patterns."""
        # K1: Failed tool calls
        failed_tool_patterns = [
            r"Tool call failed: (.+)",
            r"Error executing tool: (.+)",
            r"Failed to run (.+)",
            r"Command not found: (.+)",
            r"Tool (.+) returned error",
            r"Execution failed for (.+)",
        ]
        self._extract_patterns(failed_tool_patterns, "failed_tools")

        # K2: Quality gate reruns
        quality_rerun_patterns = [
            r"Quality gate failed, retrying",
            r"Rerunning due to quality issues",
            r"Quality check failed: (.+)",
            r"Retrying quality gate",
            r"Quality gate rerun: (.+)",
            r"Linting failed, retrying",
        ]
        self._extract_patterns(quality_rerun_patterns, "quality_reruns")

        # K12: API retry attempts
        api_retry_patterns = [
            r"Attempt (\d+) failed",
            r"Retrying in (\d+)s",
            r"Retrying with backoff",
            r"API retry attempt (\d+)",
            r"Retrying after (\d+) seconds",
            r"Backoff retry: (\d+)",
            r"Exponential backoff",
            r"Retry attempt (\d+) of (\d+)",
        ]
        self._extract_patterns(api_retry_patterns, "retries")

        # K13: Rate limit events
        rate_limit_patterns = [
            r"rate limit",
            r"429",
            r"quota exceeded",
            r"too many requests",
            r"Rate limited",
            r"API quota",
            r"Request limit exceeded",
            r"Throttled",
        ]
        self._extract_patterns(rate_limit_patterns, "rate_limits")

        # K14: API failure patterns
        api_failure_patterns = [
            r"API Error: (\d+)",
            r"HTTP (\d+)",
            r"401",
            r"403",
            r"500",
            r"502",
            r"503",
            r"504",
            r"connection failed",
            r"API request failed",
            r"Server error",
            r"Gateway timeout",
            r"Service unavailable",
        ]
        self._extract_patterns(api_failure_patterns, "api_failures")

        # General error patterns
        error_patterns = [
            r"Error: (.+)",
            r"Exception: (.+)",
            r"Failed: (.+)",
            r"FAILED (.+)",
            r"❌ (.+)",
        ]
        self._extract_patterns(error_patterns, "errors")

        # K3: Agent invocation patterns
        agent_patterns = [
            r"@agent-(\w+)",
            r"Invoking agent: (\w+)",
            r"Agent (\w+) invoked",
            r"Using (\w+-agent)",
            r"Delegating to (\w+) agent",
            r"Task assigned to (\w+)",
        ]
        self._extract_patterns(agent_patterns, "agent_invocations")

        # K4: State transition patterns
        state_transition_patterns = [
            r"State transition: (\w+) -> (\w+)",
            r"Moving from (\w+) to (\w+)",
            r"Phase: (\w+) -> (\w+)",
            r"(\w+) -> (\w+)",  # Generic transition format
            r"Status: (\w+) → (\w+)",  # Unicode arrow
            r"(\w+)\s*→\s*(\w+)",  # Space-separated transitions
        ]
        self._extract_patterns(state_transition_patterns, "state_transitions")

    def _extract_patterns(self, patterns: List[str], category: str):
        """Extract matches for a category of patterns."""
        for pattern in patterns:
            matches = re.findall(pattern, self.raw_output, re.IGNORECASE)
            self.raw_data[category].extend(matches)

    def _count_failed_tools(self) -> int:
        """Count K1: Failed tool calls."""
        return len(self.raw_data["failed_tools"])

    def _count_quality_reruns(self) -> int:
        """Count K2: Quality gate reruns."""
        return len(self.raw_data["quality_reruns"])

    def _count_agent_invocations(self) -> int:
        """Count K3: Agent invocations."""
        return len(self.raw_data["agent_invocations"])

    def _count_state_transitions(self) -> int:
        """Count K4: State transitions."""
        return len(self.raw_data["state_transitions"])

    def _extract_token_spend(self) -> int:
        """Extract K9: Token spend from output."""
        token_patterns = [
            r"Tokens used: (\d+)",
            r"Token count: (\d+)",
            r"Total tokens: (\d+)",
            r"(\d+) tokens",
            r"Spent (\d+) tokens",
            r"Token usage: (\d+)",
        ]

        total_tokens = 0
        for pattern in token_patterns:
            matches = re.findall(pattern, self.raw_output, re.IGNORECASE)
            for match in matches:
                try:
                    total_tokens += int(match)
                except ValueError:
                    continue

        return total_tokens

    def _calculate_runtime(self) -> float:
        """Calculate K11: Runtime in seconds."""
        if self.end_time > 0 and self.start_time > 0:
            return round(self.end_time - self.start_time, 2)
        return 0.0

    def _count_api_retries(self) -> int:
        """Count K12: API retry attempts."""
        return len(self.raw_data["retries"])

    def _count_rate_limits(self) -> int:
        """Count K13: Rate limit events."""
        return len(self.raw_data["rate_limits"])

    def _calculate_api_failure_rate(self) -> float:
        """Calculate K14: API failure rate percentage."""
        failures = len(self.raw_data["api_failures"])

        # Estimate total API calls (failures + successful calls)
        # Look for success indicators
        success_patterns = [
            r"200",
            r"✅",
            r"Success",
            r"Completed",
            r"OK",
        ]

        total_successes = 0
        for pattern in success_patterns:
            matches = re.findall(pattern, self.raw_output, re.IGNORECASE)
            total_successes += len(matches)

        total_calls = failures + total_successes

        if total_calls == 0:
            return 0.0

        failure_rate = (failures / total_calls) * 100
        return round(failure_rate, 2)

    def generate_report(
        self,
        scenario_id: str,
        cli_tool: str,
        prompt: str,
        plan_file: str,
        container_name: str,
        docker_image: str,
    ) -> Dict[str, Any]:
        """Generate complete evaluation report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics = self.parse_output(self.raw_output)

        return {
            "scenario_id": scenario_id,
            "timestamp": timestamp,
            "cli_tool": cli_tool,
            "prompt": prompt,
            "plan_file": plan_file,
            "container_name": container_name,
            "docker_image": docker_image,
            "exit_code": self.exit_code,
            "kpis": metrics,
            "raw_data": self.raw_data,
        }

    def get_raw_data(self) -> Dict[str, List[str]]:
        """Get raw extracted data for debugging."""
        return self.raw_data

    def reset(self):
        """Reset parser state for new test."""
        self.start_time = 0
        self.end_time = 0
        self.exit_code = 0
        self.raw_output = ""
        self.raw_data = {
            "failed_tools": [],
            "quality_reruns": [],
            "api_failures": [],
            "retries": [],
            "rate_limits": [],
            "errors": [],
            "agent_invocations": [],
            "state_transitions": [],
        }


class ReportGenerator:
    """Generates evaluation reports and comparisons."""

    @staticmethod
    def generate_markdown_summary(report: Dict[str, Any]) -> str:
        """Generate a markdown summary of the evaluation."""
        scenario_id = report.get("scenario_id", "Unknown")
        cli_tool = report.get("cli_tool", "Unknown")
        kpis = report.get("kpis", {})
        raw_data = report.get("raw_data", {})

        # Extract detailed data for analysis
        agent_invocations = raw_data.get("agent_invocations", [])
        state_transitions = raw_data.get("state_transitions", [])
        unique_agents = set(agent_invocations) if agent_invocations else set()

        md = f"""# Evaluation Report: {scenario_id}

## Test Configuration
- **CLI Tool**: {cli_tool}
- **Timestamp**: {report.get('timestamp', 'Unknown')}
- **Exit Code**: {report.get('exit_code', 'Unknown')}
- **Container**: {report.get('container_name', 'Unknown')}

## KPI Summary

| Metric | Value | Description |
|--------|-------|-------------|
| K1: Failed Tools | {kpis.get('K1_failed_tools', 0)} | CLI command execution failures |
| K2: Quality Reruns | {kpis.get('K2_quality_reruns', 0)} | Quality gate retry cycles |
| K3: Agent Invocations | {kpis.get('K3_agent_invocations', 0)} | Number of agents used |
| K4: State Transitions | {kpis.get('K4_state_transitions', 0)} | Workflow state changes |
| K9: Token Spend | {kpis.get('K9_token_spend', 0):,} | Total tokens consumed |
| K11: Runtime | {kpis.get('K11_runtime_seconds', 0)}s | End-to-end execution time |
| K12: API Retries | {kpis.get('K12_api_retry_attempts', 0)} | API retry attempts |
| K13: Rate Limits | {kpis.get('K13_rate_limit_events', 0)} | Rate limiting events |
| K14: API Failure Rate | {kpis.get('K14_api_failure_rate', 0)}% | API reliability metric |

## Execution Details

- **Agents Used**: {len(unique_agents)} unique agents
- **State Transitions**: {len(state_transitions)} workflow changes
- **Token Events**: {len(raw_data.get('retries', []))} retry events

### Agents Invoked
"""

        if unique_agents:
            for agent in sorted(unique_agents):
                md += f"- {agent}\n"
        else:
            md += "✅ No specific agent invocations detected\n"

        md += "\n### Failed Tools (if any)\n"
        failed_tools = raw_data.get("failed_tools", [])
        if failed_tools:
            md += "\n```\n" + "\n".join(failed_tools[:5]) + "\n```\n"
            if len(failed_tools) > 5:
                md += f"\n... and {len(failed_tools) - 5} more failures\n"
        else:
            md += "\n✅ No tool failures detected\n"

        md += "\n### Quality Issues (if any)\n"
        quality_issues = raw_data.get("quality_reruns", [])
        if quality_issues:
            md += "\n```\n" + "\n".join(quality_issues) + "\n```\n"
        else:
            md += "\n✅ No quality reruns detected\n"

        md += "\n### API Reliability\n"
        api_failures = raw_data.get("api_failures", [])
        rate_limits = raw_data.get("rate_limits", [])

        if api_failures or rate_limits:
            md += f"- API Failures: {len(api_failures)}\n"
            md += f"- Rate Limit Events: {len(rate_limits)}\n"
            if api_failures:
                md += (
                    "\n**API Failure Details:**\n```\n"
                    + "\n".join(api_failures[:3])
                    + "\n```\n"
                )
        else:
            md += "✅ No API reliability issues detected\n"

        return md

    @staticmethod
    def save_markdown_report(
        report: Dict[str, Any], reports_dir: str = "reports"
    ) -> str:
        """Save markdown evaluation report to disk."""
        from pathlib import Path

        # Ensure reports directory exists
        reports_path = Path(reports_dir)
        reports_path.mkdir(exist_ok=True)

        # Generate report filename
        timestamp = report.get("timestamp", "unknown")
        report_file = reports_path / f"report_{timestamp}.md"

        # Generate and save markdown content
        md_content = ReportGenerator.generate_markdown_summary(report)

        with open(report_file, "w") as f:
            f.write(md_content)

        return str(report_file)

    @staticmethod
    def save_report(report: Dict[str, Any], reports_dir: str = "reports") -> str:
        """Save evaluation report to disk."""
        from pathlib import Path
        import json

        # Ensure reports directory exists
        reports_path = Path(reports_dir)
        reports_path.mkdir(exist_ok=True)

        # Generate report filename
        timestamp = report.get("timestamp", "unknown")
        report_file = reports_path / f"run_{timestamp}.json"

        # Sanitize report (remove any sensitive data)
        sanitized_report = ReportGenerator._sanitize_report(report)

        # Save report
        with open(report_file, "w") as f:
            json.dump(sanitized_report, f, indent=2, default=str)

        return str(report_file)

    @staticmethod
    def _sanitize_report(report: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from report."""
        # Create a copy to avoid modifying original
        sanitized = report.copy()

        # Remove sensitive keys
        sensitive_keys = [
            "api_key",
            "auth_token",
            "token",
            "password",
            "secret",
            "CLAUDE_API_KEY",
            "QWEN_API_KEY",
            "GEMINI_API_KEY",
            "CLAUDE_AUTH_TOKEN",
            "OPENAI_API_KEY",
            "GEMINI_AUTH_TOKEN",
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

    @staticmethod
    def compare_with_baseline(
        current_report: Dict[str, Any], baseline_path: str = "reports/baseline.json"
    ) -> Dict[str, Any]:
        """Compare current report with baseline."""
        import json
        from pathlib import Path

        baseline_file = Path(baseline_path)
        if not baseline_file.exists():
            return {"error": "Baseline file not found"}

        try:
            with open(baseline_file, "r") as f:
                baseline = json.load(f)

            current_kpis = current_report.get("kpis", {})
            baseline_kpis = baseline.get("kpis", {})

            comparison = {}
            for kpi in current_kpis:
                current_val = current_kpis.get(kpi, 0)
                baseline_val = baseline_kpis.get(kpi, 0)

                comparison[kpi] = {
                    "current": current_val,
                    "baseline": baseline_val,
                    "change": current_val - baseline_val,
                    "change_percent": (
                        (current_val - baseline_val) / baseline_val * 100
                    )
                    if baseline_val > 0
                    else 0,
                }

            return {
                "scenario": current_report.get("scenario_id"),
                "cli_tool": current_report.get("cli_tool"),
                "comparison": comparison,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            }

        except (json.JSONDecodeError, KeyError) as e:
            return {"error": f"Failed to compare with baseline: {e}"}
