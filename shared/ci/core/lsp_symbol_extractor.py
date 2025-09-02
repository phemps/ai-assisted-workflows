#!/usr/bin/env python3
"""
LSP Symbol Extractor for Continuous Improvement Framework

Provides semantic symbol extraction using Language Server Protocol (LSP)
for true cross-file understanding, references, and type information.
Part of AI-Assisted Workflows.
"""

import asyncio
import gc
import logging
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

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
    from ci.core.memory_manager import MemoryManager
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

    # Phase 2: Symbol Origin Tracking
    enable_origin_tracking: bool = True
    enable_inheritance_detection: bool = True
    enable_import_deduplication: bool = True
    max_origin_depth: int = 3  # Limit inheritance chain traversal
    origin_cache_ttl: int = 3600  # Cache origin info for 1 hour

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProcessingMetrics:
    """Track performance metrics for async processing."""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.files_processed: int = 0
        self.symbols_extracted: int = 0
        self.failed_files: List[Tuple[Path, str]] = []
        self.worker_times: List[float] = []
        self.memory_peak_mb: float = 0.0

    @property
    def total_time(self) -> float:
        """Total processing time in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    @property
    def success_rate(self) -> float:
        """Percentage of successfully processed files."""
        total = self.files_processed + len(self.failed_files)
        return (self.files_processed / total * 100) if total > 0 else 0.0

    @property
    def symbols_per_second(self) -> float:
        """Processing rate in symbols per second."""
        return self.symbols_extracted / self.total_time if self.total_time > 0 else 0.0

    def add_failure(self, file_path: Path, error: str) -> None:
        """Record a failed file processing."""
        self.failed_files.append((file_path, error))

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for reporting."""
        return {
            "total_time_seconds": self.total_time,
            "files_processed": self.files_processed,
            "symbols_extracted": self.symbols_extracted,
            "failed_files_count": len(self.failed_files),
            "success_rate_percent": self.success_rate,
            "symbols_per_second": self.symbols_per_second,
            "memory_peak_mb": self.memory_peak_mb,
            "worker_performance": {
                "average_time": sum(self.worker_times) / len(self.worker_times)
                if self.worker_times
                else 0,
                "max_time": max(self.worker_times) if self.worker_times else 0,
                "min_time": min(self.worker_times) if self.worker_times else 0,
            },
        }


