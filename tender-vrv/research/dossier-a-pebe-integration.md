# Dossier A: pebeFinance Integrationsflächen

**Zweck:** Grundlagenrecherche für die Ausschreibung der vR verwaltungen ag (Order2Cash-Prozess, Integration pebeFinance in die Microsoft-365-Welt). Vorbereitung Team-Meeting Kundenseite am 5. August 2026.
**Stand:** 10. Juli 2026, Recherche ausschliesslich über öffentliche Quellen (pebe.ch, pebelive.ch, topsoft.ch, Drittquellen). Quellen je Aussage als [Q-Nummer], Verzeichnis am Ende.
**Lesehilfe:** Aussagen sind als VERIFIZIERT (öffentlich belegt) oder ABGELEITET (branchentypische Einschätzung, nicht pebe-spezifisch belegt) markiert. Wo etwas unbekannt ist, steht das explizit.

---

## 1. Zusammenfassung

- **pebeFINANCE hat keine öffentlich dokumentierte API.** Die belegten Integrationsflächen der Treuhand-Suite sind dateibasiert (CSV/Excel-Buchungsimport mit optionaler Lizenz «Schnittstellen» [Q13], Excel/CSV-Import in der Fakturierung [Q7], ASCII-Schnittstelle [Q12]) plus die Schweizer Bankstandards (EBICS, camt.053/054, QR-Rechnung, pain.001) [Q4, Q10, Q12, Q23]. Eine REST-API existiert nur beim separaten Cloud-Produkt pebe Live [Q14, Q15], das für vRv als Ersatz nicht in Frage kommt (KMU-Produkt, andere Datenbasis).
- **Der realistische Integrationspfad für Order2Cash ist damit: unsere Plattform führt Auftrag, Planung, mobile Ausführung und Leistungsdaten, pebeFinance bleibt führendes System für Debitoren, Fibu und Zahlungseingang.** Die Übergabe läuft über generierte Import-Dateien (Fakturapositionen oder Buchungen) und über den Zahlungsverkehr (QR-Referenz plus camt-Abgleich in pebe) [Q4, Q7, Q13].
- **Der letzte Meter ist heute ein manueller Import-Klick in pebe** (Einlesen, Vorschau, Übernehmen) [Q13]. Ob dieser Schritt automatisierbar ist (Batch, überwachter Ordner, Kommandozeile), ist öffentlich nicht belegt und muss mit pebe AG geklärt werden. Bis dahin planen wir bewusst mit einem menschlichen Freigabeschritt (passt zu einem kontrollierten Rollout).
- **Für die mobile Leistungserfassung existiert mit «pebe mobile» eine eigene Offline-App der pebe AG** (iOS/Android, Leistungen, Spesen, Foto-Anhänge, CHF 5 pro Monat und Nutzer, setzt lizenzierte pebe Leistungserfassung voraus) [Q19, Q20]. Sie deckt aber nur Zeit/Spesen ab, nicht Auftragsdisposition, Checklisten oder Statusführung, also nicht den Kern der Ausschreibung. Sie ist als Vergleichsmassstab und als Minimal-Fallback im Meeting zu erwähnen.
- **Die grössten Unbekannten liegen beim Kunden, nicht bei pebe:** Welche Module und ob die Lizenz «Schnittstellen» vorhanden ist, Betriebsmodell (lokaler Server vs. gehostetes pebeONLINE via RDP/Citrix beim Provider VoiceLan [Q8, Q9]), wer heute fakturiert und wie Debitoren-Stammdaten gepflegt werden. Diese Fragen entscheiden zwischen den Architektur-Varianten und gehören an den 5. August.

---

## 2. pebe AG und Produktfamilie

**Firma (VERIFIZIERT):** pebe AG, Messenriet 16, 8500 Frauenfeld TG, reines Software-Haus, gegründet 1977, seit über 40 Jahren am Markt, 11 bis 20 Mitarbeitende in der Schweiz, davon 6 bis 10 in der Entwicklung [Q2, Q12]. Zielgruppen: Treuhänder, KMU, Family Offices, Finanzdienstleister, branchenneutral [Q2, Q12]. Auf der Startseite werden Logos «Swiss Made Software» und «Microsoft Partner» geführt [Q2]; das Microsoft-Partner-Logo belegt aber keine technische M365-Integration über Outlook/Excel-Funktionen hinaus.

**Produktgruppen (VERIFIZIERT) [Q1, Q3]:**

