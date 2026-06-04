"""
stage1_qwen.py — Qwen 2.5 7B compresses raw content into a CompressedContent.

Talks to llama-server running locally on port 8090. The server must be running
before this is called.
"""

import json
import os

import httpx

from pipeline_schemas import CompressedContent


# Where the local llama-server lives. Configurable via .env.
QWEN_SERVER_URL = os.getenv("QWEN_SERVER_URL", "http://127.0.0.1:8090")

# Hard cap on input chars. Same as before — protects context window.
MAX_INPUT_CHARS = 8_000


PROMPT_TEMPLATE = """You compress source content into a structured pack of facts.

Rules:
- PRESERVE the author's actual claims and reasoning. Do not paraphrase into vague generalities.
- Each claim should be specific enough that a reader can act on it or evaluate it.
- Stick to what the content actually says. Do NOT add your own conclusions.
- Match the JSON schema exactly. Empty arrays are valid for examples and open_questions.

Source content:
---
{content}
---

Return ONLY valid JSON matching the schema. No preamble, no explanation."""


def run_stage1(content: str) -> CompressedContent:
    """Send raw content to Qwen via llama-server, get back CompressedContent.

    Raises RuntimeError if the server is unreachable or returns invalid output.
    """
    if not content.strip():
        raise ValueError("Content is empty.")

    if len(content) > MAX_INPUT_CHARS:
        content = content[:MAX_INPUT_CHARS] + "\n\n[content truncated]"

    prompt = PROMPT_TEMPLATE.format(content=content)

    # llama-server's /completion endpoint with json_schema constraint.
    # The schema is generated from our Pydantic model — same single source
    # of truth as if we'd hand-written it.
    payload = {
        "prompt": prompt,
        "n_predict": 1024,        # max output tokens
        "temperature": 0.3,        # low — we want faithful extraction, not creativity
        "json_schema": CompressedContent.model_json_schema(),
        "cache_prompt": True,      # llama-server caches the prompt prefix; small speedup
    }

    try:
        # 90-second timeout — Qwen 7B on a 2060 takes 30-60s typically.
        with httpx.Client(timeout=90.0) as client:
            response = client.post(
                f"{QWEN_SERVER_URL}/completion",
                json=payload,
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Cannot reach llama-server at {QWEN_SERVER_URL}. "
            "Is it running? Start it with the launch command."
        )
    except httpx.TimeoutException:
        raise RuntimeError(
            "llama-server timed out after 90s. The model may be busy or stuck."
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"llama-server returned an error: {e.response.status_code} {e.response.text[:200]}"
        )

    data = response.json()
    raw_text = data.get("content", "").strip()

    if not raw_text:
        raise RuntimeError("Qwen returned empty response.")

    # Parse JSON and validate against the schema.
    try:
        parsed_json = json.loads(raw_text)
        return CompressedContent.model_validate(parsed_json)
    except (json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(
            f"Qwen returned malformed JSON: {e}\n"
            f"Raw output (first 500 chars): {raw_text[:500]}"
        )