---
autonomy-level: L3
bike-method-phase: 1
kpi-bucket: more-customers
kpi-metric: number of script-iteration suggestions Nico actually adopts per month (target: ≥1 hook tested/wk after report ships)
---

# Weekly Call Report (Workflow B)

**Phase 2/3 brücke.** Aggregat aus Call Analytics letzte 7d → AI-generierter Report mit Skript-Vorschlägen + Hot-Lead-Liste → Notion + Email an Team.

| ID | Name | Trigger |
|---|---|---|
| **B** (`8MezhOHMkndzRBc5`) | Cold Call — Weekly Call Report | Schedule, Mo 08:00 (CRON `0 8 * * 1`) |

## Pipeline

```
Schedule Trigger (Mo 08:00)
  → Notion Get All Call Analytics (simple:false, returnAll:true)
  → Code: Aggregate Last 7 Days
       (filter call_date ≥ weekStart, group by branche, count failure_modes, extract hot_leads, compute Phase-3-readiness)
  → Code: Build LLM Payload (JSON serialize for Claude)
  → HTTP Anthropic: Generate Report (Claude Sonnet 4.6, max 4096 tokens)
  → Code: Parse Report (Markdown → HTML for email)
  → Notion: Create Weekly Report row
  → Email: Send HTML to Joaquin + Nico
```

## Aggregate-Logic

Pro Run berechnet:
- **counts**: Hot, Borderline, Cold, Direct-Abwimmlung (this week)
- **failure_modes**: Wrong-Pitch, Wrong-Time, Wrong-Person, Wrong-Tone, N/A (counts)
- **branchen_map**: pro Branche → count + outcomes-distribution + per-call summaries/quotes
- **hot_leads**: filter outcome=Hot, extract firmenname/branche/schmerzscore/summary/quote
- **phase3_ready**: total_all_time ≥ 100 AND hot_all_time ≥ 10 (Voice-Agent-Schwelle)
- **top_branche** + **top_failure_mode**: für Notion-summary fields

## LLM Output Schema (Markdown)

Claude erzeugt strikt diese Sektionen:
1. `## TL;DR` — 2-3 Zeilen
2. `## Branchen-Hook-Map` — Branchen mit ≥2 Calls (sonst skip)
3. `## Failure-Mode-Taxonomie` — Counts + 1-Satz-Diagnose
4. `## Skript-Vorschläge (3 konkrete Iterationen)` — "Statt X sag Y, weil Z"
5. `## Hot-Lead-Liste` — pro Hot-Lead: Firma, Branche, Schmerz, Top-Problem, Re-Engagement-Vorschlag
6. `## Phase-3-Status` — vs. Schwelle

System-Prompt enforced "Datenbasis zu dünn" Marker wenn weniger als 2-3 Calls in einer Sektion → keine erfundenen Patterns.

## Outputs

**Weekly Call Reports DB** (`b47a2bc0-8dac-4c8b-9727-9efa29ed49fe`):
- Week Of, Total Calls, Hot/Borderline/Cold/Direct counts, Top Branche, Top Failure Mode, Report Markdown, Phase-3-Ready? checkbox

**Email**:
- From: sexyjoaquin15@gmail.com (via SMTP cred)
- To: Joaquin + Nico (configurable in workflow)
- Branding: Helvetica, primary color `#15C97A`, monospace counters
- Body: HTML-rendered Markdown + Notion-Link

## Markdown→HTML Code

Pure-JS line-by-line parser (kein npm package). Handhabt:
- Headings (`#`, `##`, `###`)
- Bold (`**...**`), Italic (`_..._`), Code (`` `...` ``)
- Lists (`- ...`, `* ...`)
- Paragraphs

Brittle bei verschachtelten Listen. Für komplexe Reports: ggf. später richtige md library.

## Credentials

- `Notion account` (auto-assigned)
- `SMTP account` (auto-assigned, n8n SMTP cred mit Joaquins Email)
- `Anthropic Header Auth` (manual)

## Halt-Conditions

Activation = halt (sendet emails an reale Recipients). User aktiviert manuell.

Manuelle Test-Triggers: pin-data smoketest ist safe (kein realer Email-Send), aber `execute_workflow` in production = REAL EMAIL → halt before.

## Verification

1. Logic-Smoketest: execution 785 (5 fake calls inkl 1 outside-week → korrekt gefiltert, 1 Hot extracted, branchen-map sauber)
2. Real-Run: nach activation, manueller "Execute Workflow" Klick im n8n UI → schickt echten Email + Notion row

## Known Issues

- **HTML-Parser brittle**: ineinander verschachtelte Lists oder lange Paragraphs könnten broken render. Workaround: Markdown-Field in Notion ist die canonical source, Email-HTML ist nur für Quick-Read. Phase-X improvement: switch to a real markdown lib via `Function` node mit npm.
- **Email recipients hardcoded** in Workflow-Node. Für mehr Recipients: edit toEmail field oder switch zu CC-list aus Notion-DB-Query.

## Related

- Daten-Quelle: Call Analytics DB (gefüllt von Workflow A/A2)
- Output-DB: Weekly Call Reports
- Phase 3 Trigger (≥100 + ≥10): notification noch nicht implementiert (TODO Phase X)
