"""pipeline.py — per-message orchestration. THE fail-safe invariant lives here.

Per PDF attachment, strictly in this order:

    extract text (vision fallback)
    -> LLM extraction
    -> gate: ist_befund AND Nachname AND Geburtsdatum
    -> title + filename (deterministic)
    -> sink.file() succeeded
    -> record success
    ...and only after ALL attachments of the message are handled:
    -> red flag, IFF at least one PDF was newly filed AND none failed

Failure semantics (what blocks the flag vs. what doesn't):

    failed   should have been filed but wasn't (extraction error, gate miss,
             oversize, sink error) -> BLOCKS the flag. Unflagged mail = Dr.
             Ulrich handles it by hand, exactly like today.
    skipped  legitimately not our work (ist_befund=false junk, duplicate)
             -> does NOT block the flag.

A flag failure after successful filing is logged, never fatal, and never
rolls anything back. Notify (toast/clipboard) runs after the flag and is
best-effort. Nothing in this module deletes, moves, or marks mail read.

Everything is dependency-injected (sink, flagger, notifier, state_api) so the
whole matrix is offline-testable — see tools/test_praxis_pipeline.py.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime

try:
    from . import config, extractor, mailbox, pdf_text, titles, state as state_mod
except ImportError:  # direct-script / test runs
    import config  # type: ignore
    import extractor  # type: ignore
    import mailbox  # type: ignore
    import pdf_text  # type: ignore
    import titles  # type: ignore
    import state as state_mod  # type: ignore

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


@dataclass
class AttachmentOutcome:
    index: int
    pdf_name: str
    status: str
    fehler: str = ""
    dokumenttitel: str = ""
    filed_filename: str = ""
    vorname: str = ""
    nachname: str = ""
    geburtsdatum: str = ""
    zusammenfassung: str = ""
    duplicate: bool = False


@dataclass
class MessageResult:
    uid: int
    pdf_count: int = 0
    outcomes: list = field(default_factory=list)
    flag_attempted: bool = False
    flagged: bool = False

    @property
    def newly_filed(self) -> int:
        return sum(1 for o in self.outcomes if o.status == STATUS_SUCCESS and not o.duplicate)


def process_message(raw: bytes, *, uid: int, uidvalidity: int,
                    internal_date: datetime | None,
                    cfg: dict, sink, flagger, notifier,
                    state_api=state_mod) -> MessageResult:
    """Handle one raw message. flagger: (uid) -> bool. Never raises."""
    result = MessageResult(uid=uid)
    meta = mailbox.parse_message_meta(raw)
    atts = mailbox.extract_pdf_attachments(raw)
    result.pdf_count = len(atts)
    if not atts:
        return result  # kein PDF -> Mail vollständig ignorieren (Interview-Regel 1)

    max_bytes = int(cfg.get("max_pdf_mb", 25)) * 1024 * 1024

    for fname, blob, idx in atts:
        if state_api.already_processed(uidvalidity, uid, idx):
            result.outcomes.append(AttachmentOutcome(
                index=idx, pdf_name=fname, status=STATUS_SKIPPED,
                fehler="bereits verarbeitet", duplicate=True))
            continue

        sha = hashlib.sha256(blob).hexdigest()
        if state_api.seen_attachment(meta["message_id"], sha):
            # UIDVALIDITY-Reset / state-Restore: schon einmal behandelt.
            state_api.record_attachment(
                uidvalidity=uidvalidity, uid=uid, attachment_index=idx,
                attachment_sha256=sha, message_id=meta["message_id"],
                absender=meta["from_email"], pdf_dateiname=fname,
                status=STATUS_SKIPPED, fehler="Duplikat (bereits verarbeitet)")
            result.outcomes.append(AttachmentOutcome(
                index=idx, pdf_name=fname, status=STATUS_SKIPPED,
                fehler="Duplikat", duplicate=True))
            continue

        outcome = _process_attachment(
            fname, blob, idx, sha, meta, internal_date, cfg, sink, notifier,
            max_bytes=max_bytes)
        state_api.record_attachment(
            uidvalidity=uidvalidity, uid=uid, attachment_index=idx,
            attachment_sha256=sha, message_id=meta["message_id"],
            absender=meta["from_email"], pdf_dateiname=fname,
            status=outcome.status, fehler=outcome.fehler,
            filed_filename=outcome.filed_filename, dokumenttitel=outcome.dokumenttitel,
            patientin_vorname=outcome.vorname, patientin_nachname=outcome.nachname,
            geburtsdatum=outcome.geburtsdatum)
        result.outcomes.append(outcome)

    # ---- Flaggen: nur wenn neu abgelegt wurde und NICHTS fehlgeschlagen ist.
    any_failed = any(o.status == STATUS_FAILED for o in result.outcomes)
    if result.newly_filed > 0 and not any_failed:
        result.flag_attempted = True
        try:
            result.flagged = bool(flagger(uid))
        except Exception:
            result.flagged = False
        if not result.flagged:
            print(f"[befund-pipeline] Fähnchen für UID {uid} fehlgeschlagen "
                  "(Ablage war erfolgreich)", flush=True)

    # ---- Notify zuletzt: best-effort, ändert nie mehr etwas am Zustand.
    for o in result.outcomes:
        if o.status == STATUS_SUCCESS and not o.duplicate:
            _safe(notifier.doc_success, o)
        elif o.status == STATUS_FAILED and o.fehler.startswith("Ablage"):
            _safe(notifier.doc_filing_failed, o, cfg.get("hotfolder_path", ""))
        elif o.status == STATUS_FAILED:
            _safe(notifier.doc_unrecognized, o, meta["from_email"])
    return result


def _process_attachment(fname: str, blob: bytes, idx: int, sha: str, meta: dict,
                        internal_date: datetime | None, cfg: dict, sink, notifier,
                        *, max_bytes: int) -> AttachmentOutcome:
    out = AttachmentOutcome(index=idx, pdf_name=fname, status=STATUS_FAILED)

    if len(blob) > max_bytes:
        out.fehler = f"PDF zu gross ({len(blob) // (1024 * 1024)} MB)"
        return out

    text, pages = pdf_text.extract_text(blob)
    if pages == 0:
        out.fehler = "PDF nicht lesbar"
        return out

    images = None
    if pdf_text.is_scanned(text, pages, int(cfg.get("scan_min_chars_per_page", 50))):
        images = pdf_text.render_pages_png(blob, int(cfg.get("vision_max_pages", 3)))
        if not images:
            out.fehler = "Scan nicht renderbar"
            return out

    ex = extractor.extract_befund(text=None if images else text,
                                  images=images, cfg=cfg)
    if not ex["ok"]:
        out.fehler = ex["error"] or "Extraktion fehlgeschlagen"
        return out

    if not ex["ist_befund"]:
        out.status = STATUS_SKIPPED
        out.fehler = "kein Befund (z.B. Rechnung/Systemmail)"
        return out

    # DER Gate: ohne Nachname UND Geburtsdatum keine Zuordnung -> Handarbeit.
    if not ex["patientinNachname"] or not ex["geburtsdatum"]:
        out.fehler = "Patientin nicht erkannt (Name oder Geburtsdatum fehlt)"
        return out

    titel, _aus_liste = titles.resolve_titel(ex["titel_vorschlag"])
    display_sfx, file_sfx = titles.datum_suffix(ex["berichtsdatum"], internal_date)
    out.dokumenttitel = titles.dokumenttitel(titel, display_sfx)
    out.vorname = ex["patientinVorname"] or ""
    out.nachname = ex["patientinNachname"]
    out.geburtsdatum = ex["geburtsdatum"]
    out.zusammenfassung = ex["zusammenfassung_4z"] or ""

    filename = titles.build_filename(titel, file_sfx, out.nachname, out.vorname)
    res = sink.file(blob, filename, meta={
        "nachname": out.nachname, "vorname": out.vorname,
        "geburtsdatum": out.geburtsdatum, "dokumenttitel": out.dokumenttitel,
        "berichtsdatum": ex["berichtsdatum"] or "",
        "institution": ex["absenderInstitution"] or "",
    })
    if not res.ok:
        out.fehler = res.error if res.error.startswith("Ablage") else f"Ablage fehlgeschlagen: {res.error}"
        return out

    out.status = STATUS_SUCCESS
    out.filed_filename = res.final_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return out


def _safe(fn, *args):
    try:
        fn(*args)
    except Exception as e:
        print(f"[befund-pipeline] Notify-Fehler (ignoriert): {e!r}", flush=True)
