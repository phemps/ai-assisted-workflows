#!/usr/bin/env python3
"""
Base utilities for Continuous Improvement Framework
Provides common functionality to eliminate code duplication.
"""

from .error_handler import CIErrorHandler, CIErrorCode, CIErrorContext
from .module_base import CIModuleBase, CIAnalysisModule, CIConfigModule
from .config_factory import (
    ConfigFactory,
    ConfigBase,
    EmbeddingConfig,
    SimilarityConfig,
    RegistryConfig,
    DetectionConfig,
    QualityGateConfig,
    MetricsConfig,
)
from .timing_utils import (
    TimingResult,
    PerformanceTracker,
    get_performance_tracker,
    timed_operation,
    time_operation,
    OperationTimer,
    BatchTimer,
    create_performance_report,
)
from .fs_utils import (
    FileSystemUtils,
    TemporaryDirectory,
    atomic_write,
    DirectoryWatcher,
    process_files_in_batches,
)
from .profiler_base import BaseProfiler, ProfilerConfig, create_profiler_config
from .analyzer_base import BaseAnalyzer, AnalyzerConfig, create_analyzer_config
from .analyzer_registry import AnalyzerRegistry, register_analyzer

__all__ = [
    # Error handling
    "CIErrorHandler",
    "CIErrorCode",
    "CIErrorContext",
    # Base modules
    "CIModuleBase",
    "CIAnalysisModule",
    "CIConfigModule",
    # Configuration factory
    "ConfigFactory",
    "ConfigBase",
    "EmbeddingConfig",
    "SimilarityConfig",
    "RegistryConfig",
    "DetectionConfig",
    "QualityGateConfig",
    "MetricsConfig",
    # (CLI utilities removed: not used in this project)
    # Performance timing
    "TimingResult",
    "PerformanceTracker",
    "get_performance_tracker",
    "timed_operation",
    "time_operation",
    "OperationTimer",
    "BatchTimer",
    "create_performance_report",
    # File system utilities
    "FileSystemUtils",
    "TemporaryDirectory",
    "atomic_write",
    "DirectoryWatcher",
    "process_files_in_batches",
    # Profiler base classes
    "BaseProfiler",
    "ProfilerConfig",
    "create_profiler_config",
    # Analyzer base classes
    "BaseAnalyzer",
    "AnalyzerConfig",
    "create_analyzer_config",
    "AnalyzerRegistry",
    "register_analyzer",
]
