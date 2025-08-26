#!/usr/bin/env python3
"""
Test Execution Engine for CLI Evaluation System

Handles CLI command execution, output capture, and streaming.
"""

import subprocess
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class CLIToolConfig:
    """Configuration for different CLI tools."""

    name: str
    install_method: str  # 'script', 'npm', 'pip'
    auth_method: str  # 'setup-token', 'cli-arg', 'env-var', 'oauth'
    auth_key: str
    execution_pattern: str
    oauth_execution_pattern: Optional[str] = None  # Pattern to use after OAuth auth
    oauth_command: Optional[List[str]] = None  # Command to initiate OAuth
    requires_token: bool = True


class ExecutionEngine:
    """Handles CLI test execution with different authentication modes."""

    CLI_CONFIGS = {
        "claude": CLIToolConfig(
            name="claude",
            install_method="npm",
            auth_method="env-var",
            auth_key="CLAUDE_AUTH_TOKEN",
            execution_pattern='claude -p "{prompt} {plan_file}" --permission-mode bypassPermissions',
            oauth_execution_pattern='claude -p "{prompt} {plan_file}" --permission-mode bypassPermissions',
            oauth_command=["claude", "-p", "/login"],
            requires_token=True,
        ),
        "qwen": CLIToolConfig(
            name="qwen",
            install_method="npm",
            auth_method="cli-arg",
            auth_key="--openai-api-key",
            execution_pattern='cat {plan_file} | qwen -p "{prompt}" --openai-api-key "{api_key}" -y',
            oauth_execution_pattern='cat {plan_file} | qwen -p "{prompt}" -y',
            oauth_command=["qwen", "/auth"],
            requires_token=True,
        ),
        "gemini": CLIToolConfig(
            name="gemini",
            install_method="npm",
            auth_method="env-var",
            auth_key="GEMINI_API_KEY",
            execution_pattern='cat {plan_file} | gemini -p "{prompt}" --yolo',
            oauth_execution_pattern='cat {plan_file} | gemini -p "{prompt}" --yolo',
            oauth_command=["gemini", "/auth"],
            requires_token=True,
        ),
    }

    def __init__(self, cli_tool: str, docker_manager, auth_mode: str = "apikey"):
        self.cli_tool = cli_tool
        self.docker_manager = docker_manager
        self.auth_mode = auth_mode

        if cli_tool not in self.CLI_CONFIGS:
            raise ValueError(f"Unsupported CLI tool: {cli_tool}")

        self.tool_config = self.CLI_CONFIGS[cli_tool]

    def execute_test(
        self,
        prompt: str,
        scenario: Dict[str, Any],
        api_key: Optional[str] = None,
        verbose: bool = False,
    ) -> subprocess.CompletedProcess:
        """Execute the CLI test with appropriate authentication."""
        plan_file_container = f"/workspace/scenarios/{scenario['plan_file']}"

        # Build command using appropriate execution pattern
        if self.auth_mode == "oauth" and self.tool_config.oauth_execution_pattern:
            execution_pattern = self.tool_config.oauth_execution_pattern
        else:
            execution_pattern = self.tool_config.execution_pattern

        # Interpolate values into the pattern
        cli_cmd = execution_pattern.format(
            prompt=prompt, plan_file=plan_file_container, api_key=api_key or ""
        )

        print(f"⚡ Executing: {cli_cmd}")

        # Prepare environment
        environment = self._build_environment(api_key)

        # Execute with appropriate output handling
        if verbose:
            return self._execute_with_streaming(cli_cmd, environment, scenario)
        else:
            return self._execute_standard(cli_cmd, environment, scenario)

    def _build_environment(self, api_key: Optional[str] = None) -> Dict[str, str]:
        """Build environment variables for CLI execution."""
        # Container PATH for proper CLI tool resolution
        container_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/evaluator/.local/bin"

        environment = {"PATH": container_path}

        # Only add API key for non-OAuth modes
        if (
            self.auth_mode != "oauth"
            and self.tool_config.auth_method == "env-var"
            and api_key
        ):
            environment[self.tool_config.auth_key] = api_key

        return environment

    def _execute_standard(
        self, cli_cmd: str, environment: Dict[str, str], scenario: Dict[str, Any]
    ) -> subprocess.CompletedProcess:
        """Execute command with standard output capture."""
        max_duration = scenario.get("max_duration_minutes", 30) * 60

        # Build shell command
        shell_cmd = ["bash", "-c", cli_cmd]

        return self.docker_manager.execute_command(
            shell_cmd, environment=environment, timeout=max_duration
        )

    def _execute_with_streaming(
        self, cli_cmd: str, environment: Dict[str, str], scenario: Dict[str, Any]
    ) -> subprocess.CompletedProcess:
        """Execute command with real-time output streaming."""
        print("📺 Verbose mode: streaming output with capture...")

        max_duration = scenario.get("max_duration_minutes", 30) * 60
        shell_cmd = ["bash", "-c", cli_cmd]

        # Use streaming execution
        process = self.docker_manager.execute_with_streaming(
            shell_cmd, environment=environment
        )

        # Capture output while displaying
        stdout_lines = []
        stderr_lines = []

        try:
            while True:
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()

                if stdout_line:
                    print(stdout_line.rstrip())
                    stdout_lines.append(stdout_line)

                if stderr_line:
                    print(f"STDERR: {stderr_line.rstrip()}")
                    stderr_lines.append(stderr_line)

                # Check if process has terminated
                if process.poll() is not None and not stdout_line and not stderr_line:
                    break

            # Wait for process to complete
            process.wait(timeout=max_duration)

        except subprocess.TimeoutExpired:
            process.kill()
            stdout_lines.append("Process terminated due to timeout")
            stderr_lines.append(f"Timeout after {max_duration} seconds")

        # Create a CompletedProcess-like result
        return subprocess.CompletedProcess(
            args=shell_cmd,
            returncode=process.returncode or 124,
            stdout="".join(stdout_lines),
            stderr="".join(stderr_lines),
        )

    def test_authentication(self) -> bool:
        """Test if the CLI tool is properly authenticated."""
        test_commands = {
            "claude": 'claude -p "test" --permission-mode bypassPermissions',
            "qwen": 'qwen -p "test" -y',
            "gemini": 'gemini -p "test" --yolo',
        }

        if self.cli_tool not in test_commands:
            return False

        test_cmd = test_commands[self.cli_tool]
        environment = self._build_environment()

        result = self.docker_manager.execute_command(
            ["bash", "-c", test_cmd], environment=environment, timeout=30
        )

        # Check for common authentication errors
        error_patterns = [
            "Invalid API key",
            "Please run /login",
            "Authentication required",
            "401",
            "Unauthorized",
        ]

        output = result.stdout + result.stderr
        for pattern in error_patterns:
            if pattern in output:
                return False

        return result.returncode == 0

    def get_tool_config(self) -> CLIToolConfig:
        """Get the configuration for the current CLI tool."""
        return self.tool_config


