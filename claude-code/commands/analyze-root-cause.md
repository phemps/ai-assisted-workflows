---
argument-hint: [issue-description]
---

# analyze-root-cause v0.4

**Mindset**: "Find the real problem" - Systematic root cause analysis using evidence-based investigation methodology.

## Behavior

Comprehensive root cause analysis combining automated investigation tools with systematic reasoning for accurate problem identification.

### Root Cause Investigation Areas

- **Change Correlation**: Recent code changes and their impact analysis
- **Error Pattern Analysis**: Error log analysis and pattern identification
- **Execution Tracing**: Code execution flow and failure point identification
- **Five Whys Analysis**: Iterative questioning to reach fundamental causes
- **Timeline Analysis**: Sequence of events leading to the issue
- **Environmental Factors**: System configuration and dependency analysis

### Enhanced Debugging (--verbose flag)

- **Comprehensive Logging**: Structured logging with contextual information and trace correlation
- **Distributed Tracing**: Cross-service request tracing and performance analysis
- **Diagnostic Instrumentation**: Metrics collection, profiling, and observability enhancement
- **Error Context**: Detailed error information with stack traces and state capture
- **Performance Monitoring**: Resource usage tracking and bottleneck identification
- **Event Correlation**: Event timeline and causal relationship analysis

## Script Integration

Execute root cause analysis scripts via Bash tool for systematic investigation:

```bash
# Set paths and execute the analyzers
export PYTHONPATH="$(pwd)/.claude/scripts"
VENV_PYTHON="$(pwd)/.claude/venv/bin/python"

"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer root_cause:trace_execution --target . --output-format json
"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer root_cause:recent_changes --target . --output-format json
"$VENV_PYTHON" -m core.cli.run_analyzer --analyzer root_cause:error_patterns --target . --output-format json
```

## Optional Flags

--verbose: Use when you need detailed diagnostic output including comprehensive logging setup, distributed tracing configuration, and detailed error context capture for complex debugging scenarios

## Output Requirements

- Root cause analysis report with evidence-based findings
- Change correlation analysis with impact assessment
- Error pattern identification with frequency analysis
- Investigation timeline with causal relationships

$ARGUMENTS
