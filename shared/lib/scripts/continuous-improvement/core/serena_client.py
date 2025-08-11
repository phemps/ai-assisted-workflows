#!/usr/bin/env python3
"""
Serena MCP Client for Continuous Improvement Framework
Provides MCP integration wrapper with graceful degradation to AST extraction.
Part of Claude Code Workflows - integrates with 8-agent orchestration system.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))

# Import utilities and existing components
try:
    from output_formatter import AnalysisResult, ResultFormatter
    from tech_stack_detector import TechStackDetector
except ImportError as e:
    print(f"Error importing utilities: {e}", file=sys.stderr)
    sys.exit(1)

# Import Symbol from analyzers
try:
    from ..analyzers.symbol_extractor import Symbol, SerenaFallbackExtractor
except ImportError:
    try:
        # Fallback for direct execution
        sys.path.insert(0, str(Path(__file__).parent.parent / "analyzers"))
        from symbol_extractor import Symbol, SerenaFallbackExtractor
    except ImportError as e:
        print(f"Error importing Symbol components: {e}", file=sys.stderr)
        sys.exit(1)

# Optional MCP imports with graceful degradation
MCP_AVAILABLE = False
try:
    # These would be the actual MCP imports when available
    # import mcp_client
    # import serena_mcp_tools
    pass
except ImportError:
    MCP_AVAILABLE = False


class MCPConnectionStatus(Enum):
    """Status of MCP connection."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass
