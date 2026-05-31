---
name: generate-automation-test-data
description: >
  Given any automation in Automatisierbar's ecosystem (CLIENT or INTERNAL build branch, internal Python tool, n8n workflow id), read its source to infer the actual input shape and generate realistic fixture data matching that shape. Lands artifacts in GitHub (paperclipai-builds extra-testing/ folder or a fresh test-data/ branch).
---

# Generate Automation Test Data

This is the heart of the Test Data Generator agent. Use it after you've located the automation's source — it tells you how to infer the input shape and produce matching fixtures.

## Step 1 — Inference cookbook (one section per automation type)

### n8n workflows (cloud-hosted)

```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://oojoaquin.app.n8n.cloud/api/v1/workflows/<id> > workflow.json
```

Then inspect:

1. **Trigger node:** find the first node with `type` matching `webhook`, `formTrigger`, `cron`, `scheduleTrigger`, `manualTrigger`, `emailTrigger`. The trigger type determines input shape:
   - `n8n-nodes-base.webhook` → `parameters.httpMethod` + `parameters.path` + `parameters.options.responseMode`. The webhook expects a JSON / form body — fields are revealed by downstream `$json.*` references.
   - `n8n-nodes-base.formTrigger` → `parameters.formFields.values` is a list of `{fieldLabel, fieldType, requiredField}`. That IS the input shape — dump it.
   - `cron` / `scheduleTrigger` → no external input. The "input" is what the next data-fetching node reads (Notion DB row, Sheets row, Gmail message). Inspect that node's resource + filter expressions.
   - `manualTrigger` → operator-supplied at runtime, often via "Pin Data". Check `pinData` on the workflow JSON if present.
2. **Scan the next ~5 nodes** for `={{ $json.* }}`, `={{ $node["X"].json.* }}`, and `={{ $binary.* }}` expressions. Each unique field encountered is a field the workflow consumes. Enumerate them.
3. **Output shape** of the workflow is also useful (so the operator can verify): scan the LAST nodes (HTTP Request, Notion, Telegram, Email) for `={{ $json.* }}` references in body templates.

### Python Flask / FastAPI routes

```python
# grep for route decorators
grep -nE "@app\.route|@bp\.route|@router\.(get|post|put|patch|delete)" path/to/api.py
```

For each route handler, read its body to find:

- `request.json` access → JSON body keys → those are the input fields.
- `request.form` → form fields.
- `request.files["X"]` → file uploads. Read further for `.mimetype` / `.filename` checks → allowed file types.
- `request.args["X"]` → query-string params.
- `request.headers["X"]` → required headers (auth tokens, etc.).

Tip: `request.json.get("foo", default)` reveals optional fields + defaults.

### Python CLI scripts / tools

```python
# look for argparse first
grep -nE "argparse|click\.|sys\.argv|fire\.Fire" path/to/script.py
```

If `argparse.ArgumentParser`:

- Each `parser.add_argument("--name", ...)` is an input. Read `type=`, `required=`, `choices=`, `default=`.

If no argparse:

- Scan top-level `open(...)`, `pd.read_csv(...)`, `json.load(...)`, env-var accesses (`os.environ["X"]`, `os.getenv("X")`).

### Build-artifact bundles (CLIENT/INTERNAL builds)

When the operator points at `AUT-XXX`, the cloned branch usually contains:

- `BRIEF.md` or `RELEASE_NOTES.md` → describes intent + sometimes input/output explicitly.
- `PRESENTATION.md` → customer-facing description (often plain-language input/output examples).
- `TESTING.md` → step-by-step verification, lists the inputs + expected outputs.
- The actual workflow / code file (`*.workflow.code.js`, `*.py`).

Read the docs first — they usually save you 80% of the inference work. Cross-check against the actual workflow / code (docs sometimes drift).

## Step 2 — Persona library

Pick ONE persona per scenario, keep it consistent across every file you produce. ICP per `feedback_lead_icp_backoffice.md` — backoffice-heavy Swiss SMEs only.

| Persona | Sample processes | Sample synthetic name |
|---|---|---|
| Treuhand | Monatsabschluss, MWST-Abrechnung, Mahnungen, Belegfreigabe, Lohnabrechnung | Muster Treuhand AG (Zürich) |
| Anwaltskanzlei | Aktenarchiv, Honorarberechnung, Fristensteuerung, Mandantenbriefe | Kanzlei Beispiel + Partner (Bern) |
| Immobilien-Verwaltung | Bewirtschaftung, Nebenkostenabrechnung, Mietvertragserstellung | Beispiel-Liegenschaften AG (Basel) |
| Steuerberater | Steuererklärung-Vorbereitung, Lohnausweise, MWST-Anmeldung | Steuerbüro Beispiel (Luzern) |

**Synthetic-data rules:** emails → `*@example.ch`; phones → `+41 00 000 00 00` shape; tokens → `TEST_FIXTURE_<scenario>`; never real customer / company / VAT numbers.

## Step 3 — Edge-case checklist

