#!/usr/bin/env python3

import json
from pathlib import Path
import pytest
from core.config.loader import (
    load_json_config,
    load_tech_stacks,
    load_architectural_pattern_sets,
    ConfigError,
)


def test_load_json_config_missing_and_invalid(tmp_path: Path):
    missing = tmp_path / "nope.json"
    with pytest.raises(ConfigError):
        load_json_config(missing, ["x"])  # type: ignore[arg-type]

    bad = tmp_path / "bad.json"
    bad.write_text("{not-json}", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_json_config(bad, ["x"])  # type: ignore[arg-type]


def test_load_tech_stacks_shape_errors(tmp_path: Path):
    f = tmp_path / "stacks.json"
    # Missing 'stacks'
    f.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_tech_stacks(f)

    # 'stacks' not a dict
    f.write_text(json.dumps({"schema_version": 1, "stacks": []}), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_tech_stacks(f)

    # Stack missing required keys
    f.write_text(
        json.dumps({"schema_version": 1, "stacks": {"py": {"name": "x"}}}),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_tech_stacks(f)

    # Wrong list type for primary_languages
    f.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "stacks": {
                    "py": {
                        "name": "Python",
                        "primary_languages": "python",
                        "exclude_patterns": [],
                        "dependency_dirs": [],
                        "config_files": [],
                        "source_patterns": [],
                        "build_artifacts": [],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_tech_stacks(f)


def test_load_arch_patterns_missing_files(tmp_path: Path):
    # Directory exists but required files absent
    (tmp_path / "sub").mkdir(parents=True, exist_ok=True)
    with pytest.raises(ConfigError):
        load_architectural_pattern_sets(tmp_path / "sub")
