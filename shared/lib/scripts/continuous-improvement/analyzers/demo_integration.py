# flake8: noqa: E402
#!/usr/bin/env python3
"""
Duplicate Detection Framework Demo
Shows integration between SymbolExtractor output and ComparisonFramework.
Demonstrates TASK-010 implementation for future TASK-CI-018 integration.
"""

import sys
import json
from pathlib import Path

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))

from symbol_extractor import Symbol, SymbolType
from comparison_framework import (
    ComparisonFramework,
    ComparisonConfig,
)


def create_sample_symbols():
    """Create sample symbols that demonstrate duplicate detection scenarios."""
    return [
        # Exact duplicate scenario
        Symbol(
            name="calculateSum",
            symbol_type=SymbolType.FUNCTION,
            file_path="/project/utils/math.js",
            line_number=15,
            line_content="function calculateSum(numbers) { return numbers.reduce((a, b) => a + b, 0); }",
            scope="module",
            parameters=["numbers"],
        ),
        Symbol(
            name="calculateSum",
            symbol_type=SymbolType.FUNCTION,
            file_path="/project/helpers/calculator.js",
            line_number=8,
            line_content="function calculateSum(numbers) { return numbers.reduce((a, b) => a + b, 0); }",
            scope="module",
            parameters=["numbers"],
        ),
        # Similar function scenario
        Symbol(
            name="addNumbers",
            symbol_type=SymbolType.FUNCTION,
            file_path="/project/lib/arithmetic.py",
            line_number=22,
            line_content="def addNumbers(values): return sum(values)",
            scope="module",
            parameters=["values"],
        ),
        Symbol(
            name="sum_values",
            symbol_type=SymbolType.FUNCTION,
            file_path="/project/core/operations.py",
            line_number=45,
            line_content="def sum_values(nums): return sum(nums)",
            scope="module",
            parameters=["nums"],
        ),
        # Class duplicate scenario
        Symbol(
            name="DataProcessor",
            symbol_type=SymbolType.CLASS,
            file_path="/project/processing/handler.py",
            line_number=10,
            line_content="class DataProcessor:",
            scope="module",
        ),
        Symbol(
            name="DataProcessor",
            symbol_type=SymbolType.CLASS,
            file_path="/project/utils/processor.py",
            line_number=5,
            line_content="class DataProcessor:",
            scope="module",
        ),
        # Different enough symbols (should not be flagged)
        Symbol(
            name="getUserData",
            symbol_type=SymbolType.FUNCTION,
            file_path="/project/api/users.js",
            line_number=30,
            line_content="function getUserData(userId) { return database.findById(userId); }",
            scope="module",
            parameters=["userId"],
        ),
        Symbol(
            name="validatePassword",
            symbol_type=SymbolType.FUNCTION,
            file_path="/project/auth/validator.js",
            line_number=12,
            line_content="function validatePassword(password) { return password.length >= 8; }",
            scope="module",
            parameters=["password"],
        ),
    ]


def demo_basic_comparison():
    """Demonstrate basic comparison functionality."""
    print("=== DUPLICATE DETECTION FRAMEWORK DEMO ===\n")

    # Create configuration with different thresholds
    config = ComparisonConfig(
        exact_match_threshold=1.0,
        high_similarity_threshold=0.8,
        medium_similarity_threshold=0.6,
        low_similarity_threshold=0.3,
        include_symbol_types={SymbolType.FUNCTION, SymbolType.CLASS},
        exclude_symbol_types={SymbolType.IMPORT, SymbolType.VARIABLE},
    )

    # Initialize framework
    framework = ComparisonFramework(config)

    # Get sample symbols
    symbols = create_sample_symbols()
    print(f"Created {len(symbols)} sample symbols for analysis")

    # Run comparison
    result = framework.compare_symbols(symbols, "basic_similarity")

    # Display results
    print("\n=== ANALYSIS RESULTS ===")
    print(f"Total symbols analyzed: {result.summary['symbols_analyzed']}")
    print(f"Duplicates found: {result.summary['total_duplicates_found']}")
    print(f"Algorithm used: {result.summary['algorithm_used']}")
    print(f"Execution time: {result.summary['execution_time_seconds']}s")

    print("\n=== SEVERITY BREAKDOWN ===")
    for severity, count in result.summary["severity_breakdown"].items():
        if count > 0:
            print(f"  {severity.upper()}: {count}")

    print("\n=== DUPLICATE FINDINGS ===")
    for i, finding in enumerate(result.findings, 1):
        evidence = finding["evidence"]
        print(f"\n{i}. {finding['title']}")
        print(f"   Severity: {finding['severity'].upper()}")
        print(f"   Similarity Score: {evidence['similarity_score']:.3f}")
        print(f"   Comparison Type: {evidence['comparison_type']}")
        print(f"   Duplicate Reason: {evidence['duplicate_reason']}")
        print(
            f"   Files: {evidence['symbol1']['file']}:{evidence['symbol1']['line']} & {evidence['symbol2']['file']}:{evidence['symbol2']['line']}"
        )

        # Show similarity breakdown
        details = evidence["details"]
        print("   Similarity Breakdown:")
        print(f"     Name: {details['name_similarity']:.3f}")
        print(f"     Content: {details['content_similarity']:.3f}")
        print(f"     Structure: {details['structure_similarity']:.3f}")

    return result


