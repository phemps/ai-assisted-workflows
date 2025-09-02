#!/usr/bin/env python3
"""
Unified Configuration Manager for AI-Assisted Workflows

Central configuration management system that provides:
- Single source of truth for all CI system configurations using @dataclass patterns
- Environment-specific configuration loading
- Runtime configuration updates
- Simple validation and error reporting
- Legacy configuration compatibility
- Thread-safe configuration access

Part of Phase 5: Configuration Management for AI-Assisted Workflows.

Key Features:
- Simple dataclass-based configuration (no Pydantic dependencies)
- Environment variable integration with os.getenv()
- Configuration caching and change tracking
- Backward compatibility with existing systems
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from functools import lru_cache
import logging

# Setup import paths
try:
    from utils import path_resolver  # noqa: F401
    from ci.config.config_schemas import (
        CISystemConfig,
        EnvironmentType,
        validate_config,
        get_environment_config,
        create_default_config,
    )
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""

    pass


@contextmanager
def config_update_context():
    """Context manager for atomic configuration updates."""
    yield


class CIConfigManager:
    """
    Configuration manager for the CI system.

    Provides centralized configuration management using simple dataclass patterns.
    Thread-safe with basic caching and change tracking.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        environment: EnvironmentType = EnvironmentType.DEVELOPMENT,
        enable_validation: bool = True,
        enable_change_tracking: bool = False,
        config_file_name: str = "ci_config.json",
    ):
        """
        Initialize the configuration manager.

        Args:
            project_root: Root directory for the project
            environment: Target environment type
            enable_validation: Enable configuration validation
            enable_change_tracking: Enable change tracking
            config_file_name: Name of the config file
        """
        self._project_root = Path(project_root or Path.cwd()).resolve()
        self._environment = environment
        self._enable_validation = enable_validation
        self._enable_change_tracking = enable_change_tracking
        self._config_file_name = config_file_name

        # Thread safety
        self._lock = threading.RLock()
        self._config_cache = {}
        self._last_update = 0.0

        # Change tracking
        self._change_history: List[Dict[str, Any]] = []
        self._max_history_size = 100

        # Initialize configuration
        self.config = self._load_configuration()

        logger.info(
            f"Configuration manager initialized for {self._environment.value} environment"
        )

    def _load_configuration(self) -> CISystemConfig:
        """Load configuration from file or create default."""
        config_file = self._project_root / self._config_file_name

        try:
            # Create default configuration
            config = create_default_config(
                project_root=self._project_root, environment=self._environment
            )

            # Load from file if exists
            if config_file.exists():
                config.load_from_file(config_file)
                logger.info(f"Loaded configuration from {config_file}")
            else:
                logger.info("Using default configuration (no config file found)")

            # Validate if enabled
            if self._enable_validation:
                warnings = validate_config(config)
                if warnings:
                    logger.warning("Configuration validation warnings:")
                    for warning in warnings:
                        logger.warning(f"  - {warning}")

            return config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fall back to basic default config
            return CISystemConfig(
                environment=self._environment, project_root=self._project_root
            )

    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key path.

        Args:
            key_path: Dot-separated path (e.g., 'performance.max_workers')
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        with self._lock:
            try:
                value = self.config
                for key in key_path.split("."):
                    value = getattr(value, key)
                return value
            except (AttributeError, KeyError):
                return default

    @lru_cache(maxsize=128)
    def get_cached_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get cached configuration value.

        Args:
            key_path: Dot-separated path
            default: Default value if not found

        Returns:
            Cached configuration value or default
        """
        # Clear cache if config was updated
        current_time = time.time()
        if current_time - self._last_update > 300:  # 5 minutes cache TTL
            self.get_cached_config_value.cache_clear()

        return self.get_config_value(key_path, default)

    def update_config_value(self, key_path: str, value: Any) -> bool:
        """
        Update configuration value by key path.

        Args:
            key_path: Dot-separated path
            value: New value to set

        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Navigate to parent object
                config_obj = self.config
                keys = key_path.split(".")

                for key in keys[:-1]:
                    config_obj = getattr(config_obj, key)

                # Get old value for change tracking
                old_value = getattr(config_obj, keys[-1], None)

                # Set new value
                setattr(config_obj, keys[-1], value)

                # Track change if enabled
                if self._enable_change_tracking:
                    self._track_change(key_path, old_value, value)

                # Clear caches
                self.get_cached_config_value.cache_clear()
                self._last_update = time.time()

                logger.debug(f"Updated config {key_path}: {old_value} -> {value}")
                return True

            except (AttributeError, TypeError) as e:
                logger.error(f"Failed to update config {key_path}: {e}")
                return False

    def _track_change(self, key_path: str, old_value: Any, new_value: Any):
        """Track configuration changes."""
        change_event = {
            "timestamp": time.time(),
            "section": key_path,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "environment": self._environment.value,
        }

        self._change_history.append(change_event)

        # Limit history size
        if len(self._change_history) > self._max_history_size:
            self._change_history = self._change_history[-self._max_history_size :]

    def get_change_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent configuration changes."""
        with self._lock:
            return self._change_history[-limit:]

    def validate_current_config(self) -> List[str]:
        """
        Validate current configuration.

        Returns:
            List of validation warnings
        """
        with self._lock:
            return validate_config(self.config)

    def reload_configuration(self) -> bool:
        """
        Reload configuration from file.

        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                self.config = self._load_configuration()

                # Clear caches
                self.get_cached_config_value.cache_clear()
                self._last_update = time.time()

                logger.info("Configuration reloaded successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")
                return False

    def save_configuration(self, config_file: Optional[Path] = None) -> bool:
        """
        Save current configuration to file.

        Args:
            config_file: Optional path to save to

        Returns:
            True if successful, False otherwise
        """
        if config_file is None:
            config_file = self._project_root / self._config_file_name

        with self._lock:
            try:
                config_dict = self.config.to_dict()

                # Convert Path objects to strings for JSON serialization
                def convert_paths(obj):
                    if isinstance(obj, Path):
                        return str(obj)
                    elif isinstance(obj, dict):
                        return {k: convert_paths(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_paths(v) for v in obj]
                    return obj

                config_dict = convert_paths(config_dict)

                # Ensure parent directory exists
                config_file.parent.mkdir(parents=True, exist_ok=True)

                # Save to file
                with open(config_file, "w") as f:
                    json.dump(config_dict, f, indent=2, sort_keys=True)

                logger.info(f"Configuration saved to {config_file}")
                return True

            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
                return False

    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration as dictionary."""
        return self.config.get_performance_config()

    def get_legacy_config(self) -> Dict[str, Any]:
        """Get configuration in legacy format for backward compatibility."""
        return self.config.get_legacy_config()

    def get_environment_defaults(self) -> Dict[str, Any]:
        """Get environment-specific defaults."""
        return get_environment_config(self._environment)

    def get_status(self) -> Dict[str, Any]:
        """
        Get configuration manager status.

        Returns:
            Status information dictionary
        """
        with self._lock:
            return {
                "project_root": str(self._project_root),
                "environment": self._environment.value,
                "validation_enabled": self._enable_validation,
                "change_tracking_enabled": self._enable_change_tracking,
                "config_file": self._config_file_name,
                "last_update": self._last_update,
                "change_history_size": len(self._change_history),
                "cache_size": self.get_cached_config_value.cache_info().currsize
                if hasattr(self.get_cached_config_value, "cache_info")
                else 0,
                "version": self.config.version,
            }


# Global configuration manager instance
_global_config_manager: Optional[CIConfigManager] = None
_global_config_lock = threading.Lock()


def get_config_manager(
    project_root: Optional[Path] = None,
    environment: Optional[EnvironmentType] = None,
    force_recreate: bool = False,
) -> CIConfigManager:
    """
    Get or create the global configuration manager instance.

    Args:
        project_root: Project root directory
        environment: Environment type
        force_recreate: Force recreation of the manager

    Returns:
        Global configuration manager instance
    """
    global _global_config_manager

    with _global_config_lock:
        if _global_config_manager is None or force_recreate:
            # Determine environment
            if environment is None:
                env_str = os.getenv("CI_ENVIRONMENT", "development")
                try:
                    environment = EnvironmentType(env_str)
                except ValueError:
                    environment = EnvironmentType.DEVELOPMENT

            _global_config_manager = CIConfigManager(
                project_root=project_root,
                environment=environment,
                enable_validation=True,
                enable_change_tracking=True,
            )

        return _global_config_manager


def reset_config_manager():
    """Reset the global configuration manager (for testing)."""
    global _global_config_manager
    with _global_config_lock:
        _global_config_manager = None


# Convenience functions for common configuration access
def get_performance_settings() -> Dict[str, Any]:
    """Get performance configuration settings."""
    manager = get_config_manager()
    return manager.get_performance_config()


def get_chromadb_settings() -> Dict[str, Any]:
    """Get ChromaDB configuration settings."""
    manager = get_config_manager()
    return {
        "collection_name": manager.config.chromadb.collection_name,
        "persist_directory": str(manager.config.chromadb.persist_directory),
        "batch_size": manager.config.chromadb.batch_size,
        "thresholds": manager.config.get_thresholds_config(),
    }


def get_memory_settings() -> Dict[str, Any]:
    """Get memory management configuration settings."""
    manager = get_config_manager()
    return {
        "warning_threshold": manager.config.memory.warning_threshold,
        "throttle_threshold": manager.config.memory.throttle_threshold,
        "critical_threshold": manager.config.memory.critical_threshold,
        "enable_auto_gc": manager.config.memory.enable_auto_gc,
    }


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    manager = get_config_manager()
    return manager.config.debug_mode


def get_project_root() -> Path:
    """Get configured project root path."""
    manager = get_config_manager()
    return manager.config.project_root


if __name__ == "__main__":
    # Basic test when run directly
    manager = CIConfigManager(environment=EnvironmentType.TESTING)

    print("Configuration Manager Test")
    print("=" * 40)

    # Test basic functionality
    status = manager.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")

    # Test configuration access
    print("\nConfiguration Values:")
    print(f"Max workers: {manager.get_config_value('performance.max_workers')}")
    print(f"Batch size: {manager.get_config_value('performance.batch_size')}")
    print(f"Debug mode: {manager.config.debug_mode}")

    # Test validation
    warnings = manager.validate_current_config()
    if warnings:
        print("\nValidation Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✅ Configuration validation passed")

    print("\n✅ Configuration manager test completed")
