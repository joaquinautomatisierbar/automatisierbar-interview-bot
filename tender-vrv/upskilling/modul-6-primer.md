# Modul 6 · Integrations-Architektur (pebe-Brücke, Graph API, Migration, Archiv)

> Session 5, Owner: **Tej** (unterrichtet die anderen drei). Lesezeit ~45 min.
> Grundlage: [research/dossier-a-pebe-integration.md](../research/dossier-a-pebe-integration.md) (belegte pebe-Flächen + Muster, Verweise [A §n]), Dossier C (M365-Seite), Dossier D §4 (Archiv), Dossier E (E7/E9/E13/E17). Vertieft, was das Architektur-Papier ([offer/architektur-varianten.md](../offer/architektur-varianten.md)) auf Angebotsebene beschreibt.
> Warum dieses Modul: "Integration der heutigen Lösung pebeFinance in die O365-Welt" ist DIE Primär-Anforderung der Ausschreibung. Wer die Naht erklären kann, gewinnt; wer sie nur behauptet, fliegt bei der ersten Techniker-Nachfrage auf.

## Lernziele

Nach der Session kann jeder von uns:

1. Die Integrations-Hierarchie aufsagen und begründen, warum wir bei pebe auf Datei + Zahlungsbus setzen und RPA aktiv vermeiden.
2. Den Weg einer Regieleistung von der Hauswart-App bis zum abgeglichenen Zahlungseingang Station für Station erzählen.
3. Graph API in zwei Sätzen erklären, inklusive des Berechtigungsmodells.
4. Den Datenmigrations-Ablauf als geübtes Handwerk beschreiben (nicht als Hoffnung).
5. Die Archiv-Anbindung technisch skizzieren (PDF/A, Object Lock, Hash, Fristen-Job).

---

## 1. Die Integrations-Hierarchie (unser Grundsatz)

Immer das **stabilste** Mittel wählen, das den Job erledigt, nie das eindrucksvollste [A §5]:

1. **Offizielles API** des Systems. Bei pebeFINANCE: existiert nicht öffentlich (das REST-API der Werbung gehört zu pebe Live, einem separaten KMU-Cloud-Produkt [A §3.7]).
2. **Standardisierte Datenformate / der Zahlungsbus:** QR-Rechnung raus, camt.053/054 von der Bank zurück, EBICS als Abholweg, pain.001 für Zahlungen. Normiert, von pebe belegt unterstützt [A §3.2]. Der stabilste Kanal überhaupt, weil ihn die Banken pflegen.
3. **Dateischnittstelle mit Spezifikation:** CSV/Excel-Buchungsimport in pebe (braucht die optionale Lizenz "Schnittstellen"), evtl. Fakturapositions-Import [A §3.1, §3.5]. Drittanbieter arbeiten produktiv genau so; das belegt die Tragfähigkeit [A §3.1].
4. **Lesender Datenbankzugriff:** nur mit ausdrücklichem Herstellersegen, Frage P5 an pebe. Nicht einplanen, nur erfragen.
5. **RPA / UI-Automation:** Software-Fernsteuerung der Oberfläche. Brüchig bei jedem Update, im gehosteten pebeONLINE (RDP/Citrix bei VoiceLan) zusätzlich heikel, lizenz- und supportkritisch. **Vermeiden wir aktiv und sagen das im Angebot als bewussten Ausschluss** [A §5].

Merksatz: **"API vor Standard vor Datei vor DB vor Roboter."** Bei pebe heisst das: Stufen 2 + 3 kombiniert.

## 2. Die pebe-Brücke, Station für Station (den Ablauf erzählen können)

Eine Regieleistung wandert so [A §6, E13]:

1. **Erfassung:** Hauswart schliesst in der App den Auftrag ab: Checkliste, Fotos, 1.5h Zeit, Material. Offline gepuffert, synct bei Empfang.
2. **Freigabe:** Sachbearbeitung sieht den Fakturavorschlag (Positionen, Ansätze), korrigiert, gibt frei. Prüfpfad: wer, wann, was.
3. **Übergabe an pebe, Weg A (bevorzugt, falls P3 positiv):** Fakturapositionen als Importdatei an pebeFAKTURA, pebe erzeugt die QR-Rechnung. Weg B: unsere Plattform erzeugt die QR-Rechnung selbst (Swiss QR-Bill ist ein offener Standard) und liefert die BUCHUNG als CSV in die Fibu.
4. **Vorvalidierung (unser Qualitätshebel):** Bevor die Datei rausgeht, prüfen wir sie gegen dieselben Regeln, an denen der pebe-Import scheitern würde: ein Geschäftsjahr pro Datei, existierende/aktive Konten, gültige MWST-Codes, Steuercode-Konto-Paarung [A §3.1]. Ziel: Der Import läuft beim ersten Versuch durch.
5. **Der Import-Klick:** Buchhaltung öffnet pebe, Einlesen, Vorschau (Fehlerspalte), Übernehmen. **Bewusst ein Mensch**: Kontrollpunkt, kein Mangel. Automatisierung erst, wenn pebe einen unbeaufsichtigten Weg bestätigt (Frage P2).
6. **Zahlung:** Rechnung trägt die QR-Referenz; Zahlungseingang kommt als camt.053/054 zurück und gleicht in pebe automatisch ab [A §3.2].
7. **Status zurück:** Wir lesen den Zahlungsstatus aus einem pebe-Export oder direkt aus den camt-Dateien der Bank und zeigen ihn in der Plattform ("bezahlt / offen / mahnen").

