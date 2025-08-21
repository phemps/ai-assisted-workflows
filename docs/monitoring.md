# Development Monitoring System

## 🖥️ Visual Dashboard Overview

_After running `/setup-dev-monitoring`, you'll see:_

<div align="center">

![Stack Detection](../images/stack-detection-analysis.png)
_Smart stack detection: Auto-identifies React Native + Expo, tRPC + TypeScript, and sets up optimal monitoring_

![Unified Logs](../images/dev-logs-unified.png)
_Timestamped unified logging: All services stream to `/dev.log` - Claude can query logs directly_

![Service Status](../images/service-status-dashboard.png)
_Real-time service monitoring: Live status for API and Mobile services with health indicators_

</div>

## 🎯 Key Monitoring Features

| Feature                    | Description                                       | Benefit                   |
| :------------------------- | :------------------------------------------------ | :------------------------ |
| 🚀 **Live Service Status** | Real-time health indicators for all services      | Immediate issue detection |
| 📊 **Unified Logging**     | All logs stream to `/dev.log` with timestamps     | Centralized debugging     |
| 🔍 **Smart Analysis**      | Auto-detects tech stack and configures monitoring | Zero-config setup         |
| ⚡ **Hot Reload Tracking** | File watching and change detection                | Development efficiency    |
| 🛠️ **Command Suite**       | `make dev`, `make status`, `make logs`            | Streamlined workflow      |

## Setup Development Monitoring

The `/setup-dev-monitoring` command establishes comprehensive development monitoring infrastructure for any project structure through LLM-driven analysis and cross-platform automation.

### Workflow

1. **Project Component Discovery** - Identify runnable/compilable components and determine appropriate log labels
2. **Component Overlap Analysis** - Review discovered components for overlaps and conflicts
3. **Watch Pattern Analysis** - Determine file watching requirements based on discovered technologies
4. **System Dependencies Check and Install** - Verify and install required monitoring dependencies
5. **Existing File Handling** - Handle existing Procfile and Makefile appropriately
6. **Makefile Generation** - Generate Makefile with proper service configurations
7. **Procfile Generation** - Create Procfile with unified logging setup
8. **Project Integration** - Update project documentation with monitoring commands
9. **Validation and Testing** - Verify all generated files and configurations

## Continuous Improvement Monitoring

The `/setup-ci-monitoring` command configures proactive code duplication detection and refactoring automation for the current project.

### Workflow

1. **Dependency Check and Setup** - Install continuous improvement dependencies
2. **Environment Analysis** - Detect project technology stack automatically
3. **Configuration Setup** - Setup project-specific continuous improvement configuration
4. **GitHub Actions Setup** - Configure GitHub Actions workflows
5. **Initial Registry Population** - Perform initial codebase analysis and symbol extraction
6. **Post-Setup Verification** - Verify all systems are operational

## Quality Gates

The `/add-code-precommit-checks` command sets up pre-commit framework to enforce quality standards by preventing commits containing code violations.

### Workflow

1. **Check git repository** - Verify this is a git repository (required for git hooks)
2. **Check existing setup** - Look for existing pre-commit configuration
3. **Install pre-commit** - Install pre-commit if not already available
4. **Analyze project and generate config** - Detect project languages and frameworks, select appropriate hooks
5. **Install git hooks** - Set up git hooks to run automatically on commit
6. **Report completion** - Confirm pre-commit is active with configured hooks

### Supported Languages

The system automatically configures appropriate hooks for:
- TypeScript/JavaScript with ESLint and Prettier
- Python with Black, Ruff, and MyPy
- And many other languages through pre-commit hooks
