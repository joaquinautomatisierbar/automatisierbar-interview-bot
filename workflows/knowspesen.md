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
| Backup (Cron, nächtlich) | `tools/spesen/backup.py` + `deploy/knowspesen-backup.sh` |
| Uptime-Probe (Cron, ~10 Min) | `tools/spesen/health_check.py` + `deploy/knowspesen-healthcheck.sh` |
| Feedback-Backlog-Alert (Cron, 6h) | `tools/spesen/feedback_alert.py` |

## Bedienung / Setup

1. **DB anlegen + seeden (einmalig):** `POST /api/spesen/setup-db` (Cockpit-Auth) →
   Tabellen + Pauschaltarife. Mit `{"seed_demo": true}` zusätzlich Demo-KnowBodies +
   Beispielbelege (Markus). Oder lokal: `python3 tools/spesen/db.py`.
2. **Login:** Magic-Link `/spesen?k=<token>` pro KnowBody (Token in `knowbodies.login_token`).
3. **Erfassen:** Foto → OCR-Vorschlag prüfen → Kategorie/Zahlungsart/Projekt → speichern.
4. **Abschliessen:** "Monat abschliessen" → ZIP herunterladen → per Outlook an die
   Buchhaltung (fertiger E-Mail-Entwurf wird angezeigt).

## Fix-Round 2 (Operator-Feedback) — neu

- **Betrag < 1 CHF / Komma-Betrag:** Geldfelder sind `type=text inputmode=decimal`;
  `parseAmount` (JS) + `capture.parse_amount` (Python) akzeptieren `0,50`, `1'200.50`
  usw. Kein "enter a valid number" mehr.
- **Volle Korrektur + Beleg-Bild oben:** Das Erfassen-Formular IST der Editor. Beim
  Antippen eines Belegs wird das Bild oben gezeigt (`GET /api/spesen/beleg/<id>/image`)
  und ALLE Felder sind editierbar (Betrag/Währung mit FX, Kategorie, Zahlungsart, Notiz,
  Projekt, weiterverrechenbar + manueller Kaffeekasse-Override). PATCH nutzt dieselbe
  FX-Auflösung wie das Erstellen. (Beleg↔Pauschale umwandeln ist bewusst nicht möglich →
  löschen + neu.)
- **Kontroll-Bestätigung beim Abschluss:** Der KnowBody muss den Satz in
  `config.ATTESTATION_TEXT` exakt abtippen (normalisiert: Gross/Klein + Leerraum egal),
  sonst kein Abschluss. Gespeichert in `monatsabschluesse` (`bestaetigung_text/von/am`)
  UND auf dem PDF + in der Buchhaltungs-Mail als Beweis.
- **Gemeinsame Kaffeekasse:** Das Amber-Kärtchen ist antippbar → Team-Sheet mit
  Gesamttotal + Aufschlüsselung pro KnowBody + Einträgen (`GET /api/spesen/kaffeekasse`,
  über alle KnowBodies). Die `< CHF 50`-Logik bleibt.
- **Transparenz/Speicherung:** Dashboard-Zeile "🔒 N Belege sicher gespeichert · letztes
  Backup vor Xh" (aus `receipts_stored` + `last_backup_at` in der belege-Response).

### Monitoring + Backup (Cron auf dem VPS)

- **Health:** `GET /api/spesen/health` prüft DB, Receipts-Schreibbarkeit, Disk, Backup-
  Alter → 200/503. `tools/spesen/health_check.py` pollt die LIVE-URL alle ~10 Min und
  alarmiert per Telegram nur bei Zustandswechsel (down/erholt) + Nach-Erinnerung alle 6h.
- **Backup:** `tools/spesen/backup.py` macht einen konsistenten SQLite-Online-Snapshot +
  tar der Receipts → `/srv/knowspesen/backups/` (rotiert, `SPESEN_BACKUP_KEEP`), verifiziert,
  schreibt `last_backup_at/ok` in `app_meta`, Telegram-Alarm bei Fehler. Off-box-Push via
  `SPESEN_BACKUP_REMOTE` (rclone/rsync) — **OFFEN: Ziel + Zugang vom Operator.**
- **Cron installieren:** siehe `deploy/knowspesen-crontab.example` (Wrapper nach
  `/srv/knowspesen/*.sh` kopieren, `chmod +x`, in die `paperclip`-crontab eintragen;
  `mkdir -p /srv/knowspesen/logs`).

