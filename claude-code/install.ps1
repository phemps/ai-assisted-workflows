# AI-Assisted Workflows Installation Script for Windows
# Installs the complete workflow system with commands, scripts, and dependencies

param(
    [Parameter(Position=0)]
    [string]$TargetPath = "",

    [Parameter()]
    [ValidateSet("Fresh", "Merge", "UpdateWorkflows", "Interactive")]
    [string]$InstallMode = "Interactive",

    [switch]$Help,
    [switch]$DryRun,
    [switch]$SkipMcp,
    [switch]$SkipPython
)

# Script configuration
$VERSION = "1.0.0"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$LOG_FILE = "$env:TEMP\ai-workflows-install.log"

# Colors for output
$Colors = @{
    Green = [System.ConsoleColor]::Green
    Yellow = [System.ConsoleColor]::Yellow
    Red = [System.ConsoleColor]::Red
    Blue = [System.ConsoleColor]::Blue
    White = [System.ConsoleColor]::White
    Cyan = [System.ConsoleColor]::Cyan
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [System.ConsoleColor]$Color = [System.ConsoleColor]::White
    )
    $originalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Output $Message
    $Host.UI.RawUI.ForegroundColor = $originalColor
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LOG_FILE -Value $logEntry

    if ($VerbosePreference -eq 'Continue') {
        Write-ColorOutput "$logEntry" -Color $Colors.Cyan
    }
}

function Show-Usage {
    Write-ColorOutput "AI-Assisted Workflows Installer v$VERSION" -Color $Colors.Green
    Write-Output ""
    Write-Output "USAGE:"
    Write-Output "    .\install.ps1 [TARGET_PATH] [OPTIONS]"
    Write-Output ""
    Write-Output "ARGUMENTS:"
    Write-Output "    TARGET_PATH     Directory where .claude\ will be created"
    Write-Output "                   Examples:"
    Write-Output "                     ~\                    (User global: ~\.claude\)"
    Write-Output "                     .\myproject           (Project local: .\myproject\.claude\)"
    Write-Output "                     C:\path\to\project    (Custom path: C:\path\to\project\.claude\)"
    Write-Output "                   Default: current directory"
    Write-Output ""
    Write-Output "OPTIONS:"
    Write-Output "    -Help           Show this help message"
    Write-Output "    -Verbose        Enable verbose output (PowerShell built-in parameter)"
    Write-Output "    -DryRun         Show what would be done without making changes"
    Write-Output "    -SkipMcp        Skip MCP tools installation"
    Write-Output "    -SkipPython     Skip Python dependencies installation"
    Write-Output ""
    Write-Output "EXAMPLES:"
    Write-Output "    # Install in current project (creates .\.claude\)"
    Write-Output "    .\install.ps1"
    Write-Output ""
    Write-Output "    # Install globally for user (creates ~\.claude\)"
    Write-Output "    .\install.ps1 ~"
    Write-Output ""
    Write-Output "    # Install in specific project"
    Write-Output "    .\install.ps1 C:\path\to\my-project"
    Write-Output ""
    Write-Output "    # Dry run to see what would happen"
    Write-Output "    .\install.ps1 -DryRun"
    Write-Output ""
    Write-Output "    # Install without MCP tools"
    Write-Output "    .\install.ps1 -SkipMcp"
    Write-Output ""
    Write-Output "REQUIREMENTS:"
    Write-Output "    - Python 3.7+"
    Write-Output "    - Node.js (for MCP tools)"
    Write-Output "    - Claude CLI (for MCP tools)"
    Write-Output "    - Internet connection for dependencies"
}

function Test-Prerequisites {
    Write-Output ""
    Write-ColorOutput "Checking prerequisites..." -Color $Colors.Yellow
    Write-Log "Starting prerequisite checks"

    $errors = 0

    # Check Python
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)"
            if ($versionMatch -and $matches.Count -ge 3) {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]
                if (($major -eq 3 -and $minor -ge 7) -or $major -gt 3) {
                    Write-ColorOutput "[OK] $pythonVersion found" -Color $Colors.Green
                    Write-Log "Python check passed: $pythonVersion"
                } else {
                    Write-ColorOutput "[ERROR] $pythonVersion found, but Python 3.7+ required" -Color $Colors.Red
                    Write-Output "  Install: https://www.python.org/downloads/"
                    Write-Log "Python version too old: $pythonVersion" -Level "ERROR"
                    $errors++
                }
            } else {
                Write-ColorOutput "[ERROR] Could not parse Python version: $pythonVersion" -Color $Colors.Red
                Write-Log "Could not parse Python version: $pythonVersion" -Level "ERROR"
                $errors++
            }
        } else {
            throw "Python not found"
        }
    } catch {
        Write-ColorOutput "[ERROR] Python not found or not accessible" -Color $Colors.Red
        Write-Output "  Install: https://www.python.org/downloads/"
        Write-Output "  Make sure Python is in your PATH"
        Write-Log "Python not found: $($_.Exception.Message)" -Level "ERROR"
        $errors++
    }

    # Check pip
    try {
        $pipVersion = & pip --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[OK] pip found" -Color $Colors.Green
            Write-Log "pip check passed: $pipVersion"
        } else {
            throw "pip not found"
        }
    } catch {
        Write-ColorOutput "[ERROR] pip not found" -Color $Colors.Red
        Write-Output "  pip should be included with Python 3.7+"
        Write-Output "  If missing, install with: python -m ensurepip --upgrade"
        Write-Log "pip not found: $($_.Exception.Message)" -Level "ERROR"
        $errors++
    }

    # Check Node.js (only if MCP tools not skipped)
    if (-not $SkipMcp) {
        try {
            $nodeVersion = & node --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $versionNumber = $nodeVersion -replace '^v', ''
                $major = [int]($versionNumber.Split('.')[0])
                if ($major -ge 14) {
                    Write-ColorOutput "[OK] Node.js $nodeVersion found" -Color $Colors.Green
                    Write-Log "Node.js check passed: $nodeVersion"
                } else {
                    Write-ColorOutput "[ERROR] Node.js $nodeVersion found, but 14+ required for MCP tools" -Color $Colors.Red
                    Write-Output "  Install: https://nodejs.org/"
                    Write-Output "  Or use -SkipMcp to skip MCP tools installation"
                    Write-Log "Node.js version too old: $nodeVersion" -Level "ERROR"
                    $errors++
                }
            } else {
                throw "Node.js not found"
            }
        } catch {
            Write-ColorOutput "[WARNING] Node.js not found - MCP tools will be skipped" -Color $Colors.Yellow
            Write-Output "  To enable MCP tools, install Node.js: https://nodejs.org/"
            Write-Log "Node.js not found, will skip MCP tools: $($_.Exception.Message)" -Level "WARNING"
            $SkipMcp = $true
        }

        # Check Claude CLI (only if MCP tools not skipped)
        if (-not $SkipMcp) {
            try {
                $claudeVersion = & claude --version 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput "[OK] Claude CLI found" -Color $Colors.Green
                    Write-Log "Claude CLI check passed: $claudeVersion"
                } else {
                    throw "Claude CLI not found"
                }
            } catch {
                Write-ColorOutput "[WARNING] Claude CLI not found - MCP tools will be skipped" -Color $Colors.Yellow
                Write-Output "  To enable MCP tools, install Claude CLI"
                Write-Output "  Or use -SkipMcp to skip MCP tools installation"
                Write-Log "Claude CLI not found, will skip MCP tools: $($_.Exception.Message)" -Level "WARNING"
                $SkipMcp = $true
            }
        }
    } else {
        Write-ColorOutput "[INFO] MCP tools installation skipped" -Color $Colors.Yellow
        Write-Log "MCP tools installation skipped by user"
    }

    if ($errors -gt 0) {
        Write-Output ""
        Write-ColorOutput "[ERROR] Installation blocked: $errors prerequisite(s) missing" -Color $Colors.Red
        Write-Output ""
        Write-Output "Please install missing prerequisites and run again."
        Write-Log "Installation blocked due to $errors missing prerequisites" -Level "ERROR"
        exit 1
    }

    Write-Output ""
    Write-ColorOutput "[OK] All prerequisites satisfied" -Color $Colors.Green
    Write-Log "All prerequisites satisfied"
}

