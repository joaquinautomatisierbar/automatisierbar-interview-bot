# Dossier C: Variante Microsoft, seriös bewertet

> Teil der vRv-Ausschreibungsvorbereitung (Masterplan WS0, Task 0.6). Stand: 10.7.2026. Autor: Claude (Recherche via Microsoft-Preis- und Dokumentationsseiten, Microsoft Learn, Praxisberichte). Zweck: faire, belegte Einordnung der vom Kunden selbst vorgeschlagenen "Variante Microsoft" für den Termin am 5.8.2026 und für die Offerte.

**Der Originalvorschlag des Kunden (Ausschreibung, 2.7.2026):** "In Kombination von Microsoft To Do, Planner, Outlook, Teams, SharePoint und Power Automate könnten wir ein umfassendes Organisationssystem erstellen, das die Verwaltung von Aufgaben und Terminen sowie die Sicherstellung der Ausführung und Überwachung von Projekten und Aufgaben effizient unterstützt."

**Kennzeichnung:** Aussagen sind markiert als **[V]** = verifiziert (Quelle am 10.7.2026 geprüft, Nummer verweist aufs Quellenverzeichnis) oder **[A]** = abgeleitet (unsere Einschätzung bzw. Schlussfolgerung aus verifizierten Fakten). Preise sind Listenpreise, exkl. MwSt.

---

## 1. Zusammenfassung (5 Punkte)

- **Die Idee des Kunden ist gut begründet und wir sagen das auch so.** Für interne Aufgabenorganisation, Genehmigungen, Dokumentenablage, Teamkommunikation und insbesondere die BVG-konforme Langzeitaufbewahrung ist die M365-Welt stark, die Lizenzbasis existiert bei vRv bereits, und die Datenhaltung der Kern-Workloads liegt in Schweizer Rechenzentren. [V: 1, 13, 20]
- **Für drei Kernstücke des Order2Cash-Prozesses reichen die sechs genannten Tools allein nicht:** (a) mobile Hauswart-Ausführung mit Offline-Fähigkeit, Pflicht-Checklisten, Fotos und GPS, (b) strukturierte Zeit- und Materialerfassung als Basis der Verrechnung, (c) Anbindung von pebeFinance, das kein öffentliches API hat. [V: 6, 7, 8, 25; A]
- **Microsoft hat für genau diese Lücken eigene Produkte, die der Kunde nicht genannt hat:** Power Apps + Dataverse (Feld-App offline-first, GPS, Fotos, saubere Prozessdaten) und am oberen Ende Dynamics 365 Field Service. Die Variante Microsoft wird damit tragfähig, aber lizenz- und governancepflichtig. [V: 3, 8, 18]
- **Kostenbild:** Die M365-Basis ist vorhanden. Der realistische Ausbau kostet zusätzlich rund USD 10 bis 20 pro beteiligtem Nutzer und Monat je Baustein (Power Apps Premium USD 20, Power Automate Premium USD 15, Planner Plan 1 USD 10, Power BI Pro USD 14); die Field-Service-Route liegt bei USD 105 pro Techniker und Monat. Für vRv grob CHF 250 bis 400 Zusatzlizenzen pro Monat im Vollausbau ohne Field Service. [V: 2, 3, 4, 18, 23; A für die vRv-Hochrechnung]
- **Empfehlung:** Die Variante Microsoft als **Variante A** ernsthaft und mit ehrlichem Preisschild in die Offerte aufnehmen, mit uns in der ausgeschriebenen Rolle als Architekt und Projektleiter ("wir orchestrieren die Microsoft-Welt für Sie"). Daneben Variante B (massgeschneiderte Plattform) mit identischem Prozess-Scope. Entscheid über 3-Jahres-TCO, Hauswart-Akzeptanz und Governance-Kapazität, nicht über Ideologie. [A]

---

## 2. Was die Variante Microsoft gut kann (fair und konkret)

Der Kunde hat hier richtig gedacht. Konkret leistet die Kombination:

**Aufgaben- und Terminverwaltung im Backoffice.** Das neue Planner (seit 2024) vereint To Do, Planner und Project-Funktionen in einer App in Teams: persönliche Aufgaben ("Mir zugewiesen", "Mein Tag" aus To Do), Team-Boards mit Buckets, Labels, Checklisten und Anhängen, Ansichten Raster/Board/Zeitplan/Diagramme. [V: 4, 5, 27] Wiederkehrende vertragliche Aufgaben (Stiftungsverpflichtungen, Serviceintervalle) lassen sich als wiederholende Tasks mit Zuweisung und Fälligkeit abbilden. [V: 5]

