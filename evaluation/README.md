# CLI Tool Evaluation System

A secure, cross-platform CLI tool evaluation harness with Docker isolation, supporting Claude, Qwen, and Gemini CLI tools with comprehensive security hardening and container persistence.

## 🔐 Security Features

### Zero Token Persistence

- **Never stored**: Tokens are never written to files, logs, images, or containers
- **Secure contexts**: Uses Python context managers for temporary token handling
- **Automatic cleanup**: File content overwritten with random data before deletion
- **Memory safety**: Environment variables cleared after use
- **.env protection**: `.env` file automatically ignored by git to prevent token leakage

### Container Hardening

- **Read-only filesystem**: Containers run with read-only root filesystem
- **Dropped capabilities**: All Linux capabilities dropped by default
- **No privilege escalation**: `no-new-privileges` security option enabled
- **Resource limits**: Memory and CPU constraints prevent runaway processes
- **User isolation**: Containers run as non-root user (UID/GID 1001)

### Volume Security

- **Read-only scenarios**: Plan files mounted read-only
- **Isolated workspaces**: Each CLI tool gets dedicated volume
- **SELinux labeling**: Volumes use `:ro` and `:rw` with labeling where available
- **Temporary filesystems**: `/tmp` and cache directories use `tmpfs` with `noexec,nosuid`

## 🚀 Quick Start

### 1. Build Docker Images (One-time Setup)

```bash
# Cross-platform Docker image builder
python docker_build.py

# With verbose output
python docker_build.py --verbose

# Force rebuild existing images
python docker_build.py --force-rebuild
```

### 2. Configure Authentication

Create a `.env` file in the evaluation directory:

```bash
# OAuth tokens for CLI tools (never committed to git)
CLAUDE_OAUTH_TOKEN=your-claude-token
QWEN_OAUTH_TOKEN=sk-your-openai-api-key
GEMINI_OAUTH_TOKEN=your-gemini-api-key
```

**Token Precedence** (highest to lowest):

1. Command line `--auth-token` argument
2. `.env` file variables
3. Environment variables

### 3. Run Your First Test

```bash
# Test with tokens loaded from .env file
python run_eval.py scenarios/baseline_task.yaml --cli-tool claude
python run_eval.py scenarios/baseline_task.yaml --cli-tool qwen
python run_eval.py scenarios/baseline_task.yaml --cli-tool gemini

# Override with command line token
python run_eval.py scenarios/baseline_task.yaml \
  --cli-tool claude \
  --auth-token "different-token"

# Verbose mode (real-time output)
python run_eval.py scenarios/baseline_task.yaml \
  --cli-tool qwen \
  --verbose

# Check environment before running
python run_eval.py --check-env
```

### 4. View Results

Reports are saved in `reports/` directory:

- `baseline.json` - Baseline metrics
- `run_TIMESTAMP.json` - Individual test runs
- `comparison_TIMESTAMP.json` - Comparison analysis

## Metrics Tracked

| KPI     | Description         | Lower is Better |
| ------- | ------------------- | --------------- |
| **K1**  | Failed Tool Calls   | ✅              |
| **K2**  | Quality Gate Reruns | ✅              |
| **K9**  | Token Spend         | ✅              |
| **K11** | Runtime (seconds)   | ✅              |

## Test Scenario

The baseline scenario (`baseline_task.yaml`) uses a controlled implementation plan:

- **Task**: Build a REST API service with TypeScript
- **Complexity**: Medium (5 tasks, database integration, testing)
- **Duration**: ~15-30 minutes
- **Expected Issues**: Dependency conflicts, linting failures, test setup

This scenario is designed to trigger common failure points that the evaluation system can measure.

## Example Output

```
🧪 Running evaluation: baseline_task_v1
📄 Plan file: test_plan.md
⚡ Executing: claude /todo-orchestrate evaluation/scenarios/test_plan.md

# Custom CLI Tool Examples:
python run_eval.py scenarios/baseline_task.yaml --cli-tool gpt --prompt "orchestrate" --compare
python run_eval.py scenarios/baseline_task.yaml --cli-tool ./my-wrapper.sh --prompt "/plan-solution" --save-baseline

==================================================
📊 EVALUATION RESULTS
==================================================
K1_failed_tools: 3 → 1 (↓66.7%) ✅
K2_quality_reruns: 2 → 1 (↓50.0%) ✅
K9_token_spend: 45230 → 38450 (↓15.0%) ✅
K11_runtime_seconds: 272 → 225 (↓17.3%) ✅

Overall: 4 improvements, 0 regressions
📄 Detailed comparison saved to: reports/comparison_20250115_143000.json
```

## Architecture

```
evaluation/
├── run_eval.py              # Main test harness
├── parse_metrics.py         # Metrics extraction utilities
├── scenarios/
│   ├── baseline_task.yaml   # Standard test configuration
│   └── test_plan.md         # Implementation plan for testing
└── reports/
    ├── baseline.json        # Baseline metrics
    ├── run_*.json          # Individual test runs
    └── comparison_*.json   # Before/after analysis
```

## How It Works

1. **External Wrapper**: Executes specified CLI tool via subprocess
2. **Log Parsing**: Extracts metrics from stdout/stderr using regex patterns
3. **No Modifications**: Zero changes to existing orchestration code
4. **Comparison Engine**: Tracks improvements/regressions against baseline

## Adding New Test Scenarios

Create new YAML files in `scenarios/` directory:

```yaml
id: my_custom_test
description: Custom test scenario
plan_file: my_test_plan.md
max_duration_minutes: 45
track_kpis: [K1, K2, K9, K11]
```

## Extending Metrics

To add new KPIs:

1. Add regex patterns to `parse_metrics.py`
2. Update parsing logic in `run_eval.py`
3. Add thresholds to scenario YAML

## Use Cases

- **Prompt Engineering**: Test prompt changes against baseline
- **Agent Improvements**: Measure impact of agent modifications
- **Regression Testing**: Ensure changes don't break workflows
- **Performance Tuning**: Optimize token usage and runtime
- **Quality Gate Tuning**: Reduce unnecessary reruns

## Dependencies

- Python 3.7+
- Docker Desktop
- Target CLI tools (Claude, Qwen, Gemini)

Install dependencies:

```bash
pip install -r requirements.txt
```

Core dependencies:

- `python-dotenv` - .env file support for OAuth tokens
- `PyYAML` - YAML parsing for scenario files

## Future Enhancements

If this minimal system proves valuable:

- Add K3 (placeholder code detection)
- Add K13 (prompt execution accuracy)
- Multiple test scenarios
- Trend tracking over time
- Automated regression alerts