| Produkt | Inhalt | Zielgruppe |
|---|---|---|
| **pebeFINANCE** | Finanzbuchhaltung, Debitoren & Kreditoren, Anlagebuchhaltung, Lohnbuchhaltung (swissdec-zertifiziert [Q11, Q12]), Leistungserfassung, Fakturierung; mandantenfähig | Treuhänder, KMU, Family Offices |
| **pebeINVEST** | Wertschriftenbuchhaltung inkl. Portfoliobewertung, Renditeberechnung, Reporting | Finanzdienstleister |
| **pebe Live** | «Rechnungsprogramm, Lohn- & Finanzbuchhaltung für KMU. Die Cloudlösung ohne Schnickschnack» | Kleinfirmen, Startups, Klienten von Treuhändern |

**BMD-Partnerschaft (VERIFIZIERT):** «Neben der Buchhaltungslösung pebeFINANCE für den Treuhänder und pebeINVEST für den Finanzdienstleister sind wir durch unsere Partnerschaft mit BMD auch in der Lage, modular aufgebaute, komplette ERP- und CRM-Lösungen anzubieten.» [Q3] Konkret werden BMD Commerce (ERP) und BMD CRM gelistet [Q3], zudem BMD DMS und BMD Scan für Belegmanagement (siehe 3.8) [Q21].

**Deployment (VERIFIZIERT):** pebeFINANCE läuft «Lokal oder Cloud» [Q5]. On-Premise ist bei topsoft explizit gelistet [Q12]. Die Cloud-Variante («pebeFINANCE Online» / pebeONLINE) ist kein SaaS, sondern ein gehosteter Server: Zugriff via «RDP oder CITRIX» mit 128-bit-SSL, Treuhänder und Klient arbeiten auf derselben Serverumgebung [Q8]; Server-Provider-Partner ist VoiceLan [Q9]. Die FAQ bestätigt: «Der Zugriff via Remotedesktop oder CITRIX ermöglicht es dem Kunden, direkt auf Ihrer Datenbank zu buchen.» [Q10]

**Dienstleistungen (VERIFIZIERT):** Fachberatung, Projektmanagement, Hotline/Support, pebe academy [Q29]. Relevant: pebe kennt Integrationsprojekte aus der Treuhand-Zusammenarbeit und dürfte für Formatfragen ansprechbar sein.

---

## 3. Belegte Integrationsflächen

### 3.1 Buchungsimport CSV/Excel (die zentrale Fläche)

- VERIFIZIERT: «Übernahme von Buchungen aus Fremdsystemen (CSV-Schnittstelle)» als Produktmerkmal [Q4]; «Flexibler Import & Export von Buchungen (z.B. CSV)» und «Import von EXCEL und CSV Daten» [Q5].
- VERIFIZIERT (Drittquelle contofox, detaillierter Ablauf): Menüpfad «Import/Export» → «Import Allgemeine Buchungen» → Register «Import Buchungen CSV/Excel». Datei per Auswahl oder Drag & Drop, bei CSV Trennzeichen wählbar (Standard Semikolon), Button «Einlesen» lädt in eine Importvorschau mit Fehlerspalte, erst nach Fehlerbereinigung ist «Übernehmen» möglich. Importierte Zeilen erscheinen als «Schnittstellenbuchungen» [Q13].
- VERIFIZIERT: Der Import setzt die **optionale Lizenz «Schnittstellen»** voraus: «Sie für den Import von Buchungen die optionale Lizenz «Schnittstellen» benötigen» [Q13]. Fehlende Menüpunkte deuten auf fehlende Lizenz.
- VERIFIZIERT (Validierungsregeln): «Buchungen einer Importdatei dürfen nur ein Geschäftsjahr umfassen»; typische Fehlerklassen: inaktive/fehlende Konten, fehlende oder falsche MWST-Codes, steuerpflichtige Konten ohne Steuercode, Steuercode auf nicht steuerbarem Konto [Q13].
- Einordnung: contofox ist ein Drittanbieter, der genau dieses Muster produktiv nutzt (Fremddaten → pebe-kompatible Datei → Import). Das belegt, dass die Dateischnittstelle der etablierte Integrationsweg im pebe-Ökosystem ist.

### 3.2 Bankschnittstellen: ISO 20022, EBICS, QR-Rechnung

