# Dossier B: Software-Landschaft Immobilienbewirtschaftung Schweiz

> Zweck: Buy-Alternativen kennen, bevor wir am 5.8.2026 bei vR verwaltungen ag Build-vs-Buy ehrlich positionieren. Der Tender verlangt: zentrale Aufgaben-/Auftragsplattform, Workflow-Automatisierung, mobile Hauswart-App (Checklisten, Fotos, Echtzeit-Kommunikation), integrierte Abrechnung/Reporting (Zeit, Material), Schnittstelle zu pebeFinance, "oder alternative Lösungen".
> Stand: 10.7.2026, Web-Recherche. Kennzeichnung: **[V]** = verifiziert (Quelle geprüft), **[I]** = inferred (abgeleitet, nicht öffentlich belegt). Quellennummern [Q#] siehe Quellenverzeichnis.

---

## 1. Zusammenfassung (5 Bullets)

- **Der Schweizer Markt für Bewirtschaftungssoftware ist reif und dicht besetzt.** ImmoTop2, Rimo R5, GARAIO REM und AbaImmo decken Mietbuchhaltung, Heiz-/Nebenkostenabrechnung und Stockwerkeigentum seit Jahrzehnten mietrechtskonform ab [Q1, Q3, Q7, Q10]. Diese Domänenlogik nachzubauen ist chancenlos und unnötig: das sagen wir am 5.8. offen.
- **Keine der geprüften Suiten dokumentiert eine pebeFinance-Schnittstelle.** Alle bringen eine eigene Fibu mit oder koppeln an Abacus/Sage (Rimo R5 exportiert an Abacus, Sage 50, Immopac, Campos u.a., pebe fehlt in der Liste [Q3]). Wer eine Suite kauft, wechselt faktisch die Buchhaltung. pebe AG selbst führt kein Immobilien- oder Service-Modul im Portfolio [Q17], bietet aber CSV-/Standardschnittstellen für Buchungsimport aus Fremdsystemen [Q18, Q19]: genau dort kann eine Custom-Plattform andocken.
- **Die Hauswart-Anforderung wird von Standardsoftware nur generisch gelöst.** Am nächsten kommt Abacus mit AbaImmo plus AbaSmart 2 (Serviceaufträge mobil, PDF-Checklisten, Fotos, Material-/Zeiterfassung, Unterschrift) [Q12]. GARAIO OnSite (Schadenmeldung, Liegenschaftscheck) [Q8] und W&W Ticketing/Abnahme-App [Q1, Q2] decken Teilstücke. Reine FSM-Apps (PlanRadar, Craftnote, Blink) können Doku, Checklisten und Zeit, aber keine Verrechnung nach vRv-Vertragslogik und keine pebe-Anbindung [Q20, Q22, Q23].
- **vRv ist kein reiner Bewirtschafter, und genau das ist die Lücke im Standardmarkt.** Hauswartung als eigenes Team mit Leistungsverrechnung, dazu Stiftungs-/BVG-Administration und Treuhand: ein durchgängiger Order2Cash-Prozess über alle drei Geschäftsfelder existiert als Standardprodukt nicht. Immo-Suiten bilden nur das Bewirtschaftungsfeld ab. Dort, im Workflow-Layer über pebe und O365, gewinnt Custom.
- **Wahrscheinlichste Mitbieter [I]:** Abacus-Partner (BDO, Axept, All Consulting, Customize, Aandarta), W&W Immo Informatik, GARAIO REM (Bern, geografisch nah) sowie der bestehende IT-Dienstleister von vRv mit einer Microsoft-Variante (der Tender skizziert diese selbst und fragt Rechenzentrum/Managed Services ab). Unsere Position: ehrlicher Architekt, der Standard integriert statt nachbaut.

---

## 2. Marktübersicht

| Produkt | Anbieter | Fokus | Mobile / Hauswart | O365- / pebe-Bezug | Zielgrösse | Quelle |
|---|---|---|---|---|---|---|
| ImmoTop2 | W&W Immo Informatik AG, Affoltern a.A. + Bern | Gesamtlösung Bewirtschaftung Miete/STWE, integrierte Fibu, NK-Abrechnung | Abnahme-App (Tablet), W&W Portal & App, EasyContact-Meldeformular, Ticketing mit Zuweisung an Handwerker/Hauswart | Office-Integration inkl. Microsoft 365 [V]; pebe: nichts dokumentiert [I] | einige Dutzend bis mehrere tausend Objekte; >2800 Kunden W&W | [Q1, Q2] |
| Rimo R5 | W&W-Produktfamilie; Vertrieb/Cloud u.a. eXtenso IT-Services AG, Zürich | Bewirtschaftung Miete/STWE/Genossenschaften, integrierte Fibu, Heiz-/NK-Abrechnung | RIMO Sign Wohnungsprotokoll (iPad, Fotos, Unterschrift); Hauswart-Lohnprogramm; kein Hauswart-Auftrags-Cockpit dokumentiert | Export an Abacus, Sage 50, Flatfox, Immopac, Campos, Reamis, VRSG; DMS Canon/ELO/Docuware; pebe fehlt [V] | mittlere bis grössere Verwaltungen, hunderte bis tausende Objekte | [Q3, Q4, Q5] |
| GARAIO REM | GARAIO REM AG, Bern | Umfassendste CH-Suite: Rechnungswesen, Bewirtschaftung, STWE, Kostenmiete, Auftragswesen, Inkasso, Reporting; >1.9 Mio. verwaltete Objekte | OnSite-App: Schadenmeldung + Liegenschaftscheck; digitales Abnahmeprotokoll; Eigentümerportal, Mieterservices | O365: nichts dokumentiert [I]; pebe: nichts dokumentiert [I] | Grossbewirtschafter ("Profis für Profis"); REM light via Partner für <3500 Objekte | [Q6, Q7, Q8, Q9] |
| AbaImmo | Abacus Research AG, St. Gallen (Vertrieb via Partner) | Modulare Suite: Stammdaten, Sollstellungen, Mietverträge, Heiz-/NK-Abrechnung, integrierte Fibu/Debi/Kredi, webbasiert | AbaSmart 2: mobile Serviceaufträge mit Fotos, PDF-Checklisten, Barcode/QR-Material, Zeiterfassung, Unterschrift | Exchange-Integration [V]; WebService-XML/ASCII; koppelt an Abacus-Welt, nicht pebe [I] | alle Betriebsgrössen konfigurierbar; Genossenschaften, Anleger, Treuhänder | [Q10, Q11, Q12] |
| Fairwalter | Fairwalter AG, Zürich | Cloud-native Verwaltung: Vermietung, NK-Abrechnung, Buchhaltung mit KI-Belegextraktion, Dokumenten-KI | Wohnungsübergabe-App, Inventar/Schäden; kein Hauswart-Auftragswesen dokumentiert | Hosting Schweiz auf Azure [V]; O365-Workflows: nichts dokumentiert [I]; pebe: nein [I] | privat bis mittlere Verwaltungen; CHF 29 bis 699/Mt. (10 bis 1000 Objekte) | [Q13, Q14] |
| Quorum Digital | Quorum Software SA, Genf/Lausanne/Aarau | Integrierte Verwaltung: Mietzins, Verträge, Mahnwesen, Abrechnungen | keine Mobile-/Hauswart-Funktionen dokumentiert | Office-kompatibel (Word/Excel) [V]; pebe: nein [I] | Verwaltungen aller Grössen, STWEG, Genossenschaften; stark Romandie [I] | [Q15, Q16] |
| pebeFINANCE | pebe AG, Frauenfeld | Fibu, Debi, Kredi, Lohn, Leistungserfassung, Fakturierung, Anlagen; Treuhand-Standard | keine | Ist das Bestandssystem von vRv; CSV-/Standardschnittstelle für Fremdsysteme, camt.053, EBICS; kein Immo-Modul | Treuhand + KMU | [Q17, Q18, Q19] |

FSM-/Hauswart-Apps (Detail in Abschnitt 4): PlanRadar [Q20, Q21], Craftnote [Q22], Blink [Q23], Yarowa [Q24], ImmoApp/ImmoDigi [Q25], Campos [Q26].

---

## 3. Detailprofile der relevantesten Lösungen

### 3.1 ImmoTop2 (W&W Immo Informatik AG)

**Verifiziert:** Gesamtlösung mit vollständig integrierter Buchhaltung, NK-Abrechnung (Erfolgsrechnung, Abrechnungsblatt, Budgetverteilung), Mietwechselassistent, über 100 Standardauswertungen [Q1]. Mobile Prozesse via W&W Portal und App, Abnahme-App für digitale Wohnungsabnahmen auf Tablet, EasyContact als Meldeformular für Mieter/Eigentümer ohne Login. Ticketing bündelt Anliegen und weist sie automatisch Handwerkern oder Hauswarten zu, mit Statusmeldung an den Melder [Q1, Q2]. Cloud in drei Paketen ab CHF 149/Monat, on-premise möglich, Office-Integration bis Microsoft 365 [Q1]. Über 2800 Kunden im W&W-Ökosystem, skalierbar von Dutzenden bis tausenden Objekten [Q1, Q2].

**Einordnung [I]:** Der Volumen-Marktstandard der Deutschschweiz, HEV-nah. Für vRv wäre das der "sichere" Kauf, aber: eigene Fibu statt pebe, generisches Ticketing statt vRv-Order2Cash, keine Stiftungs-/Treuhandprozesse.

### 3.2 GARAIO REM (GARAIO REM AG, Bern)

**Verifiziert:** Nach eigenen Angaben verwaltet die Software täglich über 1.9 Mio. Objekte und positioniert sich als umfassendste Bewirtschaftungssoftware der Schweiz [Q6]. Funktionsumfang: Rechnungswesen, Bewirtschaftung, STWE, Kostenmiete, An-/Umsatzmiete, Auftragswesen, Inkasso/Exkasso, Reporting [Q7]. OnSite-App mit zwei Modulen (Schadenmeldung, Liegenschaftscheck) für Arbeit vor Ort [Q8]. Digitales Abnahmeprotokoll, Eigentümerportal, Mieterservices [Q7]. Keine öffentliche Preisliste. Für kleinere Verwaltungen unter 3500 Objekten gibt es GARAIO REM light über die Partner immonos und AddServices mit monatlichem Preismodell [Q9].

**Einordnung [I]:** Technologisch der modernste Grossanbieter, Sitz in Bern, also 30 Minuten von Solothurn. Kernzielgruppe sind aber institutionelle Bewirtschafter; vRv mit 28 Mitarbeitenden liegt eher im REM-light-Partnersegment. O365- und pebe-Integration: nicht dokumentiert.

### 3.3 AbaImmo + AbaSmart (Abacus Research AG)

**Verifiziert:** Modulare Gesamtlösung mit Immobilien-Stammdaten, Sollstellungen, Mietverträgen, Heiz-/NK-Abrechnung und integrierter Finanz-, Debitoren- und Kreditorenbuchhaltung, webbasiert, für alle Betriebsgrössen konfigurierbar; Zielgruppen: Baugenossenschaften, Anleger, Immobilientreuhänder [Q10, Q11]. Schnittstellen: WebService-XML, ASCII, Exchange-Integration, Anbindung weiterer Abacus-Module (Lohn, HR, Zeiterfassung, CRM, E-Banking) [Q11]. Die App AbaSmart 2 verarbeitet Serviceaufträge mobil: Auftragsempfang, Material-/Leistungserfassung inkl. Barcode/QR, Fotos, ausfüllbare PDF-Checklisten, digitale Kundenunterschrift, Zeiterfassung inkl. Wegzeit [Q12]. Vertrieb und Einführung laufen über Partner (Aandarta, Axept mit AXimmo, Customize, All Consulting, BDO u.a.) [Q11, Q27, Q28, Q29, Q30]. Keine öffentlichen Preise.

**Einordnung [I]:** Der gefährlichste Konkurrenz-Pitch für diese Ausschreibung: AbaImmo plus AbaSmart trifft die Hauswart-Anforderung (Checklisten, Fotos, Zeit, Material, Verrechnung) am vollständigsten, und Abacus deckt via Lohn/Treuhand-Module auch Nachbarfelder ab. Der Preis dafür: Wechsel der gesamten Buchhaltungswelt von pebe zu Abacus, Partnerprojekt mit klassischem ERP-Einführungsaufwand, laufende Lizenzkosten. Genau diese Trade-offs müssen wir am 5.8. sauber benennen können.

### 3.4 Rimo R5 (W&W-Produktfamilie / eXtenso IT-Services AG)

**Verifiziert:** Bewirtschaftung von Miete, STWE und Genossenschaften mit integrierter Liegenschaftsbuchhaltung, Heiz-/NK-Abrechnung mit QR-Rechnung, Offene-Posten-Verwaltung; als Einplatz-, Mehrplatz- oder Cloud-Lösung (eXtenso Cloud) [Q3, Q4]. Export-Schnittstellen zu Abacus, Sage 50, Flatfox, Immopac, Campos, Reamis, VRSG sowie DMS-Anbindungen (Canon, ELO, Docuware) [Q3]. RIMO Sign Wohnungsprotokoll-App für digitale Abnahmen mit Fotodokumentation und Unterschrift [Q5]. Integriertes Lohnprogramm für Hauswarte mit Verbuchung auf die Liegenschaft [Q3]. Zielgruppe: mittlere bis grössere Verwaltungen [Q3].

**Einordnung [I]:** Solide, verbreitet, aber die Mobile-Story beschränkt sich auf Abnahmeprotokolle. Bemerkenswert: die dokumentierte Schnittstellenliste nennt viele Fibu-Systeme, pebe ist nicht darunter.

### 3.5 Fairwalter (Fairwalter AG)

**Verifiziert:** Cloud-native Software für Verwaltung, Vermietung mit digitalem Mieterwechsel, NK-Abrechnung (Zählerstände, Akonto), Buchhaltung mit Reporting/Bilanz/Erfolgsrechnung, Kreditoren mit automatischer Belegextraktion, KI-gestütztes Dokumentenmanagement, Wohnungsübergabe-App, Bank-API [Q13]. Fünf Pakete von CHF 29 (10 Objekte) bis CHF 699/Monat (1000 Objekte, unbegrenzte Nutzer), Hosting in der Schweiz auf Microsoft Azure [Q14].

**Einordnung [I]:** Der agile Newcomer mit transparentem Pricing; zeigt, wo der SaaS-Markt preislich liegt. Für vRv als Komplettantwort zu schmal (kein Hauswart-Auftragswesen, keine Stiftungs-/Treuhandtiefe), aber ein nützlicher Preisanker in der Verhandlung.

### 3.6 Quorum Digital (Quorum Software SA)

**Verifiziert:** Integrierte Verwaltungslösung (Mietzinserhebung, Kreditorenzahlung, Inkasso, Verträge, Mahnwesen, Abrechnungen) für Verwaltungen aller Grössen, STWEG, Genossenschaften und Eigentümer; Hosting 100% in der Schweiz; Office-kompatibel; Firma seit 1998, Standorte Genf, Lausanne, Aarau, dreisprachig, swiss made software [Q15, Q16]. Keine Mobile-/Hauswart-Funktionen und keine Preise dokumentiert.

**Einordnung [I]:** Stark in der Romandie verankert; für diese Deutschschweizer Ausschreibung mit Hauswart-Fokus wenig wahrscheinlich als ernsthafter Mitbieter.

---

## 4. Hauswart- / FSM-Apps (standalone einsetzbar)

Diese Werkzeuge lösen Teilprobleme (Doku, Checklisten, Zeit), aber keines verrechnet nach vRv-Vertragslogik oder spricht pebe:

- **PlanRadar (Wien):** Mängel-/Gebäudedoku und FM: Tickets mit Fotos, Sprach-/Textnotizen, GPS-verortet auf dem Plan, digitale Checklisten, Wartungspläne, automatische PDF-Protokolle [Q21]. Preise pro Nutzer/Monat: Basic ab ca. EUR 26 bis 29, Starter ca. EUR 89 bis 99, Pro ca. EUR 129 bis 149, Enterprise auf Anfrage; Open API und über 200 Integrationen via PlanRadar Connect, Microsoft-365-Integration ab Pro [Q20]. Stark in Doku und Compliance, schwach in Verrechnung.
- **Craftnote (DE):** Digitale Baumappe für Handwerksteams: Projektordner mit Fotos/Plänen/Dokumenten, Aufgaben-Checklisten, Stechuhr-Zeiterfassung je Projekt und Mitarbeiter, Berichte, Kundenunterschrift, konsequent offline-first. EUR 14.90 bis 49.90 pro Nutzer/Monat [Q22]. Günstigster Einstieg für Foto-/Zeitdoku, aber Bau- statt Bewirtschaftungslogik, deutscher Anbieter.
- **Blink (Nürnberg):** App für Gebäudereinigung/-dienste: Zeiterfassung per QR-Code, NFC, GPS-Abgleich, Einsatz-/Schichtplanung, Tickets, Qualitätsmanagement, Chat mit Übersetzung in 19 Sprachen [Q23]. Passt auf die Reinigungs-/Hauswartungs-Belegschaft, DSGVO-orientiert (DE), keine CH-Immobilien-Domänenlogik, keine öffentliche Preisliste gefunden.
- **Yarowa (Zug):** Keine Hauswart-App, sondern eine B2B-Plattform für Auftrags- und Dienstleistermanagement: passende Handwerker/Dienstleister finden, digital beauftragen, Termine mit Mietern koordinieren, Status transparent; verbreitet bei Versicherungen und Immobilienbewirtschaftern [Q24]. Relevant für vRv dort, wo externe Dienstleister koordiniert werden, nicht für das eigene Hauswart-Team.
- **ImmoApp (ImmoDigi AG, Schweiz):** Bewohner-/Verwaltungs-App: Schaden-/Reparaturmeldungen, Pinnwand, Dokumente, Abstimmungen, Reservationen; Zielgruppen Mieter, STWE, Hauswarte, Verwaltungen; ab CHF 140/Monat, über 25 000 Nutzer, täglicher Stammdatenimport aus bestehenden Verwaltungssystemen [Q25]. Gute Referenz für die Kommunikationsschicht Mieter/Eigentümer.
- **Campos (ICFM AG, Schweiz):** Webbasierte CAFM-Plattform: Instandhaltungsaufträge zuweisen, terminieren, dokumentieren, auswerten; Flächen- und Energiemanagement; über 160 Firmen, typisch Gemeinden/Städte/Kantone [Q26]. Eher Betreiber-/Portfoliosicht als Hauswart-Alltag; Rimo R5 hat eine dokumentierte Campos-Schnittstelle [Q3].

**Fazit [I]:** vRv könnte mit FSM-Apps schnell Fotos und Checklisten digitalisieren, hätte danach aber drei unverbundene Silos (FSM-App, pebeFinance, O365) und immer noch keinen Order2Cash. Diese Apps sind für uns eher Feature-Referenz und mögliche Komponenten als Konkurrenz.

---

## 5. Build-vs-Buy-Landkarte (ehrlich)

**Wo Standardsoftware schlägt, was wir je bauen könnten:**

| Domäne | Warum Standard gewinnt |
|---|---|
| Miet-/Liegenschaftsbuchhaltung, Sollstellung, Inkasso, Mahnwesen | Jahrzehnte Domänenlogik, OR-/mietrechtskonform, QR-Rechnung, camt/EBICS, revisionserprobt [Q1, Q3, Q10] |
| Heiz-/Nebenkostenabrechnung | Verteilschlüssel, Akonto-Logik, kantonale Eigenheiten; jede Suite kann das seit Jahren [Q1, Q3, Q10, Q13] |
| Stockwerkeigentum, Mietzinsanpassungen, Formularwesen | Gepflegte Rechtslogik, laufende Updates durch Hersteller [Q7, Q10] |
| Digitale Wohnungsabnahme | Fertige, gerichtserprobte Protokoll-Apps: W&W Abnahme-App, RIMO Sign, GARAIO DAP, Fairwalter Übergabe [Q1, Q5, Q7, Q13] |
| Mieter-/Eigentümerportale | Von der Stange verfügbar (W&W Portal, GARAIO Portale, ImmoApp) [Q1, Q7, Q25] |

**Wo Custom schlägt, was Standard je liefern wird:**

| Domäne | Warum Custom gewinnt |
|---|---|
| Order2Cash über ALLE Geschäftsfelder | vRv mischt Bewirtschaftung, eigenes Hauswartungs-Profitcenter, Stiftungs-/BVG-Administration und Treuhand. Keine Immo-Suite bildet diese Kombination ab; alle enden an der Grenze des Bewirtschaftungsmandats [I, gestützt auf Funktionsumfänge Q1, Q7, Q10] |
| pebeFinance bleibt führendes Fibu-System | Keine geprüfte Suite dokumentiert eine pebe-Schnittstelle; pebe bietet CSV-/Standardimport, camt.053, EBICS [Q18, Q19]. Ein Custom-Layer verbucht Leistungen direkt nach pebe, ohne Fibu-Migration und ohne Doppelerfassung |
| Hauswart-UX exakt auf vRv-Prozesse | Vertrag → wiederkehrende Aufgaben → Checkliste mit Foto-Pflichtfeldern → Zeit/Material → Freigabe → Verrechnung, inkl. GPS und Echtzeit-Chat mit Mietern/Eigentümern: Standard-Apps liefern generische Tickets, kein vRv-Prozessmodell |
| O365-Tiefenintegration | Outlook, Teams, Planner als Arbeitsoberfläche statt Parallelwelt; Suiten koppeln nur oberflächlich (Office-Dokumente, Exchange) [Q1, Q11, Q15] |
| KI-Automatisierung | Belegverarbeitung, Priorisierung von Meldungen, Antwortentwürfe, Auswertungen auf vRv-Daten; bei Suiten nur als generische Roadmap-Features (Fairwalter Dokumenten-KI, AbaSmart AI) [Q13, Q12] |
| Kostenmodell | SaaS-Suiten kosten wiederkehrend pro Objekt/Nutzer (Anker: CHF 149 bis 699+/Mt. plus Einführung [Q1, Q14]); Custom ist Invest plus schlanker Betrieb, ohne Objektlizenzen |

**Die ehrliche Synthese [I]:** Die beste Architektur für vRv ist hybrid. Falls vRv eine vollwertige Bewirtschaftungs-Suite braucht (Frage fürs Meeting: was nutzen sie heute neben pebeFinance?), soll sie eine kaufen, nicht bauen lassen. Der Wert, den wir bauen, liegt eine Ebene darüber: die zentrale Auftrags- und Workflow-Plattform, die Hauswart-App, die pebe-Anbindung, die O365-Verzahnung und die KI-Automatisierung, also genau die vier Umsetzungspunkte des Tenders.

---

## 6. Was das für unsere Positionierung am 5.8. heisst

1. **Als Architekt auftreten, nicht als Software-Verkäufer.** Der Tender verlangt explizit "Architektur und Projektleitung". Wir präsentieren drei Wege mit ehrlichen Trade-offs: (a) Standard-Suite (stark in Buchhaltung/NK, erzwingt Fibu-Wechsel weg von pebe, generische Hauswart-UX, Lizenzkosten pro Objekt), (b) Microsoft-Bordmittel (siehe Dossier C), (c) Custom-Plattform als Workflow-Layer über pebeFinance und O365. Empfehlung: Hybrid mit Custom-Layer, Standard dort einkaufen, wo Domänenlogik tief ist.
2. **Den Abacus-Pitch vorwegnehmen.** Ein Abacus-Partner wird AbaImmo plus AbaSmart demonstrieren, und das wird gut aussehen. Unsere vorbereitete Antwort: Gesamtmigration der Buchhaltungswelt (pebe raus, Abacus rein, Treuhand-Seite betroffen), Einführungsprojekt plus laufende Lizenzen, generische Service-App statt vRv-Prozess, Stiftungs-/BVG-Prozesse bleiben trotzdem draussen.
3. **pebe-Erhalt als Differenzierer spielen.** "Primär suchen wir eine Integration der heutigen Lösung pebeFinance in die O365-Welt" steht wörtlich im Tender. Wir sind der einzige Weg, der das wörtlich nimmt: pebe bleibt führend, wir verbuchen über die dokumentierten Import-Schnittstellen (CSV/Standardschnittstelle, camt.053) [Q18, Q19]. Vorbehalt sauber benennen: pebe dokumentiert keine öffentliche REST-API [I], Integrationstiefe ist mit pebe AG früh zu verifizieren, idealerweise vor Offertabgabe.
4. **Ehrlichkeit als Taktik.** Wir sagen aktiv, was wir NICHT bauen (NK-Abrechnung, Mietbuchhaltung, Abnahmeprotokolle) und wo Standard besser ist. Das macht die Custom-Empfehlung für den Rest glaubwürdig und unterscheidet uns von jedem Suite-Anbieter, der "alles" kann.
5. **Fragen fürs Meeting:** Welche Bewirtschaftungssoftware ist heute im Einsatz (der Tender nennt nur pebeFinance; möglich, dass vieles über pebe plus Office läuft [I])? Wie viele Objekte/Mandate? Ist die Stiftungs-/BVG-Administration Teil des Scopes (dann gilt die Archivierungsanforderung 10 Jahre bis Alter 100 auch für die Plattform)? Gibt es eine Datenresidenz-Vorgabe Schweiz (relevant, weil PlanRadar/Craftnote/Blink AT/DE-Anbieter sind und ImmoDigi Server in Zürich/Frankfurt nennt [Q25])?
6. **Preisanker nutzen.** Öffentliche Signale: ImmoTop2 Cloud ab CHF 149/Mt. [Q1], Fairwalter CHF 29 bis 699/Mt. [Q14], PlanRadar bis ca. EUR 149 pro Nutzer/Mt. [Q20], ImmoApp ab CHF 140/Mt. [Q25]. Eine Suite-Einführung mit Migration und Schulung liegt real deutlich über den Listenpreisen [I]. Unser Angebot sollte Invest und Betrieb transparent trennen, genau wie der Tender es verlangt (Setup, Migration, Schulung separat ausweisen).

---

## 7. Wahrscheinliche Mitbewerber in dieser Ausschreibung

Alles in diesem Abschnitt ist **[I]** (Ableitung aus Produktfit, Geografie und Tender-Inhalt; wer tatsächlich angefragt wurde, wissen wir nicht):

- **Abacus-Kanal (höchste Wahrscheinlichkeit):** BDO (Abacus-/AbaImmo-Beratung, Treuhand-Nähe, Präsenz in der Region [Q28]), Axept mit AXimmo [Q27], All Consulting (Bern, historisch aus Solothurn [Q29]), Customize (Gold-Partner AbaImmo [Q30]), Aandarta (AbaImmo plus ImmoApp [Q11, Q25]). Treffen Buchhaltung, Immo und Lohn aus einer Hand; ihre Schwäche ist der erzwungene pebe-Ablösepfad und die generische Mobile-UX.
- **Suite-Direktanbieter:** W&W Immo Informatik (Marktbreite, HEV-Nähe, Cloud-Einstieg ab CHF 149 [Q1]), GARAIO REM AG (Sitz Bern, modernste Plattform, OnSite [Q6, Q8]; für vRv-Grösse eher via REM-light-Partner immonos/AddServices [Q9]), eXtenso (Rimo R5 [Q3]).
- **Microsoft-Lager:** Der Tender enthält bereits eine ausformulierte "Variante Microsoft" und fragt Rechenzentrum, Firewalls, VPN und Managed Services ab. Das deutet stark darauf hin, dass der bestehende IT-Dienstleister von vRv mitbietet oder die Idee geliefert hat. Kandidatenprofil: regionale M365-/MSP-Häuser wie MTF (IT Partner Solothurn), Support-4-IT (Bern/Solothurn), lightnet (Oberaargau) oder spezialisierte Power-Platform-Häuser wie IOZ [Q31, Q32]. Gegen diese gewinnen wir mit Fach-Tiefe (Hauswart-Prozess, Verrechnung, pebe) statt Infrastruktur-Breite.
- **pebe AG selbst:** Als Bestandslieferant gesetzt im Gespräch, hat aber kein Immobilien-/FSM-Produkt im Portfolio [Q17]; denkbar ist ein Vorstoss über die BMD-ERP-Partnerschaft [Q17]. Eher Partner als Gegner: eine früh abgestimmte Integrations-Zusage von pebe stärkt unser Angebot.
- **FSM-Pure-Player (PlanRadar, Blink, Craftnote):** Bieten keine Architektur- und Projektleitungsrolle und keine Abrechnungs-/pebe-Tiefe; als Generalanbieter unwahrscheinlich, als Komponente in fremden Offerten möglich.

---

## 8. Quellenverzeichnis

Alle Quellen abgerufen am 10.7.2026.

- [Q1] W&W Immo Informatik, ImmoTop2 Produktseite: https://www.wwimmo.ch/produkte/immotop2/
- [Q2] W&W News ImmoTop2 (Ticketing, EasyContact, Apps): https://www.wwimmo.ch/meta-links/aktuell/news/news-beitraege/news-2020-1-immotop2.html sowie HEV Schweiz: https://www.hev-schweiz.ch/vermieten/verwalten/immobilien-software/software-immotop2
- [Q3] eXtenso IT-Services, Angebot Rimo R5 (Funktionen, Schnittstellenliste, Cloud): https://www.extenso.ch/angebot
- [Q4] W&W Produktseite Rimo R5: https://www.wwimmo.ch/produkte/rimor5/
- [Q5] RIMO Sign Wohnungsprotokoll R5, App Store: https://apps.apple.com/ch/app/rimo-sign-wohnungsprotokoll-r4/id923389707
- [Q6] GARAIO REM Startseite (1.9 Mio. Objekte): https://www.garaio-rem.ch/de/home
- [Q7] GARAIO REM Funktionen: https://www.garaio-rem.ch/de/garaio-rem-entdecken/funktionen und Funktionsumfang-PDF: https://www.garaio-rem.ch/hubfs/Dateien/GARAIO%20REM%20Funktionsumfang%20v1.26.pdf
- [Q8] GARAIO REM OnSite: https://onsite.rem.ch/
- [Q9] GARAIO REM light (Partner immonos/AddServices, <3500 Objekte): https://www.garaiorem-light.ch/ und https://www.garaio-rem.ch/de/garaio-rem-entdecken-garaio-rem-light
- [Q10] Abacus, AbaImmo Flyer/Funktionsübersicht: https://www.abacus.ch/fileadmin/ablage/02_dokumente/01_flyer/de/flyer_abacus_abaimmo-immobilienbewirtschaftung_de.pdf und https://media.abacus.ch/abacus/produkte/AbaImmo/Abacus_Prosp_AbaImmo_2019_de_web.pdf
- [Q11] Aandarta, AbaImmo (Zielgruppen, Schnittstellen inkl. Exchange): https://www.aandarta.ch/loesungen/abaimmo/
- [Q12] Abacus AbaSmart (mobile Serviceaufträge): https://www.abacus.ch/abasmart und App Store: https://apps.apple.com/ch/app/abasmart-2/id1562951482
- [Q13] Fairwalter Website (Funktionen): https://www.fairwalter.com/
- [Q14] HEV Schweiz, Fairwalter (Preise, Azure-Hosting Schweiz): https://www.hev-schweiz.ch/vermieten/verwalten/immobilien-software/fairwalter-professionelle-websoftware-fuer-vermieter-und-immobilienverwaltungen
- [Q15] Quorum Digital: https://www.quorumsoftware.ch/de/ und Modulseite: http://www.quorumsoftware.ch/QSSA_Website/ModulesDE.html
- [Q16] swiss made software, Quorum Software SA: https://www.swissmadesoftware.org/en/companies/quorum-software-sa/home.html
- [Q17] pebe AG, Software-Portfolio (kein Immo-Modul gelistet; BMD-Partnerschaft): https://www.pebe.ch/de/Software
- [Q18] pebeFINANCE Produktseite (Module, camt.053, EBICS, CSV): https://www.pebe.ch/de/Software/pebeFINANCE/Finanzen
- [Q19] topsoft, pebeFINANCE (Schnittstellen): https://topsoft.ch/anbieter/pebe-ag/produkte/pebefinance-automatisieren-sie-ihre-buchhaltung/
- [Q20] PlanRadar Preise (inkl. M365-Integration ab Pro, Open API): https://www.planradar.com/de/preise/
- [Q21] PlanRadar Facility Management: https://www.planradar.com/at/facility-management-software/
- [Q22] Craftnote (Funktionen, Preise): https://craftnote.de/ und https://craftnote.de/funktionen/
- [Q23] Blink (Zeiterfassung QR/NFC/GPS, Tickets, Chat): https://www.blink.de/ und https://www.blink.de/blink-time/
- [Q24] Yarowa (Auftrags-/Dienstleistermanagement): https://www.yarowa.com/deutsch-ch/home/ und https://www.yarowa.com/de-1/f%C3%BCr-immobilienbewirtschafter/
- [Q25] ImmoDigi, ImmoApp (Funktionen, ab CHF 140/Mt., >25 000 Nutzer, Server Zürich/Frankfurt): https://immodigi.ch/produkte/immoapp
- [Q26] Campos CAFM (ICFM AG): https://www.campos.ch/ und https://www.icfm.ch/
- [Q27] Axept, AXimmo: https://www.axept.ch/aximmo
- [Q28] BDO, Abacus/AbaImmo-Beratung: https://www.bdo.ch/de-ch/services-de/beratung/abacus/abaimmo
- [Q29] All Consulting, Geschichte (Abacus-Partner, Standort Bern/Solothurn): https://all-consulting.ch/de/uber-uns/geschichte-der-all-consulting
- [Q30] Customize AG (Abacus Gold-Partner, AbaImmo): https://customize.ch/ueber-uns/
- [Q31] MTF, IT Partner Solothurn: https://mtf.ch/de/links/it_partner_solothurn/
- [Q32] IOZ AG (M365/Power Platform): https://www.ioz.ch/

**Recherche-Lücken (offen markiert):** Preise für GARAIO REM, AbaImmo, Rimo R5 und Quorum sind nicht öffentlich; pebe-API-Tiefe nur über Produktseiten belegt, direkte Verifikation bei pebe AG steht aus; welche Bewirtschaftungssoftware vRv heute nutzt, ist unbekannt und erste Frage am 5.8.
