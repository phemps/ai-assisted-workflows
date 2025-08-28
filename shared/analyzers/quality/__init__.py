"""
Code Quality Analysis Module

This module provides comprehensive code quality analysis tools including:
- Duplicate code detection
- Symbol extraction and comparison
- Pattern classification
- Quality metrics calculation

Part of the AI-Assisted Workflows Analysis Engine (Phase 2).
"""

from .code_duplication_analyzer import (
    CodeBlock,
    DuplicateMatch,
    DuplicationDetector,
    ExactDuplicateDetector,
    StructuralDuplicateDetector,
    SemanticDuplicateDetector,
    CompositeDuplicateDetector,
    DuplicateAnalysisReport,
)

from .pattern_classifier import (
    PatternType,
    PatternSeverity,
    PatternMatch,
    PatternDetector,
    AntiPatternDetector,
    CodeSmellDetector,
    SecurityPatternDetector,
    CompositePatternClassifier,
    PatternAnalysisReport,
)

from .result_aggregator import (
    AnalysisType,
    Priority,
    AnalysisResult,
    FileAnalysisSummary,
    ProjectAnalysisSummary,
    ResultConverter,
    ResultCorrelator,
    AnalysisAggregator,
    ComprehensiveAnalysisReport,
)


__all__ = [
    "CodeBlock",
    "DuplicateMatch",
    "DuplicationDetector",
    "ExactDuplicateDetector",
    "StructuralDuplicateDetector",
    "SemanticDuplicateDetector",
    "CompositeDuplicateDetector",
    "DuplicateAnalysisReport",
    "PatternType",
    "PatternSeverity",
    "PatternMatch",
    "PatternDetector",
    "AntiPatternDetector",
    "CodeSmellDetector",
    "SecurityPatternDetector",
    "CompositePatternClassifier",
    "PatternAnalysisReport",
    "AnalysisType",
    "Priority",
    "AnalysisResult",
    "FileAnalysisSummary",
    "ProjectAnalysisSummary",
    "ResultConverter",
    "ResultCorrelator",
    "AnalysisAggregator",
    "ComprehensiveAnalysisReport",
]

__version__ = "1.0.0"
