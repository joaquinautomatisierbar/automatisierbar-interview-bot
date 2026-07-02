---
name: Befund-Automat — Praxis Tina Ulrich (Zürich)
autonomy-level: L2
bike-method-phase: 1
kpi-bucket: less-cost
client: Praxis Dr. med. Tina Ulrich (Gynäkologie, Zürich-Altstetten)
status: Remote-Build fertig (186 Offline-Checks grün); wartet auf API-Key-Sanity-Eval, Windows-Build-Smoke-Test, Kern-Concept-Antwort, Datenschutz-Entscheid, Install-Termin
owner: Joaquin
---

# Befund-Automat — Workflow SOP

Selbständige Windows-Tray-App (`tools/praxis_ulrich/`), die das HIN-Postfach der
Praxis pollt, Befund-PDFs per LLM liest, mit korrektem Titel in Aeskulap ablegt,
die Mail NUR bei Erfolg rot markiert und Dr. Ulrich die DigiSono-Zusammenfassung
per Toast + Zwischenablage liefert. Spart ~1.5h Arztzeit/Tag (ROI-Schätzung
CHF 4'042/Monat, Baseline wird am Install-Termin real gemessen).

**Warum L2 / Phase 1:** Jede Ablage ist für Dr. Ulrich sichtbar (Fähnchen + Toast)
und wird im 2-Wochen-Pilot einzeln geprüft. Eine falsche Patientenzuordnung ist die
rote Linie: EIN Vorfall stoppt die Auto-Ablage sofort (Sink → DryRun), Ursache,
Korpus-Erweiterung, Re-Eval. Phase-2-Gate: 0 falsche Zuordnungen UND ≥95%
Erkennungsquote UND ihr subjektives OK.

## Die 5 Prozess-Elemente

- **Trigger:** IMAP-Poll alle 3 Min direkt gegen `imap.mail.hin.ch:993`
  (HIN Mail Token Service; läuft parallel zu Outlook + HIN Client, KEINE
  Abhängigkeit davon). UID-basiert, nie UNSEEN (Outlook setzt \Seen zuerst).
- **Data sources:** Roh-Mail (BODY.PEEK), PDF-Anhänge (PyMuPDF-Text, bei Scans
  Seiten-PNGs für Vision), die 25-Titel-Vorlagenliste (`config.TITEL_VORLAGEN`),
  State-DB (`%LOCALAPPDATA%\BefundAutomat\state.db`).
- **Transformations:** LLM-Extraktion (Name, Geburtsdatum, Berichtsdatum,
  Institution, Diagnose/Prozedere, Empfehlung, 4-Zeiler) → deterministische
  Titel-Validierung (exakter Listen-Match, sonst Freititel) + Datums-Suffix
  (Titel `MM/JJJJ`, Dateiname `MM-JJJJ`) → Dateiname `[Titel]_[Nachname]_[Vorname].pdf`.
- **Decision points:** (1) kein PDF → Mail komplett ignorieren; (2) `ist_befund`
  false (Rechnung/Junk) → skip, blockiert Fähnchen NICHT; (3) Gate Nachname UND
  Geburtsdatum, sonst failed → kein Fähnchen = ihr Handarbeits-Signal;
  (4) Fähnchen nur wenn ≥1 PDF neu abgelegt UND kein Anhang failed;
  (5) Fähnchen-Fehler nach Ablage: geloggt, nie fatal.
- **Destination:** Aeskulap-Import via Sink-Interface (`filing.py`): Hotfolder
  (.part → atomisches Rename), optional +GDT-Sidecar (Format PENDING Kern
  Concept), DryRun für Harness/Eskalation. Fallback ohne Vendor-Antwort:
  "Befund-Ablage"-Ordner, manueller Drag in Aeskulap.

## Unverhandelbare Invarianten (alle im Test abgedeckt)

1. Es wird NIE eine Mail gelöscht, verschoben oder als gelesen markiert.
   Einzige Mailbox-Schreiboperation: `+FLAGS (\Flagged)` nach erfolgreicher Ablage.
   (Ausnahme: doctor.py räumt seine EIGENE Selbsttest-Mail auf.)
2. Unmarkierte Mail = unbearbeitet = sie schaut manuell (heutiger Prozess).
   Jeder Fehlerpfad mündet dorthin. Absturz ist deshalb fail-safe.
3. Erfundene Patientendaten sind der schlimmste Fehler: LLM ist instruiert null
   zu liefern statt zu raten; Sanitizer erzwingt TT.MM.JJJJ; Gate blockiert ohne
   Nachname+Geburtsdatum; Titel werden deterministisch re-validiert.
4. Dedup überlebt State-Verlust und UIDVALIDITY-Resets (SHA-256 + Message-ID
   sekundär) — die Rescan-Safety-Net kann nie doppelt ablegen.
5. Alle Status sind terminal, kein Auto-Retry: ein später Retry könnte doppelt
   ablegen, nachdem sie schon von Hand gearbeitet hat.
6. --dry-run benutzt In-Memory-State + DryRun-Sink + No-Op-Flagger: berührt
   weder Mailbox noch echte State-DB.

## Tools (alle in `tools/praxis_ulrich/`)

| Modul | Zweck |
|---|---|
| `config.py` | Single edit-point: 25 Titel, IMAP-Profile (hin/test), Poll, Sink, deutsche UI-Texte. Layered: defaults < config.json < BEFUND_* env |
| `secrets_store.py` | HIN-Token + LLM-Key via Windows Credential Locker (keyring), env-Fallback dev |
| `state.py` | SQLite: processed-Log (= Pilot-Metriken) + last_uid je UIDVALIDITY + Wochen-Backup |
| `mailbox.py` | IMAP: UID-Discovery, PEEK-Fetch, flag_red; pure PDF-Anhang-Extraktion |
| `pdf_text.py` | PyMuPDF-Text + Scan-Heuristik (<50 Zeichen/Seite) + PNG-Rendering |
| `extractor.py` | LLM-Extraktion, never-raises, Feld-Sanitizer, System-Prompt mit Titelliste |
| `providers.py` | DER Provider-Swap-Punkt: anthropic implementiert, azure-openai/local Stubs |
| `titles.py` | Titel-Validierung, Datums-Suffix, Windows-sicherer Dateiname |
| `filing.py` | Sink-Interface: Hotfolder/GDT/DryRun, atomare Writes, Kollisions-Zähler |
| `pipeline.py` | DIE Invariante: Reihenfolge extract→gate→file→flag→notify je Anhang |
| `notify.py` | Toast (winotify + PowerShell-Fallback) + Clipboard (pyperclip + clip.exe), Batch-Aggregation, Fehler-Rate-Limit |
| `main.py` | Poll-Loop + Tray (pystray), Single-Instance-Lock, --once/--dry-run/--max-per-run |
| `doctor.py` | On-Site-Selbsttest + `--stats` (Pilot-Metriken) |
| `make_corpus.py` | 14 synthetische PDFs + Goldens + 5 EMLs (`testdata/`, committed, 100% fiktiv) |
| `eval_extraction.py` | Accuracy-Gate gegen echten Provider (`--only <case>` = 1 Sanity-Call) |
| `seed_test_mailbox.py` | Harness: EML-Fixtures per APPEND in Test-Postfach (kein SMTP im ganzen Paket) |

## Tests

```bash
for t in tools/test_praxis_*.py; do python3 "$t"; done   # 186 Checks, offline, ohne Key
python3 tools/praxis_ulrich/eval_extraction.py --only austritt_usz  # 1 API-Call Sanity
python3 tools/praxis_ulrich/eval_extraction.py                      # volles Gate (~14 Calls)
```

## HIN Mail Token Runbook (Install-Termin)

1. Mit Dr. Ulrich auf apps.hin.ch einloggen (HIN-Client-Session am Praxis-PC).
2. Mail Token Service → neuen Token für "IMAP-Client / Drittanwendung" erzeugen.
3. Benutzer = HIN-ID (`config.json: hin_imap_user`), Passwort = Token →
   Credential Locker (`secrets_store`, Name `imap_password`).
4. Kill-Switch für die Praxis: Token auf apps.hin.ch widerrufen → Automat
   verliert sofort den Zugriff (und meldet Verbindungsproblem per Toast).
5. Verifikation: `doctor.py` Selbsttest (Login, UIDVALIDITY, Fähnchen-Roundtrip).

## Offene Punkte / nächste Schritte

1. **ANTHROPIC_API_KEY** in die Session bringen → `eval_extraction.py --only
   austritt_usz` (1 Call), dann Entscheid volles Gate (~14 Calls, <CHF 0.50).
2. **Vendor-Mails versenden** (Entwürfe: `tools/praxis_ulrich/vendor_drafts/`) —
   Kern Concept blockiert den finalen Sink, DigiSono ist Phase 2.
3. **Windows-Build-Smoke-Test** (deploy/befund-automat-build.md) — spec/iss sind
   auf macOS verfasst und ungetestet bis zum ersten Windows-Build.
4. **Datenschutz-Entscheid** von Dr. Ulrich (tools/praxis_ulrich/DATENSCHUTZ-ENTSCHEID.md).
5. **Install-Termin** nach deploy/befund-automat-install-checklist.md, inkl.
   ROI-Baseline-Messung und Bestätigung der 3 normalisierten Titel-Schreibweisen.
6. E2E-Harness gegen Infomaniak-Test-Postfach (seed → main --once --dry-run →
   main --once mit temp-Hotfolder) — Creds: BEFUND_TEST_IMAP_USER + BEFUND_IMAP_PASSWORD.

## Self-Improvement Loop

Pilot-Fehler → Korpus-Case ergänzen (`make_corpus.py`) → Golden dazu →
Eval erneut → Prompt/Titel-Logik nachziehen → dieses SOP aktualisieren.
Phase-Aufstieg (1→2→3) NUR durch expliziten Edit nach validiertem Pilot.
