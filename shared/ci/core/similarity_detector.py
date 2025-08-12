#!/usr/bin/env python3
"""
Faiss Vector Similarity Detector for Continuous Improvement Framework

Provides efficient vector similarity search using Faiss only.
No fallback mechanisms.
Requires faiss-cpu to be installed. Part of Claude Code Workflows - integrates
with 8-agent orchestration system.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "utils"))

# Import utilities and existing components
try:
    from shared.core.utils.output_formatter import ResultFormatter
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
        print(f"Error importing Symbol: {e}", file=sys.stderr)
        sys.exit(1)

# Required Faiss imports - fail fast if unavailable
try:
    import faiss
except ImportError:
    print(
        "Error: faiss-cpu is required for SimilarityDetector.\n"
        "Install with: pip install faiss-cpu\n"
        "For GPU support: pip install faiss-gpu",
        file=sys.stderr,
    )
    sys.exit(1)


class SimilarityMethod(Enum):
    """Available Faiss similarity detection methods."""

    FAISS_L2 = "faiss_l2"
    FAISS_COSINE = "faiss_cosine"


class IndexStatus(Enum):
    """Status of similarity index operations."""

    BUILT = "built"
    EMPTY = "empty"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class SimilarityConfig:
    """Configuration for Faiss similarity detector."""

    # Similarity thresholds (compatible with comparison_framework.py)
    exact_match_threshold: float = 0.95
    high_similarity_threshold: float = 0.85
    medium_similarity_threshold: float = 0.75
    low_similarity_threshold: float = 0.65

    # Faiss settings
    use_gpu: bool = False
    index_type: str = "IndexFlatIP"  # Inner product for cosine similarity
    nprobe: int = 1  # For IVF indices

    # Performance settings
    batch_size: int = 1000
    max_results: int = 100
    enable_caching: bool = True
    cache_ttl_hours: int = 24

    # Memory management
    max_memory_gb: float = 1.0
    normalize_vectors: bool = True

    # Search settings
    return_distances: bool = True
    return_indices: bool = True
    include_self_matches: bool = False


@dataclass
class SimilarityMatch:
    """Represents a similarity match between embeddings."""

    query_index: int
    match_index: int
    similarity_score: float
    distance: float
    query_symbol: Optional[Symbol] = None
    match_symbol: Optional[Symbol] = None
    confidence: float = 1.0
    method: SimilarityMethod = SimilarityMethod.FAISS_COSINE

    def __post_init__(self):
        """Validate similarity match data."""
        if not 0.0 <= self.similarity_score <= 1.0:
            raise ValueError(
                f"Similarity score must be [0,1], got {self.similarity_score}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be [0,1], got {self.confidence}")


class SimilarityDetector:
    """
    Faiss-powered vector similarity detector. Requires Faiss to be installed.
    Provides efficient similarity search with comprehensive caching and
    batch processing.
    """

    def __init__(
        self,
        config: Optional[SimilarityConfig] = None,
        project_root: Optional[Path] = None,
    ):
        self.config = config or SimilarityConfig()
        self.project_root = project_root or Path.cwd()

        # Initialize components
        self.tech_detector = TechStackDetector()
        self.result_formatter = ResultFormatter()

        # Index state
        self._index = None
        self._embeddings = None
        self._symbols = None
        self._current_method = None
        self._index_status = IndexStatus.EMPTY

        # Cache management
        self.cache_dir = self.project_root / ".claude" / "cache" / "similarity"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}

        # Performance tracking
        self._search_times = []
        self._build_times = []

        # Initialize Faiss method
        self._initialize_faiss_method()

    def _initialize_faiss_method(self) -> None:
        """Initialize Faiss similarity method - fail fast if unavailable."""
        if not self._validate_faiss_installation():
            print(
                "Error: Faiss initialization failed. "
                "Ensure faiss-cpu is properly installed.",
                file=sys.stderr,
            )
            sys.exit(1)

        self._current_method = SimilarityMethod.FAISS_COSINE
        print("Initialized Faiss similarity detection", file=sys.stderr)

    def _validate_faiss_installation(self) -> bool:
        """Validate Faiss installation with functional test."""
        try:
            # Test basic Faiss functionality
            test_dim = 10
            test_index = faiss.IndexFlatIP(test_dim)
            test_vectors = np.random.random((5, test_dim)).astype(np.float32)
            test_index.add(test_vectors)

            # Simple search test
            _, _ = test_index.search(test_vectors[:1], 1)
            return True
        except Exception as e:
            print(f"Faiss validation failed: {e}", file=sys.stderr)
            return False

    def is_available(self) -> bool:
        """Check if Faiss similarity methods are available."""
        return self._current_method in [
            SimilarityMethod.FAISS_L2,
            SimilarityMethod.FAISS_COSINE,
        ]

    def build_index(
        self, embeddings: np.ndarray, symbols: Optional[List[Symbol]] = None
    ) -> bool:
        """
        Build Faiss similarity search index from embeddings.

        Args:
            embeddings: Numpy array of embeddings [n_vectors, embedding_dim]
            symbols: Optional list of symbols corresponding to embeddings

        Returns:
            True if index built successfully, False otherwise
        """
        if len(embeddings) == 0:
            self._index_status = IndexStatus.EMPTY
            print("Error: Cannot build index from empty embeddings", file=sys.stderr)
            return False

        start_time = time.time()

        try:
            self._embeddings = embeddings.astype(np.float32)
            self._symbols = symbols or []

            # Normalize vectors if requested
            if self.config.normalize_vectors:
                norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
                # Avoid division by zero
                norms[norms == 0] = 1.0
                self._embeddings = self._embeddings / norms

            # Build Faiss index
            success = self._build_faiss_index()

            if success:
                self._index_status = IndexStatus.BUILT
                build_time = time.time() - start_time
                self._build_times.append(build_time)

                msg = f"Built Faiss index: {len(embeddings)} vectors, "
                msg += f"{embeddings.shape[1]}D, {build_time:.3f}s"
                print(msg, file=sys.stderr)
            else:
                self._index_status = IndexStatus.ERROR
                print("Error: Failed to build Faiss index", file=sys.stderr)

            return success

        except Exception as e:
            self._index_status = IndexStatus.ERROR
            print(f"Faiss index build error: {e}", file=sys.stderr)
            return False

    def _build_faiss_index(self) -> bool:
        """Build Faiss index from embeddings."""
        try:
            embedding_dim = self._embeddings.shape[1]

            # Choose index type based on configuration
            if self.config.index_type == "IndexFlatIP":
                # Inner product index (good for normalized cosine similarity)
                self._index = faiss.IndexFlatIP(embedding_dim)
            elif self.config.index_type == "IndexFlatL2":
                # L2 distance index
                self._index = faiss.IndexFlatL2(embedding_dim)
            else:
                # Default to inner product
                self._index = faiss.IndexFlatIP(embedding_dim)

            # Move to GPU if requested and available
            if self.config.use_gpu:
                if faiss.get_num_gpus() == 0:
                    print(
                        "Error: GPU acceleration requested but " "no GPUs available",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                try:
                    res = faiss.StandardGpuResources()
                    self._index = faiss.index_cpu_to_gpu(res, 0, self._index)
                    print("Using GPU acceleration for Faiss", file=sys.stderr)
                except Exception as e:
                    print(f"Error: GPU setup failed: {e}", file=sys.stderr)
                    sys.exit(1)

            # Add embeddings to index
            self._index.add(self._embeddings)
            return True

        except Exception as e:
            print(f"Error building Faiss index: {e}", file=sys.stderr)
            return False

    def find_similar(
        self, query_embedding: np.ndarray, threshold: float = None, k: int = None
    ) -> List[SimilarityMatch]:
        """
        Find similar vectors to query embedding using Faiss.

        Args:
            query_embedding: Query vector to find similarities for
            threshold: Minimum similarity threshold
                (uses config default if None)
            k: Maximum number of results (uses config default if None)

        Returns:
            List of similarity matches sorted by similarity score (desc)
        """
        if self._index_status != IndexStatus.BUILT:
            print("Error: Faiss index not built", file=sys.stderr)
            return []

        if len(query_embedding) == 0:
            print("Error: Cannot search with empty query embedding", file=sys.stderr)
            return []

        threshold = threshold or self.config.medium_similarity_threshold
        k = k or self.config.max_results

        start_time = time.time()

        try:
            matches = self._faiss_search_similar(query_embedding, k)

            # Filter by threshold and remove self-matches if configured
            filtered_matches = []
            for match in matches:
                if match.similarity_score >= threshold:
                    if (
                        self.config.include_self_matches
                        or match.query_index != match.match_index
                    ):
                        filtered_matches.append(match)

            # Sort by similarity score (descending)
            filtered_matches.sort(key=lambda x: x.similarity_score, reverse=True)

            # Track performance
            search_time = time.time() - start_time
            self._search_times.append(search_time)

            return filtered_matches[:k]

        except Exception as e:
            print(f"Faiss similarity search error: {e}", file=sys.stderr)
            return []

    def _faiss_search_similar(
        self, query_embedding: np.ndarray, k: int
    ) -> List[SimilarityMatch]:
        """Search for similar vectors using Faiss."""
        query = query_embedding.reshape(1, -1).astype(np.float32)

        # Normalize query if embeddings were normalized
        if self.config.normalize_vectors:
            norm = np.linalg.norm(query)
            if norm == 0:
                print("Warning: Query embedding has zero norm", file=sys.stderr)
                return []
            query = query / norm

        # Search index
        distances, indices = self._index.search(query, min(k, self._index.ntotal))

        matches = []
        for i in range(len(distances[0])):
            distance = distances[0][i]
            index = indices[0][i]

            # Skip invalid indices
            if index == -1:
                continue

            # Convert distance to similarity score
            if self.config.index_type == "IndexFlatIP":
                # Inner product -> cosine similarity for normalized vectors
                similarity = max(0.0, min(1.0, distance))
            else:
                # L2 distance -> similarity (inverse relationship)
                similarity = max(0.0, 1.0 / (1.0 + distance))

            match = SimilarityMatch(
                query_index=0,  # Single query
                match_index=int(index),
                similarity_score=similarity,
                distance=distance,
                query_symbol=None,
                match_symbol=(
                    self._symbols[int(index)]
                    if self._symbols and int(index) < len(self._symbols)
                    else None
                ),
                confidence=0.95,  # High confidence for Faiss
                method=self._current_method,
            )
            matches.append(match)

        return matches

    def batch_similarity_search(
        self, embeddings: np.ndarray, threshold: float = None
    ) -> Dict[int, List[SimilarityMatch]]:
        """
        Perform Faiss similarity search for multiple query
        embeddings efficiently.

        Args:
            embeddings: Query embeddings [n_queries, embedding_dim]
            threshold: Minimum similarity threshold

        Returns:
            Dictionary mapping query indices to their similarity matches
        """
        if self._index_status != IndexStatus.BUILT:
            print("Error: Faiss index not built", file=sys.stderr)
            return {}

        if len(embeddings) == 0:
            print("Error: Cannot search with empty embeddings", file=sys.stderr)
            return {}

        threshold = threshold or self.config.medium_similarity_threshold
        results = {}

        # Process in batches to manage memory
        for start_idx in range(0, len(embeddings), self.config.batch_size):
            end_idx = min(start_idx + self.config.batch_size, len(embeddings))
            batch = embeddings[start_idx:end_idx]

            for i, query_embedding in enumerate(batch):
                query_idx = start_idx + i
                matches = self.find_similar(query_embedding, threshold)

                # Update query indices in matches
                for match in matches:
                    match.query_index = query_idx

                results[query_idx] = matches

        return results

    def compute_pairwise_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings directly.

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

    def get_detector_info(self) -> Dict[str, Any]:
        """Get Faiss detector status and diagnostic information."""
        return {
            "method": (self._current_method.value if self._current_method else None),
            "faiss_available": True,  # Always true - exit if not available
            "is_available": self.is_available(),
            "index_status": self._index_status.value,
            "config": {
                "exact_match_threshold": self.config.exact_match_threshold,
                "high_similarity_threshold": self.config.high_similarity_threshold,
                "medium_similarity_threshold": self.config.medium_similarity_threshold,
                "low_similarity_threshold": self.config.low_similarity_threshold,
                "index_type": self.config.index_type,
                "use_gpu": self.config.use_gpu,
                "batch_size": self.config.batch_size,
                "max_results": self.config.max_results,
                "normalize_vectors": self.config.normalize_vectors,
            },
            "cache_stats": self._cache_stats.copy(),
            "cache_dir": str(self.cache_dir),
            "performance": {
                "avg_search_time": (
                    sum(self._search_times) / len(self._search_times)
                    if self._search_times
                    else 0
                ),
                "avg_build_time": (
                    sum(self._build_times) / len(self._build_times)
                    if self._build_times
                    else 0
                ),
                "total_searches": len(self._search_times),
                "total_builds": len(self._build_times),
            },
            "index_info": {
                "embeddings_count": (
                    len(self._embeddings) if self._embeddings is not None else 0
                ),
                "embedding_dim": (
                    self._embeddings.shape[1] if self._embeddings is not None else 0
                ),
                "symbols_count": len(self._symbols) if self._symbols else 0,
            },
            "faiss_info": {
                "num_gpus": faiss.get_num_gpus(),
                "version": getattr(faiss, "__version__", "unknown"),
                "index_type": self.config.index_type,
                "using_gpu": self.config.use_gpu and faiss.get_num_gpus() > 0,
            },
        }

    def clear_index(self) -> None:
        """Clear the current Faiss similarity index and cached data."""
        self._index = None
        self._embeddings = None
        self._symbols = None
        self._index_status = IndexStatus.EMPTY

        # Clear performance stats
        self._search_times.clear()
        self._build_times.clear()

        print("Cleared Faiss similarity index", file=sys.stderr)


def main():
    """Main entry point for testing Faiss similarity detector functionality."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Faiss vector similarity detector"
    )
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument(
        "--test-vectors",
        type=int,
        default=100,
        help="Number of test vectors to generate",
    )
    parser.add_argument(
        "--vector-dim", type=int, default=768, help="Dimension of test vectors"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.75, help="Similarity threshold for testing"
    )
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )
    parser.add_argument(
        "--use-gpu", action="store_true", help="Enable GPU acceleration"
    )

    args = parser.parse_args()

    # Create configuration
    config = SimilarityConfig(
        medium_similarity_threshold=args.threshold, use_gpu=args.use_gpu
    )

    # Initialize detector (will exit if Faiss not available)
    detector = SimilarityDetector(config, args.project_root)

    # Generate test embeddings
    print(
        f"Generating {args.test_vectors} test vectors of "
        f"dimension {args.vector_dim}"
    )
    test_embeddings = np.random.random((args.test_vectors, args.vector_dim)).astype(
        np.float32
    )

    # Build index
    start_time = time.time()
    success = detector.build_index(test_embeddings)
    build_time = time.time() - start_time

    if not success:
        print("Error: Failed to build Faiss similarity index")
        sys.exit(1)

    # Test similarity search
    query_vector = test_embeddings[0]  # Use first vector as query
    start_time = time.time()
    matches = detector.find_similar(query_vector, args.threshold, k=10)
    search_time = time.time() - start_time

    # Output results
    if args.output == "json":
        import json

        result = {
            "success": success,
            "build_time": build_time,
            "search_time": search_time,
            "matches_found": len(matches),
            "detector_info": detector.get_detector_info(),
            "sample_matches": [
                {
                    "match_index": match.match_index,
                    "similarity_score": match.similarity_score,
                    "distance": match.distance,
                    "method": match.method.value,
                    "confidence": match.confidence,
                }
                for match in matches[:5]  # First 5 matches
            ],
        }
        print(json.dumps(result, indent=2))
    else:
        print("Faiss Similarity Detector Test Results:")
        print(f"  Index built: {success}")
        print(f"  Build time: {build_time:.3f}s")
        print(f"  Search time: {search_time:.3f}s")
        print(f"  Matches found: {len(matches)}")

        detector_info = detector.get_detector_info()
        print("\nFaiss Detector Info:")
        print(f"  Method: {detector_info['method']}")
        print(f"  Index status: {detector_info['index_status']}")
        emb_count = detector_info["index_info"]["embeddings_count"]
        print(f"  Embeddings: {emb_count}")
        print(f"  Dimensions: {detector_info['index_info']['embedding_dim']}")
        print(f"  Faiss version: {detector_info['faiss_info']['version']}")
        print(f"  GPUs available: {detector_info['faiss_info']['num_gpus']}")
        print(f"  Using GPU: {detector_info['faiss_info']['using_gpu']}")

        if matches:
            print("\nTop 5 Matches:")
            for i, match in enumerate(matches[:5]):
                print(
                    f"  {i + 1}. Index {match.match_index}: "
                    f"{match.similarity_score:.3f} similarity "
                    f"({match.method.value})"
                )


if __name__ == "__main__":
    main()