class LSPSymbolExtractor(CIConfigModule):
    """LSP-based symbol extractor for semantic analysis."""

    def __init__(
        self,
        config: SymbolExtractionConfig,
        project_root: str = ".",
        force_init: bool = False,
        memory_manager: Optional[MemoryManager] = None,
        max_workers: int = 4,
        enable_async: bool = True,
    ):
        super().__init__("lsp_symbol_extractor", project_root)

        self.config = config
        self.force_init = force_init
        self.performance_tracker = PerformanceTracker()
        self.project_root = Path(project_root).resolve()
        self.memory_manager = memory_manager
        self.max_workers = max_workers
        self.enable_async = enable_async

        # Phase 5: Async processing components
        self._semaphore = asyncio.Semaphore(max_workers) if enable_async else None
        self._processing_metrics = ProcessingMetrics()

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

    async def extract_symbols_async(
        self, file_paths: List[Path], max_workers: Optional[int] = None
    ) -> Tuple[List[Symbol], ProcessingMetrics]:
        """
        Extract symbols asynchronously with memory management.

        Args:
            file_paths: List of file paths to process
            max_workers: Override the default max workers for this operation

        Returns:
            Tuple of (extracted symbols, processing metrics)
        """
        if not self.enable_async:
            # Fallback to sync processing
            symbols = self.extract_symbols(file_paths)
            metrics = ProcessingMetrics()
            metrics.symbols_extracted = len(symbols)
            metrics.files_processed = len(file_paths)
            return symbols, metrics

        if not self.lsp_available:
            logger.warning("LSP not available, returning empty symbol list")
            return [], ProcessingMetrics()

        # Initialize metrics
        self._processing_metrics = ProcessingMetrics()
        self._processing_metrics.start_time = time.time()

        try:
            # Use memory manager for batch sizing if available
            batch_size = self.config.batch_size
            if self.memory_manager:
                batch_size = self.memory_manager.calculate_optimal_batch_size(
                    batch_size
                )

            workers = max_workers or self.max_workers
            if (
                self.memory_manager
                and self.memory_manager.get_memory_usage_percentage() > 80
            ):
                workers = min(workers, 2)  # Reduce workers under memory pressure

            logger.info(
                f"Starting async symbol extraction: {len(file_paths)} files with {workers} workers"
            )

            # Process files in batches to manage memory
            all_symbols = []
            batch_count = 0

            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i : i + batch_size]
                batch_count += 1

                logger.debug(f"Processing batch {batch_count}: {len(batch)} files")

                # Check memory before processing batch
                if self.memory_manager and self.memory_manager.should_throttle():
                    logger.warning("Memory usage high, throttling processing")
                    await asyncio.sleep(1.0)

                # Process batch concurrently
                batch_symbols = await self._process_batch_async(batch, workers)
                all_symbols.extend(batch_symbols)

                # Garbage collection after each batch
                if batch_count % 3 == 0:
                    gc.collect()
                    logger.debug(
                        f"Garbage collection completed after batch {batch_count}"
                    )

            self._processing_metrics.symbols_extracted = len(all_symbols)
            logger.info(
                f"Async processing complete: {self._processing_metrics.files_processed} files, "
                f"{self._processing_metrics.symbols_extracted} symbols, "
                f"{self._processing_metrics.success_rate:.1f}% success rate"
            )

            return all_symbols, self._processing_metrics

        except Exception as e:
            logger.error(f"Async processing failed: {e}")
            raise
        finally:
            self._processing_metrics.end_time = time.time()

    async def _process_batch_async(
        self, batch_files: List[Path], workers: int
    ) -> List[Symbol]:
        """
        Process a batch of files concurrently.

        Args:
            batch_files: Files to process in this batch
            workers: Number of concurrent workers

        Returns:
            List of extracted symbols from the batch
        """
        # Create semaphore for this batch to control concurrency
        semaphore = asyncio.Semaphore(workers)

        # Create tasks for concurrent processing
        tasks = [
            self._process_file_with_semaphore(file_path, semaphore)
            for file_path in batch_files
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        batch_symbols = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = str(result)
                self._processing_metrics.add_failure(batch_files[i], error_msg)
                logger.warning(f"Failed to process {batch_files[i]}: {error_msg}")
            else:
                symbols = result if isinstance(result, list) else []
                batch_symbols.extend(symbols)
                self._processing_metrics.files_processed += 1

        return batch_symbols

    async def _process_file_with_semaphore(
        self, file_path: Path, semaphore: asyncio.Semaphore
    ) -> List[Symbol]:
        """Process a single file with semaphore control."""
        async with semaphore:
            start_time = time.time()
            try:
                # Run the sync symbol extraction in a thread pool
                symbols = await asyncio.get_event_loop().run_in_executor(
                    None, self._extract_file_symbols_sync, file_path
                )
                worker_time = time.time() - start_time
                self._processing_metrics.worker_times.append(worker_time)
                return symbols
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                raise

    def _extract_file_symbols_sync(self, file_path: Path) -> List[Symbol]:
        """Extract symbols from a single file (sync wrapper for async processing)."""
        if not self._should_process_file(file_path):
            return []

        # Detect language and get appropriate server
        language = self._detect_language(file_path)
        if not language or language not in self.language_servers:
            return []

        server = self.language_servers[language]
        if not server:
            return []

        try:
            # Extract symbols using the existing sync method
            symbols = self._extract_file_symbols(server, file_path, language)
            return symbols
        except Exception as e:
            logger.error(f"Error extracting symbols from {file_path}: {e}")
            return []

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
        if not self.config.enable_origin_tracking:
            return symbols

        enriched_symbols = []
        for symbol in symbols:
            # Add origin tracking information
            origin_info = self._determine_symbol_origin(symbol, server, uri)

            # Update symbol with origin information
            symbol.definition_file = origin_info.get("definition_file")
            symbol.definition_line = origin_info.get("definition_line")
            symbol.is_reference = origin_info.get("is_reference", False)
            symbol.is_definition = origin_info.get("is_definition", True)
            symbol.parent_class = origin_info.get("parent_class")
            symbol.import_source = origin_info.get("import_source")
            symbol.origin_signature = origin_info.get("origin_signature")
            symbol.reference_count = origin_info.get("reference_count", 0)

            enriched_symbols.append(symbol)

        return enriched_symbols

    def _get_symbol_definition(
        self, server: SyncLanguageServer, symbol: Symbol, relative_path: str
    ) -> Optional[Dict[str, Any]]:
        """Get the original definition location for a symbol using LSP textDocument/definition."""
        try:
            # Get the line and column from the symbol
            line_number = symbol.line_number - 1  # LSP uses 0-based indexing
            column_number = 0  # Start of line by default

            # Request definition from LSP server
            definition_result = server.request_definition(
                relative_path, line_number, column_number
            )

            if (
                definition_result
                and isinstance(definition_result, tuple)
                and len(definition_result) > 0
            ):
                definitions = definition_result[0]
                if (
                    definitions
                    and isinstance(definitions, list)
                    and len(definitions) > 0
                ):
                    first_definition = definitions[0]
                    if isinstance(first_definition, dict):
                        uri = first_definition.get("uri", "")
                        range_info = first_definition.get("range", {})
                        start_pos = range_info.get("start", {})

                        # Extract file path from URI
                        definition_file = self._extract_file_from_uri(uri)
                        definition_line = (
                            start_pos.get("line", 0) + 1
                        )  # Convert to 1-based

                        return {
                            "definition_file": definition_file,
                            "definition_line": definition_line,
                            "uri": uri,
                        }

            return None

        except Exception as e:
            logger.debug(f"Error getting definition for {symbol.name}: {e}")
            return None

    def _get_symbol_references(
        self, server: SyncLanguageServer, symbol: Symbol, relative_path: str
    ) -> List[Dict[str, Any]]:
        """Get all references to a symbol using LSP textDocument/references."""
        try:
            line_number = symbol.line_number - 1  # LSP uses 0-based indexing
            column_number = 0  # Start of line by default

            # Request references from LSP server
            references_result = server.request_references(
                relative_path, line_number, column_number
            )

            references = []
            if (
                references_result
                and isinstance(references_result, tuple)
                and len(references_result) > 0
            ):
                reference_locations = references_result[0]
                if reference_locations and isinstance(reference_locations, list):
                    for ref_location in reference_locations:
                        if isinstance(ref_location, dict):
                            uri = ref_location.get("uri", "")
                            range_info = ref_location.get("range", {})
                            start_pos = range_info.get("start", {})

                            reference_file = self._extract_file_from_uri(uri)
                            reference_line = start_pos.get("line", 0) + 1

                            references.append(
                                {
                                    "file": reference_file,
                                    "line": reference_line,
                                    "uri": uri,
                                }
                            )

            return references

        except Exception as e:
            logger.debug(f"Error getting references for {symbol.name}: {e}")
            return []

    def _determine_symbol_origin(
        self, symbol: Symbol, server: SyncLanguageServer, relative_path: str
    ) -> Dict[str, Any]:
        """Determine if symbol is definition, reference, or inherited."""
        origin_info = {
            "definition_file": symbol.file_path,
            "definition_line": symbol.line_number,
            "is_reference": False,
            "is_definition": True,
            "parent_class": None,
            "import_source": None,
            "origin_signature": None,
            "reference_count": 0,
        }

        if not self.config.enable_origin_tracking:
            return origin_info

        try:
            # Get definition information
            definition_info = self._get_symbol_definition(server, symbol, relative_path)
            if definition_info:
                origin_info["definition_file"] = definition_info["definition_file"]
                origin_info["definition_line"] = definition_info["definition_line"]

                # Check if this symbol is a reference (definition is in a different location)
                current_file = Path(symbol.file_path).resolve()
                definition_file = (
                    Path(definition_info["definition_file"]).resolve()
                    if definition_info["definition_file"]
                    else current_file
                )

                if (
                    current_file != definition_file
                    or symbol.line_number != definition_info["definition_line"]
                ):
                    origin_info["is_reference"] = True
                    origin_info["is_definition"] = False

                    # For imports, extract the import source
                    if symbol.is_import or symbol.symbol_type == SymbolType.IMPORT:
                        origin_info["import_source"] = self._extract_import_source(
                            symbol
                        )

            # Get reference count
            if self.config.enable_reference_analysis:
                references = self._get_symbol_references(server, symbol, relative_path)
                origin_info["reference_count"] = len(references)

            # Generate unique origin signature for grouping
            origin_info["origin_signature"] = self._generate_origin_signature(
                symbol, origin_info
            )

            # Detect inheritance for methods and classes
            if self.config.enable_inheritance_detection and symbol.symbol_type in [
                SymbolType.METHOD,
                SymbolType.CLASS,
            ]:
                parent_class = self._detect_parent_class(symbol, server, relative_path)
                if parent_class:
                    origin_info["parent_class"] = parent_class
                    # Update origin signature to include parent class info
                    origin_info[
                        "origin_signature"
                    ] = f"{parent_class}::{origin_info['origin_signature']}"

        except Exception as e:
            logger.debug(f"Error determining origin for {symbol.name}: {e}")

        return origin_info

    def _extract_file_from_uri(self, uri: str) -> str:
        """Extract file path from LSP URI."""
        if uri.startswith("file://"):
            return uri[7:]  # Remove file:// prefix
        return uri

    def _extract_import_source(self, symbol: Symbol) -> Optional[str]:
        """Extract import source from import symbol."""
        if symbol.symbol_type == SymbolType.IMPORT:
            # Parse the line content to extract the import source
            line = symbol.line_content.strip()

            # Python imports
            if "from " in line and " import " in line:
                # from module import symbol
                parts = line.split(" import ")
                if len(parts) >= 2:
                    module_part = parts[0].replace("from ", "").strip()
                    return module_part
            elif line.startswith("import "):
                # import module
                return line.replace("import ", "").strip()

        return None

    def _generate_origin_signature(
        self, symbol: Symbol, origin_info: Dict[str, Any]
    ) -> str:
        """Generate unique origin signature for grouping symbols."""
        components = [
            origin_info.get("definition_file", symbol.file_path),
            str(origin_info.get("definition_line", symbol.line_number)),
            symbol.symbol_type.value,
            symbol.name,
        ]

        # Add import source if available
        if origin_info.get("import_source"):
            components.append(f"import:{origin_info['import_source']}")

        return "::".join(filter(None, components))

    def _detect_parent_class(
        self, symbol: Symbol, server: SyncLanguageServer, relative_path: str
    ) -> Optional[str]:
        """Detect parent class for inheritance tracking."""
        # This is a simplified implementation
        # In a full implementation, you would use LSP's typeHierarchy capabilities
        # For now, we'll detect based on scope and context

        if symbol.scope == "class" and symbol.symbol_type == SymbolType.METHOD:
            # This is a method within a class, try to determine the class name
            # This would need more sophisticated parsing or LSP hierarchy requests
            return None  # Placeholder for now

        return None

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
