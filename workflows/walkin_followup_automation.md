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
  lead when the chosen **Nächster Schritt** is one of the three email-warranting options
  (`E-Mail-Entwurf erstellen` [default] · `Wir melden uns` · `Follow-up bis Datum`; the canonical
  set is `walkin_capture.DRAFTING_NEXT_ACTIONS`). It writes the Notion lead and enqueues one job
  file. A cron (`tools/scheduled/walkin-draft-worker.sh`, every ~3 min) claims and processes the
  queue. Quality over speed: no per-run latency budget rushes the LLM.
- **Data sources** — the queued job (entering person, Cc choice, lead fields, notes); the live
  **Follow-Up Email Script + Pitch-Bibliothek** from Notion (`388bebb0…`, cached fallback); the
  entering person's **Infomaniak signature** (Mail API, per-mailbox cache); the web (server-side
  `web_search`) to find/verify the contact email when the form has none.
- **Transformations** — resolve the recipient email (form value, else web search → confident /
  best-guess); classify the sector + pick the pain-hypothesis; draft the Hormozi-framed German
  email (`claude_client.draft_walkin_followup`), whose CTA + tone are shaped by the chosen next
  step (standard = A/B-time + booking link; `Wir melden uns` = we initiate, no self-book ask;
  `Follow-up bis Datum` = time-anchored around the date); build the removable context block
  (`walkin_capture.build_context_block`); assemble the MIME with the person's signature + chosen Cc.
- **Decision points** — **ICP filter**: clearly non-back-office (Coiffeur/Restaurant/trades) →
  skip, no draft. **Confident email** → An-field pre-filled; **best-guess** → An-field left empty
  (never a guessed recipient). **Next step in the draft set** (E-Mail-Entwurf / Wir melden uns /
  Follow-up bis Datum) → draft, shaped by that choice; **Kein Interesse / keine Zeit** or
  **Sonstiges** → record the intent on the lead, draft nothing. **No mailbox creds** → retry, then
  `failed` + one operator Telegram ping.
- **Destination** — an IMAP `\Draft` in the entering person's `Drafts` folder (never SMTP → cannot
  send), plus a `✉️ Walk-in Entwurf erstellt` note on the lead page. The chosen next step +
  follow-up date are also written to the real Leads-DB props `Nächster Schritt` (select) /
  `Follow-up Datum` (date). The lead itself was created at entry and syncs to the Hub via the Hub's
  Notion sync.

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

1. ✅ **DONE (2026-07-05)** — **IMAP application passwords** for all five mailboxes are set in
   `/etc/cockpit/env` (`JOAQUIN_IMAP_*`, `INFOMANIAK_IMAP_*`, `NICO_IMAP_*`, `TEJ_IMAP_*`,
   `PATRIK_IMAP_*`). A mailbox with no creds → the job goes to `failed` after retries + one Telegram
   ping; nothing crashes.
2. **Signatures** configured in Infomaniak for each mailbox (verify nicolas/tej/patrik are set —
   otherwise their drafts ship without a signature). The existing hosting-scoped
   `INFOMANIAK_MAIL_TOKEN` should read them all; if scope is narrower, add per-mailbox
   `{PREFIX}_MAIL_TOKEN`. Verify with `python3 tools/walkin/infomaniak_signature.py --show --mailbox tej`.
3. ✅ **DONE (2026-07-05)** — cron installed: `*/3 * * * * /srv/cockpit/app/tools/scheduled/walkin-draft-worker.sh`.
4. ✅ **DONE (2026-07-05, Phase B)** — the real `Nächster Schritt` (select) / `Follow-up Datum` (date)
   properties now exist on the live Leads DB and are written on entry via `build_lead_fields`. The
   note-block line is kept as a redundant human-readable trail.

## Verification / rollout (Bike Method Phase 1)

- **Dry-run any time:** `python3 tools/walkin_draft_worker.py --dry-run --sample-lead "Muster Treuhand AG"`
  (fixtures: Muster / Alpina Immobilien / Coiffeur Belle [ICP-skip] / Codes SA / Kanzlei Steiner).
- **Supervised go-live:** one real walk-in per team member → confirm the draft lands in the RIGHT
  mailbox with the RIGHT signature + the removable context block, before trusting the cron.
- **Learnings:** on the dev Mac, mailbox creds may be absent, so the worker draws the draft but the
  IMAP push reports `no_credentials:<addr>` and the job goes to `failed` — expected locally; on the
  prod VPS all five mailboxes have creds (blocker 1).
- **Next step shapes the draft (2026-07-05):** the `Nächster Schritt` choice is no longer just a
  draft/no-draft gate. Three options draft (`DRAFTING_NEXT_ACTIONS`) and steer CTA + tone via
  `_SYSTEM_WALKIN_DRAFT`; `Kein Interesse` / `Sonstiges` still draft nothing. Verified live: default
  asks two slots + booking link; `Wir melden uns` announces we initiate (no slot ask); `Follow-up
  bis Datum` anchors the slots around the target date. To tune wording, use `/walkinmail-improvement`.
