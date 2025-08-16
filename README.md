# AI Assisted Workflows

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> **Hybrid AI-Automation System**
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

**Dependencies:**

Due to the programmatic analysis scripts, theres quite a lot of dependencies installed
full list of libraries used and languages supported found here [analysis script details](https://github.com/adam-versed/ai-assisted-workflows/docs/analysis-scripts.md)

**Supported Languages:** Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby, C/C++, Swift, Kotlin, SQL, and more

| Language            | Test Coverage            | Performance Baseline          | Import Analysis         | Bottleneck Detection    |
| ------------------- | ------------------------ | ----------------------------- | ----------------------- | ----------------------- |
| **Python**          | ✅ pytest, coverage      | ✅ cProfile, memory-profiler  | ✅ import patterns      | ✅ AST analysis         |
| **JavaScript**      | ✅ jest, nyc, c8         | ✅ npm scripts, profiling     | ✅ import/require       | ✅ performance patterns |
| **TypeScript**      | ✅ jest, nyc, c8         | ✅ npm scripts, profiling     | ✅ import patterns      | ✅ performance patterns |
| **Java**            | ✅ junit, jacoco         | ✅ maven/gradle, JFR          | ✅ import statements    | ✅ performance patterns |
| **Go**              | ✅ go test, coverage     | ✅ go build, benchmarks       | ✅ import patterns      | ✅ performance patterns |
| **Rust**            | ✅ cargo test, tarpaulin | ✅ cargo bench, flamegraph    | ✅ use statements       | ✅ performance patterns |
| **C#**              | ✅ dotnet test, coverlet | ✅ dotnet build, profiling    | ✅ using statements     | ✅ performance patterns |
| **SQL**             | ✅ SQLFluff integration  | ✅ Query performance analysis | ✅ Schema dependencies  | ✅ Query optimization   |
| **Other Languages** | ✅ Framework detection   | ✅ Language-specific patterns | ✅ Full import analysis | ✅ Performance patterns |

## Core Principles

- Minmise token usage
  - what can be offloaded to programmatic scripts is
  - just in time i.e. on loaded when needed, unless it impacts system accuracy
- Hybrid approach - Combines LLM intelligence with programmatic scripts for accuracy and repeatability
- Platform agnostic - not achieved yet, but once main prompts have stabilised going to use a templating system to allow people to roll out commands to any supported platform, starting with claude code, opencode will be next.
- Focus on LLM strengths, mitigate its weaknessess
  - good at scale, in the moment contextual flexibility, pattern matching
  - bad at repeatability and predictability

### Core Features

Implemented either by slash commands, agents, rules/user modes, programmatic scripts and git actions - the idea is to create a useful, flexible tool kit that involves the developer at the heart, not to abstract them away.

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

`/add-code-precommit-checks`

- Automatic detection of build, test, and lint commands
- Tech stack-aware validation (Node.js, Python, Rust, Go, etc.)
- Configurable quality thresholds per project
- Integration with existing CI/CD pipelines

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

## Build Flags

Global user modes existing which make certain rules apply when their argument is included within
a user request:

**Mode Flags:** `--prototype` (rapid POC), `--tdd` (test-driven)

## WIP

- eval system for testing key KPI's so we can iterate system effectively
- Github action continous improvement, monitoring code quality (placeholder usage, code duplication) with automated issue raise and address
- more agent templates, mainly focusing on specific tech i.e. typescript agent etc
- code templating system using jinja
- new pair programming paradigm

## Slash commands

Various slash commands to support developers in commont tasks, from programmatic code analysis for consistent results (non deterministic) to context aware project setup and solution planning

### Trigger workflow orchestration

claude /todo-orchestrate implementation-plan.md

### Add quality gates to your project

claude /add-code-precommit-checks

### Perform analysis on your codebase

claude /analyze-security

### Find root cause of an error

claude /analyze-root-cause "Exception: TypeError: Cannot read property 'foo' of undefined"

### explore tech solution options

claude /plan-solution whats the cheapest approach for a self hosted stt system

### create a base project using better t stack

claude /create-project [project-name] --from-todos [todos-file-path]

## 🚀 Workflow Examples

### Example 1: Complete Project Setup with Continuous Improvement

```bash
# Plan UX and product requirements
/plan-ux-prd "Mobile app for GitHub task management with real-time updates"

# Initialize project with better-t-stack.dev CLI
/create-project mobile-task-app --from-todos ./todos/todos.md

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
