# vRv Ausschreibung: Projekt-Hub

Vorbereitung auf die Ausschreibung der **vR verwaltungen ag** (Solothurn): Order2Cash digitalisieren, pebeFinance × O365, Hauswart-App. **Vor-Ort-Termin: Mittwoch, 5. August 2026.** Danach Offerten-Sprint.

## Orientierung

| Datei | Inhalt |
|---|---|
| [MASTERPLAN.md](MASTERPLAN.md) | Der freigegebene Gesamtplan (10.7.): Workstreams, Timeline, Risiken, Tool-Spec |
| [TASKS.md](TASKS.md) | Aufgaben-Board (Quelle für Hub-Import): alle Tasks mit Owner + Due |
| [ausschreibung-anfrage-2026-07-02.pdf](ausschreibung-anfrage-2026-07-02.pdf) | Original-Anfrage |
| [ausschreibung-anfrage-2026-07-02.md](ausschreibung-anfrage-2026-07-02.md) | Transkript der Anfrage (durchsuchbar) |
| [entscheidungsgrundlage-team-2026-07.pptx](entscheidungsgrundlage-team-2026-07.pptx) | Team-Entscheidungsgrundlage (Anfang Juli, 11 Slides, Scope-Modelle A/B/C) |
| research/ | Dossiers A-E (pebe, Software-Landschaft, Variante Microsoft, Security/Compliance, Teilbereichs-Machbarkeit) |
| templates/ | Versicherungsanfrage, Referenz-Freigabe, Vorab-Mail an Rolf Schmid |
| upskilling/ | Primer + Quizzes für die 8 Team-Sessions (Di/Fr) |

## Schlüsselfakten

- **Kunde:** vR verwaltungen ag, Rosenweg 2 / Rötipark, 4500 Solothurn. ~28 MA / 20 FTE. Geschäftsfelder: Personalvorsorgeverwaltung (BVG!), Immobilienverwaltung, Immobilienverkauf, eigene Hauswartung, Treuhand.
- **Kontakte:** Rolf H. Schmid (GF, MBA, eidg. dipl. Wirtschaftsprüfer) + **Mirjam Böni** ("mibo" im Verteiler). Weitere Schlüsselpersonen: Ivan Guldimann (Leiter Immobilien), Florian Kunz (Leiter Hauswartung = Nutzer der Mobile-App), Marc Mischler (Treuhand).
- **pebeFinance:** Treuhand-Buchhaltung der pebe AG. Öffentlich dokumentiert: CSV-Buchungsimport, kein REST-API. Dossier A klärt die echten Integrationsflächen (Projekt-kritisch, Risiko HOCH laut Team-PPTX).
- **Entscheidungslinie (10.7., Joaquin):** Kein Gratis-Prototyp bei diesem Deal (Premium-Positionierung, bezahlte Phasen). Kein Teilbereich wird vorab ausgeschlossen: Dossier E analysiert jeden Teilbereich (lieferbar? erlernbar bis wann? Aufwand? Haftung?), dann Team-Scope-Entscheid am 21.7. Das ersetzt die B/C-Vorab-Empfehlung aus der Team-PPTX durch eine Entscheidung mit Datenlage.

## Discovery-Tool

Lebt in `tools/vrv/` + `static/vrv.html` (Spec in MASTERPLAN.md unten). Statischer Fragenkatalog in `tools/vrv/catalog.py`: 8 Kapitel A-H, Muss/Kann-Prioritäten, Kunden-sichtbare Teilmenge für die Vorab-Seite.
