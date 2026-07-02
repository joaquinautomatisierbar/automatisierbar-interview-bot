#!/usr/bin/env python3
"""make_corpus.py — deterministic synthetic test corpus for the Befund-Automat.

Generates into tools/praxis_ulrich/testdata/ (committed to git):
  pdfs/<case_id>.pdf        13 German gynecology/lab report PDFs — ALL persons,
                            values and reports are FICTIONAL. Zero real patient
                            data, by construction.
  expected/<case_id>.json   golden extraction targets for eval_extraction.py
  eml/<name>.eml            5 raw RFC 5322 fixtures for mailbox/pipeline tests

PDFs are built with PyMuPDF (no extra dependency). The "scanned" case is a
text PDF rendered to PNG and re-embedded as image — a PDF without text layer,
which forces the vision path. Re-running always produces the same corpus
(no timestamps, no randomness).

Run: python3 tools/praxis_ulrich/make_corpus.py
"""

from __future__ import annotations

import json
import sys
from email.message import EmailMessage
from pathlib import Path

TESTDATA = Path(__file__).resolve().parent / "testdata"

_HEADER = "{institution}\n{abteilung}\n\n"
_PATIENT = "Patientin: {name}, geb. {geb}\n\n"


def _befund_text(institution, abteilung, name, geb, datum, titelzeile, befund, empfehlung):
    parts = [_HEADER.format(institution=institution, abteilung=abteilung)]
    parts.append(f"{titelzeile}\n")
    if datum:
        parts.append(f"Berichtsdatum: {datum}\n\n")
    parts.append(_PATIENT.format(name=name, geb=geb) if geb else f"Patientin: {name}\n\n")
    parts.append(f"Befund:\n{befund}\n\n")
    parts.append(f"Beurteilung und Empfehlung:\n{empfehlung}\n")
    return "".join(parts)


