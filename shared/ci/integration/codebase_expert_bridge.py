#!/usr/bin/env python3
"""
Codebase Expert Integration Bridge
==================================

PURPOSE: Simplified interface for agents to interact with ChromaDB semantic search.
Provides high-level methods for common codebase exploration patterns.

FEATURES:
- Simplified API for agent integration
- Context-aware search refinement
- Result ranking and filtering
- Caching for frequent queries
- Natural language processing for query enhancement

USAGE:
- Called by codebase-expert agent
- Provides structured results for agent decision making
- Handles embedding generation and ChromaDB queries
- Enriches results with surrounding code context
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache

# Setup import paths and import search components
try:
    from utils import path_resolver  # noqa: F401
    from ci.tools.codebase_search import CodebaseSearchEngine, CodebaseSearchResult
    from ci.integration.symbol_extractor import Symbol, SymbolType  # noqa: F401
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


@dataclass
class ExpertRecommendation:
    """Structured recommendation from codebase analysis."""

    recommendation_type: str  # "reuse", "extend", "pattern", "new"
    confidence: float  # 0.0 to 1.0
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    rationale: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.recommendation_type,
            "confidence": self.confidence,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "rationale": self.rationale,
        }


@dataclass
class ExpertAnalysis:
    """Complete analysis result from codebase expert."""

    query: str
    similar_functions: List[CodebaseSearchResult]
    reusable_components: List[CodebaseSearchResult]
    patterns: List[CodebaseSearchResult]
    recommendations: List[ExpertRecommendation]
    execution_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "similar_functions": [r.to_dict() for r in self.similar_functions],
            "reusable_components": [r.to_dict() for r in self.reusable_components],
            "patterns": [r.to_dict() for r in self.patterns],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "execution_time": self.execution_time,
            "summary": self._generate_summary(),
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total_similar_functions": len(self.similar_functions),
            "total_reusable_components": len(self.reusable_components),
            "total_patterns": len(self.patterns),
            "top_recommendation": self.recommendations[0].recommendation_type
            if self.recommendations
            else "none",
            "high_confidence_recommendations": len(
                [r for r in self.recommendations if r.confidence > 0.8]
            ),
        }


class CodebaseExpertBridge:
    """
    Integration bridge providing simplified codebase analysis for agents.

    Handles complex queries, result analysis, and recommendation generation.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.search_engine = CodebaseSearchEngine(str(project_root))
        self.query_cache = {}

    def analyze_functionality(self, functionality_description: str) -> ExpertAnalysis:
        """
        Comprehensive analysis of requested functionality.

        Args:
            functionality_description: Natural language description of what to implement

        Returns:
            ExpertAnalysis with similar functions, reusable components, patterns, and recommendations
        """
        start_time = time.time()

        # Search for similar functions
        similar_functions = self._find_similar_functions(functionality_description)

        # Find reusable components
        reusable_components = self._find_reusable_components(functionality_description)

        # Identify patterns
        patterns = self._find_patterns(functionality_description)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            functionality_description, similar_functions, reusable_components, patterns
        )

        execution_time = time.time() - start_time

        return ExpertAnalysis(
            query=functionality_description,
            similar_functions=similar_functions,
            reusable_components=reusable_components,
            patterns=patterns,
            recommendations=recommendations,
            execution_time=execution_time,
        )

    def find_similar_implementation(
        self, file_path: str, line_number: int
    ) -> List[CodebaseSearchResult]:
        """
        Find similar implementations to a specific function.

        Args:
            file_path: Path to file containing the function
            line_number: Line number of the function

        Returns:
            List of similar implementations
        """
        return self.search_engine.search_similar_to_symbol(file_path, line_number)

    def suggest_extensions(
        self, functionality_description: str, existing_file: str
    ) -> List[ExpertRecommendation]:
        """
        Suggest how to extend existing file with new functionality.

        Args:
            functionality_description: What to implement
            existing_file: File to potentially extend

        Returns:
            List of extension recommendations
        """
        # Search for similar functionality
        similar_functions = self._find_similar_functions(functionality_description)

        # Filter for functions in the target file or similar files
        relevant_functions = [
            f
            for f in similar_functions
            if existing_file in str(f.symbol.file_path)
            or Path(f.symbol.file_path).suffix == Path(existing_file).suffix
        ]

        recommendations = []
        for func in relevant_functions[:3]:  # Top 3 matches
            if func.similarity > 0.8:
                rec = ExpertRecommendation(
                    recommendation_type="extend",
                    confidence=func.similarity,
                    description=f"Extend {func.symbol.name} in {func.symbol.file_path}",
                    file_path=str(func.symbol.file_path),
                    line_number=func.symbol.line_number,
                    rationale=f"High similarity ({func.similarity:.2f}) to requested functionality",
                )
                recommendations.append(rec)

        return recommendations

    @lru_cache(maxsize=128)
    def _find_similar_functions(
        self, query: str, max_results: int = 10
    ) -> List[CodebaseSearchResult]:
        """Find functions with similar functionality."""
        return self.search_engine.search_by_query(
            query=query, max_results=max_results, threshold=0.7
        )

    @lru_cache(maxsize=128)
    def _find_reusable_components(
        self, query: str, max_results: int = 8
    ) -> List[CodebaseSearchResult]:
        """Find reusable utility functions and components."""
        utility_queries = [
            f"utility helper {query}",
            f"common {query}",
            f"shared {query}",
            f"base {query}",
        ]

        all_results = []
        for util_query in utility_queries:
            results = self.search_engine.search_by_query(
                query=util_query, max_results=max_results // 2, threshold=0.6
            )
            all_results.extend(results)

        # Remove duplicates and sort by similarity
        unique_results = {}
        for result in all_results:
            key = f"{result.symbol.file_path}:{result.symbol.line_number}"
            if (
                key not in unique_results
                or result.similarity > unique_results[key].similarity
            ):
                unique_results[key] = result

        return sorted(
            unique_results.values(), key=lambda r: r.similarity, reverse=True
        )[:max_results]

    @lru_cache(maxsize=128)
    def _find_patterns(
        self, query: str, max_results: int = 5
    ) -> List[CodebaseSearchResult]:
        """Find architectural patterns related to the functionality."""
        # Extract key terms for pattern matching
        pattern_terms = self._extract_pattern_terms(query)

        all_patterns = []
        for term in pattern_terms:
            patterns = self.search_engine.find_patterns(term, max_results=3)
            all_patterns.extend(patterns)

        # Remove duplicates
        unique_patterns = {}
        for pattern in all_patterns:
            key = f"{pattern.symbol.file_path}:{pattern.symbol.line_number}"
            if (
                key not in unique_patterns
                or pattern.similarity > unique_patterns[key].similarity
            ):
                unique_patterns[key] = pattern

        return sorted(
            unique_patterns.values(), key=lambda r: r.similarity, reverse=True
        )[:max_results]

    def _extract_pattern_terms(self, query: str) -> List[str]:
        """Extract key terms that might indicate architectural patterns."""
        # Common pattern indicators
        pattern_indicators = {
            "api": ["endpoint", "route", "handler"],
            "auth": ["authentication", "authorization", "middleware"],
            "data": ["validation", "processing", "transformation"],
            "error": ["handling", "exception", "error"],
            "async": ["promise", "callback", "await"],
            "db": ["database", "query", "transaction"],
            "cache": ["caching", "storage", "memory"],
            "test": ["testing", "mock", "fixture"],
        }

        query_lower = query.lower()
        extracted = []

        for category, terms in pattern_indicators.items():
            if any(term in query_lower for term in terms + [category]):
                extracted.append(category)

        return extracted if extracted else ["general"]

    def _generate_recommendations(
        self,
        query: str,
        similar_functions: List[CodebaseSearchResult],
        reusable_components: List[CodebaseSearchResult],
        patterns: List[CodebaseSearchResult],
    ) -> List[ExpertRecommendation]:
        """Generate actionable recommendations based on search results."""

        recommendations = []

        # High similarity function found - recommend reuse/extension
        if similar_functions and similar_functions[0].similarity > 0.85:
            best_match = similar_functions[0]
            rec = ExpertRecommendation(
                recommendation_type="reuse",
                confidence=best_match.similarity,
                description=f"Reuse or extend existing function: {best_match.symbol.name}",
                file_path=str(best_match.symbol.file_path),
                line_number=best_match.symbol.line_number,
                rationale=f"Very high similarity ({best_match.similarity:.2f}) indicates this function likely already solves the problem",
            )
            recommendations.append(rec)

        # Moderate similarity - recommend extending
        elif similar_functions and similar_functions[0].similarity > 0.7:
            best_match = similar_functions[0]
            rec = ExpertRecommendation(
                recommendation_type="extend",
                confidence=best_match.similarity
                * 0.9,  # Slightly lower confidence for extension
                description=f"Consider extending: {best_match.symbol.name}",
                file_path=str(best_match.symbol.file_path),
                line_number=best_match.symbol.line_number,
                rationale=f"Good similarity ({best_match.similarity:.2f}) suggests this could be extended rather than rewritten",
            )
            recommendations.append(rec)

        # Strong reusable components found
        high_value_components = [c for c in reusable_components if c.similarity > 0.75]
        if high_value_components:
            rec = ExpertRecommendation(
                recommendation_type="reuse",
                confidence=sum(c.similarity for c in high_value_components)
                / len(high_value_components),
                description=f"Leverage {len(high_value_components)} existing utility functions",
                rationale="Multiple high-quality reusable components available",
            )
            recommendations.append(rec)

        # Strong patterns found - recommend following
        if patterns and patterns[0].similarity > 0.7:
            best_pattern = patterns[0]
            rec = ExpertRecommendation(
                recommendation_type="pattern",
                confidence=best_pattern.similarity,
                description=f"Follow established pattern from: {best_pattern.symbol.name}",
                file_path=str(best_pattern.symbol.file_path),
                line_number=best_pattern.symbol.line_number,
                rationale="Strong pattern match indicates established architectural approach",
            )
            recommendations.append(rec)

        # No strong matches - recommend new implementation
        if not recommendations or (
            recommendations and max(r.confidence for r in recommendations) < 0.6
        ):
            rec = ExpertRecommendation(
                recommendation_type="new",
                confidence=0.8,  # High confidence in recommending new implementation when no good matches
                description="Implement new function following established patterns",
                rationale="No sufficiently similar existing implementations found",
            )
            recommendations.append(rec)

        return sorted(recommendations, key=lambda r: r.confidence, reverse=True)

    def get_codebase_statistics(self) -> Dict[str, Any]:
        """Get statistics about the indexed codebase."""
        return self.search_engine.get_statistics()


