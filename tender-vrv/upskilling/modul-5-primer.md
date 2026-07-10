# Modul 5 · Projektleitung + Offerten

> Session 6, Owner: **Joaquin** (unterrichtet die anderen drei). Lesezeit ~40 min.
> Grundlage: Dossier E (E11 Projektleitung, E8 SLA), Masterplan WS5 (Phasenmodell 5.3), [offer/sla-baukasten.md](../offer/sla-baukasten.md), [offer/offerten-skelett.md](../offer/offerten-skelett.md), Ausschreibungstext ("Rolle Lösungsanbieter: erstellen Architektur und Projektleitung", "Festpreis vs. Dienstleistungsangebot vs. Agil", "Verantwortlichkeiten, Leistungsabgrenzungen").
> Warum dieses Modul: Die Ausschreibung kauft nicht nur Software, sie kauft Führung ("Architektur und Projektleitung"). E11 sagt ehrlich: Wir praktizieren das intern täglich, haben es aber noch nie als formales Kundenmandat verkauft. Dieses Modul formalisiert es. **In derselben Session (S6) fallen zudem drei Team-Entscheide, Agenda am Ende.**

## Lernziele

Nach der Session kann jeder von uns:

1. Das Phasenmodell als Vertragslogik erklären (nicht nur als Folie) und die Frage "Festpreis, Dienstleistung oder agil?" in einem Satz beantworten.
2. Die sechs Artefakte des Projekthandbuchs nennen und sagen, was in jedes gehört.
3. Eine RACI-Zeile korrekt füllen und die Leistungsabgrenzung gegen Nachfragen verteidigen.
4. Den Change-Request-Prozess so erklären, dass er nach Schutz für BEIDE Seiten klingt.
5. Eine Abnahme mit Messkriterien definieren, statt "fertig wenn fertig" zu sagen.

---

## 1. Das Phasenmodell als Vertragslogik

Drei Phasen, jede einzeln beauftragt, jede mit eigenständigem Wert (Masterplan 5.3, Deck Folie 13):

| Phase | Inhalt | Preisform | Was vRv am Ende besitzt |
|---|---|---|---|
| 1 Detailkonzept | Prozessanalyse, Architektur, Anforderungskatalog, Mengengerüst, pebe-Abklärung | **Festpreis** | Ein Dokument, mit dem auch ein anderer Umsetzer bauen könnte |
| 2 Pilot | Ein echter Teilprozess mit echten Nutzern, Messkriterien vorab | **Festpreis oder Kostendach** | Ein laufender, gemessener Teilprozess + belastbare Rollout-Zahlen |
| 3 Rollout + Betrieb | Ausweitung, Migration, Schulung; danach Betrieb | Rollout Festpreis je Etappe, **Betrieb als Monatspauschale + SLA** | Das produktive System + Servicevertrag |

**Warum kein Gesamtfestpreis vor der Analyse** (Fragen-Bank Q10, auswendig): Er wäre entweder mit Angst-Reserve überteuert oder unseriös knapp, beides zulasten des Kunden. **Die Antwortformel: "Festpreis im Rahmen, agil im Inhalt."** Festpreis pro Phase gibt Kostensicherheit; innerhalb der Phase arbeiten wir in kurzen Zyklen mit sichtbaren Zwischenständen.

**Warum das Gate nach jeder Phase UNSER Verkaufsargument ist:** Es beweist, dass wir die nächste Phase mit Qualität verdienen wollen statt mit Vertragsbindung. Ein Prüfer versteht diese Anreizlogik sofort.

## 2. Das Projekthandbuch: sechs Artefakte, nicht mehr

Formalisierung aus E11 (20-40h, Vorlagen entstehen aus diesem Modul). Mehr Papier wäre Theater, weniger wäre fahrlässig:

1. **Projektplan:** Meilensteine mit Datum, Abhängigkeiten, kritischer Pfad; wöchentlich nachgeführt.
2. **Statusreport (wöchentlich, eine Seite):** Erledigt seit letztem Mal · Nächste Schritte · Risiken mit Ampel · **Entscheide, die wir von vRv brauchen (mit Frist)**. Der letzte Punkt ist der wichtigste: Er macht Verzögerungen sichtbar, BEVOR sie unsere Schuld werden.
3. **Entscheidungs-Log:** Datum, Entscheid, wer, Begründung, Alternativen. Verhindert das "das haben wir nie so besprochen" im Monat vier.
4. **RACI-Tabelle:** siehe Abschnitt 3.
5. **Change-Request-Formular:** siehe Abschnitt 4.
6. **Abnahmeprotokoll:** siehe Abschnitt 5.

