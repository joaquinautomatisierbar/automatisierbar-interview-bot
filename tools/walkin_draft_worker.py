#!/usr/bin/env python3
"""walkin_draft_worker.py — the deterministic executor for the walk-in auto-draft pipeline.

Claims pending jobs from walkin_draft_queue (written by POST /api/walkin/lead), and for each:
  1. resolve the recipient email (form value, else server-side web search) — same quality as
     the retired /walkinmail skill,
  2. fetch the live Follow-Up Script + Pitch-Bibliothek (Notion, cached fallback),
  3. draft the German follow-up (claude_client.draft_walkin_followup, Hormozi framing),
  4. build the removable internal context block,
  5. deposit an IMAP DRAFT in the ENTERING person's mailbox (never sends), authored as them,
     with their signature and the chosen Cc,
  6. write a '✉️ Entwurf erstellt' note back to the lead page.

Trigger: a cron every few minutes (tools/scheduled/walkin-draft-worker.sh), optionally kicked
inline from the request for immediacy. Concurrency-safe via the queue's flock. Fails safe:
missing creds / API errors never crash the run; jobs retry up to MAX_ATTEMPTS then go to `failed`
with a single operator Telegram ping.

  --dry-run           build + print each draft's MIME, touch neither the mailbox nor the queue
  --sample-lead NAME  run one canned fixture end-to-end (for /walkinmail-improvement previews)
  --max-jobs N        process at most N jobs this run (default 10)
"""
import argparse
import os
import sys
from types import SimpleNamespace

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TOOLS_DIR)
sys.path.insert(0, _TOOLS_DIR)
sys.path.insert(0, os.path.join(_TOOLS_DIR, "walkin"))

import walkin_draft_queue as queue          # noqa: E402
import team_mailboxes as tm                  # noqa: E402
import walkin_capture as wc                  # noqa: E402
import claude_client as cc                   # noqa: E402
import infomaniak_draft as draft             # noqa: E402  (tools/walkin on path)
import final_script_cache                    # noqa: E402


# --- env bootstrap ----------------------------------------------------------
# claude_client + notion_session read only os.environ; the VPS cron exports /etc/cockpit/env,
# but for local runs fill the keys we need from the repo-root .env (never overwrite existing).
def _bootstrap_env():
    path = os.path.join(_REPO_ROOT, ".env")
    try:
        with open(path) as fh:
            for ln in fh:
                s = ln.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                k = k.strip()
                if k and k not in os.environ:
                    os.environ[k] = v.strip()
    except FileNotFoundError:
        pass


def _notify(text: str):
    """Best-effort operator Telegram ping (mirrors inbox_reply_drafter._notify). Silent no-op
    if the operator bot env isn't set."""
    token = os.environ.get("OPERATOR_TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("OPERATOR_TELEGRAM_CHAT_ID")
    if not token or not chat:
        return
    try:
        import urllib.request
        import urllib.parse
        data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=10)
    except Exception:
        pass


# --- core -------------------------------------------------------------------
def _lead_fields(job: dict) -> dict:
    """The form fields a job carries (job stores them flat)."""
    keys = ("company", "contact", "role", "email", "website", "phone", "city",
            "walkin_date", "notes", "next_action", "next_action_detail", "follow_up_date")
    return {k: (job.get(k) or "") for k in keys}


def _resolve_email(fields: dict) -> dict:
    """Prefer a form-provided email (confident); else server-side web search. Never blocks."""
    form_email = (fields.get("email") or "").strip()
    if form_email:
        return {"email": form_email, "email_confident": True,
                "website": fields.get("website", ""), "sector_hint": ""}
    return cc.resolve_walkin_contact(
        company=fields.get("company", ""), city=fields.get("city", ""),
        website=fields.get("website", ""), notes=fields.get("notes", ""))


def build_draft_for_job(job: dict, cfg: dict):
    """Pure-ish assembly: resolve email -> fetch script -> draft -> context block. Returns
    (draft_dict, meta) or (None, meta) when skipped/failed. `meta` carries status details."""
    fields = _lead_fields(job)
    person = job.get("entering_person") or "Joaquin"

    resolved = _resolve_email(fields)
    if resolved.get("website") and not fields.get("website"):
        fields["website"] = resolved["website"]

    script = final_script_cache.get_final_script()
    if not script.get("text"):
        return None, {"status": "failed", "error": "no_script", "resolved": resolved}

    lead = dict(fields)
    lead["sector_hint"] = resolved.get("sector_hint", "")
    drafted = cc.draft_walkin_followup(
        lead=lead, final_script=script["text"], author_name=person,
        booking_url=cfg.get("booking", "https://cockpit.automatisierbar.ch/book"),
        ort=cfg.get("ort", "Baden"),
        next_action=fields.get("next_action", ""),
        next_action_detail=fields.get("next_action_detail", ""),
        follow_up_date=fields.get("follow_up_date", ""))

    if drafted.get("skip_reason"):
        return None, {"status": "skipped", "skip_reason": drafted["skip_reason"],
                      "sector": drafted.get("sector", ""), "resolved": resolved}
    if not drafted.get("body"):
        return None, {"status": "failed", "error": "empty_draft", "resolved": resolved}

    to = resolved["email"] if resolved.get("email_confident") else ""
    cc_list = [a for a in (job.get("cc") or []) if a and str(a).strip()]
    context = wc.build_context_block(
        fields, sector=drafted.get("sector", ""), author=person,
        email=resolved.get("email", ""), email_confident=resolved.get("email_confident", False),
        walkin_date=fields.get("walkin_date", ""))
    draft_dict = {
        "company": fields.get("company", ""),
        "to": to,
        "subject": drafted.get("subject", ""),
        "body": drafted.get("body", ""),
        "context_block": context,
        "cc": ", ".join(cc_list),
        "confident": bool(resolved.get("email_confident")),
    }
    meta = {"status": "drafted", "sector": drafted.get("sector", ""), "resolved": resolved}
    return draft_dict, meta


