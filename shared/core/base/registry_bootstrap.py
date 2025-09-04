#!/usr/bin/env python3
"""Bootstrap module to register all analyzers via decorators.

Import this module once at startup to ensure registry population.
"""

# Security analyzers
from analyzers.security import detect_secrets_analyzer as _ds  # noqa: F401
from analyzers.security import semgrep_analyzer as _sg  # noqa: F401

# Quality analyzers
from analyzers.quality import complexity_lizard as _ql  # noqa: F401
from analyzers.quality import code_duplication_analyzer as _qd  # noqa: F401
from analyzers.quality import coverage_analysis as _qc  # noqa: F401
from analyzers.quality import pattern_classifier as _qp  # noqa: F401
from analyzers.quality import result_aggregator as _qa  # noqa: F401

# Architecture analyzers
from analyzers.architecture import coupling_analysis as _ac  # noqa: F401
from analyzers.architecture import dependency_analysis as _ad  # noqa: F401
from analyzers.architecture import pattern_evaluation as _ap  # noqa: F401
from analyzers.architecture import scalability_check as _as  # noqa: F401

# Performance analyzers
from analyzers.performance import analyze_frontend as _pf  # noqa: F401
from analyzers.performance import sqlfluff_analyzer as _ps  # noqa: F401
from analyzers.performance import flake8_performance_analyzer as _pp  # noqa: F401
from analyzers.performance import performance_baseline as _pb  # noqa: F401
from analyzers.performance import profile_code as _pc  # noqa: F401

# Root cause analyzers
from analyzers.root_cause import error_patterns as _re  # noqa: F401
from analyzers.root_cause import recent_changes as _rr  # noqa: F401
from analyzers.root_cause import trace_execution as _rt  # noqa: F401
