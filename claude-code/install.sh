#!/bin/bash
# ai assisted workflows Installation Script
# Installs the complete workflow system with commands, scripts, and dependencies

set -euo pipefail

# Script configuration
SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/claude-workflows-install.log"

# Usage and help
show_usage() {
    cat << 'EOF'
Claude Code Workflows Installer

USAGE:
    ./install.sh [TARGET_PATH] [OPTIONS]

ARGUMENTS:
    TARGET_PATH     Directory where .claude/ will be created
                   Examples:
                     ~/                    (User global: ~/.claude/)
                     ./myproject           (Project local: ./myproject/.claude/)
                     /path/to/project      (Custom path: /path/to/project/.claude/)
                   Default: current directory

OPTIONS:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -n, --dry-run   Show what would be done without making changes
    --skip-mcp      Skip MCP tools installation
    --skip-python   Skip Python dependencies installation

EXAMPLES:
    # Install in current project (creates ./.claude/)
    ./install.sh

    # Install globally for user (creates ~/.claude/)
    ./install.sh ~

    # Install in specific project
    ./install.sh /path/to/my-project

    # Dry run to see what would happen
    ./install.sh --dry-run

    # Install without MCP tools
    ./install.sh --skip-mcp

REQUIREMENTS:
    - Python 3.7+
    - Node.js (for MCP tools)
    - Claude CLI (for MCP tools)
    - Internet connection for dependencies

EOF
}

# Global variables
VERBOSE=false
DRY_RUN=false
SKIP_MCP=false
SKIP_PYTHON=false

# Parse command line arguments
parse_args() {
    # Reset TARGET_PATH to empty to detect if user provided one
    TARGET_PATH=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-mcp)
                SKIP_MCP=true
                shift
                ;;
            --skip-python)
                SKIP_PYTHON=true
                shift
                ;;
            -*)
                echo "Unknown option: $1" >&2
                show_usage
                exit 1
                ;;
            *)
                if [[ -z "$TARGET_PATH" ]]; then
                    TARGET_PATH="$1"
                else
                    echo "Error: Multiple target paths specified" >&2
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Set default if no target path provided
    if [[ -z "$TARGET_PATH" ]]; then
        TARGET_PATH="$(pwd)"
    fi
}

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        log "$@"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
    fi
}

log_error() {
    echo "[ERROR] $*" | tee -a "$LOG_FILE" >&2
}

# Platform detection
detect_platform() {
    case "$(uname -s)" in
        Darwin*)
            PLATFORM="macos"
            ;;
        Linux*)
            PLATFORM="linux"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            PLATFORM="windows"
            ;;
        *)
            log_error "Unsupported platform: $(uname -s)"
            exit 1
            ;;
    esac
    log_verbose "Detected platform: $PLATFORM"
}

# Environment validation
check_python() {
    log_verbose "Checking Python installation..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        echo "Please install Python 3.7+ and try again"
        exit 1
    fi

    local python_version
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    log_verbose "Found Python $python_version"

    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)"; then
        log_error "Python 3.7+ is required, found Python $python_version"
        exit 1
    fi

    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not found"
        echo "Please install pip3 and try again"
        exit 1
    fi
}

check_node() {
    log_verbose "Checking Node.js installation..."

    if ! command -v node &> /dev/null; then
        log_error "Node.js is required for frontend analysis and MCP tools"
        echo "Install Node.js from https://nodejs.org"
        exit 1
    fi

    if ! command -v npm &> /dev/null; then
        log_error "npm is required for frontend analysis dependencies"
        echo "Install npm (usually comes with Node.js)"
        exit 1
    fi

    local node_version
    node_version=$(node --version)
    local npm_version
    npm_version=$(npm --version)
    log_verbose "Found Node.js $node_version, npm $npm_version"
}

check_claude_cli() {
    if [[ "$SKIP_MCP" == "true" ]]; then
        log_verbose "Skipping Claude CLI check (MCP installation disabled)"
        return 0
    fi

    log_verbose "Checking Claude CLI installation..."

    if ! command -v claude &> /dev/null; then
        log_error "Claude CLI is required for MCP tools but not installed"
        echo "Install Claude CLI from https://claude.ai/code or use --skip-mcp to skip MCP tools"
        exit 1
    fi

    local claude_version
    claude_version=$(claude --version 2>/dev/null || echo "unknown")
    log_verbose "Found Claude CLI $claude_version"
}

