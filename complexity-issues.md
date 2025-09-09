# Complexity Issues (from CI Xenon Gate)

This document tracks functions and modules currently exceeding the configured complexity thresholds as reported by Xenon.

Command used in CI (now disabled for parity):

- `xenon --max-absolute B --max-modules A --max-average A shared`

Flagged blocks (function-level ranks):

- shared/utils/clean_claude_config.py:6 `clean_claude_config` — C
- shared/integration/cli/run_all_analyzers.py:200 `generate_recommendations` — C
- shared/integration/cli/evaluate_security.py:318 `build_evaluation_report` — C
- shared/integration/cli/evaluate_root_cause.py:364 `main` — C
- shared/analyzers/architecture/scalability_check.py:460 `_should_flag_scalability_issue` — D
- shared/analyzers/architecture/scalability_check.py:405 `_get_lizard_metrics` — C
- shared/analyzers/architecture/pattern_evaluation.py:433 `_get_lizard_metrics` — C
- shared/analyzers/architecture/pattern_evaluation.py:343 `_check_patterns` — C
- shared/analyzers/architecture/coupling_analysis.py:347 `_extract_dependencies` — C
- shared/analyzers/performance/flake8_performance_analyzer.py:279 `_run_perflint_analysis` — C
- shared/analyzers/performance/analyze_frontend.py:716 `_is_false_positive` — E
- shared/analyzers/performance/analyze_frontend.py:448 `_scan_file_for_issues` — C
- shared/analyzers/performance/sqlfluff_analyzer.py:213 `_run_sqlfluff_analysis` — C
- shared/analyzers/root_cause/trace_execution.py:248 `_generate_investigation_pointers` — C
- shared/analyzers/root_cause/recent_changes.py:152 `analyze_target` — C
- shared/analyzers/root_cause/error_patterns.py:645 `_get_language_recommendation` — C
- shared/analyzers/root_cause/error_patterns.py:369 `_check_targeted_error_patterns` — C
- shared/analyzers/quality/result_aggregator.py:667 `get_filtered_results` — C
- shared/analyzers/quality/complexity_lizard.py:234 `_parse_lizard_output` — C
- shared/core/utils/tech_stack_detector.py:117 `get_simple_exclusions` — C
- shared/core/utils/tech_stack_detector.py:297 `_is_generated_or_vendor_code` — C
- shared/core/utils/tech_stack_detector.py:239 `should_analyze_file` — C
- shared/core/base/validation_rules.py:33 `FieldTypesRule` — C
- shared/core/base/validation_rules.py:34 `validate` — C
- shared/core/base/analyzer_base.py:530 `create_standard_finding` — C
- shared/core/base/vendor_detector.py:182 `detect_vendor_code` — C
- shared/setup/monitoring/install_monitoring_dependencies.py:160 `main` — C
- shared/generators/procfile.py:106 `main` — C

Module-level ranks:

- shared/utils/clean_claude_config.py — B
- shared/integration/cli/run_all_analyzers.py — B
- shared/integration/cli/evaluate_root_cause.py — B
- shared/analyzers/architecture/scalability_check.py — B
- shared/analyzers/root_cause/trace_execution.py — B
- shared/analyzers/root_cause/error_patterns.py — B
- shared/core/utils/tech_stack_detector.py — B
- shared/setup/test_install.py — B
- shared/setup/monitoring/update_claude_md.py — B
- shared/setup/monitoring/install_monitoring_dependencies.py — B
- shared/generators/procfile.py — B

Notes:

- Local vs CI discrepancy: CI ran Xenon; pre-commit does not. We’ve disabled Xenon in CI to align gates until we decide a remediation plan.
- Suggested remediation approach (when ready):
  - Extract small helpers from flagged functions, use guard clauses, and isolate parsing vs. normalization vs. I/O.
  - Replace nested conditionals with clear predicates, dispatch tables, or early returns.
  - Keep public interfaces and behavior unchanged; limit changes to structure and readability.
