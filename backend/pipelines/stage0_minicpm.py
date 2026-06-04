"""
stage0_minicpm.py — image bytes → text description, via MiniCPM-V.

Stage 0 of the image pipeline. Output is a plain string description that
gets fed into Stage 1 (Qwen compresses) → Stage 2 (Gemini polishes).

The ModelManager is responsible for ensuring MiniCPM is loaded before
this is called. This module assumes the right model is already up.
"""

import base64
from pathlib import Path

import httpx

from model_manager import SERVER_URL


# Prompt for MiniCPM. Note: we ask for a description that's *useful for analysis*,
# not just visual description. The downstream pipeline (Qwen + Gemini) needs
# substance to chew on, not "a square image with text on it."
PROMPT = """Describe this image in detail. Include:
- Any text visible (transcribe accurately, including handwriting)
- The structure of any diagrams, charts, or visual layouts
- The relationships between elements (what points to what, what's grouped together)
- The apparent purpose or topic the image conveys

Write your description as flowing prose, like you're explaining the image to someone who can't see it. Be thorough — downstream analysis depends on the detail you provide."""


# Image MIME types we accept. Used to construct the data: URL.
MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def run_stage0(image_bytes: bytes, filename: str) -> str:
    """Send an image to MiniCPM-V and get back a text description.

    Args:
        image_bytes: the raw bytes of the image file
        filename: the original filename — used to determine MIME type

    Returns:
        A multi-paragraph text description of the image.

    Raises:
        ValueError: if the file extension isn't supported
        RuntimeError: if MiniCPM-V is unreachable or returns malformed output
    """
    suffix = Path(filename).suffix.lower()
    mime = MIME_BY_SUFFIX.get(suffix)
    if mime is None:
        raise ValueError(
            f"Unsupported image type: {suffix}. "
            f"Supported: {sorted(MIME_BY_SUFFIX.keys())}"
        )

    # Encode as base64 and wrap in a data URL — same format as the PowerShell test.
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    # OpenAI-compatible chat completions format with image content.
    payload = {
        "model": "minicpm-v",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "max_tokens": 800,   # plenty for a detailed description
        "temperature": 0.2,  # low — we want faithful description, not creativity
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{SERVER_URL}/v1/chat/completions",
                json=payload,
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Cannot reach llama-server at {SERVER_URL}. "
            "Is MiniCPM-V loaded? ModelManager.ensure_model('minicpm') first."
        )
    except httpx.TimeoutException:
        raise RuntimeError("MiniCPM-V timed out after 120s.")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"MiniCPM-V error {e.response.status_code}: {e.response.text[:300]}"
        )

    data = response.json()
    try:
        description = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(
            f"Unexpected MiniCPM-V response shape: {e}\n"
            f"Raw response: {str(data)[:500]}"
        )

    if not description:
        raise RuntimeError("MiniCPM-V returned empty description.")

    return description