function Resolve-TargetPath {
    param([string]$Path)

    if ([string]::IsNullOrEmpty($Path)) {
        $resolvedPath = Get-Location
    } elseif ($Path -eq "~") {
        $resolvedPath = $env:USERPROFILE
    } else {
        # Convert to absolute path if relative
        if (-not [System.IO.Path]::IsPathRooted($Path)) {
            $resolvedPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
        } else {
            $resolvedPath = $Path
        }
    }

    return $resolvedPath
}

function Test-WritePermissions {
    param([string]$Path)

    try {
        $testFile = Join-Path $Path "test_write_permissions.tmp"
        New-Item -ItemType File -Path $testFile -Force | Out-Null
        Remove-Item -Path $testFile -Force
        return $true
    } catch {
        return $false
    }
}

function Handle-ExistingInstallation {
    param([string]$ClaudePath)

    if (Test-Path $ClaudePath) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "$ClaudePath.backup.$timestamp"

        Write-ColorOutput "Existing .claude directory found" -Color $Colors.Yellow

        if ($DryRun) {
            Write-ColorOutput "[DRY RUN] Would backup existing installation to: $backupPath" -Color $Colors.Blue
            Write-ColorOutput "[DRY RUN] Would prompt for installation mode selection" -Color $Colors.Blue
            return @{ BackupPath = $backupPath; Mode = "fresh" }
        }

        # Always create backup first
        Write-Output "Creating automatic backup of existing installation..."
        Copy-Item -Path $ClaudePath -Destination $backupPath -Recurse -Force
        Write-ColorOutput "Backup created: $backupPath" -Color $Colors.Green
        Write-Log "Created backup: $backupPath"

        # Determine installation mode
        if ($InstallMode -eq "Interactive") {
            # Prompt for installation mode
            Write-Output ""
            Write-Output "Found existing .claude directory at: $ClaudePath"
            Write-Output "Automatic backup created at: $backupPath"
            Write-Output ""
            Write-Output "Choose an option:"
            Write-Output "  1) Fresh install (replace existing)"
            Write-Output "  2) Merge with existing (preserve user customizations)"
            Write-Output "  3) Update workflows only (overwrite commands & scripts, preserve everything else)"
            Write-Output "  4) Cancel installation (backup remains)"
            Write-Output ""

            do {
                $choice = Read-Host "Enter choice [1-4]"
            } while ($choice -notin @("1", "2", "3", "4"))
        } else {
            # Non-interactive mode: use InstallMode parameter
            Write-Output ""
            Write-Output "Found existing .claude directory at: $ClaudePath"
            Write-Output "Automatic backup created at: $backupPath"
            Write-Output "Non-interactive mode: $InstallMode"
            Write-Output ""
            switch ($InstallMode) {
                "Fresh" { $choice = "1" }
                "Merge" { $choice = "2" }
                "UpdateWorkflows" { $choice = "3" }
                default { $choice = "1" }
            }
        }

        switch ($choice) {
            "1" {
                Write-ColorOutput "Proceeding with fresh installation" -Color $Colors.Green
                Write-Log "Fresh installation mode selected"
                Remove-Item -Path $ClaudePath -Recurse -Force
                return @{ BackupPath = $backupPath; Mode = "fresh" }
            }
            "2" {
                Write-ColorOutput "Merging with existing installation" -Color $Colors.Green
                Write-Log "Merge mode selected"
                return @{ BackupPath = $backupPath; Mode = "merge" }
            }
            "3" {
                Write-ColorOutput "Updating workflows only (commands & scripts)" -Color $Colors.Green
                Write-Log "Update workflows only mode selected"
                return @{ BackupPath = $backupPath; Mode = "update-workflows" }
            }
            "4" {
                Write-ColorOutput "Installation cancelled by user" -Color $Colors.Yellow
                Write-Output "Your backup is preserved at: $backupPath"
                Write-Log "Installation cancelled by user"
                exit 0
            }
        }
    }

    return @{ BackupPath = $null; Mode = "fresh" }
}

function Install-PythonDependencies {
    if ($SkipPython) {
        Write-ColorOutput "[INFO] Python dependencies installation skipped" -Color $Colors.Yellow
        Write-Log "Python dependencies installation skipped by user"
        return
    }

    Write-Output ""
    Write-ColorOutput "Installing Python dependencies..." -Color $Colors.Yellow
    Write-Log "Starting Python dependencies installation"

    # Scripts are now in shared/ subdirectories
    $sharedDir = Join-Path (Split-Path $SCRIPT_DIR -Parent) "shared"
    $setupDir = Join-Path $sharedDir "setup"
    $requirementsPath = Join-Path $setupDir "requirements.txt"

    if (-not (Test-Path $requirementsPath)) {
        Write-ColorOutput "[ERROR] Requirements file not found: $requirementsPath" -Color $Colors.Red
        Write-Log "Requirements file not found: $requirementsPath" -Level "ERROR"
        exit 1
    }

    if ($DryRun) {
        Write-ColorOutput "[DRY RUN] Would install Python dependencies from: $requirementsPath" -Color $Colors.Blue
        return
    }

    try {
        Write-Output "Installing packages from requirements.txt..."
        & pip install -r $requirementsPath --user

        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[OK] Python dependencies installed successfully" -Color $Colors.Green
            Write-Log "Python dependencies installed successfully"
        } else {
            Write-ColorOutput "[ERROR] Failed to install Python dependencies" -Color $Colors.Red
            Write-Log "Failed to install Python dependencies, exit code: $LASTEXITCODE" -Level "ERROR"
            exit 1
        }
    } catch {
        Write-ColorOutput "[ERROR] Error installing Python dependencies: $($_.Exception.Message)" -Color $Colors.Red
        Write-Log "Error installing Python dependencies: $($_.Exception.Message)" -Level "ERROR"
        exit 1
    }
}

