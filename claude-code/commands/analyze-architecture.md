# analyze-architecture v0.2

**Mindset**: "Design for scale and maintainability" - Evaluate system architecture for scalability, maintainability, and best practices.

## Behavior

Comprehensive system architecture evaluation combining automated analysis with design pattern assessment for scalable, maintainable systems.

### Automated Architecture Analysis

Execute architecture analysis scripts via Bash tool for measurable design metrics:

**FIRST - Resolve SCRIPT_PATH:**

1. **Try project-level .claude folder**:

   ```bash
   Glob: ".claude/scripts/analyzers/architecture/*.py"
   ```

2. **Try user-level .claude folder**:

   ```bash
   Bash: ls "$HOME/.claude/scripts/analyzers/architecture/"
   ```

3. **Interactive fallback if not found**:
   - List searched locations: `.claude/scripts/analyzers/architecture/` and `$HOME/.claude/scripts/analyzers/architecture/`
   - Ask user: "Could not locate architecture analysis scripts. Please provide full path to the scripts directory:"
   - Validate provided path contains expected scripts (pattern_evaluation.py, scalability_check.py, coupling_analysis.py, dependency_analysis.py)
   - Set SCRIPT_PATH to user-provided location

**Pre-flight environment check (fail fast if imports not resolved):**

```bash
SCRIPTS_ROOT="$(cd "$(dirname \"$SCRIPT_PATH\")/.." && pwd)"
PYTHONPATH="$SCRIPTS_ROOT" python -c "import core.base; print('env OK')"
```

**THEN - Execute via the registry-driven CLI (no per-module CLIs):**

```bash
PYTHONPATH="$SCRIPTS_ROOT" python -m core.cli.run_analyzer --analyzer architecture:patterns --target . --output-format json
PYTHONPATH="$SCRIPTS_ROOT" python -m core.cli.run_analyzer --analyzer architecture:scalability --target . --output-format json
PYTHONPATH="$SCRIPTS_ROOT" python -m core.cli.run_analyzer --analyzer architecture:coupling --target . --output-format json
PYTHONPATH="$SCRIPTS_ROOT" python -m core.cli.run_analyzer --analyzer architecture:dependency --target . --output-format json
```

### Architecture Assessment Areas

- **Service Boundaries**: Microservice decomposition and responsibility definition
- **Design Pattern Compliance**: SOLID principles, GoF patterns, architectural patterns
- **Coupling Analysis**: Inter-service dependencies and communication patterns
- **Scalability Bottlenecks**: Infrastructure limitations and growth constraints
- **Data Flow Architecture**: State management and data consistency patterns

## Analysis Process

1. **Execute automated scripts** for quantitative architecture metrics
2. **Evaluate design patterns** against established best practices
3. **Assess scalability** through bottleneck identification
4. **Analyze coupling** between components and services
5. **Generate recommendations** for architectural improvements

## Assessment Areas

Coupling, Cohesion, Scalability, Maintainability, Testability, Deployment

## Output Requirements

- Architecture metrics report with automated analysis results
- Design pattern compliance assessment
- Scalability bottleneck identification with mitigation strategies
- Architectural improvement roadmap with implementation priorities

$ARGUMENTS
