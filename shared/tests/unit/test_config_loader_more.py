#!/usr/bin/env python3

from pathlib import Path
from core.config.loader import load_architectural_pattern_sets, load_tech_stacks


def test_load_arch_patterns_happy_path(patterns_config_dir: Path):
    data = load_architectural_pattern_sets(patterns_config_dir)
    assert set(data.keys()) == {
        "architectural_patterns",
        "antipatterns",
        "language_features",
    }
    assert "singleton" in data["architectural_patterns"]
    assert "god_class" in data["antipatterns"]
    assert "decorators" in data["language_features"]


def test_load_tech_stacks_happy_path(tech_stacks_config_path: Path):
    stacks = load_tech_stacks(tech_stacks_config_path)
    for key in ["python", "node_js", "java_maven"]:
        assert key in stacks
        spec = stacks[key]
        for req in [
            "name",
            "primary_languages",
            "exclude_patterns",
            "dependency_dirs",
            "config_files",
            "source_patterns",
            "build_artifacts",
        ]:
            assert req in spec
