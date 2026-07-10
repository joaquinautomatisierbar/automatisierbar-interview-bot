# Architektur-Varianten-Papier: A / B / C

> Task WS5.2 (C entwirft, Joaquin reviewt). Entwurf 10.7.2026. Wird nach dem Scope-Entscheid (21.7.) und dem Termin (5.8.) finalisiert und speist die Offerten-Kapitel 5 bis 7 plus Anhang E.
> Quellen: Dossier A (pebe-Flächen), B (Marktlücke), C (Microsoft-Fakten inkl. Preise, Stand 10.7.), D (Security-Bausteine), E (Scope-Empfehlungen). Jede Zahl hier ist dort belegt; vor Offertabgabe Microsoft-Preise tagesaktuell neu ziehen (Preiserhöhung per 1.7.2026 angekündigt).
> **[Entscheid offen]**-Marker zeigen, was der 21.7. bzw. der 5.8. klären muss.

## 0. Grundsätze, die für ALLE Varianten gelten

1. **pebeFinance bleibt System of Record** für Fibu, Debitoren-OP und Zahlungseingang. Keine Variante baut eine parallele Debitorenbuchhaltung (teuerster möglicher Fehler).
2. **Kopplung an pebe ist datei- und bankbasiert, nie Fernsteuerung:** CSV/Excel-Buchungsimport (braucht optionale pebe-Lizenz "Schnittstellen"), evtl. Fakturapositions-Import (Umfang klärt pebe, Fragen P1-P8), QR-Rechnung raus, camt.053/054 zurück. Der Import-Klick in pebe bleibt anfangs bewusst ein menschlicher Kontrollpunkt.
3. **Identität immer Entra ID:** Login mit bestehenden vRv-Microsoft-Konten, MFA und Conditional Access von vRv gelten automatisch. Keine zweite Passwort-Welt, in keiner Variante.
4. **Produktivdaten in der Schweiz.** Bei A liegt die Datenhaltung im Schweizer M365-Tenant (Kern-Workloads Zürich/Genf; Planner-Datenstandort als Prüfpunkt ausweisen). Bei B/C zertifiziertes CH-Hosting. **[Entscheid offen: 6.3 Exoscale vs. Infomaniak, bis 27.7.]**
5. **BVG-Archivierung ist eine Übergabe, kein Nebenprodukt:** Die operative Plattform übergibt Dokumente mit Vorsorge-Charakter an ein dediziertes revisionssicheres Archiv (SharePoint+Purview ODER WORM-Objektspeicher; Ablageort nach Kundenpräferenz, Tool-Frage g7).
6. **Der Order2Cash-Fluss ist in allen Varianten derselbe** (nur die ausführenden Bausteine wechseln):

```text
Auftrag entsteht (Vertrag/Meldung/Mail) → Disposition → mobile Ausführung
(Checkliste, Foto, Zeit, Material) → Freigabe → Fakturadaten → pebeFINANCE
(Rechnung/QR ODER Buchungsimport) → Bank (camt) → Status zurück → Reporting
```

---

## 1. Variante A: Microsoft-Ausbau (Power-Platform-first)

**Idee:** Die vom Kunden vorgeschlagene M365-Welt, zu Ende gedacht. Wir liefern Architektur, Bau, Governance und Betrieb ("Baukasten mit Bauleitung").

**Bausteine:**

