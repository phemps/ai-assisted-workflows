#!/usr/bin/env python3
"""
Base CLI Installer

Abstract base class for secure CLI tool installation with cross-platform support.
"""

import os
import platform
import subprocess
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any


class PlatformInfo:
    """Cross-platform system information utility."""

    @staticmethod
    def get_platform_info() -> Dict[str, Any]:
        """Get normalized platform information."""
        system = platform.system().lower()
        arch = platform.machine().lower()

        # Normalize architecture names
        arch_mapping = {
            "x86_64": "amd64",
            "amd64": "amd64",
            "arm64": "arm64",
            "aarch64": "arm64",
        }

        normalized_arch = arch_mapping.get(arch, arch)

        return {
            "os": system,
            "arch": normalized_arch,
            "python_version": platform.python_version(),
            "node_available": shutil.which("node") is not None,
            "npm_available": shutil.which("npm") is not None,
            "docker_available": shutil.which("docker") is not None,
            "curl_available": shutil.which("curl") is not None,
            "wget_available": shutil.which("wget") is not None,
        }


class SecureSubprocessManager:
    """Secure subprocess execution with proper error handling."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    def run_command(
        self,
        cmd: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess:
        """Execute command with security best practices."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                capture_output=capture_output,
                text=True,
                timeout=self.timeout,
                check=check,
            )
            return result

        except subprocess.TimeoutExpired:
            raise TimeoutError(
                f"Command timed out after {self.timeout}s: {' '.join(cmd)}"
            )
        except FileNotFoundError:
            raise RuntimeError(f"Command not found: {cmd[0]}")
        except subprocess.CalledProcessError as e:
            if check:
                raise RuntimeError(
                    f"Command failed with exit code {e.returncode}: {' '.join(cmd)}"
                )
            return e


class BaseCLIInstaller(ABC):
    """Base class for secure CLI tool installation."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.platform_info = PlatformInfo.get_platform_info()
        self.subprocess_manager = SecureSubprocessManager()
        self.install_marker = Path(f"/home/evaluator/.{tool_name}_installed")
        self.cache_dir = Path("/home/evaluator/.cache") / tool_name

        # Check if we're running inside a container evaluation context
        self.container_name = os.environ.get("EVALUATOR_CONTAINER_NAME")
        self.in_container_context = self.container_name is not None

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def is_installed(self) -> bool:
        """Check if tool is already installed."""
        # Check if binary is in PATH
        if shutil.which(self.tool_name):
            return True

        # Check install marker
        if self.install_marker.exists():
            return True

        # Tool-specific checks can be overridden
        return self._additional_install_check()

    def _additional_install_check(self) -> bool:
        """Override for tool-specific installation checks."""
        return False

    def _run_in_container_context(
        self, cmd: List[str], timeout: int = 10
    ) -> subprocess.CompletedProcess:
        """Run command in container context if we're in an evaluator environment."""
        if self.in_container_context:
            # Container PATH for proper CLI tool resolution
            container_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/evaluator/.local/bin"

            # Prepend docker exec command
            docker_cmd = [
                "docker",
                "exec",
                "-e",
                f"PATH={container_path}",
                self.container_name,
            ] + cmd

            return subprocess.run(
                docker_cmd, capture_output=True, text=True, timeout=timeout
            )
        else:
            # Run directly (normal installation context)
            return self.subprocess_manager.run_command(cmd, timeout=timeout)

    def verify_installation(self) -> bool:
        """Verify that the tool is properly installed."""
        try:
            result = self._run_in_container_context(
                [self.tool_name, "--version"], timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def mark_installed(self) -> None:
        """Mark tool as installed."""
        try:
            self.install_marker.parent.mkdir(parents=True, exist_ok=True)
            self.install_marker.touch()
            print(f"✅ Marked {self.tool_name} as installed")
        except Exception as e:
            print(f"⚠️  Could not mark {self.tool_name} as installed: {e}")

    def _run_install_command(
        self,
        cmd: List[str],
        description: str = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = False,
    ) -> bool:
        """Execute installation command with proper error handling."""
        desc = description or f"Installing {self.tool_name}"
        print(f"🔨 {desc}...")

        try:
            if shell and len(cmd) == 1:
                # For shell commands, use shell=True
                result = subprocess.run(
                    cmd[0],
                    shell=True,
                    cwd=cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self.subprocess_manager.timeout,
                )
            else:
                result = self.subprocess_manager.run_command(cmd, cwd=cwd, env=env)

            if result.returncode == 0:
                print(f"✅ {desc} successful")
                return True
            else:
                print(f"❌ {desc} failed:")
                print(f"   Exit code: {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"❌ {desc} failed with exception: {e}")
            return False

    def download_file(self, url: str, destination: Path) -> bool:
        """Download file using curl or wget."""
        destination.parent.mkdir(parents=True, exist_ok=True)

        if self.platform_info["curl_available"]:
            cmd = ["curl", "-fsSL", url, "-o", str(destination)]
        elif self.platform_info["wget_available"]:
            cmd = ["wget", "-q", url, "-O", str(destination)]
        else:
            print("❌ Neither curl nor wget available for download")
            return False

        return self._run_install_command(cmd, f"Downloading {url}", timeout=60)

    @abstractmethod
    def install(self) -> bool:
        """Install the CLI tool. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def configure_auth(self, token: Optional[str] = None) -> bool:
        """Configure authentication. Must be implemented by subclasses."""
        pass

    def install_with_auth(self, token: Optional[str] = None) -> bool:
        """Install tool and configure authentication in one step."""
        print(f"🚀 Installing {self.tool_name} with authentication...")

        # Check if already installed
        if self.is_installed():
            print(f"✅ {self.tool_name} already installed")
            if token:
                return self.configure_auth(token)
            return True

        # Install the tool
        if not self.install():
            print(f"❌ Failed to install {self.tool_name}")
            return False

        # Verify installation
        if not self.verify_installation():
            print(f"❌ {self.tool_name} installation verification failed")
            return False

        # Mark as installed
        self.mark_installed()

        # Configure authentication if token provided
        if token:
            if not self.configure_auth(token):
                print(f"❌ Failed to configure authentication for {self.tool_name}")
                return False

        print(f"🎉 {self.tool_name} installation completed successfully!")
        return True


if __name__ == "__main__":
    # Test platform info
    info = PlatformInfo.get_platform_info()
    print("Platform Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
