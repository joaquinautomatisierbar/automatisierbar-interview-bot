---
name: write-presentation-doc
description: >
  Produce the customer-handover-ready `PRESENTATION.md` after a build. Plain Hochdeutsch, no dev jargon, tied to `desired_outcome`. Tej/Nico/Patrik read this 5 min before the implementation meeting with the customer.
---

# Write PRESENTATION.md

`PRESENTATION.md` is the document the human assignee (Tej / Nico / Patrik) reads in the 5 minutes before walking into the implementation meeting with the customer. **The customer never sees it** — but its tone shapes how the human presents the work.

## Audience

- **Reader:** Tej / Nico / Patrik. Native German speakers. Sales background. Comfortable enough with tech to skim, but **not developers**. Don't make them parse code.
- **Use-case:** quick re-orientation before the meeting. They've done the interview, maybe 5-10 days ago. Help them recall the brief + see what was built + know what to highlight.

## Required structure

```markdown
# <Customer name> — <One-line build description>

## Worum es geht

<2-3 sentence summary of the customer's pain point, IN THE CUSTOMER'S WORDS where possible. Quote the brief's "Kundenkontext / Pain-Point" section.>

## Was wir gebaut haben

<1-2 paragraphs describing the artifact in plain Hochdeutsch. No code references. No node names. Focus on the data flow as the customer experiences it: "Wenn eine Mail mit 'Dringend' im Betreff kommt, sieht der Anwalt sofort eine Slack-Nachricht."

End with one sentence tying the build to the customer's `desired_outcome` KPI:
"Damit fällt Ruths stündliche Inbox-Kontrolle (~30 Min/Tag) weg und dringende Klient-Anfragen landen innert 1 Min beim Anwalt — statt bisher 1-3 h."

>

## Wie's funktioniert (Datenfluss)

<A clean visual or numbered flow. Mermaid is fine if simple. Prose is fine too.

Example:
1. Gmail sieht eine neue Mail in `kanzlei@example.ch`
2. System prüft Subject und Body auf High-Priority-Keywords
3. Wenn high-priority → Slack-Nachricht in #client-priority mit Vorschau + Link
4. Wenn normal → keine Aktion (Inbox bleibt unverändert)

>

## Was der Kunde merkt

<Concrete: what changes from the customer's day-to-day perspective? What does Ruth do differently? What does the lawyer do differently? Don't say "the workflow runs" — say "Ruth schaut nicht mehr stündlich in die Inbox, sondern der Anwalt sieht die wichtigen Mails direkt im Slack."

>

## Offene Klärungspunkte (zu bestätigen im Implementation-Meeting)

<EVERY `## Offene Klärungspunkte` from the brief, surfaced explicitly with:
- MVP-Default
- Was der Kunde im Meeting bestätigen / korrigieren soll
- Implementation-Hebel (wie schwer / einfach ist die Umstellung)

This section is mandatory. If the brief had 0 Klärungspunkte, write "Keine offenen Punkte aus dem Brief — alles eindeutig." Otherwise list them all.

>

## ROI (ehrlich)

<Two-bar honest ROI:
- **Jetzt (Ist-Zustand):** Wo verbringt der Kunde welche Zeit?
- **Mit der Automation:** System-Zeit (Auto) + Mensch-Restzeit (Review/Approval/Edge-Cases)

Show the math: "150 Mails/Tag, Ruth braucht ~3 s/Mail für den Quick-Check → 7.5 min/Tag heute. Nach der Automation: 0 min wenn keine high-priority, ~30 s/Mail wenn der Anwalt eine high-priority anschaut → ~5 min/Tag bei ~10 high-priority Mails."

NEVER show "48 h → 15 min" claims unless the process literally has zero mandatory human review. Per the `surface-klaerungspunkte` skill, honest ROI is non-negotiable.

>

## Was Tej/Nico/Patrik im Meeting machen sollten

<3-5 bullet points:
- Welche Klärungspunkte zu durchgehen (priorisiert)
- Welcher Live-Test gemeinsam mit dem Kunden Sinn macht (z.B. "Schreib gemeinsam eine Test-Mail mit 'Dringend' und schau, ob die Slack-Notification kommt")
- Was das BAMFAM-Follow-up sein soll (date + scope)
- Anything else the human should focus on

>

## Stack & Wartung (eine Zeile)

<One technical sentence so the human knows what to say if the customer asks "wo läuft das eigentlich?":
"Läuft auf n8n Cloud (oojoaquin.app.n8n.cloud), Workflow ID kommt im RELEASE_NOTES.md."

>
```

## Tone rules

- **Hochdeutsch, nicht Schwizerdütsch.** Customer-facing language is always Hochdeutsch even in Swiss context.
- **Active voice. Short sentences.** "Das System sieht die Mail" beats "Wenn eine Mail vom System bemerkt wird".
- **No dev jargon.** "Webhook" → "Trigger". "Endpoint" → "Adresse". "Polling" → "regelmäßiger Check". "Idempotent" → don't use.
- **No code blocks in customer-facing sections.** Code blocks OK in `## Stack & Wartung` only.
- **Quote the customer's words from the brief where possible** — especially in `## Worum es geht`. It signals "we listened."

## Anti-patterns

- Dishonest ROI ("48 h → 15 min" when there's a 5-min/unit human review step) → blow up at the meeting.
- Silent Klärungspunkte (missing from "Offene Punkte" section) → silent overrides, trust gone.
- Walls of code → reader skips PRESENTATION.md entirely, defeats the purpose.
- Generic templating ("Die Automation läuft zuverlässig.") → reader can't recall the specific build, mumbles at the customer.
- Missing `desired_outcome` tie-back → the WHOLE POINT.

## When ready

Save as `PRESENTATION.md` in the Issue workspace root. Engineer is responsible for this file. Product Engineer audits it during intent review.
