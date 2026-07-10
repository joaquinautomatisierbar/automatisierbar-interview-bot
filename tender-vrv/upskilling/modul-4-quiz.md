# Modul 4 · Quiz + Drill

> 15 min in Session 1, ohne Primer offen. Lösungen zuunterst, erst nach dem Ausfüllen anschauen. Bestehensgrenze fürs Selbstvertrauen: 10 von 12.

## Quiz (12 Fragen)

1. Nenne die 8 Stationen von Order2Cash in der richtigen Reihenfolge.
2. An welcher Stelle des Prozesses geht bei Verwaltungen mit eigener Hauswartung erfahrungsgemäss am meisten Geld verloren, und warum?
3. Was ist der Unterschied zwischen Bewirtschaftung und Hauswartung bei vRv, und wer leitet was?
4. Was heisst "Regie" bzw. "Regiearbeiten"?
5. Welche pebeFINANCE-Module gibt es? Nenne mindestens fünf.
6. Warum ist das REST-API aus der pebe-Werbung KEIN Argument für unsere Integration, und was ist der belegte Integrationsweg stattdessen?
7. Was ist "pebe mobile", was kann es, was kann es nicht, und warum müssen WIR es zuerst erwähnen?
8. Wie fliesst der Zahlungseingang ohne pebe-API zurück in den Prozess? Nenne die zwei Standards.
9. Welche Lizenz-Voraussetzung hat der CSV-Buchungsimport in pebeFINANCE?
10. Ein Abacus-Partner präsentiert AbaImmo + AbaSmart. Nenne drei ehrliche Gegenargumente aus vRv-Sicht.
11. Welche zwei Branchen-Schmerzpunkte bauen wir bewusst NICHT nach, und warum ist genau das glaubwürdig?
12. Wer sind Rolf Schmid, Mirjam Böni, Ivan Guldimann und Florian Kunz, und was bedeutet jede dieser Personen für unser Angebot?

## Drill (offene Transfer-Fragen für die Runde, je 2 min)

D1. Guldimann sagt: "Wir haben doch Excel und es funktioniert." Antworte in 3 Sätzen ohne Technik-Jargon.
D2. Schmid fragt: "Warum soll ich einem 4-Personen-Team einen Prozess anvertrauen, an dem meine Verrechnung hängt?" Antworte ehrlich.
D3. Kunz fragt: "Meine Leute sind Handwerker, keine Computerleute. Was ändert sich für die konkret?" Beschreibe den Tag eines Hauswarts mit der App in 4 Sätzen.
D4. Böni fragt: "Was passiert mit unseren Daten, wenn wir in drei Jahren nicht mehr mit Ihnen arbeiten?" (Vorgriff auf Modul 3, trotzdem sprechfähig sein.)
D5. Schmid sagt: "Microsoft hat uns eine Variante mit Planner und Power Automate skizziert." Erste Reaktion in 2 Sätzen (wertschätzend, nicht abwertend).

---

## Lösungen

