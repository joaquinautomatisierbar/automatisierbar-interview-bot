# Testing — AUT-46 — Marketing image pipeline (hi-res renders, workflow diagrams, no-logo default)

**Branch:** `build/AUT-46-marketing-image-pipeline`
**Repo:** `joaquinautomatisierbar/automatisierbar-interview-bot`
**Operator:** Joaquin — complete Prerequisites 1–2 before running Smoke Test 3.

---

## Was du brauchst

- Repo lokal auf Branch `build/AUT-46-marketing-image-pipeline`:
  ```bash
  git fetch && git checkout build/AUT-46-marketing-image-pipeline
  ```
- Python 3.11+ im Repo-venv:
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```
  `cairosvg` und `Pillow` müssen installiert sein (in requirements.txt enthalten).
- `NOTION_API_KEY` und Google Drive OAuth in `.env` (für Smoke Test 3).

---

## Operator Prerequisites (vor Smoke Test 3 erledigen)

### Prerequisite 1 — Notion DB: `Image Files`-Property hinzufügen

1. Öffne Notion-Datenbank **Post Variants** (ID `013ef8bc-4837-44c3-bfa2-b8b15792fb80`).
2. Klick oben rechts auf **+** → **Files & media** → Name: `Image Files`.
3. Bestätigen. Bestehende Zeilen bleiben leer — kein Datenverlust.

### Prerequisite 2 — Drive-Ordner anlegen

1. Öffne Google Drive mit dem PR Director Service Account.
2. Erstelle Ordner: `Automatisierbar/LinkedIn-Post-Images/`.
3. Sharing: PR Director OAuth-Account braucht Schreibzugriff.

---

## Smoke Test 1a — Hero-Card Renderer (2 Min)

```bash
echo '{"headline":"Mandanten schneller onboarden","palette":"green-on-deep","aspect":"square","branding":"none"}' \
  | python3 tools/render_linkedin_image.py --output /tmp/hero_square.png
```

**Pass-Kriterien:**
- Exit-Code 0, keine Fehlermeldung.
- `/tmp/hero_square.png` existiert.
- Bild-Dimensionen: exakt 1200 × 1200 px.
  ```bash
  python3 -c "from PIL import Image; img=Image.open('/tmp/hero_square.png'); print(img.size)"
  # erwartet: (1200, 1200)
  ```
- **Kein Automatisierbar-Logo, kein Wortmarke** sichtbar (branding=none default).

### Smoke Test 1b — Portrait-Format

```bash
echo '{"headline":"Jede Woche 3 Stunden gespart","palette":"deep-on-light","aspect":"portrait","branding":"none"}' \
  | python3 tools/render_linkedin_image.py --output /tmp/hero_portrait.png
python3 -c "from PIL import Image; img=Image.open('/tmp/hero_portrait.png'); print(img.size)"
# erwartet: (1080, 1350)
```

### Smoke Test 1c — Landscape-Format

```bash
echo '{"headline":"Automatisierung ohne IT","palette":"light-on-green","aspect":"landscape","branding":"none"}' \
  | python3 tools/render_linkedin_image.py --output /tmp/hero_landscape.png
