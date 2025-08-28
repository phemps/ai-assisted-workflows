# Setup CI Monitoring (`setup-ci-monitoring`)

**Purpose**: Configure proactive code duplication detection and refactoring automation for the current project
**Usage**: `claude /setup-ci-monitoring [--threshold=0.85] [--auto-refactor=false]`

## ⚠️ CRITICAL EXECUTION INSTRUCTIONS ⚠️

**THIS SETUP REQUIRES USER INTERACTION AT CHECKPOINTS**

- This command has 4 mandatory checkpoints that require user confirmation
- **DO NOT** run all phases automatically without stopping
- **MUST** wait for user approval at each `⚠️ MANDATORY CHECKPOINT` before proceeding
- Each checkpoint includes explicit instructions on what to ask the user
- **VIOLATION OF CHECKPOINTS WILL RESULT IN INCOMPLETE SETUP**

## Phase 1: Script Path Resolution

**FIRST - Resolve SCRIPT_PATH:**

1. **Try project-level .claude folder**:

   ```bash
   Glob: ".claude/scripts/**/*.py"
   ```

2. **Try user-level .claude folder**:

   ```bash
   Bash: ls "$HOME/.claude/scripts/"
   ```

3. **Interactive fallback if not found**:
   - List searched locations: `.claude/scripts/` and `$HOME/.claude/scripts/`
   - Ask user: "Could not locate CI analysis scripts. Please provide full path to the scripts directory:"
   - Validate provided path contains expected scripts (setup/, ci/, core/ subdirectories)
   - Set SCRIPT_PATH to user-provided location

**THEN - Execute all operations with resolved SCRIPT_PATH:**

## ⚠️ MANDATORY CHECKPOINT 1 ⚠️

**STOP AND WAIT FOR USER CONFIRMATION**

Script path resolved to: `[SCRIPT_PATH]`

**DO NOT PROCEED AUTOMATICALLY**

- Display this message to the user
- Wait for explicit user approval before continuing
- Ask: "Script path resolved successfully. Ready to install dependencies? (Type 'yes' to continue)"
- Only proceed to Phase 2 after receiving user confirmation

## Phase 2: Dependency & Environment Setup

1. **Install continuous improvement dependencies**

   ```bash
   python [SCRIPT_PATH]/setup/ci/install_ci_dependencies.py
   ```

   **Expected**: All packages (MCP, CodeBERT, ChromaDB, transformers) installed successfully with user consent

2. **Install language server dependencies for comprehensive language support**
   **Languages Supported**: Python, TypeScript, JavaScript, Java, Rust (built-in) + Go, C# (automatically installed)
   **Local Development Dependencies** (optional for user setup):

   ```bash
   # For Go language support (local development)
   brew install go                           # Install Go runtime
   go install golang.org/x/tools/gopls@latest  # Install Go language server

   # For C# language support (local development)
   brew install --cask dotnet               # Install .NET runtime (macOS)
   # OR: brew install mono                  # Alternative: Mono runtime
   ```

3. **Detect project technology stack automatically**

   ```bash
   Glob: "**/*.{py,ts,js,go,rs,java,php,rb}"
   ```

4. **Verify Serena MCP availability and language server support**

   ```bash
   uvx --from git+https://github.com/oraios/serena serena --help | head -5
   ```

5. **Setup Serena MCP server for project**
   ```bash
   claude mcp remove serena; claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ci-analyzer --project $(pwd)
   ```
   **Expected**: Serena MCP server connected and ready

## ⚠️ MANDATORY CHECKPOINT 2 ⚠️

**STOP AND WAIT FOR USER CONFIRMATION**

Dependencies installed successfully. Detected languages: `[LANGUAGES]`
All code will be monitored for duplication automatically.

**DO NOT PROCEED AUTOMATICALLY**

- Display dependency installation results to the user
- Show detected languages and technology stack
- Wait for explicit user approval before continuing
- Ask: "Dependencies installed and languages detected. Ready for system configuration? (Type 'yes' to continue)"
- Only proceed to Phase 3 after receiving user confirmation

## Phase 3: System Configuration

1. **Setup project-specific continuous improvement configuration**

   ```bash
   PROJECT_NAME=$(basename "$(pwd)"); PYTHONPATH="[SCRIPT_PATH]/utils:[SCRIPT_PATH]" python [SCRIPT_PATH]/setup/ci/setup_ci_project.py --project-dir $(pwd) --project-name "$PROJECT_NAME" --threshold $THRESHOLD $([ "$AUTO_REFACTOR" = "true" ] && echo "--auto-refactor")
   ```

   **Expected**: Configuration files created in .ci-registry/ and GitHub Actions workflows in .github/workflows/ (without paths section)

2. **Configure Claude Code PostToolUse hooks for real-time indexing**
   **Tool**: Read - Check existing `.claude/settings.local.json`
   **Tool**: Write - Update `.claude/settings.local.json` with hook command using resolved paths:

   ```json
   {
     "hooks": {
       "PostToolUse": [
         {
           "matcher": "Write|Edit|MultiEdit",
           "hooks": [
             {
               "type": "command",
               "command": "python [SCRIPT_PATH]/ci/hooks/chromadb_index_hook.py --indexer-path \"[SCRIPT_PATH]/ci/core/chromadb_indexer.py\"",
               "timeout": 5
             }
           ]
         }
       ]
     }
   }
   ```

   **Expected**: PostToolUse hooks configured for file modification tools