1. Auftrag entsteht → planen → umsetzen → bestätigen → dokumentieren → Leistung erfassen/messen → verrechnen → Zahlungseingang.
2. Zwischen Umsetzen und Leistungserfassung (Station 3 bis 6): Regieleistung wird erbracht, aber nie oder verspätet erfasst und darum nie verrechnet. Zettel und Gedächtnis sind die Lecks.
3. Bewirtschaftung = Betreuung der Liegenschaften im Auftrag der Eigentümer (Leiter: Ivan Guldimann). Hauswartung = eigenes operatives Team, dessen Leistungen verrechnet werden (Leiter: Florian Kunz). Zwei Abteilungen, ein Prozess.
4. Arbeiten nach Aufwand (Stunden + Material) statt Pauschale; genau diese Leistungen müssen einzeln erfasst und verrechnet werden.
5. Finanzbuchhaltung, Debitoren, Kreditoren, Anlagenbuchhaltung, Lohn (swissdec), Leistungserfassung, Fakturierung, Wertschriftenbuchhaltung.
6. Das beworbene REST-API gehört zu "pebe Live", einem separaten Cloud-Produkt für Kleinfirmen mit eigener Datenhaltung, nicht zu vRvs pebeFINANCE. Belegter Weg: dateibasierter Import (CSV/Excel-Buchungsimport, evtl. Faktura-Import) plus Bankstandards; Formatspezifikation kommt von pebe AG direkt.
7. Offline-App der pebe AG (CHF 5/User/Monat) für Leistungs- und Spesenerfassung mit Belegfotos. Kann keine Disposition, keine Checklisten, keine Auftragssteuerung, keine Kommunikation. Wenn Schmid sie zuerst erwähnt, wirkt unsere Lösung wie ein teurer Ersatz für eine 5-Franken-App; wenn wir sie zuerst einordnen, zeigt es Sattelfestigkeit.
8. Rechnung mit QR-Referenz raus; Zahlungseingang kommt als camt.053/054-Meldung von der Bank zurück und wird in pebe automatisch abgeglichen. Den Status lesen wir aus pebe-Export oder direkt aus den camt-Dateien.
9. Die optionale Lizenz "Schnittstellen". Ob vRv sie hat, ist Frage c1/c3; falls nicht, gehört sie als Kostenposition in die Offerte.
10. (a) Kompletter Wechsel der Buchhaltungswelt: pebe raus, Abacus rein, betrifft auch die Treuhand-Seite. (b) Klassisches ERP-Einführungsprojekt plus laufende Lizenzkosten pro Nutzer/Objekt. (c) Generische Service-App statt vRv-exaktem Prozess, und die Stiftungs-/BVG-Administration bleibt trotzdem aussen vor. (Bonus: Die Ausschreibung verlangt wörtlich die Integration von pebeFinance, nicht dessen Ablösung.)
11. Nebenkostenabrechnung und Miet-/Liegenschaftsbuchhaltung: jahrzehntelange, mietrechtskonforme Domänenlogik in Standardsoftware, chancenlos und unnötig nachzubauen. Glaubwürdig, weil ein Anbieter, der offen sagt, was er NICHT baut, beim Rest ernst genommen wird.
12. Schmid: GF, eidg. dipl. Wirtschaftsprüfer, entscheidet, denkt in Belegen/Prüfpfaden/Kosten-Nutzen. Böni: Mit-Ansprechpartnerin im Verteiler, Prozess-Stimme. Guldimann: Leiter Bewirtschaftung, sein Alltag ist Stationen 1-2 und 7-8. Kunz: Leiter Hauswartung, sein Team nutzt die App; ohne seine Akzeptanz scheitert die Feld-Adoption.

### Drill-Leitplanken (keine Musterantworten auswendig, aber diese Elemente müssen vorkommen)

D1: Anerkennen, dass es funktioniert → der Verlust liegt im Unsichtbaren (nicht erfasste Regie, verspätete Verrechnung) → wir machen sichtbar und belegen, Excel bleibt als Auswertung möglich.
D2: Ehrlichkeit (junges Team) + direkte Gründerverantwortung statt wechselnder Projektleiter + Schrittweises Vorgehen mit Kontrollpunkten + Referenzen im Aufbau ehrlich benannt + Prüfpfad-Argument (alles belegt).
D3: Morgens Aufträge auf dem Handy statt Zettel → am Objekt Checkliste antippen, Foto machen, Zeit läuft mit → fertig heisst fertig, kein Abendbüro → der Rapport entsteht nebenbei.
D4: Daten gehören vRv; Export in offenen Formaten (CSV/PDF) jederzeit; vertraglich geregelt; Archiv bleibt lesbar. (Detail in Modul 3.)
D5: "Gut gedacht, und für Aufgaben, Genehmigungen und Ablage würden wir denselben Sockel wählen." Dann EINE Grenze nennen (Hauswart-Offline/GPS) und ankündigen, dass wir die Variante ernsthaft mitofferieren.
