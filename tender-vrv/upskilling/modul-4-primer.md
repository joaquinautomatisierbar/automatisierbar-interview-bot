# Modul 4 · Immobilienverwaltungs-Domäne, Order2Cash, pebeFinance

> **Session 1 · Owner: Nico** (unterrichtet die anderen drei, 60 min) · danach 15 min Quiz ([modul-4-quiz.md](modul-4-quiz.md)) + 15 min Drill.
> Ziel: Am 5.8. sprechen alle vier die Sprache des Kunden, verstehen seinen Geldfluss und können pebeFinance kompetent einordnen. Quellen: Dossier A (pebe), Dossier B (Software-Landschaft), Ausschreibung, eigene Walk-in-Gespräche mit Verwaltungen.

## 1. Warum dieses Modul zuerst

Rolf Schmid ist Wirtschaftsprüfer, Ivan Guldimann führt die Bewirtschaftung, Florian Kunz die Hauswartung. Die drei merken in den ersten fünf Minuten, ob wir ihre Welt verstehen oder nur unsere Technik. Fachkompetenz in ihrer Domäne ist der Türöffner für alles andere; die Technik glauben sie uns danach von selbst.

## 2. Die Branche in 12 Begriffen

| Begriff | Was es heisst | Warum es uns betrifft |
|---|---|---|
| **Bewirtschaftung** | Laufende Betreuung von Liegenschaften im Auftrag der Eigentümer (Vermietung, Unterhalt, Abrechnung) | Das ist Guldimanns Welt; unsere Plattform bildet ihre Aufträge ab |
| **Mandat** | Der Vertrag zwischen Eigentümer und Verwaltung; definiert Leistungen + Honorar | "Vertragliche Aufgaben" aus der Ausschreibung = Mandatspflichten; wiederkehrende Aufgaben entstehen aus dem Mandat |
| **Liegenschaft / Objekt** | Gebäude bzw. einzelne Einheit (Wohnung, Gewerbe) | Grundstruktur unserer Datenhaltung; Frage a1 fragt die Anzahl |
| **STWE / STWEG** | Stockwerkeigentum / -gemeinschaft: viele Eigentümer in einem Haus, Verwaltung organisiert Versammlungen, Erneuerungsfonds, gemeinsame Kosten | Andere Abläufe als Miete (Beschlüsse!); vRv verwaltet vermutlich beides |
| **Mietzins, Nebenkosten (NK), Akonto** | Miete + Vorauszahlungen für Heizung/Wasser etc., jährlich abgerechnet | NK-Abrechnung ist ein Branchen-Kernschmerz, aber NICHT unser Bauziel (Standard-Software kann das seit Jahrzehnten) |
| **Sollstellung** | Das buchhalterische "Einfordern" der Miete (Debitorenposition entsteht) | pebe-Sprache; Zahlungseingang gleicht gegen Sollstellungen ab |
| **Eigentümer vs. Mieter vs. Auftraggeber** | Drei verschiedene "Kunden" mit verschiedenen Interessen | Die Ausschreibung nennt "Echtzeit-Kommunikation mit Mietern, Eigentümern oder Auftraggebern": drei Zielgruppen, nicht eine |
| **Hauswartung intern** | vRv hat ein EIGENES Hauswart-Team (Leiter: Kunz), verrechnet dessen Leistungen | Das ist der Order2Cash-Kern: eigene Leute, eigene Rapporte, eigene Verrechnung. Nicht verwechseln mit externen Handwerkern |
| **Regie / Regiearbeiten** | Arbeiten nach Aufwand (Stunden + Material), nicht pauschal | Genau diese Leistungen gehen heute am häufigsten verloren |
| **Rapport** | Der Arbeitsnachweis des Hauswarts (was, wo, wie lange, Material) | Heute Papier/Zettel; unsere App macht daraus strukturierte Daten |
| **Mandatsleiter** | Verantwortliche Person pro Mandat (bei vRv z.B. Mischler für Treuhand) | Buying Center: jeder Mandatsleiter ist ein interner Stakeholder |
| **SVIT / HEV** | Branchenverbände (Bewirtschafter / Hauseigentümer) | Referenzrahmen für Standards; SVIT-Vorgaben können Doku-Anforderungen setzen (Frage g9) |

