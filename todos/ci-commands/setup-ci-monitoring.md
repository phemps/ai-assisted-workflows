# Setup CI Monitoring (`setup-ci-monitoring`)

**Purpose**: Configure proactive code duplication detection and refactoring automation for the current project
**Usage**: `claude /setup-ci-monitoring [--threshold=0.85] [--auto-refactor=false]`

## Phase 1: Dependency Check and Setup

1. **Action**: Check for existing continuous improvement setup
2. **Tool**: Read - `.ci-registry/config.json` to detect previous installations
3. **Action**: Install continuous improvement dependencies (Python packages + MCP tools)
4. **Command**: `python shared/setup/ci/install_ci_dependencies.py`
5. **Expected**: All packages (MCP, CodeBERT, Faiss, transformers) installed successfully with user consent
6. **Note**: Script follows fail-fast behavior - exits clearly if dependencies unavailable

**STOP** → Dependencies installed. Ready to analyze environment?

## Phase 2: Environment Analysis

1. **Action**: Detect project technology stack automatically
2. **Tool**: Glob - `**/*.{py,ts,js,go,rs,java,php,rb}` to identify codebase
3. **Action**: Verify Serena MCP availability and language server support
4. **Command**: `uvx --from git+https://github.com/oraios/serena serena --version`
5. **Action**: Setup Serena MCP server for project
6. **Command**: `claude mcp remove serena; claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ci-analyzer --project $(pwd)`
7. **Expected**: Serena MCP server connected and ready

**STOP** → Detected [LANGUAGES], all code will be monitored for duplication automatically. Continue with setup?

## Phase 3: Configuration Setup + CTO Integration

1. **Action**: Setup project-specific continuous improvement configuration
2. **Command**: `python shared/setup/ci/setup_ci_project.py --project-dir $(pwd) --project-name "$PROJECT_NAME" --threshold $THRESHOLD $([ "$AUTO_REFACTOR" = "true" ] && echo "--auto-refactor")`
3. **Expected**: Configuration files created in .ci-registry/ and GitHub Actions workflows in .github/workflows/

4. **Action**: Initialize code registry database
5. **Command**: `python shared/ci/core/registry_manager.py --init --project $(pwd)`
6. **Expected**: Registry initialized with project symbols and language detection

**STOP** → Configuration created. Ready to setup GitHub Actions workflows?

## Phase 4: GitHub Actions Setup

1. **Action**: Verify GitHub workflows were created by setup script
2. **Tool**: LS - `.github/workflows/` to confirm workflow files exist
3. **Expected**: `continuous-improvement.yml` present with project-specific configuration

4. **Action**: Verify MCP integration setup instructions
5. **Tool**: Read - `.ci-registry/mcp-setup.md` for manual MCP configuration steps
6. **Expected**: Instructions ready for Serena MCP integration with claude command

**STOP** → GitHub workflows and MCP integration configured. Complete MCP setup manually using instructions in `.ci-registry/mcp-setup.md`. Ready for initial registry population?

## Phase 5: Initial Registry Population

1. **Action**: Perform initial codebase analysis and symbol extraction
2. **Command**: `python shared/ci/core/registry_manager.py --full-scan --project $(pwd)`
3. **Expected**: All existing symbols cataloged in registry

4. **Action**: Generate baseline duplicate analysis
5. **Command**: `python shared/ci/core/duplicate_finder.py --baseline --threshold $THRESHOLD`
6. **Expected**: Existing duplicates identified and logged

7. **Action**: Create initial improvement report
8. **Format**:

   ```markdown
   ## Continuous Improvement Setup Complete

   **Project**: $PROJECT_NAME
   **Symbols Cataloged**: $SYMBOL_COUNT
   **Existing Duplicates**: $DUPLICATE_COUNT
   **Threshold**: $THRESHOLD

   ### Next Steps:

   - Monitor commits for new duplicates
   - Review existing duplicates in `.ci-registry/baseline-duplicates.json`
   - Adjust thresholds in `.ci-registry/config.json` if needed
   ```

**STOP** → Registry populated. Ready for verification?

## Phase 6: Post-Setup Verification

1. **Action**: Run continuous improvement status check
2. **Command**: `claude /ci-monitoring-status --verbose`
3. **Expected**: All systems report as active and healthy

4. **Action**: Initialize monitoring baseline
5. **Command**: `python shared/ci/metrics/ci_metrics_collector.py report --days 1`
6. **Expected**: Initial metrics report generated successfully

7. **Action**: Test orchestration bridge connectivity
8. **Command**: `python shared/ci/integration/orchestration_bridge.py --project-root $(pwd)`
9. **Expected**: Orchestration bridge runs successfully (may show no duplicates for clean project)

10. **Action**: Create setup completion report
11. **Format**:

    ````markdown
    ## Continuous Improvement Setup Complete

    **Project**: $PROJECT_NAME
    **Setup Completed**: $(date)
    **Baseline Symbols**: $SYMBOL_COUNT
    **Quality Gates**: $AVAILABLE_GATES

    ### System Status:

    - CI Framework: Active
    - Database: Initialized (.ci-registry/)
    - Python Dependencies: Installed
    - Serena MCP: $MCP_STATUS
    - Quality Gates: $GATE_COUNT detected
    - Agent Integration: Ready

    ### Quick Start:

    ```bash
    # Check system status anytime
    claude /ci-monitoring-status

    # Generate metrics report
    python shared/ci/metrics/ci_metrics_collector.py report

    # Find duplicates manually
    python shared/ci/integration/orchestration_bridge.py
    ```
    ````

    ### Monitoring Setup:

    - Commit hooks: Automatic analysis enabled
    - GitHub Actions: Workflow configured
    - CTO escalation: Configured for complex refactors
    - Metrics collection: Active

    Ready to start continuous improvement!

    ```

    ```

**STOP** → Continuous improvement system is now fully operational. Check status with `/ci-monitoring-status`

$ARGUMENTS
