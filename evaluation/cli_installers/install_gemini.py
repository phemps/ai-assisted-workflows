#!/usr/bin/env python3
"""
Gemini CLI Installer

Cross-platform installer for Gemini Code CLI with Google API key configuration.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional
from base_installer import BaseCLIInstaller


class GeminiInstaller(BaseCLIInstaller):
    """Gemini CLI installer with cross-platform support."""

    def __init__(self):
        super().__init__("gemini")
        self.npm_package = "@google/gemini-cli"

    def _additional_install_check(self) -> bool:
        """Gemini-specific installation check."""
        # Check if gemini config exists
        gemini_config = Path.home() / ".gemini"
        return gemini_config.exists()

    def install(self) -> bool:
        """Install Gemini CLI using npm."""
        print("🔧 Installing Gemini CLI...")

        if not self.platform_info["npm_available"]:
            print("❌ npm is required but not available")
            print("   Please install Node.js and npm first")
            return False

        # Install via npm globally
        success = self._run_install_command(
            ["npm", "install", "-g", self.npm_package], "Installing Gemini CLI via npm"
        )

        if not success:
            # Try alternative installation methods
            print("🔄 Trying alternative installation...")

            # Try with @google scope
            success = self._run_install_command(
                ["npm", "install", "-g", "@google/gemini-code"],
                "Installing Gemini CLI via npm (@google scope)",
            )

            if not success:
                # Try local installation
                success = self._run_install_command(
                    ["npm", "install", self.npm_package],
                    "Installing Gemini CLI locally",
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
        """
        Configure Gemini authentication.

        Gemini typically uses environment variables for API keys.
        """
        # Skip auth configuration in OAuth mode
        auth_mode = os.environ.get("EVALUATOR_AUTH_MODE", "apikey")
        if auth_mode == "oauth":
            print("🔐 Skipping auth configuration - OAuth will be handled separately")
            return True

        if not token:
            token = os.environ.get("GEMINI_API_KEY")  # Updated env var name

        if not token:
            print("⚠️  No API key provided for Gemini")
            print("   Gemini will need a Google API key via environment variable")
            return True  # Not necessarily an error

        print("🔐 Configuring Gemini API key...")

        # Basic validation of API key format
        if len(token) < 10:
            print("⚠️  API key seems too short")
            print("   Continuing anyway, but authentication may fail")

        try:
            # Create gemini config directory
            gemini_config_dir = Path.home() / ".gemini"
            gemini_config_dir.mkdir(exist_ok=True)

            # Store configuration info (not the actual key for security)
            config_file = gemini_config_dir / "config.json"
            config = {
                "api_key_configured": True,
                "installation_date": str(Path.ctime(Path.cwd())),
                "auth_method": "environment_variable",
                "supported_env_vars": [
                    "GEMINI_API_KEY",
                    "GOOGLE_API_KEY",
                    "GOOGLE_CLOUD_API_KEY",
                ],
                "note": "API key passed via environment variables at runtime",
            }

            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            # Set restrictive permissions
            if self.platform_info["os"] != "windows":
                config_file.chmod(0o600)

            # Test if we can set the environment variable temporarily
            original_env = os.environ.get("GEMINI_API_KEY")
            try:
                os.environ["GEMINI_API_KEY"] = token
                print("✅ Gemini API key configured successfully")
                print("   Key will be passed via GEMINI_API_KEY environment variable")
            finally:
                # Restore original environment (or remove if it wasn't set)
                if original_env is None:
                    os.environ.pop("GEMINI_API_KEY", None)
                else:
                    os.environ["GEMINI_API_KEY"] = original_env

            return True

        except Exception as e:
            print(f"⚠️  Could not save Gemini configuration: {e}")
            return True  # Not a critical failure

    def verify_installation(self) -> bool:
        """Verify Gemini installation."""
        # Basic version check
        if not super().verify_installation():
            # Try alternative commands
            try:
                # Some tools might use different version flags
                result = self._run_in_container_context(["gemini", "-v"], timeout=10)
                if result.returncode != 0:
                    result = self._run_in_container_context(
                        ["gemini", "--help"], timeout=10
                    )

                if result.returncode == 0:
                    print("✅ Gemini CLI verification successful")
                    return True

            except Exception:
                pass

            print("⚠️  Gemini CLI verification failed")
            return False

        print("✅ Gemini CLI verification successful")
        return True

    def test_api_connection(self, api_key: str) -> bool:
        """Test if the API key works with a simple request."""
        print("🧪 Testing Gemini API connection...")

        try:
            if self.in_container_context:
                # For container context, pass the API key as environment variable via docker exec
                import subprocess

                result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "-e",
                        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/evaluator/.local/bin",
                        "-e",
                        f"GEMINI_API_KEY={api_key}",
                        self.container_name,
                        "gemini",
                        "-p",
                        "Hello",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            else:
                # Set up environment for testing
                env = os.environ.copy()
                env["GEMINI_API_KEY"] = api_key

                # Test with a simple prompt
                result = self.subprocess_manager.run_command(
                    ["gemini", "-p", "Hello"], timeout=30, env=env
                )

            if result.returncode == 0:
                print("✅ API key test successful")
                return True
            else:
                print("⚠️  API key test failed (may be quota/network issue)")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"⚠️  Could not test API key: {e}")
            return False

    def setup_environment_helpers(self) -> bool:
        """Create helper scripts for setting environment variables."""
        print("📝 Creating environment helper scripts...")

        try:
            gemini_config_dir = Path.home() / ".gemini"
            gemini_config_dir.mkdir(exist_ok=True)

            # Create bash helper
            bash_helper = gemini_config_dir / "setup_env.sh"
            bash_content = """#!/bin/bash
