"""
Git operations: branch, copy files, commit, push.
All subprocess calls go through run_git() for uniform error handling.
"""

import os
import shutil
import subprocess

from config import GITHUB_REPO_PATH, GENERATED_FOLDER, CI_WORKFLOW_FILENAME, WORKFLOWS_DIR


# ── Low-level git helper ──────────────────────────────────────────────────────

def _run_git(args: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        ["git"] + args,
        cwd=GITHUB_REPO_PATH,
        capture_output=True,
        text=True,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0, output


# ── Branch management ─────────────────────────────────────────────────────────

def _branch_exists(branch_name: str) -> bool:
    _, output = _run_git(["branch", "--list", branch_name])
    return bool(output.strip())


def _create_or_switch_branch(branch_name: str) -> None:
    if _branch_exists(branch_name):
        print(f"[Git] Branch '{branch_name}' already exists — switching to it...")
        ok, output = _run_git(["checkout", branch_name])
    else:
        print(f"[Git] Creating new branch '{branch_name}'...")
        ok, output = _run_git(["checkout", "-b", branch_name])

    if not ok:
        raise RuntimeError(f"[Git] Failed to create/switch branch:\n{output}")

    print(f"[Git] ✓ On branch '{branch_name}'")


# ── File copying ──────────────────────────────────────────────────────────────

def _copy_generated_files() -> None:
    """Copy every file from GENERATED_FOLDER into the root of GITHUB_REPO_PATH."""
    if not os.path.exists(GENERATED_FOLDER):
        raise FileNotFoundError(f"[Git] Generated folder not found: {GENERATED_FOLDER}")

    copied = 0
    for filename in os.listdir(GENERATED_FOLDER):
        src = os.path.join(GENERATED_FOLDER, filename)
        dst = os.path.join(GITHUB_REPO_PATH, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"[Git] Copied {filename} → {GITHUB_REPO_PATH}/")
            copied += 1

    if copied == 0:
        raise FileNotFoundError(f"[Git] No files found in '{GENERATED_FOLDER}'")

    print(f"[Git] ✓ {copied} file(s) copied.")


# ── Commit & push ─────────────────────────────────────────────────────────────

def _commit(commit_message: str) -> None:
    print("\n[Git] Staging all changes...")
    ok, output = _run_git(["add", "."])
    if not ok:
        raise RuntimeError(f"[Git] Failed to stage changes:\n{output}")

    print(f"[Git] Committing: '{commit_message}'")
    ok, output = _run_git(["commit", "-m", commit_message])
    if not ok:
        if "nothing to commit" in output:
            print("[Git] ✓ Nothing new to commit.")
            return
        raise RuntimeError(f"[Git] Commit failed:\n{output}")

    print("[Git] ✓ Commit successful.")


def _push(branch_name: str) -> None:
    print(f"\n[Git] Pushing '{branch_name}' to origin...")
    ok, output = _run_git(["push", "-u", "origin", branch_name])
    if not ok:
        raise RuntimeError(f"[Git] Push failed:\n{output}")
    print(f"[Git] ✓ Branch '{branch_name}' pushed successfully.")


# ── CI workflow planting ──────────────────────────────────────────────────────

def _copy_ci_workflow(ci_yml_source: str) -> None:
    """
    Copy the provided CI YAML file into .github/workflows/ inside the terraform repo.
    Creates the directory if it doesn't exist.
    """
    if not os.path.isfile(ci_yml_source):
        raise FileNotFoundError(f"[Git] CI workflow file not found: {ci_yml_source}")

    os.makedirs(WORKFLOWS_DIR, exist_ok=True)

    dst = os.path.join(WORKFLOWS_DIR, CI_WORKFLOW_FILENAME)
    shutil.copy2(ci_yml_source, dst)
    print(f"[Git] CI workflow → {dst}")


# ── Public API ────────────────────────────────────────────────────────────────

def _normalize_branch_name(branch_name: str) -> str:
    """
    Ensure the branch matches the CI trigger pattern (ai/* or ai_*).
    If the user types 'my-feature' we push 'ai/my-feature'.
    If they already typed 'ai/...' or 'ai_...' we leave it alone.
    """
    if branch_name.startswith("ai/") or branch_name.startswith("ai_"):
        return branch_name
    return f"ai/{branch_name}"


def git_flow(branch_name: str, commit_message: str, ci_yml_source: str) -> None:
    """Full flow: branch → copy .tf files → plant CI workflow → commit → push."""
    branch_name = _normalize_branch_name(branch_name)
    print(f"[Git] Using branch: '{branch_name}'")
    _create_or_switch_branch(branch_name)
    _copy_generated_files()
    _copy_ci_workflow(ci_yml_source)
    _commit(commit_message)
    _push(branch_name)
