#!/usr/bin/env python3
"""
Duplicate Detection Algorithm Implementation
Part of Phase 2.2: Analysis Engine - Duplicate Detection

This module implements sophisticated duplicate code detection algorithms
that build upon the symbol extraction and comparison framework.
"""

import ast
import hashlib
import re
import difflib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CodeBlock:
    """Represents a block of code for duplicate detection analysis."""

    content: str
    file_path: str
    start_line: int
    end_line: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    complexity_score: int = 0
    ast_hash: Optional[str] = None
    token_hash: Optional[str] = None


@dataclass
class DuplicateMatch:
    """Represents a detected duplicate code match."""

    similarity_score: float
    block1: CodeBlock
    block2: CodeBlock
    match_type: str  # 'exact', 'structural', 'semantic'
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DuplicationDetector(ABC):
    """Abstract base class for duplicate detection algorithms."""

    @abstractmethod
    def detect_duplicates(self, code_blocks: List[CodeBlock]) -> List[DuplicateMatch]:
        """Detect duplicates in the given code blocks."""
        pass

    @abstractmethod
    def get_similarity_threshold(self) -> float:
        """Get the minimum similarity threshold for reporting duplicates."""
        pass


class ExactDuplicateDetector(DuplicationDetector):
    """Detects exact duplicate code blocks using content hashing."""

    def __init__(self, min_lines: int = 5, similarity_threshold: float = 1.0):
        self.min_lines = min_lines
        self.similarity_threshold = similarity_threshold

    def detect_duplicates(self, code_blocks: List[CodeBlock]) -> List[DuplicateMatch]:
        """Detect exact duplicates using content hash comparison."""
        duplicates = []
        content_hash_map: Dict[str, List[CodeBlock]] = {}

        # Group blocks by content hash
        for block in code_blocks:
            if self._should_analyze_block(block):
                content_hash = self._get_content_hash(block.content)
                if content_hash not in content_hash_map:
                    content_hash_map[content_hash] = []
                content_hash_map[content_hash].append(block)

        # Find duplicates
        for hash_key, blocks in content_hash_map.items():
            if len(blocks) > 1:
                # Create matches for all pairs
                for i in range(len(blocks)):
                    for j in range(i + 1, len(blocks)):
                        match = DuplicateMatch(
                            similarity_score=1.0,
                            block1=blocks[i],
                            block2=blocks[j],
                            match_type="exact",
                            confidence=1.0,
                            metadata={"content_hash": hash_key},
                        )
                        duplicates.append(match)

        return duplicates

    def get_similarity_threshold(self) -> float:
        return self.similarity_threshold

    def _should_analyze_block(self, block: CodeBlock) -> bool:
        """Check if block meets minimum criteria for analysis."""
        line_count = len(block.content.strip().split("\n"))
        return line_count >= self.min_lines and bool(block.content.strip())

    def _get_content_hash(self, content: str) -> str:
        """Generate hash for normalized content."""
        # Normalize whitespace and comments for better matching
        normalized = self._normalize_content(content)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _normalize_content(self, content: str) -> str:
        """Normalize content by removing comments and standardizing whitespace."""
        # Remove single-line comments
        content = re.sub(r"#.*$", "", content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'""".*?"""', "", content, flags=re.DOTALL)
        content = re.sub(r"'''.*?'''", "", content, flags=re.DOTALL)
        # Normalize whitespace
        content = re.sub(r"\s+", " ", content)
        return content.strip()


