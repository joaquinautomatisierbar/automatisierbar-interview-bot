# Offerten-Skelett: vR verwaltungen ag

> Task WS5.1. Zweck: Nach dem Termin am 5.8. wird die Offerte GEFÜLLT, nicht mehr strukturiert. Der Offerten-Sprint dauert dann Tage statt Wochen (Ziel: Rohfassung 8.8.).
>
> **Quellen-Legende** (steht bei jedem Kapitel):
> `[TOOL]` = kommt aus dem Brief-Export des Discovery-Tools (cockpit.automatisierbar.ch/vrv/fragebogen, Kapitel-Verweis wie "TOOL b" = Fragenkapitel B) · `[D-A..E]` = Dossier A-E in research/ · `[S3]` = Scope-Entscheid vom 21.7. (Dossier E Matrix) · `[6.x / 3.x / 5.x]` = offener Task aus TASKS.md · `[NEU]` = wird nach dem 5.8. frisch geschrieben.
>
> **Stilregeln für die fertige Offerte:** Sie-Form, keine Gedankenstriche, jede Zahl mit Herkunft, Piloten als Piloten gelabelt, keine Superlative ohne Beleg. Ehrlichkeit ist Positionierung (Evaluationskriterium "Transparenz").

---

## Abdeckungs-Matrix (Pflicht-Check vor Abgabe)

Jede Zeile aus "Gewünschte Informationen" der Ausschreibung muss ein Kapitel haben. Vor Abgabe abhaken:

| Gefordert (wörtlich aus der Ausschreibung) | Kapitel | Status |
|---|---|---|
| Firma, Team, Ansprechpartner | 3 | [ ] |
| Rechenzentrum: Ort, Umfang und Art | 8.1 | [ ] |
| Datensicherheit: Organisation, Notfallkonzept, Firewalls, Berechtigungsstruktur | 8.2 | [ ] |
| Sicherheitsstandards: EndpointSecurity, Firewall, VPN; BVG allenfalls FINMA | 8.3 | [ ] |
| Mobile Anbindung: AlwaysOnVPN | 8.4 | [ ] |
| Versicherungsdeckungen und Referenzen | 9 | [ ] |
| Offertstruktur: Bereitstellung Netzwerk (Initial-/laufende Kosten, Managed Services) | 10.1 | [ ] |
| Offertstruktur: Bereitstellung Hardware-Infrastruktur | 10.2 | [ ] |
| Offertstruktur: Bereitstellung Betriebssoftware (OS, Sicherheits-SW, Managed Services) | 10.3 | [ ] |
| Offertstruktur: SLAs (Reaktionszeiten, Lösungszeiten, Verfügbarkeiten) | 10.4 | [ ] |
| Festpreis vs. Dienstleistungsangebot vs. Agil | 11.3 | [ ] |
| Verantwortlichkeiten, Leistungsabgrenzungen | 11.4 | [ ] |
| Stärken und Schwächen (Flexibilität, Transparenz, Integration, Kosten-Nutzen) | 12 | [ ] |
| Kosten: Lizenzmodell/SaaS, Unternehmenslizenz, Custom/Enterprise | 13 | [ ] |
| Zusatzkosten: Setup/Customizing, Datenmigration, Schulung | 13.3 | [ ] |
| Variante Microsoft ernsthaft gewürdigt | 5 (Variante A) | [ ] |
| Aufbewahrung BVG (Beilage Art. 27i-k BVV 2) | 8.5 | [ ] |
| Datenschutz sowie KI- und Sicherheitsstrategie | 8.6 + 8.7 | [ ] |
| Zentralisierte Plattform, Workflow-Automatisierung, Hauswart-App, Abrechnung/Reporting, ERP-Schnittstellen | 4 bis 7 | [ ] |
| Rolle: Architektur und Projektleitung, Mitarbeit vRv | 11 | [ ] |

---

## 0. Begleitbrief (1 Seite) `[NEU]`

Dank für Termin + Einblick · unser Verständnis in 3 Sätzen · was die Offerte enthält (3 Varianten, ein Vorgehen) · Gültigkeitsdauer · vorgeschlagener Präsentationstermin (am 5.8. fixiert, hier bestätigen).

## 1. Management Summary (max. 2 Seiten) `[NEU, zuletzt schreiben]`

- Ausgangslage in 4 Sätzen `[TOOL a+b]`
- Unsere Empfehlung (Variante + Begründung in 3 Punkten) `[S3 + TOOL]`
- Investitions- und Betriebskosten-Rahmen der empfohlenen Variante (eine Tabelle) `[Kap. 13]`
- Vorgehen in einem Satz (bezahlte Phasen mit Ausstiegspunkten) + nächster Schritt mit Datum

