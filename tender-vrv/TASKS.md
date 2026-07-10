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
- [x] 1.8 SOP [workflows/tender_vrv_discovery.md](../workflows/tender_vrv_discovery.md) (C, 10.7.) — Betrieb, Zugänge, Widerruf, Meeting-Ablauf, Edge Cases; L2 / Bike-Phase 1

## Lane WS2: Upskilling (Sessions Di/Fr, 18:00 vorgeschlagen)

- [ ] 2.0 Session-Termine im Team fixieren (J, "legen wir später fest" 10.7.) — Vorschlag bleibt Di/Fr 18:00
- [x] 2.1 Primer + Quiz Modul 4 Immobilien-Domäne/Order2Cash/pebe FERTIG (C, 10.7.) → upskilling/modul-4-primer.md + modul-4-quiz.md; S1-Owner Nico, Termin folgt aus 2.0
- [x] 2.2 Primer + Quiz Modul 1 O365/Power Platform FERTIG (C, 10.7., 6 Tage vor Soll) → upskilling/modul-1-primer.md + modul-1-quiz.md; S2-Owner Tej, Termin folgt aus 2.0
- [x] 2.3 Primer + Quiz Modul 2 Cybersecurity/IT-Infra FERTIG (C, 10.7., 10 Tage vor Soll) → upskilling/modul-2-primer.md + modul-2-quiz.md; enthält die E4-Zahlen für die Scope-Session; S3-Owner Joaquin, Termin folgt aus 2.0
- [x] 2.4 Primer + Quiz Modul 3 Schweizer Compliance FERTIG (C, 10.7., 13 Tage vor Soll) → upskilling/modul-3-primer.md + modul-3-quiz.md (Rechtslandkarte in 12 Begriffen, B-O-F-Eselsbrücke, KI-Regeln); S4-Owner Patrik, Termin folgt aus 2.0
- [ ] 2.5 Primer + Quiz Modul 6 Integrations-Architektur (C bis 27.7.) → S5 Di 28.7. (Owner T)
- [ ] 2.6 Primer + Quiz Modul 5 Projektleitung/Offerten (C bis 30.7.) → S6 Fr 31.7. (Owner J)
- [x] 2.7 Fragen-Bank "Was Schmid fragen wird" FERTIG (C, 10.7., 15 Tage vor Soll) → upskilling/fragen-bank-schmid.md: 50 Fragen in 8 Blöcken mit Musterantworten + Drill-Anleitung S7; [Stand prüfen]-Marker (Versicherung/Hosting/Rechtsform/SLA/Referenzen) vor 4.8. auflösen
- [ ] 2.8 Mock-Meeting S7: Claude spielt Schmid/Guldimann/Kunz (alle, Sa 1.8. oder So 2.8.)
- [ ] 2.9 Generalprobe S8: Deck, Demo, Tech-Check (alle, Mo 3.8. oder Di 4.8.)

## Lane WS3: Präsentation + Unterlagen

- [~] 3.1 Company-Deck ~15 Slides, Brand-Look Website (C baut, T owned Inhalt) — **Gerüst FERTIG 10.7.** (8 Tage vor Soll): deck/deck.html, 15 Folien, Browser-QA bestanden; Platzhalter-Chips (Fotos/Bios 3.5, Rechtsform 6.2, Referenz-Freigaben, Hosting 6.3, Kontakt) müssen vor S8 auf null; Referentennotizen mit Taste N; v1 nach Team-Feedback bis 24.7., final bis 31.7.
- [ ] 3.2 Live-Demo-Dreh: Hub + Walk-in PWA + Ausgaben-PWA, Skript + Fallback-Screenshots (T+J, bis 27.7.)
- [~] 3.3 Referenzblätter Juglans/Bieri/KnowGravity/Gränacher — **Entwürfe FERTIG 10.7.** (10 Tage vor Soll): offer/referenzblaetter.md (4 Ein-Seiter, ehrliche Status-Chips, je "Was das für vRv heisst"); **JETZT dran: Freigaben einholen mit templates/referenz-freigabe.md** (T=Juglans, N=Bieri, J=KnowGravity+Gränacher, bis 28.7.); Status-Chips vor Druck 3.8. aktualisieren
- [ ] 3.4 Security-Antwortpaket 2-3 Seiten (C+J, bis 28.7., braucht Hosting-Entscheid 6.3)
- [ ] 3.5 Über-uns-Material: Fotos, Bios, Rollen (P sammelt bis 20.7., C setzt bis 24.7.)
- [ ] 3.6 Print-Set 4x (P, bis 3.8.)

