#!/usr/bin/env python3
"""
Cross-platform Docker cleanup utility for evaluation system.
Works on Windows, macOS, and Linux.
"""

import subprocess
import sys
import argparse
import platform
import tempfile
from pathlib import Path
from typing import List


class DockerCleanup:
    """Cross-platform Docker cleanup utility."""

    def __init__(self, purge: bool = False, verbose: bool = False):
        self.purge = purge
        self.verbose = verbose
        self.container_prefix = "eval_"
        self.volume_prefix = "eval_"
        self.image_prefix = "evaluation-"
        self.network_name = "evaluation-network"

    def check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_containers(self, running_only: bool = False) -> List[str]:
        """Get list of evaluation containers."""
        # ps_flag = "" if not running_only else "--filter status=running"
        cmd = [
            "docker",
            "ps",
            "-a" if not running_only else "",
            "--filter",
            f"name={self.container_prefix}",
            "--format",
            "{{.Names}}",
        ]

        # Remove empty strings from command
        cmd = [arg for arg in cmd if arg]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                containers = [
                    name.strip() for name in result.stdout.strip().split("\n")
                ]
                return [name for name in containers if name]  # Filter empty strings
            return []
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error getting containers: {e}")
            return []

    def stop_containers(self) -> int:
        """Stop all evaluation containers."""
        containers = self.get_containers(running_only=True)

        if not containers:
            print("📭 No running evaluation containers found")
            return 0

        print(f"🛑 Stopping {len(containers)} running container(s)...")

        stopped = 0
        for container in containers:
            if not container:
                continue

            try:
                if self.verbose:
                    print(f"   Stopping {container}...")

                result = subprocess.run(
                    ["docker", "stop", container],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    print(f"   ✅ Stopped: {container}")
                    stopped += 1
                else:
                    print(f"   ⚠️  Failed to stop: {container}")
                    if self.verbose and result.stderr:
                        print(f"      Error: {result.stderr.strip()}")

            except subprocess.TimeoutExpired:
                print(f"   ❌ Timeout stopping: {container}")
            except Exception as e:
                print(f"   ❌ Error stopping {container}: {e}")

        return stopped

    def remove_containers(self) -> int:
        """Remove all evaluation containers."""
        containers = self.get_containers()

        if not containers:
            print("📭 No containers to remove")
            return 0

        print(f"🗑️  Removing {len(containers)} container(s)...")

        removed = 0
        for container in containers:
            if not container:
                continue

            try:
                if self.verbose:
                    print(f"   Removing {container}...")

                result = subprocess.run(
                    [
                        "docker",
                        "rm",
                        "-f",
                        container,
                    ],  # -f to force remove running containers
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    print(f"   ✅ Removed: {container}")
                    removed += 1
                else:
                    print(f"   ⚠️  Failed to remove: {container}")
                    if self.verbose and result.stderr:
                        print(f"      Error: {result.stderr.strip()}")

            except subprocess.TimeoutExpired:
                print(f"   ❌ Timeout removing: {container}")
            except Exception as e:
                print(f"   ❌ Error removing {container}: {e}")

        return removed

    def remove_volumes(self) -> int:
        """Remove evaluation volumes."""
        print("💾 Checking for evaluation volumes...")

        try:
            cmd = [
                "docker",
                "volume",
                "ls",
                "--filter",
                f"name={self.volume_prefix}",
                "--format",
                "{{.Name}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0 or not result.stdout.strip():
                print("📭 No volumes to remove")
                return 0

            volumes = [
                vol.strip() for vol in result.stdout.strip().split("\n") if vol.strip()
            ]

            if not volumes:
                print("📭 No volumes found")
                return 0

            print(f"🗑️  Removing {len(volumes)} volume(s)...")

            removed = 0
            for volume in volumes:
                try:
                    if self.verbose:
                        print(f"   Removing volume {volume}...")

                    rm_result = subprocess.run(
                        ["docker", "volume", "rm", volume],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if rm_result.returncode == 0:
                        print(f"   ✅ Removed: {volume}")
                        removed += 1
                    else:
                        print(f"   ⚠️  Failed to remove: {volume}")
                        if self.verbose and rm_result.stderr:
                            print(f"      Error: {rm_result.stderr.strip()}")

                except subprocess.TimeoutExpired:
                    print(f"   ❌ Timeout removing: {volume}")
                except Exception as e:
                    print(f"   ❌ Error removing {volume}: {e}")

            return removed

        except subprocess.TimeoutExpired:
            print("❌ Timeout listing volumes")
            return 0
        except Exception as e:
            print(f"❌ Error removing volumes: {e}")
            return 0

    def remove_images(self) -> int:
        """Remove evaluation images."""
        print("🖼️  Checking for evaluation images...")

        try:
            cmd = [
                "docker",
                "images",
                "--filter",
                f"reference={self.image_prefix}*",
                "--format",
                "{{.Repository}}:{{.Tag}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0 or not result.stdout.strip():
                print("📭 No images to remove")
                return 0

            images = [
                img.strip() for img in result.stdout.strip().split("\n") if img.strip()
            ]

            if not images:
                print("📭 No images found")
                return 0

            print(f"🗑️  Removing {len(images)} image(s)...")

            removed = 0
            for image in images:
                try:
                    if self.verbose:
                        print(f"   Removing image {image}...")

                    rm_result = subprocess.run(
                        ["docker", "rmi", "-f", image],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if rm_result.returncode == 0:
                        print(f"   ✅ Removed: {image}")
                        removed += 1
                    else:
                        print(f"   ⚠️  Failed to remove: {image}")
                        if self.verbose and rm_result.stderr:
                            print(f"      Error: {rm_result.stderr.strip()}")

                except subprocess.TimeoutExpired:
                    print(f"   ❌ Timeout removing: {image}")
                except Exception as e:
                    print(f"   ❌ Error removing {image}: {e}")

            return removed

        except Exception as e:
            print(f"❌ Error removing images: {e}")
            return 0

    def remove_network(self) -> bool:
        """Remove evaluation network."""
        print(f"🌐 Checking for evaluation network: {self.network_name}")

        try:
            # Check if network exists
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

            if self.network_name not in result.stdout:
                print("📭 Network not found")
                return True

            # Remove network
            rm_cmd = ["docker", "network", "rm", self.network_name]
            rm_result = subprocess.run(
                rm_cmd, capture_output=True, text=True, timeout=10
            )

            if rm_result.returncode == 0:
                print(f"✅ Removed network: {self.network_name}")
                return True
            else:
                print(f"⚠️  Failed to remove network: {rm_result.stderr}")
                return False

        except Exception as e:
            print(f"⚠️  Error removing network: {e}")
            return False

    def clean_temp_files(self) -> int:
        """Clean temporary token files (platform-specific)."""
        print("🧹 Cleaning temporary token files...")

        system = platform.system().lower()
        cleaned = 0

        # Define patterns to look for
        patterns = ["*cli_token_*", "*secure_token_*", "*_token_*.key"]

        # Define temp directories based on platform
        temp_dirs = []
        if system in ["linux", "darwin"]:  # Linux or macOS
            temp_dirs = [
                Path("/tmp"),
                Path("/var/tmp"),
                Path.home() / ".cache",
                Path.home() / ".tmp",
            ]
        elif system == "windows":
            temp_dirs = [
                Path(tempfile.gettempdir()),
                Path.home() / "AppData" / "Local" / "Temp",
            ]

        for temp_dir in temp_dirs:
            if not temp_dir.exists():
                continue

            if self.verbose:
                print(f"   Checking {temp_dir}...")

            try:
                for pattern in patterns:
                    for file_path in temp_dir.glob(pattern):
                        if file_path.is_file():
                            try:
                                if self.verbose:
                                    print(f"   Found: {file_path}")

                                # Secure deletion - overwrite before removal
                                if file_path.stat().st_size > 0:
                                    with open(file_path, "wb") as f:
                                        # Overwrite with zeros, then random data
                                        import secrets

                                        file_size = max(1024, file_path.stat().st_size)
                                        f.write(b"\x00" * file_size)
                                        f.flush()
                                        f.seek(0)
                                        f.write(secrets.token_bytes(file_size))
                                        f.flush()

                                file_path.unlink()
                                cleaned += 1

                            except (OSError, IOError) as e:
                                if self.verbose:
                                    print(f"   Could not remove {file_path}: {e}")

            except Exception as e:
                if self.verbose:
                    print(f"   Error scanning {temp_dir}: {e}")

        if cleaned > 0:
            print(f"   ✅ Removed {cleaned} temporary file(s)")
        else:
            print("   ✅ No temporary files found")

        return cleaned

    def system_prune(self) -> bool:
        """Run Docker system prune to clean up unused resources."""
        print("🧹 Running Docker system cleanup...")

        try:
            # Prune stopped containers, unused networks, dangling images
            result = subprocess.run(
                ["docker", "system", "prune", "-f"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                print("✅ Docker system cleanup completed")
                if self.verbose and result.stdout:
                    print(f"   {result.stdout.strip()}")
                return True
            else:
                print(f"⚠️  Docker system cleanup failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Docker system cleanup timed out")
            return False
        except Exception as e:
            print(f"⚠️  Error during system cleanup: {e}")
            return False

    def run(self) -> int:
        """Main cleanup process."""
        print("🧹 Docker Evaluation System Cleanup")
        print("=" * 50)
        print(f"📍 Platform: {platform.system()} {platform.machine()}")
        print(f"🔧 Mode: {'FULL PURGE' if self.purge else 'STOP CONTAINERS ONLY'}")
        print(f"📢 Verbose: {'ON' if self.verbose else 'OFF'}")
        print("")

        # Check Docker availability
        if not self.check_docker():
            print("❌ Docker is not installed or not running")
            print("   Please ensure Docker is installed and the daemon is running")
            return 1

        # Initialize counters
        containers_stopped = 0
        containers_removed = 0
        volumes_removed = 0
        images_removed = 0
        temp_files_cleaned = 0

        # Always stop running containers
        containers_stopped = self.stop_containers()

        if self.purge:
            print("\n🗑️  PURGE MODE - Removing all evaluation resources...")

            # Remove containers
            containers_removed = self.remove_containers()

            # Remove volumes
            volumes_removed = self.remove_volumes()

            # Remove images
            images_removed = self.remove_images()

            # Remove network
            network_removed = self.remove_network()

        else:
            print("\n💾 Containers stopped but preserved")
            print("   Use --purge to remove all evaluation resources")

        # Always clean temp files
        print("")
        temp_files_cleaned = self.clean_temp_files()

        # Optional system prune
        if self.purge:
            print("")
            self.system_prune()

        # Summary
        print("\n" + "=" * 50)
        print("📊 CLEANUP SUMMARY")
        print("=" * 50)
        print(f"Containers stopped: {containers_stopped}")

        if self.purge:
            print(f"Containers removed: {containers_removed}")
            print(f"Volumes removed: {volumes_removed}")
            print(f"Images removed: {images_removed}")
            print(
                f"Network removed: {'✅' if 'network_removed' in locals() and network_removed else '❌'}"
            )

        print(f"Temp files cleaned: {temp_files_cleaned}")

        print("\n✅ Cleanup completed!")

        if not self.purge and containers_stopped > 0:
            print(
                "\n💡 Tip: Containers are preserved and can be restarted automatically"
            )
            print("   Use --purge next time to remove everything completely")

        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Clean up Docker evaluation containers and resources"
    )
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Remove containers, volumes, images, and network (default: stop containers only)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose output"
    )

    args = parser.parse_args()

    try:
        cleanup = DockerCleanup(purge=args.purge, verbose=args.verbose)
        return cleanup.run()
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
