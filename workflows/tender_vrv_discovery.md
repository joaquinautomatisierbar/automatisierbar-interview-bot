---
autonomy-level: L2
bike-method-phase: 1
---

# vRv Discovery-Tool: Betrieb + Nutzung

> SOP für das tender-spezifische Discovery-Tool (Ausschreibung vR verwaltungen ag, Termin 5.8.2026). Freigegeben als Teil des Masterplans vom 10.7.2026 (tender-vrv/MASTERPLAN.md, WS1). Das Tool ist ein Wegwerf-Werkzeug mit Ablaufdatum nach Offertabgabe, aber mit Produktions-Disziplin gebaut, weil es am wichtigsten Termin der Firma läuft.

## Objective

Alle Informationen strukturiert erfassen, die (a) die Offerte nach der Kapitelstruktur der Ausschreibung füllen und (b) einen Prototyp-Start erlauben. Drei Modi: interne Vorbereitung (jetzt bis 4.8.), Meeting-Erfassung am 5.8. (mobil, offline-tolerant), Kunden-Vorab-Seite (10 Fragen, Sie-Form).

## Die fünf Elemente (Operator-Pflicht)

| Element | Ausprägung |
|---|---|
| **Trigger** | Manuell: Team beantwortet Fragen laufend; Meeting-Modus am 5.8.; Kunde via Token-Link nach Vorab-Mail (Halt-Gate 4.1) |
| **Datenquellen** | 61-Fragen-Katalog (tools/vrv/catalog.py, 8 Kapitel A-H), Antworten Team + Kunde, Dossiers A-E als Kontext |
| **Transformationen** | AI nur an drei Stellen: Follow-up-Vorschläge je Kapitel, Offerten-Brief.md (Deutsch, mit "(Frage b3)"-Herkunft je Aussage), Prototyp-Spec.md (Englisch). Alles andere deterministisch |
| **Entscheidungspunkte** | Mensch: jede Antwort, Übernahme von Follow-ups, Synthese-Start, Verwendung der Exporte. AI entscheidet nichts allein (L2) |
| **Destination** | JSON-Store auf VPS (VRV_DATA_DIR=/srv/cockpit/vrv_data, ausserhalb Repo/Deploys); Exporte als .md für Offerte (tender-vrv/offer/) |

## Zugänge

- **Intern:** https://cockpit.automatisierbar.ch/vrv = **vRv Hub** (Dashboard + Lernmodule + Unterlagen, seit 10.7. abends); der Fragebogen liegt unter https://cockpit.automatisierbar.ch/vrv/fragebogen · Passwort `VRV_PASSWORD` in /etc/cockpit/env (aktuell in TASKS.md 1.3 dokumentiert) · Hub-Inhalte = /srv/cockpit/app/tender-vrv auf dem VPS; Aktualisierung: `rsync -a --exclude '.DS_Store' tender-vrv/ cockpit-vps:/srv/cockpit/app/tender-vrv/` (kein Neustart nötig, Dateien werden pro Request gelesen)
- **Kunde:** https://cockpit.automatisierbar.ch/vrv/kunde?k=<VRV_CLIENT_TOKEN> · Token in /etc/cockpit/env; **Token-Zeile löschen + Neustart = Zugriff sofort widerrufen** (Session-Cookies sind damit wertlos, Env-Check kommt zuerst)
- Ohne gesetzte Env-Vars antwortet alles 401/503 (fail-closed); auf Render sind die Vars absichtlich nicht gesetzt

## Ablauf bis zum Termin

