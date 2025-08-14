#!/usr/bin/env python3
"""
Root Cause Execution Tracer - High-level execution path and dependency analysis
================================================================================

PURPOSE: Analyzes codebase structure to provide investigation pointers for debugging.
Part of the shared/analyzers/root_cause suite using BaseAnalyzer infrastructure.

APPROACH:
- High-level execution pattern analysis
- Dependency structure identification
- Investigation pointer generation
- Error handling coverage assessment
- Complexity hotspot identification

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements execution-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import base analyzer infrastructure
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared.core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
except ImportError as e:
    print(f"Error importing base analyzer: {e}", file=sys.stderr)
    sys.exit(1)


class ExecutionTraceAnalyzer(BaseAnalyzer):
    """Analyzes execution patterns and provides investigation pointers for debugging."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        # Create execution-specific configuration
        trace_config = config or AnalyzerConfig(
            code_extensions={
                ".py",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".java",
                ".cs",
                ".cpp",
                ".c",
                ".h",
                ".hpp",
                ".go",
                ".rs",
                ".php",
                ".rb",
                ".swift",
                ".kt",
                ".scala",
            },
            skip_patterns={
                "node_modules",
                ".git",
                "__pycache__",
                ".pytest_cache",
                "build",
                "dist",
                ".next",
                ".nuxt",
                "coverage",
                "venv",
                "env",
                ".env",
                "vendor",
                "logs",
                "target",
                ".vscode",
                ".idea",
                "*.min.js",
                "*.bundle.js",
            },
        )

        # Initialize base analyzer
        super().__init__("root_cause", trace_config)

        # Simple patterns for basic component identification
        self.patterns = {
            "main_functions": [r"def main\(", r'if __name__ == ["\']__main__["\']'],
            "classes": [r"class \w+"],
            "functions": [r"def \w+\("],
            "imports": [r"import \w+", r"from \w+ import"],
            "try_blocks": [r"try:"],
            "for_loops": [r"for \w+ in"],
            "api_routes": [r"@app\.route", r"app\.(get|post|put|delete)"],
        }

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "Execution Trace Analyzer",
            "version": "2.0.0",
            "description": "Analyzes execution patterns and provides investigation pointers for debugging",
            "category": "root_cause",
            "priority": "medium",
            "capabilities": [
                "High-level execution pattern analysis",
                "Dependency structure identification",
                "Investigation pointer generation",
                "Error handling coverage assessment",
                "Complexity hotspot identification",
                "Multi-language pattern recognition",
            ],
            "supported_formats": list(self.config.code_extensions),
        }

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file for execution patterns and investigation pointers.

        Args:
            target_path: Path to file to analyze

        Returns:
            List of findings with standardized structure
        """
        all_findings = []
        file_path = Path(target_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            # Skip very large files
            if len(content) > 100000:  # 100KB limit
                return all_findings

            # Analyze file structure
            file_info = self._analyze_file_structure(content, str(file_path))

            # Generate investigation pointers based on analysis
            pointers = self._generate_investigation_pointers(file_info, str(file_path))

            # Convert pointers to findings
            for pointer in pointers:
                severity_map = {
                    "critical": "critical",
                    "high": "high",
                    "medium": "medium",
                    "low": "low",
                    "info": "info",
                }

                finding = {
                    "title": pointer["type"].replace("_", " ").title(),
                    "description": pointer["description"],
                    "severity": severity_map.get(pointer["severity"], "medium"),
                    "file_path": str(file_path),
                    "line_number": pointer.get("line_number", 0),
                    "recommendation": pointer["investigation_focus"],
                    "metadata": {
                        "pointer_type": pointer["type"],
                        "investigation_focus": pointer["investigation_focus"],
                        "evidence": pointer.get("evidence", {}),
                        "confidence": "medium",
                    },
                }
                all_findings.append(finding)

        except Exception as e:
            all_findings.append(
                {
                    "title": "File Analysis Error",
                    "description": f"Could not analyze file: {str(e)}",
                    "severity": "low",
                    "file_path": str(file_path),
                    "line_number": 0,
                    "recommendation": "Check file encoding and permissions.",
                    "metadata": {"error_type": "file_read_error", "confidence": "high"},
                }
            )

        return all_findings

    def _analyze_file_structure(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze single file structure for patterns."""
        lines = content.split("\n")
        file_info = {
            "total_lines": len(lines),
            "code_lines": len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
            ),
            "blank_lines": len([line for line in lines if not line.strip()]),
            "comment_lines": len(
                [line for line in lines if line.strip().startswith("#")]
            ),
        }

        # Count patterns in the content
        for pattern_name, patterns in self.patterns.items():
            count = 0
            for pattern in patterns:
                matches = re.findall(pattern, content)
                count += len(matches)
            file_info[pattern_name] = count

        return file_info

    def _generate_investigation_pointers(
        self, file_info: Dict[str, Any], file_path: str
    ) -> List[Dict[str, Any]]:
        """Generate investigation pointers based on file analysis."""
        pointers = []

        # Check for missing main functions
        if file_info.get("main_functions", 0) == 0 and file_path.endswith(".py"):
            pointers.append(
                {
                    "type": "no_entry_points",
                    "severity": "medium",
                    "description": "No main functions or entry points found in Python file",
                    "investigation_focus": "Identify application startup and entry points",
                    "evidence": {"main_functions": file_info.get("main_functions", 0)},
                }
            )

        # Check for error handling coverage
        total_functions = file_info.get("functions", 0)
        try_blocks = file_info.get("try_blocks", 0)
        if total_functions > 3 and try_blocks < (total_functions * 0.3):
            pointers.append(
                {
                    "type": "low_error_handling",
                    "severity": "high",
                    "description": f"Only {try_blocks} try blocks for {total_functions} functions",
                    "investigation_focus": "Review error handling and exception management",
                    "evidence": {
                        "functions": total_functions,
                        "try_blocks": try_blocks,
                    },
                }
            )

        # Check for complex files
        code_lines = file_info.get("code_lines", 0)
        if code_lines > 200:
            pointers.append(
                {
                    "type": "complex_file",
                    "severity": "medium",
                    "description": f"File has {code_lines} lines of code, indicating high complexity",
                    "investigation_focus": "Review complex file for potential issues and refactoring opportunities",
                    "evidence": {"code_lines": code_lines},
                }
            )

        # Check for API endpoints
        api_routes = file_info.get("api_routes", 0)
        if api_routes > 0:
            pointers.append(
                {
                    "type": "web_application_detected",
                    "severity": "info",
                    "description": f"Found {api_routes} API routes in file",
                    "investigation_focus": "Review web application structure and routing",
                    "evidence": {"api_routes": api_routes},
                }
            )

        # Check for low test coverage indicators
        if file_info.get("classes", 0) > 0 and file_info.get("functions", 0) > 5:
            if "test" not in file_path.lower() and try_blocks < 2:
                pointers.append(
                    {
                        "type": "potential_testing_gap",
                        "severity": "medium",
                        "description": "Complex file with multiple classes/functions but minimal error handling",
                        "investigation_focus": "Consider adding comprehensive testing and error handling",
                        "evidence": {
                            "classes": file_info.get("classes", 0),
                            "functions": file_info.get("functions", 0),
                        },
                    }
                )

        return pointers


def main():
    """Main entry point for command-line usage."""
    analyzer = ExecutionTraceAnalyzer()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