| Prozessschritt | Baustein | Anmerkung |
|---|---|---|
| Datenmodell (Aufträge, Objekte, Leistungen, Material) | **Dataverse** | rollenbasierte Sicherheit bis Zeile/Feld; Voraussetzung für Offline |
| Hauswart-App | **Power Apps** (Canvas) | Pflichtfelder, Kamera, GPS, Unterschrift, offline mit Dataverse |
| Disposition + Backoffice-Aufgaben | **Planner** (+ Plan 1 für Disponenten) | wiederkehrende Aufgaben für Vertragspflichten |
| Workflows/Genehmigungen | **Power Automate** | Standard-Konnektoren im M365-Abo enthalten; HTTP/RPA = Premium |
| pebe-Naht | Flow erzeugt Import-Datei nach SharePoint | Import-Klick durch Buchhaltung; RPA bewusst vermieden |
| Dokumente + Archiv | **SharePoint + Purview** | Retention-Labels, 70+ Jahre konfigurierbar |
| Reporting | **Power BI Pro** | über Dataverse, nicht über Planner-Diagramme |
| Kommunikation intern | Teams/Outlook | Mieter/Eigentümer: strukturiert per Mail; Portal wäre Power Pages (USD 200/Mt.) |

**Stärken:** baut auf vorhandenen Lizenzen und Gewohnheiten; Adoption fast ohne Umgewöhnung; Archiv-Story stark; Sicherheits-Pflichtkapitel weitgehend durch Microsoft-Standardantworten gedeckt.

**Grenzen (transparent in die Offerte):** Feld-Offline/GPS nur über die Premium-Schiene (Power Apps + Dataverse); Leistungserfassung braucht eigenes Datenmodell; Lizenz-Drift-Risiko (ein Premium-Konnektor macht den Flow lizenzpflichtig); Governance ist Daueraufgabe (Flow-Eigentümerschaft, DLP, 28-Tage-Run-Historie verlängern); Berechtigungen jenseits Dataverse grob (M365-Gruppen).

**Kostenbild (Listenpreise 10.7., Offerte zieht tagesaktuell):** Zusatzlizenzen Kernszenario rund **USD 280-300/Monat ≈ CHF 250-400/Monat** (6 Hauswarte Power Apps à USD 20, 3 × Power Automate Premium à USD 15, 6-8 × Planner Plan 1 à USD 10, 4 × Power BI Pro à USD 14). Referenzpunkt nach oben: Dynamics 365 Field Service USD 105/Nutzer/Monat. Dazu unser Bau- und Betriebshonorar (in jeder Variante).

**Betrieb:** Umgebungsstrategie (Dev/Test/Prod), Service-Konten, DLP-Richtlinien, Monitoring/Alerting der Flows, monatliche Reviews, Schulung. Ohne diese Bauleitung degeneriert die Variante in 1-2 Jahren zu undokumentiertem Flow-Wildwuchs (dokumentiertes Hauptrisiko, Microsoft adressiert es selbst mit CoE/DLP).

**Risiken:** pebe-Formatspezifikation kommt spät (blockiert die Naht in JEDER Variante); Planner-Datenstandort EU (Prüfpunkt); Premium-Lizenzkosten steigen mit jedem weiteren Prozess.

---

## 2. Variante B: Massgeschneiderte Plattform

**Idee:** Ein Auftrags- und Verrechnungs-System, exakt auf die drei Geschäftsfelder-Realität von vRv gebaut (Bewirtschaftung beauftragt, Hauswartung leistet, Verwaltung verrechnet). Dossier B belegt: genau diese Kombination bildet keine Standard-Suite ab.

**Bausteine:**

| Prozessschritt | Baustein | Anmerkung |
|---|---|---|
| Auftrags-Hub (Web) | eigene Plattform | Boards, Disposition, Status, Freigaben, Audit-Log |
| Hauswart-App | **Feld-PWA, offline-first** | Checklisten mit Pflichtfeldern/Foto, Zeit/Material, GPS-Einsatznachweis (Zweck nach Tool-Frage e4, nDSG-verhältnismässig); Muster mehrfach gebaut (Walk-in-PWA, Beleg-PWA) |
| M365-Naht | **Graph API** | Mail-Eingang als Auftragsquelle, Kalender, Ablage nach SharePoint; vRv arbeitet weiter in Outlook/Teams |
| pebe-Naht | **eigener Integrationsdienst** | erzeugt Importdateien, validiert vorab gegen Kontenplan/MWST-Regeln (spiegelt die belegten pebe-Prüfungen), erzeugt bei Bedarf QR-Rechnung selbst (offener Standard), liest camt für Zahlungsstatus |
| Datenhaltung | Postgres + Objektspeicher, CH | Managed DB mit Point-in-Time-Recovery, Backups 3-2-1 |
| Archiv | Übergabe an SharePoint+Purview ODER eigener WORM-Speicher | PDF/A, Hash/Zeitstempel, protokollierte Migration (GeBüV-Massstab) |
| Reporting | eingebaut + Export | Auswertungen auf dem eigenen Datenmodell; Excel-Export für Gewohnheiten |