Ein benannter Gründer führt, mit Stellvertretung; vRv hat genau EINEN Ansprechpartner (Fragen-Bank Q43: "keine Projektleiter-Rotation, sondern Leute, die es sich nicht leisten können, dass es schiefgeht").

## 3. RACI, konkret für vRv

R = Responsible (macht es) · A = Accountable (verantwortet es, genau EINE Stelle) · C = Consulted (wird vorher einbezogen) · I = Informed (wird informiert). Beispielzeilen, wie sie in die Offerte (Kap. 11.4) gehören:

| Aufgabe | Wir | vRv | pebe AG | IT-Partner/Los-Partner |
|---|---|---|---|---|
| Architektur + Detailkonzept | R/A | C | C (Formatfragen) | I |
| Plattform-Bau + Tests | R/A | C (Feedback) | — | — |
| pebe-Formatspezifikation | C | I | R/A | — |
| Import-Freigabe im Betrieb | I | R/A (Buchhaltung) | — | — |
| Testdaten + Beispieldossiers | C | R/A | — | — |
| Pilot-Abnahme | C | R/A | — | — |
| Schulung Hauswarte | R/A | C (Kunz) | — | — |
| Büronetz/Endgeräte | I | A | — | R (je nach E4/E2-Entscheid) |
| Betrieb Plattform + SLA | R/A | I | — | — |

Merkregel für Nachfragen: **Ein A pro Zeile, nie zwei.** Wenn Schmid fragt "und wer ist verantwortlich, wenn X schiefgeht", ist die Antwort immer eine Zelle dieser Tabelle, nie ein Schulterzucken.

**"Mitarbeit vRv" beziffert** (Fragen-Bank Q44, gehört aktiv in die Offerte): je ein Ansprechpartner pro Bereich; Konzeptphase 1-2h/Woche für Rückfragen; Pilot: 2-3 Hauswarte machen mit; Entscheidungswege unter einer Woche; pebe-Kontaktfreigabe. Wer die Mitarbeit verschweigt, produziert den ersten Konflikt selbst.

## 4. Change Requests ohne Drama

Der Prozess schützt beide Seiten, so erklären wir ihn auch:

- **Auslöser:** Alles, was nicht im abgenommenen Anforderungskatalog der Phase steht.
- **Formular (halbe Seite):** Beschreibung · Nutzen · Aufwand + Preis · Auswirkung auf Termin · Entscheid vRv (ja/nein/später).
- **Regel:** Kein Mehraufwand ohne schriftlichen CR VOR der Umsetzung. Keine Überraschung auf der Rechnung, nie.
- **Kulanz-Grenze (intern):** Kleinigkeiten unter ~2h machen wir ohne CR, aber dokumentiert; Kulanz, die keiner sieht, ist verschenkt, also steht sie im Statusreport ("ohne Verrechnung erledigt").
- **Sammellogik:** P4-Wünsche sammeln wir und bündeln sie in Betriebsreleases statt Einzelrechnungen (passt zum Wartungsvertrag, Fragen-Bank Q49).

## 5. Abnahmen + Messkriterien

"Fertig" ist ein Messwert, kein Gefühl. Pro Phase VORHER definiert:

- **Detailkonzept:** Abnahme = vRv bestätigt, dass Prozesse korrekt beschrieben und Anforderungen vollständig priorisiert sind (Review-Frist z.B. 10 Arbeitstage, danach gilt Schweigen als offene Punkte, nicht als Abnahme; sauber regeln).
- **Pilot (das Herzstück, Fragen-Bank Q46):** Messkriterien vorab, z.B. Erfassungsquote der Regieleistungen im Pilotbereich ≥ definiertem Ziel, Zeit von Leistung bis Rechnung halbiert, Hauswart-Akzeptanz (nutzen sie die App nach Woche 4 freiwillig weiter?). Läuft parallel zum Alltag, der heutige Prozess bleibt das Netz.
- **Rollout-Etappen:** je Etappe Abnahmeprotokoll mit Mängelklassen (A blockierend: vor Abnahme beheben · B wesentlich: Frist · C kosmetisch: nächstes Release).

## 6. Leistungsabgrenzung + Teillose (die Ausschreibungs-Frage)

Die Ausschreibung fragt wörtlich nach "Verantwortlichkeiten, Leistungsabgrenzungen". Unsere Antwort hat drei Ebenen: (1) die Verantwortungsschichten aus Modul 2 (Applikation wir, Infrastruktur-Anbieter zertifiziert, Kundenumgebung vRv/Partner), (2) die RACI-Tabelle je Aufgabe, (3) das **Teillos-Modell** aus Dossier E: getrennte Verträge je Block (Plattform/Betrieb wir; Netzwerk vor Ort Partner nach unserem Pflichtenheft; Endpoints je nach E4-Entscheid), wir als Gesamtkoordinator mit ausgewiesenem Koordinationsmandat. Kein Durchlaufumsatz, keine Haftungsdurchreiche, volle Transparenz (Evaluationskriterium!).

