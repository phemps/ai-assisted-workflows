#!/usr/bin/env python3
"""
Input Validation Analyzer - Input Security and Injection Prevention Analysis
===========================================================================

PURPOSE: Analyzes code for input validation vulnerabilities and injection attack vectors.
Part of the shared/analyzers/security suite using BaseAnalyzer infrastructure.

APPROACH:
- Missing input validation detection
- Insufficient sanitization identification
- Direct user input execution detection
- SQL injection pattern analysis
- Command injection vulnerability detection
- Path traversal and file inclusion checks
- Regex injection vulnerability detection

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements security-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import base analyzer infrastructure
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared.core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
except ImportError as e:
    print(f"Error importing base analyzer: {e}", file=sys.stderr)
    sys.exit(1)


class InputValidationAnalyzer(BaseAnalyzer):
    """Analyzes input validation and injection vulnerabilities."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        # Create security-specific configuration
        security_config = config or AnalyzerConfig(
            code_extensions={
                ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".java",
                ".cs",
                ".php",
                ".rb",
                ".go",
                ".rs",
                ".cpp",
                ".c",
                ".h",
                ".hpp",
                ".swift",
                ".kt",
                ".scala",
                ".dart",
                ".xml",
                ".html",
                ".vue",
                ".svelte",
                ".sql",
                ".sh",
                ".bash",
                ".ps1",
                ".bat",
            },
            skip_patterns={
                "node_modules",
                ".git",
                "__pycache__",
                ".pytest_cache",
                "venv",
                "env",
                ".venv",
                "dist",
                "build",
                ".next",
                "coverage",
                ".nyc_output",
                "target",
                "vendor",
                "test_fixtures",
                "*.min.js",
                "*.min.css",
            },
        )

        # Initialize base analyzer
        super().__init__("security", security_config)

        # Initialize validation patterns
        self._init_validation_patterns()
        self._init_injection_patterns()
        self._init_file_operation_patterns()
        self._init_unsafe_patterns()

        # Compile patterns for performance
        self._compiled_patterns = {}
        self._compile_all_patterns()

    def _init_validation_patterns(self):
        """Initialize input validation patterns."""
        self.validation_patterns = {
            "missing_input_validation": {
                "indicators": [
                    r"request\.(args|form|json|data|params)(?!.*(?:validat|sanitiz|check|filter))",
                    r"req\.(body|query|params)(?!.*(?:validat|sanitiz|check|filter))",
                    r"input\(.*\)(?!.*(?:validat|sanitiz|check|strip))",
                    r"params\[.*\](?!.*(?:check|validat|sanitiz))",
                    r"query\[.*\](?!.*(?:sanitiz|escape|filter))",
                    r"POST.*data(?!.*(?:validat|sanitiz|check))",
                    r"\$_(?:GET|POST|REQUEST)\[(?!.*(?:filter|escape|sanitiz))",
                ],
                "severity": "high",
                "description": "Missing input validation",
                "recommendation": "Validate all user input before processing. Use whitelist validation and type checking.",
            },
            "insufficient_sanitization": {
                "indicators": [
                    r"user.*input(?!.*(?:escape|sanitiz|clean|filter))",
                    r"request.*data(?!.*(?:filter|validat|sanitiz))",
                    r"form.*data(?!.*(?:sanitiz|escape|clean))",
                    r"query.*param(?!.*(?:escape|sanitiz|filter))",
                    r"raw.*input(?!.*(?:process|sanitiz|clean))",
                ],
                "severity": "medium",
                "description": "Insufficient input sanitization",
                "recommendation": "Sanitize all user input. Use context-appropriate escaping and encoding.",
            },
            "missing_length_check": {
                "indicators": [
                    r"(?:input|data|param).*=.*request(?!.*(?:len|length|size|max))",
                    r"buffer.*=.*user(?!.*(?:limit|max|bound))",
                    r"string.*=.*input(?!.*(?:substring|slice|truncate))",
                ],
                "severity": "medium",
                "description": "Missing input length validation",
                "recommendation": "Implement maximum length checks to prevent buffer overflows and DoS attacks.",
            },
            "missing_type_validation": {
                "indicators": [
                    r"parseInt\(.*request(?!.*(?:isNaN|Number\.is))",
                    r"int\(.*input(?!.*(?:try|except|ValueError))",
                    r"parseFloat\(.*user(?!.*(?:isNaN|Number\.is))",
                    r"to_i.*params(?!.*(?:rescue|valid))",
                ],
                "severity": "medium",
                "description": "Missing type validation",
                "recommendation": "Validate data types and handle conversion errors gracefully.",
            },
        }

    def _init_injection_patterns(self):
        """Initialize injection vulnerability patterns."""
        self.injection_patterns = {
            "sql_injection": {
                "indicators": [
                    r"(?:SELECT|INSERT|UPDATE|DELETE).*\+.*(?:request|user|input|param)",
                    r'query.*=.*[\'"].*\+.*(?:request|user|input)',
                    r"execute.*%.*(?:request|user|input)",
                    r"cursor\.execute.*%(?!.*\?)",
                    r"sql.*\.format\(.*(?:request|user|input)",
                    r"f['\"].*(?:SELECT|INSERT|UPDATE|DELETE).*{.*(?:request|user|input)",
                ],
                "severity": "critical",
                "description": "SQL injection vulnerability",
                "recommendation": "Use parameterized queries or prepared statements. Never concatenate user input into SQL.",
            },
            "command_injection": {
                "indicators": [
                    r"os\.system\(.*(?:request|user|input)",
                    r"subprocess\.(?:call|run|Popen).*(?:request|user|input)(?!.*shell=False)",
                    r"exec\(.*(?:request|user|input)",
                    r"eval\(.*(?:request|user|input)",
                    r"shell_exec\(.*(?:user|input|\$_)",
                    r"system\(.*(?:user|input|\$_)",
                    r"Process\.Start.*(?:request|user|input)",
                ],
                "severity": "critical",
                "description": "Command injection vulnerability",
                "recommendation": "Avoid system calls with user input. Use safe APIs and strict input validation.",
            },
            "ldap_injection": {
                "indicators": [
                    r"ldap.*search.*\+.*(?:user|input|request)",
                    r"ldap.*filter.*=.*\+.*(?:user|input)",
                    r"DirectorySearcher.*\+.*(?:user|input)",
                ],
                "severity": "high",
                "description": "LDAP injection vulnerability",
                "recommendation": "Use LDAP query parameterization and escape special characters.",
            },
            "xpath_injection": {
                "indicators": [
                    r"xpath.*\+.*(?:user|input|request)",
                    r"selectNodes.*\+.*(?:user|input)",
                    r"evaluate\(.*\+.*(?:request|input)",
                ],
                "severity": "high",
                "description": "XPath injection vulnerability",
                "recommendation": "Use XPath variable binding and avoid string concatenation.",
            },
            "regex_injection": {
                "indicators": [
                    r"re\.compile\(.*(?:user|input|request)",
                    r"new RegExp\(.*(?:user|input|request)",
                    r"Pattern\.compile\(.*(?:user|input|request)",
                    r"preg_match\(.*\$_(?:GET|POST|REQUEST)",
                ],
                "severity": "medium",
                "description": "Regex injection vulnerability",
                "recommendation": "Escape user input in regex patterns or use literal string matching.",
            },
            "template_injection": {
                "indicators": [
                    r"render_template_string\(.*(?:request|user|input)",
                    r"Template\(.*(?:request|user|input)",
                    r"eval.*template.*(?:user|input|request)",
                    r"{{.*request\..*}}",
                ],
                "severity": "high",
                "description": "Template injection vulnerability",
                "recommendation": "Use safe template rendering methods and avoid user-controlled templates.",
            },
        }

    def _init_file_operation_patterns(self):
        """Initialize file operation vulnerability patterns."""
        self.file_patterns = {
            "path_traversal": {
                "indicators": [
                    r"open\(.*(?:request|user|input)(?!.*(?:basename|realpath|sanitiz))",
                    r"File\.open.*(?:params|request)(?!.*(?:File\.basename|sanitiz))",
                    r"readFile.*(?:req\.|request)(?!.*path\.join)",
                    r"include.*\$_(?:GET|POST|REQUEST)(?!.*basename)",
                    r"require.*user.*input(?!.*whitelist)",
                ],
                "severity": "high",
                "description": "Path traversal vulnerability",
                "recommendation": "Validate file paths, use whitelists, and resolve to absolute paths.",
            },
            "file_upload_validation": {
                "indicators": [
                    r"upload.*file(?!.*(?:type|extension|mime|magic))",
                    r"save.*uploaded(?!.*(?:validat|check|verify))",
                    r"move_uploaded_file(?!.*(?:mime|type|check))",
                    r"file.*write.*upload(?!.*(?:sanitiz|validat))",
                ],
                "severity": "high",
                "description": "Insufficient file upload validation",
                "recommendation": "Validate file types, extensions, content, and size. Use magic number validation.",
            },
            "arbitrary_file_write": {
                "indicators": [
                    r"file.*write.*(?:request|user|input)",
                    r"fs\.write.*(?:req\.|request)",
                    r"File\.write.*params",
                    r"fwrite.*\$_(?:GET|POST|REQUEST)",
                ],
                "severity": "critical",
                "description": "Arbitrary file write vulnerability",
                "recommendation": "Never use user input directly in file paths. Implement strict access controls.",
            },
        }

    def _init_unsafe_patterns(self):
        """Initialize unsafe operation patterns."""
        self.unsafe_patterns = {
            "unsafe_deserialization": {
                "indicators": [
                    r"pickle\.loads.*(?:request|user|input)",
                    r"yaml\.load(?!.*SafeLoader).*(?:request|user|input)",
                    r"unserialize\(.*\$_(?:GET|POST|REQUEST|COOKIE)",
                    r"ObjectInputStream.*(?:request|user|input)",
                    r"json\.loads.*eval.*(?:request|user|input)",
                ],
                "severity": "critical",
                "description": "Unsafe deserialization",
                "recommendation": "Use safe deserialization methods and validate serialized data.",
            },
            "unsafe_redirect": {
                "indicators": [
                    r"redirect\(.*(?:request|user|input)(?!.*(?:whitelist|allowed|valid))",
                    r"location\.href.*=.*(?:request|user|input)",
                    r"header\(['\"]Location:.*\$_(?:GET|POST|REQUEST)",
                    r"Response\.Redirect.*Request\[",
                ],
                "severity": "medium",
                "description": "Open redirect vulnerability",
                "recommendation": "Validate redirect URLs against a whitelist of allowed destinations.",
            },
            "unsafe_reflection": {
                "indicators": [
                    r"getattr\(.*(?:request|user|input)",
                    r"Class\.forName\(.*(?:request|user|input)",
                    r"Assembly\.Load.*(?:request|user|input)",
                    r"require\(.*(?:request|user|input)",
                ],
                "severity": "high",
                "description": "Unsafe reflection/dynamic loading",
                "recommendation": "Avoid dynamic class/module loading with user input.",
            },
        }

    def _compile_all_patterns(self):
        """Compile all regex patterns for performance."""
        pattern_groups = [
            self.validation_patterns,
            self.injection_patterns,
            self.file_patterns,
            self.unsafe_patterns,
        ]

        for patterns in pattern_groups:
            for vuln_type, config in patterns.items():
                self._compiled_patterns[vuln_type] = [
                    re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                    for pattern in config["indicators"]
                ]

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "Input Validation Analyzer",
            "version": "2.0.0",
            "description": "Analyzes input validation and injection vulnerabilities",
            "category": "security",
            "priority": "critical",
            "capabilities": [
                "Input validation detection",
                "SQL injection analysis",
                "Command injection detection",
                "Path traversal identification",
                "File upload validation",
                "Template injection detection",
                "Unsafe deserialization detection",
                "Open redirect detection",
                "LDAP/XPath injection detection",
            ],
            "supported_formats": list(self.config.code_extensions),
            "patterns_checked": len(self._compiled_patterns),
        }

    def _scan_file_for_vulnerabilities(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for input validation vulnerabilities."""
        findings = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

                # Check all vulnerability patterns
                pattern_groups = [
                    ("validation", self.validation_patterns),
                    ("injection", self.injection_patterns),
                    ("file_operation", self.file_patterns),
                    ("unsafe_operation", self.unsafe_patterns),
                ]

                for category, patterns in pattern_groups:
                    for vuln_type, config in patterns.items():
                        compiled_patterns = self._compiled_patterns.get(vuln_type, [])

                        for pattern in compiled_patterns:
                            for match in pattern.finditer(content):
                                # Calculate line number
                                line_number = content[: match.start()].count("\n") + 1

                                # Get the matched line
                                line_content = (
                                    lines[line_number - 1].strip()
                                    if line_number <= len(lines)
                                    else ""
                                )

                                # Skip false positives
                                if self._is_false_positive(
                                    line_content, vuln_type, category
                                ):
                                    continue

                                findings.append(
                                    {
                                        "vuln_type": vuln_type,
                                        "category": category,
                                        "file_path": str(file_path),
                                        "line_number": line_number,
                                        "line_content": line_content[
                                            :200
                                        ],  # Truncate long lines
                                        "severity": config["severity"],
                                        "description": config["description"],
                                        "recommendation": config["recommendation"],
                                        "pattern_matched": pattern.pattern[
                                            :100
                                        ],  # Store pattern for debugging
                                    }
                                )

        except Exception as e:
            # Log but continue - file might be binary or inaccessible
            if self.verbose:
                print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)

        return findings

    def _is_false_positive(
        self, line_content: str, vuln_type: str, category: str
    ) -> bool:
        """Check if a detected vulnerability is likely a false positive."""
        line_lower = line_content.lower()

        # Skip comments
        comment_indicators = ["//", "#", "/*", "*", "<!--", "'''", '"""']
        for indicator in comment_indicators:
            if line_content.strip().startswith(indicator):
                return True

        # Skip test/example code
        if any(
            word in line_lower
            for word in ["test", "example", "sample", "demo", "mock", "fixture"]
        ):
            return True

        # Skip documentation
        if any(
            word in line_lower
            for word in ["@param", "@return", "docstring", "@example"]
        ):
            return True

        # Category-specific false positive checks
        if category == "validation" and "validate" in line_lower:
            return True  # Already has validation

        if category == "injection" and any(
            word in line_lower for word in ["prepared", "parameterized", "placeholder"]
        ):
            return True  # Using safe methods

        if category == "file_operation" and any(
            word in line_lower for word in ["whitelist", "allowed", "safe_path"]
        ):
            return True  # Has protection

        return False

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file for input validation vulnerabilities.

        Args:
            target_path: Path to file to analyze

        Returns:
            List of findings with standardized structure
        """
        all_findings = []
        file_path = Path(target_path)

        # Skip files that are too large
        if file_path.stat().st_size > 2 * 1024 * 1024:  # Skip files > 2MB
            return all_findings

        findings = self._scan_file_for_vulnerabilities(file_path)

        # Convert to standardized finding format
        for finding in findings:
            # Create detailed title
            title = f"{finding['description']} ({finding['vuln_type'].replace('_', ' ').title()})"

            # Create comprehensive description
            description = (
                f"{finding['description']} detected in {file_path.name} at line {finding['line_number']}. "
                f"Category: {finding['category'].replace('_', ' ').title()}. "
                f"This vulnerability could allow attackers to bypass security controls or execute malicious code."
            )

            standardized = {
                "title": title,
                "description": description,
                "severity": finding["severity"],
                "file_path": finding["file_path"],
                "line_number": finding["line_number"],
                "recommendation": finding["recommendation"],
                "metadata": {
                    "vuln_type": finding["vuln_type"],
                    "category": finding["category"],
                    "line_content": finding["line_content"],
                    "pattern_matched": finding["pattern_matched"],
                    "confidence": "high",
                },
            }
            all_findings.append(standardized)

        return all_findings


def main():
    """Main entry point for command-line usage."""
    analyzer = InputValidationAnalyzer()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