**Stärken:** exakte Prozess-Passform und Hauswart-UX (Handschuh, Keller, grosse Touchflächen); feine Berechtigungen und Prüfpfad auf Revisionsniveau; keine Lizenz pro Nutzer/Baustein; Änderungen in Tagen statt Release-Zyklen; volle Kontrolle über die pebe-Naht (Vorvalidierung = Import läuft beim ersten Versuch durch).

**Grenzen (transparent):** höhere initiale Bauleistung; wir werden Betreiber (SLA-Pflicht, Dossier E: E1/E8 = Kernkompetenz, ehrlich ohne 24/7-Pikett als Standard); Dokumenten-Kollaboration bleibt sinnvollerweise in M365 (nicht nachbauen).

**Kostenbild:** Investition nach Phasen (Detailkonzept → Pilot → Rollout) + laufend Hosting/Wartung/SLA statt Lizenzen. 3-Jahres-TCO in der Offerte neben Variante A. Preisanker aus dem Markt: Suiten CHF 149-699/Monat plus Einführung; Field Service USD 105/Nutzer.

**Risiken:** Schlüsselpersonen-Risiko (Antwort: Doku-Disziplin, Code-/Betriebsübergabe vertraglich, offene Formate); pebe-Format wie bei A; Offline-Tiefe kostet, falls e6 "zwingend" ergibt (20-40h Zusatz laut Dossier E).

---

## 3. Variante C: Hybrid (Empfehlungskandidat)

**Idee:** Jede Welt macht, was sie am besten kann. Nicht "halb A, halb B", sondern eine klare Schnittregel.

**Schnittregel:**

- **In M365 lebt, was Dokument, Kommunikation oder Langzeit-Archiv ist:** Outlook als Kundenkanal, Teams intern, SharePoint als Ablage, Purview für BVG-Retention, Approvals für einfache Genehmigungen.
- **Custom ist, was Prozess, Feld oder pebe-Naht ist:** Auftrags-Hub, Feld-PWA, Leistungsdatenmodell, Integrationsdienst (Dateierzeugung, Vorvalidierung, Übergabeprotokoll, camt-Lesen), Prozess-Reporting.
- **Verbindung über Graph API:** Plattform legt Rapporte/Rechnungskopien automatisch in SharePoint ab (damit greift die Purview-Retention), liest Auftrags-Mails, schreibt Kalendereinträge.

**Warum das der Favorit zur Prüfung ist:**

1. Erfüllt die Primär-Anforderung wörtlich (pebe integriert, O365-Welt genutzt statt ersetzt).
2. Vermeidet die teuersten Grenzen beider Reinformen: keine Power-Apps-Premium-Schiene fürs Feld, kein Nachbau von Dokumenten-Kollaboration/Archiv.
3. Minimiert das grösste Projektrisiko (pebe-Naht) in einem kleinen, isolierten Dienst mit menschlichem Kontrollpunkt, automatisierbar erst wenn pebe einen unbeaufsichtigten Weg bestätigt (Frage P2).
4. Governance-Last der Power Platform entfällt weitgehend (wenige bis keine Premium-Flows).

