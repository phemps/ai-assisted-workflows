#!/usr/bin/env python3
"""
Faiss Vector Similarity Detector for Continuous Improvement Framework

Provides efficient vector similarity search using Faiss with graceful
degradation to cosine similarity. Part of Claude Code Workflows - integrates
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

# Optional Faiss imports with graceful degradation
FAISS_AVAILABLE = False
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# Scipy for fallback cosine similarity
SCIPY_AVAILABLE = False
try:
    from scipy.spatial.distance import cosine as scipy_cosine

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class SimilarityMethod(Enum):
    """Available similarity detection methods."""

    FAISS_L2 = "faiss_l2"
    FAISS_COSINE = "faiss_cosine"
    SCIPY_COSINE = "scipy_cosine"
    NUMPY_COSINE = "numpy_cosine"


class IndexStatus(Enum):
    """Status of similarity index operations."""

    BUILT = "built"
    EMPTY = "empty"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class SimilarityConfig:
    """Configuration for similarity detector following existing patterns."""

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

    # Fallback settings
    use_faiss_fallback: bool = True
    cosine_similarity_threshold: float = 0.1  # Min threshold for cosine


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
    method: SimilarityMethod = SimilarityMethod.NUMPY_COSINE

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
    Faiss-powered vector similarity detector with robust fallback mechanisms.
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

        # Initialize similarity method
        self._initialize_similarity_method()

    def _initialize_similarity_method(self) -> None:
        """Initialize the best available similarity method."""
        if FAISS_AVAILABLE and self._try_initialize_faiss():
            self._current_method = SimilarityMethod.FAISS_COSINE
            print("Initialized Faiss similarity detection", file=sys.stderr)
        elif SCIPY_AVAILABLE:
            self._current_method = SimilarityMethod.SCIPY_COSINE
            print("Using scipy cosine similarity fallback", file=sys.stderr)
        else:
            self._current_method = SimilarityMethod.NUMPY_COSINE
            print("Using numpy cosine similarity fallback", file=sys.stderr)

    def _try_initialize_faiss(self) -> bool:
        """Try to initialize Faiss with error handling."""
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
            print(f"Failed to initialize Faiss: {e}", file=sys.stderr)
            return False

    def is_available(self) -> bool:
        """Check if advanced similarity methods are available."""
        return self._current_method in [
            SimilarityMethod.FAISS_L2,
            SimilarityMethod.FAISS_COSINE,
        ]

    def build_index(
        self, embeddings: np.ndarray, symbols: Optional[List[Symbol]] = None
    ) -> bool:
        """
        Build similarity search index from embeddings.

        Args:
            embeddings: Numpy array of embeddings [n_vectors, embedding_dim]
            symbols: Optional list of symbols corresponding to embeddings

        Returns:
            True if index built successfully, False otherwise
        """
        if len(embeddings) == 0:
            self._index_status = IndexStatus.EMPTY
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

            # Build appropriate index
            if self._current_method in [
                SimilarityMethod.FAISS_COSINE,
                SimilarityMethod.FAISS_L2,
            ]:
                success = self._build_faiss_index()
            else:
                # For scipy/numpy, we don't need to build an index
                success = True
                self._index = None

            if success:
                self._index_status = IndexStatus.BUILT
                build_time = time.time() - start_time
                self._build_times.append(build_time)

                msg = f"Built similarity index: {len(embeddings)} vectors, "
                msg += f"{embeddings.shape[1]}D, {build_time:.3f}s"
                print(msg, file=sys.stderr)
            else:
                self._index_status = IndexStatus.ERROR

            return success

        except Exception as e:
            self._index_status = IndexStatus.ERROR
            print(f"Index build error: {e}", file=sys.stderr)
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
            if self.config.use_gpu and faiss.get_num_gpus() > 0:
                try:
                    res = faiss.StandardGpuResources()
                    self._index = faiss.index_cpu_to_gpu(res, 0, self._index)
                    print("Using GPU acceleration for Faiss", file=sys.stderr)
                except Exception as e:
                    print(f"GPU setup failed, using CPU: {e}", file=sys.stderr)

            # Add embeddings to index
            self._index.add(self._embeddings)
            return True

        except Exception as e:
            print(f"Faiss index build error: {e}", file=sys.stderr)
            return False

    def find_similar(
        self, query_embedding: np.ndarray, threshold: float = None, k: int = None
    ) -> List[SimilarityMatch]:
        """
        Find similar vectors to query embedding.

        Args:
            query_embedding: Query vector to find similarities for
            threshold: Minimum similarity threshold (uses config default if None)
            k: Maximum number of results (uses config default if None)

        Returns:
            List of similarity matches sorted by similarity score (desc)
        """
        if self._index_status != IndexStatus.BUILT or len(query_embedding) == 0:
            return []

        threshold = threshold or self.config.medium_similarity_threshold
        k = k or self.config.max_results

        start_time = time.time()

        try:
            if self._current_method in [
                SimilarityMethod.FAISS_COSINE,
                SimilarityMethod.FAISS_L2,
            ]:
                matches = self._faiss_search_similar(query_embedding, k)
            elif self._current_method == SimilarityMethod.SCIPY_COSINE:
                matches = self._scipy_search_similar(query_embedding, k)
            else:
                matches = self._numpy_search_similar(query_embedding, k)

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
            print(f"Similarity search error: {e}", file=sys.stderr)
            return []

    def _faiss_search_similar(
        self, query_embedding: np.ndarray, k: int
    ) -> List[SimilarityMatch]:
        """Search for similar vectors using Faiss."""
        query = query_embedding.reshape(1, -1).astype(np.float32)

        # Normalize query if embeddings were normalized
        if self.config.normalize_vectors:
            norm = np.linalg.norm(query)
            if norm > 0:
                query = query / norm

        # Search index
        distances, indices = self._index.search(query, min(k, self._index.ntotal))

        matches = []
        for i in range(len(distances[0])):
            distance = distances[0][i]
            index = indices[0][i]

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

    def _scipy_search_similar(
        self, query_embedding: np.ndarray, k: int
    ) -> List[SimilarityMatch]:
        """Search for similar vectors using scipy cosine distance."""
        similarities = []

        for i, embedding in enumerate(self._embeddings):
            # Calculate cosine similarity
            distance = scipy_cosine(query_embedding, embedding)
            similarity = max(0.0, 1.0 - distance)  # Convert distance to similarity

            similarities.append((similarity, i, distance))

        # Sort by similarity (descending) and take top k
        similarities.sort(reverse=True)

        matches = []
        for similarity, index, distance in similarities[:k]:
            match = SimilarityMatch(
                query_index=0,  # Single query
                match_index=index,
                similarity_score=similarity,
                distance=distance,
                query_symbol=None,
                match_symbol=(
                    self._symbols[index]
                    if self._symbols and index < len(self._symbols)
                    else None
                ),
                confidence=0.85,  # Good confidence for scipy
                method=self._current_method,
            )
            matches.append(match)

        return matches

    def _numpy_search_similar(
        self, query_embedding: np.ndarray, k: int
    ) -> List[SimilarityMatch]:
        """Search for similar vectors using numpy cosine similarity."""
        # Normalize vectors for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norms = self._embeddings / np.linalg.norm(
            self._embeddings, axis=1, keepdims=True
        )

        # Calculate cosine similarities
        similarities = np.dot(embeddings_norms, query_norm)

        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:k]

        matches = []
        for idx in top_indices:
            similarity = similarities[idx]
            distance = 1.0 - similarity

            match = SimilarityMatch(
                query_index=0,  # Single query
                match_index=int(idx),
                similarity_score=max(0.0, min(1.0, float(similarity))),
                distance=float(distance),
                query_symbol=None,
                match_symbol=(
                    self._symbols[int(idx)]
                    if self._symbols and int(idx) < len(self._symbols)
                    else None
                ),
                confidence=0.75,  # Basic confidence for numpy
                method=self._current_method,
            )
            matches.append(match)

        return matches

    def batch_similarity_search(
        self, embeddings: np.ndarray, threshold: float = None
    ) -> Dict[int, List[SimilarityMatch]]:
        """
        Perform similarity search for multiple query embeddings efficiently.

        Args:
            embeddings: Query embeddings [n_queries, embedding_dim]
            threshold: Minimum similarity threshold

        Returns:
            Dictionary mapping query indices to their similarity matches
        """
        if self._index_status != IndexStatus.BUILT or len(embeddings) == 0:
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
        Compute similarity between two embeddings directly.

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
        """Get detector status and diagnostic information."""
        return {
            "method": (self._current_method.value if self._current_method else None),
            "faiss_available": FAISS_AVAILABLE,
            "scipy_available": SCIPY_AVAILABLE,
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
        }

    def clear_index(self) -> None:
        """Clear the current similarity index and cached data."""
        self._index = None
        self._embeddings = None
        self._symbols = None
        self._index_status = IndexStatus.EMPTY

        # Clear performance stats
        self._search_times.clear()
        self._build_times.clear()

        print("Cleared similarity index", file=sys.stderr)


def main():
    """Main entry point for testing similarity detector functionality."""
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
        "--no-faiss", action="store_true", help="Disable Faiss and use fallback"
    )

    args = parser.parse_args()

    # Create configuration
    config = SimilarityConfig(medium_similarity_threshold=args.threshold)

    # Initialize detector
    detector = SimilarityDetector(config, args.project_root)

    # Override method if Faiss disabled
    if args.no_faiss:
        if SCIPY_AVAILABLE:
            detector._current_method = SimilarityMethod.SCIPY_COSINE
        else:
            detector._current_method = SimilarityMethod.NUMPY_COSINE

    # Generate test embeddings
    print(f"Generating {args.test_vectors} test vectors of dimension {args.vector_dim}")
    test_embeddings = np.random.random((args.test_vectors, args.vector_dim)).astype(
        np.float32
    )

    # Build index
    start_time = time.time()
    success = detector.build_index(test_embeddings)
    build_time = time.time() - start_time

    if not success:
        print("Failed to build similarity index")
        return

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
        print("Similarity Detector Test Results:")
        print(f"  Index built: {success}")
        print(f"  Build time: {build_time:.3f}s")
        print(f"  Search time: {search_time:.3f}s")
        print(f"  Matches found: {len(matches)}")

        detector_info = detector.get_detector_info()
        print("\nDetector Info:")
        print(f"  Method: {detector_info['method']}")
        print(f"  Faiss available: {detector_info['faiss_available']}")
        print(f"  Index status: {detector_info['index_status']}")
        print(f"  Embeddings: {detector_info['index_info']['embeddings_count']}")
        print(f"  Dimensions: {detector_info['index_info']['embedding_dim']}")

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