check_eslint() {
    log "Checking ESLint installation (required for frontend analysis)..."

    # Check if ESLint is available via npx
    if ! npx eslint --version &> /dev/null; then
        log "ESLint not found, installing required packages..."
        install_eslint_packages
    else
        log_verbose "ESLint found, verifying required plugins..."
        verify_eslint_plugins
    fi
}

check_security_tools() {
    log "Checking security analysis tools (required for semantic analysis)..."

    # Check if Semgrep is available
    if ! command -v semgrep &> /dev/null; then
        log "Semgrep not found, will be installed with Python dependencies..."
        SEMGREP_MISSING=true
    else
        local semgrep_version
        semgrep_version=$(semgrep --version 2>/dev/null || echo "unknown")
        log_verbose "Found Semgrep $semgrep_version"
    fi

    # Check if detect-secrets is available
    if ! command -v detect-secrets &> /dev/null; then
        log "detect-secrets not found, will be installed with Python dependencies..."
        DETECT_SECRETS_MISSING=true
    else
        local detect_secrets_version
        detect_secrets_version=$(detect-secrets --version 2>/dev/null || echo "unknown")
        log_verbose "Found detect-secrets $detect_secrets_version"
    fi

    # Check if sqlfluff is available
    if ! command -v sqlfluff &> /dev/null; then
        log "SQLFluff not found, will be installed with Python dependencies..."
        SQLFLUFF_MISSING=true
    else
        local sqlfluff_version
        sqlfluff_version=$(sqlfluff --version 2>/dev/null || echo "unknown")
        log_verbose "Found SQLFluff $sqlfluff_version"
    fi
}

install_eslint_packages() {
    log "Installing ESLint and required plugins..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "Would install ESLint packages"
        return 0
    fi

    cd "$INSTALL_DIR"

    # Create package.json if it doesn't exist
    if [[ ! -f "package.json" ]]; then
        log_verbose "Creating package.json..."
        cat > package.json << EOF
{
  "name": "claude-code-workflows",
  "version": "1.0.0",
  "description": "Frontend analysis dependencies for Claude Code Workflows",
  "private": true,
  "devDependencies": {}
}
EOF
    fi

    # Install ESLint and required plugins
    log_verbose "Installing ESLint packages..."
    if npm install --save-dev \
        eslint@latest \
        @typescript-eslint/parser@latest \
        @typescript-eslint/eslint-plugin@latest \
        eslint-plugin-react@latest \
        eslint-plugin-react-hooks@latest \
        eslint-plugin-import@latest \
        eslint-plugin-vue@latest \
        eslint-plugin-svelte@latest; then
        log "ESLint packages installed successfully"
    else
        log_error "Failed to install ESLint packages"
        echo "Please install manually with:"
        echo "  npm install -g eslint @typescript-eslint/parser eslint-plugin-react eslint-plugin-vue eslint-plugin-import"
        exit 1
    fi
}

verify_eslint_plugins() {
    local required_plugins=(
        "@typescript-eslint/parser"
        "eslint-plugin-react"
        "eslint-plugin-import"
        "eslint-plugin-vue"
    )

    for plugin in "${required_plugins[@]}"; do
        # Try to check if plugin is available (this is a best-effort check)
        if ! npm list "$plugin" &> /dev/null && ! npm list -g "$plugin" &> /dev/null; then
            log_verbose "Plugin $plugin may not be available, but continuing..."
        fi
    done

    log_verbose "ESLint plugin verification completed"
}

