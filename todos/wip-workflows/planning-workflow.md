Project: AI-Assisted Workflows

A hybrid AI-automation system that provides specialized workflow commands, LLM actions, and Python analysis scripts for multi-function,
just-in-time development automation. The system installs into .claude/ directories and provides custom slash commands, 8-agent orchestration, and
dynamic quality gates that adapt to project technology stacks.

Features

- 8-Agent Orchestration System: Specialized agents for planning, implementation, quality monitoring, and version control
- 25+ Slash Commands: Analysis, planning, implementation, fixing, and setup commands
- 30+ Python Analysis Scripts: Security, performance, architecture, code quality, and root cause analysis
- Dynamic Quality Gates: Technology-aware quality enforcement that adapts to detected stack
- Cross-Platform Support: Works on macOS, Linux, and Windows development environments
- Development Monitoring: Unified logging, service orchestration, and real-time error detection
- Multi-Mode Operation: Prototype, TDD, sequential thinking, and git-enhanced search modes
- Framework-Specific Rules: Optimized workflows for React, Next.js, React Native, Expo, and more

Tech Stack

- Languages: Python 3.7+, Bash/Shell, Markdown, Node.js
- Analysis Tools: bandit, safety, semgrep, pylint, flake8, lizard, radon
- Performance Tools: psutil, memory-profiler, py-spy, networkx
- Testing: pytest, pytest-cov, black, isort
- Integration: MCP tools (sequential-thinking, grep), Claude Code CLI
- Installation: Cross-platform shell scripts with dependency management

Structure

ai-assisted-workflows/
├── claude-code/ # Main workflow system
│ ├── agents/ # 8-agent orchestration definitions (9 files)
│ ├── commands/ # Slash command implementations (25 files)
│ ├── modes/ # Operational modes (5 files)
│ ├── rules/ # Framework-specific rules (8 files)
│ ├── templates/ # Generation templates (4 files)
│ └── install.sh # Main installation script
├── shared/lib/scripts/ # Python analysis tools
│ ├── analyze/ # Analysis scripts by category (17 files)
│ ├── plan/ # Planning utilities (1 file)
│ ├── setup/ # Installation and dependency management (3 files)
│ └── utils/ # Cross-platform utilities (12 files)
├── test_codebase/ # Example projects for testing workflows
├── todos/wip-workflows/ # Experimental workflow agents (9 files)
└── docs/ # Technical documentation

Key Files:

- claude-code/install.sh - Main cross-platform installation script (941 lines)
- CLAUDE.md - Project-specific instructions for Claude Code
- README.md - User documentation and examples
- shared/lib/scripts/setup/requirements.txt - Python dependencies (42 packages)

Entry Points:

- ./claude-code/install.sh - Install to current directory (creates ./.claude/)
- ./claude-code/install.sh ~ - Install globally (creates ~/.claude/)
- /setup-dev-monitoring - Optional unified development monitoring

Architecture

This is a hybrid AI-automation system built around an 8-agent orchestration model that coordinates specialized AI agents through a central build
orchestrator. The system combines LLM intelligence with traditional automation tools to provide comprehensive development workflow automation.

Key Components:

- build-orchestrator: Central workflow coordinator managing all agent interactions and 5-phase execution
- @agent-plan-manager: Task state tracking with comprehensive state machine (16 states)
- @agent-fullstack-developer: Cross-platform implementation across web, mobile, and backend
- @agent-solution-validator: Pre-implementation validation and technical approach review
- @agent-quality-monitor: Dynamic quality gate detection that adapts to technology stack
- @agent-git-manager: Version control operations with pre-commit hook integration
- @agent-documenter: Documentation discovery and deduplication prevention
- @agent-log-monitor: Runtime error detection and monitoring integration
- @agent-cto: Critical escalation handler (3 failures → CTO → 2 attempts → human)

Commands

- Installation: ./claude-code/install.sh [options] - Cross-platform installation with MCP integration
- Analysis: /analyze-security, /analyze-architecture, /analyze-performance, /analyze-code-quality - Comprehensive analysis suite
- Planning: /plan-solution, /plan-ux-prd, /plan-refactor - Strategic planning workflows
- Implementation: /todo-orchestrate, /todo-branch, /todo-worktree - Multi-agent execution
- Monitoring: /setup-dev-monitoring - Unified development environment monitoring
- Quality: /add-code-precommit-checks - Dynamic quality gate installation
- Fixes: /fix-bug, /fix-performance - Systematic issue resolution

Build Flags: --prototype (rapid iteration), --tdd (test-driven), --seq (complex analysis), --gitgrep (enhanced search)

Testing

Framework: pytest with coverage analysis and cross-platform testing

Running Tests:

# From test_codebase directories

npm run test # JavaScript/TypeScript projects
pytest # Python analysis scripts
./test_install.py # Installation verification

Creating New Tests:
Tests are organized by category in test_codebase/ with example projects:

