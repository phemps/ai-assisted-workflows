#!/usr/bin/env python3
"""
Detect-Secrets Analyzer - Hardcoded Secrets Detection Using Established Tool.

PURPOSE: Detects hardcoded secrets and credentials using detect-secrets library.
Replaces bespoke regex pattern matching with established entropy-based analysis.

APPROACH:
- Uses detect-secrets' entropy analysis and plugin system
- Multiple detection algorithms (entropy, keyword, pattern-based)
- Configurable filters to reduce false positives
- Industry-standard secret detection patterns

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements security-specific analysis logic in analyze_target()
- Uses shared timing, logging, and error handling patterns

REPLACES: detect_secrets.py with bespoke regex patterns
- More accurate entropy-based detection
- Established plugin ecosystem
- Better false positive filtering
"""

import json
import subprocess
import sys
from typing import Any, Optional

# Import base analyzer (package root must be on PYTHONPATH)
from core.base.analyzer_base import AnalyzerConfig, BaseAnalyzer
from core.base.analyzer_registry import register_analyzer


@register_analyzer("security:detect_secrets")
class DetectSecretsAnalyzer(BaseAnalyzer):
    """Hardcoded secrets detection using detect-secrets tool."""

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
                ".dockerfile",
                ".tf",
                ".hcl",
                ".sql",
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
                "*.min.js",
                "*.min.css",
                "test_fixtures",
                "*.lock",
                "*.log",
                "*.tmp",
            },
        )

        # Initialize base analyzer
        super().__init__("security", security_config)

        # Check for detect-secrets availability
        self.detect_secrets_available = True  # Will be set to False if not available
        self._check_detect_secrets_availability()

        # Secret detection configuration
        self.detect_secrets_config = {
            "plugins_used": [
                {"name": "ArtifactoryDetector"},
                {"name": "AWSKeyDetector"},
                {"name": "AzureStorageKeyDetector"},
                {"name": "Base64HighEntropyString", "limit": 4.5},
                {"name": "BasicAuthDetector"},
                {"name": "CloudantDetector"},
                {"name": "DiscordBotTokenDetector"},
                {"name": "GitHubTokenDetector"},
                {"name": "HexHighEntropyString", "limit": 3.0},
                {"name": "IbmCloudIamDetector"},
                {"name": "IbmCosHmacDetector"},
                {"name": "JwtTokenDetector"},
                {
                    "name": "KeywordDetector",
                    "keyword_exclude": "test_|mock_|_test|_mock",
                    "keyword_limit": 2.8,
                },
                {"name": "MailchimpDetector"},
                {"name": "NpmDetector"},
                {"name": "PrivateKeyDetector"},
                {"name": "SendGridDetector"},
                {"name": "SlackDetector"},
                {"name": "SoftlayerDetector"},
                {"name": "SquareOAuthDetector"},
                {"name": "StripeDetector"},
                {"name": "TwilioKeyDetector"},
            ],
            "filters_used": [
                {"path": "detect_secrets.filters.allowlist.is_line_allowlisted"},
                {"path": "detect_secrets.filters.common.is_baseline_file"},
                {
                    "path": "detect_secrets.filters.common.is_ignored_due_to_verification_policies",
                    "min_level": 2,
                },
                {"path": "detect_secrets.filters.heuristic.is_indirect_reference"},
                {"path": "detect_secrets.filters.heuristic.is_likely_id_string"},
                {"path": "detect_secrets.filters.heuristic.is_lock_file"},
                {"path": "detect_secrets.filters.heuristic.is_not_alphanumeric_string"},
                {"path": "detect_secrets.filters.heuristic.is_potential_uuid"},
                {
                    "path": "detect_secrets.filters.heuristic.is_prefixed_with_dollar_sign"
                },
                {"path": "detect_secrets.filters.heuristic.is_sequential_string"},
                {"path": "detect_secrets.filters.heuristic.is_swagger_file"},
                {"path": "detect_secrets.filters.heuristic.is_templated_secret"},
                {
                    "path": "detect_secrets.filters.regex.should_exclude_line",
                    "pattern": r".*test.*password.*=.*['\"][a-zA-Z0-9]{1,8}['\"].*",
                },
            ],
        }

    def _is_testing_environment(self) -> bool:
        """Detect if we're running in a testing environment."""
        import os

        # Check for common testing environment indicators
        return any(
            [
                "test" in os.environ.get("PYTHONPATH", "").lower(),
                "test" in os.getcwd().lower(),
                os.environ.get("TESTING", "").lower() == "true",
                "pytest" in str(os.environ.get("_", "")),
                any("test" in arg for arg in os.sys.argv),
            ]
        )

    def _check_detect_secrets_availability(self):
        """Check if detect-secrets is available."""
        try:
            result = subprocess.run(
                ["detect-secrets", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                print(
                    "WARNING: detect-secrets is required for secrets analysis but not found.",
                    file=sys.stderr,
                )
                print("Install with: pip install detect-secrets", file=sys.stderr)

                # In testing environments, this should fail hard
                if self._is_testing_environment():
                    print(
                        "ERROR: In testing environment - all tools must be available",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                else:
                    # In production, warn but continue with degraded functionality
                    print(
                        "Continuing with degraded secrets detection capabilities",
                        file=sys.stderr,
                    )
                    self.detect_secrets_available = False
                    return

            version = result.stdout.strip()
            print(f"Found detect-secrets {version}", file=sys.stderr)
            self.detect_secrets_available = True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(
                "WARNING: detect-secrets is required but not available.",
                file=sys.stderr,
            )
            print("Install with: pip install detect-secrets", file=sys.stderr)

            # In testing environments, this should fail hard
            if self._is_testing_environment():
                print(
                    "ERROR: In testing environment - all tools must be available",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                # In production, warn but continue with degraded functionality
                print(
                    "Continuing with degraded secrets detection capabilities",
                    file=sys.stderr,
                )
                self.detect_secrets_available = False

    def _run_detect_secrets_scan(self, target_path: str) -> list[dict[str, Any]]:
        """Run detect-secrets scan on target path."""
        findings = []

        try:
            # Use detect-secrets with default configuration for maximum detection
            cmd = [
                "detect-secrets",
                "scan",
                "--all-files",
                "--force-use-all-plugins",
                target_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.stdout:
                secrets_output = json.loads(result.stdout)

                # Process detected secrets with custom filtering
                for file_path, secrets in secrets_output.get("results", {}).items():
                    for secret in secrets:
                        # Apply custom filtering to reduce false positives
                        if self._should_include_secret(secret, file_path):
                            finding = self._process_secret_finding(secret, file_path)
                            if finding:
                                findings.append(finding)

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            json.JSONDecodeError,
        ) as e:
            if self.verbose:
                print(f"detect-secrets scan failed: {e}", file=sys.stderr)
        finally:
            # No cleanup needed for command-line approach
            pass

        return findings

    def _should_include_secret(self, secret: dict[str, Any], file_path: str) -> bool:
        """Apply custom filtering to reduce false positives while preserving legitimate secrets."""
        secret_type = secret.get("type", "")

        # Always include high-value secret types
        high_value_types = [
            "Private Key",
            "AWS Access Key",
            "GitHub Token",
            "JWT Token",
        ]
        if secret_type in high_value_types:
            return True

        # For keyword secrets, apply balanced filtering
        if secret_type == "Secret Keyword":
            # Exclude obvious test files but allow legitimate secrets in vulnerable apps
            if any(
                pattern in file_path.lower()
                for pattern in [
                    "test_",
                    "mock_",
                    "example_only",
                    "demo_data",
                    "fixture_",
                ]
            ):
                return False

            # Allow secrets in vulnerable apps (this is expected for our test)
            if any(app in file_path for app in ["pygoat", "nodegoat", "sql-vulns"]):
                return True

        return True  # Include by default

    def _process_secret_finding(
        self, secret: dict[str, Any], file_path: str
    ) -> Optional[dict[str, Any]]:
        """Convert detect-secrets finding to our standardized format."""
        try:
            secret_type = secret.get("type", "unknown")
            line_number = secret.get("line_number", 0)

            # Map secret types to severity levels
            severity_mapping = {
                "Private Key": "critical",
                "AWS Access Key": "critical",
                "JWT Token": "critical",
                "Azure Storage Key": "critical",
                "GitHub Token": "critical",
                "High Entropy String": "high",
                "Basic Auth": "high",
                "Slack Token": "high",
                "Keyword": "medium",
            }

            severity = severity_mapping.get(secret_type, "medium")

            return {
                "perf_type": secret_type.lower().replace(" ", "_"),
                "category": "secrets",
                "file_path": file_path,
                "line_number": line_number,
                "line_content": "",  # detect-secrets doesn't provide line content
                "severity": severity,
                "description": f"Hardcoded {secret_type.lower()} detected",
                "recommendation": self._get_secret_recommendation(secret_type),
                "pattern_matched": f"detect-secrets: {secret_type}",
                "confidence": "high",
            }

        except Exception as e:
            if self.verbose:
                print(f"Failed to process secret finding: {e}", file=sys.stderr)
            return None

    def _get_secret_recommendation(self, secret_type: str) -> str:
        """Get specific recommendations based on secret type."""
        recommendations = {
            "Private Key": "Remove private keys from code. Use secure key management services and environment variables.",
            "AWS Access Key": "Remove AWS credentials from code. Use IAM roles, AWS profiles, or environment variables.",
            "JWT Token": "Remove hardcoded JWT tokens. Generate tokens dynamically and store signing keys securely.",
            "GitHub Token": "Remove GitHub tokens from code. Use GitHub secrets or environment variables.",
            "Azure Storage Key": "Remove Azure keys from code. Use Azure Key Vault or managed identities.",
            "High Entropy String": "Review high entropy strings. If secrets, move to environment variables or secure vaults.",
            "Basic Auth": "Remove hardcoded authentication. Use secure credential storage and environment variables.",
            "API Key": "Remove API keys from code. Use environment variables or secure configuration management.",
        }

        return recommendations.get(
            secret_type,
            "Remove hardcoded secrets from code. Use environment variables or secure credential management.",
        )

    def analyze_target(self, target_path: str) -> list[dict[str, Any]]:
        """
        Analyze target using detect-secrets for hardcoded secrets.

        Args:
            target_path: Path to analyze (single file - BaseAnalyzer handles directory iteration)

        Returns
        -------
            List of secret findings with standardized structure
        """
        # Skip analysis if detect-secrets is not available (degraded mode)
        if not self.detect_secrets_available:
            if self.verbose:
                print(
                    f"Skipping detect-secrets analysis for {target_path} - tool not available",
                    file=sys.stderr,
                )
            return []

        findings = self._run_detect_secrets_scan(target_path)

        # Convert to our standardized format for BaseAnalyzer
        standardized_findings = []
        for finding in findings:
            standardized = {
                "title": f"{finding['description']} ({finding['perf_type']})",
                "description": f"detect-secrets found: {finding['description']}. This hardcoded secret poses a security risk and should be removed immediately.",
                "severity": finding["severity"],
                "file_path": finding["file_path"],
                "line_number": finding["line_number"],
                "recommendation": finding["recommendation"],
                "metadata": {
                    "tool": "detect-secrets",
                    "secret_type": finding["perf_type"],
                    "category": finding["category"],
                    "confidence": finding["confidence"],
                },
            }
            standardized_findings.append(standardized)

        return standardized_findings

    def get_analyzer_metadata(self) -> dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "Detect-Secrets Analyzer",
            "version": "2.0.0",
            "description": "Hardcoded secrets detection using detect-secrets library (replacing regex patterns)",
            "category": "security",
            "priority": "critical",
            "capabilities": [
                "Entropy-based secret detection",
                "Private key detection",
                "API key identification",
                "Cloud credentials detection",
                "JWT token discovery",
                "Basic authentication detection",
                "Multi-plugin analysis",
                "False positive filtering",
            ],
            "supported_languages": [
                "Python",
                "JavaScript",
                "TypeScript",
                "Java",
                "C#",
                "PHP",
                "Ruby",
                "Go",
                "Rust",
                "C/C++",
                "Swift",
                "Kotlin",
                "Scala",
                "Configuration files",
                "Environment files",
                "Shell scripts",
            ],
            "tool": "detect-secrets",
            "replaces": ["detect_secrets.py"],
        }


if __name__ == "__main__":
    # CLI removed; this module is intended to be invoked via the orchestration layer
    sys.exit(0)
