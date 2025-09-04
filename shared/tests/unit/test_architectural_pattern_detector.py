#!/usr/bin/env python3

from pathlib import Path
from core.utils.architectural_pattern_detector import ArchitecturalPatternDetector


def test_singleton_detection_from_config():
    detector = ArchitecturalPatternDetector(
        config_dir=Path("shared/config/patterns").resolve()
    )
    content = (
        "class MySingleton:\n"
        "    _instance = None\n\n"
        "    def __new__(cls, *args, **kwargs):\n"
        "        if cls._instance is None:\n"
        "            cls._instance = super().__new__(cls)\n"
        "        return cls._instance\n"
    )
    matches = detector.detect_patterns(content, "example.py", "python")
    assert any(m.pattern_name == "singleton" and m.confidence >= 0.7 for m in matches)
