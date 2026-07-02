#!/usr/bin/env python3
"""Offline tests for praxis_ulrich pdf_text + extractor sanitization + provider
dispatch. No network, no API key (extractor is tested via mocked provider).

Run: python3 tools/test_praxis_extractor.py
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BEFUND_DATA_DIR", tempfile.mkdtemp(prefix="befund_ext_"))
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("BEFUND_LLM_API_KEY", None)

from praxis_ulrich import extractor, pdf_text, providers, make_corpus  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


TESTDATA = Path(make_corpus.TESTDATA)
if not (TESTDATA / "pdfs" / "austritt_usz.pdf").exists():
    make_corpus.build()

# --- pdf_text: text path ---------------------------------------------------------
blob = (TESTDATA / "pdfs" / "austritt_usz.pdf").read_bytes()
text, pages = pdf_text.extract_text(blob)
check("Text extrahiert", "Muster, Maria" in text and "12.03.1985" in text)
check("Seitenmarker", "[Seite 1]" in text)
check("page_count 1", pages == 1)
check("nicht als Scan erkannt", not pdf_text.is_scanned(text, pages))

# --- pdf_text: scanned path -------------------------------------------------------
sblob = (TESTDATA / "pdfs" / "scanned_ultraschall.pdf").read_bytes()
stext, spages = pdf_text.extract_text(sblob)
check("Scan: kein Textlayer", len(stext) < 50 and spages == 1)
check("Scan erkannt", pdf_text.is_scanned(stext, spages))
pngs = pdf_text.render_pages_png(sblob, max_pages=3)
check("Scan: PNG gerendert", len(pngs) == 1 and pngs[0][:8] == b"\x89PNG\r\n\x1a\n")

check("kaputtes PDF -> ('',0)", pdf_text.extract_text(b"kein pdf") == ("", 0))
check("kaputtes PDF -> keine Scans", pdf_text.render_pages_png(b"kein pdf") == [])
check("page_count 0 -> nicht Scan", not pdf_text.is_scanned("", 0))

# --- extractor: _parse_json --------------------------------------------------------
p = extractor._parse_json
check("plain JSON", p('{"a": 1}') == {"a": 1})
check("json fence", p('```json\n{"a": 1}\n```') == {"a": 1})
check("prosa drumherum", p('Hier: {"a": 1} fertig.') == {"a": 1})
try:
    p("kein json")
    check("kein JSON -> raises", False)
except ValueError:
    check("kein JSON -> raises", True)

# --- extractor: _sanitise ----------------------------------------------------------
s = extractor._sanitise({
    "ist_befund": "ja", "patientinVorname": "  Maria ", "patientinNachname": "Muster",
    "geburtsdatum": "12.03.1985", "berichtsdatum": "2026-06-10",
    "absenderInstitution": "USZ", "confidence": "1.7",
    "titel_vorschlag": "Urinkultur", "titel_ist_aus_liste": 1,
    "zusammenfassung_4z": "a\nb\nc\nd",
})
check("ist_befund truthy -> True", s["ist_befund"] is True)
check("Vorname getrimmt", s["patientinVorname"] == "Maria")
check("geburtsdatum TT.MM.JJJJ ok", s["geburtsdatum"] == "12.03.1985")
check("berichtsdatum falsches Format -> None", s["berichtsdatum"] is None)
check("confidence geklemmt", s["confidence"] == 1.0)
check("titel_ist_aus_liste -> bool", s["titel_ist_aus_liste"] is True)

s2 = extractor._sanitise({})
check("leeres dict -> alles leer/None", s2["patientinNachname"] is None and s2["ist_befund"] is False
      and s2["confidence"] == 0.0)
s3 = extractor._sanitise({"geburtsdatum": "1.3.1985", "confidence": None})
check("Datum ohne führende Null -> None", s3["geburtsdatum"] is None)
check("confidence None -> 0.0", s3["confidence"] == 0.0)

# --- extractor: never raises, gates ------------------------------------------------
r = extractor.extract_befund(text=None, images=None)
check("kein Inhalt -> ok=False", r["ok"] is False and "kein PDF-Inhalt" in r["error"])
r = extractor.extract_befund(text="Bericht ...")
check("kein API-Key -> ok=False, kein Raise", r["ok"] is False and "API-Key" in r["error"])

os.environ["BEFUND_LLM_API_KEY"] = "sk-test"
r = extractor.extract_befund(text="x", cfg={"llm_provider": "azure-openai"})
check("azure Stub -> ok=False mit Hinweis", r["ok"] is False and "Stub" in r["error"])
r = extractor.extract_befund(text="x", cfg={"llm_provider": "gibtsnicht"})
check("unbekannter Provider -> ok=False", r["ok"] is False)

# --- extractor: happy path mit gemocktem Provider -----------------------------------
_real = providers.run_extraction
def _mock(system, blocks, cfg, key, max_tokens=1200):
    check("System-Prompt enthält Titelliste", "Urinkultur" in system and "Verlaufsbericht" in system)
    check("System-Prompt verbietet Erfinden", "Erfinde NIEMALS" in system)
    return ('```json\n{"ist_befund": true, "patientinVorname": "Maria", '
            '"patientinNachname": "Muster", "geburtsdatum": "12.03.1985", '
            '"berichtsdatum": "10.06.2026", "absenderInstitution": "USZ", '
            '"diagnose_prozedere": "ok", "empfehlung": "ok", '
            '"titel_vorschlag": "Urinkultur", "titel_ist_aus_liste": true, '
            '"zusammenfassung_4z": "a\\nb\\nc\\nd", "confidence": 0.95}\n```')
providers.run_extraction = _mock
try:
    r = extractor.extract_befund(text="Patientin: Maria Muster ...")
    check("mock happy path ok", r["ok"] is True and r["patientinNachname"] == "Muster")
    check("4-Zeiler durchgereicht", r["zusammenfassung_4z"] == "a\nb\nc\nd")

    def _mock_broken(system, blocks, cfg, key, max_tokens=1200):
        return "Entschuldigung, das kann ich nicht."
    providers.run_extraction = _mock_broken
    r = extractor.extract_befund(text="x")
    check("unparsbare Antwort -> ok=False, kein Raise", r["ok"] is False)

    captured = {}
    def _mock_capture(system, blocks, cfg, key, max_tokens=1200):
        captured["blocks"] = blocks
        return '{"ist_befund": true}'
    providers.run_extraction = _mock_capture
    extractor.extract_befund(images=[b"png1", b"png2"])
    check("Bilder-Pfad: 2 image-Blocks + Hinweistext",
          [b["type"] for b in captured["blocks"]] == ["image_png", "image_png", "text"])
    extractor.extract_befund(text="nur text")
    check("Text-Pfad: 1 Text-Block", [b["type"] for b in captured["blocks"]] == ["text"])
finally:
    providers.run_extraction = _real
    del os.environ["BEFUND_LLM_API_KEY"]

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("alle Tests grün ✅")
