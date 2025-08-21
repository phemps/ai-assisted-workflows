# Workflow Examples

## 📱 Example 1: Complete Project Setup with Continuous Improvement

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

## 🔬 Example 2: Research and Implement with Quality Assurance

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

## 🔧 Example 3: Existing Project Integration

```bash
# 1. Analyze existing codebase
/analyze-architecture
/analyze-code-quality
/analyze-security

# 2. Setup continuous improvement for existing project
/setup-ci-monitoring
```

**The system will:**

- 🔍 Detect your current tech stack automatically
- ⚙️ Configure appropriate similarity thresholds
- 🛠️ Set up quality gates matching your build tools
- 📊 Begin monitoring for code quality improvements

## 🎯 Example 4: Task Implementation with Worktree Isolation

```bash
# Implement a specific task in an isolated worktree
/todo-worktree
```

This approach allows you to:
- Work on tasks in isolation
- Easily resume interrupted work
- Maintain clean commit history
- Switch between tasks seamlessly

## 🔍 Example 5: Security Analysis and Refactoring

```bash
# 1. Analyze codebase for security issues
/analyze-security

# 2. Use results in plan-mode call
/plan-refactor

# 3. Ask it to invoke @agent-python-expert for expert planning
@agent-python-expert Please review this security analysis and provide expert planning for the identified issues.

# 4. Pass to /todo-orchestrate to implement
/todo-orchestrate security-remediation-plan.md
```

This workflow ensures:
- Comprehensive security analysis
- Expert-level planning for complex issues
- Automated implementation with quality gates
- Proper testing and validation
