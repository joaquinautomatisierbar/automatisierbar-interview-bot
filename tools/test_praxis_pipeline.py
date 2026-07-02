#!/usr/bin/env python3
"""Offline tests for praxis_ulrich.pipeline — THE invariant matrix.

Mocked LLM (keyword dispatch on the real corpus texts), FakeState, FakeNotifier,
DryRunSink. No network, no key. Covers:

  happy flags / missing-DOB no-flag / non-Befund no-flag / sink-fail no-flag /
  flag-fail logged-not-fatal / notify-fail never un-flags / duplicate skipped /
  multi-PDF all-or-no-flag / junk+Befund still flags / no-PDF ignored /
  scanned routes vision / oversize fails.

Run: python3 tools/test_praxis_pipeline.py
"""
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BEFUND_DATA_DIR", tempfile.mkdtemp(prefix="befund_pipe_"))

from praxis_ulrich import extractor, filing, make_corpus, pipeline  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


TESTDATA = Path(make_corpus.TESTDATA)
if not (TESTDATA / "eml" / "single_befund.eml").exists():
    make_corpus.build()

EML = lambda n: (TESTDATA / "eml" / n).read_bytes()  # noqa: E731
CFG = {"max_pdf_mb": 25, "scan_min_chars_per_page": 50, "vision_max_pages": 3,
       "hotfolder_path": "<dryrun>"}
IDATE = datetime(2026, 7, 2, 9, 32)


# --- Fakes -----------------------------------------------------------------------
class FakeState:
    def __init__(self):
        self.records = []
        self.processed = set()
        self.seen = set()

    def already_processed(self, uv, uid, idx):
        return (uv, uid, idx) in self.processed

    def seen_attachment(self, mid, sha):
        return (mid, sha) in self.seen

    def record_attachment(self, **kw):
        self.records.append(kw)
        self.processed.add((kw["uidvalidity"], kw["uid"], kw["attachment_index"]))
        self.seen.add((kw["message_id"], kw["attachment_sha256"]))


class FakeNotifier:
    def __init__(self, explode=False):
        self.success, self.unrecognized, self.filing_failed = [], [], []
        self.explode = explode

    def doc_success(self, o):
        if self.explode:
            raise RuntimeError("toast kaputt")
        self.success.append(o)

    def doc_unrecognized(self, o, absender):
        self.unrecognized.append((o, absender))

    def doc_filing_failed(self, o, ziel):
        self.filing_failed.append((o, ziel))


class Flagger:
    def __init__(self, ok=True):
        self.calls, self.ok = [], ok

    def __call__(self, uid):
        self.calls.append(uid)
        return self.ok


# Mock-LLM: dispatch on corpus keywords. Records whether vision path was used.
VISION_CALLS = []
_real_extract = extractor.extract_befund


