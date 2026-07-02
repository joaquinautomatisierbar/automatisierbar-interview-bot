"""extractor.py — LLM extraction of Befund fields from a PDF (text or scanned).

extract_befund(...) NEVER raises (spesen/ocr.py pattern): every failure mode —
no API key, provider error, unparseable JSON — returns ok=False with an error
string, which the pipeline turns into "kein Fähnchen, Mail bleibt liegen".

Every field the model returns is sanitised deterministically before anything
downstream sees it: dates must match TT.MM.JJJJ, strings are trimmed and
capped, ist_befund/confidence are coerced. The title decision (list match vs
free-form) is NOT trusted from the model — titles.py re-validates against
config.TITEL_VORLAGEN with an exact match.

The gate the pipeline enforces: ist_befund AND patientinNachname AND
geburtsdatum. The model is instructed to leave fields null rather than guess —
a hallucinated patient name is the one clinically unacceptable failure.
"""

from __future__ import annotations

import json
import re

try:
    from . import config, providers, secrets_store
except ImportError:  # direct-script / test runs
    import config  # type: ignore
    import providers  # type: ignore
    import secrets_store  # type: ignore

_DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

_FIELDS_EMPTY = {
    "ist_befund": False,
    "patientinVorname": None,
    "patientinNachname": None,
    "geburtsdatum": None,
    "berichtsdatum": None,
    "absenderInstitution": None,
    "diagnose_prozedere": None,
    "empfehlung": None,
    "titel_vorschlag": None,
    "titel_ist_aus_liste": False,
    "zusammenfassung_4z": None,
    "confidence": 0.0,
}


def _system_prompt() -> str:
    titel_liste = "\n".join(f"- {t}" for t in config.TITEL_VORLAGEN)
    return (
        "Du bist ein präziser medizinischer Dokumenten-Assistent für eine "
        "Gynäkologie-Praxis in Zürich. Du liest Befundberichte (PDF-Inhalt als Text "
        "oder Bild) und extrahierst Felder als JSON.\n"
        "WICHTIGSTE REGEL: Erfinde NIEMALS Patientendaten. Wenn Name oder "
        "Geburtsdatum nicht eindeutig lesbar sind, setze das Feld auf null und senke "
        "die confidence. Ein falsch zugeordneter Befund ist der schlimmste Fehler.\n"
        "Antworte AUSSCHLIESSLICH mit gültigem JSON, ohne Erklärung, ohne Markdown.\n\n"
        "Felder:\n"
        '- ist_befund: bool — true NUR wenn das Dokument ein medizinischer Befund-/'
        "Arztbericht zu einer Patientin ist (Labor, Ultraschall, Austrittsbericht, "
        "Operationsbericht usw.). Rechnungen, Werbung, System-Mails, Lizenzdokumente: false.\n"
        '- patientinVorname: string|null\n'
        '- patientinNachname: string|null\n'
        '- geburtsdatum: "TT.MM.JJJJ"|null — Geburtsdatum der Patientin.\n'
        '- berichtsdatum: "TT.MM.JJJJ"|null — Datum des Berichts (nicht heute, nicht '
        "das Geburtsdatum).\n"
        '- absenderInstitution: string|null — z.B. "Universitätsspital Zürich".\n'
        '- diagnose_prozedere: string|null — 1–3 Sätze Deutsch.\n'
        '- empfehlung: string|null — 1–2 Sätze Deutsch.\n'
        '- titel_vorschlag: string — wähle den am besten passenden Titel EXAKT aus der '
        "Vorlagenliste unten; wenn keiner inhaltlich passt, formuliere einen kurzen "
        f"freien deutschen Titel (max. {config.FREITITEL_MAX_LEN} Zeichen, beschreibt "
        "Berichtstyp, ggf. Institution; KEIN Patientenname, KEIN Datum im Titel).\n"
        "- titel_ist_aus_liste: bool — true nur wenn titel_vorschlag wörtlich aus der Liste ist.\n"
        '- zusammenfassung_4z: string — exakt 4 Zeilen, getrennt mit \\n: '
        "Zeile 1 Patientendaten (Name, geb. TT.MM.JJJJ), Zeile 2 Befund, "
        "Zeile 3 Diagnose/Prozedere, Zeile 4 Empfehlung.\n"
        "- confidence: 0.0-1.0.\n\n"
        f"Vorlagenliste Dokumenttitel:\n{titel_liste}"
    )


def _parse_json(text: str) -> dict:
    """Tolerant JSON parse: strips ``` fences and leading/trailing prose."""
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("kein JSON-Objekt in der Antwort")
    return json.loads(t[start:end + 1])


def _s(v, cap: int) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s[:cap] if s else None


def _date(v) -> str | None:
    if isinstance(v, str) and _DATE_RE.match(v.strip()):
        return v.strip()
    return None


def _sanitise(d: dict) -> dict:
    out = dict(_FIELDS_EMPTY)
    out["ist_befund"] = bool(d.get("ist_befund"))
    out["patientinVorname"] = _s(d.get("patientinVorname"), 80)
    out["patientinNachname"] = _s(d.get("patientinNachname"), 80)
    out["geburtsdatum"] = _date(d.get("geburtsdatum"))
    out["berichtsdatum"] = _date(d.get("berichtsdatum"))
    out["absenderInstitution"] = _s(d.get("absenderInstitution"), 120)
    out["diagnose_prozedere"] = _s(d.get("diagnose_prozedere"), 600)
    out["empfehlung"] = _s(d.get("empfehlung"), 400)
    out["titel_vorschlag"] = _s(d.get("titel_vorschlag"), 120)
    out["titel_ist_aus_liste"] = bool(d.get("titel_ist_aus_liste"))
    z = _s(d.get("zusammenfassung_4z"), 1200)
    out["zusammenfassung_4z"] = z
    try:
        out["confidence"] = max(0.0, min(1.0, float(d.get("confidence", 0.0))))
    except (TypeError, ValueError):
        out["confidence"] = 0.0
    return out


def extract_befund(*, text: str | None = None, images: list[bytes] | None = None,
                   cfg: dict | None = None) -> dict:
    """Return {ok, error, **fields}. Never raises. Exactly one LLM call."""
    base = {"ok": False, "error": "", **_FIELDS_EMPTY}
    cfg = cfg or config.load()

    if not text and not images:
        return {**base, "error": "kein PDF-Inhalt (weder Text noch Bilder)"}

    api_key = secrets_store.get_secret("llm_api_key")
    if not api_key and (cfg.get("llm_provider") or "anthropic") != "local":
        return {**base, "error": "LLM nicht konfiguriert (kein API-Key)"}

    blocks: list[dict] = []
    if images:
        for png in images:
            blocks.append({"type": "image_png", "data": png})
        blocks.append({"type": "text", "text": "Analysiere diesen eingescannten Befundbericht (Seiten als Bilder)."})
    else:
        blocks.append({"type": "text", "text": f"Analysiere diesen Befundbericht:\n\n{text}"})

    try:
        raw = providers.run_extraction(_system_prompt(), blocks, cfg, api_key or "")
        clean = _sanitise(_parse_json(raw))
        return {"ok": True, "error": "", **clean}
    except NotImplementedError as e:
        return {**base, "error": str(e)}
    except Exception as e:
        print(f"[befund-extractor] error={e!r}", flush=True)
        return {**base, "error": f"Extraktion fehlgeschlagen: {type(e).__name__}"}
