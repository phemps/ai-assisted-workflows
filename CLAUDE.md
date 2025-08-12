# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the Claude Code Workflows repository - a hybrid AI-automation system that provides specialized workflow commands, LLM actions, and Python analysis scripts for development automation. The system installs into `.claude/` directories and provides custom slash commands, agent orchestration, and quality gates.

## Common Development Tasks

### Installation and Setup

```bash
# Install to current directory (creates ./.claude/)
./claude-code/install.sh

# Install globally for user (creates ~/.claude/)
./claude-code/install.sh ~

# Install with optional monitoring setup
./claude-code/install.sh
/setup-dev-monitoring  # After installation
```

### Available Slash Commands

The system provides numerous slash commands organized by category:

- **Analysis**: `/analyze-security`, `/analyze-architecture`, `/analyze-performance`, `/analyze-code-quality`
- **Planning**: `/plan-solution`, `/plan-ux-prd`, `/plan-refactor`
- **Implementation**: `/todo-orchestrate`, `/todo-branch`, `/todo-worktree`
- **Fixes**: `/fix-bug`, `/fix-performance`
- **Quality**: `/add-code-precommit-checks`, `/add-code-posttooluse-quality-gates`

### Build Flags

Commands support various flags to modify behavior:

- `--prototype`: Rapid prototyping mode (relaxes quality gates)
- `--tdd`: Test-driven development mode
- `--seq`: Sequential thinking for complex breakdowns
- `--gitgrep`: Enhanced git repository search

## Architecture

### Directory Structure

```
claude-code/
├── agents/           # Agent definition files (*.md)
├── commands/         # Slash command implementations (*.md)
├── modes/           # Mode configuration files (*.modes.md)
├── rules/           # Framework-specific rules (*.rules.md)
├── docs/            # Technical documentation
└── templates/       # Template files for generation

opencode/            # Open-source components for community contribution
├── agents/          # Public agent definitions
├── docs/            # Public documentation for extensibility
├── modes/           # Public mode configurations
└── plugins/         # Plugin architecture components

shared/              # Shared libraries and configurations
├── analyzers/       # Analysis engines by category (BaseAnalyzer/BaseProfiler)
│   ├── architecture/    # Coupling, patterns, scalability analysis
│   ├── performance/     # Code and database profiling tools
│   ├── quality/         # Complexity, coverage, duplicates, patterns
│   ├── root_cause/      # Error tracing and analysis tools
│   └── security/        # Authentication, secrets, vulnerability scanning
├── ci/              # Continuous improvement system
├── config/          # Shared configuration files
│   └── formatter/   # Code formatting configurations (biome.json, ruff.toml)
├── core/            # Base utilities and shared infrastructure
│   └── base/        # BaseAnalyzer/BaseProfiler infrastructure
├── generators/      # Code and document generators
├── scripts/         # Standalone utility scripts
├── setup/           # Installation and setup utilities
└── tests/           # Test suites (unit + integration)

test_codebase/       # Example test projects
todos/               # Work-in-progress workflows
```

### Agent System

The repository implements an 8-agent orchestration system:

1. **build-orchestrator**: Central workflow coordinator
2. **plan-manager**: Task state and progress tracking
3. **fullstack-developer**: Cross-platform implementation
4. **solution-validator**: Pre-implementation validation
5. **quality-monitor**: Dynamic quality gate detection
6. **git-manager**: Version control operations
7. **documenter**: Documentation discovery
8. **log-monitor**: Runtime error detection
9. **cto**: Critical escalation handler (3 failures → CTO → 2 attempts → human)

### Python Scripts Architecture

The `shared/analyzers/` directory contains specialized analysis tools built on BaseAnalyzer/BaseProfiler infrastructure:

#### **BaseAnalyzer/BaseProfiler Infrastructure**

All analysis tools extend common base classes providing:

- **Standardized CLI**: Consistent argument parsing (--max-files, --batch-size, --timeout, --output-format)
- **File Scanning**: Configurable extensions and skip patterns with batch processing
- **Result Formatting**: Unified output formatting across json/console/summary modes
- **Strict Validation**: No placeholder findings - all results are genuine, actionable issues
- **Error Handling**: Robust error handling with detailed logging and recovery
- **Performance Tracking**: Built-in timing, file counting, and progress reporting

#### **Analysis Categories**

- **Security** (`shared/analyzers/security/`): Authentication analysis, secret detection, vulnerability scanning
  - Uses BaseAnalyzer infrastructure for consistent CLI and result formatting
  - Employs bandit, safety, semgrep integration patterns
- **Quality** (`shared/analyzers/quality/`): Complexity analysis, test coverage, code duplication, pattern classification
  - All 6 quality analyzers now use BaseAnalyzer infrastructure (100% conversion complete)
  - Includes orchestration engines for comprehensive quality assessment
- **Performance** (`shared/analyzers/performance/`): Code profiling, database profiling, bottleneck detection
  - Uses BaseProfiler infrastructure for performance-specific analysis patterns
  - Static analysis patterns with future integration points for dynamic profiling tools
- **Architecture** (`shared/analyzers/architecture/`): Coupling analysis, dependency analysis, scalability checks
- **Root Cause** (`shared/analyzers/root_cause/`): Error pattern detection, execution tracing, recent changes analysis