python3 -c "from PIL import Image; img=Image.open('/tmp/hero_landscape.png'); print(img.size)"
# erwartet: (1200, 627)
```

### Smoke Test 1d — Fehlerfall (ungültiges JSON)

```bash
echo 'kein json' | python3 tools/render_linkedin_image.py --output /tmp/error_test.png
echo "Exit-Code: $?"
# erwartet: Exit-Code 2, Fehlermeldung auf stderr, keine PNG-Datei geschrieben
```

---

## Smoke Test 2 — Workflow-Diagram Renderer (3 Min)

```bash
cat > /tmp/workflow_spec.json << 'EOF'
{
  "title": "Mandantenfall-Abschluss Pipeline",
  "subtitle": "Outlook → Backoffice → Abschluss",
  "phases": [
    {
      "label": "Eingang",
      "color": "blue",
      "steps": [
        {"label": "E-Mail empfangen", "kind": "trigger", "icon": "✉", "endpoint": "outlook.office365.com"},
        {"label": "Mandantendaten extrahieren", "kind": "action", "icon": "⚙"}
      ]
    },
    {
      "label": "Validierung",
      "color": "yellow",
      "steps": [
        {"label": "Aktenzeichen prüfen", "kind": "decision", "icon": "◆"},
        {"label": "Pflichtfelder validieren", "kind": "decision", "icon": "◆"}
      ]
    },
    {
      "label": "Backoffice",
      "color": "red",
      "steps": [
        {"label": "Bexio-Eintrag anlegen", "kind": "action", "icon": "⚙", "endpoint": "api.bexio.com"},
        {"label": "Dokument ablegen", "kind": "action", "icon": "⚙"},
        {"label": "Bestätigung senden", "kind": "action", "icon": "⚙"}
      ]
    }
  ],
  "error_path": {
    "label": "Fehlerbehandlung",
    "steps": [
      {"label": "Slack-Alert senden", "kind": "action", "icon": "⚙"},
      {"label": "Manuelle Prüfung", "kind": "manual", "icon": "👤"}
    ]
  }
}
EOF
python3 tools/render_n8n_workflow_diagram.py --input /tmp/workflow_spec.json --output-dir /tmp/diagrams/
```

**Pass-Kriterien:**
- Exit-Code 0.
- `/tmp/diagrams/diagram_landscape.png` existiert → Dimensionen 2400 × 1200 px.
- `/tmp/diagrams/diagram_square.png` existiert → Dimensionen 1200 × 1200 px.
  ```bash
  python3 -c "
  from PIL import Image
  l=Image.open('/tmp/diagrams/diagram_landscape.png'); print('landscape:', l.size)
  s=Image.open('/tmp/diagrams/diagram_square.png'); print('square:', s.size)
  "
  # erwartet: landscape: (2400, 1200)  square: (1200, 1200)
  ```
- Öffne die PNGs in Preview: Titelleiste dunkelgrün, Phasenblöcke farblich unterschiedlich, Error-Pfad sichtbar.

---

## Smoke Test 3 — Integration (Bike-Method Phase 1, 10 Min)

**Voraussetzungen:** Prerequisite 1 + 2 erledigt, `.env` mit NOTION_API_KEY + Drive OAuth.

```bash
python tools/linkedin_brief.py --week-of 2026-05-22 --person Joaquin
```

Warte, bis der Marketing PR Dispatcher → PR Director-Run abgeschlossen ist (Paperclip Dashboard / Telegram-Benachrichtigung).

**Pass-Kriterien:**
1. In Notion **Post Variants DB** erscheinen 5–7 neue Zeilen für KW 22/2026.
2. Jede Zeile hat **2–4 Dateien** in der `Image Files`-Property (direkte Notion-Anhänge, bei Grösse >5 MB als Drive-Link).
3. Zeilen zu Workflow-Themen haben mind. 1 Diagramm (render_n8n_workflow_diagram).
4. **Kein Automatisierbar-Wortmarke** auf einem der Bilder (da `image_branding` im Brief nicht gesetzt = default `none`).
5. Alle Bilder: kürzeste Seite ≥ 1080 px (Landscape 627 px ist per LinkedIn-Spec für das Format korrekt).

**Fail → Defect Issue anlegen** mit konkreten Abweichungen. Phase 1 gilt als bestanden, wenn alle 5 Kriterien erfüllt sind.

---

## Ergebnis festhalten

Nach bestandenem Smoke Test 3: Merge-Anfrage an Joaquin (PR auf `main` aus `build/AUT-46-marketing-image-pipeline`).
2 weitere Friday-Runs abwarten → dann Phase 2-Promotion.
