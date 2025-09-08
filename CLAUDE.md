# Project: AI-Assisted Workflows

A comprehensive development automation system that combines Claude Code CLI workflows, Python analysis tools, and an 8-agent orchestration system for intelligent code quality management.

## Tech Stack

- Languages: Python 3.7+, TypeScript/JavaScript, Bash/Shell, SQL
- Security Tools: Semgrep, Detect-secrets, Bandit, Safety, SQLFluff
- Quality Analysis: Flake8, Pylint, Lizard, Radon, McCabe, Vulture
- Testing: pytest, pytest-cov, Karma, Jasmine, Custom evaluation frameworks
- Development Tools: Biome, Ruff, Black, Rich CLI, Click
- CI/CD: GitHub Actions, Cross-platform workflows

## Project Structure

ai-assisted-workflows/
├── claude-code/ # Claude Code CLI workflows and configurations
│ ├── commands/ # 28 slash commands for development workflows
│ ├── agents/ # 19 specialized agents (8-agent orchestration + 6 experts + 5 support)
│ ├── rules/ # Technology-specific coding standards and best practices
│ ├── templates/ # PRD, subagent, and todo templates
│ ├── docs/ # CLI documentation and integration guides
│ └── install.sh/.ps1 # Cross-platform installation scripts
├── shared/ # Core Python analysis infrastructure
│ ├── core/base/ # BaseAnalyzer and BaseProfiler frameworks
│ ├── analyzers/ # 22 analysis tools across 5 categories
│ │ ├── security/ # Vulnerability scanning and secrets detection
│ │ ├── quality/ # Code complexity, duplication, and pattern analysis
│ │ ├── architecture/ # Dependency analysis and scalability checks
│ │ ├── performance/ # Profiling, bottleneck detection, and optimization
│ │ └── root_cause/ # Error pattern analysis and trace execution
│ ├── config/ # Configuration templates and CI workflows
│ ├── setup/ # Installation scripts and dependency management
│ └── tests/ # Comprehensive test suite with E2E integration tests
│ └── integration/ # Security analyzer evaluation and E2E CI testing
├── test_codebase/ # Controlled test applications for validation
│ ├── vulnerable-apps/ # 9 vulnerable applications with known security issues
│ ├── clean-apps/ # 5 clean applications for false positive testing
│ └── juice-shop-monorepo/ # Complex real-world application for comprehensive testing
├── docs/ # Comprehensive project documentation
│ ├── installation.md # Installation and setup guide
│ ├── agents.md # Agent orchestration system documentation
│ ├── analysis-scripts.md # Language support and analysis capabilities
│ └── workflow-examples.md # Common workflow examples and use cases
└── todos/ # Task management and workflow documentation

### Entry Points:

- claude-code/commands/ - 28 slash commands for workflows
- shared/analyzers/ - Direct Python analysis tool execution
- shared/tests/integration/ - Comprehensive testing and evaluation frameworks

## Architecture

The system uses a hybrid AI-automation approach combining traditional static analysis with modern ML techniques:

### Core Components:

- BaseAnalyzer Framework: Provides shared infrastructure for all 22 analysis tools with strict validation
- 8-Agent Orchestration: State-machine workflow management with quality gates and CTO escalation
- Expert Agent Routing: Language and complexity-based delegation to specialized agents

### Data Flow:

User Input → Claude Commands → Agent Orchestration → Analysis Tools → Results

### Key Integrations:

- Serena MCP: Enhanced codebase search via Language Server Protocol
- GitHub Actions: Automated CI/CD with quality gate enforcement
- Multi-Language LSP: Symbol extraction across 10+ programming languages
