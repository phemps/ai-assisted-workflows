# Project: AI-Assisted Workflows

A comprehensive development automation system that combines Claude Code CLI workflows, Python analysis tools, and an 8-agent orchestration system for intelligent code quality management with AI-powered semantic duplicate detection.

## Features

- 8-Agent Orchestration System - Multi-agent workflow coordination with quality gates and CTO escalation
- 28 Slash Commands - Development workflow automation including security, performance, and architecture analysis
- 22 Python Analysis Tools - Across 4 categories: Security, Performance, Quality, Architecture, and Root Cause analysis
- AI-Powered Duplicate Detection - Semantic code analysis using CodeBERT embeddings and ChromaDB vector storage
- Python Aanalysis Tools - multi-Language Support analysis for 10+ programming languages (Python, TypeScript, Java, Go, Rust, C#, PHP, SQL, Solidity)
- CI Framework - GitHub Actions workflows with automated quality monitoring and refactoring recommendations
- Expert Agent System - 6 specialized expert agents for language-specific planning and architecture decisions
- Security Evaluation Framework - Testing against 14 vulnerable applications with known security issues
- Cross-Platform Installation - Bash and PowerShell installers for macOS, Linux, and Windows

### **Python Analysis Tools** (`shared/analyzers/`)

- **Security**: Authentication, secrets detection, vulnerability scanning, input validation
- **Quality**: Complexity analysis, code duplication, test coverage, pattern classification
- **Architecture**: Dependency analysis, coupling metrics, scalability checks, pattern evaluation
- **Performance**: Code profiling, database profiling, bottleneck detection, frontend analysis
- **Root Cause**: Error patterns, trace execution, recent changes analysis

### **CI Framework** (`shared/ci/`)

- Semantic duplicate detection using CodeBERT embeddings
- Dynamic quality gate detection based on tech stack
- Integration with Serena MCP for efficient code search
- Real-time indexing via PostToolUse hooks for Write/Edit/MultiEdit operations
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

### Expert Agents

- **python-expert** - Proactive Python development planning, architecture decisions, and modernization strategies using best practices
- **typescript-expert** - Proactive TypeScript development planning, architecture decisions, and modern TypeScript implementation patterns
- **codebase-expert** - Universal codebase search handling semantic queries, symbol matching, and structural searches via ChromaDB and Serena MCP routing
- **rag-architecture-expert** - RAG system architecture planning, technology selection, and implementation strategy for document search and Q&A systems
- **terraform-gcp-expert** - GCP infrastructure development planning, Terraform architecture decisions, and cloud modernization strategies
- **git-action-expert** - GitHub Actions workflow planning, CI/CD pipeline design, and automation strategy development

## Tech Stack

- Languages: Python 3.7+, TypeScript/JavaScript, Bash/Shell, SQL
- AI/ML Frameworks: ChromaDB, Transformers (Hugging Face), CodeBERT, PyTorch, Sentence-Transformers
- Security Tools: Semgrep, Detect-secrets, Bandit, Safety, SQLFluff
- Quality Analysis: Flake8, Pylint, Lizard, Radon, McCabe, Vulture
- Testing: pytest, pytest-cov, Karma, Jasmine, Custom evaluation frameworks
- Development Tools: Biome, Ruff, Black, Rich CLI, Click
- CI/CD: GitHub Actions, Cross-platform workflows
- Vector Storage: ChromaDB for semantic code search and duplicate detection

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
│ ├── ci/ # AI-powered continuous improvement system
│ │ ├── core/ # Semantic duplicate detection with CodeBERT
│ │ ├── workflows/ # Decision matrix and GitHub integration
│ │ ├── integration/ # Orchestration bridge and codebase search
│ │ └── tools/ # ChromaDB search and unified codebase search
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

### Key Files:

- CLAUDE.md - Project architecture and component documentation
- README.md - Quick start guide and feature overview
- claude-code/install.sh - Main installation script
- shared/core/base/analyzer_base.py - Base framework for all analysis tools
- shared/ci/core/semantic_duplicate_detector.py - AI-powered duplicate detection

### Entry Points:

- claude-code/commands/ - 28 slash commands for workflows
- shared/analyzers/ - Direct Python analysis tool execution
- shared/tests/integration/ - Comprehensive testing and evaluation frameworks

## Architecture

The system uses a hybrid AI-automation approach combining traditional static analysis with modern ML techniques:

### Core Components:

- BaseAnalyzer Framework: Provides shared infrastructure for all 22 analysis tools with strict validation
- 8-Agent Orchestration: State-machine workflow management with quality gates and CTO escalation
- Semantic Analysis Pipeline: LSP symbol extraction → CodeBERT embeddings → ChromaDB storage → similarity search
- Expert Agent Routing: Language and complexity-based delegation to specialized agents
- CI Integration: GitHub Actions with incremental analysis and automated refactoring recommendations

### Data Flow:

User Input → Claude Commands → Agent Orchestration → Analysis Tools → Results
↓
CI Pipeline → Duplicate Detection → Decision Matrix → Expert Agents → Actions

### Key Integrations:

- ChromaDB: Vector database for semantic code search and duplicate detection
- Serena MCP: Enhanced codebase search via Language Server Protocol
- GitHub Actions: Automated CI/CD with quality gate enforcement
- Multi-Language LSP: Symbol extraction across 10+ programming languages

## Path Resolver System

The AI-Assisted Workflows framework uses a simplified path resolver system that provides consistent import resolution across different deployment contexts without complex smart imports logic.

### Purpose & Problem Solved

**Challenge**: The framework supports multiple deployment scenarios:

- Development environment (`shared/` directory structure)
- Project-local deployment (`./project/.claude/scripts/`)
- User-global deployment (`~/.claude/scripts/`)
- Custom path deployment (`/anywhere/.claude/scripts/`)

**Solution**: A simplified import system using a central path resolver that establishes the package root and enables direct imports throughout the framework.

### How It Works

1. **Central Path Resolution**: `shared/utils/path_resolver.py` contains the package root detection logic
2. **Simple Import Pattern**: All modules use direct imports after importing the path resolver
3. **No Complex Configuration**: Installation simply copies files without path manipulation
4. **Standard Python Imports**: Uses normal Python import mechanism with established paths

### Standard Usage Pattern

All analyzers, CI components, and framework modules follow this simplified pattern:

```python
# Setup import paths and import utilities
try:
    from utils.path_resolver import PACKAGE_ROOT
    from core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)
```

**Key Requirements**:

- Import `path_resolver` first to establish package root
- Use direct imports for all framework modules
- Single try/except block for clean error handling
- Always use `sys.exit(1)` on import failure

### Common Import Patterns

**Core Infrastructure**:

```python
from utils.path_resolver import PACKAGE_ROOT
from core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig
from core.base.profiler_base import BaseProfiler, ProfilerConfig
```

**Utility Modules**:

```python
from utils.path_resolver import PACKAGE_ROOT
from core.utils.output_formatter import ResultFormatter, AnalysisResult
from core.utils.tech_stack_detector import TechStackDetector
from core.utils.cross_platform import PlatformDetector
```

**CI/CD Components**:

```python
from utils.path_resolver import PACKAGE_ROOT
from ci.core.chromadb_storage import ChromaDBStorage
from ci.core.semantic_duplicate_detector import DuplicateFinder
from ci.workflows.decision_matrix import DecisionMatrix
```

### Development Guidelines

**Standard Import Approach**:

- ✅ Always import `path_resolver` first
- ✅ Use direct imports for all framework modules
- ✅ Single try/except block for import error handling
- ✅ Clear error messages with sys.exit(1) on failure

**Direct Imports (no path_resolver needed)**:

- ✅ Standard library modules (`sys`, `pathlib`, `json`, etc.)
- ✅ External packages (`requests`, `click`, `rich`, etc.)
- ✅ Same-directory relative imports

**Benefits of Simplified System**:

- Reduced complexity and maintenance overhead
- Standard Python import behavior
- Easier debugging and development
- No dynamic import resolution
- Better IDE support and code completion

### Installation Integration

The path resolver system requires minimal configuration during installation:

1. **Path Detection**: Install script detects target deployment location
2. **File Copying**: Framework files copied to `$INSTALL_DIR/scripts/`
3. **Path Resolver**: `path_resolver.py` establishes package root automatically
4. **No Complex Setup**: No sed manipulation or dynamic configuration needed
5. **Standard Structure**: Uses conventional Python package layout

This provides consistent module resolution with significantly reduced complexity compared to the previous smart imports system.

### Commands

- Setup: ./claude-code/install.sh - Install complete system
- Analysis: /analyze-security, /analyze-code-quality, /analyze-performance, /analyze-architecture
- Development: /plan-solution, /plan-refactor, /create-project, /fix-bug
- Orchestration: /todo-orchestrate implementation-plan.md - Multi-agent workflow execution
- CI Setup: /setup-ci-monitoring - Configure automated duplicate detection
- Testing: /add-serena-mcp - Enhanced code search capabilities
- Python Tools: cd shared && python analyzers/security/semgrep_analyzer.py ../test_codebase/project --output-format json

## Testing

Frameworks: pytest, Custom evaluation frameworks, Integration test suites

Running Tests:

# Run all analyzer integration tests

cd shared && PYTHONPATH=/Users/adamjackson/LocalDev/ai-assisted-workflows/shared/utils:/Users/adamjackson/LocalDev/ai-assisted-workflows/shared python tests/integration/test_all_analyzers.py ../test_codebase/juice-shop-monorepo --output-format json --max-files 2

# Security analyzer evaluation

cd shared/tests/integration && PYTHONPATH=/Users/adamjackson/LocalDev/ai-assisted-workflows/shared/utils:/Users/adamjackson/LocalDev/ai-assisted-workflows/shared python test_security_analysers.py --analyzer detect_secrets --verbose

# E2E continuous improvement pipeline testing

cd shared && python tests/integration/test_continuous_improvement_e2e.py

# Root cause analyzers integration test

PYTHONPATH=/Users/adamjackson/LocalDev/ai-assisted-workflows/shared/utils:/Users/adamjackson/LocalDev/ai-assisted-workflows/shared python shared/tests/integration/test_root_cause_analyzers.py

# Individual analyzer testing

cd shared && python analyzers/security/detect_secrets_analyzer.py ../test_codebase/project --max-files 10

### Creating New Tests:

- Analysis Tests: Extend shared/tests/integration/ with new analyzer validation
- Security Tests: Add vulnerable applications to test_codebase/vulnerable-apps/
- Expected Findings: Update shared/tests/integration/security_expected_findings.json for evaluation
- Unit Tests: Add to shared/tests/unit/ following BaseAnalyzer patterns

### Test Structure:

- Integration tests validate complete workflows end-to-end
- Security evaluation tests against 14 applications with 544 known vulnerabilities
- Unit tests focus on individual component validation
- E2E tests validate the complete AI-assisted workflow pipeline including duplicate detection and agent orchestration

### Test Commands:

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

- `--analyzer`: Choose specific analyzer (detect_secrets, semgrep)
- `--applications`: Test specific applications only
- `--max-files`: Limit number of files scanned per application
- `--min-severity medium`: Filter findings by severity
- `--verbose`: Show detailed execution progress and debug information
- `--output-format json` Output results in JSON format

## Continuous Improvement Integration

**Code Duplication Detection**: Automated via GitHub Actions and Claude Code agents

### System Status

- **Languages Monitored**: Auto-detected
- **Registry**: `.ci-registry/` (SQLite database with symbol tracking)
- **Analysis Threshold**: Configurable in `.ci-registry/ci_config.json`
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

Edit `.ci-registry/ci_config.json` to adjust:

- Similarity thresholds (exact: 1.0, high: 0.8, medium: 0.6)
- Auto-refactor settings (enabled: false by default)
- Language-specific exclusions
- Quality gate integration

The system uses fail-fast architecture requiring MCP, CodeBERT, and Faiss dependencies.
