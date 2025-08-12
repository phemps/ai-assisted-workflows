#!/usr/bin/env python3
"""
Pattern Classification Engine
Part of Phase 2.3: Analysis Engine - Pattern Classification

This module implements sophisticated pattern classification for code analysis,
identifying anti-patterns, design patterns, code smells, and best practices.
"""

import ast
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging
from abc import ABC, abstractmethod
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Classification of different pattern types."""

    DESIGN_PATTERN = "design_pattern"
    ANTI_PATTERN = "anti_pattern"
    CODE_SMELL = "code_smell"
    BEST_PRACTICE = "best_practice"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"


class PatternSeverity(Enum):
    """Severity levels for detected patterns."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class PatternMatch:
    """Represents a detected pattern in code."""

    pattern_name: str
    pattern_type: PatternType
    severity: PatternSeverity
    file_path: str
    start_line: int
    end_line: int
    confidence: float
    description: str
    recommendation: str
    code_snippet: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class PatternDetector(ABC):
    """Abstract base class for pattern detectors."""

    @abstractmethod
    def detect_patterns(self, code: str, file_path: str) -> List[PatternMatch]:
        """Detect patterns in the given code."""
        pass

    @abstractmethod
    def get_pattern_types(self) -> List[PatternType]:
        """Get the types of patterns this detector can find."""
        pass