# case_id -> (pdf_text, golden)
# golden fields: ist_befund, nachname, vorname, geburtsdatum, berichtsdatum,
#   titel_erwartet (None = free-form acceptable), titel_ist_aus_liste, gate_pass
CASES: dict[str, tuple[str, dict]] = {
    "austritt_usz": (
        _befund_text(
            "Universitätsspital Zürich", "Klinik für Geburtshilfe",
            "Muster, Maria", "12.03.1985", "10.06.2026",
            "Austrittsbericht nach Spontangeburt",
            "Spontangeburt am 08.06.2026 in der 39 4/7 SSW. Mädchen, 3240 g, APGAR 8/9/10. "
            "Unauffälliger Wochenbettverlauf, Uterus gut kontrahiert, Lochien regelrecht.",
            "Wochenbettkontrolle in 6 Wochen in der Praxis. Bei Fieber oder verstärkter "
            "Blutung vorzeitige Wiedervorstellung.",
        ),
        {"ist_befund": True, "nachname": "Muster", "vorname": "Maria",
         "geburtsdatum": "12.03.1985", "berichtsdatum": "10.06.2026",
         "titel_erwartet": "Austrittsbericht Geburt USZ", "titel_ist_aus_liste": True,
         "gate_pass": True},
    ),
    "nipt_vnatal": (
        _befund_text(
            "Genetica AG Zürich", "Pränataldiagnostik",
            "Beispiel, Anna", "07.11.1992", "15.06.2026",
            "NIPT V-Natal — Nicht-invasiver Pränataltest",
            "V-Natal NIPT aus mütterlichem Blut, 13 1/7 SSW. Trisomie 21, 18, 13: "
            "kein Hinweis auf Aneuploidie. Fetale Fraktion 9.2%.",
            "Unauffälliges Resultat. Reguläre Schwangerschaftskontrollen weiterführen.",
        ),
        {"ist_befund": True, "nachname": "Beispiel", "vorname": "Anna",
         "geburtsdatum": "07.11.1992", "berichtsdatum": "15.06.2026",
         "titel_erwartet": "NIPT V-Natal", "titel_ist_aus_liste": True, "gate_pass": True},
    ),
    "urinkultur": (
        _befund_text(
            "Synlab Suisse", "Mikrobiologie",
            "Probe, Petra", "23.01.1978", "18.06.2026",
            "Urinkultur — Mittelstrahlurin",
            "E. coli 10^5 KBE/ml. Resistenzprüfung: sensibel auf Nitrofurantoin, "
            "Fosfomycin; resistent auf Amoxicillin.",
            "Antibiogramm-gerechte Therapie empfohlen. Kontrollkultur nach Abschluss "
            "der Therapie.",
        ),
        {"ist_befund": True, "nachname": "Probe", "vorname": "Petra",
         "geburtsdatum": "23.01.1978", "berichtsdatum": "18.06.2026",
         "titel_erwartet": "Urinkultur", "titel_ist_aus_liste": True, "gate_pass": True},
    ),
    "labor_blutbild": (
        _befund_text(
            "Labor Team AG", "Hämatologie",
            "Mustermann, Laura", "30.09.1988", "20.06.2026",
            "Laborbefund — kleines Blutbild und Ferritin",
            "Hämoglobin 10.9 g/dl (leicht erniedrigt), Ferritin 8 µg/l (deutlich "
            "erniedrigt). Übrige Werte im Normbereich.",
            "Eisensubstitution empfohlen. Kontrolle von Hb und Ferritin in 8 Wochen.",
        ),
        {"ist_befund": True, "nachname": "Mustermann", "vorname": "Laura",
         "geburtsdatum": "30.09.1988", "berichtsdatum": "20.06.2026",
         "titel_erwartet": None, "titel_ist_aus_liste": False, "gate_pass": True},
    ),
    "zyto_pap": (
        _befund_text(
            "Institut für Pathologie Zürich", "Zytologie",
            "Fiktiv, Claudia", "14.05.1975", "22.06.2026",
            "Zytologischer Befund — Zervixabstrich (PAP)",
            "Abstrich gut beurteilbar. Plattenepithelzellen ohne intraepitheliale "
            "Läsion oder Malignität (NILM). HPV high-risk: negativ.",
            "Nächster Vorsorgeabstrich in 3 Jahren gemäss Richtlinien.",
        ),
        {"ist_befund": True, "nachname": "Fiktiv", "vorname": "Claudia",
         "geburtsdatum": "14.05.1975", "berichtsdatum": "22.06.2026",
         "titel_erwartet": None, "titel_ist_aus_liste": False, "gate_pass": True},
    ),
    "mamma_us": (
        _befund_text(
            "Stadtspital Zürich Triemli", "Brustzentrum",
            "Muster, Eva", "02.02.1969", "25.06.2026",
            "Mammasonografie beidseits",
            "Beidseits regelrechtes Drüsenparenchym. Keine suspekte Herdläsion, keine "
            "pathologisch vergrösserten Lymphknoten axillär. BI-RADS 1 beidseits.",
            "Reguläre Vorsorge weiterführen. Nächste Kontrolle in 12 Monaten.",
        ),
        {"ist_befund": True, "nachname": "Muster", "vorname": "Eva",
         "geburtsdatum": "02.02.1969", "berichtsdatum": "25.06.2026",
         "titel_erwartet": "Brustzentrum Mamma-US", "titel_ist_aus_liste": True,
         "gate_pass": True},
    ),
    "missing_dob": (
        _befund_text(
            "Spital Limmattal", "Frauenklinik",
            "Testfall, Nora", "", "26.06.2026",
            "Verlaufsbericht ambulante Kontrolle",
            "Patientin in gutem Allgemeinzustand. Verlaufskontrolle unauffällig. "
            "(Hinweis: Geburtsdatum auf diesem Bericht nicht angegeben.)",
            "Weiteres Prozedere gemäss Praxis.",
        ),
        {"ist_befund": True, "nachname": "Testfall", "vorname": "Nora",
         "geburtsdatum": None, "berichtsdatum": "26.06.2026",
         "titel_erwartet": None, "titel_ist_aus_liste": False, "gate_pass": False},
    ),
    "reversed_name": (
        _befund_text(
            "Universitätsspital Zürich", "Ultraschall-Abteilung",
            "Sanchez Rivera Carmen", "19.07.1991", "27.06.2026",
            "Ultraschallbericht Dr. T. Burkhardt",
            "Biometrie in der 28 2/7 SSW regelrecht, Schätzgewicht 1180 g (P45). "
            "Fruchtwassermenge und Doppler unauffällig. Plazenta Vorderwand, regelrecht.",
            "Nächste Wachstumskontrolle in 4 Wochen.",
        ),
        {"ist_befund": True, "nachname": "Sanchez Rivera", "vorname": "Carmen",
         "geburtsdatum": "19.07.1991", "berichtsdatum": "27.06.2026",
         "titel_erwartet": "Ultraschallbericht Dr. T. Burkhardt USZ",
         "titel_ist_aus_liste": True, "gate_pass": True, "lenient_name_order": True},
    ),
    "scanned_ultraschall": (
        _befund_text(
            "Universitätsspital Zürich", "Ultraschall-Abteilung",
            "Bildtest, Sofia", "03.04.1994", "28.06.2026",
            "Ultraschallbericht Dr. T. Burkhardt",
            "Ersttrimester-Ultraschall 12 3/7 SSW. Scheitel-Steiss-Länge 61 mm, "
            "Nackentransparenz 1.4 mm. Zeitgerechte Entwicklung.",
            "Reguläre Kontrolle in 4 Wochen. NIPT besprochen.",
        ),
        {"ist_befund": True, "nachname": "Bildtest", "vorname": "Sofia",
         "geburtsdatum": "03.04.1994", "berichtsdatum": "28.06.2026",
         "titel_erwartet": "Ultraschallbericht Dr. T. Burkhardt USZ",
         "titel_ist_aus_liste": True, "gate_pass": True, "scanned": True},
    ),
    "microsoft_junk": (
        "Microsoft Ireland Operations Ltd.\n\nIhre Rechnung für Microsoft 365 Business "
        "Standard\n\nRechnungsnummer: E0400123456\nAbrechnungszeitraum: 01.06.2026 - "
        "30.06.2026\nBetrag: CHF 13.70\n\nVielen Dank für Ihren Einkauf. Diese Rechnung "
        "wurde automatisch erstellt.",
        {"ist_befund": False, "nachname": None, "vorname": None,
         "geburtsdatum": None, "berichtsdatum": None,
         "titel_erwartet": None, "titel_ist_aus_liste": False, "gate_pass": False},
    ),
    "freeform_hiv": (
        _befund_text(
            "Synlab Suisse", "Serologie",
            "Anonyma, Julia", "11.12.1996", "29.06.2026",
            "Serologischer Befund — HIV-Screening",
            "HIV-1/2-Antikörper und p24-Antigen (4. Generation): negativ.",
            "Kein Hinweis auf HIV-Infektion. Jahreskontrolle empfohlen.",
        ),
        {"ist_befund": True, "nachname": "Anonyma", "vorname": "Julia",
         "geburtsdatum": "11.12.1996", "berichtsdatum": "29.06.2026",
         "titel_erwartet": None, "titel_ist_aus_liste": False, "gate_pass": True},
    ),
    "no_berichtsdatum": (
        _befund_text(
            "Gynart AG Zürich", "Andrologie-Labor",
            "Partnerin, Mia", "25.08.1990", "",
            "Ejakulatanalyse des Partners",
            "Spermiogramm des Partners: Konzentration 48 Mio/ml, Motilität a+b 52%, "
            "Morphologie 6% Normalformen. Werte innerhalb der WHO-Referenzbereiche.",
            "Unauffälliges Spermiogramm. Weiteres Vorgehen gemäss Kinderwunsch-Sprechstunde.",
        ),
        {"ist_befund": True, "nachname": "Partnerin", "vorname": "Mia",
         "geburtsdatum": "25.08.1990", "berichtsdatum": None,
         "titel_erwartet": "Ejakulatanalyse Partner", "titel_ist_aus_liste": True,
         "gate_pass": True},
    ),
    "umlaut_name": (
        _befund_text(
            "Stadtspital Zürich Triemli", "Frauenklinik",
            "Müller-Lüthi, Zoë", "09.10.1987", "30.06.2026",
            "Operationsbericht — Laparoskopie",
            "Laparoskopische Ovarialzystektomie links am 29.06.2026. Histologie: "
            "benignes seröses Zystadenom. Komplikationsloser Verlauf.",
            "Fadenentfernung nicht nötig (resorbierbar). Kontrolle in der Praxis in "
            "2 Wochen.",
        ),
        {"ist_befund": True, "nachname": "Müller-Lüthi", "vorname": "Zoë",
         "geburtsdatum": "09.10.1987", "berichtsdatum": "30.06.2026",
         "titel_erwartet": "Operationsbericht Spital", "titel_ist_aus_liste": True,
         "gate_pass": True},
    ),
    "rhd_genotyp": (
        _befund_text(
            "Blutspende Zürich", "Molekulare Diagnostik",
            "Negativ, Rhea", "17.06.1993", "01.07.2026",
            "Fetale RHD-Genotypisierung aus mütterlichem Plasma",
            "RhD-negative Schwangere, 25 0/7 SSW. Fetales RHD-Gen: NACHGEWIESEN. "
            "Das Kind ist mit hoher Wahrscheinlichkeit RhD-positiv.",
            "Anti-D-Prophylaxe in der 28. SSW indiziert.",
        ),
        {"ist_befund": True, "nachname": "Negativ", "vorname": "Rhea",
         "geburtsdatum": "17.06.1993", "berichtsdatum": "01.07.2026",
         "titel_erwartet": "Fetale RHD Genotypisierung (Rhesusfaktor)",
         "titel_ist_aus_liste": True, "gate_pass": True},
    ),
}