# Directory setup with custom paths
setup_install_dir() {
    log_verbose "Setting up installation directory..."

    # Resolve and validate target path
    if [[ "$TARGET_PATH" == "~" ]]; then
        TARGET_PATH="$HOME"
    elif [[ "$TARGET_PATH" == ~* ]]; then
        TARGET_PATH="${TARGET_PATH/#\~/$HOME}"
    fi

    # Convert to absolute path
    TARGET_PATH=$(realpath "$TARGET_PATH" 2>/dev/null || echo "$TARGET_PATH")

    # Create target directory if it doesn't exist
    if [[ ! -d "$TARGET_PATH" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log "Would create directory: $TARGET_PATH"
        else
            log_verbose "Creating target directory: $TARGET_PATH"
            mkdir -p "$TARGET_PATH"
        fi
    fi

    # Set final installation path
    # Check if TARGET_PATH already ends with .claude
    if [[ "$TARGET_PATH" == */.claude ]]; then
        # User already specified .claude in the path
        INSTALL_DIR="$TARGET_PATH"
        log_verbose "Target path already ends with .claude, using it directly"
    else
        # Append .claude to the path
        INSTALL_DIR="$TARGET_PATH/.claude"
        log_verbose "Appending .claude to target path"
    fi

    log "Installation target: $INSTALL_DIR"

    # Handle existing installation
    if [[ -d "$INSTALL_DIR" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log "Would handle existing .claude directory at: $INSTALL_DIR"
            log "Would create automatic backup before proceeding"
            log "Would prompt user for fresh install/merge/workflows-only/cancel choice"
        else
            # Always create a backup first
            local backup_dir="${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
            log "Creating automatic backup of existing installation to: $backup_dir"
            cp -r "$INSTALL_DIR" "$backup_dir"

            echo ""
            echo "Found existing .claude directory at: $INSTALL_DIR"
            echo "Automatic backup created at: $backup_dir"
            echo ""
            echo "Choose an option:"
            echo "  1) Fresh install (replace existing)"
            echo "  2) Merge with existing (preserve user customizations)"
            echo "  3) Update workflows only (overwrite commands & scripts, preserve everything else)"
            echo "  4) Cancel installation (backup remains)"
            echo ""
            read -p "Enter choice [1-4]: " choice

            case $choice in
                1)
                    log "Proceeding with fresh installation"
                    rm -rf "$INSTALL_DIR"
                    ;;
                2)
                    log "Merging with existing installation"
                    MERGE_MODE=true
                    ;;
                3)
                    log "Updating workflows only (commands & scripts)"
                    UPDATE_WORKFLOWS_ONLY=true
                    ;;
                4)
                    log "Installation cancelled by user"
                    echo "Your backup is preserved at: $backup_dir"
                    exit 0
                    ;;
                *)
                    log_error "Invalid choice"
                    echo "Your backup is preserved at: $backup_dir"
                    exit 1
                    ;;
            esac
        fi
    fi

    # Create installation directory
    if [[ "$DRY_RUN" == "true" ]]; then
        log "Would create installation directory: $INSTALL_DIR"
    else
        mkdir -p "$INSTALL_DIR"
    fi
}

# Handle global rules merging or copying
handle_global_rules() {
    local source_dir="$1"
    local source_rules_md="$source_dir/rules/global.claude.rules.md"
    local target_claude_md="$INSTALL_DIR/claude.md"

    # Check if our source global.claude.rules.md exists
    if [[ ! -f "$source_rules_md" ]]; then
        log_error "Global rules file not found: $source_rules_md"
        exit 1
    fi

    if [[ -f "$target_claude_md" ]]; then
        # Target claude.md exists, append our content as a new section
        log_verbose "Existing claude.md found, appending Claude Code Workflows section..."

        # Check if our section already exists (search for our header comment)
        if grep -q "# Claude Code Workflows v" "$target_claude_md" 2>/dev/null; then
            log_verbose "Claude Code Workflows section already exists, skipping merge"
            return 0
        fi

        # Append our content as a new section with header
        {
            echo ""
            echo "---"
            echo ""
            echo "# Claude Code Workflows v$SCRIPT_VERSION - Auto-generated, do not edit"
            echo ""
            cat "$source_rules_md"
        } >> "$target_claude_md"

        log "Appended Claude Code Workflows section to existing claude.md"
    else
        # No existing claude.md, copy ours with header
        log_verbose "No existing claude.md found, creating new one with global rules..."
        {
            echo "# Claude Code Workflows v$SCRIPT_VERSION - Auto-generated, do not edit"
            echo ""
            cat "$source_rules_md"
        } > "$target_claude_md"
        log "Created claude.md with global rules in installation directory"
    fi
}

