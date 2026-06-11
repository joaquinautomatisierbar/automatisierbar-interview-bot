---
name: surface-klaerungspunkte
description: >
  Audit every `## Offene Klärungspunkte` from the brief against PRESENTATION.md. Each must be explicitly surfaced with MVP default + human-confirmation flag — never silently overridden. Use when reviewing intent quality.
---

# Surface Klärungspunkte

The interview bot emits `## Offene Klärungspunkte` for every place where the MVP default could contradict the customer's literal statements. Surfacing each one is **non-negotiable**. Past mistakes that broke pilot relationships:

- Silently inventing `belege@meier-treuhand.ch` after the customer explicitly said "no central inbox" → trust gone.
- Assuming "biweekly" when the customer said "every 14 days from the first of the month" → first run misfired, customer noticed.
- Defaulting `dedup = yes` when the customer didn't address dedup → MVP missed messages they wanted.

## Audit procedure

For every item in `## Offene Klärungspunkte`:

1. **Find it in PRESENTATION.md.** It must appear under a heading like `## Offene Punkte` or `## Klärungspunkte` — anywhere visible to the human who reads PRESENTATION.md before the meeting.
2. **Verify the MVP-default is named.** The presentation must state what the artifact *does* in the absence of customer confirmation. Not "to be decided" — specifically, "MVP behavior: <X>."
3. **Verify a human-confirmation flag exists.** The presentation must explicitly invite the human to confirm or override the default at the implementation meeting.
4. **Cross-check the implementation.** If the brief said "MVP default: NOT dedup" but the workflow code implements dedup, the Klärungspunkt is silently overridden — fail.

## What "surfaced" looks like

Example PRESENTATION.md section that passes audit:

```markdown
## Offene Klärungspunkte (zu bestätigen im Implementation-Meeting)

1. **`eilt` im Body, aber nicht im Subject:**
   - MVP-Default: NICHT als high-priority klassifiziert (zu hohes False-Positive-Risiko)
   - **Im Meeting zu klären:** Will der Kunde "eilt" im Body als high-priority werten?
   - Implementation-Hebel: 1 Zeile im `Classify Priority` Code-Node — schneller Switch wenn der Kunde Ja sagt

2. **Duplikate (gleiche Mail mehrfach gesendet):**
   - MVP-Default: jeder neue messageId → eine neue Slack-Notification (kein Dedup)
   - **Im Meeting zu klären:** Soll innerhalb 1 h dieselbe Mail nur einmal pingen?
   - Implementation-Hebel: Dedup-Cache im n8n Code-Node mit messageId + Timestamp — moderate Komplexität

3. **Sichtbarkeit für Ruth:**
   - MVP-Default: Slack-Channel ist offen für alle Mitglieder inkl. Ruth (wenn sie im Channel ist)
   - **Im Meeting zu klären:** Soll Ruth die Notifications auch sehen, oder nur Anwälte?
   - Implementation-Hebel: 2. Slack-Channel + Routing-Logik wenn Ruth ausgeschlossen werden soll
```

## What FAILS audit

- Klärungspunkt missing entirely from PRESENTATION.md → silent override
- Klärungspunkt mentioned in passing without MVP default → human doesn't know what the artifact does
- Klärungspunkt with MVP default but no "to be confirmed" flag → human reads it as a final decision
- Implementation behavior contradicts the stated MVP default → the artifact lies about itself

## When this skill applies

- **Product Engineer** runs the audit on every artifact before deciding SHIP vs NEEDS_QOL.
- **Engineer** runs the audit on themselves before posting `READY_FOR_TEST` — catch your own gaps before QA sees them.
- **CTO** spot-checks during plan creation: if the brief has 5+ Klärungspunkte and several might block the MVP from working at all, flag for human decision via `request_confirmation` *before* the Engineer starts building.

## Output when issuing NEEDS_QOL

```
NEEDS_QOL: 2 Klärungspunkte silently overridden

1. Brief item: "soll dieselbe Mail mehrfach pingen?"
   - Customer said: <quote from brief>
   - Artifact does: <observed implementation behavior>
   - Gap: <one-line>
   - Required fix: surface in PRESENTATION.md as MVP-default + flag, OR implement the alternative if the customer's preference is clear from context.

2. Brief item: ...
```

Quote the brief verbatim. Force the gap into a comparable structure for Engineer.