**Die vier offenen Klärpunkte mit pebe AG** (Mail nach Freigabe am 5.8., Katalog P1-P8 in [A §7]): Formatspezifikation (P1), Automatisierbarkeit des Imports (P2), Umfang Fakturaimport (P3), Statusrückkanal/OP-Export (P4). Bis zur Antwort planen wir Weg B als sicheren Fall.

## 3. Graph API: die eine Tür zur M365-Welt

**Was:** Microsofts einheitliches API über Mail, Kalender, Teams, SharePoint/OneDrive, Nutzer, Planner. Für uns die Brücke, mit der die Custom-Plattform in vRvs Microsoft-Welt hineinarbeitet, statt daneben zu stehen: Auftrags-Mails lesen, Rapporte/Rechnungskopien automatisch nach SharePoint ablegen (dort greift die Purview-Retention!), Kalendereinträge schreiben.

**Berechtigungsmodell (die Nachfrage eines IT-Partners):** Eine registrierte App im Entra-Tenant von vRv erhält **granulare Berechtigungen** (z.B. nur Ablage in eine bestimmte SharePoint-Site, nur ein definiertes Postfach lesen), vom Tenant-Admin ausdrücklich freigegeben (Admin Consent). Zwei Arten: Application Permissions (Dienst läuft selbständig) und Delegated (im Namen eines Nutzers). Wir beantragen das Minimum, vRv sieht und genehmigt jede Berechtigung. Passt exakt zu Least Privilege aus Modul 2.

## 4. Werkzeugwahl dazwischen: eigener Dienst vs. Power Automate vs. n8n

Kein Dogma, Auftrag entscheidet (Hausregel: kein Werkzeug-Bias):

- **Eigener Integrationsdienst** für die pebe-Naht: deterministisch, versioniert, offline testbar mit Beispieldateien, Protokoll je Übergabe. Buchungsdaten sind kein Ort für Klick-Flows.
- **Power Automate** für M365-interne Abläufe in Variante A (Genehmigungen, Ablage-Trigger), innerhalb der Seeded-Grenzen; Premium-Konnektoren machen den Flow lizenzpflichtig (Modul 1).
- **n8n / Skripte** für interne Hilfsautomationen ohne Compliance-Gewicht.

Ein Satz fürs Gespräch: "Für Buchungsdaten bauen wir einen kleinen, testbaren Dienst mit Protokoll, keinen Klick-Workflow. Das ist der Unterschied zwischen Integration und Bastelei."

## 5. Datenmigration als Handwerk (E9, Fragen-Bank Q45)

