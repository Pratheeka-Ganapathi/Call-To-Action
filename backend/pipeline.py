"""
pipeline.py — the core analysis pipeline.

Tuned for low token usage during development.
"""

import os

from google import genai
from google.genai import types

from schemas import ContentAnalysis


# Input cap — protects API quota from huge inputs.
# 8k chars ≈ 2k tokens. Plenty for an article or short chapter.
# Bump this number once development is stable.
MAX_INPUT_CHARS = 8_000

# Output cap — hard ceiling on response size.
# 1024 tokens is enough for our small structured output.
MAX_OUTPUT_TOKENS = 1024


PROMPT_TEMPLATE = """You analyze content to help readers ACT on what they read, not just remember it.

Rules:
- Be CONCISE. Short sentences. No filler.
- Stick to the EXACT counts requested in the schema.
- action_items: things to DO.
- decisions_to_make: real CHOICES with tradeoffs.
- questions_to_explore: open threads the content raises.

Content:
---
{content}
---

Return only valid JSON matching the schema."""


def run_analysis(content: str) -> ContentAnalysis:
    """Send text content to Gemini and return a structured analysis."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Load it from .env first.")

    if not content.strip():
        raise ValueError("Content is empty — nothing to analyze.")

    if len(content) > MAX_INPUT_CHARS:
        content = content[:MAX_INPUT_CHARS] + "\n\n[content truncated]"

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=PROMPT_TEMPLATE.format(content=content),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ContentAnalysis,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )

    if response.parsed is None:
        raise RuntimeError("Gemini returned no parsed response.")

    return response.parsed