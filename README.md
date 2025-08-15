# AI Assisted Workflows

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> **Hybrid AI-Automation System with Continuous Improvement Engine**
> Specialized workflow commands + LLM actions + Python analysis scripts + 8-Agent orchestration = comprehensive development automation with intelligent code quality management

## 📋 TL;DR

**Installation:**

```bash
./claude-code/install.sh              # Install to current directory
./claude-code/install.sh ~            # Install globally
/setup-dev-monitoring                 # Optional: Setup unified dev logging
/setup-ci-monitoring                  # Optional: Git actions quality checks (WIP, not ready yet)
/add-serena-mcp                       # Recommended per project mcp lsp tool
```

### Core Features

**🔍 Intelligent Code Analysis**

- Proactive code duplication detection using CodeBERT embeddings (WIP, not ready yet)
- Semantic pattern matching with Serena MCP integration
- Confidence-scored similarity analysis with configurable thresholds
- Multi-language support via Language Server Protocol

**🚀 8-Agent Orchestration**

- **plan-manager**: Task state and progress tracking
- **fullstack-developer**: Cross-platform implementation
- **solution-validator**: Pre-implementation validation
- **quality-monitor**: Dynamic quality gate detection
- **git-manager**: Version control operations
- **documenter**: Documentation discovery and management
- **log-monitor**: Runtime error detection
- **cto**: Critical escalation handler (3 failures → CTO → 2 attempts → human)

**⚡ Dynamic Quality Gates**

- Automatic detection of build, test, and lint commands
- Tech stack-aware validation (Node.js, Python, Rust, Go, etc.)
- Configurable quality thresholds per project
- Integration with existing CI/CD pipelines

### Quick Start

# Trigger comprehensive workflow orchestration

claude /todo-orchestrate implementation-plan.md

# Add quality gates to your project

claude /add-code-precommit-checks

````

### System Status Monitoring (WIP, not ready yet)

```bash
# Quick health check
$ claude /ci-monitoring-status
🔍 Continuous Improvement Status Report

📊 System Health:
  CI Framework: ✅ Active
  Database: ✅ Connected
  Python Dependencies: ✅ Available
  Serena MCP: ✅ Connected

📈 Recent Activity (Last 7 days):
  Metrics Recorded: 42
  Build Metrics: 12 (avg: 23.4s)
  Test Metrics: 15 (avg: 8.2s)
  Quality Metrics: 10
  Performance Metrics: 5

⚡ Pending Recommendations: 3
  High Priority: 1
  Medium Priority: 2

🚀 Next Steps:
  - Review recommendations: python3 shared/ci/framework/ci_framework.py recommendations
````

## 🚀 Workflow Examples

### Example 1: Complete Project Setup with Continuous Improvement

```bash
# Plan UX and product requirements
/plan-ux-prd "Mobile app for GitHub task management with real-time updates"

# Initialize project with better-t-stack.dev CLI
/create-project mobile-task-app --from-todos ./todos/todos.md

# Setup continuous improvement system
/setup-ci-monitoring --threshold=0.85 --auto-refactor=simple \9 (WIP, not ready yet)

# Setup development monitoring
/setup-dev-monitoring

# Add quality gates
/add-code-precommit-checks
```

### Example 2: Research and Implement with Quality Assurance

```bash
# Research and plan approaches with TDD mode
/plan-solution --tdd "Add real-time updates using WebSockets"

# Implement with continuous quality monitoring
/todo-orchestrate --seq

# System automatically:
# - Detects code duplications during implementation
# - Runs appropriate quality gates based on tech stack
# - Escalates complex issues to CTO agent
# - Generates refactoring suggestions and PRs
```

### Example 3: Existing Project Integration

```bash
# Analyze existing codebase
/analyze-architecture
/analyze-code-quality
/analyze-security

# Setup continuous improvement for existing project
/setup-ci-monitoring (WIP, not ready yet)

# The system will:
# - Detect your current tech stack automatically
# - Configure appropriate similarity thresholds
# - Set up quality gates matching your build tools
# - Begin monitoring for code quality improvements
```

## 🛠️ Available Commands

### Core Workflow Commands

**Analysis:** `/analyze-security`, `/analyze-architecture`, `/analyze-performance`, `/analyze-code-quality`
**Planning:** `/plan-solution`, `/plan-ux-prd`, `/plan-refactor`
**Project Setup:** `/create-project` - Initialize with [better-t-stack.dev](https://better-t-stack.dev/new)
**Implementation:** `/todo-orchestrate`, `/todo-worktree`
**Fixes:** `/fix-bug`, `/fix-performance`

### Continuous Improvement Commands (WIP, not ready yet)

**Setup:** `/setup-ci-monitoring` - Initialize AI-powered code quality system
**Monitoring:** `/ci-monitoring-status` - Health check and activity overview

### Build Flags

**Mode Flags:** `--prototype` (rapid POC), `--tdd` (test-driven)

## 📊 Development Monitoring System

**What you see after `/setup-dev-monitoring`:**

![Stack Detection](images/stack-detection-analysis.png)
_Smart stack detection: Auto-identifies React Native + Expo, tRPC + TypeScript, and sets up optimal monitoring_

![Unified Logs](images/dev-logs-unified.png)
_Timestamped unified logging: All services stream to `/dev.log` - Claude can query logs directly_

![Service Status](images/service-status-dashboard.png)
_Real-time service monitoring: Live status for API and Mobile services with health indicators_

**Key Monitoring Features:**

- 🚀 **Live service status**: Real-time health indicators for all services
- 📊 **Unified logging**: All logs stream to `/dev.log` with timestamps
- 🔍 **Smart analysis**: Auto-detects tech stack and configures monitoring
- ⚡ **Hot reload tracking**: File watching and change detection
- 🛠️ **Available commands**: `make dev`, `make status`, `make logs`

## 🏗️ Architecture Overview

### Directory Structure

```
.claude/
├── commands/                  # Slash commands for workflows and CI
├── agents/                    # 8-agent orchestration definitions
├── rules/                     # Tech stack and quality gate rules
├── templates/                 # Project and code generation templates
└── scripts/
  ├── ci/                    # Continuous improvement engine
  │   ├── core/              # Embeddings, Serena MCP, similarity
  │   ├── analyzers/         # Symbol extraction, duplication, metrics
  │   ├── workflows/         # GitHub, escalation, orchestration
  │   ├── framework/         # CI framework core logic
  │   ├── metrics/           # Metrics collection and reporting
  │   ├── detection/         # Build/test/lint/quality gate detection
  │   └── integration/       # Agent and CI/CD integration
  ├── analyze/               # Security, performance, architecture analysis
  ├── setup/                 # Install, monitoring, environment setup
  └── utils/                 # Cross-platform utilities and helpers
```

Feel free to explore and adapt these for experimentation.

## 🙏 Acknowledgments

- **Todo workflow** - Adapted from [@badlogic](https://github.com/badlogic/claude-commands/blob/main/todo.md)'s efficient Claude Commands plan mode
- **Development monitoring** - Inspired by [@mitsuhiko](https://github.com/mitsuhiko)'s unified logging approach
- **Agent orchestration** - Built on principles from distributed system design patterns

## 📄 License

MIT License - See LICENSE file for details.

---
