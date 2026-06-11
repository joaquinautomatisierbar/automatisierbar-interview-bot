---
name: compute-honest-roi
description: >
  Estimate time-saved per process step (machine-saved time + Mensch-Restzeit explicitly
  split) and compute weekly/monthly/yearly CHF savings. Reject inflated framings like
  "98% automation" or "replaces FTE". Use this BEFORE invoking build-visual-process-diagram
  to populate the time_minutes_before / time_minutes_after fields honestly.
---

# Compute Honest ROI

Swiss KMU owners catch dishonest ROI math instantly. The brief gets killed in the implementation meeting. This skill enforces honest framing.

## What "honest" means

For every process step:

- `time_minutes_before`: how long does the human currently spend, per cycle?
- `time_minutes_after`: how long does the human STILL spend after the automation runs?

**`time_minutes_after` is rarely 0.** Common scenarios where it stays > 0:

| Step type | Why human time remains |
|---|---|
| Classification / triage | Spot-check the AI's calls (~5-10% of items) |
| Document filing | Confirm filing target / reject misfiles |
| Outbound message | Approve before send (Phase 1 Bike-Method) |
| Data entry into legacy system | Manual UI override when API gaps |
| Customer-facing reply | Tone check, signature verification |

ONLY zero out `time_minutes_after` when:

- The step is a pure webhook → another system (no human downstream)
- The customer has explicitly approved unattended operation post-pilot (rare in Phase 1)
- The step is purely internal logging / telemetry

## Estimation heuristics

When the brief's `process_map` doesn't include explicit timings:

### `time_minutes_before` defaults (per cycle, per step)

| Activity | Default |
|---|---|
| Manually reading + triaging an inbound message | 2-5 min |
| Opening a tool, navigating to the relevant record | 1-3 min |
| Copy-paste between two systems | 2-5 min |
| Manual classification / decision | 1-3 min |
| Writing a short outbound reply | 5-15 min |
| Filing a document into a legacy system (Winjur, etc.) | 3-8 min |
| Looking up status / context | 2-5 min |
| Notifying a colleague | 1-2 min |

### `time_minutes_after` defaults

| Step type | Default after automation |
|---|---|
| Pure machine-to-machine | 0 |
| Machine action + human spot-check (1 in 10) | ~1-2 min |
| Machine drafts, human reviews + sends | 30-50% of original time |
| Machine prepares, human approves UI button | 1-2 min |

### Cycles per week

Pull from the brief's `## Fehler & Volumen` section if explicit. Otherwise:

- Daily process (e.g. inbox triage): 5 cycles/week
- Weekly process (e.g. status report): 1 cycle/week
- Per-event process (e.g. new client onboarding): estimate from brief's `## Volumen`, default 2-5/week

When in doubt, **err low** (under-promise on cycles, under-promise on savings).

## CHF math

```
minutes_saved_per_cycle = sum(time_minutes_before - time_minutes_after) for all steps
hours_saved_per_week = minutes_saved_per_cycle × cycles_per_week / 60
chf_saved_per_week = hours_saved_per_week × hourly_rate_chf
chf_saved_per_month = chf_saved_per_week × 4.33
chf_saved_per_year = chf_saved_per_week × 52
```

**Default `hourly_rate_chf`: 70.** Override only if the brief specifies otherwise (e.g. customer is a Treuhand whose own hourly is CHF 180 — then use their rate, not the operator's CHF 70).

## Output framing

In `PRESENTATION.md`, `roi-page.html`, the SVG, and Telegram pings — ALWAYS use one of:

✅ "X Stunden pro Woche bei der Routine-Arbeit, Y Stunden Mensch-Kontrollzeit bleibt erhalten."

✅ "Maschine-Zeit gespart: 4 h/Woche. Mensch-Zeit für Kontrolle: 30 min/Woche."

✅ "Bei CHF 70/h × 5 Zyklen/Woche: CHF 280/Woche, CHF 1.213/Monat, CHF 14.560/Jahr."

NEVER use:

❌ "98% Zeit gespart"

❌ "Vollautomatisiert" / "Voll-Autopilot" / "Zero-Touch"

❌ "Replaces 1 FTE" / "Ersetzt Mitarbeiter"

❌ "Kein Mensch mehr nötig"

## Edge cases

- **Brief has no `## Fehler & Volumen` section**: surface a Klärungspunkt "Wie viele Zyklen pro Woche fallen aktuell an?" — don't make up the number.
- **Customer's process has steps with truly 0 human time before**: rare. Almost always there's an "open the tool" or "switch context" minute. Add 1 min minimum.
- **Customer's process is 100% automatable with 0 review**: rare in Phase 1. If you think so, flag in the comment: "Empfehle Phase-1 mit menschlicher Kontrolle, Phase-2 ohne nach 3-4 Wochen Validierung."
- **No hourly rate available**: default CHF 70. Note it in the output ("Bei angenommenem Stundensatz CHF 70…").

## Workflow

1. Read the brief's `process_map` (steps array).
2. Read `## Fehler & Volumen` section for `cycles_per_week` + any explicit timings.
3. Read `## desired_outcome` for the customer's primary KPI (informs whether to optimize for machine-saved time vs error-rate-reduction).
4. For each step, fill `time_minutes_before` from explicit text or defaults above.
5. For each step, fill `time_minutes_after`:
   - 0 if truly machine-to-machine
   - 30-50% of before if human review remains
   - 1-2 min if approval button still needed
6. Compute totals + CHF.
7. Build the JSON for `build-visual-process-diagram`.
8. Reference these numbers (honestly) in roi-page.html footer and live-demo-script intro.