**Grenzen:** zwei Welten heisst zwei Betriebsflächen (unsere Plattform + M365-Konfiguration); Verantwortungsschnitt muss im Vertrag glasklar sein (RACI, Offerten-Kapitel 11.4).

**Kostenbild:** Bauleistung nahe B (Feld + Kern), aber ohne Premium-Lizenzsockel von A; M365-Zusatzkosten nur punktuell (evtl. Planner Plan 1 für Disponenten, Purview-Add-on je nach Archiv-Tiefe). **[Entscheid offen: Archiv-Weg g7 bestimmt, ob Purview-Add-on oder WORM-Speicher budgetiert wird.]**

---

## 4. Entscheidungsraster (für Offerte Kapitel 7.5)

Qualitativ; die Zahlen liefert das Kostenkapitel nach dem 5.8.:

| Kriterium | A Microsoft | B Custom | C Hybrid |
|---|---|---|---|
| Hauswart-UX (offline, Foto-Pflicht, GPS) | gut, nur mit Power Apps + Dataverse (Premium) | am stärksten, exakt gebaut | am stärksten (Feld = custom) |
| Leistungserfassung → Verrechnung | eigenes Datenmodell nötig (Dataverse) | nativ im Kern | nativ im Kern |
| pebe-Naht | Datei via Flow, Validierungstiefe begrenzt | eigener Dienst mit Vorvalidierung | eigener Dienst mit Vorvalidierung |
| Dokumente + BVG-Archiv | am stärksten (SharePoint+Purview) | Übergabe nötig | am stärksten (M365-Seite) |
| Laufende Lizenzkosten | wachsen pro Nutzer/Baustein | keine (Hosting statt Lizenz) | punktuell |
| Governance-/Betriebslast | Flow-Governance dauerhaft | bei uns als Betreiber | geteilt, klein je Seite |
| Änderungsgeschwindigkeit | Baukasten-Takt | Tage | Tage (Prozesskern) |
| Exit/Datenhoheit | Tenant gehört vRv; Flows/Apps migrierbar mit Aufwand | Export offen, Code-Übergabe vertraglich | beides |
| 3-Jahres-TCO | **[nach 5.8. beziffern]** | **[nach 5.8. beziffern]** | **[nach 5.8. beziffern]** |

## 5. Was der 5.8. für dieses Papier klären muss (Tool-Fragen)

- Mengengerüst: Hauswarte, Disponenten, Aufträge/Monat, Rechnungen/Monat (a-Kapitel; skaliert Lizenz- UND Baukosten)
- M365-Stand: Pläne (Standard/Premium?), wer administriert den Tenant (d-Kapitel)
- pebe: Module, Lizenz "Schnittstellen", Betriebsmodell lokal vs. pebeONLINE, wer fakturiert heute womit (c-Kapitel; entscheidet Fakturaposition vs. Buchungsimport vs. QR-Eigenerzeugung)
- Feld: Geräte, Empfang, Offline-Pflicht (e6), GPS-Zweck (e4)
- Kommunikation: genügt strukturierte Mail oder ist ein Portal gewünscht (Power Pages / custom Portal = eigene Kostenposition)
- Archiv: bestehendes DMS? Präferenz SharePoint vs. dedizierter Speicher (g7)
- IT-Betrieb: wer ist der heutige IT-Partner, was soll konsolidiert werden (g1; bestimmt die Teillos-Struktur aus Dossier E)

## 6. Scope-Anschluss (Dossier E)

Dieses Papier beschreibt die LÖSUNGS-Architektur. Die Betriebs-/Infrastruktur-Lose (Netzwerk, Hardware, Endpoints, SLA-Stufen) kommen aus dem Scope-Entscheid vom 21.7. und werden im Offerten-Kapitel 10 als Teillose ausgewiesen (Empfehlung Dossier E: "wir orchestrieren, Partner betreibt die Vor-Ort-Schicht"; einzige echte Debatte E4 Endpoints). **[Entscheid offen: 21.7.]**
