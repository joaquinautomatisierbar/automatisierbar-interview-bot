"""vapi_client.py — minimal Vapi assistant read/update helpers for the Script-Tuner.

Reads VAPI_API_KEY + VAPI_ASSISTANT_ID from the environment (Render injects them;
locally, the __main__ block loads .env). Uses `requests` (already a dependency).

Public API:
  get_assistant() -> dict
  update_system_prompt(text: str) -> dict
  place_call(*, number, session_id, ...) -> dict   # POST /call (cockpit dialer)
  get_call(call_id: str) -> dict                   # GET /call/{id} (live status)

SAFETY: update_system_prompt PATCHes the LIVE assistant. It is invoked only from the
dry_run=false branch of /api/voice/script/apply. place_call PLACES A REAL OUTBOUND
CALL — only the cockpit batch runner calls it, gated by eligibility + a budget cap.
get_assistant()/get_call() are read-only.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

_REPO_ROOT = Path(__file__).resolve().parent.parent
VAPI_BASE = "https://api.vapi.ai"
_TIMEOUT = 20


def _load_dotenv() -> None:
    """Idempotent .env loader (mirrors tools/linkedin_brief.py). Does NOT override
    vars already in the environment. Only needed for standalone CLI use — the Flask
    process already has the vars."""
    env_path = _REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _assistant_id() -> str:
    aid = os.environ.get("VAPI_ASSISTANT_ID", "").strip()
    if not aid:
        raise RuntimeError("VAPI_ASSISTANT_ID not set")
    return aid


def _headers() -> dict:
    key = os.environ.get("VAPI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("VAPI_API_KEY not set")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def get_assistant() -> dict:
    """GET the full assistant object (so we can merge, never clobber, the model block)."""
    resp = requests.get(
        f"{VAPI_BASE}/assistant/{_assistant_id()}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def update_system_prompt(text: str) -> dict:
    """PATCH model.messages[0] (role=system) content to `text`, preserving every
    other model field (provider, model id, maxTokens, etc.) and any non-system
    messages. GETs first, deep-merges, then PATCHes.

    Returns the PATCH response JSON. Raises on HTTP error (caller maps to 502)."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("system prompt text must be a non-empty string")

    current = get_assistant()
    model = dict(current.get("model") or {})
    messages = list(model.get("messages") or [])

    # Find the existing system message; replace its content. If none exists,
    # prepend one. Preserve all other messages untouched.
    sys_idx = next(
        (i for i, m in enumerate(messages)
         if isinstance(m, dict) and m.get("role") == "system"),
        None,
    )
    if sys_idx is None:
        messages.insert(0, {"role": "system", "content": text})
    else:
        messages[sys_idx] = {**messages[sys_idx], "role": "system", "content": text}

    # PATCH body: only the model object, with the full (merged) messages array.
    # Vapi's PATCH replaces the model object, so we send the merged copy — every
    # original key (provider/model/maxTokens/temperature/...) is retained.
    model["messages"] = messages
    patch_body = {"model": model}

    resp = requests.patch(
        f"{VAPI_BASE}/assistant/{_assistant_id()}",
        headers=_headers(),
        json=patch_body,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _phone_number_id() -> str:
    pid = os.environ.get("VAPI_PHONE_NUMBER_ID", "").strip()
    if not pid:
        raise RuntimeError("VAPI_PHONE_NUMBER_ID not set")
    return pid


def place_call(*, number: str, session_id: str, lead_id: str = "", firma: str = "",
               branche: str = "", kontakt_nachname: str = "",
               disclosure_line: str = "", context: str = "") -> dict:
    """Place ONE outbound call via Vapi (POST /call). Returns the created call object
    ({id, status, ...}). The conversation runs async on Vapi's side; poll get_call(id)
    for status/cost/transcript. `metadata.session_id` lets Workflow E feed the same
    voice session the cockpit batch uses. Raises on HTTP error.

    WARNING: this dials a real phone. Callers must gate on eligibility + budget."""
    if not number:
        raise ValueError("number is required")
    payload = {
        "phoneNumberId": _phone_number_id(),
        "assistantId": _assistant_id(),
        "customer": {"number": number},
        "assistantOverrides": {
            "variableValues": {
                "firma": firma or "",
                "branche": branche or "",
                "kontakt_nachname": kontakt_nachname or "",
                "disclosure_line": disclosure_line or "",
                "context": context or "",
            }
        },
        "metadata": {"lead_id": lead_id or "", "session_id": session_id or "",
                     "firma": firma or "", "branche": branche or ""},
    }
    resp = requests.post(f"{VAPI_BASE}/call", headers=_headers(), json=payload, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_call(call_id: str) -> dict:
    """GET a call's live state: {status, endedReason, cost, startedAt, endedAt,
    transcript, analysis:{summary, structuredData}}. Read-only. Raises on HTTP error."""
    if not call_id:
        raise ValueError("call_id is required")
    resp = requests.get(f"{VAPI_BASE}/call/{call_id}", headers=_headers(), timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    # Manual smoketest helper — READ-ONLY by default. Never PATCHes.
    import argparse
    import sys

    _load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--get", action="store_true", help="print current system prompt")
    args = ap.parse_args()
    if args.get:
        a = get_assistant()
        msgs = (a.get("model") or {}).get("messages") or []
        sysmsg = next((m.get("content") for m in msgs if m.get("role") == "system"), "")
        print(sysmsg)
        sys.exit(0)
    ap.print_help()