**Genehmigungen und einfache Workflows.** Die Approvals-App in Teams und Power-Automate-Genehmigungsflüsse (Auftragsfreigabe, Offertfreigabe, Spesen) sind ohne Zusatzlizenz nutzbar, solange nur Standard-Konnektoren (SharePoint, Outlook, Teams, Planner, To Do) im Spiel sind: die dafür nötige Power-Automate-Nutzung ist in M365 enthalten ("seeded"). [V: 2, 10]

**Dokumente und Zusammenarbeit.** SharePoint-Dokumentbibliotheken mit Versionierung, Metadaten und Co-Authoring, Teams als Kommunikationszentrale, Outlook als Dreh- und Angelpunkt der Kundenkorrespondenz. Für ein 28-Personen-Team, das heute schon in O365 arbeitet, entfällt der Umgewöhnungsaufwand fast vollständig. [V: 1; A für die Adoption-Einschätzung]

**BVG-konforme Aufbewahrung: hier ist die Microsoft-Welt sogar besonders stark.** Die Ausschreibung verlangt Aufbewahrung nach Art. 27i bis 27k BVV 2 (10 Jahre nach Leistungsende bis zum 100. Altersjahr, jederzeit lesbar). SharePoint plus Microsoft Purview deckt das strukturell ab: Aufbewahrungsrichtlinien und -etiketten verhindern Löschung/Änderung über definierte Fristen. In Microsoft 365 Business Premium sind manuelle Aufbewahrungsetiketten und organisationsweite Aufbewahrungsrichtlinien bereits enthalten; erweiterte Funktionen (automatische Klassifizierung, Records Management mit regulatorischer Sperre) sind als Purview-Add-on zulizenzierbar. [V: 13, 14] Fristen von 70+ Jahren sind konfigurierbar; das "jederzeit lesbar" ist mit gängigen Formaten (PDF) in SharePoint gut erfüllbar. [A]

**Schweizer Datenhaltung.** Exchange, SharePoint/OneDrive und Teams speichern Daten für Schweizer Tenants in den Microsoft-Rechenzentren Zürich und Genf; inzwischen sind über 500 Services lokal verfügbar, inkl. Azure OpenAI und M365 Copilot. [V: 20] Wichtiges Detail für den Termin: einzelne Dienste fallen nicht darunter; Praxisberichte verorten insbesondere Planner-Daten in der EU statt in der Schweiz. Das ist für vRv vermutlich tragbar (Aufgabendaten, keine Vorsorgedokumente), muss aber in der Datenschutzbetrachtung sauber ausgewiesen werden. [V: 21 als Praxisbericht; A: als Prüfpunkt führen, nicht als Fakt behaupten]

**Betriebsreife.** Hyperscaler-Betrieb mit SLA, Entra ID Single Sign-on, MFA und Conditional Access (in Business Premium), zentrale Administration. Für die in der Ausschreibung geforderten Kapitel Rechenzentrum, Datensicherheit und Sicherheitsstandards liefert die Microsoft-Welt belastbare Standardantworten. [V: 1, 20; A]

**Fazit dieses Abschnitts:** Als internes Organisations- und Kollaborationssystem ist der Vorschlag des Kunden nicht nur plausibel, sondern der richtige Sockel. Wo er an Grenzen stösst, ist die Feldarbeit und die Verrechnungskette.

---

## 3. Wo die Variante für den vRv-Use-Case an Grenzen stösst (je Grenze mit Beleg)

**Grenze 1: Hauswart-Ausführung mobil (Checklisten, Fotos, Offline).**
Planner-Tasks erlauben maximal 20 Checklistenpunkte und 10 Anhänge pro Aufgabe; Checklistenpunkte kennen keine Pflichtfelder, keine Foto-Pflicht pro Punkt und keine Eingabetypen (Zahl, Auswahl, Unterschrift). [V: 6] Die Planner-Mobile-App ist offline nur eingeschränkt nutzbar; auf iOS ist der Offline-Modus lesend. [V: 6, 7] Ein Hauswart im Keller ohne Empfang kann also weder eine strukturierte Abnahme durchführen noch verlässlich dokumentieren. To Do ist als persönliche Aufgabenliste konzipiert und trägt zur Team-Ausführung nichts Strukturiertes bei. [V: 4, 5; A für die Einsatz-Schlussfolgerung]

**Grenze 2: GPS-Anbindung.**
Die Ausschreibung nennt GPS ausdrücklich als organisatorische Voraussetzung. In To Do, Planner, Outlook, Teams, SharePoint und Power Automate ist keine GPS-Erfassung für Aufgaben oder Einsätze vorgesehen (in keiner Funktionsbeschreibung enthalten). [A, gestützt auf V: 4, 5, 6] GPS gibt es in der Microsoft-Welt erst mit Power Apps (Location-Signal der Canvas-App, nur im Vordergrund aktiv) oder mit Dynamics 365 Field Service. [V: 24, 18]