def demo_algorithm_configuration():
    """Demonstrate algorithm configuration capabilities."""
    print("\n\n=== ALGORITHM CONFIGURATION DEMO ===\n")

    config = ComparisonConfig()
    framework = ComparisonFramework(config)

    # Show available algorithms
    print(f"Available algorithms: {', '.join(framework.get_available_algorithms())}")

    # Configure algorithm with different weights
    print("\nConfiguring basic_similarity algorithm with custom weights...")
    framework.configure_algorithm(
        "basic_similarity", name_weight=0.5, content_weight=0.3, structure_weight=0.2
    )

    symbols = create_sample_symbols()[:4]  # Use subset for demo
    result = framework.compare_symbols(symbols, "basic_similarity")

    print("Results with custom weights:")
    print(f"  Duplicates found: {result.summary['total_duplicates_found']}")

    if result.findings:
        finding = result.findings[0]
        details = finding["evidence"]["details"]
        print("  First finding similarity breakdown:")
        print(f"    Name: {details['name_similarity']:.3f}")
        print(f"    Content: {details['content_similarity']:.3f}")
        print(f"    Structure: {details['structure_similarity']:.3f}")


def demo_json_output():
    """Demonstrate JSON output format for CI integration."""
    print("\n\n=== JSON OUTPUT FOR CI INTEGRATION ===\n")

    config = ComparisonConfig(low_similarity_threshold=0.7)  # Higher threshold for demo
    framework = ComparisonFramework(config)
    symbols = create_sample_symbols()
    result = framework.compare_symbols(symbols, "basic_similarity")

    # Create output compatible with existing AnalysisResult pattern
    output = {
        "analysis_type": result.analysis_type,
        "findings": result.findings,
        "summary": result.summary,
        "metadata": result.metadata,
    }

    print("JSON Output (formatted for readability):")
    print(json.dumps(output, indent=2, default=str))


def demo_integration_points():
    """Show key integration points for TASK-CI-018."""
    print("\n\n=== INTEGRATION POINTS FOR FUTURE TASK-CI-018 ===\n")

    print("1. SYMBOL EXTRACTION INTEGRATION:")
    print("   - SymbolExtractor produces List[Symbol] from project files")
    print("   - ComparisonFramework.compare_symbols(symbols) analyzes duplicates")
    print("   - Output format matches existing AnalysisResult patterns")

    print("\n2. PLUGGABLE ALGORITHM ARCHITECTURE:")
    print("   - ComparisonAlgorithm abstract base class for custom algorithms")
    print("   - ComparisonFramework.register_algorithm() for new algorithms")
    print("   - Algorithm-specific configuration via configure() method")

    print("\n3. CONFIGURATION SYSTEM:")
    print("   - ComparisonConfig dataclass with sensible defaults")
    print("   - Threshold-based similarity scoring (exact/high/medium/low)")
    print("   - Symbol type filtering and file exclusion patterns")

    print("\n4. SIMILARITY SCORING FRAMEWORK:")
    print("   - SimilarityScore dataclass with detailed comparison metadata")
    print("   - ComparisonType enum for categorizing similarity types")
    print("   - DuplicateReason enum for explaining why symbols are similar")

    print("\n5. CI SYSTEM COMPATIBILITY:")
    print("   - ComparisonResult follows existing AnalysisResult pattern")
    print("   - JSON output format for automated processing")
    print("   - Severity-based findings for quality gate integration")


def main():
    """Main demo entry point."""
    try:
        # Run all demos
        demo_basic_comparison()
        demo_algorithm_configuration()
        demo_json_output()
        demo_integration_points()

        print("\n\n=== DEMO COMPLETE ===")
        print("Successfully demonstrated TASK-010 Duplicate Detection Framework")
        print("Ready for TASK-CI-018 CI system integration")

    except Exception as e:
        print(f"Demo failed with error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
