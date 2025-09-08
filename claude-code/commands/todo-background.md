---
description: Fires off a full Claude Code instance in the background
argument-hint: [prompt] [model] [report-file]
allowed-tools: Bash, BashOutput, Read, Edit, MultiEdit, Write, Grep, Glob, WebFetch, WebSearch, TodoWrite, Task
---

# Background Claude Code

Run a Claude Code instance in the background to perform tasks autonomously while you continue working.

## Variables

USER_PROMPT: $1
MODEL: $2 (defaults to 'sonnet' if not provided)
REPORT_FILE: $3 (defaults to './agents/background/background-report-DAY-NAME_HH_MM_SS.md' if not provided)

## Instructions

- Capture timestamp in a variable FIRST to ensure consistency across file creation and references
- Create the initial report file with header BEFORE launching the background agent
- Fire off a new Claude Code instance using the Bash tool with run_in_background=true
- IMPORTANT: Pass the `USER_PROMPT` exactly as provided with no modifications
- Set the model to either 'sonnet' or 'opus' based on `MODEL` parameter
- Configure Claude Code with all necessary flags for automated operation
- All report format instructions are embedded in the --append-system-prompt
- Use --print flag to run in non-interactive mode
- Use --output-format text for standard text output
- Use --dangerously-skip-permissions to bypass permission prompts for automated operation
- Use all provided CLI flags AS IS. Do not alter them.

## Process

1. **Capture timestamp** - Store current timestamp for consistent file naming
2. **Create report file** - Initialize the report file with header and timestamp
3. **Launch background instance** - Start Claude Code with all required flags
4. **Configure monitoring** - Set up progress tracking and output capture
5. **Confirm launch** - Report successful background task initiation

## Command Structure

```bash
# Capture timestamp for consistency
TIMESTAMP=$(date +"%A_%H_%M_%S")
DEFAULT_REPORT="./agents/background/background-report-${TIMESTAMP}.md"
REPORT_FILE=${3:-$DEFAULT_REPORT}

# Create initial report file
mkdir -p "$(dirname "$REPORT_FILE")"
echo "# Background Task Report - $(date)" > "$REPORT_FILE"
echo "## Task: $1" >> "$REPORT_FILE"
echo "## Started: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Launch background Claude Code instance
claude --model "${2:-sonnet}" \
  --print \
  --output-format text \
  --dangerously-skip-permissions \
  --append-system-prompt "Report all progress and results to: $REPORT_FILE. Use Write tool to append updates." \
  "$1"
```

## Usage Examples

- `/todo-background "Analyze the codebase for performance issues"` - Uses default sonnet model and auto-generated report file
- `/todo-background "Refactor the authentication module" opus ./reports/auth-refactor.md` - Uses opus model with custom report location
- `/todo-background "Run security audit and create remediation plan" sonnet` - Sonnet model with default report location

## Output

- **Background Process ID** - For monitoring the running task
- **Report File Location** - Where progress updates will be written
- **Task Summary** - Brief description of what was initiated
- **Monitoring Instructions** - How to check progress and results

$ARGUMENTS