# File copy operations
copy_files() {
    log_verbose "Copying workflow files..."

    local source_dir="$SCRIPT_DIR"

    # Verify source files exist
    # Check if we have the expected subdirectories
    local shared_dir="$(dirname "$source_dir")/shared"
    if [[ ! -d "$source_dir/commands" ]] || [[ ! -d "$shared_dir" ]]; then
        log_error "Source files not found"
        log_error "Expected to find: $source_dir/commands/ and $shared_dir"
        exit 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "Would copy files from $source_dir to $INSTALL_DIR"
        return 0
    fi

    # Copy workflow files
    log_verbose "Copying workflow files..."
    if [[ "${MERGE_MODE:-false}" == "true" ]]; then
        # Merge mode: preserve existing files, copy new ones
        log "Merge mode: preserving existing files while adding new ones..."

        # Track what's being preserved vs added
        local preserved_count=0
        local added_count=0
        local custom_commands=()

        # Check for custom commands
        if [[ -d "$INSTALL_DIR/commands" ]]; then
            for cmd in "$INSTALL_DIR/commands"/*; do
                if [[ -f "$cmd" ]]; then
                    local cmd_name=$(basename "$cmd")
                    if ! [[ -f "$source_dir/commands/$cmd_name" ]]; then
                        custom_commands+=("$cmd_name")
                    fi
                fi
            done
        fi

        # Copy with no-clobber, excluding docs directory
        find "$source_dir" -mindepth 1 -maxdepth 1 -not -name "docs" -not -name "install.sh" -not -name "install.ps1" -exec cp -rn {} "$INSTALL_DIR/" \; 2>/dev/null || true

        # Copy scripts from shared/ subdirectories if they don't exist
        local shared_dir="$(dirname "$source_dir")/shared"
        if [[ ! -d "$INSTALL_DIR/scripts" ]]; then
            mkdir -p "$INSTALL_DIR/scripts"
            for subdir in analyzers generators setup utils tests ci core; do
                if [[ -d "$shared_dir/$subdir" ]]; then
                    cp -r "$shared_dir/$subdir" "$INSTALL_DIR/scripts/$subdir"
                fi
            done
        fi

        # Report custom commands preserved
        if [[ ${#custom_commands[@]} -gt 0 ]]; then
            echo "  Preserved custom commands:"
            for cmd in "${custom_commands[@]}"; do
                echo "    - $cmd"
            done
        fi

        echo "  Merge complete. Existing files preserved, new files added."
    elif [[ "${UPDATE_WORKFLOWS_ONLY:-false}" == "true" ]]; then
        # Update workflows only: update built-in commands, scripts, agents, templates, and rules, preserve custom commands and everything else
        log "Updating workflows only: built-in commands, scripts, agents, templates, and rules directories..."

        # Update built-in commands while preserving custom commands
        if [[ -d "$source_dir/commands" ]]; then
            log "  Updating commands directory (preserving custom commands)..."
            local custom_commands=()

            # Identify existing custom commands
            if [[ -d "$INSTALL_DIR/commands" ]]; then
                for cmd in "$INSTALL_DIR/commands"/*; do
                    if [[ -f "$cmd" ]]; then
                        local cmd_name=$(basename "$cmd")
                        if ! [[ -f "$source_dir/commands/$cmd_name" ]]; then
                            custom_commands+=("$cmd_name")
                        fi
                    fi
                done
            fi

            # Create commands directory if it doesn't exist
            mkdir -p "$INSTALL_DIR/commands"

            # Copy/overwrite built-in commands (this preserves any custom commands not in source)
            cp "$source_dir/commands"/* "$INSTALL_DIR/commands/"

            # Report preserved custom commands
            if [[ ${#custom_commands[@]} -gt 0 ]]; then
                echo "    Preserved custom commands:"
                for cmd in "${custom_commands[@]}"; do
                    echo "      - $cmd"
                done
            fi
        fi

        # Update scripts directory (preserve custom scripts)
        local shared_dir="$(dirname "$source_dir")/shared"
        if [[ -d "$shared_dir" ]]; then
            log "  Updating scripts directory (preserving custom scripts)..."

            # Backup custom scripts if they exist
            local custom_scripts=()
            if [[ -d "$INSTALL_DIR/scripts" ]]; then
                # Find custom scripts that aren't in our source
                while IFS= read -r -d '' script_file; do
                    local rel_path="${script_file#$INSTALL_DIR/scripts/}"
                    local found_in_source=false
                    for subdir in analyzers generators setup utils tests ci core; do
                        if [[ -f "$shared_dir/$subdir/${rel_path#*/}" ]] && [[ "$rel_path" == "$subdir/"* ]]; then
                            found_in_source=true
                            break
                        fi
                    done
                    if [[ "$found_in_source" == "false" ]]; then
                        custom_scripts+=("$rel_path")
                    fi
                done < <(find "$INSTALL_DIR/scripts" -type f -print0 2>/dev/null)

                # Create temp backup of custom scripts
                if [[ ${#custom_scripts[@]} -gt 0 ]]; then
                    local temp_backup=$(mktemp -d)
                    for script in "${custom_scripts[@]}"; do
                        local script_dir=$(dirname "$temp_backup/$script")
                        mkdir -p "$script_dir"
                        cp "$INSTALL_DIR/scripts/$script" "$temp_backup/$script"
                    done
                fi
            fi

            # Remove and recreate scripts directory
            rm -rf "$INSTALL_DIR/scripts"
            mkdir -p "$INSTALL_DIR/scripts"
            for subdir in analyzers generators setup utils tests ci core; do
                if [[ -d "$shared_dir/$subdir" ]]; then
                    cp -r "$shared_dir/$subdir" "$INSTALL_DIR/scripts/$subdir"
                fi
            done

            # Restore custom scripts
            if [[ ${#custom_scripts[@]} -gt 0 ]]; then
                echo "    Preserved custom scripts:"
                for script in "${custom_scripts[@]}"; do
                    local script_dir=$(dirname "$INSTALL_DIR/scripts/$script")
                    mkdir -p "$script_dir"
                    cp "$temp_backup/$script" "$INSTALL_DIR/scripts/$script"
                    echo "      - $script"
                done
                rm -rf "$temp_backup"
            fi
        fi

        # Update agents directory
        if [[ -d "$source_dir/agents" ]]; then
            log "  Updating agents directory..."
            rm -rf "$INSTALL_DIR/agents"
            cp -r "$source_dir/agents" "$INSTALL_DIR/"
        fi

        # Update templates directory
        if [[ -d "$source_dir/templates" ]]; then
            log "  Updating templates directory..."
            rm -rf "$INSTALL_DIR/templates"
            cp -r "$source_dir/templates" "$INSTALL_DIR/"
        fi

        # Update rules directory
        if [[ -d "$source_dir/rules" ]]; then
            log "  Updating rules directory..."
            rm -rf "$INSTALL_DIR/rules"
            cp -r "$source_dir/rules" "$INSTALL_DIR/"
        fi

        echo "  Workflow update complete. Built-in commands, scripts, agents, templates, and rules updated, custom commands and other files preserved."
    else
        # Fresh install: copy everything except docs and install scripts
        find "$source_dir" -mindepth 1 -maxdepth 1 -not -name "docs" -not -name "install.sh" -not -name "install.ps1" -exec cp -r {} "$INSTALL_DIR/" \;

        # Copy scripts from shared/ subdirectories
        local shared_dir="$(dirname "$source_dir")/shared"
        mkdir -p "$INSTALL_DIR/scripts"
        for subdir in analyzers generators setup utils tests ci core; do
            if [[ -d "$shared_dir/$subdir" ]]; then
                cp -r "$shared_dir/$subdir" "$INSTALL_DIR/scripts/$subdir"
            fi
        done
    fi

    # Copy CLAUDE.md if it exists in source directory
    if [[ -f "$source_dir/CLAUDE.md" ]]; then
        log_verbose "Copying CLAUDE.md..."
        cp "$source_dir/CLAUDE.md" "$INSTALL_DIR/"
    fi

    # Handle global rules merging or copying
    handle_global_rules "$source_dir"

    # Set proper permissions
    find "$INSTALL_DIR" -name "*.py" -exec chmod +x {} \;
    find "$INSTALL_DIR" -name "*.sh" -exec chmod +x {} \;

    log "Files copied successfully"
}

# Create installation log for uninstall tracking
create_installation_log() {
    log "Creating installation log for uninstall tracking..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "Would create installation log"
        return 0
    fi

    local log_file="$INSTALL_DIR/installation-log.txt"
    local requirements_file="$INSTALL_DIR/scripts/setup/requirements.txt"

    # Create log file with header
    cat > "$log_file" << EOF
# Claude Code Workflows Installation Log
# DO NOT DELETE - Used by uninstall script to determine safe removal
# Generated on: $(date)
# Installation directory: $INSTALL_DIR

[PRE_EXISTING_PYTHON_PACKAGES]
EOF

    # Check which Python packages were already installed
    if [[ -f "$requirements_file" ]]; then
        while IFS= read -r line; do
            # Skip empty lines and comments
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
            # Extract package name (everything before ==, >=, etc.)
            local pkg=$(echo "$line" | sed 's/[>=<].*//' | tr -d ' ')
            if [[ -n "$pkg" ]] && python3 -m pip show "$pkg" &>/dev/null; then
                echo "$pkg" >> "$log_file"
                log_verbose "Pre-existing Python package: $pkg"
            fi
        done < "$requirements_file"
    fi

    # Check which MCP servers were already installed
    cat >> "$log_file" << EOF

[PRE_EXISTING_MCP_SERVERS]
EOF

    if command -v claude &> /dev/null; then
        # Check our MCP servers
        local our_mcp_servers=("sequential-thinking" "grep")
        for server in "${our_mcp_servers[@]}"; do
            if claude mcp list 2>/dev/null | grep -q "^$server"; then
                echo "$server" >> "$log_file"
                log_verbose "Pre-existing MCP server: $server"
            fi
        done
    fi

    # Initialize sections for newly installed items
    cat >> "$log_file" << EOF

[NEWLY_INSTALLED_PYTHON_PACKAGES]

[NEWLY_INSTALLED_MCP_SERVERS]
EOF

    log_verbose "Installation log created: installation-log.txt"
}

# Update installation log with newly installed items
update_installation_log() {
    local item_type="$1"
    local item_name="$2"

    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    local log_file="$INSTALL_DIR/installation-log.txt"

    if [[ ! -f "$log_file" ]]; then
        return 0
    fi

    # Add item to appropriate section
    if [[ "$item_type" == "python" ]]; then
        echo "$item_name" >> "$log_file"
    elif [[ "$item_type" == "mcp" ]]; then
        # Find the line number of the section and insert after it
        local line_num=$(grep -n "^\[NEWLY_INSTALLED_MCP_SERVERS\]" "$log_file" | cut -d: -f1)
        if [[ -n "$line_num" ]]; then
            sed -i '' "${line_num}a\\
$item_name" "$log_file"
        fi
    fi

    log_verbose "Added to installation log: $item_type - $item_name"
}

# Python dependency installation
install_python_deps() {
    if [[ "$SKIP_PYTHON" == "true" ]]; then
        log "Skipping Python dependencies installation"
        return 0
    fi

    log "Installing Python dependencies..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "Would run Python dependency installation"
        return 0
    fi

    local setup_script="$INSTALL_DIR/scripts/setup/install_dependencies.py"

    if [[ ! -f "$setup_script" ]]; then
        log_error "Setup script not found: $setup_script"
        exit 1
    fi

    # Get list of packages that will be installed
    local requirements_file="$INSTALL_DIR/scripts/setup/requirements.txt"
    local packages_to_check=()

    if [[ -f "$requirements_file" ]]; then
        while IFS= read -r line; do
            # Skip empty lines and comments
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
            # Extract package name (everything before ==, >=, etc.)
            local pkg=$(echo "$line" | sed 's/[>=<].*//' | tr -d ' ')
            [[ -n "$pkg" ]] && packages_to_check+=("$pkg")
        done < "$requirements_file"
    fi

    log_verbose "Running installation script..."
    cd "$INSTALL_DIR"

    # Run Python dependency installation with automatic 'yes' response
    if echo "y" | python3 "$setup_script"; then
        log "Python dependencies installed successfully"

        # Check which packages are now installed and update log for newly installed ones
        for pkg in "${packages_to_check[@]}"; do
            if python3 -m pip show "$pkg" &>/dev/null; then
                # Check if this package was pre-existing by reading the installation log
                local log_file="$INSTALL_DIR/installation-log.txt"
                if [[ -f "$log_file" ]]; then
                    # Check if package is NOT in the pre-existing list
                    if ! grep -A 100 "^\[PRE_EXISTING_PYTHON_PACKAGES\]" "$log_file" | grep -q "^$pkg$"; then
                        update_installation_log "python" "$pkg"
                    fi
                else
                    # No log file, assume it's newly installed
                    update_installation_log "python" "$pkg"
                fi
            fi
        done
    else
        log_error "Python dependencies installation failed"
        exit 1
    fi
}

# MCP tools installation
install_mcp_tools() {
    if [[ "$SKIP_MCP" == "true" ]]; then
        log "Skipping MCP tools installation"
        return 0
    fi

    log "Installing MCP tools..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "Would install MCP tools: sequential-thinking, grep"
        return 0
    fi

    local mcp_failed=false

    # Install sequential-thinking
    log_verbose "Installing sequential-thinking MCP tool..."
    # First check if already installed (with a small delay to ensure claude mcp list is ready)
    sleep 1
    if claude mcp list 2>&1 | grep -q "^sequential-thinking:"; then
        log_verbose "sequential-thinking already installed, skipping"
        update_installation_log "mcp" "sequential-thinking"
    else
        # Try to install, capturing the actual error
        local install_output
        install_output=$(claude mcp add sequential-thinking -s user -- npx -y @modelcontextprotocol/server-sequential-thinking 2>&1)
        local install_status=$?

        if [[ $install_status -eq 0 ]]; then
            log_verbose "sequential-thinking installed successfully"
            update_installation_log "mcp" "sequential-thinking"
        elif echo "$install_output" | grep -q "already exists"; then
            log_verbose "sequential-thinking already exists (detected during install), marking as successful"
            update_installation_log "mcp" "sequential-thinking"
        else
            log_error "Failed to install sequential-thinking MCP tool: $install_output"
            mcp_failed=true
        fi
    fi

    # Install grep
    log_verbose "Installing grep MCP tool..."
    # Check if already installed
    if claude mcp list 2>&1 | grep -q "^grep:"; then
        log_verbose "grep already installed, skipping"
        update_installation_log "mcp" "grep"
    else
        # Try to install, capturing the actual error
        local install_output
        install_output=$(claude mcp add --transport http grep https://mcp.grep.app 2>&1)
        local install_status=$?

        if [[ $install_status -eq 0 ]]; then
            log_verbose "grep installed successfully"
            update_installation_log "mcp" "grep"
        elif echo "$install_output" | grep -q "already exists"; then
            log_verbose "grep already exists (detected during install), marking as successful"
            update_installation_log "mcp" "grep"
        else
            log_error "Failed to install grep MCP tool: $install_output"
            mcp_failed=true
        fi
    fi

    if [[ "$mcp_failed" == "true" ]]; then
        log "Some MCP tools failed to install. You can install them manually later using:"
        echo "  claude mcp add sequential-thinking -s user -- npx -y @modelcontextprotocol/server-sequential-thinking"
        echo "  claude mcp add --transport http grep https://mcp.grep.app"
    else
        log "MCP tools installed successfully"
    fi
}

# Installation verification
verify_installation() {
    log "Verifying installation..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "Would verify installation"
        return 0
    fi

    if [[ "$DRY_RUN" != "true" ]]; then
        local test_script="$INSTALL_DIR/scripts/setup/test_install.py"

        # Test Python dependencies
        if [[ "$SKIP_PYTHON" != "true" ]] && [[ -f "$test_script" ]]; then
            log_verbose "Testing Python dependencies..."
            cd "$INSTALL_DIR"
            if python3 "$test_script" >> "$LOG_FILE" 2>&1; then
                log_verbose "Python dependencies verification passed"
            else
                log_error "Python dependencies verification failed"
                exit 1
            fi
        fi
    fi

    # Test MCP tools
    if [[ "$DRY_RUN" != "true" ]] && [[ "$SKIP_MCP" != "true" ]]; then
        log_verbose "Testing MCP tools..."
        if claude mcp list 2>/dev/null | grep -q "sequential-thinking"; then
            log_verbose "MCP tools verification passed"
        else
            log "Warning: MCP tools verification failed (this is non-critical)"
        fi
    fi

    # Test file structure
    if [[ "$DRY_RUN" != "true" ]]; then
        local required_dirs=("commands" "scripts" "rules" "templates")
        for dir in "${required_dirs[@]}"; do
            if [[ ! -d "$INSTALL_DIR/$dir" ]]; then
                log_error "Required directory missing: $INSTALL_DIR/$dir"
                exit 1
            fi
        done


        # Verify custom commands preservation if in merge mode
        if [[ "${MERGE_MODE:-false}" == "true" ]]; then
            log_verbose "Verifying custom commands preservation..."
            local custom_commands_found=0

            if [[ -d "$INSTALL_DIR/commands" ]]; then
                for cmd in "$INSTALL_DIR/commands"/*; do
                    if [[ -f "$cmd" ]]; then
                        local cmd_name=$(basename "$cmd")
                        # Check if this is a custom command (not in source)
                        if ! [[ -f "$SCRIPT_DIR/commands/$cmd_name" ]]; then
                            log_verbose "  Custom command preserved: $cmd_name"
                            ((custom_commands_found++))
                        fi
                    fi
                done
            fi

            if [[ $custom_commands_found -gt 0 ]]; then
                log "Verified: $custom_commands_found custom command(s) preserved"
            fi
        fi
    fi

    log "Installation verification completed successfully"
}

# Display post-installation information
show_completion() {
    echo ""
    echo "🎉 Claude Code Workflows installation completed successfully!"
    echo ""
    echo "Installation location: $INSTALL_DIR"
    echo ""
    echo "Available commands (12 total):"
    echo "  Analysis: analyze-security, analyze-architecture, analyze-performance, etc."
    echo "  Planning: plan-solution, plan-ux-prd, plan-refactor"
    echo "  Fixing:  fix-bug, fix-performance, fix-test"
    echo "  Build Flags: --prototype, --tdd (via claude.md)"
    echo ""
    echo "Usage examples:"
    echo "  /analyze-security   (run security analysis)"
    echo "  /plan-solution     (solve technical challenges)"
    echo "  /fix-bug --tdd     (test-driven bug fixing)"
    echo ""

    if [[ "$SKIP_MCP" != "true" ]]; then
        echo "MCP Tools available:"
        echo "  --seq (sequential thinking for complex analysis)"
        echo "  --gitgrep (grep for GitHub repository search)"
        echo ""
    fi

    echo "For more information:"
    echo "  View commands: ls $INSTALL_DIR/commands/"
    echo "  Documentation: cat $INSTALL_DIR/CLAUDE.md"
    echo "  Log file: $LOG_FILE"
    echo ""
}

# Error handling and cleanup
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Installation failed with exit code $exit_code"
        echo ""
        echo "Installation failed. Check the log file for details: $LOG_FILE"
        echo ""
        echo "Common solutions:"
        echo "  1. Ensure Python 3.7+ is installed"
        echo "  2. Check internet connectivity"
        echo "  3. Run with --skip-mcp if MCP tools are causing issues"
        echo "  4. Run with --skip-python if Python deps are causing issues"
        echo ""
    fi
}

# Main installation function
main() {
    parse_args "$@"

    # Set up error handling
    trap cleanup EXIT

    # Initialize log file
    echo "Claude Code Workflows Installation Log" > "$LOG_FILE"
    echo "Started: $(date)" >> "$LOG_FILE"
    echo "Arguments: $*" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"

    log "Starting Claude Code Workflows installation (v$SCRIPT_VERSION)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN MODE - no changes will be made"
    fi

    # Run installation steps
    detect_platform
    check_python
    check_node
    check_claude_cli
    check_security_tools
    setup_install_dir
    copy_files
    create_installation_log
    install_python_deps
    check_eslint
    install_mcp_tools
    verify_installation

    if [[ "$DRY_RUN" != "true" ]]; then
        show_completion
    else
        log "Dry run completed - no changes were made"
    fi
}

# Run main function with all arguments
main "$@"
