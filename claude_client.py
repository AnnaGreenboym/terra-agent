"""
Thin wrapper around the Anthropic SDK.
One job: send a prompt, get back clean HCL text.
"""

import re
import anthropic

from config import ANTHROPIC_API_KEY, MODEL
from prompts import SYSTEM_PROMPT


def _strip_markdown_fences(text: str) -> str:
    """Belt-and-suspenders cleanup in case the model ignores our instructions."""
    text = re.sub(r"^```(?:hcl|terraform)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


# Module-level client — created once, reused across calls.
# Instantiation is deferred to first import, so tests can monkeypatch before importing.
_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def ask_claude(prompt: str, max_tokens: int = 4096) -> str:
    """Send *prompt* to Claude and return clean HCL text."""
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    return _strip_markdown_fences(raw)
