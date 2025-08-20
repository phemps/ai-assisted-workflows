# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## AI-Assisted Workflows Project

A comprehensive development automation system combining workflow commands, Python analysis tools, and an 8-agent orchestration system for intelligent code quality management.

## Key Commands

### Installation & Setup

```bash
# Install workflows system
./claude-code/install.sh              # Install to current directory
./claude-code/install.sh ~            # Install globally

# Setup monitoring systems
/setup-ci-monitoring                  # AI-powered continuous improvement
/setup-dev-monitoring                 # Live service monitoring dashboard
/ci-monitoring-status                 # Check CI system health
```

### Core Development Commands

```bash
# Analysis commands
/analyze-architecture                 # Architectural patterns and dependencies
/analyze-code-quality                 # Code complexity and quality metrics
/analyze-security                     # Security vulnerability scanning
/analyze-performance                  # Performance bottlenecks
/analyze-root-cause                   # Error pattern analysis

# Planning & Implementation
/plan-solution [--tdd] [--seq]        # Research and plan approaches
/plan-ux-prd                          # UX and product requirements
/todo-orchestrate                     # Trigger 8-agent workflow orchestration
/todo-worktree                        # Git worktree task management

# Fixes & Improvements
/fix-bug                              # Bug fixing workflow
/fix-performance                      # Performance optimization
/add-code-precommit-checks           # Add quality gates
```

## Architecture

### Core Infrastructure

**BaseAnalyzer Framework** (`shared/core/base/analyzer_base.py`)

- Abstract base class for all analysis tools
- Provides shared infrastructure: file scanning, CLI, error handling, result formatting
- Strict validation with no placeholder logic
- All 9 inheriting analyzers fully functional with real findings

**Python Analysis Tools** (`shared/analyzers/`)

- **Security**: Authentication, secrets detection, vulnerability scanning, input validation
- **Quality**: Complexity analysis, code duplication, test coverage, pattern classification
- **Architecture**: Dependency analysis, coupling metrics, scalability checks, pattern evaluation
- **Performance**: Code profiling, database profiling, bottleneck detection, frontend analysis
- **Root Cause**: Error patterns, trace execution, recent changes analysis

**CI Framework** (`shared/ci/`)

- Semantic duplicate detection using CodeBERT embeddings
- Dynamic quality gate detection based on tech stack
- Integration with Serena MCP for efficient code search
- Metrics collection and recommendation generation

### 8-Agent Orchestration System

1. **plan-manager** - Task state and progress tracking
2. **fullstack-developer** - Cross-platform implementation
3. **solution-validator** - Pre-implementation validation
4. **quality-monitor** - Independent quality verification
5. **git-manager** - Version control operations
6. **documenter** - Documentation discovery and management
7. **log-monitor** - Runtime error detection
8. **cto** - Critical escalation (3 failures � CTO � human)

## Testing & Quality

### Running Tests

```bash
# Run all analyzer integration tests
cd shared && python -m tests/integration/test_all_analyzers.py -v

# Test individual analyzer
PYTHONPATH=shared python shared/analyzers/quality/complexity_lizard.py test_codebase/monorepo

# Test analysis engine
PYTHONPATH=shared python shared/analyzers/quality/analysis_engine.py test_codebase/monorepo --min-severity medium
```

### Quality Gates

The system automatically detects and runs appropriate quality checks based on tech stack:

- **JavaScript/TypeScript**: npm test, eslint, tsc
- **Python**: pytest, ruff, mypy
- **Rust**: cargo test, cargo clippy
- **Go**: go test, golangci-lint

## Project Structure

```
.
├── claude-code/               # Claude-specific workflows and configurations
│   ├── commands/              # Slash commands for Claude
│   ├── agents/                # 8-agent system definitions
│   ├── modes/                 # Behavior modification modes
│   └── install.sh             # Installation script
├── eval/                      # WIP evaluation framework
├── opencode/                    # WIP Opencode-specific workflows and configurations
├── shared/                    # Shared Python infrastructure
│   ├── core/base/             # BaseAnalyzer and BaseProfiler frameworks
│   ├── analyzers/             # Analysis tools by category
│   ├── ci/                    # Continuous improvement framework
│   └── setup/                 # Installation and setup scripts
├── test_codebase/             # Test projects for validation
└── todos/                     # Task management and workflows
```

## Metrics & Monitoring

Check system health and recent activity:

```bash
# Quick status check
claude /ci-monitoring-status

# Detailed metrics report
python shared/ci/metrics/ci_metrics_collector.py report

# View pending recommendations
python shared/ci/framework/ci_framework.py recommendations
```

## Debugging Tips

- Check logs in `/tmp/claude-workflows-install.log` for installation issues
- Use `--verbose` flag with analyzers for detailed output
- Test analyzers with `--max-files N` to limit scope during debugging if needed
- All service logs stream to `/dev.log` when dev monitoring is enabled

## Continuous Improvement Integration

**Code Duplication Detection**: Automated via GitHub Actions and Claude Code agents

### System Status

- **Languages Monitored**: python, javascript, typescript, php, c
- **Registry**: `.ci-registry/` (SQLite database with symbol tracking)
- **Analysis Threshold**: Configurable in `.ci-registry/config.json`
- **GitHub Integration**: Workflow configured for PR/push analysis

### Available Commands

```bash
# Check system status
claude /continuous-improvement-status

# Manual duplicate analysis
python shared/ci/integration/orchestration_bridge.py

# Generate metrics report
python shared/ci/metrics/ci_metrics_collector.py report

# Registry management
python shared/ci/core/registry_manager.py --status
```

### Workflow Integration

- **Automatic**: GitHub Actions analyze changes and create issues for complex duplicates
- **CTO Escalation**: Complex refactoring delegated to `claude /todo-orchestrate`
- **Quality Gates**: Integrated with existing project quality checks
- **Metrics**: Performance tracking in `.ci-registry/reports/`

### Configuration

Edit `.ci-registry/config.json` to adjust:

- Similarity thresholds (exact: 1.0, high: 0.8, medium: 0.6)
- Auto-refactor settings (enabled: false by default)
- Language-specific exclusions
- Quality gate integration

The system uses fail-fast architecture requiring MCP, CodeBERT, and Faiss dependencies.
