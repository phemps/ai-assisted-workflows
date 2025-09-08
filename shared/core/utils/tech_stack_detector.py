#!/usr/bin/env python3
"""
Tech Stack Detection and Filtering Utility
Automatically detects project technology stack and provides appropriate filtering rules.
"""

import json
from pathlib import Path
from typing import List, Set, Dict
from dataclasses import dataclass

from core.config.loader import load_tech_stacks, ConfigError


@dataclass
class TechStackConfig:
    """Configuration for a specific technology stack."""

    name: str
    primary_languages: Set[str]
    exclude_patterns: Set[str]
    dependency_dirs: Set[str]
    config_files: Set[str]
    source_patterns: Set[str]
    build_artifacts: Set[str]
    boilerplate_patterns: Set[str] = None

    def __post_init__(self):
        if self.boilerplate_patterns is None:
            self.boilerplate_patterns = set()


class TechStackDetector:
    """Detects project technology stack and provides filtering rules."""

    def __init__(self, config_path: Path | None = None):
        # Default to repo config if not provided
        if config_path is None:
            config_path = (
                Path(__file__).resolve().parents[2]
                / "config"
                / "tech_stacks"
                / "tech_stacks.json"
            )
        try:
            stacks_raw: Dict[str, Dict] = load_tech_stacks(config_path)
        except ConfigError as e:
            raise RuntimeError(f"Tech stacks config error: {e}")

        # Materialize dataclass configs, ensure sets
        self.tech_stacks: Dict[str, TechStackConfig] = {}
        for key, spec in stacks_raw.items():
            self.tech_stacks[key] = TechStackConfig(
                name=spec["name"],
                primary_languages=set(spec.get("primary_languages", [])),
                exclude_patterns=set(spec.get("exclude_patterns", [])),
                dependency_dirs=set(spec.get("dependency_dirs", [])),
                config_files=set(spec.get("config_files", [])),
                source_patterns=set(spec.get("source_patterns", [])),
                build_artifacts=set(spec.get("build_artifacts", [])),
                boilerplate_patterns=set(spec.get("boilerplate_patterns", []))
                if spec.get("boilerplate_patterns")
                else None,
            )

    @classmethod
    def from_config(cls, config_path: Path) -> "TechStackDetector":
        return cls(config_path=config_path)

    def detect_tech_stack(self, project_path: str) -> List[str]:
        """
        Detect technology stacks in the project.

        Args:
            project_path: Path to the project root

        Returns:
            List of detected technology stack names
        """
        detected_stacks = []
        project_root = Path(project_path)

        # Check for each tech stack
        for stack_id, config in self.tech_stacks.items():
            if self._matches_tech_stack(project_root, config):
                detected_stacks.append(stack_id)

        return detected_stacks

    def _matches_tech_stack(self, project_root: Path, config: TechStackConfig) -> bool:
        """Check if project matches a specific tech stack."""
        config_file_matches = 0

        # Check for config files
        for config_file in config.config_files:
            if self._file_exists_pattern(project_root, config_file):
                config_file_matches += 1

        # If multiple config files match, it's likely this tech stack
        return config_file_matches > 0

    def _file_exists_pattern(self, project_root: Path, pattern: str) -> bool:
        """Check if files matching pattern exist."""
        if "*" in pattern:
            # Handle glob patterns
            try:
                matches = list(project_root.glob(pattern))
                return len(matches) > 0
            except Exception:
                return False
        else:
            # Direct file check
            return (project_root / pattern).exists()

    def get_simple_exclusions(self, project_path: str) -> dict:
        """
        Get simple, reliable exclusion lists by tech stack.

        Returns:
            dict with 'directories' and 'files' to exclude
        """
        detected_stacks = self.detect_tech_stack(project_path)

        # Universal exclusions (always apply)
        excluded_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            ".coverage",
            "coverage",
            ".nyc_output",
            "logs",
            "tmp",
            "temp",
            # Universal vendor/build directories (exclude regardless of stack detection)
            "node_modules",
            "dist",
            "build",
            ".next",
            ".nuxt",
        }
        excluded_files = {
            ".DS_Store",
            "Thumbs.db",
            ".env",
            ".env.local",
            ".env.production",
        }
        excluded_extensions = {".log", ".tmp", ".cache"}

        # Tech-specific exclusions
        if "react_native_expo" in detected_stacks:
            excluded_dirs.update(
                {
                    "node_modules",
                    "Pods",
                    "build",
                    "android/build",
                    "ios/build",
                    ".expo",
                    "web-build",
                    "dist",
                    ".next",
                }
            )
            # Special handling for iOS Pods directory structure
            excluded_dirs.add("ios/Pods")

        if "node_js" in detected_stacks:
            excluded_dirs.update({"node_modules", "dist", "build", ".next", ".nuxt"})

        if "python" in detected_stacks:
            excluded_dirs.update(
                {
                    "__pycache__",
                    ".pytest_cache",
                    "venv",
                    ".venv",
                    "env",
                    ".env",
                    "site-packages",
                    "dist",
                    "build",
                    ".tox",
                }
            )
            excluded_extensions.update({".pyc", ".pyo", ".pyd"})

        if "java_maven" in detected_stacks or "java_gradle" in detected_stacks:
            excluded_dirs.update({"target", "build", ".gradle", ".idea", ".settings"})
            excluded_extensions.update({".class", ".jar", ".war"})

        if "dotnet" in detected_stacks:
            excluded_dirs.update({"bin", "obj", "packages", ".vs"})
            excluded_extensions.update({".dll", ".exe", ".pdb"})

        if "go" in detected_stacks:
            excluded_dirs.update({"vendor", "bin"})

        if "rust" in detected_stacks:
            excluded_dirs.update({"target", "Cargo.lock"})

        if "php" in detected_stacks:
            excluded_dirs.update({"vendor", "cache"})

        if "ruby" in detected_stacks:
            excluded_dirs.update({"vendor", "coverage"})

        if "cpp" in detected_stacks:
            excluded_dirs.update(
                {
                    "build",
                    "cmake-build-debug",
                    "cmake-build-release",
                    ".vs",
                    "Debug",
                    "Release",
                    "x64",
                }
            )
            excluded_extensions.update({".o", ".obj", ".exe", ".dll", ".so", ".dylib"})

        if "swift" in detected_stacks:
            excluded_dirs.update({".build", "build", "DerivedData"})

        if "kotlin" in detected_stacks:
            excluded_dirs.update({"build", ".gradle", ".idea"})
            excluded_extensions.update({".class", ".jar"})

        return {
            "directories": excluded_dirs,
            "files": excluded_files,
            "extensions": excluded_extensions,
        }

    def should_analyze_file(self, file_path: str, project_path: str = "") -> bool:
        """
        Universal method to determine if a file should be analyzed.
        Combines simple directory exclusions with content-based detection.

        Args:
            file_path: Path to the file to check
            project_path: Project root path (for relative path calculation)

        Returns:
            True if file should be analyzed, False if it should be excluded
        """
        import os
        from pathlib import Path

        # Get exclusion lists
        exclusions = self.get_simple_exclusions(
            project_path or os.path.dirname(file_path)
        )

        # Convert to Path object for easier manipulation
        path_obj = Path(file_path)
        path_parts_lower = {p.lower() for p in path_obj.parts}

        # Check if file is in an excluded directory (dead simple - just check if name appears in path)
        path_str = str(path_obj).lower()
        for excluded_dir in exclusions["directories"]:
            if excluded_dir.lower() in path_str:
                return False

        # Check excluded files by name
        if path_obj.name.lower() in {f.lower() for f in exclusions["files"]}:
            return False

        # Check excluded extensions
        if path_obj.suffix.lower() in exclusions["extensions"]:
            return False

        # Content-based detection for remaining files
        return not self._is_generated_or_vendor_code(
            file_path, dev_dir_parts=path_parts_lower
        )

    def _is_generated_or_vendor_code(
        self, file_path: str, dev_dir_parts: Set[str] | None = None
    ) -> bool:
        """
        Detect if file is generated or vendor code based on content analysis.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # Read first few lines to check for generation markers
                first_lines = [f.readline().strip() for _ in range(10)]
                content_sample = "\n".join(first_lines)

            # Check for generation markers
            generation_markers = [
                "// Generated by",
                "/* Generated by",
                "# Generated by",
                "@generated",
                "// This file is auto-generated",
                "/* This file is auto-generated",
                "# This file is auto-generated",
                "// DO NOT EDIT",
                "/* DO NOT EDIT",
                "# DO NOT EDIT",
                "// Code generated by",
                "/* Code generated by",
                "# Code generated by",
                "// WARNING: This file is machine generated",
                "This file was automatically generated",
            ]

            content_lower = content_sample.lower()
            if any(marker.lower() in content_lower for marker in generation_markers):
                return True

            # Check for minified code (very long lines, no spaces around operators)
            if any(len(line) > 500 and " " not in line[:100] for line in first_lines):
                return True

            # Check for vendor/library signatures
            vendor_markers = [
                "copyright",
                "licence",
                "license",
                "all rights reserved",
                "jquery",
                "lodash",
                "bootstrap",
                "foundation",
                "angular",
                "react",
                "vue",
                "webpack",
                "babel",
            ]

            if any(marker in content_lower for marker in vendor_markers):
                # Additional check: if it's in a clearly non-vendor location, keep it
                path_lower = file_path.lower()
                in_dev_dir = any(
                    dev_dir in path_lower
                    for dev_dir in ["/src/", "/app/", "/components/", "/pages/"]
                )
                # Also check by path parts for robustness across platforms
                if dev_dir_parts is None:
                    dev_dir_parts = set()
                if in_dev_dir or (
                    dev_dir_parts & {"src", "app", "components", "pages"}
                ):
                    return False
                return True

        except (IOError, UnicodeDecodeError, PermissionError):
            # If we can't read the file, err on the side of analyzing it
            pass

        return False


def main():
    """Command-line interface for tech stack detection."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect project technology stack")
    parser.add_argument("project_path", help="Path to project root")
    parser.add_argument(
        "--format", choices=["json", "report"], default="report", help="Output format"
    )

    args = parser.parse_args()

    detector = TechStackDetector()
    detected_stacks = detector.detect_tech_stack(args.project_path)
    exclusions = detector.get_simple_exclusions(args.project_path)

    if args.format == "json":
        result = {"detected_tech_stacks": detected_stacks, "exclusions": exclusions}
        print(json.dumps(result, indent=2))
    else:
        # Human-readable report
        print(f"Tech Stack Analysis: {args.project_path}")
        print("=" * 50)

        print("\nDetected Tech Stacks:")
        for stack_id in detected_stacks:
            stack_config = detector.tech_stacks[stack_id]
            print(
                f"  • {stack_config.name} ({', '.join(stack_config.primary_languages)})"
            )

        print("\nExclusion Summary:")
        print(f"  • {len(exclusions['directories'])} excluded directories")
        print(f"  • {len(exclusions['files'])} excluded files")
        print(f"  • {len(exclusions['extensions'])} excluded extensions")

        if not detected_stacks:
            print("\n⚠️  No specific tech stack detected. Using universal patterns.")


if __name__ == "__main__":
    main()
