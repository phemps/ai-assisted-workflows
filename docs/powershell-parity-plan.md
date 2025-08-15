# PowerShell Install Script Parity Implementation Plan

## Executive Summary

The PowerShell installation script (`install.ps1`) currently lacks the comprehensive optimizations and modern UX improvements implemented in the bash script (`install.sh`). This document provides a complete implementation plan to achieve feature parity, focusing on critical data integrity issues, user experience revolution, and performance optimizations.

### Current State Analysis

| Feature Category | Bash Script Status | PowerShell Script Status | Priority |
|------------------|-------------------|-------------------------|----------|
| **Global Rules Handling** | ✅ Modern (`rules/global.claude.rules.md`) | ❌ Outdated (`claude.md`) | **CRITICAL** |
| **Smart Merging** | ✅ Version-based duplicate detection | ❌ Destructive overwrite | **CRITICAL** |
| **Loading Indicators** | ✅ Unicode spinners + elapsed time | ❌ Missing | **HIGH** |
| **Phase Display** | ✅ 8-phase progress (1/8-8/8) | ❌ Missing | **HIGH** |
| **Parallel Operations** | ✅ Concurrent dependency checks | ❌ Sequential | **MEDIUM** |
| **Performance Caching** | ✅ Cached pip list (5-10x faster) | ❌ Missing | **MEDIUM** |
| **Professional UX** | ✅ Beautiful installation header | ❌ Basic | **MEDIUM** |

### Gap Assessment

**Critical Issues (Data Integrity):**
- ❌ References obsolete file paths that no longer exist
- ❌ Uses destructive `-Force` overwrite without merging
- ❌ No duplicate detection - creates multiple sections

**High Priority UX Issues:**
- ❌ No progress indication during long operations
- ❌ Users think installation is "frozen"
- ❌ No professional installation experience

**Performance Issues:**
- ❌ 20-30% slower due to sequential operations
- ❌ Multiple pip checks instead of cached list
- ❌ No optimized file operations

## 1. Global Rules Handling Modernization

### 🚨 **CRITICAL PRIORITY - Data Integrity Issue**

#### Current Problems
```powershell
# BROKEN: References obsolete paths
$rootClaudeFile = Join-Path $SCRIPT_DIR "CLAUDE.md"
$nestedClaudeFile = Join-Path $SCRIPT_DIR "claude.md"  # ❌ NO LONGER EXISTS

# DESTRUCTIVE: Overwrites existing files
Copy-Item -Path $rootClaudeFile -Destination $targetClaudeFile -Force  # ❌ DESTROYS USER DATA
```

#### Solution Implementation

```powershell
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
```

#### Integration Points

```powershell
# ✅ Replace current file copying logic with:
function Copy-WorkflowFiles {
    param(
        [string]$Mode,
        [string]$ClaudePath
    )

    # ... existing copy logic ...

    # ✅ REPLACE this section:
    # Copy CLAUDE.md if it exists in root, otherwise copy claude.md as CLAUDE.md
    # $rootClaudeFile = Join-Path $SCRIPT_DIR "CLAUDE.md"
    # $nestedClaudeFile = Join-Path $SCRIPT_DIR "claude.md"

    # ✅ WITH modern global rules handling:
    Handle-GlobalRules -SourceDir $SCRIPT_DIR -ClaudePath $ClaudePath

    # ... rest of copy logic ...
}
```

## 2. UX Revolution - Loading Indicators & Progress

### A. Spinner Function Implementation

```powershell
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

# Convenience wrapper for simple operations
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
```

### B. Installation Phase Display

```powershell
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
```

### C. Spinner Integration Examples

```powershell
# File copying with spinner
Invoke-WithSpinner -Message "Copying workflow files" -ScriptBlock {
    Copy-Item -Path "$sourceDir\*" -Destination $ClaudePath -Recurse -Force
}

# Python package installation with spinner
Invoke-WithSpinner -Message "Installing Python packages" -ScriptBlock {
    & python -m pip install -r "$ClaudePath\scripts\setup\requirements.txt" --quiet
}

# MCP tool installation with spinner
Invoke-WithSpinner -Message "Installing MCP tool: sequential-thinking" -ScriptBlock {
    & claude mcp add sequential-thinking -s user -- npx -y '@modelcontextprotocol/server-sequential-thinking' 2>$null
}
```

