# PowerShell Test Helper Functions
# Utility functions for testing the PowerShell installer

# Test environment configuration
$script:TestConfig = @{
    DefaultTimeout = 60  # seconds
    MaxRetries = 3
    TempPrefix = "ai-workflows-test"
    LogLevel = "INFO"
}

# Mock objects for testing
$script:MockResults = @{}

function New-TestEnvironment {
    param(
        [string]$Name,
        [string]$BaseDir = $env:TEMP
    )

    $testDir = Join-Path $BaseDir "$($script:TestConfig.TempPrefix)-$Name-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

    if (-not (Test-Path $testDir)) {
        New-Item -ItemType Directory -Path $testDir -Force | Out-Null
    }

    return $testDir
}

function Remove-TestEnvironment {
    param([string]$TestDir)

    if (Test-Path $TestDir) {
        try {
            Remove-Item -Path $TestDir -Recurse -Force -ErrorAction Stop
            return $true
        } catch {
            Write-Warning "Failed to remove test environment $TestDir : $_"
            return $false
        }
    }
    return $true
}

function New-MockClaudeInstallation {
    param(
        [string]$Path,
        [hashtable]$CustomFiles = @{},
        [string[]]$CustomCommands = @(),
        [string]$ClaudeContent = "# Default claude.md content"
    )

    $claudeDir = Join-Path $Path ".claude"

    # Create directory structure
    $dirs = @("commands", "scripts", "agents", "templates", "rules")
    foreach ($dir in $dirs) {
        $dirPath = Join-Path $claudeDir $dir
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
    }

    # Create claude.md
    $claudeFile = Join-Path $claudeDir "claude.md"
    $ClaudeContent | Out-File -FilePath $claudeFile -Encoding UTF8

    # Create CLAUDE.md
    $projectClaudeFile = Join-Path $claudeDir "CLAUDE.md"
    "# Project Documentation`nThis is the main project documentation." | Out-File -FilePath $projectClaudeFile -Encoding UTF8

    # Create custom commands
    foreach ($cmd in $CustomCommands) {
        $cmdFile = Join-Path $claudeDir "commands" "$cmd.md"
        "# $cmd Command`nCustom command: $cmd" | Out-File -FilePath $cmdFile -Encoding UTF8
    }

    # Create custom files
    foreach ($file in $CustomFiles.Keys) {
        $filePath = Join-Path $claudeDir $file
        $fileDir = Split-Path $filePath -Parent
        if (-not (Test-Path $fileDir)) {
            New-Item -ItemType Directory -Path $fileDir -Force | Out-Null
        }
        $CustomFiles[$file] | Out-File -FilePath $filePath -Encoding UTF8
    }

    # Create installation log
    $logFile = Join-Path $claudeDir "installation-log.txt"
    @"
AI-Assisted Workflows Installation Log
=====================================
Installation Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Installer Version: 1.0.0 (Test Mock)
Target Path: $claudeDir
Install Mode: mock
MCP Tools: Skipped
Python Dependencies: Skipped
"@ | Out-File -FilePath $logFile -Encoding UTF8

    return $claudeDir
}

function Test-InstallationIntegrity {
    param(
        [string]$ClaudePath,
        [string[]]$RequiredFiles = @("CLAUDE.md", "commands", "scripts", "installation-log.txt"),
        [string[]]$RequiredCommands = @()
    )

    $issues = @()

    # Check if .claude directory exists
    if (-not (Test-Path $ClaudePath)) {
        $issues += "Main .claude directory not found: $ClaudePath"
        return @{ Valid = $false; Issues = $issues }
    }

    # Check required files/directories
    foreach ($file in $RequiredFiles) {
        $filePath = Join-Path $ClaudePath $file
        if (-not (Test-Path $filePath)) {
            $issues += "Required file/directory missing: $file"
        }
    }

    # Check required commands
    foreach ($cmd in $RequiredCommands) {
        $cmdFile = Join-Path $ClaudePath "commands" "$cmd.md"
        if (-not (Test-Path $cmdFile)) {
            $issues += "Required command missing: $cmd"
        }
    }

    # Check claude.md is not empty
    $claudeFile = Join-Path $ClaudePath "claude.md"
    if (Test-Path $claudeFile) {
        $content = Get-Content $claudeFile -Raw -ErrorAction SilentlyContinue
        if ([string]::IsNullOrWhiteSpace($content)) {
            $issues += "claude.md exists but is empty"
        }
    }

    return @{
        Valid = ($issues.Count -eq 0)
        Issues = $issues
        Path = $ClaudePath
    }
}