function Install-McpTools {
    param([string]$ClaudePath)

    if ($SkipMcp) {
        Write-ColorOutput "[INFO] MCP tools installation skipped" -Color $Colors.Yellow
        Write-Log "MCP tools installation skipped"
        return
    }

    Write-Output ""
    Write-ColorOutput "Installing MCP tools..." -Color $Colors.Yellow
    Write-Log "Starting MCP tools installation"

    if ($DryRun) {
        Write-ColorOutput "[DRY RUN] Would install MCP tools via Claude CLI" -Color $Colors.Blue
        return
    }

    try {
        # Install sequential-thinking MCP server
        Write-Output "Installing sequential-thinking MCP server..."
        Start-Sleep -Seconds 1  # Small delay to ensure claude mcp list is ready
        $mcpListOutput = & claude mcp list 2>&1
        if ($mcpListOutput -match "^sequential-thinking:") {
            Write-ColorOutput "[INFO] sequential-thinking already installed, skipping" -Color $Colors.Yellow
            Write-Log "sequential-thinking already installed, skipping"
        } else {
            # Try to install, capturing the actual output
            $installOutput = & claude mcp add sequential-thinking -s user -- npx -y "@modelcontextprotocol/server-sequential-thinking" 2>&1
            $installExitCode = $LASTEXITCODE

            if ($installExitCode -eq 0) {
                Write-ColorOutput "[OK] sequential-thinking MCP server installed" -Color $Colors.Green
                Write-Log "sequential-thinking MCP server installed successfully"
            } elseif ($installOutput -match "already exists") {
                Write-ColorOutput "[INFO] sequential-thinking already exists, marking as successful" -Color $Colors.Yellow
                Write-Log "sequential-thinking already exists (detected during install)"
            } else {
                Write-ColorOutput "[WARNING] Failed to install sequential-thinking MCP server: $installOutput" -Color $Colors.Yellow
                Write-Log "Failed to install sequential-thinking MCP server: $installOutput" -Level "WARNING"
            }
        }

        # Install grep MCP server
        Write-Output "Installing grep MCP server..."
        $mcpListOutput = & claude mcp list 2>&1
        if ($mcpListOutput -match "^grep:") {
            Write-ColorOutput "[INFO] grep already installed, skipping" -Color $Colors.Yellow
            Write-Log "grep already installed, skipping"
        } else {
            # Try to install, capturing the actual output
            $installOutput = & claude mcp add --transport http grep https://mcp.grep.app 2>&1
            $installExitCode = $LASTEXITCODE

            if ($installExitCode -eq 0) {
                Write-ColorOutput "[OK] grep MCP server installed" -Color $Colors.Green
                Write-Log "grep MCP server installed successfully"
            } elseif ($installOutput -match "already exists") {
                Write-ColorOutput "[INFO] grep already exists, marking as successful" -Color $Colors.Yellow
                Write-Log "grep already exists (detected during install)"
            } else {
                Write-ColorOutput "[WARNING] Failed to install grep MCP server: $installOutput" -Color $Colors.Yellow
                Write-Log "Failed to install grep MCP server: $installOutput" -Level "WARNING"
            }
        }

    } catch {
        Write-ColorOutput "[WARNING] Error installing MCP tools: $($_.Exception.Message)" -Color $Colors.Yellow
        Write-Log "Error installing MCP tools: $($_.Exception.Message)" -Level "WARNING"
    }
}

