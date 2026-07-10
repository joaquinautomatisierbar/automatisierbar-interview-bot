# vRv Ausschreibung: Projekt-Hub

Vorbereitung auf die Ausschreibung der **vR verwaltungen ag** (Solothurn): Order2Cash digitalisieren, pebeFinance × O365, Hauswart-App. **Vor-Ort-Termin: Mittwoch, 5. August 2026.** Danach Offerten-Sprint.

**Das ist die zentrale Einstiegsseite.** Board mit jedem Task, Owner und Status: [TASKS.md](TASKS.md). Plan dahinter: [MASTERPLAN.md](MASTERPLAN.md). Stand dieser Seite: 10.7.2026 abends.

## Status-Schnellblick

| | |
|---|---|
| **Fertig (Claude-Strecke)** | Dossiers A-E · Discovery-Tool LIVE (v1 + Kunden-Vorab-Seite) · alle 6 Modul-Primer + Quizzes · 50-Fragen-Bank · Deck-Gerüst (15 Folien) · Ablauf-Drehbuch 5.8. · Mock-Meeting-Drehbuch S7 · Offerten-Skelett · Architektur-Papier (Entwurf) · SLA-Baukasten · Hosting-Kostenblatt · Referenzblätter (Entwürfe) · Vorab-Mail (Review-Fassung) · Security-Antwortpaket (Entwurf) · Datenschutz-Statement + AVV (Entwürfe) · PL-Vorlagen |
| **Wartet auf Team** | Session-Termine (2.0, blockiert die Sessions) · Scope-Entscheid 21.7. (0.10) · Joaquin-Reviews: Vorab-Mail, Architektur, AVV, Security-Paket, Hosting-Entscheid 6.3, Tool-Walkthrough · Referenz-Freigaben (T/N/J) · Versicherungsanfragen (P) · Rechtsform-Story (J) · Über-uns-Material (P) · Demo-Dreh (T+J) · Deep-Recon (N) |
| **Nächste Meilensteine** | 21.7. Scope-Entscheid · 22.7. Vorab-Mail raus (nach Review + Halt-Gate) · 24.7. Deck v1 · 28.7. Freigaben + Architektur + Security-Paket final · 1./2.8. Mock-Meeting · 3./4.8. Generalprobe · **5.8. Termin** |

## Live-Zugänge

- **Discovery-Tool (Team):** cockpit.automatisierbar.ch/vrv · Passwort siehe [TASKS.md](TASKS.md) Task 1.3
- **Kunden-Vorab-Seite:** Link mit Token siehe Task 1.5; Versand erst mit Vorab-Mail nach Halt-Gate. Token löschen (auf dem VPS in /etc/cockpit/env) = Zugriff widerrufen
- **Betriebs-SOP zum Tool:** [../workflows/tender_vrv_discovery.md](../workflows/tender_vrv_discovery.md)

## Orientierung: alle Dateien

