# Referenzblätter (Entwürfe für Kunden-Freigabe)

> Task WS3.3. Vier Ein-Seiter, werden nach Freigabe Anhang A der Offerte und Teil des Print-Sets (3.6).
> **Ablauf:** Owner holt Freigabe mit dem Anfrage-Text aus [templates/referenz-freigabe.md](../templates/referenz-freigabe.md), und zwar mit dem EXAKTEN Blatt-Text unten. Tej = Juglans · Nico = Bieri · Joaquin = KnowGravity + Gränacher. Ziel: Freigaben bis 28.7.
> **Ehrlichkeitsregeln:** Status-Chip stimmt mit der Realität überein (produktiv / geliefert / Pilot). Schätzungen sind als Schätzungen gelabelt. Kein "seit Jahren", kein "zahlreiche Kunden". Zitat + Ansprechperson erst nach ausdrücklicher Freigabe.
> **[Stand prüfen]** vor Drucklegung 3.8.: Status-Chips gegen Realität aktualisieren (z.B. falls Bieri bis dahin eingeführt ist).

---

## Blatt 1 · Juglans Landschaftsarchitektur GmbH

**Branche:** Landschaftsarchitektur / Gartenbau · **Projekt:** Offerten-Generator · **Status-Chip: IM EINSATZ (Pilotbetrieb seit Juli 2026)**

**Ausgangslage.** Offerten entstanden aus Erfahrungswissen und Altdokumenten: zeitaufwendig, positionsweise von Hand zusammengesucht, mit dem Risiko vergessener Positionen.

**Lösung.**
- Offerten-Generator, der aus Projektangaben in Minuten eine fertige, bepreiste Offerte erstellt
- Positionskatalog aus 20 historischen Offerten des Betriebs aufgebaut; Live-Suche über alle Positionen
- KI schlägt passende Positionen und Mengen vor; eine deterministische Prüfschicht stellt sicher, dass **nur echte Katalogpositionen mit echten Preisen** in der Offerte landen (keine erfundenen Werte)
- Entwürfe speicherbar, Export als fertiges Offert-Dokument

**Status, ehrlich:** Ausgeliefert und beim Kunden im Einsatz, Pilotbetrieb mit laufender Nutzungsmessung seit Anfang Juli 2026. Eine Offline-Version für den Betriebsstandort ohne Internetabdeckung ist in Arbeit.

**Was das für vR verwaltungen ag heisst:**
- Genau die Verrechnungs-Disziplin, die Order2Cash braucht: aus Strukturdaten werden Dokumente, ohne Abtippen
- Die Prüfschicht-Idee ("KI schlägt vor, Deterministik validiert, Mensch gibt frei") ist dasselbe Muster, mit dem wir Buchungsdaten für pebeFinance absichern würden

**Technik in einem Satz:** Web-Applikation auf Schweizer Server, passwortgeschützt, KI-Vorschläge mit deterministischer Absicherung.

> Zitat: [nach Freigabe] · Ansprechperson: [nach Freigabe, nur mit Voranmeldung]

**Freigabe:** [ ] Text ok · [ ] Logo ok · [ ] Ansprechperson ok · Owner: Tej

---

## Blatt 2 · KnowGravity Inc., Zürich

**Branche:** IT- und Unternehmensberatung (6 Mitarbeitende) · **Projekt:** Spesen-App · **Status-Chip: GELIEFERT (online, Feinschliff mit dem Kunden läuft)**

**Ausgangslage.** Spesenbelege wurden gesammelt, abgetippt und am Monatsende von Hand für den Treuhänder aufbereitet; Kleinbeträge und Fremdwährungen machten es mühsam.

**Lösung.**
- Mobile Web-App (auf dem Handy installierbar): Beleg fotografieren, automatische Texterkennung füllt Betrag, Datum und Händler vor, Mitarbeiter bestätigt
- Fremdwährungen mit automatischem Tageskurs; Pauschalen nach firmeneigenem Regelwerk
- **Monatsabschluss auf Knopfdruck:** PDF-Bericht + Excel + Beleg-Paket, dazu ein fertiger E-Mail-Entwurf an den Treuhänder; mit Kontroll-Bestätigung des Mitarbeiters
- Gesundheits-Überwachung und tägliche Backups eingebaut

**Status, ehrlich:** Erste Version geliefert und online in Nutzung; Feinschliff läuft, sobald der Kunde sein internes Spesen-Regelwerk finalisiert hat.

