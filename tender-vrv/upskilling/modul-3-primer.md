# Modul 3 · Schweizer Compliance (nDSG, BVG-Aufbewahrung, Aufsicht, KI)

> Session 4, Owner: **Patrik** (unterrichtet die anderen drei). Lesezeit ~40 min.
> Grundlage: [research/dossier-d-security-compliance.md](../research/dossier-d-security-compliance.md) §3 (nDSG), §4 (BVG/GeBüV), §5 (FINMA-Abgrenzung), §8 (KI); alles dort quellenbelegt (Fedlex, EDÖB, OAK BV, BVSA, FINMA). Verweise als [D §n].
> Warum dieses Modul: vRv verwaltet eine Personalvorsorge-Stiftung. Der Entscheider ist Wirtschaftsprüfer. Compliance ist hier kein Anhang, sondern ein Prüfkriterium, und die Beilage der Ausschreibung (BVG-Aufbewahrungsartikel) ist ein deutlicher Hinweis, wo Schmid hinschauen wird. Gleichzeitig gilt: Wer die Aufsichts-Landkarte präziser erklären kann als die Konkurrenz, gewinnt Vertrauen mit Wissen statt mit Grösse.

## Lernziele

Nach der Session kann jeder von uns:

1. Unsere Rolle nach Datenschutzgesetz benennen (Auftragsbearbeiter) und die vier Pflichten daraus aufzählen.
2. Erklären, was ein AVV ist und was zwingend hineingehört.
3. Die BVG-Aufbewahrung (Fristen! Träger! "jederzeit lesbar"!) technisch übersetzen und die ehrliche Scope-Grenze ziehen.
4. Die Aufsichts-Landkarte fehlerfrei zeichnen: BVSA, OAK BV, und wo FINMA wirklich vorkommt.
5. Die KI-Strategie in vier Regeln vortragen, ohne bei der US/EU-Frage ins Schwimmen zu kommen.

---

## 1. Die Rechtslandkarte in 12 Begriffen

**1 · DSG / nDSG (SR 235.1, seit 1.9.2023)** [D §3]. Das Schweizer Datenschutzgesetz ("neues DSG"). Gilt, sobald Personendaten bearbeitet werden: Mieter, Eigentümer, Versicherte, Mitarbeitende. Dazu die Verordnung DSV mit den Detail-Anforderungen an Datensicherheit.

**2 · Verantwortlicher vs. Auftragsbearbeiter** [D §3]. Der Verantwortliche bestimmt Zweck und Mittel (= vRv). Der Auftragsbearbeiter bearbeitet im Auftrag (= wir, sobald vRv-Daten in unserer Lösung liegen). Diese Rollenverteilung bestimmt fast alle Pflichten.

**3 · Art. 9 DSG: unsere vier Kernpflichten** [D §3]. (a) Nur so bearbeiten, wie es vRv selbst dürfte. (b) Datensicherheit gewährleisten können und das belegen (dokumentierte TOMs = technisch-organisatorische Massnahmen). (c) **Unterauftragsbearbeiter nur mit vorgängiger Genehmigung** (bei uns: Hosting-Anbieter, E-Mail-Dienst, KI-Anbieter; die Liste steht transparent im AVV). (d) Keine entgegenstehenden Geheimhaltungspflichten.

