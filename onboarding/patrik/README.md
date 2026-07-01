# Patrik — 8-Wochen Co-Founder Apprenticeship

*Remote/async, ~2026-07-01 → 2026-08-26. Ends right before all four founders start HSG together on 2026-09-07.*

This folder is the **operating kit** for developing Patrik over the 8 weeks he's away. Full rationale + stress-tested design lives in the plan: `~/.claude/plans/hey-another-thing-so-mossy-bonbon.md`. This README is the map to the kit.

---

## What this is (in one paragraph)

Patrik is a co-founder but the least-developed one — today you can't hand him a broad "get X done" and reliably know it lands. He falls apart on **ambiguity** and **errors**, and left alone does ~3–5h/week. The goal is two co-equal things by 2026-08-26: a **trusted generalist** (scoped brief → self-verified deliverable with light review) *and* a **work-ethic shift** (ownership, solutions-not-problems, wanting to give 120%). The method: he learns *our own system* (Bike Method, Autonomy L1→L3, EAD, Map-5, WAT, Intern Rule) by being managed inside it — starting almost fully guided, fading to independent, one notch per week.

## The honest graduation bar

> **"Given a scoped brief with acceptance criteria, Patrik reliably produces a self-verified sandbox artifact or ops deliverable at Autonomy L2–L3 with only light review, escalates cleanly instead of stalling, and has surfaced at least one improvement candidate himself."**

Ceiling is **L3 / Bike Phase 3**. He does *not* reach hands-off autonomy, and **the prod-deploy PR-gate never opens during the program.** Graduation = "trusted to be reviewed lightly," not "unsupervised on prod."

## The one risk everything is bent against

**He quietly ghosts around week 3.** Remote silence is invisible; when he hits friction he freezes (see the Notion-outage history). Every mechanic here exists to make being-stuck *safe to show* and asking-for-help *frictionless*, and to pull hours through ownership rather than tracking. **If W3 goes silent, that's the emergency — not a red error.**

---

## The kit (read in this order)

| File | For | What it is |
|---|---|---|
| [week-plan.md](week-plan.md) | You | The W0–W8 program: per-week competency, deliverables, acceptance bars, the 3 gates. Your master reference. |
| [owned-surface.md](owned-surface.md) | You | The one real thing Patrik owns end-to-end (the Lead-Ops Digest) — the motivation engine. |
| [task-card-template.md](task-card-template.md) | You | The 3-field card Patrik sees + the hidden operator metadata + the GitHub Issue template for his fork. |
| [framing-playbook.md](framing-playbook.md) | You | The German "chasch mer mit X hälfe?" reframes + tone rules + the accountability engine (keep/cut). |
| [w0-setup-sop.md](w0-setup-sop.md) | Patrik | The 6-step fork + sandbox setup he follows on day one. |
| [escape-hatch.md](escape-hatch.md) | Patrik | The anti-freeze card. Pin it in his repo / have him print it. |
| [progression-log.md](progression-log.md) | You (+ shared) | The milestone/honor-roll log. Gate passes get dated entries here. |

## The 3 rules Patrik must internalize (tell him these on day one)

1. **Nüt gaat live ohni Review.** Full read access to everything, build freely in your sandbox — but nothing merges/deploys/sends-for-real until a founder reviews the PR. Same rule we run our AI agents on.
2. **Wenn's hakt: nöd iigfriere, zeig's.** Stuck > 20 min = screenshot + one line, ping immediately. No form. Getting stuck is normal and *showable* — it's literally the content of Friday's Bug-of-the-Week.
3. **Chum mit em Vorschlag, nöd nu mit em Problem.** (From week 5 on, for design questions — not for breaks.) Bring what you'd do + one specific question, not a blank "was jetzt?".

## Weekly rhythm (async-first)

- **Monday** — you post 1–2 task cards ("chasch mer mit X hälfe?") + "womit chan i der die Wuche hälfe?"
- **Midweek** — Tej buddy 30-min stuck-swap. PR comments = the mentoring log.
- **Friday** — ≤3-min Show-&-Tell Loom (he *shows*, never *reports*), incl. Bug-of-the-Week.
- **Gate weeks** — end of W2 (Gate 1), W5 (Gate 2), W8 (Gate 3 = graduation).

## Before W1 starts (your setup checklist)

- [ ] Create Patrik's GitHub **fork** of the repo (or a clone he owns), `.env` removed, no push to real remotes.
- [ ] Generate his **sandbox `.env`**: scratch n8n instance, throwaway Notion *test* Leads DB, budget-capped Haiku key, test Telegram bot.
- [ ] Confirm the **owned surface** (Lead-Ops Digest) or swap it — see [owned-surface.md](owned-surface.md).
- [ ] Confirm **Tej** as buddy (or pick another near-peer).
- [ ] Set up the task board: GitHub Issues on his fork now → migrate to the Hub when it's confirmed live.
- [ ] Do a **dry run**: walk one real task card through the whole loop (card → build → deliberate break → Escape-Hatch → PR → review) so the machine is proven before Patrik touches it.