Always include at least 3 of these in any fixture set:

- An overdue / out-of-range / past-deadline item.
- A duplicate row (same key, different timestamps).
- A weird date format ("31.04.2026" — invalid; "1.Jan.2026"; ISO-only field with German format).
- An empty optional field.
- A Sonderzeichen / Umlaut in a name (`Müller`, `Bär`, `Schöni`).
- A field at the boundary (very large invoice amount, very long string, file at the 60KB limit if uploading to interview bot).
- A non-Swiss-format outlier (US phone, UK postcode, EUR currency) the workflow must reject or handle.

## Step 4 — Fixture recipes

### CSV (pandas-readable)

```python
import pandas as pd
df = pd.DataFrame([
  {"rechnung_nr": "R-2026-0142", "kunde": "Bach AG", "betrag_chf": 1850.00, "faellig_am": "2026-04-15", "status": "offen"},
  {"rechnung_nr": "R-2026-0142", "kunde": "Bach AG", "betrag_chf": 1850.00, "faellig_am": "2026-04-15", "status": "offen"},  # duplicate
  {"rechnung_nr": "R-2026-0099", "kunde": "Müller GmbH", "betrag_chf": 24500.00, "faellig_am": "2026-03-01", "status": "überfällig"},
  # ...
])
df.to_csv("invoices.csv", index=False, encoding="utf-8")
```

### XLSX (openpyxl-via-pandas)

```python
df.to_excel("invoices.xlsx", index=False, engine="openpyxl")
```

### JSON (matches inferred webhook body shape exactly)

```python
import json
samples = [
  {"customer_email": "buchhaltung@example.ch", "amount_chf": 1850.00, "due_date": "2026-04-15", ...},
  {"customer_email": "kontakt@example.ch", "amount_chf": 0, "due_date": None, ...},  # edge: zero + null
]
json.dump(samples, open("webhook-bodies.json","w"), indent=2, ensure_ascii=False)
```

### PDF (ReportLab via the existing helper)

```python
import sys; sys.path.insert(0, "/home/paperclip/_context/tools")
from generate_pdf import generate_pdf  # if importable; else inline ReportLab
# Or simpler: write a markdown "SOP" + use the operator's existing PDF tool to render.
```

For overnight runs, prefer a plain text file with a `.txt` extension over a heavyweight PDF unless the automation specifically requires PDF input.

### Notes / Markdown

A short `notes.md` per scenario that lists the persona, the captured edge cases, and any context not obvious from filenames.

## Step 5 — BRIEF.md is non-negotiable

Every output folder must contain `BRIEF.md` with this shape:

```markdown
# Test fixture brief — <scenario>

## Automation tested
- Path / branch / workflow id: `<verbatim>`
- Read at commit / timestamp: `<sha or ISO>`

## Inferred input shape
<verbatim schema or quoted source — JSON, argparse output, n8n nodes excerpt, etc.>

## Persona
<persona name + town>

## Files in this folder
- `invoices.csv` — 24 rows, 3 deliberate edge cases (see below).
- `webhook-bodies.json` — 8 sample payloads, 2 edge cases.
- ...

## Edge cases included
1. Duplicate invoice (R-2026-0142 twice).
2. Sonderzeichen in customer name (`Müller GmbH`).
3. ...

## How to plug in
1. <Step 1: where to feed the CSV>
2. <Step 2: how to fire the webhook>
3. <Step 3: what to verify in the automation's output>
```

## Step 6 — GitHub mechanics

Inside your agent workspace:

```bash
# Authenticate by embedding the PAT in the clone URL.
PAT="$GITHUB_PAT_JOAQUINAUTOMATISIERBAR"
git clone --depth 1 "https://${PAT}@github.com/joaquinautomatisierbar/paperclipai-builds.git" /tmp/builds
cd /tmp/builds

# Existing build branch case:
git fetch origin build/AUT-66
git checkout build/AUT-66
mkdir -p extra-testing/20260601-2330-treuhand-mahnung
# write files...
git add extra-testing/20260601-2330-treuhand-mahnung
git -c user.email="testdata-agent@automatisierbar.ch" -c user.name="Test Data Generator" \
    commit -m "Test data: Treuhand Mahnung (build AUT-66)"
git push origin build/AUT-66

# Fresh test-data branch case:
git checkout -b test-data/interview-bot-20260601-2330
mkdir -p .  # commit at repo root
# write files at repo root...
git add .
git commit ...
git push -u origin test-data/interview-bot-20260601-2330
```

If the push is rejected (non-fast-forward, etc.), don't force-push. Pull + replay or abort + report to operator.

## Hard rules (reiterated from AGENTS.md)

- Read-only on every automation. Never modify, never run it, never push to its `main`.
- Never invent fields the inference didn't surface. Ask via Issue comment instead.
- Never include real customer data. Personas are synthetic; emails are `@example.ch`.
- Never re-generate the same scenario into the same folder. Bump the timestamp.
- Never push secrets into a fixture.
