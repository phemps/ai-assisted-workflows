# Programming Language Support and Analysis Capabilities

## Supported Languages

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

## Python Libraries and Dependencies

### Core Dependencies

- `python-dotenv>=0.19.0` - Environment variable management
- `requests>=2.25.0` - HTTP requests for external API integrations
- `pathlib2>=2.3.5` - Backport for older Python versions

### Security Analysis

- `bandit>=1.7.0` - Python security linting
- `safety>=2.0.0` - Vulnerability scanning against CVE database
- `semgrep>=1.45.0` - Semantic static analysis security scanner (replacing bespoke patterns)
- `detect-secrets>=1.4.0` - Hardcoded secrets detection (replacing regex patterns)
- `sqlfluff>=2.3.0` - SQL linting and security analysis

### Performance Analysis

- `psutil>=5.8.0` - System and process monitoring utilities
- `memory-profiler>=0.60.0` - Memory usage profiling and tracking
- `py-spy>=0.3.0` - Python profiler for performance analysis (Unix only)
- `perflint>=0.7.0` - Performance anti-pattern detection (PERF error codes)
- `flake8-comprehensions>=3.10.0` - List/dict comprehension performance rules
- `flake8-bugbear>=23.3.0` - Bug and performance issue detection

### Code Quality Analysis

- `flake8>=4.0.0` - Python style guide enforcement (PEP 8)
- `pylint>=2.12.0` - Comprehensive code analysis and linting
- `radon>=5.1.0` - Code complexity metrics (cyclomatic, halstead)
- `lizard>=1.17.0` - Advanced complexity analysis for multiple languages
- `vulture>=2.3` - Dead code detection and cleanup
- `mccabe>=0.6.0` - Complexity checker for functions

### Architecture Analysis

- `pydeps>=1.10.0` - Dependency analysis and visualization
- `networkx>=2.6.0` - Graph analysis for architectural patterns

### Development and Testing

- `pytest>=6.2.0` - Python testing framework
- `pytest-cov>=3.0.0` - Python test coverage measurement
- `black>=22.0.0` - Opinionated code formatting
- `isort>=5.10.0` - Import statement organization

### Foundation Layer - Agent Orchestration

- `pyyaml>=6.0` - YAML configuration parsing
- `jinja2>=3.0.0` - Template rendering for dynamic commands
- `click>=8.0.0` - CLI framework for command processing
- `rich>=12.0.0` - Rich terminal output and progress bars
- `typing-extensions>=4.0.0` - Enhanced type hints for Python <3.9

### Foundation Layer - Cross-Platform Support

- `platformdirs>=2.5.0` - Cross-platform directory detection
- `shutil-backports>=1.0.0` - Enhanced file operations (Python <3.8)
- `subprocess32>=3.5.4` - Backport subprocess improvements (Python <3.2)

### Foundation Layer - State Management

- `filelock>=3.8.0` - File-based locking for task coordination
- `watchdog>=2.1.0` - File system monitoring for dynamic updates

### Continuous Improvement Framework

- `faiss-cpu>=1.7.0` - Vector similarity search for semantic duplicate detection
- `transformers>=4.21.0` - Pre-trained models for code analysis
- `torch>=1.12.0` - Deep learning framework for embeddings
- `sentence-transformers>=2.2.0` - Sentence embeddings for code similarity
- `tokenizers>=0.13.0` - Fast tokenization for code analysis
- `numpy>=1.21.0` - Scientific computing and array operations
- `scipy>=1.7.0` - Advanced scientific computing
- `scikit-learn>=1.0.0` - Machine learning algorithms
- `datasets>=2.0.0` - Dataset management and processing
- `uvx>=0.0.1` - Python package executor for MCP integration
- `dataclasses>=0.6` - Backport for older Python versions

### Continuous Improvement Framework

- `multilspy>=0.1.0` - Language Server Protocol support for multi-language symbol extraction
- Framework path reorganization: CI components moved from `shared/lib/scripts/continuous-improvement/` to `shared/ci/`
- Integration with existing analysis tools for semantic duplicate detection
- GitHub Actions workflow support for automated code quality monitoring

### Frontend Analysis (Required - Node.js)

These dependencies are automatically installed by the installer via npm:
- `eslint@latest` - JavaScript/TypeScript linting
- `@typescript-eslint/parser@latest` - TypeScript parsing for ESLint
- `@typescript-eslint/eslint-plugin@latest` - TypeScript-specific linting rules
- `eslint-plugin-react@latest` - React-specific linting rules
- `eslint-plugin-react-hooks@latest` - React Hooks linting rules
- `eslint-plugin-import@latest` - Import/export syntax checking
- `eslint-plugin-vue@latest` - Vue.js-specific linting rules
- `eslint-plugin-svelte@latest` - Svelte-specific linting rules