### Deploy nach Änderungen

1. Geänderte Dateien nach `cockpit-vps:/srv/cockpit/app` rsyncen (Code ist noch NICHT in
   git — vor jedem VPS `git pull` committen, sonst Konflikt auf `api.py`).
2. `sudo systemctl restart knowspesen` → der Startup-Hook (`KNOWSPESEN_HOME=1`) ruft
   `db.init_db()` idempotent auf → Schema-Migration (neue Attestation-Spalten) + Re-Seed
   der Tarife laufen automatisch. Kein manuelles `setup-db` nötig.
3. Service-Worker-Cache ist auf `knowspesen-v3` erhöht → PWA einmal ganz schliessen/neu
   öffnen, damit das neue HTML kommt.

## Tests (offline, keine API-Credits)

```
python3 tools/test_spesen_pauschalen.py
python3 tools/test_spesen_currency.py
python3 tools/test_spesen_capture.py       # inkl. parse_amount (Komma/Apostroph/<1 CHF)
python3 tools/test_spesen_month_close.py
python3 tools/test_spesen_routes.py        # inkl. Bild-Endpoint, PATCH-Währung, Kaffeekasse, health, Attestation
```

## Markus-Antwort 2026-07-10 eingearbeitet

Quelle + Assets: `references/knowgravity/` (`markus-email-2026-07-10.md` + 2 Beispiel-PDFs + 3 Logos).

- ✅ **6 echte KnowBodies** → `seed.seed_knowbodies()` (sichere Zufalls-Tokens, idempotent).
  Deployment: `python3 tools/spesen/seed.py --real` → 6 Magic-Links verteilen.
- ✅ **KnowGravity-Logo + Rebrand**: Navy → Petrol/Teal (`#004040`/`#00A090`) in
  `static/spesen.html`+`.webmanifest`, PWA-Icons (`make_icons.py`, Feder-Glyph),
  `report_pdf.py`+`report_excel.py`. SW-Cache `knowspesen-v4`.
- ✅ **Regelwerk aus Beispielen** (in `config.PAUSCHALTARIFE`): Nachtessen CHF 30 (>19:30),
  Frühstück CHF 10 (<07:30), Auto-km CHF 0.70 (Firma-Anteil 5/7). `sbb_pauschale` entfernt
  (SBB = normaler Beleg via E-Ticket-Upload). CHF-50-Minimum bestätigt.
- ✅ **Monats-Grid „Verpflegung & Kilometer“** neu gebaut (nach Vorbild des Client-Blatts):
  `tools/spesen/verpflegung.py` (Engine) + `db.py` Tabellen `verpflegung_tag`/`kilometer_monat`
  + Routes `/api/spesen/verpflegung|kilometer` + PWA-Tab in `spesen.html` (Autosave) +
  Landscape-Seite im Monats-PDF + Excel-Blatt „Verpflegung“. Tests:
  `test_spesen_verpflegung.py` + `test_spesen_verpflegung_routes.py`.

## Noch offen (Markus: „ab nächster Woche“)

- **Volles Spesenreglement + Prozess-Varianten** (Halbtag/Ganztag-Zeitregeln,
  Übernachtungs-Ansatz noch `is_placeholder`, ob Übernachtung/Bahn pauschal vs. Beleg).
- **Fragen an Gubser Kalt & Partner** (MwSt pro Beleg? Konten/Kategorien? E-Mail) →
  `SPESEN_ACCOUNTANT_EMAIL` für den Versand-Entwurf.
- **Kaffeekasse/SharePoint-Ablage** + Bestätigung Lieferantenrechnung-Ausschluss.
- **Zahlungsart-Taxonomie** ggf. an Client-Schema Bar/CC/EC angleichen (aktuell nur geflaggt).
- **Preis** (Markus: „was uns der ganze Spass kosten soll“).
- **Prod-Deploy** auf `knowspesen.automatisierbar.ch` erst auf Joaquins Go.

## Selbst-Verbesserungs-Loop / nächste Stufen

- Phase 2: Beispiel-Templates eingearbeitet, Tarife final, Live mit 6 echten Logins.
- Richtung L3: Auto-ZIP am Monatsanfang (nach Vertrauensaufbau), Reminder-Mail
  scharfschalten (`reminder._send`), evtl. direkter Versand an die Treuhand.
