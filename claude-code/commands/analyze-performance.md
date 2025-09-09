# analyze-performance v0.4

**Mindset**: "Where are the bottlenecks?" - Combine static analysis with live performance monitoring.

## Behavior

Comprehensive performance analysis combining automated script analysis with live testing capabilities for complete performance optimization.

### Automated Performance Analysis

Execute performance analysis scripts via Bash tool for measurable bottleneck detection:

```bash
# Set paths and execute the analyzers
export PYTHONPATH="$(pwd)/.claude/scripts"
VENV_PYTHON="$(pwd)/.claude/venv/bin/python"

"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer performance:flake8-perf --target . --output-format json
"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer performance:frontend --target . --output-format json
"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer performance:sqlfluff --target . --output-format json
```

### Performance Assessment Areas

- **Database Optimization**: Query analysis, N+1 detection, index optimization, execution plans
- **Frontend Performance**: Bundle analysis, render optimization, memory leak detection
- **Algorithm Complexity**: CPU/memory profiling and optimization recommendations
- **Network Optimization**: Request optimization, caching strategy evaluation
- **Scalability Analysis**: Bottleneck identification for high-load scenarios

## Analysis Process

1. **Execute automated scripts** for measurable performance data
2. **Analyze performance metrics** in context of user experience
3. **Identify bottlenecks** through systematic profiling
4. **Prioritize optimizations** by impact and implementation effort
5. **Generate recommendations** with before/after validation

## Performance Areas

Database, Frontend, Algorithms, Memory, Network, Caching, Scalability

## Output Requirements

- Performance metrics report with script analysis results
- Bottleneck identification with impact assessment
- Optimization recommendations prioritized by ROI
- Implementation guidance with code examples

$ARGUMENTS