#### **Key Architecture Benefits**

- **Code Elimination**: 400+ lines of boilerplate eliminated across 20+ analyzers
- **No False Positives**: Strict validation prevents placeholder findings like "security finding" or "Analysis issue detected"
- **Developer Trust**: All findings are genuine, actionable security/quality issues with specific titles and recommendations
- **Consistent Interface**: Identical CLI interfaces, argument parsing, and output formatting across all analyzers
- **Quality Assurance**: Robust validation prevents broken analyzer implementations from silently passing

### Shared Libraries and Configuration

The `shared/` directory provides:

- **Config**: Centralized configuration files for code formatters (Biome, Ruff)
- **Scripts**: Reusable Python analysis and utility scripts organized by function
- **Cross-platform Support**: Platform-agnostic utilities for Windows, macOS, and Linux

### Open Source Components

The `opencode/` directory contains:

- **Public Agents**: Community-extensible agent definitions
- **Documentation**: Public APIs for plugin and extension development
- **Mode Templates**: Reusable behavior modification patterns
- **Plugin Architecture**: Framework for third-party integrations

### Command Implementation

Commands are Markdown files that can:

- Use `$ARGUMENTS` placeholder for dynamic values
- Be namespaced using subdirectories (e.g., `frontend:component`)
- Exist at project level (`.claude/commands/`) or user level (`~/.claude/commands/`)

### Mode System

Modes are activated by flags and modify Claude's behavior:

- Each mode has a corresponding `.modes.md` file
- Modes are resolved first from project `.claude/modes/`, then user `~/.claude/modes/`
- Modes contain specific instructions that override default behavior

## Quality Gates and Testing

The system implements dynamic quality gate detection that adapts to the project's technology stack. When working on changes:

1. Quality gates are automatically enforced unless `--prototype` flag is used
2. The quality-monitor agent detects available test/lint commands
3. Pre-commit checks can be added via `/add-code-precommit-checks`
4. Post-tool-use quality gates via `/add-code-posttooluse-quality-gates`

## Working with BaseAnalyzer/BaseProfiler Infrastructure

### **Creating New Analyzers**

All new analysis tools should extend BaseAnalyzer or BaseProfiler infrastructure:

```python
from shared.core.base.analyzer_base import BaseAnalyzer, create_standard_finding

class MyCustomAnalyzer(BaseAnalyzer):
    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        # Implement your analysis logic
        findings = []

        # Use helper function for consistent finding format
        finding = create_standard_finding(
            title="Specific Issue Found",
            description="Detailed description of the actual issue",
            severity="medium",
            file_path=target_path,
            line_number=42,
            recommendation="Specific action to fix this issue"
        )
        findings.append(finding)

        return findings
```

### **Analyzer Implementation Requirements**

- ✅ **All Required Fields**: title, description, severity, file_path, line_number, recommendation
- ✅ **No Placeholder Values**: Use specific titles like "SQL Injection Vulnerability", not "security finding"
- ✅ **Real File Paths**: Actual paths, not "unknown"
- ✅ **Actionable Recommendations**: Specific fixes, not "Review issue"
- ✅ **Proper CLI Integration**: Use `analyzer.run_cli()` pattern
- ✅ **Legacy Compatibility**: Provide backward-compatible function wrappers

### **Validation Testing**

```bash
# Test individual analyzer with strict validation
cd shared && PYTHONPATH=. python analyzers/category/your_analyzer.py ../test_codebase/monorepo --max-files 5

# Success indicators:
# ✅ No KeyError exceptions
# ✅ Real finding titles (not generic placeholders)
# ✅ Specific descriptions and recommendations
# ✅ Actual file paths and line numbers
```

### **Documentation References**

- **Interface Specification**: `shared/core/base/ANALYZER_INTERFACE.md`
- **Helper Functions**: `create_standard_finding()`, `validate_finding()` in `analyzer_base.py`
- **Working Examples**: All analyzers in `shared/analyzers/` categories

## Working with the Codebase

When making changes to this repository:

1. **Adding new commands**: Create `.md` files in `claude-code/commands/`
2. **Adding new agents**: Create `.md` files in `claude-code/agents/` or `opencode/agents/` for public agents
3. **Adding new modes**: Create `.modes.md` files in `claude-code/modes/` or `opencode/modes/` for public modes
4. **Adding new analyzers**: Extend BaseAnalyzer/BaseProfiler in appropriate `shared/analyzers/` category
5. **Adding shared utilities**: Place reusable Python utilities in `shared/scripts/` or `shared/core/`
6. **Adding configurations**: Place shared config files in `shared/config/` organized by tool type

### Installation Script

The main installation script (`claude-code/install.sh`) handles:

- Creating `.claude/` directory structure
- Installing Python dependencies from `shared/lib/scripts/setup/requirements.txt`
- Copying shared libraries and configurations to the target installation
- Setting up MCP tools (optional)
- Creating backups of existing installations
- Cross-platform compatibility (macOS, Linux, Windows via WSL)

## Important Notes

1. This repository itself doesn't have traditional build/test commands - it's a collection of tools installed into other projects
2. The `test_codebase/` directory contains example projects for testing workflows
3. The `todos/wip-workflows/` directory contains experimental workflows under development
4. All agent communication flows through the build orchestrator except for specific exceptions documented in `workflow-config.md`
