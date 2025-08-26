#!/usr/bin/env python3
"""
ChromaDB Indexing Hook for Claude Code PostToolUse Events

This hook triggers ChromaDB indexing when files are modified via Write, Edit, or MultiEdit tools.
Runs in background to avoid blocking Claude Code operations.

Usage: Called automatically by Claude Code when PostToolUse events match Write|Edit|MultiEdit
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional


def parse_hook_input() -> Dict[str, Any]:
    """Parse JSON input from Claude Code hook system."""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing hook input: {e}", file=sys.stderr)
        return {}


def extract_modified_files(hook_data: Dict[str, Any]) -> List[str]:
    """Extract file paths from PostToolUse hook data."""
    modified_files = []

    tool_name = hook_data.get("tool_name", "")
    tool_input = hook_data.get("tool_input", {})
    tool_response = hook_data.get("tool_response", {})

    try:
        if tool_name == "Write":
            # Write tool: single file
            file_path = tool_input.get("file_path")
            if file_path and tool_response.get("success"):
                modified_files.append(file_path)

        elif tool_name == "Edit":
            # Edit tool: single file
            file_path = tool_input.get("file_path")
            if file_path and tool_response.get("success"):
                modified_files.append(file_path)

        elif tool_name == "MultiEdit":
            # MultiEdit tool: single file with multiple edits
            file_path = tool_input.get("file_path")
            if file_path and tool_response.get("success"):
                modified_files.append(file_path)

    except Exception as e:
        print(f"Error extracting file paths: {e}", file=sys.stderr)

    return modified_files


def get_project_root() -> Optional[str]:
    """Get project root from CLAUDE_PROJECT_DIR environment variable."""
    return os.environ.get("CLAUDE_PROJECT_DIR")


def is_indexing_enabled(project_root: str) -> bool:
    """Check if ChromaDB indexing is enabled for this project."""
    try:
        ci_registry = Path(project_root) / ".ci-registry"
        config_file = ci_registry / "ci_config.json"

        return ci_registry.exists() and config_file.exists()
    except Exception:
        return False


def start_background_indexing(project_root: str, modified_files: List[str]) -> bool:
    """Start ChromaDB indexing in background process."""
    try:
        # Path to the ChromaDBIndexer script
        indexer_script = (
            Path(project_root) / "shared" / "ci" / "core" / "chromadb_indexer.py"
        )

        if not indexer_script.exists():
            print(
                f"ChromaDB indexer script not found: {indexer_script}", file=sys.stderr
            )
            return False

        # Build command
        cmd = [
            sys.executable,
            str(indexer_script),
            "--project-root",
            project_root,
            "--incremental",
        ]

        # Add modified files
        if modified_files:
            cmd.extend(["--files"] + modified_files)

        # Start background process with proper detachment
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # Detach from parent process
            cwd=project_root,
        )

        return True

    except Exception as e:
        print(f"Failed to start background indexing: {e}", file=sys.stderr)
        return False


def log_hook_activity(project_root: str, message: str) -> None:
    """Log hook activity to CI registry logs."""
    try:
        log_dir = Path(project_root) / ".ci-registry" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "chromadb_hooks.log"

        with open(log_file, "a") as f:
            import datetime

            timestamp = datetime.datetime.now().isoformat()
            f.write(f"{timestamp} - {message}\n")

    except Exception:
        # Silently ignore logging failures
        pass


def main():
    """Main hook entry point."""
    # Parse input from Claude Code
    hook_data = parse_hook_input()

    if not hook_data:
        # No input data, exit silently
        sys.exit(0)

    # Get project root
    project_root = get_project_root()
    if not project_root:
        # No project root available, exit silently
        sys.exit(0)

    # Check if indexing is enabled
    if not is_indexing_enabled(project_root):
        # Indexing not enabled, exit silently
        sys.exit(0)

    # Extract modified files
    modified_files = extract_modified_files(hook_data)

    if not modified_files:
        # No files to index, exit silently
        sys.exit(0)

    # Log activity
    tool_name = hook_data.get("tool_name", "Unknown")
    log_message = f"Hook triggered by {tool_name}, indexing {len(modified_files)} file(s): {', '.join(modified_files)}"
    log_hook_activity(project_root, log_message)

    # Start background indexing
    success = start_background_indexing(project_root, modified_files)

    if success:
        log_hook_activity(
            project_root,
            f"Background indexing started for {len(modified_files)} file(s)",
        )
    else:
        log_hook_activity(
            project_root,
            f"Failed to start background indexing for {len(modified_files)} file(s)",
        )

    # Always exit successfully to avoid blocking Claude Code
    sys.exit(0)


if __name__ == "__main__":
    main()
