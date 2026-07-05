"""walkin_capture.py — server-side helpers for Walk-in mode (Phase 1).

Keeps api.py thin and the sidecar schema in ONE place (shared with
transcribe_walkin_memos.py). Three concerns:

1. Voice memos on disk: save an uploaded audio blob to WALKIN_MEMO_DIR with a
   sortable name + a sidecar JSON that is the idempotency ledger. The upload
   route only ever writes status="pending"; the daily transcription cron is the
   only writer of "transcribed"/"error".
2. Lead capture: build the schema-aware Leads-DB field dict and the matching
   one-line 💡-callout entry for a walk-in (both writes happen in the route, each
   best-effort so one failure never blocks the other).
3. Pure/offline: every function here is filesystem- or string-only, so the
   regression test can exercise it without Notion or a network.

Sidecar schema (one file `{audio_filename}.json` next to each audio file):
    {
      "audio": "20260630-141233__Nico__a8f2c1d4.m4a",
      "recorder": "Nico",
      "recorded_at": "2026-06-30T14:12:33+02:00",
      "duration_sec": 47,
      "mime": "audio/mp4",
      "status": "pending" | "transcribed" | "error",
      "kb_page_id": null | "<notion page id>",
      "transcribed_at": null | "<iso>",
      "error": null | "<message>",
      "attempts": 0
    }
"""

import json
import os
import re
import tempfile
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Zurich")

# Notes free-text cap (the big "write everything I know" box).
NOTES_MAX = 4000

# Leads-DB `Rolle` select options (verbatim) — only set Rolle if the posted role
# matches one of these, else omit (a bad select name would be dropped anyway).
ROLE_OPTIONS = {
    "Founder / Inhaber", "Admin / Office", "Operations",
    "Freelancer", "Mitarbeiter", "Leiter/Chef Stv.",
}

# mime → file extension. Covers what mobile browsers emit: iOS Safari →
# audio/mp4 (sometimes video/mp4), Android/Chrome → audio/webm.
_MIME_EXT = {
    "audio/mp4": ".m4a", "audio/x-m4a": ".m4a", "audio/aac": ".m4a",
    "video/mp4": ".m4a",
    "audio/webm": ".webm", "video/webm": ".webm",
    "audio/ogg": ".ogg", "audio/opus": ".ogg",
    "audio/mpeg": ".mp3", "audio/mp3": ".mp3",
    "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/wave": ".wav",
}
_KNOWN_AUDIO_EXT = {".m4a", ".webm", ".ogg", ".mp3", ".wav", ".aac", ".opus", ".flac"}


def memo_dir() -> str:
    return os.environ.get("WALKIN_MEMO_DIR", "/srv/cockpit/voice_memos")


def max_per_day() -> int:
    try:
        return int(os.environ.get("WALKIN_TRANSCRIBE_MAX_PER_DAY", "10"))
    except (TypeError, ValueError):
        return 10


def _now_local() -> datetime:
    return datetime.now(TZ)


def ext_for_mime(mime: str, filename: str = "") -> str:
    """Return a safe file extension for an audio upload, or '' if not an allowed
    audio/video-audio type. Maps known mimes; for any other audio/* (or the iOS
    video/* containers) falls back to the original filename's extension."""
    mime = (mime or "").split(";")[0].strip().lower()
    if mime in _MIME_EXT:
        return _MIME_EXT[mime]
    if mime.startswith("audio/") or mime in ("video/mp4", "video/webm"):
        _, ext = os.path.splitext(filename or "")
        ext = ext.lower()
        if ext in _KNOWN_AUDIO_EXT:
            return ext
        return ".m4a"  # sane default container for an unknown audio mime
    return ""


def _safe_recorder(recorder: str) -> str:
    """Strip a recorder name to filename-safe characters."""
    r = re.sub(r"[^A-Za-z0-9_-]", "", (recorder or "").strip()) or "unknown"
    return r[:24]


def _sidecar_path(audio_filename: str) -> str:
    return os.path.join(memo_dir(), audio_filename + ".json")


def _atomic_write_json(path: str, data: dict) -> None:
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def save_voice_memo(recorder: str, content: bytes, mime: str,
                    orig_filename: str = "", duration_sec=None) -> dict:
    """Write the audio blob + a pending sidecar to WALKIN_MEMO_DIR. Returns the
    sidecar dict. Raises ValueError on an unsupported audio type or empty content."""
    if not content:
        raise ValueError("leere Datei")
    ext = ext_for_mime(mime, orig_filename)
    if not ext:
        raise ValueError(f"Audioformat nicht unterstützt: {mime or orig_filename}")

    now = _now_local()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    base = f"{stamp}__{_safe_recorder(recorder)}__{uuid.uuid4().hex[:8]}{ext}"

    d = memo_dir()
    os.makedirs(d, exist_ok=True)
    audio_path = os.path.join(d, base)
    with open(audio_path, "wb") as f:
        f.write(content)

    try:
        dur = int(float(duration_sec)) if duration_sec not in (None, "") else None
    except (TypeError, ValueError):
        dur = None

    sidecar = {
        "audio": base,
        "recorder": recorder or "",
        "recorded_at": now.isoformat(timespec="seconds"),
        "duration_sec": dur,
        "mime": (mime or "").split(";")[0].strip().lower(),
        "bytes": len(content),
        "status": "pending",
        "kb_page_id": None,
        "transcribed_at": None,
        "error": None,
        "attempts": 0,
    }
    _atomic_write_json(_sidecar_path(base), sidecar)
    return sidecar


