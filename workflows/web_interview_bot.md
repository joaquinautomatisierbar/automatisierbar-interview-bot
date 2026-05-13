---
autonomy-level: L2
bike-method-phase: 1
kpi-bucket: less-cost
kpi-metric: zero-followup rate ≥ 80% on first 3 prod interviews after redesign (and ≥ 90% by interview 10)
---

# Web Interview Bot — `automatisierbar-interview-bot.onrender.com`

## Objective

Capture enough process detail in a single 10–15 min web session that a developer (or Claude Code) can build an n8n MVP end-to-end with **zero clarifying follow-ups**.

Replaces the older Telegram-only flow ([telegram_interview_bot.md](telegram_interview_bot.md), now legacy) and the original web flow that asked categorical questions but skipped the actual process narrative.

## Architecture (process map)

| Element | Implementation |
|---|---|
| **Trigger** | User opens `/?s=…` (resume) or `/` (new) — frontend SPA in [static/index.html](../static/index.html). |
| **Data sources** | Free-text context, optional Notion lead autocomplete, optional file uploads (Excel/CSV/PDF/PNG/JPG/TXT/MD), optional sidebar notes pad. |
| **Transformations** | Server-side LLM (Claude Sonnet 4.6) classifies context and emits adaptive questions; file-extract pipeline turns uploads into plain text; process-map rows persist as structured JSON. |
| **Decision points** | Question generation: process-selection vs technical detail. Round loop: complete vs needs_more. Notion payoff: skip if heading already exists. |
| **Destination** | Notion lead page: per-round Q&A blocks, ROI block, **Mermaid flowchart + step table + Claude Code code block** auto-appended on completion. PDF spec downloadable. |

## Phase order (4 phases)

1. **Context** (`screen-context`)
   - User picks a lead (autocompletes Notion Leads DB) or types free text.
   - Submit → `POST /api/session/start` → session created in Notion + first batch of questions returned but **queued** (not shown yet).
   - Sidebar unlocks at this point.

2. **Process map** (`screen-process-map`) — *NEW*
   - Guided table: `Wer | Was | Tool | Daten rein | Daten raus | Auto?`
   - Pre-filled with 3 empty rows; user adds/removes via `+ Schritt hinzufügen` / `×`.
   - Auto column is a 3-state dropdown (`✓ ja` / `~ teils` / `✗ nein`).
   - Notes textarea below the table for sonderfälle.
   - Submit → `POST /api/session/{id}/process_map` → state persisted; queued questions then shown.
   - Skip button → bypasses the persistence call but still transitions to questions (process_map stays empty).

3. **Q&A rounds** (`screen-questions`)
   - Same as before; LLM asks max 8 questions, max 3 rounds typical.
   - Choice questions always include `Andere…` as an escape — selecting it reveals a freeform textarea.
   - Sidebar still active — user can drop more files / notes mid-round.
   - On `status: complete` → ROI screen; on `needs_more` → next round.

4. **ROI + payoff** (`screen-roi`)
   - User-facing: bars, savings, complexity, build time.
   - Notion payoff (auto-written): `Aktueller Prozess (Ist-Zustand)` heading + Mermaid flowchart + collapsible Schritt-Details table + `Build Prompt für Claude Code` heading + callout + markdown code block with the full prompt.

## Sidebar (always-on while session active)

- **Drag-drop file zone** — accepts `.xlsx .xls .csv .pdf .png .jpg .jpeg .txt .md`, max 5 MB each, max 10 files per session.
- **Notes pad** — autosaves every ~1.5 s after last keystroke.
- **Mobile (<900 px)** — collapses to a bottom-sheet drawer, opened via the floating 📎 FAB (badge shows attachment count).
- Backend: `POST /api/session/{id}/attachment` (multipart), `DELETE …/attachment/{idx}`, `PATCH …/extras`.
- File extraction lives in [tools/file_extract.py](../tools/file_extract.py) — Excel/CSV via pandas+openpyxl, PDF via PyMuPDF, images via Claude vision, text raw.

## State (Notion `State` rich_text JSON, ~200 kB ceiling)

```json
{
  "session_id": "...",
  "status": "active|complete",
  "round": 1,
  "context": "...",
  "all_qa": [{"round": 1, "qa": [{"question": "...", "answer": "..."}]}],
  "current_questions": [],
  "roi": {...},
  "lead_page_id": "...",
  "process_map": [{"step": 1, "who": "...", "action": "...", "tool": "...", "data_in": "...", "data_out": "...", "automatable": "yes|partial|no"}],
  "process_map_notes": "...",
  "attachments": [{"filename": "x.xlsx", "mime": "...", "size": 38421, "kind": "excel", "extracted_text": "..."}],
  "extra_context": "..."
}
```