3. **Make hook script executable**

   ```bash
   chmod +x [SCRIPT_PATH]/ci/hooks/chromadb_index_hook.py
   ```

4. **Initialize code registry database**

   ```bash
   PYTHONPATH="[SCRIPT_PATH]/utils:[SCRIPT_PATH]" python [SCRIPT_PATH]/ci/core/chromadb_storage.py --clear-collection --project-root $(pwd)
   ```

   **Expected**: ChromaDB collection initialized with project symbols and language detection

5. **Start initial codebase indexing**
   ```bash
   PYTHONPATH="[SCRIPT_PATH]/utils:[SCRIPT_PATH]" python [SCRIPT_PATH]/ci/core/chromadb_storage.py --full-scan --project-root $(pwd) &
   ```
   **Message**: Display to user: "Initial codebase indexing started in background. This may take 1-5 minutes for large codebases."

## ⚠️ MANDATORY CHECKPOINT 3 ⚠️

**STOP AND WAIT FOR USER CONFIRMATION**

System configured successfully:

- Real-time indexing hooks active (PostToolUse)
- Initial registry population started in background
- ChromaDB collection initialized
- GitHub workflows configured

**DO NOT PROCEED AUTOMATICALLY**

- Display configuration summary to the user
- Show hook status and indexing progress
- Wait for explicit user approval before continuing
- Ask: "System configured and background indexing started. Ready for verification and testing? (Type 'yes' to continue)"
- Only proceed to Phase 4 after receiving user confirmation

## Phase 4: Verification & Reporting

1. **Test hook functionality**

   ```bash
   echo '{}' | CLAUDE_PROJECT_DIR=$(pwd) PYTHONPATH="[SCRIPT_PATH]/utils:[SCRIPT_PATH]" python [SCRIPT_PATH]/ci/hooks/chromadb_index_hook.py --indexer-path "[SCRIPT_PATH]/ci/core/chromadb_indexer.py"
   ```

   **Expected**: Script exits with code 0 (no errors)

2. **Verify GitHub workflows were created**
   **Tool**: LS - `.github/workflows/` to confirm workflow files exist
   **Expected**: `continuous-improvement.yml` present with project-specific configuration

3. **Run continuous improvement status check**

   ```bash
   claude /ci-monitoring-status --verbose
   ```

   **Expected**: All systems report as active and healthy

4. **Generate initial metrics report**

   ```bash
   PYTHONPATH="[SCRIPT_PATH]/utils:[SCRIPT_PATH]" python [SCRIPT_PATH]/ci/metrics/ci_metrics_collector.py report --days 1
   ```

   **Expected**: Initial metrics report generated successfully

5. **Test orchestration bridge connectivity**

   ```bash
   PYTHONPATH="[SCRIPT_PATH]/utils:[SCRIPT_PATH]" python [SCRIPT_PATH]/ci/integration/orchestration_bridge.py --project-root $(pwd)
   ```

   **Expected**: Orchestration bridge runs successfully (may show no duplicates for clean project)

6. **Create setup completion report**:

   ````markdown
   ## Continuous Improvement Setup Complete

   **Project**: $PROJECT_NAME
   **Setup Completed**: $(date)
   **Baseline Symbols**: $SYMBOL_COUNT
   **Threshold**: $THRESHOLD

   ### System Status:

   - CI Framework: Active
   - Database: Initialized (.ci-registry/)
   - Python Dependencies: Installed
   - Serena MCP: Connected
   - Real-time Indexing: Active (PostToolUse hooks)
   - GitHub Actions: Configured

   ### Real-time Indexing:

   ChromaDB will automatically index files when you:

   - Create new files (Write tool)
   - Edit existing files (Edit tool)
   - Make multiple edits (MultiEdit tool)

   Configuration saved to .claude/settings.local.json (not committed to git)
   Hook logs available at: .ci-registry/logs/chromadb_hooks.log

   ### Quick Start:

   ```bash
   # Check system status anytime
   claude /ci-monitoring-status

   # Generate metrics report
   python [SCRIPT_PATH]/ci/metrics/ci_metrics_collector.py report

   # Find duplicates manually
   python [SCRIPT_PATH]/ci/integration/orchestration_bridge.py
   ```
   ````

   Ready to start continuous improvement!

   ```

   ```

## ✅ SETUP COMPLETE - FINAL CHECKPOINT ✅

**STOP AND PRESENT COMPLETION SUMMARY**

**CONTINUOUS IMPROVEMENT SYSTEM FULLY OPERATIONAL**

**DO NOT PROCEED FURTHER - SETUP IS COMPLETE**

- Present the setup completion report to the user
- Highlight key system status and next steps
- Inform user they can check status anytime with `/ci-monitoring-status`
- Wait for user acknowledgment or questions
- **TASK COMPLETE** - No further automated actions required

$ARGUMENTS