class StructuralDuplicateDetector(DuplicationDetector):
    """Detects structurally similar code using AST comparison."""

    def __init__(self, similarity_threshold: float = 0.8, min_nodes: int = 10):
        self.similarity_threshold = similarity_threshold
        self.min_nodes = min_nodes

    def detect_duplicates(self, code_blocks: List[CodeBlock]) -> List[DuplicateMatch]:
        """Detect structural duplicates using AST similarity."""
        duplicates = []
        ast_structures = []

        # Parse AST for each block
        for block in code_blocks:
            try:
                tree = ast.parse(block.content)
                structure = self._extract_ast_structure(tree)
                if len(structure) >= self.min_nodes:
                    ast_structures.append((block, structure))
            except SyntaxError:
                logger.debug(
                    f"Syntax error in block from {block.file_path}:{block.start_line}"
                )
                continue

        # Compare structures
        for i in range(len(ast_structures)):
            for j in range(i + 1, len(ast_structures)):
                block1, structure1 = ast_structures[i]
                block2, structure2 = ast_structures[j]

                similarity = self._calculate_structural_similarity(
                    structure1, structure2
                )
                if similarity >= self.similarity_threshold:
                    match = DuplicateMatch(
                        similarity_score=similarity,
                        block1=block1,
                        block2=block2,
                        match_type="structural",
                        confidence=self._calculate_confidence(similarity),
                        metadata={
                            "ast_nodes_1": len(structure1),
                            "ast_nodes_2": len(structure2),
                        },
                    )
                    duplicates.append(match)

        return duplicates

    def get_similarity_threshold(self) -> float:
        return self.similarity_threshold

    def _extract_ast_structure(self, tree: ast.AST) -> List[str]:
        """Extract structural signature from AST."""
        structure = []

        class StructureVisitor(ast.NodeVisitor):
            def visit(self, node):
                # Record node type and key attributes
                node_signature = type(node).__name__

                # Add specific attributes for certain node types
                if isinstance(node, ast.FunctionDef):
                    node_signature += f"({len(node.args.args)})"
                elif isinstance(node, ast.ClassDef):
                    node_signature += f"({len(node.bases)})"
                elif isinstance(node, ast.For):
                    node_signature += "(loop)"
                elif isinstance(node, ast.If):
                    node_signature += "(branch)"

                structure.append(node_signature)
                self.generic_visit(node)

        visitor = StructureVisitor()
        visitor.visit(tree)
        return structure

    def _calculate_structural_similarity(
        self, structure1: List[str], structure2: List[str]
    ) -> float:
        """Calculate similarity between two AST structures."""
        if not structure1 or not structure2:
            return 0.0

        # Use sequence matching for structural similarity
        matcher = difflib.SequenceMatcher(None, structure1, structure2)
        return matcher.ratio()

    def _calculate_confidence(self, similarity: float) -> float:
        """Calculate confidence score based on similarity."""
        # Higher similarity = higher confidence
        # Structural matches are generally less confident than exact matches
        return min(similarity * 0.9, 0.95)