class MCPConfig:
    """Configuration for MCP client following existing patterns."""

    # Connection settings
    server_endpoint: str = "mcp://serena/default"
    timeout_seconds: int = 30
    retry_attempts: int = 3

    # Feature flags
    enable_semantic_analysis: bool = True
    enable_ast_enhancement: bool = True
    enable_dependency_tracking: bool = True

    # Fallback behavior
    use_ast_fallback: bool = True
    fallback_threshold_seconds: float = 5.0

    # Symbol filtering (compatible with existing config)
    max_symbols_per_request: int = 1000
    include_symbol_types: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize default filters."""
        if self.include_symbol_types is None:
            self.include_symbol_types = ["function", "class", "method", "interface"]

        if self.exclude_patterns is None:
            self.exclude_patterns = ["test_*", "*_test.py", "*/test/*", "*.spec.*"]


class SerenaClient:
    """
    MCP client for Serena tools with robust AST fallback.
    Integrates with existing SymbolExtractor architecture.
    """

    def __init__(
        self, config: Optional[MCPConfig] = None, project_root: Optional[Path] = None
    ):
        self.config = config or MCPConfig()
        self.project_root = project_root or Path.cwd()
        self.connection_status = MCPConnectionStatus.UNAVAILABLE

        # Initialize components
        self.tech_detector = TechStackDetector()
        self.fallback_extractor = SerenaFallbackExtractor()
        self.result_formatter = ResultFormatter()

        # Connection state
        self._client = None
        self._last_connection_attempt = 0
        self._connection_errors = []

        # Initialize MCP if available
        self._initialize_mcp()

    def _initialize_mcp(self) -> None:
        """Initialize MCP connection with error handling."""
        if not MCP_AVAILABLE:
            self.connection_status = MCPConnectionStatus.UNAVAILABLE
            return

        try:
            # This would be the actual MCP initialization
            # self._client = mcp_client.connect(self.config.server_endpoint)
            # self.connection_status = MCPConnectionStatus.CONNECTED
            # Placeholder
            self.connection_status = MCPConnectionStatus.UNAVAILABLE

        except Exception as e:
            self.connection_status = MCPConnectionStatus.ERROR
            self._connection_errors.append(str(e))
            print(f"MCP connection failed: {e}", file=sys.stderr)

    def is_available(self) -> bool:
        """Check if Serena MCP is available and connected."""
        return (
            MCP_AVAILABLE
            and self.connection_status == MCPConnectionStatus.CONNECTED
            and self._client is not None
        )

    def extract_symbols(self, file_paths: List[Path]) -> List[Symbol]:
        """
        Extract symbols using Serena MCP with fallback to AST.

        Args:
            file_paths: List of files to analyze

        Returns:
            List of extracted symbols
        """
        start_time = time.time()

        # Try MCP extraction first if available
        if self.is_available():
            try:
                symbols = self._extract_with_mcp(file_paths)

                # Check if extraction took too long or failed
                elapsed = time.time() - start_time
                if symbols and elapsed < self.config.fallback_threshold_seconds:
                    return symbols

            except Exception as e:
                self._connection_errors.append(str(e))
                print(f"MCP extraction failed, using fallback: {e}", file=sys.stderr)

        # Fallback to AST/regex extraction
        if self.config.use_ast_fallback:
            return self._extract_with_fallback(file_paths)
        else:
            return []

    def _extract_with_mcp(self, file_paths: List[Path]) -> Optional[List[Symbol]]:
        """
        Extract symbols using Serena MCP tools.
        This is a placeholder for the actual MCP integration.
        """
        if not self.is_available():
            return None

        symbols = []

        for file_path in file_paths:
            try:
                if not file_path.exists():
                    continue

                # Placeholder for actual MCP call
                # mcp_result = self._client.analyze_file(
                #     file_path=str(file_path),
                #     content=content,
                #     config={
                #         "include_types":
                #           self.config.include_symbol_types,
                #         "enable_semantic":
                #           self.config.enable_semantic_analysis,
                #         "enable_ast":
                #           self.config.enable_ast_enhancement
                #     }
                # )
                # symbols.extend(self._convert_mcp_symbols(
                #     mcp_result, file_path))

                # For now, return None to trigger fallback
                return None

            except Exception as e:
                print(f"MCP analysis failed for {file_path}: {e}", file=sys.stderr)
                continue

        return symbols

    def _extract_with_fallback(self, file_paths: List[Path]) -> List[Symbol]:
        """Extract symbols using existing AST/regex fallback."""
        all_symbols = []

        for file_path in file_paths:
            try:
                if not file_path.exists():
                    continue

                content = file_path.read_text(encoding="utf-8", errors="ignore")

                # Use existing fallback extractor
                if file_path.suffix == ".py":
                    symbols = self.fallback_extractor.extract_python_symbols_ast(
                        content, file_path
                    )
                else:
                    symbols = self.fallback_extractor.extract_symbols_regex(
                        content, file_path
                    )

                # Apply filtering
                filtered_symbols = self._apply_filters(symbols)
                all_symbols.extend(filtered_symbols)

            except Exception as e:
                print(
                    f"Fallback extraction failed for {file_path}: {e}", file=sys.stderr
                )
                continue

        return all_symbols

    def _convert_mcp_symbols(
        self, mcp_result: Dict[str, Any], file_path: Path
    ) -> List[Symbol]:
        """
        Convert MCP response to Symbol objects.
        This would handle the actual MCP response format.
        """
        symbols = []

        # Placeholder for MCP response parsing
        # for mcp_symbol in mcp_result.get("symbols", []):
        #     symbol = Symbol(
        #         name=mcp_symbol["name"],
        #         symbol_type=SymbolType(mcp_symbol["type"]),
        #         file_path=str(file_path),
        #         line_number=mcp_symbol["line"],
        #         line_content=mcp_symbol["content"],
        #         scope=mcp_symbol.get("scope", "module"),
        #         visibility=mcp_symbol.get("visibility"),
        #         parameters=mcp_symbol.get("parameters"),
        #         return_type=mcp_symbol.get("return_type"),
        #         complexity=mcp_symbol.get("complexity"),
        #         dependencies=mcp_symbol.get("dependencies")
        #     )
        #     symbols.append(symbol)

        return symbols

    def _apply_filters(self, symbols: List[Symbol]) -> List[Symbol]:
        """Apply configured filters to symbols."""
        filtered = []

        for symbol in symbols:
            # Type filtering
            if self.config.include_symbol_types:
                if symbol.symbol_type.value not in self.config.include_symbol_types:
                    continue

            # Pattern exclusions (basic check)
            excluded = False
            for pattern in self.config.exclude_patterns:
                if pattern.replace("*", "") in symbol.file_path.lower():
                    excluded = True
                    break

            if excluded:
                continue

            filtered.append(symbol)

            # Limit check
            if len(filtered) >= self.config.max_symbols_per_request:
                break

        return filtered

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection status and diagnostic information."""
        return {
            "status": self.connection_status.value,
            "mcp_available": MCP_AVAILABLE,
            "is_connected": self.is_available(),
            "server_endpoint": self.config.server_endpoint,
            "last_attempt": self._last_connection_attempt,
            "error_count": len(self._connection_errors),
            "recent_errors": (
                self._connection_errors[-3:] if self._connection_errors else []
            ),
            "fallback_enabled": self.config.use_ast_fallback,
            "config": {
                "timeout": self.config.timeout_seconds,
                "retry_attempts": self.config.retry_attempts,
                "max_symbols": self.config.max_symbols_per_request,
            },
        }

    def reconnect(self) -> bool:
        """Attempt to reconnect to MCP server."""
        self._last_connection_attempt = time.time()
        self._initialize_mcp()
        return self.is_available()

    def test_extraction(self, test_file_path: Optional[Path] = None) -> AnalysisResult:
        """
        Test symbol extraction on a file to verify functionality.

        Args:
            test_file_path: Optional specific file to test
                (defaults to self analysis)

        Returns:
            AnalysisResult with test findings
        """
        start_time = time.time()

        # Use this file as test subject if none provided
        if test_file_path is None:
            test_file_path = Path(__file__)

        if not test_file_path.exists():
            return self._create_error_result(f"Test file not found: {test_file_path}")

        try:
            symbols = self.extract_symbols([test_file_path])

            # Create test findings
            findings = []
            # Limit to first 5 for test
            for i, symbol in enumerate(symbols[:5]):
                findings.append(
                    {
                        "finding_id": f"test_symbol_{i:03d}",
                        "title": f"Test Symbol: {symbol.name}",
                        "description": (
                            f"Successfully extracted "
                            f"{symbol.symbol_type.value} symbol"
                        ),
                        "severity": "info",
                        "file_path": symbol.file_path,
                        "line_number": symbol.line_number,
                        "evidence": {
                            "symbol_type": symbol.symbol_type.value,
                            "name": symbol.name,
                            "scope": symbol.scope,
                            "line_content": symbol.line_content[:100],
                        },
                    }
                )

            execution_time = time.time() - start_time

            # Convert findings to proper Finding objects
            from output_formatter import AnalysisResult, AnalysisType, Finding, Severity

            result = AnalysisResult(
                analysis_type=AnalysisType.CODE_QUALITY,
                script_name="serena_client_test.py",
                target_path=str(test_file_path),
            )

            # Add findings
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

            # Add metadata
            result.metadata.update(
                {
                    "test_successful": True,
                    "symbols_extracted": len(symbols),
                    "test_file": str(test_file_path),
                    "extraction_method": ("mcp" if self.is_available() else "fallback"),
                    "execution_time_seconds": round(execution_time, 2),
                    "connection_info": self.get_connection_info(),
                    "project_root": str(self.project_root),
                }
            )

            result.set_execution_time(start_time)

            return result

        except Exception as e:
            return self._create_error_result(f"Test extraction failed: {e}")

    def _create_error_result(self, error_message: str) -> AnalysisResult:
        """Create an error result for failed operations."""
        from output_formatter import AnalysisResult, AnalysisType, Finding, Severity

        result = AnalysisResult(
            analysis_type=AnalysisType.CODE_QUALITY,
            script_name="serena_client_error.py",
            target_path=str(self.project_root),
        )

        # Add error finding
        error_finding = Finding(
            finding_id="error_001",
            title="Serena Client Error",
            description=error_message,
            severity=Severity.HIGH,
            evidence={"error_details": error_message},
        )
        result.add_finding(error_finding)

        # Mark as failed
        result.set_error(error_message)

        # Add metadata
        result.metadata.update(
            {"test_successful": False, "connection_info": self.get_connection_info()}
        )

        return result


