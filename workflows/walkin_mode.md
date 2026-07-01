---
autonomy-level: L3
bike-method-phase: 1
kpi-bucket: more-customers
kpi-metric: walk-in leads captured per field day (lossless capture) + voice-memo transcripts/week feeding the future appointment-setter playbook (target ≥5/wk)
---

# Walk-in Mode (Phase 1)

A phone-installable PWA the door-to-door team uses in the field, at
**walkin.automatisierbar.ch** (the cockpit Flask app, `api.py`, on its own Caddy
host + PWA scope). Two functions: capture a walk-in as a lead, and record voice
memos that become a transcribed knowledge base for the appointment-setter playbook
we write once we hire. Built separate from the Hub so it ships now; ported into the
Hub later.

## The five process elements

- **Trigger** — a team member, in the field, opens the installed PWA and either saves
  a new lead (typed, or **scanned from a business card**) or records a voice memo. The
  transcription leg is also triggered by a daily VPS cron (07:00 Europe/Zurich).
- **Data sources** — the operator's typed capture (free-text + light fields); an
  optional **business-card photo** (Claude Vision OCR); recorded audio blobs; the live
  Leads DB (dedup); the 💡-callout; Gemini (transcription).
- **Transformations** — optionally OCR a card photo into prefill fields (Claude Vision +
  role classification); build a schema-aware Leads-DB row + a one-line callout entry
  from the capture; store audio + a sidecar ledger on disk; transcribe pending audio
  with Gemini and write transcripts into the Knowledge Base DB.
- **Decision points** — the operator reviews/edits every OCR prefill before saving
  (OCR is advisory, never auto-saves); dedup (expand an existing lead vs create a new
  one); per-day transcription cap (Gemini free tier); per-memo retry/skip (attempts < 3).
- **Destination** — Interview Datenbank (Leads DB) row · 💡-callout line on the
  Operations Cockpit · Walk-in Knowledge Base DB (one row per transcribed memo) ·
  voice memos on the VPS filesystem.

## Autonomy / rollout

- **Lead capture** is deterministic (no AI decides anything — the operator writes, the
  app stores). Effectively L2: human authored, system persisted.
- **Transcription** is L3: the daily cron runs end-to-end; the operator validates
  periodically via the Knowledge Base DB.
- **Bike-Method Phase 1**: the FIRST real lead write (live Leads DB + live callout are
  production data) is supervised and **halts to Telegram** before proceeding.

## Capture flow — `POST /api/walkin/lead`

Auth: team magic-link (`_team_member`). Body: `{company*, notes*, contact, role, email,
website, city, phone, walkin_date}`. Two best-effort, isolated writes:

1. **Leads DB** (`tools/notion_session.py`): dedup by email/phone
   (`find_lead_by_email_or_phone`) → `expand_lead` (fills only empty props) or
   `create_inbound_lead`. Tagged `HOT STATUS = WALK IN BUT NO BAMFAM`,
   `Outreach Channel = Walk-In`, `Pipeline Stage = Problem Interview`,
   `Outreach Gemacht? = Contacted = true`, `Gesprächsdatum/Last contacted = walkin_date`.
   The verbatim notes are also pasted onto the lead page body (`append_booking_note`).
2. **💡-callout** (`append_walkin_callout_line`): one **unmarked** line
   `Company → details. notes` appended to block `389bebb0c2f9804eb2bef28e599c0a68`, so
   `/walkinmail` (which marks it ✅ after drafting) and `/walkinleadsconvert` keep
   working unchanged. Do not add ✅ here.

The two skills remain the downstream owners of mail-drafting + lead-conversion; this
just moves the *capture* from hand-typing in Notion to the field PWA.

## Visitenkarte scan — `POST /api/walkin/card-ocr`

A "📇 Visitenkarte scannen" button at the top of the **Neuer Lead** tab. Mirrors the
KnowSpesen receipt-OCR pattern exactly, but is **advisory prefill only** — it feeds the
existing lead form; the operator reviews/edits and saves via the unchanged
`POST /api/walkin/lead`. There is **no separate lead-write path** for cards.

- **Client** (`static/walkin.html`): the photo is downscaled to ≤1600px JPEG q0.85 in the
  browser (canvas, which also normalises iOS HEIC), POSTed as multipart `file`.
- **Server** (`tools/walkin_card_ocr.py` → `extract_card`): one Claude Vision call
  (`MODEL_FAST` = `claude-sonnet-4-6`, `max_tokens=500`, base64 image, ephemeral system
  cache). Returns a sanitised prefill dict `{name, company, title, role, email, phone,
  website, city, postal_code, address, confidence}`. Fail-safe like the spesen OCR:
  empty image / bad MIME / missing key / API error all return HTTP 200 with `ok:false`
  so the form stays manual — it **never raises**.
- **Role classification** — the model maps the printed job title onto exactly one of the
  six `Rolle` options (`walkin_capture.ROLE_OPTIONS`) or `null`; the raw `title` is kept
  and folded into the notes so nothing is lost when it can't be mapped.