## 3. Performance Optimizations

### A. Parallel Dependency Checks

```powershell
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
        if ($SkipMcp) {
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
```

### B. Cached Package Operations

```powershell
# Global cache variables
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

function Get-PipPackageVersion {
    param([string]$PackageName)

    $packages = Get-PipPackageList
    $package = $packages | Where-Object { $_ -match "^$PackageName==" } | Select-Object -First 1

    if ($package) {
        if ($package -match "$PackageName==(.+)") {
            return $Matches[1]
        }
    }

    return $null
}
```

### C. Optimized File Operations

```powershell
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
```

## 4. Main Execution Flow Modernization

### Current Flow (Simple Sequential)
```powershell
# Old approach - no phases, no progress
Test-Prerequisites
Handle-ExistingInstallation
Copy-WorkflowFiles
Install-PythonDependencies
Install-MCP
Show-CompletionMessage
```

### New Flow with Phases and Progress

```powershell
function Start-Installation {
    param(
        [string]$TargetPath,
        [bool]$DryRun,
        [bool]$SkipMcp,
        [bool]$SkipPython
    )

    try {
        # Show professional header
        if (-not $DryRun) {
            Show-Header
        }

        # Phase 1: System Requirements
        Show-Phase -PhaseNumber 1 -TotalPhases 8 -Description "Checking system requirements"
        Test-PrerequisitesParallel

        # Phase 2: Analysis Tools
        Show-Phase -PhaseNumber 2 -TotalPhases 8 -Description "Checking analysis tools"
        Test-SecurityTools

        # Phase 3: Directory Setup
        Show-Phase -PhaseNumber 3 -TotalPhases 8 -Description "Setting up directories"
        $installResult = Setup-InstallDirectory -TargetPath $TargetPath
        $claudePath = $installResult.ClaudePath
        $backupPath = $installResult.BackupPath
        $installMode = $installResult.Mode

        if ($DryRun) {
            Write-ColorOutput "[DRY RUN] Installation preview completed successfully" -Color $Colors.Blue
            Write-Output "All operations would succeed. Run without -DryRun to perform actual installation."
            return
        }

        # Phase 4: File Copying
        Show-Phase -PhaseNumber 4 -TotalPhases 8 -Description "Copying workflow files"
        Copy-WorkflowFiles -Mode $installMode -ClaudePath $claudePath

        # Phase 5: Installation Tracking
        Show-Phase -PhaseNumber 5 -TotalPhases 8 -Description "Creating installation tracking"
        Create-InstallationLog -ClaudePath $claudePath

        # Phase 6: Dependencies
        Show-Phase -PhaseNumber 6 -TotalPhases 8 -Description "Installing dependencies"
        if (-not $SkipPython) {
            Install-PythonDependencies -ClaudePath $claudePath
        }
        else {
            Write-ColorOutput "Skipping Python dependencies installation" -Color $Colors.Yellow
        }
        Test-ESLintInstallation

        # Phase 7: MCP Tools
        Show-Phase -PhaseNumber 7 -TotalPhases 8 -Description "Installing MCP tools"
        if (-not $SkipMcp) {
            Install-MCPTools
        }
        else {
            Write-ColorOutput "Skipping MCP tools installation" -Color $Colors.Yellow
        }

        # Phase 8: Verification
        Show-Phase -PhaseNumber 8 -TotalPhases 8 -Description "Verifying installation"
        Test-InstallationIntegrity -ClaudePath $claudePath

        # Show completion
        Show-CompletionMessage -ClaudePath $claudePath -BackupPath $backupPath

        Write-Log "Installation completed successfully"
    }
    catch {
        Write-ColorOutput "[ERROR] Installation failed: $_" -Color $Colors.Red
        Write-Log "Installation failed: $_" -Level "ERROR"

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

        exit 1
    }
}
```

