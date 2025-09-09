---
argument-hint: <bug-description-or-location>
---

# fix-bug v0.4

**Mindset**: "Fix it right, keep it working" - Preserve existing functionality while eliminating defects.

## Behavior

Systematic bug diagnosis and resolution using structured debugging methodology with comprehensive validation.

## Systematic Bug Resolution Framework

### Comprehensive Diagnosis (35%)

- **Bug Reproduction**: Controlled environment with minimal reproduction case
- **Error Investigation**: Stack trace analysis, log analysis, state inspection
- **Root Cause Analysis**: Five Whys technique, timeline analysis, change correlation
- **Impact Assessment**: Severity classification and business impact evaluation

### Planning Phase (25%)

- **Fix Strategy Selection**: Minimal fix vs systematic fix approach
- **Risk Assessment**: Regression risk, performance risk, security implications
- **Testing Strategy**: Reproduction test, regression suite, edge case coverage
- **Rollback Planning**: Rollback triggers, procedures, monitoring strategy

### Implementation Phase (30%)

- **Test-Driven Fixing**: Write failing test, implement fix, expand test coverage
- **Root Cause Focus**: Address fundamental cause, not just symptoms
- **Defensive Programming**: Add validation, error handling, logging
- **Code Quality**: Maintain readability and maintainability

### Validation Phase (10%)

- **Before/After Comparison**: Document exact behavior change
- **Regression Testing**: Run full test suite to ensure no side effects
- **Integration Verification**: Cross-component interactions work correctly
- **Manual Testing**: Human verification of fix in realistic scenarios

## Script Integration

Execute debugging analysis scripts via Bash tool for systematic issue analysis:

```bash
# Set paths and execute the analyzers
export PYTHONPATH="$(pwd)/.claude/scripts"
VENV_PYTHON="$(pwd)/.claude/venv/bin/python"

"$VENV_PYTHON" -m analyzers.root_cause.trace_execution . --output-format json
"$VENV_PYTHON" -m analyzers.root_cause.recent_changes . --output-format json
"$VENV_PYTHON" -m analyzers.root_cause.error_patterns . --output-format json
```

## Quality Gates

- **Diagnosis Gate**: Reproducible bug with identified root cause
- **Planning Gate**: Comprehensive fix strategy with risk mitigation
- **Implementation Gate**: Working fix with comprehensive test coverage
- **Validation Gate**: No regressions with enhanced monitoring

## Output Requirements

- Detailed bug reproduction steps and root cause analysis
- Minimal, targeted fix addressing fundamental cause
- Comprehensive test suite including reproduction test
- Bug analysis documentation with lessons learned

$ARGUMENTS
