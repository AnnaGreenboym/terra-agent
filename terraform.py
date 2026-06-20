"""
Terraform file management and validation.

Responsibilities:
- Write / read the generated .tf file
- Run the terraform validation pipeline (fmt → init → validate → plan)
- Orchestrate the generate-and-fix loop (calls claude_client + prompts)
"""

import os
import subprocess
from dataclasses import dataclass

from config import GENERATED_FOLDER, TF_FILE
from claude_client import ask_claude
from prompts import build_generate_prompt, build_fix_prompt


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    success: bool
    failed_step: str | None   # e.g. "validate"; None when all steps pass
    output: str               # full stdout/stderr from every step


# ── File helpers ──────────────────────────────────────────────────────────────

def save_tf(code: str) -> None:
    os.makedirs(GENERATED_FOLDER, exist_ok=True)
    with open(TF_FILE, "w", encoding="utf-8") as f:
        f.write(code)


def read_tf() -> str:
    with open(TF_FILE, "r", encoding="utf-8") as f:
        return f.read()


# ── Subprocess helper ─────────────────────────────────────────────────────────

def _run_terraform(args: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        ["terraform"] + args,
        cwd=GENERATED_FOLDER,
        capture_output=True,
        text=True,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0, output


# ── Validation pipeline ───────────────────────────────────────────────────────

_PIPELINE_STEPS = ["fmt -no-color", "init -no-color", "validate -no-color", "plan -no-color"]


def validate_terraform() -> ValidationResult:
    """
    Run fmt → init → validate → plan.
    Stops at the first failure and reports which step broke.
    """
    for step in _PIPELINE_STEPS:
        step_args = step.split()
        step_name = step_args[0]          # "fmt", "init", etc.
        print(f"  Running terraform {step_name}...")

        ok, output = _run_terraform(step_args)
        if not ok:
            print(f"  ✗ Failed at terraform {step_name}\n{output}")
            return ValidationResult(success=False, failed_step=step_name, output=output)

        print(f"  ✓ terraform {step_name} passed")

    return ValidationResult(success=True, failed_step=None, output="All steps passed")


# ── Generate-and-fix orchestration ───────────────────────────────────────────

def generate_terraform(user_input: str, max_attempts: int) -> bool:
    """
    1. Ask Claude to generate initial Terraform.
    2. Validate; on failure ask Claude to fix and retry — up to *max_attempts* times.
    Returns True if a valid configuration was produced, False otherwise.
    """
    generate_prompt = build_generate_prompt(user_input)

    print("\n[Terraform] Asking Claude to generate Terraform...")
    save_tf(ask_claude(generate_prompt))
    print("[Terraform] Initial file written.")

    for attempt in range(1, max_attempts + 1):
        print(f"\n[Terraform] ── Attempt {attempt}/{max_attempts} ──")
        result = validate_terraform()

        if result.success:
            print("\n[Terraform] ✓ Terraform is valid.")
            return True

        fix_prompt = build_fix_prompt(
            original_prompt=generate_prompt,
            broken_code=read_tf(),
            failed_step=result.failed_step,
            error_output=result.output,
        )
        print("\n[Terraform] Asking Claude to fix the error...")
        save_tf(ask_claude(fix_prompt))
        print("[Terraform] main.tf updated.")

    print("\n[Terraform] ✗ Could not produce valid Terraform after max attempts.")
    return False