# Gemini CLI Environment Setup
# Source this file to set up Gemini environment variables
# Usage: source ~/.gemini/setup_env.sh

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY not set"
    echo "   Export your API key: export GEMINI_API_KEY=your_api_key_here"
else
    echo "✅ GEMINI_API_KEY is configured"
fi
"""

            with open(bash_helper, "w") as f:
                f.write(bash_content)

            if self.platform_info["os"] != "windows":
                bash_helper.chmod(0o755)

            # Create PowerShell helper for Windows
            if self.platform_info["os"] == "windows":
                ps_helper = gemini_config_dir / "setup_env.ps1"
                ps_content = """# Gemini CLI Environment Setup
# Run this script to set up Gemini environment variables
# Usage: . ~/.gemini/setup_env.ps1

if (-not $env:GEMINI_API_KEY) {
    Write-Host "⚠️  GEMINI_API_KEY not set" -ForegroundColor Yellow
    Write-Host "   Set your API key: `$env:GEMINI_API_KEY = 'your_api_key_here'" -ForegroundColor Yellow
} else {
    Write-Host "✅ GEMINI_API_KEY is configured" -ForegroundColor Green
}
"""

                with open(ps_helper, "w") as f:
                    f.write(ps_content)

            print("✅ Environment helper scripts created")
            return True

        except Exception as e:
            print(f"⚠️  Could not create helper scripts: {e}")
            return False


def main():
    """Main installer entry point."""
    installer = GeminiInstaller()

    # Get API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")

    # Install with authentication
    success = installer.install_with_auth(api_key)

    if success:
        # Create environment helper scripts
        installer.setup_environment_helpers()

        # Optionally test the API key
        if api_key and len(sys.argv) > 1 and sys.argv[1] == "--test-api":
            installer.test_api_connection(api_key)

    if success:
        print("🎉 Gemini CLI installation and configuration completed!")
        print("💡 Remember to set GEMINI_API_KEY environment variable")
        print(f"   Helper scripts created in {Path.home() / '.gemini'}")
        sys.exit(0)
    else:
        print("❌ Gemini CLI installation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
