---
name: Workflow D — Outbound Dialer / Batch Runner
autonomy-level: L3
bike-method-phase: 1
status: SPEC (build with user — needs n8n Vapi credential + Lead-DB schema fields)
n8n-id: TBD
owner: Joaquin
---

# Workflow D — Outbound Dialer / Batch Runner

Operator presses a button → pulls eligible Swiss B2B leads → fires AI calls via Vapi → marks them dialed. Stops at a call cap / hot-lead target / budget.

## Five elements
- **Trigger:** Webhook `POST /cold-call-dial` (from a Notion button; also MCP `execute_workflow`-able). Body: `{max_calls, target_hot?, branche?, city?, cooldown_days, dry_run, disclose_ratio}`.
- **Data sources:** Notion Lead-DB `31cbebb0-c2f9-8047-9e9f-fc59851f8a34` (`getAll`, `simple:false`, `returnAll:true`); 700-CHF budget tracker; `prompts/voice_agent_conversation.md` (assistant already holds the prompt).
- **Transformations:** Code node — E.164-normalize phone; build per-lead Vapi payload (ADAPTER-OUT).
- **Decision points (eligibility / pre-dial gate):** keep a lead IFF `phone` present & +41-normalizable · `Branche` ∈ ICP backoffice set (+ optional batch branche/city) · `Stern Opt-Out != true` (NEW field) · `Last contacted` null|older-than-cooldown · `Call Attempts < 2` (NEW field) · Pipeline Stage not in {Workflow Interview…Paying, OUT}. Sort never-called-first → take `max_calls`. Split disclose A/B by `disclose_ratio`. **Budget gate:** refuse if `700 − spent < buffer`. **`dry_run`** → return eligible list, NO dials.
- **Destination:** for each lead → Vapi `POST /call`; then Notion update lead (`Last contacted=now`, `Contacted=true`, `Outreach Channel="AI Cold Call"`, `Call Attempts +1`).

## Vapi call payload (ADAPTER-OUT)
```json
{
  "phoneNumberId": "87349fc2-c185-4b30-8ba5-e17512cd4ca9",   // swap to +41 number for Phase 2
  "assistantId": "0a7576f1-35ac-4293-977e-09b6fc3b5923",
  "customer": { "number": "+41..." },
  "assistantOverrides": {
    "variableValues": { "firma": "...", "branche": "...", "kontakt_nachname": "...",
                        "disclosure_line": "" }
  },
  "metadata": { "lead_id": "<notion page id>", "session_id": "<from /session/start>" }
}
```
Auth: `Authorization: Bearer <VAPI_API_KEY>` (n8n HTTP Header Auth credential — UI-only, user creates).

## Nodes (plan)
Webhook → Code(validate+defaults) → Budget gate → Notion getAll → Code(eligibility+sort+take+A/B) → IF dry_run (return list / continue) → HTTP POST app `/api/voice/session/start` (open session) → SplitInBatches(1) → Set(ADAPTER-OUT) → HTTP POST Vapi `/call` → Notion update lead → Wait(20–40s) → loop → Code(summary) → Telegram checkpoint.

## Rollout
- New workflow → Bike Phase 1. First live dial: `notify-telegram.sh halt` + poll before firing. Phase 1 `max_calls=1` to founders' phones; ramp 5→20 as gates pass (see plan). Never auto-advance phases.
- Prereqs before live: n8n Vapi credential; Lead-DB fields `Stern Opt-Out`(checkbox) + `Call Attempts`(number) + `AI Cold Call` channel option; Stern-checked list; +41 number live (Phase 2).