**4 · AVV (Auftragsbearbeitungsvertrag)** [D §3]. Der Vertrag, der das regelt. Mindestinhalt: Gegenstand und Dauer, Datenarten und betroffene Personen, Weisungsrecht, Vertraulichkeit der Mitarbeitenden, TOMs als Anhang, Unterauftragsbearbeiter-Liste, Unterstützung bei Auskunftsbegehren, Meldung von Verletzungen, Löschung/Rückgabe bei Vertragsende, Audit-Rechte. Unser Template entsteht in Task 6.5 (Review durch Joaquin, optional Anwalts-Review, CHF 500-1'500 gut investiert [E16]).

**5 · Besonders schützenswerte Personendaten (Art. 5 lit. c)** [D §3]. U.a. Gesundheitsdaten. Im Vorsorgeumfeld real: Invaliditätsfälle. Konsequenz: höhere Sorgfaltslatte, Datenminimierung, und der nächste Begriff.

**6 · DSFA (Datenschutz-Folgenabschätzung, Art. 22)** [D §3]. Pflicht bei potenziell hohem Risiko, insbesondere umfangreicher Bearbeitung besonders schützenswerter Daten. Unsere Praxis-Antwort: Vor Produktivsetzung erstellen wir gemeinsam eine kurze, ehrliche DSFA (zwei Seiten, kein 40-Seiten-Gutachten).

**7 · Meldung von Datensicherheitsverletzungen (Art. 24)** [D §3]. Der Verantwortliche meldet dem EDÖB, wenn ein hohes Risiko für Betroffene resultiert. Wir als Auftragsbearbeiter melden JEDE Verletzung an vRv, unsere Zusage: **innert 24 Stunden nach Feststellung**. (Nicht verwechseln mit den 48h für kritische Patches, Modul 2.)

**8 · Auslandsbekanntgabe (Art. 16/17)** [D §3]. Ohne Weiteres nur in Länder mit angemessenem Schutzniveau (Staatenliste Anhang 1 DSV; EU/EWR ja). USA: seit 15.9.2024 angemessen für Unternehmen, die nach dem **Swiss-U.S. Data Privacy Framework zertifiziert** sind; sonst Garantien wie EU-Standardklauseln. Merksatz: "USA geht, aber nur DPF-zertifiziert oder mit Klauseln, und es steht im AVV."

**9 · Verzeichnis der Bearbeitungstätigkeiten (Art. 12)** [D §3]. Ausnahme für Firmen unter 250 Mitarbeitenden ohne hohes Risiko; wir führen trotzdem ein schlankes Verzeichnis, weil es Prüfer-Fragen in einer Tabelle beantwortet.

**10 · BVG-Aufbewahrung (Art. 27i-k BVV 2, die Beilage der Ausschreibung!)** [D §4]. Vorsorgeeinrichtungen müssen alle Unterlagen aufbewahren, die für Vorsorgeansprüche wesentlich sind. **Fristen: 10 Jahre nach Ende der Leistungspflicht; wurden keine Leistungen geltend gemacht, bis zum 100. Altersjahr der versicherten Person.** Andere Träger als Papier sind zulässig, **sofern jederzeit lesbar machbar**. Bei Liquidation sorgen die Liquidatoren für die Aufbewahrung. Praktische Konsequenz: Planungshorizont bis 70+ Jahre; "jederzeit lesbar" ist in Wahrheit eine **Migrations-Anforderung** (kein Format lebt so lange).

**11 · GeBüV / revisionssicher (SR 221.431)** [D §4]. Der Massstab dafür, WIE elektronisch archiviert wird (kaufmännische Aufbewahrung nach OR: 10 Jahre): **Integrität** (Änderungen müssen feststellbar sein), veränderbare Träger nur mit technischem Integritätsnachweis (Signatur/**Zeitstempel**), **dokumentierte Abläufe** inkl. Protokolle, **protokollierte Migration** bei Format-/Trägerwechsel. Technische Übersetzung bei uns: PDF/A + Objektspeicher mit Versionierung und Object Lock (WORM) + SHA-256-Hashes mit Zeitstempel + Retention-Frist pro Dossier (Fristende hängt am Ereignis!) + Migrationskonzept mit Restore-Tests. Alternative in der Microsoft-Welt: SharePoint + Purview-Retention (Modul 1).

**12 · Die ehrliche Scope-Grenze** [D §4]. Die ausgeschriebene Order2Cash-Plattform ist ein **operatives System**. Sie wird nur dann zum BVG-Archiv-Thema, wenn Vorsorgeunterlagen darin entstehen oder landen. Unsere Architektur-Antwort: Die Plattform hält operative Daten; Dokumente mit Vorsorge-Charakter werden **an ein dediziertes revisionssicheres Archiv übergeben** (bestehendes DMS, SharePoint+Purview oder ein von uns eingerichteter WORM-Speicher). Wir versprechen kein 70-Jahre-Archiv als Nebenprodukt einer Task-App, und genau diese Präzision überzeugt einen Prüfer.

## 2. Die Aufsichts-Landkarte (der Glanz-Moment) [D §5]

- **Direktaufsicht über Vorsorgeeinrichtungen:** die regionalen BVG- und Stiftungsaufsichtsbehörden (Art. 61 BVG). Für Solothurn: die **BVSA** (BVG- und Stiftungsaufsicht Aargau; AG und SO haben die Aufsicht zusammengelegt).
- **Oberaufsicht:** die **OAK BV** (Oberaufsichtskommission Berufliche Vorsorge) wacht über die regionalen Behörden; direkt beaufsichtigt sie nur Anlagestiftungen, Sicherheitsfonds, Auffangeinrichtung.
- **FINMA:** beaufsichtigt in der 2. Säule **nur die Lebensversicherer** (Vollversicherungslösungen, Tarifgenehmigung). Eine Stiftung ist höchstens indirekt berührt, wenn sie Risiken bei einem Lebensversicherer rückgedeckt hat.
- **Lesart der Ausschreibungszeile "BVG allenfalls FINMA":** BVG-Pflichten zwingend; FINMA-nahe Standards (Rundschreiben 2023/1, Outsourcing-Grundsätze) als **freiwillige Messlatte**: klare Verantwortlichkeiten, Auditierbarkeit, Datenstandort Schweiz. Genau so sagen wir es am Termin (Fragen-Bank Q30).

Eselsbrücke fürs Team: **"B-O-F: BVSA direkt, OAK oben, FINMA fast nie."**

## 3. KI und Datenschutz (unsere vier Regeln) [D §8]

1. **Datenklassifizierung:** Pro Anwendungsfall ist definiert, was ein Modell sehen darf. Besonders schützenswerte Daten gehen nicht oder nur pseudonymisiert an KI-Dienste; oft reichen Metadaten (Datenminimierung).
2. **Kontrollierte Anbieter und Orte:** Nur Geschäftskunden-APIs mit vertraglichem "kein Training auf Kundendaten" und definierten Löschfristen. Verarbeitungsorte ehrlich: Daten liegen in der Schweiz, KI-Verarbeitung wahlweise EU oder USA unter DPF; **"alles inklusive KI in der Schweiz" verspricht Stand heute niemand glaubwürdig**, und wer es tut, disqualifiziert sich.
3. **Human-in-the-loop:** KI entwirft, Menschen geben frei; Autonomie steigt erst nach nachgewiesener Zuverlässigkeit.
4. **Nachvollziehbarkeit:** KI-Aufrufe protokolliert; KI-Anbieter stehen als Unterauftragsbearbeiter im AVV.

## 4. Was davon in welches Offerten-Kapitel fliesst

Kapitel 8.5 (BVG-Archivierung) ← Begriffe 10-12 · Kapitel 8.6 (Datenschutz) ← Begriffe 1-9 · Kapitel 8.7 (KI-Strategie) ← Abschnitt 3 · Kapitel 8.3 (Aufsichts-Einordnung) ← Abschnitt 2. Fertige Textbausteine liegen in [D §7]; dieses Modul macht uns MÜNDLICH sattelfest.

---

## 5. Zehn sprechfähige Sätze (auswendig können)

1. "Sobald wir Daten Ihrer Mieter, Eigentümer oder Versicherten bearbeiten, sind wir Auftragsbearbeiter nach Artikel 9 Datenschutzgesetz, und das regeln wir in einem Auftragsbearbeitungsvertrag mit dokumentierten Massnahmen."
2. "Jeder Dienstleister, den wir einsetzen, vom Hosting bis zur KI, steht namentlich im Vertrag und braucht Ihre vorgängige Genehmigung."
3. "Verletzungen der Datensicherheit melden wir Ihnen innert 24 Stunden nach Feststellung; die Meldung an den Datenschutzbeauftragten liegt dann bei Ihnen, und wir liefern Ihnen alles dafür zu."
4. "Im Vorsorgeumfeld können Gesundheitsdaten auftauchen, etwa bei Invaliditätsfällen; darum machen wir vor der Produktivsetzung gemeinsam eine kurze Datenschutz-Folgenabschätzung."
5. "Ihre Daten bleiben in der Schweiz; wo ein Hilfsdienst im Ausland verarbeitet, steht es im Vertrag, mit Rechtsgrundlage, bei den USA heisst das DPF-zertifiziert."
6. "Die BVG-Aufbewahrung heisst konkret: zehn Jahre nach Ende der Leistungspflicht, ohne Leistungsbezug bis zum hundertsten Altersjahr, jederzeit lesbar."
7. "Jederzeit lesbar über siebzig Jahre ist keine Format-, sondern eine Migrations-Anforderung: dokumentierte, protokollierte Überführung auf neue Formate, genau wie es die Geschäftsbücherverordnung verlangt."
8. "Revisionssicher heisst bei uns: Schreibschutz während der Frist, Prüfsummen mit Zeitstempel, protokollierte Abläufe, und die Frist hängt am Ereignis, nicht pauschal am Kalender."
9. "Die Aufgabenplattform ist ein operatives System; Vorsorgeunterlagen übergibt sie an ein dediziertes revisionssicheres Archiv. Wir versprechen Ihnen kein 70-Jahre-Archiv als Nebenprodukt einer Task-App."
10. "Ihre Stiftung beaufsichtigt die BVSA, darüber wacht die OAK BV; die FINMA kommt in der zweiten Säule nur bei Lebensversicherern ins Spiel. Wo Sie FINMA-Niveau als Messlatte wollen, orientieren wir uns freiwillig an deren Outsourcing-Grundsätzen."

## 6. Verbindung zu den anderen Modulen

- **Modul 2 (S3):** Die technische Seite derselben Fragen (TOMs, Backup, Verschlüsselung); 24h-Meldung vs. 48h-Patch nicht verwechseln.
- **Modul 1 (S2):** SharePoint + Purview als Microsoft-Weg für die BVG-Retention.
- **Modul 6 (S5):** Archiv-Anbindung technisch (PDF/A, Object Lock, Hash-Ketten).
- **Tasks:** AVV-Template 6.5 (bis 1.8.), Datenschutz-Statement, DSFA-Kurzvorlage.
