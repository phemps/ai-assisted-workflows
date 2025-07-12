# Create an install.sh that copies the claude folder subdirectories to a choice of project folder or user folder specified as an argument, it should lead to adding them within a .claude directory, which the script may need to create or if present copy items to. Additionally we need to run the install scripts in scripts/setup for the analysis scripts and we need to add something to handle installing mcp tools context7 and sequential thinking.

**Status:** Refining
**Created:** 2025-07-12T15:54:31
**Agent PID:** 738

## Description
Create a comprehensive installation script (install.sh) that deploys the Claude Code Workflows system to user-specified locations. The script handles directory setup, copies all 18 workflow commands and 23 Python analysis scripts, installs Python dependencies via the existing setup infrastructure, and provides guidance for MCP tools installation (context7, sequential thinking, magic UI).

Key Requirements: Support custom installation paths with examples for project-local (./project/.claude) and user-global (~/.claude) locations, handle existing .claude directories gracefully, execute Python dependency installation using existing scripts/setup infrastructure, validate installations across platforms, and provide clear user guidance for MCP tools setup since these are Claude Code extensions rather than traditional packages.

## Implementation Plan
- [ ] **Create install.sh script** (install.sh:1-300) - Main installation script with argument parsing and environment detection
- [ ] **Add environment validation functions** (install.sh:20-80) - Check Python 3.7+, Node.js, Claude CLI, and platform compatibility
- [ ] **Implement directory setup logic with custom paths** (install.sh:85-120) - Handle user-specified installation paths with examples (./project/.claude, ~/.claude), validate paths, and handle existing .claude directories with conflict resolution
- [ ] **Add file copy operations** (install.sh:125-150) - Copy claude/ directory structure with proper permissions and filtering
- [ ] **Integrate Python dependency installation** (install.sh:155-180) - Leverage existing claude/scripts/setup/install_dependencies.py infrastructure
- [ ] **Add MCP tools installation guidance** (install.sh:185-220) - Install sequential-thinking and context7 MCP tools via Claude CLI
- [ ] **Create CLI integration** (install.sh:225-260) - Generate executable wrapper script for claude-workflows command
- [ ] **Add verification and testing** (install.sh:265-290) - Execute test_install.py and validate MCP tools installation
- [ ] **Implement error handling and logging** (install.sh:15-295) - Comprehensive error handling with rollback capability and detailed logging
- [ ] **Add usage documentation** (install.sh:1-15) - Usage examples, help text, installation modes, and custom path examples
- [ ] **Automated test**: Run install.sh in dry-run mode to verify script logic
- [ ] **User test**: Test installation script on target system with both custom paths and default modes

## Original Todo
Create an install.sh that copies the claude folder subdirectories to a choice of project folder or user folder specified as an argument, it should lead to adding them within a .claude directory, which the script may need to create or if present copy items to. Additionally we need to run the install scripts in scripts/setup for the analysis scripts and we need to add something to handle installing mcp tools context7 and sequential thinking.