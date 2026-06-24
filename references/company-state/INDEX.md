# Company State — Index

Live snapshot of company state, refreshed by `tools/sync_company_state.py` (runs daily on VPS via systemd timer). Read by every paperclip agent at activation via the `recall-learnings` skill.

**Last refreshed:** 2026-06-01T10:15

## Files

- [founder-syncs.md](founder-syncs.md) — last 2 entries from Meeting Notes DB, lightly cleaned
- [active-clients.md](active-clients.md) — Lead-DB rows in active pipeline stages (Paying / Pilot / Hot / Qualified)
- [this-week.md](this-week.md) — 7-day signals: git commits, decisions log entries, Notion movement, n8n executions
- [team-capacity.md](team-capacity.md) — derived view of who's available + active commitments

## Refresh

- **Local:** `bash tools/paperclip/scripts/sync-company-state.sh`
- **VPS:** systemd timer fires twice daily (06:00 + 14:00 Europe/Zurich); see `install-linkedin-brief-vps.sh`

## Cleaning rules (founder syncs)

KPI/definition glossary blocks are dropped (the long "EBITDA stands for…" / "MRR / NPS / CSAT" lists). S3 attachment URLs are collapsed to `[image]`. Each entry is capped at 2000 chars to keep the recall-learnings context budget bounded.
