#!/usr/bin/env python3
"""
Claude CLI Installer

Cross-platform installer for Claude Code CLI with secure authentication.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from base_installer import BaseCLIInstaller


class ClaudeInstaller(BaseCLIInstaller):
    """Claude CLI installer with cross-platform support."""

    def __init__(self):
        super().__init__("claude")
        self.npm_package = "@anthropic-ai/claude-code@latest"

    def _additional_install_check(self) -> bool:
        """Claude-specific installation check."""
        # Check if claude config exists
        claude_config = Path.home() / ".claude"
        return claude_config.exists()

    def install(self) -> bool:
        """Install Claude CLI using npm."""
        print("🔧 Installing Claude CLI...")

        if not self.platform_info["npm_available"]:
            print("❌ npm is required but not available")
            print("   Please install Node.js and npm first")
            return False

        # Install via npm globally
        success = self._run_install_command(
            ["npm", "install", "-g", self.npm_package], "Installing Claude CLI via npm"
        )

        if not success:
            # Try alternative installation methods
            print("🔄 Trying alternative installation...")

            # Try installing without -g flag (user installation)
            success = self._run_install_command(
                ["npm", "install", self.npm_package],
                "Installing Claude CLI locally",
                cwd=str(Path.home()),
            )

            if success:
                # Update PATH to include local node_modules
                local_bin = Path.home() / "node_modules" / ".bin"
                if local_bin.exists():
                    current_path = os.environ.get("PATH", "")
                    os.environ["PATH"] = f"{local_bin}:{current_path}"

        return success

    def configure_auth(self, token: Optional[str] = None) -> bool:
        """Configure Claude authentication using setup-token command."""
        if not token:
            token = os.environ.get("CLAUDE_AUTH_TOKEN")

        if not token:
            print("⚠️  No authentication token provided for Claude")
            return True  # Not necessarily an error

        print("🔐 Configuring Claude authentication...")

        try:
            # Use claude setup-token command
            process = subprocess.Popen(
                ["claude", "setup-token"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Send token followed by newline
            stdout, stderr = process.communicate(input=f"{token}\n", timeout=30)

            if process.returncode == 0:
                print("✅ Claude authentication configured successfully")
                return True
            else:
                print("❌ Claude authentication failed:")
                print(f"   Exit code: {process.returncode}")
                if stderr:
                    print(f"   Error: {stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Claude authentication timed out")
            process.kill()
            return False
        except Exception as e:
            print(f"❌ Claude authentication failed: {e}")
            return False

    def verify_installation(self) -> bool:
        """Verify Claude installation with enhanced checks."""
        # Basic version check
        if not super().verify_installation():
            # Try alternative commands
            try:
                # Some tools might use different version flags
                result = self._run_in_container_context(["claude", "-v"], timeout=10)
                if result.returncode != 0:
                    result = self._run_in_container_context(
                        ["claude", "--help"], timeout=10
                    )

                if result.returncode == 0:
                    print("✅ Claude CLI verification successful")
                    return True

            except Exception:
                pass

            print("⚠️  Claude CLI verification failed")
            return False

        print("✅ Claude CLI verification successful")
        return True


def main():
    """Main installer entry point."""
    installer = ClaudeInstaller()

    # Get token from environment
    token = os.environ.get("CLAUDE_AUTH_TOKEN")

    # Install with authentication
    success = installer.install_with_auth(token)

    if success:
        print("🎉 Claude CLI installation and configuration completed!")
        sys.exit(0)
    else:
        print("❌ Claude CLI installation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
