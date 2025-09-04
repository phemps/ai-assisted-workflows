#!/usr/bin/env python3
"""
Lightweight analyzer registry to map names to analyzer classes.

Purpose: Allow orchestration to construct analyzers by name without tight coupling.
"""

from __future__ import annotations

from typing import Dict, Optional, Callable, Any

from .analyzer_base import BaseAnalyzer, AnalyzerConfig


class AnalyzerRegistry:
    """In-memory registry of analyzer classes keyed by a unique name."""

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, analyzer_cls: type) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("Analyzer name must be a non-empty string")
        if name in cls._registry:
            raise ValueError(f"Analyzer already registered: {name}")
        cls._registry[name] = analyzer_cls

    @classmethod
    def get(cls, name: str) -> type:
        try:
            return cls._registry[name]
        except KeyError:
            raise KeyError(f"Analyzer not registered: {name}")

    @classmethod
    def create(cls, name: str, config: Optional[AnalyzerConfig] = None) -> BaseAnalyzer:
        analyzer_cls = cls.get(name)
        # Analyzer classes in this project accept (config: Optional[AnalyzerConfig])
        return analyzer_cls(config=config)  # type: ignore[call-arg]


def register_analyzer(name: str) -> Callable[[Any], Any]:
    """Class decorator to register an analyzer under a unique name."""

    def _decorator(analyzer_cls: Any) -> Any:
        AnalyzerRegistry.register(name, analyzer_cls)
        return analyzer_cls

    return _decorator
