# Decisions Log

Append-only record of meaningful architectural decisions and *why* they were made. Memory holds facts; this file holds reasoning. When future-you (or a fresh session) wonders "why did we do X instead of Y," this is where the answer lives.

**Format per entry:**

```
## YYYY-MM-DD — Short title

**Decision:** what was decided.

**Why:** the reasoning, constraints, what would change your mind.

**Alternatives considered:** what else was on the table.

**Owner:** who's accountable. (default: Joaquin)
```

Keep it terse. Three lines per field max. The point is *why*, not exhaustive minutes.

---

## 2026-04-22 — Telegram credential always "Workflow Interview Bot"

**Decision:** Every Telegram node across every workflow uses the credential named `Workflow Interview Bot`. Never reassign, never create per-workflow Telegram creds.

**Why:** n8n auto-rebinds credentials by ID, not name. If you create a second Telegram cred and a workflow gets reimported or duplicated, n8n silently picks whichever cred sorts first — leading to messages going to the wrong bot/chat. One canonical cred = no ambiguity.

**Alternatives considered:** Per-workflow creds (rejected — fragile under copy/import). Per-bot creds (rejected — overhead for marginal isolation).

**Owner:** Joaquin

---

## 2026-04-26 — Anthropic API via HTTP Request node, not the dedicated Anthropic node

**Decision:** All Claude calls in n8n workflows use a `HTTP Request` node (typeVersion 4.2) hitting `api.anthropic.com/v1/messages` with HTTP Header Auth, *not* the dedicated Anthropic node.

**Why:** Established pattern from the LinkedIn engagement bot. Gives us full control over `model`, `max_tokens`, `system`, tool definitions, and streaming. The dedicated node lags behind API features and hides params behind operation/resource discriminators we don't need.

**Alternatives considered:** Dedicated Anthropic node (rejected — abstraction tax, slower to update, harder to debug).

**Owner:** Joaquin

---

## 2026-04-26 — Cold-Call pipeline split: Workflow A (Drive Trigger) + A2 (Webhook Trigger)

**Decision:** Production transcript-analyzer is two workflows with identical logic but different triggers. A fires on Drive `fileCreated`; A2 fires on Webhook POST `/cold-call-backfill`.

**Why:** Drive-Trigger workflows are not callable from MCP (no manual execute). We need backfill + autonomous testing — A2 lets us run the same code via `execute_workflow` with body params (`file_id`, `limit`, `force`). Mirroring this pattern is now standard for any prod workflow we want to test/backfill from outside n8n's UI.

