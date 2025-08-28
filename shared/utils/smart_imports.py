#!/usr/bin/env python3
"""
Smart Import System - Production Version
========================================

Universal import system for AI-Assisted Workflows that works across:
- Development environment (shared/)
- Local deployment (.claude/scripts/)
- Global deployment (~/.claude/scripts/)
- Custom deployment (anywhere)

The PACKAGE_ROOT is automatically configured:
- In development: Calculated from file location
- After deployment: Set by install.sh during installation
"""

import sys
import importlib
from pathlib import Path
from typing import Any, Optional, Dict, Tuple, Type

# Package configuration
# Default to development path - this gets replaced during installation
# In development: this is the actual path to shared/
# After deployment: install.sh replaces this with the deployment path
PACKAGE_ROOT = Path(__file__).resolve().parents[1]  # Default: shared/
PACKAGE_NAME = "shared"

# Ensure package root is in sys.path (only add if not already there)
package_root_str = str(PACKAGE_ROOT)
if package_root_str not in sys.path:
    sys.path.insert(0, package_root_str)

# Also add parent directory to support imports
parent_root = str(PACKAGE_ROOT.parent)
if parent_root not in sys.path:
    sys.path.insert(0, parent_root)

# Cache for imported modules to avoid repeated imports
_import_cache: Dict[str, Any] = {}


def get_package_info() -> Dict[str, Any]:
    """Get information about the current package configuration."""
    return {
        "package_root": str(PACKAGE_ROOT),
        "package_name": PACKAGE_NAME,
        "python_path": sys.path[:5],  # First 5 entries
    }


def _try_import(module_paths: list[str], item_name: Optional[str] = None) -> Any:
    """
    Try multiple import paths until one succeeds.

    Args:
        module_paths: List of module paths to try
        item_name: Optional specific item to import from module

    Returns:
        The imported module or item

    Raises:
        ImportError: If all import attempts fail
    """
    errors = []
    for module_path in module_paths:
        try:
            module = importlib.import_module(module_path)
            if item_name:
                return getattr(module, item_name)
            return module
        except (ImportError, AttributeError) as e:
            errors.append(f"{module_path}: {e}")
            continue

    raise ImportError(f"Failed to import from any of: {module_paths}. Errors: {errors}")


# ============================================================================
# Core Base Classes
# ============================================================================


def import_analyzer_base() -> Tuple[Type, Type]:
    """Import BaseAnalyzer and AnalyzerConfig from the base module."""
    cache_key = "analyzer_base"
    if cache_key not in _import_cache:
        try:
            # Try direct import first (for deployed environments)
            module = importlib.import_module("core.base.analyzer_base")
        except ImportError:
            # In development or different structure
            module = importlib.import_module("shared.core.base.analyzer_base")

        BaseAnalyzer = module.BaseAnalyzer
        AnalyzerConfig = module.AnalyzerConfig
        _import_cache[cache_key] = (BaseAnalyzer, AnalyzerConfig)

    return _import_cache[cache_key]


def import_base_analyzer() -> Type:
    """Import just BaseAnalyzer class."""
    return import_analyzer_base()[0]


def import_analyzer_config() -> Type:
    """Import just AnalyzerConfig class."""
    return import_analyzer_base()[1]


def import_profiler_base() -> Tuple[Type, Type]:
    """Import BaseProfiler and ProfilerConfig from the base module."""
    cache_key = "profiler_base"
    if cache_key not in _import_cache:
        try:
            # Try direct import first (for deployed environments)
            module = importlib.import_module("core.base.profiler_base")
        except ImportError:
            # In development or different structure
            module = importlib.import_module("shared.core.base.profiler_base")

        BaseProfiler = module.BaseProfiler
        ProfilerConfig = module.ProfilerConfig
        _import_cache[cache_key] = (BaseProfiler, ProfilerConfig)

    return _import_cache[cache_key]


# ============================================================================
# Utility Modules
# ============================================================================


