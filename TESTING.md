# Testing — AUT-37 — Interview-Bot textbox fix + pre-dispatch validation gate

INTERNAL change to the Interview-Bot at `automatisierbar-interview-bot.onrender.com`.
This branch ships TWO independent improvements. Test BOTH before approving the
merge to `main`.

## Was du brauchst

- Lokal das Repo gecheckt-out auf der Branch `feature/aut-37-validation-textbox-fix`
  (Joaquin: `git fetch && git checkout feature/aut-37-validation-textbox-fix`).
- `.env` mit gesetztem `ANTHROPIC_API_KEY` und `NOTION_API_KEY`
  (sind bei Joaquin schon drin — beim Klon übernehmen).
- Python 3.11+ im Repo-`venv` (`.venv/bin/python --version`).
- Chrome oder Safari mit DevTools (für die Mobile-Ansicht).

## Quick-Check (2 Min) — Server startet sauber

In der Repo-Root:

```bash
.venv/bin/python api.py
```

Erwartet: Log-Zeilen wie `Running on http://127.0.0.1:5001`. Keine Tracebacks.
Falls Crash beim Start: `ImportError`-Output an Joaquin schicken.

Server laufen lassen — alle weiteren Tests gehen gegen `http://127.0.0.1:5001`.

## Golden-Path A — Textbox-Fix (5 Min, Desktop ≥900px)

1. Öffne `http://127.0.0.1:5001/static/index.html` in Chrome.
2. Tipp im Kontextfeld auf der Startseite irgendwas ein
   (z.B. "Treuhandbüro Meier Buchhaltung & Mahnungen"),
   klick "Weiter" — Bot stellt die ersten Fragen.
3. Beantworte 1-2 Runden, bis du auf den **PROZESS-MAP** Screen kommst
   (Tabelle mit Spalten: Wer / Was passiert / Tool / Daten rein / Daten raus).
4. In Zeile 1 → Spalte "Wer" → tipp **wörtlich**:
   `Buchhalterin überträgt PDF in Bexio und prüft Betrag, IBAN, Fälligkeit`
5. Klick irgendwo anders hin (Blur).
6. **Erwartet:** Der gesamte Satz ist sichtbar — die Zelle ist auf 2-3 Zeilen
   hochgewachsen, nichts ist abgeschnitten.
7. Wiederhol dasselbe in Spalte "Tool", "Daten rein", "Daten raus" mit einem
   langen Satz. Alle Zellen müssen wrappen, nichts abschneiden.

Wenn die Zelle den Text horizontal abschneidet wie eine `<input>`-Box →
das ist der Bug, AUT-37 nicht erfüllt. An Joaquin escalieren.

## Golden-Path A2 — Textbox-Fix (3 Min, Mobile <900px)

1. Chrome DevTools öffnen (Cmd+Opt+I).
2. Klick auf das Device-Toolbar-Icon (Cmd+Shift+M) → Wähle "iPhone 12 Pro".
3. Reload die Seite, geh wieder zum **PROZESS-MAP** Screen.
4. Selber Test: lang Satz in "Wer" eintippen, dann blur.
5. **Erwartet:** Zellen sind jetzt vertikal gestapelt (jede Zeile ist
   ein eigener Block mit Label oben). Der Satz wrappt vollständig sichtbar.

Wenn Mobile-Layout horizontal-scrollt statt vertikal zu stapeln → an Joaquin.

## Golden-Path B — Pre-Dispatch Validation Gate (8 Min)

1. Schliess Interview komplett ab — Kontext eingeben, 1-3 Frage-Runden, Prozess-Map
   ausfüllen, bis du auf den **ROI**-Screen kommst (mit den zwei Balken
   "Heute" / "Mit Automatisierung").
2. Warte bis das Panel "🤖 An das Build-Team senden" unten erscheint (kommt nach
   ~5s — der Prompt wird im Hintergrund generiert).
3. Klick **"An Build-Team senden →"**.
4. **Erwartet (Fall 1 — Brief ist gut):**
   - Button schaltet auf "Prüfe Brief…" (~10-12s).
   - Falls Sonnet-Validator passiert: Button schaltet auf "Wird gesendet…"
     und der bekannte grüne "✓ An Build-Team gesendet — Issue AUT-XX" erscheint.
   - In den Render-Logs (Terminal mit `python api.py`) siehst du:
     `[claude-stats] label=validate_brief_completeness status=pass missing_count=0 …`