**Alternatives considered:** Single workflow with composite trigger (rejected — n8n doesn't cleanly support multi-trigger to single execution path with shared state). Manual UI execution (rejected — kills MCP autonomy).

**Owner:** Joaquin

---

## 2026-04-26 — Audio→Transcript handled by separate Workflow C (Gemini), not inlined

**Decision:** Audio files land in a dedicated "Audiofiles Training" Drive folder. Workflow C transcribes via Gemini 2.5 Flash and writes `.txt` to a separate "Transcripts" folder, which then triggers Workflow A.

**Why:** Two reasons. (1) Workflow A's trigger is Drive `fileCreated` on the Transcripts folder — keeps it simple and idempotent. (2) Re-transcription is a different concern from re-classification; separating them lets us re-run either independently. (3) Gemini 2.5 Flash is the cheapest decent option for Schweizerdeutsch ($0.001/min) — different model than Claude (used downstream for classification).

**Alternatives considered:** Inline Gemini call inside Workflow A (rejected — couples two failure modes, harder to backfill). OpenAI Whisper (rejected — worse on Schwizerdütsch).

**Owner:** Joaquin

---

## 2026-04-26 — Notion getAll: always `simple: false` and `returnAll: true`

**Decision:** Every Notion `getAll` operation in any workflow sets `simple: false` and `returnAll: true`.

**Why:** `simple: true` returns flattened format (`property_firma`) — incompatible with how every other Notion node in n8n expects properties shaped (`properties.Firma.rich_text[0].plain_text`). `returnAll: false` silently caps at 100 rows even with `limit: 200` set (Notion API page size). Both burned us during the Cold-Call pipeline build.

**Alternatives considered:** Document the gotcha and let each workflow set it (rejected — too easy to forget).

**Owner:** Joaquin

---

## 2026-05-02 — LinkedIn Engagement Bot: full n8n architecture, Render endpoints kept as backup

**Decision:** The LinkedIn bot runs end-to-end inside n8n. Voice prompt is embedded in an n8n Code node. The Render `/api/linkedin/*` endpoints still exist (smoke-tested in Phase 1) but the Telegram bot does not call them in production.

**Why:** Originally the bot was Telegram → Render API → n8n. Cutting Render out of the hot path removes a deploy step, an API key (`PDF_API_KEY`), and a network hop per message. Repo file `prompts/linkedin_voice.md` stays as the canonical reviewable source — n8n Code-node embedding is a copy that gets refreshed when the prompt changes.

**Alternatives considered:** Stay on Render (rejected — extra ops surface for no gain). Drop Render entirely (rejected — keep as Phase-1 fallback in case n8n cloud has an outage).

**Owner:** Joaquin

---

## 2026-05-09 — Lead Scraper v2: Notion-queue + Baden epicenter + dedup

**Decision:** Refactored the manual single-term lead scraper (`kolnAPK0JyR5SxL8`) into a daily-cron pipeline that pulls Pending rows from a new Notion "Scraping Queue" DB, dedups Apify Google Maps results against existing Lead-DB by `placeId`, and writes only new leads. Cities are pre-seeded sorted by km from Baden 5400 (epicenter, T1-T3 = 24 rows). Default search-term list is 20 backoffice-heavy KMU categories (Immobilien, Treuhand, Anwaltskanzlei, etc.) — explicitly NOT walk-in retail or trades.

**Why:** Bucket: more customers. Metric: weekly net-new leads added (post-dedup) → calls/week → bookings. The old scraper had two failure modes blocking the 1000-call-by-2026-05-16 push: (1) every run re-added the same leads, polluting the DB and burning Cold-Call agent on already-tried numbers; (2) hardcoded `["Immobilien"]` literal-match returned <30% of the actual KMUs in any region. Notion-queue gives the user single-pane control over "what gets scraped next" without opening n8n; epicenter ordering matches the walk-in/proximity preference Joaquin called out explicitly. ICP whitelist (no Coiffeur/Bäckerei/etc.) was a separate rule he added during Phase-1 confirmation — those have no automation pain and would just add LCV-zero rows.

**Alternatives considered:**
- Rebuild in trigger.dev (rejected — would add days of yak shaving + ops surface fragmentation right when the May-16 deadline matters most; n8n is already the home for every other workflow).
- Auto-generate (location × term) cartesian product without a queue (rejected — no per-run cap, no audit trail of what's been done, can't reorder priorities visually).
- Per-item Notion `databasePage GET` for dedup (rejected — N API calls per scrape, hits Notion rate limit). Bulk fetch + in-memory `Set` is one call, scales fine to 100k+ leads.
- Hardcode KMU terms in a Python config file (rejected — wanted the term list visible/editable in the workflow itself for fast iteration).

**Owner:** Joaquin

---

## 2026-05-10 — Web interview bot: process-map narrative + sidebar uploads + Notion payoff

**Decision:** Restructured the deployed web interview bot at `automatisierbar-interview-bot.onrender.com` from a context → categorical-Q&A → ROI flow into a context → **process-map** → Q&A → ROI flow with a persistent sidebar (file uploads + free-text notes). On completion, the lead's Notion page now auto-gets a Mermaid flowchart of the captured process, a collapsible step table, and the Claude Code build prompt as a markdown code block — copy-paste from Notion straight into Claude Code with no round-trip back to the web app. New backend endpoints: `POST/GET …/process_map`, `POST/DELETE …/attachment`, `PATCH …/extras`. New file: `tools/file_extract.py` (Excel/CSV via pandas+openpyxl, PDF via PyMuPDF, images via Claude vision, text raw). KPI bucket: less-cost; metric: zero-followup rate ≥ 80% on first 3 post-redesign prod interviews.

**Why:** Tej review of the prior bot: "viel zu wenig Info für einen Deep-Dive — du weisst nach dem Fragebogen nicht genau wie der Prozess abläuft." The categorical 7-element checklist (trigger/services/data/logic/output/errors/volume) lets the LLM mark "complete" without ever capturing the actual A→Z step sequence (who → does what → in which tool → with what data). Build phase then has to reverse-engineer the narrative — exactly the cycle the bot was supposed to eliminate. Forcing a guided-table walkthrough up front anchors every later detail question to a concrete step ("In Schritt 3 — welches Format hat die Excel?"), and the file-upload sidebar finally lets prospects hand over their actual sheet/screenshot/SOP instead of describing them in prose. Notion payoff means the developer (or Claude Code) starts from a self-contained briefing — visual flow + structured data + ready-to-paste prompt — without re-opening the interview app. Andere-escape rule (every choice question gets a free-text fallback) addresses the second Tej complaint: "nicht immer Multiple Choice, sondern immer eine Other-Option."

**Alternatives considered:**
- Tear out `_SYSTEM_EVALUATE_CONTEXT` entirely and rebuild around process-first capture (rejected — bigger blast radius, would re-test every existing flow path; insertion phase keeps the categorical questions as the technical-detail layer that *follows* the narrative).
- Keep flow, only deepen prompts (rejected — Tej's complaint isn't about prompt depth but about the LLM not knowing the process narrative existed; needed structural capture, not better prompting).
- Telegram-bot extension (rejected — Tej's "side panel for extra info, drag-drop file upload, always-available free text" specifically pointed at richer UI than chat; web app already exists).
- Sidebar pre-session staging (deferred — would require localStorage→server migration on session start; current "sidebar locks until first context submit" handles 95% of cases).
- Hard-delete payoff if it already exists, then re-write (rejected — Notion API archives are heavy + irreversible; idempotency = skip write if heading already present, operator clears manually if needed).
- Mermaid via LLM call (rejected — wasteful; deterministic generator from process_map rows is cheaper, faster, and produces consistent output).

**Owner:** Joaquin

---

## 2026-05-10 — Lead-DB cleanup as two-step button flow with AI judgment + Notion archive

**Decision:** Built two new n8n workflows — `Lead Cleanup — Preview` (`vHiLceheTFzyTj92`) and `Lead Cleanup — Confirm` (`e5q3mlrYzrGkltCI`) — both webhook-triggered from Notion buttons on a dedicated `Lead Ops — Cleanup` page. Preview AI-judges every untouched lead (Pipeline Stage = Problem Interview, no Outreach, no Interview, not flagged Do-Not-Remove) via Claude Haiku 4.5 batch call, writes `Cleanup Status = Pending Removal` + `Cleanup Reason` on non-ICP rows. Confirm archives every still-flagged row via PATCH to Notion's archive endpoint. Tied to the **less-cost** bucket and **cold-call connect-to-qualified-conversation rate** metric.

**Why:** Pre-1000-call push (deadline 2026-05-16), the Lead-DB had legacy non-ICP rows from before the scraper's backoffice whitelist landed (Coiffeur, Restaurant, Bäckerei, single-person trades). Calling them wastes time. Branche is mostly empty pre-call, so rule-based filters fail — needed AI judgment from name + website. Two-step + manual review-in-Notion + Notion-archive (not delete) gives multiple safety layers: operator can un-flag false positives between Preview and Confirm, and archived rows are restorable from Notion trash for 30 days.

**Alternatives considered:**
- Reuse the existing `Suggested Action` / `Fit Reasoning` properties (rejected — they're already populated by the post-call Lead Fit Scorer, mixing semantics would obscure both workflows). Adding 3 dedicated properties (`Cleanup Status`, `Cleanup Reason`, `Do Not Remove`) keeps the cleanup flow self-contained.
- Hard-delete instead of archive (rejected — no recovery path. Notion archive's 30-day trash window is the safety net.)
- Single-step button with Telegram halt-and-poll for confirmation (rejected — review-in-Notion is more thorough than yes/no over Telegram. Operator can scroll through all flagged rows, judge edge cases, un-flag specific ones.)
- Schedule-based daily cleanup (rejected — phase 1 needs human-in-the-loop. Promote to scheduled later if trust is established.)

**Owner:** Joaquin