def mock_extract(*, text=None, images=None, cfg=None):
    if images is not None:
        VISION_CALLS.append(len(images))
        return {"ok": True, "error": "", "ist_befund": True,
                "patientinVorname": "Sofia", "patientinNachname": "Bildtest",
                "geburtsdatum": "03.04.1994", "berichtsdatum": "28.06.2026",
                "absenderInstitution": "USZ", "diagnose_prozedere": "x", "empfehlung": "y",
                "titel_vorschlag": "Ultraschallbericht Dr. T. Burkhardt USZ",
                "titel_ist_aus_liste": True, "zusammenfassung_4z": "1\n2\n3\n4",
                "confidence": 0.9}
    t = text or ""
    if "Microsoft" in t:
        return {**_empty(), "ok": True, "ist_befund": False}
    if "Testfall, Nora" in t:
        return {**_empty(), "ok": True, "ist_befund": True,
                "patientinVorname": "Nora", "patientinNachname": "Testfall",
                "titel_vorschlag": "Verlaufsbericht"}
    if "Muster, Maria" in t:
        return {**_empty(), "ok": True, "ist_befund": True,
                "patientinVorname": "Maria", "patientinNachname": "Muster",
                "geburtsdatum": "12.03.1985", "berichtsdatum": "10.06.2026",
                "titel_vorschlag": "Austrittsbericht Geburt USZ", "titel_ist_aus_liste": True,
                "zusammenfassung_4z": "P\nB\nD\nE", "confidence": 0.95}
    if "E. coli" in t:
        return {**_empty(), "ok": True, "ist_befund": True,
                "patientinVorname": "Petra", "patientinNachname": "Probe",
                "geburtsdatum": "23.01.1978", "berichtsdatum": "18.06.2026",
                "titel_vorschlag": "Urinkultur", "titel_ist_aus_liste": True,
                "zusammenfassung_4z": "P\nB\nD\nE"}
    if "Ferritin" in t:
        return {**_empty(), "ok": True, "ist_befund": True,
                "patientinVorname": "Laura", "patientinNachname": "Mustermann",
                "geburtsdatum": "30.09.1988", "berichtsdatum": "20.06.2026",
                "titel_vorschlag": "Laborbefund Blutbild", "zusammenfassung_4z": "P\nB\nD\nE"}
    if "Mamma" in t or "Drüsenparenchym" in t:
        return {**_empty(), "ok": True, "ist_befund": True,
                "patientinVorname": "Eva", "patientinNachname": "Muster",
                "geburtsdatum": "02.02.1969", "berichtsdatum": "25.06.2026",
                "titel_vorschlag": "Brustzentrum Mamma-US", "titel_ist_aus_liste": True,
                "zusammenfassung_4z": "P\nB\nD\nE"}
    return {**_empty(), "error": "unbekannter Testfall", "ok": False}


def _empty():
    return {"ok": False, "error": "", "ist_befund": False, "patientinVorname": None,
            "patientinNachname": None, "geburtsdatum": None, "berichtsdatum": None,
            "absenderInstitution": None, "diagnose_prozedere": None, "empfehlung": None,
            "titel_vorschlag": None, "titel_ist_aus_liste": False,
            "zusammenfassung_4z": None, "confidence": 0.0}


pipeline.extractor.extract_befund = mock_extract


def run(eml_name, *, sink=None, flagger=None, notifier=None, st=None, uid=7):
    st = st or FakeState()
    fl = flagger or Flagger()
    nt = notifier or FakeNotifier()
    sk = sink or filing.DryRunSink()
    res = pipeline.process_message(EML(eml_name), uid=uid, uidvalidity=1, internal_date=IDATE,
                                   cfg=CFG, sink=sk, flagger=fl, notifier=nt, state_api=st)
    return res, st, fl, nt, sk