class AntiPatternDetector(PatternDetector):
    """Detects common anti-patterns in code."""

    def __init__(self):
        self.patterns = {
            "god_class": self._detect_god_class,
            "long_method": self._detect_long_method,
            "feature_envy": self._detect_feature_envy,
            "data_clumps": self._detect_data_clumps,
            "primitive_obsession": self._detect_primitive_obsession,
            "shotgun_surgery": self._detect_shotgun_surgery,
            "refused_bequest": self._detect_refused_bequest,
        }

    def detect_patterns(self, code: str, file_path: str) -> List[PatternMatch]:
        """Detect anti-patterns in code."""
        matches = []

        try:
            tree = ast.parse(code)

            for pattern_name, detector_func in self.patterns.items():
                try:
                    pattern_matches = detector_func(tree, code, file_path)
                    matches.extend(pattern_matches)
                except Exception as e:
                    logger.debug(f"Error detecting {pattern_name}: {e}")

        except SyntaxError:
            logger.debug(f"Syntax error in {file_path}")

        return matches

    def get_pattern_types(self) -> List[PatternType]:
        return [PatternType.ANTI_PATTERN]

    def _detect_god_class(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect god class anti-pattern (classes with too many responsibilities)."""
        matches = []

        class GodClassVisitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                attributes = []

                # Count attribute assignments in __init__
                for n in node.body:
                    if isinstance(n, ast.FunctionDef) and n.name == "__init__":
                        for stmt in ast.walk(n):
                            if isinstance(stmt, ast.Attribute) and isinstance(
                                stmt.ctx, ast.Store
                            ):
                                attributes.append(stmt.attr)

                # God class heuristics
                method_count = len(methods)
                attr_count = len(set(attributes))
                lines = (
                    node.end_lineno - node.lineno if hasattr(node, "end_lineno") else 0
                )

                if method_count > 20 or attr_count > 15 or lines > 500:
                    severity = (
                        PatternSeverity.HIGH
                        if method_count > 30
                        else PatternSeverity.MEDIUM
                    )
                    confidence = min(0.9, (method_count + attr_count) / 50)

                    matches.append(
                        PatternMatch(
                            pattern_name="God Class",
                            pattern_type=PatternType.ANTI_PATTERN,
                            severity=severity,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            confidence=confidence,
                            description=f"Class '{node.name}' has too many responsibilities "
                            f"({method_count} methods, {attr_count} attributes)",
                            recommendation="Consider breaking this class into smaller, more focused classes using Single Responsibility Principle",
                            code_snippet=f"class {node.name}:",
                            metadata={
                                "methods": method_count,
                                "attributes": attr_count,
                                "lines": lines,
                            },
                        )
                    )

                self.generic_visit(node)

        visitor = GodClassVisitor()
        visitor.visit(tree)
        return matches

    def _detect_long_method(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect long method anti-pattern."""
        matches = []

        class LongMethodVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                lines = getattr(node, "end_lineno", node.lineno) - node.lineno

                if lines > 50:  # Threshold for long method
                    severity = (
                        PatternSeverity.HIGH if lines > 100 else PatternSeverity.MEDIUM
                    )
                    confidence = min(0.95, lines / 150)

                    matches.append(
                        PatternMatch(
                            pattern_name="Long Method",
                            pattern_type=PatternType.ANTI_PATTERN,
                            severity=severity,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            confidence=confidence,
                            description=f"Method '{node.name}' is too long ({lines} lines)",
                            recommendation="Break this method into smaller, more focused methods",
                            code_snippet=f"def {node.name}({', '.join([arg.arg for arg in node.args.args])}):",
                            metadata={"lines": lines},
                        )
                    )

                self.generic_visit(node)

        visitor = LongMethodVisitor()
        visitor.visit(tree)
        return matches

    def _detect_feature_envy(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect feature envy anti-pattern (method uses another class more than its own)."""
        matches = []

        class FeatureEnvyVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None
                self.current_method = None

            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class

            def visit_FunctionDef(self, node):
                if self.current_class:  # Only check methods, not standalone functions
                    old_method = self.current_method
                    self.current_method = node

                    # Count attribute accesses
                    external_accesses = []
                    self_accesses = 0

                    for child in ast.walk(node):
                        if isinstance(child, ast.Attribute):
                            if isinstance(child.value, ast.Name):
                                if child.value.id == "self":
                                    self_accesses += 1
                                else:
                                    external_accesses.append(child.value.id)

                    # Feature envy heuristic
                    if external_accesses and len(external_accesses) > self_accesses * 2:
                        most_used = max(
                            set(external_accesses), key=external_accesses.count
                        )
                        usage_count = external_accesses.count(most_used)

                        matches.append(
                            PatternMatch(
                                pattern_name="Feature Envy",
                                pattern_type=PatternType.ANTI_PATTERN,
                                severity=PatternSeverity.MEDIUM,
                                file_path=file_path,
                                start_line=node.lineno,
                                end_line=getattr(node, "end_lineno", node.lineno),
                                confidence=min(0.8, usage_count / 10),
                                description=f"Method '{node.name}' seems more interested in class '{most_used}' than its own class",
                                recommendation=f"Consider moving this method to the '{most_used}' class or refactoring the design",
                                code_snippet=f"def {node.name}():",
                                metadata={
                                    "external_accesses": len(external_accesses),
                                    "self_accesses": self_accesses,
                                },
                            )
                        )

                    self.current_method = old_method

                self.generic_visit(node)

        visitor = FeatureEnvyVisitor()
        visitor.visit(tree)
        return matches

    def _detect_data_clumps(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect data clumps (same set of parameters appearing together frequently)."""
        matches = []

        # Track parameter groups
        parameter_groups = []

        class DataClumpVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if (
                    len(node.args.args) >= 3
                ):  # Only consider functions with multiple parameters
                    params = [arg.arg for arg in node.args.args if arg.arg != "self"]
                    if len(params) >= 3:
                        parameter_groups.append((tuple(sorted(params)), node))
                self.generic_visit(node)

        visitor = DataClumpVisitor()
        visitor.visit(tree)

        # Find common parameter groups
        param_counts = {}
        for params, node in parameter_groups:
            if params in param_counts:
                param_counts[params].append(node)
            else:
                param_counts[params] = [node]

        # Report data clumps
        for params, nodes in param_counts.items():
            if len(nodes) >= 2:  # Same parameter group appears in multiple functions
                for node in nodes:
                    matches.append(
                        PatternMatch(
                            pattern_name="Data Clumps",
                            pattern_type=PatternType.ANTI_PATTERN,
                            severity=PatternSeverity.MEDIUM,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            confidence=0.7,
                            description=f"Method '{node.name}' has parameters that appear together in multiple places: {', '.join(params)}",
                            recommendation="Consider creating a data class or structure to group these related parameters",
                            code_snippet=f"def {node.name}({', '.join(params)}):",
                            metadata={
                                "parameter_group": params,
                                "occurrences": len(nodes),
                            },
                        )
                    )

        return matches

    def _detect_primitive_obsession(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect primitive obsession (overuse of primitive types instead of small objects)."""
        matches = []
        # This is a complex pattern that would require more sophisticated analysis
        # For now, we'll implement a basic version
        return matches

    def _detect_shotgun_surgery(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect shotgun surgery (making a change requires modifications in many places)."""
        matches = []
        # This requires cross-file analysis, which would be implemented at a higher level
        return matches

    def _detect_refused_bequest(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect refused bequest (subclass doesn't use inherited functionality)."""
        matches = []
        # This requires inheritance analysis across multiple files
        return matches


class CodeSmellDetector(PatternDetector):
    """Detects various code smells."""

    def __init__(self):
        self.smells = {
            "dead_code": self._detect_dead_code,
            "duplicate_code": self._detect_duplicate_code,
            "large_class": self._detect_large_class,
            "long_parameter_list": self._detect_long_parameter_list,
            "switch_statements": self._detect_switch_statements,
            "temporary_field": self._detect_temporary_field,
            "inappropriate_intimacy": self._detect_inappropriate_intimacy,
        }

    def detect_patterns(self, code: str, file_path: str) -> List[PatternMatch]:
        """Detect code smells in code."""
        matches = []

        try:
            tree = ast.parse(code)

            for smell_name, detector_func in self.smells.items():
                try:
                    smell_matches = detector_func(tree, code, file_path)
                    matches.extend(smell_matches)
                except Exception as e:
                    logger.debug(f"Error detecting {smell_name}: {e}")

        except SyntaxError:
            logger.debug(f"Syntax error in {file_path}")

        return matches

    def get_pattern_types(self) -> List[PatternType]:
        return [PatternType.CODE_SMELL]

    def _detect_dead_code(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect potentially dead/unreachable code."""
        matches = []

        class DeadCodeVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Look for unreachable code after return statements
                found_return = False
                for i, stmt in enumerate(node.body):
                    if isinstance(stmt, ast.Return):
                        found_return = True
                    elif found_return and not isinstance(stmt, ast.Pass):
                        matches.append(
                            PatternMatch(
                                pattern_name="Dead Code",
                                pattern_type=PatternType.CODE_SMELL,
                                severity=PatternSeverity.MEDIUM,
                                file_path=file_path,
                                start_line=stmt.lineno,
                                end_line=getattr(stmt, "end_lineno", stmt.lineno),
                                confidence=0.8,
                                description="Code after return statement is unreachable",
                                recommendation="Remove unreachable code or restructure the function logic",
                                code_snippet="# Code after return statement",
                                metadata={"function": node.name},
                            )
                        )
                        break

                self.generic_visit(node)

        visitor = DeadCodeVisitor()
        visitor.visit(tree)
        return matches

    def _detect_duplicate_code(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect duplicate code blocks within the same file."""
        # This would integrate with the duplicate detection system
        return []

    def _detect_large_class(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect excessively large classes."""
        # Similar to god class but focused on size metrics
        matches = []

        class LargeClassVisitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                lines = getattr(node, "end_lineno", node.lineno) - node.lineno

                if lines > 300:  # Large class threshold
                    matches.append(
                        PatternMatch(
                            pattern_name="Large Class",
                            pattern_type=PatternType.CODE_SMELL,
                            severity=PatternSeverity.MEDIUM,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            confidence=min(0.9, lines / 500),
                            description=f"Class '{node.name}' is very large ({lines} lines)",
                            recommendation="Consider breaking this class into smaller, more cohesive classes",
                            code_snippet=f"class {node.name}:",
                            metadata={"lines": lines},
                        )
                    )

                self.generic_visit(node)

        visitor = LargeClassVisitor()
        visitor.visit(tree)
        return matches

    def _detect_long_parameter_list(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect functions with too many parameters."""
        matches = []

        class LongParameterVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                param_count = len(node.args.args)

                if param_count > 5:  # Long parameter list threshold
                    matches.append(
                        PatternMatch(
                            pattern_name="Long Parameter List",
                            pattern_type=PatternType.CODE_SMELL,
                            severity=PatternSeverity.MEDIUM,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=node.lineno,
                            confidence=min(0.9, param_count / 10),
                            description=f"Function '{node.name}' has too many parameters ({param_count})",
                            recommendation="Consider using parameter objects, introducing a parameter object, or preserving whole object",
                            code_snippet=f"def {node.name}({', '.join([arg.arg for arg in node.args.args])}):",
                            metadata={"parameter_count": param_count},
                        )
                    )

                self.generic_visit(node)

        visitor = LongParameterVisitor()
        visitor.visit(tree)
        return matches

    def _detect_switch_statements(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect complex switch-like statements that could benefit from polymorphism."""
        matches = []

        class SwitchStatementVisitor(ast.NodeVisitor):
            def visit_If(self, node):
                # Count chained if-elif statements
                elif_count = 0
                current = node

                while hasattr(current, "orelse") and current.orelse:
                    if isinstance(current.orelse[0], ast.If):
                        elif_count += 1
                        current = current.orelse[0]
                    else:
                        break

                if elif_count > 3:  # Complex if-elif chain
                    matches.append(
                        PatternMatch(
                            pattern_name="Complex Switch Statement",
                            pattern_type=PatternType.CODE_SMELL,
                            severity=PatternSeverity.MEDIUM,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(current, "end_lineno", node.lineno),
                            confidence=min(0.8, elif_count / 8),
                            description=f"Complex if-elif chain with {elif_count + 1} branches",
                            recommendation="Consider using polymorphism, strategy pattern, or lookup tables",
                            code_snippet="if ... elif ... elif ...",
                            metadata={"branches": elif_count + 1},
                        )
                    )

                self.generic_visit(node)

        visitor = SwitchStatementVisitor()
        visitor.visit(tree)
        return matches

    def _detect_temporary_field(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect temporary fields (instance variables set only in certain circumstances)."""
        # This requires more sophisticated analysis
        return []

    def _detect_inappropriate_intimacy(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect classes that know too much about each other's internal details."""
        # This requires cross-class analysis
        return []


class SecurityPatternDetector(PatternDetector):
    """Detects security-related patterns and vulnerabilities."""

    def __init__(self):
        self.patterns = {
            "sql_injection": self._detect_sql_injection,
            "hardcoded_secrets": self._detect_hardcoded_secrets,
            "insecure_random": self._detect_insecure_random,
            "path_traversal": self._detect_path_traversal,
            "eval_usage": self._detect_eval_usage,
        }

    def detect_patterns(self, code: str, file_path: str) -> List[PatternMatch]:
        """Detect security patterns in code."""
        matches = []

        try:
            tree = ast.parse(code)

            for pattern_name, detector_func in self.patterns.items():
                try:
                    security_matches = detector_func(tree, code, file_path)
                    matches.extend(security_matches)
                except Exception as e:
                    logger.debug(f"Error detecting {pattern_name}: {e}")

            # Also check string patterns
            matches.extend(self._detect_string_patterns(code, file_path))

        except SyntaxError:
            logger.debug(f"Syntax error in {file_path}")

        return matches

    def get_pattern_types(self) -> List[PatternType]:
        return [PatternType.SECURITY_ISSUE]

    def _detect_sql_injection(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect potential SQL injection vulnerabilities."""
        matches = []

        class SqlInjectionVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                # Look for execute() calls with string formatting
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "execute"
                    and node.args
                ):
                    arg = node.args[0]
                    if isinstance(arg, (ast.BinOp, ast.JoinedStr, ast.FormattedValue)):
                        matches.append(
                            PatternMatch(
                                pattern_name="SQL Injection Risk",
                                pattern_type=PatternType.SECURITY_ISSUE,
                                severity=PatternSeverity.HIGH,
                                file_path=file_path,
                                start_line=node.lineno,
                                end_line=getattr(node, "end_lineno", node.lineno),
                                confidence=0.7,
                                description="SQL query construction using string formatting/concatenation",
                                recommendation="Use parameterized queries or prepared statements",
                                code_snippet="execute(...)",
                                metadata={"call_type": "execute"},
                            )
                        )

                self.generic_visit(node)

        visitor = SqlInjectionVisitor()
        visitor.visit(tree)
        return matches

    def _detect_hardcoded_secrets(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect hardcoded passwords, API keys, etc."""
        matches = []

        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "hardcoded token"),
        ]

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, description in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append(
                        PatternMatch(
                            pattern_name="Hardcoded Secrets",
                            pattern_type=PatternType.SECURITY_ISSUE,
                            severity=PatternSeverity.CRITICAL,
                            file_path=file_path,
                            start_line=i,
                            end_line=i,
                            confidence=0.8,
                            description=f"Found {description} in code",
                            recommendation="Use environment variables or secure configuration management",
                            code_snippet=line.strip(),
                            metadata={"secret_type": description},
                        )
                    )

        return matches

    def _detect_insecure_random(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect use of insecure random number generation."""
        matches = []

        class InsecureRandomVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "random"
                ):
                    matches.append(
                        PatternMatch(
                            pattern_name="Insecure Random",
                            pattern_type=PatternType.SECURITY_ISSUE,
                            severity=PatternSeverity.MEDIUM,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            confidence=0.6,
                            description="Using insecure random number generation",
                            recommendation="Use secrets module for cryptographically secure random numbers",
                            code_snippet=f"random.{node.func.attr}()",
                            metadata={"method": node.func.attr},
                        )
                    )

                self.generic_visit(node)

        visitor = InsecureRandomVisitor()
        visitor.visit(tree)
        return matches

    def _detect_path_traversal(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect potential path traversal vulnerabilities."""
        matches = []

        class PathTraversalVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                # Look for file operations with user input
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id in ["open", "file"]
                    and node.args
                ):
                    # This is a simplified check - real implementation would be more sophisticated
                    arg = node.args[0]
                    if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                        matches.append(
                            PatternMatch(
                                pattern_name="Path Traversal Risk",
                                pattern_type=PatternType.SECURITY_ISSUE,
                                severity=PatternSeverity.MEDIUM,
                                file_path=file_path,
                                start_line=node.lineno,
                                end_line=getattr(node, "end_lineno", node.lineno),
                                confidence=0.5,
                                description="File path constructed from user input without validation",
                                recommendation="Validate and sanitize file paths, use allowlists",
                                code_snippet="open(...)",
                                metadata={"function": node.func.id},
                            )
                        )

                self.generic_visit(node)

        visitor = PathTraversalVisitor()
        visitor.visit(tree)
        return matches

    def _detect_eval_usage(
        self, tree: ast.AST, code: str, file_path: str
    ) -> List[PatternMatch]:
        """Detect dangerous use of eval() and exec()."""
        matches = []

        class EvalUsageVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                    matches.append(
                        PatternMatch(
                            pattern_name="Dangerous Code Execution",
                            pattern_type=PatternType.SECURITY_ISSUE,
                            severity=PatternSeverity.CRITICAL,
                            file_path=file_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            confidence=0.9,
                            description=f"Use of {node.func.id}() function for code execution",
                            recommendation="Avoid eval/exec, use safer alternatives like ast.literal_eval or specific parsing",
                            code_snippet=f"{node.func.id}(...)",
                            metadata={"function": node.func.id},
                        )
                    )

                self.generic_visit(node)

        visitor = EvalUsageVisitor()
        visitor.visit(tree)
        return matches

    def _detect_string_patterns(self, code: str, file_path: str) -> List[PatternMatch]:
        """Detect security issues through string pattern matching."""
        matches = []

        dangerous_patterns = [
            (r'subprocess\.call\(["\'][^"\']*\s*\+', "command injection risk"),
            (r'os\.system\(["\'][^"\']*\s*\+', "command injection risk"),
            (r"shell=True", "shell injection risk"),
        ]

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    matches.append(
                        PatternMatch(
                            pattern_name="Command Injection Risk",
                            pattern_type=PatternType.SECURITY_ISSUE,
                            severity=PatternSeverity.HIGH,
                            file_path=file_path,
                            start_line=i,
                            end_line=i,
                            confidence=0.7,
                            description=f"Potential {description}",
                            recommendation="Validate input and use subprocess safely",
                            code_snippet=line.strip(),
                            metadata={"pattern": description},
                        )
                    )

        return matches


class CompositePatternClassifier:
    """Combines multiple pattern detectors for comprehensive analysis."""

    def __init__(self, detectors: Optional[List[PatternDetector]] = None):
        if detectors:
            self.detectors = detectors
        else:
            # Default set of detectors
            self.detectors = [
                AntiPatternDetector(),
                CodeSmellDetector(),
                SecurityPatternDetector(),
            ]

    def classify_patterns(self, code: str, file_path: str) -> List[PatternMatch]:
        """Run all pattern detectors and combine results."""
        all_matches = []

        for detector in self.detectors:
            try:
                matches = detector.detect_patterns(code, file_path)
                all_matches.extend(matches)
                logger.info(f"{type(detector).__name__} found {len(matches)} patterns")
            except Exception as e:
                logger.error(f"Error in {type(detector).__name__}: {e}")

        # Remove duplicates and sort by severity/confidence
        unique_matches = self._deduplicate_matches(all_matches)
        return self._sort_matches(unique_matches)

    def _deduplicate_matches(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Remove duplicate pattern matches."""
        seen_matches = set()
        unique_matches = []

        for match in matches:
            match_id = (
                match.pattern_name,
                match.file_path,
                match.start_line,
                match.end_line,
            )
            if match_id not in seen_matches:
                seen_matches.add(match_id)
                unique_matches.append(match)

        return unique_matches

    def _sort_matches(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Sort matches by severity and confidence."""
        severity_order = {
            PatternSeverity.CRITICAL: 0,
            PatternSeverity.HIGH: 1,
            PatternSeverity.MEDIUM: 2,
            PatternSeverity.LOW: 3,
            PatternSeverity.INFO: 4,
        }

        return sorted(
            matches, key=lambda m: (severity_order[m.severity], -m.confidence)
        )


class PatternAnalysisReport:
    """Generates comprehensive reports of pattern classification results."""

    def __init__(self, matches: List[PatternMatch]):
        self.matches = matches
        self.stats = self._calculate_statistics()

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate analysis statistics."""
        if not self.matches:
            return {"total_matches": 0}

        stats = {
            "total_matches": len(self.matches),
            "by_type": {},
            "by_severity": {},
            "high_confidence": 0,
            "files_affected": set(),
            "avg_confidence": 0.0,
        }

        confidence_sum = 0.0

        for match in self.matches:
            # Count by type
            pattern_type = match.pattern_type.value
            stats["by_type"][pattern_type] = stats["by_type"].get(pattern_type, 0) + 1

            # Count by severity
            severity = match.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

            # High confidence matches
            if match.confidence > 0.8:
                stats["high_confidence"] += 1

            # Confidence tracking
            confidence_sum += match.confidence

            # File tracking
            stats["files_affected"].add(match.file_path)

        stats["avg_confidence"] = confidence_sum / len(self.matches)
        stats["files_affected"] = list(stats["files_affected"])

        return stats

    def generate_summary(self) -> str:
        """Generate a summary report."""
        if not self.matches:
            return "No patterns detected."

        summary = f"""
Pattern Classification Summary
=============================

Total Patterns: {self.stats['total_matches']}
High Confidence: {self.stats['high_confidence']}
Average Confidence: {self.stats['avg_confidence']:.2f}
Files Affected: {len(self.stats['files_affected'])}

Patterns by Type:
"""

        for pattern_type, count in self.stats["by_type"].items():
            summary += f"  {pattern_type.replace('_', ' ').title()}: {count}\n"

        summary += "\nPatterns by Severity:\n"
        for severity, count in self.stats["by_severity"].items():
            summary += f"  {severity.capitalize()}: {count}\n"

        return summary

    def generate_detailed_report(self) -> str:
        """Generate a detailed report with all patterns."""
        report = self.generate_summary()
        report += "\n\nDetailed Patterns:\n" + "=" * 50 + "\n"

        for i, match in enumerate(self.matches[:20], 1):  # Limit to top 20
            report += (
                f"\nPattern #{i} - {match.pattern_name} ({match.severity.value}):\n"
            )
            report += f"  File: {match.file_path}:{match.start_line}-{match.end_line}\n"
            report += f"  Type: {match.pattern_type.value}, Confidence: {match.confidence:.2f}\n"
            report += f"  Description: {match.description}\n"
            report += f"  Recommendation: {match.recommendation}\n"
            report += f"  Code: {match.code_snippet}\n"

        if len(self.matches) > 20:
            report += f"\n... and {len(self.matches) - 20} more patterns."

        return report


def main():
    """Example usage of the pattern classification system."""
    sample_code = """
def process_user_data(username, password, email, phone, address):
    # Hardcoded password - security issue
    admin_password = "admin123"

    # SQL injection risk
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)

    # Long method with many parameters
    if user_type == "admin":
        admin_logic()
    elif user_type == "moderator":
        moderator_logic()
    elif user_type == "user":
        user_logic()
    elif user_type == "guest":
        guest_logic()
    elif user_type == "premium":
        premium_logic()

    return result
"""

    # Initialize classifier
    classifier = CompositePatternClassifier()

    # Classify patterns
    matches = classifier.classify_patterns(sample_code, "example.py")

    # Generate report
    report = PatternAnalysisReport(matches)
    print(report.generate_detailed_report())


if __name__ == "__main__":
    main()
