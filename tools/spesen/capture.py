"""capture.py — server-side beleg helpers. Pure / filesystem only (no network, no
DB), so the regression test exercises it without Claude or SQLite.

Three concerns, mirroring walkin_capture.py:
  1. validate_beleg_payload — what the confirm form must contain.
  2. save_receipt_image — write the uploaded photo to SPESEN_RECEIPT_DIR with a
     sortable, collision-free name (atomic write). Returns the stored basename.
  3. build_beleg_fields — merge the confirmed payload + the route-resolved amounts
     (betrag_chf, Wechselkurs, Kaffeekasse flag, image path) into the exact column
     dict db.insert_beleg expects.

The route owns the network bits (OCR preview, FX conversion, pauschale lookup) and
passes the results in via `resolved`; this keeps capture deterministic + testable.
"""

from __future__ import annotations

import os
import re
import tempfile
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Zurich")

NOTE_MAX = 2000
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CCY_RE = re.compile(r"^[A-Za-z]{3}$")

# Accepted receipt files: images (for OCR) + PDF (SBB/Revolut; stored, no OCR).
_IMG_MIME_EXT = {
    "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/pjpeg": ".jpg",
    "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif",
    "application/pdf": ".pdf",
}
_KNOWN_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}


def receipt_dir() -> str:
    return os.environ.get("SPESEN_RECEIPT_DIR", "/srv/knowspesen/receipts")


def _now_local() -> datetime:
    return datetime.now(TZ)


def ext_for_image_mime(mime: str, filename: str = "") -> str:
    """Safe extension for a receipt upload (image or PDF), or '' if not allowed."""
    mime = (mime or "").split(";")[0].strip().lower()
    if mime in _IMG_MIME_EXT:
        return _IMG_MIME_EXT[mime]
    # fallback: trust a known file extension (covers image/* variants + PDFs sent
    # as application/octet-stream by some browsers).
    _, ext = os.path.splitext(filename or "")
    ext = ext.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    if ext in _KNOWN_IMG_EXT:
        return ext
    return ""


def _safe(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]", "", (name or "").strip()) or "kb"
    return s[:24]


def abs_path_for(basename: str) -> str:
    """Resolve a stored basename to an absolute path (for the ZIP step)."""
    return os.path.join(receipt_dir(), basename)


def save_receipt_image(knowbody: str, content: bytes, mime: str, orig_filename: str = "") -> str:
    """Write the image to SPESEN_RECEIPT_DIR, return the stored basename.
    Raises ValueError on an unsupported type or empty content."""
    if not content:
        raise ValueError("leere Datei")
    ext = ext_for_image_mime(mime, orig_filename)
    if not ext:
        raise ValueError(f"Bildformat nicht unterstützt: {mime or orig_filename}")
    now = _now_local()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    base = f"{stamp}__{_safe(knowbody)}__{uuid.uuid4().hex[:8]}{ext}"
    d = receipt_dir()
    os.makedirs(d, exist_ok=True)
    # atomic: write temp in same dir, then rename
    fd, tmp = tempfile.mkstemp(dir=d, suffix=ext)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        os.replace(tmp, os.path.join(d, base))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return base


def to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "yes", "ja", "on")


def validate_beleg_payload(p: dict) -> list:
    """Return a list of invalid/missing field names ([] = ok)."""
    bad = []
    art = (p.get("art") or "beleg").strip()
    if art not in ("beleg", "pauschale"):
        bad.append("art")

    datum = (p.get("datum") or "").strip()
    if not _DATE_RE.match(datum):
        bad.append("datum")

    if not (p.get("kategorie") or "").strip():
        bad.append("kategorie")

    if art == "pauschale":
        if not (p.get("pauschale_code") or "").strip():
            bad.append("pauschale_code")
    else:
        betrag = p.get("betrag_original", p.get("betrag"))
        try:
            if betrag is None or float(betrag) <= 0:
                bad.append("betrag_original")
        except (TypeError, ValueError):
            bad.append("betrag_original")
        waehrung = (p.get("waehrung") or "").strip()
        if not _CCY_RE.match(waehrung):
            bad.append("waehrung")
    return bad


def build_beleg_fields(p: dict, knowbody_id: int, resolved: dict) -> dict:
    """Merge confirmed payload + route-resolved amounts into the db column dict.

    `resolved` carries what the route computed (network-dependent):
      betrag_chf, betrag_original, waehrung, wechselkurs, kurs_quelle,
      ist_kaffeekasse, bild_pfad, pauschale_code, art
    """
    art = (resolved.get("art") or p.get("art") or "beleg").strip()
    waehrung = (resolved.get("waehrung") or p.get("waehrung") or "CHF").strip().upper()
    fields = {
        "knowbody_id": knowbody_id,
        "art": art if art in ("beleg", "pauschale") else "beleg",
        "haendler": (p.get("haendler") or "").strip()[:120] or None,
        "beleg_datum": (p.get("datum") or "").strip(),
        "betrag_original": resolved.get("betrag_original"),
        "waehrung": waehrung,
        "wechselkurs": resolved.get("wechselkurs"),
        "kurs_quelle": resolved.get("kurs_quelle"),
        "betrag_chf": resolved.get("betrag_chf"),
        "kategorie": (p.get("kategorie") or "").strip() or None,
        "unterkategorie": (p.get("unterkategorie") or "").strip() or None,
        "zahlungsart": (p.get("zahlungsart") or "").strip() or None,
        "projekt": (p.get("projekt") or "").strip() or None,
        "weiterverrechenbar": 1 if to_bool(p.get("weiterverrechenbar")) else 0,
        "pauschale_code": resolved.get("pauschale_code") or None,
        "ist_kaffeekasse": 1 if resolved.get("ist_kaffeekasse") else 0,
        "bild_pfad": resolved.get("bild_pfad") or None,
        "ocr_confidence": resolved.get("ocr_confidence"),
        "notiz": (p.get("notiz") or "").strip()[:NOTE_MAX] or None,
    }
    return fields
