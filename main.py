"""
Entry point for the Terraform AI Agent.

Flow:
  1. Collect user inputs
  2. Generate & validate Terraform (with auto-fix loop)
  3. Push .tf files + CI workflow to the terraform repo
"""

import sys

from config import MAX_FIX_ATTEMPTS
from terraform import generate_terraform
from git_handler import git_flow


def _prompt(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        print(f"✗ '{label}' cannot be empty.")
        sys.exit(1)
    return value


def main() -> None:
    print("=== Terraform AI Agent ===\n")

    user_input     = _prompt("What Terraform infrastructure should we create?")
    branch_name    = _prompt("GitHub branch name")
    commit_message = _prompt("Commit message")
    ci_yml_path    = _prompt("Path to CI workflow YAML file")

    # ── Step 1: Generate & validate Terraform ────────────────────────────────
    print("\n=== Terraform Generation ===")
    if not generate_terraform(user_input, max_attempts=MAX_FIX_ATTEMPTS):
        print("\n✗ Terraform generation failed. Aborting.")
        sys.exit(1)

    # ── Step 2: Push .tf files + CI workflow in one commit ───────────────────
    print("\n=== Git Flow ===")
    try:
        git_flow(branch_name, commit_message, ci_yml_source=ci_yml_path)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"\n✗ Git error: {exc}")
        sys.exit(1)

    print("\n✓ Done — Terraform and CI workflow pushed to GitHub.")


if __name__ == "__main__":
    main()
