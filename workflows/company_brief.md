---
name: company_brief
autonomy-level: L2
bike-method-phase: 1
kpi-bucket: more value per customer + less cost
kpi-metric: better-prepped meetings; Tej stops hand-writing WF briefs
last_updated: 2026-07-05
---

# Company Brief Automation (Hub M9) — Cockpit engine

Auto-generates a self-contained HTML pre-meeting **brief** for a company before a scheduled
meeting. This SOP covers the **cockpit (Python) engine**; the trigger + inbox notification +
client-page embed live in the **Hub** (M9, NestJS). See the Hub repo `docs/ROADMAP.md` v2·M9.

## The five process elements

- **Trigger:** the Hub's BullMQ `brief.worker` detects an `appointment` Record whose `startDate`
  is within `BRIEF_LEAD_HOURS` (~18h) and that isn't yet briefed, then POSTs here.
- **Data sources:** the linked Notion lead (Interview Datenbank `31cbebb0…`), its interview-spec
  `State` JSON (Pilot/General), the lead page body (`Notiz vom Besuch`), live web research
  (Anthropic `web_search` tool), and — future — IMAP mail history.
- **Transformations:** one Claude call per brief → validated structured JSON → deterministic HTML.
- **Decision points:** brief type is auto-derived from the lead's Pipeline Stage (no override).
- **Destination:** HTML written to `BRIEFS_DIR`, served at `/b/<token>.html`; the Hub embeds it on
  the client page + notifies the meeting's attendees.

## Brief types (auto by stage)

| Pipeline Stage | Type | Contents |
|---|---|---|
| Workflow Interview · Process Mapping · Problem Interview | **wf** | Firmensteckbrief, Was die Firma macht, Entscheidungsträger, Automatisierungs-Hypothesen, Gesprächsleitfaden (Mom-Test), Gates, Was sie EUCH fragen könnten |
| Prototype Building · Prototype Testing · Pilot Client | **pilot** | Kurzprofil, was im Interview herauskam, **das gebaute Produkt & wie es aussieht**, wen ihr trefft, Ziel + nächster Schritt |
| Paying Client | **general** | Kurzprofil + Beziehungsstatus, Historie, wen ihr trefft, Produktstand, mögliche Themen |
| OUT / other | — | skipped (HTTP 422 `{skip:true}`) |

Every type opens with an **ELI5 "Was macht diese Firma eigentlich?"** section (third-grader
level) + a "Für Erwachsene" note — this is a hard requirement (fixes the "read the brief, still
didn't get what they do" problem). Style clones `company-formation/equity-plan/explainer.html`.

## Files

- `tools/brief_generator.py` — engine. `classify_brief_type(stage)`, `gather_context(...)`,
  `generate_brief_content(...)` (the Claude call, `web_search` on for WF), `render_html(...)`
  (deterministic), `generate(lead_page_id, brief_type=None)` (orchestrator).
- `api.py` — `POST /api/brief/generate` (auth `X-Brief-Secret`), `GET /b/<token>.html`,
  `briefs.*` host dispatch (404 root, no index).
- `deploy/Caddyfile.briefs` — the subdomain block (reverse_proxy → :8082).

## Endpoint

`POST /api/brief/generate`  header `X-Brief-Secret: <BRIEF_SHARED_SECRET>`
body `{"lead_page_id": "<notion page id>", "brief_type"?: "wf|pilot|general", "appointment_id"?: "..."}`
→ `200 {ok, brief_url, brief_type, firma, summary}` · `422 {skip:true}` (bad stage / no lead) ·
`400` (bad payload) · `401` (bad/absent secret) · `500` (generation/write error).

`brief_type` omitted → derived from the lead's stage.

## Config (env — `/etc/cockpit/env` on the VPS)

- `BRIEF_SHARED_SECRET` — shared with the Hub worker (required; endpoint is fail-closed).
- `BRIEFS_DIR` — where HTML is written (default `./.tmp/briefs`; set to a persistent dir on the VPS,
  e.g. `/srv/cockpit/briefs`).
- `BRIEF_BASE_URL` — default `https://cockpit.automatisierbar.ch` (works immediately, no new DNS).
  Flip to `https://briefs.automatisierbar.ch` once that subdomain + Caddy block are live.
- `BRIEF_MODEL_WF` / `BRIEF_MODEL_PILOT` / `BRIEF_MODEL_GENERAL` — default Sonnet (`MODEL_FAST`).
  WF benefits from Sonnet + web research (judgment for hypotheses + Gesprächsleitfaden); set to
  `claude-haiku-4-5-20251001` to cut cost if quality holds.
- `ANTHROPIC_API_KEY`, `NOTION_API_KEY` — already present.

## Operational notes / learned constraints

- **Generation takes ~90–150s** (web_search + a large structured completion). The endpoint is
  **synchronous**, so the cockpit gunicorn **`--timeout` must be ≥300** (default was 120 — raise it
  in `deploy/cockpit.service` + `daemon-reload` + restart) and the Hub client timeout ~280s.
- The Hub worker must POST briefs **sequentially** (one at a time), so at most one generation runs
  at once — the 2nd of the 2 gunicorn workers stays free for normal cockpit traffic.
- **Fail-safe:** research/generation failures degrade the brief, they don't crash; a hard failure
  returns 500 and the Hub retries next tick.
- **Cost/paid:** each brief is a paid Claude call (+ web_search for WF). Halt-before-acting on the
  first real run; a single verification call is fine.
- **Future:** (a) async endpoint (202 + `GET /api/brief/status/<token>`) to avoid tying up a worker;
  (b) IMAP mail-history section via `team_mailboxes.py` + `inbox_reply_drafter.py` primitives.

## Verify

1. `pytest tests/test_brief.py` (mapping, render self-containment, endpoint auth/validation).
2. Real: find a Workflow-Interview lead, `brief_generator.generate(<page_id>, "wf")`, open the HTML,
   confirm the ELI5 section + no fabricated facts + `#0f766e`/amber styling.
3. Endpoint: `curl -XPOST .../api/brief/generate -H "X-Brief-Secret: …" -d '{"lead_page_id":"…"}'`
   → `brief_url`; open it; confirm it renders standalone + embeds in an iframe.
