"""
schemas.py — Pydantic models defining the analysis output shape.

These get sent to Gemini as the response_schema, forcing structured output.
The shape here MUST match the TypeScript types in the frontend's analysis.ts.

Tuned for SHORT output during development to conserve API quota.
"""

from pydantic import BaseModel, Field


class Metadata(BaseModel):
    title: str = Field(
        description="A concise title. Max 8 words."
    )
    content_type: str = Field(
        description="One of: 'article', 'book_chapter', 'research', 'essay', 'other'."
    )


class Summary(BaseModel):
    main_point: str = Field(
        description=(
            "The single most important claim. MAXIMUM 20 WORDS. "
            "One sentence, one idea. No preamble. "
            "Do not chain claims with 'which' or 'and'."
        )
    )
    key_takeaways: list[str] = Field(
        description="EXACTLY 3 takeaways. Each one short sentence (max 15 words)."
    )


class CallToAction(BaseModel):
    headline: str = Field(
        description="Action-oriented title. Max 8 words."
    )
    action_items: list[str] = Field(
        description=(
            "EXACTLY 3 concrete actions. "
            "Each must be specific, short (max 20 words), and tied to the content. "
            "Bad: 'Think about your customers.' "
            "Good: 'Pick one customer and write down what job they hired your product to do.'"
        )
    )
    decisions_to_make: list[str] = Field(
        description=(
            "EXACTLY 2 decisions. Each framed as a question. Max 20 words each."
        )
    )
    questions_to_explore: list[str] = Field(
        description=(
            "EXACTLY 2 open questions. Things the content raises but doesn't settle. "
            "Max 20 words each."
        )
    )


class ContentAnalysis(BaseModel):
    """Top-level output that Gemini returns and the API sends to the frontend."""
    metadata: Metadata
    summary: Summary
    cta: CallToAction