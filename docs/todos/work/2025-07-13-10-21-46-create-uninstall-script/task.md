# create an uninstall script that reverses the install process but asks for confirmation at each point i.e. remove scripts? remove python libraries (list them)? remove mcp servers (list them)? The mcp server list should be backed up before hand.

**Status:** Refining
**Created:** 2025-07-13T10:21:46
**Agent PID:** 36629

## Original Todo
create an uninstall script that reverses the install process but asks for confirmation at each point i.e. remove scripts? remove python libraries (list them)? remove mcp servers (list them)? The mcp server list should be backed up before hand.

## Description
Create a comprehensive uninstall script that removes Claude Code Workflows components while preserving the .claude directory structure. The script should:

1. **Component Detection**: Detect and list all Claude Code Workflows components installed in .claude directory
2. **Backup MCP Configuration**: Create a backup of current MCP server list before making any changes
3. **Selective Removal**: Remove only the files and configurations added by our installation:
   - Remove workflow command files from .claude/commands/
   - Remove analysis script files from .claude/scripts/
   - Remove rule files from .claude/rules/
   - Remove our sections from claude.md (Build Approach Flags section)
4. **Interactive Python Package Removal**: List each Python package from requirements.txt and ask yes/no for removal
5. **Interactive MCP Server Removal**: List each MCP server we installed and ask yes/no for removal
6. **Preserve User Content**: Keep the .claude directory and any user-added files intact

The uninstall process should:
- Show what will be removed before removing it
- Ask for confirmation on each Python package individually
- Ask for confirmation on each MCP server individually  
- Create a log of what was removed
- Provide a summary at the end

## Implementation Plan
- [ ] Create uninstall.sh in project root (same location as install.sh)
- [ ] Add script header with logging functions from install.sh (uninstall.sh:1-50)
- [ ] Implement .claude directory detection logic (uninstall.sh:51-100)
- [ ] Create function to remove workflow command files (uninstall.sh:101-150)
- [ ] Create function to remove script directories (uninstall.sh:151-200)
- [ ] Create function to remove rule files (uninstall.sh:201-250)
- [ ] Create function to remove claude.md sections (uninstall.sh:251-300)
- [ ] Create function to backup MCP server list (uninstall.sh:301-350)
- [ ] Create function to list and remove Python packages interactively (uninstall.sh:351-450)
- [ ] Create function to list and remove MCP servers interactively (uninstall.sh:451-550)
- [ ] Add main execution flow with confirmation prompts (uninstall.sh:551-650)
- [ ] Add command line argument parsing (--dry-run, --verbose, --help) (uninstall.sh:651-700)
- [ ] Automated test: Test dry-run mode
- [ ] Automated test: Test component detection
- [ ] User test: Run uninstall on test installation
- [ ] User test: Verify selective removal works correctly

## Notes