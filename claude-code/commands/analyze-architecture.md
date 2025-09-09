# analyze-architecture v0.4

**Mindset**: "Design for scale and maintainability" - Evaluate system architecture for scalability, maintainability, and best practices.

## Behavior

Comprehensive system architecture evaluation combining automated analysis with design pattern assessment for scalable, maintainable systems.

### Automated Architecture Analysis

Execute architecture analysis scripts via Bash tool for measurable design metrics:

```bash
# Set paths and execute the analyzers
export PYTHONPATH="$(pwd)/.claude/scripts"
VENV_PYTHON="$(pwd)/.claude/venv/bin/python"

"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer architecture:patterns --target . --output-format json
"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer architecture:scalability --target . --output-format json
"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer architecture:coupling --target . --output-format json
"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer architecture:dependency --target . --output-format json
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