class SemanticDuplicateDetector(DuplicationDetector):
    """Detects semantically similar code using token-based analysis."""

    def __init__(self, similarity_threshold: float = 0.7, min_tokens: int = 20):
        self.similarity_threshold = similarity_threshold
        self.min_tokens = min_tokens

    def detect_duplicates(self, code_blocks: List[CodeBlock]) -> List[DuplicateMatch]:
        """Detect semantic duplicates using token similarity."""
        duplicates = []
        token_vectors = []

        # Create token vectors for each block
        for block in code_blocks:
            tokens = self._extract_semantic_tokens(block.content)
            if len(tokens) >= self.min_tokens:
                token_vectors.append((block, tokens))

        # Compare token vectors
        for i in range(len(token_vectors)):
            for j in range(i + 1, len(token_vectors)):
                block1, tokens1 = token_vectors[i]
                block2, tokens2 = token_vectors[j]

                similarity = self._calculate_token_similarity(tokens1, tokens2)
                if similarity >= self.similarity_threshold:
                    match = DuplicateMatch(
                        similarity_score=similarity,
                        block1=block1,
                        block2=block2,
                        match_type="semantic",
                        confidence=self._calculate_confidence(similarity),
                        metadata={"tokens_1": len(tokens1), "tokens_2": len(tokens2)},
                    )
                    duplicates.append(match)

        return duplicates

    def get_similarity_threshold(self) -> float:
        return self.similarity_threshold

    def _extract_semantic_tokens(self, content: str) -> List[str]:
        """Extract semantic tokens from code content."""
        # Remove comments and strings, focus on identifiers and keywords
        tokens = []

        try:
            tree = ast.parse(content)

            class TokenExtractor(ast.NodeVisitor):
                def visit_Name(self, node):
                    tokens.append(node.id)
                    self.generic_visit(node)

                def visit_Attribute(self, node):
                    tokens.append(node.attr)
                    self.generic_visit(node)

                def visit_FunctionDef(self, node):
                    tokens.append(f"def:{node.name}")
                    self.generic_visit(node)

                def visit_ClassDef(self, node):
                    tokens.append(f"class:{node.name}")
                    self.generic_visit(node)

            extractor = TokenExtractor()
            extractor.visit(tree)

        except SyntaxError:
            # Fallback to simple tokenization
            tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", content)

        return tokens

    def _calculate_token_similarity(
        self, tokens1: List[str], tokens2: List[str]
    ) -> float:
        """Calculate similarity based on shared tokens."""
        if not tokens1 or not tokens2:
            return 0.0

        set1 = set(tokens1)
        set2 = set(tokens2)

        # Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _calculate_confidence(self, similarity: float) -> float:
        """Calculate confidence score for semantic matches."""
        # Semantic matches have lower confidence than structural/exact
        return min(similarity * 0.8, 0.85)


class CompositeDuplicateDetector:
    """Combines multiple detection strategies for comprehensive analysis."""

    def __init__(
        self,
        exact_detector: Optional[ExactDuplicateDetector] = None,
        structural_detector: Optional[StructuralDuplicateDetector] = None,
        semantic_detector: Optional[SemanticDuplicateDetector] = None,
    ):
        self.detectors = []

        if exact_detector:
            self.detectors.append(exact_detector)
        if structural_detector:
            self.detectors.append(structural_detector)
        if semantic_detector:
            self.detectors.append(semantic_detector)

        # Default detectors if none provided
        if not self.detectors:
            self.detectors = [
                ExactDuplicateDetector(),
                StructuralDuplicateDetector(),
                SemanticDuplicateDetector(),
            ]

    def detect_all_duplicates(
        self, code_blocks: List[CodeBlock]
    ) -> List[DuplicateMatch]:
        """Run all detection strategies and combine results."""
        all_duplicates = []

        for detector in self.detectors:
            try:
                duplicates = detector.detect_duplicates(code_blocks)
                all_duplicates.extend(duplicates)
                logger.info(
                    f"{type(detector).__name__} found {len(duplicates)} duplicates"
                )
            except Exception as e:
                logger.error(f"Error in {type(detector).__name__}: {e}")

        # Remove duplicates and sort by similarity score
        unique_duplicates = self._deduplicate_matches(all_duplicates)
        return sorted(unique_duplicates, key=lambda x: x.similarity_score, reverse=True)

    def _deduplicate_matches(
        self, matches: List[DuplicateMatch]
    ) -> List[DuplicateMatch]:
        """Remove duplicate matches based on file paths and line numbers."""
        seen_pairs = set()
        unique_matches = []

        for match in matches:
            # Create a consistent identifier for the match pair
            pair_id = self._create_match_pair_id(match)

            if pair_id not in seen_pairs:
                seen_pairs.add(pair_id)
                unique_matches.append(match)

        return unique_matches

    def _create_match_pair_id(self, match: DuplicateMatch) -> str:
        """Create a unique identifier for a match pair."""
        block1 = match.block1
        block2 = match.block2

        # Ensure consistent ordering
        if (block1.file_path, block1.start_line) > (
            block2.file_path,
            block2.start_line,
        ):
            block1, block2 = block2, block1

        return f"{block1.file_path}:{block1.start_line}-{block1.end_line}||{block2.file_path}:{block2.start_line}-{block2.end_line}"