**Grenze 3: Strukturierte Zeit- und Materialerfassung für die Verrechnung.**
Order2Cash heisst bei vRv: Leistung erfassen, messen, verrechnen. Planner und To Do haben keine Felder für Arbeitszeit, Material, Ansätze oder Kostenstellen; auch Planner Premium (Plan 1) ergänzt Projektsichten (Timeline, Abhängigkeiten, Sprints, benutzerdefinierte Felder), aber keine Leistungserfassung im Abrechnungssinn. [V: 4, 5] Ohne strukturierte Erfassung entsteht keine automatische Faktura-Grundlage; der Medienbruch (Zettel, Excel) bliebe bestehen. Lösung innerhalb der Microsoft-Welt: eigene Datenstruktur in Microsoft Lists oder Dataverse plus Erfassungs-App (Power Apps). [A]

**Grenze 4: Echtzeit-Kommunikation mit Mietern und Eigentümern (externe Nutzer).**
Teams-Gastzugang setzt pro Person ein Entra-B2B-Gastkonto voraus: Einladung per E-Mail, Annahme, Verwaltung im eigenen Verzeichnis. [V: 15] Shared Channels (B2B Direct Connect) funktionieren nur mit Gegenstellen, die selbst eine Entra-Organisation haben, also nicht mit Privatpersonen. [V: 16] Für Dutzende bis Hunderte Mieter ist das operativ unrealistisch; real bleibt E-Mail (Outlook) der Kanal, was "Echtzeit" relativiert. Ein echtes Mieter-/Eigentümerportal hiesse in der Microsoft-Welt Power Pages, lizenziert ab USD 200 pro Website und Monat je 100 authentifizierte Nutzer. [V: 17; A für die Praktikabilitäts-Einschätzung]

**Grenze 5: Integration pebeFinance (Buchhaltung ohne öffentliches API).**
pebeFinance bietet gemäss öffentlicher Dokumentation CSV-Buchungsimport und Scanning-/Archiv-Anbindung, aber kein öffentliches REST-API (Detail in Dossier A). [V: 25] Power Automate hat folglich keinen pebe-Konnektor; die realistischen Wege sind (a) Dateiaustausch: Flows erzeugen Buchungs-/Faktura-CSVs in SharePoint, pebe importiert sie, oder (b) Desktop-RPA gegen die pebe-Oberfläche. Beides ist machbar, aber: der HTTP-Konnektor und Custom Connectors (falls je Middleware/API ins Spiel kommt) sind Premium-Funktionen, attended RPA erfordert Power Automate Premium (USD 15/Nutzer/Monat), unattended RPA einen Process-Bot (USD 150/Bot/Monat). [V: 2, 10] RPA gegen eine Desktop-Oberfläche ist erfahrungsgemäss wartungsanfällig bei jedem pebe-Update; der CSV-Weg ist robuster, bleibt aber asynchron (kein Echtzeit-Zahlungsstatus). [A]

**Grenze 6: Reporting-Tiefe über den Gesamtprozess.**
Planner-Diagramme zeigen Task-Status je Plan, nicht "Auftrag bis Zahlungseingang". Durchgängiges Order2Cash-Reporting (inkl. Arbeitszeit, Material, offene Posten) verlangt eine saubere Datenbasis (Dataverse oder Lists) plus Power BI; Power BI Pro kostet seit dem 1.4.2025 USD 14 pro Nutzer und Monat. [V: 23; A für die Architektur-Folgerung]

**Grenze 7: Berechtigungsgranularität und Datentrennung.**
Planner-Pläne hängen an M365-Gruppen: wer Mitglied ist, sieht den ganzen Plan; Feld- oder Zeilensicherheit gibt es dort nicht. Für die Trennung nach Mandaten (Stiftung, Eigentümerschaften, Treuhand) braucht es entweder viele Gruppen (Wildwuchs) oder Dataverse mit rollenbasierter Sicherheit. [V: 5, 6 für das Gruppenmodell; A für die Konsequenz]

**Grenze 8: Plattform-Limiten bei Prozessdaten.**
SharePoint-Listen speichern zwar bis 30 Mio. Einträge, aber der List View Threshold von 5'000 Elementen pro Abfrage ist in SharePoint Online fix und erzwingt Indexierung/Filterdisziplin. [V: 12] Flow-Ausführungshistorie wird standardmässig nur 28 Tage aufbewahrt (für Nachvollziehbarkeit von Abrechnungsläufen zu kurz, verlängerbar via Dataverse-Metadaten). [V: 11] API-Tageslimits: 6'000 Aktionen pro Tag mit M365-Lizenz, 40'000 mit Power-Automate-Premium. Für ein prozesslastiges System mit vielen Flows ist das ein reales Dimensionierungsthema. [V: 10]

