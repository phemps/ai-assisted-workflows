# CI Monitoring Status Check (`ci-monitoring-status`)

**Purpose**: Check the status and health of the continuous improvement system for the current project
**Usage**: `claude /ci-monitoring-status [--verbose] [--history-days=7]`

## Phase 1: System Status Verification

1. **Action**: Check if CI registry is initialized
2. **Tool**: Read - `.ci-registry/ci_config.json` to verify project configuration exists
3. **Expected**: Project configuration file found with project settings
4. **On missing**: Display setup instructions with `/setup-ci-monitoring`

5. **Action**: Verify CI registry database
6. **Tool**: LS - `.ci-registry/` to confirm directory structure
7. **Expected**: Registry directories: cache/, reports/, backups/
8. **On missing**: CI registry not initialized

9. **Action**: Verify Python dependencies for duplicate detection
10. **Command**: `python -c "import faiss, transformers, torch; print('✅ ML dependencies available')"`
11. **Expected**: Import succeeds without errors
12. **On failure**: Display dependency installation instructions

## Phase 2: Core Components Health Check

1. **Action**: Test duplicate detection system
2. **Command**: `PYTHONPATH=shared python -c "from shared.ci.core.semantic_duplicate_detector import DuplicateFinder; print('✅ Duplicate finder ready')"`
3. **Expected**: DuplicateFinder imports successfully
4. **On failure**: Components missing or import errors

5. **Action**: Check registry manager status
6. **Command**: `PYTHONPATH=shared python -c "from shared.ci.core.registry_manager import RegistryManager; print('✅ Registry manager ready')"`
7. **Expected**: RegistryManager imports successfully
8. **On failure**: Registry components not available

9. **Action**: Verify orchestration bridge connectivity
10. **Command**: `PYTHONPATH=shared python -c "from shared.ci.integration.orchestration_bridge import SimplifiedOrchestrationBridge; print('✅ Orchestration bridge ready')"`
11. **Expected**: OrchestrationBridge imports successfully
12. **On failure**: Integration components not configured

## Phase 3: GitHub Actions Integration Status

1. **Action**: Check for GitHub Actions workflow
2. **Tool**: Read - `.github/workflows/continuous-improvement.yml`
3. **Expected**: CI workflow configured for duplicate detection
4. **On missing**: GitHub Actions integration not set up

5. **Action**: Check recent workflow runs
6. **Command**: `gh run list --workflow "Continuous Improvement - Code Duplication Detection" --limit 5`
7. **Expected**: Recent workflow runs visible
8. **On failure**: GitHub CLI not configured or no runs

## Phase 4: Metrics and Activity Overview

1. **Action**: Check for recent analysis reports
2. **Tool**: LS - `.ci-registry/reports/` to check for analysis files
3. **Expected**: Analysis reports or empty directory if no runs yet
4. **On missing**: No analysis activity recorded

5. **Action**: Get baseline duplicate analysis status
6. **Tool**: Read - `.ci-registry/baseline-duplicates.json` if exists
7. **Expected**: Baseline duplicates from initial setup
8. **On missing**: Initial baseline analysis not completed

## Phase 5: Status Summary Report

**Console Output Format**:

```
🔍 CI Monitoring Status Report

📊 System Health:
  CI Registry: [✅ Initialized / ❌ Not Found] (.ci-registry/ci_config.json)
  Configuration: [✅ Active / ❌ Missing] (Threshold: $THRESHOLD)
  ML Dependencies: [✅ Available / ❌ Missing] (faiss, transformers, torch)

🧠 Core Components:
  DuplicateFinder: [✅ Ready / ❌ Import Error]
  Registry Manager: [✅ Ready / ❌ Import Error]
  Orchestration Bridge: [✅ Ready / ❌ Import Error]

📈 Recent Activity (Last $HISTORY_DAYS days):
  Analysis Reports: $REPORT_COUNT found
  GitHub Workflow Runs: $WORKFLOW_RUNS
  Last Analysis: $LAST_ANALYSIS_DATE

🔧 GitHub Integration:
  Workflow: [✅ Configured / ❌ Missing] (.github/workflows/continuous-improvement.yml)
  Recent Status: [✅ Passing / ❌ Failing / ⏳ Running]

⚙️ Configuration:
  Project: $PROJECT_NAME
  Similarity Threshold: $THRESHOLD
  Auto-refactor: [✅ Enabled / ❌ Disabled]
  Languages Monitored: [$LANGUAGES]

🚀 Next Steps:
  - Run manual analysis: PYTHONPATH=shared python shared/ci/integration/orchestration_bridge.py
  - View detailed metrics: /ci-monitoring-status --verbose
  - Setup missing components: /setup-ci-monitoring
  - Check GitHub workflow: gh run list --workflow "Continuous Improvement - Code Duplication Detection"
```

**JSON Output** (when --verbose flag used):

```json
{
  "status": "active|partial|not_initialized",
  "system_health": {
    "ci_registry": {
      "status": "initialized",
      "config_path": ".ci-registry/project_config.json",
      "directories": ["cache", "reports", "backups"]
    },
    "ml_dependencies": {
      "status": "available",
      "packages": ["faiss-cpu", "transformers", "torch"],
      "missing": []
    }
  },
  "core_components": {
    "duplicate_finder": {
      "status": "ready",
      "import_test": "success"
    },
    "registry_manager": {
      "status": "ready",
      "import_test": "success"
    },
    "orchestration_bridge": {
      "status": "ready",
      "import_test": "success"
    }
  },
  "recent_activity": {
    "period_days": 7,
    "analysis_reports": 0,
    "workflow_runs": 3,
    "last_analysis": null
  },
  "github_integration": {
    "workflow_configured": true,
    "workflow_path": ".github/workflows/continuous-improvement.yml",
    "recent_status": "running"
  },
  "configuration": {
    "project_name": "ai-assisted-workflows",
    "similarity_threshold": 0.85,
    "auto_refactor_enabled": false,
    "languages": ["python", "javascript", "typescript", "php", "c"],
    "analysis_mode": "incremental"
  },
  "installation_path": ".ci-registry/",
  "last_updated": "$TIMESTAMP"
}
```

## Error Handling

**CI System Not Initialized**:

```
❌ Continuous Improvement system not found

The CI monitoring system has not been set up for this project.

Missing: .ci-registry/project_config.json

To initialize:
  claude /setup-ci-monitoring

This will:
  - Install ML dependencies (faiss, transformers, torch)
  - Initialize CI registry database
  - Configure duplicate detection system
  - Set up GitHub Actions workflow
```

**Missing Dependencies**:

```
❌ CI System Dependencies Missing

Missing Python packages for ML duplicate detection:
  - faiss-cpu: ❌ Not installed
  - transformers: ✅ Available
  - torch: ❌ Not installed

To fix:
  pip install faiss-cpu transformers torch sentence-transformers numpy scipy multilspy
```

**Components Available But Import Errors**:

```
⚠️  CI Components Import Issues

System initialized but components failing to import:
  - DuplicateFinder: ❌ ImportError: No module named 'shared.ci.core'
  - Registry Manager: ✅ Ready
  - Orchestration Bridge: ❌ ImportError: No module named 'shared'

Check PYTHONPATH and run from project root with:
  PYTHONPATH=shared python -m shared.ci.integration.orchestration_bridge
```

$ARGUMENTS