## 2. Ausgangslage + unser Verständnis `[TOOL a, b, f]`

- 2.1 vR verwaltungen ag: Geschäftsfelder, Mengengerüst (Mitarbeitende, Hauswarte, Aufträge/Monat, Rechnungen/Monat) `[TOOL a]` **Platzhalter: Zahlen NUR aus dem Tool-Brief, jede mit "(Frage xx)"-Herkunft**
- 2.2 Order2Cash heute: Ist-Ablauf über die 8 Stationen, erfasste Bruchstellen `[TOOL b]`
- 2.3 Was die Ausschreibung verlangt (Kurzfassung in unseren Worten, gegen Missverständnisse) `[Transkript]`
- 2.4 Wo heute Wert verloren geht (unverrechnete Regie, Medienbrüche; nur belegte Aussagen aus dem Termin, keine erfundenen Zahlen) `[TOOL b6/f]`

## 3. Firma, Team, Ansprechpartner `[3.5 Über-uns-Material + 6.2 Rechtsform-Story]`

- 3.1 Wer wir sind (4 Gründer, Arbeitsweise, warum es uns gibt) `[3.5]`
- 3.2 Rechtsform + Verbindlichkeit **[Platzhalter: Formulierung aus 6.2, Owner Joaquin]**
- 3.3 Ihr Ansprechpartner + Stellvertretung (namentlich, mit Foto)
- 3.4 Eingesetzte Partner, falls `[S3]` Teillose ergibt (Modell "wir orchestrieren, Partner betreibt Vor-Ort-Schicht", Dossier E) **[Platzhalter: Partner erst nach 5.8. ansprechen, Doppelrollen-Risiko]**

## 4. Lösungskonzept im Überblick `[NEU, gestützt auf D-A/B/C + TOOL]`

- 4.1 Leitplanken: pebeFinance bleibt führendes System (wörtliche Anforderung); M365-Welt wird genutzt, nicht ersetzt; Hauswart-App für den Feldalltag; jede Leistung prüfbar (Prüfpfad-Argument)
- 4.2 Was wir bewusst NICHT bauen (NK-Abrechnung, Mietbuchhaltung, Abnahmeprotokolle: dort gewinnt Standardsoftware) `[D-B §5]`
- 4.3 Datenfluss-Diagramm: Auftrag → Planung → mobile Ausführung → Leistung → Faktura → pebe → Zahlungseingang → Reporting

## 5. Variante A: Microsoft-Ausbau `[D-C, fertig vorstrukturiert]`

- 5.1 Würdigung der Kundenidee (Sockel: Planner, Approvals, SharePoint, Purview) `[D-C §2]`
- 5.2 Vervollständigung: Power Apps + Dataverse + Power BI, mit Begründung je Baustein `[D-C §4]`
- 5.3 Grenzen transparent (Feld/Offline/GPS, Leistungserfassung, pebe-Naht, Governance) `[D-C §3+§6]`
- 5.4 Lizenzkosten-Tabelle (tagesaktuelle Microsoft-Preisliste CH ziehen! Preiserhöhung 1.7.2026) `[D-C §5]`
- 5.5 Unsere Rolle: Architektur, Bau, Governance, Betrieb ("Baukasten mit Bauleitung")

## 6. Variante B: Massgeschneiderte Plattform `[NEU + D-A/B; Hub/PWA-Substanz]`

- 6.1 Aufbau: Auftrags-Hub (Board, Disposition, Status) + Hauswart-PWA (offline, Foto, Checklisten, GPS-Einsatznachweis) + Graph-Anbindung an Outlook/Teams/SharePoint + pebe-Integrationsdienst
- 6.2 Warum exakte Passform hier gewinnt (vRv-Prozess über alle drei Geschäftsfelder; keine Suite bildet das ab) `[D-B §5]`
- 6.3 Betrieb: CH-Hosting, Wartung, Weiterentwicklung `[6.3 Hosting-Entscheid]`
- 6.4 Grenzen transparent (Bauleistung höher; Archiv-Tiefe via M365 oder WORM-Speicher)

## 7. Variante C: Hybrid (Empfehlungskandidat) `[NEU]`

- 7.1 Schnitt: Kollaboration + Dokumente + Archiv in M365; Prozesskern + Feld + pebe-Naht custom
- 7.2 pebeFinance-Integration im Detail (gilt für alle Varianten): belegte Flächen CSV-Buchungsimport (Lizenz "Schnittstellen"), Fakturapositions-Weg (Klärung pebe P1-P8), QR + camt.053/054 als Zahlungsbus, kontrollierter Import-Klick als Freigabeschritt `[D-A §3+§6]` **[Platzhalter: Antworten von pebe AG einfügen, Kontakt nach Freigabe am 5.8.]**
- 7.3 Mobile Lösung Hauswartung (Checklisten mit Pflichtfeldern, Foto, offline, GPS-Zweck aus e4) `[TOOL e]`
- 7.4 Verrechnung + Reporting (Zeit/Material → Fakturavorschlag → pebe; Auswertungen) `[TOOL f]`
- 7.5 Empfehlung + Begründung über 3-Jahres-TCO `[Kap. 13]`

