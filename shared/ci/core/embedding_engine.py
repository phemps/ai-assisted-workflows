#!/usr/bin/env python3
"""
CodeBERT Embedding Engine for Continuous Improvement Framework

Provides local CodeBERT embeddings using transformers library.
Part of AI-Assisted Workflows - integrates with 8-agent orchestration system.
ChromaDB handles all caching and persistence.

Requires transformers and torch libraries - exits with error if unavailable.
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np

# Use smart imports for module access
try:
    from smart_imports import (
        import_output_formatter,
        import_tech_stack_detector,
        import_symbol_extractor,
    )
except ImportError as e:
    print(f"Error importing smart imports: {e}", file=sys.stderr)
    sys.exit(1)

# Import utilities and existing components
try:
    output_formatter_module = import_output_formatter()
    ResultFormatter = output_formatter_module.ResultFormatter

    tech_stack_module = import_tech_stack_detector()
    TechStackDetector = tech_stack_module.TechStackDetector

    symbol_extractor_module = import_symbol_extractor()
    Symbol = symbol_extractor_module.Symbol
except ImportError as e:
    print(f"Error importing utilities: {e}", file=sys.stderr)
    sys.exit(1)

# Required transformers imports - fail fast if unavailable
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
except ImportError as e:
    print(f"ERROR: Required dependencies not available: {e}", file=sys.stderr)
    print(
        "Please install required dependencies: pip install torch " "transformers",
        file=sys.stderr,
    )
    sys.exit(1)


class EmbeddingMethod(Enum):
    """Available embedding methods."""

    CODEBERT = "codebert"


@dataclass
class EmbeddingConfig:
    """Configuration for CodeBERT embedding engine."""

    # Model settings
    model_name: str = "microsoft/codebert-base"
    batch_size: int = 32
    max_length: int = 512

    # Performance settings
    use_gpu: bool = False
    normalize_embeddings: bool = True

    # Memory management
    max_memory_gb: float = 2.0
    clear_model_after_batch: bool = True

    # Symbol filtering (compatible with existing config)
    max_symbols_per_batch: int = 100
    include_symbol_types: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize default filters."""
        if self.include_symbol_types is None:
            self.include_symbol_types = ["function", "class", "method", "interface"]

        if self.exclude_patterns is None:
            self.exclude_patterns = ["test_*", "*_test.py", "*/test/*", "*.spec.*"]


