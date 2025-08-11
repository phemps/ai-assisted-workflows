# Setup Continuous Improvement (`setup-continuous-improvement`)

**Purpose**: Configure proactive code duplication detection and refactoring automation for the current project
**Usage**: `claude /setup-continuous-improvement [--threshold=0.85] [--auto-refactor=false] [--languages=auto]`

## Phase 1: Environment Analysis

1. **Action**: Detect project technology stack and languages
2. **Tool**: Glob - `**/*.{py,ts,js,go,rs,java,php,rb}` to identify supported languages
3. **Action**: Verify Serena MCP availability and language server support
4. **Command**: `uvx --from git+https://github.com/oraios/serena serena --version`
5. **Action**: Check for existing continuous improvement setup
6. **Tool**: Read - `.ci-registry/config.json` to detect previous installations

**STOP** → Which languages should be monitored for duplicates? (detected: $DETECTED_LANGUAGES)

## Phase 2: Dependency Installation

1. **Action**: Install Python dependencies for continuous improvement system
2. **Command**: `pip install -r shared/lib/scripts/continuous-improvement/requirements.txt`
3. **Expected**: All packages installed successfully
4. **Action**: Setup Serena MCP server for project
5. **Command**: `claude mcp remove serena; claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ci-analyzer --project $(pwd)`
6. **Expected**: Serena MCP server connected and ready

## Phase 3: Configuration Setup

1. **Action**: Create continuous improvement configuration
2. **Tool**: Write - `.ci-registry/config.json` with project-specific settings:

   ```json
   {
     "project_name": "$PROJECT_NAME",
     "languages": ["$SELECTED_LANGUAGES"],
     "thresholds": {
       "exact_duplicate": 0.95,
       "near_duplicate": $THRESHOLD,
       "similar_pattern": 0.75
     },
     "auto_refactor": $AUTO_REFACTOR,
     "ignore_patterns": ["**/node_modules/**", "**/venv/**", "**/.git/**"]
   }
   ```

3. **Action**: Initialize code registry database
4. **Command**: `python shared/lib/scripts/continuous-improvement/core/registry_manager.py --init --project $(pwd)`
5. **Expected**: Registry initialized with project symbols

## Phase 4: GitHub Workflow Setup

1. **Action**: Create GitHub workflow file for continuous monitoring
2. **Tool**: Write - `.github/workflows/continuous-improvement.yml`:

   ```yaml
   name: Continuous Code Improvement

   on:
     push:
       branches: [main, develop]
     pull_request:
       types: [opened, synchronize]

   jobs:
     analyze-duplicates:
       runs-on: ubuntu-latest

       steps:
         - name: Checkout Code
           uses: actions/checkout@v4
           with:
             fetch-depth: 2

         - name: Setup Python
           uses: actions/setup-python@v4
           with:
             python-version: "3.11"

         - name: Install Dependencies
           run: |
             pip install -r shared/lib/scripts/continuous-improvement/requirements.txt

         - name: Setup Serena MCP
           run: |
             pip install uv
             uvx --from git+https://github.com/oraios/serena \
               serena start-mcp-server --context ci-analyzer --project .

         - name: Load Registry Cache
           uses: actions/cache@v3
           with:
             path: .ci-registry/
             key: ci-registry-${{ hashFiles('**/*.py', '**/*.ts', '**/*.js') }}

         - name: Analyze Changes
           run: |
             python shared/lib/scripts/continuous-improvement/workflows/github_monitor.py \
               --changed-files "${{ steps.changes.outputs.files }}" \
               --threshold $THRESHOLD
   ```

3. **Action**: Configure repository secrets if auto-refactor enabled
4. **Action**: Set up issue templates for duplication reports

**STOP** → Should the workflow create issues or PRs for detected duplicates? (recommended: issues for review)

## Phase 5: Initial Registry Population

1. **Action**: Perform initial codebase analysis
2. **Command**: `python shared/lib/scripts/continuous-improvement/analyzers/symbol_extractor.py --full-scan --project $(pwd)`
3. **Expected**: All existing symbols cataloged in registry

4. **Action**: Generate baseline similarity matrix
5. **Command**: `python shared/lib/scripts/continuous-improvement/analyzers/duplicate_finder.py --baseline --threshold $THRESHOLD`
6. **Expected**: Existing duplicates identified and logged

7. **Action**: Create initial improvement report
8. **Format**:

   ```markdown
   ## Continuous Improvement Setup Complete

   **Project**: $PROJECT_NAME
   **Languages**: $LANGUAGES
   **Symbols Cataloged**: $SYMBOL_COUNT
   **Existing Duplicates**: $DUPLICATE_COUNT
   **Threshold**: $THRESHOLD

   ### Next Steps:

   - Monitor commits for new duplicates
   - Review existing duplicates in `.ci-registry/baseline-duplicates.json`
   - Adjust thresholds in `.ci-registry/config.json` if needed
   ```

## Phase 6: CTO Agent Integration

1. **Action**: Configure CTO agent for complex refactoring decisions
2. **Tool**: Edit - `.ci-registry/config.json` to add CTO escalation rules:

   ```json
   {
     "cto_escalation": {
       "enabled": true,
       "triggers": {
         "complex_refactor_symbol_count": 5,
         "cross_file_duplicates": true,
         "architectural_changes": true
       },
       "auto_pr_threshold": 0.9
     }
   }
   ```

3. **Action**: Create CTO workflow trigger template
4. **Tool**: Write - `.github/workflows/cto-refactor.yml` for repository dispatch events

## Quality Gates

**Quality gate**: Serena MCP Connection
**Command**: `claude mcp list | grep serena`
**Pass criteria**: Serena appears as connected
**Failure action**: Retry installation with verbose logging

**Quality gate**: Registry Initialization
**Command**: `ls -la .ci-registry/`
**Pass criteria**: config.json, registry.faiss, and symbols.json exist
**Failure action**: Reinitialize with error logging

**Quality gate**: Workflow Validation
**Command**: `github-action-validator .github/workflows/continuous-improvement.yml`
**Pass criteria**: Workflow syntax valid
**Failure action**: Fix YAML syntax and retry

## Configuration Options

**Threshold Tuning**:

- `--threshold=0.95`: Only exact duplicates (strict)
- `--threshold=0.85`: Near duplicates (balanced, default)
- `--threshold=0.75`: Similar patterns (aggressive)

**Auto-refactor Modes**:

- `--auto-refactor=false`: Issues only (safe, default)
- `--auto-refactor=simple`: Simple extractions only
- `--auto-refactor=true`: All refactors (requires approval)

**Language Selection**:

- `--languages=auto`: Detect from codebase (default)
- `--languages=py,ts,js`: Specific language list
- `--languages=all`: Monitor all supported languages

## Troubleshooting

**Issue**: Serena MCP connection fails
**Solution**: Verify `uv` is installed, check project permissions, retry with `--verbose`

**Issue**: Registry initialization slow
**Solution**: Use `--languages` flag to limit scope, check available memory

**Issue**: High false positive rate
**Solution**: Increase `--threshold`, add patterns to ignore list

**Issue**: GitHub workflow not triggering
**Solution**: Verify workflow file permissions, check repository settings

## Expected Outcomes

- **Immediate**: Project configured with duplication monitoring
- **Within 1 week**: Baseline duplicates identified and reported
- **Ongoing**: New duplicates caught at commit time
- **Long-term**: Reduced code duplication and improved maintainability

$ARGUMENTS
