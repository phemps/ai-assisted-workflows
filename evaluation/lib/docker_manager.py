#!/usr/bin/env python3
"""
Docker Container Management for CLI Evaluation System

Handles Docker container lifecycle, security, and volume management.
"""

import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List


class DockerManager:
    """Manages Docker containers for CLI tool evaluation."""

    # Docker image mapping for different CLI tools
    DOCKER_IMAGES = {
        "claude": "evaluation-node:latest",
        "qwen": "evaluation-node:latest",
        "gemini": "evaluation-node:latest",
    }

    def __init__(self, cli_tool: str, scenario: Dict[str, Any]):
        self.cli_tool = cli_tool
        self.scenario = scenario
        self.docker_image = self.DOCKER_IMAGES.get(cli_tool, "evaluation-base:latest")
        self.container_name = self._generate_container_name()

    def _generate_container_name(self) -> str:
        """Generate consistent container name based on CLI tool."""
        # First check for existing containers with this CLI tool
        existing_name = self._find_existing_container()
        if existing_name:
            return existing_name

        # Create consistent hash from CLI tool name
        hash_input = f"eval_{self.cli_tool}".encode()
        container_hash = hashlib.sha256(hash_input).hexdigest()[:12]
        return f"eval_{self.cli_tool}_{container_hash}"

    def _find_existing_container(self) -> Optional[str]:
        """Find existing container for this CLI tool."""
        try:
            # Get containers sorted by creation time (newest first)
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--filter",
                    f"name=eval_{self.cli_tool}",
                    "--format",
                    "{{.Names}}\t{{.Status}}\t{{.CreatedAt}}",
                    "--no-trunc",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        container_name = parts[0]
                        status = parts[1]
                        # Prefer running containers, then any container
                        if "Up" in status:
                            return container_name

                # If no running container, return the most recent one
                if lines:
                    return lines[0].split("\t")[0]
        except subprocess.TimeoutExpired:
            pass

        return None

    def create_container(self, auth_mode: str = "apikey") -> bool:
        """Create a new Docker container with security hardening."""
        print(f"🐳 Creating secure container: {self.container_name}")

        # Get scenario-specific settings
        docker_config = self.scenario.get("docker", {})
        memory = docker_config.get("memory", "4g")
        cpus = docker_config.get("cpus", 2)

        cmd = [
            "docker",
            "create",
            "--name",
            self.container_name,
            "--memory",
            memory,
            "--memory-swap",
            memory,
            "--cpus",
            str(cpus),
            "--security-opt",
            "no-new-privileges:true",
            "--cap-drop",
            "ALL",
            "--cap-add",
            "NET_BIND_SERVICE",  # Minimal network capability
            "-v",
            f"{Path.cwd()}/scenarios:/workspace/scenarios:ro",
            "-v",
            f"{Path.cwd()}/cli_installers:/workspace/installers:ro",
            "-v",
            f"eval_workspace_{self.container_name}:/home/evaluator/workspace:rw",
            "--network",
            "bridge",  # Need network for CLI installation
            "--restart",
            "no",
        ]

        # Add interactive flags for OAuth mode
        if auth_mode == "oauth":
            cmd.extend(["-it"])

        cmd.extend([self.docker_image, "sleep", "infinity"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"❌ Failed to create container: {result.stderr}")
                return False

            # Start the container
            start_result = subprocess.run(
                ["docker", "start", self.container_name],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if start_result.returncode != 0:
                print(f"❌ Failed to start container: {start_result.stderr}")
                return False

            print("✅ Container created and started successfully")
            return True

        except subprocess.TimeoutExpired:
            print("❌ Container creation timed out")
            return False
        except Exception as e:
            print(f"❌ Error creating container: {e}")
            return False

    def container_exists(self) -> bool:
        """Check if the container already exists."""
        try:
            result = subprocess.run(
                ["docker", "inspect", self.container_name],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def is_container_running(self) -> bool:
        """Check if the container is currently running."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{.State.Running}}",
                    self.container_name,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and result.stdout.strip() == "true"
        except subprocess.TimeoutExpired:
            return False

    def start_container(self) -> bool:
        """Start a stopped container."""
        if self.is_container_running():
            return True

        print("🔄 Starting stopped container...")
        try:
            start_result = subprocess.run(
                ["docker", "start", self.container_name],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if start_result.returncode == 0:
                print("✅ Container started successfully")
                return True
            else:
                print(f"❌ Failed to start container: {start_result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Container start timed out")
            return False

    def stop_container(self) -> bool:
        """Stop a running container."""
        if not self.is_container_running():
            return True

        try:
            result = subprocess.run(
                ["docker", "stop", self.container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            # Force kill if stop times out
            try:
                subprocess.run(
                    ["docker", "kill", self.container_name],
                    capture_output=True,
                    timeout=10,
                )
                return True
            except Exception:
                return False

    def remove_container(self) -> bool:
        """Remove the container and its volumes."""
        # Stop first if running
        self.stop_container()

        try:
            # Remove container
            result = subprocess.run(
                ["docker", "rm", self.container_name],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print(f"🗑️  Container {self.container_name} removed")

            # Remove associated volume
            volume_name = f"eval_workspace_{self.container_name}"
            subprocess.run(
                ["docker", "volume", "rm", volume_name], capture_output=True, timeout=5
            )

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            return False

    def execute_command(
        self,
        command: List[str],
        environment: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> subprocess.CompletedProcess:
        """Execute a command inside the container."""
        # Build Docker exec command
        docker_cmd = ["docker", "exec"]

        # Add environment variables
        if environment:
            for key, value in environment.items():
                docker_cmd.extend(["-e", f"{key}={value}"])

        docker_cmd.append(self.container_name)
        docker_cmd.extend(command)

        try:
            return subprocess.run(
                docker_cmd, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            # Return a mock result for timeout
            result = subprocess.CompletedProcess(
                args=docker_cmd,
                returncode=124,  # Timeout exit code
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
            )
            return result

    def execute_with_streaming(
        self,
        command: List[str],
        environment: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> subprocess.Popen:
        """Execute a command with streaming output capability."""
        # Build Docker exec command
        docker_cmd = ["docker", "exec"]

        # Add environment variables
        if environment:
            for key, value in environment.items():
                docker_cmd.extend(["-e", f"{key}={value}"])

        docker_cmd.append(self.container_name)
        docker_cmd.extend(command)

        return subprocess.Popen(
            docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

    def copy_to_container(self, src_path: str, dest_path: str) -> bool:
        """Copy file from host to container."""
        try:
            result = subprocess.run(
                ["docker", "cp", src_path, f"{self.container_name}:{dest_path}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def copy_from_container(self, src_path: str, dest_path: str) -> bool:
        """Copy file from container to host."""
        try:
            result = subprocess.run(
                ["docker", "cp", f"{self.container_name}:{src_path}", dest_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def get_container_info(self) -> Dict[str, Any]:
        """Get detailed container information."""
        try:
            result = subprocess.run(
                ["docker", "inspect", self.container_name],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                import json

                container_data = json.loads(result.stdout)
                if container_data:
                    return container_data[0]

            return {}
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return {}

    def ensure_container_ready(self, auth_mode: str = "apikey") -> bool:
        """Ensure container exists and is running."""
        container_existed = self.container_exists()

        if container_existed:
            print(f"♻️  Reusing existing container: {self.container_name}")

            # Start if stopped
            if not self.is_container_running():
                if not self.start_container():
                    print("❌ Failed to start existing container, creating new one...")
                    container_existed = False

        if not container_existed:
            if not self.create_container(auth_mode):
                return False

        return True

    def cleanup(self, tear_down: bool = False):
        """Clean up container resources."""
        if tear_down:
            print(f"🗑️  Removing container: {self.container_name}")
            self.remove_container()
        else:
            print(f"💾 Container preserved for reuse: {self.container_name}")

    def check_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