class DuplicateAnalysisReport:
    """Generates comprehensive reports of duplicate detection results."""

    def __init__(self, matches: List[DuplicateMatch]):
        self.matches = matches
        self.stats = self._calculate_statistics()

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate analysis statistics."""
        if not self.matches:
            return {"total_matches": 0}

        stats = {
            "total_matches": len(self.matches),
            "by_type": {},
            "high_confidence": 0,
            "avg_similarity": 0.0,
            "files_affected": set(),
            "total_duplicate_lines": 0,
        }

        similarity_sum = 0.0

        for match in self.matches:
            # Count by type
            match_type = match.match_type
            stats["by_type"][match_type] = stats["by_type"].get(match_type, 0) + 1

            # High confidence matches
            if match.confidence > 0.8:
                stats["high_confidence"] += 1

            # Similarity tracking
            similarity_sum += match.similarity_score

            # File tracking
            stats["files_affected"].add(match.block1.file_path)
            stats["files_affected"].add(match.block2.file_path)

            # Line count tracking
            lines1 = match.block1.end_line - match.block1.start_line + 1
            lines2 = match.block2.end_line - match.block2.start_line + 1
            stats["total_duplicate_lines"] += lines1 + lines2

        stats["avg_similarity"] = similarity_sum / len(self.matches)
        stats["files_affected"] = list(stats["files_affected"])

        return stats

    def generate_summary(self) -> str:
        """Generate a summary report."""
        if not self.matches:
            return "No duplicate code detected."

        summary = f"""
Duplicate Code Detection Summary
===============================

Total Matches: {self.stats['total_matches']}
High Confidence Matches: {self.stats['high_confidence']}
Average Similarity Score: {self.stats['avg_similarity']:.2f}
Files Affected: {len(self.stats['files_affected'])}
Total Duplicate Lines: {self.stats['total_duplicate_lines']}

Matches by Type:
"""

        for match_type, count in self.stats["by_type"].items():
            summary += f"  {match_type.capitalize()}: {count}\n"

        return summary

    def generate_detailed_report(self) -> str:
        """Generate a detailed report with all matches."""
        report = self.generate_summary()
        report += "\n\nDetailed Matches:\n" + "=" * 50 + "\n"

        for i, match in enumerate(self.matches[:10], 1):  # Limit to top 10
            report += f"\nMatch #{i} ({match.match_type.capitalize()}):\n"
            report += f"  Similarity: {match.similarity_score:.2f}, Confidence: {match.confidence:.2f}\n"
            report += f"  Block 1: {match.block1.file_path}:{match.block1.start_line}-{match.block1.end_line}\n"
            report += f"  Block 2: {match.block2.file_path}:{match.block2.start_line}-{match.block2.end_line}\n"

            if match.metadata:
                report += f"  Metadata: {match.metadata}\n"

        if len(self.matches) > 10:
            report += f"\n... and {len(self.matches) - 10} more matches."

        return report


def main():
    """Example usage of the duplicate detection system."""
    # This would typically be called by the analysis orchestrator
    sample_blocks = [
        CodeBlock(
            content="def calculate_sum(a, b):\n    return a + b",
            file_path="example1.py",
            start_line=1,
            end_line=2,
        ),
        CodeBlock(
            content="def calculate_sum(x, y):\n    return x + y",
            file_path="example2.py",
            start_line=10,
            end_line=11,
        ),
    ]

    # Initialize composite detector
    detector = CompositeDuplicateDetector()

    # Detect duplicates
    matches = detector.detect_all_duplicates(sample_blocks)

    # Generate report
    report = DuplicateAnalysisReport(matches)
    print(report.generate_detailed_report())


if __name__ == "__main__":
    main()
