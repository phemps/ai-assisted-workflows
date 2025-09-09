# AI Assisted Workflows

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

</div>

---

> **🤖 Hybrid AI-Automation System**
> Specialized workflow commands + LLM actions + Python analysis scripts + 8-Agent orchestration = comprehensive development automation

---

## Core Principles

### 🚀 Minimize Token Usage

- Offload to programmatic scripts wherever possible
- Just-in-time loading when needed (unless it impacts system accuracy)

### 🔄 Hybrid Approach

- Combines LLM intelligence with programmatic scripts for accuracy and repeatability

### 🎯 Focus on LLM Strengths, Mitigate Weaknesses

- **LLM Strengths:** Scale, contextual flexibility, pattern matching
- **LLM Weaknesses:** Repeatability and predictability

## Quick Start

### 📦 Installation

```bash
./claude-code/install.sh              # Install to current directory
./claude-code/install.sh ~            # Install globally
/setup-dev-monitoring                 # Optional: Setup unified dev logging
/add-serena-mcp                       # Recommended per project mcp lsp tool
```

For detailed installation instructions, see [Installation Guide](docs/installation.md).

## Supporting Subagent strategies

- 🚀 **8-Agent Orchestration System**
- 🧠 **Planning Mode Expert Subagents**
- ⚡ **Free Tier Agent Maximization**

For detailed agent strategy information, see [Agent Orchestration System](docs/agents.md)

## Supported Languages and Analysis Types

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

For detailed information about language support and analysis capabilities, see [Analysis Scripts](docs/analysis-scripts.md).

## Common Workflow Examples

### 1. Setup a project from scratch with monitoring and CI process

```bash
/create-project my-app --from-todos ./todos/todos.md
/setup-dev-monitoring
/add-code-precommit-checks
```

[See detailed project setup documentation](docs/workflow-examples.md#example-1-complete-project-setup-with-continuous-improvement)

### 2. Creating a simple todo list and passing it to the orchestrate command

```bash
/todo-orchestrate implementation-plan.md
```

[See detailed orchestration documentation](docs/agents.md#todo-orchestration)

### 3. Passing a simple todo list to todo-worktree for single agent focus (based on @badlogics https://github.com/badlogic/claude-commands)

```bash
/todo-worktree
```

[See detailed worktree documentation](docs/agents.md#todo-worktree-implementation)

### 4. Analyze current code base for security issues

```bash
/analyze-security
/plan-refactor  # Use results in plan-mode call
@agent-python-expert  # Invoke for expert planning
/todo-orchestrate  # Implement the plan
```

[See detailed security analysis documentation](docs/workflow-examples.md#example-5-security-analysis-and-refactoring)

## Directory Structure

```
claude-code/
├── commands/                  # Slash commands for workflows and CI
├── agents/                    # 8-agent + 2 subagent orchestration definitions
│   ├── gemini-handler.md      # Context-heavy analysis delegation
│   ├── qwen-handler.md        # Tool-intensive operations delegation
│   └── [8-core-agents...]     # Main orchestration agents
├── rules/                     # Tech stack and quality gate rules
│   └── global.claude.rules.md # Agent delegation strategy
├── docs/                      # CLI tool integration guides
│   ├── gemini-cli-guide.md    # Gemini CLI setup and usage
│   └── qwen-code-cli-guide.md # Qwen Code CLI setup and usage
├── templates/                 # Project and code generation templates
└── scripts/
    ├── analyze/               # Security, performance, architecture analysis
    ├── setup/                 # Install, monitoring, environment setup
    └── utils/                 # Cross-platform utilities and helpers

docs/
├── analysis-scripts.md        # Language support and analysis capabilities
├── agents.md                  # Agent orchestration system documentation
├── installation.md            # Installation and setup guide
├── monitoring.md              # Development and CI monitoring systems
└── workflow-examples.md       # Common workflow examples and use cases
```

## Documentation

For detailed documentation on specific components, see:

- [Installation Guide](docs/installation.md)
- [Agent Orchestration System](docs/agents.md)
- [Language Support and Analysis Capabilities](docs/analysis-scripts.md)
- [Development Monitoring System](docs/monitoring.md)
- [Workflow Examples](docs/workflow-examples.md)

## License

**MIT License** - See LICENSE file for details.

---
