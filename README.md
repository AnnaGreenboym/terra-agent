# 🤖 Terra-Agent

An AI-powered CLI tool that generates, validates, and deploys Terraform infrastructure to AWS — fully automated from a plain English description.

You describe the infrastructure. Claude writes the Terraform. The agent validates it, auto-fixes any errors, and pushes it to your Terraform repo along with a ready-to-run CI/CD pipeline.

---

## How It Works

```
You type a description
        ↓
Claude generates Terraform HCL
        ↓
Agent runs: fmt → init → validate → plan
        ↓ (auto-fix loop on failure, up to 5 attempts)
Valid .tf pushed to Terraform repo
        ↓
CI workflow planted at .github/workflows/
        ↓
GitHub Actions: validates → cost estimate → security scan → opens PR
```

---

## Project Structure

```
terra-agent/
├── main.py              # Entry point — collects inputs, orchestrates the flow
├── config.py            # All configuration (paths, model, limits)
├── config_example.py    # Safe template to copy → config.py
├── prompts.py           # All Claude prompt templates
├── claude_client.py     # Anthropic SDK wrapper
├── terraform.py         # Terraform file I/O + validation pipeline + fix loop
├── git_handler.py       # Branch, copy, commit, push
├── terraform_ci.yml     # CI workflow planted into the Terraform repo
└── requirements.txt     # anthropic
```

---

## Prerequisites

- Python 3.11+
- [Terraform CLI](https://developer.hashicorp.com/terraform/install) installed and on `PATH`
- Git installed and configured
- An [Anthropic API key](https://console.anthropic.com/)
- A local clone of your Terraform target repo

---

## Setup

**1. Clone this repo**
```bash
git clone https://github.com/your-username/terra-agent.git
cd terra-agent
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure**

Copy the example config and fill in your values:
```bash
cp config_example.py config.py
```

Edit `config.py`:
```python
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]   # or paste directly (don't commit)
GITHUB_REPO_PATH  = "/path/to/your/local/terraform-repo"
```

Or use environment variables:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_REPO_PATH="/path/to/terraform-repo"
```

---

## Usage

```bash
python main.py
```

You will be prompted for three inputs:

```
What Terraform infrastructure should we create?: EC2 instance with a Lambda that runs every 5 minutes
GitHub branch name: my-feature
Commit message: feat: add EC2 and scheduled Lambda
```

The agent will:
1. Generate `main.tf` via Claude
2. Run `terraform fmt → init → validate → plan` — auto-fixing up to 5 times on failure
3. Push the `.tf` file to your Terraform repo on branch `ai/my-feature`
4. Plant `terraform_ci.yml` at `.github/workflows/` in the same commit

> Branch names are automatically prefixed with `ai/` to match the CI trigger pattern. Typing `my-feature` becomes `ai/my-feature`.

---

## CI/CD Pipeline (Terraform repo)

Once the agent pushes, GitHub Actions runs automatically:

| Step | Tool | Behaviour |
|------|------|-----------|
| Checkout | `actions/checkout@v4` | — |
| AWS credentials | `aws-actions/configure-aws-credentials@v4` | Connects to eu-central-1 |
| Terraform init / validate / plan | `hashicorp/setup-terraform@v3` | Blocks on failure |
| Cost estimate | [Infracost](https://www.infracost.io/) | Warn only, never blocks |
| Security scan | [Trivy](https://trivy.dev/) | CRITICAL / HIGH / MEDIUM, warn only |
| Open PR to `main` | `peter-evans/create-pull-request@v6` | Auto-labeled `ai-generated` |

### Required GitHub Secrets (Terraform repo)

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user with read access for `terraform plan` |
| `AWS_SECRET_ACCESS_KEY` | Corresponding secret |
| `INFRACOST_API_KEY` | Free at [infracost.io](https://www.infracost.io/) |
| `GITHUB_TOKEN` | Provided automatically by GitHub Actions |

---

## Configuration Reference

All settings live in `config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | env var | Claude API key |
| `MODEL` | `claude-sonnet-4-6` | Claude model to use |
| `GENERATED_FOLDER` | `generated` | Local folder for generated `.tf` files |
| `MAX_FIX_ATTEMPTS` | `5` | Max auto-fix retries before aborting |
| `GITHUB_REPO_PATH` | env var | Absolute path to local Terraform repo clone |
| `CI_WORKFLOW_FILENAME` | `terraform_ci.yml` | Filename used when planting the workflow |

---

## Security Note

`config.py` contains your API key and local paths — **never commit it**.
It is listed in `.gitignore`. Always use `config_example.py` as the committed template.

---

## Requirements

```
anthropic>=0.40.0
```
