---
argument-hint: [target-path]
---

# analyze-code-quality v0.2

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

**FIRST - Resolve SCRIPT_PATH:**

1. **Try project-level .claude folder**:

   ```bash
   Glob: ".claude/scripts/analyzers/quality/*.py"
   ```

2. **Try user-level .claude folder**:

   ```bash
   Bash: ls "$HOME/.claude/scripts/analyzers/quality/"
   ```

3. **Interactive fallback if not found**:
   - List searched locations: `.claude/scripts/analyzers/quality/` and `$HOME/.claude/scripts/analyzers/quality/`
   - Ask user: "Could not locate code_quality analysis scripts. Please provide full path to the scripts directory:"
   - Validate provided path contains expected scripts (complexity_lizard.py)
   - Set SCRIPT_PATH to user-provided location

**Pre-flight environment check (fail fast if imports not resolved):**

```bash
SCRIPTS_ROOT="$(cd "$(dirname \"$SCRIPT_PATH\")/../.." && pwd)"
PYTHONPATH="$SCRIPTS_ROOT" python -c "import core.base; print('env OK')"
```

**THEN - Execute via the registry-driven CLI (no per-module CLIs):**

```bash
PYTHONPATH="$SCRIPTS_ROOT" python -m core.cli.run_analyzer --analyzer quality:lizard --target . --output-format json
```

## Output Requirements

- Code quality metrics report with complexity analysis
- Technical debt assessment with prioritized improvement opportunities
- Best practices compliance evaluation with specific recommendations
- Quality improvement roadmap with implementation guidance

$ARGUMENTS
