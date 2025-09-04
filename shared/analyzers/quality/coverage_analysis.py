#!/usr/bin/env python3
"""
Language-agnostic test coverage analysis script.
Analyzes test coverage across multiple programming languages and frameworks.

Converted to use BaseAnalyzer infrastructure for standardized CLI, file scanning,
error handling, and result formatting patterns.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import base analyzer (package root must be on PYTHONPATH)
from core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig


class TestCoverageAnalyzer(BaseAnalyzer):
    """Language-agnostic test coverage analyzer extending BaseAnalyzer infrastructure."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        super().__init__("test_coverage", config)

        # Language-specific test patterns and coverage tools
        self.language_configs = {
            "python": {
                "test_patterns": [r"test_.*\.py$", r".*_test\.py$", r"tests?/.*\.py$"],
                "source_patterns": [r".*\.py$"],
                "coverage_tools": ["coverage", "pytest-cov"],
                "coverage_files": [".coverage", "coverage.xml", "htmlcov/"],
                "exclude_dirs": ["__pycache__", ".pytest_cache", "venv", ".venv"],
            },
            "javascript": {
                "test_patterns": [
                    r".*\.test\.js$",
                    r".*\.spec\.js$",
                    r"__tests__/.*\.js$",
                    r"tests?/.*\.js$",
                ],
                "source_patterns": [r".*\.js$", r".*\.jsx$"],
                "coverage_tools": ["jest", "nyc", "c8"],
                "coverage_files": ["coverage/", ".nyc_output/", "coverage.json"],
                "exclude_dirs": ["node_modules", "coverage", "dist", "build"],
            },
            "typescript": {
                "test_patterns": [
                    r".*\.test\.ts$",
                    r".*\.spec\.ts$",
                    r"__tests__/.*\.ts$",
                ],
                "source_patterns": [r".*\.ts$", r".*\.tsx$"],
                "coverage_tools": ["jest", "nyc", "c8"],
                "coverage_files": ["coverage/", ".nyc_output/", "coverage.json"],
                "exclude_dirs": ["node_modules", "coverage", "dist", "build"],
            },
            "java": {
                "test_patterns": [
                    r".*Test\.java$",
                    r".*Tests\.java$",
                    r"src/test/.*\.java$",
                ],
                "source_patterns": [r".*\.java$"],
                "coverage_tools": ["jacoco", "cobertura"],
                "coverage_files": ["target/site/jacoco/", "target/cobertura/"],
                "exclude_dirs": ["target", ".gradle", "build"],
            },
            "go": {
                "test_patterns": [r".*_test\.go$"],
                "source_patterns": [r".*\.go$"],
                "coverage_tools": ["go test"],
                "coverage_files": ["coverage.out", "coverage.html"],
                "exclude_dirs": ["vendor/"],
            },
            "rust": {
                "test_patterns": [
                    r"tests/.*\.rs$",
                    r".*\.rs$",
                ],  # Rust tests can be in same file
                "source_patterns": [r".*\.rs$"],
                "coverage_tools": ["tarpaulin", "grcov"],
                "coverage_files": ["target/tarpaulin/", "target/debug/coverage/"],
                "exclude_dirs": ["target/"],
            },
            "csharp": {
                "test_patterns": [
                    r".*Test\.cs$",
                    r".*Tests\.cs$",
                    r".*\.Tests/.*\.cs$",
                ],
                "source_patterns": [r".*\.cs$"],
                "coverage_tools": ["coverlet", "dotcover"],
                "coverage_files": ["coverage.xml", "TestResults/"],
                "exclude_dirs": ["bin/", "obj/", "packages/"],
            },
            "ruby": {
                "test_patterns": [r".*_test\.rb$", r"test/.*\.rb$", r"spec/.*\.rb$"],
                "source_patterns": [r".*\.rb$"],
                "coverage_tools": ["simplecov"],
                "coverage_files": ["coverage/", ".resultset.json"],
                "exclude_dirs": ["vendor/", "coverage/"],
            },
            "php": {
                "test_patterns": [r".*Test\.php$", r"tests/.*\.php$"],
                "source_patterns": [r".*\.php$"],
                "coverage_tools": ["phpunit", "xdebug"],
                "coverage_files": ["coverage/", "clover.xml"],
                "exclude_dirs": ["vendor/", "coverage/"],
            },
            "cpp": {
                "test_patterns": [
                    r".*_test\.cpp$",
                    r".*_test\.cc$",
                    r"test.*\.cpp$",
                    r"tests/.*\.cpp$",
                ],
                "source_patterns": [
                    r".*\.cpp$",
                    r".*\.cc$",
                    r".*\.cxx$",
                    r".*\.c\+\+$",
                ],
                "coverage_tools": ["gcov", "lcov", "llvm-cov"],
                "coverage_files": ["coverage.info", "coverage/", "coverage.xml"],
                "exclude_dirs": [
                    "build/",
                    "cmake-build-*/",
                    ".vs/",
                    "Debug/",
                    "Release/",
                ],
            },
            "swift": {
                "test_patterns": [
                    r".*Tests\.swift$",
                    r".*Test\.swift$",
                    r"Tests/.*\.swift$",
                ],
                "source_patterns": [r".*\.swift$"],
                "coverage_tools": ["swift test", "xccov"],
                "coverage_files": [".build/debug/codecov/", "DerivedData/"],
                "exclude_dirs": [".build/", "DerivedData/", "Packages/"],
            },
            "kotlin": {
                "test_patterns": [r".*Test\.kt$", r".*Tests\.kt$", r"src/test/.*\.kt$"],
                "source_patterns": [r".*\.kt$", r".*\.kts$"],
                "coverage_tools": ["jacoco", "kover"],
                "coverage_files": ["build/reports/jacoco/", "build/reports/kover/"],
                "exclude_dirs": ["build/", ".gradle/", "out/"],
            },
        }

        # Generic test indicators (language-agnostic)
        self.generic_test_indicators = [
            r"test",
            r"spec",
            r"_test",
            r"Test",
            r"Tests",
            r"__tests__",
            r"assert",
            r"expect",
            r"should",
            r"describe",
            r"it\(",
            r"@Test",
            r"#[test]",
            r"func.*Test",
            r"def test_",
        ]

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file for coverage patterns - called by BaseAnalyzer for each file.

        Args:
            target_path: Single file path to analyze

        Returns:
            List of coverage analysis findings for this specific file
        """
        target = Path(target_path)

        if not target.is_file():
            return []

        # Since BaseAnalyzer calls this for individual files, we need to analyze
        # at the directory level to get meaningful coverage ratios
        # Check if this is a source or test file and categorize

        findings = []
        file_type = self.categorize_file(target)

        if file_type:
            # For each file, we generate a finding about its role in coverage
            finding = {
                "finding_id": f"FILE_CATEGORY_{file_type['language'].upper()}",
                "title": f"{file_type['language'].title()} {file_type['type'].title()} File",
                "description": f"File categorized as {file_type['type']} file for {file_type['language']}",
                "severity": "info",
                "file_path": str(target),
                "line_number": 1,
                "recommendation": f"Ensure {file_type['type']} files follow {file_type['language']} best practices for coverage analysis",
                "evidence": {
                    "file_type": file_type["type"],
                    "language": file_type["language"],
                    "patterns_matched": file_type.get("patterns_matched", []),
                },
            }
            findings.append(finding)

        return findings

    def categorize_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Categorize a file as test or source for a specific language."""
        # Map file extensions to languages
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c++": "cpp",
            ".c": "cpp",
            ".h": "cpp",
            ".hpp": "cpp",
            ".swift": "swift",
            ".kt": "kotlin",
            ".kts": "kotlin",
        }

        suffix = file_path.suffix.lower()
        if suffix not in ext_map:
            return None

        language = ext_map[suffix]
        config = self.language_configs.get(language, {})

        # Check test patterns first
        test_patterns = config.get("test_patterns", [])
        for pattern in test_patterns:
            if re.search(pattern, str(file_path)):
                return {
                    "language": language,
                    "type": "test",
                    "patterns_matched": [pattern],
                }

        # Check source patterns
        source_patterns = config.get("source_patterns", [])
        for pattern in source_patterns:
            if re.search(pattern, str(file_path)):
                return {
                    "language": language,
                    "type": "source",
                    "patterns_matched": [pattern],
                }

        return None

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Get coverage analyzer-specific metadata."""
        return {
            "analyzer_name": "TestCoverageAnalyzer",
            "analyzer_version": "2.0.0",
            "analysis_type": "test_coverage",
            "supported_languages": list(self.language_configs.keys()),
            "coverage_tools_supported": [
                tool
                for config in self.language_configs.values()
                for tool in config.get("coverage_tools", [])
            ],
            "description": "Language-agnostic test coverage analysis across multiple programming languages",
        }


# Legacy function for backward compatibility
def analyze_coverage(target_path: str, output_format: str = "json") -> dict:
    """
    Legacy function wrapper for backward compatibility.

    Args:
        target_path: Path to analyze
        output_format: Output format ("json" or "console")

    Returns:
        Analysis results dictionary
    """
    config = AnalyzerConfig(target_path=target_path, output_format=output_format)
    analyzer = TestCoverageAnalyzer(config)
    return analyzer.analyze(target_path)


if __name__ == "__main__":
    raise SystemExit(0)
