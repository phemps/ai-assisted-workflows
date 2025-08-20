#!/usr/bin/env python3
"""
CI System Exception Hierarchy
"""

from typing import Optional, Dict, Any


class CISystemError(Exception):
    """Base exception for CI system failures.

    Preserves exit codes for compatibility with existing fail-fast behavior
    while enabling proper exception handling and testing.
    """

    def __init__(
        self, message: str, exit_code: int = 1, context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.exit_code = exit_code
        self.context = context or {}
        self.message = message

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}: {v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class CIConfigurationError(CISystemError):
    """Configuration-related CI failures."""

    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, exit_code=8, context=context)
        self.config_file = config_file


class CIDependencyError(CISystemError):
    """Dependency-related CI failures."""

    def __init__(
        self,
        message: str,
        missing_dependency: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, exit_code=2, context=context)
        self.missing_dependency = missing_dependency


class CIAnalysisError(CISystemError):
    """Analysis-related CI failures."""

    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, exit_code=1, context=context)
        self.analysis_type = analysis_type


class CISymbolExtractionError(CIAnalysisError):
    """Symbol extraction specific failures."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, analysis_type="symbol_extraction", context=context)
        self.file_path = file_path


class CIEmbeddingError(CIAnalysisError):
    """Embedding generation specific failures."""

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, analysis_type="embedding_generation", context=context)
        self.model_name = model_name


class CISimilarityError(CIAnalysisError):
    """Similarity detection specific failures."""

    def __init__(
        self,
        message: str,
        similarity_threshold: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, analysis_type="similarity_detection", context=context)
        self.similarity_threshold = similarity_threshold
