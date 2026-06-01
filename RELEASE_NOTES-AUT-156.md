# Release Notes — AUT-156

## Interviewer Selector + Re-evaluate Button (Changes 1 & 2)

**Shipped to branch:** 2026-06-01
**Tag:** INTERNAL
**Branch:** `build/AUT-156-interviewer-selector-reevaluate`
**Render service:** `automatisierbar-interview-bot-o8h2` (auto-deploys from main on merge)
**Reviewer:** Joaquin — please verify locally + merge when satisfied

---

## 1. Was wurde geändert

Zwei unabhängige, additive Änderungen am Interview-Bot (`api.py` + `static/index.html`). Keine neuen Umgebungsvariablen, keine Schema-Änderungen, kein Breaking Change.

**Change 1 — Interviewer-Selector (Frontend only)**
Auf dem Start-Screen (vor dem ersten Interview) erscheint jetzt eine 4-Button-Pill-Gruppe: `Joaquin / Nico / Tej / Patrik`. Standardmäßig ist "Joaquin" aktiv. Die Auswahl wird als `interviewer`-Feld im POST `/api/session/start` mitgeschickt. Das Backend-Feld `interviewer` war bereits vorhanden — `api.py:133–180` speichert es unverändert in der Notion-Session. Die Änderung ist rein im Frontend.

**Zweck:** Jede Session trägt jetzt den Interviewer-Namen — in Notion sichtbar, ohne manuelle Nachbearbeitung.

**Change 2 — Re-evaluate Button + `/reevaluate`-Route**
Auf dem ROI-Screen erscheint unter den "Offene Annahmen" ein neuer Button **"Angaben korrigieren"**. Ein Klick öffnet ein Inline-Panel mit Textarea + "Neu auswerten →"-Button.

Backend: Neuer Endpunkt `POST /api/session/<session_id>/reevaluate`. Lädt die Session, **hängt** den `correction_note`-Text als `\n[RE-EVALUATE NOTE]: …` an das bestehende `extra_context` an (nie überschreiben), ruft `evaluate_answers()` auf und gibt `{ status, next }` zurück — gleiche Form wie `/answers`.

Frontend: Loading-Lock `_reevaluateLock` verhindert Doppel-Klick. Leeres Textarea → Shake-Animation, kein API-Call. Antwort → `showQuestions()` (neue Fragen) oder `showROI()` (aktualiserter ROI-Screen).

**Zweck:** Kunden können Korrekturen direkt im Interview eintippen, ohne die Session neu zu starten.

---

## 2. Commits auf Branch

```
2f2a1dc  AUT-156: interviewer selector + /reevaluate route (Changes 1 & 2)
d3829fe  AUT-156: add ROLLBACK.md and TESTING.md entries
```

**Geänderte Dateien:**
- `api.py` — +80 Zeilen (neuer `/reevaluate`-Endpunkt bei Zeile ~463)
- `static/index.html` — +106 Zeilen (Pill-Selector ~Zeile 829, Re-evaluate-Panel ~Zeile 1036)
- `ROLLBACK.md` — Rollback-Anweisungen für beide Changes (vollständig + chirurgisch)
- `TESTING.md` — 5-Test-Suite für Joaquin (Change 1 + Change 2 + Edge-Cases)

---

## 3. Änderungen prüfen (für Joaquin)

```bash
cd "/home/paperclip/automatisierbar-interview-bot"  # oder lokaler MacBook-Pfad

# Branch holen
git fetch origin
git checkout build/AUT-156-interviewer-selector-reevaluate

# Vollständiger Diff gegen main
git diff main...build/AUT-156-interviewer-selector-reevaluate

# Nur Backend (neuer /reevaluate-Endpunkt)
git diff main...build/AUT-156-interviewer-selector-reevaluate -- api.py

# Nur Frontend (Pill-Selector + Re-evaluate-Panel)
git diff main...build/AUT-156-interviewer-selector-reevaluate -- static/index.html
```

**Kritische Stellen zum Eyeballen:**
- `api.py` ~Zeile 463: `reevaluate_session()` — APPEND-Logik: `extra_context = extra_context + f"\n[RE-EVALUATE NOTE]: {correction_note}"` (nie `=` allein)
- `static/index.html` — `_reevaluateLock: false` in App-State + `if (this._reevaluateLock) return;` am Anfang von `submitReevaluate()`

---

## 4. Lokale Verifikation (MacBook, vor Merge)

```bash
# Abhängigkeiten (keine neuen — requirements.txt unverändert)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# App lokal starten
ANTHROPIC_API_KEY=<dein Key> python api.py

# Browser: http://localhost:5000
```

Vollständige Test-Anleitung: **`TESTING.md`** auf diesem Branch — 5 Szenarien (Pill-Selector, Panel öffnen/schliessen, leeres Feld, Korrektur mit Text, Doppelklick-Lock) mit Step-by-Step auf Deutsch.

Wenn alles ✅: Branch in `main` mergen → Render deployt automatisch in ~2-3 Min.

---

## 5. Deploy-Prozedur

```bash
git checkout main
git merge --no-ff build/AUT-156-interviewer-selector-reevaluate
git push origin main
```

Oder via GitHub PR:
`https://github.com/joaquinautomatisierbar/automatisierbar-interview-bot/compare/main...build/AUT-156-interviewer-selector-reevaluate`

Render auto-deployed von `main` — kein manueller Dashboard-Schritt nötig.

---

## 6. Rollback

Vollständige Anleitung in **`ROLLBACK.md`** → Abschnitt "AUT-156".

Schnell-Rollback (beide Changes zusammen):

```bash
git revert --no-edit 2f2a1dc
git push origin main
# Render deployt reverted state in ~2-3 Min
```

Chirurgischer Rollback (nur Change 1 oder nur Change 2): Schritte im `ROLLBACK.md` dokumentiert.

---

## 7. Laufzeitanforderungen

Keine neuen Credentials. Bestehende `ANTHROPIC_API_KEY` und `NOTION_API_KEY` (Render env vars) sind ausreichend.

---

## 8. Pre-Merge-Checkliste (Release Engineer)

- [x] Branch `build/AUT-156-interviewer-selector-reevaluate` auf GitHub gepusht
- [x] Kein Commit auf `main`
- [x] `.env` ist in `.gitignore` — Diff auf API-Key-Leakage geprüft: sauber
- [x] APPEND-Logik verifiziert: `extra_context` wird nie überschrieben
- [x] Loading-Lock verifiziert: `_reevaluateLock` setzt auf `true`, wird in `finally` zurückgesetzt
- [x] 400 auf leeres `correction_note` verifiziert
- [x] QA `TEST_PASS` und Product Engineer `SHIP` auf AUT-156 geloggt
- [ ] Joaquin reviewed Diff + merged zu `main` *(Owner: Joaquin)*
- [ ] Render-Deploy nach Merge beobachten (5 Min) *(Owner: Release Engineer, auf Joaquin's Signal)*
