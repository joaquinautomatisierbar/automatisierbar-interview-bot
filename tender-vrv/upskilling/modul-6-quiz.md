# Modul 6 · Quiz + Drill

> 15 min in Session 5, ohne Primer offen. Lösungen zuunterst. Bestehensgrenze fürs Selbstvertrauen: 10 von 12.

## Quiz (12 Fragen)

1. Sage die Integrations-Hierarchie auf und ordne pebe je Stufe ein.
2. Warum ist das REST-API aus der pebe-Werbung für vRv irrelevant? (Präzis, das prüft Sattelfestigkeit.)
3. Erzähle den Weg einer Regieleistung von der Hauswart-App bis zum abgeglichenen Zahlungseingang in maximal 7 Stationen.
4. Welche pebe-Importfehler fängt unsere Vorvalidierung ab? Nenne vier Regelklassen.
5. Warum bleibt der Import-Klick anfangs ein Mensch, und unter welcher Bedingung automatisieren wir ihn?
6. Weg A vs. Weg B der Rechnungserzeugung: Unterschied, und wovon hängt die Wahl ab?
7. Was ist die Graph API, und wie beruhigst du einen IT-Partner, der nach den Berechtigungen fragt?
8. Wann eigener Integrationsdienst, wann Power Automate, wann n8n? Je ein Kriterium + Beispiel.
9. Die fünf Schritte unserer Datenmigration in der richtigen Reihenfolge.
10. Nenne vier technische Elemente der Archiv-Übergabe (Format, Speicher, Nachweis, Frist).
11. Warum ist RPA gegen die pebe-Oberfläche doppelt riskant im pebeONLINE-Betrieb?
12. Die vier wichtigsten offenen Fragen an die pebe AG (P-Nummern nicht nötig, Inhalt zählt).

## Drill (offene Transfer-Fragen, je 2 min)

D1. IT-Partner von vRv am Termin: "Und wie greifen Sie auf pebe zu? ODBC? API? Was genau?" Antworte technisch präzis, ohne zu schwurbeln.
D2. Schmid: "Was, wenn pebe den Import von Rechnungspositionen gar nicht unterstützt?" Zeige, dass Plan B kein Notnagel ist.
D3. Böni: "Woher wissen wir, dass bei der Übernahme unserer alten Daten nichts verloren geht?"
D4. Guldimann: "Können Sie nicht einfach ein Programm schreiben, das in pebe klickt wie ein Mensch?" Erkläre freundlich, warum wir genau das nicht tun.
D5. Kunz: "Der Hauswart hat den Auftrag im Keller abgeschlossen, aber das Handy hatte kein Netz. Wo ist die Erfassung jetzt?" Erzähle den Sync-Weg so, dass ein Nicht-Techniker ruhig wird.

---

## Lösungen