function Copy-WorkflowFiles {
    param(
        [string]$ClaudePath,
        [string]$InstallMode = "fresh"
    )

    Write-Log "Starting workflow files copy in mode: $InstallMode"

    # Source directory is the script directory itself
    $sourceClaudeDir = $SCRIPT_DIR

    if (-not (Test-Path $sourceClaudeDir)) {
        Write-ColorOutput "[ERROR] Source claude directory not found: $sourceClaudeDir" -Color $Colors.Red
        Write-Log "Source claude directory not found: $sourceClaudeDir" -Level "ERROR"
        exit 1
    }

    if ($DryRun) {
        Write-ColorOutput "[DRY RUN] Would copy workflow files from: $sourceClaudeDir" -Color $Colors.Blue
        Write-ColorOutput "[DRY RUN] Would copy to: $ClaudePath" -Color $Colors.Blue
        Write-ColorOutput "[DRY RUN] Install mode: $InstallMode" -Color $Colors.Blue
        return
    }

    try {
        # Create target directory
        if (-not (Test-Path $ClaudePath)) {
            New-Item -ItemType Directory -Path $ClaudePath -Force | Out-Null
        }

        switch ($InstallMode) {
            "fresh" {
                # Fresh install: copy everything except docs and install scripts
                Write-ColorOutput "Fresh install mode: copying all files" -Color $Colors.Green

                Invoke-WithSpinner -Message "Copying workflow files" -ScriptBlock {
                    $items = Get-ChildItem $sourceClaudeDir -Recurse | Where-Object {
                        $relativePath = [System.IO.Path]::GetRelativePath($sourceClaudeDir, $_.FullName)
                        -not ($relativePath -like "docs\*" -or $relativePath -eq "docs" -or $relativePath -eq "install.sh" -or $relativePath -eq "install.ps1")
                    }
                    foreach ($item in $items) {
                        $relativePath = [System.IO.Path]::GetRelativePath($sourceClaudeDir, $item.FullName)
                        $targetPath = Join-Path $ClaudePath $relativePath
                        $targetDir = Split-Path $targetPath -Parent

                        if (-not (Test-Path $targetDir)) {
                            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                        }

                        if ($item.PSIsContainer) {
                            if (-not (Test-Path $targetPath)) {
                                New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
                            }
                        } else {
                            Copy-Item -Path $item.FullName -Destination $targetPath -Force
                        }
                    }
                }

                # Copy scripts from shared/ subdirectories
                Invoke-WithSpinner -Message "Copying shared scripts" -ScriptBlock {
                    Copy-SharedScripts -ClaudePath $ClaudePath
                }
            }
            "merge" {
                # Merge mode: preserve existing files, copy new ones
                Write-ColorOutput "Merge mode: preserving existing files while adding new ones" -Color $Colors.Green

                # Track custom commands
                $customCommands = @()
                $commandsPath = Join-Path $ClaudePath "commands"

                if (Test-Path $commandsPath) {
                    foreach ($cmd in Get-ChildItem $commandsPath -Filter "*.md") {
                        $sourceCmd = Join-Path $sourceClaudeDir "commands" $cmd.Name
                        if (-not (Test-Path $sourceCmd)) {
                            $customCommands += $cmd.Name
                        }
                    }
                }

                # Copy with no-clobber (preserve existing)
                $items = Get-ChildItem $sourceClaudeDir | Where-Object {
                    $_.Name -notin @("docs", "install.sh", "install.ps1")
                }
                foreach ($item in $items) {
                    $targetPath = Join-Path $ClaudePath $item.Name
                    if ($item.PSIsContainer) {
                        if (-not (Test-Path $targetPath)) {
                            Copy-Item -Path $item.FullName -Destination $targetPath -Recurse -Force
                        }
                    } else {
                        if (-not (Test-Path $targetPath)) {
                            Copy-Item -Path $item.FullName -Destination $targetPath -Force
                        }
                    }
                }

                # Copy scripts from shared/ subdirectories if they don't exist
                if (-not (Test-Path (Join-Path $ClaudePath "scripts"))) {
                    Copy-SharedScripts -ClaudePath $ClaudePath
                }

                # Report custom commands preserved
                if ($customCommands.Count -gt 0) {
                    Write-Output "  Preserved custom commands:"
                    foreach ($cmd in $customCommands) {
                        Write-Output "    - $cmd"
                    }
                }

                Write-Output "  Merge complete. Existing files preserved, new files added."
            }
            "update-workflows" {
                # Update workflows only: update built-in commands, scripts, agents, templates, and rules
                Write-ColorOutput "Update workflows mode: updating built-in commands, scripts, agents, templates, and rules" -Color $Colors.Green

                # Update built-in commands while preserving custom commands
                $commandsPath = Join-Path $ClaudePath "commands"
                $sourceCommandsPath = Join-Path $sourceClaudeDir "commands"
                if (Test-Path $sourceCommandsPath) {
                    Write-Output "  Updating commands directory (preserving custom commands)..."

                    # Identify custom commands
                    $customCommands = @()
                    if (Test-Path $commandsPath) {
                        foreach ($cmd in Get-ChildItem $commandsPath -Filter "*.md") {
                            $sourceCmd = Join-Path $sourceCommandsPath $cmd.Name
                            if (-not (Test-Path $sourceCmd)) {
                                $customCommands += @{Name = $cmd.Name; Path = $cmd.FullName}
                            }
                        }
                    }

                    # Backup custom commands
                    $tempCustomCommands = @()
                    foreach ($cmd in $customCommands) {
                        $tempPath = [System.IO.Path]::GetTempFileName() + ".md"
                        Copy-Item -Path $cmd.Path -Destination $tempPath -Force
                        $tempCustomCommands += @{Name = $cmd.Name; TempPath = $tempPath}
                    }

                    # Create commands directory and copy built-in commands
                    if (-not (Test-Path $commandsPath)) {
                        New-Item -ItemType Directory -Path $commandsPath -Force | Out-Null
                    }
                    Copy-Item -Path (Join-Path $sourceCommandsPath "*") -Destination $commandsPath -Force

                    # Restore custom commands
                    foreach ($cmd in $tempCustomCommands) {
                        Copy-Item -Path $cmd.TempPath -Destination (Join-Path $commandsPath $cmd.Name) -Force
                        Remove-Item -Path $cmd.TempPath -Force
                    }

                    # Report preserved custom commands
                    if ($customCommands.Count -gt 0) {
                        Write-Output "    Preserved custom commands:"
                        foreach ($cmd in $customCommands) {
                            Write-Output "      - $($cmd.Name)"
                        }
                    }
                }

                # Update scripts directory (preserve custom scripts)
                Write-Output "  Updating scripts directory (preserving custom scripts)..."
                $scriptsPath = Join-Path $ClaudePath "scripts"

                # Backup custom scripts if they exist
                $customScripts = @()
                if (Test-Path $scriptsPath) {
                    $sharedDir = Join-Path (Split-Path $SCRIPT_DIR -Parent) "shared"
                    foreach ($scriptFile in Get-ChildItem $scriptsPath -Recurse -File) {
                        $relativePath = [System.IO.Path]::GetRelativePath($scriptsPath, $scriptFile.FullName)
                        $foundInSource = $false
                        foreach ($subdir in @("analyzers", "generators", "setup", "utils", "tests", "ci", "core")) {
                            $sourcePath = Join-Path $sharedDir $subdir ($relativePath -replace "^$subdir[\\/]", "")
                            if ((Test-Path $sourcePath) -and $relativePath.StartsWith("$subdir\")) {
                                $foundInSource = $true
                                break
                            }
                        }
                        if (-not $foundInSource) {
                            $tempPath = [System.IO.Path]::GetTempFileName()
                            Copy-Item -Path $scriptFile.FullName -Destination $tempPath -Force
                            $customScripts += @{RelativePath = $relativePath; TempPath = $tempPath}
                        }
                    }
                }

                # Remove and recreate scripts directory
                if (Test-Path $scriptsPath) {
                    Remove-Item -Path $scriptsPath -Recurse -Force
                }
                Copy-SharedScripts -ClaudePath $ClaudePath

                # Restore custom scripts
                if ($customScripts.Count -gt 0) {
                    Write-Output "    Preserved custom scripts:"
                    foreach ($script in $customScripts) {
                        $targetPath = Join-Path $scriptsPath $script.RelativePath
                        $targetDir = Split-Path $targetPath -Parent
                        if (-not (Test-Path $targetDir)) {
                            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                        }
                        Copy-Item -Path $script.TempPath -Destination $targetPath -Force
                        Remove-Item -Path $script.TempPath -Force
                        Write-Output "      - $($script.RelativePath)"
                    }
                }

                # Update agents directory
                $agentsPath = Join-Path $ClaudePath "agents"
                $sourceAgentsPath = Join-Path $sourceClaudeDir "agents"
                if (Test-Path $sourceAgentsPath) {
                    Write-Output "  Updating agents directory..."
                    if (Test-Path $agentsPath) {
                        Remove-Item -Path $agentsPath -Recurse -Force
                    }
                    Copy-Item -Path $sourceAgentsPath -Destination $agentsPath -Recurse -Force
                }

                # Update templates directory
                $templatesPath = Join-Path $ClaudePath "templates"
                $sourceTemplatesPath = Join-Path $sourceClaudeDir "templates"
                if (Test-Path $sourceTemplatesPath) {
                    Write-Output "  Updating templates directory..."
                    if (Test-Path $templatesPath) {
                        Remove-Item -Path $templatesPath -Recurse -Force
                    }
                    Copy-Item -Path $sourceTemplatesPath -Destination $templatesPath -Recurse -Force
                }

                # Update rules directory
                $rulesPath = Join-Path $ClaudePath "rules"
                $sourceRulesPath = Join-Path $sourceClaudeDir "rules"
                if (Test-Path $sourceRulesPath) {
                    Write-Output "  Updating rules directory..."
                    if (Test-Path $rulesPath) {
                        Remove-Item -Path $rulesPath -Recurse -Force
                    }
                    Copy-Item -Path $sourceRulesPath -Destination $rulesPath -Recurse -Force
                }

                Write-Output "  Workflow update complete. Built-in commands, scripts, agents, templates, and rules updated, custom commands and other files preserved."
            }
        }

        # Copy CLAUDE.md project documentation
        $rootClaudeFile = Join-Path $SCRIPT_DIR "CLAUDE.md"
        $targetClaudeFile = Join-Path $ClaudePath "CLAUDE.md"

        if (Test-Path $rootClaudeFile) {
            Copy-Item -Path $rootClaudeFile -Destination $targetClaudeFile -Force
        }

        # ✅ REPLACE with modern global rules handling
        Handle-GlobalRules -SourceDir $SCRIPT_DIR -ClaudePath $ClaudePath

        # Create installation log
        $installLog = Join-Path $ClaudePath "installation-log.txt"
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $mcpStatus = if ($SkipMcp) { "Skipped" } else { "Installed" }
        $pythonStatus = if ($SkipPython) { "Skipped" } else { "Installed" }
        @"
AI-Assisted Workflows Installation Log
=====================================
Installation Date: $timestamp
Installer Version: $VERSION
Target Path: $ClaudePath
Install Mode: $InstallMode
MCP Tools: $mcpStatus
Python Dependencies: $pythonStatus
"@ | Set-Content -Path $installLog

        Write-ColorOutput "[OK] Workflow files copied successfully" -Color $Colors.Green
        Write-Log "Workflow files copied successfully to: $ClaudePath"

    } catch {
        Write-ColorOutput "[ERROR] Error copying workflow files: $($_.Exception.Message)" -Color $Colors.Red
        Write-Log "Error copying workflow files: $($_.Exception.Message)" -Level "ERROR"
        exit 1
    }

    # Ensure required directories exist
    $commandsDir = Join-Path $ClaudePath "commands"
    $scriptsDir = Join-Path $ClaudePath "scripts"

    if (-not (Test-Path $commandsDir)) {
        Write-Log "Creating missing commands directory: $commandsDir"
        New-Item -ItemType Directory -Path $commandsDir -Force | Out-Null
    }

    if (-not (Test-Path $scriptsDir)) {
        Write-Log "Creating missing scripts directory: $scriptsDir"
        New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    }
}

function Copy-SharedScripts {
    param([string]$ClaudePath)

    $sharedDir = Join-Path (Split-Path $SCRIPT_DIR -Parent) "shared"
    Write-Log "Looking for shared directory at: $sharedDir"

    if (Test-Path $sharedDir) {
        $targetScriptsDir = Join-Path $ClaudePath "scripts"
        Write-Log "Creating scripts directory at: $targetScriptsDir"
        New-Item -ItemType Directory -Path $targetScriptsDir -Force | Out-Null
        Write-Log "Copying scripts from shared/ subdirectories to $targetScriptsDir"

        $copiedCount = 0
        foreach ($subdir in @("analyzers", "generators", "setup", "utils", "tests", "ci", "core")) {
            $sourcePath = Join-Path $sharedDir $subdir
            if (Test-Path $sourcePath) {
                $targetPath = Join-Path $targetScriptsDir $subdir
                Copy-Item -Path $sourcePath -Destination $targetPath -Recurse -Force
                Write-Log "Copied $subdir to scripts directory"
                $copiedCount++
            } else {
                Write-Log "Source directory not found: $sourcePath" -Level "WARNING"
            }
        }

        if ($copiedCount -eq 0) {
            Write-Log "No subdirectories were copied from shared/" -Level "WARNING"
        } else {
            Write-Log "Successfully copied $copiedCount subdirectories to scripts"
        }
    } else {
        Write-Log "Shared directory not found at: $sharedDir" -Level "ERROR"
        Write-ColorOutput "[WARNING] Shared scripts directory not found: $sharedDir" -Color $Colors.Yellow
    }
}

function Test-Installation {
    param([string]$ClaudePath)

    Write-Output ""
    Write-ColorOutput "Verifying installation..." -Color $Colors.Yellow
    Write-Log "Starting installation verification"

    $errors = 0

    # Check main directories
    $requiredDirs = @("commands", "scripts", "rules", "templates", "agents")
    foreach ($dir in $requiredDirs) {
        $dirPath = Join-Path $ClaudePath $dir
        if (Test-Path $dirPath) {
            Write-ColorOutput "[OK] Directory $dir found" -Color $Colors.Green
        } else {
            Write-ColorOutput "[ERROR] Directory $dir missing" -Color $Colors.Red
            $errors++
        }
    }

    # Check key files
    $requiredFiles = @("claude.md", "CLAUDE.md")
    foreach ($file in $requiredFiles) {
        $filePath = Join-Path $ClaudePath $file
        if (Test-Path $filePath) {
            Write-ColorOutput "[OK] File $file found" -Color $Colors.Green
        } else {
            Write-ColorOutput "[WARNING] File $file missing" -Color $Colors.Yellow
        }
    }

    # Count command files
    $commandsPath = Join-Path $ClaudePath "commands"
    if (Test-Path $commandsPath) {
        $commandCount = (Get-ChildItem $commandsPath -Filter "*.md" | Measure-Object).Count
        Write-ColorOutput "[INFO] Commands found: $commandCount" -Color $Colors.Green
    }

    # Count script files
    $scriptsPath = Join-Path $ClaudePath "scripts"
    if (Test-Path $scriptsPath) {
        $scriptCount = (Get-ChildItem $scriptsPath -Filter "*.py" -Recurse | Measure-Object).Count
        Write-ColorOutput "[INFO] Python scripts found: $scriptCount" -Color $Colors.Green
    }

    # Count template files
    $templatesPath = Join-Path $ClaudePath "templates"
    if (Test-Path $templatesPath) {
        $templateCount = (Get-ChildItem $templatesPath -Filter "*.md" | Measure-Object).Count
        Write-ColorOutput "[INFO] Templates found: $templateCount" -Color $Colors.Green
    }

    if ($errors -gt 0) {
        Write-ColorOutput "[ERROR] Installation verification failed: $errors errors found" -Color $Colors.Red
        Write-Log "Installation verification failed: $errors errors found" -Level "ERROR"
        return $false
    } else {
        Write-ColorOutput "[OK] Installation verification successful" -Color $Colors.Green
        Write-Log "Installation verification successful"
        return $true
    }
}

function Show-CompletionMessage {
    param([string]$ClaudePath, [string]$BackupPath)

    Write-Output ""
    Write-ColorOutput "==================================" -Color $Colors.Green
    Write-ColorOutput "Installation completed successfully!" -Color $Colors.Green
    Write-ColorOutput "==================================" -Color $Colors.Green
    Write-Output ""

    Write-ColorOutput "AI-Assisted Workflows v$VERSION installed to:" -Color $Colors.Yellow
    Write-Output "  $ClaudePath"
    Write-Output ""

    if ($BackupPath) {
        Write-ColorOutput "Previous installation backed up to:" -Color $Colors.Yellow
        Write-Output "  $BackupPath"
        Write-Output ""
    }

    Write-ColorOutput "Available commands:" -Color $Colors.Yellow
    $commandsPath = Join-Path $ClaudePath "commands"
    if (Test-Path $commandsPath) {
        $commands = Get-ChildItem $commandsPath -Filter "*.md" | ForEach-Object { $_.BaseName }
        $commandCount = $commands.Count
        Write-Output "  Total commands: $commandCount"
        foreach ($command in $commands | Select-Object -First 5) {
            Write-Output "  • $command"
        }
        if ($commandCount -gt 5) {
            Write-Output "  • ... and $($commandCount - 5) more"
        }
    }
    Write-Output ""

    Write-ColorOutput "Next steps:" -Color $Colors.Yellow
    Write-Output "  1. Read documentation: $ClaudePath\CLAUDE.md"
    Write-Output "  2. Try a command: claude /analyze-security"
    Write-Output "  3. Use build flags: --prototype or --tdd"
    Write-Output ""

    if (-not $SkipMcp) {
        Write-ColorOutput "MCP Tools configured:" -Color $Colors.Yellow
        Write-Output "  • sequential-thinking - Complex analysis workflows"
        Write-Output "  • grep - GitHub repository code search"
        Write-Output ""
    }

    Write-ColorOutput "Enable Codebase-Expert Agent (AI-powered code search):" -Color $Colors.Yellow
    Write-Output "  1. /setup-ci-monitoring    (index codebase for semantic search)"
    Write-Output "  2. /setup-serena-mcp       (enable enhanced LSP support)"
    Write-Output "  3. Review ci_config.json   (configure directory exclusions)"
    Write-Output ""

    Write-ColorOutput "For help and support:" -Color $Colors.Yellow
    Write-Output "  • Documentation: $ClaudePath\README.md"
    Write-Output "  • Log file: $LOG_FILE"
    Write-Output ""
}

# Global spinner state
$script:SpinnerChars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
$script:SpinnerIndex = 0
$script:ActiveSpinner = $null

function Start-Spinner {
    param(
        [string]$Message,
        [scriptblock]$Action
    )

    # Start background job
    $job = Start-Job -ScriptBlock $Action
    $startTime = Get-Date

    # Show spinner while job runs
    while ($job.State -eq 'Running') {
        $elapsed = (Get-Date) - $startTime
        $elapsedString = "{0:mm\:ss}" -f $elapsed

        # Get current spinner character
        $spinnerChar = $script:SpinnerChars[$script:SpinnerIndex % $script:SpinnerChars.Length]
        $script:SpinnerIndex++

        # Display spinner with message and elapsed time
        Write-Host -NoNewline ("`r{0} {1} [{2}]" -f $spinnerChar, $Message, $elapsedString)
        Start-Sleep -Milliseconds 100
    }

    # Clear spinner line
    Write-Host -NoNewline ("`r{0}`r" -f (' ' * 60))

    # Get job result and clean up
    $result = Receive-Job $job -ErrorAction SilentlyContinue
    $error = $job.ChildJobs[0].Error
    Remove-Job $job

    # Handle errors
    if ($error.Count -gt 0) {
        throw $error[0]
    }

    return $result
}

function Invoke-WithSpinner {
    param(
        [string]$Message,
        [scriptblock]$ScriptBlock
    )

    try {
        $result = Start-Spinner -Message $Message -Action $ScriptBlock
        Write-ColorOutput "✓ $Message completed" -Color $Colors.Green
        return $result
    }
    catch {
        Write-ColorOutput "✗ $Message failed: $_" -Color $Colors.Red
        throw
    }
}

function Show-Phase {
    param(
        [int]$PhaseNumber,
        [int]$TotalPhases,
        [string]$Description
    )

    Write-Output ""
    Write-ColorOutput "[$PhaseNumber/$TotalPhases] $Description" -Color $Colors.Cyan
    Write-ColorOutput ("-" * 40) -Color $Colors.Blue
}

function Show-Header {
    if ($DryRun) {
        return  # Skip header in dry run mode
    }

    Write-Output ""
    Write-ColorOutput "┌─────────────────────────────────────┐" -Color $Colors.Green
    Write-ColorOutput "│  AI-Assisted Workflows Installer    │" -Color $Colors.Green
    Write-ColorOutput "│  Version $VERSION                   │" -Color $Colors.Green
    Write-ColorOutput "└─────────────────────────────────────┘" -Color $Colors.Green
}

# Global cache variables for performance
$script:PipListCache = $null
$script:CacheTimestamp = $null
$script:CacheValidityMinutes = 5

function Get-PipPackageList {
    param([bool]$ForceRefresh = $false)

    $now = Get-Date
    $cacheExpired = $script:CacheTimestamp -eq $null -or
                   ($now - $script:CacheTimestamp).TotalMinutes -gt $script:CacheValidityMinutes

    if ($ForceRefresh -or $cacheExpired -or $script:PipListCache -eq $null) {
        Write-Log "Caching pip package list for performance..."
        try {
            $script:PipListCache = & pip list --format=freeze 2>$null
            $script:CacheTimestamp = $now
            Write-Log "Cached $($script:PipListCache.Count) pip packages"
        }
        catch {
            Write-Log "Failed to cache pip list: $_" -Level "ERROR"
            $script:PipListCache = @()
        }
    }

    return $script:PipListCache
}

function Test-PipPackageInstalled {
    param([string]$PackageName)

    $packages = Get-PipPackageList
    $found = $packages | Where-Object { $_ -match "^$PackageName==" }

    if ($found) {
        Write-Log "Package $PackageName found in cache"
        return $true
    }
    else {
        Write-Log "Package $PackageName not found in cache"
        return $false
    }
}

function Test-PrerequisitesParallel {
    Write-Log "Starting parallel prerequisite checks"

    # Define check scripts
    $pythonCheck = {
        try {
            $version = & python --version 2>&1
            $pipVersion = & pip --version 2>&1
            return @{
                Tool = "Python"
                Version = $version
                PipVersion = $pipVersion
                Found = $true
                ExitCode = 0
            }
        }
        catch {
            return @{
                Tool = "Python"
                Found = $false
                Error = $_.Exception.Message
                ExitCode = 1
            }
        }
    }

    $nodeCheck = {
        try {
            $nodeVersion = & node --version 2>&1
            $npmVersion = & npm --version 2>&1
            return @{
                Tool = "Node.js"
                NodeVersion = $nodeVersion
                NpmVersion = $npmVersion
                Found = $true
                ExitCode = 0
            }
        }
        catch {
            return @{
                Tool = "Node.js"
                Found = $false
                Error = $_.Exception.Message
                ExitCode = 1
            }
        }
    }

    $claudeCheck = {
        if ($using:SkipMcp) {
            return @{
                Tool = "Claude CLI"
                Found = $true
                Skipped = $true
                ExitCode = 0
            }
        }

        try {
            $version = & claude --version 2>&1
            return @{
                Tool = "Claude CLI"
                Version = $version
                Found = $true
                ExitCode = 0
            }
        }
        catch {
            return @{
                Tool = "Claude CLI"
                Found = $false
                Error = $_.Exception.Message
                ExitCode = 1
            }
        }
    }

    # Start parallel jobs
    Write-ColorOutput "Running dependency checks in parallel..." -Color $Colors.Cyan
    $jobs = @()
    $jobs += Start-Job -ScriptBlock $pythonCheck
    $jobs += Start-Job -ScriptBlock $nodeCheck
    $jobs += Start-Job -ScriptBlock $claudeCheck

    # Wait for completion with timeout
    $timeout = 30 # seconds
    $completed = Wait-Job $jobs -Timeout $timeout

    if ($completed.Count -lt $jobs.Count) {
        Write-ColorOutput "[WARNING] Some dependency checks timed out" -Color $Colors.Yellow
        $jobs | Stop-Job
    }

    # Collect and process results
    $results = $jobs | Receive-Job
    $jobs | Remove-Job

    $hasErrors = $false

    foreach ($result in $results) {
        if ($result.Skipped) {
            Write-ColorOutput "[SKIP] $($result.Tool): Skipped" -Color $Colors.Yellow
        }
        elseif ($result.Found) {
            $versionInfo = ""
            if ($result.Version) { $versionInfo = ": $($result.Version)" }
            if ($result.NodeVersion) { $versionInfo = ": Node $($result.NodeVersion), npm $($result.NpmVersion)" }
            if ($result.PipVersion) { $versionInfo = ": $($result.Version), pip $($result.PipVersion)" }

            Write-ColorOutput "[OK] $($result.Tool)$versionInfo" -Color $Colors.Green
            Write-Log "$($result.Tool) check passed$versionInfo"
        }
        else {
            Write-ColorOutput "[ERROR] $($result.Tool): Not found or failed" -Color $Colors.Red
            if ($result.Error) {
                Write-Log "$($result.Tool) check failed: $($result.Error)" -Level "ERROR"
            }
            $hasErrors = $true
        }
    }

    if ($hasErrors) {
        Write-ColorOutput "Prerequisites check failed. Please install missing dependencies." -Color $Colors.Red
        exit 1
    }

    Write-Log "All prerequisite checks completed successfully"
}

function Copy-FilesOptimized {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Description = "Copying files"
    )

    Invoke-WithSpinner -Message $Description -ScriptBlock {
        # Use robocopy for better performance on Windows if available
        if (Get-Command robocopy -ErrorAction SilentlyContinue) {
            # Robocopy with optimized flags
            $result = & robocopy $Source $Destination /E /NFL /NDL /NJH /NJS /NC /NS /NP 2>$null
            # Robocopy exit codes 0-7 are success, 8+ are errors
            if ($LASTEXITCODE -gt 7) {
                throw "Robocopy failed with exit code $LASTEXITCODE"
            }
        }
        else {
            # Fallback to PowerShell native copy
            Copy-Item -Path "$Source\*" -Destination $Destination -Recurse -Force
        }
    }
}

