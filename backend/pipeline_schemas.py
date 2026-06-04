"""
pipeline_schemas.py — schemas for inter-stage data.

CompressedContent is what Qwen produces and Gemini consumes.
This sits between stages and is the contract both sides honor.
"""

from pydantic import BaseModel, Field


class CompressedContent(BaseModel):
    """Mid-density compression of source content. Aim: ~50% of input size."""

    title: str = Field(
        description="A concise title for the content. Max 12 words."
    )
    thesis: str = Field(
        description=(
            "The central argument of the content, in 1-2 full sentences. "
            "State it as a claim, not a description. "
            "Bad: 'This article discusses customer research.' "
            "Good: 'Effective customer research focuses on the jobs customers hire products to do, not on feature preferences.'"
        )
    )
    claims: list[str] = Field(
        description=(
            "4 to 7 substantive claims from the content, each as a complete sentence. "
            "Include the claim AND its supporting reason or condition. "
            "Preserve the author's reasoning — do not collapse to one-liners. "
            "Bad: 'Features matter less than jobs.' "
            "Good: 'Features only drive purchases when they help a job get done better, faster, or more reliably; otherwise they add weight without pull.'"
        )
    )
    examples: list[str] = Field(
        description=(
            "2 to 4 concrete examples the content uses to illustrate its points. "
            "Include enough detail that the example is meaningful on its own. "
            "Skip if the content has no real examples."
        ),
        default_factory=list,
    )
    open_questions: list[str] = Field(
        description=(
            "0 to 3 questions, tradeoffs, or tensions the content raises but does NOT settle. "
            "Empty list if the content has clean conclusions throughout."
        ),
        default_factory=list,
    )