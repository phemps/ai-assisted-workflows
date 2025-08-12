# flake8: noqa: E402
#!/usr/bin/env python3
"""
Duplicate Detection Framework Demo
Shows integration between SymbolExtractor output and consolidated DuplicateFinder.
Updated after detection system consolidation.
"""

import sys
from pathlib import Path

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "utils"))

from symbol_extractor import Symbol, SymbolType

# Import consolidated duplicate finder
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from semantic_duplicate_detector import (
    DuplicateFinder,
    DuplicateFinderConfig,
    AnalysisMode,
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
    """Demonstrate basic duplicate detection functionality."""
    print("=== CONSOLIDATED DUPLICATE DETECTION DEMO ===\n")

    # Create configuration with different thresholds
    config = DuplicateFinderConfig(
        analysis_mode=AnalysisMode.TARGETED,
        exact_duplicate_threshold=1.0,
        high_similarity_threshold=0.8,
        medium_similarity_threshold=0.6,
        low_similarity_threshold=0.3,
        include_symbol_types=["function", "class", "method"],
        max_symbols=100,  # Limit for demo
        enable_caching=False,  # Disable for demo
    )

    # Get sample symbols
    symbols = create_sample_symbols()
    print(f"Created {len(symbols)} sample symbols for analysis")

    try:
        # Initialize finder (may fail if MCP components not available)
        finder = DuplicateFinder(config)

        # Run duplicate detection on symbols directly
        duplicates = finder.find_duplicates(symbols, threshold=0.6)

        # Create a summary result
        result = finder._create_comparison_result(duplicates, symbols)

        # Display results
        print("\n=== ANALYSIS RESULTS ===")
        print(f"Total symbols analyzed: {len(symbols)}")
        print(f"Duplicates found: {len(duplicates)}")
        print("Detection method: embedding_similarity")
        print(f"Execution time: {result.summary.get('execution_time_seconds', 0)}s")

        print("\n=== SEVERITY BREAKDOWN ===")
        for severity, count in result.summary.get("severity_breakdown", {}).items():
            if count > 0:
                print(f"  {severity.upper()}: {count}")

        print("\n=== DUPLICATE FINDINGS ===")
        for i, finding in enumerate(result.findings, 1):
            evidence = finding["evidence"]
            print(f"\n{i}. {finding['title']}")
            print(f"   Severity: {finding['severity'].upper()}")
            print(f"   Similarity Score: {evidence['similarity_score']:.3f}")
            print(
                f"   Comparison Type: {evidence.get('comparison_type', 'semantic_similarity')}"
            )
            print(
                f"   Duplicate Reason: {evidence.get('duplicate_reason', 'similar_functionality')}"
            )

            orig_symbol = evidence["original_symbol"]
            dup_symbol = evidence["duplicate_symbol"]
            print(
                f"   Files: {orig_symbol['file']}:{orig_symbol['line']} & {dup_symbol['file']}:{dup_symbol['line']}"
            )

        return result

    except Exception as e:
        print(f"Demo requires MCP components to be available: {e}")
        print("This demonstrates the fail-fast behavior of the consolidated system.")
        return None


def demo_configuration():
    """Demonstrate configuration capabilities."""
    print("\n\n=== CONFIGURATION DEMO ===\n")

    # Show different configuration options
    print("Available configuration options:")
    print("  - Analysis modes: full, incremental, targeted")
    print("  - Similarity thresholds: exact, high, medium, low")
    print("  - Performance settings: batch_size, max_symbols, enable_caching")
    print("  - Symbol filtering: include/exclude types, file patterns")

    # Create configuration with different settings
    config = DuplicateFinderConfig(
        analysis_mode=AnalysisMode.TARGETED,
        high_similarity_threshold=0.9,  # Higher threshold
        medium_similarity_threshold=0.7,
        batch_size=50,
        max_symbols=500,
        include_symbol_types=["function", "class"],
        min_symbol_length=20,
    )

    print("\nConfiguration example:")
    print(f"  Analysis mode: {config.analysis_mode.value}")
    print(f"  High similarity threshold: {config.high_similarity_threshold}")
    print(f"  Medium similarity threshold: {config.medium_similarity_threshold}")
    print(f"  Batch size: {config.batch_size}")


def demo_integration_points():
    """Show key integration points for CI system."""
    print("\n\n=== INTEGRATION POINTS FOR CI SYSTEM ===\n")

    print("1. CONSOLIDATED DETECTION SYSTEM:")
    print("   - Single DuplicateFinder class handles all duplicate detection")
    print("   - Fail-fast behavior with clear error messages")
    print("   - All 4 core components required: Serena, CodeBERT, Faiss, SQLite")

    print("\n2. SYMBOL PROCESSING PIPELINE:")
    print(
        "   - Symbol extraction → Embedding generation → Similarity detection → Registry updates"
    )
    print("   - Batch processing with configurable memory limits")
    print("   - Incremental analysis support for changed files only")

    print("\n3. CONFIGURATION SYSTEM:")
    print("   - DuplicateFinderConfig with sensible defaults")
    print("   - Threshold-based similarity scoring with validation")
    print("   - Performance tuning via batch sizes and memory limits")

    print("\n4. QUALITY INTEGRATION:")
    print("   - ComparisonResult follows existing AnalysisResult pattern")
    print("   - Severity-based findings: critical, high, medium, low")
    print("   - JSON output format for automated processing")

    print("\n5. ORCHESTRATION INTEGRATION:")
    print("   - Used by orchestration_bridge for GitHub Actions integration")
    print("   - CTO decision matrix for automatic vs manual duplicate handling")
    print("   - Integrates with todo-orchestrate for fix workflows")


def main():
    """Main demo entry point."""
    try:
        # Run all demos
        demo_basic_comparison()
        demo_configuration()
        demo_integration_points()

        print("\n\n=== DEMO COMPLETE ===")
        print("Successfully demonstrated consolidated duplicate detection system")
        print("System ready for CI integration with fail-fast behavior")

    except Exception as e:
        print(f"Demo failed with error: {e}", file=sys.stderr)
        print("This is expected if MCP components are not available")
        print("The consolidated system requires all 4 core components to function")


if __name__ == "__main__":
    main()