function Set-ExecutablePermissions {
    param([string]$Path)

    Invoke-WithSpinner -Message "Setting file permissions" -ScriptBlock {
        # Windows equivalent - ensure files are not read-only
        Get-ChildItem -Path $Path -Recurse -Include "*.py","*.sh","*.ps1" -ErrorAction SilentlyContinue |
        ForEach-Object {
            if ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
                $_.Attributes = $_.Attributes -band (-bnot [System.IO.FileAttributes]::ReadOnly)
            }
        }
    }
}

function Invoke-SafeOperation {
    param(
        [scriptblock]$Operation,
        [string]$Description,
        [int]$MaxRetries = 3,
        [int]$RetryDelaySeconds = 5
    )

    $attempt = 1

    while ($attempt -le $MaxRetries) {
        try {
            Write-Log "Attempting $Description (attempt $attempt of $MaxRetries)"
            $result = & $Operation
            Write-Log "$Description completed successfully"
            return $result
        }
        catch {
            Write-Log "$Description failed on attempt $attempt : $_" -Level "WARNING"

            if ($attempt -eq $MaxRetries) {
                Write-ColorOutput "[ERROR] $Description failed after $MaxRetries attempts" -Color $Colors.Red
                throw
            }

            Write-ColorOutput "[RETRY] Retrying $Description in $RetryDelaySeconds seconds..." -Color $Colors.Yellow
            Start-Sleep -Seconds $RetryDelaySeconds
            $attempt++
        }
    }
}

