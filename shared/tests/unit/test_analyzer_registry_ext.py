#!/usr/bin/env python3

import pytest
from core.base import AnalyzerRegistry, BaseAnalyzer, AnalyzerConfig


class DummyAnalyzerA(BaseAnalyzer):
    def __init__(self, config: AnalyzerConfig | None = None):
        super().__init__("dummy_a", config)

    def analyze_target(self, target_path: str):  # pragma: no cover - trivial
        return []

    def get_analyzer_metadata(self):  # pragma: no cover - trivial
        return {"name": "A"}


class DummyAnalyzerB(BaseAnalyzer):
    def __init__(self, config: AnalyzerConfig | None = None):
        super().__init__("dummy_b", config)

    def analyze_target(self, target_path: str):  # pragma: no cover - trivial
        return []

    def get_analyzer_metadata(self):  # pragma: no cover - trivial
        return {"name": "B"}


def test_registry_duplicate_and_missing_handling():
    # Clean state per test: use unique keys
    AnalyzerRegistry.register("test:dummy-a", DummyAnalyzerA)
    # Idempotent: re-register same class should be no-op
    AnalyzerRegistry.register("test:dummy-a", DummyAnalyzerA)

    # Registering different class under same name should raise
    with pytest.raises(ValueError):
        AnalyzerRegistry.register("test:dummy-a", DummyAnalyzerB)

    # Missing key access
    with pytest.raises(KeyError):
        AnalyzerRegistry.get("test:does-not-exist")

    # Successful create
    inst = AnalyzerRegistry.create("test:dummy-a")
    assert isinstance(inst, DummyAnalyzerA)

    # Invalid name
    with pytest.raises(ValueError):
        AnalyzerRegistry.register("", DummyAnalyzerA)
