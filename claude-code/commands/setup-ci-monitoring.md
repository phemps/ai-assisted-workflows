# Setup CI Monitoring (`setup-ci-monitoring`)

**Purpose**: Configure proactive code duplication detection and refactoring automation for the current project
**Usage**: `claude /setup-ci-monitoring [--threshold=0.85] [--auto-refactor=false]`

## Phase 1: Dependency Check and Setup

1. **Action**: Check for existing continuous improvement setup
2. **Tool**: Read - `.ci-registry/config.json` to detect previous installations
3. **Action**: Install continuous improvement dependencies (Python packages + MCP tools)
4. **Command**: `python shared/setup/ci/install_ci_dependencies.py`
5. **Expected**: All packages (MCP, CodeBERT, ChromaDB, transformers) installed successfully with user consent
6. **Note**: Script follows fail-fast behavior - exits clearly if dependencies unavailable

7. **Action**: Install language server dependencies for comprehensive language support
8. **Languages Supported**: Python, TypeScript, JavaScript, Java, Rust (built-in) + Go, C# (automatically installed)
9. **Local Development Dependencies** (optional for user setup):

   ```bash
   # For Go language support (local development)
   brew install go                           # Install Go runtime
   go install golang.org/x/tools/gopls@latest  # Install Go language server

   # For C# language support (local development)
   brew install --cask dotnet               # Install .NET runtime (macOS)
   # OR: brew install mono                  # Alternative: Mono runtime
   ```

10. **GitHub Actions**: Go and C# language servers automatically installed in CI workflows
11. **Impact**: GitHub Actions workflows include full language support. For local duplicate detection, Go/C# files require the runtime dependencies above.

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
5. **Command**: `python shared/ci/core/chromadb_storage.py --init --project $(pwd)`
6. **Expected**: ChromaDB collection initialized with project symbols and language detection

**STOP** → Configuration created. Ready to setup real-time indexing hooks?

## Phase 3.5: Real-time Indexing Hook Setup

1. **Action**: Verify ChromaDB indexing hook script availability
2. **FIRST - Resolve HOOK_SCRIPT_PATH**:

   a. **Try shared CI hooks folder**:

   ```bash
   Glob: "shared/ci/hooks/chromadb_index_hook.py"
   ```

   b. **Try alternate locations**:

   ```bash
   Bash: ls "$HOME/.claude/scripts/ci/hooks/chromadb_index_hook.py"
   ```

   c. **Interactive fallback if not found**:

   - List searched locations: `shared/ci/hooks/` and `$HOME/.claude/scripts/ci/hooks/`
   - Ask user: "Could not locate ChromaDB indexing hook script. Please provide full path to chromadb_index_hook.py:"
   - Validate provided path contains executable Python script
   - Set HOOK_SCRIPT_PATH to user-provided location

3. **Action**: Configure Claude Code PostToolUse hooks for real-time indexing
4. **Tool**: Read - Check existing `.claude/settings.local.json`
5. **Action**: Merge PostToolUse hook configuration (preserve existing hooks)
6. **Tool**: Write - Update `.claude/settings.local.json` with:
   ```json
   {
     "hooks": {
       "PostToolUse": [
         {
           "matcher": "Write|Edit|MultiEdit",
           "hooks": [
             {
               "type": "command",
               "command": "python $CLAUDE_PROJECT_DIR/[HOOK_SCRIPT_PATH]",
               "timeout": 5
             }
           ]
         }
       ]
     }
   }
   ```
7. **Expected**: PostToolUse hooks configured for file modification tools

8. **Action**: Make hook script executable
9. **Command**: `chmod +x [HOOK_SCRIPT_PATH]`
10. **Expected**: Hook script has executable permissions

11. **Action**: Test hook configuration
12. **Command**: Test with empty JSON to verify script handles input gracefully:
    ```bash
    echo '{}' | CLAUDE_PROJECT_DIR=$(pwd) python [HOOK_SCRIPT_PATH]
    ```
13. **Expected**: Script exits with code 0 (no errors)

14. **Message**: Display to user:

    ```
    Real-time indexing configured! ChromaDB will automatically index files when you:
    - Create new files (Write tool)
    - Edit existing files (Edit tool)
    - Make multiple edits (MultiEdit tool)

    Configuration saved to .claude/settings.local.json (not committed to git)
    Hook logs available at: .ci-registry/logs/chromadb_hooks.log
    ```

**STOP** → Real-time indexing hooks configured. Ready to setup GitHub Actions workflows?

## Phase 4: GitHub Actions Setup

1. **Action**: Verify GitHub workflows were created by setup script
2. **Tool**: LS - `.github/workflows/` to confirm workflow files exist
3. **Expected**: `continuous-improvement.yml` present with project-specific configuration

4. **Action**: Verify MCP integration setup instructions
5. **Tool**: Read - `.ci-registry/mcp-setup.md` for manual MCP configuration steps
6. **Expected**: Instructions ready for Serena MCP integration with claude command

**STOP** → GitHub workflows and MCP integration configured. Complete MCP setup manually using instructions in `.ci-registry/mcp-setup.md`. Ready for initial registry population?

## Phase 5: Initial Registry Population

1. **Action**: Start initial codebase indexing in background (for user setup)
2. **Command**: `python shared/ci/core/chromadb_storage.py --full-scan --project-root $(pwd) &`
3. **Message**: Display to user: "Initial codebase indexing started in background. This may take 1-5 minutes for large codebases. Check status with \`claude /ci-monitoring-status\`"
4. **Expected**: Background indexing process started

5. **Action**: For GitHub Actions workflows, indexing runs synchronously
6. **Note**: GitHub Actions will automatically detect incomplete indexing and run full scan before duplicate detection

7. **Action**: Verify indexing completion (optional check)
8. **Command**: `python shared/ci/core/chromadb_storage.py --check-indexing --project-root $(pwd)`
9. **Expected**: Indexing status reported with symbol counts

10. **Action**: Create initial improvement report
11. **Format**:

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

10. **Action**: Verify real-time indexing hooks are configured
11. **Tool**: Read - `.claude/settings.local.json`
12. **Expected**: PostToolUse hooks configured for Write|Edit|MultiEdit
13. **Action**: Test hook functionality
14. **Command**:
    ```bash
    echo '{"tool_name":"Write","tool_input":{"file_path":"test.py"},"tool_response":{"success":true}}' | \
    CLAUDE_PROJECT_DIR=$(pwd) python shared/ci/hooks/chromadb_index_hook.py
    ```
15. **Expected**: Hook executes without errors
16. **Action**: Verify hook logging
17. **Tool**: Read - `.ci-registry/logs/chromadb_hooks.log` (if exists)
18. **Expected**: Hook activity logged (or log file created for future use)

19. **Action**: Create setup completion report
20. **Format**:

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
    - Real-time Indexing: Active (PostToolUse hooks)

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

    - Real-time indexing: PostToolUse hooks for Write/Edit/MultiEdit
    - Hook configuration: .claude/settings.local.json (not committed)
    - GitHub Actions: Workflow configured
    - CTO escalation: Configured for complex refactors
    - Metrics collection: Active

    Ready to start continuous improvement!

    ```

    ```

**STOP** → Continuous improvement system is now fully operational. Check status with `/ci-monitoring-status`

$ARGUMENTS