## Analysis Scripts Architecture

The analysis system is organized under `shared/` with the following structure:

```
shared/
├── analyzers/               # 19 Analysis Tools by Category
│   ├── security/           # Security vulnerability detection
│   │   ├── semgrep_analyzer.py
│   │   └── detect_secrets_analyzer.py
│   ├── performance/        # Performance analysis and optimization
│   │   ├── profile_code.py
│   │   ├── performance_baseline.py
│   │   ├── analyze_frontend.py
│   │   ├── flake8_performance_analyzer.py
│   │   └── sqlfluff_analyzer.py
│   ├── architecture/       # Design and architectural analysis
│   │   ├── dependency_analysis.py
│   │   ├── coupling_analysis.py
│   │   ├── scalability_check.py
│   │   └── pattern_evaluation.py
│   ├── quality/           # Code quality and complexity metrics
│   │   ├── complexity_lizard.py
│   │   ├── code_duplication_analyzer.py
│   │   ├── coverage_analysis.py
│   │   ├── pattern_classifier.py
│   │   └── analysis_engine.py
│   └── root_cause/        # Debugging and error analysis
│       ├── error_patterns.py
│       ├── recent_changes.py
│       └── trace_execution.py
├── core/base/             # BaseAnalyzer framework
├── ci/                    # Continuous improvement framework
├── setup/                 # Installation and dependency management
├── generators/            # Code generation utilities
├── tests/                 # Integration tests
└── utils/                 # Shared utilities
```

### Security Analysis (2 Analyzers)

**`semgrep_analyzer.py`** - Semantic Static Analysis Security Scanner
- OWASP Top 10 vulnerability detection using Semgrep's semantic analysis
- Multi-language support with native language parsers
- Real-time rule updates from security community
- Replaces bespoke regex patterns with established semantic analysis

**`detect_secrets_analyzer.py`** - Hardcoded Secrets Detection
- Identifies API keys, passwords, tokens in source code
- Uses entropy-based detection and known patterns
- Supports multiple secret types and custom patterns
- Replaces manual regex-based secret scanning

### Performance Analysis (5 Analyzers)

**`profile_code.py`** - Code Profiling and Bottleneck Detection
- Performance profiling using cProfile and memory-profiler
- Identifies CPU and memory bottlenecks
- Generates performance reports with hotspot analysis
- Cross-platform profiling support

**`performance_baseline.py`** - Performance Baseline Establishment
- Establishes performance baselines for critical code paths
- Tracks performance regression over time
- Supports custom performance metrics and thresholds
- Integration with CI/CD pipelines

**`analyze_frontend.py`** - Frontend Performance Analysis
- JavaScript/TypeScript performance analysis
- Bundle size analysis and optimization suggestions
- React/Vue/Angular specific performance patterns
- Integration with ESLint performance plugins

**`flake8_performance_analyzer.py`** - Python Performance Anti-patterns
- Uses flake8-bugbear and perflint for performance issue detection
- Identifies inefficient list comprehensions and loops
- Detects memory leaks and resource management issues
- PERF error codes for systematic performance improvements

**`sqlfluff_analyzer.py`** - SQL Performance and Security Analysis
- SQL query performance analysis using SQLFluff
- Identifies inefficient queries and missing indexes
- SQL security vulnerability detection
- Multi-dialect SQL support

### Architecture Analysis (4 Analyzers)

**`dependency_analysis.py`** - Dependency Graph Analysis
- Analyzes import dependencies and circular references
- Generates dependency graphs using NetworkX
- Identifies architectural violations and tight coupling
- Supports multiple languages and module systems

**`coupling_analysis.py`** - Module Coupling Metrics
- Measures coupling between modules and classes
- Identifies high coupling that affects maintainability
- Provides refactoring suggestions for decoupling
- Generates coupling heat maps and reports

**`scalability_check.py`** - Scalability Assessment
- Analyzes code patterns for scalability issues
- Identifies performance bottlenecks under load
- Database query analysis for scalability
- Concurrent programming pattern analysis

**`pattern_evaluation.py`** - Architecture Pattern Evaluation
- Evaluates adherence to architectural patterns (MVC, DDD, etc.)
- Identifies anti-patterns and code smells
- Suggests architectural improvements
- Pattern compliance scoring and reporting

### Quality Analysis (5 Analyzers)

**`complexity_lizard.py`** - Code Complexity Analysis
- Uses Lizard for multi-language complexity analysis
- Cyclomatic complexity, Halstead metrics, and NLOC
- Identifies overly complex functions and classes
- Supports Python, JavaScript, Java, C++, and more