- Monorepo: Next.js/React/TypeScript with Convex database
- Python: Flask application examples
- Worktree: Git worktree implementation examples

# Example test structure for analysis scripts

def test_security_analysis():
"""Test security vulnerability detection"""
result = scan_vulnerabilities.analyze_project("./test_project")
assert result.vulnerabilities_found == expected_count

> Ultrathink I now want you to use that same primer workflow but exclusively target this directory todos/PRPs-agentic-eng - its a task
> documentation workflow approach for workign with code assist agent tools. I want a comprehensive, very detailed report on how it works, with
> explanation of flow through the system and how each elements contributes to that.

✻ Thinking…

The user wants me to analyze the "todos/PRPs-agentic-eng" directory to understand how it works as a task documentation workflow approach for
working with code assist agent tools. They want a comprehensive, detailed report on:

1. How it works
2. Flow through the system
3. How each element contributes to that flow
4. Use this analysis to see how to breakdown this approach
5. Use the format from @claude-code/commands/plan-ux-prd.md to create a new orchestration flow
6. Similar to @claude-code/commands/todo-orchestrate.md but specifically for creating project documentation
7. Incorporate learnings from all these approaches for a code assist agent to implement

First I need to analyze the todos/PRPs-agentic-eng directory to understand its structure and approach.

⏺ I'll analyze the todos/PRPs-agentic-eng directory to understand this task documentation workflow approach, then create a comprehensive report on
how it works and how we can adapt it for documentation orchestration.

⏺ Update Todos
⎿ ☐ Analyze todos/PRPs-agentic-eng directory structure and contents
☐ Map workflow processes and documentation approaches
☐ Identify key elements and their contributions to the system flow
☐ Compare with existing plan-ux-prd.md and todo-orchestrate.md patterns
☐ Design new documentation orchestration workflow
☐ Generate comprehensive analysis report

✻ Thinking…

I need to first explore the todos/PRPs-agentic-eng directory to understand what's in there and how it's structured. Let me start by analyzing the
directory structure and then read the key files to understand the workflow approach.

⏺ Update Todos
⎿ ☐ Analyze todos/PRPs-agentic-eng directory structure and contents
☐ Map workflow processes and documentation approaches
☐ Identify key elements and their contributions to the system flow
☐ Compare with existing plan-ux-prd.md and todo-orchestrate.md patterns
☐ Design new documentation orchestration workflow
☐ Generate comprehensive analysis report

✻ Thinking…

Let me start by exploring the structure of the todos/PRPs-agentic-eng directory to understand what's there.

⏺ List(todos/PRPs-agentic-eng)
⎿ Listed 43 paths (ctrl+r to expand)

✻ Thinking…

Looking at the directory structure, I can see this is a structured workflow system with several key components:

1. PRPs/: This seems to be the main directory containing Product Requirements Proposals or similar documentation
2. ai_docs/: Contains documentation about Claude Code functionality
3. templates/: Contains template files for different types of PRPs
4. scripts/: Contains Python scripts for running PRP workflows
5. claude_md_files/: Contains CLAUDE.md files for different tech stacks
6. example files: Showing real-world usage examples

Let me read the key files to understand the workflow better, starting with the README and main CLAUDE.md file.

✻ Thinking…

Now I'll generate the comprehensive analysis report. This needs to cover:

1. How the PRP system works
2. Flow through the system and how each element contributes
3. Analysis of how this compares to the existing plan-ux-prd.md and todo-orchestrate.md patterns

Let me compile all of this into a comprehensive report.

⏺ PRPs-Agentic-Eng: Comprehensive Analysis Report

Executive Summary

The PRPs-agentic-eng system represents a sophisticated Product Requirement Prompt (PRP) Framework designed to enable AI agents to achieve
one-pass implementation success through comprehensive context engineering. Unlike traditional Product Requirements Documents (PRDs), PRPs combine
business requirements with curated codebase intelligence, implementation blueprints, and executable validation gates.

Core Innovation: PRP = PRD + curated codebase intelligence + agent/runbook - providing the minimum viable context packet for production-ready
code generation.

System Architecture Analysis

1. Directory Structure and Organization

PRPs-agentic-eng/
├── .claude/
│ └── commands/ # 34 specialized Claude Code commands
│ ├── prp-commands/ # Core PRP creation and execution (12 commands)
│ ├── development/ # Development utilities (6 commands)
│ ├── code-quality/ # Review and refactoring (3 commands)
│ ├── git-operations/ # Smart Git operations (3 commands)
│ ├── rapid-development/ # Parallel creation and experimental (10 commands)
│ └── typescript/ # TypeScript-specific workflows (4 commands)
├── PRPs/
│ ├── templates/ # Structured PRP templates with validation
│ ├── scripts/ # Python runner for PRP execution
│ ├── ai_docs/ # Curated Claude Code documentation (14 files)
│ └── \*.md # Active and example PRPs
├── claude_md_files/ # Framework-specific CLAUDE.md examples (7 files)
├── CLAUDE.md # Project-specific AI guidance
└── pyproject.toml # Python package configuration