## 3. vRv konkret: wer sie sind

- **5 Geschäftsfelder:** Personalvorsorgeverwaltung (Stiftungen! BVG!), Immobilienbewirtschaftung, Immobilienverkauf, **eigene Hauswartung**, Treuhand. ~28 Mitarbeitende, ~10 Jahre, Rötipark Solothurn.
- **Die Stiftung ist der wichtigste Kunde** ("vor allem der Stiftung gegenüber verpflichtet"): Pensionskassen-Verwaltung heisst Dokumentationspflichten (BVG Art. 27i-k, Modul 3) und einen tiefen Respekt vor sauberen Nachweisen. Schmid denkt in Belegen und Prüfpfaden.
- **Personen:** Rolf H. Schmid (GF, eidg. dipl. Wirtschaftsprüfer, MBA), Mirjam Böni (Verteiler "mibo", Mit-Ansprechpartnerin), Ivan Guldimann (Leiter Immobilienbewirtschaftung), Florian Kunz (Leiter Hauswartung = künftige App-Nutzer), Marc Mischler (Mandatsleiter Treuhand).
- **Was das strategisch heisst:** vRv ist kein reiner Bewirtschafter. Die Kombination aus Bewirtschaftung + eigenem Hauswart-Profitcenter + Stiftungs-/Treuhand-Administration gibt es als Standardsoftware nicht (Dossier B). Genau diese Querschnitts-Lücke ist unser Terrain.

## 4. Order2Cash: der Geldfluss, den wir digitalisieren

**Die 8 Stationen** (Ausschreibungs-Wortlaut in Klammern):

1. **Auftrag entsteht** (Aufgabe gemäss Vertrag ODER Annahme eines Auftrags): wiederkehrend aus dem Mandat (Heizungskontrolle jeden Monat) oder ad hoc (Mieter meldet tropfenden Hahn, Eigentümer bestellt Gartenpflege)
2. **Planen** (planen): Wer macht es wann? Disposition der Hauswarte, Material, Termine mit Mietern
3. **Umsetzen** (umsetzen): Hauswart vor Ort, heute mit Zetteln, Fotos auf dem Privathandy, WhatsApp
4. **Bestätigen** (bestätigen): Arbeit erledigt, allenfalls Unterschrift/Abnahme
5. **Dokumentieren** (dokumentieren): Rapport, Fotos, Checkliste; Nachweis gegenüber Eigentümer/Stiftung
6. **Leistung erfassen/messen** (Leistung erfassen/messen): Stunden, Material, Ansatz; die Brücke zur Verrechnung
7. **Verrechnen** (verrechnen): Rechnung an Eigentümer/Mieter/Auftraggeber ODER Weiterverrechnung im Mandat; QR-Rechnung raus
8. **Zahlungseingang** (bis zum vollständigen Zahlungseingang): Bank meldet Zahlung (camt), Abgleich, offene Posten, Mahnwesen

**Wo das Geld verloren geht (der Business Case, auswendig können):**

- **Zwischen 3 und 6:** Regiearbeit wird gemacht, aber nie erfasst → nie verrechnet. Jede Branchenkennerin bestätigt: unverrechnete Regieleistung ist der teuerste stille Verlust einer Verwaltung mit eigener Hauswartung. Frage b5 zielt exakt dahin.
- **Zwischen 6 und 7:** Zettel-Rapporte stapeln sich, Verrechnung passiert Wochen später oder pauschal "aus dem Gedächtnis".
- **In 8:** Mahnwesen manuell (wer hat welche Mahnstufe?), bekannter Pain aus unseren Walk-in-Gesprächen.

**Der Satz fürs Meeting:** "Order2Cash heisst für uns: Vom Moment, wo die Aufgabe entsteht, bis das Geld auf dem Konto ist, geht keine Leistung mehr verloren, und jeder Schritt ist belegt."

## 5. Die bekannten Schmerzpunkte der Branche (aus unseren Gesprächen)

Aus dem Walk-in-Script (validierte Hypothesen, am Termin als Gesprächsöffner nutzbar):

