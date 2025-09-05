#!/usr/bin/env python3

import pytest
from core.base.analyzer_base import validate_finding


def _base():
    return {
        "title": "t",
        "description": "d",
        "severity": "low",
        "file_path": "x.py",
        "line_number": 1,
        "recommendation": "r",
        "metadata": {},
    }


@pytest.mark.parametrize(
    "field,value,errmsg",
    [
        ("title", "", "non-empty string"),
        ("description", " ", "non-empty string"),
        ("recommendation", "", "non-empty string"),
        ("file_path", " ", "non-empty string"),
        ("line_number", -1, "non-negative"),
        ("severity", "urgent", "Invalid severity"),
    ],
)
def test_field_type_and_severity_errors(field, value, errmsg):
    finding = _base()
    finding[field] = value
    with pytest.raises(ValueError) as exc:
        validate_finding(finding)
    assert errmsg in str(exc.value)
