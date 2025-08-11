#!/usr/bin/env python3
"""
CodeBERT Embedding Engine for Continuous Improvement Framework

Provides local CodeBERT embeddings using transformers library.
Part of Claude Code Workflows - integrates with 8-agent orchestration system.

Requires transformers and torch libraries - exits with error if unavailable.
"""

import hashlib
import json
import pickle
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))

# Import utilities and existing components
try:
    from output_formatter import ResultFormatter
    from tech_stack_detector import TechStackDetector
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
        print(f"Error importing Symbol: {e}", file=sys.stderr)
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


class CacheStatus(Enum):
    """Status of embedding cache operations."""

    HIT = "hit"
    MISS = "miss"
    WRITE_ERROR = "write_error"
    READ_ERROR = "read_error"


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
    enable_caching: bool = True
    cache_ttl_hours: int = 168  # 1 week

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

        # Cache management
        self.cache_dir = self.project_root / ".claude" / "cache" / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}

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

        # Check cache first
        cached_embeddings, cache_misses = self._load_cached_embeddings(symbols)

        # Generate embeddings for cache misses
        if cache_misses:
            new_embeddings = self._generate_batch_embeddings(cache_misses)

            # Cache new embeddings
            if self.config.enable_caching:
                self._cache_embeddings(cache_misses, new_embeddings)

            # Combine cached and new embeddings
            all_embeddings = self._combine_embeddings(
                symbols, cached_embeddings, cache_misses, new_embeddings
            )
        else:
            all_embeddings = cached_embeddings

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

    def _get_cache_key(self, symbol: Symbol) -> str:
        """Generate cache key for symbol."""
        content = self._symbol_to_text(symbol)
        cache_data = {
            "content": content,
            "method": self._current_method.value,
            "config_hash": self._get_config_hash(),
        }

        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def _get_config_hash(self) -> str:
        """Get hash of embedding configuration for cache validation."""
        config_data = {
            "model_name": self.config.model_name,
            "normalize": self.config.normalize_embeddings,
            "max_length": self.config.max_length,
        }
        config_string = json.dumps(config_data, sort_keys=True)
        return hashlib.md5(config_string.encode()).hexdigest()[:8]

    def _load_cached_embeddings(
        self, symbols: List[Symbol]
    ) -> Tuple[Dict, List[Symbol]]:
        """Load cached embeddings and return cache misses."""
        cached_embeddings = {}
        cache_misses = []

        if not self.config.enable_caching:
            return cached_embeddings, symbols

        for symbol in symbols:
            cache_key = self._get_cache_key(symbol)
            cache_file = self.cache_dir / f"{cache_key}.pkl"

            try:
                if cache_file.exists():
                    # Check if cache is still valid
                    if self._is_cache_valid(cache_file):
                        with open(cache_file, "rb") as f:
                            cached_embeddings[cache_key] = pickle.load(f)
                        self._cache_stats["hits"] += 1
                    else:
                        cache_misses.append(symbol)
                        self._cache_stats["misses"] += 1
                else:
                    cache_misses.append(symbol)
                    self._cache_stats["misses"] += 1
            except Exception as e:
                cache_misses.append(symbol)
                self._cache_stats["errors"] += 1
                msg = f"Cache read error for {cache_key}: {e}"
                print(msg, file=sys.stderr)

        return cached_embeddings, cache_misses

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cached embedding is still valid."""
        try:
            age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
            return age_hours < self.config.cache_ttl_hours
        except Exception:
            return False

    def _cache_embeddings(self, symbols: List[Symbol], embeddings: np.ndarray) -> None:
        """Cache embeddings for symbols."""
        if not self.config.enable_caching or len(embeddings) == 0:
            return

        for i, symbol in enumerate(symbols):
            try:
                cache_key = self._get_cache_key(symbol)
                cache_file = self.cache_dir / f"{cache_key}.pkl"

                with open(cache_file, "wb") as f:
                    pickle.dump(embeddings[i], f)
            except Exception as e:
                self._cache_stats["errors"] += 1
                print(f"Cache write error: {e}", file=sys.stderr)

    def _combine_embeddings(
        self,
        all_symbols: List[Symbol],
        cached_embeddings: Dict,
        cache_misses: List[Symbol],
        new_embeddings: np.ndarray,
    ) -> np.ndarray:
        """Combine cached and new embeddings in original order."""
        result = []
        new_idx = 0

        for symbol in all_symbols:
            cache_key = self._get_cache_key(symbol)

            if cache_key in cached_embeddings:
                result.append(cached_embeddings[cache_key])
            else:
                result.append(new_embeddings[new_idx])
                new_idx += 1

        return np.array(result) if result else np.array([])

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
                "enable_caching": self.config.enable_caching,
            },
            "cache_stats": self._cache_stats.copy(),
            "cache_dir": str(self.cache_dir),
            "performance": {
                "avg_embedding_time": (
                    sum(self._embedding_times) / len(self._embedding_times)
                    if self._embedding_times
                    else 0
                ),
                "total_batches": len(self._embedding_times),
            },
        }

    def clear_cache(self, older_than_hours: Optional[int] = None) -> int:
        """Clear embedding cache files."""
        cleared_count = 0
        cutoff_time = None

        if older_than_hours:
            cutoff_time = time.time() - (older_than_hours * 3600)

        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                should_delete = True

                if cutoff_time:
                    file_age = cache_file.stat().st_mtime
                    should_delete = file_age < cutoff_time

                if should_delete:
                    cache_file.unlink()
                    cleared_count += 1
        except Exception as e:
            print(f"Cache clear error: {e}", file=sys.stderr)

        return cleared_count


def main():
    """Main entry point for testing embedding engine functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Test CodeBERT embedding engine")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--test-text", help="Text to test embedding generation")
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear embedding cache"
    )

    args = parser.parse_args()

    # Create configuration
    config = EmbeddingConfig(enable_caching=not args.no_cache)

    # Initialize engine
    engine = EmbeddingEngine(config, args.project_root)

    if args.clear_cache:
        cleared = engine.clear_cache()
        print(f"Cleared {cleared} cache files")
        return

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
            print(f"  Cache hits: {engine_info['cache_stats']['hits']}")
            print(f"  Cache misses: {engine_info['cache_stats']['misses']}")
    else:
        # Just show engine info
        engine_info = engine.get_engine_info()
        if args.output == "json":
            print(json.dumps(engine_info, indent=2))
        else:
            print("CodeBERT Embedding Engine Status:")
            print(f"  Method: {engine_info['method']}")
            print(f"  Available: {engine_info['is_available']}")
            cache_enabled = engine_info["config"]["enable_caching"]
            print(f"  Cache enabled: {cache_enabled}")


if __name__ == "__main__":
    main()