5. **Erwartet (Fall 2 — Brief hat Lücken, häufiger):**
   - Button schaltet auf "Prüfe Brief…" (~10-12s).
   - Statt grüne Erfolgs-Nachricht: orangener Banner "Brief ist noch nicht
     vollständig (Pass 1 / 4) — bitte ergänzen, bevor wir senden:"
   - Darunter Liste der fehlenden Elemente (z.B. "Trigger: Welcher genaue
     Tagesabschnitt löst den Cronjob aus?").
   - Zwei Buttons: **"Klärung anfordern"** (primary) und **"Erneut prüfen"** (ghost).

6. Klick **"Klärung anfordern"** → Textarea erscheint, schreib z.B.
   `Trigger ist Cronjob 08:00 Europe/Zurich. Tool für Versand ist Outlook 365.`
   → Klick **"Speichern + erneut prüfen"**.
7. **Erwartet:** Button geht wieder auf "Prüfe Brief…" → entweder grünes
   "Gesendet" oder eine zweite Lücken-Liste (Pass 2 / 4).

## Edge-Case Test — 4-Pass Soft-Warn (3 Min)

1. Wiederhole Schritt 6 dreimal mit absichtlich nichtssagenden Klärungen
   (z.B. einfach "ok" eintippen), bis du auf Pass 4 bist.
2. **Erwartet:** Banner wird jetzt: "⚠️ Validierung hat nach **4 Durchläufen**
   noch Lücken — Build-Team wird wahrscheinlich nachfragen. Trotzdem senden?"
3. Daneben Button **"Trotzdem senden →"** und **"Klärung anfordern"**.
4. Klick **"Trotzdem senden →"** → Dispatch läuft wie bisher (vorausgesetzt
   `BUILD_DISPATCHER_WEBHOOK_URL` ist gesetzt; lokal ist sie ggf. NICHT gesetzt
   und du kriegst stattdessen `503 Build-Dispatcher noch nicht konfiguriert` —
   das ist OK).

## Failure-Mode Test — Validator nicht erreichbar (2 Min)

Simulieren, dass `/validate` ausfällt, ohne den Operator zu blockieren:

1. Im Terminal mit `python api.py` → Strg+C → Server stoppen.
2. Editiere `tools/claude_client.py`, Zeile mit `validate_brief_completeness`,
   und füge ganz oben in den Funktionskörper ein: `raise RuntimeError("simulated fail")`.
3. Server wieder starten.
4. Geh durch das Interview bis ROI → klick "An Build-Team senden".
5. **Erwartet:** Kein "Pass 1 / 4"-Banner. Stattdessen geht es direkt auf
   "Wird gesendet…" und entweder Erfolg oder die übliche Dispatcher-Fehlermeldung.
   In der Browser-DevTools-Console solltest du eine `console.warn`-Zeile sehen:
   `validate failed — fail-open to direct dispatch: …`
6. Setze die Änderung in `tools/claude_client.py` zurück (`git checkout tools/claude_client.py`).

## Smoke-Tests vom Engineer — schon gelaufen

Engineer hat zwei Python-Smokes in `.tmp/` hinterlassen:

- `.tmp/aut37_smoke.py` — ruft `validate_brief_completeness` direkt mit zwei
  präparierten Prompts auf (GOOD vs BAD). Output: beide Calls liefern wohlgeformtes
  JSON mit gültigen `element`-Labels. Kosten ~$0.027 für beide Calls.
- `.tmp/aut37_endpoint_smoke.py` — Flask `test_client` gegen `POST /validate`
  mit gemocktem `notion_session`. 12/12 Checks grün (HTTP-Codes, Antwort-Shape,
  `pass_number`-Inkrement, `soft_warn` ab Pass 4, State-Persistence).

Wenn QA sie nochmals laufen lassen will:

```bash
.venv/bin/python .tmp/aut37_smoke.py            # ~25s, ~$0.03
.venv/bin/python .tmp/aut37_endpoint_smoke.py   # ~25s, ~$0.03
```

Beide drucken `PASS — N checks green.` am Ende.

## Wenn was nicht klappt

| Symptom | Erste Aktion | Bei Anhalten → |
|---|---|---|
| Server crashed beim `python api.py`-Start | Lies den letzten Traceback | An Joaquin schicken |
| Prozess-Map-Zellen schneiden Text ab | DevTools → Inspect die Zelle. Sollte `<textarea>` sein, nicht `<input>` | An Joaquin: "AUT-37 Track A nicht angekommen, Zelle ist `<input>`" |
| "An Build-Team senden" hängt > 30s in "Prüfe Brief…" | Render-Log angucken — sollte alle 10-15s eine `[claude-stats] label=validate_brief_completeness`-Zeile sehen. Wenn nicht: Anthropic-API-Timeout | An Joaquin |
| `/validate` antwortet 409 "Interview noch nicht abgeschlossen" trotz fertigem ROI-Screen | Im Browser-Network-Tab schauen ob `GET /api/session/<id>/prompt` vor dem Klick durchgelaufen ist | An Joaquin |
| Klärungs-Liste rendert leer (weiße Box) | DevTools-Console — bin in `_renderValidationGap` ein TypeError? | An Joaquin mit Console-Screenshot |
| "Trotzdem senden"-Button erscheint nicht bei Pass 4 | Im Network-Tab das `/validate`-Response anschauen — `soft_warn` muss `true` und `pass_number` muss `>= 4` sein | An Joaquin |

## Vor dem Merge auf `main`

- [ ] Track A: long-text-Test auf Desktop (≥900px) wrappt sauber.
- [ ] Track A: long-text-Test auf iPhone 12 Pro wrappt sauber.
- [ ] Track A: alte Sessions (z.B. von gestern) laden noch korrekt — `?s=<old-sid>` in der URL probieren.
- [ ] Track B: `pass` Pfad funktioniert (Brief geht direkt durch wenn er gut ist).
- [ ] Track B: `needs_clarification` Pfad rendert die fehlenden Punkte inline.
- [ ] Track B: "Klärung anfordern" → speichert in extras → re-validiert.
- [ ] Track B: nach 4 Pässen erscheint "Trotzdem senden".
- [ ] Track B: simulierter Validator-Fehler blockiert NICHT den Dispatch (Fail-Open).
- [ ] RELEASE_NOTES.md gelesen — Joaquin weiss, was nach Render-Auto-Deploy live geht.

Wenn alles ✅: Engineer-Branch `feature/aut-37-validation-textbox-fix` lokal in
`main` mergen → `git push origin main` → Render deployt automatisch in 2-3 Min.

Wenn ein Punkt ✗: Issue auf QA zurückreichen mit `TEST_FAIL: <welcher Check>`.