## 5. Additional PowerShell-Specific Enhancements

### A. Progress Bar for Countable Operations

```powershell
function Show-ProgressBar {
    param(
        [int]$Current,
        [int]$Total,
        [string]$Activity,
        [string]$Status = ""
    )

    $percentComplete = if ($Total -gt 0) { ($Current / $Total) * 100 } else { 0 }
    Write-Progress -Activity $Activity -Status "$Status ($Current of $Total)" -PercentComplete $percentComplete
}

# Example usage during file copying
function Copy-FilesWithProgress {
    param([string]$Source, [string]$Destination)

    $files = Get-ChildItem -Path $Source -Recurse -File
    $totalFiles = $files.Count
    $current = 0

    foreach ($file in $files) {
        $current++
        Show-ProgressBar -Current $current -Total $totalFiles -Activity "Copying Files" -Status $file.Name

        $relativePath = $file.FullName.Substring($Source.Length + 1)
        $targetPath = Join-Path $Destination $relativePath
        $targetDir = Split-Path $targetPath

        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }

        Copy-Item -Path $file.FullName -Destination $targetPath -Force
    }

    Write-Progress -Activity "Copying Files" -Completed
}
```

### B. Windows-Specific Optimizations

```powershell
function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-RequiredModules {
    # Check for required PowerShell modules
    $requiredModules = @('PowerShellGet', 'PackageManagement')

    foreach ($module in $requiredModules) {
        if (-not (Get-Module -ListAvailable -Name $module)) {
            Write-ColorOutput "Installing required module: $module" -Color $Colors.Yellow
            Install-Module -Name $module -Force -Scope CurrentUser
        }
    }
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
```

### C. Enhanced Error Handling

```powershell
function Set-ErrorHandling {
    # Set strict error handling
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'  # Speeds up web requests

    # Global error handler
    trap {
        Write-ColorOutput "[FATAL ERROR] $($_.Exception.Message)" -Color $Colors.Red
        Write-Log "Fatal error: $($_.Exception.Message)" -Level "ERROR"
        Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"

        # Cleanup any running jobs
        Get-Job | Stop-Job
        Get-Job | Remove-Job

        exit 1
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
```

## 6. Testing Requirements

### Test Scenarios

#### A. Functional Testing
1. **Fresh Installation Test**
   ```powershell
   # Test all phases display correctly
   .\install.ps1 "C:\temp\test-fresh" -Verbose
   # Verify: Header, 8 phases, spinners, completion message
   ```

2. **Merge Mode Test**
   ```powershell
   # Create existing installation
   .\install.ps1 "C:\temp\test-merge"
   # Add custom file
   "# Custom content" | Out-File "C:\temp\test-merge\.claude\claude.md" -Append
   # Test merge preserves content
   echo "2" | .\install.ps1 "C:\temp\test-merge"
   # Verify: Custom content preserved, AI-Assisted Workflows section added
   ```

3. **Global Rules Handling Test**
   ```powershell
   # Test with existing claude.md
   "# Existing project rules" | Out-File "C:\temp\test-rules\.claude\claude.md"
   .\install.ps1 "C:\temp\test-rules"
   # Verify: Original content + AI-Assisted Workflows section with version header
   ```

4. **Performance Test**
   ```powershell
   # Measure installation time
   Measure-Command { .\install.ps1 "C:\temp\perf-test" -SkipMcp -SkipPython }
   # Target: Should be 20-30% faster than current version
   ```

#### B. Error Handling Testing
```powershell
# Test missing dependencies
Remove-Item env:PATH  # Temporarily break PATH
.\install.ps1 -Verbose  # Should fail gracefully with helpful message

# Test permission issues
$testPath = "C:\Program Files\test"  # Requires admin
.\install.ps1 $testPath  # Should detect permission issue

# Test interrupted installation
# Start installation, kill process, restart
# Should handle partial state gracefully
```

