# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## AI-Assisted Workflows Project

A comprehensive development automation system that creeates workflow commands, Python analysis tools, and an 8-agent orchestration system for intelligent code quality management.

## Python Analysis Tools Architecture

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

## Agent Systems

### 8-Agent Orchestration System

1. **plan-manager** - Task state and progress tracking
2. **fullstack-developer** - Cross-platform implementation
3. **solution-validator** - Pre-implementation validation
4. **quality-monitor** - Independent quality verification
5. **git-manager** - Version control operations
6. **documenter** - Documentation discovery and management
7. **log-monitor** - Runtime error detection
8. **cto** - Critical escalation (3 failures � CTO � human)

### Expert Agents

- **python-expert** - Proactive Python development planning, architecture decisions, and modernization strategies using best practices
- **typescript-expert** - Proactive TypeScript development planning, architecture decisions, and modern TypeScript implementation patterns
- **codebase-expert** - Universal codebase search handling semantic queries, symbol matching, and structural searches via ChromaDB and Serena MCP routing
- **rag-architecture-expert** - RAG system architecture planning, technology selection, and implementation strategy for document search and Q&A systems
- **terraform-gcp-expert** - GCP infrastructure development planning, Terraform architecture decisions, and cloud modernization strategies
- **git-action-expert** - GitHub Actions workflow planning, CI/CD pipeline design, and automation strategy development

## Evals, Testing & Quality Systems

### E2E Analyser test

```bash
# Run all analyzer integration tests
cd shared && python -m tests/integration/test_all_analyzers.py -v

# Test individual analyzer
PYTHONPATH=shared python shared/analyzers/quality/complexity_lizard.py test_codebase/monorepo

# Test analysis engine
PYTHONPATH=shared python shared/analyzers/quality/analysis_engine.py test_codebase/monorepo --min-severity medium
```

### Security Analyzer Evaluation

The evaluation framework tests our security analyzers against known vulnerable applications and displays results directly in the terminal.

**Quick Start:**

```bash
cd shared/tests/integration

# Run evaluation with specific analyzer (clean output)
python test_security_analysers.py --analyzer detect_secrets

# Run with detailed progress information
python test_security_analysers.py --analyzer semgrep --verbose

# Test specific applications only
python test_security_analysers.py --analyzer detect_secrets --applications test-python test-java

# Run with limited file scanning
python test_security_analysers.py --analyzer semgrep --max-files 10
```

**Output:**

- **Coverage Table**: Shows Issues Found | Issues Expected | Coverage % for each application
- **Summary Metrics**: Total coverage, precision, recall, and F1-scores
- **Terminal Output Only**: No files written - all results displayed on screen
- **Clean Default Output**: Only essential progress and final results (use `--verbose` for detailed info)

**Understanding the Results:**

- **Coverage %**: (Issues Found / Issues Expected) × 100 - measures detection quantity
- **Dynamic Expected Count**: Only counts vulnerabilities that the specific analyzer should detect
- **Applications**: Tests against vulnerable apps across multiple languages
- **Expected Findings**: Defined in `shared/tests/integration/security_expected_findings.json`

**Analyzer Capabilities:**

- **detect_secrets**: API keys, private keys, high entropy strings, authentication tokens
- **semgrep**: SQL injection, XSS, authentication bypasses, hardcoded credentials
- **sqlfluff**: SQL performance issues, anti-patterns, security flaws in SQL files
- Each analyzer is only tested against vulnerabilities it's designed to find

**Options:**

- `--analyzer`: Choose specific analyzer (detect_secrets, semgrep, sqlfluff)
- `--applications`: Test specific applications only
- `--max-files`: Limit number of files scanned per application
- `--verbose`: Show detailed execution progress and debug information

### CI Duplicate Detection Test

**End-to-End Integration Test** (`shared/tests/integration/test_continuous_improvement_e2e.py`)

Tests the complete AI-assisted workflow pipeline:

