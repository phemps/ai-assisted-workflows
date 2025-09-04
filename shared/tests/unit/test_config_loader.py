#!/usr/bin/env python3

from pathlib import Path
import json
import pytest
from core.config.loader import load_architectural_pattern_sets, ConfigError


def test_load_architectural_pattern_sets_success():
    config_dir = Path("shared/config/patterns").resolve()
    cfg = load_architectural_pattern_sets(config_dir)
    assert "architectural_patterns" in cfg
    assert "antipatterns" in cfg
    assert "language_features" in cfg
    assert isinstance(cfg["architectural_patterns"], dict)
    assert isinstance(cfg["antipatterns"], dict)
    assert isinstance(cfg["language_features"], dict)


def test_load_architectural_pattern_sets_missing_files_raises(tmp_path: Path):
    # Create only one required file with minimal valid content; others missing
    (tmp_path / "architectural_patterns.json").write_text(
        json.dumps({"schema_version": 1, "patterns": {}}), encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        load_architectural_pattern_sets(tmp_path)
