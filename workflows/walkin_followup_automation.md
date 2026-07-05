---
autonomy-level: L2
bike-method-phase: 1
kpi-bucket: more-customers
kpi-metric: walk-in follow-up reply rate + time-to-draft (draft ready within minutes of the visit, authored as the person who was there → higher reply rate, no manual drafting step)
---

# Walk-in Follow-up Automation (auto-draft into each person's mailbox)

Removes the manual `/walkinmail` step. The moment a team member enters a walk-in lead in the field
PWA, a server-side pipeline drafts a same-quality German follow-up email and deposits it as an
**openable draft in that person's own Infomaniak mailbox** (Nico's entry → `nicolas@` Drafts),
authored as them, with their signature and a removable internal context block. Nothing is sent —
the operator opens the draft, deletes the context block, checks the An-field, and hits send.

L2 by design (AI drafts, human reviews + edits before send). Phase 1 on rollout: watch every output
per person, advance the cron cadence only after a clean week. Supersedes the retired `/walkinmail`
and `/walkinleadsconvert` skills and the 💡-callout. To improve the drafts, use
`/walkinmail-improvement`.

## The five process elements

- **Trigger** — `POST /api/walkin/lead` (field PWA `static/walkin.html`) fires on each captured
  lead when the chosen **Nächster Schritt** is `E-Mail-Entwurf erstellen` (the default). It writes
  the Notion lead and enqueues one job file. A cron (`tools/scheduled/walkin-draft-worker.sh`, every
  ~3 min) claims and processes the queue. Quality over speed: no per-run latency budget rushes the LLM.
- **Data sources** — the queued job (entering person, Cc choice, lead fields, notes); the live
  **Follow-Up Email Script + Pitch-Bibliothek** from Notion (`388bebb0…`, cached fallback); the
  entering person's **Infomaniak signature** (Mail API, per-mailbox cache); the web (server-side
  `web_search`) to find/verify the contact email when the form has none.
- **Transformations** — resolve the recipient email (form value, else web search → confident /
  best-guess); classify the sector + pick the pain-hypothesis; draft the Hormozi-framed German
  email (`claude_client.draft_walkin_followup`); build the removable context block
  (`walkin_capture.build_context_block`); assemble the MIME with the person's signature + chosen Cc.
- **Decision points** — **ICP filter**: clearly non-back-office (Coiffeur/Restaurant/trades) →
  skip, no draft. **Confident email** → An-field pre-filled; **best-guess** → An-field left empty
  (never a guessed recipient). **Next step ≠ E-Mail-Entwurf** → record the intent on the lead, draft
  nothing (the follow-up engine is deferred to the CRM). **No mailbox creds** → retry, then `failed`
  + one operator Telegram ping.
- **Destination** — an IMAP `\Draft` in the entering person's `Drafts` folder (never SMTP → cannot
  send), plus a `✉️ Walk-in Entwurf erstellt` note on the lead page. The lead itself was created at
  entry and syncs to the Hub via the Hub's Notion sync.

## Components

| Piece | File |
|---|---|
| Mailbox routing (name → address / creds / signature) | `tools/team_mailboxes.py` |
| Draft generation + email resolution | `tools/claude_client.py` (`draft_walkin_followup`, `resolve_walkin_contact`, `_SYSTEM_WALKIN_DRAFT`) |
| Follow-Up Script live+cache+fallback | `tools/walkin/final_script_cache.py` (+ `final_script_fallback.md`) |
| Job queue (flock, atomic) | `tools/walkin_draft_queue.py` |
| Worker | `tools/walkin_draft_worker.py` + `tools/scheduled/walkin-draft-worker.sh` |
| Context block + per-mailbox signature | `tools/walkin/infomaniak_draft.py`, `tools/walkin/infomaniak_signature.py` |
| Entry endpoint | `api.py` `walkin_create_lead` |
| Form (Cc + Nächster Schritt) | `static/walkin.html` |

## Operator blockers (credential UIs — the build degrades gracefully until these exist)

1. **IMAP application passwords** for `nicolas@`, `tej@`, `patrik@` (Infomaniak Manager → Mail →
   Security) → set in `/etc/cockpit/env`:
   `NICO_IMAP_USER` / `NICO_IMAP_PASSWORD`, `TEJ_IMAP_USER` / `TEJ_IMAP_PASSWORD`,
   `PATRIK_IMAP_USER` / `PATRIK_IMAP_PASSWORD`. `joaquin@` (`JOAQUIN_IMAP_*`) and `info@`
   (`INFOMANIAK_IMAP_*`) already have creds. A mailbox with no creds → the job goes to `failed`
   after retries + one Telegram ping; nothing crashes.
2. **Signatures** configured in Infomaniak for each mailbox (nicolas/tej/patrik currently have
   none → their drafts ship without a signature until set). The existing hosting-scoped
   `INFOMANIAK_MAIL_TOKEN` should read them all; if scope is narrower, add per-mailbox
   `{PREFIX}_MAIL_TOKEN`. Verify with `python3 tools/walkin/infomaniak_signature.py --show --mailbox tej`.
3. **Install the cron:** `crontab -u paperclip -e` → `*/3 * * * * /srv/cockpit/app/tools/scheduled/walkin-draft-worker.sh`.
4. **(Phase B) approval** before adding real `Nächster Schritt` / `Follow-up Datum` properties to
   the live Leads DB — until then those values live in the lead's note block.

## Verification / rollout (Bike Method Phase 1)

- **Dry-run any time:** `python3 tools/walkin_draft_worker.py --dry-run --sample-lead "Muster Treuhand AG"`
  (fixtures: Muster / Alpina Immobilien / Coiffeur Belle [ICP-skip] / Codes SA / Kanzlei Steiner).
- **Supervised go-live:** one real walk-in per team member → confirm the draft lands in the RIGHT
  mailbox with the RIGHT signature + the removable context block, before trusting the cron.
- **Learnings:** on the dev Mac, `nicolas@`/`tej@`/`patrik@` have no creds yet, so the worker draws
  the draft but the IMAP push reports `no_credentials:<addr>` and the job goes to `failed` — expected
  until the operator provisions the app-passwords above.
