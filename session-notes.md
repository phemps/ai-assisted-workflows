Session Notes — Import Resolution and Analyzer Execution

Summary

- Issue: Deployed analyzers failed with "No module named 'utils'" when run via direct file paths.
- Root cause: `python path/to/script.py` sets `sys.path[0]` to the analyzer’s directory (e.g., `analyzers/quality`), so top-level packages (`utils`, `core`) aren’t importable. The prior pattern relied on importing `utils.path_resolver` for side effects, which failed if the package root wasn’t already importable.
- Decision: Standardize on module execution (`python -m analyzers.<category>.<name>`) with `PYTHONPATH` set to the package root. Remove all sys.path side-effects.

What Changed

- Standardized execution:
  - Commands now derive `SCRIPTS_ROOT = dirname(dirname(SCRIPT_PATH))` and run:
    - `PYTHONPATH="$SCRIPTS_ROOT" python -m analyzers.<category>.<name> ...`
- Removed side-effect imports:
  - Deleted `from utils import path_resolver  # noqa: F401` and surrounding try/except from analyzer entrypoints and setup/generator scripts.
  - `shared/core/base/module_base.py`: removed side-effect import of `utils.path_resolver`.
- Path resolver simplified:
  - `shared/utils/path_resolver.py`: no longer mutates `sys.path`; provides pure path helpers with `PACKAGE_ROOT` computed from file location.
- Command docs updated to module execution across:
  - analyze-code-quality, analyze-architecture, analyze-security, analyze-performance, analyze-root-cause, fix-performance, fix-bug, plan-refactor, plan-solution.
- Documentation aligned:
  - `CLAUDE.md` now describes module execution and path helper usage without side effects.

Rationale and Trade-offs

- Pros:
  - Idiomatic Python packaging model, deterministic imports, cleaner code (no `noqa F401`).
  - Works regardless of where the user deploys scripts, as long as `PYTHONPATH` points to the package root.
- Cons:
  - Direct single-file execution (`python …/script.py`) is no longer supported by design; runners must set `PYTHONPATH` or `cd` to the package root.

Run Examples

- Deployed (any location):
  - After resolving `SCRIPT_PATH` (e.g., `$HOME/.claude/scripts/analyzers/quality`):
    - `SCRIPTS_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"`
    - `PYTHONPATH="$SCRIPTS_ROOT" python -m analyzers.quality.complexity_lizard . --output-format json`
- Development:
  - `cd shared && python -m analyzers.quality.complexity_lizard ../test_codebase/clean-apps --output-format json`

Outcome

- Deployed test confirmed working with module execution; import errors resolved without path mutations or fallbacks.

---

Refactor Plan — Code Quality Improvements Roadmap

Scope and Goals

- Reduce complexity in hotspot functions and constructors.
- Externalize hard-coded pattern/config data into validated configs.
- Decrease parameter counts using small, typed parameter objects.
- Tighten tests with fixtures/parametrization and clearer orchestration.

Acceptance Targets

- Max function length ≤ 60 lines in refactored hotspots.
- Cyclomatic complexity ≤ 10 for refactored functions.
- No functions with >5 parameters in touched modules.
- Architectural/tech patterns loaded from validated config files.

Phased Plan (Trackable)

1. Phase 1 — Quick Wins (1–2 days)

- [ ] Refactor security evaluator into parse/run/report helpers.
- [ ] Add config loader and schema validation utilities.
- [ ] Externalize architectural pattern definitions to configs.
- [x] Reduce parameter counts with dataclasses for formatter/CLI where applicable.

2. Phase 2 — Structural Improvements (3–5 days)

- [ ] Introduce validation rule chain (replace monolithic validate_finding).
- [ ] Add pytest fixtures and parameterized tests for analyzers.
- [ ] Create shared test helpers and builders.

3. Phase 3 — Architecture (1 week)

- [ ] Externalize all tech stack definitions; add detector factory.
- [ ] Introduce strategy registry for analyzers.
- [ ] Add CI gates: complexity thresholds and coverage fail-under.

Implementation Notes

- No fallbacks or legacy paths retained; migrate call sites as needed.
- Configs include explicit `schema_version` and are validated at load time.
- Prefer pure functions and guard clauses to reduce nesting/CC.

Progress Log

- [x] Start: Refactor test_security_analysers main() into helpers.
- [x] Add `shared/core/config/loader.py` and minimal schemas.
- [x] Replace in-code architectural patterns with `configs/patterns/*.json`.
- [x] Swap analyzer finding validation to rule chain.
- [x] Externalize TechStackDetector definitions to JSON; add from_config.
- [x] Add pytest unit tests for validation rules, config loader, detectors.
- [x] Add shared test fixtures (config paths) and builders for findings.
- [x] Remove unused CLI framework (CLIBase, create_cli/run_cli paths) across analyzers; align modules for agent orchestration.
- [x] Add ruff and mypy: pre-commit hook + CI steps; add mypy.ini.
- [x] Update developer docs: remove CLI usage, show agent/orchestrated examples.
