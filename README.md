# Claude Code Workflows

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> **Hybrid AI-Automation System for Claude Code**  
> 12 specialized workflow commands + 25 Python analysis scripts + claude.md build switches = Production-ready development automation

Transform your Claude Code experience with measurable, automated analysis across **security**, **performance**, **architecture**, and **code quality**. Get professional-grade insights in seconds, not hours.

## 🛠️ Installation

### Prerequisites

- **Python 3.7+** (automation scripts)
- **Claude CLI** (MCP tool integration)
- **Node.js** (any version, for MCP tools)

### Installation Options

```bash
# Current directory (creates ./.claude/)
./install.sh

# User global (creates ~/.claude/)
./install.sh ~

# Custom location
./install.sh /my/project/path

# Advanced options
./install.sh --dry-run     # Preview changes
./install.sh --skip-mcp    # Skip MCP tools if no Claude CLI
./install.sh --verbose     # Debug output
```

### Handling Existing Installations

The installer automatically detects existing `.claude` directories and offers:

- **Backup & Replace:** Saves your old setup, installs fresh
- **Merge:** Preserves customizations, adds new features
- **Cancel:** Exit without changes

## 🎯 Commands Reference

### 🔍 Analysis Commands (6)

| Command                     | Purpose                      | Key Features                                                  |
| --------------------------- | ---------------------------- | ------------------------------------------------------------- |
| **`/analyze-security`**     | OWASP Top 10 security review | Vulnerability scanning, secret detection, auth analysis       |
| **`/analyze-architecture`** | System design analysis       | Coupling analysis, scalability assessment, pattern evaluation |
| **`/analyze-performance`**  | Performance optimization     | Bottleneck detection, database profiling, resource analysis   |
| **`/analyze-code-quality`** | Code metrics & quality       | Complexity analysis, dead code detection, style enforcement   |
| **`/analyze-root-cause`**   | Debug investigation          | Error patterns, execution tracing, change analysis            |
| **`/analyze-ux`**           | User experience review       | Accessibility evaluation, usability assessment                |

### 📐 Plan Commands (3)

| Command              | Purpose                         | Key Features                                                   |
| -------------------- | ------------------------------- | -------------------------------------------------------------- |
| **`/plan-solution`** | Technical challenge solving     | Research-driven solution design with 3 options                 |
| **`/plan-ux-prd`**   | UX-focused product requirements | User experience design, interface specifications               |
| **`/plan-refactor`** | Refactoring strategy            | Code improvement planning, automated analysis, risk assessment |

### 🔧 Fix Commands (3)

| Command                | Purpose                  | Key Features                                 |
| ---------------------- | ------------------------ | -------------------------------------------- |
| **`/fix-bug`**         | Issue resolution         | Root cause analysis, comprehensive debugging |
| **`/fix-performance`** | Performance optimization | Bottleneck resolution, scaling improvements  |
| **`/fix-test`**        | Test failure resolution  | CI/CD debugging, test suite optimization     |

### 🎛️ Universal Build Flags

Enhance any command with these flags (defined in claude.md):

| Flag              | Purpose                    | When to Use                                                  |
| ----------------- | -------------------------- | ------------------------------------------------------------ |
| **`--prototype`** | Rapid prototyping approach | Quick proof-of-concept development with minimal setup        |
| **`--tdd`**       | Test-driven development    | Systematic test-first development with quality gates         |
| **`--c7`**        | Context7 integration       | Framework-specific best practices (React, Vue, Django, etc.) |
| **`--seq`**       | Sequential thinking        | Complex multi-step analysis breakdown                        |
| **`--magic`**     | Magic UI components        | Pre-built UI components for rapid prototyping                |

**Example Usage:**

```bash
# Security analysis with framework best practices
/analyze-security --c7

# Feature planning with test-driven development and UI components
/plan-solution --tdd --magic --seq

# Rapid prototype development
/plan-solution --prototype --magic
```

## 🔒 Security Analysis

### OWASP Top 10 Coverage

The security analysis provides comprehensive OWASP testing criteria coverage through automated vulnerability detection.

**Example with included test_codebase:**

```bash
/analyze-security
```

**Detected Issues:**

- **A01: Injection** → SQL injection in authentication
- **A02: Cryptographic Failures** → Hardcoded JWT secrets
- **A03: Injection** → Command injection via eval()
- **A07: Identity Failures** → Weak authentication patterns

## ⚡ Analysis Scripts Architecture

**25 Analysis Scripts Organized by Category:**

```
claude/scripts/analyze/
├── security/        # OWASP Top 10 vulnerability detection
├── performance/     # Bottleneck detection, baseline establishment
├── architecture/    # Design analysis, coupling detection
├── code_quality/    # Complexity metrics, test coverage analysis
└── root_cause/      # Debugging and error pattern analysis
```

**Dependencies:** 20+ production-ready packages including bandit, safety, psutil, flake8, pylint, radon, lizard, vulture, pydeps, and networkx.

## 🤝 Contributing

This project enhances Claude Code with production-ready automation. Contributions welcome for:

- Additional analysis scripts
- New workflow commands
- Platform-specific optimizations
- MCP tool integrations

## 📄 License

MIT License - See LICENSE file for details.

---
