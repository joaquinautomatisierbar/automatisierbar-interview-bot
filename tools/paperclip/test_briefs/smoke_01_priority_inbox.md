# Synthetic Test Brief — Priority Inbox Slack Notifier

Mock Claude Code prompt mirroring what `api.py` would emit for a real interview.
Used to smoke-test the Builder→QA→Reviewer loop in Phase 2.

---

# Build-Brief: Priority Inbox → Slack Alert

## Kundenkontext

**Branche:** Anwaltskanzlei (3 Anwälte + 1 Assistentin, Aargau)
**Pain-Point:** Die Assistentin (Ruth) checkt die gemeinsame Inbox `kanzlei@example.ch` ca. alle 60 Min, um dringende Klient-Anfragen nicht zu verpassen. Das frisst täglich ~30 Min reine Check-Zeit + Kontext-Switch-Kosten, und trotzdem dauert es manchmal 2-3 h bis ein "dringend"-Mail bei einem Anwalt landet.

**Was sie wollen:** Slack-Notification in `#client-priority` *innerhalb 5 Min*, wenn eine Mail "high priority" ist. Normale Mails bleiben in der Inbox wie heute — keine Änderung am Inbox-Workflow.

## Prozess-Map

| Wer | Was | Tool | Daten rein | Daten raus |
|---|---|---|---|---|
| Ruth | Checkt Inbox stündlich | Gmail | E-Mails | Markiert "dringend" mental, sagt Anwalt Bescheid |
| Anwalt | Reagiert auf Mündlich-Hinweis | — | Ruths Hinweis | Antwort an Klient |

## Soll-Prozess

| Schritt | Wer | Was | Tool | Daten rein | Daten raus |
|---|---|---|---|---|---|
| 1 | System | Empfängt neue Mail | Gmail Trigger | Email object | Email JSON |
| 2 | System | Klassifiziert Priorität | Code/Logic | Subject + Body | priority: "high" / "normal" |
| 3 | System | Bei "high" → Slack | Slack Send | Email-Daten | Slack Message in #client-priority |

## Trigger

Gmail "new email" auf der gemeinsamen Inbox `kanzlei@example.ch`.

## Logik & Regeln

Priority-Klassifikation per **Keyword-Match** (case-insensitive) in Subject ODER Body:
- Hard-Match (immer high): `dringend`, `dringend!`, `urgent`, `asap`, `sofort`, `notfall`
- Soft-Hint (high wenn Subject startet mit oder allein steht): `eilt`, `wichtig`

Slack-Message-Format:
```
🚨 Dringend von {from}
Betreff: {subject}
Auszug: {first 200 chars of body}
[Im Gmail öffnen]({gmail_link})
```

## Ausgabe & Aktionen

- Slack-Channel: `#client-priority` (Workspace-ID + Channel-ID in n8n-Credential)
- Bei `normal`: keine Aktion. Inbox-Workflow bleibt unverändert.

## Fehler & Volumen

- ~150 Mails/Tag total, davon ~5-8 high priority
- Gmail-Trigger-Latenz: bis zu 60 s OK
- Bei Slack-API-5xx: 1× retry nach 30 s, dann ignorieren (kein Re-Queue nötig — wenn Slack down ist, ist ohnehin niemand erreichbar)
- Bei Slack-API-401/403: alert an Operator (Mail an Joaquin), nicht still failen

## MVP Assumptions

1. Slack-Credentials existieren in n8n (Workspace + Channel-ID werden in der Workflow-Config gesetzt).
2. Gmail-OAuth ist eingerichtet für `kanzlei@example.ch`.
3. Keyword-Liste oben ist abschliessend für die MVP; spätere Iterationen können LLM-basierte Klassifikation hinzufügen.
4. Der Slack-Channel `#client-priority` existiert bereits und der Bot ist als Member hinzugefügt.

## Offene Klärungspunkte

1. **Was bei `eilt` im Body, aber nicht im Subject?** Customer hat nicht klar gesagt. MVP-Default: NICHT als high klassifizieren (false-positive-Risiko zu hoch). PRESENTATION.md muss diesen Default offenlegen.
2. **Was wenn dieselbe Email innerhalb 1 h mehrfach getriggert wird (z.B. Customer hat Mail vergessen, schickt nochmal)?** Customer hat nicht gesagt. MVP-Default: jeder neue `messageId` führt zu einer Slack-Notification (kein Dedup). Surface als Decision-Punkt.
3. **Soll Ruth selbst die Slack-Notification sehen?** Customer sagte nur "Anwälte". MVP-Default: alle Channel-Member sehen sie (Ruth hat Zugriff zum Channel falls sie das Mitglied ist). Nicht explizit Ruth ausschließen.

## desired_outcome

**KPI-Bucket:** less-cost.
**Metric:** Ruths inbox-check time / Tag → 0 (Ziel: <5 Min, statt 30 Min heute).
**Sekundärmetrik:** Zeit von "high-priority Mail kommt rein" → "Anwalt hat es gesehen" → <5 Min (statt heute 60-180 Min).

## Erfolgskriterien für den MVP

- Workflow validiert (`validate_workflow` passes)
- Pin-data Test: high-priority Mail → Slack-Notification (im Test-Modus: assertion gegen erwartetes Output-Shape, kein echter Slack-Call)
- Pin-data Test: normal Mail → keine Slack-Notification
- Pin-data Test: 5xx-Fehler von Slack → 1× retry, dann graceful fail
- `PRESENTATION.md` und `TESTING.md` sind hand-over-ready
- Alle 3 Klärungspunkte sind in PRESENTATION.md surface'd, nicht versteckt
