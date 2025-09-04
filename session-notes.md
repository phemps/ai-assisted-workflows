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
