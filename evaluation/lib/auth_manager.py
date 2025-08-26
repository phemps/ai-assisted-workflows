#!/usr/bin/env python3
"""
Authentication Management for CLI Evaluation System

Handles OAuth and API key authentication for different CLI tools.
"""

import subprocess
import time
from abc import ABC, abstractmethod
from typing import Optional


class BaseAuthenticator(ABC):
    """Base class for CLI authentication methods."""

    def __init__(self, cli_tool: str, container_name: str):
        self.cli_tool = cli_tool
        self.container_name = container_name

    @abstractmethod
    def authenticate(self) -> bool:
        """Perform authentication. Returns True if successful."""
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if already authenticated. Returns True if valid credentials exist."""
        pass


class OAuthAuthenticator(BaseAuthenticator):
    """Interactive OAuth authentication for CLI tools."""

    # OAuth instructions for each CLI tool
    OAUTH_INSTRUCTIONS = {
        "claude": {
            "init_command": "claude",
            "auth_method": 'Choose "Claude app (requires Max subscription)"',
            "steps": [
                "1. Run: claude",
                '2. Choose "Claude app (requires Max subscription)" when prompted',
                "3. Copy the URL displayed and open it in your browser",
                "4. Complete authentication on the Claude website",
                "5. Copy the code from the website back to the terminal",
                "6. Approve trust for the working directory when prompted",
            ],
            "test_command": 'claude -p "hello world" --permission-mode bypassPermissions',
        },
        "qwen": {
            "init_command": "qwen /auth",
            "auth_method": "OAuth authentication flow",
            "steps": [
                "1. Run: qwen /auth",
                "2. Follow the OAuth authentication prompts",
                "3. Complete authentication in your browser",
                "4. Return to terminal once complete",
            ],
            "test_command": 'qwen -p "hello world" -y',
        },
        "gemini": {
            "init_command": "gemini /auth",
            "auth_method": "Google account authentication",
            "steps": [
                "1. Run: gemini /auth",
                "2. Follow the Google authentication prompts",
                "3. Complete authentication in your browser",
                "4. Return to terminal once complete",
            ],
            "test_command": 'gemini -p "hello world" --yolo',
        },
    }

    # OAuth credential file locations for each CLI tool
    OAUTH_CREDENTIAL_PATHS = {
        "claude": "/home/evaluator/.claude/.credentials.json",
        "qwen": "/home/evaluator/.qwen/oauth_creds.json",
        "gemini": "/home/evaluator/.gemini/google_accounts.json",
    }

    def __init__(self, cli_tool: str, container_name: str):
        super().__init__(cli_tool, container_name)
        if cli_tool not in self.OAUTH_INSTRUCTIONS:
            raise ValueError(f"OAuth not supported for CLI tool: {cli_tool}")
        self.instructions = self.OAUTH_INSTRUCTIONS[cli_tool]

    def authenticate(self) -> bool:
        """Guide user through interactive OAuth authentication."""
        print(f"🔐 Starting OAuth authentication for {self.cli_tool}...")

        # Check if already authenticated
        if self.is_authenticated():
            print(f"✅ {self.cli_tool} already authenticated via OAuth")
            return True

        # Display interactive instructions
        self._display_instructions()

        # Wait for user to complete authentication
        self._wait_for_completion()

        # Verify authentication worked
        if self.is_authenticated():
            print(f"✅ OAuth authentication successful for {self.cli_tool}")
            self._mark_oauth_complete()
            return True
        else:
            print(f"❌ OAuth authentication verification failed for {self.cli_tool}")
            return False

    def is_authenticated(self) -> bool:
        """Check if OAuth credentials exist and are valid."""
        # Check for OAuth completion flag
        flag_check = [
            "docker",
            "exec",
            self.container_name,
            "test",
            "-f",
            "/home/evaluator/.oauth_complete",
        ]
        try:
            if (
                subprocess.run(flag_check, capture_output=True, timeout=5).returncode
                == 0
            ):
                return True
        except subprocess.TimeoutExpired:
            pass

        # Check for tool-specific credential files
        if self.cli_tool in self.OAUTH_CREDENTIAL_PATHS:
            cred_path = self.OAUTH_CREDENTIAL_PATHS[self.cli_tool]
            check_cmd = ["docker", "exec", self.container_name, "test", "-f", cred_path]
            try:
                return (
                    subprocess.run(check_cmd, capture_output=True, timeout=5).returncode
                    == 0
                )
            except subprocess.TimeoutExpired:
                return False

        return False

    def _display_instructions(self):
        """Display step-by-step OAuth instructions to the user."""
        print("\n" + "=" * 70)
        print(f"🔐 OAUTH SETUP FOR {self.cli_tool.upper()}")
        print("=" * 70)
        print("\nPlease complete the following steps:")
        print("\n📱 STEP 1: Start Interactive Session")
        print("─" * 40)
        print(f"docker start {self.container_name}")
        print(f"docker exec -it {self.container_name} /bin/bash")

        print("\n🔑 STEP 2: Complete Authentication")
        print("─" * 40)
        for step in self.instructions["steps"]:
            print(f"   {step}")

        print("\n✅ STEP 3: Test Authentication")
        print("─" * 40)
        print(f"   {self.instructions['test_command']}")

        print("\n💡 STEP 4: Return Here")
        print("─" * 40)
        print("   Once authentication is complete, return to this terminal")
        print("   and press Enter to continue...")
        print("\n" + "=" * 70)

    def _wait_for_completion(self):
        """Wait for user to complete the OAuth flow."""
        input("\n⏳ Press Enter when OAuth authentication is complete...")

        # Give user a moment to return to this terminal
        print("🔍 Verifying authentication...")
        time.sleep(1)

    def _mark_oauth_complete(self):
        """Create flag file to indicate OAuth is complete."""
        cmd = [
            "docker",
            "exec",
            self.container_name,
            "touch",
            "/home/evaluator/.oauth_complete",
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            print("⚠️  Warning: Timeout marking OAuth as complete")

    def verify_with_test_command(self) -> bool:
        """Verify OAuth authentication by running a test command."""
        test_cmd = self.instructions["test_command"]

        docker_cmd = [
            "docker",
            "exec",
            "-e",
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/evaluator/.local/bin",
            self.container_name,
        ] + test_cmd.split()

        try:
            result = subprocess.run(
                docker_cmd, capture_output=True, text=True, timeout=30
            )

            # Check for common error patterns
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

            # If exit code is 0 and no error patterns, assume success
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("⚠️  Test command timed out")
            return False
        except Exception as e:
            print(f"⚠️  Error running test command: {e}")
            return False


class APIKeyAuthenticator(BaseAuthenticator):
    """API key-based authentication for CLI tools."""

    def __init__(self, cli_tool: str, container_name: str, api_key: str):
        super().__init__(cli_tool, container_name)
        self.api_key = api_key

    def authenticate(self) -> bool:
        """Configure API key authentication."""
        if not self.api_key:
            print(f"⚠️  No API key provided for {self.cli_tool}")
            return False

        print(f"🔑 Configuring API key authentication for {self.cli_tool}...")

        # API key authentication is handled during execution
        # No pre-setup required for most CLI tools
        return True

    def is_authenticated(self) -> bool:
        """Check if API key is present."""
        return bool(self.api_key)


class AuthManager:
    """Main authentication manager that coordinates different auth methods."""

    def __init__(self, cli_tool: str, container_name: str):
        self.cli_tool = cli_tool
        self.container_name = container_name

    def get_authenticator(
        self, auth_mode: str, api_key: Optional[str] = None
    ) -> BaseAuthenticator:
        """Factory method to get the appropriate authenticator."""
        if auth_mode == "oauth":
            return OAuthAuthenticator(self.cli_tool, self.container_name)
        elif auth_mode == "apikey":
            if not api_key:
                raise ValueError("API key required for apikey authentication mode")
            return APIKeyAuthenticator(self.cli_tool, self.container_name, api_key)
        else:
            raise ValueError(f"Unknown authentication mode: {auth_mode}")

    def authenticate(self, auth_mode: str, api_key: Optional[str] = None) -> bool:
        """Perform authentication using the specified mode."""
        authenticator = self.get_authenticator(auth_mode, api_key)
        return authenticator.authenticate()

    def is_authenticated(self, auth_mode: str, api_key: Optional[str] = None) -> bool:
        """Check if authentication is valid for the specified mode."""
        authenticator = self.get_authenticator(auth_mode, api_key)
        return authenticator.is_authenticated()