Session-state writer (`tools/notion_session.py:add_attachment`) enforces a 180 kB pre-write ceiling and rejects with `state_full`/`too_many` so the user gets a clear UI message instead of a silent Notion error.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/session/start` | Create session + return queued round-1 questions |
| GET  | `/api/session/{id}` | Resume — re-hydrate full state |
| POST | `/api/session/{id}/answers` | Submit a round; LLM evaluates against process map + extras + attachments |
| GET  | `/api/session/{id}/process_map` | Re-hydrate the captured walkthrough |
| POST | `/api/session/{id}/process_map` | Persist the walkthrough (steps + notes) |
| PATCH | `/api/session/{id}/extras` | Save sidebar notes pad (autosaved) |
| POST | `/api/session/{id}/attachment` | Upload + extract a file; persists `extracted_text` |
| DELETE | `/api/session/{id}/attachment/{idx}` | Remove one attachment |
| GET  | `/api/session/{id}/pdf` | Download Bedarfsanalyse PDF |
| GET  | `/api/session/{id}/prompt` | Generate the Claude Code build prompt on demand |

## Notion payoff layout (auto-written on completion)

```
══ Aktueller Prozess (Ist-Zustand) ══         ← heading_2
[mermaid code block]                            ← flowchart TD with 3-color step nodes
"Notizen: …"                                    ← paragraph (only if process_map_notes set)
▶ Schritt-Details (Tabelle)                    ← toggle (collapsed)
   [table block: # | Wer | Was | Tool | Daten rein | Daten raus | Auto?]
══ Build Prompt für Claude Code ══             ← heading_2
📋 Diesen Prompt in Claude Code einfügen…     ← callout
[code block, language=markdown, full prompt]    ← copy-paste destination
```

**Idempotency:** `_page_already_has_payoff` scans top-level blocks for the `Aktueller Prozess (Ist-Zustand)` heading. If found, the write is skipped — operator clears the page manually if a fresh re-run is wanted.

**Mermaid generator** (deterministic, no LLM): `_build_mermaid` renders one node per step with class-driven coloring (`auto`=green, `partial`=yellow, `manual`=red). Sanitizes labels: replaces `"` → `'`, `<` → `‹`, `>` → `›`, `|` → `/`, caps each field at 24–36 chars.

## Models + caching

- `claude-sonnet-4-6` for all interactive endpoints (round eval, prompt, spec, vision OCR, claude code prompt).
- `claude-opus-4-7` reserved but not used at runtime — Render's gunicorn 30 s timeout would kill it.
- System prompts cache via `cache_control: ephemeral`.

## What changed (vs the prior web flow)

1. New `Process Map` phase between context and Q&A.
2. Persistent right-side sidebar with file uploads + notes pad (mobile bottom-sheet).
3. `Andere…` escape on every choice question (prompt rule + UI fallback).
4. Backend now accepts file uploads and feeds extracted text + extras + process map to every LLM call.
5. End-of-interview Notion page auto-gets the **Mermaid flowchart, step table, and Claude Code build prompt as a code block** — operator copies straight from Notion.

## Operating notes

- **Render auto-deploys on push to `main`.** Don't push from inside this Claude Code session without halting first — production traffic hits the deployed server.
- **Cost guard:** image OCR uses one Sonnet call per uploaded image (~CHF 0.01–0.03 each). Excel/CSV/PDF/text are free local extraction.
- **State ceiling:** 10 attachments or 180 kB JSON, whichever first. Frontend shows the cap clearly.
- **Bike Method Phase 1**: every interview gets an operator review (Notion page open, scroll to bottom, eyeball the Claude Code prompt) until 3 consecutive sessions produce a working n8n MVP without follow-up. Then advance to Phase 2.

## KPI tie

- **Bucket:** less-cost (faster discovery → fewer follow-up calls → lower CAC).
- **Metric:** zero-followup rate ≥ 80% on first 3 prod interviews after redesign. Measured via the post-build sales call: did the developer have to come back to ask the prospect anything? If yes → regression.

## Future improvements (not in scope)

- Pre-session attachment staging (drop a file before writing context — currently locked until session exists).
- Decision-node detection in mermaid (action contains `?` → render as `{...}` diamond).
- Server-side question gap analysis after process-map submit (one extra Sonnet call to flag obvious holes before round 1).
