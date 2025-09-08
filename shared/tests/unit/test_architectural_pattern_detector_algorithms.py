#!/usr/bin/env python3

import re
from pathlib import Path
from core.utils.architectural_pattern_detector import (
    ArchitecturalPatternDetector,
    PatternMatch,
)


# Language features filtering (core)
def test_identify_language_features_filters_by_language(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    # A visibility modifier (non-Python feature) should not be flagged for Python
    content = "public class X {}\n"
    features = detector._identify_language_features(content, language="python")  # type: ignore[attr-defined]
    assert features == set()


# Pattern matcher and exclusions (core)
def test_find_pattern_matches_and_exclusions(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    # Craft content to satisfy the 'singleton' scorer (>= 0.7 confidence)
    content = "_instance X __new__\n_instance SKIP __new__\nOTHER\n"
    lines = content.split("\n")
    feature_lines = {2}  # exclude second line
    pattern_info = {
        "indicators": [r"_instance.*?__new__"],
        "exclude_patterns": [r"SKIP"],
        "severity": "low",
        "description": "demo",
    }
    found = detector._find_pattern_matches(  # type: ignore[attr-defined]
        content, lines, "singleton", pattern_info, feature_lines, "x.py"
    )
    assert len(found) == 1


def test_find_pattern_matches_anti_classification(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    # Exercise anti classification via private matcher with a simple indicator
    body = "\n".join([f"def m{i}(x): return x" for i in range(16)])
    content = f"{body}\n"
    lines = content.split("\n")
    found = detector._find_pattern_matches(  # type: ignore[attr-defined]
        content,
        lines,
        "god_class",
        {
            "indicators": [r".*"],
            "exclude_patterns": [],
            "severity": "low",
            "description": "anti",
        },
        set(),
        "x.py",
    )
    assert found and found[0].pattern_type == "anti"


# Confidence scoring and clamping (core)
def test_confidence_scorers_and_penalties(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    text = "class S:\n    _instance=None\n    def __new__(cls): return super().__new__(cls)"
    m = re.search(r"_instance", text)
    assert m is not None
    conf = detector._calculate_confidence(m, text, "singleton")  # type: ignore[attr-defined]
    assert 0.5 <= conf <= 1.0


def test_calculate_confidence_missing_scorer_and_clamp(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    text = "@decorator\n/** doc */\n# comment"
    m = re.search(r"@\w+", text)
    assert m is not None
    score = detector._calculate_confidence(m, text, "unknown_pattern")  # type: ignore[attr-defined]
    assert 0.0 <= score <= 1.0


# AST-based analysis (core)
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


def test_analyze_python_ast_syntax_error_returns_empty(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    bad = "def broken(:\n    pass"
    assert detector.analyze_python_ast(bad, "broken.py") == []


# Summary and recommendations (core)
def test_generate_recommendations_limit_and_counts():
    det = ArchitecturalPatternDetector()
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
        # Add more anti patterns to trigger generic recommendation and cap
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
            for i in range(6)
        ],
    ]
    summary = det.get_pattern_summary(matches)
    assert summary["total_patterns"] == len(matches)
    assert len(summary["recommendations"]) <= 5
    recs = "\n".join(summary["recommendations"])
    assert ("large classes" in recs) or ("Break down" in recs)
    assert ("parameter" in recs) or ("builder" in recs)
