# Modul 1 · O365 + Power Platform (inkl. Variante Microsoft)

> Session 2, Owner: **Tej** (unterrichtet die anderen drei, Feynman-Prinzip). Lesezeit ~45 min, Unterrichtszeit 60 min + Quiz + Drill.
> Grundlage: [research/dossier-c-variante-microsoft.md](../research/dossier-c-variante-microsoft.md). Jede Zahl dort quellenbelegt (Quellenverzeichnis mit 28 geprüften Quellen, Stand 10.7.2026). Verweise hier als [C §n].
> Warum dieses Modul: vRv arbeitet heute in O365 und hat die "Variante Microsoft" **selbst vorgeschlagen**. Wer die Microsoft-Welt nicht kennt, kann sie weder wertschätzend einordnen noch glaubwürdig integrieren. Am 5.8. müssen alle vier die M365-Landkarte zeichnen können.

## Lernziele

Nach der Session kann jeder von uns:

1. Die M365-Landkarte aus dem Kopf skizzieren (welches Tool macht was, was kostet es).
2. Die Variante Microsoft in 2 Sätzen anerkennen UND in 3 Punkten vervollständigen, ohne abzuwerten.
3. Die drei Bruchstellen für den vRv-Use-Case nennen, je mit der Microsoft-eigenen Antwort daneben.
4. Das Kostenbild sprechfähig wiedergeben (Grössenordnungen, nicht Rappen).
5. Erklären, warum "Baukasten mit Bauleitung" unsere Rolle in dieser Variante ist.

---

## 1. Die M365-Landkarte in 16 Begriffen

Reihenfolge: erst die Welt, die vRv kennt, dann die Bausteine, die sie nicht genannt haben.

**Microsoft 365 (die Lizenzwelt).** Abo-Pakete pro Nutzer und Monat. Business Basic CHF 5.67 (nur Web-Apps), Business Standard CHF 19.03 (Desktop-Office, vermutlich vRvs heutige Basis), Business Premium CHF 25.92 (zusätzlich Security: Intune, Defender, Entra ID P1, Purview-Basis). Alles Jahresabo, exkl. MwSt. [C §5] Achtung: Microsoft hat eine Preiserhöhung per 1.7.2026 angekündigt, CHF-Preise vor Offertabgabe zwingend neu ziehen (Dossier E, E4).

**Entra ID (früher Azure AD).** Das zentrale Identitätssystem: jedes Login, jede Berechtigung. Für uns dreifach wichtig: **SSO** (unsere Lösung nutzt die bestehenden Microsoft-Konten), **MFA** (zweiter Faktor zentral erzwungen) und **Conditional Access** (Regeln wie "Zugriff nur von verwalteten Geräten"). Unsere Plattform baut keine eigene Passwort-Welt daneben. [C §2, §3]

**Outlook / Exchange.** Dreh- und Angelpunkt der Kundenkorrespondenz bei vRv. Bleibt in jeder Variante der Kanal zu Mietern und Eigentümern. Bonus-Wissen: pebe Leistungserfassung hat eine dokumentierte Standardschnittstelle zu Outlook (Dossier A), die einzige belegte pebe-Microsoft-Integration.

**Teams.** Interne Kommunikationszentrale, stark. Grenze nach aussen: Externe brauchen pro Person ein Entra-B2B-Gastkonto (Einladung, Annahme, Verwaltung). Für Dutzende bis Hunderte Mieter operativ unrealistisch; "Echtzeit-Kommunikation mit Mietern" via Teams ist ein Papierversprechen. Shared Channels gehen nur mit Firmen, die selbst Entra haben. [C §3 Grenze 4]

**SharePoint / OneDrive.** Dokumentablage mit Versionierung, Metadaten, Co-Authoring. Der Ort für Dokumente in jeder Variante. Technische Grenze für Prozessdaten: List View Threshold von 5'000 Elementen pro Abfrage (fix in SharePoint Online), erzwingt Indexierung und Filterdisziplin. [C §2, §3 Grenze 8]

**Microsoft Lists.** Strukturierte Tabellen auf SharePoint-Basis, ohne Zusatzlizenz. Gut für den Einstieg (Auftragslisten, Objektstammdaten), aber mit den SharePoint-Limiten und ohne Offline-Feld-App. Nicht das Endausbau-Ziel für Verrechnungsdaten. [C §4]

**To Do.** Persönliche Aufgabenliste. Trägt zur strukturierten Team-Ausführung nichts bei, füttert aber "Mein Tag" im neuen Planner. [C §2, §3 Grenze 1]