def _text_pdf(text: str) -> bytes:
    import fitz
    doc = fitz.open()
    page = doc.new_page()  # A4
    page.insert_textbox(fitz.Rect(50, 50, 545, 800), text, fontsize=10, fontname="helv")
    data = doc.tobytes(deflate=True)
    doc.close()
    return data


def _scanned_pdf(text: str) -> bytes:
    """Text PDF -> PNG -> new PDF containing only the image (no text layer)."""
    import fitz
    src = fitz.open(stream=_text_pdf(text), filetype="pdf")
    pix = src[0].get_pixmap(dpi=150)
    png = pix.tobytes("png")
    src.close()
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(fitz.Rect(0, 0, 595, 842), stream=png)
    data = doc.tobytes(deflate=True)
    doc.close()
    return data


def _eml(from_, subject, attachments: list[tuple[str, bytes, str]], msg_id: str) -> bytes:
    m = EmailMessage()
    m["From"] = from_
    m["To"] = "praxis-ulrich@hin.ch"
    m["Subject"] = subject
    m["Message-ID"] = msg_id
    m["Date"] = "Thu, 02 Jul 2026 09:32:00 +0200"
    m.set_content("Guten Tag\n\nAnbei der Bericht.\n\nFreundliche Grüsse")
    for fname, blob, subtype in attachments:
        maintype, _, sub = subtype.partition("/")
        m.add_attachment(blob, maintype=maintype, subtype=sub, filename=fname)
    return bytes(m)


