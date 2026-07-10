# Modul 3 · Quiz + Drill

> 15 min in Session 4, ohne Primer offen. Lösungen zuunterst. Bestehensgrenze fürs Selbstvertrauen: 10 von 12.

## Quiz (12 Fragen)

1. Wer ist beim vRv-Projekt Verantwortlicher, wer Auftragsbearbeiter, und wer bestimmt Zweck und Mittel der Datenbearbeitung?
2. Nenne die vier Kernpflichten aus Art. 9 DSG für uns als Auftragsbearbeiter.
3. Was gehört zwingend in den AVV? Nenne mindestens sechs Inhalte.
4. Warum ist bei vRv mit besonders schützenswerten Personendaten zu rechnen, und welche zwei Konsequenzen ziehen wir daraus?
5. Wer meldet was an wen bei einer Datensicherheitsverletzung, und in welcher Frist (unsere Zusage)?
6. Dürfen Personendaten in die USA? Erkläre die aktuelle Rechtslage in zwei Sätzen.
7. Die BVG-Aufbewahrungsfristen aus der Ausschreibungs-Beilage: nenne beide Fristvarianten und die Bedingung an den Datenträger.
8. Warum ist "jederzeit lesbar" über 70 Jahre eine Migrations-Anforderung, und was verlangt die GeBüV bei einer Migration?
9. Nenne vier technische Elemente eines revisionssicheren Archivs nach GeBüV-Massstab.
10. Wie lautet unsere ehrliche Scope-Grenze zwischen Order2Cash-Plattform und BVG-Archiv?
11. Zeichne die Aufsichts-Landkarte: Wer beaufsichtigt die Vorsorgeeinrichtung von vRv direkt, wer führt die Oberaufsicht, und wo kommt die FINMA tatsächlich vor?
12. Unsere vier KI-Regeln, und der eine Satz zur "alles in der Schweiz auch für KI"-Frage.

## Drill (offene Transfer-Fragen, je 2 min)

D1. Schmid: "Untersteht Ihre Lösung dann der FINMA-Aufsicht?" Antworte präzis und nutze die Gelegenheit zu glänzen.
D2. Böni: "Was passiert mit unseren Daten, wenn wir in drei Jahren nicht mehr mit Ihnen arbeiten?" (Jetzt die Vollversion, nicht der Modul-4-Vorgriff.)
D3. Schmid: "Brauchen wir für Ihr System eine Datenschutz-Folgenabschätzung?" Antworte ohne Angst zu schüren und ohne abzuwiegeln.
D4. Schmid: "Sie nutzen amerikanische KI. Ist das mit dem Schweizer Datenschutz überhaupt vereinbar?" Antworte ehrlich, ohne ins Schwimmen zu kommen.
D5. Guldimann: "Müssen wir jetzt wirklich jedes Papierchen 70 Jahre aufheben?" Entlaste ihn fachlich korrekt.

---

## Lösungen

