"""ocr.py — receipt OCR via Claude Vision. Advisory only; the KnowBody always
confirms before save, so an OCR miss is caught by a human (L2 review).

extract_receipt(image_bytes, media_type) -> a sanitised prefill dict. It NEVER
raises: on a missing key, bad image type, API error or unpar. JSON it returns
ok=False with empty fields so the route just shows an empty (manual) form.

Follows the established claude_client.py call shape (MODEL_FAST, system cache_control,
_parse_json). anthropic is imported lazily so importing this module costs nothing.
"""

from __future__ import annotations

import base64
import os
import re

# Claude image API accepts these media types only. iOS HEIC is re-encoded to JPEG
# client-side before upload; anything else is rejected with a clear message.
_ALLOWED_MEDIA = {"image/jpeg", "image/png", "image/webp", "image/gif"}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CCY_RE = re.compile(r"^[A-Z]{3}$")

_OCR_SYSTEM = (
    "Du bist ein präziser Beleg-Scanner für Schweizer Spesenabrechnungen. "
    "Extrahiere NUR, was auf dem Beleg sichtbar ist. Erfinde nichts. "
    "Wenn ein Feld unklar oder nicht lesbar ist, setze es auf null und senke die confidence. "
    "Antworte ausschliesslich mit gültigem JSON, ohne Erklärung, ohne Markdown."
)

_OCR_USER = (
    "Lies diesen Beleg und gib JSON zurück:\n"
    '{"haendler": string|null, "datum": "YYYY-MM-DD"|null, '
    '"betrag": number|null, "waehrung": "CHF|EUR|USD|GBP|..."|null, '
    '"confidence": 0.0-1.0}\n'
    "- haendler: Name des Geschäfts/Restaurants/Anbieters.\n"
    "- datum: Belegdatum im Format YYYY-MM-DD.\n"
    "- betrag: zu zahlender Gesamtbetrag (Total/Summe), nur die Zahl.\n"
    "- waehrung: 3-Buchstaben-Code (Standard CHF, wenn klar Schweiz und kein anderes Zeichen).\n"
    "- confidence: wie sicher du insgesamt bist (0 = geraten, 1 = eindeutig)."
)


def _normalise_media_type(media_type: str) -> str:
    mt = (media_type or "").split(";")[0].strip().lower()
    if mt in ("image/jpg", "image/pjpeg"):
        mt = "image/jpeg"
    return mt


def _sanitise(d: dict) -> dict:
    haendler = d.get("haendler")
    haendler = str(haendler).strip()[:120] if haendler else None

    datum = d.get("datum")
    datum = datum if (isinstance(datum, str) and _DATE_RE.match(datum)) else None

    betrag = d.get("betrag")
    try:
        betrag = round(float(betrag), 2) if betrag is not None else None
        if betrag is not None and betrag < 0:
            betrag = None
    except (TypeError, ValueError):
        betrag = None

    waehrung = d.get("waehrung")
    waehrung = str(waehrung).strip().upper() if waehrung else None
    if waehrung is not None and not _CCY_RE.match(waehrung):
        waehrung = None

    try:
        conf = float(d.get("confidence", 0.0))
        conf = max(0.0, min(1.0, conf))
    except (TypeError, ValueError):
        conf = 0.0

    return {"haendler": haendler, "datum": datum, "betrag": betrag,
            "waehrung": waehrung, "confidence": conf}


def extract_receipt(image_bytes: bytes, media_type: str, *, model: str = "") -> dict:
    """Return {ok, haendler, datum, betrag, waehrung, confidence, error}. Never raises."""
    base = {"ok": False, "haendler": None, "datum": None, "betrag": None,
            "waehrung": None, "confidence": 0.0, "error": ""}

    if not image_bytes:
        return {**base, "error": "leeres Bild"}
    mt = _normalise_media_type(media_type)
    if mt not in _ALLOWED_MEDIA:
        return {**base, "error": f"Bildformat nicht unterstützt: {media_type or '?'} (JPEG/PNG/WebP)"}
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {**base, "error": "OCR nicht konfiguriert"}

    try:
        import anthropic
        from claude_client import MODEL_FAST, _parse_json

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        b64 = base64.standard_b64encode(image_bytes).decode()
        msg = client.messages.create(
            model=model or MODEL_FAST,
            max_tokens=400,
            system=[{"type": "text", "text": _OCR_SYSTEM, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}},
                {"type": "text", "text": _OCR_USER},
            ]}],
        )
        parsed = _parse_json(msg.content[0].text)
        clean = _sanitise(parsed)
        return {"ok": True, "error": None, **clean}
    except Exception as e:
        print(f"[spesen-ocr] error={e!r}", flush=True)
        return {**base, "error": f"OCR fehlgeschlagen: {type(e).__name__}"}