def build(dest: Path = TESTDATA) -> dict:
    (dest / "pdfs").mkdir(parents=True, exist_ok=True)
    (dest / "expected").mkdir(parents=True, exist_ok=True)
    (dest / "eml").mkdir(parents=True, exist_ok=True)

    pdf_bytes: dict[str, bytes] = {}
    for case_id, (text, golden) in CASES.items():
        blob = _scanned_pdf(text) if golden.get("scanned") else _text_pdf(text)
        pdf_bytes[case_id] = blob
        (dest / "pdfs" / f"{case_id}.pdf").write_bytes(blob)
        (dest / "expected" / f"{case_id}.json").write_text(
            json.dumps(golden, ensure_ascii=False, indent=2), encoding="utf-8")

    emls = {
        "single_befund.eml": _eml(
            "befunde@usz.ch", "Austrittsbericht Ihrer Patientin",
            [("austritt.pdf", pdf_bytes["austritt_usz"], "application/pdf")],
            "<eml-single@test>"),
        "multi_pdf.eml": _eml(
            "labor@synlab.ch", "2 Befunde",
            [("urinkultur.pdf", pdf_bytes["urinkultur"], "application/pdf"),
             ("blutbild.pdf", pdf_bytes["labor_blutbild"], "application/pdf")],
            "<eml-multi@test>"),
        "no_pdf.eml": _eml(
            "sekretariat@spital-limmattal.ch", "Terminanfrage", [], "<eml-nopdf@test>"),
        "junk_pdf.eml": _eml(
            "billing@microsoft.com", "Ihre Microsoft-Rechnung",
            [("invoice.pdf", pdf_bytes["microsoft_junk"], "application/pdf")],
            "<eml-junk@test>"),
        "mixed_attachments.eml": _eml(
            "befunde@triemli.ch", "Mammasonografie",
            [("logo.png", b"\x89PNG\r\n\x1a\nfake", "image/png"),
             ("mamma_us.pdf", pdf_bytes["mamma_us"], "application/pdf")],
            "<eml-mixed@test>"),
    }
    for name, blob in emls.items():
        (dest / "eml" / name).write_bytes(blob)

    return {"pdfs": len(pdf_bytes), "emls": len(emls)}


if __name__ == "__main__":
    n = build()
    print(f"Corpus generiert: {n['pdfs']} PDFs, {n['emls']} EMLs -> {TESTDATA}")
    sys.exit(0)
