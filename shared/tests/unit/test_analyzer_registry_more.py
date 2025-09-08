#!/usr/bin/env python3

from core.base import AnalyzerRegistry, BaseAnalyzer, AnalyzerConfig


class DummyAnalyzerExtra(BaseAnalyzer):
    def __init__(
        self, config: AnalyzerConfig | None = None, *, extra: str | None = None
    ):
        super().__init__("dummy_extra", config)
        self.extra = extra

    def analyze_target(self, target_path: str):  # pragma: no cover - trivial
        return []

    def get_analyzer_metadata(self):  # pragma: no cover - trivial
        return {"name": "dummy_extra", "extra": self.extra}


def test_create_passes_kwargs_through():
    name = "test:dummy-extra-kwargs"
    AnalyzerRegistry.register(name, DummyAnalyzerExtra)
    inst = AnalyzerRegistry.create(name, extra="value42")
    assert isinstance(inst, DummyAnalyzerExtra)
    assert inst.extra == "value42"
