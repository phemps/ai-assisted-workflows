#!/usr/bin/env python3
"""
Qwen CLI Installer

Cross-platform installer for Qwen Code CLI with OpenAI API key configuration.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional
from base_installer import BaseCLIInstaller


class QwenInstaller(BaseCLIInstaller):
    """Qwen CLI installer with cross-platform support."""

    def __init__(self):
        super().__init__("qwen")
        self.npm_package = "@qwen-code/qwen-code@latest"

    def _additional_install_check(self) -> bool:
        """Qwen-specific installation check."""
        # Check if qwen config exists
        qwen_config = Path.home() / ".qwen"
        return qwen_config.exists()

    def install(self) -> bool:
        """Install Qwen CLI using npm."""
        print("🔧 Installing Qwen CLI...")

        if not self.platform_info["npm_available"]:
            print("❌ npm is required but not available")
            print("   Please install Node.js and npm first")
            return False

        # Install via npm globally
        success = self._run_install_command(
            ["npm", "install", "-g", self.npm_package], "Installing Qwen CLI via npm"
        )

        if not success:
            # Try alternative installation methods
            print("🔄 Trying alternative installation...")

            # Try installing without -g flag (user installation)
            success = self._run_install_command(
                ["npm", "install", self.npm_package],
                "Installing Qwen CLI locally",
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
        Configure Qwen authentication.

        Note: Qwen uses OpenAI API key passed at runtime via --openai-api-key flag,
        not during installation. This method stores the key for later use.
        """
        if not token:
            token = os.environ.get("QWEN_OAUTH_TOKEN")

        if not token:
            print("⚠️  No API key provided for Qwen")
            print("   Qwen will need an OpenAI API key at runtime")
            return True  # Not necessarily an error

        print("🔐 Configuring Qwen API key...")

        # Validate OpenAI API key format
        if not token.startswith("sk-") or len(token) < 40:
            print("⚠️  API key doesn't match OpenAI format (sk-...)")
            print("   Continuing anyway, but authentication may fail")

        try:
            # Create qwen config directory
            qwen_config_dir = Path.home() / ".qwen"
            qwen_config_dir.mkdir(exist_ok=True)

            # Store API key in config file (for reference only, not used by qwen)
            config_file = qwen_config_dir / "config.json"
            config = {
                "api_key_configured": True,
                "installation_date": str(Path.ctime(Path.cwd())),
                "note": "API key passed at runtime via --openai-api-key flag",
            }

            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            # Set restrictive permissions
            if self.platform_info["os"] != "windows":
                config_file.chmod(0o600)

            print("✅ Qwen configuration saved")
            print("   API key will be passed at runtime via --openai-api-key flag")
            return True

        except Exception as e:
            print(f"⚠️  Could not save Qwen configuration: {e}")
            return True  # Not a critical failure

    def verify_installation(self) -> bool:
        """Verify Qwen installation."""
        # Basic version check
        if not super().verify_installation():
            # Try alternative commands
            try:
                # Some tools might use different version flags
                result = self._run_in_container_context(["qwen", "-v"], timeout=10)
                if result.returncode != 0:
                    result = self._run_in_container_context(
                        ["qwen", "--help"], timeout=10
                    )

                if result.returncode == 0:
                    print("✅ Qwen CLI verification successful")
                    return True

            except Exception:
                pass

            print("⚠️  Qwen CLI verification failed")
            return False

        print("✅ Qwen CLI verification successful")
        return True

    def test_api_connection(self, api_key: str) -> bool:
        """Test if the API key works with a simple request."""
        print("🧪 Testing API key connection...")

        try:
            # Test with a simple prompt
            result = self._run_in_container_context(
                ["qwen", "-p", "Hello", "--openai-api-key", api_key], timeout=30
            )

            if result.returncode == 0:
                print("✅ API key test successful")
                return True
            else:
                print("⚠️  API key test failed (may be quota/network issue)")
                return False

        except Exception as e:
            print(f"⚠️  Could not test API key: {e}")
            return False


def main():
    """Main installer entry point."""
    installer = QwenInstaller()

    # Get API key from environment
    api_key = os.environ.get("QWEN_OAUTH_TOKEN")

    # Install with authentication
    success = installer.install_with_auth(api_key)

    if success and api_key:
        # Optionally test the API key
        if len(sys.argv) > 1 and sys.argv[1] == "--test-api":
            installer.test_api_connection(api_key)

    if success:
        print("🎉 Qwen CLI installation and configuration completed!")
        print("💡 Remember to pass API key at runtime: --openai-api-key YOUR_KEY")
        sys.exit(0)
    else:
        print("❌ Qwen CLI installation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
