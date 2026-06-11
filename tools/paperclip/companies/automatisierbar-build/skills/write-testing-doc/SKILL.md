---
name: write-testing-doc
description: >
  Produce `TESTING.md` so the human assignee (Tej/Nico/Patrik) can verify the artifact locally before the customer meeting — without needing developer skills. Concrete commands or button-click steps only.
---

# Write TESTING.md

`TESTING.md` is the **smoke-test runbook** the human assignee runs in the 5-10 minutes between reading PRESENTATION.md and joining the customer meeting. It catches obvious-broken before the customer does.

## Audience

- **Reader:** Tej / Nico / Patrik. Not developers. Comfortable with curl in a terminal *if* the commands are exact. Comfortable clicking around n8n editor / Render dashboard / etc.
- **Use-case:** "Does the deliverable actually work right now, end-to-end, in production?" — 5-10 min check.

## Required structure

```markdown
# Testing — <Customer name> — <Build description>

## Was du brauchst

<List everything the tester needs to have ready:
- n8n login (oojoaquin.app.n8n.cloud)
- Slack workspace access (or whichever integration)
- A test inbox / test webhook / test data file
- Any auth keys (name them — don't paste them)>

## Quick-Check (2 Min)

<The shortest possible "is this even running?" check. Usually one command or one click.

Example for n8n:
1. Öffne https://oojoaquin.app.n8n.cloud/workflows/<workflow-id>
2. Klick "Test workflow" oben rechts
3. Sieh in der Execution-History — sollte ohne Fehler durchlaufen (alle Knoten grün)
>

## Golden-Path Test (5 Min)

<The "happy path" the customer will use day 1. Walk through exactly.

Example:
1. Öffne deinen Gmail-Test-Account
2. Schicke eine Mail an `kanzlei@example.ch` mit Subject "Dringend - Test"
3. Warte 30-60s (Gmail-Polling-Latenz)
4. Öffne den Test-Slack-Channel `#test-priority`
5. **Erwartet:** Eine Nachricht "🚨 Dringend von <test-account>" mit Mail-Vorschau und "Im Gmail öffnen"-Link
6. Klick den Link — muss in Gmail die richtige Mail öffnen

Wenn nicht: schau in n8n-Execution-History (Schritt 1) auf den letzten Run — welcher Knoten hat einen roten Punkt?
>

## Edge-Case Test (3 Min)

<One or two specific edge cases the brief flagged. Test each in 1 min.

Example:
1. Schicke eine **normale** Mail (Subject "Sitzung Donnerstag") an die Test-Inbox
2. **Erwartet:** KEINE Slack-Nachricht (normale Mails werden bewusst nicht gepingt)
3. Wenn doch eine kommt: das ist ein Klassifikations-Bug, an Joaquin escalieren
>

## Failure-Mode Test (optional, 3 Min)

<If easy to simulate, show how. Otherwise skip.

Example:
1. Wenn du den Slack-Workspace temporär kicken kannst: kick den Bot raus
2. Schicke eine Test-Mail mit "Dringend"
3. **Erwartet:** Workflow läuft durch ohne Crash, Slack-Schritt loggt einen Auth-Fehler, danach kommt eine Mail an Joaquin (System-Operator-Alert)
4. Bot wieder zum Workspace hinzufügen
>

## Wenn was nicht klappt

<Concrete escalation table:

| Symptom | Erste Aktion | Bei Anhalten → |
|---|---|---|
| n8n Test-Run zeigt einen Knoten in Rot | Klick den Knoten, lies den Fehler-Hinweis. Oft fehlende Credential | An Joaquin: "Workflow <id>, Knoten <name>, Fehler: <kopiert>" |
| Slack-Nachricht kommt nicht an | Prüf #test-priority Channel exists + Bot ist Mitglied | An Joaquin mit Workflow-ID |
| Gmail-Polling triggert nicht | Prüf in n8n: Trigger ist active? Gmail-OAuth nicht abgelaufen? | An Joaquin |
| Alles grün aber Inhalt der Slack-Nachricht falsch | Screenshot machen, vergleichen mit PRESENTATION.md Section "Wie's funktioniert" | An Joaquin |
>

## Vor dem Kunden-Meeting

<Final check: 1-2 confirmations:

- [ ] Quick-Check hat funktioniert
- [ ] Golden-Path hat funktioniert
- [ ] Edge-Case hat funktioniert
- [ ] Offene Klärungspunkte aus PRESENTATION.md sind dir bewusst — du fragst den Kunden im Meeting durch
- [ ] Du weisst, wie du im Meeting einen Live-Test mit dem Kunden gemeinsam fahren kannst (Test-Mail schicken und Slack-Notification zusammen anschauen)

Wenn ein Punkt nicht funktioniert: NICHT zum Meeting gehen. An Joaquin halt-and-poll, Meeting verschieben.
>
```

## Tone rules

- **Concrete commands.** "Klick X" / "Schick eine Mail an Y mit Subject Z" — not "verify the workflow."
- **Exact URLs and IDs.** Engineer fills these in. Don't write `<workflow-id>` placeholders without filling them.
- **Expected vs actual side-by-side.** Every step says what the tester should SEE after they did the action.
- **Escalation path is concrete.** "An Joaquin mit Workflow-ID" — not "contact technical support."

## Anti-patterns

- "Open the n8n editor and check the workflow runs" → not actionable. What does "check it runs" mean to a non-developer?
- "Verify all assertions pass" → developer-speak. Tej won't run the test suite.
- Missing the Edge-Case section → the most embarrassing bugs surface there.
- No escalation table → tester gets stuck at the first error and stops.

## When ready

Save as `TESTING.md` in the Issue workspace root. Engineer is responsible. Product Engineer audits that a non-developer can actually follow it (sometimes this means Product Engineer mentally walks through it).
