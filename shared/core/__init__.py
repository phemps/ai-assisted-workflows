"""Core shared libraries and utilities."""

# Re-export from base for convenience
from .base import (
    CIErrorHandler,
    CIErrorCode,
    CIErrorContext,
    CIModuleBase,
    CIAnalysisModule,
    CIConfigModule,
    ConfigFactory,
    ConfigBase,
    # CLI utilities intentionally not re-exported in this project
    timed_operation,
    time_operation,
    FileSystemUtils,
    atomic_write,
)

# Re-export from utils for convenience
from .utils import (
    validate_target_directory,
    validate_git_repository,
    ValidationError,
    ArchitecturalPatternDetector,
    PlatformDetector,
    CommandExecutor,
    PathUtils,
    DependencyChecker,
    ResultFormatter,
    TechStackDetector,
)

__all__ = [
    # Base exports
    "CIErrorHandler",
    "CIErrorCode",
    "CIErrorContext",
    "CIModuleBase",
    "CIAnalysisModule",
    "CIConfigModule",
    "ConfigFactory",
    "ConfigBase",
    # (CLI utilities removed)
    "timed_operation",
    "time_operation",
    "FileSystemUtils",
    "atomic_write",
    # Utils exports
    "validate_target_directory",
    "validate_git_repository",
    "ValidationError",
    "ArchitecturalPatternDetector",
    "PlatformDetector",
    "CommandExecutor",
    "PathUtils",
    "DependencyChecker",
    "ResultFormatter",
    "TechStackDetector",
]
