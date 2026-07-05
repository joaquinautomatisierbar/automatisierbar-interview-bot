---
title: Mail-Sync CRM Logger (inbound + outbound mail → Hub LeadMail thread)
autonomy-level: L3   # logging + tagging auto; risky lead-state changes are L2 (human confirm)
bike-method-phase: 1 # dry-run → supervised → cron; risky deltas stay human-confirmed indefinitely
kpi-bucket: more-customers + less-cost
kpi-metric: % of inbound lead replies logged+tagged in the Hub without manual entry; operator min/week saved on mail triage
last_updated: 2026-07-05
---

# Mail-Sync CRM Logger

Detects every email a lead/client sends us (and every mail we send them), classifies its intent,
and logs it onto that lead's **Mailverkehr** thread in the Automatisierbar Hub with a tag, so the
operator sees the whole exchange in one place instead of copy-pasting/summarizing from inboxes.
Inbound replies also nudge the CRM: a follow-up date on interest/questions (safe, auto), a
one-tap-confirm "mark lost" on an Absage (risky, never auto). Nothing is ever sent.

## The five process elements

- **Trigger** — VPS cron every ~5 min (`tools/scheduled/mail-sync.sh`), + a one-time 2-week backfill.
- **Data sources** — INBOX + Sent of the 5 team mailboxes over IMAP (read-only, `BODY.PEEK`, never
  marks \Seen), across `joaquin / tej / nicolas / patrik / info` (`team_mailboxes.py`).
- **Transformations** — parse headers/body → skip bulk/self/auto (inbound) / internal-only (outbound)
  → dedup on the per-mailbox ledger → classify intent (Claude Haiku) → build the LeadMail POST body.
- **Decision points** — direction (incoming vs outgoing) picks the tag set + the counterparty address;
  the Hub resolves the lead (thread → email → parked) and maps the intent tag to a CRM-state action
  (safe → apply; risky → stage for confirm; none → log only).
- **Destination** — the Hub via `POST /api/v1/leadmails` (X-API-Key). The Hub stores the tagged
  LeadMail, applies safe deltas through the audited `record.update` (which writes back to Notion),
  and stages risky ones. Nothing writes to a mailbox.

## Architecture

```
5 mailboxes (INBOX+Sent) ─IMAP RO─▶ tools/mail_sync (cockpit VPS cron)
   parse → skip → dedup → classify(Haiku) → POST /api/v1/leadmails (X-API-Key)
        ▼
   Hub (automatisierbar-hub): LeadMailService.ingest
     match: thread(inReplyTo/references) → email(leadCrm.dedup) → parked(recordId null)
     safe delta → record.update → Notion writeback ; risky (Absage) → suggestedAction pending
        ▼
   Hub lead page → lead-mail-thread.tsx (tagged thread + one-tap confirm) ; Postfach = parked review
```

The mail thread lives in the **Hub Postgres DB** (a growing per-message thread doesn't belong in
Notion). Lead-state changes ride `record.update`, so the writeback-eligible fields (nextActionDate,
lostReason, …) propagate to the Notion Leads DB automatically.

## Components

**cockpit repo (`tools/mail_sync/`):**
- `imap_read.py` — reuses `inbox_reply_drafter` (parse_incoming/should_skip/_connect_inbox/_find_folder);
  adds To/Cc extraction, Sent detection, `should_skip_outbound`, a read-only INBOX/Sent iterator.
- `taxonomy.py` — the intent-tag keys + labels + `normalize_intent` (fail-safe validation).
- `classify.py` — `classify_mail_intent` (Haiku, per-direction prompt, fails safe to the default tag).
- `payload.py` — `build_leadmail_payload` + stable `external_message_id` (Message-ID or sha1 fallback).
- `state.py` — per-mailbox dedup ledger (`.tmp/mail-sync-state.<mailbox>.json`).
- `hub_client.py` — `post_leadmail` with retry (5xx/429/network retry, 4xx terminal).
- `sync.py` — the worker + CLI. `tools/scheduled/mail-sync.sh` — cron entrypoint.
- Tests: `tests/test_mail_sync.py` (23, offline).

**Hub repo (`automatisierbar-hub`):**
- `packages/db` migration `…_leadmail` + `model LeadMail` (child of Record, nullable recordId = parking,
  unique externalMessageId = dedup).
- `packages/shared/src/mail-intent.ts` — the SAME tag keys as `taxonomy.py` + the intent→action map.
- `apps/api/src/services/leadmail/` — service + REST schema; router `lead-mail.router.ts`; REST route
  `POST /api/v1/leadmails` (+ scope `leadmail:write`); wired into `services/index.ts` + `deps.ts` + `router.ts`.
- `apps/web/src/components/leads/lead-mail-thread.tsx` — the Mailverkehr section in `lead-detail.tsx`.

## Intent taxonomy (keys shared verbatim across Python + Hub)