## 8. Sicherheit, Datenschutz, Compliance `[D-D, Bausteine fertig formuliert]`

> Dossier D §7 enthält für 8.1 bis 8.7 fertige, ehrliche Textbausteine. Hier nur einsetzen + auf Scope-Entscheide anpassen.

- 8.1 Rechenzentrum: Ort, Umfang, Art `[D-D §7 Baustein 1]` **[Platzhalter: 6.3-Entscheid Exoscale/Infomaniak]**
- 8.2 Datensicherheit: Organisation, Notfallkonzept (RPO/RTO, 3-2-1, getestete Restores), Firewalls, Berechtigungsstruktur (RBAC, Entra SSO) `[D-D §7]`
- 8.3 Sicherheitsstandards: EndpointSecurity, Firewall, VPN; BVG-/FINMA-Einordnung (BVSA + OAK BV, FINMA nur Lebensversicherer; freiwillige Orientierung an RS 2023/1) `[D-D §5+§7]` **[Platzhalter: E4-Entscheid ändert den Endpoint-Absatz: Konzept vs. betriebenes Angebot]**
- 8.4 Mobile Anbindung / AlwaysOnVPN (TLS + Entra SSO + MFA; AOVPN-kompatibel; Zero-Trust-Einordnung) `[D-D §2.3+§7]`
- 8.5 BVG-Aufbewahrung Art. 27i-k BVV 2: operatives System vs. dediziertes Archiv; Umsetzungswege SharePoint+Purview oder WORM-Objektspeicher (PDF/A, Hash, Zeitstempel, protokollierte Migration nach GeBüV) `[D-D §4]` **[Platzhalter: Ablageort-Präferenz aus TOOL g7]**
- 8.6 Datenschutz nDSG: Auftragsbearbeiter Art. 9, AVV mit TOMs, Unterauftragsbearbeiter-Liste, DSFA vor Produktivsetzung, 24h-Meldefrist `[D-D §3 + 6.5 AVV-Template]`
- 8.7 KI- und Sicherheitsstrategie (4 Regeln: Datenklassifizierung, kontrollierte Anbieter/Orte, Human-in-the-loop, Protokollierung) `[D-D §8, Baustein fertig]`

## 9. Versicherungsdeckungen und Referenzen

- 9.1 Versicherungen: Berufshaftpflicht + Cyber, Deckungssummen, Versicherer **[Platzhalter: aus 6.1, Offerten bis 1.8.; falls E4=selbst: "Managed Endpoint/Workplace Services" muss explizit eingeschlossen sein, Dossier E]**
- 9.2 Referenzen: 1 Seite je Projekt, ehrlich gelabelt (produktiv / geliefert / Pilot) `[3.3 Referenzblätter + 6.4 Freigaben]`
- 9.3 Eigene Systeme als lebende Referenz (Hub, Feld-PWA, Beleg-OCR; am Termin gezeigt)

## 10. Offertstruktur Dienstleistungen (Antwort auf den Kriterienkatalog) `[S3 entscheidet die Form!]`

> Empfohlene Form laut Dossier E: **Teillose mit getrennten Verträgen**, wir als Gesamtkoordinator (exakt die ausgeschriebene Rolle). Kein Durchlaufumsatz, klare Haftung, volle Transparenz.

- 10.1 Netzwerk (Initial-/laufende Kosten, Managed Services): **[Platzhalter S3: erwartete Empfehlung "Partner nach unserem Pflichtenheft"; Los ausweisen, Partner nach 5.8. anfragen]** `[D-E E2]`
- 10.2 Hardware: Koordination + Deployment durch uns in Stunden, Einkauf direkt/Partner ohne Aufschlag `[D-E E3]`
- 10.3 Betriebssoftware (OS, Sicherheits-SW, Managed Services): **[Platzhalter S3/E4: "selbst mit Support-Fenster + Partner-Backstop" ODER "Partner"; Business-Premium-Sockel in beiden Fällen]** `[D-E E4/E5]`
- 10.4 SLAs: Stufen Bronze/Silber/Gold mit Reaktions-/Lösungszeiten + Verfügbarkeiten, Monitoring 24/7 automatisiert, Pikett ehrlich abgegrenzt `[5.5 SLA-Baukasten]`

