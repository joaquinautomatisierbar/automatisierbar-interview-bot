"""titles.py — deterministic title + filename logic. Pure functions, no I/O.

The LLM *suggests* a title; nothing it says is trusted for the list decision.
resolve_titel() re-validates with an exact match against config.TITEL_VORLAGEN —
if the suggestion is not literally in the list it is treated as free-form and
capped. The date suffix and the filename are built here, never by the model.

Date suffix rule (interview round 3): always append MM/JJJJ, primarily from the
Berichtsdatum inside the PDF, fallback e-mail receive date ("ist egal, optimal
aber wenn direkt aus dem bericht"). In FILENAMES the slash is illegal on
Windows, so the display form "06/2026" becomes "06-2026" there — the document
title she sees (toast, Aeskulap metadata) keeps the slash.
"""

from __future__ import annotations

import re
from datetime import datetime

try:
    from . import config
except ImportError:  # direct-script / test runs
    import config  # type: ignore

# Windows-forbidden filename chars + control chars. Umlauts stay (NTFS is fine
# with them and her existing titles use them).
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WS = re.compile(r"\s+")

FILENAME_MAX_LEN = 150  # generous headroom below MAX_PATH even with deep hotfolder paths


def resolve_titel(titel_vorschlag: str | None) -> tuple[str, bool]:
    """(titel, ist_aus_liste). Exact list match wins; anything else is a
    free-form title, cleaned and capped. Empty suggestion -> 'Befundbericht'."""
    t = _WS.sub(" ", (titel_vorschlag or "").strip())
    if t in config.TITEL_VORLAGEN:
        return t, True
    if not t:
        return "Befundbericht", False
    return t[:config.FREITITEL_MAX_LEN].strip(), False


def datum_suffix(berichtsdatum: str | None, email_date: datetime | None) -> tuple[str, str]:
    """(display 'MM/JJJJ', filename 'MM-JJJJ'). Berichtsdatum (TT.MM.JJJJ) wins,
    then the e-mail date, then today — a suffix always exists."""
    mm = jjjj = None
    if berichtsdatum:
        m = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", berichtsdatum)
        if m:
            mm, jjjj = m.group(2), m.group(3)
    if mm is None and email_date is not None:
        mm, jjjj = f"{email_date.month:02d}", str(email_date.year)
    if mm is None:
        now = datetime.now()
        mm, jjjj = f"{now.month:02d}", str(now.year)
    return f"{mm}/{jjjj}", f"{mm}-{jjjj}"


def dokumenttitel(titel: str, display_suffix: str) -> str:
    """The title Dr. Ulrich sees, e.g. 'Urinkultur 06/2026'."""
    return f"{titel} {display_suffix}"


def _clean_component(s: str) -> str:
    # Spaces stay — her existing Aeskulap titles contain them.
    s = _FORBIDDEN.sub("_", s or "")
    return _WS.sub(" ", s).strip()


def build_filename(titel: str, filename_suffix: str,
                   nachname: str, vorname: str) -> str:
    """'[Titel MM-JJJJ]_[Nachname]_[Vorname].pdf', Windows-safe, length-capped.
    The patient part is never truncated (identification beats title verbosity)."""
    patient = f"_{_clean_component(nachname)}_{_clean_component(vorname)}.pdf"
    head = _clean_component(f"{titel} {filename_suffix}")
    room = FILENAME_MAX_LEN - len(patient)
    if len(head) > room:
        head = head[:max(room, 10)].rstrip(" _.")
    return head + patient
