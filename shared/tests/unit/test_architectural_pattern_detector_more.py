#!/usr/bin/env python3

import re
from pathlib import Path
from core.utils.architectural_pattern_detector import (
    ArchitecturalPatternDetector,
    PatternMatch,
)


def test_identify_language_features_filters_by_language(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    # A visibility modifier (non-Python language feature) should not be flagged for Python
    content = "public class X {}\n"
    features = detector._identify_language_features(content, language="python")  # type: ignore[attr-defined]
    assert features == set()


def test_find_pattern_matches_anti_classification(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    # Exercise anti classification branch directly via private matcher with a simple indicator
    body = "\n".join([f"def m{i}(x): return x" for i in range(16)])
    content = f"{body}\n"
    lines = content.split("\n")
    feature_lines = set()
    pattern_info = {
        # Match the whole content so confidence scorer sees many 'def' occurrences
        "indicators": [r".*"],
        "exclude_patterns": [],
        "severity": "low",
        "description": "anti demo",
    }
    found = detector._find_pattern_matches(  # type: ignore[attr-defined]
        content, lines, "god_class", pattern_info, feature_lines, "x.py"
    )
    assert found and found[0].pattern_type == "anti"


def test_calculate_confidence_missing_scorer_and_clamp(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    text = "@decorator\n/** doc */\n# comment"
    m = re.search(r"@\w+", text)
    assert m is not None
    # Unknown pattern name exercises missing-scorer branch and penalties; clamps to [0,1]
    score = detector._calculate_confidence(m, text, "unknown_pattern")  # type: ignore[attr-defined]
    assert 0.0 <= score <= 1.0


def test_analyze_python_ast_syntax_error_returns_empty(patterns_config_dir: Path):
    detector = ArchitecturalPatternDetector(config_dir=patterns_config_dir)
    bad = "def broken(:\n    pass"
    assert detector.analyze_python_ast(bad, "broken.py") == []


def test_generate_recommendations_limit_and_counts():
    det = ArchitecturalPatternDetector()
    # Build >5 anti-pattern matches to trigger generic recommendation and limit to 5
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
    ] + [
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
    ]
    summary = det.get_pattern_summary(matches)
    assert summary["total_patterns"] == len(matches)
    assert len(summary["recommendations"]) <= 5
    joined = "\n".join(summary["recommendations"])
    assert ("large classes" in joined) or ("Break down" in joined)
    assert ("parameter" in joined) or ("builder" in joined)


# Note: Strategy pattern detection is exercised in other tests; omit here to keep runtime fast.