## 11. Vorgehen, Projektorganisation, Zusammenarbeit

- 11.1 Phasenmodell: Phase 1 Detailkonzept (Festpreis, eigenständiger Wert, gehört vRv) → Phase 2 Pilot (echter Teilprozess, Messkriterien, Festpreis/Kostendach) → Phase 3 Rollout + Betrieb (Plattform-Miete + SLA). Ausstiegspunkt nach jeder Phase. **Kein Gratis-Anteil, nirgends.**
- 11.2 Terminplan ab Beauftragung **[Platzhalter: Termine erst nach 5.8. mit Mengengerüst]**
- 11.3 Antwort "Festpreis vs. Dienstleistung vs. Agil": Festpreis im Rahmen (pro Phase), agil im Inhalt (wöchentlich sichtbare Ergebnisse) `[5.3]`
- 11.4 Verantwortlichkeiten + Leistungsabgrenzung: RACI-Tabelle (wir / vRv / IT-Partner vRv / pebe AG / allfällige Teillos-Partner) `[NEU; Muster aus Modul 5]`
- 11.5 Mitarbeit vRv konkret (Ansprechpartner je Bereich, Stunden/Woche, Pilot-Hauswarte, pebe-Freigabe) `[TOOL h]`

## 12. Stärken und Schwächen (ehrliche Selbsteinschätzung)

> Die Ausschreibung bewertet Anbieter nach Flexibilität, Transparenz, Integration, Kosten-Nutzen. Wir beantworten das proaktiv UND ehrlich, inkl. echter Schwächen (junges Unternehmen, kleine Struktur, Referenzen im Aufbau) mit jeweils der konkreten Gegenmassnahme. Keine Scheinschwächen ("wir sind zu perfektionistisch").

- 12.1 Flexibilität · 12.2 Transparenz · 12.3 Integration · 12.4 Kosten-Nutzen · 12.5 Ehrliche Schwächen + Gegenmassnahmen

## 13. Kosten `[5.3 Preismodell; zuletzt füllen]`

- 13.1 Investition je Variante (A/B/C) nach Phasen, Festpreise/Kostendächer
- 13.2 Laufende Kosten je Variante: Lizenzmodell (A: M365-Zusatzlizenzen, tagesaktuell), SaaS/Betrieb (B/C: Hosting + Wartung + SLA-Stufe), auf 3 Jahre gerechnet (TCO-Tabelle nebeneinander)
- 13.3 Zusatzkosten separat: Setup/Customizing, Datenmigration, Schulung, pebe-Lizenz "Schnittstellen" (falls nicht vorhanden, `[TOOL c1/c3]`), allfällige Purview-/Archiv-Kosten
- 13.4 Annahmen + was den Preis bewegt (Hauswart-Anzahl, Offline-Pflicht, Portal ja/nein, Archiv-Weg)

## 14. Offene Punkte + Annahmen `[TOOL Brief §8, deterministisch]`

- Der Brief-Export listet alle am 5.8. offen gebliebenen Muss-Fragen automatisch. Hier übernehmen + je Punkt: Annahme, die wir getroffen haben, und bis wann sie zu bestätigen ist. Nichts weghalluzinieren.

## 15. Anhang

- A: Referenzblätter `[3.3]` · B: AVV-Muster + TOMs `[6.5]` · C: SLA-Detailtabellen `[5.5]` · D: Lizenzpreis-Quellen (Microsoft-Preisliste CH, Datum) · E: Architektur-Diagramme `[5.2]` · F: Fragenkatalog an pebe AG (P1-P8, als Beleg der Gründlichkeit) `[D-A §7]`

---

## Arbeitsablauf nach dem 5.8. (so wird das Skelett zur Offerte)

1. **6.8.:** Tool-Synthese laufen lassen (Brief-Export), in Kap. 2, 7.3, 7.4, 11.5, 14 einfüllen; offene Muss-Fragen als Nachfass-Mail an Böni/Schmid formulieren.
2. **6.8.:** pebe AG kontaktieren (P1-P8, Freigabe vorausgesetzt); Antwortfristen setzen.
3. **7.8.:** Scope-Formulierungen (Kap. 10) an die am Termin gehörte Realität anpassen (wer ist der heutige IT-Partner? was soll wirklich konsolidiert werden?).
4. **7.-8.8.:** Kosten (Kap. 13) kalkulieren, Management Summary (Kap. 1) zuletzt schreiben, Abdeckungs-Matrix abhaken.
5. **Review:** Nico + Joaquin lesen gegen die Ehrlichkeitsregeln; Zero-Context-Test (versteht es jemand ohne Vorwissen?); dann Abgabe gemäss am Termin zugesagtem Datum.
