## Path Resolver System

The AI-Assisted Workflows framework uses a simplified path resolver system that provides consistent import resolution across different deployment contexts without complex smart imports logic.

### Purpose & Problem Solved

**Challenge**: The framework supports multiple deployment scenarios:

- Development environment (`shared/` directory structure)
- Project-local deployment (`./project/.claude/scripts/`)
- User-global deployment (`~/.claude/scripts/`)
- Custom path deployment (`/anywhere/.claude/scripts/`)

**Solution**: A simplified import system using a central path helper module (no sys.path mutation) and module execution. Runners set `PYTHONPATH` to the package root and analyzers run as modules.

### How It Works

1. **Central Path Helpers**: `shared/utils/path_resolver.py` provides path utilities without modifying `sys.path`
2. **Module Execution**: Commands run analyzers via `python -m analyzers.<category>.<name>` with `PYTHONPATH` set to the package root
3. **No Complex Configuration**: Installation simply copies files; runners ensure `PYTHONPATH` is set
4. **Standard Python Imports**: Modules use direct imports (no side-effect imports)

### Standard Usage Pattern

- Invocation (runner):

```bash
# path to package root (shared/ in dev, scripts/ in deploy)
SCRIPTS_ROOT=/path/to/scripts/root
PYTHONPATH="$SCRIPTS_ROOT" python -m analyzers.quality.complexity_lizard . --output-format json
```

- Imports (inside modules):

```python
from core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
```

**Key Requirements**:

- Runners must ensure the package root is on `PYTHONPATH` (or run from the root)
- Modules use direct imports for all framework components
- Avoid import side-effects for path setup

### Common Import Patterns

**Core Infrastructure**:

```python
from core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
from core.base.profiler_base import BaseProfiler, ProfilerConfig
```

**Utility Modules**:

```python
from core.utils.output_formatter import ResultFormatter, AnalysisResult
from core.utils.tech_stack_detector import TechStackDetector
from core.utils.cross_platform import PlatformDetector
```

### Development Guidelines

**Standard Import Approach**:

- ✅ Ensure runner sets `PYTHONPATH` to the package root (or `cd` to it)
- ✅ Use direct imports for all framework modules
- ✅ Keep imports simple; avoid side-effect imports to modify `sys.path`

**Direct Imports (no path_resolver needed)**:

- ✅ Standard library modules (`sys`, `pathlib`, `json`, etc.)
- ✅ External packages (`requests`, `click`, `rich`, etc.)
- ✅ Same-directory relative imports

## Installation Integration

The installation provides the scripts and command workflows. Runners (commands or CI) set `PYTHONPATH` to the package root (e.g., `$INSTALL_DIR/scripts`) and call analyzers via `python -m`. This ensures consistent module resolution without mutating `sys.path` at runtime.

### Commands

- Setup: ./claude-code/install.sh - Install complete system
- Analysis: /analyze-security, /analyze-code-quality, /analyze-performance, /analyze-architecture
- Development: /plan-solution, /plan-refactor, /create-project, /fix-bug
- Orchestration: /todo-orchestrate implementation-plan.md - Multi-agent workflow execution
- Testing: /add-serena-mcp - Enhanced code search capabilities
- Python Tools: cd shared && python analyzers/security/semgrep_analyzer.py ../test_codebase/project --output-format json
