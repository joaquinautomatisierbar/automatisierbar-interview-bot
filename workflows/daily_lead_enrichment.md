---
title: Daily Lead Context Enrichment
autonomy-level: L3
bike-method-phase: 1
workflow_id: 6yduFHU9FDKN7z4h
workflow_name: "⭐️ Context Enrichment — Daily 07:00"
schedule: "0 7 * * * (Europe/Zurich)"
status: LIVE / active — activated 2026-06-11 after supervised batch (6 enriched / 2 thin / 0 hallucinated); runs daily 07:00. MAX_PER_RUN=50, REQUIRE_WEBSITE=false.
supersedes: ToHhLCWNSI1YkFpx (archived — "Context Enrichment (nightly)")
last_updated: 2026-06-11
---

# Daily Lead Context Enrichment

## Objective
Every morning, give the cold-callers a short, **factual** "call card" for each lead that doesn't
have one yet — grounded **only** in the company's real website. The caller reads it before dialing
so they can show they did their homework (the single biggest lever on whether a prospect will talk).
**Never hallucinate:** no usable website → no context. And report results so nobody has to check
Notion manually.

## The five process elements
- **Trigger:** Schedule, daily 07:00 Europe/Zurich (`0 7 * * *`).
- **Data sources:** Notion Leads DB "Interview Datenbank" (`31cbebb0-c2f9-8047-9e9f-fc59851f8a34`);
  each lead's website (the `website` URL field, or one found via Tavily Search); the live website
  content (Tavily Extract).
- **Transformations:** scrape → clean text → Claude Haiku writes a 5-line call card
  (WAS / GROESSE / STANDORT / AUFHAENGER / OPENER) or returns the sentinel `KEIN_KONTEXT`.
- **Decision points:** has a saved website? → search if not. Found a plausible site? Enough content
  for a real card, or `KEIN_KONTEXT`? Transient API failure (retry) vs. permanent thin site (skip)?
- **Destination:** Notion lead — `Context` (rich_text), `Last Enriched` (date), `Enrichment Status`
  (select). Plus a Telegram run-summary to the operator (chat `7971390512`).

## Node chain (19 nodes)
```
Daily 07:00 → Get All Leads → Filter Candidates → Resolve URL → Needs Search?
  ├ true  → Tavily Search → Pick Site → Has URL? ┬ true → Tavily Extract …
  │                                              └ false → Mark No Site ┐
  └ false → ───────────────────────────────────────────→ Tavily Extract …
  Tavily Extract → Prep Website Text → Claude Call Card → Parse Card ┐
  (Search / Extract / Claude error outputs) → Mark Retry ────────────┤
                          {Mark No Site, Parse Card, Mark Retry} → Collect Decisions
  Collect Decisions ┬ Should Write? (true) → Update Lead (Notion)
                    └ Tally → Operator Summary (Telegram)
```

## Per-lead outcomes (what lands in Notion)
| Situation | Context | Last Enriched | Enrichment Status | Retried next day? |
|---|---|---|---|---|
| Good site → real card | call card | today | `Angereichert` | no |
| Site too thin / Claude returns `KEIN_KONTEXT` | *(blank)* | today | `Website zu dünn` | no |
| No saved website + none found by search | *(blank)* | today | `Kein Website` | no |
| Tavily/Claude transport error (transient) | *(blank)* | *(blank)* | — | **yes** (07:00) |

Anti-hallucination is enforced twice: (1) the prompt instructs `KEIN_KONTEXT` for empty/thin/JS/error
pages; (2) `Pick Site` only accepts a found URL whose host/title matches a company-name token and
isn't a directory/social domain (avoids summarizing the wrong company).

## Candidate filter (Filter Candidates Code node)
Keep a lead when ALL hold: `Context` empty **and** `Last Enriched` empty **and**
`Cleanup Status` ≠ "Pending Removal" **and** Pipeline not in {OUT, Paying}. Capped at
**`MAX_PER_RUN`** (top of the node's code) so a big backlog doesn't burn Tavily credits / time —
the backlog drains over several mornings.
- Supervised-test value: `8`.  → **raise to ~50 before activating** the schedule.

## Credentials
| Node | Type | Credential |
|---|---|---|
| Get All Leads / Update Lead | notionApi | Notion account (`N0c1Nn5s4jZ0ZzuO`) — auto-bound |
| Tavily Search / Tavily Extract | tavilyApi (predefined) | Tavily account (`NVDKy3NgNseMrgGo`) — **bind in UI** |
| Claude Call Card | httpHeaderAuth | Anthropic Credential (`MnrsoXjxzBdxxm0v`) — **bind in UI** |
| Operator Summary | telegramApi | Automatisierbar Operator (`CVuR0MmRvUcbtakS`) — bound |

> n8n won't attach credentials to HTTP Request nodes via the API (UI-only). The three HTTP nodes
> must have their credential selected once in the n8n editor.

## Tavily API (via HTTP Request, predefined `tavilyApi` cred)
- Search: `POST https://api.tavily.com/search` body `{query, max_results:5, search_depth:"basic"}`.
- Extract: `POST https://api.tavily.com/extract` body `{urls:[url], extract_depth:"basic"}`; clean
  page text in `results[].raw_content`; unreachable sites land in `failed_results` (200, not an HTTP
  error) → treated as thin, not as a transient retry. True transport errors hit the node's error
  output → `Mark Retry`.

## Rollout (Bike-Method Phase 1)
1. Bind the 3 HTTP creds in the UI.
2. Supervised run via `execute_workflow` (manual) with `MAX_PER_RUN=8`; inspect each lead in Notion —
   cards factual, thin/no-site leads left **blank** (no junk), no wrong-company summaries.
3. Tune prompt / `Pick Site` matching if needed; re-run.
4. Operator approves → set `MAX_PER_RUN≈50`, activate the 07:00 schedule, confirm the Telegram summary.
5. Watch 1–2 mornings, then hands-off (advance toward Phase 3 once stable).

## Known gotchas / lessons
- n8n Code node **runOnceForEachItem** must `return { json: {...} }` (a single object) — **not**
  `return [{ json }]`. Returning an array there fails with "A 'json' property isn't an object".
- The community Tavily node (`@tavily/n8n-nodes-tavily.tavily`) can't be introspected/validated by
  the Workflow SDK ("invalid package name") → call Tavily via HTTP Request instead.
- Post-HTTP Code nodes recover lead fields via `$('Resolve URL').item` (pairedItem); a `.all()[$itemIndex]`
  fallback keeps pinned-data tests from breaking.
- No re-enrichment cadence yet (a written card is never refreshed). Possible future: re-enrich when
  `Last Enriched` > 90 days.
