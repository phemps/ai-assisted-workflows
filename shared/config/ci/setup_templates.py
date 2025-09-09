#!/usr/bin/env python3
"""
Template Setup Utility for Continuous Improvement.

Replaces inline file creation with template copying and variable substitution.
"""

import shutil
from pathlib import Path


class TemplateSetup:
    """Utility for setting up continuous improvement configuration from templates."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        # Ensure project root exists
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.templates_dir = Path(__file__).parent / "templates"
        self.workflows_dir = Path(__file__).parent / "github-workflows"

    def setup_config(
        self, project_name: str, threshold: float = 0.85, auto_refactor: bool = False
    ) -> bool:
        """
        Set up continuous improvement configuration using templates.

        Args:
            project_name: Name of the project
            threshold: Duplicate detection threshold
            auto_refactor: Whether to enable automatic refactoring

        Returns
        -------
            True if setup succeeded, False otherwise
        """
        try:
            # Create .ci-registry directory
            ci_registry_dir = self.project_root / ".ci-registry"
            ci_registry_dir.mkdir(exist_ok=True)

            # Setup config.json from template
            self._setup_config_json(project_name, threshold, auto_refactor)

            # Setup GitHub workflows
            self._setup_github_workflows()

            return True

        except Exception as e:
            print(f"Setup failed: {e}")
            return False

    def _setup_config_json(
        self, project_name: str, threshold: float, auto_refactor: bool
    ) -> None:
        """Set up config.json from template."""
        template_path = self.templates_dir / "config.json.template"
        target_path = self.project_root / ".ci-registry" / "config.json"

        # Read template
        template_content = template_path.read_text()

        # Substitute variables
        config_content = template_content.replace("{{PROJECT_NAME}}", project_name)
        config_content = config_content.replace("{{THRESHOLD}}", str(threshold))
        config_content = config_content.replace(
            "{{AUTO_REFACTOR}}", str(auto_refactor).lower()
        )

        # Write config
        target_path.write_text(config_content)
        print(f"✅ Created config.json at {target_path}")

    def _setup_github_workflows(self) -> None:
        """Set up GitHub workflows from templates."""
        # Create .github/workflows directory
        workflows_target = self.project_root / ".github" / "workflows"
        workflows_target.mkdir(parents=True, exist_ok=True)

        # Copy workflow files
        for workflow_file in self.workflows_dir.glob("*.yml"):
            target_file = workflows_target / workflow_file.name
            shutil.copy2(workflow_file, target_file)
            print(f"✅ Created workflow {workflow_file.name} at {target_file}")


def main():
    """Run template setup from the command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup continuous improvement from templates"
    )
    parser.add_argument("--project-name", required=True, help="Name of the project")
    parser.add_argument(
        "--threshold", type=float, default=0.85, help="Duplicate detection threshold"
    )
    parser.add_argument(
        "--auto-refactor", action="store_true", help="Enable automatic refactoring"
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    setup = TemplateSetup(args.project_root)
    success = setup.setup_config(args.project_name, args.threshold, args.auto_refactor)

    if success:
        print("\n🎉 Continuous improvement setup complete!")
        print("📁 Configuration: .ci-registry/config.json")
        print("⚙️ GitHub workflows: .github/workflows/")
        print("🔧 Edit .ci-registry/config.json to customize settings")
    else:
        print("❌ Setup failed - check error messages above")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
