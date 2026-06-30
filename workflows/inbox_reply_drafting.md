---
autonomy-level: L2
bike-method-phase: 1
kpi-bucket: more-customers
kpi-metric: median response time to inbound appointment/client mail (faster, more consistent replies → fewer dropped leads); % of inbound business mail with a ready draft waiting
---

# Inbox Auto-Reply Drafting (joaquin@automatisierbar.ch)

Removes the manual loop of pasting an inbound email into Claude, copying the answer back,
editing, and sending. Every **business-relevant** email arriving at
`joaquin@automatisierbar.ch` gets a ready-to-edit **reply draft** placed in the Infomaniak
Drafts folder, threaded under the original. Joaquin opens his normal mail app, checks/edits,
and hits send. **Nothing is sent automatically** — the draft is the approval surface, exactly
like the `/walkinmail` flow.

L2 by design (AI drafts, human reviews + edits before send). Phase 1 on rollout: watch every
output, then advance the cron only after a clean week.

## The five process elements

- **Trigger** — a VPS cron (`tools/scheduled/inbox-reply-drafter.sh`) runs every ~10 min and
  polls the INBOX for mail received since the last run.
- **Data sources** — the incoming email; the Leads DB (`31cbebb0-c2f9-8047-9e9f-fc59851f8a34`,
  matched on sender email); the Termine DB (`COCKPIT_APPOINTMENTS_DB_ID`) for any existing
  appointment; the Cockpit `/api/book/slots` endpoint for live free slots; the operator's
  Infomaniak signature.
- **Transformations** — classify relevance + category + language (Claude Haiku); gather CRM /
  calendar context; draft a reply in Joaquin's voice (Claude Sonnet).
- **Decision points** — business-relevant? already replied to / already drafted? an
  appointment ask → fetch slots? confident draft → append.
- **Destination** — a threaded reply draft (`In-Reply-To` / `References`, `Re:` subject) in
  the Infomaniak Drafts folder. A `.tmp/` run log; optional operator-Telegram summary.

## Tools (WAT layer 3)

| File | Role |
|---|---|
| `tools/inbox_reply_drafter.py` | Orchestrator: poll → skip → dedup → classify → context → draft → append. |
| `tools/scheduled/inbox-reply-drafter.sh` | Cron wrapper (sources `/etc/cockpit/env`, venv python, logs to `.tmp/`, always exit 0). |
| `tools/claude_client.py` | `classify_inbox_email()` (Haiku) + `draft_inbox_reply()` (Sonnet). Both fail safe → no draft. |
| `tools/walkin/infomaniak_draft.py` | `build_message()` (extended with `in_reply_to`/`references`) + IMAP APPEND + folder detection. |
| `tools/walkin/infomaniak_signature.py` | Real signature, auto-appended. |
| `tools/notion_session.py` | `find_lead_by_email_or_phone()` + `list_appointments()` for context (read-only). |
| `tools/test_inbox_reply_drafter.py` | Offline tests (parsing, skip rules, threading, slots, state, dedup). |

## How a draft is built (per message)

1. **Read** INBOX with `BODY.PEEK` and a `readonly` select — messages stay **unread**.
2. **Pre-LLM skip** (cheap): own/team domain (`@automatisierbar.ch`), `no-reply`/`mailer-daemon`
   senders, `Auto-Submitted`, `List-Unsubscribe` / `List-Id` (newsletters), `Precedence: bulk`.
3. **Dedup**: skip a `Message-ID` already in the local state file, or already referenced by an
   `In-Reply-To`/`References` in the **Sent** or **Drafts** folders (already answered or drafted).
