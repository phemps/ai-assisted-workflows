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
- **Claude Code**
- **Node.js** (any version, for MCP tools, optional)

### Recommended Optionals

- **Context7 MCP** best practice documentation to support code generation
- **Sequential thinking MCP** use to breakdown complext tasks (can augment or cheaper alternative for non reasoning models)

- **Todo workflow** CC command from [badlogic](https://github.com/badlogic/claude-commands/blob/main/todo.md) - pairs well with the workflows, particularly /plan-\* as they produce todo.md lists. It's a more efficient version of CC plan mode/todos

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

### Handling Existing .Claude Installations

**Automatic Backup:** All installation options automatically create a timestamped backup of your existing installation before making any changes.

The installer automatically detects existing `.claude` directories and the interactive terminal install will offer four options:

1. **Fresh Install:** install fresh (complete replacement)
2. **Merge:** Preserve user customizations while adding new features (no overwrites)
3. **Update Workflows Only:** Update built-in commands and scripts while preserving custom commands and all other files (recommended for updates)
4. **Cancel:** Exit without changes

### Python Libraries Installed

**Security Analysis:**

- `bandit` - Security linting and vulnerability detection
- `safety` - Known vulnerability scanning against CVE database
- `semgrep` - Static analysis security scanner

**Performance Analysis:**

- `psutil` - System and process monitoring utilities
- `memory-profiler` - Memory usage profiling and tracking
- `py-spy` - Python profiler for performance analysis (Unix only)

**Code Quality Analysis:**

- `flake8` - Python style guide enforcement (PEP 8)
- `pylint` - Comprehensive code analysis and linting
- `radon` - Code complexity metrics (cyclomatic, halstead)
- `lizard` - Advanced complexity analysis for multiple languages
- `vulture` - Dead code detection and cleanup
- `mccabe` - Complexity checker for functions

**Architecture Analysis:**

- `pydeps` - Dependency analysis and visualization
- `networkx` - Graph analysis for architectural patterns

**Multi-Language Testing Framework Detection:**

- `pytest` - Python testing framework detection and performance benchmarks
- `pytest-cov` - Test coverage analysis across multiple programming languages

**Development Tools:**

- `black` - Opinionated code formatting
- `isort` - Import statement organization

**Core Dependencies:**

- `requests` - HTTP requests for external API integrations
- `python-dotenv` - Environment variable management

### MCP Tools (Optional Enhancement)

When Claude CLI is available, these MCP tools are automatically installed to enhance workflow capabilities:

**Available MCP Tools:**

- **`sequential-thinking`** - Multi-step reasoning and analysis breakdown (enables `--seq` flag)
- **`filesystem`** - Advanced file operations and project navigation
- **`puppeteer`** - Browser automation for web analysis and testing

**MCP Tool Benefits:**

- **Context7** - Framework-specific best practices and contextually accurate language detection (React, Vue, Django, Spring, etc.) via `--c7` flag
- **Magic UI** - Pre-built component library access via `--magic` flag
- **Sequential Thinking** - Complex problem breakdown via `--seq` flag
- **Browser Tools** - Automated web testing and analysis capabilities

**Context7 ensures our analysis scripts provide contextually correct results** by understanding:

- Framework conventions (React hooks, Django models, Spring annotations)
- Language-specific patterns (Go interfaces, Rust ownership, TypeScript generics)
- Build tool configurations (Maven, Gradle, npm, Cargo)

```bash
# Install with MCP tools (requires Claude CLI + Node.js)
./install.sh

# Install without MCP tools (Python scripts only)
./install.sh --skip-mcp
```

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

## 🌐 Programming Language Support

### Universal Analysis (All Languages)

**Security:** Vulnerability scanning, secret detection, authentication analysis  
**Architecture:** Dependency analysis, coupling detection, scalability assessment  
**Code Quality:** Complexity metrics (via Lizard), dead code detection

### Language-Specific Analysis

**Supported Languages:** Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby, C/C++, Swift, Kotlin

| Language       | Test Coverage            | Performance Baseline         | Import Analysis      | Bottleneck Detection     |
| -------------- | ------------------------ | ---------------------------- | -------------------- | ------------------------ |
| **Python**     | ✅ pytest, coverage      | ✅ cProfile, memory-profiler | ✅ import patterns   | ✅ AST analysis          |
| **JavaScript** | ✅ jest, nyc, c8         | ✅ npm scripts, profiling    | ✅ import/require    | ✅ performance patterns  |
| **TypeScript** | ✅ jest, nyc, c8         | ✅ npm scripts, profiling    | ✅ import patterns   | ✅ performance patterns  |
| **Java**       | ✅ junit, jacoco         | ✅ maven/gradle, JFR         | ✅ import statements | ✅ performance patterns  |
| **Go**         | ✅ go test, coverage     | ✅ go build, benchmarks      | ⚠️ Basic             | ✅ performance patterns  |
| **Rust**       | ✅ cargo test, tarpaulin | ✅ cargo bench, flamegraph   | ⚠️ Basic             | ✅ performance patterns  |
| **C#**         | ✅ dotnet test, coverlet | ✅ dotnet build, profiling   | ✅ using statements  | ✅ performance patterns  |
| **Others**     | ⚠️ Basic detection       | ⚠️ Basic detection           | ❌                   | ✅ file pattern analysis |

**Context7 Integration:** Use `--c7` flag with any analysis command for framework-specific best practices and contextually accurate language detection.

## 🤝 Contributing

This project enhances Claude Code with production-ready automation. Contributions welcome for:

- Additional analysis scripts
- New workflow commands
- Platform-specific optimizations
- MCP tool integrations

## 📄 License

MIT License - See LICENSE file for details.

---
