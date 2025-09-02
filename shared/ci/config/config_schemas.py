#!/usr/bin/env python3
"""
Unified Configuration Schemas for AI-Assisted Workflows

Simple dataclass-based configuration models that follow the existing
codebase patterns. Provides centralized configuration management without
introducing new dependencies like Pydantic.

Part of Phase 5: Configuration Management for AI-Assisted Workflows.

Key Features:
- Simple @dataclass configurations following existing patterns
- Environment variable support with os.getenv()
- __post_init__ validation following existing conventions
- Aggregation of existing component configurations
- No new dependencies - uses Python standard library
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from enum import Enum
from dataclasses import dataclass, field, asdict

# Setup import paths and import existing configs
try:
    from utils import path_resolver  # noqa: F401

    # Import existing configurations that already use @dataclass
    from ci.core.chromadb_storage import ChromaDBConfig
    from ci.core.lsp_symbol_extractor import SymbolExtractionConfig
    from ci.core.memory_manager import MemoryConfig
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


class EnvironmentType(Enum):
    """Environment types for configuration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class PerformanceConfig:
    """Configuration for async processing and performance optimization."""

    # Async processing settings
    max_workers: int = 4
    batch_size: int = 50
    processing_timeout: int = 300  # seconds
    enable_concurrent_processing: bool = True

    # Memory optimization
    enable_memory_monitoring: bool = True
    memory_limit_mb: float = 1000.0
    enable_auto_throttling: bool = True

    # Performance tuning
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    enable_batch_optimization: bool = True

    def __post_init__(self):
        """Load from environment and validate."""
        # Load from environment variables
        self.max_workers = int(os.getenv("CI_PERF_MAX_WORKERS", self.max_workers))
        self.batch_size = int(os.getenv("CI_PERF_BATCH_SIZE", self.batch_size))
        self.memory_limit_mb = float(
            os.getenv("CI_PERF_MEMORY_LIMIT_MB", self.memory_limit_mb)
        )

        # Validate settings
        if self.max_workers < 1 or self.max_workers > 20:
            raise ValueError("max_workers must be between 1 and 20")
        if self.batch_size < 1 or self.batch_size > 1000:
            raise ValueError("batch_size must be between 1 and 1000")
        if self.memory_limit_mb < 100.0:
            raise ValueError("memory_limit_mb must be at least 100.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ExpertAgentConfig:
    """Configuration for expert agent routing and execution."""

    # Agent settings
    enable_expert_routing: bool = True
    default_expert_timeout: float = 300.0
    enable_batch_processing: bool = True
    max_findings_per_batch: int = 50

    # Language-specific experts
    python_expert_enabled: bool = True
    typescript_expert_enabled: bool = True
    cto_expert_enabled: bool = True

    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 2.0

    def __post_init__(self):
        """Load from environment and validate."""
        # Load from environment variables
        self.enable_expert_routing = (
            os.getenv(
                "CI_EXPERT_ROUTING_ENABLED", str(self.enable_expert_routing)
            ).lower()
            == "true"
        )
        self.max_findings_per_batch = int(
            os.getenv("CI_EXPERT_MAX_FINDINGS", self.max_findings_per_batch)
        )

        # Validate settings
        if self.default_expert_timeout < 30.0 or self.default_expert_timeout > 1800.0:
            raise ValueError(
                "default_expert_timeout must be between 30 and 1800 seconds"
            )
        if self.max_findings_per_batch < 10 or self.max_findings_per_batch > 200:
            raise ValueError("max_findings_per_batch must be between 10 and 200")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AnalysisConfig:
    """Configuration for code analysis and duplicate detection."""

    # Analysis modes
    analysis_mode: Literal["comprehensive", "targeted", "fast"] = "targeted"
    enable_incremental_analysis: bool = True
    enable_duplicate_detection: bool = True
    enable_semantic_analysis: bool = True

    # Quality gates
    enable_quality_gates: bool = True
    max_false_positive_rate: float = 0.1
    min_confidence_threshold: float = 0.8

    # Performance settings
    max_files_per_analysis: int = 1000
    analysis_timeout_seconds: int = 600

    def __post_init__(self):
        """Load from environment and validate."""
        # Load from environment variables
        mode_env = os.getenv("CI_ANALYSIS_MODE", self.analysis_mode)
        if mode_env in ["comprehensive", "targeted", "fast"]:
            self.analysis_mode = mode_env

        # Validate settings
        if not (0.0 <= self.max_false_positive_rate <= 1.0):
            raise ValueError("max_false_positive_rate must be between 0.0 and 1.0")
        if not (0.0 <= self.min_confidence_threshold <= 1.0):
            raise ValueError("min_confidence_threshold must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MonitoringConfig:
    """Configuration for system monitoring and metrics."""

    # Basic monitoring
    enable_monitoring: bool = True
    metrics_collection_interval: int = 60  # seconds
    enable_performance_tracking: bool = True

    # Logging
    log_level: str = "INFO"
    enable_debug_logging: bool = False

    def __post_init__(self):
        """Load from environment and validate."""
        # Load from environment variables
        log_level_env = os.getenv("CI_LOG_LEVEL", self.log_level)
        if log_level_env in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            self.log_level = log_level_env

        self.enable_debug_logging = os.getenv("CI_DEBUG", "false").lower() == "true"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CISystemConfig:
    """
    Main configuration for the AI-Assisted Workflows CI System.

    Aggregates all component configurations using existing @dataclass patterns.
    Provides environment variable support and simple validation.
    """

    # Environment settings
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    project_root: Path = field(default_factory=Path.cwd)
    debug_mode: bool = False

    # Component configurations - using existing dataclass configs
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    chromadb: ChromaDBConfig = field(default_factory=ChromaDBConfig)
    symbol_extraction: SymbolExtractionConfig = field(
        default_factory=SymbolExtractionConfig
    )
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    expert_agents: ExpertAgentConfig = field(default_factory=ExpertAgentConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Version and metadata
    version: str = "1.0.0"
    config_source: str = "default"
    last_updated: Optional[str] = None

    def __post_init__(self):
        """Load environment variables and validate configuration."""
        # Load environment settings
        env_str = os.getenv("CI_ENVIRONMENT", self.environment.value)
        try:
            self.environment = EnvironmentType(env_str)
        except ValueError:
            self.environment = EnvironmentType.DEVELOPMENT

        # Resolve project root
        project_root_env = os.getenv("CI_PROJECT_ROOT")
        if project_root_env:
            self.project_root = Path(project_root_env).resolve()
        else:
            self.project_root = self.project_root.resolve()

        # Set debug mode based on environment
        if self.environment == EnvironmentType.PRODUCTION:
            self.debug_mode = False
        elif self.environment == EnvironmentType.TESTING:
            self.debug_mode = True
        else:
            self.debug_mode = os.getenv("CI_DEBUG", "false").lower() == "true"

        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate the complete configuration."""
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")

        # Basic validation - components will validate themselves in their __post_init__
        if not self.version:
            raise ValueError("Configuration version cannot be empty")

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == EnvironmentType.DEVELOPMENT

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == EnvironmentType.PRODUCTION

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == EnvironmentType.TESTING

    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration as dictionary."""
        return self.performance.to_dict()

    def get_thresholds_config(self) -> Dict[str, float]:
        """Get similarity thresholds configuration."""
        return {
            "exact": self.chromadb.exact_match_threshold,
            "high": self.chromadb.high_similarity_threshold,
            "medium": self.chromadb.medium_similarity_threshold,
            "low": self.chromadb.low_similarity_threshold,
        }

    def get_legacy_config(self) -> Dict[str, Any]:
        """Get configuration in legacy format for backward compatibility."""
        return {
            "project": {
                "root": str(self.project_root),
                "environment": self.environment.value,
                "debug": self.debug_mode,
                "analysis": {
                    "mode": self.analysis.analysis_mode,
                    "enable_incremental": self.analysis.enable_incremental_analysis,
                    "max_files": self.analysis.max_files_per_analysis,
                },
                "exclusions": {
                    "directories": getattr(
                        self.symbol_extraction, "exclude_directories", []
                    ),
                    "files": getattr(
                        self.symbol_extraction, "exclude_file_patterns", []
                    ),
                    "patterns": [],
                },
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire configuration to dictionary."""
        return asdict(self)

    def load_from_file(self, config_file: Path):
        """Load configuration from JSON file."""
        if not config_file.exists():
            return

        try:
            import json

            with open(config_file, "r") as f:
                config_data = json.load(f)

            # Update basic settings from file
            if "environment" in config_data:
                self.environment = EnvironmentType(config_data["environment"])
            if "debug_mode" in config_data:
                self.debug_mode = config_data["debug_mode"]

            # Component configs handle their own loading through __post_init__

        except Exception as e:
            print(
                f"Warning: Failed to load config file {config_file}: {e}",
                file=sys.stderr,
            )


# Configuration validation functions
def validate_config(config: CISystemConfig) -> List[str]:
    """
    Validate configuration and return list of warnings/issues.

    Args:
        config: Configuration to validate

    Returns:
        List of validation warnings (empty if all valid)
    """
    warnings = []

    # Validate project root
    if not config.project_root.exists():
        warnings.append(f"Project root does not exist: {config.project_root}")

    # Validate component configurations
    try:
        # Performance validation
        if config.performance.max_workers < 1:
            warnings.append("Performance max_workers should be at least 1")

        # ChromaDB validation
        thresholds = [
            config.chromadb.low_similarity_threshold,
            config.chromadb.medium_similarity_threshold,
            config.chromadb.high_similarity_threshold,
            config.chromadb.exact_match_threshold,
        ]

        if not (thresholds == sorted(thresholds)):
            warnings.append(
                "ChromaDB similarity thresholds should be in ascending order"
            )

        # Memory validation
        if config.memory.warning_threshold >= config.memory.throttle_threshold:
            warnings.append(
                "Memory warning threshold should be less than throttle threshold"
            )

    except Exception as e:
        warnings.append(f"Configuration validation error: {e}")

    return warnings


def get_environment_config(environment: EnvironmentType) -> Dict[str, Any]:
    """
    Get environment-specific configuration defaults.

    Args:
        environment: Target environment type

    Returns:
        Dictionary of environment-specific settings
    """
    base_config = {"debug_mode": False, "enable_monitoring": True, "log_level": "INFO"}

    if environment == EnvironmentType.DEVELOPMENT:
        return {
            **base_config,
            "debug_mode": True,
            "log_level": "DEBUG",
            "enable_caching": False,  # Fresh data for development
        }
    elif environment == EnvironmentType.TESTING:
        return {
            **base_config,
            "debug_mode": True,
            "log_level": "DEBUG",
            "batch_size": 10,  # Smaller batches for testing
            "processing_timeout": 60,  # Shorter timeouts
        }
    elif environment == EnvironmentType.PRODUCTION:
        return {
            **base_config,
            "debug_mode": False,
            "log_level": "WARNING",
            "enable_caching": True,
            "batch_size": 100,  # Larger batches for efficiency
        }

    return base_config


# Default configuration factory
def create_default_config(
    project_root: Optional[Path] = None,
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT,
) -> CISystemConfig:
    """
    Create a default configuration instance.

    Args:
        project_root: Optional project root path
        environment: Target environment

    Returns:
        Configured CISystemConfig instance
    """
    config = CISystemConfig(
        environment=environment, project_root=project_root or Path.cwd()
    )

    return config