def main():
    """Command-line interface for testing the bridge."""
    import argparse

    parser = argparse.ArgumentParser(description="Codebase Expert Bridge CLI")
    parser.add_argument("--analyze", help="Analyze functionality description")
    parser.add_argument("--similar-to", help="Find similar to FILE:LINE")
    parser.add_argument(
        "--extend", help="Suggest extensions for FILE with FUNCTIONALITY", nargs=2
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--format", choices=["json", "summary"], default="json")

    args = parser.parse_args()

    bridge = CodebaseExpertBridge(args.project_root)

    if args.analyze:
        analysis = bridge.analyze_functionality(args.analyze)
        if args.format == "json":
            print(json.dumps(analysis.to_dict(), indent=2))
        else:
            print(f"Analysis for: {analysis.query}")
            print(f"Found {len(analysis.similar_functions)} similar functions")
            print(f"Found {len(analysis.reusable_components)} reusable components")
            print(f"Found {len(analysis.patterns)} patterns")
            print(f"Generated {len(analysis.recommendations)} recommendations")
            if analysis.recommendations:
                print(f"Top recommendation: {analysis.recommendations[0].description}")

    elif args.similar_to:
        try:
            file_path, line_number = args.similar_to.rsplit(":", 1)
            results = bridge.find_similar_implementation(file_path, int(line_number))
            output = {"results": [r.to_dict() for r in results]}
            print(json.dumps(output, indent=2))
        except ValueError:
            print("Error: --similar-to format should be FILE:LINE")
            sys.exit(1)

    elif args.extend:
        functionality, existing_file = args.extend
        recommendations = bridge.suggest_extensions(functionality, existing_file)
        output = {"recommendations": [r.to_dict() for r in recommendations]}
        print(json.dumps(output, indent=2))

    else:
        stats = bridge.get_codebase_statistics()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