- VERIFIZIERT: «Automatisiertes Verbuchen von Kontoauszügen» (camt.053) und «Direktes Abholen von Bankauszügen via EBICS» [Q4, Q5]; FAQ: «Via EBICS lassen sich Kontoauszüge automatisch ohne Zwischenschritte einlesen und weiterverarbeiten.» [Q10]
- VERIFIZIERT: camt.054 (ISO-20022), Electronic Banking / integriertes Online-Banking, ESR/ESR+/BESR-Verarbeitung [Q12].
- VERIFIZIERT: QR-Rechnung: «Der ab Sommer 2020 neue Schweizer Zahlungsstandard ist in pebeFINANCE bereits umgesetzt.» [Q10]; QR-Rechnungen in der Fakturierung [Q7]; Verarbeitung eingehender QR-Rechnungen inkl. Erkennung [Q24].
- VERIFIZIERT (ältere Versions-Doku, Alter beachten): Zahlungsaufträge im pain.001-Format (ISO 20022), Mischung pain.001/DTA möglich, je Auftraggeber-Bankkonto wird eine eigene Datei erstellt und ans Finanzinstitut übermittelt; für pain.001 ist die IBAN Pflicht [Q23]. Hinweis: Das Dokument stammt aus der Umstellungszeit (DTA wurde 2018 abgelöst); dass pain.001 heute Standard ist, ist plausibel und durch das aktive EBICS/camt-Featureset gestützt, die aktuell unterstützten Versionen (z.B. pain.001.001.09, camt.053.001.08 nach Swiss Payment Standards) sind aber öffentlich nicht belegt.

### 3.3 Kreditoren: Scanning und Belegverarbeitung

- VERIFIZIERT: Kreditorenbuchhaltung mit Scannen, Archivieren und automatisierter Zahlungsverarbeitung; integriert in Finanz-, Anlagenbuchhaltung und Kostenrechnung [Q4].
- VERIFIZIERT: Verarbeitung von QR-, PDF- und ZUGFeRD/FacturX-Rechnungen [Q12].
- Für Order2Cash sekundär (unsere Strecke ist debitorenseitig), aber relevant als Belegweg: pebe kann strukturierte Rechnungs-PDFs lesen. ABGELEITET: Ein «Belegweg» (unsere Plattform erzeugt PDF/QR-Beleg, pebe liest ihn ein) wäre als Notlösung denkbar, ist aber kreditorenseitig gedacht und für Debitorenfakturen nicht belegt.

### 3.4 Leistungserfassung (pebeLEISTUNG) und pebe mobile

- VERIFIZIERT: Zeiterfassung mit «Stoppuhr- und Rechenfunktionen», «Automatische Übernahme von Stammdaten», «Integration von Termin- und Aufgabenverwaltung» [Q5]; Barauslagen und Spesen, verschiedene Verrechnungsarten mit auftragsbezogenen Verrechnungssätzen, komplett integrierte Offen-Posten-Buchhaltung, «Fakturavorschlag für Honorarrechnung», Einzel- und Sammelrechnung [Q6].
- VERIFIZIERT: «Standardschnittstelle zu MS Outlook» (Termin-/Aufgabenverwaltung) [Q6]. Das ist die einzige belegte, produktseitige Microsoft-Integration jenseits von Excel-Import/-Export.
- VERIFIZIERT: **pebe mobile**: «Offline-App für die gängigen Smartphone Betriebssysteme» [Q6]; erfasst unterwegs Leistungen und Spesen, Foto-Funktion für Belege, Übermittlung per WLAN mit einem Klick, danach sofort zur Fakturierung verfügbar; CHF 5 pro Monat und Nutzer; setzt installierte, lizenzierte pebe Leistungserfassung voraus [Q19]. In Apple App Store und Google Play verfügbar [Q20].
- Einordnung für die Ausschreibung: pebe mobile ist reine Zeit-/Spesenerfassung. Auftragsannahme, Disposition, Checklisten, Materiallisten, Auftragsstatus oder Unterschriften sind nicht dokumentiert. Der geforderte mobile Hauswart-Prozess geht deutlich darüber hinaus.

### 3.5 Fakturierung (pebeFAKTURA)

- VERIFIZIERT: Sammel- und Monatsrechnungen, Kopiermöglichkeit für «Massenfakturen», QR-Rechnungen, Report Designer für eigene Druckvorlagen, Lieferscheine und Offerten, mandantenfähig [Q5, Q7].
- VERIFIZIERT: «Import von EXCEL und CSV Daten» im Fakturierungs-Kontext [Q7]. **Unklar ist der genaue Umfang** (Stammdaten? Fakturapositionen? Leistungen?), siehe Abschnitt 4. Genau diese Frage entscheidet, ob unsere Plattform Fakturapositionen anliefern kann und pebe die Rechnung erzeugt.

### 3.6 Weitere belegte Flächen

- VERIFIZIERT: «Import- und Exportfunktion für Mandantenadressen im Excelformat», integrierte Handelsregisterabfrage über ZEFIX [Q1].
- VERIFIZIERT: ASCII-Schnittstelle, Excel-Import/-Export, PDF-Verarbeitung, «via Cloud Daten austauschen» [Q12].
- VERIFIZIERT: swissdec-zertifizierte Lohnbuchhaltung [Q11, Q12]. ABGELEITET: swissdec-Zertifizierung impliziert üblicherweise ELM-Lohnmeldungen; ELM ist auf den gesichteten Seiten nicht namentlich belegt.
- VERIFIZIERT: **Automatic PDF Processor** (Drittprodukt von M. & R. Gillmeister, pebe ist Vertriebspartner): versendet Dokumente aus pebeFINANCE, etwa Lohnabrechnungen oder Debitorenrechnungen, direkt per E-Mail an Empfänger; pebe-Kunden erhalten 20% Rabatt (Code PEBE20) [Q22]. Relevanz: belegt, dass pebe-Output (Rechnungen) dateiseitig abgreifbar und automatisiert versendbar ist.

