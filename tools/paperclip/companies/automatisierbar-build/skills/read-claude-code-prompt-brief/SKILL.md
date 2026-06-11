---
name: read-claude-code-prompt-brief
description: >
  Parse the structured Claude-Code-style build brief produced by Automatisierbar's web interview bot (api.py). Extract intent (`desired_outcome`), structure (process map), assumptions (`## MVP Assumptions`), and uncertainty (`## Offene Klärungspunkte`) before planning or reviewing a Build.
---

# Read Claude Code Prompt Brief

Automatisierbar's web interview bot emits a structured Claude-Code-style build prompt at the end of every customer interview. The format is consistent. Pull the fields below explicitly — never skip a section.

## What the brief contains

| Section | Purpose | How you use it |
|---|---|---|
| Kundenkontext / Pain-Point | Narrative customer description | Anchors the "why" — never lose sight of this |
| Prozess-Map (Ist-Zustand) | Wer / Was / Tool / Daten rein / Daten raus | Source of truth for what the customer described |
| Soll-Prozess | Same table for the target state | What you build toward |
| Trigger | Event that starts the workflow | Maps directly to webhook / cron / file-event |
| Logik & Regeln | Business logic | The "if/then" of the implementation |
| Ausgabe & Aktionen | Destinations + side effects | What integrations are needed |
| Fehler & Volumen | Error handling expectations + scale | Drives retry strategy, idempotency, batching |
| `## MVP Assumptions` | Explicit assumptions the brief honors | Honor verbatim; if you change one, surface why |
| `## Offene Klärungspunkte` | Places where MVP defaults could conflict with customer's literal statements | These MUST be surfaced in PRESENTATION.md, not silently overridden |
| `desired_outcome` | The business KPI this is supposed to move | Anchor for Product Engineer's intent review |

## Reading discipline

1. Read the brief **end-to-end** before reasoning about implementation. Skipping ahead leads to building against an outdated mental model.
2. List every `## Offene Klärungspunkte` item separately. For each, decide: (a) surface with MVP default, (b) require human confirmation before build, or (c) implementer's call with clear reasoning in PRESENTATION.md.
3. Cross-check the Prozess-Map against the narrative. If the map omits a step the narrative mentions, flag it as a possible Klärungspunkt.
4. Identify the **KPI bucket** the `desired_outcome` falls into (more customers / more value per customer / less cost). This binds the Product Engineer's review later.

## Example brief structure

```
# Build-Brief: <title>

## Kundenkontext
<narrative>

## Prozess-Map
| Wer | Was | Tool | Daten rein | Daten raus |
...

## Soll-Prozess
...

## Trigger
...

## Logik & Regeln
...

## Ausgabe & Aktionen
...

## Fehler & Volumen
...

## MVP Assumptions
1. ...
2. ...

## Offene Klärungspunkte
1. <ambiguous point + suggested MVP default>
2. ...

## desired_outcome
**KPI-Bucket:** <bucket>
**Metric:** <specific metric>
```

## What to extract before planning

- Stack constraints (does the brief mention customer has existing n8n? existing trigger.dev? wants visual editor for non-developer?)
- Volume + latency from `## Fehler & Volumen`
- Number of integrations (rough count of distinct services touched)
- Number of unresolved Klärungspunkte → drives need for human confirmation before build

If the brief is *missing* one of these sections, that's a sign the interview bot fell back to V2 format or the customer didn't engage. Flag to CTO before building.
