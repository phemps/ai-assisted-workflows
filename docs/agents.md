# Agent Orchestration System

## 🚀 8-Agent Orchestration System

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

## 🧠 Planning Mode Expert Subagents

| Subagent                    | Specialization         | Purpose                                       |
| :-------------------------- | :--------------------- | :-------------------------------------------- |
| **python-expert**           | Python Development     | Expert planning for Python tasks              |
| **typescript-expert**       | TypeScript Development | Expert planning for TypeScript tasks          |
| **rag-architecture-expert** | RAG Systems            | Architecture planning for RAG implementations |
| **terraform-gcp-expert**    | Infrastructure         | Terraform and GCP infrastructure planning     |

## ⚡ Session Uptime Maximization Subagents

| Subagent           | Purpose                   | Benefits                                       |
| :----------------- | :------------------------ | :--------------------------------------------- |
| **gemini-handler** | Context-heavy analysis    | Offload large context operations to Gemini CLI |
| **qwen-handler**   | Tool-intensive operations | Delegate high tool-usage tasks to Qwen CLI     |

## ⚡ Free Tier Agent Maximization

**Strategic subagents that extend Claude Code session uptime by leveraging free AI CLI tools:**

| Agent                     | Specialization            | Free Tier Benefits                                 |
| :------------------------ | :------------------------ | :------------------------------------------------- |
| **@agent-gemini-handler** | 🧠 Context-Heavy Analysis | 1,000 requests/day • 1M token context • OAuth      |
| **@agent-qwen-handler**   | 🔧 Tool-Heavy Operations  | 2,000 requests/day • Request-based billing • OAuth |

**Smart Delegation Triggers:**

- **Context-heavy tasks** (>5 files, >50k tokens) → `@agent-gemini-handler`
- **Tool-intensive workflows** (>100 operations, batch processing) → `@agent-qwen-handler`
- **Automatic fallback** to direct Claude Code execution on agent limits

## Todo Orchestration

The `/todo-orchestrate` command executes complete build workflows using intelligent sub-agent coordination with quality gates.

### Usage

```bash
/todo-orchestrate <IMPLEMENTATION_PLAN_PATH> [--prototype] [--parallel] [--max-retries=3]
```

### Workflow Orchestration Logic

The system follows a comprehensive orchestration workflow:

1. **Initial Setup** - Parse implementation plan and create task registry
2. **Main Orchestration Loop** - Execute continuous task processing through all phases until all tasks completed
3. **Task Selection** - Get next highest priority pending task in current phase
4. **Validation** - Validate technical approach with appropriate quality expectations
5. **Implementation** - Implement feature and check for runtime errors
6. **Quality Verification** - Execute dynamic quality gates based on tech stack
7. **Commit** - Attempt to commit changes with proper error handling
8. **Failure Escalation** - Escalate to CTO agent after 3 failures

### Key Features

- **Continuous Orchestration**: Single command runs entire workflow to completion
- **Dynamic Quality Gates**: Adapts to project tech stack automatically
- **Prototype Mode Support**: Automatic test skipping with --prototype flag
- **Intelligent Failure Handling**: 3 failures → CTO → 2 attempts → human escalation
- **State Persistence**: Progress tracked throughout execution
- **Phase Testing Plans**: Automatic generation of user testing plans after each phase

## Todo Worktree Implementation

The `/todo-worktree` command provides a structured workflow to transform vague todos into implemented features using git worktrees and subagent assignment.

### Workflow Phases

1. **INIT** - Check for task resume, initialize project description if needed
2. **SELECT** - Choose a todo from todos/todos.md and create a git worktree
3. **REFINE** - Research codebase and refine implementation plan
4. **IMPLEMENT** - Execute the implementation plan with validation
5. **COMMIT** - Create PR and clean up worktree

This approach supports task isolation, resumption, and clean commit history.