2. Core Workflow Processes

A. PRP Creation Workflow

1. Research Phase (/prp-base-create)

   - Spawn parallel subagents for codebase analysis
   - Conduct external documentation research at scale
   - Build comprehensive context through batch tool utilization
   - Apply "No Prior Knowledge" test for context completeness

2. Template Population

   - Use structured templates (prp_base.md, prp_spec.md, prp_planning.md)
   - Fill context sections with specific, actionable references
   - Create dependency-ordered implementation tasks
   - Define 4-level validation gates (syntax, unit, integration, domain-specific)

3. Quality Validation

   - Context completeness check
   - Template structure compliance
   - Information density standards verification

B. PRP Execution Workflow

1. Load and Plan (/prp-base-execute)

   - Read PRP file completely
   - Create comprehensive implementation plan using TodoWrite
   - Spawn subagents with PRP-inspired prompts for parallel work

2. Progressive Implementation

   - Follow Implementation Tasks sequence from PRP
   - Use specific patterns and examples referenced in PRP context
   - Create files in locations specified by desired codebase tree

3. 4-Level Validation System

   - Level 1: Syntax & style (ruff, mypy, formatting)
   - Level 2: Unit tests (pytest with coverage)
   - Level 3: Integration testing (API calls, database validation)
   - Level 4: Domain-specific validation (MCP servers, performance testing)

4. Completion Verification

   - Final validation checklist execution
   - Success criteria verification from "What" section
   - Anti-pattern avoidance confirmation

5. Key System Elements and Their Contributions

Templates System

- prp_base.md: Comprehensive 317-line template with validation loops
- prp_spec.md: Specification-focused template
- prp_planning.md: Planning template with diagram support
- Contribution: Ensures structural consistency and completeness across all PRPs

AI Documentation Curation (ai_docs/)

- 14 curated files covering Claude Code functionality
- Context injection: Pipes library documentation directly into PRPs
- Contribution: Eliminates guesswork by providing exact documentation references

Command Orchestration (34 commands)

- Specialized workflows: Each command handles specific aspects of development
- Parallel execution: Commands spawn subagents for concurrent work
- Pattern consistency: All commands follow PRP methodology
- Contribution: Provides systematic approach to complex development tasks

Python Runner Script (prp_runner.py)

- 3 execution modes: Interactive, JSON output, streaming JSON
- Meta-prompt injection: Adds workflow guidance to every PRP execution
- Claude Code integration: Direct integration with allowedTools and output formatting
- Contribution: Enables automated and programmatic PRP execution

4. Flow Through the System

Creation Flow:

User Request → Research Phase → Template Selection → Context Population → Quality Gates → PRP File → Repository Storage
↓ ↓ ↓ ↓ ↓ ↓ ↓
Spawn Agents → Codebase Analysis → Structured Format → Actionable Context → Validation → \*.md File → Ready for Execution

Execution Flow:

PRP File → Load Context → Implementation Plan → Progressive Build → Validation Gates → Working Code → Completion
↓ ↓ ↓ ↓ ↓ ↓ ↓
Runner → Parse Template → TodoWrite Breakdown → Follow Patterns → 4-Level Testing → Deliverable → Move to Completed/

Comparison with Existing AI-Assisted Workflows

vs. plan-ux-prd.md

| Aspect      | plan-ux-prd.md                     | PRPs-agentic-eng                         |
| ----------- | ---------------------------------- | ---------------------------------------- |
| Scope       | UX/UI focused PRD generation       | Full-stack implementation PRPs           |
| Context     | User research and design specs     | Complete codebase intelligence           |
| Output      | Traditional PRD document           | Executable implementation guide          |
| Validation  | 5-item UX quality checklist        | 4-level progressive validation gates     |
| Process     | 2-phase: gather info → generate    | Multi-phase: research → create → execute |
| Agent Usage | Single agent with script execution | Multiple parallel subagents              |

Key Insight: PRPs extend beyond UI/UX requirements to comprehensive implementation context.

vs. todo-orchestrate.md

| Aspect           | todo-orchestrate.md                       | PRPs-agentic-eng                             |
| ---------------- | ----------------------------------------- | -------------------------------------------- |
| Purpose          | Execute existing implementation plans     | Create and execute comprehensive PRPs        |
| Agent System     | 8-agent orchestration with CTO escalation | Command-driven with parallel subagents       |
| Quality Gates    | Dynamic tech stack detection              | 4-level standardized validation              |
| Context Source   | Implementation plan files                 | Self-contained PRP with curated intelligence |
| Failure Handling | 3 failures → CTO → human escalation       | Pattern-based fixing with validation retry   |
| Scope            | Build orchestration                       | End-to-end development workflow              |

Key Insight: PRPs provide upfront context engineering vs. runtime orchestration.