- Outgoing: `out_erstkontakt out_followup out_terminvorschlag out_angebot out_rueckfrage_beantwortet out_reaktivierung`
- Incoming: `in_interesse in_rueckfrage in_preis in_absage in_spaeter in_abwesenheit in_sonstiges`
- Incoming → action: interesse/rueckfrage/preis → set nextActionDate +2d (safe); spaeter → +30d (safe);
  **absage → mark lost (risky, confirm)**; abwesenheit/sonstiges → none. Safe deltas only fill an EMPTY
  nextActionDate (never clobber an operator-set follow-up).

## Deploy runbook

**Hub (os.automatisierbar.ch):** land the leadMail files on `main` (coordinate with any concurrent
Hub work in the shared checkout), push, then on the VPS: `bash infra/deploy.sh` (pre-deploy backup →
build → `migrate:deploy` → restart). Verify `GET /trpc/health` + that the LeadMail table exists.

**Mint the Hub API key** (leadmail:write) via the admin `apiKey` tRPC router (or a tsx one-off calling
`apiKey.create({ name, actorUserId: <automation user>, scopes: ['leadmail:write'] })`). Copy the plaintext.

**cockpit (VPS `/srv/cockpit/app`):**
1. `/etc/cockpit/env`: add `HUB_API_BASE=https://os.automatisierbar.ch` + `HUB_API_KEY=<minted key>`
   (IMAP creds + ANTHROPIC_API_KEY already present). `systemctl restart cockpit` not required (cron tool).
2. Deploy code — the VPS `/srv/cockpit/app` has UNCOMMITTED prod work + divergent git, so DO NOT
   `git reset`/blind-pull (see memory `reference_cockpit_vps_deploy`). All mail_sync files are NEW,
   so scp them additively: backup, then
   `scp -r tools/mail_sync tools/scheduled/mail-sync.sh cockpit-vps:/srv/cockpit/app/tools/`,
   `chown -R paperclip:paperclip /srv/cockpit`, and `python -m py_compile tools/mail_sync/*.py` to verify.
3. `chmod +x /srv/cockpit/app/tools/scheduled/mail-sync.sh`; `crontab -u paperclip -e` → add
   `CRON_TZ=Europe/Zurich` + `*/5 * * * * /srv/cockpit/app/tools/scheduled/mail-sync.sh`.

**Backfill (last 2 weeks):** dry-run first, then live.
```
# preview (no Hub writes; Haiku spend):
python3 tools/mail_sync/sync.py --mailbox all --dry-run --verbose
# structural preview (no API, no writes):
python3 tools/mail_sync/sync.py --mailbox all --dry-run --no-llm --verbose
# live:
python3 tools/mail_sync/sync.py --mailbox all
```

## Verification (end-to-end)

1. `tests/test_mail_sync.py` green (offline).
2. Dry-run against a real mailbox shows correct counterparty + tags (done: joaquin Sent, internal-only skipped).
3. After deploy: POST a sample body to `/api/v1/leadmails` (201 new / 200 dedup); open a Hub lead with mail
   → the thread shows in/out mails in order with tags; an Absage shows a pending confirm (not an auto-flip);
   confirming sets lostReason (visible in Details + written back to Notion); an unknown sender lands in Postfach.
4. Re-run the worker → no duplicate rows (unique externalMessageId), no re-classification of processed ids.

## Edge cases / notes

- Never sends: imports imaplib only. Read-only INBOX/Sent. Missing creds / errors → logged no-op.
- Idempotent: local ledger avoids re-classification; the Hub unique externalMessageId avoids duplicate rows.
- Match-key sparsity (leads without emails): mitigated by thread linkage; genuine correspondence carries an
  address, and unmatched mail is parked (never dropped). Domain-fallback + email-backfill = a later enhancement.
- Liveness: the thread polls every 30s (socket.io realtime = a later enhancement).
- The old free-text "📧 Mail" quick-capture on the lead page stays as a manual fallback.
- **VPS mailbox routing:** `INFOMANIAK_IMAP_*` on the cockpit VPS points at joaquin@, so the `info`
  mailbox falls back to joaquin's box (re-scans it, deduped harmlessly at the Hub) and info@ is not
  scanned separately. To cover info@, set `INFO_IMAP_USER`/`INFO_IMAP_PASSWORD` in /etc/cockpit/env.
- **Do NOT `chmod 600 /etc/cockpit/env`** — it must be 640 root:paperclip so the paperclip cron can read it.
- Manual runs: `sudo -u paperclip bash tools/scheduled/mail-sync-run.sh <sync.py args>` (parses env correctly).

## Status
LIVE in prod 2026-07-05: Hub 36316b0 on os.automatisierbar.ch; cockpit cron `*/5` on the VPS; 2-week
backfill = 56 mails (30 matched / 26 parked), 0 dups, 0 failures.
