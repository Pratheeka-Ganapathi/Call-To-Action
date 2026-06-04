"""
extractor.py — get plain text out of an input file.

Supports .pdf (via PyMuPDF) and .txt. The single public function returns
a string. Caller doesn't care which input type was used.
"""

from pathlib import Path

import pymupdf


SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


def extract_text(path: Path) -> str:
    """Return the text content of the file at `path`.

    Raises ValueError for unsupported extensions or empty PDFs.
    """
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        return _extract_from_pdf(path)

    raise ValueError(
        f"Unsupported file type: {suffix}. "
        f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
    )


def _extract_from_pdf(path: Path) -> str:
    """Use PyMuPDF to pull text out of a PDF, page by page."""
    with pymupdf.open(path) as doc:
        pages = [page.get_text() for page in doc]

    full_text = "\n\n".join(pages).strip()

    if not full_text:
        # Scanned PDFs (image-only, no text layer) extract to empty string.
        # Surface this clearly instead of sending nothing to Gemini.
        raise ValueError(
            f"No extractable text in {path.name}. "
            "This PDF may be a scanned image — OCR isn't supported yet."
        )

    return full_text


def extract_text_from_bytes(filename: str, data: bytes) -> str:
    """Same as extract_text, but for bytes (used by the FastAPI server).

    Writes the bytes to a temp file and runs the regular extractor.
    PyMuPDF needs a real file path, so we briefly materialize one.
    """
    import tempfile

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    # NamedTemporaryFile with delete=False so we can close it before reading.
    # On Windows you can't have a file open in two places, so we close-then-open.
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix
    ) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        return extract_text(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
