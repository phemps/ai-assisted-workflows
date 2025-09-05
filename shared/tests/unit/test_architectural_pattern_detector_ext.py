#!/usr/bin/env python3

import re
from pathlib import Path
from core.utils.architectural_pattern_detector import (
    ArchitecturalPatternDetector,
    PatternMatch,
    main as arch_main,
)


def test_ast_analysis_detects_god_class_and_long_parameter_list(
    patterns_config_dir: Path,
):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    content = (
        "class MegaClass:\n"
        + "\n".join([f"    def m{i}(self): pass" for i in range(20)])
        + "\n\n"
        "def fn(a,b,c,d,e,f,g):\n    return a+b+c+d+e+f+g\n"
    )
    matches = detector.analyze_python_ast(content, "mega.py")
    names = {m.pattern_name for m in matches}
    assert "god_class" in names
    assert "long_parameter_list" in names


def test_confidence_scorers_and_penalties(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    # Simulate a regex match for singleton-like text
    text = "class S:\n    _instance=None\n    def __new__(cls): return super().__new__(cls)"
    m = re.search(r"_instance", text)
    assert m is not None
    # Access private confidence calculator through the public API by crafting a fake match
    conf = detector._calculate_confidence(m, text, "singleton")  # type: ignore[attr-defined]
    assert 0.5 <= conf <= 1.0
    # Penalty for annotations/comments patterns
    m2 = re.search(r"@decorator", "@decorator\n")
    assert m2 is not None
    conf2 = detector._calculate_confidence(m2, "@decorator\n", "factory")  # type: ignore[attr-defined]
    assert conf2 <= conf


def test_get_pattern_summary_and_recommendations():
    detector = ArchitecturalPatternDetector()
    matches = [
        PatternMatch(
            pattern_type="anti",
            pattern_name="god_class",
            severity="high",
            description="",
            line_number=1,
            context="",
            confidence=0.9,
            is_language_feature=False,
        ),
        PatternMatch(
            pattern_type="anti",
            pattern_name="long_parameter_list",
            severity="medium",
            description="",
            line_number=2,
            context="",
            confidence=0.9,
            is_language_feature=False,
        ),
        # Push singleton count to trigger DI recommendation
        *[
            PatternMatch(
                pattern_type="architectural",
                pattern_name="singleton",
                severity="low",
                description="",
                line_number=10 + i,
                context="",
                confidence=0.9,
                is_language_feature=False,
            )
            for i in range(4)
        ],
    ]
    summary = detector.get_pattern_summary(matches)
    assert summary["total_patterns"] >= 2
    assert summary["patterns_by_type"].get("god_class", 0) >= 1
    # At least one recommendation should be returned for these anti-patterns
    assert summary["recommendations"]


def test_find_pattern_matches_and_exclusions(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    # Craft content to satisfy the 'singleton' scorer (>= 0.7 confidence)
    content = "_instance X __new__\n_instance SKIP __new__\nOTHER\n"
    lines = content.split("\n")
    # feature_lines exclude second line
    feature_lines = {2}
    pattern_info = {
        "indicators": [r"_instance.*?__new__"],
        "exclude_patterns": [r"SKIP"],
        "severity": "low",
        "description": "demo",
    }
    found = detector._find_pattern_matches(  # type: ignore[attr-defined]
        content, lines, "singleton", pattern_info, feature_lines, "x.py"
    )
    # First line matches; second excluded by feature_lines; third doesn't match
    assert len(found) == 1


def test_architectural_pattern_detector_cli_main(
    tmp_path: Path, patterns_config_dir: Path, monkeypatch
):
    # Create a sample Python file with patterns
    fp = tmp_path / "sample.py"
    fp.write_text(
        "class Many:\n"
        + "\n".join([f"    def m{i}(self): pass" for i in range(16)])
        + "\n\n"
        "def g(a,b,c,d,e,f,g): return 1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")
    monkeypatch.setenv("LC_ALL", "C")
    # Invoke CLI main; it prints a report; just ensure it runs without error
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[2]))
    monkeypatch.setenv("PATTERNS_DIR", str(patterns_config_dir))
    monkeypatch.setenv("TERM", "dumb")
    monkeypatch.setenv("COLUMNS", "80")
    # Simulate argv
    import sys

    argv_bak = sys.argv[:]
    sys.argv = ["arch", str(fp), "--language", "python"]
    try:
        arch_main()
    finally:
        sys.argv = argv_bak


def test_summary_confidence_buckets_and_recommendations():
    det = ArchitecturalPatternDetector()
    matches = [
        PatternMatch(
            pattern_type="anti",
            pattern_name="feature_envy",
            severity="low",
            description="",
            line_number=1,
            context="",
            confidence=0.4,
            is_language_feature=False,
        ),
        PatternMatch(
            pattern_type="anti",
            pattern_name="long_parameter_list",
            severity="medium",
            description="",
            line_number=2,
            context="",
            confidence=0.7,
            is_language_feature=False,
        ),
        PatternMatch(
            pattern_type="anti",
            pattern_name="god_class",
            severity="high",
            description="",
            line_number=3,
            context="",
            confidence=0.9,
            is_language_feature=False,
        ),
        # add more anti-patterns to trigger generic recommendation
        *[
            PatternMatch(
                pattern_type="anti",
                pattern_name=f"anti_{i}",
                severity="low",
                description="",
                line_number=10 + i,
                context="",
                confidence=0.8,
                is_language_feature=False,
            )
            for i in range(5)
        ],
    ]
    summary = det.get_pattern_summary(matches)
    # bucket distribution covered
    assert summary["patterns_by_confidence"]["low"] >= 1
    assert summary["patterns_by_confidence"]["medium"] >= 1
    assert summary["patterns_by_confidence"]["high"] >= 1
    # recommendations include specific and generic
    recs = "\n".join(summary["recommendations"])
    assert "Break down large classes" in recs or "large classes" in recs
    assert "parameter objects" in recs or "parameter" in recs
    assert "architectural refactoring" in recs or "refactoring" in recs