## 7. Offerten-Handwerk (Kurzfassung, das Skelett führt)

- Struktur: exakt die Kapitel der "Gewünschten Informationen", Abdeckungs-Matrix vor Abgabe abhaken ([offer/offerten-skelett.md](../offer/offerten-skelett.md)).
- Zahlen: 3-Jahres-TCO beider Hauptvarianten nebeneinander; Zusatzkosten (Migration, Schulung, Lizenzen) einzeln; jede Zahl mit Herkunft.
- Ehrlichkeit: Piloten heissen Piloten; Schwächen-Kapitel mit echten Schwächen + Gegenmassnahme.
- Übergabe: Die Offerte wird PRÄSENTIERT (45 min, Termin wurde am 5.8. fixiert), nicht nur gemailt. Das PDF geht danach raus.
- Gültigkeit + nächster Schritt mit Datum auf der letzten Seite.

## 8. S6-Entscheid-Agenda (in dieser Session festnageln)

1. **Rollenverteilung 5.8. (Task 4.2):** Vorschlag Nico Gespräch, Joaquin Technik+Tool, Tej Demo+Notizen, Patrik optional 4. Person oder Fokus Tech-Kit/Print. Entscheiden, dann Vorab-Mail-Teilnehmersatz finalisieren.
2. **SLA-Zahlen validieren** (sla-baukasten.md §2): Können wir Silber-Reaktionszeiten neben HSG-Stundenplänen halten? Wenn nein: Zeiten anpassen, BEVOR sie in der Offerte stehen.
3. **Preismodell-Eckwerte (5.3):** Stundensatz-Basis, Phasen-1-Festpreisrahmen, Betriebs-Pauschalen-Logik. Joaquin führt, Ergebnis geht in Offerten-Kapitel 13.

---

## 9. Zehn sprechfähige Sätze (auswendig können)

1. "Ihre Frage Festpreis, Dienstleistung oder agil beantworten wir so: Festpreis im Rahmen, agil im Inhalt, pro Phase, mit einem Ausstiegspunkt nach jeder."
2. "Ein Gesamtfestpreis vor der Analyse wäre entweder mit Angst-Reserve überteuert oder unseriös knapp kalkuliert, beides ginge zu Ihren Lasten."
3. "Das Detailkonzept gehört Ihnen, auch wenn Sie danach mit jemand anderem bauen. Wir verdienen die nächste Phase mit der Qualität der laufenden."
4. "Sie bekommen jede Woche eine Seite: erledigt, nächste Schritte, Risiken, und welche Entscheide wir von Ihnen brauchen, mit Frist."
5. "In unserer Verantwortungstabelle hat jede Aufgabe genau einen Verantwortlichen. Wenn etwas schiefgeht, zeigt die Tabelle wohin, nicht der Finger."
6. "Mehraufwand gibt es nur mit schriftlichem Change Request vor der Umsetzung: Beschreibung, Preis, Terminwirkung, Ihr Entscheid. Nie eine Überraschung auf der Rechnung."
7. "Der Pilot hat vorher definierte Messkriterien; Ihr heutiger Prozess läuft parallel weiter und bleibt das Netz, bis die Kriterien erfüllt sind."
8. "Was wir von Ihnen brauchen, steht beziffert in der Offerte: ein Ansprechpartner pro Bereich, ein bis zwei Stunden pro Woche in der Konzeptphase, zwei bis drei Hauswarte im Pilot."
9. "Für Blöcke wie das Netzwerk vor Ort arbeiten wir mit spezialisierten Partnern in getrennten Losen, nach unserem Pflichtenheft, mit uns als Gesamtkoordinator. Sie sehen jeden Franken dort, wo er hingehört."
10. "Die Offerte präsentieren wir Ihnen in 45 Minuten persönlich; den Termin dafür haben wir ja bereits fixiert."

## 10. Verbindung zu den anderen Modulen

- **Modul 2/3:** Verantwortungsschichten + AVV = die vertragliche Seite derselben Abgrenzung.
- **Modul 6:** Abnahme- und Validierungsdisziplin technisch.
- **Tasks:** PL-Vorlagen (Statusreport, CR-Formular, Abnahmeprotokoll, Entscheidungs-Log) entstehen nach diesem Modul als Dateien; Preismodell 5.3; Rollen 4.2.
