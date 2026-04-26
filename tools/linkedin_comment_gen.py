"""linkedin_comment_gen.py — Generate 3-variant LinkedIn comments in Joaquin's voice.

Note: uses `from __future__ import annotations` so PEP 604 union types (str | None)
work on Python 3.9 (local) as well as 3.11 (Render).

Loads the voice system prompt from prompts/linkedin_voice.md, calls Claude with
ephemeral prompt caching on the system block (large prompt, repeated calls),
and returns parsed JSON with three variants (Erfahrung / Sicht / Frage).

Public API:
    generate_from_text(post_text: str) -> dict
    generate_from_image(image_b64: str, media_type: str = "image/jpeg") -> dict

Both return:
    {
      "post_summary": "...",
      "post_branche": "Recht | Treuhand | ...",
      "comments": [
        {"variant": "Erfahrung", "text": "..." | None, "skip_reason": "..." | None},
        {"variant": "Sicht", "text": "..."},
        {"variant": "Frage", "text": "..."}
      ]
    }
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import anthropic

MODEL = "claude-opus-4-7"
MAX_TOKENS = 1500

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "linkedin_voice.md"
_voice_prompt_cache: str | None = None


def _voice_prompt() -> str:
    global _voice_prompt_cache
    if _voice_prompt_cache is None:
        _voice_prompt_cache = _PROMPT_PATH.read_text(encoding="utf-8")
    return _voice_prompt_cache


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _parse_json(text: str) -> dict[str, Any]:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"No JSON found in response: {text[:200]}")
    return json.loads(m.group())


def _call(user_content: list[dict] | str) -> dict[str, Any]:
    msg = _client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[{
            "type": "text",
            "text": _voice_prompt(),
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_content}],
    )
    return _parse_json(msg.content[0].text)


def generate_from_text(post_text: str) -> dict[str, Any]:
    """Generate 3 comment variants from a pasted/forwarded LinkedIn post."""
    if not post_text or not post_text.strip():
        raise ValueError("post_text is empty")
    return _call(f"LINKEDIN-POST (Text):\n\n{post_text.strip()}")


def generate_from_image(image_b64: str, media_type: str = "image/jpeg") -> dict[str, Any]:
    """Generate 3 comment variants from a LinkedIn screenshot.

    The model extracts the post text from the image AND generates the three
    comments in a single API call.
    """
    if not image_b64:
        raise ValueError("image_b64 is empty")
    return _call([
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_b64,
            },
        },
        {
            "type": "text",
            "text": (
                "Im Bild ist ein LinkedIn-Post (Screenshot). "
                "Lies den Post-Text vollständig aus dem Bild aus, "
                "ignoriere UI-Elemente (Reactions-Counter, Avatare, Buttons), "
                "und generiere dann die drei Kommentar-Varianten gemäss System-Prompt."
            ),
        },
    ])


# ---------------------------------------------------------------------------
# CLI for local smoke tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python linkedin_comment_gen.py '<post text>'")
        print("       python linkedin_comment_gen.py --image path/to/screenshot.jpg")
        sys.exit(1)

    if sys.argv[1] == "--image":
        import base64
        path = sys.argv[2]
        ext = Path(path).suffix.lower()
        media = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(ext, "image/jpeg")
        with open(path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode()
        result = generate_from_image(b64, media)
    else:
        result = generate_from_text(" ".join(sys.argv[1:]))

    print(json.dumps(result, ensure_ascii=False, indent=2))