| Ort | Inhalt |
|---|---|
| [MASTERPLAN.md](MASTERPLAN.md) | Der freigegebene Gesamtplan (10.7.): Workstreams, Timeline, Risiken, Tool-Spec |
| [TASKS.md](TASKS.md) | **Aufgaben-Board** (Quelle fürs Hub-Projekt 0.2): alle Tasks mit Owner, Due, Stand |
| [ausschreibung-anfrage-2026-07-02.pdf](ausschreibung-anfrage-2026-07-02.pdf) / [.md](ausschreibung-anfrage-2026-07-02.md) | Original-Anfrage + durchsuchbares Transkript |
| [entscheidungsgrundlage-team-2026-07.pptx](entscheidungsgrundlage-team-2026-07.pptx) | Team-Entscheidungsgrundlage Anfang Juli (Scope-Modelle A/B/C) |
| **research/** | Dossiers: [A pebe-Integration](research/dossier-a-pebe-integration.md) · [B Software-Landschaft](research/dossier-b-software-landschaft.md) · [C Variante Microsoft](research/dossier-c-variante-microsoft.md) · [D Security/Compliance](research/dossier-d-security-compliance.md) · [E Teilbereichs-Machbarkeit](research/dossier-e-machbarkeit.md) (Grundlage Scope-Entscheid 21.7.) |
| **upskilling/** | Primer + Quiz je Modul 1-6 (alle fertig) + [50-Fragen-Bank Schmid](upskilling/fragen-bank-schmid.md) |
| **deck/** | [deck.html](deck/deck.html): 15-Folien-Gerüst im Brand-Look (Browser öffnen; N = Referentennotizen); v1 nach Team-Feedback |
| **meeting/** | [Ablauf-Drehbuch 5.8.](meeting/ablauf-drehbuch.md) (Minutenplan, BAMFAM, Notfälle) · [Mock-Meeting S7](meeting/mock-meeting-s7.md) (Personas, Szenario-Kanon, Bewertungsbogen) |
| **offer/** | [Offerten-Skelett](offer/offerten-skelett.md) · [Architektur-Varianten](offer/architektur-varianten.md) · [SLA-Baukasten](offer/sla-baukasten.md) · [Hosting-Kostenblatt](offer/hosting-kostenblatt.md) (Joaquin-Entscheid!) · [Referenzblätter](offer/referenzblaetter.md) · [Security-Antwortpaket](offer/security-antwortpaket.md) |
| **templates/** | [Vorab-Mail Schmid](templates/vorab-mail-schmid.md) · [Versicherungsanfrage](templates/versicherungsanfrage.md) · [Referenz-Freigabe](templates/referenz-freigabe.md) · [Datenschutz-Statement](templates/datenschutz-statement.md) · [AVV-Template](templates/avv-template.md) · [PL-Vorlagen/Projekthandbuch](templates/projekthandbuch-vorlagen.md) |

## Schlüsselfakten

- **Kunde:** vR verwaltungen ag, Rosenweg 2 / Rötipark, 4500 Solothurn. ~28 MA / 20 FTE. Geschäftsfelder: Personalvorsorgeverwaltung (BVG!), Immobilienverwaltung, Immobilienverkauf, eigene Hauswartung, Treuhand.
- **Kontakte:** Rolf H. Schmid (GF, MBA, eidg. dipl. Wirtschaftsprüfer) + **Mirjam Böni** ("mibo" im Verteiler). Weitere Schlüsselpersonen: Ivan Guldimann (Leiter Immobilien), Florian Kunz (Leiter Hauswartung = Nutzer der Mobile-App), Marc Mischler (Treuhand).
- **pebeFinance:** Treuhand-Buchhaltung der pebe AG. Kein öffentliches REST-API; belegte Flächen: CSV-Buchungsimport (Lizenz "Schnittstellen"), Fakturaimport (mit pebe klären), Zahlungsbus QR + camt. Detail: Dossier A.
- **Entscheidungslinien (10.7., Joaquin):** Kein Gratis-Prototyp bei diesem Deal (Premium-Positionierung, bezahlte Phasen). Kein Teilbereich vorab ausgeschlossen: Dossier E analysiert, Team entscheidet am 21.7. je Teilbereich (selbst/Partner/nicht anbieten). Kapazität: alle 4 auch nach HSG-Start ~6h/Tag.

## Discovery-Tool

Lebt in `tools/vrv/` + `static/vrv.html` (Spec in MASTERPLAN.md unten). Statischer Fragenkatalog in `tools/vrv/catalog.py`: 8 Kapitel A-H, 61 Fragen, Muss/Kann-Prioritäten, Kunden-sichtbare Teilmenge für die Vorab-Seite. Fürs Mock-Meeting: lokale Instanz starten (Anleitung in [meeting/mock-meeting-s7.md](meeting/mock-meeting-s7.md)), nie gegen die Live-Daten üben.
