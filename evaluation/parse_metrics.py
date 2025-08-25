#!/usr/bin/env python3
"""
Metrics Parsing Utilities

Helper functions for extracting KPIs from CLI tool logs and outputs.
"""

import re
import json
from typing import Dict, List, Any, Tuple
from pathlib import Path


class MetricsParser:
    """Utility class for parsing orchestration workflow metrics"""

    def __init__(self):
        self.tool_failure_patterns = [
            r"Tool execution failed",
            r'"error":\s*true',
            r"Command not found",
            r"Permission denied",
            r"No such file or directory",
            r"Exit code: [1-9]\d*",
            r"Error: .*",
            r"Failed to .*",
            r"npm ERR!",
            r"TypeError:",
            r"SyntaxError:",
            r"ModuleNotFoundError",
            r"FileNotFoundError",
        ]

        self.quality_rerun_patterns = [
            r"quality_review.*in_progress",
            r"testing.*in_progress",
            r"Rerunning quality checks",
            r"Quality gate failed.*retrying",
            r"Re-attempting.*quality",
            r"Lint.*failed.*retry",
            r"Tests.*failed.*retry",
            r"Type check.*failed.*retry",
        ]

        self.token_patterns = [
            r"tokens?[:\s]*(\d+)",
            r"usage[:\s]*(\d+)",
            r"input_tokens[:\s]*(\d+)",
            r"output_tokens[:\s]*(\d+)",
            r"total_tokens[:\s]*(\d+)",
            r"cost[:\s]*\$?(\d+\.?\d*)",
        ]

        self.state_transition_patterns = [
            r"State transition: (\w+) -> (\w+)",
            r"Moving from (\w+) to (\w+)",
            r"Phase: (\w+) -> (\w+)",
        ]

    def parse_failed_tools(self, text: str) -> Tuple[int, List[str]]:
        """
        Parse K1: Failed Tool Calls
        Returns (count, list_of_failures)
        """
        failures = []
        for pattern in self.tool_failure_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if isinstance(matches, list) and matches:
                failures.extend([str(m) for m in matches])

        return len(failures), failures

    def parse_quality_reruns(self, text: str) -> Tuple[int, List[str]]:
        """
        Parse K2: Quality Gate Reruns
        Returns (count, list_of_reruns)
        """
        reruns = []
        for pattern in self.quality_rerun_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if isinstance(matches, list) and matches:
                reruns.extend([str(m) for m in matches])

        return len(reruns), reruns

    def parse_token_usage(self, text: str) -> Tuple[int, List[int]]:
        """
        Parse K9: Token Spend
        Returns (total_tokens, list_of_individual_counts)
        """
        token_counts = []

        for pattern in self.token_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Handle both integer and float matches
                    if "." in str(match):
                        # Skip cost values for now, focus on token counts
                        continue
                    tokens = int(match)
                    if tokens > 0 and tokens < 1000000:  # Sanity check
                        token_counts.append(tokens)
                except (ValueError, TypeError):
                    continue

        return sum(token_counts), token_counts

    def parse_state_transitions(self, text: str) -> List[Dict[str, str]]:
        """
        Parse state transitions for understanding workflow progression
        Returns list of transitions: [{'from': 'state1', 'to': 'state2'}, ...]
        """
        transitions = []

        for pattern in self.state_transition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    transitions.append({"from": match[0], "to": match[1]})

        return transitions

    def detect_agent_invocations(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect which agents were invoked during execution
        """
        agent_patterns = [
            r"@agent-(\w+)",
            r"Invoking agent: (\w+)",
            r"Agent (\w+) invoked",
        ]

        agents = []
        for pattern in agent_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                agents.append({"agent": match, "pattern": pattern})

        return agents

    def extract_error_context(self, text: str, error_line: str) -> str:
        """
        Extract context around an error for better debugging
        """
        lines = text.split("\n")
        error_line_clean = error_line.strip()

        # Find the line with the error
        for i, line in enumerate(lines):
            if error_line_clean in line:
                # Return 3 lines before and after for context
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context_lines = lines[start:end]
                return "\n".join(context_lines)

        return error_line  # Fallback to just the error line

    def parse_all_metrics(self, text: str, runtime_seconds: float) -> Dict[str, Any]:
        """
        Parse all supported metrics from text output
        """
        # Parse individual metrics
        failed_tools_count, failed_tools_list = self.parse_failed_tools(text)
        quality_reruns_count, quality_reruns_list = self.parse_quality_reruns(text)
        token_total, token_list = self.parse_token_usage(text)

        # Additional analysis
        state_transitions = self.parse_state_transitions(text)
        agent_invocations = self.detect_agent_invocations(text)

        # Count unique agents used
        unique_agents = set(agent["agent"] for agent in agent_invocations)

        return {
            "kpis": {
                "K1_failed_tools": failed_tools_count,
                "K2_quality_reruns": quality_reruns_count,
                "K9_token_spend": token_total,
                "K11_runtime_seconds": round(runtime_seconds, 2),
            },
            "detailed_data": {
                "failed_tools_details": failed_tools_list,
                "quality_reruns_details": quality_reruns_list,
                "token_counts_individual": token_list,
                "state_transitions": state_transitions,
                "agent_invocations": agent_invocations,
                "unique_agents_used": list(unique_agents),
                "agent_count": len(unique_agents),
            },
        }


class ReportGenerator:
    """Generate formatted reports from parsed metrics"""

    def __init__(self):
        pass

    def generate_markdown_summary(
        self, metrics: Dict[str, Any], scenario_id: str
    ) -> str:
        """Generate a markdown summary of the evaluation"""
        kpis = metrics["kpis"]
        details = metrics["detailed_data"]

        md = f"""# Evaluation Report: {scenario_id}

## KPI Summary

| Metric | Value | Description |
|--------|-------|-------------|
| K1: Failed Tools | {kpis['K1_failed_tools']} | Number of tool execution failures |
| K2: Quality Reruns | {kpis['K2_quality_reruns']} | Quality gate retry cycles |
| K9: Token Spend | {kpis['K9_token_spend']:,} | Total tokens consumed |
| K11: Runtime | {kpis['K11_runtime_seconds']}s | End-to-end execution time |

## Execution Details

- **Agents Used**: {details['agent_count']} unique agents
- **State Transitions**: {len(details['state_transitions'])} transitions
- **Token Events**: {len(details['token_counts_individual'])} token measurements

### Agents Invoked
{chr(10).join(f'- {agent}' for agent in details['unique_agents_used'])}

### Failed Tools (if any)
"""

        if details["failed_tools_details"]:
            md += "\n```\n" + "\n".join(details["failed_tools_details"][:5]) + "\n```\n"
            if len(details["failed_tools_details"]) > 5:
                md += f"\n... and {len(details['failed_tools_details']) - 5} more failures\n"
        else:
            md += "\n✅ No tool failures detected\n"

        md += "\n### Quality Issues (if any)\n"
        if details["quality_reruns_details"]:
            md += "\n```\n" + "\n".join(details["quality_reruns_details"]) + "\n```\n"
        else:
            md += "\n✅ No quality reruns detected\n"

        return md

    def save_markdown_report(
        self, metrics: Dict[str, Any], scenario_id: str, timestamp: str
    ) -> str:
        """Save markdown report to file"""
        md_content = self.generate_markdown_summary(metrics, scenario_id)

        report_path = Path(f"evaluation/reports/report_{timestamp}.md")
        with open(report_path, "w") as f:
            f.write(md_content)

        return str(report_path)


def main():
    """Test the metrics parser with sample input"""
    sample_text = """
    Tool execution failed: npm install
    Error: Command not found: nonexistent-command
    quality_review -> in_progress
    State transition: testing -> quality_review
    @agent-fullstack-developer invoked
    tokens: 15432
    output_tokens: 8291
    Exit code: 1
    """

    parser = MetricsParser()
    metrics = parser.parse_all_metrics(sample_text, 180.5)

    print("Sample Metrics Parse:")
    print(json.dumps(metrics, indent=2))

    # Generate report
    generator = ReportGenerator()
    md_report = generator.generate_markdown_summary(metrics, "test_scenario")
    print("\nMarkdown Report:")
    print(md_report)


if __name__ == "__main__":
    main()
