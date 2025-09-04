#!/usr/bin/env python3

from typing import Dict, Any, List, Optional

from core.base.analyzer_registry import AnalyzerRegistry, register_analyzer
from core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig


@register_analyzer("test:dummy")
class DummyAnalyzer(BaseAnalyzer):
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        super().__init__("test", config or AnalyzerConfig())

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        return []

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        return {"name": "Dummy"}


def test_registry_get_and_create():
    cls = AnalyzerRegistry.get("test:dummy")
    assert issubclass(cls, BaseAnalyzer)
    inst = AnalyzerRegistry.create("test:dummy")
    assert isinstance(inst, DummyAnalyzer)
