"""config.py — single edit-point for all Befund-Automat domain values.

Everything the practice (or we, during the pilot) might tweak lives here:
the 25-title template list, IMAP profiles, poll cadence, filing behaviour,
and every German UI string. Layered resolution, lowest priority first:

    code defaults (this file)
      < %LOCALAPPDATA%\\BefundAutomat\\config.json   (per-install overrides)
      < BEFUND_* environment variables                (dev / harness)

Secrets (HIN Mail Token, LLM API key) are NEVER read from config.json —
see secrets_store.py (Windows Credential Locker via keyring, env fallback).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_NAME = "BefundAutomat"

# ---------------------------------------------------------------------------
# Data directory: state.db, config.json, logs/. Outside the install dir so a
# reinstall (= our update path) never touches state. BEFUND_DATA_DIR wins so
# tests and the dev harness can point everything at a temp folder.
# ---------------------------------------------------------------------------


def data_dir() -> Path:
    override = os.environ.get("BEFUND_DATA_DIR")
    if override:
        p = Path(override)
    elif sys.platform == "win32":
        p = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / APP_NAME
    else:  # dev on macOS/Linux
        p = Path.home() / ".befund-automat"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Dokumenttitel-Vorlagen (25) — verbatim the list Dr. Ulrich uses in Aeskulap
# (interview round 1). Three obvious typos in the raw interview transcript were
# normalised ("Einwilligungserkärung" -> "Einwilligungserklärung",
# "Ejukulatanalyse" -> "Ejakulatanalyse", "Definitver" -> "Definitiver");
# CONFIRM the corrected spellings with her on install day — if she wants the
# typo forms (because Aeskulap autocompletes on them), edit ONLY this list.
# The final document title is always "<Titel> MM/JJJJ".
# ---------------------------------------------------------------------------

TITEL_VORLAGEN = [
    "Austrittsbericht Geburt Spital Limmattal",
    "Austrittsbericht Geburt STZ",
    "Austrittsbericht Geburt USZ",
    "Berichte vorgängige Praxis",
    "Brustzentrum Mamma-US",
    "Einwilligungserklärung mit Unterschrift",
    "Ejakulatanalyse Partner",
    "Ejakulatanalyse Gynart",
    "ETT zweizeitig",
    "Fetale RHD Genotypisierung (Rhesusfaktor)",
    "Geburtsbericht",
    "Geburtsbericht Spital Limmattal",
    "I clot Bericht",
    "Kurzbericht Geburt STZ",
    "NIPT (V-Natal) mit Geschlechtsangabe",
    "NIPT V-Natal",
    "Operationsbericht Spital",
    "STZ Definitiver Geburtsbericht",
    "STZ Gyn Austrittsbericht",
    "STZ MG und Mammasonografie",
    "STZ OP- und Austrittsbericht",
    "Ultraschallbericht Dr. T. Burkhardt USZ",
    "Urinkultur",
    "Urinsediment",
    "Verlaufsbericht",
]

# Free-form titles the LLM invents are capped here (Aeskulap UI + filename budget).
FREITITEL_MAX_LEN = 60

# ---------------------------------------------------------------------------
# Defaults. Every key here can be overridden by config.json and BEFUND_* env
# (env key = "BEFUND_" + key.upper()).
# ---------------------------------------------------------------------------

_DEFAULTS: dict = {
    # --- mailbox ---------------------------------------------------------
    # profile "hin"  = production (Praxis; auth = HIN-ID + Mail-Token)
    # profile "test" = dev harness (Infomaniak test mailbox)
    "profile": "test",
    "hin_imap_host": "imap.mail.hin.ch",
    "hin_imap_port": 993,
    "hin_imap_user": "",                    # HIN-ID, set at install
    "test_imap_host": "mail.infomaniak.com",
    "test_imap_port": 993,
    "test_imap_user": "",
    "mailbox_folder": "INBOX",
    "poll_interval_sec": 180,
    "rescan_window_days": 3,                # startup UID-rescan safety net
    "max_pdf_mb": 25,                       # larger attachments -> skip + log

    # --- filing ----------------------------------------------------------
    # sink: "hotfolder" | "hotfolder+gdt" (pending Kern Concept) | "dryrun"
    "sink": "hotfolder",
    # Install-day value. Pre-decided fallback if Kern Concept has not answered:
    # a "Befund-Ablage" folder in her Documents (she drags into Aeskulap herself).
    "hotfolder_path": "",
    "filename_date_sep": "-",               # MM-JJJJ in filenames (\\/ illegal on Windows)

    # --- LLM -------------------------------------------------------------
    # provider: "anthropic" (implemented) | "azure-openai" | "local" (stubs).
    # Go-live provider is decided at the Datenschutz gate; this is one flip.
    "llm_provider": "anthropic",
    "llm_model": "",                        # empty = provider default
    "vision_max_pages": 3,                  # scanned PDFs: pages rendered for vision
    "scan_min_chars_per_page": 50,          # below this avg -> treat as scanned

    # --- behaviour -------------------------------------------------------
    "error_toast_cooldown_min": 60,         # identical error toasts max 1/h
    "consecutive_poll_failures_alert": 5,   # then one daily "Verbindung" toast
}

# German UI strings, one place. {}-style format fields filled by notify.py.
TEXTE = {
    "toast_ok_title": "Befund abgelegt ✅",
    "toast_ok_body": "{titel}: {vorname} {nachname} ({geburtsdatum}). "
                     "Zusammenfassung ist in der Zwischenablage, bitte in DigiSono einfügen.",
    "toast_unrecognized_title": "Befund nicht erkannt ⚠️",
    "toast_unrecognized_body": "PDF «{dateiname}» von {absender}: Name oder Geburtsdatum "
                               "nicht lesbar. Bitte manuell bearbeiten (Mail ist unmarkiert).",
    "toast_filing_failed_title": "Ablage fehlgeschlagen ⚠️",
    "toast_filing_failed_body": "PDF «{dateiname}» konnte nicht abgelegt werden. "
                                "Bitte Ordner prüfen: {ziel}",
    "toast_connection_title": "Befund-Automat: Verbindung gestört ⚠️",
    "toast_connection_body": "Das Postfach ist seit längerem nicht erreichbar. "
                             "Neue Befunde bitte wie bisher von Hand bearbeiten.",
    "clipboard_doc_header": "[{titel} · {vorname} {nachname}]",
    "tray_status_ok": "Befund-Automat läuft ({n} Befunde heute)",
    "tray_quit": "Beenden",
    "tray_open_log": "Protokoll öffnen",
}


# ---------------------------------------------------------------------------
# Layered loading
# ---------------------------------------------------------------------------


def _load_json_overrides() -> dict:
    cfg_file = data_dir() / "config.json"
    if not cfg_file.exists():
        return {}
    try:
        loaded = json.loads(cfg_file.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}
    except Exception as e:  # corrupt config must not kill the app -> defaults
        print(f"[befund-config] config.json unlesbar, nutze Defaults: {e!r}", flush=True)
        return {}


def _env_override(key: str, current):
    raw = os.environ.get("BEFUND_" + key.upper())
    if raw is None:
        return current
    if isinstance(current, bool):
        return raw.strip().lower() in ("1", "true", "yes", "ja")
    if isinstance(current, int):
        try:
            return int(raw)
        except ValueError:
            return current
    return raw


def load() -> dict:
    """Resolve the effective config: defaults < config.json < BEFUND_* env."""
    cfg = dict(_DEFAULTS)
    for k, v in _load_json_overrides().items():
        if k in cfg:
            cfg[k] = v
    for k in cfg:
        cfg[k] = _env_override(k, cfg[k])
    return cfg


def imap_settings(cfg: dict) -> dict:
    """The active profile's IMAP connection settings (without the secret)."""
    p = cfg.get("profile", "test")
    prefix = "hin" if p == "hin" else "test"
    return {
        "profile": p,
        "host": cfg[f"{prefix}_imap_host"],
        "port": int(cfg[f"{prefix}_imap_port"]),
        "user": cfg[f"{prefix}_imap_user"],
        "folder": cfg.get("mailbox_folder", "INBOX"),
    }