class CLIInstallationManager:
    """Manages CLI tool installation in containers."""

    def __init__(self, docker_manager):
        self.docker_manager = docker_manager

    def is_cli_installed(self, cli_tool: str) -> bool:
        """Check if CLI tool is installed in the container."""
        # Try to run the CLI tool version command
        result = self.docker_manager.execute_command(
            [cli_tool, "--version"], timeout=10
        )
        return result.returncode == 0

    def install_cli(
        self, cli_tool: str, auth_mode: str = "apikey", api_key: Optional[str] = None
    ) -> bool:
        """Install CLI tool in the container."""
        print(f"📥 Installing {cli_tool}...")

        # Use installer scripts
        install_script = f"install_{cli_tool}.py"

        # Container PATH for proper execution
        container_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/evaluator/.local/bin"

        # Build environment for installer
        environment = {
            "PATH": container_path,
            "EVALUATOR_CONTAINER_NAME": self.docker_manager.container_name,
            "EVALUATOR_AUTH_MODE": auth_mode,
        }

        # Add API key if provided and not OAuth mode
        if auth_mode != "oauth" and api_key:
            env_key_mapping = {
                "claude": "CLAUDE_API_KEY",
                "qwen": "QWEN_API_KEY",
                "gemini": "GEMINI_API_KEY",
            }

            if cli_tool in env_key_mapping:
                environment[env_key_mapping[cli_tool]] = api_key

        # Run installer
        result = self.docker_manager.execute_command(
            ["python3", f"/workspace/installers/{install_script}"],
            environment=environment,
            timeout=300,  # 5 minutes for installation
        )

        if result.returncode == 0:
            print(f"✅ {cli_tool} installation completed")
            return True
        else:
            print(f"❌ {cli_tool} installation failed:")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