---

## 4. Was der Kunde nicht erwähnt hat, aber zur Variante dazugehört

Die ehrliche Botschaft am 5.8.: "Ihre Liste ist der richtige Sockel. Microsoft selbst würde für Ihren Use Case drei weitere Bausteine dazustellen." Das ist keine Schwächung der Kundenidee, sondern ihre Vervollständigung.

**Power Apps (der eigentliche Schlüssel zur Hauswart-App).** Canvas-Apps liefern genau das, was Planner mobil nicht kann: eigene Formulare mit Pflichtfeldern, Kamera-Integration für Fotos, GPS via Location-Signal, Barcode-Scan, Unterschrift. [V: 3, 24] Offline-first ist seit der General Availability der Dataverse-Offline-Funktion für Canvas-Apps ein eingebauter Schalter, setzt aber zwingend Dataverse als Datenquelle voraus (nicht SharePoint) und damit Premium-Lizenzen. [V: 8, 9] Lizenz: Power Apps Premium USD 20 pro Nutzer und Monat (USD 12 ab 2'000 Nutzern). Wichtig: der frühere Per-App-Plan (USD 5) wurde Anfang 2026 aus dem Microsoft-Licensing-Guide entfernt und wird auf der offiziellen Preisseite nicht mehr geführt; als nutzungsbasierte Alternative existiert Pay-as-you-go über Azure. [V: 3 für die Preisseite; V: 26 als Drittquellen für die Streichung; am Termin nicht als Deal-Detail verkaufen, in der Offerte mit aktueller Preisliste belegen]

**Dataverse (die Datenbank hinter dem Prozess).** Strukturierte Tabellen für Aufträge, Leistungen, Material, Objekte; rollenbasierte Sicherheit bis auf Zeilen-/Feldebene; Grundlage für Offline-Profile und sauberes Reporting. Kapazität: Tenant-Basis 10 GB Datenbank + 20 GB File + 2 GB Log, seit Dezember 2025 je nach Lizenz erhöht; pro Premium-Lizenz akkruieren 250 MB DB + 2 GB File; Zusatzkapazität USD 40 pro GB und Monat. [V: 22, 2, 3]

**Microsoft Lists.** Die lizenzkostenfreie Zwischenstufe für strukturierte Daten (Auftragslisten, Objektstammdaten) mit Formularen und Regeln, aber mit den SharePoint-Limiten (5'000er-Threshold) und ohne Offline-Feld-App. Gut für den Einstieg, nicht das Endausbau-Ziel für die Verrechnungsdaten. [V: 12; A]

**Planner Plan 1 (Premium).** Für die Einsatzplanung der Hauswartung und Projektsichten: Timeline/Gantt, Abhängigkeiten, Sprints, benutzerdefinierte Felder, USD 10 pro Nutzer und Monat. Sinnvoll für Disponenten, nicht für jeden Mitarbeiter. [V: 4, 5]

**Dynamics 365 Field Service (der Referenzpunkt am oberen Ende).** Microsofts eigenes Produkt für exakt diesen Anwendungsfall: Work Orders, Disposition, offline-fähige Mobile App, Inspections (Checklisten mit Fragetypen, Pflichtfeldern, Fotos, offline ausfüllbar), Zeit- und Materialbuchung, Standort/Navigation. USD 105 pro Nutzer und Monat, Contractor-Lizenz USD 50, Team Member USD 8. [V: 18, 19] Für 28 Mitarbeitende mit eigener Hauswartung ist das funktional ein Volltreffer und preislich ein Statement. Als Argument am Termin wertvoll: dass Microsoft für Hauswart-Szenarien ein eigenes 105-Dollar-Produkt führt, zeigt, dass der Use Case grösser ist als To Do + Planner. [A]

**Power Pages und Power BI** als optionale Ergänzungen für Mieterportal (USD 200/Monat je 100 authentifizierte Nutzer/Site) und Reporting (USD 14/Nutzer/Monat). [V: 17, 23]

---

## 5. Lizenz- und Kostenbild (Listenpreise, Stand 10.7.2026)

M365-Preise: Microsoft-Preisliste Schweiz in CHF. Power-Platform-/Dynamics-Preise: offizielle US-Preisseiten in USD; die CHF-Listenpreise liegen erfahrungsgemäss in ähnlicher Höhe und werden in der Offerte tagesaktuell aus der Microsoft-Preisliste Schweiz ausgewiesen. [V: 1, 2, 3, 4, 17, 18, 23; A für die CHF-Näherung]

| Baustein | Listenpreis pro Monat | Wofür | Quelle |
| --- | --- | --- | --- |
| Microsoft 365 Business Basic | CHF 5.67 /User (Jahresabo) | Web-Apps, Teams, SharePoint | [1] |
| Microsoft 365 Business Standard | CHF 19.03 /User (Jahresabo) | heutige Basis (vermutlich) | [1] |
| Microsoft 365 Business Premium | CHF 25.92 /User (Jahresabo) | + Security, Intune, Purview-Basis (manuelle Retention-Labels, org-weite Richtlinien) | [1, 13] |
| Planner Plan 1 (Premium) | USD 10 /User | Timeline, Abhängigkeiten, Sprints, Custom Fields | [4, 5] |
| Power Automate Premium | USD 15 /User | Premium-/Custom-Konnektoren, HTTP, attended RPA, 40'000 API-Calls/Tag | [2, 10] |
| Power Automate Process | USD 150 /Bot | unattended RPA (z.B. gegen pebe-Oberfläche) | [2] |
| Power Apps Premium | USD 20 /User (USD 12 ab 2'000 User) | unbegrenzte Apps, Dataverse-Zugriff, Offline-Feld-App | [3] |
| Dataverse DB-Zusatzkapazität | USD 40 /GB | über Basis + Akkruals hinaus | [3, 22] |
| Power BI Pro | USD 14 /User | Prozess-Reporting (Preis seit 1.4.2025) | [23] |
| Power Pages | USD 200 /Site je 100 auth. Nutzer | Mieter-/Eigentümerportal (optional) | [17] |
| Dynamics 365 Field Service | USD 105 /User (Contractor USD 50, Team Member USD 8) | vollwertige FSM-Alternative | [18] |

**Grobe Hochrechnung vRv (Annahmen, [A]):** bestehende M365-Basis bleibt wie sie ist (kein Zusatz). Ausbau Variante Microsoft im Kernszenario: 6 Hauswarte × Power Apps Premium (USD 120) + 3 Flow-Verantwortliche/Servicekonto × Power Automate Premium (USD 45) + 6 bis 8 Disponenten/Backoffice × Planner Plan 1 (USD 60 bis 80) + 4 × Power BI Pro (USD 56). **Ergibt rund USD 280 bis 300 Listenpreis pro Monat, grössenordnungsmässig CHF 250 bis 400 pro Monat** zusätzlich zur heutigen Basis, zuzüglich einmaligem Bau-/Integrationsaufwand (unser Honorar, in beiden Varianten anfallend). Die Field-Service-Route ersetzt den Power-Apps-Teil und läge allein für 6 Hauswarte bei USD 630 pro Monat. Kein Anspruch auf Rappengenauigkeit; Zweck ist die ehrliche Grössenordnung fürs Gespräch. Zahl der Hauswarte am 5.8. verifizieren.

**Wichtig für die Ehrlichkeit des Vergleichs:** Diese Lizenzkosten sind der laufende Sockel der Variante Microsoft. Bei der massgeschneiderten Variante fallen stattdessen Hosting-/Betriebskosten und unser Wartungsvertrag an. Der faire Vergleich ist der 3-Jahres-TCO beider Varianten inkl. Bau, Lizenzen, Betrieb und Änderungskosten. [A]

---

## 6. Betriebs- und Governance-Aufwand (was oft unterschätzt wird)

Die Variante Microsoft ist kein Produkt, sondern ein Baukasten. Jemand muss ihn zusammensetzen und betreiben:

- **Eigentümerschaft der Flows und Apps.** Flows gehören standardmässig dem Konto der erstellenden Person; verlässt sie die Firma oder ist im Urlaub, stehen Prozesse still. Professionell heisst: Service-Konten, geteilte Eigentümerschaft, Umgebungsstrategie (Dev/Test/Prod) und Solutions für Versionierung/Transport, was wiederum Dataverse voraussetzt. [V: 10 für das Lizenz-/Plattformmodell; A für die Betriebspraxis]
- **Fehlerbehandlung und Monitoring müssen gebaut werden.** Flows haben keine automatische Alarmierung im Fehlerfall; Try/Catch-Scopes, Retry-Logik und Benachrichtigungen sind Handarbeit. Die Run-Historie von 28 Tagen reicht für Verrechnungs-Nachvollziehbarkeit nicht und muss via Dataverse-Metadaten verlängert werden. [V: 11]
- **Citizen-Developer-Wildwuchs ist das dokumentierte Hauptrisiko.** Microsoft adressiert es selbst mit Data-Loss-Prevention-Richtlinien (welche Konnektoren dürfen kombiniert werden) und dem CoE Starter Kit für Inventarisierung und Governance. Ohne diese Leitplanken entstehen in 1 bis 2 Jahren Dutzende undokumentierte Flows, die niemand mehr anfassen will. [V: 28; A für die Prognose]
- **Lizenz-Drift.** Ein einziger Premium-Konnektor (z.B. HTTP für eine künftige Schnittstelle) macht den ganzen Flow premium-pflichtig; das Kostenbild muss deshalb pro Prozess gepflegt werden. [V: 2, 10]
- **Was "wir orchestrieren die Microsoft-Welt für Sie" als Dienstleistung konkret heisst:** (1) Architektur: Umgebungen, DLP-Richtlinien, Namenskonventionen, Berechtigungsmodell, Datenmodell in Dataverse/Lists. (2) Bau: Hauswart-App (Power Apps), Auftrags- und Leistungsdatenmodell, Genehmigungs- und Faktura-Flows, pebe-CSV-Brücke, Power-BI-Berichte, Purview-Aufbewahrung. (3) Betrieb: Monitoring/Alerting, monatliche Reviews, Änderungswesen, Dokumentation, Schulung; SLA-Struktur gemäss Anforderungskatalog der Ausschreibung. Genau die in der Ausschreibung gewünschte Rolle (Architektur und Projektleitung, Mitarbeit vRv). [A, Rollendefinition aus der Ausschreibung; V: 25 intern]

---

## 7. Fazit: als Variante A in unsere Offerte

**Ehrliche Einordnung:** Die Variante Microsoft ist tragfähig, wenn man sie zu Ende denkt. Zu Ende gedacht heisst: nicht sechs Tools, sondern sechs Tools plus Power Apps, Dataverse und Power BI, mit sauberer Governance. Ihre Stärken liegen im Backoffice (Aufgaben, Genehmigungen, Dokumente, Kommunikation intern), in der BVG-Archivierung (SharePoint + Purview, Schweizer Datenhaltung der Kern-Workloads) und im Kosteneinstieg auf vorhandenen Lizenzen. Ihre strukturellen Schwächen liegen im Feld (Hauswart-UX, Offline, GPS, Foto-Pflichten), in der Verrechnungskette (strukturierte Leistungserfassung) und an der Naht zu pebeFinance (kein API, nur CSV oder RPA).

**Wie wir sie liefern würden:** als Architekt und Integrator in genau der ausgeschriebenen Rolle. Wir entwerfen das Datenmodell, bauen Feld-App, Flows und Berichte, richten Purview-Aufbewahrung und Governance ein, betreiben und schulen. Wir können das glaubwürdig anbieten, weil wir beide Welten beherrschen (Power Automate/n8n und Custom-Plattformen) und keinen Anreiz haben, dem Kunden die eine oder andere Welt zu verkaufen.

**Positionierung in der Offerte:** Variante A = Microsoft-Ausbau (Lizenzmodell, tiefere Baukosten, Baukasten-Grenzen transparent). Variante B = massgeschneiderte Plattform (unsere bestehenden Bausteine: Feld-PWA mit Offline und Foto, Auftrags-Hub, pebe-CSV-Brücke; höhere Bauleistung, dafür exakte Passform, volle Kontrolle über UX, Berechtigungen und Archivierung, keine Lizenz-Drift). Beide mit identischem Prozess-Scope und 3-Jahres-TCO nebeneinander. Denkbar und offen ansprechen: ein Hybrid (M365 als Kollaborations- und Archiv-Ebene, custom nur dort, wo der Baukasten teuer oder schwach ist). [A]

---

## 8. Gesprächsleitfaden für den 5.8. (wertschätzend und kompetent)

**Grundhaltung:** Der Kunde hat die Variante selbst vorgeschlagen. Wir behandeln sie als ernsthafte Option und uns als den Partner, der sie am besten beurteilen und umsetzen kann. Nie "geht nicht" sagen, immer "dafür sieht Microsoft X vor, das gehört zur Variante dazu und kostet Y".

1. **Anerkennen (wörtlich so beginnen):** "Ihre Variante Microsoft ist gut gedacht. Für Aufgaben, Genehmigungen, Dokumente und gerade für die BVG-Aufbewahrung ist die M365-Welt stark, und Sie haben die Lizenzen schon. Wir würden denselben Sockel wählen."
2. **Discovery-Fragen stellen (Antworten bestimmen das Kostenbild):**
   - Welche M365-Pläne sind heute im Einsatz (Business Standard oder Premium)? Wie viele Nutzer?
   - Wie viele Hauswarte, welche Geräte (iOS/Android), wie ist der Empfang in den Liegenschaften?
   - Wer soll Flows und Apps intern pflegen können (die Governance-Frage)?
   - Wo läuft pebeFinance (lokal, gehostet), welche Module (Leistungserfassung, Fakturierung) sind aktiv in Gebrauch?
   - Wie läuft Mieter-/Eigentümerkommunikation heute, und ist ein Portal gewünscht oder genügt strukturierte E-Mail?
3. **Die drei Bruchstellen zeigen, ohne abzuwerten:** Hauswart-Mobile (Planner offline lesend, 20 Checklistenpunkte, kein GPS), Leistungserfassung (keine Zeit-/Materialfelder), pebe-Naht (kein API). Je Bruchstelle sofort die Microsoft-eigene Antwort danebenstellen: Power Apps + Dataverse, bzw. CSV-Brücke/RPA. Das demonstriert Kompetenz in ihrer Welt.
4. **Der Field-Service-Moment:** "Microsoft selbst positioniert für Hauswart-Einsätze Dynamics 365 Field Service für 105 Dollar pro Nutzer und Monat. Das zeigt zweierlei: Ihr Use Case ist anspruchsvoller als Planner, und es gibt einen Preisanker, unter dem sich beide unserer Varianten bewegen."
5. **Live zeigen statt behaupten:** kurze Demo unserer Feld-PWA (Checkliste, Foto, offline) neben einem Planner-Task auf dem Handy. Der Unterschied erklärt sich selbst; kein abwertender Kommentar nötig.
6. **Abschluss:** "Wir offerieren Ihnen beide Varianten mit gleichem Prozessumfang und einem ehrlichen 3-Jahres-Kostenvergleich. Wir verdienen in beiden Fällen am Bauen und Betreiben, nicht am Lizenzverkauf. Sie entscheiden auf Basis von Zahlen und einer Live-Erfahrung, nicht auf Basis unserer Präferenz."

**Sprachregelungen:** "Vervollständigen statt ersetzen" (ihre 6 Tools + 2 Bausteine), "Baukasten mit Bauleitung" (Governance als Dienstleistung), "Preisschild statt Bauchgefühl" (Lizenzliste offenlegen). Nicht verwenden: "Spielzeug", "reicht nicht", "das kann Planner nicht" ohne die Microsoft-eigene Lösung im selben Satz.

---

## 9. Quellenverzeichnis (alle geprüft am 10.7.2026)

1. Microsoft 365 Business Pläne und Preise Schweiz (CHF, Jahresabo, exkl. MwSt.): https://www.microsoft.com/de-ch/microsoft-365/business/microsoft-365-plans-and-pricing
2. Power Automate Preise (Premium USD 15, Process USD 150, Hosted Process USD 215; Konnektor-Umfang): https://www.microsoft.com/en-us/power-platform/products/power-automate/pricing
3. Power Apps Preise (Premium USD 20 bzw. 12, Dataverse-Add-on USD 40/GB; kein Per-App-Plan mehr gelistet): https://www.microsoft.com/en-us/power-platform/products/power-apps/pricing
4. Microsoft Planner Pläne und Preise (Plan 1 USD 10, Plan 3 USD 30): https://www.microsoft.com/en-us/microsoft-365/planner/microsoft-planner-business-plans-and-pricing
5. Planner Basic vs. Premium Vergleich (Ansichten, Abhängigkeiten, Custom Fields): https://support.microsoft.com/en-us/planner/compare-microsoft-planner-basic-vs-premium-plans
6. Microsoft Planner Limits (20 Checklistenpunkte, 10 Anhänge u.a.): https://learn.microsoft.com/en-us/planner/planner-limits
7. Planner Offline-Verhalten (Praxisbericht Office 365 for IT Pros): https://office365itpros.com/2020/09/04/planner-secret-offline-mode/
8. Mobile Offline für Canvas Apps, Übersicht und Voraussetzungen (Dataverse, Offline-Profil): https://learn.microsoft.com/en-us/power-apps/mobile/canvas-mobile-offline-overview und https://learn.microsoft.com/en-us/power-apps/mobile/limitations-canvas-apps
9. GA-Ankündigung Dataverse Offline für Canvas Apps (Microsoft Power Platform Blog): https://www.microsoft.com/en-us/power-platform/blog/power-apps/announcing-general-availability-of-built-in-dataverse-offline-for-canvas-apps/
10. Power-Platform-Request-Limits (6'000/Tag M365-Lizenz, 40'000/Tag Premium) und Lizenz-FAQ (Premium-Konnektoren inkl. HTTP): https://learn.microsoft.com/en-us/power-platform/admin/api-request-limits-allocations und https://learn.microsoft.com/en-us/power-platform/admin/power-automate-licensing/faqs
11. Flow-Limits und Run-Historie (28 Tage Standard, Verlängerung via Dataverse): https://learn.microsoft.com/en-us/power-automate/limits-and-config und https://learn.microsoft.com/en-us/power-automate/dataverse/cloud-flow-run-metadata
12. SharePoint List View Threshold 5'000 (fix in SPO, 30 Mio. Elemente Speicher): https://support.microsoft.com/en-us/sharepoint/lists/data-and-lists/list-view-threshold-for-large-lists-and-libraries und https://learn.microsoft.com/en-us/troubleshoot/sharepoint/lists-and-libraries/items-exceeds-list-view-threshold
13. Purview Data Lifecycle/Records Management Lizenzierung (Business Premium: manuelle Labels, org-weite Richtlinien): https://learn.microsoft.com/en-us/office365/servicedescriptions/microsoft-365-service-descriptions/microsoft-purview-data-lifecycle-records-management
14. Microsoft Purview Service Description (Add-on-Pfad für Business Premium): https://learn.microsoft.com/en-us/office365/servicedescriptions/microsoft-365-service-descriptions/microsoft-365-tenantlevel-services-licensing-guidance/microsoft-purview-service-description
15. Teams-Gastzugang (Entra-B2B-Gastkonto, Einladung pro Person): https://learn.microsoft.com/en-us/microsoftteams/guest-access
16. Gastzugang vs. External Access / Shared Channels (B2B Direct Connect nur mit Entra-Organisation): https://learn.microsoft.com/en-us/microsoftteams/communicate-with-users-from-other-organizations
17. Power Pages Preise (USD 200/Site/Monat je 100 authentifizierte Nutzer): https://www.microsoft.com/en-us/power-platform/products/power-pages/pricing
18. Dynamics 365 Field Service Preise (USD 105, Contractor USD 50, Team Member USD 8): https://www.microsoft.com/en-us/dynamics-365/products/field-service/pricing und https://www.randgroup.com/insights/microsoft/dynamics-365/customer-engagement/field-service/understanding-dynamics-365-field-service-pricing/
19. Field Service Inspections (Fragetypen, Pflichtfelder, Fotos, offline): https://learn.microsoft.com/en-us/dynamics365/field-service/inspections-customer-assets
20. Microsoft Rechenzentren Schweiz, 5-Jahres-Bilanz (Zürich/Genf, 500+ lokale Services): https://news.microsoft.com/de-ch/2024/08/29/5-jahre-microsoft-rechenzentren-in-der-schweiz-500-lokale-services-50000-kunden/
21. Datenstandort-Übersicht Microsoft Trust Center; Praxisberichte zur Planner-Datenhaltung in der EU: https://www.microsoft.com/de-ch/trust-center/privacy/data-location und https://www.procloud.ch/office-365-aus-schweizer-rechenzentren-seien-sie-einer-der-ersten/ (Sekundärquelle, am Termin als Prüfpunkt führen)
22. Dataverse-Kapazität (Basis 10 GB DB + 20 GB File + 2 GB Log; Akkruals; Erhöhungen Dez. 2025): https://learn.microsoft.com/en-us/power-platform/admin/capacity-storage und https://licensing.guide/december-2025-dataverse-default-capacity-changes-illustrated/
23. Power BI Preiserhöhung per 1.4.2025 (Pro USD 14, PPU USD 24): https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/Important-update-to-Microsoft-Power-BI-pricing/ba-p/5174341 und https://www.microsoft.com/en-us/power-platform/products/power-bi/pricing
24. Power Apps Location-Signal / GPS in Canvas Apps (Praxisreferenz + API-Referenz): https://powerappsguide.com/blog/post/gps-3-common-questions-about-location-services und https://learn.microsoft.com/en-us/power-apps/developer/component-framework/reference/device/getcurrentposition
25. Intern: tender-vrv/MASTERPLAN.md, Abschnitt "Fakten aus Recon" (pebeFinance: CSV-Buchungsimport, Scanning/Archiv, kein öffentliches REST-API; Basis pebe.ch, Detail in Dossier A)
26. Streichung des Power-Apps-Per-App-Plans Anfang 2026 (Drittquellen, in Offerte gegen aktuelle Microsoft-Preisliste prüfen): https://citizendevelopmentacademy.com/power-automate-pricing/ und https://www.synapx.com/blogs/understanding-power-automate-licensing-options/
27. Neues Planner (Vereinigung To Do, Planner, Project in Teams, GA 2024): https://adoption.microsoft.com/en-us/microsoft-planner/
28. Governance-Werkzeuge: CoE Starter Kit und DLP-Richtlinien: https://learn.microsoft.com/en-us/power-platform/guidance/coe/starter-kit und https://learn.microsoft.com/en-us/power-platform/admin/wp-data-loss-prevention
