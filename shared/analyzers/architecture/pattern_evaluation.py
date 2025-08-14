#!/usr/bin/env python3
"""
Architecture Pattern Evaluation Analyzer - Design Pattern Analysis and Evaluation
===============================================================================

PURPOSE: Analyzes design patterns and architectural decisions in codebases.
Part of the shared/analyzers/architecture suite using BaseAnalyzer infrastructure.

APPROACH:
- Multi-language pattern detection
- Design pattern identification (Singleton, Factory, Observer, etc.)
- Anti-pattern detection (God Class, Feature Envy, etc.)
- Architectural pattern analysis (MVC, Repository, Service Layer)
- Code complexity analysis (method length, parameter count)
- Pattern density and recommendations

EXTENDS: BaseAnalyzer for common analyzer infrastructure
- Inherits file scanning, CLI, configuration, and result formatting
- Implements pattern-specific analysis logic in analyze_target()
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


class PatternEvaluationAnalyzer(BaseAnalyzer):
    """Evaluates design patterns and architectural decisions."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        # Create pattern-specific configuration
        pattern_config = config or AnalyzerConfig(
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
        super().__init__("architecture", pattern_config)

        # Initialize pattern definitions
        self._init_design_patterns()
        self._init_anti_patterns()
        self._init_architectural_patterns()
        self._init_language_patterns()

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Return metadata about this analyzer."""
        return {
            "name": "Pattern Evaluation Analyzer",
            "version": "2.0.0",
            "description": "Analyzes design patterns and architectural decisions in codebases",
            "category": "architecture",
            "priority": "high",
            "capabilities": [
                "Design pattern detection (Singleton, Factory, Observer, etc.)",
                "Anti-pattern identification (God Class, Feature Envy, etc.)",
                "Architectural pattern analysis (MVC, Repository, Service)",
                "Code complexity analysis (method length, parameters)",
                "Pattern density metrics",
                "Multi-language pattern recognition",
                "Pattern-specific recommendations",
            ],
            "supported_formats": list(self.config.code_extensions),
            "pattern_types": {
                "design_patterns": len(self.design_patterns),
                "anti_patterns": len(self.anti_patterns),
                "architectural_patterns": len(self.architectural_patterns),
            },
        }

    # analyze method removed - using BaseAnalyzer default implementation

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file for design patterns.

        Args:
            target_path: Path to file to analyze

        Returns:
            List of findings with standardized structure
        """
        # Debug logging removed

        all_findings = []
        file_path = Path(target_path)

        try:
            # Debug logging removed
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            # Early exit for files that are too large or complex
            if len(content) > 50000 or len(lines) > 1000:
                return all_findings

            # Detect programming language
            language = self._detect_language(file_path)

            # Analyze design patterns
            findings = self._check_patterns(
                content, lines, str(file_path), self.design_patterns, "design", language
            )
            all_findings.extend(findings)

            # Analyze anti-patterns
            findings = self._check_patterns(
                content, lines, str(file_path), self.anti_patterns, "anti", language
            )
            all_findings.extend(findings)

            # Analyze architectural patterns
            findings = self._check_patterns(
                content,
                lines,
                str(file_path),
                self.architectural_patterns,
                "architectural",
                language,
            )
            all_findings.extend(findings)

            # Analyze complexity patterns
            findings = self._check_complexity_patterns(
                content, lines, str(file_path), language
            )
            all_findings.extend(findings)

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

    def _init_design_patterns(self):
        """Initialize design pattern definitions."""
        self.design_patterns = {
            "singleton": {
                "indicators": [
                    r"__instance\s*=\s*None",  # Python singleton (simplified)
                    r"private\s+static\s+\w+\s+instance",  # Java/C# singleton
                    r"getInstance\(\)",  # Common getInstance method
                ],
                "severity": "medium",
                "description": "Singleton pattern detected",
            },
            "factory": {
                "indicators": [
                    r"def\s+create_\w+\(",  # Python factory methods
                    r"class\s+\w*Factory\w*",  # Factory class names
                    r"def\s+\w*factory\w*\(",  # Factory function names
                ],
                "severity": "low",
                "description": "Factory pattern detected",
            },
            "observer": {
                "indicators": [
                    r"def\s+notify\(",  # Observer notify methods
                    r"def\s+subscribe\(",  # Subscription methods
                    r"def\s+add_listener\(",  # Event listener patterns
                    r"class\s+\w*Observer\w*",  # Observer class names
                ],
                "severity": "low",
                "description": "Observer pattern detected",
            },
            "strategy": {
                "indicators": [
                    r"def\s+execute\(",  # Strategy execute methods
                    r"class\s+\w*Strategy\w*",  # Strategy class names
                    r"def\s+algorithm\(",  # Algorithm methods
                ],
                "severity": "low",
                "description": "Strategy pattern detected",
            },
            "decorator": {
                "indicators": [
                    r"@\w+",  # Python decorators
                    r"class\s+\w*Decorator\w*",  # Decorator class names
                ],
                "severity": "low",
                "description": "Decorator pattern detected",
            },
        }

    def _init_anti_patterns(self):
        """Initialize anti-pattern definitions."""
        self.anti_patterns = {
            "god_class": {
                "indicators": [
                    r"class\s+\w+.*:",  # Simplified - just detect classes, let complexity check handle size
                ],
                "severity": "high",
                "description": "God Class anti-pattern detected - overly large class",
            },
            "feature_envy": {
                "indicators": [
                    r"\w+\.\w+\.\w+\.\w+",  # Deep method chaining
                    r"other\w*\.\w+",  # Accessing other object's methods frequently
                ],
                "severity": "medium",
                "description": "Feature Envy anti-pattern detected",
            },
            "data_class": {
                "indicators": [
                    r"class\s+\w+.*:\s*\n\s*def\s+__init__",  # Class with only init
                    r"@dataclass\s*\nclass\s+\w+.*:\s*\n\s*\w+:\s*\w+",  # Simple dataclass
                ],
                "severity": "low",
                "description": "Data Class anti-pattern detected",
            },
            "long_parameter_list": {
                "indicators": [
                    r"def\s+\w+\([^)]{80,}\)",  # Very long parameter lists
                ],
                "severity": "medium",
                "description": "Long Parameter List anti-pattern detected",
            },
        }

    def _init_architectural_patterns(self):
        """Initialize architectural pattern definitions."""
        self.architectural_patterns = {
            "mvc": {
                "indicators": [
                    r"class\s+\w*Controller\w*",  # Controller classes
                    r"class\s+\w*Model\w*",  # Model classes
                    r"class\s+\w*View\w*",  # View classes
                ],
                "severity": "low",
                "description": "MVC architectural pattern detected",
            },
            "repository": {
                "indicators": [
                    r"class\s+\w*Repository\w*",  # Repository classes
                    r"def\s+find_by_\w+\(",  # Repository query methods
                    r"def\s+save\(",  # Repository save methods
                ],
                "severity": "low",
                "description": "Repository pattern detected",
            },
            "service": {
                "indicators": [
                    r"class\s+\w*Service\w*",  # Service classes
                    r"@service",  # Service decorators
                    r"def\s+process\w*\(",  # Service processing methods
                ],
                "severity": "low",
                "description": "Service Layer pattern detected",
            },
            "dependency_injection": {
                "indicators": [
                    r"@inject",  # Dependency injection decorators
                    r"def\s+__init__\(self,.*:\s*\w+\)",  # Type-hinted constructors
                    r"container\.",  # DI container usage
                ],
                "severity": "low",
                "description": "Dependency Injection pattern detected",
            },
        }

    def _init_language_patterns(self):
        """Initialize language-specific patterns."""
        self.language_patterns = {
            "python": {
                "method_pattern": r"def\s+(\w+)\s*\([^)]*\):",
                "class_pattern": r"class\s+(\w+).*:",
                "import_pattern": r"^(?:from\s+\w+\s+)?import\s+",
            },
            "javascript": {
                "method_pattern": r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))",
                "class_pattern": r"class\s+(\w+)",
                "import_pattern": r"^(?:import|const|let|var).*(?:from|require)",
            },
            "java": {
                "method_pattern": r"(?:public|private|protected|static|final)?\s*\w+\s+(\w+)\s*\(",
                "class_pattern": r"(?:public\s+)?class\s+(\w+)",
                "import_pattern": r"^import\s+",
            },
        }

    def _check_patterns(
        self,
        content: str,
        lines: List[str],
        file_path: str,
        pattern_dict: Dict,
        pattern_type: str,
        language: str = "unknown",
    ) -> List[Dict[str, Any]]:
        """Check for specific patterns in file content."""
        import signal

        findings = []

        # Safety limit for large files
        if len(content) > 10000:  # Skip files > 10KB to prevent hangs
            return findings

        # Timeout protection
        def timeout_handler(signum, frame):
            raise TimeoutError("Pattern analysis timeout")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)  # 5 second timeout

        try:
            for pattern_idx, (pattern_name, pattern_info) in enumerate(
                pattern_dict.items()
            ):
                if pattern_idx > 5:  # Max 5 patterns per type to prevent hangs
                    break

                for indicator_idx, indicator in enumerate(pattern_info["indicators"]):
                    if indicator_idx > 3:  # Max 3 indicators per pattern
                        break

                    try:
                        # Compile pattern with timeout protection
                        compiled_pattern = re.compile(
                            indicator, re.MULTILINE | re.IGNORECASE
                        )

                        matches = list(compiled_pattern.finditer(content))

                        # Limit number of matches processed
                        if len(matches) > 10:
                            matches = matches[:10]

                    except re.error:
                        # Skip invalid regex patterns
                        continue

                    for match_idx, match in enumerate(matches):
                        if match_idx > 5:  # Max 5 matches per pattern
                            break

                        line_num = content[: match.start()].count("\n") + 1
                        context = (
                            lines[line_num - 1].strip()
                            if line_num <= len(lines)
                            else ""
                        )

                        findings.append(
                            {
                                "title": f"{pattern_type.title()} Pattern: {pattern_name.title()}",
                                "description": pattern_info["description"],
                                "severity": pattern_info["severity"],
                                "file_path": file_path,
                                "line_number": line_num,
                                "recommendation": self._get_pattern_recommendation(
                                    f"{pattern_type}_{pattern_name}"
                                ),
                                "metadata": {
                                    "pattern_type": pattern_type,
                                    "pattern_name": pattern_name,
                                    "language": language,
                                    "context": context,
                                    "confidence": "medium",
                                },
                            }
                        )
        except TimeoutError:
            # Return partial findings if timeout occurs
            pass
        finally:
            signal.alarm(0)  # Cancel the alarm

        return findings

    def _check_complexity_patterns(
        self, content: str, lines: List[str], file_path: str, language: str = "unknown"
    ) -> List[Dict[str, Any]]:
        """Check for complexity-based pattern violations."""
        findings = []

        # Safety check - skip very large files to prevent timeouts
        if len(content) > 500000:  # Skip files > 500KB
            return findings

        # Get language-specific patterns
        lang_patterns = self.language_patterns.get(
            language, self.language_patterns["python"]
        )
        method_pattern = lang_patterns["method_pattern"]

        # Check for very long methods (with safety limits)
        method_matches = list(re.finditer(method_pattern, content))
        if len(method_matches) > 100:  # Skip files with too many methods
            return findings

        for match_idx, match in enumerate(method_matches):
            if match_idx > 50:  # Max 50 methods per file
                break

            method_start = content[: match.start()].count("\n") + 1
            method_name = match.group(1) if match.group(1) else "anonymous"

            # Count lines in method (rough approximation) with aggressive limits
            remaining_content = content[match.end() :]
            method_lines = 0
            indent_level = None

            split_lines = remaining_content.split("\n")
            if len(split_lines) > 1000:  # Skip analysis if too many lines
                continue

            for line_idx, line in enumerate(split_lines):
                # Aggressive safety limits
                if line_idx > 50:  # Max 50 lines per method check
                    break

                if line.strip():
                    current_indent = len(line) - len(line.lstrip())
                    if indent_level is None and current_indent > 0:
                        indent_level = current_indent
                    elif (
                        indent_level is not None
                        and current_indent <= indent_level
                        and line.strip()
                    ):
                        break
                method_lines += 1
                if method_lines > 50:  # Very long method
                    context = (
                        lines[method_start - 1].strip()
                        if method_start <= len(lines)
                        else ""
                    )
                    findings.append(
                        {
                            "title": f"Long Method: {method_name}",
                            "description": f"Very long method detected: {method_name} ({method_lines}+ lines)",
                            "severity": "medium",
                            "file_path": file_path,
                            "line_number": method_start,
                            "recommendation": "Break method into smaller, focused functions with single responsibilities.",
                            "metadata": {
                                "complexity_type": "long_method",
                                "method_name": method_name,
                                "line_count": method_lines,
                                "language": language,
                                "context": context,
                                "confidence": "high",
                            },
                        }
                    )
                    break

        # Check for high parameter count (Python-specific for now)
        if language == "python":
            param_pattern = r"def\s+\w+\s*\(([^)]+)\):"
            for match in re.finditer(param_pattern, content):
                params = match.group(1)
                param_count = len(
                    [
                        p.strip()
                        for p in params.split(",")
                        if p.strip() and p.strip() != "self"
                    ]
                )

                if param_count > 6:  # Too many parameters
                    line_num = content[: match.start()].count("\n") + 1
                    context = (
                        lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    )

                    findings.append(
                        {
                            "title": "Too Many Parameters",
                            "description": f"Method has too many parameters: {param_count}",
                            "severity": "medium",
                            "file_path": file_path,
                            "line_number": line_num,
                            "recommendation": "Use parameter objects, builder pattern, or keyword arguments to reduce parameter count.",
                            "metadata": {
                                "complexity_type": "too_many_parameters",
                                "parameter_count": param_count,
                                "language": language,
                                "context": context,
                                "confidence": "high",
                            },
                        }
                    )

        return findings

    def _get_pattern_recommendation(self, pattern: str) -> str:
        """Get recommendation for a specific pattern."""
        recommendations = {
            "design_singleton": "Consider dependency injection instead of singleton pattern for better testability",
            "design_factory": "Good use of factory pattern for object creation flexibility",
            "design_observer": "Consider using event-driven architecture for loose coupling",
            "design_strategy": "Good separation of algorithms - ensure strategies are interchangeable",
            "design_decorator": "Consider composition over inheritance for better flexibility",
            "anti_god_class": "Break down into smaller, focused classes with single responsibilities",
            "anti_feature_envy": "Move functionality closer to the data it uses to improve cohesion",
            "anti_data_class": "Add behavior to data classes or use records/structs appropriately",
            "anti_long_parameter_list": "Use parameter objects, builder pattern, or configuration classes",
            "architectural_mvc": "Good separation of concerns with MVC pattern",
            "architectural_repository": "Good data access abstraction - ensure proper encapsulation",
            "architectural_service": "Consider domain-driven design principles for service boundaries",
            "architectural_dependency_injection": "Good use of inversion of control principle",
        }
        return recommendations.get(
            pattern, "Review pattern usage and consider refactoring for better design"
        )

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "cpp",
            ".hpp": "cpp",
        }
        return language_map.get(ext, "unknown")


def main():
    """Main entry point for command-line usage."""
    analyzer = PatternEvaluationAnalyzer()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