**Planner (neu seit 2024).** Vereint To Do, Planner und Project-Funktionen in einer App in Teams: Boards mit Buckets, Labels, Checklisten, wiederkehrende Aufgaben (wichtig für Stiftungs-/Serviceintervalle). Premium-Stufe "Plan 1" (USD 10/User/Monat) ergänzt Timeline/Gantt, Abhängigkeiten, Custom Fields. Harte Limits: **max. 20 Checklistenpunkte und 10 Anhänge pro Task, keine Pflichtfelder, keine Eingabetypen, Mobile-App offline nur eingeschränkt (iOS: lesend), kein GPS, keine Zeit-/Materialfelder.** [C §2, §3 Grenzen 1-3]

**Power Automate.** Workflow-Engine ("Flows"). Entscheidend ist die Lizenzgrenze: Mit Standard-Konnektoren (SharePoint, Outlook, Teams, Planner, To Do) ist die Nutzung in M365 **enthalten** ("seeded"). Sobald ein Flow einen Premium-Konnektor braucht (HTTP!, Custom Connector) oder RPA, kostet es **USD 15/User/Monat** (Premium), unattended RPA-Bot **USD 150/Monat**. Weitere Betriebsfakten: Run-Historie standardmässig nur 28 Tage, API-Tageslimits 6'000 (M365-Lizenz) bzw. 40'000 (Premium). [C §2, §3 Grenzen 5+8]

**Power Apps.** Der eigentliche Schlüssel zur Hauswart-App in der Microsoft-Welt: eigene Formulare mit Pflichtfeldern, Kamera, GPS (Location-Signal), Barcode, Unterschrift. **Offline-first geht nur mit Dataverse als Datenquelle** (nicht SharePoint) und damit Premium-Lizenz: USD 20/User/Monat. Der frühere 5-Dollar-Per-App-Plan wurde Anfang 2026 gestrichen. [C §4]

**Dataverse.** Die Datenbank hinter der Power Platform: strukturierte Tabellen, rollenbasierte Sicherheit bis auf Zeilen-/Feldebene (die Antwort auf Mandantentrennung Stiftung/Eigentümer/Treuhand), Grundlage für Offline-Profile und sauberes Reporting. Kapazität: Tenant-Basis 10 GB DB + 20 GB File, Zusatz USD 40/GB/Monat. [C §4, §3 Grenze 7]

**Power BI.** Reporting über den Gesamtprozess (Auftrag bis Zahlungseingang), braucht saubere Datenbasis (Dataverse/Lists). Pro-Lizenz USD 14/User/Monat (seit 1.4.2025). Planner-Diagramme allein zeigen nur Task-Status. [C §3 Grenze 6, §4]

**Power Pages.** Externe Portale (Mieter/Eigentümer) mit Login: USD 200 pro Website und Monat je 100 authentifizierte Nutzer. Der Preis macht "Portal" zur bewussten Entscheidung, nicht zur Beilage. [C §3 Grenze 4]

**Dynamics 365 Field Service.** Microsofts eigenes Produkt für exakt den Hauswart-Use-Case: Work Orders, Disposition, offline-fähige Mobile App, Inspections (Checklisten mit Fragetypen, Pflichtfeldern, Fotos), Zeit- und Materialbuchung. **USD 105 pro Nutzer und Monat.** Für uns der wichtigste Preisanker im Gespräch. [C §4]

**Purview.** Compliance-Schicht: Aufbewahrungsrichtlinien und -etiketten verhindern Löschung/Änderung über definierte Fristen (BVG-Archivierung!). In Business Premium enthalten: manuelle Labels + org-weite Richtlinien. Automatische Klassifizierung und Records Management kosten extra. [C §2]

**Intune + Defender for Business.** Gerätemanagement + EDR, beides in Business Premium. Relevant für die E4-Entscheidung (Endpoints selbst betreiben oder nicht, Dossier E); im Kundengespräch gehört es zur Antwort "Sicherheitsstandards".

**Graph API.** Die eine API über fast alles (Mail, Kalender, Teams, SharePoint, Planner, Nutzer). Unsere Integrationsfläche, egal welche Variante: Custom-Plattform spricht über Graph mit der M365-Welt. Merken: Graph ist der Grund, warum "Custom" und "Microsoft-Welt" kein Widerspruch ist.

**Schweizer Datenhaltung.** Exchange, SharePoint/OneDrive und Teams speichern für Schweizer Tenants in Zürich/Genf (500+ Services lokal). Aber nicht alles: Praxisberichte verorten Planner-Daten in der EU. Als Prüfpunkt führen, nicht als Fakt behaupten. [C §2]

---

## 2. Was die Variante Microsoft gut kann (zuerst! immer zuerst!)

Der Kunde hat richtig gedacht. Vier Stärken, die wir aktiv aussprechen [C §2]:

