#!/usr/bin/env python3
"""
Symbol Extractor for Continuous Improvement Framework
Hybrid approach using Serena MCP with robust AST fallback.
Part of AI-Assisted Workflows - integrates with 8-agent orchestration system.
"""

import ast
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "utils"))

try:
    from shared.core.utils.output_formatter import AnalysisResult, ResultFormatter
    from shared.core.utils.tech_stack_detector import TechStackDetector
except ImportError as e:
    print(f"Error importing utilities: {e}", file=sys.stderr)
    sys.exit(1)


class SymbolType(Enum):
    """Types of code symbols we extract."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    INTERFACE = "interface"
    TYPE = "type"


@dataclass
class Symbol:
    """Represents a code symbol with metadata."""

    name: str
    symbol_type: SymbolType
    file_path: str
    line_number: int
    line_content: str
    scope: str
    visibility: Optional[str] = None
    parameters: Optional[List[str]] = None
    return_type: Optional[str] = None
    complexity: Optional[int] = None
    dependencies: Optional[List[str]] = None


class SerenaFallbackExtractor:
    """Robust AST-based symbol extraction when Serena MCP is unavailable."""

    def __init__(self):
        # Import patterns from coupling_analysis.py
        self.import_patterns = {
            "python": {
                "pattern": r"(?:from\s+(\S+)\s+import|import\s+(\S+))",
                "groups": [1, 2],
            },
            "javascript": {
                "pattern": (
                    r'(?:import\s+.*?from\s+[\'"]([^\'"]+)[\'"]\|'
                    r'require\([\'"]([^\'"]+)[\'"]\))'
                ),
                "groups": [1, 2],
            },
            "typescript": {
                "pattern": (
                    r'(?:import\s+.*?from\s+[\'"]([^\'"]+)[\'"]\|'
                    r'require\([\'"]([^\'"]+)[\'"]\))'
                ),
                "groups": [1, 2],
            },
            "java": {"pattern": r"import\s+([^;]+);", "groups": [1]},
            "csharp": {"pattern": r"using\s+([^;]+);", "groups": [1]},
            "go": {
                "pattern": r'import\s+(?:"([^"]+)"|`([^`]+)`)',
                "groups": [1, 2],
            },
            "rust": {"pattern": r"use\s+([^;]+);", "groups": [1]},
            "php": {
                "pattern": (
                    r"(?:use\s+([^;]+);|require_once\s+['\"]([^'\"]+)\""
                    r"['\"]|include_once\s+['\"]([^'\"]+)['\"])"
                ),
                "groups": [1, 2, 3],
            },
            "ruby": {
                "pattern": (
                    r"(?:require\s+['\"]([^'\"]+)['\"]|require_relative\s+"
                    r"['\"]([^'\"]+)['\"])"
                ),
                "groups": [1, 2],
            },
            "swift": {"pattern": r"import\s+(\w+)", "groups": [1]},
            "kotlin": {"pattern": r"import\s+([^;]+)", "groups": [1]},
            "cpp": {"pattern": r"#include\s+[<\"]([^>\"]+)[>\"]", "groups": [1]},
            "c": {"pattern": r"#include\s+[<\"]([^>\"]+)[>\"]", "groups": [1]},
        }

        # Function patterns from complexity_lizard.py
        self.function_patterns = {
            ".js": [
                (r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", "function"),
                (
                    r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
                    r"(?:async\s+)?\([^)]*\)\s*(?::|=>)",
                    "arrow",
                ),
                (r"^\s*(?:export\s+)?class\s+(\w+)", "class"),
            ],
            ".ts": [
                (r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", "function"),
                (
                    r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
                    r"(?:async\s+)?\([^)]*\)\s*(?::|=>)",
                    "arrow",
                ),
                (r"^\s*(?:export\s+)?class\s+(\w+)", "class"),
                (r"^\s*(?:export\s+)?interface\s+(\w+)", "interface"),
                (r"^\s*(?:export\s+)?type\s+(\w+)", "type"),
            ],
            ".py": [
                (r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", "function"),
                (r"^\s*class\s+(\w+)", "class"),
            ],
            ".java": [
                (
                    r"^\s*(?:public|private|protected)?\s*(?:static\s+)?"
                    r"(?:final\s+)?(?:abstract\s+)?class\s+(\w+)",
                    "class",
                ),
                (
                    r"^\s*(?:public|private|protected)?\s*(?:static\s+)?"
                    r"(?:final\s+)?(?:synchronized\s+)?(?:\w+\s+)*"
                    r"(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{",
                    "method",
                ),
            ],
            ".go": [
                (r"^\s*func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(", "function"),
                (r"^\s*type\s+(\w+)\s+(?:struct|interface)", "type"),
            ],
            ".rs": [
                (r"^\s*(?:pub\s+)?fn\s+(\w+)\s*\(", "function"),
                (r"^\s*(?:pub\s+)?struct\s+(\w+)", "struct"),
                (r"^\s*(?:pub\s+)?enum\s+(\w+)", "enum"),
                (r"^\s*(?:pub\s+)?trait\s+(\w+)", "trait"),
            ],
        }

        # Extension to language mapping
        self.extension_language_map = {
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
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "cpp",
            ".hpp": "cpp",
        }

    def extract_python_symbols_ast(self, content: str, file_path: Path) -> List[Symbol]:
        """Extract Python symbols using AST parsing."""
        symbols = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fallback to regex for malformed files
            return self.extract_symbols_regex(content, file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append(
                    Symbol(
                        name=node.name,
                        symbol_type=SymbolType.FUNCTION,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        line_content=content.split("\n")[node.lineno - 1].strip(),
                        scope="module" if node.col_offset == 0 else "class",
                        parameters=[arg.arg for arg in node.args.args],
                    )
                )
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append(
                    Symbol(
                        name=node.name,
                        symbol_type=SymbolType.FUNCTION,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        line_content=content.split("\n")[node.lineno - 1].strip(),
                        scope="module" if node.col_offset == 0 else "class",
                        parameters=[arg.arg for arg in node.args.args],
                    )
                )
            elif isinstance(node, ast.ClassDef):
                symbols.append(
                    Symbol(
                        name=node.name,
                        symbol_type=SymbolType.CLASS,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        line_content=content.split("\n")[node.lineno - 1].strip(),
                        scope="module",
                    )
                )
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._extract_import_info(node)
                if import_info:
                    symbols.append(
                        Symbol(
                            name=import_info,
                            symbol_type=SymbolType.IMPORT,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            line_content=content.split("\n")[node.lineno - 1].strip(),
                            scope="module",
                        )
                    )

        return symbols

    def extract_symbols_regex(self, content: str, file_path: Path) -> List[Symbol]:
        """Extract symbols using regex patterns (fallback method)."""
        symbols = []
        lines = content.split("\n")
        suffix = file_path.suffix.lower()
        language = self.extension_language_map.get(suffix, "unknown")

        # Extract imports
        if language in self.import_patterns:
            pattern_config = self.import_patterns[language]
            for i, line in enumerate(lines):
                match = re.search(pattern_config["pattern"], line)
                if match:
                    for group_idx in pattern_config["groups"]:
                        if match.group(group_idx):
                            symbols.append(
                                Symbol(
                                    name=match.group(group_idx),
                                    symbol_type=SymbolType.IMPORT,
                                    file_path=str(file_path),
                                    line_number=i + 1,
                                    line_content=line.strip(),
                                    scope="module",
                                )
                            )
                            break

        # Extract functions and classes
        if suffix in self.function_patterns:
            patterns = self.function_patterns[suffix]
            for i, line in enumerate(lines):
                for pattern, pattern_type in patterns:
                    match = re.search(pattern, line)
                    if match:
                        symbol_type = (
                            SymbolType.CLASS
                            if pattern_type
                            in ["class", "struct", "enum", "trait", "interface"]
                            else SymbolType.FUNCTION
                        )
                        if pattern_type == "interface":
                            symbol_type = SymbolType.INTERFACE
                        elif pattern_type == "type":
                            symbol_type = SymbolType.TYPE

                        symbols.append(
                            Symbol(
                                name=match.group(1),
                                symbol_type=symbol_type,
                                file_path=str(file_path),
                                line_number=i + 1,
                                line_content=line.strip(),
                                scope=self._infer_scope(lines, i),
                            )
                        )

        return symbols

    def _extract_import_info(self, node) -> Optional[str]:
        """Extract import information from AST node."""
        if isinstance(node, ast.Import):
            return ", ".join([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join([alias.name for alias in node.names])
            return module + ": " + names if module else names
        return None

    def _infer_scope(self, lines: List[str], current_line: int) -> str:
        """Infer the scope of a symbol based on indentation."""
        current_indent = len(lines[current_line]) - len(lines[current_line].lstrip())

        # Look backwards for class definition
        for i in range(current_line - 1, -1, -1):
            line = lines[i].strip()
            if not line:
                continue

            line_indent = len(lines[i]) - len(lines[i].lstrip())
            if line_indent < current_indent and (
                line.startswith("class ")
                or line.startswith("struct ")
                or line.startswith("interface ")
            ):
                return "class"

        return "module"


class SymbolExtractor:
    """Main symbol extractor with Serena MCP integration and AST fallback."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.tech_detector = TechStackDetector()
        self.fallback_extractor = SerenaFallbackExtractor()
        self.result_formatter = ResultFormatter()

        # Initialize Serena client with proper integration
        self.serena_client = self._initialize_serena_client()
        self.serena_available = self.serena_client is not None

    def _initialize_serena_client(self):
        """Initialize Serena MCP client if available."""
        try:
            # Import SerenaClient from the core module
            from ..core.serena_client import SerenaClient, MCPConfig

            # Create client with project-specific configuration
            config = MCPConfig(
                use_ast_fallback=True,
                enable_semantic_analysis=True,
                max_symbols_per_request=1000,
            )

            client = SerenaClient(config, self.project_root)
            return client

        except ImportError:
            # Fallback import for direct execution
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
                from serena_client import SerenaClient, MCPConfig

                config = MCPConfig(use_ast_fallback=True)
                return SerenaClient(config, self.project_root)

            except ImportError:
                return None

    def extract_symbols(
        self, file_paths: Optional[List[Path]] = None, use_serena: bool = True
    ) -> AnalysisResult:
        """
        Extract symbols from files using hybrid approach.

        Args:
            file_paths: Specific files to analyze (default: all project files)
            use_serena: Whether to attempt Serena MCP first (default: True)
        """
        start_time = time.time()

        # Detect tech stack for filtering
        detected_stacks = self.tech_detector.detect_tech_stack(str(self.project_root))

        # Handle case where no tech stacks are detected
        if not detected_stacks:
            # Use a default config for universal patterns
            tech_config = self._get_default_tech_config()
        else:
            # Use the first detected tech stack config
            tech_config = self.tech_detector.tech_stacks[detected_stacks[0]]

        # Get files to analyze
        if file_paths is None:
            file_paths = self._get_project_files(tech_config)

        all_symbols = []
        processed_files = 0

        for file_path in file_paths:
            try:
                if not file_path.exists():
                    continue
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                # Try Serena MCP first if available and requested
                if use_serena and self.serena_available:
                    symbols = self.serena_client.extract_symbols([file_path])
                    if symbols:  # If Serena succeeded
                        all_symbols.extend(symbols)
                        processed_files += 1
                        continue

                # Fallback to AST/regex extraction
                if file_path.suffix == ".py":
                    symbols = self.fallback_extractor.extract_python_symbols_ast(
                        content, file_path
                    )
                else:
                    symbols = self.fallback_extractor.extract_symbols_regex(
                        content, file_path
                    )

                all_symbols.extend(symbols)
                processed_files += 1
            except Exception as e:
                print(f"Error processing {file_path}: {e}", file=sys.stderr)
                continue
        # Convert to analysis result format
        findings = []
        symbol_summary = {}

        for symbol in all_symbols:
            symbol_key = symbol.symbol_type.value + "s"
            symbol_summary[symbol_key] = symbol_summary.get(symbol_key, 0) + 1

            findings.append(
                {
                    "finding_id": (
                        f"symbol_{symbol.symbol_type.value}_{len(findings)}"
                    ),
                    "title": (f"{symbol.symbol_type.value.title()}: {symbol.name}"),
                    "description": (
                        f"Found {symbol.symbol_type.value} "
                        f"'{symbol.name}' in {symbol.scope} scope"
                    ),
                    "severity": "info",
                    "file_path": symbol.file_path,
                    "line_number": symbol.line_number,
                    "evidence": {
                        "symbol_type": symbol.symbol_type.value,
                        "name": symbol.name,
                        "scope": symbol.scope,
                        "visibility": symbol.visibility,
                        "parameters": symbol.parameters,
                        "return_type": symbol.return_type,
                        "line_content": symbol.line_content,
                    },
                }
            )

        execution_time = time.time() - start_time

        # Convert to proper AnalysisResult format
        from shared.core.utils.output_formatter import (
            AnalysisResult,
            AnalysisType,
            Finding,
            Severity,
        )

        result = AnalysisResult(
            analysis_type=AnalysisType.CODE_QUALITY,
            script_name="symbol_extractor.py",
            target_path=str(self.project_root),
        )

        # Add findings as proper Finding objects
        for finding_data in findings:
            finding = Finding(
                finding_id=finding_data["finding_id"],
                title=finding_data["title"],
                description=finding_data["description"],
                severity=Severity.INFO,
                file_path=finding_data.get("file_path"),
                line_number=finding_data.get("line_number"),
                evidence=finding_data.get("evidence"),
            )
            result.add_finding(finding)

        # Add metadata including summary information
        result.metadata.update(
            {
                "total_symbols": len(all_symbols),
                "files_processed": processed_files,
                "extraction_method": (
                    "serena_mcp"
                    if (use_serena and self.serena_available)
                    else "ast_fallback"
                ),
                "symbol_breakdown": symbol_summary,
                "execution_time_seconds": round(execution_time, 2),
                "project_root": str(self.project_root),
                "tech_stack": tech_config.name,
                "detected_stacks": detected_stacks,
                "serena_available": self.serena_available,
                "serena_connection": (
                    self.serena_client.get_connection_info()
                    if self.serena_client
                    else None
                ),
            }
        )

        result.set_execution_time(start_time)

        return result

    def get_serena_connection_info(self) -> Optional[Dict]:
        """Get Serena MCP connection information for diagnostics."""
        if self.serena_client:
            return self.serena_client.get_connection_info()
        return None

    def _get_project_files(self, tech_config) -> List[Path]:
        """Get all relevant project files based on tech stack."""
        files = []
        exclude_patterns = tech_config.exclude_patterns

        for pattern in tech_config.source_patterns:
            for file_path in self.project_root.rglob(pattern):
                # Check if file should be excluded
                should_exclude = False
                for exclude_pattern in exclude_patterns:
                    if self._matches_pattern(
                        str(file_path.relative_to(self.project_root)), exclude_pattern
                    ):
                        should_exclude = True
                        break

                if not should_exclude:
                    files.append(file_path)

        return files

    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches exclusion pattern."""
        import fnmatch

        return fnmatch.fnmatch(file_path, pattern.replace("/**/*", "/*"))

    def _get_default_tech_config(self):
        """Get default tech config when no tech stacks are detected."""
        from shared.core.utils.tech_stack_detector import TechStackConfig

        return TechStackConfig(
            name="Universal",
            primary_languages={"unknown"},
            exclude_patterns={
                ".git/**/*",
                "__pycache__/**/*",
                "node_modules/**/*",
                "build/**/*",
                "dist/**/*",
                "target/**/*",
                "*.log",
            },
            dependency_dirs={"node_modules", "__pycache__", "build", "dist"},
            config_files=set(),
            source_patterns={"**/*.py", "**/*.js", "**/*.ts", "**/*.java", "**/*.go"},
            build_artifacts={"build", "dist", "target"},
        )


def main():
    """Main entry point for symbol extraction."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract code symbols with Serena MCP integration"
    )
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument(
        "--files", nargs="*", type=Path, help="Specific files to analyze"
    )
    parser.add_argument(
        "--no-serena", action="store_true", help="Skip Serena MCP, use AST/regex only"
    )
    parser.add_argument(
        "--output", choices=["json", "summary"], default="json", help="Output format"
    )
    parser.add_argument(
        "--test-serena", action="store_true", help="Test Serena MCP connection"
    )

    args = parser.parse_args()

    # Initialize extractor
    extractor = SymbolExtractor(args.project_root)

    # Test Serena connection if requested
    if args.test_serena:
        if extractor.serena_client:
            test_result = extractor.serena_client.test_extraction()
            print("Serena MCP Test Results:")
            status = (
                "SUCCESS" if test_result.metadata.get("test_successful") else "FAILED"
            )
            print(f"  Status: {status}")
            if extractor.serena_client.get_connection_info():
                conn_info = extractor.serena_client.get_connection_info()
                print(f"  Connection: {conn_info['status']}")
                print(f"  MCP Available: {conn_info['mcp_available']}")
            print(
                f"  Symbols Found: "
                f"{test_result.metadata.get('symbols_extracted', 0)}"
            )
            print(
                f"  Method: "
                f"{test_result.metadata.get('extraction_method', 'unknown')}"
            )
        else:
            print("Serena client not available")
        return

    # Extract symbols
    result = extractor.extract_symbols(
        file_paths=args.files, use_serena=not args.no_serena
    )

    # Output results
    if args.output == "json":
        formatter = ResultFormatter()
        print(formatter.format_result(result))
    else:
        metadata = result.metadata
        print("Symbol Extraction Complete:")
        print(f"  Total symbols: {metadata['total_symbols']}")
        print(f"  Files processed: {metadata['files_processed']}")
        print(f"  Method used: {metadata['extraction_method']}")
        print(f"  Execution time: {metadata['execution_time_seconds']}s")
        print("  Symbol breakdown:")
        for symbol_type, count in metadata["symbol_breakdown"].items():
            print(f"    {symbol_type}: {count}")
        if metadata.get("serena_connection"):
            conn = metadata["serena_connection"]
            print(
                f"  Serena Status: {conn['status']} " f"(MCP: {conn['mcp_available']})"
            )


if __name__ == "__main__":
    main()
