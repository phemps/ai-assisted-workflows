#!/usr/bin/env python3
"""
Serena MCP Client for Continuous Improvement Framework
Provides MCP integration for AI-Assisted Workflows - requires MCP connection.
Part of AI-Assisted Workflows - integrates with 8-agent orchestration system.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "utils"))

# Import utilities
try:
    from shared.core.utils.output_formatter import AnalysisResult, ResultFormatter
    from shared.core.utils.tech_stack_detector import TechStackDetector
except ImportError as e:
    print(f"Error importing utilities: {e}", file=sys.stderr)
    sys.exit(1)

# Import Symbol from analyzers
try:
    from ..analyzers.symbol_extractor import Symbol
except ImportError:
    try:
        # Fallback for direct execution
        sys.path.insert(0, str(Path(__file__).parent.parent / "analyzers"))
        from symbol_extractor import Symbol
    except ImportError as e:
        print(f"Error importing Symbol components: {e}", file=sys.stderr)
        sys.exit(1)

# Required MCP imports - fail fast if not available
try:
    # These would be the actual MCP imports
    # import mcp_client
    # import serena_mcp_tools
    # Set to False until actual MCP imports are available
    MCP_AVAILABLE = False
except ImportError as e:
    print(f"ERROR: MCP libraries are required but not installed: {e}", file=sys.stderr)
    print("Please install MCP dependencies to use SerenaClient", file=sys.stderr)
    sys.exit(1)


class MCPConnectionStatus(Enum):
    """Status of MCP connection."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass
