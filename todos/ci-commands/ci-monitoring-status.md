# CI Monitoring Status Check (`ci-monitoring-status`)

**Purpose**: Check the status and health of the continuous improvement system for the current project
**Usage**: `claude /ci-monitoring-status [--verbose] [--history-days=7]`

## Phase 1: System Status Verification

1. **Action**: Check if CI registry is initialized
2. **Tool**: Read - `.ci-registry/config.json` to verify configuration exists
3. **Expected**: CI configuration file found with project settings
4. **On missing**: Display setup instructions with `/setup-ci-monitoring`

5. **Action**: Verify CI registry database
6. **Tool**: LS - `.ci-registry/` to confirm directory structure
7. **Expected**: Registry directories: cache/, reports/, backups/
8. **On missing**: CI registry not initialized

9. **Action**: Verify Python dependencies for duplicate detection
10. **Command**: `python -c "import faiss, transformers, torch; print('✅ ML dependencies available')"`
11. **Expected**: Import succeeds without errors
12. **On failure**: Display dependency installation instructions

13. **Action**: Check Serena MCP integration status
14. **Command**: `uvx --from git+https://github.com/oraios/serena serena --version`
15. **Expected**: Serena version displayed successfully
16. **On missing**: MCP integration unavailable - fail-fast system requires this

## Phase 2: Core Components Health Check

1. **Action**: Test duplicate detection system
2. **Command**: `python shared/lib/scripts/continuous-improvement/core/duplicate_finder.py --test --threshold 0.85`
3. **Expected**: DuplicateFinder initializes with all 4 core components
4. **On failure**: Components missing (MCP, CodeBERT, Faiss, SQLite)

5. **Action**: Check registry manager status
6. **Command**: `python shared/lib/scripts/continuous-improvement/core/registry_manager.py --status --project $(pwd)`
7. **Expected**: Registry database accessible with symbol count
8. **On failure**: Registry initialization required

9. **Action**: Verify orchestration bridge connectivity
10. **Command**: `python shared/lib/scripts/continuous-improvement/integration/orchestration_bridge.py --dry-run --project-root $(pwd)`
11. **Expected**: Orchestration bridge runs without errors
12. **On failure**: Integration components not configured

## Phase 3: GitHub Actions Integration Status

1. **Action**: Check for GitHub Actions workflow
2. **Tool**: Read - `.github/workflows/continuous-improvement.yml`
3. **Expected**: CI workflow configured for duplicate detection
4. **On missing**: GitHub Actions integration not set up

5. **Action**: Verify MCP setup instructions
6. **Tool**: Read - `.ci-registry/mcp-setup.md`
7. **Expected**: Instructions for manual Serena MCP integration
8. **On missing**: MCP integration guidance not available

## Phase 4: Metrics and Activity Overview

1. **Action**: Check recent CI metrics collection
2. **Command**: `python shared/lib/scripts/continuous-improvement/metrics/ci_metrics_collector.py report --days $HISTORY_DAYS`
3. **Expected**: Metrics report with duplication analysis activity
4. **On failure**: No recent CI activity recorded

5. **Action**: Get baseline duplicate analysis status
6. **Tool**: Read - `.ci-registry/baseline-duplicates.json` if exists
7. **Expected**: Baseline duplicates from initial setup
8. **On missing**: Initial baseline analysis not completed

## Phase 5: Status Summary Report

**Console Output Format**:

```
🔍 CI Monitoring Status Report

📊 System Health:
  CI Registry: [✅ Initialized / ❌ Not Found]
  Configuration: [✅ Active / ❌ Missing] (.ci-registry/config.json)
  ML Dependencies: [✅ Available / ❌ Missing] (faiss, transformers, torch)
  Serena MCP: [✅ Connected / ❌ Required - Fail-fast] (uvx serena)

🧠 Core Components:
  DuplicateFinder: [✅ Ready / ❌ Dependencies Missing]
  Registry Manager: [✅ Active / ❌ Not Initialized] ($SYMBOL_COUNT symbols)
  Orchestration Bridge: [✅ Connected / ❌ Configuration Error]
  Quality Gates: [✅ Detected / ⚠️  Manual Setup] ($GATE_COUNT gates)

📈 Recent Activity (Last $HISTORY_DAYS days):
  Duplicate Detection Runs: $DETECTION_COUNT
  Symbols Analyzed: $ANALYZED_COUNT
  Duplicates Found: $DUPLICATE_COUNT
  Auto-fixes Applied: $AUTOFIX_COUNT
  Manual Reviews Created: $REVIEW_COUNT

🔧 GitHub Integration:
  Workflow: [✅ Configured / ❌ Missing] (.github/workflows/continuous-improvement.yml)
  MCP Setup: [✅ Instructions Ready / ❌ Missing] (.ci-registry/mcp-setup.md)

⚙️ Configuration:
  Project: $PROJECT_NAME
  Similarity Threshold: $THRESHOLD
  Auto-refactor: [✅ Enabled / ❌ Disabled]
  Languages Monitored: [$LANGUAGES]

🚀 Next Steps:
  - Run manual analysis: python shared/lib/scripts/continuous-improvement/integration/orchestration_bridge.py
  - View detailed metrics: /ci-monitoring-status --verbose
  - Generate full report: python shared/lib/scripts/continuous-improvement/metrics/ci_metrics_collector.py report
  - Setup missing components: /setup-ci-monitoring
  - Complete MCP integration: cat .ci-registry/mcp-setup.md
```

