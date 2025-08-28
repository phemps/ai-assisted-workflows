#!/usr/bin/env python3
"""
Codebase Search Tool - ChromaDB Semantic Query Interface
=========================================================

PURPOSE: Command-line interface for semantic code search using ChromaDB.
Enables natural language queries to find similar functions, patterns, and reusable components.

FEATURES:
- Natural language query to semantic search
- Function similarity search by file/line reference
- Pattern discovery across the codebase
- JSON output for agent integration

DEPENDENCIES:
- ChromaDBStorage: Existing vector storage system
- EmbeddingEngine: CodeBERT embeddings from duplicate detection
- Symbol extraction infrastructure

USAGE EXAMPLES:
python codebase_search.py --query "function that validates user input"
python codebase_search.py --similar-to "src/auth.py:42"
python codebase_search.py --find-patterns "error handling middleware"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Setup import paths and import CI components
try:
    from utils import path_resolver  # noqa: F401
    from ci.core.chromadb_storage import ChromaDBStorage, ChromaDBConfig
    from ci.core.embedding_engine import EmbeddingEngine, EmbeddingConfig
    from ci.integration.symbol_extractor import Symbol, SymbolType
    from ci.core.lsp_symbol_extractor import LSPSymbolExtractor, SymbolExtractionConfig
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class CodebaseSearchResult:
    """Structured result from codebase search."""

    def __init__(self, symbol: Symbol, similarity: float, context: str = ""):
        self.symbol = symbol
        self.similarity = similarity
        self.context = context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "name": self.symbol.name,
            "file_path": str(self.symbol.file_path),
            "line_number": self.symbol.line_number,
            "symbol_type": self.symbol.symbol_type.value,
            "similarity_score": self.similarity,
            "context": self.context,
            "signature": getattr(self.symbol, "signature", ""),
            "docstring": getattr(self.symbol, "docstring", ""),
        }


class CodebaseSearchEngine:
    """
    Semantic search engine for codebase exploration.

    Leverages ChromaDB and CodeBERT embeddings from the duplicate detection system.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()

        # Initialize ChromaDB storage
        self.chromadb_config = ChromaDBConfig(
            persist_directory=self.project_root / ".ci-registry" / "chromadb"
        )
        self.storage = ChromaDBStorage(self.chromadb_config)

        # Initialize embedding engine
        self.embedding_config = EmbeddingConfig()
        self.embedding_engine = EmbeddingEngine(self.embedding_config)

        # Initialize symbol extractor for file queries
        self.symbol_config = SymbolExtractionConfig()
        self.symbol_extractor = LSPSymbolExtractor(
            self.symbol_config, str(self.project_root)
        )

        # Verify ChromaDB is available and indexed
        if not self.storage.is_available():
            print(
                "WARNING: ChromaDB not initialized. Run full scan first:",
                file=sys.stderr,
            )
            print(
                "cd shared && PYTHONPATH=.. python ci/core/chromadb_storage.py --project-root .. --full-scan",
                file=sys.stderr,
            )

    def search_by_query(
        self, query: str, max_results: int = 10, threshold: float = 0.7
    ) -> List[CodebaseSearchResult]:
        """
        Search codebase using natural language query.

        Args:
            query: Natural language description of what to find
            max_results: Maximum number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of CodebaseSearchResult objects
        """
        if not self.storage.is_available():
            return []

        # Convert query to embedding
        try:
            # Create a dummy symbol for the query to use the existing embedding engine
            query_symbol = Symbol(
                name=query,
                symbol_type=SymbolType.FUNCTION,  # Use function as a generic type
                file_path="query",
                line_number=1,
                line_content=query,
                scope="global",
            )

            query_embeddings = self.embedding_engine.generate_embeddings([query_symbol])
            query_embedding = query_embeddings[0]
        except Exception as e:
            print(f"Error generating embedding: {e}", file=sys.stderr)
            return []

        # Search ChromaDB for similar symbols
        matches = self.storage.find_similar(
            query_embedding=query_embedding, threshold=threshold, k=max_results
        )

        # Convert to search results
        results = []
        for match in matches:
            if hasattr(match, "match_symbol") and match.match_symbol:
                context = f"Semantic similarity to query: '{query}'"
                result = CodebaseSearchResult(
                    symbol=match.match_symbol,
                    similarity=match.similarity_score,
                    context=context,
                )
                results.append(result)

        return sorted(results, key=lambda r: r.similarity, reverse=True)

    def search_similar_to_symbol(
        self, file_path: str, line_number: int, max_results: int = 10
    ) -> List[CodebaseSearchResult]:
        """
        Find symbols similar to a specific function/symbol in a file.

        Args:
            file_path: Path to source file
            line_number: Line number of the symbol
            max_results: Maximum number of results

        Returns:
            List of similar CodebaseSearchResult objects
        """
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File not found: {file_path}", file=sys.stderr)
            return []

        # Extract symbols from the file
        try:
            symbols = self.symbol_extractor.extract_symbols([file_path])
        except Exception as e:
            print(f"Error extracting symbols: {e}", file=sys.stderr)
            return []

        # Find the symbol at the specified line
        target_symbol = None
        for symbol in symbols:
            if symbol.line_number == line_number or (
                symbol.line_number
                <= line_number
                <= getattr(symbol, "end_line_number", symbol.line_number)
            ):
                target_symbol = symbol
                break

        if not target_symbol:
            print(f"No symbol found at {file_path}:{line_number}", file=sys.stderr)
            return []

        # Get embedding for the target symbol
        try:
            symbol_embeddings = self.embedding_engine.generate_embeddings(
                [target_symbol]
            )
            symbol_embedding = symbol_embeddings[0]
        except Exception as e:
            print(f"Error generating embedding for symbol: {e}", file=sys.stderr)
            return []

        # Search for similar symbols
        matches = self.storage.find_similar(
            query_embedding=symbol_embedding,
            threshold=0.6,  # Lower threshold for similar symbols
            k=max_results + 1,  # +1 to exclude the original symbol
        )

        # Convert to search results, excluding the original symbol
        results = []
        for match in matches:
            if hasattr(match, "match_symbol") and match.match_symbol:
                # Skip the original symbol
                if (
                    str(match.match_symbol.file_path) == str(file_path)
                    and match.match_symbol.line_number == line_number
                ):
                    continue

                context = (
                    f"Similar to {target_symbol.name} at {file_path}:{line_number}"
                )
                result = CodebaseSearchResult(
                    symbol=match.match_symbol,
                    similarity=match.similarity_score,
                    context=context,
                )
                results.append(result)

        return sorted(results, key=lambda r: r.similarity, reverse=True)[:max_results]

    def find_patterns(
        self, pattern_query: str, max_results: int = 15
    ) -> List[CodebaseSearchResult]:
        """
        Find code patterns across the codebase.

        Args:
            pattern_query: Description of the pattern to find
            max_results: Maximum number of results

        Returns:
            List of CodebaseSearchResult objects representing the pattern
        """
        # Use broader search for patterns
        results = self.search_by_query(
            query=f"code pattern example: {pattern_query}",
            max_results=max_results,
            threshold=0.5,  # Lower threshold for pattern discovery
        )

        # Enhance context for pattern results
        for result in results:
            result.context = f"Pattern match for: '{pattern_query}'"

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the indexed codebase."""
        if not self.storage.is_available():
            return {"error": "ChromaDB not available"}

        try:
            stats = self.storage.get_statistics()
            return {
                "total_symbols": stats.get("total_vectors", 0),
                "collections": stats.get("collections", []),
                "search_performance": stats.get("avg_search_time", 0),
                "last_updated": stats.get("last_update", "unknown"),
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Main entry point for codebase search tool."""
    parser = argparse.ArgumentParser(
        description="Semantic codebase search using ChromaDB"
    )

    # Query modes
    parser.add_argument(
        "--query", "-q", help="Natural language query for semantic search"
    )
    parser.add_argument("--similar-to", help="Find similar symbols to FILE:LINE format")
    parser.add_argument(
        "--find-patterns", help="Find code patterns matching description"
    )

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
    parser.add_argument("--stats", action="store_true", help="Show codebase statistics")

    args = parser.parse_args()

    # Initialize search engine
    try:
        search_engine = CodebaseSearchEngine(args.project_root)
    except Exception as e:
        print(f"FATAL: Failed to initialize search engine: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle statistics request
    if args.stats:
        stats = search_engine.get_statistics()
        print(json.dumps(stats, indent=2))
        return

    # Perform search based on mode
    results = []

    if args.query:
        results = search_engine.search_by_query(
            query=args.query, max_results=args.max_results, threshold=args.threshold
        )
    elif args.similar_to:
        try:
            file_path, line_number = args.similar_to.rsplit(":", 1)
            line_number = int(line_number)
            results = search_engine.search_similar_to_symbol(
                file_path=file_path,
                line_number=line_number,
                max_results=args.max_results,
            )
        except ValueError:
            print("Error: --similar-to format should be FILE:LINE", file=sys.stderr)
            sys.exit(1)
    elif args.find_patterns:
        results = search_engine.find_patterns(
            pattern_query=args.find_patterns, max_results=args.max_results
        )
    else:
        print(
            "Error: Must specify --query, --similar-to, --find-patterns, or --stats",
            file=sys.stderr,
        )
        sys.exit(1)

    # Output results
    if args.format == "json":
        output = {
            "query_info": {
                "query": args.query or args.similar_to or args.find_patterns,
                "max_results": args.max_results,
                "threshold": args.threshold,
                "results_found": len(results),
            },
            "results": [result.to_dict() for result in results],
        }
        print(json.dumps(output, indent=2))
    else:
        # Text format
        print(f"Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.symbol.name} ({result.symbol.symbol_type.value})")
            print(f"   File: {result.symbol.file_path}:{result.symbol.line_number}")
            print(f"   Similarity: {result.similarity:.3f}")
            print(f"   Context: {result.context}")
            if hasattr(result.symbol, "signature") and result.symbol.signature:
                print(f"   Signature: {result.symbol.signature}")
            print()


if __name__ == "__main__":
    main()
