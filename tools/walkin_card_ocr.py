"""walkin_card_ocr.py — business-card OCR via Claude Vision for Walk-in mode.

Mirrors tools/spesen/ocr.py: photograph a Visitenkarte, extract structured lead
fields (name/company/role/email/phone/website/city/address), and hand them back as a
prefill dict the operator REVIEWS before saving (L2). It NEVER raises: on a missing
key, bad image type, API error or unparseable JSON it returns ok=False with empty
fields so the walk-in lead form just stays manual.

Follows the established claude_client.py call shape (MODEL_FAST, system cache_control,
_parse_json). anthropic is imported lazily so importing this module costs nothing.

`role` is the model's best mapping of the printed job title onto exactly ONE of the six
Leads-DB `Rolle` options (walkin_capture.ROLE_OPTIONS), or null when none fits — that is
what makes the form's Rolle select auto-pick. `title` keeps the raw printed title so
nothing is lost when role can't be mapped (the route pastes it into the lead notes).
"""

from __future__ import annotations

import base64
import os
import re

# Claude image API accepts these media types only. iOS HEIC is re-encoded to JPEG
# client-side before upload; anything else is rejected with a clear message.
_ALLOWED_MEDIA = {"image/jpeg", "image/png", "image/webp", "image/gif"}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# The six Leads-DB `Rolle` select options (single source of truth in walkin_capture,
# same set the Neuer-Lead <select> renders). Import so the two never drift.
try:
    from walkin_capture import ROLE_OPTIONS
except Exception:  # pragma: no cover — import guard for odd sys.path setups
    ROLE_OPTIONS = {
        "Founder / Inhaber", "Admin / Office", "Operations",
        "Freelancer", "Mitarbeiter", "Leiter/Chef Stv.",
    }

# Sorted for a stable prompt string (helps prompt caching stay warm).
_ROLE_LIST = "|".join(sorted(ROLE_OPTIONS))

_OCR_SYSTEM = (
    "Du bist ein präziser Visitenkarten-Scanner. "
    "Extrahiere NUR, was auf der Visitenkarte sichtbar ist. Erfinde nichts. "
    "Wenn ein Feld unklar oder nicht lesbar ist, setze es auf null und senke die confidence. "
    "Antworte ausschliesslich mit gültigem JSON, ohne Erklärung, ohne Markdown."
)

_OCR_USER = (
    "Lies diese Visitenkarte und gib JSON zurück:\n"
    '{"name": string|null, "company": string|null, "title": string|null, '
    '"role": "' + _ROLE_LIST + '"|null, '
    '"email": string|null, "phone": string|null, "website": string|null, '
    '"city": string|null, "postal_code": string|null, "address": string|null, '
    '"confidence": 0.0-1.0}\n'
    "- name: Vollständiger Name der Person.\n"
    "- company: Firmen-/Unternehmensname.\n"
    "- title: Berufsbezeichnung/Position wie gedruckt (z.B. 'Geschäftsführer', 'CFO').\n"
    "- role: Ordne den title GENAU einer dieser Kategorien zu, oder null wenn keine passt: "
    + _ROLE_LIST + ".\n"
    "  Faustregeln: CEO/Inhaber/Gründer/Partner -> 'Founder / Inhaber'; "
    "Buchhaltung/Sekretariat/Empfang/Backoffice -> 'Admin / Office'; "
    "Betriebs-/Logistik-/Produktionsleitung -> 'Operations'; "
    "Selbstständig/Einzelfirma/freischaffend -> 'Freelancer'; "
    "Stv. Geschäftsführer/Abteilungs-/Teamleiter -> 'Leiter/Chef Stv.'; "
    "sonst normale/r Angestellte/r -> 'Mitarbeiter'.\n"
    "- email: E-Mail-Adresse.\n"
    "- phone: Telefonnummer wie gedruckt (Direktwahl/Mobil bevorzugt, sonst Zentrale).\n"
    "- website: Web-Adresse ohne http:// oder https://.\n"
    "- city: Ort/Stadt aus der Adresse.\n"
    "- postal_code: Postleitzahl aus der Adresse.\n"
    "- address: nur die Strassenzeile (Strasse und Hausnummer).\n"
    "- confidence: wie sicher du insgesamt bist (0 = geraten, 1 = eindeutig)."
)


def _normalise_media_type(media_type: str) -> str:
    mt = (media_type or "").split(";")[0].strip().lower()
    if mt in ("image/jpg", "image/pjpeg"):
        mt = "image/jpeg"
    return mt


def _clean_str(v, cap: int):
    s = str(v).strip() if v is not None else ""
    return s[:cap] if s else None


def _sanitise(d: dict) -> dict:
    name = _clean_str(d.get("name"), 120)
    company = _clean_str(d.get("company"), 120)
    title = _clean_str(d.get("title"), 120)

    # role: keep ONLY if it maps exactly onto a Leads-DB select option, else drop
    # (a free-text title like "Marketing Manager" would be rejected by Notion anyway).
    role = d.get("role")
    role = str(role).strip() if role else ""
    role = role if role in ROLE_OPTIONS else None

    email = d.get("email")
    email = str(email).strip().lower() if email else ""
    email = email if (email and _EMAIL_RE.match(email)) else None

    phone = _clean_str(d.get("phone"), 60)

    website = d.get("website")
    if website:
        website = re.sub(r"^https?://", "", str(website).strip(), flags=re.I).strip("/ ")
        website = website[:200] or None
    else:
        website = None

    city = _clean_str(d.get("city"), 80)
    postal_code = _clean_str(d.get("postal_code"), 20)
    address = _clean_str(d.get("address"), 200)

    try:
        conf = float(d.get("confidence", 0.0))
        conf = max(0.0, min(1.0, conf))
    except (TypeError, ValueError):
        conf = 0.0

    return {"name": name, "company": company, "title": title, "role": role,
            "email": email, "phone": phone, "website": website, "city": city,
            "postal_code": postal_code, "address": address, "confidence": conf}


def extract_card(image_bytes: bytes, media_type: str, *, model: str = "") -> dict:
    """Return {ok, name, company, title, role, email, phone, website, city,
    postal_code, address, confidence, error}. Never raises."""
    base = {"ok": False, "name": None, "company": None, "title": None, "role": None,
            "email": None, "phone": None, "website": None, "city": None,
            "postal_code": None, "address": None, "confidence": 0.0, "error": ""}

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
            max_tokens=500,
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
        print(f"[walkin-card-ocr] error={e!r}", flush=True)
        return {**base, "error": f"OCR fehlgeschlagen: {type(e).__name__}"}