**`code_duplication_analyzer.py`** - Duplicate Code Detection
- Identifies code duplication across files and projects
- Semantic similarity analysis using embeddings
- Refactoring suggestions for duplicate code elimination
- Configurable similarity thresholds

**`coverage_analysis.py`** - Test Coverage Analysis
- Multi-language test coverage analysis
- Integration with pytest, jest, junit, and other frameworks
- Coverage gap identification and recommendations
- Historical coverage trend analysis

**`pattern_classifier.py`** - Code Pattern Classification
- Classifies code patterns and architectural elements
- Identifies design patterns in use
- Anti-pattern detection and remediation suggestions
- Machine learning-based pattern recognition

**`analysis_engine.py`** - Unified Quality Analysis Engine
- Orchestrates multiple quality analyzers
- Aggregates results and provides unified scoring
- Quality gate enforcement for CI/CD pipelines
- Customizable quality rules and thresholds

### Root Cause Analysis (3 Analyzers)

**`error_patterns.py`** - Error Pattern Analysis
- Analyzes error logs and stack traces for patterns
- Identifies common failure modes and root causes
- Correlation analysis between errors and code changes
- Automated error categorization and prioritization

**`recent_changes.py`** - Recent Change Impact Analysis
- Analyzes git history for potential error causes
- Correlates recent changes with system failures
- Identifies high-risk changes and contributors
- Change impact assessment and blast radius analysis

**`trace_execution.py`** - Execution Trace Analysis
- Analyzes execution traces for performance and correctness
- Identifies execution paths leading to errors
- Performance bottleneck identification in traces
- Distributed tracing support for microservices

## Security Analysis Details

### OWASP Top 10 Coverage

The security analysis provides comprehensive OWASP testing criteria coverage through automated vulnerability detection using Semgrep's semantic analysis engine.

**Example with included test_codebase:**

```bash
/analyze-security
```

**Detected Issues:**

- **A01: Injection** → SQL injection in authentication (detected by Semgrep semantic analysis)
- **A02: Cryptographic Failures** → Hardcoded JWT secrets (detected by detect-secrets)
- **A03: Injection** → Command injection via eval() (detected by Semgrep patterns)
- **A07: Identity Failures** → Weak authentication patterns (detected by Semgrep rules)

## Programming Language Support

### Universal Analysis (All Languages)

**Security:** Vulnerability scanning via Semgrep, secret detection, authentication analysis
**Architecture:** Dependency analysis, coupling detection, scalability assessment
**Code Quality:** Complexity metrics via Lizard, dead code detection

### Established Tools Integration

The analysis system leverages proven, established tools rather than bespoke implementations:

| Category | Tool | Languages Supported | Analysis Type |
|----------|------|-------------------|---------------|
| **Security** | Semgrep | 30+ languages | Semantic vulnerability detection |
| **Security** | detect-secrets | All text files | Hardcoded secrets detection |
| **Quality** | Lizard | 20+ languages | Complexity analysis |
| **Performance** | Language-specific profilers | Python, JS/TS, Java, Go, Rust | Performance profiling |
| **SQL** | SQLFluff | All SQL dialects | SQL quality and security |
| **Frontend** | ESLint ecosystem | JavaScript, TypeScript | Performance and quality |

### Language-Specific Analysis

**Supported Languages:** Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby, C/C++, Swift, Kotlin, SQL, and more

| Language | Test Coverage | Performance Baseline | Import Analysis | Bottleneck Detection |
|----------|--------------|---------------------|-----------------|---------------------|
| **Python** | ✅ pytest, coverage | ✅ cProfile, memory-profiler | ✅ import patterns | ✅ AST analysis |
| **JavaScript** | ✅ jest, nyc, c8 | ✅ npm scripts, profiling | ✅ import/require | ✅ performance patterns |
| **TypeScript** | ✅ jest, nyc, c8 | ✅ npm scripts, profiling | ✅ import patterns | ✅ performance patterns |
| **Java** | ✅ junit, jacoco | ✅ maven/gradle, JFR | ✅ import statements | ✅ performance patterns |
| **Go** | ✅ go test, coverage | ✅ go build, benchmarks | ✅ import patterns | ✅ performance patterns |
| **Rust** | ✅ cargo test, tarpaulin | ✅ cargo bench, flamegraph | ✅ use statements | ✅ performance patterns |
| **C#** | ✅ dotnet test, coverlet | ✅ dotnet build, profiling | ✅ using statements | ✅ performance patterns |
| **SQL** | ✅ SQLFluff integration | ✅ Query performance analysis | ✅ Schema dependencies | ✅ Query optimization |
| **Other Languages** | ✅ Framework detection | ✅ Language-specific patterns | ✅ Full import analysis | ✅ Performance patterns |
