# AI Assisted Workflows

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

</div>

---

> **🤖 Hybrid AI-Automation System**
> Specialized workflow commands + LLM actions + Python analysis scripts + 8-Agent orchestration = comprehensive development automation with intelligent code quality management

---

## 🚀 Quick Start

### 📦 Installation

```bash
./claude-code/install.sh              # Install to current directory
./claude-code/install.sh ~            # Install globally
/setup-dev-monitoring                 # Optional: Setup unified dev logging
/setup-ci-monitoring                  # Optional: Git actions quality checks (WIP, not ready yet)
/add-serena-mcp                       # Recommended per project mcp lsp tool
```

### 🔧 Dependencies

Due to the programmatic analysis scripts, there's quite a lot of dependencies installed.
Full list of libraries used and languages supported found here: [analysis script details](https://github.com/adam-versed/ai-assisted-workflows/docs/analysis-scripts.md)

### 🌐 Supported Languages

**Core Support:** Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby, C/C++, Swift, Kotlin, SQL, and more

| Language            | Test Coverage            | Performance Baseline          | Import Analysis         | Bottleneck Detection    |
| :------------------ | :----------------------- | :---------------------------- | :---------------------- | :---------------------- |
| **Python**          | ✅ pytest, coverage      | ✅ cProfile, memory-profiler  | ✅ import patterns      | ✅ AST analysis         |
| **JavaScript**      | ✅ jest, nyc, c8         | ✅ npm scripts, profiling     | ✅ import/require       | ✅ performance patterns |
| **TypeScript**      | ✅ jest, nyc, c8         | ✅ npm scripts, profiling     | ✅ import patterns      | ✅ performance patterns |
| **Java**            | ✅ junit, jacoco         | ✅ maven/gradle, JFR          | ✅ import statements    | ✅ performance patterns |
| **Go**              | ✅ go test, coverage     | ✅ go build, benchmarks       | ✅ import patterns      | ✅ performance patterns |
| **Rust**            | ✅ cargo test, tarpaulin | ✅ cargo bench, flamegraph    | ✅ use statements       | ✅ performance patterns |
| **C#**              | ✅ dotnet test, coverlet | ✅ dotnet build, profiling    | ✅ using statements     | ✅ performance patterns |
| **SQL**             | ✅ SQLFluff integration  | ✅ Query performance analysis | ✅ Schema dependencies  | ✅ Query optimization   |
| **Other Languages** | ✅ Framework detection   | ✅ Language-specific patterns | ✅ Full import analysis | ✅ Performance patterns |

## 🎯 Core Principles

### 🚀 **Minimize Token Usage**

- Offload to programmatic scripts wherever possible
- Just-in-time loading when needed (unless it impacts system accuracy)

### 🔄 **Hybrid Approach**

- Combines LLM intelligence with programmatic scripts for accuracy and repeatability

### 🌐 **Platform Agnostic**

- Not achieved yet, but once main prompts have stabilized, will use a templating system
- Allow people to roll out commands to any supported platform
- Starting with Claude Code, Opencode will be next

### 🎯 **Focus on LLM Strengths, Mitigate Weaknesses**

- **LLM Strengths:** Scale, contextual flexibility, pattern matching
- **LLM Weaknesses:** Repeatability and predictability

---

## ✨ Core Features

_Implemented through slash commands, agents, rules/user modes, programmatic scripts and git actions - creating a flexible toolkit that involves the developer at the heart, not abstracting them away._

### 🔍 **Intelligent Code Analysis**

- 🧠 Proactive code duplication detection using CodeBERT embeddings _(WIP)_
- 🔍 Semantic pattern matching with Serena MCP integration
- 📊 Confidence-scored similarity analysis with configurable thresholds
- 🌐 Multi-language support via Language Server Protocol

### 🚀 **8-Agent Orchestration System**

| Agent                   | Role                | Responsibility                              |
| :---------------------- | :------------------ | :------------------------------------------ |
| **plan-manager**        | 📋 Project Manager  | Task state and progress tracking            |
| **fullstack-developer** | 💻 Developer        | Cross-platform implementation               |
| **solution-validator**  | ✅ Architect        | Pre-implementation validation               |
| **quality-monitor**     | 🔍 QA Engineer      | Dynamic quality gate detection              |
| **git-manager**         | 🌿 DevOps           | Version control operations                  |
| **documenter**          | 📚 Technical Writer | Documentation discovery and management      |
| **log-monitor**         | 📊 Site Reliability | Runtime error detection                     |
| **cto**                 | 🎯 Escalation       | Critical handler (3 failures → CTO → human) |

### ⚡ **Dynamic Quality Gates**

```bash
/add-code-precommit-checks
```

- 🔍 Automatic detection of build, test, and lint commands
- 🛠️ Tech stack-aware validation (Node.js, Python, Rust, Go, etc.)
- ⚙️ Configurable quality thresholds per project
- 🔄 Integration with existing CI/CD pipelines

---

## 📊 Development Monitoring System

### 🖥️ **Visual Dashboard Overview**

_After running `/setup-dev-monitoring`, you'll see:_

<div align="center">

![Stack Detection](images/stack-detection-analysis.png)
_Smart stack detection: Auto-identifies React Native + Expo, tRPC + TypeScript, and sets up optimal monitoring_

![Unified Logs](images/dev-logs-unified.png)
_Timestamped unified logging: All services stream to `/dev.log` - Claude can query logs directly_

![Service Status](images/service-status-dashboard.png)
_Real-time service monitoring: Live status for API and Mobile services with health indicators_

</div>

### 🎯 **Key Monitoring Features**

| Feature                    | Description                                       | Benefit                   |
| :------------------------- | :------------------------------------------------ | :------------------------ |
| 🚀 **Live Service Status** | Real-time health indicators for all services      | Immediate issue detection |
| 📊 **Unified Logging**     | All logs stream to `/dev.log` with timestamps     | Centralized debugging     |
| 🔍 **Smart Analysis**      | Auto-detects tech stack and configures monitoring | Zero-config setup         |
| ⚡ **Hot Reload Tracking** | File watching and change detection                | Development efficiency    |
| 🛠️ **Command Suite**       | `make dev`, `make status`, `make logs`            | Streamlined workflow      |

---

## 🏗️ Build Flags

_Global user modes that activate when their argument is included in a user request:_

### 🎛️ **Available Mode Flags**

| Flag          | Mode               | Description                          |
| :------------ | :----------------- | :----------------------------------- |
| `--prototype` | 🚀 **Rapid POC**   | Fast prototyping with minimal setup  |
| `--tdd`       | ✅ **Test-Driven** | Comprehensive test-first development |

---

## 🚧 Work In Progress

### 🔬 **Evaluation System**

- Testing key KPIs for effective system iteration

### 🤖 **GitHub Actions CI**

- Continuous improvement monitoring
- Code quality tracking (placeholder usage, code duplication)
- Automated issue creation and resolution

### 🛠️ **Agent Templates**

- More specialized agent templates
- Technology-specific agents (TypeScript, etc.)

### 📋 **Code Templating**

- Jinja-based templating system

### 👥 **Pair Programming**

- New paradigm development

---

## 💻 Slash Commands

_Various slash commands to support developers in common tasks - from programmatic code analysis for consistent results to context-aware project setup and solution planning._

### 🎯 **Core Commands**

#### **Workflow Orchestration**

```bash
claude /todo-orchestrate implementation-plan.md
```

#### **Quality Gates**

```bash
claude /add-code-precommit-checks
```

#### **Code Analysis**

```bash
claude /analyze-security
```

#### **Root Cause Analysis**

```bash
claude /analyze-root-cause "Exception: TypeError: Cannot read property 'foo' of undefined"
```

#### **Solution Planning**

```bash
claude /plan-solution whats the cheapest approach for a self hosted stt system
```

#### **Project Creation**

```bash
claude /create-project [project-name] --from-todos [todos-file-path]
```

---

## 🚀 Workflow Examples

### 📱 **Example 1: Complete Project Setup with Continuous Improvement**

```bash
# 1. Plan UX and product requirements
/plan-ux-prd "Mobile app for GitHub task management with real-time updates"

# 2. Initialize project with better-t-stack.dev CLI
/create-project mobile-task-app --from-todos ./todos/todos.md

# 3. Setup development monitoring
/setup-dev-monitoring

# 4. Add quality gates
/add-code-precommit-checks
```

### 🔬 **Example 2: Research and Implement with Quality Assurance**

```bash
# 1. Research and plan approaches with TDD mode
/plan-solution --tdd "Add real-time updates using WebSockets"

# 2. Implement with continuous quality monitoring
/todo-orchestrate --seq
```

**System automatically:**

- ✅ Detects code duplications during implementation
- ✅ Runs appropriate quality gates based on tech stack
- ✅ Escalates complex issues to CTO agent
- ✅ Generates refactoring suggestions and PRs

### 🔧 **Example 3: Existing Project Integration**

```bash
# 1. Analyze existing codebase
/analyze-architecture
/analyze-code-quality
/analyze-security

# 2. Setup continuous improvement for existing project
/setup-ci-monitoring  # (WIP, not ready yet)
```

**The system will:**

- 🔍 Detect your current tech stack automatically
- ⚙️ Configure appropriate similarity thresholds
- 🛠️ Set up quality gates matching your build tools
- 📊 Begin monitoring for code quality improvements

---

## 📁 Directory Structure

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

_Feel free to explore and adapt these for experimentation._

---

## 🙏 Acknowledgments

### 🌟 **Inspirations & Adaptations**

| Component                  | Credit                                                                     | Source                              |
| :------------------------- | :------------------------------------------------------------------------- | :---------------------------------- |
| **Todo Workflow**          | [@badlogic](https://github.com/badlogic/claude-commands/blob/main/todo.md) | Efficient Claude Commands plan mode |
| **Development Monitoring** | [@mitsuhiko](https://github.com/mitsuhiko)                                 | Unified logging approach            |
| **Agent Orchestration**    | Community                                                                  | Distributed system design patterns  |

---

## 📄 License

**MIT License** - See LICENSE file for details.

---

<div align="center">

_Built with ❤️ for the developer community_

</div>
