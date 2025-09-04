#!/usr/bin/env python3

from core.base import AnalyzerRegistry
import core.base.registry_bootstrap  # noqa: F401 - side-effect imports register analyzers


def test_bootstrap_registers_some_analyzers():
    # Spot-check a few keys across categories
    for key in [
        "security:detect_secrets",
        "security:semgrep",
        "quality:lizard",
        "architecture:dependency",
        "performance:frontend",
        "root_cause:error_patterns",
    ]:
        cls = AnalyzerRegistry.get(key)
        assert cls is not None