1. vRv ist Verantwortlicher (bestimmt Zweck und Mittel), wir sind Auftragsbearbeiter, sobald Personendaten von Mietern, Eigentümern, Versicherten oder Mitarbeitenden in unserer Lösung bearbeitet werden.
2. (a) Nur so bearbeiten, wie es der Verantwortliche selbst dürfte; (b) Datensicherheit gewährleisten und mit dokumentierten TOMs belegen können; (c) Unterauftragsbearbeiter nur mit vorgängiger Genehmigung des Verantwortlichen; (d) keine entgegenstehenden gesetzlichen oder vertraglichen Geheimhaltungspflichten.
3. Gegenstand und Dauer · Art der Daten und betroffene Personen · Weisungsrecht · Vertraulichkeitspflicht der Mitarbeitenden · TOMs als Anhang · Unterauftragsbearbeiter-Regelung/-Liste · Unterstützungspflichten (Auskunftsbegehren) · Meldung von Verletzungen · Löschung/Rückgabe bei Vertragsende · Audit-/Nachweisrechte. (Sechs davon.)
4. Personalvorsorge heisst im Leistungsfall auch Invaliditäts- und damit Gesundheitsdaten (Art. 5 lit. c: besonders schützenswert). Konsequenzen: Datenminimierung/Pseudonymisierung gegenüber KI-Diensten und eine DSFA vor Produktivsetzung; insgesamt höhere Sorgfaltslatte bei TOMs.
5. Wir melden JEDE Verletzung an vRv, Zusage innert 24 Stunden nach Feststellung. vRv als Verantwortlicher meldet dem EDÖB, wenn ein hohes Risiko für die Betroffenen resultiert; wir liefern die nötigen Informationen zu.
6. Grundsatz: Bekanntgabe ohne Weiteres nur in Staaten mit angemessenem Schutzniveau (Staatenliste DSV). Für die USA gilt seit 15.9.2024 Angemessenheit für Unternehmen mit Swiss-U.S.-DPF-Zertifizierung; ohne diese braucht es Garantien wie EU-Standardklauseln. Bei uns steht jeder solche Fall im AVV.
7. Bei ausgerichteten Leistungen: 10 Jahre nach Beendigung der Leistungspflicht. Ohne Geltendmachung: bis zum vollendeten bzw. hypothetischen 100. Altersjahr der versicherten Person (Freizügigkeitsfall: 10 Jahre nach Überweisung). Datenträger: andere als Papier zulässig, sofern die Unterlagen jederzeit lesbar gemacht werden können.
8. Kein Dateiformat und kein Speichersystem lebt 70 Jahre; Lesbarkeit sichert man durch geplante Überführung auf neue Formate/Träger. GeBüV: Migration erlaubt, wenn Vollständigkeit und Korrektheit sichergestellt sind und die Migration protokolliert wird; Verfügbarkeit und Lesbarkeit müssen gewahrt bleiben.
9. PDF/A als Langzeitformat · Objektspeicher mit Versionierung und Object Lock/WORM (keine Änderung/Löschung während der Frist) · SHA-256-Hash pro Dokument plus zeitgestempelte Hash-Listen (Integrität + Speicherzeitpunkt nachweisbar) · Retention-Frist pro Dossier am Ereignis hängend, mit jährlichem Prüfjob · dokumentierte Abläufe/Protokolle · Migrationskonzept mit Restore-Tests. (Vier davon.)
10. Die Plattform ist ein operatives System (Aufträge, Checklisten, Leistungen, Verrechnung). Dokumente mit Vorsorge-Charakter werden an ein dediziertes revisionssicheres Archiv übergeben (bestehendes DMS, SharePoint+Purview oder von uns eingerichteter WORM-Speicher). Wir versprechen kein 70-Jahre-Archiv als Nebenprodukt.
11. Direktaufsicht: BVSA (BVG- und Stiftungsaufsicht Aargau, zuständig auch für Solothurn, Art. 61 BVG). Oberaufsicht: OAK BV (beaufsichtigt die regionalen Behörden; direkt nur Anlagestiftungen, Sicherheitsfonds, Auffangeinrichtung). FINMA: nur die Lebensversicherer im BVG-Geschäft (Vollversicherung, Tarifgenehmigung); eine Stiftung ist höchstens indirekt via Rückdeckung berührt.
12. Datenklassifizierung (was darf ein Modell sehen; besonders schützenswertes nicht oder pseudonymisiert) · kontrollierte Anbieter/Orte (Geschäftskunden-APIs, vertraglich kein Training, Löschfristen; Orte im AVV) · Human-in-the-loop (KI entwirft, Mensch gibt frei) · Nachvollziehbarkeit (Protokollierung, KI-Anbieter als Unterauftragsbearbeiter deklariert). Der eine Satz: "Daten liegen in der Schweiz; die KI-Verarbeitung läuft wahlweise in der EU oder in den USA unter dem Datenschutz-Rahmenwerk, vertraglich ohne Training; wer Ihnen alles inklusive KI in der Schweiz verspricht, ist Stand heute nicht ehrlich."

### Drill-Leitplanken (Elemente, die vorkommen müssen)

D1: Nein + präzise Landkarte (BVSA direkt, OAK BV oben, FINMA nur Lebensversicherer) → massgebend für das Projekt: BVG/BVV 2, DSG, kaufmännische Aufbewahrung → Bonus: "Wo Sie FINMA-Niveau als Messlatte wünschen, orientieren wir uns freiwillig am RS 2023/1: Verantwortlichkeiten, Auditierbarkeit, Datenstandort Schweiz."
D2: Vertraglich vor Unterschrift geregelt → vollständiger Export in offenen Formaten (CSV/PDF), Übergabe innert Frist, nachweisliche Löschung bei uns, Übergangsunterstützung → archivpflichtige Unterlagen liegen ohnehin im revisionssicheren Archiv und bleiben unabhängig von uns lesbar → "Ihre Daten sind Ihre Daten, kein Verhandlungspunkt."
D3: Ja, und das ist gut so: Vorsorge-Nähe kann besonders schützenswerte Daten bedeuten → wir erstellen sie gemeinsam VOR der Produktivsetzung, kurz und ehrlich (zwei Seiten, kein Gutachten) → sie beantwortet genau die Fragen, die eine Revisionsstelle stellt; Aufwand klein, Wirkung gross.
D4: Ehrlich trennen: Ihre Produktivdaten liegen in der Schweiz → an KI-Dienste geht nur Klassifiziertes, ohne besonders schützenswerte Daten, vertraglich ohne Training, mit Löschfristen → Verarbeitungsort wählbar EU oder USA-DPF, steht im AVV → und der Gegen-Anker: "Wer Ihnen alles inklusive KI in der Schweiz verspricht, ist Stand heute nicht ehrlich."
D5: Entlasten: Die Pflicht betrifft Vorsorgeunterlagen der Stiftung, nicht jedes Papier der Bewirtschaftung → kaufmännisch gelten 10 Jahre → unsere Architektur sortiert genau deshalb: operatives System für den Alltag, dediziertes Archiv nur für das, was wirklich langfristig aufbewahrt werden muss, mit Frist am Ereignis statt pauschal.