class MCPConfig:
    """Configuration for MCP client - MCP connection required."""

    # Connection settings
    server_endpoint: str = "mcp://serena/default"
    timeout_seconds: int = 30
    retry_attempts: int = 3

    # Feature flags
    enable_semantic_analysis: bool = True
    enable_ast_enhancement: bool = True
    enable_dependency_tracking: bool = True

    # Symbol filtering
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
    MCP client for Serena tools - requires MCP connection.
    Single-purpose component for Serena MCP integration only.
    """

    def __init__(
        self,
        config: Optional[MCPConfig] = None,
        project_root: Optional[Path] = None,
        force_init: bool = False,
    ):
        self.config = config or MCPConfig()
        self.project_root = project_root or Path.cwd()
        self.connection_status = MCPConnectionStatus.UNAVAILABLE

        # Initialize components
        self.tech_detector = TechStackDetector()
        self.result_formatter = ResultFormatter()

        # Connection state
        self._client = None
        self._last_connection_attempt = 0
        self._connection_errors = []

        # Initialize MCP - required for operation
        self._initialize_mcp()

        # Exit if MCP is not available (unless forced for testing)
        if not self.is_available() and not force_init:
            print(
                "ERROR: Serena MCP connection is required but unavailable",
                file=sys.stderr,
            )
            print(
                "This component requires a working MCP connection to function",
                file=sys.stderr,
            )
            sys.exit(1)

    def _initialize_mcp(self) -> None:
        """Initialize MCP connection - required for operation."""
        if not MCP_AVAILABLE:
            self.connection_status = MCPConnectionStatus.UNAVAILABLE
            print("ERROR: MCP libraries not available", file=sys.stderr)
            return

        try:
            # This would be the actual MCP initialization
            # self._client = mcp_client.connect(self.config.server_endpoint)
            # self.connection_status = MCPConnectionStatus.CONNECTED

            # Placeholder - set to UNAVAILABLE until real MCP is implemented
            self.connection_status = MCPConnectionStatus.UNAVAILABLE
            print("ERROR: MCP connection implementation not available", file=sys.stderr)

        except Exception as e:
            self.connection_status = MCPConnectionStatus.ERROR
            self._connection_errors.append(str(e))
            print(f"ERROR: MCP connection failed: {e}", file=sys.stderr)

    def is_available(self) -> bool:
        """Check if Serena MCP is available and connected."""
        return (
            MCP_AVAILABLE
            and self.connection_status == MCPConnectionStatus.CONNECTED
            and self._client is not None
        )

    def extract_symbols(self, file_paths: List[Path]) -> List[Symbol]:
        """
        Extract symbols using Serena MCP only - no fallback.

        Args:
            file_paths: List of files to analyze

        Returns:
            List of extracted symbols

        Raises:
            RuntimeError: If MCP is not available or connection fails
        """
        if not self.is_available():
            raise RuntimeError(
                "Serena MCP connection is not available. "
                "This component requires MCP to function."
            )

        try:
            return self._extract_with_mcp(file_paths)
        except Exception as e:
            self._connection_errors.append(str(e))
            error_msg = f"MCP extraction failed: {e}"
            print(f"ERROR: {error_msg}", file=sys.stderr)
            raise RuntimeError(error_msg)

    def _extract_with_mcp(self, file_paths: List[Path]) -> List[Symbol]:
        """
        Extract symbols using Serena MCP tools.
        This is a placeholder for the actual MCP integration.
        """
        if not self.is_available():
            raise RuntimeError("MCP connection not available")

        symbols = []

        for file_path in file_paths:
            try:
                if not file_path.exists():
                    print(f"WARNING: File not found: {file_path}", file=sys.stderr)
                    continue

                # Placeholder for actual MCP call
                # content = file_path.read_text(
                #     encoding="utf-8", errors="ignore"
                # )
                # mcp_result = self._client.analyze_file(
                #     file_path=str(file_path),
                #     content=content,
                #     config={
                #         "include_types":
                #             self.config.include_symbol_types,
                #         "enable_semantic":
                #             self.config.enable_semantic_analysis,
                #         "enable_ast":
                #             self.config.enable_ast_enhancement
                #     }
                # )
                # file_symbols = self._convert_mcp_symbols(
                #     mcp_result, file_path
                # )
                # filtered_symbols = self._apply_filters(file_symbols)
                # symbols.extend(filtered_symbols)

                # Placeholder - raise error since MCP not implemented
                raise RuntimeError("MCP implementation not yet available")

            except Exception as e:
                error_msg = f"MCP analysis failed for {file_path}: {e}"
                print(f"ERROR: {error_msg}", file=sys.stderr)
                raise RuntimeError(error_msg)

        return symbols

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
                type_val = symbol.symbol_type.value
                if type_val not in self.config.include_symbol_types:
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
            "mcp_only": True,
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
        Test symbol extraction on a file to verify MCP functionality.

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

        # Check MCP availability first
        if not self.is_available():
            return self._create_error_result(
                "MCP connection not available - cannot perform test"
            )

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
                            f"{symbol.symbol_type.value} symbol via MCP"
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
            from shared.core.utils.output_formatter import (
                AnalysisResult,
                AnalysisType,
                Finding,
                Severity,
            )

            result = AnalysisResult(
                analysis_type=AnalysisType.CODE_QUALITY,
                script_name="serena_mcp_test.py",
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
                    "extraction_method": "mcp",
                    "execution_time_seconds": round(execution_time, 2),
                    "connection_info": self.get_connection_info(),
                    "project_root": str(self.project_root),
                }
            )

            result.set_execution_time(start_time)

            return result

        except Exception as e:
            return self._create_error_result(f"MCP test extraction failed: {e}")

    def _create_error_result(self, error_message: str) -> AnalysisResult:
        """Create an error result for failed operations."""
        from shared.core.utils.output_formatter import (
            AnalysisResult,
            AnalysisType,
            Finding,
            Severity,
        )

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
    """Main entry point for testing Serena MCP client functionality."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Serena MCP client - requires MCP connection"
    )
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--test-file", type=Path, help="File to test extraction on")
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force test even if MCP unavailable (will fail)",
    )

    args = parser.parse_args()

    print("Serena MCP Client - Testing MCP functionality...")
    print("NOTE: This tool requires a working MCP connection to function.\n")

    try:
        # Create configuration (no fallback options)
        config = MCPConfig()

        # Initialize client (will exit if MCP unavailable unless forced)
        if args.force:
            print(
                "WARNING: Forcing initialization despite MCP "
                "unavailability (operations will fail)"
            )

        client = SerenaClient(config, args.project_root, force_init=args.force)

        # Test extraction
        result = client.test_extraction(args.test_file)

        # Output results
        if args.output == "json":
            formatter = ResultFormatter()
            print(formatter.format_result(result))
        else:
            metadata = result.metadata
            connection_info = metadata.get("connection_info", {})

            print("Serena MCP Client Test Results:")
            success = metadata.get("test_successful", False)
            print(f"  Test successful: {success}")
            num_symbols = metadata.get("symbols_extracted", 0)
            print(f"  Symbols extracted: {num_symbols}")
            method = metadata.get("extraction_method", "unknown")
            print(f"  Extraction method: {method}")
            exec_time = metadata.get("execution_time_seconds", 0)
            print(f"  Execution time: {exec_time}s")
            print("\nMCP Connection Status:")
            print(f"  Status: {connection_info.get('status', 'unknown')}")
            mcp_avail = connection_info.get("mcp_available", False)
            print(f"  MCP Available: {mcp_avail}")
            mcp_only = connection_info.get("mcp_only", True)
            print(f"  MCP Only Mode: {mcp_only}")

            if connection_info.get("error_count", 0) > 0:
                errors = connection_info.get("recent_errors", [])
                print(f"  Recent errors: {errors}")

            if not result.success:
                print(f"\nError: {result.error_message or 'Unknown error'}")
            elif not metadata.get("test_successful", False):
                print("\nTest failed but no specific error reported")

    except SystemExit:
        print("EXITED: MCP connection required but not available")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
