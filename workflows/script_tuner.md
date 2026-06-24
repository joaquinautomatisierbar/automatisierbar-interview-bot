---
name: Script-Tuner — per-session voice-script improvement loop
autonomy-level: L2
bike-method-phase: 1
status: BUILT + locally tested (2026-06-02); pending Render deploy
owner: Joaquin
---

# Script-Tuner

After each batch ("session") of AI cold calls, the operator reviews AI-generated suggestions to improve the call script, approves/rejects/edits each, and one click re-deploys the improved script to the live Vapi assistant. The script improves session-to-session. Lives in the existing Flask app ([api.py](../api.py) + [static/tuner.html](../static/tuner.html)).

## Five elements
- **Trigger:** operator opens `/voice/tuner/<session_id>` after a dialing session (link delivered by Workflow E / weekly report later).
- **Data sources:** `data/voice_sessions/<id>.json` (calls + transcripts + analysis, written by Workflow E) and `prompts/voice_agent_system.txt` (current deployed system prompt = machine-readable source of truth).
- **Transformations:** `claude_client.generate_script_suggestions(transcripts, current_prompt, stats)` (Claude Sonnet) → concrete `{section, current, proposed, rationale}` suggestions; `_compute_voice_stats()` → session stats incl. disclose A/B hot-rate split.
- **Decision points:** operator hits **Übernehmen** / **Verwerfen** / **Anpassen** (edit) per suggestion. This is L2 — AI drafts, human approves every change. No auto-apply.
- **Destination:** on apply (non-dry-run) → PATCH the live Vapi assistant system prompt via [tools/vapi_client.py](../tools/vapi_client.py), atomically rewrite `prompts/voice_agent_system.txt`, bump version + prepend to `prompts/voice_agent_changelog.md`.

## Endpoints (all `/api/voice/*` require `X-API-Key` = `PDF_API_KEY`)
| Route | Purpose |
|---|---|
| `POST /api/voice/session/start` | create session → `{session_id}` |
| `POST /api/voice/session/<id>/call` | append a call `{lead_id, firma, branche, disclose_ai, transcript, outcome?, analysis?}` (Workflow E calls this) |
| `GET  /api/voice/session/<id>` | full session + cached report |
| `POST /api/voice/session/<id>/report` | generate (or return cached; `{force:true}` to regenerate) stats + suggestions |
| `POST /api/voice/script/apply` | `{session_id, decisions:[{suggestion_id, action, edited_text?}], dry_run}` → compose new prompt; **dry_run defaults True** |
| `GET  /voice/tuner/<id>` | serves the operator review page |

## Safety
- `apply` **dry_run defaults True** — only `dry_run:false` mutates the live assistant. Live path PATCHes Vapi *first*, then writes the file (atomic via tmp+os.replace) only on success.
- All data/mutating routes auth-gated (`_auth_ok`, fail-closed if `PDF_API_KEY` unset).
- snippet replacement is exact-match-once; unmatched snippets are reported in `skipped`, never force-applied.

## Run / test
- Local e2e test: `python3 .tmp/test_tuner.py` (uses Flask test_client, real report call, dry-run apply). Last run: all green.
- **Render deploy (pending — needs user):** ensure env has `VAPI_API_KEY`, `VAPI_ASSISTANT_ID`, `ANTHROPIC_API_KEY`, `PDF_API_KEY`. The `data/voice_sessions/` dir persists on the instance (or migrate store to Notion later for multi-instance).

## Known follow-ups
- Session store is file-based (single-instance). Fine for v1; move to Notion if Render scales to multiple workers.
- Suggestion `current` snippets must match `voice_agent_system.txt` exactly to apply — the LLM is instructed to quote verbatim; monitor `skipped` rate.