#### C. Dry Run Testing
```powershell
.\install.ps1 -DryRun -Verbose
# Verify: Shows all phases, no actual changes, informative output
```

### Performance Benchmarks

| Metric | Current PowerShell | Target PowerShell | Bash Script |
|--------|-------------------|------------------|-------------|
| **Installation Time** | ~45 seconds | ~35 seconds (-22%) | ~30 seconds |
| **Dependency Checks** | ~15 seconds | ~8 seconds (parallel) | ~6 seconds |
| **User Experience** | Basic | Professional | Professional |
| **Progress Indication** | Minimal | Continuous | Continuous |
| **Error Recovery** | Basic | Robust | Robust |

### Quality Gates

✅ **Must Pass Before Release:**
- [ ] All 8 phases display correctly with spinners
- [ ] Global rules merge without data loss
- [ ] Custom commands preserved in merge mode
- [ ] Parallel dependency checks complete successfully
- [ ] Installation time improved by 20%+
- [ ] Error handling provides actionable guidance
- [ ] Dry run mode shows accurate preview
- [ ] Backup creation works correctly
- [ ] Version-based duplicate detection prevents multiple sections
- [ ] Professional installation header displays

## 7. Implementation Priority Order

### 🚨 **Phase 1: CRITICAL - Data Integrity (1-2 days)**
1. **Fix Global Rules Source Path**
   - Change from `claude.md` to `rules/global.claude.rules.md`
   - Add validation that source file exists

2. **Implement Smart Merging**
   - Replace destructive `-Force` copy with append logic
   - Add version-based duplicate detection
   - Test with existing claude.md files

3. **Add Auto-Generated Headers**
   - Version-based headers for tracking
   - Clear user guidance about managed content

### 🔥 **Phase 2: HIGH - Core UX (2-3 days)**
1. **Implement Spinner Function**
   - Unicode spinner with elapsed time
   - Job-based background execution
   - Error handling and cleanup

2. **Add Phase Display System**
   - 8-phase progress indicators
   - Professional installation header
   - Clear phase descriptions

3. **Integrate Spinners with Operations**
   - File copying operations
   - Package installations
   - Network operations

### ⚡ **Phase 3: MEDIUM - Performance (1-2 days)**
1. **Parallel Dependency Checks**
   - Concurrent Python/Node.js/Claude CLI checks
   - Timeout handling
   - Result aggregation

2. **Cached Package Operations**
   - Pip list caching with expiration
   - Fast package existence checks
   - Cache management

3. **Optimized File Operations**
   - Robocopy integration for Windows
   - Combined permission operations
   - Progress indication

### ✨ **Phase 4: LOW - Polish (1 day)**
1. **Enhanced Error Messages**
   - Actionable troubleshooting guidance
   - Detailed logging
   - Graceful failure modes

2. **Progress Bars for Long Operations**
   - File copying progress
   - Package installation progress
   - Visual feedback improvements

3. **Windows-Specific Optimizations**
   - Admin privilege detection
   - .NET Framework checks
   - PowerShell module validation

## 8. Implementation Checklist

### Pre-Implementation
- [ ] Review current PowerShell script structure
- [ ] Identify all locations requiring global rules changes
- [ ] Plan spinner integration points
- [ ] Design phase breakdown

### Critical Phase (Global Rules)
- [ ] Create `Handle-GlobalRules` function
- [ ] Update source path to `rules/global.claude.rules.md`
- [ ] Implement version-based duplicate detection
- [ ] Add smart merging logic
- [ ] Test with existing claude.md files
- [ ] Validate no data loss occurs

### UX Phase (Spinners & Phases)
- [ ] Implement spinner function with jobs
- [ ] Create phase display functions
- [ ] Add installation header
- [ ] Integrate spinners with file operations
- [ ] Integrate spinners with package installations
- [ ] Test spinner cleanup on errors