### 3.7 pebe Live REST API (wichtige Abgrenzung)

- VERIFIZIERT: pebe Live (Cloud-Produkt) «bietet eine moderne REST API, mit der sich externe Systeme einfach und flexibel anbinden lassen» [Q14]. Eingeführt mit Release 8.0 (November 2023): «Sie betreiben einen Webshop und möchten Rechnungen, Kundenstamm oder Buchungen an pebe Live übergeben?»; API-Key «jederzeit über das Konto / Einstellungen» generierbar; Swagger-Dokumentation unter app.pebelive.ch/swagger/index.html [Q15, Q16].
- VERIFIZIERT: pebe Live exportiert Buchungen als Excel-Datei an die pebeFINANCE des Treuhänders; exportierte Buchungen werden gesperrt und sind nur noch stornierbar [Q17, Q18].
- **Abgrenzung:** Die REST API gehört zu pebe Live, nicht zu pebeFINANCE. pebe Live ist ein eigenständiges KMU-Cloud-Produkt mit eigener Datenhaltung. Für vRv (Treuhand-/Verwaltungsbetrieb mit pebeFinance) ist sie kein direkter Integrationspunkt. Sie zeigt aber, dass pebe AG API-Technologie beherrscht; die Roadmap-Frage «API für pebeFINANCE?» gehört an pebe.
- Randnotiz: Ein früheres Cloud-Produkt «pebe smart» hatte laut Support-Artikel ebenfalls eine «Offene Schnittstelle» (API) [Q25]; Capterra führt pebe Live unter dem Slug «pebe-smart» [Q26]. Details nicht mehr abrufbar (403), rein historisch.

### 3.8 DMS und Archivierung via BMD

- VERIFIZIERT (Blogpost 26.06.2018): pebeFINANCE-Dokumente lassen sich mit BMD DMS elektronisch archivieren: «Gleich ob es sich um Dokumente handelt, die in BMD, pebeFINANCE oder Office erstellt wurden, das Archivieren ist unkompliziert.» BMD Scan als integrierter Scan-Arbeitsplatz (OCR- und QR-Code-Erkennung, Belegtrennung), eigene Abläufe im BMD Workflow-Studio, optionales Vier-Augen-Prinzip [Q21].
- Einordnung: Es existiert also ein pebe-naher DMS-Pfad (BMD). Für die M365-Integration der Ausschreibung ist SharePoint als Ablage wahrscheinlich der bessere Fit; ob vRv bereits BMD DMS einsetzt, ist zu erfragen.

---

## 4. Was NICHT belegt oder unklar ist

