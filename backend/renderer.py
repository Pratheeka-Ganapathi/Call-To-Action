"""
renderer.py — render a ContentAnalysis to a PDF using fpdf2.

Pure Python, no system dependencies. Will be replaced with WeasyPrint +
Jinja2 templates in a later module for proper design.
"""

from pathlib import Path

from fpdf import FPDF

from schemas import ContentAnalysis


# fpdf2's built-in fonts only support Latin-1. Replace common Unicode chars
# that Gemini tends to output (smart quotes, em-dashes, etc.) with ASCII.
_UNICODE_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-",
    "\u2026": "...",
    "\u2022": "*",
}


def _sanitize(text: str) -> str:
    for old, new in _UNICODE_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def _heading(pdf: FPDF, text: str, size: int) -> None:
    pdf.set_font("Helvetica", style="B", size=size)
    pdf.multi_cell(0, 8, _sanitize(text))
    pdf.ln(2)


def _body(pdf: FPDF, text: str, size: int = 11, italic: bool = False) -> None:
    pdf.set_font("Helvetica", style="I" if italic else "", size=size)
    pdf.multi_cell(0, 6, _sanitize(text))
    pdf.ln(2)


def _bullets(pdf: FPDF, items: list[str], size: int = 11) -> None:
    pdf.set_font("Helvetica", size=size)
    for item in items:
        pdf.multi_cell(0, 6, _sanitize(f"- {item}"))
        pdf.ln(1)
    pdf.ln(3)


def render_to_pdf(analysis: ContentAnalysis, output_path: Path) -> None:
    """Write the full analysis to a PDF at output_path."""
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=20, top=20, right=20)
    pdf.add_page()

    _heading(pdf, analysis.metadata.title, size=20)
    pdf.ln(3)

    _body(pdf, analysis.summary.main_point, size=12, italic=True)
    pdf.ln(5)

    _heading(pdf, "Key Takeaways", size=14)
    _bullets(pdf, analysis.summary.key_takeaways)

    _heading(pdf, analysis.cta.headline, size=16)
    pdf.ln(2)

    _heading(pdf, "Action Items", size=12)
    _bullets(pdf, analysis.cta.action_items)

    _heading(pdf, "Decisions to Make", size=12)
    _bullets(pdf, analysis.cta.decisions_to_make)

    _heading(pdf, "Questions to Explore", size=12)
    _bullets(pdf, analysis.cta.questions_to_explore)

    pdf.output(str(output_path))