- **Prefill rules** — only fills empty fields (never clobbers what the operator typed);
  seeds `Notizen` with an editable default (`Visitenkarte gescannt (<date>). Titel: …
  Adresse: …`) so the required-notes check passes and the 💡-callout keeps context.
- **Photo lifecycle** — used for extraction only, **never stored** (no disk write, no new
  env var). The size cap reuses `SPESEN_MAX_IMAGE_BYTES`.

Autonomy: **L2** (AI drafts fields, human reviews before every save) — a capture aid,
not an autonomous writer.

## Voice-memo flow

- **Upload** — `POST /api/walkin/memo` (multipart). Accepts `audio/*` and `video/mp4`
  (iOS Safari emits mp4/aac, Android webm/opus). Saved to `WALKIN_MEMO_DIR`
  (`/srv/cockpit/voice_memos`) as `{YYYYMMDD-HHMMSS}__{recorder}__{uuid8}.{ext}` with a
  sidecar `{name}.json` (`status:"pending"`). Per-memo cap `WALKIN_MAX_AUDIO_MB` (20).
- **Transcribe** — `tools/transcribe_walkin_memos.py` via the daily cron
  (`tools/scheduled/walkin-transcribe.sh`). Picks up to
  `WALKIN_TRANSCRIBE_MAX_PER_DAY` (10) pending memos (oldest first), calls
  gemini-2.5-flash (inline base64, `x-goog-api-key`, thinking disabled), writes the
  transcript to the Walk-in Knowledge Base DB, flips the sidecar to `transcribed`.
  Idempotent — a transcribed memo is never re-sent; a failure increments `attempts`
  and is retried next day (skipped after 3). The operator never plays audio back.
- **Knowledge Base DB** — created once via `POST /api/walkin/setup-kb-db` (operator
  auth), parent = Operations Cockpit. Props: Name, Transcript, Recorded By, Recorded
  At, Duration (s), Audio Filename, Status, Topic.

## Config / prerequisites

`/etc/cockpit/env` (see `deploy/cockpit.env.example`): `GEMINI_API_KEY` (free Google
AI Studio key — until set, the cron no-ops; capture + upload still work),
`ANTHROPIC_API_KEY` (**required for the Visitenkarte-scan OCR route** — until set, the
scan returns `ok:false "OCR nicht konfiguriert"` and the form stays manual; the same
key KnowSpesen's receipt OCR uses), `WALKIN_KB_DB_ID` (after setup-kb-db),
`WALKIN_MEMO_DIR`, `WALKIN_TRANSCRIBE_MAX_PER_DAY`, `WALKIN_MAX_AUDIO_MB`. DNS A-record
`walkin → 187.124.188.2` + the Caddy host block (`deploy/Caddyfile.cockpit`). Full
runbook: `deploy/COCKPIT_HANDOFF.md` → "Walk-in mode".

## Halt-before-acting

The first real lead submission writes to the production Leads DB + live callout. Before
that first production run:

```
bash .claude/hooks/notify-telegram.sh halt "First real Walk-in lead write to live Leads DB + 💡-callout — proceed?"
```

## Known limits / seams (Phase 2)

- **`/walkinmail` from the app** — the callout line is already produced in the exact
  format the skill consumes; the seam is a future `POST /api/walkin/draft-mail` calling
  `tools/walkin/infomaniak_draft.py` (drafts only, never sends), operator-gated.
- **Audio format** — Gemini is sent the container's natural mime (m4a→audio/mp4,
  webm→audio/webm). If a format is rejected, that memo is flagged `error` in its
  sidecar (and visible in the log); a future ffmpeg pre-convert step is the fix.
- **Offline memo queue** — Phase 1 is online-only (a failed upload shows a retry toast).
  IndexedDB + Background Sync is the enhancement.
- **>20 MB memos** — capped at upload; the Gemini Files API resumable path is the v2
  escape hatch.
- **Playbook synthesis** — accumulate transcripts, then summarise into the playbook
  (`Topic` / `Recorded By` are the grouping seams).
- **Audio pruning** — audio kept indefinitely for now (~1 MB/min); prune-after-N-days is
  a later cron.

## Verification

See `deploy/COCKPIT_HANDOFF.md` and the regression tests `tools/test_walkin_capture.py`
(pure/offline: lead-field + callout-line builders, validation, mime→ext, sidecar
round-trip) and `tools/test_walkin_card_ocr.py` (pure/offline: card-OCR sanitiser +
role-enum guard + fail-safe returns; no API call). Live smoke: curl the lead endpoint
against a sandbox DB (`NOTION_LEADS_DB_ID` + `WALKIN_CALLOUT_BLOCK_ID` overrides), curl
the memo upload with a sample audio file, then
`python3 tools/transcribe_walkin_memos.py --dry-run`. Card-OCR smoke (one paid Vision
call): with `ANTHROPIC_API_KEY` set, `curl -F file=@card.jpg <host>/api/walkin/card-ocr`
(needs a team session) and confirm the JSON extracts name/company/email/phone + `ok:true`.