1. **Keine API für pebeFINANCE dokumentiert.** Weder REST/SOAP noch COM/DB-Zugriff sind öffentlich beschrieben. Ob ein unterstützter Direktzugriff auf die Datenbank (z.B. lesende Views/ODBC) möglich und vom Hersteller toleriert ist: unbekannt, muss mit pebe geklärt werden.
2. **Automatisierbarkeit des Imports unklar.** Der belegte Buchungsimport ist ein UI-Ablauf (Einlesen, Vorschau, Übernehmen) [Q13]. Ob es einen unbeaufsichtigten Modus gibt (überwachter Ordner, CLI, Job): unbekannt.
3. **Spezifikation der Importformate nicht öffentlich.** Spaltenlayout des CSV/Excel-Buchungsimports (Konten, MWST-Codes, Kostenstellen, Belegnummern, Sammelbuchungen) ist nirgends publiziert; contofox beschreibt nur den Ablauf. Formatspezifikation muss pebe liefern.
4. **Umfang des Excel/CSV-Imports in der Fakturierung unklar** [Q7]: Können Fakturapositionen oder erfasste Leistungen aus Fremdsystemen angeliefert werden, so dass pebe die QR-Rechnung erzeugt? Nicht belegt. Ebenso unklar: Import von Debitoren-Stammdaten (belegt ist nur der Mandantenadressen-Import [Q1]).
5. **Kein Export-/Statusrückkanal dokumentiert.** Wie Zahlungseingänge oder OP-Status strukturiert aus pebe heraus exportiert werden können (Report, CSV, automatisiert): unbekannt. «Flexibler Import & Export von Buchungen» [Q5] deutet auf Export hin, Details fehlen.
6. **pebe Live API-Umfang nicht öffentlich einsehbar.** Die Swagger-Seite rendert nur mit Login/JavaScript [Q16]; Endpunkte, Objekte und Lese-/Schreibrichtungen sind ungeprüft. Für vRv nachrangig (siehe 3.7).
7. **Aktuelle ISO-20022-Versionsstände** (pain.001.001.09, camt.053.001.08 usw.): nicht belegt, nur ältere Doku [Q23].
8. **Kein Auftrags-/Werkauftragsmodul belegt.** pebeFINANCE kennt Offerten und Lieferscheine in der Fakturierung [Q7], aber keine dokumentierte Auftragsdisposition, Einsatzplanung oder mobile Auftragsabwicklung. Der Order2Cash-Vorbau muss ausserhalb von pebe entstehen; das stützt die Grundannahme der Ausschreibung.
9. **Kundenseitige Unbekannte (vRv):** lizenzierte Module, Lizenz «Schnittstellen» ja/nein, Version/Wartungsstand, Betriebsmodell (lokal vs. pebeONLINE/VoiceLan [Q8, Q9]), Betreiber/IT-Partner, heutige Fakturierungs- und Mahnprozesse, Debitoren-Stammdatenführung, Einsatz von pebe Leistungserfassung oder pebe mobile, evtl. vorhandene Immobilien-Fachsoftware neben pebe. Alles unbekannt, gehört ins Meeting am 5. August. (Kontext vRv: Personalvorsorge, Immobilien, Hauswartungen, Treuhand; 28 Mitarbeitende, 20 Vollzeitstellen, Rosenweg 2, Solothurn [Q27, Q28].)

---

## 5. Typische Integrationsmuster ohne API (ABGELEITET, branchenüblich)

Bei Schweizer Treuhand-Paketen ohne öffentliche API (gleiche Klasse wie ältere Sage-, Pinus- oder Q3-Installationen) haben sich vier Muster etabliert. Alles in diesem Abschnitt ist Einschätzung aus Projektpraxis, kein pebe-Beleg, ausser wo markiert:

1. **Dateischnittstelle als Standardweg:** Das Vorsystem erzeugt Import-Dateien exakt im Zielformat, legt sie in einen definierten Ablageort (SharePoint-Ordner, Netzlaufwerk, SFTP), und die Buchhaltung importiert sie im Paket mit Vorschau und Freigabe. Vorteil: robust, prüfbar, revisionsfreundlich. Nachteil: Latenz (Batch) und ein manueller Klick. Dass dieses Muster bei pebe produktiv funktioniert, ist durch contofox belegt [Q13].
2. **Zahlungsverkehr als Integrations-Bus:** Rechnung mit QR-Referenz erzeugen, Verbuchung in die Fibu importieren, Zahlungseingang läuft über camt.053/054 automatisch in pebe auf [Q4, Q12]. Der Zahlungsstatus für das Vorsystem wird entweder aus einem pebe-Export oder direkt aus den camt-Dateien der Bank gelesen. Sehr verbreitet in der Schweiz, weil die Bankformate normiert sind.
3. **Lesender Datenbankzugriff (nur mit Herstellersegen):** Bei On-Premise-Installationen wird gelegentlich ein Read-only-Zugriff auf die Datenbank für Status-Synchronisation eingerichtet. Ob pebe das unterstützt: unbekannt, Herstellerfrage.
4. **RPA/UI-Automation als letzte Option:** Automatisiertes Bedienen des Windows-Clients bzw. der RDP/Citrix-Session. Brüchig (Updates, Session-Handling, Lizenz- und Supportfragen), im gehosteten pebeONLINE-Umfeld zusätzlich heikel. Nur einsetzen, wenn ein zwingender Schritt weder datei- noch bankseitig abbildbar ist, und nur nach Rücksprache mit pebe.

Empfohlene Grundhaltung: Muster 1 + 2 kombinieren, Muster 3 als Frage an pebe mitnehmen, Muster 4 aktiv vermeiden und im Angebot als bewusst ausgeschlossenes Risiko benennen.

---

## 6. Konsequenzen für unsere Architektur-Varianten

**Gemeinsame Grundsätze für alle Varianten (aus der Beleglage):**

