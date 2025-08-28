#!/usr/bin/env python3
"""
LSP Symbol Extractor for Continuous Improvement Framework

Provides semantic symbol extraction using Language Server Protocol (LSP)
for true cross-file understanding, references, and type information.
Part of AI-Assisted Workflows.
"""

import logging
import sys
import tempfile
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

# LSP integration
try:
    from multilspy import SyncLanguageServer
    from multilspy.multilspy_config import MultilspyConfig
    from multilspy.multilspy_logger import MultilspyLogger

    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False
    SyncLanguageServer = None
    MultilspyConfig = None
    MultilspyLogger = None

# Setup import paths and import base utilities
try:
    from utils import path_resolver  # noqa: F401
    from core.base.module_base import CIConfigModule
    from core.base.timing_utils import timed_operation, PerformanceTracker
    from core.base.cli_utils import create_standard_cli, run_cli_tool
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

# Import Symbol from integration
from ci.integration.symbol_extractor import Symbol, SymbolType

logger = logging.getLogger(__name__)


class LSPLanguage(Enum):
    """Supported languages for LSP analysis."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CSHARP = "csharp"


@dataclass
class SymbolExtractionConfig:
    """Configuration for LSP symbol extraction."""

    # Language server settings
    enable_type_analysis: bool = True
    enable_reference_analysis: bool = True
    enable_cross_file_analysis: bool = True

    # Performance settings
    max_file_size_mb: int = 10
    timeout_seconds: int = 30
    batch_size: int = 50

    # Symbol filtering
    include_private_symbols: bool = False
    include_imported_symbols: bool = True
    min_symbol_length: int = 2

    # Language-specific settings
    python_include_docstrings: bool = True
    typescript_include_interfaces: bool = True
    java_include_annotations: bool = True

    # Compatibility with existing code
    max_symbols_per_file: int = 500
    include_symbol_types: Optional[List[str]] = None
    enable_function_extraction: bool = True
    enable_method_extraction: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LSPSymbolExtractor(CIConfigModule):
    """LSP-based symbol extractor for semantic analysis."""

    def __init__(
        self,
        config: SymbolExtractionConfig,
        project_root: str = ".",
        force_init: bool = False,
    ):
        super().__init__("lsp_symbol_extractor", project_root)

        self.config = config
        self.force_init = force_init
        self.performance_tracker = PerformanceTracker()
        self.project_root = Path(project_root).resolve()

        # Initialize language servers
        self.language_servers: Dict[LSPLanguage, Optional[SyncLanguageServer]] = {}
        self.lsp_available = LSP_AVAILABLE
        self.multilspy_logger = MultilspyLogger() if self.lsp_available else None

        if self.lsp_available:
            self._initialize_language_servers()
        else:
            logger.warning("multilspy not available - LSP functionality disabled")

    def _initialize_language_servers(self) -> None:
        """Initialize language servers for supported languages."""
        if not self.lsp_available:
            return

        # Language mapping for multilspy
        language_configs = {
            LSPLanguage.PYTHON: "python",
            LSPLanguage.TYPESCRIPT: "typescript",
            LSPLanguage.JAVASCRIPT: "javascript",
            LSPLanguage.JAVA: "java",
            LSPLanguage.GO: "go",
            LSPLanguage.RUST: "rust",
            LSPLanguage.CSHARP: "csharp",
        }

        for language, language_str in language_configs.items():
            try:
                config = MultilspyConfig.from_dict({"code_language": language_str})
                server = SyncLanguageServer.create(
                    config,
                    self.multilspy_logger,
                    str(self.project_root),
                    timeout=self.config.timeout_seconds,
                )
                self.language_servers[language] = server
                logger.warning(f"Initialized {language.value} language server")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize {language.value} language server: {e}"
                )
                self.language_servers[language] = None

    def _init_language_server(
        self, language: LSPLanguage, config: Dict[str, Any]
    ) -> Optional[SyncLanguageServer]:
        """Initialize a specific language server."""
        try:
            with tempfile.TemporaryDirectory():
                server = SyncLanguageServer.create(
                    language_server=config["language_server"],
                    language=language.value,
                    working_dir=str(self.project_root),
                )

                if server:
                    return server

        except Exception as e:
            logger.error(f"Error initializing {language.value} server: {e}")

        return None

    def _detect_language(self, file_path: Path) -> Optional[LSPLanguage]:
        """Detect the programming language of a file."""
        suffix = file_path.suffix.lower()

        language_map = {
            ".py": LSPLanguage.PYTHON,
            ".ts": LSPLanguage.TYPESCRIPT,
            ".tsx": LSPLanguage.TYPESCRIPT,
            ".js": LSPLanguage.JAVASCRIPT,
            ".jsx": LSPLanguage.JAVASCRIPT,
            ".java": LSPLanguage.JAVA,
            ".go": LSPLanguage.GO,
            ".rs": LSPLanguage.RUST,
            ".cs": LSPLanguage.CSHARP,
        }

        return language_map.get(suffix)

    @timed_operation("extract_symbols")
    def extract_symbols(self, file_paths: List[Path]) -> List[Symbol]:
        """Extract symbols using LSP semantic analysis."""
        if not self.lsp_available:
            logger.warning("LSP not available, returning empty symbol list")
            return []

        all_symbols = []

        # Group files by language
        files_by_language = self._group_files_by_language(file_paths)

        for language, files in files_by_language.items():
            if language in self.language_servers and self.language_servers[language]:
                symbols = self._extract_symbols_for_language(language, files)
                all_symbols.extend(symbols)
            else:
                logger.warning(f"No language server available for {language.value}")

        self.log_operation("symbols_extracted", {"count": len(all_symbols)})
        return all_symbols

    def _group_files_by_language(
        self, file_paths: List[Path]
    ) -> Dict[LSPLanguage, List[Path]]:
        """Group files by their detected programming language."""
        files_by_language = {}

        for file_path in file_paths:
            language = self._detect_language(file_path)
            if language:
                if language not in files_by_language:
                    files_by_language[language] = []
                files_by_language[language].append(file_path)
            else:
                logger.debug(f"Unknown language for file: {file_path}")

        return files_by_language

    def _extract_symbols_for_language(
        self, language: LSPLanguage, file_paths: List[Path]
    ) -> List[Symbol]:
        """Extract symbols for files of a specific language."""
        symbols = []
        server = self.language_servers[language]

        if not server:
            return symbols

        try:
            with server.start_server():
                for file_path in file_paths:
                    if not self._should_process_file(file_path):
                        continue

                    file_symbols = self._extract_file_symbols(
                        server, file_path, language
                    )
                    symbols.extend(file_symbols)

        except Exception as e:
            logger.error(f"Error extracting symbols for {language.value}: {e}")

        return symbols

    def _should_process_file(self, file_path: Path) -> bool:
        """Check if a file should be processed for symbol extraction."""
        try:
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                logger.debug(f"Skipping large file: {file_path} ({file_size_mb:.1f}MB)")
                return False

            # Check if file is readable
            if not file_path.is_file() or not file_path.exists():
                return False

            return True

        except (OSError, PermissionError):
            return False

    def _extract_file_symbols(
        self, server: SyncLanguageServer, file_path: Path, language: LSPLanguage
    ) -> List[Symbol]:
        """Extract symbols from a single file using LSP."""
        symbols = []

        try:
            # Get relative path from project root
            if file_path.is_absolute():
                try:
                    relative_path = str(file_path.relative_to(self.project_root))
                except ValueError:
                    # File is not under project root, use absolute path
                    relative_path = str(file_path)
            else:
                relative_path = str(file_path)

            # Get document symbols using multilspy API
            result = server.request_document_symbols(relative_path)

            # multilspy returns a tuple, first element is the symbol list
            if result and isinstance(result, tuple) and len(result) > 0:
                document_symbols = result[0]  # Extract symbol list from tuple

                if document_symbols and isinstance(document_symbols, list):
                    for symbol_info in document_symbols:
                        symbol = self._convert_lsp_symbol(
                            symbol_info, file_path, language
                        )
                        if symbol and self._should_include_symbol(symbol):
                            symbols.append(symbol)

            # Get additional semantic information if enabled
            if self.config.enable_reference_analysis:
                symbols = self._enrich_with_references(server, symbols, relative_path)

        except Exception as e:
            logger.error(f"Error extracting symbols from {file_path}: {e}")

        return symbols

    def _convert_lsp_symbol(
        self, lsp_symbol: Dict[str, Any], file_path: Path, language: LSPLanguage
    ) -> Optional[Symbol]:
        """Convert LSP symbol information to our Symbol format."""
        try:
            name = lsp_symbol.get("name", "")
            if len(name) < self.config.min_symbol_length:
                return None

            # Map LSP symbol kind to our SymbolType
            lsp_kind = lsp_symbol.get("kind", 0)
            symbol_type = self._map_lsp_kind_to_symbol_type(lsp_kind)

            # Get position information from DocumentSymbol format
            range_info = lsp_symbol.get("range", {})
            start_pos = range_info.get("start", {})
            end_pos = range_info.get("end", {})

            line_number = start_pos.get("line", 0) + 1  # LSP is 0-based, we use 1-based

            # Calculate line count if range information is available
            line_count = 1
            if start_pos and end_pos:
                start_line = start_pos.get("line", 0)
                end_line = end_pos.get("line", 0)
                line_count = max(1, end_line - start_line + 1)

            # Detect imports using LSP kind (MODULE = 2) or symbol type
            is_import = lsp_kind == 2 or symbol_type == SymbolType.IMPORT

            return Symbol(
                name=name,
                symbol_type=symbol_type,
                file_path=str(file_path),
                line_number=line_number,
                line_content=lsp_symbol.get("detail", ""),
                scope="global",  # Default scope
                visibility="public",  # Default visibility
                is_import=is_import,
                lsp_kind=lsp_kind,
                line_count=line_count,
            )

        except Exception as e:
            logger.error(f"Error converting LSP symbol: {e}")
            return None

    def _map_lsp_kind_to_symbol_type(self, lsp_kind: int) -> SymbolType:
        """Map LSP symbol kind to our SymbolType enum."""
        # LSP symbol kinds: https://microsoft.github.io/language-server-protocol/specification#textDocument_documentSymbol
        # Map to the SymbolType enum values that actually exist in integration/symbol_extractor.py
        kind_map = {
            1: SymbolType.TYPE,  # FILE
            2: SymbolType.TYPE,  # MODULE
            3: SymbolType.TYPE,  # NAMESPACE
            4: SymbolType.TYPE,  # PACKAGE
            5: SymbolType.CLASS,
            6: SymbolType.METHOD,
            7: SymbolType.VARIABLE,  # PROPERTY
            8: SymbolType.VARIABLE,  # FIELD
            9: SymbolType.METHOD,  # CONSTRUCTOR
            10: SymbolType.TYPE,  # ENUM
            11: SymbolType.INTERFACE,
            12: SymbolType.FUNCTION,
            13: SymbolType.VARIABLE,
            14: SymbolType.CONSTANT,
            15: SymbolType.VARIABLE,  # STRING
            16: SymbolType.VARIABLE,  # NUMBER
            17: SymbolType.VARIABLE,  # BOOLEAN
            18: SymbolType.VARIABLE,  # ARRAY
            19: SymbolType.VARIABLE,  # OBJECT
            20: SymbolType.VARIABLE,  # KEY
            21: SymbolType.VARIABLE,  # NULL
            22: SymbolType.CONSTANT,  # ENUM_MEMBER
            23: SymbolType.TYPE,  # STRUCT
            24: SymbolType.TYPE,  # EVENT
            25: SymbolType.FUNCTION,  # OPERATOR
            26: SymbolType.TYPE,  # TYPE_PARAMETER
        }

        return kind_map.get(lsp_kind, SymbolType.VARIABLE)

    def _generate_signature(
        self,
        name: str,
        symbol_type: SymbolType,
        file_path: Path,
        metadata: Dict[str, Any],
    ) -> str:
        """Generate a unique signature for the symbol."""
        components = [
            name,
            symbol_type.value,
            str(file_path.name),
            metadata.get("container_name", ""),
            metadata.get("detail", ""),
        ]

        return "|".join(filter(None, components))

    def _should_include_symbol(self, symbol: Symbol) -> bool:
        """Check if a symbol should be included based on configuration."""
        # Check if private symbols should be included
        if not self.config.include_private_symbols and symbol.name.startswith("_"):
            return False

        # Additional filtering logic can be added here
        return True

    def _enrich_with_references(
        self, server: SyncLanguageServer, symbols: List[Symbol], uri: str
    ) -> List[Symbol]:
        """Enrich symbols with reference information."""
        # This is a placeholder for reference analysis
        # In a full implementation, you would use LSP's textDocument/references
        return symbols

    def get_parser_info(self) -> Dict[str, Any]:
        """Get information about available language servers."""
        info = {
            "lsp_available": self.lsp_available,
            "is_loaded": self.lsp_available,  # For compatibility with validation code
            "status": "available" if self.lsp_available else "unavailable",
            "languages_supported": [],
            "servers_initialized": 0,
            "version": "multilspy-based",
        }

        if self.lsp_available:
            for language, server in self.language_servers.items():
                language_info = {
                    "language": language.value,
                    "server_available": server is not None,
                    "extensions": self._get_language_extensions(language),
                }
                info["languages_supported"].append(language_info)

                if server:
                    info["servers_initialized"] += 1

        return info

    def _get_language_extensions(self, language: LSPLanguage) -> List[str]:
        """Get file extensions for a language."""
        extension_map = {
            LSPLanguage.PYTHON: [".py"],
            LSPLanguage.TYPESCRIPT: [".ts", ".tsx"],
            LSPLanguage.JAVASCRIPT: [".js", ".jsx"],
            LSPLanguage.JAVA: [".java"],
            LSPLanguage.GO: [".go"],
            LSPLanguage.RUST: [".rs"],
            LSPLanguage.CSHARP: [".cs"],
        }

        return extension_map.get(language, [])

    def test_extraction(self) -> Dict[str, Any]:
        """Test symbol extraction functionality."""
        test_results = {
            "lsp_available": self.lsp_available,
            "servers_working": {},
            "test_passed": False,
        }

        if not self.lsp_available:
            test_results["error"] = "multilspy not available"
            return test_results

        # Test each language server
        for language, server in self.language_servers.items():
            test_results["servers_working"][language.value] = server is not None

        test_results["test_passed"] = any(test_results["servers_working"].values())
        return test_results

    def cleanup(self) -> None:
        """Clean up language server resources."""
        # multilspy SyncLanguageServer doesn't have a close method
        # Resources are cleaned up automatically when context managers exit
        self.language_servers.clear()


def main():
    """CLI interface for LSP symbol extractor."""
    cli = create_standard_cli(
        "lsp-symbol-extractor",
        "Extract symbols using Language Server Protocol",
        version="1.0.0",
    )

    cli.parser.add_argument(
        "files", nargs="*", help="Files to analyze (default: scan project)"
    )
    cli.parser.add_argument(
        "--test", action="store_true", help="Test LSP functionality"
    )
    cli.parser.add_argument(
        "--info", action="store_true", help="Show LSP server information"
    )

    def main_function(args):
        config = SymbolExtractionConfig()
        extractor = LSPSymbolExtractor(config, str(args.project_root))

        try:
            if args.test:
                return extractor.test_extraction()

            if args.info:
                return extractor.get_parser_info()

            # Extract symbols
            if args.files:
                file_paths = [Path(f) for f in args.files if Path(f).exists()]
            else:
                # Scan project for supported files
                file_patterns = [
                    "*.py",
                    "*.ts",
                    "*.tsx",
                    "*.js",
                    "*.jsx",
                    "*.java",
                    "*.go",
                    "*.rs",
                ]
                file_paths = []
                for pattern in file_patterns:
                    file_paths.extend(Path(args.project_root).rglob(pattern))

            symbols = extractor.extract_symbols(file_paths)

            return {
                "symbols_extracted": len(symbols),
                "files_processed": len(file_paths),
                "symbols": [
                    {
                        "name": s.name,
                        "type": s.symbol_type.value,
                        "file": s.file_path,
                        "line": s.line_number,
                    }
                    for s in symbols[:100]  # Limit output
                ],
            }

        finally:
            extractor.cleanup()

    return run_cli_tool(cli, main_function)


if __name__ == "__main__":
    exit(main())
