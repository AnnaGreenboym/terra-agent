"""
All Claude prompt templates live here.
Keeping them separate means you can iterate on wording
without touching execution logic.
"""

SYSTEM_PROMPT = (
    "You are a senior DevOps and Terraform engineer. "
    "Return ONLY raw Terraform HCL code — no markdown, no explanations, no ``` blocks."
)


def build_generate_prompt(user_input: str) -> str:
    return f"""
You are a senior DevOps and Terraform engineer.

Your task is to generate VALID Terraform code for AWS infrastructure.

STRICT RULES:
1. Cloud provider is always AWS.
2. Region must always be: eu-central-1.
3. Use AWS Free Tier-compatible resources wherever possible.
4. Prefer the cheapest available components.
5. Use minimal resources; avoid unnecessary services.

The infrastructure MUST include:
{user_input}

EC2 REQUIREMENTS:
- Amazon Linux AMI
- Free-tier eligible instance type (t2.micro or t3.micro)
- SSH access enabled via security group

TERRAFORM BEST PRACTICES:
- Use resource references instead of hardcoded IDs
- Use descriptive resource names
- Declare dependencies explicitly
- Output the EC2 public IP

OUTPUT FORMAT (CRITICAL):
Return ONLY raw Terraform HCL. No explanations, no comments outside blocks,
no markdown, no ``` fences. Start directly with:

provider "aws"

End with the final closing brace.
""".strip()


def build_fix_prompt(
    original_prompt: str,
    broken_code: str,
    failed_step: str,
    error_output: str,
) -> str:
    return f"""
The Terraform you generated failed validation.

Original request:
{original_prompt}

Current (broken) Terraform:
{broken_code}

Failed step: terraform {failed_step}

Error output:
{error_output}

Fix the code so it satisfies the original request. Keep:
- Cloud provider: AWS
- Region: eu-central-1
- Infrastructure minimal, cheap, and Free Tier-friendly

Return ONLY the corrected raw Terraform HCL. No markdown, no explanations.
""".strip()