1. API vor Standard vor Datei vor Datenbank vor Roboter. pebe: (1) kein öffentliches API; (2) Zahlungsstandards belegt (QR, camt.053/054, EBICS, pain.001) = unser stabilster Kanal; (3) CSV/Excel-Buchungsimport (Lizenz "Schnittstellen") + evtl. Fakturaimport = belegter Dateiweg; (4) DB-Zugriff nur falls pebe ihn absegnet (Frage P5), nicht eingeplant; (5) RPA bewusst ausgeschlossen.
2. Das beworbene REST-API gehört zu pebe Live, einem eigenständigen Cloud-Produkt für Kleinfirmen mit eigener Datenhaltung. vRv nutzt pebeFINANCE, ein anderes Produkt ohne öffentlich dokumentiertes API. Die Existenz der Live-API zeigt nur, dass pebe API-Technik beherrscht; die Roadmap-Frage für pebeFINANCE stellen wir pebe direkt.
3. (1) Hauswart schliesst Auftrag in der App ab (Checkliste, Foto, Zeit, Material; offline gepuffert). (2) Sync in die Plattform. (3) Sachbearbeitung prüft Fakturavorschlag und gibt frei. (4) Plattform erzeugt geprüfte Übergabedatei (Weg A Positionen / Weg B Buchung + eigene QR-Rechnung). (5) Buchhaltung importiert in pebe (Vorschau, Übernehmen). (6) Rechnung mit QR-Referenz raus, Zahlung kommt als camt zurück, pebe gleicht ab. (7) Plattform liest Status (Export/camt) und zeigt bezahlt/offen/mahnen.
4. Nur ein Geschäftsjahr pro Datei · Konten existieren und sind aktiv · MWST-Codes vorhanden und gültig · Steuercode passt zum Konto (steuerpflichtiges Konto ohne Code bzw. Code auf nicht steuerbarem Konto wird abgefangen). Ziel: Import läuft beim ersten Versuch durch.
5. Er ist der Kontrollpunkt der Buchhaltung (Vier-Augen vor der Fibu) und der belegte, unterstützte Weg. Automatisierung erst, wenn pebe einen unbeaufsichtigten Modus (überwachter Ordner, CLI, Job) offiziell bestätigt (Frage P2); vorher wäre es Bastelei am Buchungsstoff.
6. Weg A: Wir liefern Fakturapositionen, pebe erzeugt die Rechnung (bevorzugt, weniger Doppelspur in der Rechnungsdarstellung). Weg B: Wir erzeugen die QR-Rechnung selbst (offener Standard) und liefern die Buchung als CSV. Wahl hängt an pebe-Antwort P3 (Umfang des Excel/CSV-Imports in der Fakturierung); bis dahin ist Weg B der sichere Planungsfall.
7. Microsofts einheitliches API über Mail, Kalender, Teams, SharePoint, Nutzer. Beruhigung: registrierte App im Tenant von vRv, granulare Berechtigungen aufs Minimum (z.B. nur eine SharePoint-Site, nur ein Postfach), jede einzelne vom Admin ausdrücklich freigegeben (Admin Consent), Application vs. Delegated sauber getrennt, jederzeit entziehbar.
8. Eigener Dienst: wenn Determinismus, Tests und Protokoll Pflicht sind (Buchungsdaten, pebe-Naht). Power Automate: M365-interne Abläufe in Variante A innerhalb der Seeded-Grenzen (Genehmigungsflow); Premium-Konnektor = Lizenzfalle. n8n/Skripte: interne Hilfsautomationen ohne Compliance-Gewicht (z.B. interner Report). Werkzeug folgt Auftrag, kein Bias.
9. Quellen-Analyse → Mapping-Tabelle (Quellfeld→Zielfeld, Regeln, Lücken) → Validierung jeder Zeile → Testlauf in Testumgebung mit echten Daten (idempotent) → Stichproben-Abnahme durch den Kunden, erst dann Produktivlauf mit Protokoll.
10. PDF/A als Langzeitformat · Speicher mit Versionierung + Object Lock/WORM (oder SharePoint mit Purview-Retention) · SHA-256-Hash je Dokument + zeitgestempelte Hash-Listen · Retention-Frist am Ereignis pro Dossier mit jährlichem Prüfjob · protokollierte Migration + Restore-Tests. (Vier davon.)
11. Erstens bricht UI-Automation bei jedem pebe-Update (Masken ändern sich). Zweitens läuft pebeONLINE als RDP/Citrix-Session beim Hoster VoiceLan: Fernsteuerung einer Remote-Session ist technisch fragil und lizenz-/supportrechtlich heikel; der Hoster kann es untersagen.
12. Formatspezifikation des Buchungsimports (Spalten, Pflichtfelder, Beispieldateien) · Automatisierbarkeit des Imports (Ordner/CLI/Job oder nur UI) · Umfang des Fakturapositions-/Leistungsimports · strukturierter Export von Zahlungseingängen/OP-Status als Rückkanal. (Dazu nachrangig: DB-Zugriff, ISO-Versionen, Kosten Lizenz "Schnittstellen", Dateitransport bei pebeONLINE.)

### Drill-Leitplanken (Elemente, die vorkommen müssen)

D1: Ehrlich vorneweg: kein öffentliches API bei pebeFINANCE → unser Zugriff ist dateibasiert (Buchungs-/evtl. Fakturaimport nach pebe-Spezifikation) plus Zahlungsstandards (QR/camt/EBICS) → kein ODBC-Direktzugriff ohne Herstellersegen, das fragen wir pebe offiziell → RPA schliessen wir aus. Wer so antwortet, klingt nach Erfahrung, nicht nach Ausweichen.
D2: Dann greift Weg B, der von Anfang an der Planungsfall ist: Wir erzeugen die QR-Rechnung selbst (offener Schweizer Standard) und liefern pebe die Buchung über den belegten CSV-Import → funktional identisches Ergebnis, Zahlungsabgleich läuft gleich → kein Projektrisiko, nur eine Weiche.
D3: Mapping-Tabelle macht jede Übernahme sichtbar → Validierung jeder Zeile, Ausschussliste mit Begründung statt stillem Verlust → Testlauf mit echten Daten in Testumgebung → Ihre Stichproben-Abnahme inkl. Grenzfällen vor dem Produktivlauf → Protokoll. Zahlenbeispiel nennen (wir haben Migrationen im vierstelligen Datensatzbereich protokolliert durchgeführt).
D4: Anerkennen (naheliegende Idee) → drei ehrliche Gründe: bricht bei jedem Update, im gehosteten pebe doppelt fragil, und für Buchungsdaten wollen wir Protokoll statt Klick-Imitation → der belegte Dateiweg tut dasselbe, nur robust und prüfbar → Bonus: pebe-Drittanbieter arbeiten produktiv genau so.
D5: Nichts ist weg: Die App speichert lokal auf dem Gerät und zeigt sichtbar an, was noch nicht übertragen ist → sobald Empfang da ist, überträgt sie automatisch, ohne Zutun → im Büro sieht man den Auftrag danach mit allen Fotos und Zeiten → und falls ein Gerät kaputtgeht, bevor es syncen konnte: nur die seit dem letzten Empfang erfassten Einträge wären betroffen, deshalb synct die App bei jeder Gelegenheit.