def main():
    """Main entry point for testing Serena client functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Serena MCP client with fallback")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--test-file", type=Path, help="File to test extraction on")
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )
    parser.add_argument(
        "--no-fallback", action="store_true", help="Disable AST fallback"
    )

    args = parser.parse_args()

    # Create configuration
    config = MCPConfig(use_ast_fallback=not args.no_fallback)

    # Initialize client
    client = SerenaClient(config, args.project_root)

    # Test extraction
    result = client.test_extraction(args.test_file)

    # Output results
    if args.output == "json":
        formatter = ResultFormatter()
        print(formatter.format_result(result))
    else:
        metadata = result.metadata
        connection_info = metadata.get("connection_info", {})

        print("Serena Client Test Results:")
        print(f"  Test successful: " f"{metadata.get('test_successful', False)}")
        print(f"  Symbols extracted: " f"{metadata.get('symbols_extracted', 0)}")
        print(
            f"  Extraction method: " f"{metadata.get('extraction_method', 'unknown')}"
        )
        print(f"  Execution time: " f"{metadata.get('execution_time_seconds', 0)}s")
        print("\nConnection Status:")
        print(f"  Status: {connection_info.get('status', 'unknown')}")
        print(f"  MCP Available: " f"{connection_info.get('mcp_available', False)}")
        print(
            f"  Fallback enabled: " f"{connection_info.get('fallback_enabled', False)}"
        )

        if connection_info.get("error_count", 0) > 0:
            print(f"  Recent errors: " f"{connection_info.get('recent_errors', [])}")

        if not result.success:
            print(f"\nError: {result.error_message or 'Unknown error'}")
        elif not metadata.get("test_successful", False):
            print("\nTest failed but no specific error reported")


if __name__ == "__main__":
    main()
