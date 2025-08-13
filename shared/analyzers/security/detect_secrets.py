#!/usr/bin/env python3
"""
Secrets Detection Analyzer - Hardcoded Credentials and Sensitive Data Scanner
=============================================================================

PURPOSE: Detects hardcoded secrets, credentials, and sensitive data in source code.
Part of the shared/analyzers/security suite using BaseAnalyzer infrastructure.

APPROACH:
- Pattern-based detection for various secret types
- API keys, passwords, database URLs
- JWT secrets, AWS keys, private keys
- Environment-specific secret detection

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


class SecretsDetectionAnalyzer(BaseAnalyzer):
    """Detects hardcoded secrets and credentials in source code."""

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
                ".vue",
                ".xml",
                ".json",
                ".yml",
                ".yaml",
                ".env",
                ".properties",
                ".ini",
                ".cfg",
                ".conf",
                ".toml",
                ".config",
                ".sh",
                ".bash",
                ".zsh",
                ".fish",
                ".ps1",
                ".bat",
                ".cmd",
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

        # Secret detection patterns
        self.secret_patterns = {
            "hardcoded_password": {
                "patterns": [
                    r'(?i)(password|passwd|pwd|pass)\s*[=:]\s*["\']([^"\']{3,})["\']',
                    r'(?i)(password|passwd|pwd|pass)\s*=\s*(?!None|null|undefined|false|true|0|""|\'\'|<|{|\[)([^"\'\s]{3,})',
                ],
                "severity": "critical",
                "description": "Hardcoded password detected",
                "recommendation": "Store passwords in environment variables or secure vaults. Never commit passwords to version control.",
            },
            "api_key": {
                "patterns": [
                    r'(?i)(api[_-]?key|apikey|api[_-]?secret)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
                    r'(?i)(x[_-]?api[_-]?key|api[_-]?token)\s*[=:]\s*["\']([^"\']{10,})["\']',
                ],
                "severity": "critical",
                "description": "Hardcoded API key found",
                "recommendation": "Move API keys to environment variables or use a secrets management service.",
            },
            "database_url": {
                "patterns": [
                    r'(?i)(database[_-]?url|db[_-]?url|connection[_-]?string)\s*[=:]\s*["\']([^"\']*://[^"\']+)["\']',
                    r'(?i)mongodb(?:\+srv)?://[^"\'\s]+',
                    r'(?i)postgres(?:ql)?://[^"\'\s]+',
                    r'(?i)mysql://[^"\'\s]+',
                    r'(?i)redis://[^"\'\s]+',
                ],
                "severity": "high",
                "description": "Database connection string with credentials",
                "recommendation": "Use environment variables for database URLs. Consider using connection pooling with secure credential storage.",
            },
            "jwt_secret": {
                "patterns": [
                    r'(?i)(jwt[_-]?secret|jwt[_-]?key|token[_-]?secret)\s*[=:]\s*["\']([^"\']{10,})["\']',
                    r'(?i)secret[_-]?key\s*[=:]\s*["\']([^"\']{10,})["\']',
                ],
                "severity": "critical",
                "description": "JWT/Token secret exposed",
                "recommendation": "Generate strong random secrets and store them in environment variables. Rotate secrets regularly.",
            },
            "aws_credentials": {
                "patterns": [
                    r'(?i)aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*["\']([A-Z0-9]{20})["\']',
                    r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']([A-Za-z0-9/+=]{40})["\']',
                    r"AKIA[0-9A-Z]{16}",
                ],
                "severity": "critical",
                "description": "AWS credentials detected",
                "recommendation": "Use AWS IAM roles or AWS Secrets Manager. Never commit AWS credentials to source code.",
            },
            "private_key": {
                "patterns": [
                    r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
                    r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----",
                    r"-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----",
                    r"-----BEGIN\s+EC\s+PRIVATE\s+KEY-----",
                    r"-----BEGIN\s+PGP\s+PRIVATE\s+KEY-----",
                ],
                "severity": "critical",
                "description": "Private cryptographic key exposed",
                "recommendation": "Never commit private keys to version control. Use secure key management systems.",
            },
            "github_token": {
                "patterns": [
                    r"ghp_[a-zA-Z0-9]{36}",
                    r"gho_[a-zA-Z0-9]{36}",
                    r"ghu_[a-zA-Z0-9]{36}",
                    r"ghs_[a-zA-Z0-9]{36}",
                    r"ghr_[a-zA-Z0-9]{36}",
                ],
                "severity": "critical",
                "description": "GitHub access token detected",
                "recommendation": "Revoke this token immediately and use GitHub's encrypted secrets for CI/CD.",
            },
            "google_api": {
                "patterns": [
                    r"AIza[0-9A-Za-z\-_]{35}",
                    r'(?i)google[_-]?api[_-]?key\s*[=:]\s*["\']([^"\']{30,})["\']',
                ],
                "severity": "high",
                "description": "Google API key exposed",
                "recommendation": "Restrict API key usage and store in environment variables.",
            },
            "slack_token": {
                "patterns": [
                    r"xox[baprs]-[0-9]{10,48}",
                    r'(?i)slack[_-]?token\s*[=:]\s*["\']([^"\']{30,})["\']',
                ],
                "severity": "high",
                "description": "Slack token detected",
                "recommendation": "Use OAuth and store tokens securely. Rotate tokens regularly.",
            },
            "stripe_key": {
                "patterns": [
                    r"sk_live_[0-9a-zA-Z]{24,}",
                    r"rk_live_[0-9a-zA-Z]{24,}",
                ],
                "severity": "critical",
                "description": "Stripe live API key exposed",
                "recommendation": "Revoke immediately! Use Stripe's restricted keys and environment variables.",
            },
            "oauth_secret": {
                "patterns": [
                    r'(?i)(client[_-]?secret|oauth[_-]?secret)\s*[=:]\s*["\']([^"\']{10,})["\']',
                    r'(?i)(app[_-]?secret|application[_-]?secret)\s*[=:]\s*["\']([^"\']{10,})["\']',
                ],
                "severity": "high",
                "description": "OAuth client secret exposed",
                "recommendation": "Regenerate client secrets and use secure storage. Implement PKCE for public clients.",
            },
            "encryption_key": {
                "patterns": [
                    r'(?i)(encryption[_-]?key|encrypt[_-]?key|crypto[_-]?key)\s*[=:]\s*["\']([^"\']{16,})["\']',
                    r'(?i)(aes[_-]?key|des[_-]?key)\s*[=:]\s*["\']([^"\']{8,})["\']',
                ],
                "severity": "critical",
                "description": "Encryption key exposed",
                "recommendation": "Use key management services (KMS) and never store encryption keys in code.",
            },
        }

        # Compiled patterns cache
        self._compiled_patterns = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for secret_type, config in self.secret_patterns.items():
            self._compiled_patterns[secret_type] = [
                re.compile(pattern, re.MULTILINE | re.DOTALL)
                for pattern in config["patterns"]
            ]

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "Secrets Detection Analyzer",
            "version": "2.0.0",
            "description": "Detects hardcoded secrets and credentials in source code",
            "category": "security",
            "priority": "critical",
            "capabilities": [
                "Password detection",
                "API key scanning",
                "Private key detection",
                "Cloud credential scanning",
                "OAuth secret detection",
                "Database URL scanning",
                "JWT secret detection",
                "Encryption key detection",
            ],
            "supported_formats": list(self.config.code_extensions),
            "patterns_checked": len(self.secret_patterns),
        }

    def _scan_file_for_secrets(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for secrets."""
        findings = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

                # Check each secret pattern
                for secret_type, patterns in self._compiled_patterns.items():
                    config = self.secret_patterns[secret_type]

                    for pattern in patterns:
                        for match in pattern.finditer(content):
                            # Calculate line number
                            line_start = content[: match.start()].count("\n") + 1

                            # Extract the matched value (safely)
                            matched_groups = match.groups()
                            if matched_groups:
                                # Get the last group which is usually the secret value
                                secret_value = (
                                    matched_groups[-1]
                                    if len(matched_groups) > 0
                                    else match.group(0)
                                )
                            else:
                                secret_value = match.group(0)

                            # Mask the secret value for display
                            if len(secret_value) > 8:
                                masked_value = (
                                    secret_value[:4] + "***" + secret_value[-4:]
                                )
                            else:
                                masked_value = "***"

                            # Get the line content
                            line_content = (
                                lines[line_start - 1].strip()
                                if line_start <= len(lines)
                                else ""
                            )

                            # Skip false positives
                            if self._is_false_positive(
                                line_content, secret_value, secret_type
                            ):
                                continue

                            findings.append(
                                {
                                    "secret_type": secret_type,
                                    "file_path": str(file_path),
                                    "line_number": line_start,
                                    "line_content": line_content[
                                        :100
                                    ],  # Truncate long lines
                                    "masked_value": masked_value,
                                    "severity": config["severity"],
                                    "description": config["description"],
                                    "recommendation": config["recommendation"],
                                }
                            )

        except Exception as e:
            # Log but continue - file might be binary or inaccessible
            if self.verbose:
                print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)

        return findings

    def _is_false_positive(
        self, line_content: str, secret_value: str, secret_type: str
    ) -> bool:
        """Check if a detected secret is likely a false positive."""
        # Common false positive patterns
        false_positive_indicators = [
            "example",
            "sample",
            "test",
            "demo",
            "dummy",
            "placeholder",
            "your-",
            "my-",
            "xxx",
            "todo",
            "change-me",
            "replace",
            "<",
            ">",
            "${",
            "{{",
            "process.env",
            "os.environ",
            "getenv",
            "ENV[",
            "config.",
            "settings.",
            "options.",
        ]

        line_lower = line_content.lower()
        value_lower = secret_value.lower()

        # Check for placeholder values
        for indicator in false_positive_indicators:
            if indicator in value_lower or indicator in line_lower:
                return True

        # Check for environment variable references
        if "$" in secret_value or "%" in secret_value:
            return True

        # Check for obvious non-secrets
        if secret_value in [
            "password",
            "secret",
            "key",
            "token",
            "undefined",
            "null",
            "none",
            "true",
            "false",
        ]:
            return True

        # Check for import/require statements
        if any(
            keyword in line_lower
            for keyword in ["import ", "require(", "from ", "include"]
        ):
            return True

        return False

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file for hardcoded secrets.

        Args:
            target_path: Path to file to analyze

        Returns:
            List of findings with standardized structure
        """
        all_findings = []
        file_path = Path(target_path)

        # Skip files that are too large
        if file_path.stat().st_size > 1024 * 1024:  # Skip files > 1MB
            return all_findings

        findings = self._scan_file_for_secrets(file_path)

        # Convert to standardized finding format
        for finding in findings:
            standardized = self.create_finding(
                title=f"{finding['description']}: {finding['secret_type']}",
                description=f"{finding['description']} in {file_path.name}. "
                f"Secret type: {finding['secret_type'].replace('_', ' ').title()}. "
                f"This could lead to unauthorized access if exposed.",
                severity=finding["severity"],
                file_path=finding["file_path"],
                line_number=finding["line_number"],
                recommendation=finding["recommendation"],
                metadata={
                    "secret_type": finding["secret_type"],
                    "line_content": finding["line_content"],
                    "masked_value": finding["masked_value"],
                    "confidence": "high",
                },
            )
            all_findings.append(standardized)

        return all_findings


def main():
    """Main entry point for command-line usage."""
    analyzer = SecretsDetectionAnalyzer()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
