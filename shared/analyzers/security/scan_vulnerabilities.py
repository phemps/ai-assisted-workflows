#!/usr/bin/env python3
"""
Vulnerability Scanner - OWASP Top 10 and Security Pattern Analysis
==================================================================

PURPOSE: Comprehensive vulnerability scanning for OWASP Top 10 and common security issues.
Part of the shared/analyzers/security suite using BaseAnalyzer infrastructure.

APPROACH:
- SQL, Command, LDAP, XPath injection detection
- XSS (Reflected, Stored, DOM) vulnerability scanning
- Insecure deserialization and XXE detection
- Cryptographic weakness identification
- Security misconfiguration detection
- Data exposure and error disclosure analysis

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements security-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import base analyzer infrastructure
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from shared.core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
except ImportError as e:
    print(f"Error importing base analyzer: {e}", file=sys.stderr)
    sys.exit(1)


class VulnerabilityScanner(BaseAnalyzer):
    """Scans for OWASP Top 10 and common security vulnerabilities."""

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

        # Initialize vulnerability patterns
        self._init_injection_patterns()
        self._init_xss_patterns()
        self._init_deserialization_patterns()
        self._init_xxe_patterns()
        self._init_data_exposure_patterns()
        self._init_misconfiguration_patterns()

        # Compile patterns for performance
        self._compiled_patterns = {}
        self._compile_all_patterns()

        # OWASP category mapping
        self.owasp_categories = {
            "injection": "A03:2021 – Injection",
            "xss": "A03:2021 – Injection",
            "broken_auth": "A07:2021 – Identity and Authentication Failures",
            "data_exposure": "A02:2021 – Cryptographic Failures",
            "xxe": "A05:2021 – Security Misconfiguration",
            "broken_access": "A01:2021 – Broken Access Control",
            "misconfiguration": "A05:2021 – Security Misconfiguration",
            "deserialization": "A08:2021 – Software and Data Integrity Failures",
            "components": "A06:2021 – Vulnerable Components",
            "logging": "A09:2021 – Security Logging and Monitoring Failures",
            "ssrf": "A10:2021 – Server-Side Request Forgery",
        }

    def _init_injection_patterns(self):
        """Initialize injection vulnerability patterns."""
        self.injection_patterns = {
            "sql_injection": {
                "indicators": [
                    r'query\s*=\s*[\'"].*%.*[\'"]',
                    r'execute\s*\(\s*[\'"].*%.*[\'"]',
                    r"cursor\.execute.*%",
                    r"SELECT.*\+.*user",
                    r"INSERT.*\+.*request",
                    r"UPDATE.*\+.*input",
                    r"DELETE.*\+.*param",
                    r"query.*\+.*\$_(?:GET|POST|REQUEST)",
                    r"sql.*\.\s*format\s*\(.*user",
                    r"f['\"].*SELECT.*{.*}",
                    r"executeQuery.*\+.*request\.get",
                ],
                "severity": "critical",
                "description": "SQL injection vulnerability detected",
                "recommendation": "Use parameterized queries or prepared statements. Never concatenate user input directly into SQL queries.",
            },
            "command_injection": {
                "indicators": [
                    r"os\.system\s*\(.*\+",
                    r"subprocess\.(call|run|Popen).*\+",
                    r"exec\s*\(.*user",
                    r"eval\s*\(.*request",
                    r"shell=True.*\+",
                    r"system\(.*\$",
                    r"Runtime\.getRuntime\(\)\.exec",
                    r"Process\s*\(.*\+",
                    r"spawn.*user.*input",
                    r"shelljs\.exec.*\+",
                ],
                "severity": "critical",
                "description": "Command injection vulnerability detected",
                "recommendation": "Avoid system calls with user input. Use safe alternatives or strict input validation and escaping.",
            },
            "ldap_injection": {
                "indicators": [
                    r"ldap.*search.*\+",
                    r"ldap.*filter.*user",
                    r"distinguished.*name.*\+",
                    r"ldap.*query.*request",
                    r"DirectorySearcher.*\+",
                    r"SearchFilter.*user.*input",
                ],
                "severity": "high",
                "description": "LDAP injection vulnerability detected",
                "recommendation": "Use LDAP query parameterization and escape special characters in user input.",
            },
            "xpath_injection": {
                "indicators": [
                    r"xpath.*\+.*user",
                    r"xml.*query.*\+",
                    r"xpath.*request",
                    r"xml.*search.*input",
                    r"selectNodes.*\+",
                    r"evaluate\(.*\+.*request",
                ],
                "severity": "high",
                "description": "XPath injection vulnerability detected",
                "recommendation": "Use XPath query parameterization and validate user input.",
            },
            "nosql_injection": {
                "indicators": [
                    r"find\({.*\$where.*user",
                    r"collection\.find.*eval",
                    r"mongo.*\$ne.*user",
                    r"db\..*\({.*\+.*}",
                    r"aggregate.*\$.*user.*input",
                ],
                "severity": "critical",
                "description": "NoSQL injection vulnerability detected",
                "recommendation": "Validate and sanitize user input. Avoid using $where and JavaScript expressions with user data.",
            },
        }

    def _init_xss_patterns(self):
        """Initialize XSS vulnerability patterns."""
        self.xss_patterns = {
            "reflected_xss": {
                "indicators": [
                    r"innerHTML\s*=.*request",
                    r"document\.write.*user",
                    r"response.*write.*request",
                    r"render.*\+.*input",
                    r"html.*\+.*user.*input",
                    r"echo.*\$_(?:GET|POST|REQUEST)",
                    r"print.*request\.get",
                    r"out\.println.*request\.getParameter",
                ],
                "severity": "high",
                "description": "Reflected XSS vulnerability detected",
                "recommendation": "Encode user input before rendering. Use Content Security Policy (CSP) headers.",
            },
            "stored_xss": {
                "indicators": [
                    r"save.*user.*input.*(?!.*escape)",
                    r"store.*user.*data.*(?!.*sanitize)",
                    r"database.*insert.*user.*(?!.*clean)",
                    r"persist.*request.*(?!.*filter)",
                    r"write.*file.*user.*input",
                ],
                "severity": "high",
                "description": "Stored XSS vulnerability detected",
                "recommendation": "Sanitize user input before storing and encode when displaying.",
            },
            "dom_xss": {
                "indicators": [
                    r"location\.href\s*=.*user",
                    r"window\.location\s*=.*input",
                    r"document\.location\s*=.*request",
                    r"eval\(.*window\.location",
                    r"setTimeout\(.*user.*input",
                    r"setInterval\(.*request",
                    r"Function\(.*user.*\)",
                ],
                "severity": "high",
                "description": "DOM-based XSS vulnerability detected",
                "recommendation": "Validate and sanitize client-side input. Avoid using eval() and similar functions.",
            },
        }

    def _init_deserialization_patterns(self):
        """Initialize deserialization vulnerability patterns."""
        self.deserialization_patterns = {
            "unsafe_deserialization": {
                "indicators": [
                    r"pickle\.loads",
                    r"yaml\.load(?!.*Loader=yaml\.SafeLoader)",
                    r"ObjectInputStream",
                    r"unserialize\(",
                    r"json\.loads.*eval",
                    r"readObject\(\)",
                    r"deserialize.*user.*input",
                    r"Marshal\.load",
                    r"JsonConvert\.DeserializeObject.*Type",
                ],
                "severity": "critical",
                "description": "Unsafe deserialization vulnerability detected",
                "recommendation": "Use safe deserialization methods. Validate and sign serialized objects.",
            }
        }

    def _init_xxe_patterns(self):
        """Initialize XXE vulnerability patterns."""
        self.xxe_patterns = {
            "xml_external_entity": {
                "indicators": [
                    r"XMLReader.*DTD.*VALIDATION",
                    r"DocumentBuilder.*setExpandEntityReferences.*true",
                    r"SAXParser.*Feature.*external",
                    r"etree\.parse.*resolve_entities.*True",
                    r"LIBXML_NOENT",
                    r"DOMDocument.*loadXML.*LIBXML",
                    r"XmlReader.*DtdProcessing\.Parse",
                ],
                "severity": "high",
                "description": "XML External Entity (XXE) vulnerability detected",
                "recommendation": "Disable external entity processing and DTD processing in XML parsers.",
            }
        }

    def _init_data_exposure_patterns(self):
        """Initialize data exposure patterns."""
        self.data_exposure_patterns = {
            "error_disclosure": {
                "indicators": [
                    r"printStackTrace\(\)",
                    r"print.*exception.*details",
                    r"response.*write.*error.*stack",
                    r"debug\s*=\s*True",
                    r"display_errors\s*=\s*On",
                    r"error_reporting\(E_ALL\)",
                ],
                "severity": "medium",
                "description": "Sensitive error information disclosure detected",
                "recommendation": "Log errors securely and display generic error messages to users.",
            },
            "logs_exposure": {
                "indicators": [
                    r"log.*password",
                    r"logger.*credit.*card",
                    r"console\.log.*secret",
                    r"print.*api.*key",
                    r"debug.*token",
                ],
                "severity": "high",
                "description": "Sensitive data in logs detected",
                "recommendation": "Never log sensitive information like passwords, tokens, or credit card numbers.",
            },
            "unencrypted_storage": {
                "indicators": [
                    r"password.*plain.*text",
                    r"store.*credit.*card.*(?!.*encrypt)",
                    r"save.*ssn.*(?!.*hash)",
                    r"database.*password.*varchar",
                ],
                "severity": "critical",
                "description": "Unencrypted sensitive data storage detected",
                "recommendation": "Encrypt sensitive data at rest using strong encryption algorithms.",
            },
        }

    def _init_misconfiguration_patterns(self):
        """Initialize misconfiguration patterns."""
        self.misconfiguration_patterns = {
            "weak_crypto": {
                "indicators": [
                    r"MD5\(",
                    r"SHA1\(",
                    r"DES\.",
                    r"RC4",
                    r"crypto.*ECB",
                    r"Random\(\)(?!.*crypto)",
                    r"math\.random.*password",
                    r"rand\(\).*token",
                ],
                "severity": "high",
                "description": "Weak cryptographic algorithm detected",
                "recommendation": "Use strong cryptographic algorithms (AES-256, SHA-256+, etc.)",
            },
            "insecure_randomness": {
                "indicators": [
                    r"Random\(\).*(?:password|token|secret)",
                    r"math\.random.*(?:password|token|key)",
                    r"rand\(\).*(?:session|auth)",
                    r"mt_rand.*security",
                ],
                "severity": "high",
                "description": "Insecure random number generation detected",
                "recommendation": "Use cryptographically secure random number generators.",
            },
            "missing_security_headers": {
                "indicators": [
                    r"response\.setHeader.*(?!.*X-Frame-Options)",
                    r"header\(.*(?!.*Content-Security-Policy)",
                    r"HttpResponse.*(?!.*X-Content-Type-Options)",
                ],
                "severity": "medium",
                "description": "Missing security headers detected",
                "recommendation": "Implement security headers: CSP, X-Frame-Options, X-Content-Type-Options, etc.",
            },
            "debug_enabled": {
                "indicators": [
                    r"DEBUG\s*=\s*(?:True|true|1)",
                    r"app\.debug\s*=\s*True",
                    r"WP_DEBUG.*true",
                    r"FLASK_DEBUG\s*=\s*1",
                    r"NODE_ENV.*development",
                ],
                "severity": "medium",
                "description": "Debug mode enabled in production code",
                "recommendation": "Disable debug mode in production environments.",
            },
        }

    def _compile_all_patterns(self):
        """Compile all regex patterns for performance."""
        pattern_groups = [
            self.injection_patterns,
            self.xss_patterns,
            self.deserialization_patterns,
            self.xxe_patterns,
            self.data_exposure_patterns,
            self.misconfiguration_patterns,
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
            "name": "Vulnerability Scanner",
            "version": "2.0.0",
            "description": "Comprehensive OWASP Top 10 vulnerability scanner",
            "category": "security",
            "priority": "critical",
            "capabilities": [
                "SQL/NoSQL injection detection",
                "Command injection detection",
                "XSS vulnerability scanning",
                "XXE vulnerability detection",
                "Unsafe deserialization detection",
                "Cryptographic weakness identification",
                "Security misconfiguration detection",
                "Sensitive data exposure analysis",
                "OWASP Top 10 mapping",
            ],
            "supported_formats": list(self.config.code_extensions),
            "patterns_checked": len(self._compiled_patterns),
        }

    def _scan_file_for_vulnerabilities(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for vulnerabilities."""
        findings = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

                # Check all vulnerability patterns
                pattern_groups = [
                    ("injection", self.injection_patterns),
                    ("xss", self.xss_patterns),
                    ("deserialization", self.deserialization_patterns),
                    ("xxe", self.xxe_patterns),
                    ("data_exposure", self.data_exposure_patterns),
                    ("misconfiguration", self.misconfiguration_patterns),
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
                                if self._is_false_positive(line_content, vuln_type):
                                    continue

                                # Get OWASP category
                                owasp_category = self.owasp_categories.get(
                                    category, "Security Issue"
                                )

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
                                        "owasp_category": owasp_category,
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

    def _is_false_positive(self, line_content: str, vuln_type: str) -> bool:
        """Check if a detected vulnerability is likely a false positive."""
        line_lower = line_content.lower()

        # Skip comments
        comment_indicators = ["//", "#", "/*", "*", "<!--", "'''", '"""']
        for indicator in comment_indicators:
            if line_content.strip().startswith(indicator):
                return True

        # Skip test/example code
        if any(
            word in line_lower for word in ["test", "example", "sample", "demo", "mock"]
        ):
            return True

        # Skip import statements
        if any(
            keyword in line_lower
            for keyword in ["import ", "require(", "from ", "include"]
        ):
            if "sql" not in vuln_type:  # SQL imports might still be vulnerable
                return True

        # Skip documentation
        if any(
            word in line_lower
            for word in ["@param", "@return", "docstring", "@example"]
        ):
            return True

        return False

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file for vulnerabilities.

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
                f"{finding['description']} in {file_path.name} at line {finding['line_number']}. "
                f"Category: {finding['owasp_category']}. "
                f"This vulnerability could allow attackers to compromise the application's security."
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
                    "owasp_category": finding["owasp_category"],
                    "line_content": finding["line_content"],
                    "pattern_matched": finding["pattern_matched"],
                    "confidence": "high",
                },
            }
            all_findings.append(standardized)

        return all_findings

    def generate_summary_stats(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for vulnerabilities found."""
        if not findings:
            return {
                "total_vulnerabilities": 0,
                "severity_breakdown": {},
                "vulnerability_types": {},
                "owasp_categories": {},
                "security_score": 100.0,
            }

        # Count by severity
        severity_counts = defaultdict(int)
        vuln_type_counts = defaultdict(int)
        owasp_counts = defaultdict(int)

        for finding in findings:
            metadata = finding.get("metadata", {})
            severity_counts[finding["severity"]] += 1
            vuln_type_counts[metadata.get("vuln_type", "unknown")] += 1
            owasp_counts[metadata.get("owasp_category", "Unknown")] += 1

        # Calculate security score (0-100, higher is better)
        score_weights = {"critical": 20, "high": 10, "medium": 5, "low": 2}
        total_weight = sum(
            score_weights.get(sev, 1) * count for sev, count in severity_counts.items()
        )
        security_score = max(0, 100 - total_weight)

        return {
            "total_vulnerabilities": len(findings),
            "severity_breakdown": dict(severity_counts),
            "vulnerability_types": dict(vuln_type_counts),
            "owasp_categories": dict(owasp_counts),
            "security_score": round(security_score, 1),
            "critical_count": severity_counts.get("critical", 0),
            "high_count": severity_counts.get("high", 0),
        }


def main():
    """Main entry point for command-line usage."""
    analyzer = VulnerabilityScanner()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