class EmbeddingEngine:
    """
    CodeBERT embedding engine for code embeddings.
    Provides local embeddings with comprehensive caching and batch processing.
    Requires transformers library - fails fast if unavailable.
    """

    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        project_root: Optional[Path] = None,
    ):
        self.config = config or EmbeddingConfig()
        self.project_root = project_root or Path.cwd()

        # Initialize components
        self.tech_detector = TechStackDetector()
        self.result_formatter = ResultFormatter()

        # Model state
        self._model = None
        self._tokenizer = None
        self._current_method = EmbeddingMethod.CODEBERT

        # Performance tracking
        self._embedding_times = []
        self._memory_usage = []

        # Initialize CodeBERT model
        self._initialize_codebert_model()

    def _initialize_codebert_model(self) -> None:
        """Initialize CodeBERT model - fail fast if unavailable."""
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            self._model = AutoModel.from_pretrained(self.config.model_name)

            # Move to GPU if available and requested
            if self.config.use_gpu and torch.cuda.is_available():
                self._model = self._model.cuda()
                print("Using GPU acceleration for CodeBERT", file=sys.stderr)

            print("Initialized CodeBERT embeddings", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to initialize CodeBERT model: {e}", file=sys.stderr)
            print(
                "Please ensure the transformers library is installed "
                "and the model is available",
                file=sys.stderr,
            )
            sys.exit(1)

    def is_available(self) -> bool:
        """Check if CodeBERT embedding is available."""
        return self._model is not None and self._tokenizer is not None

    def generate_embeddings(self, symbols: List[Symbol]) -> np.ndarray:
        """
        Generate embeddings for a list of symbols.

        Args:
            symbols: List of symbols to embed

        Returns:
            numpy array of embeddings [n_symbols, embedding_dim]
        """
        if not symbols:
            return np.array([])

        start_time = time.time()

        # Generate embeddings for all symbols
        all_embeddings = self._generate_batch_embeddings(symbols)

        # Track performance
        execution_time = time.time() - start_time
        self._embedding_times.append(execution_time)

        return all_embeddings

    def _generate_batch_embeddings(self, symbols: List[Symbol]) -> np.ndarray:
        """Generate embeddings for symbols using CodeBERT."""
        return self._generate_codebert_embeddings(symbols)

    def _generate_codebert_embeddings(self, symbols: List[Symbol]) -> np.ndarray:
        """Generate embeddings using CodeBERT model."""
        embeddings = []

        # Process in batches to manage memory
        for i in range(0, len(symbols), self.config.batch_size):
            batch = symbols[i : i + self.config.batch_size]
            batch_texts = [self._symbol_to_text(symbol) for symbol in batch]

            # Tokenize batch
            inputs = self._tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.config.max_length,
                return_tensors="pt",
            )

            # Move to GPU if available
            if self.config.use_gpu and torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Generate embeddings
            with torch.no_grad():
                outputs = self._model(**inputs)
                # Use [CLS] token embeddings
                last_hidden = outputs.last_hidden_state[:, 0, :]
                batch_embeddings = last_hidden.cpu().numpy()

            embeddings.append(batch_embeddings)

            # Clear memory if requested
            if self.config.clear_model_after_batch:
                torch.cuda.empty_cache() if torch.cuda.is_available() else None

        result = np.vstack(embeddings) if embeddings else np.array([])

        # Normalize if requested
        if self.config.normalize_embeddings and len(result) > 0:
            norms = np.linalg.norm(result, axis=1, keepdims=True)
            result = result / norms

        return result

    def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score [0, 1]
        """
        # Handle edge cases
        if len(embedding1) == 0 or len(embedding2) == 0:
            return 0.0

        # Ensure same dimensions
        if embedding1.shape != embedding2.shape:
            return 0.0

        # Compute cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Clamp to [0, 1] range
        return max(0.0, min(1.0, similarity))

    def _symbol_to_text(self, symbol: Symbol) -> str:
        """Convert symbol to text for embedding generation."""
        parts = [
            f"name: {symbol.name}",
            f"type: {symbol.symbol_type.value}",
            f"content: {symbol.line_content.strip()}",
        ]

        if symbol.parameters:
            parts.append(f"parameters: {', '.join(symbol.parameters)}")

        if symbol.return_type:
            parts.append(f"returns: {symbol.return_type}")

        if symbol.scope and symbol.scope != "module":
            parts.append(f"scope: {symbol.scope}")

        return " | ".join(parts)

    def get_engine_info(self) -> Dict[str, Any]:
        """Get engine status and diagnostic information."""
        return {
            "method": self._current_method.value,
            "is_available": self.is_available(),
            "config": {
                "model_name": self.config.model_name,
                "batch_size": self.config.batch_size,
                "max_length": self.config.max_length,
                "use_gpu": self.config.use_gpu,
                "normalize_embeddings": self.config.normalize_embeddings,
            },
            "performance": {
                "avg_embedding_time": (
                    sum(self._embedding_times) / len(self._embedding_times)
                    if self._embedding_times
                    else 0
                ),
                "total_batches": len(self._embedding_times),
            },
        }


def main():
    """Main entry point for testing embedding engine functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Test CodeBERT embedding engine")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--test-text", help="Text to test embedding generation")
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )

    args = parser.parse_args()

    # Create configuration
    config = EmbeddingConfig()

    # Initialize engine
    engine = EmbeddingEngine(config, args.project_root)

    # Test embedding generation
    if args.test_text:
        from symbol_extractor import Symbol, SymbolType

        test_symbol = Symbol(
            name="test_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.py",
            line_number=1,
            line_content=args.test_text,
            scope="module",
        )

        start_time = time.time()
        embeddings = engine.generate_embeddings([test_symbol])
        execution_time = time.time() - start_time

        if args.output == "json":
            result = {
                "success": True,
                "embedding_shape": (embeddings.shape if len(embeddings) > 0 else None),
                "execution_time": execution_time,
                "engine_info": engine.get_engine_info(),
            }
            print(json.dumps(result, indent=2))
        else:
            print("Embedding Engine Test Results:")
            print(f"  Success: {len(embeddings) > 0}")
            shape = embeddings.shape if len(embeddings) > 0 else "None"
            print(f"  Embedding shape: {shape}")
            print(f"  Execution time: {execution_time:.3f}s")

            engine_info = engine.get_engine_info()
            print("\nEngine Info:")
            print(f"  Method: {engine_info['method']}")
            print(f"  Available: {engine_info['is_available']}")
    else:
        # Just show engine info
        engine_info = engine.get_engine_info()
        if args.output == "json":
            print(json.dumps(engine_info, indent=2))
        else:
            print("CodeBERT Embedding Engine Status:")
            print(f"  Method: {engine_info['method']}")
            print(f"  Available: {engine_info['is_available']}")


if __name__ == "__main__":
    main()