def list_sidecars() -> list:
    """Load every sidecar in the memo dir (newest first). Missing dir → []."""
    d = memo_dir()
    if not os.path.isdir(d):
        return []
    out = []
    for fn in os.listdir(d):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            continue
    out.sort(key=lambda s: s.get("recorded_at", ""), reverse=True)
    return out


def update_sidecar(audio_filename: str, **changes) -> dict:
    """Read-modify-write a sidecar atomically. Returns the new dict (or {} if gone)."""
    path = _sidecar_path(audio_filename)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    data.update(changes)
    _atomic_write_json(path, data)
    return data


def pending_memos() -> list:
    """Sidecars still needing transcription (status=pending, attempts<3), oldest first."""
    pend = [s for s in list_sidecars()
            if s.get("status") == "pending" and int(s.get("attempts", 0)) < 3]
    pend.sort(key=lambda s: s.get("recorded_at", ""))  # FIFO
    return pend


def transcribed_today_count() -> int:
    today = _now_local().date().isoformat()
    return sum(1 for s in list_sidecars()
               if (s.get("transcribed_at") or "")[:10] == today)


def memo_stats() -> dict:
    cards = list_sidecars()
    return {
        "total": len(cards),
        "pending": sum(1 for s in cards if s.get("status") == "pending"),
        "errored": sum(1 for s in cards if s.get("status") == "error"),
        "transcribed_today": transcribed_today_count(),
        "max_per_day": max_per_day(),
    }


def list_memos_compact() -> list:
    """Trim each sidecar to what the PWA status view needs."""
    return [{
        "memo": s.get("audio"),
        "recorder": s.get("recorder"),
        "recorded_at": s.get("recorded_at"),
        "duration_sec": s.get("duration_sec"),
        "status": s.get("status"),
        "error": s.get("error"),
    } for s in list_sidecars()]


# --- Lead capture: Leads-DB fields + the matching 💡-callout line ----------------

def validate_lead_payload(p: dict) -> list:
    """Return a list of invalid/missing field names ([] = ok)."""
    bad = []
    if not (p.get("company") or "").strip():
        bad.append("company")
    if not (p.get("notes") or "").strip():
        bad.append("notes")
    email = (p.get("email") or "").strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        bad.append("email")
    return bad


def build_lead_fields(p: dict, walkin_date: str) -> dict:
    """Build the schema-aware Leads-DB {prop: value} dict for a walk-in capture.
    Empty values are dropped downstream by notion_session.build_props."""
    company = (p.get("company") or "").strip()
    city = (p.get("city") or "").strip()
    notes = (p.get("notes") or "").strip()[:NOTES_MAX]
    fields = {
        "Name": (f"{company} {city}".strip() if city else company),
        "Firma": company,
        "Geschäftsführer / CEO": (p.get("contact") or "").strip(),
        "email": (p.get("email") or "").strip().lower(),
        "website": (p.get("website") or "").strip(),
        "phone": (p.get("phone") or "").strip(),
        "city": city,
        "Context": f"WALK-IN ({walkin_date})\n{notes}",
        "Outreach Channel": "Walk-In",
        "Outreach Gemacht?": True,
        "Contacted": True,
        "Gesprächsdatum": walkin_date,
        "Last contacted": walkin_date,
        "Pipeline Stage": "Problem Interview",
        "HOT STATUS": "WALK IN BUT NO BAMFAM",
        "War-Room Status": "○ Offen – keine Antwort",
    }
    role = (p.get("role") or "").strip()
    if role in ROLE_OPTIONS:
        fields["Rolle"] = role
    return fields


def build_callout_line(p: dict) -> str:
    """Build the single unmarked 💡-callout line `Company → details. notes` that
    /walkinmail will later parse. Collapses any newlines so it stays one line; the
    full verbatim notes are also pasted onto the lead page body by the route."""
    company = (p.get("company") or "").strip()
    detail_parts = [p.get("contact"), p.get("role"), p.get("email"),
                    p.get("website"), p.get("city"), p.get("phone")]
    detail = ", ".join(x.strip() for x in detail_parts if x and x.strip())
    notes = (p.get("notes") or "").strip()[:NOTES_MAX]
    tail = (detail + (". " if notes else "")) if detail else ""
    line = f"{company} → {tail}{notes}".strip()
    return re.sub(r"\s+", " ", line).strip()


def build_context_block(p: dict, *, sector: str = "", author: str = "", email: str = "",
                        email_confident: bool = True, walkin_date: str = "") -> str:
    """The removable 'who is this lead again' reminder that rides at the top of the draft (the
    operator deletes it before sending). Pure/offline, same charter as build_callout_line.
    Only non-empty lines are included; the verbatim visit note comes last."""
    company = (p.get("company") or "").strip()
    contact = (p.get("contact") or "").strip()
    role = (p.get("role") or "").strip()
    kontakt = f"{contact} ({role})" if contact and role else (contact or role)
    email_line = email or (p.get("email") or "").strip()
    if email_line and not email_confident:
        email_line += "  (unsicher, bitte prüfen)"
    rows = [
        ("Firma", company),
        ("Kontakt", kontakt),
        ("Ort", (p.get("city") or "").strip()),
        ("Website", (p.get("website") or "").strip()),
        ("E-Mail", email_line),
        ("Telefon", (p.get("phone") or "").strip()),
        ("Besuchsdatum", (walkin_date or p.get("walkin_date") or "").strip()),
        ("Erfasst von", (author or "").strip()),
        ("Branche/Hypothese", (sector or "").strip()),
    ]
    lines = [f"{label}: {value}" for label, value in rows if value]
    notes = (p.get("notes") or "").strip()
    if notes:
        lines.append("Notiz vom Besuch:")
        lines.append(notes)
    return "\n".join(lines)
