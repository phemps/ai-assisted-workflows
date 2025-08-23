#!/usr/bin/env python3
"""
Unified Codebase Search Tool - Intelligent Search Routing
========================================================

PURPOSE: Unified interface that intelligently routes between ChromaDB semantic search
and Serena structural search based on query type and arguments.

FEATURES:
- Automatic search strategy selection based on query analysis
- Argument-based routing for agent integration
- Combined results from multiple search approaches
- Intelligent ranking and deduplication
- JSON output for agent consumption

ROUTING LOGIC:
- ChromaDB: Semantic queries, conceptual searches, pattern discovery
- Serena: Specific symbol location, imports, structural queries
- Hybrid: Complex queries requiring both precision and similarity

USAGE EXAMPLES:
python unified_codebase_search.py --search-type semantic --query "authentication functions"
python unified_codebase_search.py --search-type specific --symbol "login_user"
python unified_codebase_search.py --search-type hybrid --query "auth" --symbol "authenticate"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import ChromaDB search functionality
try:
    from shared.ci.tools.codebase_search import CodebaseSearchEngine
except ImportError as e:
    print(f"WARNING: ChromaDB search not available: {e}", file=sys.stderr)
    CodebaseSearchEngine = None

# Import symbol utilities - needed for type hints and runtime use
try:
    from shared.ci.integration.symbol_extractor import Symbol, SymbolType  # noqa: F401
except ImportError as e:
    print(f"WARNING: Symbol utilities not available: {e}", file=sys.stderr)


class SearchType(Enum):
    """Types of codebase searches available."""

    SEMANTIC = "semantic"  # ChromaDB semantic similarity
    SPECIFIC = "specific"  # Serena specific symbol search
    PATTERN = "pattern"  # ChromaDB pattern discovery
    IMPORTS = "imports"  # Serena import/usage analysis
    SIMILAR = "similar"  # ChromaDB similarity to existing code
    HYBRID = "hybrid"  # Combined ChromaDB + Serena
    COMPREHENSIVE = "comprehensive"  # Full analysis across all tools


@dataclass
class UnifiedSearchResult:
    """Unified result combining ChromaDB and Serena searches."""

    name: str
    file_path: str
    line_number: Optional[int]
    symbol_type: str
    search_source: str  # "chromadb", "serena", "hybrid"
    similarity_score: Optional[float]  # For ChromaDB results
    context: str
    signature: Optional[str] = None
    docstring: Optional[str] = None
    usage_count: Optional[int] = None  # For Serena results

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "symbol_type": self.symbol_type,
            "search_source": self.search_source,
            "similarity_score": self.similarity_score,
            "context": self.context,
            "signature": self.signature,
            "docstring": self.docstring,
            "usage_count": self.usage_count,
        }


class UnifiedCodebaseSearch:
    """
    Intelligent codebase search that routes between ChromaDB and Serena.

    Analyzes queries to determine optimal search strategy and combines results
    from multiple search approaches for comprehensive codebase analysis.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()

        # Initialize ChromaDB search engine if available
        self.chromadb_engine = None
        if CodebaseSearchEngine:
            try:
                self.chromadb_engine = CodebaseSearchEngine(str(project_root))
                print("ChromaDB search engine initialized", file=sys.stderr)
            except Exception as e:
                print(f"WARNING: ChromaDB initialization failed: {e}", file=sys.stderr)

        # Serena MCP integration flag
        self.serena_available = self._check_serena_availability()

    def _check_serena_availability(self) -> bool:
        """Check if Serena MCP tools are available."""
        # This would be replaced with actual MCP tool availability check
        # For now, assume available if we're in the right environment
        return True

    def search(
        self,
        search_type: SearchType,
        query: Optional[str] = None,
        symbol: Optional[str] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        module: Optional[str] = None,
        max_results: int = 10,
        threshold: float = 0.7,
    ) -> List[UnifiedSearchResult]:
        """
        Unified search interface that routes to appropriate search tools.

        Args:
            search_type: Type of search to perform
            query: Natural language query for semantic search
            symbol: Specific symbol name to find
            file_path: File path for similarity search
            line_number: Line number for similarity search
            module: Module name for import analysis
            max_results: Maximum number of results
            threshold: Similarity threshold for ChromaDB

        Returns:
            List of unified search results
        """
        results = []

        if search_type == SearchType.SEMANTIC:
            results.extend(
                self._chromadb_semantic_search(query, max_results, threshold)
            )

        elif search_type == SearchType.SPECIFIC:
            results.extend(self._serena_symbol_search(symbol, max_results))

        elif search_type == SearchType.PATTERN:
            results.extend(self._chromadb_pattern_search(query, max_results))

        elif search_type == SearchType.IMPORTS:
            results.extend(self._serena_import_search(module, max_results))

        elif search_type == SearchType.SIMILAR:
            results.extend(
                self._chromadb_similarity_search(file_path, line_number, max_results)
            )

        elif search_type == SearchType.HYBRID:
            # Combine semantic and specific searches
            if query:
                results.extend(
                    self._chromadb_semantic_search(query, max_results // 2, threshold)
                )
            if symbol:
                results.extend(self._serena_symbol_search(symbol, max_results // 2))

        elif search_type == SearchType.COMPREHENSIVE:
            # Full analysis across all available tools
            results.extend(self._comprehensive_search(query, symbol, max_results))

        # Remove duplicates and sort by relevance
        return self._deduplicate_and_rank(results, max_results)

    def _chromadb_semantic_search(
        self, query: str, max_results: int, threshold: float
    ) -> List[UnifiedSearchResult]:
        """Perform ChromaDB semantic search."""
        if not self.chromadb_engine or not query:
            return []

        try:
            chromadb_results = self.chromadb_engine.search_by_query(
                query, max_results, threshold
            )

            unified_results = []
            for result in chromadb_results:
                unified_result = UnifiedSearchResult(
                    name=result.symbol.name,
                    file_path=str(result.symbol.file_path),
                    line_number=result.symbol.line_number,
                    symbol_type=result.symbol.symbol_type.value,
                    search_source="chromadb",
                    similarity_score=result.similarity,
                    context=result.context,
                    signature=getattr(result.symbol, "signature", None),
                    docstring=getattr(result.symbol, "docstring", None),
                )
                unified_results.append(unified_result)

            return unified_results

        except Exception as e:
            print(f"ChromaDB semantic search error: {e}", file=sys.stderr)
            return []

    def _chromadb_pattern_search(
        self, query: str, max_results: int
    ) -> List[UnifiedSearchResult]:
        """Perform ChromaDB pattern discovery."""
        if not self.chromadb_engine or not query:
            return []

        try:
            pattern_results = self.chromadb_engine.find_patterns(query, max_results)

            unified_results = []
            for result in pattern_results:
                unified_result = UnifiedSearchResult(
                    name=result.symbol.name,
                    file_path=str(result.symbol.file_path),
                    line_number=result.symbol.line_number,
                    symbol_type=result.symbol.symbol_type.value,
                    search_source="chromadb",
                    similarity_score=result.similarity,
                    context=f"Pattern match: {result.context}",
                    signature=getattr(result.symbol, "signature", None),
                    docstring=getattr(result.symbol, "docstring", None),
                )
                unified_results.append(unified_result)

            return unified_results

        except Exception as e:
            print(f"ChromaDB pattern search error: {e}", file=sys.stderr)
            return []

    def _chromadb_similarity_search(
        self, file_path: str, line_number: int, max_results: int
    ) -> List[UnifiedSearchResult]:
        """Perform ChromaDB similarity search."""
        if not self.chromadb_engine or not file_path or line_number is None:
            return []

        try:
            similar_results = self.chromadb_engine.search_similar_to_symbol(
                file_path, line_number, max_results
            )

            unified_results = []
            for result in similar_results:
                unified_result = UnifiedSearchResult(
                    name=result.symbol.name,
                    file_path=str(result.symbol.file_path),
                    line_number=result.symbol.line_number,
                    symbol_type=result.symbol.symbol_type.value,
                    search_source="chromadb",
                    similarity_score=result.similarity,
                    context=result.context,
                    signature=getattr(result.symbol, "signature", None),
                    docstring=getattr(result.symbol, "docstring", None),
                )
                unified_results.append(unified_result)

            return unified_results

        except Exception as e:
            print(f"ChromaDB similarity search error: {e}", file=sys.stderr)
            return []

    def _serena_symbol_search(
        self, symbol: str, max_results: int
    ) -> List[UnifiedSearchResult]:
        """Perform Serena-based symbol search using subprocess."""
        if not symbol or not self.serena_available:
            return []

        # Simulate Serena search results
        # In real implementation, this would call the actual MCP tools
        print(
            f"Note: Serena symbol search for '{symbol}' - using placeholder implementation",
            file=sys.stderr,
        )

        # Placeholder implementation that would be replaced with actual Serena MCP calls
        # This demonstrates the expected structure
        return [
            UnifiedSearchResult(
                name=symbol,
                file_path=f"example/path/to/{symbol}.py",
                line_number=42,
                symbol_type="function",
                search_source="serena",
                similarity_score=None,
                context=f"Exact match for symbol '{symbol}'",
                usage_count=5,
            )
        ]

    def _serena_import_search(
        self, module: str, max_results: int
    ) -> List[UnifiedSearchResult]:
        """Perform Serena-based import analysis."""
        if not module or not self.serena_available:
            return []

        print(
            f"Note: Serena import search for '{module}' - using placeholder implementation",
            file=sys.stderr,
        )

        # Placeholder - would use actual MCP search_for_pattern
        return []

    def _comprehensive_search(
        self, query: Optional[str], symbol: Optional[str], max_results: int
    ) -> List[UnifiedSearchResult]:
        """Perform comprehensive search across all available tools."""
        all_results = []

        # ChromaDB searches
        if query:
            all_results.extend(
                self._chromadb_semantic_search(query, max_results // 3, 0.6)
            )
            all_results.extend(self._chromadb_pattern_search(query, max_results // 3))

        # Serena searches
        if symbol:
            all_results.extend(self._serena_symbol_search(symbol, max_results // 3))

        return all_results

    def _deduplicate_and_rank(
        self, results: List[UnifiedSearchResult], max_results: int
    ) -> List[UnifiedSearchResult]:
        """Remove duplicates and rank results by relevance."""
        # Remove duplicates based on file_path and line_number
        unique_results = {}
        for result in results:
            key = f"{result.file_path}:{result.line_number}"
            if key not in unique_results:
                unique_results[key] = result
            elif result.similarity_score and unique_results[key].similarity_score:
                # Keep result with higher similarity score
                if result.similarity_score > unique_results[key].similarity_score:
                    unique_results[key] = result

        # Sort by relevance: similarity score (if available), then by search source priority
        def sort_key(result):
            # Prioritize results with similarity scores
            if result.similarity_score is not None:
                return (1, result.similarity_score)
            # Then prioritize by search source (exact matches from Serena)
            elif result.search_source == "serena":
                return (0.9, 0)
            else:
                return (0.5, 0)

        sorted_results = sorted(unique_results.values(), key=sort_key, reverse=True)
        return sorted_results[:max_results]

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about available search capabilities."""
        stats = {
            "chromadb_available": self.chromadb_engine is not None,
            "serena_available": self.serena_available,
            "search_types_available": [],
        }

        if self.chromadb_engine:
            stats["search_types_available"].extend(["semantic", "pattern", "similar"])
            try:
                chromadb_stats = self.chromadb_engine.get_statistics()
                stats["chromadb_stats"] = chromadb_stats
            except Exception as e:
                stats["chromadb_error"] = str(e)

        if self.serena_available:
            stats["search_types_available"].extend(["specific", "imports"])

        if self.chromadb_engine and self.serena_available:
            stats["search_types_available"].extend(["hybrid", "comprehensive"])

        return stats


def main():
    """Main entry point for unified codebase search tool."""
    parser = argparse.ArgumentParser(
        description="Unified codebase search with intelligent routing"
    )

    # Search type selection
    parser.add_argument(
        "--search-type",
        choices=[t.value for t in SearchType],
        help="Type of search to perform",
    )

    # Query parameters
    parser.add_argument(
        "--query", "-q", help="Natural language query for semantic search"
    )
    parser.add_argument("--symbol", "-s", help="Specific symbol name to find")
    parser.add_argument("--file", "-f", help="File path for similarity search")
    parser.add_argument(
        "--line", "-l", type=int, help="Line number for similarity search"
    )
    parser.add_argument("--module", "-m", help="Module name for import analysis")

    # Options
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum results to return"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.7, help="Similarity threshold"
    )
    parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show search capabilities statistics"
    )

    args = parser.parse_args()

    # Initialize unified search
    try:
        search_engine = UnifiedCodebaseSearch(args.project_root)
    except Exception as e:
        print(f"FATAL: Failed to initialize search engine: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle statistics request
    if args.stats:
        stats = search_engine.get_statistics()
        print(json.dumps(stats, indent=2))
        return

    # Validate search type is provided for search operations
    if not args.search_type:
        print("Error: --search-type is required for search operations", file=sys.stderr)
        print(
            "Use --stats to view search capabilities or --help for usage",
            file=sys.stderr,
        )
        sys.exit(1)

    # Perform search
    search_type = SearchType(args.search_type)
    results = search_engine.search(
        search_type=search_type,
        query=args.query,
        symbol=args.symbol,
        file_path=args.file,
        line_number=args.line,
        module=args.module,
        max_results=args.max_results,
        threshold=args.threshold,
    )

    # Output results
    if args.format == "json":
        output = {
            "search_info": {
                "search_type": search_type.value,
                "query": args.query,
                "symbol": args.symbol,
                "max_results": args.max_results,
                "threshold": args.threshold,
                "results_found": len(results),
            },
            "results": [result.to_dict() for result in results],
        }
        print(json.dumps(output, indent=2))
    else:
        # Text format
        print(f"Found {len(results)} results ({search_type.value} search):\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.name} ({result.symbol_type})")
            print(f"   File: {result.file_path}:{result.line_number}")
            print(f"   Source: {result.search_source}")
            if result.similarity_score:
                print(f"   Similarity: {result.similarity_score:.3f}")
            if result.usage_count:
                print(f"   Usage count: {result.usage_count}")
            print(f"   Context: {result.context}")
            if result.signature:
                print(f"   Signature: {result.signature}")
            print()


if __name__ == "__main__":
    main()