**Was das für vR verwaltungen ag heisst:**
- Mobile Belegerfassung mit Foto und Texterkennung ist genau das Muster für Material- und Spesenerfassung Ihrer Hauswarte
- Der Monatsabschluss zeigt die saubere Übergabe an die Buchhaltung: strukturiert, geprüft, mit Beleg, statt Zettelwirtschaft

**Technik in einem Satz:** Installierbare Web-App (PWA) auf Schweizer Server, Texterkennung per KI, Berichte als PDF/Excel.

> Zitat: [nach Freigabe] · Ansprechperson: [nach Freigabe, nur mit Voranmeldung]

**Freigabe:** [ ] Text ok · [ ] Logo ok · [ ] Ansprechperson ok · Owner: Joaquin

---

## Blatt 3 · Bieri Rechtsanwälte, Zürich

**Branche:** Anwaltskanzlei · **Projekt:** Dokumenten-Workflow Fallabschluss · **Status-Chip: FERTIG ENTWICKELT (vor Einführung)**

**Ausgangslage.** Beim Abschluss eines Falls entstehen mehrere Dokumente in fester Abfolge, mit Korrespondenz über Outlook; jeder Schritt war Handarbeit und musste in der richtigen Reihenfolge erinnert werden.

**Lösung.**
- Achtstufiger Dokumenten-Workflow für Fallabschlüsse, automatisiert von der Vorlage bis zum Versandentwurf
- **Integration in die bestehende Outlook-Umgebung** der Kanzlei: die Anwälte arbeiten weiter in ihren gewohnten Werkzeugen
- Jeder Schritt nachvollziehbar, nichts geht vergessen, die Reihenfolge ist garantiert

**Status, ehrlich:** Fertig entwickelt, steht vor der Einführung in der Kanzlei.

**Was das für vR verwaltungen ag heisst:**
- Beweis für die geforderte O365-Integration: Wir bauen in die Microsoft-Welt hinein, nicht daneben
- Eine Kanzlei stellt an Vertraulichkeit und Sorgfalt ähnliche Ansprüche wie eine Vorsorge- und Treuhand-Umgebung

**Technik in einem Satz:** Workflow-Automatisierung mit Outlook-/Microsoft-365-Integration.

> Zitat: [nach Freigabe] · Ansprechperson: [nach Freigabe, nur mit Voranmeldung]

**Freigabe:** [ ] Text ok · [ ] Logo ok · [ ] Ansprechperson ok · Owner: Nico

---

## Blatt 4 · Exclusive Homes Gränacher GmbH

**Branche:** Immobilienvermittlung · **Projekt:** Automatischer Dossier-Versand · **Status-Chip: PILOT (im Aufbau)**

**Ausgangslage.** Interessenten-Anfragen zu Objekten wurden einzeln beantwortet; das Zusammenstellen und Versenden der Verkaufsdossiers band jede Woche viele Stunden.

**Lösung.**
- Pilot, der eingehende Anfragen erkennt und das passende Verkaufsdossier automatisch versendet
- Die vorgelagerte Prozess-Diagnose ergab ein Einsparpotenzial von **rund 15 Stunden pro Woche (Schätzung aus der Diagnose, der Pilot läuft zur Validierung)**

**Status, ehrlich:** Pilot im Aufbau; die Einsparungszahl ist eine begründete Schätzung, noch kein Messwert.

**Was das für vR verwaltungen ag heisst:**
- Branchennähe: Immobilien-Abläufe, Objektdaten, Interessenten- und Eigentümerkommunikation sind uns vertraut
- Zeigt unser Vorgehen: erst Diagnose mit bezifferter Hypothese, dann Pilot, der die Zahl beweisen muss, erst dann Ausbau

**Technik in einem Satz:** E-Mail-/Dokumenten-Automatisierung mit definierten Freigabepunkten.

> Zitat: [nach Freigabe] · Ansprechperson: [nach Freigabe, nur mit Voranmeldung]

**Freigabe:** [ ] Text ok · [ ] Logo ok · [ ] Ansprechperson ok · Owner: Joaquin

---

## Nicht als Referenz verwenden (aus templates/referenz-freigabe.md)

- Beris Metzgerei nur mündlich als "zahlender Kunde", falls direkt gefragt (anderer Sektor, keine Messwerte)
- Praxis Ulrich gar nicht (medizinischer Kontext, datenschutz-sensibel)
- Eigene interne Systeme (Hub, Feld-PWA, Beleg-Erfassung) sind KEINE Kundenreferenzen; sie laufen als Live-Demo unter "wir benutzen, was wir bauen"