1. Ein-/Auszugsprotokolle: 30-45 min pro Wechsel, fast identischer Inhalt
2. Nebenkostenabrechnung: Zahlen aus mehreren Quellen manuell zusammentragen
3. Handwerker-Offerten einholen und vergleichen: Mail-Pingpong + Tabelle
4. Mieterkorrespondenz bei Wechsel: Kündigungsbestätigung, Termine, Übergabedokumente, alles einzeln
5. Mahnwesen: wer, welche Stufe, wann die nächste

Davon liegt im Order2Cash-Kern: 5 (Station 8), 3 teilweise (Station 1-2, externe Vergabe), 1 und 4 sind Nachbarprozesse (gut als Phase-2-Ideen, nicht überversprechen). 2 (NK) bewusst NICHT bauen: Standard-Software-Terrain (Dossier B).

## 6. pebeFinance: die 7 Sätze, die sitzen müssen

1. **Was es ist:** Treuhand-Buchhaltungssoftware der pebe AG (Frauenfeld, seit 1977, 11-20 Mitarbeitende), mandantenfähig; Module: Fibu, Debitoren/Kreditoren, Anlagen, Lohn (swissdec-zertifiziert), **Leistungserfassung**, **Fakturierung**, Wertschriften.
2. **Wie vRv es vermutlich nutzt:** als buchhalterisches Rückgrat über mehrere Mandanten (eigene Firma + Stiftungen + evtl. Kundenmandate). Welche Module lizenziert sind, ist Frage c1: die Architektur-Weiche Nr. 1.
3. **Betrieb:** lokal ODER als "pebeONLINE" gehostet (RDP/Citrix beim Provider VoiceLan). Frage c2; entscheidet, wie Dateien rein- und rauskommen.
4. **Integrationsflächen (belegt):** CSV/Excel-Buchungsimport (braucht die **optionale Lizenz "Schnittstellen"**!), Excel/CSV-Import in der Fakturierung (Umfang unklar), Bankstandards EBICS + camt.053/054 + QR-Rechnung + pain.001. **Kein öffentliches REST-API.** Das API der pebe-Werbung gehört zu "pebe Live", einem separaten Cloud-Produkt für Kleinfirmen, nicht zu vRvs pebeFINANCE.
5. **Der realistische Integrationsweg:** Unsere Plattform führt Auftrag bis Leistung; pebe bleibt führend für Fibu, Debitoren, Zahlungseingang. Übergabe als Importdatei (mit menschlichem Freigabe-Klick als bewusstem Kontrollpunkt), Zahlungsstatus über QR-Referenz raus / camt rein.
6. **pebe mobile existiert** (CHF 5/User/Monat, offline, Leistungen + Spesen + Belegfotos). Es kann NUR Zeit/Spesen erfassen: keine Disposition, keine Checklisten, keine Auftragssteuerung, keine Mieter-Kommunikation. **Wir sprechen es selbst an, bevor Schmid es tut:** "pebe mobile ist gute Zeiterfassung; die Ausschreibung verlangt aber Auftragssteuerung, Checklisten, Fotos und Kommunikation, also den Prozess davor und danach."
7. **Was pebe nicht hat:** kein Auftrags-/Werkauftragsmodul, kein Immobilien-Modul, keine mobile Auftragsabwicklung. Der Order2Cash-Vorbau MUSS ausserhalb von pebe entstehen; genau das schreibt die Ausschreibung.

**Merksatz:** "pebe bleibt. Wir bauen davor, nicht daneben." (= Kern-Differenzierung, siehe 7.)

## 7. Software-Landschaft: die 4 Namen, die fallen werden

| Name | Ein-Satz-Einordnung | Unsere Antwort |
|---|---|---|
| **ImmoTop2** (W&W) | Deutschschweizer Volumen-Standard für Bewirtschaftung mit eigener Fibu, Cloud ab CHF 149/Mt. | Stark in Mietbuchhaltung/NK; erzwingt aber Abschied von pebe und liefert generisches Ticketing statt vRv-Prozess |
| **Rimo R5** (W&W-Familie) | Solide Bewirtschaftungs-Suite, Schnittstellen zu Abacus/Sage etc. | pebe fehlt in der Schnittstellenliste; Mobile = Abnahmeprotokolle, kein Hauswart-Cockpit |
| **GARAIO REM** (Bern) | Modernste Grossbewirtschafter-Plattform (1.9 Mio. Objekte) | Zielgruppe institutionell; vRv-Grösse läuft über Partner-Ableger "REM light" |
| **AbaImmo + AbaSmart** (Abacus) | **Gefährlichster Pitch:** mobile Serviceaufträge mit PDF-Checklisten, Fotos, Zeit/Material, Unterschrift | Trifft die Hauswart-Anforderung fast ganz, ABER: kompletter Wechsel der Buchhaltungswelt (pebe raus, Abacus rein, Treuhand betroffen), ERP-Einführungsprojekt, laufende Lizenzen, Stiftungs-/BVG-Prozesse trotzdem draussen |

