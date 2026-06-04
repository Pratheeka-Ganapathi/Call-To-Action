"""
pipeline.py — orchestrates the analysis pipelines.

Two entry points:
  - run_analysis(content)         — text/PDF: Qwen → Gemini
  - run_analysis_from_image(...)  — image: MiniCPM-V → Qwen → Gemini

Both return ContentAnalysis. The two-vs-three stage difference is hidden
from callers (api.py).
"""

from model_manager import manager
from pipeline_schemas import CompressedContent
from pipelines.stage0_minicpm import run_stage0
from pipelines.stage1_qwen import run_stage1
from pipelines.stage2_gemini import run_stage2
from schemas import ContentAnalysis


def run_analysis(content: str) -> ContentAnalysis:
    """Text/PDF pipeline. Stage 1 (Qwen) → Stage 2 (Gemini)."""
    manager.ensure_model("qwen")
    pack: CompressedContent = run_stage1(content)
    analysis: ContentAnalysis = run_stage2(pack)
    return analysis


def run_analysis_from_image(
    image_bytes: bytes,
    filename: str,
) -> ContentAnalysis:
    """Image pipeline. Stage 0 (MiniCPM) → Stage 1 (Qwen) → Stage 2 (Gemini)."""
    # Step 1 — load MiniCPM, get a text description.
    manager.ensure_model("minicpm")
    description = run_stage0(image_bytes, filename)

    # Step 2 — swap to Qwen, run normal text pipeline.
    # We can't just call run_analysis() here because we'd swap to Qwen twice.
    # The shared text-side logic is two lines, easier to repeat than refactor.
    manager.ensure_model("qwen")
    pack: CompressedContent = run_stage1(description)
    analysis: ContentAnalysis = run_stage2(pack)
    return analysis