1. **Backoffice-Aufgaben und Termine:** neues Planner mit wiederkehrenden Tasks deckt die vertraglichen Pflichten (Stiftung, Serviceintervalle) strukturell ab.
2. **Genehmigungen ohne Zusatzkosten:** Approvals + Power-Automate-Standardflows sind in M365 enthalten, solange nur Standard-Konnektoren im Spiel sind.
3. **BVG-Aufbewahrung ist eine echte Microsoft-Stärke:** SharePoint + Purview mit Retention-Labels, Fristen von 70+ Jahren konfigurierbar, Kern-Workloads in Schweizer Rechenzentren. Das sagen wir laut, denn es macht uns glaubwürdig.
4. **Betriebsreife + Adoption:** 28 Leute arbeiten schon in O365, Umgewöhnung fast null; Entra SSO/MFA/Conditional Access liefern Standardantworten auf halbe Sicherheitskapitel der Ausschreibung.

Merksatz: **"Ihre Liste ist der richtige Sockel."** Erst danach kommt das Aber.

## 3. Die drei Bruchstellen, je mit Microsofts eigener Antwort

Nie "geht nicht" sagen. Immer "dafür sieht Microsoft X vor, das gehört zur Variante dazu und kostet Y". [C §3, §8]

| Bruchstelle | Beleg | Microsofts eigene Antwort |
|---|---|---|
| **1. Hauswart mobil** (Checklisten mit Pflicht-Foto, offline im Keller, GPS) | Planner: 20 Checklistenpunkte, keine Pflichtfelder, iOS offline lesend, kein GPS | Power Apps + Dataverse (offline-first, Kamera, GPS, Unterschrift), USD 20/User; am oberen Ende Field Service USD 105/User |
| **2. Leistungserfassung für die Verrechnung** (Zeit, Material, Ansätze) | Planner/To Do haben keine Zeit-/Material-/Kostenstellen-Felder, auch Plan 1 nicht | Eigenes Datenmodell in Dataverse (oder Lists) + Erfassung via Power Apps + Reporting via Power BI |
| **3. pebe-Naht** (kein öffentliches API, Dossier A) | Kein pebe-Konnektor; HTTP/Custom Connector = Premium-Lizenz; RPA gegen Desktop wartungsanfällig | CSV-Brücke: Flows erzeugen Buchungs-/Faktura-Dateien in SharePoint, Import-Klick in pebe bleibt als Kontrollpunkt |