- pebeFinance bleibt System of Record für Fibu, Debitoren-OP und Zahlungseingang. Wir bauen keine parallele Debitorenbuchhaltung (Doppelspurigkeit wäre der teuerste Fehler).
- Kopplung dateibasiert und bankseitig, nicht per API. Der Übergabepunkt ist entweder (a) Fakturapositionen an pebeFAKTURA (falls Import-Umfang das hergibt [Q7], zu klären) oder (b) fertige QR-Rechnung aus unserer Plattform plus Buchungsimport in die Fibu [Q13]. Entscheid erst nach Antwort von pebe auf Frage P3/P4 (unten).
- Die Lizenz «Schnittstellen» [Q13] ist harte Voraussetzung und gehört als Kostenposition ins Angebot, falls vRv sie nicht hat.
- Beim Betriebsmodell pebeONLINE (RDP/Citrix bei VoiceLan [Q8, Q9]) muss der Dateitransport in die gehostete Umgebung geklärt werden (gemapptes Laufwerk, SFTP, Ablagefreigabe). Bei lokalem Server genügt ein synchronisierter Ordner.

**Variante A: Power-Platform-first (M365-nativ).** Auftragseingang (Outlook/Forms/Telefonerfassung), Planung (Power Apps/Planner), mobile Hauswart-App (Power Apps, offlinefähig), Zeit/Material in Dataverse, Rechnungsfreigabe in Teams. Power Automate erzeugt die pebe-Importdatei und legt sie samt Prüfprotokoll in SharePoint ab; eine Sachbearbeiterin importiert in pebe (Vorschau, Übernehmen). Konsequenz der Beleglage: Der Import-Klick bleibt, Power Automate kann pebe nicht fernsteuern. Das ist ehrlich als «teilautomatisiert mit Kontrollpunkt» zu verkaufen und passt zum risikoarmen Rollout. Die Outlook-Standardschnittstelle der pebe Leistungserfassung [Q6] ist ein Bonus-Argument, trägt aber keinen Prozess.

**Variante B: Custom-Plattform.** Gleiche Kopplungsflächen, aber eigener Integrationsdienst: erzeugt Importdateien, validiert sie vorab gegen Kontenplan/MWST-Regeln (spiegelt die belegten pebe-Prüfungen [Q13], damit der Import beim ersten Versuch durchläuft), erzeugt bei Bedarf die QR-Rechnung selbst (Swiss QR-Bill ist offener Standard) und liest camt-Dateien für den Zahlungsstatus. Höhere Baukosten, dafür volle Kontrolle über Formate, Wiederholbarkeit und Protokollierung. Sinnvoll, falls pebe keinen Fakturapositions-Import zulässt und wir die Rechnungserzeugung übernehmen müssen.

**Variante C: Hybrid (Empfehlungskandidat).** M365/Power Apps als Front-End (Erfassung, Disposition, mobile Ausführung, Freigaben) plus ein kleiner, eigener Integrationsdienst, der ausschliesslich die pebe-Schnittstelle besitzt: Dateierzeugung, Vorvalidierung, Übergabeprotokoll, Archiv nach SharePoint. Der Import in pebe bleibt anfänglich ein menschlicher Freigabeschritt und wird nur automatisiert, wenn pebe einen unbeaufsichtigten Weg bestätigt. Diese Variante minimiert das grösste Projektrisiko (die unklare letzte Meile zu pebe) bei maximaler M365-Nähe für die Nutzer.

**Risiko-Hinweise für alle Varianten:** (1) Formatspezifikation des Imports muss früh von pebe kommen, sonst blockiert sie den Zeitplan. (2) Falls vRv Debitorenrechnungen heute gar nicht in pebe schreibt (sondern z.B. in einer Immobilien-Fachsoftware), verschiebt sich die ganze Kopplung; unbedingt am 5. August klären. (3) pebe mobile [Q19] im Meeting aktiv adressieren: erklären, warum die Ausschreibung mehr verlangt als Zeiterfassung, sonst wirkt unsere Lösung als teurer Ersatz für eine 5-Franken-App.

---

## 7. Offene Fragen

### An vRv (Meeting 5. August 2026)