function Measure-InstallationPerformance {
    param(
        [scriptblock]$InstallationScript,
        [int]$Iterations = 3,
        [int]$TimeoutSeconds = 120
    )

    $results = @()

    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $startTime = Get-Date
            $startMemory = [System.GC]::GetTotalMemory($false)

            # Execute installation with timeout
            $job = Start-Job -ScriptBlock $InstallationScript
            $completed = Wait-Job $job -Timeout $TimeoutSeconds

            if ($completed) {
                $endTime = Get-Date
                $endMemory = [System.GC]::GetTotalMemory($true)

                $duration = ($endTime - $startTime).TotalSeconds
                $memoryUsed = $endMemory - $startMemory

                $results += @{
                    Iteration = $i
                    Duration = $duration
                    MemoryUsed = $memoryUsed
                    Success = $true
                    Error = $null
                }

                Receive-Job $job | Out-Null
            } else {
                Stop-Job $job
                $results += @{
                    Iteration = $i
                    Duration = $TimeoutSeconds
                    MemoryUsed = 0
                    Success = $false
                    Error = "Timeout after $TimeoutSeconds seconds"
                }
            }

            Remove-Job $job

        } catch {
            $results += @{
                Iteration = $i
                Duration = 0
                MemoryUsed = 0
                Success = $false
                Error = $_.Exception.Message
            }
        }
    }

    # Calculate statistics
    $successfulRuns = $results | Where-Object { $_.Success }

    if ($successfulRuns.Count -gt 0) {
        $avgDuration = ($successfulRuns | Measure-Object -Property Duration -Average).Average
        $minDuration = ($successfulRuns | Measure-Object -Property Duration -Minimum).Minimum
        $maxDuration = ($successfulRuns | Measure-Object -Property Duration -Maximum).Maximum
        $avgMemory = ($successfulRuns | Measure-Object -Property MemoryUsed -Average).Average
    } else {
        $avgDuration = $minDuration = $maxDuration = $avgMemory = 0
    }

    return @{
        TotalIterations = $Iterations
        SuccessfulRuns = $successfulRuns.Count
        FailedRuns = $Iterations - $successfulRuns.Count
        AverageDuration = $avgDuration
        MinimumDuration = $minDuration
        MaximumDuration = $maxDuration
        AverageMemoryUsage = $avgMemory
        Results = $results
    }
}

function Test-FileContent {
    param(
        [string]$FilePath,
        [string[]]$ExpectedContent = @(),
        [string[]]$UnexpectedContent = @(),
        [switch]$CaseSensitive
    )

    if (-not (Test-Path $FilePath)) {
        return @{
            Valid = $false
            Issues = @("File not found: $FilePath")
        }
    }

    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    $issues = @()

    if ([string]::IsNullOrWhiteSpace($content)) {
        $issues += "File is empty: $FilePath"
        return @{ Valid = $false; Issues = $issues }
    }

    # Check expected content
    foreach ($expected in $ExpectedContent) {
        $found = if ($CaseSensitive) {
            $content.Contains($expected)
        } else {
            $content.ToLower().Contains($expected.ToLower())
        }

        if (-not $found) {
            $issues += "Expected content not found: '$expected'"
        }
    }

    # Check unexpected content
    foreach ($unexpected in $UnexpectedContent) {
        $found = if ($CaseSensitive) {
            $content.Contains($unexpected)
        } else {
            $content.ToLower().Contains($unexpected.ToLower())
        }

        if ($found) {
            $issues += "Unexpected content found: '$unexpected'"
        }
    }

    return @{
        Valid = ($issues.Count -eq 0)
        Issues = $issues
        ContentLength = $content.Length
    }
}

