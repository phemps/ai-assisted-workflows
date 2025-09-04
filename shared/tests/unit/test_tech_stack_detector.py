#!/usr/bin/env python3

from pathlib import Path
from core.utils.tech_stack_detector import TechStackDetector


def test_detect_node_stack_with_package_json(tmp_path: Path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    detector = TechStackDetector.from_config(
        Path("shared/config/tech_stacks/tech_stacks.json").resolve()
    )
    detected = detector.detect_tech_stack(str(tmp_path))
    assert "node_js" in detected

    exclusions = detector.get_simple_exclusions(str(tmp_path))
    # Node stacks should include node_modules in directories
    assert any("node_modules" in d for d in exclusions["directories"]) or (
        "node_modules" in exclusions["directories"]
    )
