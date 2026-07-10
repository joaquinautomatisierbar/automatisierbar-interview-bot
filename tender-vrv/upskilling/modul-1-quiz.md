# Modul 1 · Quiz + Drill

> 15 min in Session 2, ohne Primer offen. Lösungen zuunterst, erst nach dem Ausfüllen anschauen. Bestehensgrenze fürs Selbstvertrauen: 10 von 12.

## Quiz (12 Fragen)

1. Welche sechs Tools nennt vRv in ihrer "Variante Microsoft", und welche zwei Bausteine fehlen für ihren Use Case (laut Microsoft selbst)?
2. Nenne drei harte Planner-Limits, die die Hauswart-Arbeit direkt betreffen.
3. Wann ist Power Automate in M365 enthalten, und wann wird es lizenzpflichtig? Nenne die zwei Premium-Preise.
4. Was ist Dataverse, und warum ist es der Schlüssel zur Offline-Feld-App?
5. Wofür steht Entra ID, und welche drei Funktionen daraus nutzt unsere Lösung?
6. BVG-Archivierung in der Microsoft-Welt: Welche Produkte, was ist in Business Premium enthalten, und welcher Prüfpunkt gehört zur Schweizer Datenhaltung?
7. Der "Field-Service-Moment": Was kostet Dynamics 365 Field Service, und was beweist dieser Preis im Gespräch?
8. Wie lautet unsere Hochrechnung für den Lizenz-Ausbau der Variante Microsoft bei vRv (Kernszenario), und auf welchen Annahmen beruht sie?
9. Nenne zwei Plattform-Limiten, die bei einem prozesslastigen System wehtun (mit Zahl).
10. Warum kann Power Automate pebeFinance nicht direkt ansteuern, und was sind die zwei realistischen Wege?
11. "Echtzeit-Kommunikation mit Mietern über Teams": Wo ist die Grenze, und was wäre die Microsoft-Antwort mit Preis?
12. Was heisst "Baukasten mit Bauleitung" konkret? Nenne drei Governance-Punkte.

## Drill (offene Transfer-Fragen für die Runde, je 2 min)

D1. Schmid: "Wir bezahlen Microsoft schon. Warum sollen wir zusätzlich Sie bezahlen?" Antworte in 3 Sätzen.
D2. Guldimann: "Unser IT-Partner sagt, mit Power Automate lässt sich das alles abbilden." Antworte wertschätzend, ohne den Partner schlecht zu machen.
D3. Böni: "Was kostet uns die Microsoft-Variante am Ende wirklich pro Monat?" Antworte ehrlich mit Grössenordnung und dem, was die Zahl bestimmt.
D4. Kunz: "Meine Hauswarte sollen im Keller Checklisten ausfüllen. Geht das mit Planner?" Antworte ohne das Wort "nein" zu verwenden.
D5. Schmid: "Sie offerieren beides? Dann empfehlen Sie doch sicher die Variante, an der Sie mehr verdienen." Entkräfte in 2 Sätzen.

---

## Lösungen