function Invoke-WithRetry {
    param(
        [scriptblock]$ScriptBlock,
        [int]$MaxRetries = $script:TestConfig.MaxRetries,
        [int]$DelaySeconds = 1,
        [string]$Description = "Operation"
    )

    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            $result = & $ScriptBlock
            return @{
                Success = $true
                Result = $result
                Attempts = $attempt
                Error = $null
            }
        } catch {
            if ($attempt -eq $MaxRetries) {
                return @{
                    Success = $false
                    Result = $null
                    Attempts = $attempt
                    Error = $_.Exception.Message
                }
            }

            Write-Warning "$Description failed on attempt $attempt/$MaxRetries : $_"
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

function New-MockPowerShellEnvironment {
    param(
        [hashtable]$EnvironmentVariables = @{},
        [string[]]$AvailableCommands = @("python", "pip", "node", "npm", "claude"),
        [hashtable]$CommandOutputs = @{}
    )

    # Store original environment
    $originalEnv = @{}
    foreach ($var in $EnvironmentVariables.Keys) {
        $originalEnv[$var] = [Environment]::GetEnvironmentVariable($var, "Process")
        [Environment]::SetEnvironmentVariable($var, $EnvironmentVariables[$var], "Process")
    }

    # Create mock commands if needed
    $mockDir = Join-Path $env:TEMP "mock-commands-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    New-Item -ItemType Directory -Path $mockDir -Force | Out-Null

    foreach ($cmd in $AvailableCommands) {
        $mockScript = Join-Path $mockDir "$cmd.bat"
        $output = if ($CommandOutputs.ContainsKey($cmd)) { $CommandOutputs[$cmd] } else { "$cmd version 1.0.0" }

        @"
@echo off
echo $output
exit /b 0
"@ | Out-File -FilePath $mockScript -Encoding ASCII
    }

    # Add mock directory to PATH
    $originalPath = $env:PATH
    $env:PATH = "$mockDir;$env:PATH"

    return @{
        MockDirectory = $mockDir
        OriginalEnvironment = $originalEnv
        OriginalPath = $originalPath
        Cleanup = {
            # Restore environment
            foreach ($var in $EnvironmentVariables.Keys) {
                if ($originalEnv[$var]) {
                    [Environment]::SetEnvironmentVariable($var, $originalEnv[$var], "Process")
                } else {
                    [Environment]::SetEnvironmentVariable($var, $null, "Process")
                }
            }

            # Restore PATH
            $env:PATH = $originalPath

            # Remove mock directory
            if (Test-Path $mockDir) {
                Remove-Item -Path $mockDir -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

function Test-PowerShellCompatibility {
    param([string]$ScriptPath)

    $results = @{
        WindowsPowerShell = $null
        PowerShellCore = $null
        SyntaxValid = $false
        CompatibilityIssues = @()
    }

    # Test syntax
    try {
        $content = Get-Content $ScriptPath -Raw
        $errors = $null
        [System.Management.Automation.PSParser]::Tokenize($content, [ref]$errors) | Out-Null
        $results.SyntaxValid = ($errors.Count -eq 0)
        if ($errors.Count -gt 0) {
            $results.CompatibilityIssues += $errors | ForEach-Object { "Syntax: $($_.Message)" }
        }
    } catch {
        $results.CompatibilityIssues += "Failed to parse script: $_"
    }

    # Test Windows PowerShell if available
    try {
        if (Get-Command powershell -ErrorAction SilentlyContinue) {
            $testResult = powershell -Command "& { try { . '$ScriptPath' -Help } catch { `$_.Exception.Message } }" 2>&1
            $results.WindowsPowerShell = @{
                Available = $true
                TestPassed = ($testResult -like "*AI-Assisted Workflows*")
                Output = $testResult
            }
        } else {
            $results.WindowsPowerShell = @{ Available = $false }
        }
    } catch {
        $results.WindowsPowerShell = @{
            Available = $true
            TestPassed = $false
            Error = $_.Exception.Message
        }
    }

    # Test PowerShell Core if available
    try {
        if (Get-Command pwsh -ErrorAction SilentlyContinue) {
            $testResult = pwsh -Command "& { try { . '$ScriptPath' -Help } catch { `$_.Exception.Message } }" 2>&1
            $results.PowerShellCore = @{
                Available = $true
                TestPassed = ($testResult -like "*AI-Assisted Workflows*")
                Output = $testResult
            }
        } else {
            $results.PowerShellCore = @{ Available = $false }
        }
    } catch {
        $results.PowerShellCore = @{
            Available = $true
            TestPassed = $false
            Error = $_.Exception.Message
        }
    }

    return $results
}

# Export functions that should be available to test scripts
Export-ModuleMember -Function *
