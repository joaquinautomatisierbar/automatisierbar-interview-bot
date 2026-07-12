"""Docs manifest + dashboard data for the vRv hub (/vrv).

The hub serves the tender documents (tender-vrv/) read-only to the logged-in
team. Serving is manifest-exact: a request path is looked up as a literal
string in the manifest, no filesystem path math ever touches user input, so
traversal is structurally impossible. The dashboard parses TASKS.md live on
every request (11KB, read-only, safe under 2 gunicorn workers).

VRV_DOCS_DIR is read at call time (store.py pattern) so tests can repoint it;
default resolves to <repo>/tender-vrv, which on the VPS is
/srv/cockpit/app/tender-vrv (content ships via rsync, never git).
"""
import os
import re
from copy import deepcopy
from pathlib import Path

COUNTDOWN_TARGET = "2026-08-05"

MIME_BY_KIND = {
    "md": "text/markdown",
    "pdf": "application/pdf",
    "html": "text/html",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
ATTACHMENT_KINDS = {"pptx"}  # pdf/html/md render inline in the browser


def _i(path, title, desc, kind="md"):
    return {"path": path, "title": title, "desc": desc, "kind": kind}


DOCS_MANIFEST = [
    {"id": "lernen", "title": "Lernen", "items": [
        _i("upskilling/modul-4-primer.md", "Modul 4 · Immobilien & Order2Cash", "Session 1 · Nico erklärt: die Branche, der Prozess, pebe"),
        _i("upskilling/modul-4-quiz.md", "Modul 4 · Quiz", "Selbsttest nach Session 1"),
        _i("upskilling/modul-1-primer.md", "Modul 1 · Microsoft 365 & Power Platform", "Session 2 · Tej erklärt: die Variante Microsoft fair einordnen"),
        _i("upskilling/modul-1-quiz.md", "Modul 1 · Quiz", "Selbsttest nach Session 2"),
        _i("upskilling/modul-2-primer.md", "Modul 2 · Cybersecurity & IT-Infrastruktur", "Session 3 · Joaquin erklärt: Endpoint, Firewall, VPN, Backup"),
        _i("upskilling/modul-2-quiz.md", "Modul 2 · Quiz", "Selbsttest nach Session 3"),
        _i("upskilling/modul-2-deck.html", "Modul 2 · Präsentation (60 min)", "Session 3 · Foliensatz mit Referentennotizen (Taste N)", kind="html"),
        _i("upskilling/modul-2-handout.md", "Modul 2 · Handout & Hausaufgabe", "Spickzettel + Sicherheits-Audit · Abgabe Mi 15.7., 18:00"),
        _i("upskilling/modul-2-handout.pdf", "Modul 2 · Handout (PDF)", "Druckfassung zum Mitnehmen", kind="pdf"),
        _i("upskilling/modul-3-primer.md", "Modul 3 · Schweizer Compliance", "Session 4 · Patrik erklärt: nDSG, BVG-Aufbewahrung, Aufsicht"),
        _i("upskilling/modul-3-quiz.md", "Modul 3 · Quiz", "Selbsttest nach Session 4"),
        _i("upskilling/modul-6-primer.md", "Modul 6 · Integrations-Architektur", "Session 5 · Tej erklärt: die pebe-Brücke, Graph API, Migration"),
        _i("upskilling/modul-6-quiz.md", "Modul 6 · Quiz", "Selbsttest nach Session 5"),
        _i("upskilling/modul-5-primer.md", "Modul 5 · Projektleitung & Offerten", "Session 6 · Joaquin erklärt: Phasenmodell, RACI, Change Requests"),
        _i("upskilling/modul-5-quiz.md", "Modul 5 · Quiz", "Selbsttest nach Session 6"),
        _i("upskilling/modul-5-deck.html", "Modul 5 · Präsentation (60 min)", "Session 6 · Foliensatz mit Klick-Builds + Referentennotizen (Taste N)", kind="html"),
        _i("upskilling/modul-5-handout.md", "Modul 5 · Handout & Hausaufgabe", "Spickzettel + Statusreport-Übung · Abgabe So 2.8., 18:00"),
        _i("upskilling/modul-5-handout.pdf", "Modul 5 · Handout (PDF)", "Druckfassung mit ausfüllbaren Vorlagen", kind="pdf"),
        _i("upskilling/fragen-bank-schmid.md", "Fragen-Bank: Was Schmid fragen wird", "50 Prüfer-Fragen mit ehrlichen Musterantworten, Drill in S7"),
        _i("upskilling/guide-praesentation.md", "Session-Werkstatt · Präsentations-Guide", "So baust du dein Session-Deck mit Claude Code, inkl. Upload-Anleitung"),
        _i("upskilling/guide-handout.md", "Session-Werkstatt · Handout-Guide", "Einheitliche Handout-Struktur + Copy-paste-Vorlage für dein Modul"),
    ]},
    {"id": "termin", "title": "Termin 5.8.", "items": [
        _i("meeting/ablauf-drehbuch.md", "Ablauf-Drehbuch 5.8.", "Minutenplan 10/15/60/10 mit Rollen, Notfällen und Abschluss"),
        _i("meeting/mock-meeting-s7.md", "Mock-Meeting S7", "Probe-Rollenspiel: Claude spielt die Kundenseite, mit Bewertungsbogen"),
        _i("templates/vorab-mail-schmid.md", "Vorab-Mail an Rolf Schmid", "Review-Fassung, Versand bis 22.7. nach Freigabe"),
    ]},
    {"id": "praesentation", "title": "Präsentation", "items": [
        _i("deck/deck.html", "Präsentations-Deck (15 Folien)", "Im Browser öffnen · Taste N = Referentennotizen", kind="html"),
        _i("entscheidungsgrundlage-team-2026-07.pptx", "Team-Entscheidungsgrundlage (PPTX)", "Interne Folien von Anfang Juli, Scope-Modelle A/B/C", kind="pptx"),
    ]},
    {"id": "offerte", "title": "Offerte", "items": [
        _i("offer/offerten-skelett.md", "Offerten-Skelett", "Kapitelstruktur exakt nach den Kundenfragen, mit Abdeckungs-Matrix"),
        _i("offer/architektur-varianten.md", "Architektur-Varianten A/B/C", "Microsoft-first, Custom, Hybrid: Bausteine, Grenzen, Kostenbild"),
        _i("offer/sla-baukasten.md", "SLA-Baukasten", "Support-Stufen Bronze/Silber/Gold mit Reaktionszeiten"),
        _i("offer/hosting-kostenblatt.md", "Hosting-Kostenblatt", "Schweizer Anbieter im Vergleich, Entscheid-Checkliste für Joaquin"),
        _i("offer/referenzblaetter.md", "Referenzblätter", "4 Ein-Seiter über unsere Projekte, ehrlich gelabelt"),
        _i("offer/security-antwortpaket.md", "Security-Antwortpaket", "Antworten auf alle Sicherheitsfragen der Ausschreibung (Entwurf)"),
    ]},
    {"id": "vertraege", "title": "Verträge & Vorlagen", "items": [
        _i("templates/projekthandbuch-vorlagen.md", "Projekthandbuch-Vorlagen", "Statusreport, Change Request, RACI, Abnahmeprotokoll und mehr"),
        _i("templates/avv-template.md", "AVV-Template", "Auftragsbearbeitungsvertrag nach Art. 9 DSG (Entwurf)"),
        _i("templates/datenschutz-statement.md", "Datenschutz-Statement", "Ein-Seiter für die Offerte, Kapitel 8.6 (Entwurf)"),
        _i("templates/referenz-freigabe.md", "Referenz-Freigabe (Vorlage)", "Mustertext, um Kunden um Erlaubnis zu fragen"),
        _i("templates/versicherungsanfrage.md", "Versicherungsanfrage (Vorlage)", "Mustertext für Berufshaftpflicht + Cyber, Patrik verschickt"),
    ]},
    {"id": "wissen", "title": "Wissen (Recherche)", "items": [
        _i("research/dossier-a-pebe-integration.md", "Dossier A · pebeFinance", "Wie man pebe wirklich anbinden kann (kein API, CSV, Zahlungsbus)"),
        _i("research/dossier-b-software-landschaft.md", "Dossier B · Software-Landschaft CH", "Konkurrenz und Alternativen, gefährlichster Pitch: Abacus"),
        _i("research/dossier-c-variante-microsoft.md", "Dossier C · Variante Microsoft", "Was Planner & Co. können und wo die Grenzen liegen, mit Preisen"),
        _i("research/dossier-d-security-compliance.md", "Dossier D · Security & Compliance", "nDSG, BVG-Archivierung, Aufsicht, Hosting, fertige Antwort-Bausteine"),
        _i("research/dossier-e-machbarkeit.md", "Dossier E · Teilbereichs-Machbarkeit", "Grundlage für den Scope-Entscheid am 21.7."),
        _i("ausschreibung-anfrage-2026-07-02.md", "Die Ausschreibung (Transkript)", "Durchsuchbare Textfassung der Original-Anfrage"),
        _i("ausschreibung-anfrage-2026-07-02.pdf", "Die Ausschreibung (Original-PDF)", "Original-Anfrage der vR verwaltungen ag vom 2.7.2026", kind="pdf"),
    ]},
    {"id": "plan", "title": "Plan & Steuerung", "items": [
        _i("naechste-schritte.md", "Nächste Schritte pro Person", "Wer muss was bis wann tun (wird laufend nachgeführt)"),
        _i("TASKS.md", "Aufgaben-Board", "Alle Aufgaben mit Owner, Frist und Stand, nach Arbeitspaketen"),
        _i("README.md", "Projekt-Übersicht", "Einstiegsseite mit Status-Schnellblick und Datei-Inventar"),
        _i("MASTERPLAN.md", "Masterplan", "Der freigegebene Gesamtplan vom 10.7. (eingefroren)"),
    ]},
]

_BY_PATH = {item["path"]: item for section in DOCS_MANIFEST for item in section["items"]}


def docs_dir():
    configured = (os.environ.get("VRV_DOCS_DIR") or "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "tender-vrv"


def manifest():
    base = docs_dir()
    sections = deepcopy(DOCS_MANIFEST)
    for section in sections:
        for item in section["items"]:
            item["exists"] = (base / item["path"]).is_file()
    # Self-service materials (tools/vrv/materials.py) merge into "lernen" as
    # virtual entries so the hub groups/labels them like committed modules.
    # Static wins: paths already in _BY_PATH are never shadowed. Degrades to
    # the static manifest if the materials layer is broken.
    try:
        from vrv import materials as _materials
        extra = [it for it in _materials.manifest_items() if it["path"] not in _BY_PATH]
        for item in extra:
            entry = _materials.by_virtual_path(item["path"])
            item["exists"] = bool(entry) and os.path.isfile(_materials.abs_path_for(entry))
        for section in sections:
            if section["id"] == "lernen":
                section["items"].extend(extra)
                break
    except Exception:  # noqa: BLE001 — manifest must degrade, not 500
        pass
    return sections


def resolve(relpath):
    """(absolute path, manifest item) — or None unless relpath is EXACTLY a
    manifest key or a registered material's virtual path. Both lookups compare
    user input against stored strings before any filesystem call, so encoded
    traversal (../, %2e%2e) is just a string that isn't in either index."""
    item = _BY_PATH.get(relpath)
    if item is not None:
        return docs_dir() / relpath, item
    try:
        from vrv import materials as _materials
        entry = _materials.by_virtual_path(relpath)
    except Exception:  # noqa: BLE001 — a broken materials layer must not 500 docs
        entry = None
    if entry is None:
        return None
    from pathlib import Path as _Path
    item = {
        "path": relpath,
        "title": entry.get("orig_name", relpath),
        "desc": "",
        "kind": _materials.ROLES[entry["role"]]["kind"],
        "material": True,
    }
    return _Path(_materials.abs_path_for(entry)), item


def read_doc_text(relpath):
    resolved = resolve(relpath)
    if resolved is None:
        return None
    path, _item = resolved
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# TASKS.md parsing (dashboard)
# ---------------------------------------------------------------------------

_LANE_RE = re.compile(r"^##\s+Lane\s+(WS\d+):\s*(.+?)\s*$")
_TASK_RE = re.compile(r"^- \[([ x~])\]\s?(.*)$")
_FENCE_RE = re.compile(r"^\s*```")
_MILESTONE_H2_RE = re.compile(r"^##\s+Meilensteine\b")
_H2_RE = re.compile(r"^##\s+")
_STAND_RE = re.compile(r"Stand:\s*([0-9][0-9.]*[0-9])")

_STATE_BY_MARK = {"x": "done", "~": "doing", " ": "open"}


def parse_tasks(text):
    """Tolerant TASKS.md parser. Fenced code is skipped first; tasks count only
    at column 0 (the legend's literal [x] sits in a blockquote and never
    matches); unknown H2 sections are ignored so the board format can evolve."""
    lanes = []
    milestones = []
    current_lane = None
    in_milestones = False
    in_fence = False

    for line in text.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        lane_match = _LANE_RE.match(line)
        if lane_match:
            current_lane = {
                "id": lane_match.group(1),
                "title": lane_match.group(2),
                "items": [],
            }
            lanes.append(current_lane)
            in_milestones = False
            continue

        if _MILESTONE_H2_RE.match(line):
            in_milestones = True
            current_lane = None
            continue
        if _H2_RE.match(line):
            in_milestones = False
            current_lane = None
            continue

        if in_milestones and line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            if all(re.fullmatch(r"[\s:-]*", c) for c in cells):
                continue  # separator row
            if cells[0] == "Datum":
                continue  # header row
            emph = "**" in cells[0] or "**" in cells[1]
            milestones.append({
                "date": cells[0].replace("**", "").strip(),
                "label": cells[1].replace("**", "").strip(),
                "emph": emph,
            })
            continue

        task_match = _TASK_RE.match(line)
        if task_match and current_lane is not None:
            current_lane["items"].append({
                "state": _STATE_BY_MARK[task_match.group(1)],
                "text": task_match.group(2).strip(),
            })

    for lane in lanes:
        states = [item["state"] for item in lane["items"]]
        lane["done"] = states.count("done")
        lane["doing"] = states.count("doing")
        lane["open"] = states.count("open")
        lane["total"] = len(states)

    stand_match = _STAND_RE.search(text)
    return {
        "lanes": lanes,
        "milestones": milestones,
        "stand": stand_match.group(1) if stand_match else None,
    }


def dashboard_payload():
    """Everything the hub start view needs. Must never raise: a broken or
    missing file degrades to None + error text, the hub shows a friendly note."""
    tasks = None
    tasks_error = None
    try:
        text = read_doc_text("TASKS.md")
        if text is None:
            tasks_error = "TASKS.md nicht gefunden"
        else:
            tasks = parse_tasks(text)
    except Exception as exc:  # noqa: BLE001 — dashboard must degrade, not 500
        tasks_error = str(exc)[:300]

    try:
        naechste = read_doc_text("naechste-schritte.md")
    except Exception:  # noqa: BLE001
        naechste = None

    return {
        "ok": True,
        "countdown_target": COUNTDOWN_TARGET,
        "tasks": tasks,
        "tasks_error": tasks_error,
        "naechste_schritte_md": naechste,
    }
