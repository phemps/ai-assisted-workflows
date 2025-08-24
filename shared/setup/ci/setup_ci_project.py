#!/usr/bin/env python3
"""
setup_ci_project.py v1.0

Project-specific setup for continuous improvement framework.
Configures registry, GitHub Actions, and integrates with existing project structure.
Follows the pattern from dev-monitoring setup_project.py equivalent.
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional


def run_command(cmd, shell=False, cwd=None):
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, shell=shell, cwd=cwd
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def detect_project_languages(
    project_dir: str, exclusion_patterns: Optional[List[str]] = None
) -> List[str]:
    """Detect programming languages in the project using TechStackDetector."""
    try:
        # Import the shared TechStackDetector
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core" / "utils"))
        from tech_stack_detector import TechStackDetector

        # Use TechStackDetector to get detected tech stacks
        detector = TechStackDetector()
        detected_stacks = detector.detect_tech_stack(project_dir)

        # Extract languages from detected tech stacks
        languages = set()
        for stack_id in detected_stacks:
            if stack_id in detector.tech_stacks:
                stack_config = detector.tech_stacks[stack_id]
                languages.update(stack_config.primary_languages)

        return sorted(list(languages))

    except ImportError:
        # Fallback to original logic if shared utility not available
        print("Warning: Using fallback language detection", file=sys.stderr)
        language_patterns = {
            "python": ["**/*.py"],
            "javascript": ["**/*.js", "**/*.jsx"],
            "typescript": ["**/*.ts", "**/*.tsx"],
            "java": ["**/*.java"],
            "go": ["**/*.go"],
            "rust": ["**/*.rs"],
            "php": ["**/*.php"],
            "ruby": ["**/*.rb"],
            "c": ["**/*.c", "**/*.h"],
            "cpp": ["**/*.cpp", "**/*.hpp", "**/*.cc"],
            "csharp": ["**/*.cs"],
        }

        detected = []
        project_path = Path(project_dir)

        for lang, patterns in language_patterns.items():
            for pattern in patterns:
                if list(project_path.glob(pattern)):
                    detected.append(lang)
                    break

        return detected


def create_ci_registry_structure(project_dir: str) -> bool:
    """Create .ci-registry directory structure."""
    print("Creating CI registry structure...")

    ci_registry = Path(project_dir) / ".ci-registry"

    # Create directories
    directories = [
        ci_registry,
        ci_registry / "cache",
        ci_registry / "reports",
        ci_registry / "backups",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory.relative_to(project_dir)}")

    return True


def create_ci_config(
    project_dir: str,
    project_name: str,
    threshold: float,
    auto_refactor: bool,
    languages: List[str],
) -> bool:
    """Create CI configuration file."""
    print("Creating CI configuration...")

    config = {
        "version": "1.0",
        "setup_date": subprocess.run(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True
        ).stdout.strip(),
        "project": {
            "project_name": project_name,
            "languages": languages,
            "analysis": {
                "similarity_threshold": threshold,
                "exact_duplicate_threshold": 1.0,
                "high_similarity_threshold": max(0.8, threshold),
                "medium_similarity_threshold": max(0.6, threshold - 0.2),
                "low_similarity_threshold": max(0.3, threshold - 0.4),
                "analysis_mode": "incremental",
                "batch_size": 100,
                "enable_caching": True,
            },
            "automation": {
                "auto_refactor_enabled": auto_refactor,
                "max_auto_fix_complexity": "low",
                "require_human_review": ["cross_module", "high_risk", "architectural"],
                "github_integration": True,
            },
            "exclusions": {
                "directories": [
                    "node_modules",
                    ".git",
                    "__pycache__",
                    "dist",
                    "build",
                    "target",
                    "test_codebase",
                ],
                "files": ["*.min.js", "*.bundle.js", "*.map"],
                "patterns": ["test/**", "tests/**", "**/*.test.*", "**/*.spec.*"],
            },
            "quality_gates": {
                "enabled": True,
                "auto_detect": True,
                "custom_commands": [],
            },
            "metrics": {"collection_enabled": True, "retention_days": 90},
        },
        "registry": {
            "enable_caching": True,
            "cache_ttl_hours": 24,
            "max_entries": 10000,
            "backup_enabled": True,
            "backup_frequency_hours": 6,
            "compression_enabled": True,
        },
    }

    # Save unified CI configuration
    ci_config_file = Path(project_dir) / ".ci-registry" / "ci_config.json"
    with open(ci_config_file, "w") as f:
        json.dump(config, f, indent=2)

    print(
        f"  ✓ Created unified CI configuration: {ci_config_file.relative_to(project_dir)}"
    )
    return True


def create_github_workflows(project_dir: str, project_name: str) -> bool:
    """Create GitHub Actions workflows for CI."""
    print("Creating GitHub Actions workflows...")

    workflows_dir = Path(project_dir) / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Main continuous improvement workflow
    ci_workflow = f"""name: Continuous Improvement - Code Duplication Detection