def _writeback_lead_note(job: dict, meta: dict):
    """Append a '✉️ Entwurf erstellt' note to the lead page (best-effort; never fatal).
    Does NOT touch the Branche property — writing a possibly-invalid select option to the live
    Leads DB is left to the dedicated enrichment cron."""
    page_id = job.get("lead_page_id")
    if not page_id:
        return
    try:
        import notion_session as ns
        if not ns.available():
            return
        person = job.get("entering_person") or ""
        date = job.get("walkin_date") or ""
        sector = meta.get("sector") or ""
        r = meta.get("resolved") or {}
        addr = r.get("email") or "An: leer"
        lines = [f"Für: {person} · {date}", f"Branche/Hypothese: {sector}", f"An: {addr}"]
        ns.append_booking_note(page_id, "✉️ Walk-in Entwurf erstellt", lines)
    except Exception as e:
        print(f"[walkin-worker] lead note writeback failed: {e}", flush=True)


def process_job(job: dict, cfg: dict, *, write_note: bool = True) -> dict:
    """Draft + deposit for one already-claimed job. Returns a per-job result dict."""
    job_id = job["job_id"]
    person = job.get("entering_person") or "Joaquin"
    company = job.get("company") or "(?)"
    queue.update_job(job_id, status="processing", claimed_at=queue._now_local().isoformat())

    draft_dict, meta = build_draft_for_job(job, cfg)

    if meta["status"] == "skipped":
        queue.update_job(job_id, status="skipped", skip_reason=meta.get("skip_reason"),
                         sector=meta.get("sector"))
        if write_note:
            _writeback_lead_note(job, meta)
        return {"company": company, "status": "skipped", "reason": meta.get("skip_reason")}

    if meta["status"] == "failed" or draft_dict is None:
        return _retry_or_fail(job, meta.get("error", "draft_failed"))

    # Deposit the IMAP draft into the entering person's mailbox.
    mcfg = tm.draft_cfg(person, cfg)
    mcfg["cc"] = ""  # per-draft cc is authoritative; never fall back to the tej@ default
    payload = {"from": mcfg["from"], "drafts": [draft_dict]}
    args = SimpleNamespace(
        user=tm.imap_user(person), user_env=tm.imap_user_env(person),
        password_env=tm.imap_password_env(person),
        host=None, port=None, folder=None, dedup=False, no_verify=False)
    rc = draft.cmd_push(payload, mcfg, args)
    r = meta.get("resolved") or {}
    if rc == 2:  # creds missing / IMAP login failed
        return _retry_or_fail(job, f"no_credentials:{tm.address(person)}")
    if rc == 1:  # append failed
        return _retry_or_fail(job, "imap_append_failed")

    queue.update_job(job_id, status="drafted", drafted_at=queue._now_local().isoformat(),
                     sector=meta.get("sector"), resolved_email=r.get("email"),
                     resolved_email_confident=r.get("email_confident"), error=None)
    if write_note:
        _writeback_lead_note(job, meta)
    tag = "" if r.get("email_confident") else " (An: leer)"
    return {"company": company, "status": "drafted", "mailbox": tm.address(person), "tag": tag}


def _retry_or_fail(job: dict, error: str) -> dict:
    job_id = job["job_id"]
    attempts = job.get("attempts", 0) + 1
    if attempts >= queue.MAX_ATTEMPTS:
        queue.update_job(job_id, status="failed", attempts=attempts, error=error)
        return {"company": job.get("company"), "status": "failed", "attempts": attempts,
                "error": error, "terminal": True}
    queue.update_job(job_id, status="pending", attempts=attempts, error=error, claimed_at=None)
    return {"company": job.get("company"), "status": "retry", "attempts": attempts, "error": error}


