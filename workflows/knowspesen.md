---
name: KnowSpesen — Digitale Spesenerfassung (KnowGravity)
autonomy-level: L2
bike-method-phase: 1
kpi-bucket: less-cost
client: KnowGravity Inc. (Markus Schacher)
status: MVP gebaut, Demo-bereit; wartet auf Regelwerk + echte KnowBody-Daten
owner: Joaquin
---

# KnowSpesen — Workflow SOP

Mobile-First PWA, mit der die 6 KnowBodies Belege per Foto erfassen, Claude Vision
die Felder vorausfüllt, der KnowBody kontrolliert und ergänzt, und am Monatsende per
Knopfdruck ein ZIP (PDF-Abrechnung + Excel + alle Belege) für die Treuhandfirma
entsteht, das der KnowBody selbst per Outlook verschickt.

**Warum L2 / Phase 1:** OCR ist beratend, der Mensch bestätigt jeden Beleg vor dem
Speichern; der ZIP-Versand bleibt manuell. Erst nach validiertem Live-Betrieb (und
Kunden-Vertrauen) kann Richtung L3 (Auto-ZIP) erhöht werden, genau wie vom Kunden
gewünscht ("erstes Jahr so, dann evtl. vollautomatisch").

## Die 5 Prozess-Elemente

- **Trigger:** (1) KnowBody fotografiert/lädt einen Beleg in der PWA; (2) KnowBody
  klickt "Monat abschliessen"; (3) Cron am 25. (Erinnerung an offene Monate).
- **Data sources:** das Belegfoto (Claude Vision OCR), Eingaben des KnowBody,
  Pauschaltarife (`pauschaltarife`-Tabelle, aus `config.py` geseedet), Tageskurse
  (frankfurter.dev / EZB), SQLite-DB.
- **Transformations:** OCR-Extraktion → Bestätigung → Fremdwährung→CHF → Pauschale
  auflösen → Kaffeekasse-Flag (< CHF 50) → Speichern; beim Abschluss Aggregation +
  PDF + Excel + ZIP.
- **Decision points:** Beleg vs. Pauschale; Währung CHF vs. Fremdwährung (API ok vs.
  manueller CHF-Fallback); Pauschale bekannt vs. Platzhalter (Tarif folgt → blockiert);
  Betrag < 50 → Kaffeekasse (aus ZIP ausgeschlossen); weiterverrechenbar ja/nein.
- **Destination:** SQLite (`belege`, `monatsabschluesse`) + Belegbilder auf Disk;
  Monats-ZIP (Download) das der KnowBody per Outlook an Gubser Kalt & Partner sendet.

## Architektur

- Eigenständiger Flask-Sibling-Service (`knowspesen.service`, `:8083`,
  `KNOWSPESEN_HOME=1`), gleicher `api.py`-Code wie das Cockpit, aber isoliert:
  eigene `/etc/knowspesen/env`, eigene SQLite (`SPESEN_DB_PATH`), eigener Caddy-Host
  `knowspesen.automatisierbar.ch`. Kunden-App-Crash kann die Cockpit-Ops nicht umwerfen.
- Code: `tools/spesen/*` (db, config, ocr, currency, pauschalen, capture, report_pdf,
  report_excel, month_close, email_draft, reminder, seed); Routen in `api.py`
  (`/spesen`, `/api/spesen/*`); Frontend `static/spesen.{html,sw.js,webmanifest}`.

## Tools (deterministische Ausführung)

| Aufgabe | Tool |
|---|---|
| Schema + Seeds + Queries | `tools/spesen/db.py` |
| Domänenwerte (1 Edit-Punkt) | `tools/spesen/config.py` |
| Beleg-OCR (Claude Vision, beratend) | `tools/spesen/ocr.py` |
| Fremdwährung → CHF | `tools/spesen/currency.py` |
| Pauschalen + Kaffeekasse-Regel | `tools/spesen/pauschalen.py` |
| Beleg validieren + Bild speichern | `tools/spesen/capture.py` |
| Monatsabschluss → PDF/Excel/ZIP | `tools/spesen/{report_pdf,report_excel,month_close,email_draft}.py` |
| Erinnerung (Cron) | `tools/spesen/reminder.py` |
| Demo-Daten | `tools/spesen/seed.py` |

## Bedienung / Setup

1. **DB anlegen + seeden (einmalig):** `POST /api/spesen/setup-db` (Cockpit-Auth) →
   Tabellen + Pauschaltarife. Mit `{"seed_demo": true}` zusätzlich Demo-KnowBodies +
   Beispielbelege (Markus). Oder lokal: `python3 tools/spesen/db.py`.
2. **Login:** Magic-Link `/spesen?k=<token>` pro KnowBody (Token in `knowbodies.login_token`).
3. **Erfassen:** Foto → OCR-Vorschlag prüfen → Kategorie/Zahlungsart/Projekt → speichern.
4. **Abschliessen:** "Monat abschliessen" → ZIP herunterladen → per Outlook an die
   Buchhaltung (fertiger E-Mail-Entwurf wird angezeigt).

## Tests (offline, keine API-Credits)

```
python3 tools/test_spesen_pauschalen.py
python3 tools/test_spesen_currency.py
python3 tools/test_spesen_capture.py
python3 tools/test_spesen_month_close.py
python3 tools/test_spesen_routes.py
```

## Offen / beim Kunden (siehe Follow-up-Mail an Markus)

- **Regelwerk-Tarife** (Auto-km, SBB-Klasse, Übernachtung, Abendessen): in
  `config.PAUSCHALTARIFE` als `is_placeholder` gebaut; bei Eingang Werte eintragen +
  `is_placeholder=False`, Service neu starten (re-seedet aus config).
- **6 echte KnowBody-Namen + E-Mails** → `seed`/`upsert_knowbody` + Tokens.
- **Beispiel-Dokumente** (heutige Excel/Word-Abrechnung + Beispiel-ZIP) → Output angleichen.
- **Kaffeekasse-Interpretation** (`config.KAFFEEKASSE_ALSO_SMALL_RECEIPTS`) + SharePoint-Ablage.
- **Buchhaltungs-E-Mail** (`SPESEN_ACCOUNTANT_EMAIL`) für den Versand-Entwurf.

## Selbst-Verbesserungs-Loop / nächste Stufen

- Phase 2: Beispiel-Templates eingearbeitet, Tarife final, Live mit 6 echten Logins.
- Richtung L3: Auto-ZIP am Monatsanfang (nach Vertrauensaufbau), Reminder-Mail
  scharfschalten (`reminder._send`), evtl. direkter Versand an die Treuhand.
