# Duplicate Detection Comparison Framework (TASK-010)

This directory contains the implementation of TASK-010: Duplicate Detection Comparison Framework, which prepares the foundation for future CI system integration (TASK-CI-018).

## Overview

The framework provides a pluggable comparison system for detecting duplicate code symbols with configurable similarity scoring and algorithm support. It builds upon the existing Symbol dataclass and AnalysisResult patterns established in the continuous improvement system.

## Key Components

### Core Classes

- **`ComparisonAlgorithm`** (Abstract Base Class): Interface for pluggable comparison algorithms
- **`ComparisonConfig`** (Dataclass): Configuration system with sensible defaults
- **`SimilarityScore`** (Dataclass): Framework for scoring similarity between symbols
- **`ComparisonResult`** (Dataclass): Extended AnalysisResult for comparison findings
- **`ComparisonFramework`** (Main Class): Orchestrates symbol comparison and algorithm management

### Enums

- **`ComparisonType`**: Categories of comparison (exact_match, semantic_similarity, structural_similarity, name_similarity)
- **`DuplicateReason`**: Reasons for similarity (identical_implementation, similar_functionality, copy_paste_error, refactor_candidate)

### Default Algorithm

- **`BasicSimilarityAlgorithm`**: Implementation using name, content, and structural similarity with configurable weights

## Architecture Features

### 1. Pluggable Algorithm Interface

```python
class ComparisonAlgorithm(ABC):
    @abstractmethod
    def compare_symbols(self, symbols: List[Symbol]) -> List[SimilarityScore]:
        """Compare symbols and return similarity scores."""
        pass

    @abstractmethod
    def configure(self, **kwargs) -> None:
        """Configure algorithm-specific parameters."""
        pass
```

### 2. Configuration System

```python
@dataclass
class ComparisonConfig:
    # Thresholds
    exact_match_threshold: float = 1.0
    high_similarity_threshold: float = 0.8
    medium_similarity_threshold: float = 0.6
    low_similarity_threshold: float = 0.3

    # Symbol filtering
    include_symbol_types: Set[SymbolType] = None
    exclude_symbol_types: Set[SymbolType] = None

    # Algorithm weights
    name_similarity_weight: float = 0.3
    structure_similarity_weight: float = 0.4
    content_similarity_weight: float = 0.3
```

### 3. Similarity Scoring Framework

```python
@dataclass
class SimilarityScore:
    symbol1: Symbol
    symbol2: Symbol
    score: float  # 0.0 to 1.0
    comparison_type: ComparisonType
    reason: Optional[DuplicateReason] = None
    confidence: float = 1.0
    details: Dict[str, Any] = None
```

### 4. CI-Compatible Output

The framework produces `ComparisonResult` objects that follow the existing AnalysisResult pattern:

```python
{
    "analysis_type": "duplicate_detection",
    "findings": [...],  # List of duplicate findings with evidence
    "summary": {...},   # Analysis summary with counts and metrics
    "metadata": {...}   # Framework metadata and configuration
}
```

## Integration Points for TASK-CI-018

### Symbol Extraction Integration

The framework seamlessly integrates with the existing `SymbolExtractor`:

```python
# Extract symbols from project
extractor = SymbolExtractor(project_root)
symbol_result = extractor.extract_symbols()

# Convert to Symbol objects and compare
framework = ComparisonFramework()
comparison_result = framework.compare_symbols(symbols)
```

### CI System Compatibility

1. **Output Format**: Compatible with existing AnalysisResult patterns
2. **Severity Levels**: Maps similarity scores to standard severity levels (critical/high/medium/low)
3. **JSON Output**: Structured format for automated processing
4. **Quality Gates**: Severity-based findings for integration with quality gate systems

## Files

- **`comparison_framework.py`**: Core framework implementation
- **`demo_integration.py`**: Comprehensive demonstration script
- **`duplicate_detector.py`**: Integration example (reference implementation)
- **`__init__.py`**: Package exports

## Usage Examples

### Basic Usage

```python
from comparison_framework import ComparisonFramework, ComparisonConfig
from symbol_extractor import SymbolExtractor

# Configure framework
config = ComparisonConfig(
    high_similarity_threshold=0.8,
    low_similarity_threshold=0.3
)

# Initialize and run
framework = ComparisonFramework(config)
extractor = SymbolExtractor(project_root)

# Extract and compare
symbols = extract_symbols_from_project()  # Implementation specific
result = framework.compare_symbols(symbols, "basic_similarity")
```

### Algorithm Configuration

```python
# Configure algorithm weights
framework.configure_algorithm("basic_similarity",
                             name_weight=0.5,
                             content_weight=0.3,
                             structure_weight=0.2)
```

### Custom Algorithm Registration

```python
class MyCustomAlgorithm(ComparisonAlgorithm):
    def compare_symbols(self, symbols):
        # Custom implementation
        pass

    def configure(self, **kwargs):
        # Custom configuration
        pass

# Register and use
custom_algo = MyCustomAlgorithm(config)
framework.register_algorithm(custom_algo)
result = framework.compare_symbols(symbols, "my_custom_algorithm")
```

## Testing

Run the comprehensive demo to see the framework in action:

```bash
python demo_integration.py
```

This demonstrates:
- Basic comparison functionality
- Algorithm configuration
- JSON output format
- Integration points for CI systems

## Performance Considerations

- **Max Comparisons**: Configurable limit (`max_comparisons_per_run`) prevents performance issues on large codebases
- **Symbol Filtering**: Pre-filtering reduces comparison overhead
- **Efficient Algorithms**: Basic algorithm uses simple similarity metrics for performance

## Future Extensions

The pluggable architecture supports:

1. **Advanced Algorithms**: AST-based structural comparison, semantic analysis
2. **Machine Learning**: Trained models for similarity detection
3. **Language-Specific**: Custom algorithms for different programming languages
4. **Integration**: Serena MCP integration when available

## Validation

The framework has been tested with:
- ✅ Symbol extraction integration
- ✅ Configurable similarity thresholds
- ✅ Pluggable algorithm architecture
- ✅ CI-compatible output format
- ✅ Performance safeguards
- ✅ Comprehensive error handling

Ready for TASK-CI-018 CI system integration.
