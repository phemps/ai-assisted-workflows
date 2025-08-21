# Installation and Setup

## 📦 Installation

```bash
./claude-code/install.sh              # Install to current directory
./claude-code/install.sh ~            # Install globally
/setup-dev-monitoring                 # Optional: Setup unified dev logging
/setup-ci-monitoring                  # Optional: Continuous improvement monitoring with duplicate detection
/add-serena-mcp                       # Recommended per project mcp lsp tool
```

## 🤖 Free Tier AI CLI Tools

**Maximize session uptime with free AI CLI tools that extend workflow capabilities:**

```bash
# Gemini CLI - Context-heavy analysis (1,000 requests/day)
npm install -g @google/gemini-cli
gemini  # OAuth authentication

# Qwen Code CLI - Tool-intensive operations (2,000 requests/day)
npm install -g @qwen-code/qwen-code@latest
qwen    # OAuth authentication
```

**Benefits:**

- 🔋 **Extended uptime**: Preserve Claude Code subscription for core interactions
- 🆓 **Free tier leverage**: 3,000+ daily requests across both tools
- 🔄 **Smart fallback**: Automatic degradation to Claude Code on limits
- 📊 **Usage optimization**: Built-in rate limiting and request management

## 🔧 Dependencies

Due to the programmatic analysis scripts, there's quite a lot of dependencies installed.
Full list of libraries used and languages supported found here: [Analysis Scripts](analysis-scripts.md)

## Installation Details

### Installation Options

```bash
# Current directory (uses ./.claude/)
./claude-code/install.sh

# User global (uses ~/.claude/)
./claude-code/install.sh ~

# Custom location
./claude-code/install.sh /my/project/path

# Advanced options
./claude-code/install.sh --dry-run       # Preview changes without making modifications
./claude-code/install.sh --verbose      # Enable detailed debug output
./claude-code/install.sh --skip-mcp     # Skip MCP tools installation (Python scripts only)
./claude-code/install.sh --skip-python  # Skip Python dependencies installation
./claude-code/install.sh --help         # Show detailed help and usage information
```

### Dependencies Installation

The installer automatically handles all dependencies:

**Python Dependencies:**
- Runs `shared/setup/install_dependencies.py` to install packages from `shared/setup/requirements.txt`
- Optionally installs CI framework dependencies from `shared/setup/ci/requirements.txt`
- Validates Python 3.7+ compatibility

**Node.js Dependencies:**
- Automatically installs ESLint and plugins via npm if not present
- Creates a `package.json` in the installation directory
- Installs comprehensive frontend analysis tools (ESLint, TypeScript, React, Vue, Svelte plugins)

**Installation Tracking:**
- Creates an installation log for clean uninstallation tracking
- Tracks which packages were pre-existing vs newly installed

### Handling Existing .Claude Installations

**Automatic Backup:** All installation options automatically create a timestamped backup of your existing installation before making any changes.

The installer automatically detects existing `.claude` directories and offers four options:

1. **Fresh Install:** Complete replacement of existing installation
2. **Merge:** Preserve user customizations while adding new features (no overwrites)
3. **Update Workflows Only:** Update built-in commands and scripts while preserving custom commands and all other files (recommended for updates)
4. **Cancel:** Exit without changes

## Uninstalling

To safely remove AI-Assisted Workflows components while preserving your .claude directory:

```bash
# Preview what would be removed (recommended first step)
./uninstall.sh --dry-run

# Uninstall from current directory
./uninstall.sh

# Uninstall from specific path
./uninstall.sh /path/to/installation

# Verbose output for detailed logging
./uninstall.sh --verbose
```

**Smart Uninstall Features:**

- **📦 Safe Removal**: Only removes workflow components, preserves .claude structure and user files
- **⚠️ Dependency Tracking**: Distinguishes pre-existing vs newly installed Python packages/MCP servers using installation-log.txt
- **💾 Automatic Backups**: Creates backups of MCP configuration and claude.md before changes
- **🧹 Thorough Cleanup**: Removes **pycache** folders and empty directories
- **📝 Installation Log**: Uses installation-log.txt to provide intelligent removal warnings

The uninstaller will interactively prompt for each Python package and MCP server removal, showing whether each item was:

- **🔧 Newly installed** by AI-Assisted Workflows (safer to remove)
- **⚠️ Pre-existing** before installation (likely used by other projects - caution advised)