**Unsere Differenzierung in einem Satz:** "Jede Suite auf dem Markt zwingt Sie, pebeFinance zu ersetzen. Die Ausschreibung verlangt wörtlich das Gegenteil, und genau das bauen wir: die Integration Ihrer heutigen Lösung in die O365-Welt."

Ausserdem gut zu wissen: **Fairwalter** (Cloud-Newcomer, CHF 29-699/Mt., Preisanker), **PlanRadar/Blink** (Feld-Apps ohne Verrechnungstiefe), **Yarowa** (Plattform für EXTERNE Dienstleister-Vergabe, nicht fürs eigene Team), **ImmoApp** (Mieter-Kommunikations-App, ab CHF 140/Mt.).

## 8. Sprachführer fürs Meeting

Sagen: "Bewirtschaftung" (nicht "Property Management") · "Liegenschaft/Objekt" · "Rapport" (nicht "Report") · "Regie" · "Mandat" · "verrechnen" (nicht "billen") · "Hauswartung" (nicht "Facility Management", ausser Kunz sagt es selbst) · "Offene Posten" · "Mahnlauf". Vermeiden: Tech-Jargon (API, Payload, Deployment) ohne Übersetzung; stattdessen "Schnittstelle", "Übergabedatei", "automatischer Abgleich".

## 9. Die 10 sprechfähigen Sätze (jeder kann alle 10)

1. "Sie haben fünf Geschäftsfelder; die Ausschreibung betrifft den Weg vom Auftrag bis zum Zahlungseingang, quer durch Bewirtschaftung und Hauswartung."
2. "Der teuerste Verlust in diesem Prozess ist erfahrungsgemäss die Regieleistung, die erbracht, aber nie verrechnet wird."
3. "pebe bleibt Ihr buchhalterisches Rückgrat. Wir bauen davor, nicht daneben."
4. "pebeFINANCE hat belegte Import-Schnittstellen; entscheidend ist, welche Module Sie lizenziert haben und ob die Schnittstellen-Lizenz dabei ist."
5. "Der Zahlungseingang läuft elegant über Standards: QR-Referenz auf der Rechnung, camt-Meldung von der Bank, automatischer Abgleich in pebe."
6. "pebe mobile ist gute Zeiterfassung; Ihre Ausschreibung verlangt den ganzen Prozess: Disposition, Checklisten, Fotos, Kommunikation, Verrechnung."
7. "Nebenkostenabrechnung und Mietbuchhaltung bauen wir bewusst nicht nach; dafür gibt es erprobte Standardsoftware. Unser Wert liegt im Workflow darüber."
8. "Jede Standard-Suite am Markt würde Sie zwingen, pebe zu ersetzen. Wir nehmen Ihre Anforderung wörtlich."
9. "Für Herrn Kunz' Team bauen wir die App um die echten Handgriffe: Checkliste, Foto, Zeit, Material, fertig. Keine Schulungswoche nötig."
10. "Am Ende zählt für Sie als Prüfer: jeder Schritt belegt, jede Leistung nachvollziehbar, jederzeit auswertbar."

## 10. Vorbereitung auf die Session

Jeder liest vor S1: diesen Primer (20 min) + überfliegt Dossier A Kapitel 1+4 (pebe-Zusammenfassung + Unbekannte). Nico bereitet 3 eigene Beispiele aus den Walk-in-Gesprächen vor. Danach Quiz (ohne Spicken) + Drill: Nico spielt Guldimann und fragt "Warum soll ich nicht einfach AbaImmo kaufen?", jeder antwortet einmal.