## Lane WS4: Meeting-Playbook 5.8.

- [~] 4.1 Vorab-Mail an Rolf Schmid — **Review-Fassung FERTIG 10.7.** (templates/vorab-mail-schmid.md, mit echtem Vorab-Fragen-Link + Versand-Checkliste); **JETZT dran: Review Nico + Joaquin**, Versand bis 22.7. NUR nach Halt-Gate; Teilnehmer-Satz braucht Rollen-Vorentscheid oder die "zu dritt"-Vereinfachung
- [ ] 4.2 Rollenverteilung entscheiden (Team in S6, 31.7.) — Vorschlag: N Gespräch, J Technik+Tool, T Demo+Notizen, P optional
- [x] 4.3 Ablauf-Drehbuch 10/15/60/10 mit BAMFAM-Abschluss FERTIG (C, 10.7., 15 Tage vor Soll) → meeting/ablauf-drehbuch.md (Rollen je Block, Kapitel-Zeitbudgets, Kürzungsplan 60 min, Notfall-Szenarien, verbotene Sätze, Debrief); Rollen = Vorschlag bis Entscheid 4.2; wird in S7/S8 geprobt
- [ ] 4.4 Red-Team-Drill mit Fragen-Bank (alle, in S7)
- [ ] 4.5 Tech-Kit: Laptop+iPad, Hotspot, Offline-Fallbacks, Adapter, Visitenkarten (P, bis 3.8.)

## Lane WS5: Offerte + Prototyp

- [~] 5.1 Offerten-Skelett nach ihrer Kapitelstruktur — **Skelett FERTIG 10.7.**: offer/offerten-skelett.md mit Abdeckungs-Matrix (jede "Gewünschte Information" → Kapitel), Quellen-Legende (TOOL/Dossier/Task) und Arbeitsablauf nach 5.8.; Scope-abhängige Kapitel (10.x) nach Entscheid 21.7. fixieren, füllen ab 6.8.
- [~] 5.2 Architektur-Varianten-Papier A/B/C — **Entwurf FERTIG 10.7.**: offer/architektur-varianten.md (gemeinsame Grundsätze, Bausteine je Variante, Entscheidungsraster, offene Punkte→Tool-Fragen); **JETZT dran: Joaquin-Review**; Scope-Entscheid 21.7. + Termin-Antworten einarbeiten, final bis 27.7.
- [ ] 5.3 Preismodell-Optionen: bezahlte Phasen, kein Gratis-Prototyp (J+C, bis 31.7.)
- [ ] 5.4 Demo-Asset "Muster-Slice" Go/No-Go nach 0.10, dann Build (J, Entscheid 21.7.)
- [x] 5.5 SLA-Baukasten Bronze/Silber/Gold FERTIG (C, 10.7., 17 Tage vor Soll) → offer/sla-baukasten.md (Prio-Definitionen, 3 Stufen mit Reaktions-/Lösungszeiten + Verfügbarkeit, moderate Pönalen-Mechanik, Abgrenzung, Sprechfassung); Zahlen in S6 gegen Kapazität + E4 validieren; Preise je Stufe folgen in 5.3

## Lane WS6: Firmen-Gaps

- [ ] 6.1 Versicherung: Anfragen an AXA/Mobiliar/Zurich/Helvetia/Broker raus (P mit C-Template, bis 14.7.; Offerten in Hand bis 1.8.; Entscheid J)
- [ ] 6.2 Rechtsform-Story festlegen + GmbH-Fahrplan (J, bis 31.7.)
- [~] 6.3 CH-Hosting-Standard definieren — **Entscheidungsvorlage FERTIG 10.7.**: offer/hosting-kostenblatt.md (Referenz-Setup, Anbieter-Vergleich mit Exoscale-Zahlen Stand 2/2026, Empfehlung Exoscale-Betrieb + Infomaniak-Offsite, 10-min-Entscheid-Checkliste); **JETZT dran: Joaquin entscheidet + zieht CHF-Preise im Portal** (bis 27.7.); danach Baustein 8.1 + AVV-Liste + SLA-Kopplung durch C
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