1. **V1:** Welche pebeFINANCE-Module sind lizenziert (Fibu, Debitoren, Kreditoren, Lohn, Leistungserfassung, Fakturierung)? Ist die optionale Lizenz «Schnittstellen» vorhanden?
2. **V2:** Welche Version, welcher Wartungsvertrag, wer betreut die Installation (interner IT-Partner, pebe direkt)?
3. **V3:** Betriebsmodell: lokaler Server bei vRv, eigener Terminalserver oder gehostetes pebeONLINE (RDP/Citrix, VoiceLan)? Wer administriert die Umgebung, wie kommen Dateien hinein und heraus?
4. **V4:** Wer schreibt heute Debitorenrechnungen, womit (pebeFAKTURA, Word/Excel, Immobilien-Software)? Wie laufen Mahnwesen und Zahlungsabgleich (camt/EBICS aktiv, QR-Referenzen im Einsatz)?
5. **V5:** Gibt es neben pebe eine Immobilienbewirtschaftungs-Software (Liegenschaftenbuchhaltung, Nebenkosten) oder eine PK-Verwaltungslösung mit eigener Fakturierung? Wo genau soll Order2Cash andocken?
6. **V6:** Wo leben die Debitoren-Stammdaten (Mieter, Eigentümer, STWEG, PK-Kunden), und wer pflegt sie? Erwartung an Stammdaten-Sync?
7. **V7:** Nutzt vRv heute pebe Leistungserfassung oder pebe mobile? Erfahrungen?
8. **V8:** Mengengerüst: Aufträge/Monat, Rechnungen/Monat, Anzahl Hauswarte und Disponenten, Spitzenzeiten.
9. **V9:** M365-Stand: Lizenzen (Business Premium, E3/E5, Power-Platform-Lizenzen?), Nutzung von Teams/SharePoint, wer ist der M365-Partner?
10. **V10:** Welche Exporte/Importe laufen heute schon rund um pebe (Excel-Auswertungen, Bankdateien, Lohn), und wer führt sie aus?

### An pebe AG (direkt, parallel zur Kundenklärung)

1. **P1:** Offizielle Spezifikation des CSV/Excel-Buchungsimports (Spaltenlayout, Pflichtfelder, MWST-Codes, Kostenstellen, Belegnummern, Sammelbuchungen). Gibt es Beispieldateien?
2. **P2:** Ist der Buchungsimport automatisierbar (überwachter Ordner, Kommandozeile, Hintergrundjob) oder ausschliesslich UI-geführt?
3. **P3:** Können Fakturapositionen bzw. erfasste Leistungen aus Fremdsystemen in pebeFAKTURA/pebeLEISTUNG importiert werden (Umfang von «Import von EXCEL und CSV Daten»)? Format?
4. **P4:** Können Debitoren-Stammdaten und Debitoren-OPs strukturiert importiert/exportiert werden? Gibt es einen automatisierbaren Export von Zahlungseingängen/OP-Status (Rückkanal für Statussync)?
5. **P5:** Existiert irgendeine programmatische Schnittstelle zu pebeFINANCE (Webservice, COM, unterstützter Read-only-DB-Zugriff/ODBC)? Falls nein: Ist eine REST-API für pebeFINANCE auf der Roadmap (analog pebe Live)?
6. **P6:** Bei pebeONLINE-Hosting: Wie liefern Drittsysteme Dateien in die Umgebung und holen sie ab (SFTP, Laufwerksfreigabe)? Gibt es Einschränkungen seitens VoiceLan?
7. **P7:** Welche ISO-20022-Versionen sind aktuell unterstützt (pain.001, camt.053/054 nach Swiss Payment Standards)?
8. **P8:** Kosten und Bezug: Lizenz «Schnittstellen», pebe mobile pro Nutzer, ggf. BMD DMS. Bietet pebe Fachberatung für Drittsystem-Integrationen an?

---

## 8. Quellenverzeichnis