def run(*, max_jobs: int = 10, dry_run: bool = False, sample_lead: str = None,
        write_note: bool = True) -> dict:
    _bootstrap_env()
    cfg = draft.load_config()
    cfg.setdefault("ort", "Baden")

    if dry_run or sample_lead:
        job = _sample_job(sample_lead or "Muster Treuhand AG")
        draft_dict, meta = build_draft_for_job(job, cfg)
        print(f"[dry ] status={meta['status']} "
              f"sector={meta.get('sector','')} email={(meta.get('resolved') or {}).get('email','')}")
        if draft_dict:
            mcfg = tm.draft_cfg(job["entering_person"], cfg)
            draft.cmd_dry_run({"from": mcfg["from"], "drafts": [draft_dict]}, mcfg)
        return {"dry_run": True, "status": meta["status"]}

    jobs = queue.pending_jobs()[:max_jobs]
    if not jobs:
        return {"processed": 0, "results": [], **queue.job_stats()}

    results = []
    failures = []
    for job in jobs:
        fd = queue.claim(job["job_id"])
        if fd is None:
            continue  # another worker holds it
        try:
            res = process_job(job, cfg, write_note=write_note)
            results.append(res)
            if res.get("terminal"):
                failures.append(res)
        except Exception as e:  # never let one job kill the run
            print(f"[walkin-worker] job {job['job_id']} crashed: {e}", flush=True)
            failures.append(_retry_or_fail(job, f"crash:{e}"))
        finally:
            queue.release(fd)

    drafted = sum(1 for r in results if r.get("status") == "drafted")
    for r in results:
        print(f"[{r['status']:8}] {r.get('company')} "
              f"{r.get('mailbox','')}{r.get('tag','')} {r.get('error','') or r.get('reason','')}")
    if failures:
        names = ", ".join(f"{f.get('company')} ({f.get('error')})" for f in failures)
        _notify(f"[walk-in drafts] {len(failures)} dauerhaft fehlgeschlagen: {names}. "
                f"Bitte prüfen (IMAP-Creds?).")
    summary = {"processed": len(results), "drafted": drafted,
               "failed": len(failures), "results": results, **queue.job_stats()}
    print(f"[done] {drafted} Entwürfe, {len(failures)} dauerhaft fehlgeschlagen, "
          f"{len(results)} bearbeitet")
    return summary


# --- canned fixtures (for --dry-run / --sample-lead + the improvement skill) ---
_FIXTURES = {
    "Muster Treuhand AG": {
        "company": "Muster Treuhand AG", "contact": "Remo Meier", "role": "Founder / Inhaber",
        "city": "Baden", "website": "", "email": "info@muster-treuhand.ch", "phone": "",
        "walkin_date": "2026-07-04",
        "notes": "Sehr interessiert. Macht Belege noch von Hand, MwSt-Abrechnung frisst Zeit."},
    "Alpina Immobilien": {
        "company": "Alpina Immobilien", "contact": "", "role": "", "city": "Zürich",
        "website": "", "email": "", "phone": "", "walkin_date": "2026-07-04",
        "notes": "Verwaltet viele Objekte, schreibt Mieter einzeln an. Chef war offen."},
    "Coiffeur Belle": {
        "company": "Coiffeur Belle", "contact": "Sandra", "role": "", "city": "Baden",
        "website": "", "email": "", "phone": "", "walkin_date": "2026-07-04",
        "notes": "Nett, aber reiner Salon. Kein Backoffice."},
    "Codes SA": {
        "company": "Codes SA", "contact": "", "role": "", "city": "Genève", "website": "",
        "email": "", "phone": "", "walkin_date": "2026-07-04",
        "notes": "Empfangsdame leitet an die Geschäftsleitung weiter. Bitte Mail schicken."},
    "Kanzlei Steiner": {
        "company": "Kanzlei Steiner", "contact": "Dr. Steiner", "role": "Leiter/Chef Stv.",
        "city": "Baden", "website": "steiner-recht.ch", "email": "", "phone": "",
        "walkin_date": "2026-07-04",
        "notes": "Anwaltskanzlei, tippt Dossiers ab. Interessiert an weniger Papierkram."},
}


def _sample_job(name: str) -> dict:
    f = _FIXTURES.get(name) or dict(_FIXTURES["Muster Treuhand AG"], company=name)
    return {"job_id": "sample", "entering_person": "Nico", "cc": [], "lead_page_id": None,
            "next_action": "E-Mail-Entwurf erstellen", **f}


def main():
    ap = argparse.ArgumentParser(description="Process the walk-in auto-draft queue.")
    ap.add_argument("--dry-run", action="store_true", help="Build + print MIME, no mailbox/queue writes")
    ap.add_argument("--sample-lead", help="Run one canned fixture end-to-end (for previews)")
    ap.add_argument("--max-jobs", type=int, default=10, help="Max jobs to process this run")
    ap.add_argument("--no-lead-note", action="store_true", help="Skip the Notion lead-note writeback")
    args = ap.parse_args()
    run(max_jobs=args.max_jobs, dry_run=args.dry_run, sample_lead=args.sample_lead,
        write_note=not args.no_lead_note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
