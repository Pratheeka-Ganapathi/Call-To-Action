"""
stage2_gemini.py — Gemini takes CompressedContent and produces ContentAnalysis.

This used to be the entirety of pipeline.py. The prompt is updated to take
the structured input from Stage 1 instead of raw text.
"""

import os

from google import genai
from google.genai import types

from pipeline_schemas import CompressedContent
from schemas import ContentAnalysis


MAX_OUTPUT_TOKENS = 2048


PROMPT_TEMPLATE = """You receive a structured pack representing the key facts from content a reader just consumed.

Your job is to produce a final analysis that helps the reader ACT on what they read.

Principles for the Call to Action:
- CONCRETE over abstract.
- SPECIFIC to the claims and examples below.
- TIME-BOUND where possible.
- HONEST: if the pack flags an open question, surface it as a decision or question; do not invent resolutions.

Three CTA buckets must NOT overlap:
- action_items: things to DO. Specific, verb-led.
- decisions_to_make: real CHOICES with tradeoffs.
- questions_to_explore: open threads to investigate.

Title from the pack: {title}
Thesis: {thesis}

Claims:
{claims}

Examples:
{examples}

Open questions raised by the content:
{open_questions}

Return only valid JSON matching the schema."""


def _format_list(items: list[str], empty_text: str = "(none)") -> str:
    """Format a list of strings as a numbered block for the prompt."""
    if not items:
        return empty_text
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))


def run_stage2(pack: CompressedContent) -> ContentAnalysis:
    """Send the compressed pack to Gemini, get back the final ContentAnalysis."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Load it from .env first.")

    prompt = PROMPT_TEMPLATE.format(
        title=pack.title,
        thesis=pack.thesis,
        claims=_format_list(pack.claims),
        examples=_format_list(pack.examples, "(no examples in source)"),
        open_questions=_format_list(pack.open_questions, "(no open questions raised)"),
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ContentAnalysis,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )

    if response.parsed is None:
        # Surface what Gemini actually returned so we can see why parsing failed.
        raw = "<unable to read>"
        try:
            raw = response.text or "<empty>"
        except Exception:
            pass
        finish_reason = "unknown"
        try:
            finish_reason = response.candidates[0].finish_reason.name
        except (IndexError, AttributeError):
            pass
        raise RuntimeError(
            f"Gemini returned no parsed response. "
            f"Finish reason: {finish_reason}. "
            f"Raw text (first 500 chars): {raw[:500]}"
        )

    return response.parsed