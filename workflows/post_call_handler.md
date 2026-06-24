---
name: Workflow E — Post-Call Handler
autonomy-level: L3
bike-method-phase: 1
status: SPEC (build with user — needs Vapi server.url + n8n Vapi credential)
n8n-id: TBD
owner: Joaquin
---

# Workflow E — Post-Call Handler

Receives each finished call from Vapi, lands the transcript so the **existing Workflow A** classifies it, and feeds the Script-Tuner.

## Five elements
- **Trigger:** Webhook `POST /voice-call-result` — set as the Vapi assistant's `server.url` with `serverMessages: ["end-of-call-report"]`.
- **Data sources:** Vapi `end-of-call-report` payload: `{ message.transcript, message.analysis.structuredData, message.cost, message.endedReason, message.call.metadata {lead_id, session_id, firma, branche, disclose_ai} }`. (No `recordingUrl` — recording is OFF.)
- **Transformations:** ADAPTER-IN Code node normalizes the payload; build a transcript `.txt` body.
- **Decision points:** `connected && transcript present?`
- **Destination (two writes):**
  1. **Google Drive** — create `<Firma>__joaquin.m4a_<YYYYMMDD-HHMMSS>.txt` in the Transcripts folder `1PJUP0AOlU3SyT0NZF9_rzKfx19tRTVJh`. This fires the **existing Workflow A** (`9kra1rbKJacENksN`) → classify → Notion Lead-DB + Call Analytics, attributed to Joaquin via the `__joaquin` suffix.
  2. **Flask app** — `POST {APP}/api/voice/session/<session_id>/call` with `{lead_id, firma, branche, disclose_ai, transcript, outcome, analysis}` (X-API-Key) → feeds the Script-Tuner.
  - Also: add Vapi `cost` to the running 700-CHF budget tracker.
  - **Voicemail / not connected** branch → light log only (outcome `Direct-Abwimmlung`), no Drive drop, retry-eligible.

## Nodes (plan)
Webhook → Code (ADAPTER-IN) → IF (connected & transcript) → [Google Drive: Create from Text] + [HTTP Request: POST app] ; ELSE → Code (log). Budget increment via a small Notion update or a counter record.

## Build notes
- Reuse n8n Drive binary/text-file create pattern; filename convention must match Workflow A's parser (`<Firma>__<interviewer>.m4a_<ts>.txt`).
- App call needs `X-API-Key` header (= `PDF_API_KEY`); store as an n8n credential/env.
- Keep classification in Workflow A (do NOT re-classify here) — one classifier, apples-to-apples with human calls.