1. **Jetzt bis 4.8. (alle):** Kapitel A-H durchgehen, beantworten was intern bekannt ist, Rest bleibt offen (Muss-Zähler zeigt Lücken je Kapitel). Notizen-Feld für Kontext nutzen.
2. **Nach Joaquin+Nico-Review der Vorab-Mail (4.1, Halt-Gate!):** Kunden-Link an Schmid senden. Kundenantworten erscheinen intern als "Vorab vom Kunden", können Team-Antworten nie überschreiben.
3. **Mock-Meeting S7 (1./2.8.):** Ernstfall-Test im Meeting-Modus am Handy/iPad. Danach gefundene Reibungen fixen (Bike-Phase 1: jede Ausgabe wird beobachtet).
4. **5.8., vor dem Reingehen:** App auf beiden Geräten ÖFFNEN (SPA navigiert nie, localStorage-Queue puffert offline; Badge zeigt "N lokal, nicht synchronisiert"). Hotspot als Backup (Tech-Kit 4.5). Panik-Button kopiert alle Antworten als JSON.
5. **Im Termin:** Meeting-Modus an (grosse Touchflächen). Reihenfolge: Mengengerüst zuerst (a-Kapitel), dann B/C/E (Prozess/pebe/Hauswarte), G/H am Schluss. Muss-Fragen vor Nice-Fragen.

## Nach dem Termin (6.8.)

1. Synthese starten: intern → Synthese-Panel → Brief (202 + Poll, Status liegt auf Disk, nicht im Prozess). Bei Fehler: einmal neu starten, dann Fehlertext lesen statt raten.
2. `Offerten-Brief.md` exportieren → füllt tender-vrv/offer/offerten-skelett.md (Kapitel 2, 7.3, 7.4, 11.5, 14). Offene Muss-Fragen stehen deterministisch im Brief-Abschnitt 8, daraus die Nachfass-Mail bauen.
3. `Prototyp-Spec.md` exportieren, sobald Scope-Entscheid + pebe-Antworten da sind (darf nach dem 5.8. rutschen, Task 1.6).
4. Kunden-Token nach Offertabgabe aus /etc/cockpit/env entfernen (Widerruf).

## Edge Cases + gelernte Constraints

- **2 gunicorn-Worker:** Synthese-Status NIE im Prozess-Speicher erwarten; nur der Disk-Store zählt. UI pollt.
- **Corrupt State:** Store legt .corrupt-Sidecar an und startet leer neu statt zu crashen; Sidecar aufheben für Forensik.
- **Client-Isolation:** Client-Endpoints serialisieren über harte Whitelist (id, text, type, options, value). why_it_matters/Notizen/Team-Antworten dürfen dort nie auftauchen; Tests decken das ab (tests/test_vrv.py, 30 grün am 10.7.).
- **Deploy-Änderungen:** NUR per Datei-Kopie-Methode (Memory: cockpit-VPS hat ungecommittete Prod-Änderungen, lokaler Branch trägt fremde unpushed Commits). Ablauf + Backup-Muster in TASKS.md 1.3; py_compile vor Restart; danach /book + /interview Smoke.
- **Kein Service Worker, bewusst:** Während der Iterationswochen wäre eine stale Shell gefährlicher als der localStorage-Queue-Ansatz.
- **Caps:** Antworten 4000 Zeichen, Notizen 2000. Längeres gehört als Dokument in tender-vrv/, nicht in den Store.

## Tools

- `tools/vrv/catalog.py` (Fragen, statisch) · `tools/vrv/store.py` (flock-JSON-Store) · `tools/vrv/synthesis.py` (Follow-ups + 2 Synthesen, claude-sonnet-4-6 mit Continuation) · `tools/vrv/routes.py` (Blueprint) · `static/vrv.html` + `static/vrv-kunde.html`
- Tests: `pytest tests/test_vrv.py` (offline, mockt Claude; muss vor jedem Deploy grün sein)

## Verifikation (Definition of done je Nutzung)

Ein kompletter Kapitel-Durchlauf am Handy + beide Exporte generiert = Tool hat geliefert. Am 5.8. zählt nur: alle Muss-Fragen beantwortet oder bewusst als "unklar" markiert, nichts verloren (Queue leer synchronisiert).