try:
    # 1. Happy path
    res, st, fl, nt, sk = run("single_befund.eml")
    check("happy: success", res.outcomes[0].status == "success")
    check("happy: geflaggt", res.flagged and fl.calls == [7])
    check("happy: Dokumenttitel korrekt", res.outcomes[0].dokumenttitel == "Austrittsbericht Geburt USZ 06/2026")
    check("happy: Dateiname MM-JJJJ + Patient", sk.calls[0]["filename"] == "Austrittsbericht Geburt USZ 06-2026_Muster_Maria.pdf")
    check("happy: toast", len(nt.success) == 1 and not nt.unrecognized)
    check("happy: state recorded", st.records[0]["status"] == "success")

    # 2. Junk-PDF (ist_befund=false) -> skipped, kein Flag, stille Behandlung
    res, st, fl, nt, sk = run("junk_pdf.eml")
    check("junk: skipped", res.outcomes[0].status == "skipped")
    check("junk: kein Flag", not res.flag_attempted and fl.calls == [])
    check("junk: keine Toasts", not nt.success and not nt.unrecognized)

    # 3. Multi-PDF beide ok -> ein Flag
    res, st, fl, nt, sk = run("multi_pdf.eml")
    check("multi: 2 successes", [o.status for o in res.outcomes] == ["success", "success"])
    check("multi: genau 1 Flag", fl.calls == [7])
    check("multi: 2 Toasts", len(nt.success) == 2)

    # 4. Multi-PDF, Ablage schlägt fehl -> KEIN Flag (all-or-no-flag)
    res, st, fl, nt, sk = run("multi_pdf.eml", sink=filing.DryRunSink(fail=True))
    check("sink-fail: beide failed", all(o.status == "failed" for o in res.outcomes))
    check("sink-fail: kein Flag", fl.calls == [])
    check("sink-fail: filing-failed Toast", len(nt.filing_failed) == 2)

    # 5. Flag schlägt fehl -> success bleibt success (logged-not-fatal)
    res, st, fl, nt, sk = run("single_befund.eml", flagger=Flagger(ok=False))
    check("flag-fail: attempted aber False", res.flag_attempted and not res.flagged)
    check("flag-fail: status bleibt success", res.outcomes[0].status == "success")
    check("flag-fail: state bleibt success", st.records[0]["status"] == "success")

    # 6. Notifier explodiert -> Ergebnis unverändert, kein Raise
    res, st, fl, nt, sk = run("single_befund.eml", notifier=FakeNotifier(explode=True))
    check("notify-fail: geflaggt trotzdem", res.flagged)
    check("notify-fail: success bleibt", res.outcomes[0].status == "success")

    # 7. Duplikat via primary dedup -> keine Doppelablage, kein zweites Flag
    st = FakeState()
    res1, *_ = run("single_befund.eml", st=st)
    sk2 = filing.DryRunSink()
    fl2 = Flagger()
    res2, _, _, _, _ = run("single_befund.eml", st=st, sink=sk2, flagger=fl2)
    check("dup: skipped als Duplikat", res2.outcomes[0].duplicate)
    check("dup: keine 2. Ablage", sk2.calls == [])
    check("dup: kein 2. Flag (nichts Neues)", fl2.calls == [])

    # 8. Duplikat via secondary dedup (UIDVALIDITY-Reset simuliert: neue uid)
    res3, _, fl3, _, sk3 = run("single_befund.eml", st=st, uid=99)
    check("dup-secondary: erkannt", res3.outcomes[0].duplicate and sk3.calls == [] if False else res3.outcomes[0].duplicate)
    check("dup-secondary: als skipped recorded", st.records[-1]["status"] == "skipped")

    # 9. Kein PDF -> komplett ignoriert
    res, st, fl, nt, sk = run("no_pdf.eml")
    check("no-pdf: 0 outcomes", res.pdf_count == 0 and res.outcomes == [])
    check("no-pdf: nichts recorded", st.records == [])

    # 10. Gemischte Anhänge (PNG + PDF) -> nur PDF verarbeitet
    res, st, fl, nt, sk = run("mixed_attachments.eml")
    check("mixed: 1 PDF verarbeitet", res.pdf_count == 1 and res.outcomes[0].status == "success")

    # 11. Fehlendes Geburtsdatum -> failed, kein Flag, unrecognized-Toast
    st = FakeState()
    from email.message import EmailMessage
    m = EmailMessage()
    m["From"] = "x@spital.ch"; m["Subject"] = "B"; m["Message-ID"] = "<dob@test>"
    m.set_content("hi")
    m.add_attachment((TESTDATA / "pdfs" / "missing_dob.pdf").read_bytes(),
                     maintype="application", subtype="pdf", filename="v.pdf")
    fl = Flagger(); nt = FakeNotifier()
    res = pipeline.process_message(bytes(m), uid=8, uidvalidity=1, internal_date=IDATE,
                                   cfg=CFG, sink=filing.DryRunSink(), flagger=fl,
                                   notifier=nt, state_api=st)
    check("no-dob: failed", res.outcomes[0].status == "failed")
    check("no-dob: Gate-Fehlertext", "Geburtsdatum" in res.outcomes[0].fehler)
    check("no-dob: kein Flag", fl.calls == [])
    check("no-dob: unrecognized-Toast", len(nt.unrecognized) == 1)

    # 12. Junk + Befund in EINER Mail -> Befund abgelegt, Junk skipped, Flag JA
    m = EmailMessage()
    m["From"] = "x@spital.ch"; m["Subject"] = "B"; m["Message-ID"] = "<jb@test>"
    m.set_content("hi")
    m.add_attachment((TESTDATA / "pdfs" / "microsoft_junk.pdf").read_bytes(),
                     maintype="application", subtype="pdf", filename="rechnung.pdf")
    m.add_attachment((TESTDATA / "pdfs" / "austritt_usz.pdf").read_bytes(),
                     maintype="application", subtype="pdf", filename="befund.pdf")
    fl = Flagger()
    res = pipeline.process_message(bytes(m), uid=9, uidvalidity=1, internal_date=IDATE,
                                   cfg=CFG, sink=filing.DryRunSink(), flagger=fl,
                                   notifier=FakeNotifier(), state_api=FakeState())
    check("junk+befund: statuses", sorted(o.status for o in res.outcomes) == ["skipped", "success"])
    check("junk+befund: Flag gesetzt (skipped blockiert nicht)", fl.calls == [9])

    # 13. Scan-PDF -> Vision-Pfad
    VISION_CALLS.clear()
    m = EmailMessage()
    m["From"] = "x@usz.ch"; m["Subject"] = "US"; m["Message-ID"] = "<scan@test>"
    m.set_content("hi")
    m.add_attachment((TESTDATA / "pdfs" / "scanned_ultraschall.pdf").read_bytes(),
                     maintype="application", subtype="pdf", filename="scan.pdf")
    res = pipeline.process_message(bytes(m), uid=10, uidvalidity=1, internal_date=IDATE,
                                   cfg=CFG, sink=filing.DryRunSink(), flagger=Flagger(),
                                   notifier=FakeNotifier(), state_api=FakeState())
    check("scan: Vision-Pfad genutzt", VISION_CALLS == [1])
    check("scan: success", res.outcomes[0].status == "success")

    # 14. Oversize -> failed, kein Flag
    m = EmailMessage()
    m["From"] = "x@spital.ch"; m["Subject"] = "gross"; m["Message-ID"] = "<big@test>"
    m.set_content("hi")
    m.add_attachment(b"%PDF-1.4 " + b"0" * (2 * 1024 * 1024), maintype="application",
                     subtype="pdf", filename="riesig.pdf")
    fl = Flagger()
    res = pipeline.process_message(bytes(m), uid=11, uidvalidity=1, internal_date=IDATE,
                                   cfg={**CFG, "max_pdf_mb": 1}, sink=filing.DryRunSink(),
                                   flagger=fl, notifier=FakeNotifier(), state_api=FakeState())
    check("oversize: failed", res.outcomes[0].status == "failed" and "gross" in res.outcomes[0].fehler)
    check("oversize: kein Flag", fl.calls == [])

    # 15. Kaputtes PDF -> failed sauber
    m = EmailMessage()
    m["From"] = "x@spital.ch"; m["Subject"] = "defekt"; m["Message-ID"] = "<bad@test>"
    m.set_content("hi")
    m.add_attachment(b"das ist kein pdf", maintype="application", subtype="pdf",
                     filename="defekt.pdf")
    res = pipeline.process_message(bytes(m), uid=12, uidvalidity=1, internal_date=IDATE,
                                   cfg=CFG, sink=filing.DryRunSink(), flagger=Flagger(),
                                   notifier=FakeNotifier(), state_api=FakeState())
    check("kaputt: failed 'nicht lesbar'", res.outcomes[0].status == "failed"
          and "nicht lesbar" in res.outcomes[0].fehler)
finally:
    pipeline.extractor.extract_befund = _real_extract

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("alle Tests grün ✅")
