# vRv Ausschreibung: Masterplan Vorbereitung bis 5. August 2026

> Freigegeben von Joaquin am 10.7.2026. Lebendes Dokument: Status wird in [TASKS.md](TASKS.md) gepflegt, Änderungen am Plan hier nachgezogen.

## Kontext

vR verwaltungen ag (Solothurn) hat Automatisierbar am 2.7.2026 eine Ausschreibungs-Anfrage geschickt: Order2Cash-Prozess digital abbilden, pebeFinance in die O365-Welt integrieren, Hauswart-Mobile-App, Abrechnung + Reporting. Am **5. August 2026** ist der Vor-Ort-Termin (Discovery-Besuch, danach wird die Offerte geschrieben). 26 Tage Vorbereitungszeit.

Der Plan liefert: (1) das vRv Discovery-Tool, (2) das intensive Team-Upskilling, (3) Präsentation + Unterlagen, (4) Meeting-Playbook, (5) Offerten- und Prototyp-Vorbereitung, (6) die komplette Aufgabenverteilung mit Timeline. Erster Inbound-Lead überhaupt (bisher 100% Outbound, 0 Referrals): strategisch überproportional wertvoll als erste echte Fallstudie.

**Getroffene Entscheidungen (Joaquin, 10.7.):** Task-Board im Automatisierbar Hub · Deck im Brand-Look der Website (dunkel, #15C97A) · Tool intern + Vorab-Option für vRv · Upskilling intensiv mit 2 Sessions/Woche · **Kein Gratis-Prototyp bei diesem Deal** (wirkt bei einer 28-MA-Firma billig, senkt den wahrgenommenen Wert; bezahlte Phasen, Premium-Positionierung) · **Kein Teilbereich wird vorab ausgeschlossen**: erst Machbarkeits-/Lernbarkeits-Analyse pro Teilbereich, dann objektive Team-Entscheidung mit Pros/Cons · **Kapazität:** alle 4 Vollzeit bis 7.9., danach weiterhin ~6h/Tag pro Person neben HSG; Projektplan geht von kontinuierlicher Kapazität aus.

## Fakten aus Recon (verifiziert 10.7.2026)

**vR verwaltungen ag** (vrverwaltungen.ch, moneyhouse.ch):

- ~28 Mitarbeitende / 20 FTE, ~10 Jahre, Rötipark Solothurn. Ausschreibung ging vermutlich an mehrere Anbieter (Evaluations-Kriterienkatalog "Stärken und Schwächen der Anbieter").
- 5 Geschäftsfelder: **Personalvorsorgeverwaltung** (daher BVG-Anforderungen), Immobilienverwaltung, Immobilienverkauf, **eigene Hauswartung**, Treuhand.
- Schlüsselpersonen: **Rolf H. Schmid** (GF, MBA, eidg. dipl. Wirtschaftsprüfer: wird scharfe Kosten- und Compliance-Fragen stellen), **Mirjam Böni** ("mibo" im Verteiler, laut Team-PPTX Mit-Ansprechpartnerin), **Ivan Guldimann** (Leiter Immobilienbewirtschaftung), **Florian Kunz** (Leiter Hauswartung, sein Team = Nutzer der Mobile-App), **Marc Mischler** (Treuhand).

**pebeFinance** (pebe.ch): Treuhand-Buchhaltungssoftware der pebe AG (40+ Jahre, Schweiz, .NET). Module: Fibu (mandantenfähig), Debitoren/Kreditoren, Anlagen, Lohn, **Leistungserfassung**, **Fakturierung**, Wertschriften. Kein Immobilien-Modul. Integrationsflächen laut öffentlicher Doku: **CSV-Buchungsimport**, Scanning/Archiv-Anbindung, **kein öffentliches REST-API**. Kern-Discovery-Frage: Welche Module nutzt vRv wirklich, und wo bricht der Prozess heute (vermutlich vorne: Auftragsannahme, Planung, mobile Ausführung, manuelle Übergabe in pebe).

**Vorarbeit im Repo:** Team-Entscheidungsgrundlage [entscheidungsgrundlage-team-2026-07.pptx](entscheidungsgrundlage-team-2026-07.pptx) (Risiken: pebe-API HOCH, Scope-Überdehnung HOCH; Scope-Modelle A voller Scope / B nur Automatisierung / C mit Partner). Immobilienverwaltungs-Schmerzpunkt-Hypothesen in `tools/walkin/final_script_fallback.md:81-91` (Ein-/Auszugsprotokolle, NK-Abrechnung, Handwerker-Offerten, Mieterkorrespondenz, Mahnwesen) als Discovery-Munition.

## Was die Ausschreibung verlangt (destilliert)

1. **Prozess:** Order2Cash digital: Auftrag → planen → umsetzen → bestätigen → dokumentieren → Leistung erfassen/messen → verrechnen → Zahlungseingang
2. **Integration:** pebeFinance ↔ O365 nahtlos, oder Alternativen
3. **Rahmen:** Cloud, Mobile App, GPS, Outlook-Integration, Datenschutz + KI- und Sicherheitsstrategie
4. **Umsetzung:** zentrale Aufgaben-/Auftragsplattform, Workflow-Automatisierung, Hauswart-App (Checklisten, Foto, Echtzeit-Komm mit Mietern/Eigentümern), integrierte Abrechnung + Reporting (Arbeitszeit, Material), ERP-Schnittstellen
5. **Rolle:** Lösungsanbieter erstellt **Architektur und Projektleitung**, vRv arbeitet mit
6. **Pflichtkapitel der Offerte (= ihre "Gewünschte Informationen"):** Firma/Team/Ansprechpartner · Rechenzentrum (Ort/Umfang/Art) · Datensicherheit (Organisation, Notfallkonzept, Firewalls, Berechtigungsstruktur) · Sicherheitsstandards (EndpointSecurity, Firewall, VPN, BVG allenfalls FINMA) · Mobile/AlwaysOnVPN · **Versicherungsdeckungen + Referenzen** · Offertstruktur (Netzwerk, Hardware, Betriebssoftware, SLAs mit Reaktions-/Lösungszeiten/Verfügbarkeiten) · Stärken/Schwächen (Flexibilität, Transparenz, Integration, Kosten-Nutzen) · Kosten (SaaS-Lizenzmodell / Unternehmenslizenz / Custom; Zusatzkosten Setup, Datenmigration, Schulung)
7. **Kundenidee "Variante Microsoft":** To Do + Planner + Outlook + Teams + SharePoint + Power Automate. Müssen wir ernsthaft beherrschen und fair einordnen (nie abkanzeln, der Kunde hat sie selbst vorgeschlagen).
8. **BVG-Aufbewahrung** (Art. 27i-k BVV 2): Vorsorgeunterlagen 10 Jahre nach Leistungsende bzw. bis zum 100. Altersjahr, jederzeit lesbar → revisionssichere Archivierung als Anforderung.

## Strategische Lage

- **Volltreffer aufs ICP** (Immobilien/Treuhand-KMU, backoffice-lastig). Die Hauswart-App-Anforderung (Checkliste + Foto + mobil) ist fast deckungsgleich mit bereits gebauten Assets (Walk-in PWA, Hub mobile, Ausgaben-PWA). Der Hub selbst IST eine "zentralisierte Plattform für Aufgaben/Aufträge".
- **Scope-Frage Infrastruktur/MSP (offen, wird analysiert statt ausgeschlossen):** Der Katalog fragt neben der Prozessplattform auch Bereitstellung von Netzwerk, Hardware, Betriebssoftware und Managed Services ab. Das ist weniger eine Wissens- als eine Betriebs-Frage (24/7-Verantwortung, Pikett, Hardware-Logistik, Lizenz-Reselling, Haftung). Vorgehen: **Dossier E zerlegt jeden Teilbereich** (was genau liefern/betreiben, erlernbar bis wann, Aufwand, Haftungs-/Versicherungsfolgen, Marge), dann **Team-Entscheidung je Teilbereich: selbst / mit Partner / nicht anbieten**, mit Pros/Cons. Partner-Modelle sind bei Gesamtanbietern normal und kein Makel. Am 5.8. zusätzlich klären: Wer ist der heutige IT-Partner, was soll wirklich konsolidiert werden, was ist Vorlagen-Text?
- **Compliance-Gewicht:** Personalvorsorge heisst BVG-Daten. Scope-Empfehlung (final nach Dossier E + Termin): Order2Cash/Hauswartung als Kern, Vorsorge-Kernsysteme nur nach bewusster Entscheidung. BVG-konforme Archivierung als Anforderung einplanen, Schweizer Hosting-Story Pflicht.
- **Wettbewerb:** vermutlich klassische Systemhäuser, evtl. pebe-Partner oder Immobilien-Software-Anbieter (ImmoTop2, Rimo R5, GARAIO REM, AbaImmo, Fairwalter: im Dossier verifizieren). Differenzierung: massgeschneiderte Plattform statt Lizenz-Korsett, Geschwindigkeit + kurze Lieferzyklen, 4 Gründer persönlich statt anonymer Agentur, KI-native Arbeitsweise, Transparenz. Die Evaluationskriterien (Flexibilität, Transparenz, Integration, Kosten-Nutzen) spielen uns zu. **Kein Gratis-Angebot**: Wert zeigen über Substanz (Live-Demo eigener Systeme), nicht über den Preis.
- **Kapazität:** alle 4 Vollzeit bis 7.9. (HSG-Start), danach ~6h/Tag pro Person. Der Offerten-Projektplan rechnet mit kontinuierlicher Team-Kapazität; parallel laufende Client-Builds (Bieri, Gränacher, Praxis Ulrich) werden im Wochenplan priorisiert.

## Workstreams

### WS0: Scaffold + Recherche-Sprint (10.-14.7.)

| # | Aufgabe | Owner | Details |
|---|---|---|---|
| 0.1 | Projekt-Scaffold `tender-vrv/` im Repo | Claude | PDF ablegen, Masterplan, Unterordner research/, upskilling/, templates/ |
| 0.2 | Hub-Projekt "vRv Ausschreibung" mit allen Tasks dieses Plans | Claude + Joaquin | Lanes je Workstream, Owner + Due-Dates; doppelt als Demo-Material am 5.8. |
| 0.3 | decisions/log.md Eintrag | Claude | Bucket: more customers; KPI: Offerte fristgerecht abgegeben + Termin-Qualität (alle Must-Fragen beantwortet) |
| 0.4 | Recherche-Dossier A: pebe AG + pebeFinance Integrationsflächen | Claude | Module, CSV-Formate, DMS/Scanning-Schnittstellen, pebe Live API, Partner-Programm; Fallback: anonyme Anfrage an pebe |
| 0.5 | Dossier B: Software-Landschaft Immobilienverwaltung CH | Claude | ImmoTop2, Rimo R5, GARAIO REM, AbaImmo, Fairwalter + Hauswart-/FSM-Apps; ehrliche Build-vs-Buy-Landkarte |
| 0.6 | Dossier C: Variante Microsoft seriös bewertet | Claude | Was Planner/To Do/Teams/SharePoint/Power Automate wirklich können, Grenzen (Hauswart-UX, Offline, GPS, Foto-Doku, Abrechnungstiefe), Lizenzkosten |
| 0.7 | Dossier D: Security/Compliance-Antwortkatalog | Claude | nDSG, BVG 27i-k, FINMA-Abgrenzung (wo sie NICHT greift), EndpointSecurity/VPN/AlwaysOnVPN/Firewall Begriffe + unsere Standard-Antworten |
| 0.8 | vRv-Deep-Recon | Nico + Claude | LinkedIn-Profile Schmid/Böni/Guldimann/Kunz, Facts-Seite, Handelsregister, verwaltete Liegenschaften/Stiftung. "mibo" = Mirjam Böni (erledigt via Team-PPTX) |
| 0.9 | **Dossier E: Teilbereichs-Machbarkeitsanalyse (Kernstück)** | Claude, bis 18.7. | Für JEDEN abgefragten Teilbereich (Rechenzentrum/Hosting, Netzwerk-Bereitstellung, Hardware, Betriebssoftware + Sicherheits-SW, EndpointSecurity/EDR, Firewall, VPN/AlwaysOnVPN, Managed Services/SLA-Betrieb, Datenmigration, Schulung, Projektleitung, Plattform-Bau, pebe-Integration, Mobile App, KI-Strategie, Datenschutz/BVG-Archivierung): Was genau muss geliefert/betrieben werden · erlernbar bis Projektstart? Lernpfad + Stunden · laufender Betriebsaufwand · Haftungs-/Versicherungsfolgen · Marge/Kommodität · Optionen selbst/Partner/nicht anbieten mit Pros + Cons + Empfehlung. Keine Vorab-Ausschlüsse. |
| 0.10 | Scope-Entscheidungs-Session (45 min, an S3 angehängt, ~21.7.) | alle 4 | Dossier E durchgehen, je Teilbereich entscheiden: selbst / Partner / nicht anbieten. Ergebnis fliesst in Deck, Architektur-Papier, Offerten-Skelett und Upskilling-Vertiefung |

### WS1: vRv Discovery-Tool

Kern: strukturierter Fragenkatalog nach Offerten-Kapiteln als Web-Tool (Blueprint im bestehenden Flask-Stack), drei Modi: interne Vorbereitung, Meeting-Erfassung am 5.8. (mobiltauglich, Lücken-Anzeige pro Kapitel), optionale Vorab-Ansicht für vRv per Token-Link. Exporte: Offerten-Brief.md (nach ihrer Kapitelstruktur) + Prototyp-Spec.md. Detail-Spec am Ende dieses Dokuments.

- Eigenes Blueprint `tools/vrv/` + `static/vrv.html` nach dem ausgaben-Muster, abgesicherte Registrierung in api.py; die Produktions-Interview-Routen bleiben unberührt
- Statischer Fragenkatalog (kein AI-Adaptivmodus); AI nur für Follow-up-Vorschläge pro Kapitel + die zwei Abschluss-Synthesen (claude-sonnet-4-6, Continuation-Pattern)
- 8 Kapitel A-H (Detail-Spec unten), Persistenz als flock-gesicherter JSON-Store auf Disk (nicht Notion, Begründung unten)
- Eigene fail-closed Auth (Team-Passwort + separater Client-Token für die Vorab-Ansicht); keine ungateten AI-Endpoints
- Owner: Claude baut, Joaquin reviewt, ganzes Team testet im Mock-Meeting (Session 7)

### WS2: Team-Upskilling intensiv (14.7.-4.8., 8 Sessions à 90 min, 2x/Woche)

Format pro Session: 60 min Modul (der Owner unterrichtet die anderen auf Basis meines Primers, Feynman-Prinzip) + 15 min Quiz (von mir generiert) + 15 min Q&A-Drill. Ich liefere pro Modul: kompakten Primer (10-15 Seiten destilliert, Stil wie references/library/), Quiz mit Lösungen, Drill-Fragen.

| Session | Datum (Vorschlag Di/Fr) | Modul | Owner |
|---|---|---|---|
| S1 | Di 14.7. | Kickoff + Modul 4: Immobilienverwaltungs-Domäne, Order2Cash, pebeFinance | Nico |
| S2 | Fr 17.7. | Modul 1: O365 + Power Platform (inkl. Variante Microsoft) | Tej |
| S3 | Di 21.7. | Modul 2: Cybersecurity + IT-Infrastruktur (Endpoint, Firewall, VPN/AlwaysOn, MFA, Zero Trust, Backup 3-2-1, Notfallkonzept, RBAC) **+ 45 min Scope-Entscheidungs-Session (0.10)** | Joaquin |
| S4 | Fr 24.7. | Modul 3: Schweizer Compliance (nDSG, BVG-Aufbewahrung, FINMA-Abgrenzung, Datenstandort, AVV) | Patrik |
| S5 | Di 28.7. | Modul 6: Integrations-Architektur (API vs CSV vs RPA, Middleware/n8n, Graph API, Datenmigration, revisionssichere Archivierung) | Tej |
| S6 | Fr 31.7. | Modul 5: Projektleitung + Offerten (Festpreis vs Dienstleistung vs agil, SLAs, Leistungsabgrenzung, RACI, Change Requests) | Joaquin |
| S7 | Sa 1.8. oder So 2.8. | **Mock-Meeting:** Claude spielt Schmid/Guldimann/Kunz (50 fiese Fragen), Team übt Rollen + Tool live | alle |
| S8 | Mo 3.8. oder Di 4.8. | Generalprobe: Deck-Durchlauf, Demo-Dreh, Feinschliff, Tech-Check | alle |

Zusätzlich: **Fragen-Bank "Was Schmid fragen wird"**, 50 realistische Prüfer-Fragen mit Musterantworten (Haftung, Datenleck, Konkursfall, Referenzen, Teamgrösse, Preis), als Lern- und Drill-Material.

Nach der Scope-Entscheidung (0.10) werden Module vertieft: Entscheidet ihr euch, Infrastruktur-Teilbereiche selbst anzubieten, liefert Dossier E den konkreten Lernpfad pro Bereich (Ressourcen, Übungsumgebung, Stundenbudget) und Modul 2/6 werden entsprechend erweitert. "Erlernbar egal was es kostet" ist explizit die Messlatte: Die Analyse nennt den Preis in Stunden, die Entscheidung trifft das Team.

### WS3: Präsentation + Unterlagen

| # | Aufgabe | Owner | Details |
|---|---|---|---|
| 3.1 | Company-Deck (~15 Slides, Brand-Look Website) | Claude baut, Tej owned Inhalt | Struktur: Cover · Wer wir sind (4 Gründer, selbst bauend) · Wie wir arbeiten (erst verstehen, dann bauen; kurze Lieferzyklen, früh sichtbare Ergebnisse; KI-native Entwicklung) · Portfolio (ehrlich gelabelt: Juglans deployed, KnowSpesen geliefert, Bieri MVP, Gränacher Immobilien-Pilot mit Schätzwert als Schätzung) · Unser Verständnis von vRv (Order2Cash, 5 Geschäftsfelder) · Lösungsansätze (3 Varianten inkl. faire Microsoft-Einordnung) · Sicherheit + Datenschutz · Vorgehen + Zeitplan (bezahlte Phasen, kein Gratis-Angebot) · Team + Ansprechpartner · Nächste Schritte |
| 3.2 | Live-Demo-Dreh | Tej + Joaquin | Hub (os.automatisierbar.ch) als Beweis "zentrale Aufgabenplattform, von uns gebaut, wir arbeiten selbst drin" + Walk-in PWA (mobil, Foto, Spracherfassung = Hauswart-App-Beweis) + Ausgaben-PWA (Beleg-OCR = Material-/Spesenerfassung). Demo-Skript mit Fallback-Screenshots (13 Hub-Screenshots in references/clickup-capture/, NICHT die ClickUp-Referenzbilder im screenshots/-Unterordner) |
| 3.3 | Referenzblätter (1 Seite pro Projekt) | Claude entwirft, je Kunden-Owner holt Freigabe | Juglans (Tej), Bieri (Nico), KnowGravity + Gränacher (Joaquin). Ehrlichkeitsregel: Pilot als Pilot labeln, Schätzung als Schätzung |
| 3.4 | Security-Antwortpaket (2-3 Seiten) | Claude + Joaquin | Unsere Antworten auf ihre Pflichtfragen: Hosting/Rechenzentrum (Schweizer Cloud-Story definieren!), Verschlüsselung, Berechtigungskonzept, Backup/Notfallkonzept (existiert: verschlüsselte Backups + RESTORE.md), Endpoint/VPN-Praxis, KI-Strategie (welche Daten gehen wohin, EU/CH-Verarbeitung) |
| 3.5 | Über-uns-Material | Patrik sammelt, Claude setzt | Fotos, Kurz-Bios mit echten Nachnamen, Rollen; existiert bisher nirgends (Website zeigt nur Initialen) |
| 3.6 | Print-Set | Patrik | Deck-Handout + Referenzblätter + Firmen-Onepager gedruckt, 4 Exemplare |

### WS4: Meeting-Playbook 5.8.

| # | Aufgabe | Owner | Details |
|---|---|---|---|
| 4.1 | Vorab-Mail an Rolf Schmid (bis ~22.7.) | Nico + Claude entwirft | Dank, Agenda-Vorschlag (90-120 min), Teilnehmer beidseits klären, Bitte um Besichtigung Hauswartung (Kunz' Prozesse live sehen), optional: Vorab-Fragebogen-Link (Tool-Modus 3). Versand erst nach Joaquin-Review + Halt-Gate |
| 4.2 | Rollenverteilung | Team entscheidet in S6 | Vorschlag: Nico Gesprächsführung, Joaquin Architektur/Technik + Tool-Erfassung, Tej Demo + Notizen. Patrik optional (3 Personen wirken bei 28-MA-KMU fokussierter; Entscheid beim Team) |
| 4.3 | Ablauf-Drehbuch | Claude | 10 min Vorstellung (Deck kompakt) · 15 min Demo · 60 min Discovery mit Tool (Kapitel A-H, Mengengerüst zuerst) · 10 min nächste Schritte: **BAMFAM, Offerten-Präsentationstermin direkt fixieren** |
| 4.4 | Red-Team-Vorbereitung | Claude + alle | Die 50-Fragen-Bank aus WS2, Fokus Haftung/Versicherung/Grösse/Referenzen |
| 4.5 | Tech-Kit | Patrik | Laptop + iPad geladen, Hotspot als Backup, Offline-Fallback (Screenshots/PDF-Deck lokal), Visitenkarten?, Beamer-Adapter |

### WS5: Offerte + Prototyp-Vorbereitung

| # | Aufgabe | Owner | Details |
|---|---|---|---|
| 5.1 | Offerten-Skelett | Claude | Kapitelstruktur exakt nach ihren "Gewünschte Informationen", mit Platzhaltern, die das Discovery-Tool füllt. Vorbereitet VOR dem 5.8., damit der Offerten-Sprint danach Tage statt Wochen dauert |
| 5.2 | Architektur-Varianten-Papier | Claude + Joaquin | **A: Power-Platform-first** (ihre Variante Microsoft, wir als Architekt/Integrator; ehrliche Grenzen) · **B: Custom-Plattform** (Hub-DNA: Auftrags-Board + Hauswart-PWA offline-fähig mit Foto/GPS/Checklisten + Graph-API-Anbindung an Outlook/Teams/SharePoint + pebeFinance via CSV-Buchungsimport/Leistungsschnittstelle) · **C: Hybrid** (Kern custom, Kollaboration in Teams, einfache Flows in Power Automate). Mit Trade-offs, Datenflüssen, Betriebsmodell |
| 5.3 | Preismodell-Optionen | Joaquin + Claude sparringt | **Bewusst KEIN Gratis-Prototyp bei diesem Deal** (Premium-Positionierung; weicht vom Standard-KMU-Wedge ab). Stattdessen bezahlte Phasen: Phase 1 Detailkonzept/Vorstudie (Festpreis, eigenständiger Wert: Architektur + Anforderungskatalog) · Phase 2 Pilot (Festpreis oder Kostendach) · Phase 3 Rollout + Betrieb (Plattform-Miete + Support-SLA). Antwortet direkt auf ihre Frage "Festpreis vs Dienstleistung vs Agil"; Zusatzkosten (Migration, Schulung) transparent ausgewiesen |
| 5.4 | Demo-Asset "Muster-Slice" (intern) | Joaquin | Dünner Order2Cash-Slice als VERTRIEBS-Demo für Termin/Offerte: Auftrag erfassen → Hauswart-Checkliste mobil + Foto → Rapport → Verrechnungsvorschlag/CSV-Export. Zeigt Substanz statt Rabatt; wird nie als "gratis für Sie" angeboten. Go/No-Go nach Scope-Entscheid 0.10 (nur bauen, wenn Zeitbudget es erlaubt) |
| 5.5 | SLA-Baukasten | Claude | Reaktions-/Lösungszeiten, Verfügbarkeit, Supportfenster als vordefinierte Stufen (Bronze/Silber/Gold), damit wir am Termin sprechfähig sind |

### WS6: Firmen-Gaps schliessen (parallel, nicht optional)

| # | Gap | Aufgabe | Owner | Ziel bis |
|---|---|---|---|---|
| 6.1 | **Keine Versicherung** (0 Treffer im Repo, vRv fragt explizit) | Offerten für Berufshaftpflicht + Cyber einholen (AXA, Mobiliar, Zurich, Helvetia, esurance-Broker); Claude liefert Anfrage-Template + Deckungs-Checkliste | Patrik, Entscheid Joaquin | Offerte in Hand bis 1.8., Abschluss vor Vertragsunterschrift |
| 6.2 | **Rechtsform** (informelles Einzelunternehmen, GmbH via Vater-Shell geplant) | Sprechfähige Story festlegen: "Gründung in Umsetzung, GmbH vor Vertragsstart"; company-formation-Schritte priorisieren | Joaquin | Story bis S6; GmbH-Fahrplan konkret |
| 6.3 | **Hosting-Story** (Hostinger-VPS ist keine CH-Antwort) | Schweizer Hosting-Standard für Kundenprojekte definieren (Infomaniak / Exoscale / Azure Switzerland North), Kostenblatt | Joaquin + Claude | bis S5, fliesst in Security-Paket + Offerte |
| 6.4 | Referenz-Freigaben | Jeder fragt seinen Kunden (siehe 3.3) | Nico koordiniert | bis 28.7. |
| 6.5 | Datenschutz-Statement | nDSG-Kurzerklärung + AVV-Template für Kundenprojekte | Claude, Review Joaquin | bis 1.8. |

## Timeline (Kalenderwochen)

- **W1, 10.-13.7.:** Plan-Freigabe, Scaffold, Hub-Projekt + Tasks, Dossiers A-E gestartet, Tool-Spec fixiert, Versicherungsanfragen raus, Session-Termine im Team fixiert
- **W2, 14.-20.7.:** Tool v1 (intern + Meeting-Modus) gebaut + getestet, **Dossier E fertig (18.7.)**, Primer 1+4 + Quizzes, S1 + S2, Deck-Gerüst, Referenz-Anfragen raus
- **W3, 21.-27.7.:** **Scope-Entscheidungs-Session an S3 (21.7.)**, danach Deck v1 + Architektur-Papier + Offerten-Skelett-Gliederung auf den Entscheid ausgerichtet; Tool v2 (Vorab-Ansicht + Exporte), Vorab-Mail an Schmid (Halt-Gate), S4, Demo-Dreh, Security-Paket, SLA-Baukasten
- **W4, 28.7.-3.8.:** S5 + S6, Offerten-Skelett + Preismodelle final, Mock-Meeting S7 (Tool im Ernstfall-Test), Generalprobe S8, Print-Set, Tech-Kit
- **4.8.:** Puffer/Feinschliff. **5.8.: Termin.** 6.-8.8.: Offerten-Sprint aus Tool-Export.

## Risiken

1. **Parallel-Last:** 3 laufende Client-Prototypen (Bieri, Gränacher, Praxis Ulrich) + dieses Programm. Claude übernimmt die Artefakt-Produktion; die Gründer-Rollen = Lernen, Review, Entscheide, Kundenkontakt. Wenn es eng wird: vRv priorisieren (grösster Deal in Sicht), im Wochenplan explizit machen.
2. **Ehrlichkeits-Disziplin:** Alle Referenzen sind Piloten/MVPs, eine zahlende Kundin. Nichts als "live" verkaufen, was im Aufbau ist. Ein Wirtschaftsprüfer merkt Aufschneiderei sofort; Ehrlichkeit + gezeigte Substanz (Live-Demo der eigenen Systeme) ist die stärkere Karte.
3. **Scope-Zusage ohne Analyse:** Am Termin in Begeisterung "machen wir alles selbst" zusagen, bevor Dossier E + Entscheidungs-Session durch sind. Gegenmittel: Die Scope-Entscheidung (0.10) ist VOR dem Termin gefallen und im Playbook fixiert; für Unerwartetes gilt die Formel "nehmen wir strukturiert auf und beantworten es in der Offerte verbindlich".
4. **pebe-API-Unbekannte:** Falls Dossier A keine brauchbare Schnittstelle findet, Architektur B auf CSV-Import + Datei-Workflows auslegen und das am Termin transparent so sagen ("Detailklärung mit pebe AG in Phase 1").
5. **BVG/FINMA-Tiefe:** Vorsorge-Kernsysteme nur nach bewusster Team-Entscheidung anfassen (Dossier E liefert die Analyse dazu). Archivierungs-Anforderungen (Art. 27i-k) in jeder Variante einplanen.

## Verifikation

- **Tool:** pytest (Muster tests/test_interview_features.py, gemockte Claude/Notion), lokaler End-to-End-Lauf, VPS-Smoke nach Deploy-Runbook, Ernstfall-Test im Mock-Meeting S7. Definition of done: ein kompletter Durchlauf Kapitel A-H auf dem Handy + beide Exporte generiert.
- **Primer/Quizzes:** Jede Faktenaussage quellenbelegt (Dossiers); Quiz-Lösungen gegengeprüft; Team-Feedback nach jeder Session eingearbeitet.
- **Deck:** Browser-Render-Check (Beamer-Auflösung 1280x720 + 1920x1080), Zero-Context-Test (versteht es jemand ohne Vorwissen), Ehrlichkeits-Review gegen Referenz-Status.
- **Hub-Projekt:** Alle Tasks sichtbar mit Owner + Due-Date; wöchentlicher Review im Team-Sync.
- **Gesamtprobe:** Mock-Meeting S7 + Generalprobe S8 sind die End-to-End-Tests des gesamten Programms.

Arbeitsregeln: Kundenkontakt (Vorab-Mail, Fragebogen-Link) und VPS-Deploys laufen über Halt-Gates. Das Tool schreibt in einen eigenen JSON-Store auf Disk (`data/vrv/`, gitignored), nie in Produktions-Datenbanken.

---

## WS1 Detail-Spec: vRv Discovery-Tool (code-verifiziert)

Alle Integrationspunkte wurden gegen den echten Code geprüft (Registrierungsstelle api.py:5013-5017/5028, ausgaben-Auth-Muster tools/ausgaben/routes.py:99-110, MODEL_FAST claude_client.py:15, Continuation-Loop claude_client.py:330, Token-Pattern api.py:3329-3350, Async-Synthese-Pattern api.py:268-350, Brand-Tokens home.html:14-26, gunicorn 2 Worker/300s Timeout deploy/cockpit.service:22).

### Dateien

**Neu:** `tools/vrv/__init__.py` · `tools/vrv/catalog.py` (statische CHAPTERS + QUESTIONS + Progress-Helpers, pure) · `tools/vrv/store.py` (JSON-Store, atomarer Write via os.replace + fcntl.flock, VRV_DATA_DIR zur Laufzeit gelesen, Default `data/vrv/`) · `tools/vrv/synthesis.py` (Follow-up-Vorschläge + 2 Synthesen) · `tools/vrv/routes.py` (Blueprint, lazy Imports) · `static/vrv.html` (internes SPA) · `static/vrv-kunde.html` (Client-Vorab-Seite, v2) · `tests/test_vrv.py`

**Modifiziert (3 additive Edits):** api.py (abgesicherte Blueprint-Registrierung nach Zeile 5028, Muster 5013-5017) · .gitignore (+`data/vrv/`) · deploy/cockpit.env.example (+VRV_PASSWORD, VRV_CLIENT_TOKEN, optional VRV_API_KEY/VRV_DATA_DIR, Kommentar "nur Cockpit-VPS"). Kein Caddy-Change (/vrv läuft unter cockpit.automatisierbar.ch mit).

### Fragenkatalog (8 Kapitel, ~50-70 Fragen)

A Unternehmen + Kontext · B Order2Cash Ist-Prozess · C pebeFinance + Datenflüsse · D Microsoft-365-Landschaft · E Hauswarte + mobile Abläufe · F Verrechnung + Reporting · G IT, Sicherheit + Compliance · H Projekt, Budget + Entscheidung. Jede Frage: id, chapter, text, client_text (Sie-Form-Variante), type text/choice (choice endet immer mit "Andere…", Hausregel), why_it_matters (interne Coaching-Note, geht NIE an den Client), maps_to_offer_section, priority must/nice, client_visible.

### Routen (Kurzfassung)

- `GET /vrv` Seite; `POST /api/vrv/login|logout`, `GET /api/vrv/whoami` (fail-closed: ohne VRV_PASSWORD → 503, Muster ausgaben_login)
- `GET /api/vrv/catalog|state` (Antworten + Fortschritt je Kapitel "3 von 7 Muss offen"), `PATCH /api/vrv/answer/<qid>`, `POST /api/vrv/questions` (Follow-up übernehmen), `POST /api/vrv/followups/<chapter>` (AI-Vorschläge, sync)
- `POST /api/vrv/synthesize/<brief|spec>` → 202 + Hintergrund-Thread (Status auf Disk, nie im Prozess-Speicher: 2 Worker!), `GET /api/vrv/synthesis/<kind>` Poll, `GET /api/vrv/export/<kind>.md` Download, `GET /api/vrv/health`
- v2: `GET /vrv/kunde` (?k=VRV_CLIENT_TOKEN → Session → Redirect-clean, Muster /walkin api.py:4288-4299), `GET /api/vrv/client/questions` (Whitelist-Serialisierung: nur id, client_text, type, options, client_value), `PATCH /api/vrv/client/answer/<qid>` (nur client_value, 403 für nicht-sichtbare Fragen)

Auth-Modell: `session["vrv_auth"]` (Team) strikt getrennt von `session["vrv_client"]`; Client-Session kann NIE interne Endpoints aufrufen; Env-Var-Check zuerst, damit das Entfernen von VRV_CLIENT_TOKEN nach der Ausschreibung allen Client-Zugriff widerruft (Session-Cookies leben 365 Tage).

### Datenmodell

Ein Tender = eine Datei `data/vrv/state.json`: answers je qid mit {value, note, status open/answered/skipped/unclear, source prep/meeting/client, updated_by, client_value separat (Client kann Team-Antworten nie überschreiben; UI zeigt "Vorab vom Kunden: …")}, custom_questions, followup_suggestions, synthesis-Status je kind.

**Storage-Entscheid JSON-auf-Disk statt Notion, weil:** (1) notion_session's Session-CRUD queried hart die Produktions-"Interview Datenbank" (notion_session.py:194-221, Fallback-ID Zeile 27), nur Underscore-Privates wäre generisch: fragile Kopplung; (2) Meeting-Modus braucht <100ms-Saves ohne Internet-Abhängigkeit; (3) Deploy (git pull/reset) fasst gitignorte Dateien nicht an, Präzedenz: data/voice_sessions/, .tmp/briefs; (4) die echten Deliverables sind die zwei exportierten .md-Dateien; optional v2-Button "Snapshot nach Notion" (eine Seite, via _pack) als Backup.

### Offline-Strategie am 5.8.

**Kein Service Worker** (Stale-Shell-Risiko während 4 Wochen schneller Iteration). Stattdessen: localStorage-Write-Behind-Queue (jede Antwort synchron lokal, Flush mit Retry/Backoff + online-Listener), sichtbares Badge "N Antworten lokal, noch nicht synchronisiert", Panik-Button "Antworten als JSON kopieren". Betriebsregel: App vor dem Reingehen öffnen, SPA navigiert nie. Handy-Hotspot als Backup im Tech-Kit (WS4.5).

### Synthese-Ausgaben

1. **Offerten-Brief.md** (Deutsch, Sie-Form): 8 Abschnitte (Ausgangslage · Ist-Analyse Order2Cash · Soll-Konzept pebeFinance↔M365 · Mobile Lösung Hauswarte · Verrechnung + Reporting · Rahmenbedingungen · Vorgehen + Projektorganisation · **Offene Punkte vor Offertstellung**). Grounding-Regeln: nur erfasste Antworten, Herkunft je Aussage "(Frage b3)", "Keine Angabe" bei Lücken, keine erfundenen Zahlen; offene Muss-Fragen werden dem Prompt deterministisch mitgegeben (Lücken können nicht weghalluziniert werden).
2. **Prototyp-Spec.md** (Englisch): spiegelt die bewährte generate_claude_code_prompt-Struktur (claude_client.py:711-751) + neue Sektion "Prototype Scope (In/Out)"; harte Regeln portiert (keine TBD-Platzhalter, Kundenfeldnamen als Ground Truth, "(MVP default — confirm with client)"-Marker).

### Tests (tests/test_vrv.py, offline, Muster test_interview_features.py + test_brief.py)

Katalog-Invarianten (ids unique, choice endet "Andere…", je Kapitel ≥1 Muss, Client-Subset ~10 + alle client_visible) · Store (Roundtrip, flock-Serialisierung bei 2 Writern, Caps 4000/2000, Progress-Mathe) · Auth-fail-closed-Matrix (ohne Env-Vars alles 401/503, Client-Session kommt nicht an interne Routen) · **Client-Isolation kritisch** (Roh-JSON enthält kein why_it_matters/note/value, PATCH auf nicht-sichtbare qid → 403) · Synthese (mock LLM, 202→pending→done, Fehlerpfad, text/markdown-Export) · Regressions-Guard (api-Import ohne VRV_*-Env bootet, /interview liefert weiter BOT_MARKER).

### Build-Phasen + Aufwand

- **Phase 0 (0.5 Tage, blockierend):** Fragenkatalog-Inhalte aus dem PDF + Dossiers transkribieren (~50-70 Fragen)
- **v1 (~2.5-3.5 Tage):** Package + Store + Tests → Routen + Auth → Registrierung → vrv.html (Login/Übersicht/Kapitel/Autosave/Meeting-Modus) → Brief-Synthese + Export → Deploy + Smoke
- **v2 (~1.5-2 Tage):** Client-Vorab-Seite (**bis ~24.7. live**, damit vRv 1-2 Wochen Zeit hat) → Prototyp-Spec-Export (kann nach dem 5.8. folgen) → AI-Follow-ups (erster Streichkandidat)

Gesamt ~5-6 Dev-Tage auf 3.5 Kalenderwochen: komfortabler Puffer.

### Risiko-Flags aus dem Code (nicht in diesem Feature fixen, aber wissen)

- `SESSION_COOKIE_SECURE` gilt nur auf Render (api.py:41): auf dem VPS laufen alle Auth-Cookies ohne Secure-Flag trotz HTTPS. Vorbestehend, betrifft alle Tools; separat als Fix einplanen (Joaquin entscheidet).
- Render registriert das Blueprint mit; ohne VRV_*-Env-Vars ist dort alles 401/503 (harmlos, dokumentieren).
- Runtime-Writes nur in gitignorte Pfade (tracked Dateien wie data/cockpit_budget.json NICHT imitieren, sonst brechen künftige Pulls).
