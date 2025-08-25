#!/usr/bin/env python3
"""
Cross-platform Docker image builder for CLI evaluation system.
Works on Windows, macOS, and Linux.
"""

import subprocess
import sys
import platform
import argparse
from pathlib import Path


class DockerBuilder:
    """Cross-platform Docker image builder."""

    def __init__(self, verbose: bool = False):
        self.docker_dir = Path(__file__).parent / "docker"
        self.evaluation_dir = Path(__file__).parent
        self.verbose = verbose

        # Image configurations: (dockerfile, tag, description)
        self.images = [
            ("Dockerfile.base", "evaluation-base:latest", "Minimal Alpine base image"),
            ("Dockerfile.python", "evaluation-python:latest", "Python-specific image"),
            ("Dockerfile.node", "evaluation-node:latest", "Node.js-specific image"),
        ]

        # Persistent volumes for CLI tools
        self.volumes = [
            "eval_workspace_claude",
            "eval_workspace_qwen",
            "eval_workspace_gemini",
        ]

        self.network_name = "evaluation-network"

    def check_docker(self) -> bool:
        """Check if Docker is available."""
        print("🔍 Checking Docker availability...")
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Docker found: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ Docker check failed: {result.stderr}")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"❌ Docker not found or not responding: {e}")
            return False

    def check_docker_running(self) -> bool:
        """Check if Docker daemon is running."""
        print("🔍 Checking Docker daemon status...")
        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("✅ Docker daemon is running")
                return True
            else:
                print("❌ Docker daemon is not running")
                print("   Please start Docker Desktop or Docker daemon")
                return False
        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"❌ Could not check Docker daemon status: {e}")
            return False

    def build_image(self, dockerfile: str, tag: str, description: str) -> bool:
        """Build a Docker image."""
        dockerfile_path = self.docker_dir / dockerfile

        if not dockerfile_path.exists():
            print(f"❌ Dockerfile not found: {dockerfile_path}")
            return False

        print(f"🔨 Building {description} ({tag})...")

        cmd = [
            "docker",
            "build",
            "-f",
            str(dockerfile_path),
            "-t",
            tag,
            str(self.docker_dir),
        ]

        if self.verbose:
            print(f"   Command: {' '.join(cmd)}")

        try:
            if self.verbose:
                # Stream output in real-time
                result = subprocess.run(
                    cmd, text=True, timeout=600
                )  # 10 minute timeout
            else:
                # Capture output
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=600
                )

            if result.returncode == 0:
                print(f"✅ Successfully built {tag}")
                return True
            else:
                print(f"❌ Failed to build {tag}")
                if not self.verbose and result.stderr:
                    print(f"   Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"❌ Build timed out for {tag}")
            return False
        except Exception as e:
            print(f"❌ Error building {tag}: {e}")
            return False

    def create_network(self) -> bool:
        """Create isolated Docker network."""
        print(f"🌐 Creating evaluation network: {self.network_name}")

        try:
            # Check if network exists first
            check_cmd = [
                "docker",
                "network",
                "ls",
                "--filter",
                f"name={self.network_name}",
                "--format",
                "{{.Name}}",
            ]
            result = subprocess.run(
                check_cmd, capture_output=True, text=True, timeout=10
            )

            if self.network_name in result.stdout:
                print("✅ Network already exists")
                return True

            # Create network with isolation
            create_cmd = [
                "docker",
                "network",
                "create",
                "--driver",
                "bridge",
                "--internal",
                self.network_name,
            ]

            result = subprocess.run(
                create_cmd, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                print("✅ Network created successfully")
                return True
            else:
                print(f"⚠️  Network creation failed: {result.stderr}")
                print("   Continuing anyway (network might already exist)")
                return True  # Not critical if already exists

        except subprocess.TimeoutExpired:
            print("❌ Network creation timed out")
            return False
        except Exception as e:
            print(f"⚠️  Error creating network: {e}")
            return False

    def create_volumes(self) -> bool:
        """Create persistent volumes for workspaces."""
        print("💾 Creating persistent volumes...")

        success_count = 0
        for volume_name in self.volumes:
            try:
                # Check if volume exists
                check_cmd = [
                    "docker",
                    "volume",
                    "ls",
                    "--filter",
                    f"name={volume_name}",
                    "--format",
                    "{{.Name}}",
                ]
                result = subprocess.run(
                    check_cmd, capture_output=True, text=True, timeout=10
                )

                if volume_name in result.stdout:
                    print(f"   {volume_name}: already exists")
                    success_count += 1
                    continue

                # Create volume
                create_cmd = ["docker", "volume", "create", volume_name]
                result = subprocess.run(
                    create_cmd, capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    print(f"   {volume_name}: created")
                    success_count += 1
                else:
                    print(f"   {volume_name}: failed - {result.stderr}")

            except subprocess.TimeoutExpired:
                print(f"   {volume_name}: timed out")
            except Exception as e:
                print(f"   {volume_name}: error - {e}")

        print(f"📊 Created {success_count}/{len(self.volumes)} volumes")
        return success_count == len(self.volumes)

    def list_images(self) -> None:
        """List built evaluation images."""
        print("\n📋 Available evaluation images:")
        try:
            cmd = [
                "docker",
                "images",
                "--filter",
                "reference=evaluation-*",
                "--format",
                "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}",
            ]
            result = subprocess.run(cmd, timeout=10)

            if result.returncode != 0:
                print("   Could not list images")

        except Exception as e:
            print(f"   Error listing images: {e}")

    def cleanup_build_artifacts(self) -> None:
        """Clean up Docker build artifacts."""
        print("\n🧹 Cleaning up build artifacts...")
        try:
            # Remove dangling images
            subprocess.run(
                ["docker", "image", "prune", "-f"], capture_output=True, timeout=60
            )

            # Remove unused build cache
            subprocess.run(
                ["docker", "builder", "prune", "-f"], capture_output=True, timeout=60
            )

            print("✅ Build artifacts cleaned")

        except Exception as e:
            print(f"⚠️  Could not clean build artifacts: {e}")

    def get_system_info(self) -> dict:
        """Get system information for debugging."""
        info = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "docker_available": False,
            "docker_version": None,
            "docker_running": False,
        }

        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["docker_available"] = True
                info["docker_version"] = result.stdout.strip()

                # Check if daemon is running
                daemon_result = subprocess.run(
                    ["docker", "info"], capture_output=True, timeout=5
                )
                info["docker_running"] = daemon_result.returncode == 0

        except Exception:
            pass

        return info

    def run(self, force_rebuild: bool = False, cleanup: bool = False) -> int:
        """Main build process."""
        print("🐳 Docker Evaluation System Builder")
        print("=" * 50)

        # Display system info
        system_info = self.get_system_info()
        print(f"📍 Platform: {system_info['platform']} {system_info['machine']}")
        print(f"🐍 Python: {system_info['python_version']}")

        # Check Docker
        if not system_info["docker_available"]:
            print("\n❌ Docker is not installed or not in PATH")
            print("   Please install Docker Desktop and ensure it's in your PATH")
            return 1

        print(f"🐳 {system_info['docker_version']}")

        if not system_info["docker_running"]:
            print("❌ Docker daemon is not running")
            print("   Please start Docker Desktop or Docker daemon")
            return 1

        print("\n🚀 Starting build process...")

        # Check if we need to rebuild existing images
        if not force_rebuild:
            print("💡 Use --force-rebuild to rebuild existing images")

        # Build images
        built_images = 0
        for dockerfile, tag, description in self.images:
            if self.build_image(dockerfile, tag, description):
                built_images += 1
            else:
                print("⚠️  Continuing with remaining builds...")

        print(f"\n📊 Built {built_images}/{len(self.images)} images successfully")

        # Create network
        network_success = self.create_network()

        # Create volumes
        volumes_success = self.create_volumes()

        # List results
        self.list_images()

        # Optional cleanup
        if cleanup:
            self.cleanup_build_artifacts()

        # Final status
        print("\n" + "=" * 50)
        if built_images == len(self.images) and network_success and volumes_success:
            print("✅ BUILD COMPLETED SUCCESSFULLY!")
            print("\n🎯 Next steps:")
            print("   1. Run: python run_eval_docker.py --help")
            print(
                "   2. Test: python run_eval_docker.py scenarios/baseline_task.yaml --cli-tool claude"
            )
            return 0
        else:
            print("⚠️  BUILD COMPLETED WITH WARNINGS")
            print(f"   Images: {built_images}/{len(self.images)} built")
            print(f"   Network: {'✅' if network_success else '❌'}")
            print(f"   Volumes: {'✅' if volumes_success else '❌'}")
            print("\n   You may still be able to run evaluations")
            return 0  # Non-critical issues


def main():
    parser = argparse.ArgumentParser(
        description="Build Docker images for CLI evaluation system"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose build output"
    )
    parser.add_argument(
        "--force-rebuild",
        "-f",
        action="store_true",
        help="Rebuild images even if they exist",
    )
    parser.add_argument(
        "--cleanup",
        "-c",
        action="store_true",
        help="Clean up build artifacts after build",
    )

    args = parser.parse_args()

    try:
        builder = DockerBuilder(verbose=args.verbose)
        return builder.run(force_rebuild=args.force_rebuild, cleanup=args.cleanup)
    except KeyboardInterrupt:
        print("\n\n❌ Build cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
