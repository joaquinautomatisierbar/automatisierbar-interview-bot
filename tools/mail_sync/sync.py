#!/usr/bin/env python3
"""mail_sync/sync.py — read INBOX + Sent across the team mailboxes, classify each message's
intent, and push it to the Automatisierbar Hub as a tagged LeadMail.

Per run, per mailbox:
  1. connect read-only (BODY.PEEK => nothing is marked \\Seen)
  2. INBOX since the lookback window: drop bulk/self/no-reply/auto (should_skip), dedup on the
     local ledger, classify the counterparty's response, POST it (direction=incoming)
  3. Sent since the lookback window: drop internal-only/no-recipient (should_skip_outbound),
     dedup, classify OUR intent, POST it (direction=outgoing)
  4. mark each successfully-pushed message-id in the per-mailbox ledger (idempotent re-runs)

The Hub resolves the lead (thread -> email -> domain -> parked), dedups on externalMessageId,
and maps intentTag -> CRM-state action. This side never sends mail and never writes CRM state
directly — it reads, classifies, and forwards. Missing creds / errors degrade to a logged no-op.

The last-2-weeks BACKFILL is just this worker's normal run (default lookback = 14 days):
  python3 -m mail_sync.sync --mailbox all --dry-run --verbose     # preview classifications
  python3 -m mail_sync.sync --mailbox all                          # live: push to the Hub

Env (.env or /etc/cockpit/env): HUB_API_BASE, HUB_API_KEY (leadmail:write scope),
ANTHROPIC_API_KEY (classify), per-mailbox {PREFIX}_IMAP_USER/PASSWORD.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from mail_sync import imap_read, classify, payload, hub_client, taxonomy
from mail_sync import state as mstate

DEFAULT_SINCE_DAYS = 14      # the "last 2 weeks" window == the backfill window
DEFAULT_MAX_SCAN = 300       # cap classify calls per mailbox per run
_ALL = "all"


def _env(key, default=None):
    import team_mailboxes as tm
    return tm.env(key, default)


def _canonical_mailboxes(selector: str):
    """Resolve a --mailbox selector to canonical mailbox_name strings."""
    import team_mailboxes as tm
    if selector == _ALL:
        return [tm.resolve(name)["mailbox_name"] for name in tm.all_mailboxes()]
    return [tm.resolve(selector)["mailbox_name"]]


def _notify(text: str) -> None:
    """Low-noise operator ping on real failures (off unless creds present)."""
    tok, chat = _env("OPERATOR_TELEGRAM_BOT_TOKEN", ""), _env("OPERATOR_TELEGRAM_CHAT_ID", "")
    if not (tok and chat):
        return
    try:
        import requests
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": chat, "text": text, "disable_web_page_preview": True},
                      timeout=10)
    except Exception:
        pass


def _classify(direction, p, no_llm):
    if no_llm:
        return taxonomy.normalize_intent({}, direction)  # default tag, zero cost
    return classify.classify_mail_intent(
        direction=direction, subject=p.get("subject", ""), body=p.get("body_text", ""),
        from_name=p.get("from_name", ""), from_email=p.get("from_email", ""),
        to_email=p.get("to_email", ""))


def _process_folder(*, imap, folder, direction, since_str, state, counts, mailbox,
                    hub_base, hub_key, dry_run, no_llm, max_scan, verbose):
    """Read one folder, classify + push each new message. Mutates `state` and `counts`."""
    for p in imap_read.fetch_parsed_since(imap, folder, since_str):
        if counts["scanned"] >= max_scan:
            break
        mid = p.get("message_id", "")
        eid = payload.external_message_id(p, mailbox, folder)
        key = mid or eid
        if mstate.is_seen(state, key):
            counts["seen"] += 1
            continue
        if direction == "incoming":
            skip, reason = imap_read.should_skip(p)
        else:
            skip, reason = imap_read.should_skip_outbound(p)
        if skip:
            counts["skipped"] += 1
            if verbose:
                who = p.get("from_email") if direction == "incoming" else p.get("to_email")
                print(f"[skip:{reason}] {direction} {who} | {p.get('subject','')[:60]}")
            continue

        counts["scanned"] += 1
        intent = _classify(direction, p, no_llm)
        body = payload.build_leadmail_payload(
            p, direction=direction, mailbox=mailbox, folder=folder, intent=intent)
        tag = intent["intent_tag"]

        if dry_run:
            cp = body["fromEmail"] if direction == "incoming" else body["toEmail"]
            print(f"[dry:{direction}] {cp:32} {tag:26} conf={intent['confidence']:.2f} "
                  f"| {body['subject'][:56]}")
            counts["would_push"] += 1
            continue

        res = hub_client.post_leadmail(body, base_url=hub_base, api_key=hub_key)
        if res.ok:
            mstate.mark_seen(state, key)
            counts["pushed"] += 1
            if verbose:
                matched = (res.body or {}).get("matched")
                print(f"[ok:{direction}] {tag:26} matched={matched} | {body['subject'][:56]}")
        elif res.status and 400 <= res.status < 500:
            # terminal (schema/auth) — mark seen so we don't reclassify+repost a poison message
            mstate.mark_seen(state, key)
            counts["failed_terminal"] += 1
            print(f"[FAIL-terminal {res.status}] {body['subject'][:56]}: {res.body}")
        else:
            counts["failed_transient"] += 1  # leave unmarked -> retried next run
            print(f"[FAIL-transient] {body['subject'][:56]}: {res.error}")


def run(mailbox, *, dry_run=False, since_days=DEFAULT_SINCE_DAYS, max_scan=DEFAULT_MAX_SCAN,
        do_inbox=True, do_sent=True, no_llm=False, verbose=False) -> dict:
    hub_base = _env("HUB_API_BASE", "")
    hub_key = _env("HUB_API_KEY", "")
    if not dry_run and not (hub_base and hub_key):
        print("[mail-sync] HUB_API_BASE / HUB_API_KEY missing — refusing live push (use --dry-run).")
        return {"skipped": "no_hub_creds"}

    since_str = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%d-%b-%Y")
    imap, user = imap_read._connect_inbox(mailbox)
    if not imap:
        print(f"[mail-sync:{mailbox}] no IMAP connection — skipping (no-op).")
        return {"skipped": "no_imap", "mailbox": mailbox}

    state = mstate.load_state(mailbox)
    counts = {"scanned": 0, "pushed": 0, "would_push": 0, "seen": 0, "skipped": 0,
              "failed_terminal": 0, "failed_transient": 0}
    try:
        typ, lines = imap.list()
        sent_folder = imap_read.find_sent_folder(lines)
        print(f"[mail-sync:{mailbox}] user={user} sent={sent_folder!r} since={since_str} "
              f"dry_run={dry_run} no_llm={no_llm}")
        if do_inbox:
            _process_folder(imap=imap, folder="INBOX", direction="incoming", since_str=since_str,
                            state=state, counts=counts, mailbox=mailbox, hub_base=hub_base,
                            hub_key=hub_key, dry_run=dry_run, no_llm=no_llm, max_scan=max_scan,
                            verbose=verbose)
        if do_sent and sent_folder:
            _process_folder(imap=imap, folder=sent_folder, direction="outgoing", since_str=since_str,
                            state=state, counts=counts, mailbox=mailbox, hub_base=hub_base,
                            hub_key=hub_key, dry_run=dry_run, no_llm=no_llm, max_scan=max_scan,
                            verbose=verbose)
        if not dry_run:
            state["last_run"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            mstate.save_state(state, mailbox)
        summary = (f"[mail-sync:{mailbox}] pushed={counts['pushed']} would_push={counts['would_push']} "
                   f"seen={counts['seen']} skipped={counts['skipped']} scanned={counts['scanned']} "
                   f"fail(term={counts['failed_terminal']} trans={counts['failed_transient']}) "
                   f"dry_run={dry_run}")
        print(summary)
        if not dry_run and (counts["failed_terminal"] or counts["failed_transient"]):
            _notify(f"📬 Mail-Sync ({mailbox}): {counts['failed_terminal']} terminal, "
                    f"{counts['failed_transient']} transiente Fehler beim Hub-Push")
        return counts
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="Log inbound+outbound mail to the Hub as tagged LeadMails.")
    ap.add_argument("--mailbox", default=_ALL,
                    help="joaquin|tej|nico|patrik|info|all (default all)")
    ap.add_argument("--dry-run", action="store_true", help="Classify + print, no Hub writes / no state change")
    ap.add_argument("--no-llm", action="store_true", help="Skip classification (default tag) — zero-cost structural preview")
    ap.add_argument("--since-days", type=int, default=DEFAULT_SINCE_DAYS, help="Lookback window (default 14 = backfill)")
    ap.add_argument("--max-scan", type=int, default=DEFAULT_MAX_SCAN, help="Cap classify calls per mailbox per run")
    ap.add_argument("--inbox-only", action="store_true", help="Only INBOX (inbound)")
    ap.add_argument("--sent-only", action="store_true", help="Only Sent (outbound)")
    ap.add_argument("--verbose", action="store_true", help="Per-message logging")
    args = ap.parse_args()

    do_inbox = not args.sent_only
    do_sent = not args.inbox_only
    total = {"pushed": 0, "would_push": 0, "failed_terminal": 0, "failed_transient": 0}
    for mb in _canonical_mailboxes(args.mailbox):
        c = run(mb, dry_run=args.dry_run, since_days=args.since_days, max_scan=args.max_scan,
                do_inbox=do_inbox, do_sent=do_sent, no_llm=args.no_llm, verbose=args.verbose)
        for k in total:
            total[k] += c.get(k, 0)
    print(f"[mail-sync] TOTAL pushed={total['pushed']} would_push={total['would_push']} "
          f"fail(term={total['failed_terminal']} trans={total['failed_transient']})")


if __name__ == "__main__":
    main()
