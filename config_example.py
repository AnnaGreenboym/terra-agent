import os

# ── Claude API ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]          # required; fail fast
MODEL: str             = "claude-sonnet-4-6"

# ── Terraform ─────────────────────────────────────────────────────────────────
GENERATED_FOLDER: str  = "generated"
TF_FILE: str           = os.path.join(GENERATED_FOLDER, "main.tf")
MAX_FIX_ATTEMPTS: int  = 5

# ── GitHub ────────────────────────────────────────────────────────────────────
GITHUB_REPO_PATH: str  = os.environ.get("GITHUB_REPO_PATH", ".")
