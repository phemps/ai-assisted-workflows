# Continuous Improvement Status Check (`continuous-improvement-status`)

**Purpose**: Check the status and health of the continuous improvement system for the current project
**Usage**: `claude /continuous-improvement-status [--verbose] [--history-days=7]`

## Phase 1: System Status Verification

1. **Action**: Check if CI framework is initialized
2. **Tool**: Read - `.claude/ci_metrics.db` to verify database exists
3. **Expected**: CI database file found and accessible
4. **On missing**: Display setup instructions with `/setup-continuous-improvement`

5. **Action**: Verify Python dependencies for CI framework
6. **Command**: `python3 -c "from continuous_improvement import CIFramework; print('✅ CI Framework available')"`
7. **Expected**: Import succeeds without errors
8. **On failure**: Display dependency installation instructions

9. **Action**: Check Serena MCP integration status
10. **Command**: `claude mcp list | grep serena`
11. **Expected**: Serena MCP server listed as connected
12. **On missing**: Optional - display MCP setup recommendations

## Phase 2: CI Metrics Overview

1. **Action**: Initialize CI framework and collect basic status
2. **Tool**: Execute Python script to get CI framework status
3. **Script**: `python3 shared/lib/scripts/continuous-improvement/framework/ci_framework.py report --project-root . --output-format console`
4. **Expected**: CI report with recent metrics summary

5. **Action**: Check recent CI activity (last 7 days by default)
6. **Script**: `python3 shared/lib/scripts/continuous-improvement/framework/ci_framework.py metrics --days $HISTORY_DAYS`
7. **Expected**: JSON output with recent metrics data

8. **Action**: Get pending CI recommendations
9. **Script**: `python3 shared/lib/scripts/continuous-improvement/framework/ci_framework.py recommendations`
10. **Expected**: List of pending improvement recommendations

## Phase 3: Project Quality Gates Status

1. **Action**: Check quality gate detection capabilities
2. **Script**: `python3 shared/lib/scripts/continuous-improvement/detection/quality_gate_detector.py detect --project-root .`
3. **Expected**: Available build/test/lint commands detected

4. **Action**: Verify quality gate execution (dry run)
5. **Script**: `python3 shared/lib/scripts/continuous-improvement/detection/quality_gate_detector.py execute --mode production --dry-run --correlation-id status-check`
6. **Expected**: Quality gates would execute successfully

## Phase 4: Status Summary Report

**Console Output Format**:

```
🔍 Continuous Improvement Status Report

📊 System Health:
  CI Framework: [✅ Active / ❌ Not Initialized]
  Database: [✅ Connected / ❌ Missing]
  Python Dependencies: [✅ Available / ❌ Missing]
  Serena MCP: [✅ Connected / ⚠️  Optional / ❌ Missing]

📈 Recent Activity (Last $HISTORY_DAYS days):
  Metrics Recorded: $METRICS_COUNT
  Build Metrics: $BUILD_COUNT (avg: ${BUILD_TIME}s)
  Test Metrics: $TEST_COUNT (avg: ${TEST_TIME}s)
  Quality Metrics: $QUALITY_COUNT
  Performance Metrics: $PERF_COUNT

🎯 Quality Gates:
  Build Command: [$BUILD_CMD or "Not detected"]
  Test Command: [$TEST_CMD or "Not detected"]
  Lint Command: [$LINT_CMD or "Not detected"]
  Type Check: [$TYPE_CMD or "Not detected"]

⚡ Pending Recommendations: $PENDING_COUNT
  High Priority: $HIGH_PRIORITY_COUNT
  Medium Priority: $MEDIUM_PRIORITY_COUNT
  Low Priority: $LOW_PRIORITY_COUNT

🚀 Next Steps:
  - View detailed metrics: /continuous-improvement-status --verbose
  - Review recommendations: python3 shared/lib/scripts/continuous-improvement/framework/ci_framework.py recommendations
  - Generate full report: python3 shared/lib/scripts/continuous-improvement/metrics/ci_metrics_collector.py report
  - Setup missing components: /setup-continuous-improvement
```

**JSON Output** (when --verbose flag used):

```json
{
  "status": "active|partial|not_initialized",
  "system_health": {
    "ci_framework": {
      "status": "active",
      "database_path": ".claude/ci_metrics.db"
    },
    "dependencies": { "status": "available", "missing": [] },
    "serena_mcp": { "status": "connected", "optional": true }
  },
  "recent_activity": {
    "period_days": 7,
    "metrics_summary": {
      "total_metrics": 45,
      "build_metrics": { "count": 12, "avg_time": 23.4 },
      "test_metrics": { "count": 15, "avg_time": 8.2, "avg_coverage": 78.5 },
      "quality_metrics": { "count": 10, "avg_errors": 2.3 },
      "performance_metrics": { "count": 8, "avg_cpu": 45.2 }
    }
  },
  "quality_gates": {
    "build_command": "npm run build",
    "test_command": "npm test",
    "lint_command": "npm run lint",
    "typecheck_command": "npx tsc --noEmit"
  },
  "recommendations": {
    "total_pending": 6,
    "by_priority": { "high": 1, "medium": 3, "low": 2 },
    "categories": { "performance": 2, "quality": 3, "architecture": 1 }
  },
  "installation_path": ".claude/",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## Configuration Options

**History Period**:

- `--history-days=7`: Check last 7 days of activity (default)
- `--history-days=30`: Extended history for trend analysis
- `--history-days=1`: Recent activity only

**Output Modes**:

- Default: Concise console summary
- `--verbose`: Detailed JSON output with full metrics
- `--json`: Always output JSON format

## Error Handling

**CI Framework Not Initialized**:

```
❌ Continuous Improvement system not found

The CI framework has not been set up for this project.

To initialize:
  claude /setup-continuous-improvement

This will:
  - Install Python dependencies
  - Initialize CI metrics database
  - Configure quality gate detection
  - Set up agent orchestration integration
```

**Missing Dependencies**:

```
⚠️  CI Framework partially available

Missing Python dependencies. To fix:
  pip install -r shared/lib/scripts/setup/requirements.txt

Or run full setup:
  claude /setup-continuous-improvement
```

**No Recent Activity**:

```
📊 Continuous Improvement Status: Active but Quiet

System is initialized but no recent CI activity detected.

To start collecting metrics:
  - Make commits to trigger automatic analysis
  - Run manual analysis: python3 shared/lib/scripts/continuous-improvement/metrics/ci_metrics_collector.py report
  - Check setup: claude /setup-continuous-improvement
```

## Quality Gates

**Quick Health Check**:

- **CI Database**: File exists and is readable
- **Python Imports**: CI framework modules load successfully
- **Quality Detection**: Build/test/lint commands can be detected
- **Recent Activity**: At least one metric recorded in last 7 days

**Comprehensive Check** (with --verbose):

- **Database Schema**: All required tables present
- **Metrics Trends**: Analysis of build/test/quality trends
- **Agent Integration**: Orchestration bridge connectivity
- **Performance History**: System resource usage during CI

## Troubleshooting

**Database Locked Error**:

- **Solution**: Check for running CI processes, restart if needed

**Import Errors**:

- **Solution**: Run `pip install -r shared/lib/scripts/setup/requirements.txt`

**No Quality Gates Detected**:

- **Solution**: Ensure project has package.json, Cargo.toml, or Python files with standard tooling

**Serena MCP Not Found** (non-critical):

- **Solution**: Run `claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server`

$ARGUMENTS