**JSON Output** (when --verbose flag used):

```json
{
  "status": "active|partial|not_initialized",
  "system_health": {
    "ci_registry": {
      "status": "initialized",
      "config_path": ".ci-registry/config.json",
      "directories": ["cache", "reports", "backups"]
    },
    "ml_dependencies": {
      "status": "available",
      "packages": [
        "faiss-cpu",
        "transformers",
        "torch",
        "sentence-transformers"
      ],
      "missing": []
    },
    "serena_mcp": {
      "status": "connected",
      "version": "1.2.3",
      "fail_fast_required": true
    }
  },
  "core_components": {
    "duplicate_finder": {
      "status": "ready",
      "components_required": ["MCP", "CodeBERT", "Faiss", "SQLite"],
      "fail_fast": true
    },
    "registry_manager": {
      "status": "active",
      "symbol_count": 1247,
      "database_path": ".ci-registry/registry.db"
    },
    "orchestration_bridge": {
      "status": "connected",
      "github_integration": true
    }
  },
  "recent_activity": {
    "period_days": 7,
    "detection_runs": 12,
    "symbols_analyzed": 3421,
    "duplicates_found": 8,
    "auto_fixes_applied": 3,
    "manual_reviews_created": 2
  },
  "github_integration": {
    "workflow_configured": true,
    "workflow_path": ".github/workflows/continuous-improvement.yml",
    "mcp_setup_available": true
  },
  "configuration": {
    "project_name": "example-project",
    "similarity_threshold": 0.85,
    "auto_refactor_enabled": false,
    "languages": ["python", "typescript", "javascript"],
    "analysis_mode": "incremental"
  },
  "installation_path": ".ci-registry/",
  "last_updated": "2025-08-11T23:45:00Z"
}
```

## Error Handling

**CI System Not Initialized**:

```
❌ Continuous Improvement system not found

The CI monitoring system has not been set up for this project.

Missing: .ci-registry/config.json

To initialize:
  claude /setup-ci-monitoring

This will:
  - Install ML dependencies (faiss, transformers, torch)
  - Initialize CI registry database
  - Configure duplicate detection system
  - Set up GitHub Actions workflow
  - Create Serena MCP integration instructions
```

**Missing Dependencies** (Fail-Fast):

```
❌ CI System Dependencies Missing

The system requires exact ML stack with no fallbacks:
  Missing: faiss-cpu, transformers, torch

To fix:
  python shared/lib/scripts/setup/continuous-improvement/install_ci_dependencies.py

Or run full setup:
  claude /setup-ci-monitoring

Note: System follows fail-fast behavior - no graceful degradation
```

**Serena MCP Not Available** (Fail-Fast):

```
❌ Serena MCP Integration Required

CI monitoring system requires Serena MCP with no fallbacks.

Test MCP availability:
  uvx --from git+https://github.com/oraios/serena serena --version

Setup instructions:
  cat .ci-registry/mcp-setup.md

Complete setup:
  claude /setup-ci-monitoring
```

**Components Available But No Activity**:

```
📊 CI Monitoring Status: Ready but Inactive

System is initialized but no duplicate detection activity detected.

To start monitoring:
  - Manual analysis: python shared/lib/scripts/continuous-improvement/integration/orchestration_bridge.py
  - Check GitHub Actions: git commit and push to trigger workflow
  - Verify configuration: cat .ci-registry/config.json
  - Full system test: claude /setup-ci-monitoring --verify
```

**Partial Configuration**:

```
⚠️  CI Monitoring Partially Configured

System components:
  ✅ Dependencies installed
  ✅ Registry initialized
  ❌ GitHub Actions workflow missing
  ❌ MCP integration incomplete

To complete setup:
  claude /setup-ci-monitoring

Or manual fixes:
  - GitHub workflow: check .github/workflows/continuous-improvement.yml
  - MCP integration: follow .ci-registry/mcp-setup.md
```

$ARGUMENTS