def import_output_formatter() -> Any:
    """Import output formatter utilities."""
    cache_key = "output_formatter"
    if cache_key not in _import_cache:
        module = _try_import(
            ["core.utils.output_formatter", "shared.core.utils.output_formatter"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_tech_stack_detector() -> Any:
    """Import tech stack detector."""
    cache_key = "tech_stack_detector"
    if cache_key not in _import_cache:
        module = _try_import(
            ["core.utils.tech_stack_detector", "shared.core.utils.tech_stack_detector"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_file_utils() -> Any:
    """Import file utilities (redirected to cross_platform)."""
    cache_key = "file_utils"
    if cache_key not in _import_cache:
        # file_utils was renamed to cross_platform, so redirect
        module = _try_import(
            ["core.utils.cross_platform", "shared.core.utils.cross_platform"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


# ============================================================================
# CI/CD Components
# ============================================================================


def import_chromadb_storage() -> Any:
    """Import ChromaDB storage module."""
    cache_key = "chromadb_storage"
    if cache_key not in _import_cache:
        module = _try_import(
            ["ci.core.chromadb_storage", "shared.ci.core.chromadb_storage"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_chromadb_indexer() -> Type:
    """Import ChromaDBIndexer class."""
    cache_key = "chromadb_indexer"
    if cache_key not in _import_cache:
        module = _try_import(
            ["ci.core.chromadb_indexer", "shared.ci.core.chromadb_indexer"]
        )
        _import_cache[cache_key] = module.ChromaDBIndexer
    return _import_cache[cache_key]


def import_embedding_engine() -> Any:
    """Import embedding engine module."""
    cache_key = "embedding_engine"
    if cache_key not in _import_cache:
        module = _try_import(
            ["ci.core.embedding_engine", "shared.ci.core.embedding_engine"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_semantic_duplicate_detector() -> Any:
    """Import semantic duplicate detector module."""
    cache_key = "semantic_duplicate_detector"
    if cache_key not in _import_cache:
        module = _try_import(
            [
                "ci.core.semantic_duplicate_detector",
                "shared.ci.core.semantic_duplicate_detector",
            ]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_symbol_extractor() -> Any:
    """Import symbol extractor module."""
    cache_key = "symbol_extractor"
    if cache_key not in _import_cache:
        module = _try_import(
            [
                "ci.integration.symbol_extractor",
                "shared.ci.integration.symbol_extractor",
            ]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_lsp_symbol_extractor() -> Any:
    """Import LSP symbol extractor module."""
    cache_key = "lsp_symbol_extractor"
    if cache_key not in _import_cache:
        module = _try_import(
            ["ci.core.lsp_symbol_extractor", "shared.ci.core.lsp_symbol_extractor"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_decision_matrix() -> Any:
    """Import decision matrix module."""
    cache_key = "decision_matrix"
    if cache_key not in _import_cache:
        module = _try_import(
            ["ci.workflows.decision_matrix", "shared.ci.workflows.decision_matrix"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_codebase_search() -> Any:
    """Import codebase search module."""
    cache_key = "codebase_search"
    if cache_key not in _import_cache:
        module = _try_import(
            ["ci.tools.codebase_search", "shared.ci.tools.codebase_search"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_orchestration_bridge() -> Any:
    """Import orchestration bridge module."""
    cache_key = "orchestration_bridge"
    if cache_key not in _import_cache:
        module = _try_import(
            [
                "ci.integration.orchestration_bridge",
                "shared.ci.integration.orchestration_bridge",
            ]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


# ============================================================================
# Analyzer Modules
# ============================================================================


def import_security_analyzer(name: str) -> Type:
    """Import a specific security analyzer by name."""
    cache_key = f"security_{name}"
    if cache_key not in _import_cache:
        module = _try_import(
            [f"analyzers.security.{name}", f"shared.analyzers.security.{name}"]
        )
        # Most analyzers have a class with similar naming pattern
        class_name = "".join(word.capitalize() for word in name.split("_"))
        if hasattr(module, class_name):
            _import_cache[cache_key] = getattr(module, class_name)
        else:
            _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_quality_analyzer(name: str) -> Type:
    """Import a specific quality analyzer by name."""
    cache_key = f"quality_{name}"
    if cache_key not in _import_cache:
        module = _try_import(
            [f"analyzers.quality.{name}", f"shared.analyzers.quality.{name}"]
        )
        class_name = "".join(word.capitalize() for word in name.split("_"))
        if hasattr(module, class_name):
            _import_cache[cache_key] = getattr(module, class_name)
        else:
            _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_performance_analyzer(name: str) -> Type:
    """Import a specific performance analyzer by name."""
    cache_key = f"performance_{name}"
    if cache_key not in _import_cache:
        module = _try_import(
            [f"analyzers.performance.{name}", f"shared.analyzers.performance.{name}"]
        )
        class_name = "".join(word.capitalize() for word in name.split("_"))
        if hasattr(module, class_name):
            _import_cache[cache_key] = getattr(module, class_name)
        else:
            _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_architecture_analyzer(name: str) -> Type:
    """Import a specific architecture analyzer by name."""
    cache_key = f"architecture_{name}"
    if cache_key not in _import_cache:
        module = _try_import(
            [f"analyzers.architecture.{name}", f"shared.analyzers.architecture.{name}"]
        )
        class_name = "".join(word.capitalize() for word in name.split("_"))
        if hasattr(module, class_name):
            _import_cache[cache_key] = getattr(module, class_name)
        else:
            _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_root_cause_analyzer(name: str) -> Type:
    """Import a specific root cause analyzer by name."""
    cache_key = f"root_cause_{name}"
    if cache_key not in _import_cache:
        module = _try_import(
            [f"analyzers.root_cause.{name}", f"shared.analyzers.root_cause.{name}"]
        )
        class_name = "".join(word.capitalize() for word in name.split("_"))
        if hasattr(module, class_name):
            _import_cache[cache_key] = getattr(module, class_name)
        else:
            _import_cache[cache_key] = module
    return _import_cache[cache_key]


# ============================================================================
# Core Base Module Components
# ============================================================================


def import_cli_utils() -> Any:
    """Import CLI utilities from core.base.cli_utils."""
    cache_key = "cli_utils"
    if cache_key not in _import_cache:
        module = _try_import(["core.base.cli_utils", "shared.core.base.cli_utils"])
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_base_module() -> Any:
    """Import base module components from core.base."""
    cache_key = "base_module"
    if cache_key not in _import_cache:
        module = _try_import(["core.base", "shared.core.base"])
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_timing_utils() -> Any:
    """Import timing utilities from core.base.timing_utils."""
    cache_key = "timing_utils"
    if cache_key not in _import_cache:
        module = _try_import(
            ["core.base.timing_utils", "shared.core.base.timing_utils"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_error_handler() -> Any:
    """Import error handler from core.base.error_handler."""
    cache_key = "error_handler"
    if cache_key not in _import_cache:
        module = _try_import(
            ["core.base.error_handler", "shared.core.base.error_handler"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


def import_cross_platform() -> Any:
    """Import cross platform utilities from core.utils.cross_platform."""
    cache_key = "cross_platform"
    if cache_key not in _import_cache:
        module = _try_import(
            ["core.utils.cross_platform", "shared.core.utils.cross_platform"]
        )
        _import_cache[cache_key] = module
    return _import_cache[cache_key]


# ============================================================================
# Utility Functions
# ============================================================================


def clear_import_cache():
    """Clear the import cache (useful for testing)."""
    global _import_cache
    _import_cache = {}


def setup_imports():
    """
    Setup function to ensure all paths are configured.
    This is called automatically on module import but can be called manually.
    """
    # Paths are already set up at module level
    pass


# For direct module execution (testing)
if __name__ == "__main__":
    import json

    info = get_package_info()
    print("Smart Import System Configuration (Production)")
    print("=" * 60)
    print(json.dumps(info, indent=2))

    # Test some imports
    print("\nTesting imports...")
    try:
        BaseAnalyzer, AnalyzerConfig = import_analyzer_base()
        print(f"✓ BaseAnalyzer imported from: {BaseAnalyzer.__module__}")
    except ImportError as e:
        print(f"✗ Failed to import BaseAnalyzer: {e}")