| Nr. | Quelle | URL |
|---|---|---|
| Q1 | pebe AG Startseite (Produktgruppen, Mandantenadressen-Import/Export Excel, ZEFIX) | https://www.pebe.ch |
| Q2 | pebe Home «Buchhaltungsprogramme für Schweizer Treuhänder & KMU» (Firma, Logos) | https://www.pebe.ch/de/Home |
| Q3 | pebe Software-Übersicht (Produktfamilie, BMD-Partnerschaft, BMD Commerce/CRM) | https://www.pebe.ch/de/Software |
| Q4 | pebeFINANCE Finanzen (camt.053, EBICS, CSV-Schnittstelle Fremdsysteme, Kreditoren) | https://www.pebe.ch/de/Software/pebeFINANCE/Finanzen |
| Q5 | pebe Buchhaltungssoftware Landingpage (Buchungsimport/-export CSV, Excel/CSV, pebeMOBILE, lokal oder Cloud) | https://www.pebe.ch/Buchhaltungssoftware |
| Q6 | pebeLEISTUNG Leistungserfassung (Verrechnungssätze, OP, Fakturavorschlag, Outlook-Schnittstelle, Offline-App) | https://www.pebe.ch/de/Software/pebeFINANCE/Leistung |
| Q7 | pebeFAKTURA Fakturierung (Sammel-/Massenfakturen, QR, Report Designer, Excel/CSV-Import) | https://www.pebe.ch/de/Software/pebeFINANCE/Fakturierung |
| Q8 | pebe Klienten-Zusammenarbeit (pebeFINANCE Online: RDP/Citrix, SSL; pebeFINANCE Client) | https://www.pebe.ch/de/Software/pebeFINANCE/Klienten |
| Q9 | pebe Cloud/pebe Online (externer Server, Provider VoiceLan) | https://www.pebe.ch/de/Cloud |
| Q10 | pebe FAQ (QR seit Sommer 2020, EBICS, nahtloser Datenaustausch pebeINVEST/pebe Live, RDP/Citrix) | https://www.pebe.ch/de/Uberpebe/FAQ |
| Q11 | pebe Lohnsoftware Landingpage (swissdec, EBICS, QR) | https://www.pebe.ch/de/Landingpages/Lohnsoftware |
| Q12 | topsoft Marktplatz-Eintrag pebeFINANCE (Firma 1977, 11-20 MA, On-Prem, ESR/BESR, camt.054, ZUGFeRD/FacturX, ASCII, swissdec) | https://topsoft.ch/anbieter/pebe-ag/produkte/pebefinance-automatisieren-sie-ihre-buchhaltung/ |
| Q13 | contofox Knowledge Base «Der Importablauf in pebeFINANCE» (Menüpfad, Lizenz «Schnittstellen», Validierung) | https://contofox.com/kb/der-importablauf-in-pebefinanz/ |
| Q14 | pebe Live Website (REST-API-Aussage, Module, Treuhandportal) | https://www.pebelive.ch/ |
| Q15 | pebe Live Handbuch, Release 8.0 November 2023 (REST API, API-Key, Swagger-Link) | https://www.pebelive.ch/live-handbuch/release-herbst-2023/ |
| Q16 | pebe Live API Swagger (existiert, Inhalt nur mit Login/JS einsehbar) | https://app.pebelive.ch/swagger/index.html |
| Q17 | pebe Live Handbuch «Buchungsexport für pebeFINANCE» (Excel-Export, Sperre/Storno) | https://www.pebelive.ch/live-handbuch/buchungsexport-fuer-pebefinanz/ |
| Q18 | pebe Blog «pebe Live, neue Module und Funktionen» (11.07.2022, Excel-Import in pebeFINANCE) | https://www.pebe.ch/DE/Uberpebe/Blog/pebe_Live_%E2%80%93_Neue_Module_und_Funktionen |
| Q19 | pebe Blog «pebe mobile» (Offline-App, Foto-Funktion, CHF 5/Monat/User, Lizenzvoraussetzung) | https://www.pebe.ch/DE/Uberpebe/Blog/pebe_mobile |
| Q20 | pebe mobile in App Store / Google Play | https://apps.apple.com/ch/app/pebe-mobile/id1290720982 und https://play.google.com/store/apps/details?id=ch.pebe.mobile |
| Q21 | pebe Blog «Digitales Belegmanagement» (26.06.2018, BMD DMS, BMD Scan, Workflow-Studio) | https://www.pebe.ch/DE/Uberpebe/Blog/Digitales_Belegmanagement |
| Q22 | pebe Services «Automatic PDF Processor» (Vertriebspartner Gillmeister, E-Mail-Versand von pebe-Dokumenten) | https://www.pebe.ch/de/Services/AutomaticPDFProcessor |
| Q23 | pebeFINANCE «Highlights Version» (ältere Release-Doku: pain.001/DTA, Datei je Bankkonto; Alter beachten) | https://docplayer.org/72770150-Pebefinance-highlights-version.html |
| Q24 | pebe «QR-Rechnung einfach erklärt» (Verarbeitung eingehender QR-Rechnungen) | https://www.pebe.ch/QR-Rechnung-einfach-erklaert |
| Q25 | pebe smart Support «pebe smart API (Offene Schnittstelle)» (Seite liefert 403, nur Titel belegt) | https://pebesmart.zendesk.com/hc/de/articles/115007612748-pebe-smart-API-Offene-Schnittstelle- |
| Q26 | Capterra-Eintrag pebe Live unter Slug «pebe-smart» | https://www.capterra.com.de/software/182907/pebe-smart |
| Q27 | vR verwaltungen ag Website (Personalvorsorge, Immobilien, Hauswartungen, Treuhand) | https://www.vrverwaltungen.ch/de/ |
| Q28 | vR verwaltungen ag Facts & Figures (28 Mitarbeitende, 20 Vollzeitstellen) | https://www.vrverwaltungen.ch/de/facts-figures.html |
| Q29 | pebe Services (Fachberatung, Projektmanagement, Support, pebe academy) | https://www.pebe.ch/de/Services |

---

*Dossier A, erstellt 10.07.2026. Verifizierungsgrad: Abschnitte 2 und 3 quellenbelegt, Abschnitt 5 branchentypische Einschätzung, Abschnitt 6 eigene Ableitung. Nächster Schritt: Fragenkatalog V1 bis V10 ins Meeting-Briefing für den 5. August übernehmen, P1 bis P8 als E-Mail-Entwurf an pebe AG vorbereiten.*
