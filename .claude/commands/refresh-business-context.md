---
description: Walk through refreshing references/business-context.md — fresh §3 funnel numbers, §7 progress, resolve §9 open questions, bump last_updated.
---

# Refresh Business Context

You are helping Joaquin do the bi-weekly refresh of `references/business-context.md`. The doc is the single source of truth for what Automatisierbar sells, current funnel reality, and 6-month targets — downstream advice (library skill, level-up, ICP fit calls) only stays useful if these numbers are current.

## How to run this

1. **Read `references/business-context.md`.** Note the `last_updated` field and skim §3 (Funnel Reality) + §7 (6-Month Horizon) + §9 (Open Questions) — those are the sections most likely to have moved.

2. **Pull what you can verify autonomously first** (don't ask Joaquin questions you can answer yourself):
   - Pipeline count: query the Notion Lead DB ("Interview Datenbank", `31cbebb0-c2f9-8047-9e9f-fc59851f8a34`) for hot leads, pilots in build, paying clients via the Notion MCP.
   - Transcript count: list files in the Drive "Transcripts" folder (`1PJUP0AOlU3SyT0NZF9_rzKfx19tRTVJh`) via Drive MCP and count.
   - Workflow execution counts (last 14 days): use n8n MCP `get_execution` on the Cold Call Voice Agent workflows if instrumented.

3. **Ask Joaquin only for what you CAN'T verify**, in one batched message:
   - Calls/walk-ins last 2 weeks (Nico + Joaquin + Tej totals)
   - Conversations and hot-leads delta
   - Bieri / Gränacher status (still in pilot? converted? walked? new clients added?)
   - MRR + cumulative revenue (any payments received?)
   - Any §9 open questions resolved (handover decided? pricing locked? walk-ins formalized as wedge?)
   - Any new strategic priors to add to §6
   - Any new constraints in §8 (budget changes, time blocks shifted)

4. **Use `AskUserQuestion` for binary checks** ("did Bieri convert? yes/no/still pending"). Use plain text for numbers.

5. **Edit the file** with the new values. Preserve structure exactly — only update the changed cells. Always:
   - Bump `last_updated:` to today's date (run `date -u +%Y-%m-%d` to get it; convert to local if needed)
   - If a TBD became a real value, replace it
   - If a value became wrong, replace it
   - If a §9 open question got resolved, move the resolution into the relevant section AND remove the §9 entry
   - If a new question surfaced, add it to §9

6. **Sanity-check the trajectory math** before finishing. If the user reports e.g. "still 0 paying clients" and the Q2 target was "5 by 2026-05-30," flag it directly: "trajectory is off — what's the lever you're pulling?" Don't just record the number and move on.

7. **Telegram-ping when done** with a one-line summary so Joaquin sees it on his phone:
   ```
   bash .claude/hooks/notify-telegram.sh checkpoint "business-context.md refreshed: [headline change in <12 words>]"
   ```

8. **Do not commit** unless Joaquin asks. Just save the file edits.

## Halt conditions

- If §3 numbers regressed sharply (e.g. hot leads dropped from 10 → 3) without explanation, halt and ask before recording — could be a measurement error.
- If §7 trajectory is meaningfully off (e.g. 2026-05-30 5-clients goal is impossible given current state on the day of refresh), halt and surface to Joaquin directly so it gets re-baselined deliberately, not silently.
- If `last_updated` is already today's date, halt and ask — refresh may have already happened today.

## What this is NOT

- Not a strategy session. You're updating numbers, not redesigning the offer. If a strategic question surfaces ("should we pivot to wedge real estate?"), flag it for a separate `/level-up` session.
- Not a pricing decision. If Joaquin wants pricing/guarantee help, point him to the `library` skill — that's its job, not this routine's.
