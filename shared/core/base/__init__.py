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
from .cli_utils import CLIBase, OutputHandler, create_standard_cli, run_cli_tool
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
    # CLI utilities
    "CLIBase",
    "OutputHandler",
    "create_standard_cli",
    "run_cli_tool",
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
]
