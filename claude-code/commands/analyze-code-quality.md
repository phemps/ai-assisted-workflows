# analyze-code-quality v0.4

**Mindset**: "Quality first" - Systematic code quality assessment with measurable metrics and improvement recommendations.

## Behavior

Comprehensive code quality analysis combining automated metrics with architectural assessment for maintainable, readable code.

### Code Quality Assessment Areas

- **Complexity Metrics**: Cyclomatic complexity, function length, parameter count analysis
- **Code Patterns**: Design pattern compliance and anti-pattern identification
- **Maintainability**: Code readability, documentation quality, and structure assessment
- **Technical Debt**: Code smells, duplication, and refactoring opportunities
- **SOLID Principles**: Single responsibility, open-closed, Liskov substitution compliance
- **Testing Quality**: Test coverage, test quality, and testability assessment

## Script Integration

Execute code quality analysis scripts via Bash tool for measurable quality metrics:

```bash
# Set paths and execute the analyzer
export PYTHONPATH="$(pwd)/.claude/scripts"
VENV_PYTHON="$(pwd)/.claude/venv/bin/python"

"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer quality:lizard --target . --output-format json
```

## Output Requirements

- Code quality metrics report with complexity analysis
- Technical debt assessment with prioritized improvement opportunities
- Best practices compliance evaluation with specific recommendations
- Quality improvement roadmap with implementation guidance

$ARGUMENTS
