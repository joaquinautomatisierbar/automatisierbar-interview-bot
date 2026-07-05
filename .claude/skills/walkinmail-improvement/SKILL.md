---
name: walkinmail-improvement
description: Use when the operator types /walkinmail-improvement or wants to improve/tune the automatic walk-in follow-up email DRAFTS — e.g. "the walk-in mails should propose appointment times differently", "verbessere die Walk-in Mails", "change how the draft opens", "the drafts are too long / too formal", "add X to the walk-in email", "the follow-up should mention Y". This is the authoring counterpart to the (retired) /walkinmail runtime skill: it knows the whole auto-draft system (the Notion Final Script, the drafting system prompt, the context block, per-mailbox signatures, the worker) and routes an improvement point to the right place, applies it safely, and shows a before/after sample draft. It does NOT send or draft real mail.
---

# /walkinmail-improvement — tune the automatic walk-in draft quality

The walk-in follow-up email is now drafted **automatically**: when a team member enters a lead in
the field PWA, a server-side pipeline drafts a same-quality German follow-up into that person's
Infomaniak Drafts (see `workflows/walkin_followup_automation.md`). This skill is how the operator
improves those drafts over time. One run = one improvement, applied to the **right knob**, proven
with a before/after sample. Never sends, never drafts real mail.

## The System Map — where every knob lives

Take the operator's improvement point and route it to exactly ONE of these:

| The improvement is about… | Edit here | Safety |
|---|---|---|
| **Copy / structure / wording / the pitch / appointment-time phrasing / the sector pain-hypotheses** | **Notion "Follow-Up Email Script" page** (`388bebb0c2f98088991deea070765a37`) — Final Script (template) + Branchenspezifische Pitch-Bibliothek. This is the source of truth the drafter reads live each run. | Notion edit = **safe** (operator already edits copy here). |
| **Framing rules / guardrails** (ICP filter, Hormozi order, banned phrasings, the 10-Stunden rule, siezen, no-em-dash, no-price, output JSON shape, the sign-off convention) | `tools/claude_client.py` → `_SYSTEM_WALKIN_DRAFT` | Code/prompt edit = **halt + confirm** first. |
| **How the recipient email is found** (search heuristics, confident/best-guess rule) | `tools/claude_client.py` → `resolve_walkin_contact` | Code edit = **halt + confirm**. |
| **What fields appear in the removable context block** | `tools/walkin_capture.py` → `build_context_block` | Code edit = confirm. |
| **Visual styling of the context block** (the amber "vor dem Senden löschen" box) | `tools/walkin/infomaniak_draft.py` → `_render_context_block_plain` / `_render_context_block_html` | Code edit = confirm. |
| **A team member's mailbox / address / signature routing** | `tools/team_mailboxes.py` (`ROSTER`) | Code edit = confirm. |
| **Notion outage / stale fallback copy** | `tools/walkin/final_script_fallback.md` (committed snapshot) — must stay in sync with the Notion page | Regenerate with `--refresh`. |
| **Retry caps / failure notifications / cron cadence** | `tools/walkin_draft_worker.py`, `tools/scheduled/walkin-draft-worker.sh` | Code edit = confirm. |

**Most improvements are copy** and belong in Notion (safe). Only reach for the system prompt when
the change is a *rule* (a hard do/don't), not a *phrasing*.

## Procedure

1. **Classify** the improvement point against the map above. If it's ambiguous (could be copy OR a
   rule), ask the operator one clarifying question, or default to the Notion copy edit (reversible,
   safe).
2. **Show the current state** of the surface you're about to touch (fetch the Notion page section,
   or read the code block) so the operator sees what's there.
3. **Apply the change:**
   - **Notion copy** → edit the Final Script / Pitch-Bibliothek page directly (use REAL line breaks,
     not `\n` — `notion-update-page` mangles `\n`). Then **refresh the committed fallback** so an
     outage can't serve stale copy: `python3 tools/walkin/final_script_cache.py --refresh` (this
     rewrites `final_script_cache.txt`; also update `final_script_fallback.md` if the change is
     load-bearing).
   - **Prompt / code** (`_SYSTEM_WALKIN_DRAFT`, `resolve_walkin_contact`, context block, roster,
     worker) → **halt first** for anything touching the Grand-Slam-Offer wording, the 10-Stunden
     rule, the ICP filter, or the sign-off convention: `bash .claude/hooks/notify-telegram.sh halt
     "<what you're about to change and why>"`. Then make the edit.
4. **Prove it — before/after sample draft.** Generate a fresh sample with the change applied:
   `python3 tools/walkin_draft_worker.py --sample-lead "Muster Treuhand AG" --dry-run`
   (fixtures: Muster Treuhand AG · Alpina Immobilien · Coiffeur Belle [ICP-skip] · Codes SA
   [forward-invite] · Kanzlei Steiner [website-hint]). Pick the fixture whose sector/shape best
   exercises the change. Read the drafted body and confirm the improvement actually landed and no
   guardrail broke (no em-dash, ends at "Freundliche Grüsse aus {Ort},", no price/jargon, "kostet
   nichts" said once, ICP-skip still fires for Coiffeur).
5. **Tie it to the goal (KPI)** and report: what you changed, where, the before/after diff of the
   sample draft, and which bucket it serves (more customers / more value per customer / less cost —
   walk-in drafts are a *reply-rate* lever). If the change was a prompt/code edit, note it in
   `decisions/log.md`.

## Edit-safety rules

- **Never sends.** This skill only edits config/copy/code and runs `--dry-run` previews. Real drafts
  are created only by the live worker on the VPS.
- **Notion is the source of truth for copy.** Prefer a Notion edit over hardcoding copy in the prompt.
  Whenever you edit the Notion Final Script, refresh the committed fallback in the same run.
- **Prompt/code edits touching the offer, the 10-Stunden rule, the ICP filter, or the sign-off →
  halt + confirm** before applying, and always show the before/after sample.
- **One improvement per run.** Don't batch unrelated changes — each should be provable with its own
  sample draft.
- **Keep the guardrails intact:** siezen, no Gedankenstriche (— / –) in the email text, no prices,
  no tech jargon, dream-outcome-first, "kostet nichts" exactly once, sign-off ends the body.

## Reference
- Runtime pipeline + operator blockers: `workflows/walkin_followup_automation.md`.
- Business grounding: `references/business-context.md` (offer, ICP, free pilot, no pricing talk yet).
- Tone: `references/war-room/walkin_opener.md`.