"on":
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

permissions:
  contents: read
  pull-requests: write
  issues: write
  actions: read

jobs:
  duplicate-detection:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608  # v4.1.0
      with:
        fetch-depth: 0  # Full history for comprehensive analysis

    - name: Setup Python
      uses: actions/setup-python@f677139bbe7f9c59b41e40162b753c062f5d49a3  # v5.3.0
      with:
        python-version: '3.9'
        cache: 'pip'

    - name: Install CI dependencies
      run: |
        python -m pip install --upgrade pip
        pip install numpy<2.0.0
        pip install chromadb==0.4.24
        pip install opentelemetry-api==1.25.0 opentelemetry-sdk==1.25.0 opentelemetry-exporter-otlp-proto-grpc==1.25.0
        pip install transformers torch sentence-transformers scipy multilspy

    - name: Read project languages
      id: languages
      run: |
        if [ -f ".ci-registry/ci_config.json" ]; then
          languages=$(python -c "
          import json, sys
          try:
              with open('.ci-registry/ci_config.json') as f:
                  config = json.load(f)
              langs = config.get('project', {{}}).get('languages', [])
              print(','.join(langs))
          except Exception as e:
              print('', file=sys.stderr)  # Empty fallback
              sys.exit(0)
          ") || languages=""
          echo "detected_languages=$languages" >> $GITHUB_OUTPUT
          echo "Detected project languages: $languages"
        else
          echo "detected_languages=" >> $GITHUB_OUTPUT
          echo "No CI config found - skipping language-specific installations"
        fi

    - name: Setup Go
      if: contains(steps.languages.outputs.detected_languages, 'go')
      uses: actions/setup-go@0a12ed9d6a96ab950c8f026ed9f722fe0da7ef32  # v5.2.0
      with:
        go-version: '1.21'
        cache: true

    - name: Setup .NET
      if: contains(steps.languages.outputs.detected_languages, 'csharp')
      uses: actions/setup-dotnet@6bd8b7f7774af54e05809fcc5431931b3eb1ddee  # v4.1.0
      with:
        dotnet-version: '8.0'

    - name: Install language server dependencies
      run: |
        # Install language servers based on detected languages
        languages="${{{{ steps.languages.outputs.detected_languages }}}}"
        echo "Installing language servers for: $languages"

        if [[ "$languages" == *"go"* ]]; then
          echo "Installing Go language server (gopls)..."
          go install golang.org/x/tools/gopls@latest
          echo "$HOME/go/bin" >> $GITHUB_PATH

          # Validate installation
          if command -v gopls >/dev/null 2>&1; then
            go version
            gopls version
            echo "✅ gopls installed successfully"
          else
            echo "❌ gopls installation failed" >&2
            exit 1
          fi
        else
          echo "Skipping Go language server installation"
        fi

        if [[ "$languages" == *"csharp"* ]]; then
          echo "Verifying .NET installation..."
          dotnet --version
        else
          echo "Skipping .NET language server verification"
        fi

        echo "Language server setup complete"

    - name: Verify multilspy installation
      run: |
        python -c "import multilspy; print('multilspy library installed successfully')"

    - name: Get changed files
      id: changed-files
      run: |
        if [ "${{{{ github.event_name }}}}" == "pull_request" ]; then
          git diff --name-only ${{{{ github.event.pull_request.base.sha }}}}..${{{{ github.sha }}}} > changed_files.txt
        else
          git diff --name-only HEAD~1 HEAD > changed_files.txt
        fi
        echo "files=$(cat changed_files.txt | tr '\\n' ' ')" >> $GITHUB_OUTPUT
        echo "Changed files:"
        cat changed_files.txt

    - name: Ensure CI registry directory exists
      run: |
        mkdir -p .ci-registry/reports
        mkdir -p .ci-registry/cache
        mkdir -p .ci-registry/backups

    - name: Check initial indexing status
      id: indexing-check
      run: |
        if [ -f ".ci-registry/ci_config.json" ]; then
          cd shared && PYTHONPATH=.. python ci/core/chromadb_storage.py \\
            --project-root .. \\
            --check-indexing \\
            --output json > ../indexing_status.json

          # Parse indexing status with inline Python
          initial_completed=$(python -c "import json; data=json.load(open('indexing_status.json')); print(str(data.get('initial_index_completed', False)).lower())" 2>/dev/null || echo "false")

          echo "initial_completed=$initial_completed" >> $GITHUB_OUTPUT
          echo "Initial indexing completed: $initial_completed"

          if [ "$initial_completed" = "true" ]; then
            echo "Initial indexing already completed - proceeding with incremental analysis"
          else
            echo "Initial indexing required - will run full scan first"
          fi
        else
          echo "initial_completed=false" >> $GITHUB_OUTPUT
          echo "No CI config found - assuming fresh setup"
        fi

    - name: Run initial full scan
      if: steps.indexing-check.outputs.initial_completed == 'false'
      run: |
        echo "Running initial full codebase scan..."
        cd shared && PYTHONPATH=.. python ci/core/chromadb_storage.py \\
          --project-root .. \\
          --full-scan

        echo "Initial scan completed - ChromaDB now contains full codebase index"

    - name: Run duplicate detection
      run: |
        cd shared && PYTHONPATH=.. python ci/integration/orchestration_bridge.py \\
          --project-root .. \\
          --changed-files ${{{{ steps.changed-files.outputs.files }}}}

    - name: Upload analysis results
      if: always()
      uses: actions/upload-artifact@26f96dfa697d77e81fd5907df203aa23a56210a8  # v4.3.0
      with:
        name: duplication-analysis
        path: |
          .ci-registry/reports/
          .ci-registry/baseline-duplicates.json
        retention-days: 30

    - name: Collect diagnostic information
      if: failure()
      run: |
        echo "=== Diagnostic Information ==="
        echo "Python Version: $(python --version)"
        echo "Current Directory: $(pwd)"
        echo "Available Python packages:"
        pip list | grep -E "(chromadb|transformers|torch|multilspy)"

        # Check for log files
        if [ -d ".ci-registry/logs" ]; then
          echo "CI Registry logs:"
          ls -la .ci-registry/logs/
        fi

    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea  # v7.0.1
      with:
        script: |
          const fs = require('fs');
          const path = '.ci-registry/reports/latest-analysis.json';

          if (fs.existsSync(path)) {{
            const analysis = JSON.parse(fs.readFileSync(path, 'utf8'));
            const duplicateCount = analysis.findings?.length || 0;
            const summary = analysis.summary || {{}};

            const status = duplicateCount > 0 ?
              'Code duplications detected. Review analysis artifacts for details.' :
              'No significant code duplication detected.';

            const comment = '## Code Duplication Analysis Results\\n\\n' +
              'Project: {project_name}\\n' +
              'Analysis Date: ' + (analysis.analysis_date || 'Unknown') + '\\n' +
              'Duplicates Found: ' + duplicateCount + '\\n' +
              'Similarity Threshold: ' + (analysis.config?.similarity_threshold || '0.85') + '\\n\\n' +
              '### Summary\\n' +
              '- Automatic Fixes: ' + (summary.automatic_fixes || 0) + '\\n' +
              '- GitHub Issues: ' + (summary.github_issues || 0) + '\\n' +
              '- Skipped: ' + (summary.skipped || 0) + '\\n' +
              '- Errors: ' + (summary.errors || 0) + '\\n\\n' +
              'Status: ' + status + '\\n\\n' +
              'Analysis completed by Continuous Improvement Framework.';

            github.rest.issues.createComment({{
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            }});
          }}

    - name: Check analysis results
      run: |
        if [ -f ".ci-registry/reports/latest-analysis.json" ]; then
          echo "Analysis completed successfully"
          cat .ci-registry/reports/latest-analysis.json
        else
          echo "No analysis results found"
        fi
"""

    ci_workflow_file = workflows_dir / "continuous-improvement.yml"
    with open(ci_workflow_file, "w") as f:
        f.write(ci_workflow)

    print(f"  ✓ Created {ci_workflow_file.relative_to(project_dir)}")

    return True


def setup_serena_mcp_integration(project_dir: str) -> bool:
    """Setup Serena MCP integration for the project."""
    print("Setting up Serena MCP integration...")

    # Test if Serena MCP is available
    success, stdout, stderr = run_command(
        ["uvx", "--from", "git+https://github.com/oraios/serena", "serena", "--version"]
    )

    if not success:
        print(f"  ⚠️  Serena MCP not available: {stderr}")
        print(
            "  Run manually later: claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server"
        )
        return False

    print(f"  ✓ Serena MCP available: {stdout}")

    # Add instruction for manual MCP setup (since we can't modify claude config from here)
    mcp_setup_file = Path(project_dir) / ".ci-registry" / "mcp-setup.md"
    mcp_content = f"""# Serena MCP Setup Instructions

To complete continuous improvement setup, add Serena MCP to Claude:

```bash
# Remove existing serena MCP if present
claude mcp remove serena

# Add Serena MCP for this project
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ci-analyzer --project {project_dir}
```

## Verification

Test the setup:

```bash
# Check if Serena MCP is connected
claude mcp list

# Test code analysis
python shared/ci/core/semantic_duplicate_detector.py --test
```

## Integration Status

- ✅ Serena available via uvx
- ⏳ Manual MCP configuration required
- ⏳ Project-specific context setup needed

Run the commands above to complete integration.
"""

    with open(mcp_setup_file, "w") as f:
        f.write(mcp_content)

    print(
        f"  ✓ Created MCP setup instructions: {mcp_setup_file.relative_to(project_dir)}"
    )
    return True


def update_project_claude_md(project_dir: str, languages: List[str]) -> bool:
    """Update project CLAUDE.md with CI integration notes."""
    print("Updating project CLAUDE.md...")

    claude_md_path = Path(project_dir) / "CLAUDE.md"

    ci_section = f"""
## Continuous Improvement Integration

**Code Duplication Detection**: Automated via GitHub Actions and Claude Code agents

### System Status
- **Languages Monitored**: {', '.join(languages) if languages else 'Auto-detected'}
- **Registry**: `.ci-registry/` (SQLite database with symbol tracking)
- **Analysis Threshold**: Configurable in `.ci-registry/ci_config.json`
- **GitHub Integration**: Workflow configured for PR/push analysis

### Available Commands
```bash
# Check system status
claude /continuous-improvement-status

# Manual duplicate analysis
python shared/ci/integration/orchestration_bridge.py

# Generate metrics report
python shared/ci/metrics/ci_metrics_collector.py report

# Registry management
python shared/ci/core/registry_manager.py --status
```

### Workflow Integration
- **Automatic**: GitHub Actions analyze changes and create issues for complex duplicates
- **CTO Escalation**: Complex refactoring delegated to `claude /todo-orchestrate`
- **Quality Gates**: Integrated with existing project quality checks
- **Metrics**: Performance tracking in `.ci-registry/reports/`

### Configuration
Edit `.ci-registry/ci_config.json` to adjust:
- Similarity thresholds (exact: 1.0, high: 0.8, medium: 0.6)
- Auto-refactor settings (enabled: false by default)
- Language-specific exclusions
- Quality gate integration

The system uses fail-fast architecture requiring MCP, CodeBERT, and Faiss dependencies.
"""

    if claude_md_path.exists():
        # Read existing content
        with open(claude_md_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Check if CI section already exists
        if "## Continuous Improvement Integration" in existing_content:
            print("  ✓ CI section already exists in CLAUDE.md")
            return True

        # Append CI section
        with open(claude_md_path, "a", encoding="utf-8") as f:
            f.write(ci_section)

        print("  ✓ Updated existing CLAUDE.md with CI integration")
    else:
        # Create new CLAUDE.md with CI section
        with open(claude_md_path, "w", encoding="utf-8") as f:
            f.write(f"# {Path(project_dir).name}\n{ci_section}")

        print("  ✓ Created CLAUDE.md with CI integration")

    return True


def main():
    """Main function for project-specific CI setup."""
    parser = argparse.ArgumentParser(
        description="Setup continuous improvement framework for project"
    )
    parser.add_argument("--project-dir", required=True, help="Project directory path")
    parser.add_argument(
        "--project-name", help="Project name (auto-detected if not provided)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold (default: 0.85)",
    )
    parser.add_argument(
        "--auto-refactor", action="store_true", help="Enable automatic refactoring"
    )

    args = parser.parse_args()

    # Validate project directory
    if not os.path.isdir(args.project_dir):
        print(f"❌ Project directory not found: {args.project_dir}")
        return 1

    project_name = args.project_name or Path(args.project_dir).name

    print(f"Setting up Continuous Improvement for: {project_name}")
    print(f"Project directory: {args.project_dir}")
    print(f"Similarity threshold: {args.threshold}")
    print(f"Auto-refactor: {'enabled' if args.auto_refactor else 'disabled'}")

    try:
        # Detect project languages
        print("\nDetecting project languages...")
        # Use standard exclusion patterns
        exclusion_patterns = [
            "node_modules",
            ".git",
            "__pycache__",
            "dist",
            "build",
            "target",
            "test_codebase",
        ]
        languages = detect_project_languages(args.project_dir, exclusion_patterns)
        if languages:
            print(f"  ✓ Detected: {', '.join(languages)}")
        else:
            print("  ⚠️  No common languages detected, will monitor all files")

        # Create CI registry structure
        if not create_ci_registry_structure(args.project_dir):
            return 1

        # Create configuration
        if not create_ci_config(
            args.project_dir,
            project_name,
            args.threshold,
            args.auto_refactor,
            languages,
        ):
            return 1

        # Create GitHub workflows
        if not create_github_workflows(args.project_dir, project_name):
            return 1

        # Setup MCP integration
        setup_serena_mcp_integration(args.project_dir)

        # Update project documentation
        update_project_claude_md(args.project_dir, languages)

        print("\n" + "=" * 60)
        print("🎉 Continuous Improvement Setup Complete!")
        print("\n📋 Summary:")
        print(f"  - Registry: .ci-registry/ created with {len(languages)} languages")
        print(
            f"  - Configuration: Threshold {args.threshold}, auto-refactor {'on' if args.auto_refactor else 'off'}"
        )
        print("  - GitHub Actions: Workflow configured for duplicate detection")
        print("  - Documentation: CLAUDE.md updated with CI integration")

        print("\n🚀 Next Steps:")
        print("  1. Complete MCP setup: cat .ci-registry/mcp-setup.md")
        print(
            "  2. Initialize registry: python shared/ci/core/registry_manager.py --init"
        )
        print("  3. Test system: claude /continuous-improvement-status")
        print("  4. Run analysis: python shared/ci/integration/orchestration_bridge.py")

        return 0

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