function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-DotNetFramework {
    # Check .NET Framework version for compatibility
    try {
        $dotNetVersion = (Get-ItemProperty "HKLM:SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full\" -Name Release -ErrorAction SilentlyContinue).Release
        if ($dotNetVersion -ge 461808) { # .NET Framework 4.7.2 or later
            Write-Log ".NET Framework version check passed"
            return $true
        }
        else {
            Write-ColorOutput "[WARNING] .NET Framework 4.7.2 or later recommended" -Color $Colors.Yellow
            return $true # Don't fail installation, just warn
        }
    }
    catch {
        Write-Log "Could not determine .NET Framework version" -Level "WARNING"
        return $true # Don't fail installation
    }
}

function Handle-GlobalRules {
    param(
        [string]$SourceDir,
        [string]$ClaudePath
    )

    # ✅ CORRECT: Use modern path
    $sourceRulesFile = Join-Path $SourceDir "rules\global.claude.rules.md"
    $targetClaudeFile = Join-Path $ClaudePath "claude.md"

    # ✅ Validate source exists
    if (-not (Test-Path $sourceRulesFile)) {
        Write-ColorOutput "[ERROR] Global rules file not found: $sourceRulesFile" -Color $Colors.Red
        Write-Log "Global rules file missing: $sourceRulesFile" -Level "ERROR"
        exit 1
    }

    Write-Log "Processing global rules from: $sourceRulesFile"

    if (Test-Path $targetClaudeFile) {
        # ✅ SMART MERGE: Check for existing section
        Write-Log "Existing claude.md found, checking for AI-Assisted Workflows section..."

        $content = Get-Content $targetClaudeFile -Raw -ErrorAction SilentlyContinue
        if ($content -match "# AI-Assisted Workflows v") {
            Write-Log "AI-Assisted Workflows section already exists, skipping merge"
            Write-ColorOutput "AI-Assisted Workflows section already exists in claude.md" -Color $Colors.Yellow
            return
        }

        # ✅ Append with version header
        Write-Log "Appending AI-Assisted Workflows section to existing claude.md"
        Write-ColorOutput "Appending AI-Assisted Workflows section to existing claude.md" -Color $Colors.Green

        Add-Content -Path $targetClaudeFile -Value ""
        Add-Content -Path $targetClaudeFile -Value "---"
        Add-Content -Path $targetClaudeFile -Value ""
        Add-Content -Path $targetClaudeFile -Value "# AI-Assisted Workflows v$VERSION - Auto-generated, do not edit"
        Add-Content -Path $targetClaudeFile -Value ""

        $rulesContent = Get-Content $sourceRulesFile
        Add-Content -Path $targetClaudeFile -Value $rulesContent

        Write-Log "Successfully appended AI-Assisted Workflows section"
    }
    else {
        # ✅ Create new with header
        Write-Log "Creating new claude.md with global rules"
        Write-ColorOutput "Creating claude.md with global rules" -Color $Colors.Green

        $headerContent = @(
            "# AI-Assisted Workflows v$VERSION - Auto-generated, do not edit",
            ""
        )

        $rulesContent = Get-Content $sourceRulesFile
        $allContent = $headerContent + $rulesContent

        $allContent | Out-File -FilePath $targetClaudeFile -Encoding UTF8
        Write-Log "Successfully created claude.md with global rules"
    }
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Initialize logging
Write-Log "Starting AI-Assisted Workflows installation v$VERSION"
Write-Log "Command line: $($MyInvocation.Line)"

# Main installation process
try {
    # Show professional header
    if (-not $DryRun) {
        Show-Header
    }

    Write-ColorOutput "Target directory: $(Resolve-TargetPath $TargetPath)" -Color $Colors.Yellow
    Write-Output ""

    # Phase 1: System Requirements
    Show-Phase -PhaseNumber 1 -TotalPhases 8 -Description "Checking system requirements"

    # Resolve target path
    $resolvedTargetPath = Resolve-TargetPath $TargetPath
    $claudePath = Join-Path $resolvedTargetPath ".claude"

    # Check write permissions
    if (-not (Test-WritePermissions $resolvedTargetPath)) {
        Write-ColorOutput "[ERROR] No write permission for: $resolvedTargetPath" -Color $Colors.Red
        Write-Log "No write permissions for target path: $resolvedTargetPath" -Level "ERROR"
        exit 1
    }

    Test-PrerequisitesParallel

    # Phase 2: Directory Setup
    Show-Phase -PhaseNumber 2 -TotalPhases 8 -Description "Setting up directories"

    # Handle existing installation and get install mode
    $installResult = Handle-ExistingInstallation $claudePath
    $backupPath = $installResult.BackupPath
    $installMode = $installResult.Mode

    if ($DryRun) {
        Write-ColorOutput "[DRY RUN] Installation preview completed successfully" -Color $Colors.Blue
        Write-Output "All operations would succeed. Run without -DryRun to perform actual installation."
        exit 0
    }

    # Phase 3: File Copying
    Show-Phase -PhaseNumber 3 -TotalPhases 8 -Description "Copying workflow files"
    Copy-WorkflowFiles $claudePath $installMode

    # Phase 4: Installation Tracking
    Show-Phase -PhaseNumber 4 -TotalPhases 8 -Description "Creating installation tracking"
    # Installation log is created within Copy-WorkflowFiles

    # Phase 5: Dependencies
    Show-Phase -PhaseNumber 5 -TotalPhases 8 -Description "Installing dependencies"
    if (-not $SkipPython) {
        Install-PythonDependencies
    } else {
        Write-ColorOutput "Skipping Python dependencies installation" -Color $Colors.Yellow
    }

    # Phase 6: MCP Tools
    Show-Phase -PhaseNumber 6 -TotalPhases 8 -Description "Installing MCP tools"
    if (-not $SkipMcp) {
        Install-McpTools $claudePath
    } else {
        Write-ColorOutput "Skipping MCP tools installation" -Color $Colors.Yellow
    }

    # Phase 7: Verification
    Show-Phase -PhaseNumber 7 -TotalPhases 8 -Description "Verifying installation"
    if (-not (Test-Installation $claudePath)) {
        Write-ColorOutput "[ERROR] Installation verification failed" -Color $Colors.Red
        Write-Log "Installation verification failed" -Level "ERROR"
        exit 1
    }

    # Phase 8: Completion
    Show-Phase -PhaseNumber 8 -TotalPhases 8 -Description "Finalizing installation"
    Show-CompletionMessage $claudePath $backupPath
    Write-Log "Installation completed successfully"

} catch {
    Write-ColorOutput "[ERROR] Installation failed: $($_.Exception.Message)" -Color $Colors.Red
    Write-Log "Installation failed: $($_.Exception.Message)" -Level "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"

    # Cleanup guidance
    Write-Output ""
    Write-ColorOutput "Installation failed. Common solutions:" -Color $Colors.Yellow
    Write-Output "  1. Ensure Python 3.7+ is installed and in PATH"
    Write-Output "  2. Check internet connectivity for package downloads"
    Write-Output "  3. Run PowerShell as Administrator if permission issues occur"
    Write-Output "  4. Use -SkipMcp if Claude CLI is causing issues"
    Write-Output "  5. Use -SkipPython if Python dependencies are causing issues"
    Write-Output ""
    Write-Output "Log file: $LOG_FILE"

    # Cleanup any running jobs
    Get-Job | Stop-Job -ErrorAction SilentlyContinue
    Get-Job | Remove-Job -ErrorAction SilentlyContinue

    exit 1
}