1. Genannt: To Do, Planner, Outlook, Teams, SharePoint, Power Automate. Fehlend: Power Apps (Feld-App mit Pflichtfeldern, Kamera, GPS, offline) und Dataverse (Datenmodell, Sicherheit, Offline-Voraussetzung); dazu sinnvollerweise Power BI fürs Reporting.
2. Max. 20 Checklistenpunkte pro Task, max. 10 Anhänge, keine Pflichtfelder/Eingabetypen, Mobile offline nur eingeschränkt (iOS lesend), kein GPS, keine Zeit-/Materialfelder. (Drei davon reichen.)
3. Enthalten ("seeded"), solange nur Standard-Konnektoren (SharePoint, Outlook, Teams, Planner, To Do) im Spiel sind. Lizenzpflichtig bei Premium-Konnektoren (z.B. HTTP), Custom Connectors oder RPA: Premium USD 15/User/Monat, unattended Process-Bot USD 150/Monat.
4. Die Datenbank der Power Platform: strukturierte Tabellen mit rollenbasierter Sicherheit bis Zeilen-/Feldebene. Die Offline-Funktion für Canvas Apps setzt zwingend Dataverse als Datenquelle voraus (SharePoint reicht nicht), darum führt an Dataverse (und Premium-Lizenzen) kein Weg zur offline-fähigen Hauswart-App vorbei.
5. Microsofts Identitätssystem (früher Azure AD). Wir nutzen SSO (Login mit bestehenden vRv-Konten), MFA und Conditional Access; dadurch greift das zentrale Join/Leave-Management von vRv automatisch auch für unsere Lösung.
6. SharePoint als Ablage + Purview für Aufbewahrung (Retention-Labels/-Richtlinien verhindern Löschung/Änderung, Fristen 70+ Jahre konfigurierbar). In Business Premium enthalten: manuelle Labels + org-weite Richtlinien; automatische Klassifizierung/Records Management kosten extra. Prüfpunkt: Kern-Workloads (Exchange, SharePoint, Teams) liegen in Zürich/Genf, aber Planner-Daten laut Praxisberichten in der EU; als Prüfpunkt ausweisen, nicht als Fakt behaupten.
7. USD 105 pro Nutzer und Monat (Contractor USD 50, Team Member USD 8). Beweist zweierlei: Der Hauswart-Use-Case ist anspruchsvoller als To Do + Planner (sonst hätte Microsoft kein eigenes Produkt dafür), und es gibt einen Preisanker, unter dem sich beide unserer Varianten bewegen.
8. Rund USD 280-300 Listenpreis pro Monat, grössenordnungsmässig CHF 250-400 zusätzlich zur heutigen Basis. Annahmen: 6 Hauswarte × Power Apps Premium (USD 120), 3 × Power Automate Premium (USD 45), 6-8 × Planner Plan 1 (USD 60-80), 4 × Power BI Pro (USD 56). Hauswart-Zahl am 5.8. verifizieren; Preiserhöhung per 1.7.2026 vor Offerte neu ziehen.
9. SharePoint List View Threshold 5'000 Elemente pro Abfrage (fix); Flow-Run-Historie 28 Tage Standard (zu kurz für Verrechnungs-Nachvollziehbarkeit); API-Tageslimits 6'000 (M365) bzw. 40'000 (Premium) Aktionen. (Zwei reichen.)
10. pebeFINANCE hat kein öffentliches API, also existiert kein Konnektor. Weg (a): Dateiaustausch, Flow erzeugt Buchungs-/Faktura-CSV in SharePoint, Sachbearbeitung importiert in pebe (Vorschau, Übernehmen) als Kontrollpunkt. Weg (b): Desktop-RPA gegen die pebe-Oberfläche, wartungsanfällig bei jedem Update und lizenzteuer; vermeiden wir aktiv.
11. Grenze: Jeder externe Teilnehmer braucht ein Entra-B2B-Gastkonto (Einladung pro Person); bei Dutzenden bis Hunderten Mietern operativ unrealistisch, real bleibt E-Mail. Microsoft-Antwort: Power Pages als Portal, USD 200 pro Website und Monat je 100 authentifizierte Nutzer.
12. Service-Konten + geteilte Eigentümerschaft (Flows gehören sonst der erstellenden Person), gebaute Fehlerbehandlung/Alarmierung (Flows melden Fehler nicht von selbst) + verlängerte Run-Historie, DLP-Richtlinien + CoE gegen Citizen-Developer-Wildwuchs, Umgebungsstrategie Dev/Test/Prod, Lizenz-Drift-Überwachung. (Drei reichen.)

### Drill-Leitplanken (Elemente, die vorkommen müssen)

D1: Lizenzen ≠ Lösung (der Baukasten baut sich nicht selbst) → wir liefern Architektur, Bau und Betrieb auf dem vorhandenen Sockel → Ihre Microsoft-Investition wird dadurch mehr wert, nicht ersetzt.
D2: Zustimmen für Genehmigungen/Standardflows → ergänzen: für Feld-App, Leistungserfassung und pebe-Naht sieht Microsoft selbst Power Apps/Dataverse vor, plus Governance → anbieten, das gemeinsam mit dem Partner sauber zu architektieren; wir offerieren genau diese Variante seriös mit.
D3: Ehrliche Grössenordnung CHF 250-400/Monat Zusatzlizenzen im Kernszenario → die Zahl hängt an Hauswart-Anzahl, Offline-Bedarf und Reporting-Tiefe → dazu kommt in jeder Variante der Bau-/Integrationsaufwand; genauer 3-Jahres-Vergleich in der Offerte.
D4: Anerkennen der Idee → Planner ist fürs Backoffice gebaut (Limits nüchtern nennen: Checklisten, offline lesend) → für den Keller-Fall sieht Microsoft Power Apps mit Offline-Dataverse vor → genau das (oder unsere Feld-PWA) zeigen wir live.
D5: Wir verdienen in beiden Varianten am Bauen und Betreiben, nicht am Lizenzverkauf → deshalb gleicher Prozessumfang + 3-Jahres-TCO nebeneinander, Entscheid liegt bei Ihnen auf Zahlenbasis.
