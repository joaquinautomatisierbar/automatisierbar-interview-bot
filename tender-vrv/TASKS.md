# vRv Ausschreibung: Aufgaben-Board

> Quelle für das Hub-Projekt "vRv Ausschreibung". Status: `[ ]` offen · `[~]` läuft · `[x]` erledigt. Owner-Kürzel: J=Joaquin, N=Nico, T=Tej, P=Patrik, C=Claude. Stand: 10.7.2026.

## Lane WS0: Scaffold + Recherche (bis 18.7.)

- [x] 0.1 Projekt-Scaffold `tender-vrv/` (C, 10.7.)
- [~] 0.2 Hub-Projekt anlegen mit diesen Lanes (C+J, bis 12.7.)
- [x] 0.3 decisions/log.md Eintrag (C, 10.7.)
- [x] 0.4 Dossier A: pebeFinance Integrationsflächen (C, 10.7.) — Kernbefunde: kein API, CSV-Import braucht "Schnittstellen"-Lizenz, camt/QR als Zahlungs-Bus, ACHTUNG "pebe mobile" existiert (Einwand vorbereiten)
- [x] 0.5 Dossier B: Software-Landschaft CH (C, 10.7.) — keine Suite mit pebe-Schnittstelle; gefährlichster Pitch: AbaImmo+AbaSmart; Mitbewerber-Landkarte drin
- [x] 0.6 Dossier C: Variante Microsoft (C, 10.7.) — Planner-Grenzen verifiziert (20 Checklistenpunkte, kein GPS); Power Apps/Field Service als Preisanker; CH-Preise drin
- [x] 0.7 Dossier D: Security/Compliance-Katalog (C, 10.7.) — BVSA/OAK-BV-statt-FINMA präzis belegt + sprechfähige Bausteine; Hosting-Empfehlung Exoscale/Infomaniak
- [ ] 0.8 vRv-Deep-Recon: LinkedIn Schmid/Böni/Guldimann/Kunz, Facts-Seite, Handelsregister, Stiftungs-Mandate (N+C, bis 15.7.) — "mibo" = Mirjam Böni bereits identifiziert
- [x] 0.9 **Dossier E: Teilbereichs-Machbarkeitsanalyse** (C, fertig 10.7., 8 Tage vor Soll) — 17 Teilbereiche bewertet; die EINE echte Debatte ist E4 Endpoints (selbst = 150-250 Lernstunden MD-102 + Helpdesk-Bindung vs. ~CHF 2'500/Mt wiederkehrend); Partner-Longlist Region drin (Ansprache erst NACH 5.8., Doppelrollen-Risiko)
- [ ] 0.10 **Scope-Entscheidungs-Session** 45 min an S3 (alle 4, 21.7.) — Vorbereitung: Executive Summary + E4 in research/dossier-e-machbarkeit.md lesen; Entscheid-Spalte der Matrix füllen

## Lane WS1: Discovery-Tool

- [x] 1.0 Phase 0: Fragenkatalog v1 (61 Fragen, 8 Kapitel) in tools/vrv/catalog.py (C, 10.7.)
- [x] 1.1 v1: store.py + synthesis.py + routes.py + Auth + Registrierung + 25 Tests grün (C, 10.7.)
- [x] 1.2 v1: static/vrv.html komplett, Browser-Smoke bestanden (Login → Antwort → Disk → Zähler 45/46 → Meeting-Modus) (C, 10.7.)
- [x] 1.3 v1: **LIVE auf cockpit.automatisierbar.ch/vrv** (C, 10.7.) — sichere Datei-Deploy-Methode (kein git reset, VPS-Prod-Änderungen unangetastet, Backup api.py.bak-vrv-*); Passwort `vRv-Discovery-2026$672e` + VRV_DATA_DIR=/srv/cockpit/vrv_data in /etc/cockpit/env; Live-Smoke ok, /book + /interview unverändert 200. Erster echter Brief-Lauf sobald Antworten drin sind
- [ ] 1.4 Joaquin-Review + Team-Walkthrough des Tools (J, bis 22.7.) — einfach cockpit.automatisierbar.ch/vrv am Handy öffnen
- [x] 1.5 v2: **Client-Vorab-Seite LIVE** /vrv/kunde (C, 10.7., 14 Tage vor Soll) — Link für vRv: `https://cockpit.automatisierbar.ch/vrv/kunde?k=Y-nEjyA6pcjrL-Qo9DqvZ-it` (Token in /etc/cockpit/env; Token löschen = Zugriff widerrufen). Versand an Schmid erst mit Vorab-Mail 4.1 nach Halt-Gate
- [ ] 1.6 v2: Prototyp-Spec-Export (C, bis 28.7., darf nach dem 5.8. rutschen)
- [ ] 1.7 Ernstfall-Test im Mock-Meeting S7 (alle, 1./2.8.)

## Lane WS2: Upskilling (Sessions Di/Fr, 18:00 vorgeschlagen)

- [ ] 2.0 Session-Termine im Team fixieren (J, "legen wir später fest" 10.7.) — Vorschlag bleibt Di/Fr 18:00
- [x] 2.1 Primer + Quiz Modul 4 Immobilien-Domäne/Order2Cash/pebe FERTIG (C, 10.7.) → upskilling/modul-4-primer.md + modul-4-quiz.md; S1-Owner Nico, Termin folgt aus 2.0
- [ ] 2.2 Primer + Quiz Modul 1 O365/Power Platform (C bis 16.7.) → S2 Fr 17.7. (Owner T)
- [ ] 2.3 Primer + Quiz Modul 2 Cybersecurity/IT-Infra (C bis 20.7.) → S3 Di 21.7. (Owner J) + Scope-Session
- [ ] 2.4 Primer + Quiz Modul 3 Schweizer Compliance (C bis 23.7.) → S4 Fr 24.7. (Owner P)
- [ ] 2.5 Primer + Quiz Modul 6 Integrations-Architektur (C bis 27.7.) → S5 Di 28.7. (Owner T)
- [ ] 2.6 Primer + Quiz Modul 5 Projektleitung/Offerten (C bis 30.7.) → S6 Fr 31.7. (Owner J)
- [ ] 2.7 Fragen-Bank "Was Schmid fragen wird" (50 Fragen + Musterantworten) (C, bis 25.7.)
- [ ] 2.8 Mock-Meeting S7: Claude spielt Schmid/Guldimann/Kunz (alle, Sa 1.8. oder So 2.8.)
- [ ] 2.9 Generalprobe S8: Deck, Demo, Tech-Check (alle, Mo 3.8. oder Di 4.8.)

## Lane WS3: Präsentation + Unterlagen

- [ ] 3.1 Company-Deck ~15 Slides, Brand-Look Website (C baut, T owned Inhalt; Gerüst bis 18.7., v1 bis 24.7., final bis 31.7.)
- [ ] 3.2 Live-Demo-Dreh: Hub + Walk-in PWA + Ausgaben-PWA, Skript + Fallback-Screenshots (T+J, bis 27.7.)
- [ ] 3.3 Referenzblätter Juglans/Bieri/KnowGravity/Gränacher (C entwirft bis 20.7.; Freigaben: T=Juglans, N=Bieri, J=KnowGravity+Gränacher, bis 28.7.)
- [ ] 3.4 Security-Antwortpaket 2-3 Seiten (C+J, bis 28.7., braucht Hosting-Entscheid 6.3)
- [ ] 3.5 Über-uns-Material: Fotos, Bios, Rollen (P sammelt bis 20.7., C setzt bis 24.7.)
- [ ] 3.6 Print-Set 4x (P, bis 3.8.)

## Lane WS4: Meeting-Playbook 5.8.

- [ ] 4.1 Vorab-Mail an Rolf Schmid: Agenda, Teilnehmer, Besichtigung Hauswartung, optional Fragebogen-Link (C entwirft bis 15.7., N+J Review, Versand bis 22.7. nach Halt-Gate)
- [ ] 4.2 Rollenverteilung entscheiden (Team in S6, 31.7.) — Vorschlag: N Gespräch, J Technik+Tool, T Demo+Notizen, P optional
- [ ] 4.3 Ablauf-Drehbuch 10/15/60/10 mit BAMFAM-Abschluss (C, bis 25.7.)
- [ ] 4.4 Red-Team-Drill mit Fragen-Bank (alle, in S7)
- [ ] 4.5 Tech-Kit: Laptop+iPad, Hotspot, Offline-Fallbacks, Adapter, Visitenkarten (P, bis 3.8.)

## Lane WS5: Offerte + Prototyp

- [ ] 5.1 Offerten-Skelett nach ihrer Kapitelstruktur (C, Gliederung bis 22.7. nach Scope-Entscheid, final bis 31.7.)
- [ ] 5.2 Architektur-Varianten-Papier A/B/C (C+J, bis 27.7.)
- [ ] 5.3 Preismodell-Optionen: bezahlte Phasen, kein Gratis-Prototyp (J+C, bis 31.7.)
- [ ] 5.4 Demo-Asset "Muster-Slice" Go/No-Go nach 0.10, dann Build (J, Entscheid 21.7.)
- [ ] 5.5 SLA-Baukasten Bronze/Silber/Gold (C, bis 27.7.)

## Lane WS6: Firmen-Gaps

- [ ] 6.1 Versicherung: Anfragen an AXA/Mobiliar/Zurich/Helvetia/Broker raus (P mit C-Template, bis 14.7.; Offerten in Hand bis 1.8.; Entscheid J)
- [ ] 6.2 Rechtsform-Story festlegen + GmbH-Fahrplan (J, bis 31.7.)
- [ ] 6.3 CH-Hosting-Standard definieren: Infomaniak/Exoscale/Azure CH + Kostenblatt (J+C, bis 27.7.)
- [ ] 6.4 Referenz-Freigaben einholen (N koordiniert, bis 28.7.)
- [ ] 6.5 Datenschutz-Statement + AVV-Template (C, Review J, bis 1.8.)

## Meilensteine

| Datum | Meilenstein |
|---|---|
| 14.7. | Dossiers A-D fertig, S1 gehalten, Versicherungsanfragen raus |
| 18.7. | Dossier E fertig, Tool v1 funktionsfähig, Deck-Gerüst |
| 21.7. | **Scope-Entscheid gefallen** (S3) |
| 22.7. | Vorab-Mail an Schmid raus |
| 24.7. | Client-Vorab-Seite live, Deck v1 |
| 28.7. | Referenz-Freigaben da, Architektur-Papier + Security-Paket fertig |
| 1.8. | Versicherungs-Offerte in Hand, Mock-Meeting |
| 3./4.8. | Generalprobe, alles gedruckt + gepackt |
| **5.8.** | **Termin bei vRv, Solothurn** |
| 8.8. | Offerten-Rohfassung aus Tool-Export |
