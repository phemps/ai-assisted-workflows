# Shared Directory Reorganization Map

This document tracks all file movements during the reorganization of the shared/ directory.
Format: `OLD PATH` → `NEW PATH`

## Config Files

- `shared/config/formatter/` → `shared/config/formatters/`
- `shared/lib/scripts/continuous-improvement/config/` → `shared/config/ci/`

## Core Base Utilities

- `shared/lib/scripts/continuous-improvement/base/` → `shared/core/base/`
  - `__init__.py` → `__init__.py`
  - `cli_utils.py` → `cli_utils.py`
  - `config_factory.py` → `config_factory.py`
  - `error_handler.py` → `error_handler.py`
  - `fs_utils.py` → `fs_utils.py`
  - `module_base.py` → `module_base.py`
  - `timing_utils.py` → `timing_utils.py`

## Core General Utilities

- `shared/lib/scripts/utils/` → `shared/core/utils/`
  - `analysis_environment.py` → `analysis_environment.py`
  - `architectural_pattern_detector.py` → `architectural_pattern_detector.py`
  - `cross_platform.py` → `cross_platform.py`
  - `output_formatter.py` → `output_formatter.py`
  - `tech_stack_detector.py` → `tech_stack_detector.py`

## Analyzers

- `shared/lib/scripts/analyze/` → `shared/analyzers/`
  - `architecture/` → `architecture/`
  - `code_quality/` → `quality/`
  - `performance/` → `performance/`
  - `root_cause/` → `root_cause/`
  - `security/` → `security/`

## Continuous Improvement → CI

- `shared/lib/scripts/continuous-improvement/` → `shared/ci/`
  - Core components remain in `core/`
  - `analyzers/demo_integration.py` → `integration/demo_integration.py`
  - `analyzers/symbol_extractor.py` → `integration/symbol_extractor.py`
  - All other subdirectories maintain structure

## Generators (New Directory)

- `shared/lib/scripts/plan/generate_analysis_report.py` → `shared/generators/analysis_report.py`
- `shared/lib/scripts/plan/generate_prd.py` → `shared/generators/prd.py`
- `shared/lib/scripts/utils/generate_makefile.py` → `shared/generators/makefile.py`
- `shared/lib/scripts/utils/generate_procfile.py` → `shared/generators/procfile.py`

## Setup Scripts

- `shared/lib/scripts/setup/continuous-improvement/` → `shared/setup/ci/`
- `shared/lib/scripts/setup/dev-monitoring/` → `shared/setup/monitoring/`
- Other setup files remain in `shared/setup/`

## Standalone Scripts

- `shared/lib/scripts/utils/clean_claude_config.py` → `shared/scripts/clean_claude_config.py`

## Test Files

- `shared/lib/scripts/analyze/code_quality/test_duplicate_detection.py` → `shared/tests/unit/test_duplicate_detection.py`
  - **Note**: Unit test for duplicate detection components
- `shared/lib/scripts/analyze/code_quality/test_integration.py` → `shared/tests/integration/test_analysis_engine.py`
  - **Note**: This is an integration test for the analysis engine, moved to integration folder
- `shared/lib/scripts/setup/test_install.py` → `shared/setup/test_install.py` (keeping with setup for now)

## Integration Tests

- `shared/lib/scripts/run_all_analysis.py` → `shared/tests/integration/test_all_analyzers.py`
  - **Note**: This is actually an integration test that validates all analyzers work together

## Analysis Tools (Misplaced Files Corrected)

- `shared/lib/scripts/analyze/code_quality/test_coverage_analysis.py` → `shared/analyzers/quality/coverage_analysis.py`
  - **Note**: This was initially misplaced in tests/ - it's an analysis tool, not a test file

## Import Path Updates Required

### Old Import Pattern:

```python
from shared.lib.scripts.continuous-improvement.base import CIModuleBase
from shared.lib.scripts.utils import output_formatter
```

### New Import Pattern:

```python
from shared.core.base import CIModuleBase
from shared.core.utils import output_formatter
```

## Files with Updated References

### Command Files Updated:

- `/todos/ci-commands/setup-ci-monitoring.md` - All paths updated to new structure
- `/todos/ci-commands/ci-monitoring-status.md` - All paths updated to new structure

### Documentation Updated:

- `/README.md` - 4 CI framework references updated
- `/shared/ci/README.md` - All example commands updated

### Python Files Updated:

- 76 Python files had their imports automatically updated using update_imports.py script
- All sys.path.insert statements updated to reference new paths
- All direct imports from utils and base modules updated

## Summary of Changes

### Directories Restructured:

- `shared/lib/scripts/` → Removed unnecessary nesting
- `shared/config/formatter/` → `shared/config/formatters/`
- `shared/lib/scripts/continuous-improvement/` → `shared/ci/`
- `shared/lib/scripts/analyze/` → `shared/analyzers/`
- `shared/lib/scripts/analyze/code_quality/` → `shared/analyzers/quality/`

### New Top-Level Organization:

- `shared/core/` - Base classes and utilities
- `shared/analyzers/` - All analysis tools
- `shared/ci/` - Continuous improvement system
- `shared/generators/` - Code and config generators
- `shared/setup/` - Installation and setup scripts
- `shared/scripts/` - Standalone executable scripts
- `shared/tests/` - All test files
- `shared/config/` - All configuration files

### Files Cleaned Up:

The old `lib/` directory has been removed since all files have been successfully reorganized and are under version control for rollback if needed.
