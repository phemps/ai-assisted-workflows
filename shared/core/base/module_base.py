#!/usr/bin/env python3
"""
Base Module Class for Continuous Improvement Framework
Eliminates duplication of import setup and path management patterns.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .error_handler import CIErrorHandler, CIErrorContext


class CIModuleBase:
    """Base class for all CI framework modules with common setup functionality."""

    def __init__(self, module_name: str, project_root: Optional[str] = None):
        self.module_name = module_name
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.logger = None

        # Setup common paths and imports
        self._setup_paths()
        self._setup_logging()
        self._import_common_utilities()

    def _setup_paths(self) -> None:
        """Setup sys.path for utility imports."""
        script_dir = Path(__file__).parent.parent.parent
        utils_path = script_dir / "utils"

        if str(utils_path) not in sys.path:
            sys.path.insert(0, str(utils_path))

    def _setup_logging(self) -> None:
        """Setup module-specific logging."""
        self.logger = logging.getLogger(f"ci.{self.module_name}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"%(asctime)s - {self.module_name} - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _import_common_utilities(self) -> None:
        """Import commonly used utilities with error handling."""
        with CIErrorContext("importing common utilities", self.module_name):
            try:
                # Import common utilities that are used across modules
                global ResultFormatter, AnalysisResult, TechStackDetector, PlatformDetector
                global CrossPlatformUtils, OutputFormatter

                from shared.core.utils.output_formatter import (
                    ResultFormatter,
                    AnalysisResult,
                )
                from shared.core.utils.tech_stack_detector import TechStackDetector

                try:
                    from shared.core.utils.cross_platform import (
                        PlatformDetector,
                        CrossPlatformUtils,
                    )
                except ImportError:
                    # Platform utilities may not be available in all environments
                    PlatformDetector = None
                    CrossPlatformUtils = None
                    self.logger.warning("Platform utilities not available")

                self.ResultFormatter = ResultFormatter
                self.AnalysisResult = AnalysisResult
                self.TechStackDetector = TechStackDetector
                self.PlatformDetector = PlatformDetector
                self.CrossPlatformUtils = CrossPlatformUtils

            except ImportError as e:
                CIErrorHandler.import_error("common utilities", e)

    def get_config_path(self, config_name: str) -> Path:
        """Get path to configuration file."""
        return self.project_root / ".ci-registry" / config_name

    def get_cache_path(self, cache_name: str) -> Path:
        """Get path to cache file."""
        cache_dir = self.project_root / ".cache" / "ci-framework"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / cache_name

    def get_output_path(self, output_name: str) -> Path:
        """Get path to output file."""
        output_dir = self.project_root / ".ci-output"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / output_name

    def create_result(self, result_type: str = "analysis") -> Any:
        """Create appropriate result object for this module."""
        if result_type == "analysis":
            return self.ResultFormatter.create_performance_result(
                f"{self.module_name}.py", str(self.project_root)
            )
        elif result_type == "architecture":
            return self.ResultFormatter.create_architecture_result(
                f"{self.module_name}.py", str(self.project_root)
            )
        elif result_type == "monitoring":
            return self.ResultFormatter.create_monitoring_result(
                f"{self.module_name}.py", f"CI Framework - {self.module_name}"
            )
        elif result_type == "performance":
            return self.ResultFormatter.create_performance_result(
                f"{self.module_name}.py", str(self.project_root)
            )
        else:
            return self.ResultFormatter.create_performance_result(
                f"{self.module_name}.py", str(self.project_root)
            )

    def validate_threshold(
        self, name: str, value: float, min_val: float = 0.0, max_val: float = 1.0
    ) -> None:
        """Validate threshold values with standard error handling."""
        if not (min_val <= value <= max_val):
            CIErrorHandler.validation_error(
                name, value, f"number between {min_val} and {max_val}"
            )

    def validate_config(self, config: Dict[str, Any], required_keys: list) -> None:
        """Validate configuration dictionary has required keys."""
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            CIErrorHandler.config_error(
                f"Missing required configuration keys: {missing_keys}",
                self.get_config_path("config.json"),
            )

    def safe_file_read(self, file_path: Path, encoding: str = "utf-8") -> str:
        """Safely read file with error handling."""
        try:
            return file_path.read_text(encoding=encoding)
        except PermissionError as e:
            CIErrorHandler.permission_error("read file", file_path, e)
        except FileNotFoundError:
            CIErrorHandler.fatal_error(
                f"Required file not found: {file_path}",
                error_code=4,  # CIErrorCode.FILE_NOT_FOUND
                file_path=file_path,
            )

    def safe_file_write(
        self, file_path: Path, content: str, encoding: str = "utf-8"
    ) -> None:
        """Safely write file with error handling."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=encoding)
        except PermissionError as e:
            CIErrorHandler.permission_error("write file", file_path, e)

    def log_operation(
        self, operation: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log operation with consistent format."""
        message = f"{operation}"
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({detail_str})"
        self.logger.info(message)


class CIAnalysisModule(CIModuleBase):
    """Base class for analysis modules with additional analysis-specific functionality."""

    def __init__(self, module_name: str, project_root: Optional[str] = None):
        super().__init__(module_name, project_root)
        self.analysis_start_time = None

    def start_analysis(self) -> None:
        """Start timing analysis operation."""
        import time

        self.analysis_start_time = time.time()
        self.log_operation("analysis_started")

    def complete_analysis(self, result: Any) -> Any:
        """Complete analysis and set timing metadata."""
        if self.analysis_start_time is not None:
            import time

            execution_time = time.time() - self.analysis_start_time
            result.set_execution_time(self.analysis_start_time)
            self.log_operation(
                "analysis_completed", {"execution_time": f"{execution_time:.3f}s"}
            )
        return result


class CIConfigModule(CIModuleBase):
    """Base class for configuration-related modules."""

    def __init__(self, module_name: str, project_root: Optional[str] = None):
        super().__init__(module_name, project_root)
        self.config_cache = {}

    def load_config(
        self, config_name: str, required_keys: Optional[list] = None
    ) -> Dict[str, Any]:
        """Load and cache configuration with validation."""
        if config_name in self.config_cache:
            return self.config_cache[config_name]

        config_path = self.get_config_path(config_name)

        try:
            import json

            config_content = self.safe_file_read(config_path)
            config = json.loads(config_content)

            if required_keys:
                self.validate_config(config, required_keys)

            self.config_cache[config_name] = config
            self.log_operation(
                "config_loaded", {"config": config_name, "keys": len(config)}
            )
            return config

        except json.JSONDecodeError as e:
            CIErrorHandler.config_error(
                f"Invalid JSON in configuration file: {e}", config_path
            )

    def save_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """Save configuration and update cache."""
        import json

        config_path = self.get_config_path(config_name)
        config_content = json.dumps(config, indent=2)
        self.safe_file_write(config_path, config_content)
        self.config_cache[config_name] = config
        self.log_operation("config_saved", {"config": config_name, "keys": len(config)})
