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
# API keys for CLI tools (never committed to git)
CLAUDE_API_KEY=your-claude-api-key
QWEN_API_KEY=sk-your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
```

**Authentication Methods**:

1. **API Key mode** (automated): `--auth apikey --api-key "your-key"`
2. **OAuth mode** (interactive): `--auth oauth` (triggers browser authentication)

**API Key Precedence** (highest to lowest):

1. Command line `--api-key` argument
2. `.env` file variables
3. Environment variables

### 3. Run Your First Test

```bash
# API Key mode with keys loaded from .env file
python run_eval.py scenarios/baseline_task.yaml --cli-tool claude --auth apikey
python run_eval.py scenarios/baseline_task.yaml --cli-tool qwen --auth apikey
python run_eval.py scenarios/baseline_task.yaml --cli-tool gemini --auth apikey

# OAuth mode (interactive browser authentication)
python run_eval.py scenarios/baseline_task.yaml --cli-tool claude --auth oauth
python run_eval.py scenarios/baseline_task.yaml --cli-tool qwen --auth oauth
python run_eval.py scenarios/baseline_task.yaml --cli-tool gemini --auth oauth

# Override with command line API key
python run_eval.py scenarios/baseline_task.yaml \
  --cli-tool claude \
  --auth apikey \
  --api-key "different-api-key"

# Verbose mode (real-time output)
python run_eval.py scenarios/baseline_task.yaml \
  --cli-tool qwen \
  --auth apikey \
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

| KPI     | Description          | Lower is Better | Category       |
| ------- | -------------------- | --------------- | -------------- |
| **K1**  | Failed Tool Calls    | ✅              | Infrastructure |
| **K2**  | Quality Gate Reruns  | ✅              | Quality        |
| **K3**  | Agent Invocations    | ➖              | Orchestration  |
| **K4**  | State Transitions    | ➖              | Orchestration  |
| **K9**  | Token Spend          | ✅              | Cost           |
| **K11** | Runtime (seconds)    | ✅              | Performance    |
| **K12** | API Retry Attempts   | ✅              | Infrastructure |
| **K13** | Rate Limit Events    | ✅              | Infrastructure |
| **K14** | API Failure Rate (%) | ✅              | Infrastructure |

## Test Scenario

The baseline scenario (`baseline_task.yaml`) uses a controlled implementation plan:

- **Task**: Build a REST API service with TypeScript
- **Complexity**: Medium (5 tasks, database integration, testing)
- **Duration**: ~15-30 minutes
- **Expected Issues**: Dependency conflicts, linting failures, test setup

This scenario is designed to trigger common failure points that the evaluation system can measure.

## Example Output

```
🐳 CLI Evaluation System - CLAUDE
📄 Scenario: baseline_task_v1
--------------------------------------------------
🔐 Using OAuth authentication for claude
📱 Please complete the browser-based authentication flow...
Running: claude -p /login
✅ OAuth authentication successful for claude
⚡ Starting timed execution...
⚡ Executing: claude -p "/todo-orchestrate test_plan.md" --permission-mode bypassPermissions

==================================================
📊 TEST RESULTS SUMMARY
==================================================
Scenario: baseline_task_v1
CLI Tool: claude
Exit Code: 0
Total Time: 185.42s
Report: reports/run_20250825_210330.json

📈 Key Performance Indicators:
   K1_failed_tools: 0
   K2_quality_reruns: 1
   K3_agent_invocations: 3
   K4_state_transitions: 8
   K9_token_spend: 12450
   K11_runtime_seconds: 185.4
   K12_api_retry_attempts: 2
   K13_rate_limit_events: 0
   K14_api_failure_rate: 0%

✅ Test completed successfully!
```

## Architecture

```
evaluation/
├── run_eval.py                    # Main test harness with OAuth support
├── lib/
│   ├── evaluator.py              # Core evaluation engine with Docker isolation
│   └── secure_token_manager.py   # Secure token handling
├── cli_installers/
│   ├── install_claude.py         # Claude CLI installer with OAuth/API key support
│   ├── install_qwen.py           # Qwen CLI installer
│   └── install_gemini.py         # Gemini CLI installer
├── docker/
│   ├── Dockerfile.base           # Base Alpine image
│   ├── Dockerfile.node           # Node.js image for npm-based CLIs
│   └── Dockerfile.python         # Python image
├── scenarios/
│   ├── baseline_task.yaml        # Standard test configuration
│   └── test_plan.md              # Implementation plan for testing
└── reports/
    ├── baseline.json             # Baseline metrics
    ├── run_*.json               # Individual test runs
    └── comparison_*.json        # Before/after analysis
```

## How It Works

1. **Docker Isolation**: Each CLI tool runs in a secure, isolated container
2. **Dual Authentication**: Supports both API key (automated) and OAuth (interactive) authentication
3. **Container Persistence**: Containers are reused across runs for efficiency, OAuth credentials persist
4. **Secure Token Handling**: API keys never stored in files, containers, or logs
5. **Comprehensive Metrics**: Tracks 9 KPIs including API reliability, orchestration, and workflow metrics
6. **Log Parsing**: Extracts metrics from CLI output using 40+ regex patterns
7. **Comparison Engine**: Tracks improvements/regressions against baseline measurements

## Adding New Test Scenarios

Create new YAML files in `scenarios/` directory:

```yaml
id: my_custom_test
description: Custom test scenario
plan_file: my_test_plan.md
max_duration_minutes: 45
track_kpis: [K1, K2, K9, K11, K12, K13, K14]
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

- `python-dotenv` - .env file support for API keys and OAuth tokens
- `PyYAML` - YAML parsing for scenario files

## OAuth Authentication Details

The evaluation framework supports OAuth authentication for all CLI tools:

### OAuth Commands by CLI Tool:

- **Claude**: `claude -p "/login"` - Opens browser for Anthropic account login
- **Qwen**: `qwen /auth` - OAuth authentication flow
- **Gemini**: `gemini /auth` - Google account authentication

### OAuth State Detection:

The system automatically detects existing OAuth credentials:

- **Qwen**: Checks for `~/.qwen/oauth_creds.json`
- **Gemini**: Checks for `~/.gemini/google_accounts.json`
- **Claude**: Checks for `~/.claude/.credentials.json` (Linux) or macOS Keychain
- **Universal**: Creates `~/.oauth_complete` flag after successful authentication

### OAuth vs API Key Comparison:

| Aspect          | OAuth Mode            | API Key Mode          |
| --------------- | --------------------- | --------------------- |
| **Setup**       | Interactive browser   | Automated             |
| **Persistence** | Container volumes     | Environment variables |
| **Security**    | Browser-based flow    | Secure file contexts  |
| **CI/CD**       | Manual setup required | Fully automated       |
| **Reuse**       | Persists across runs  | Passed each time      |

## Future Enhancements

- **Additional KPIs**: K3 (placeholder code detection), K15+ (custom metrics)
- **Multi-scenario Testing**: Parallel execution of different test scenarios
- **Trend Analysis**: Historical performance tracking and regression detection
- **Advanced Comparisons**: Side-by-side CLI tool performance analysis
- **Automated Alerting**: Slack/email notifications for significant regressions