4. **Classify** (Haiku) → `{business_relevant, category, reply_language, confidence}`. Non-business
   mail is dropped (and its id recorded so it isn't re-classified every run).
5. **Context**: match the sender to a lead; find any existing appointment; for
   `appointment_booking`/`appointment_reschedule`, pull 2-3 real free slots from `/api/book/slots`.
6. **Draft** (Sonnet): mirrors the sender's language (German Hochdeutsch + Sie by default), warm
   and not salesy, **no em-dashes**, no buzzwords, no prices, ends with the closing salutation
   (signature auto-appends). Appointment mails weave in the concrete slots + the booking link.
7. **Append** a threaded draft to the Drafts folder. `To:` = `Reply-To` or `From`. No auto-Cc
   (these are Joaquin's personal-inbox conversations).

## Edge cases & guarantees

- **Never sends.** The orchestrator imports `imaplib` only, never `smtplib` / the Mail-API send
  path. By construction it can only deposit a draft.
- **Idempotent.** State file `.tmp/inbox-reply-drafter-state.json` (pruned to 30 days) + the
  Sent/Drafts `In-Reply-To` scan prevent double-drafting and re-answering.
- **Fail-safe.** Missing IMAP creds, Notion key, or Anthropic key → logged no-op, never a crash.
  A classify/draft API error → that message is skipped, not drafted (errs toward silence).
- **Bounded cost.** `--max-scan` caps classify calls/run; `--max-per-run` caps drafts/run.
- **Threading correctness.** `In-Reply-To` = original `Message-ID`; `References` = original chain
  + `Message-ID`; subject normalized to a single `Re:`.

## Environment

In `.env` (local dev) / `/etc/cockpit/env` (VPS):

```
# REQUIRED — joaquin@ mailbox app-password (the cockpit's INFOMANIAK_IMAP_* point at info@)
JOAQUIN_IMAP_USER=joaquin@automatisierbar.ch
JOAQUIN_IMAP_PASSWORD=<infomaniak app-password>     # NOT the normal login password
JOAQUIN_IMAP_HOST=mail.infomaniak.com               # optional, this is the default
JOAQUIN_IMAP_PORT=993                               # optional, this is the default
# Context + drafting (already present on the VPS for the cockpit)
NOTION_API_KEY=...
COCKPIT_APPOINTMENTS_DB_ID=...                       # Termine DB; without it, no appt context
ANTHROPIC_API_KEY=...
# Optional
BOOKING_SLOTS_URL=http://127.0.0.1:8082/api/book/slots   # default
INFOMANIAK_MAIL_TOKEN=...                            # signature fetch (reused from cockpit)
INBOX_DRAFTER_NOTIFY=1                               # opt-in operator-Telegram summary
```

`INFOMANIAK_MAIL_TOKEN` is reused for the signature (mailbox `joaquin`, hosting `985192`); if it
lacks joaquin-mailbox scope the cached `tools/walkin/signature.*` is used instead.

## Rollout (Bike Method, phase 1 → cron)

1. **Offline tests** — `python3 tools/test_inbox_reply_drafter.py` and
   `python3 tools/walkin/infomaniak_draft.py --selftest` (covers the new threading headers).
2. **Dry-run** — `python3 tools/inbox_reply_drafter.py --dry-run --verbose --max-scan 5`.
   Reads the real inbox + makes a few Claude calls (paid), writes nothing. Check classification,
   threading targets, language, voice, and slot proposals. (Halt-to-Telegram first per the
   halt-before-acting policy: this is the first real-inbox + paid-API run.)
3. **Supervised live** — drop `--dry-run`, `--max-per-run 2`. Open the mail app; confirm each
   draft is threaded under the right email, addressed correctly, signature attached, voice right.
4. **Idempotency** — re-run immediately; expect zero new drafts.
5. **Cron** — install the every-10-min crontab (below) only after a clean supervised week.

## Deployment (VPS)

```bash
# redeploy after pushing to feat/cockpit-booking
ssh cockpit-vps 'cd /srv/cockpit/app && git fetch -q origin feat/cockpit-booking && \
  git reset -q --hard origin/feat/cockpit-booking && chown -R paperclip:paperclip /srv/cockpit && \
  systemctl restart cockpit'
# add JOAQUIN_IMAP_* to /etc/cockpit/env (operator action)
# install cron (runs as paperclip):
#   CRON_TZ=Europe/Zurich
#   */10 * * * * /srv/cockpit/app/tools/scheduled/inbox-reply-drafter.sh
# logs: /srv/cockpit/app/.tmp/inbox-reply-drafter.log (+ .err)
```

## Learnings / quirks

- The VPS `INFOMANIAK_IMAP_*` belong to **info@** (booking confirmations). Reading joaquin@'s
  inbox needs a **separate** app-password → `JOAQUIN_IMAP_*`. Do not reuse the info@ creds.
- `readonly` INBOX select + `BODY.PEEK` is essential — a normal fetch would mark mail read.
- The Sent/Drafts `In-Reply-To` scan is the single mechanism that covers both "already answered"
  and "draft already exists" — no separate Drafts-content dedup needed.