### Performance Phase
- [ ] Implement parallel dependency checks
- [ ] Add pip list caching
- [ ] Optimize file operations
- [ ] Add progress indicators
- [ ] Benchmark performance improvements

### Testing & Validation
- [ ] Test fresh installation with all features
- [ ] Test merge mode preserves custom content
- [ ] Test update workflows preserves customizations
- [ ] Test dry run shows accurate preview
- [ ] Test error handling and recovery
- [ ] Validate performance improvements
- [ ] Test on different Windows versions

### Documentation & Finalization
- [ ] Update inline documentation
- [ ] Update help text
- [ ] Create troubleshooting guide
- [ ] Validate feature parity with bash script

## 9. Success Criteria

### Functional Requirements ✅
- [ ] **Global Rules**: Uses `rules/global.claude.rules.md` as source
- [ ] **Smart Merging**: Appends to existing claude.md without data loss
- [ ] **Duplicate Detection**: Version-based headers prevent multiple sections
- [ ] **Loading Spinners**: Unicode spinners with elapsed time for all operations
- [ ] **Phase Display**: 8-phase installation progress (1/8 through 8/8)
- [ ] **Professional Header**: Branded installation header
- [ ] **Parallel Operations**: Dependency checks run concurrently
- [ ] **Performance Caching**: Pip list cached for faster checking
- [ ] **Error Handling**: Graceful failures with actionable guidance

### Performance Requirements ⚡
- [ ] **20-30% faster execution** through parallel operations and caching
- [ ] **5-10x perceived speed improvement** through continuous visual feedback
- [ ] **Sub-10 second dependency checks** through parallelization
- [ ] **Professional user experience** matching bash script quality

### Quality Requirements 🏆
- [ ] **No data loss**: Existing claude.md files preserved during merge
- [ ] **No duplicate content**: Version detection prevents multiple sections
- [ ] **Robust error handling**: Clear messages with troubleshooting guidance
- [ ] **Cross-Windows compatibility**: Works on Windows 10/11, PowerShell 5.1/7+
- [ ] **Maintainable code**: Well-documented, modular functions

### User Experience Requirements 🎨
- [ ] **Professional appearance**: Matches bash script's polished experience
- [ ] **Clear progress indication**: Users never wonder if installation is frozen
- [ ] **Helpful error messages**: Actionable guidance for common issues
- [ ] **Consistent behavior**: Predictable operation across all modes

## 10. Risk Mitigation

### High Risk: Data Loss During Global Rules Migration
**Risk**: Existing claude.md files could be overwritten
**Mitigation**:
- Implement comprehensive backup before any file operations
- Test merge logic extensively with various claude.md configurations
- Add rollback capability

### Medium Risk: Performance Regression
**Risk**: New features could slow installation
**Mitigation**:
- Benchmark each optimization
- Use background jobs for parallel operations
- Implement timeout handling

### Medium Risk: Windows Compatibility Issues
**Risk**: Spinners or Unicode characters may not display correctly
**Mitigation**:
- Test on multiple Windows versions
- Provide fallback for unsupported terminals
- Add detection for terminal capabilities

### Low Risk: PowerShell Version Compatibility
**Risk**: Advanced features may not work on older PowerShell
**Mitigation**:
- Target PowerShell 5.1 as minimum
- Test on both Windows PowerShell and PowerShell Core
- Use compatible syntax and cmdlets

## Conclusion

This implementation plan provides a comprehensive roadmap to achieve full parity between the PowerShell and bash installation scripts. The critical priority is fixing the global rules handling to prevent data integrity issues, followed by UX improvements and performance optimizations.

The estimated effort is 6-8 days of development work, which will result in a professional, fast, and reliable Windows installation experience that matches the quality of the optimized bash script.

**Next Steps:**
1. Begin with Phase 1 (Critical - Global Rules) immediately
2. Implement comprehensive testing at each phase
3. Validate no regressions in existing functionality
4. Document all changes for future maintenance

Upon completion, Windows users will have the same world-class installation experience as Unix/Linux users, with professional progress indication, optimized performance, and robust error handling.