Dazu vier leisere Grenzen, die wir kennen, aber nicht ungefragt ausbreiten: Mieter-Kommunikation (Gastkonten-Problem, Portal = Power Pages USD 200), Reporting-Tiefe (braucht Dataverse + Power BI), Berechtigungsgranularität (Planner-Pläne hängen an M365-Gruppen: wer drin ist, sieht alles), Plattform-Limiten (5'000er-Threshold, 28-Tage-Historie, API-Tageslimits). [C §3]

## 4. Das Kostenbild sprechfähig

Grössenordnungen für das Gespräch, Details stehen in [C §5]:

- **Basis:** vorhandene M365-Lizenzen bleiben, kein Zusatz.
- **Ausbau Kernszenario** (Annahmen: 6 Hauswarte Power Apps, 3 Flow-Verantwortliche Power Automate Premium, 6-8 Disponenten Planner Plan 1, 4 Power BI): rund **USD 280-300 Listenpreis/Monat, grössenordnungsmässig CHF 250-400/Monat** zusätzlich. Zahl der Hauswarte am 5.8. verifizieren!
- **Field-Service-Route:** allein für 6 Hauswarte USD 630/Monat. Der Anker: "Microsoft selbst positioniert für Hauswart-Einsätze ein 105-Dollar-Produkt. Das zeigt, Ihr Use Case ist grösser als To Do + Planner."
- **Der faire Vergleich ist der 3-Jahres-TCO:** Variante Microsoft = tiefere Baukosten + laufende Lizenzen + Governance-Aufwand. Variante Custom = höhere Bauleistung + Hosting/Wartung statt Lizenzen. Wir verdienen in beiden am Bauen und Betreiben, nicht am Lizenzverkauf. Das ist unser Neutralitäts-Argument.

## 5. Governance: der Teil, den alle unterschätzen

Die Variante Microsoft ist kein Produkt, sondern ein Baukasten. Was "wir orchestrieren die Microsoft-Welt für Sie" konkret heisst [C §6]:

1. **Eigentümerschaft:** Flows gehören standardmässig der erstellenden Person. Person weg = Prozess steht. Professionell: Service-Konten, geteilte Eigentümerschaft, Dev/Test/Prod-Umgebungen, Solutions für Versionierung.
2. **Fehlerbehandlung ist Handarbeit:** Flows alarmieren im Fehlerfall nicht von selbst; Try/Catch, Retry, Benachrichtigung muss man bauen. Run-Historie 28 Tage reicht für Verrechnungs-Nachvollziehbarkeit nicht.
3. **Citizen-Developer-Wildwuchs** ist das dokumentierte Hauptrisiko; Microsoft adressiert es selbst mit DLP-Richtlinien + CoE Starter Kit. Ohne Leitplanken: in 1-2 Jahren Dutzende undokumentierte Flows.
4. **Lizenz-Drift:** ein einziger Premium-Konnektor macht den ganzen Flow premium-pflichtig. Kostenbild pro Prozess pflegen.

Sprachregelung dafür: **"Baukasten mit Bauleitung."** Genau die ausgeschriebene Rolle (Architektur + Projektleitung).

## 6. Wie wir sie am 5.8. einordnen (Kurzleitfaden)

Vollversion in [C §8]. Die Choreografie:

1. **Anerkennen, wörtlich:** "Ihre Variante Microsoft ist gut gedacht. Für Aufgaben, Genehmigungen, Dokumente und gerade für die BVG-Aufbewahrung ist die M365-Welt stark, und Sie haben die Lizenzen schon. Wir würden denselben Sockel wählen."
2. **Discovery-Fragen** (bestimmen das Kostenbild): Welche Pläne (Standard/Premium)? Wie viele Hauswarte, welche Geräte, Empfang in den Liegenschaften? Wer pflegt Flows intern? Wo läuft pebe? Mieter-Kommunikation heute, Portal gewünscht?
3. **Bruchstellen zeigen, MS-Antwort daneben** (Tabelle oben).
4. **Field-Service-Moment** (Preisanker).
5. **Live zeigen statt behaupten:** unsere Feld-PWA neben einem Planner-Task auf dem Handy. Der Unterschied erklärt sich selbst.
6. **Abschluss:** "Wir offerieren beide Varianten mit gleichem Prozessumfang und ehrlichem 3-Jahres-Kostenvergleich. Sie entscheiden auf Basis von Zahlen und einer Live-Erfahrung, nicht auf Basis unserer Präferenz."

**Verbotene Wörter:** "Spielzeug", "reicht nicht", "das kann Planner nicht" (ohne die Microsoft-Lösung im selben Satz). **Pflicht-Vokabeln:** "vervollständigen statt ersetzen", "Baukasten mit Bauleitung", "Preisschild statt Bauchgefühl".

---

## 7. Zehn sprechfähige Sätze (auswendig können)

1. "Ihre Variante Microsoft ist gut gedacht, und wir würden denselben Sockel wählen: Aufgaben, Genehmigungen, Dokumente, Archivierung."
2. "Zu Ende gedacht heisst die Variante: Ihre sechs Tools plus Power Apps und Dataverse. Das sagt Microsoft selbst, nicht wir."
3. "Planner erlaubt 20 Checklistenpunkte ohne Pflichtfelder und ist auf dem iPhone offline nur lesend. Für den Hauswart im Keller sieht Microsoft dafür Power Apps mit Dataverse vor."
4. "GPS gibt es in der Microsoft-Welt erst mit Power Apps oder Field Service, in Planner und To Do ist es schlicht nicht vorgesehen."
5. "Für Zeit und Material gibt es in Planner kein Feld. Ohne strukturierte Erfassung bleibt der Zettel, und der Zettel ist heute Ihr teuerstes Formular."
6. "Microsoft positioniert für genau Ihren Hauswart-Fall Dynamics Field Service für 105 Dollar pro Nutzer und Monat. Beide unserer Varianten liegen darunter."
7. "Der Ausbau der Microsoft-Variante kostet grob 250 bis 400 Franken Lizenzen pro Monat zusätzlich; der faire Vergleich beider Varianten ist der 3-Jahres-TCO."
8. "Power Automate ist gratis, bis der erste Premium-Konnektor kommt; ein HTTP-Aufruf macht den ganzen Flow lizenzpflichtig. Solche Kostenfallen managen wir für Sie."
9. "Flows gehören dem Konto, das sie erstellt hat. Verlässt die Person die Firma, steht der Prozess. Darum gehören Service-Konten und Governance von Anfang an dazu."
10. "Wir verdienen in beiden Varianten am Bauen und Betreiben, nicht am Lizenzverkauf. Deshalb können wir Ihnen beide ehrlich nebeneinanderlegen."

---

## 8. Verbindung zu den anderen Modulen

- **Modul 4 (gehalten):** Order2Cash-Stationen = die Prozessbrille, durch die jede M365-Funktion bewertet wird.
- **Modul 2 (S3):** Entra/Conditional Access/Intune/Defender vertieft; dort fällt auch der Scope-Entscheid E4 (Endpoints selbst betreiben?).
- **Modul 6 (S5):** Graph API, CSV-Brücke zu pebe, Integrationsmuster im Detail.
- **Offerte:** Dieses Modul liefert Variante A des Architektur-Papiers (WS5.2) und die Lizenz-Tabelle des Kostenkapitels.