Der Ablauf, den wir zusagen (und mehrfach geübt haben, u.a. 2'079 Datensätze Lead-Archivierung):

1. **Quellen-Analyse:** Was existiert wo (pebe-Stammdaten, Excel-Listen, Alt-Software), Qualität, Duplikate.
2. **Mapping-Tabelle:** Quellfeld → Zielfeld, Transformationsregeln, Pflichtfeld-Lücken sichtbar gemacht. Kundenfeldnamen sind Ground Truth.
3. **Validierungsregeln:** dieselbe Disziplin wie bei der pebe-Datei; jede Zeile besteht oder wird mit Grund ausgewiesen.
4. **Testlauf in der Testumgebung** mit echten Daten, nie direkt in Produktion; idempotent (wiederholbar ohne Doppelungen).
5. **Stichproben-Abnahme durch vRv** (definierte Stichprobe + Grenzfälle), erst dann Produktivlauf mit Protokoll.

Transparent als eigene Offerten-Position (die Ausschreibung verlangt Migrationskosten explizit ausgewiesen).

## 6. Archiv-Anbindung technisch (E17, D §4 in Kurzform)

Die Plattform ist operativ; Langzeit-Dokumente wandern in ein revisionssicheres Archiv. Technisch heisst Übergabe:

1. Dokument als **PDF/A** rendern (Langzeitformat), Metadaten strukturiert daneben.
2. Ablage in Speicher mit **Versionierung + Object Lock (WORM)**: während der Frist weder änder- noch löschbar. Alternativ via Graph nach SharePoint, wo **Purview-Retention** die Sperre trägt.
3. **SHA-256-Hash pro Dokument** + zeitgestempelte Hash-Listen: Integrität und Speicherzeitpunkt nachweisbar (GeBüV-Kern).
4. **Frist am Ereignis:** Retention-Feld pro Dossier (Ende Leistungspflicht / 100. Altersjahr), jährlicher Prüfjob statt Pauschalfrist.
5. **Migrationskonzept:** protokollierte Format-/Trägerwechsel + Restore-Tests. "Jederzeit lesbar" ist eine Migrations-Zusage, keine Format-Magie (Modul 3).

## 7. Sicherer mobiler Zugriff, technisch begründet (E7-Reframe für Techniker-Gespräche)

Warum unsere Lösung kein VPN braucht: TLS transportverschlüsselt, Identität + MFA + Gerätezustand prüft Entra Conditional Access **pro Zugriff** statt einmal am Netzrand. Koexistenz mit AOVPN: läuft durch den Tunnel; bei Performance-Themen Split-Tunnel-Ausnahme mit dem IT-Partner abstimmen. Moderne Alternative für interne Alt-Systeme: Entra Private Access (Connector-VM im Netz, Zugriff pro App nach Richtlinie, USD 5/User/Monat), von Microsoft als VPN-Nachfolger positioniert; SSTP-Retirement 31.3.2026 als Marktsignal [E7].

---

## 8. Zehn sprechfähige Sätze (auswendig können)

1. "Unsere Regel heisst: API vor Standard vor Datei vor Datenbank vor Roboter. Bei pebe heisst das Zahlungsstandards plus Dateischnittstelle."
2. "pebeFINANCE hat kein öffentliches API; das beworbene REST-API gehört zu pebe Live, einem separaten Cloud-Produkt. Wer Ihnen eine API-Integration in pebeFINANCE verspricht, hat nicht recherchiert."
3. "Der Zahlungsverkehr ist unser stabilster Kanal: QR-Referenz raus, camt-Meldung zurück, und pebe gleicht automatisch ab. Diesen Standard pflegen die Banken, nicht wir."
4. "Wir prüfen jede Importdatei vorab gegen dieselben Regeln, an denen der pebe-Import scheitern würde: ein Geschäftsjahr, gültige Konten, passende Steuercodes. Der Import soll beim ersten Klick durchlaufen."
5. "Der Import-Klick bleibt bewusst bei Ihrer Buchhaltung: Das ist Ihr Kontrollpunkt. Automatisiert wird er erst, wenn pebe einen unbeaufsichtigten Weg offiziell bestätigt."
6. "Software-Fernsteuerung der pebe-Oberfläche schliessen wir bewusst aus: Sie bricht bei jedem Update, und im gehosteten Betrieb ist sie doppelt heikel."
7. "In Ihre Microsoft-Welt arbeiten wir über Graph, mit granularen Berechtigungen, die Ihr Administrator einzeln sieht und freigibt, nur das Minimum."
8. "Rapporte und Rechnungskopien legt die Plattform automatisch in SharePoint ab; damit greift Ihre Aufbewahrungsrichtlinie, ohne dass jemand daran denken muss."
9. "Migration heisst bei uns Mapping-Tabelle, Validierung jeder Zeile, Testlauf mit Ihren echten Daten und Ihre Stichproben-Abnahme, bevor irgendetwas produktiv wird."
10. "Für Buchungsdaten bauen wir einen kleinen, testbaren Dienst mit Übergabeprotokoll, keinen Klick-Workflow."

## 9. Verbindung zu den anderen Modulen

- **Modul 1:** Graph/Power-Automate-Lizenzgrenzen; SharePoint/Purview-Seite des Archivs.
- **Modul 2:** Least Privilege = dasselbe Prinzip wie App-Berechtigungen; E7-Reframe gemeinsam.
- **Modul 3:** GeBüV-Anforderungen, die Abschnitt 6 technisch umsetzt.
- **Modul 4:** die Order2Cash-Stationen, an denen die Brücke hängt.
- **Offerte:** Kapitel 7.2 (pebe-Integration) + 13.3 (Migrationskosten); Architektur-Papier §0-§3.