1. **Semantic Duplicate Detection**: Uses CodeBERT embeddings to identify functionally similar code across files
2. **CTO Decision Matrix**: Automated decision-making for refactoring complexity and risk assessment
3. **Orchestration Bridge**: Integration layer connecting duplicate detection with task orchestration
4. **Todo-Orchestrate Integration**: Seamless handoff to 8-agent system for complex refactoring tasks

**Test Process**:

- Creates temporary test projects with known duplicate patterns
- Validates LSP symbol extraction and semantic similarity detection
- Tests filtering of meaningful duplicates (excludes imports, built-ins, trivial matches)
- Verifies decision matrix logic for auto-refactor vs. CTO escalation
- Confirms orchestration bridge functionality and task delegation

**Key Validations**:

- Symbol extraction accuracy across multiple languages
- Semantic similarity thresholds (exact: 1.0, high: 0.8, medium: 0.6)
- Filter effectiveness for noise reduction
- Integration with existing CI/CD workflows
- Performance metrics collection and reporting

## Project Structure

```
.
├── claude-code/               # Claude Code CLI workflows and configurations
│   ├── commands/              # 25+ slash commands for development workflows
│   ├── agents/                # 19 specialized agents including 6 expert agents
│   ├── rules/                 # Technology-specific coding standards and best practices
│   ├── templates/             # PRD, subagent, and todo templates
│   ├── docs/                  # CLI documentation and guides
│   └── install.sh             # Cross-platform installation script
├── docs/                      # Comprehensive project documentation
│   ├── analysis-scripts.md    # Language support and analysis capabilities
│   ├── agents.md              # Agent orchestration system documentation
│   ├── ci-decision-matrix.md  # Code duplication decision criteria
│   ├── installation.md        # Installation and setup guide
│   ├── monitoring.md          # Development and CI monitoring systems
│   └── workflow-examples.md   # Common workflow examples and use cases
├── eval/                      # Evaluation framework design documents
├── opencode/                  # OpenCode IDE integration (WIP)
│   ├── agents/                # OpenCode-specific agent configurations
│   ├── plugins/               # IDE plugins and extensions
│   └── rules/                 # OpenCode coding standards
├── shared/                    # Core Python analysis infrastructure
│   ├── core/base/             # BaseAnalyzer and BaseProfiler frameworks
│   ├── analyzers/             # 15+ analysis tools across 4 categories
│   │   ├── security/          # Vulnerability scanning and secrets detection
│   │   ├── quality/           # Code complexity, duplication, and pattern analysis
│   │   ├── architecture/      # Dependency analysis and scalability checks
│   │   ├── performance/       # Profiling, bottleneck detection, and optimization
│   │   └── root_cause/        # Error pattern analysis and trace execution
│   ├── ci/                    # AI-powered continuous improvement system
│   │   ├── core/              # Semantic duplicate detection with CodeBERT
│   │   ├── workflows/         # Decision matrix and GitHub integration
│   │   ├── integration/       # Orchestration bridge and codebase search
│   │   └── metrics/           # CI metrics collection and reporting
│   ├── config/               # Configuration templates and CI workflows
│   ├── setup/                # Installation scripts and dependency management
│   └── tests/                # Comprehensive test suite with E2E integration tests
│       └── integration/      # Integration tests including security analyzer evaluation
│           ├── test_security_analysers.py  # Security analyzer evaluation framework
│           └── security_expected_findings.json  # Vulnerability mappings for evaluation
├── test_codebase/            # Controlled test applications for validation
│   ├── vulnerable-apps/      # 9 vulnerable applications with known security issues
│   ├── clean-apps/           # 5 clean applications for false positive testing
│   ├── code-quality-issues/  # Applications with code quality problems
│   └── eval-framework/       # Security analyzer evaluation system
│       └── minimal_evaluator.py    # Legacy evaluator (deprecated)
└── todos/                    # Task management and workflow documentation
```
