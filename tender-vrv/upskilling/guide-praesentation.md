# Präsentations-Guide: So baust du dein Session-Deck mit Claude Code

> Für Nico (Modul 4), Tej (Modul 1 + 6) und Patrik (Modul 3). Dieser Guide ist so geschrieben, dass du ihn **direkt deinem Claude Code geben kannst**. Zusammen mit deinem Primer hat Claude dann alles, um in einem Rutsch ein gutes Deck zu bauen, im gleichen Stil wie die Module 2 und 5.

## So gehst du vor (5 Schritte)

1. **Lade das Referenz-Deck herunter:** Hub → Lernen → Modul 5 → Präsentation öffnen, dann im Browser speichern (Cmd+S / Ctrl+S, als "Webseite, nur HTML"). Das ist das Skelett: Folien-Engine, Look, Klick-Builds, Notizen-Panel sind alle schon drin.
2. **Sammle deinen Stoff:** dein Primer aus dem Hub (Lernen → dein Modul → Primer) plus alles, was du selbst erklären willst.
3. **Gib Claude Code drei Dinge:** diesen Guide, das heruntergeladene `modul-5-deck.html` als Referenz-Skelett, und deinen Primer. Dann den Prompt unten.
4. **Prüfe das Ergebnis** gegen die Checkliste am Ende dieses Guides. Lass Claude nachbessern, bis alles erfüllt ist.
5. **Lade hoch:** Hub → Lernen → dein Modul → **Material** → Präsentation (HTML-Deck). Fertig, der Button erscheint automatisch auf deiner Modul-Karte.

## Prompt-Vorlage (kopieren, anpassen, an Claude Code schicken)

```
Baue mir ein Lehr-Deck für eine 60-Minuten-Team-Session zum Thema [DEIN THEMA].
Publikum: meine 3 Mitgründer, KEIN Vorwissen zum Thema.
Angehängt: (1) guide-praesentation.md mit der Methode, folge ihr strikt.
(2) modul-5-deck.html als Referenz-Skelett: übernimm Folien-Engine, CSS-Look,
Klick-Build-Mechanik und Notizen-Panel exakt, ersetze nur die Inhalte.
(3) mein Primer mit dem Fachstoff.
Zeig mir zuerst den Folien-Outline zur Freigabe, baue erst danach.
```

## Die Methode, Teil 1: Didaktik (wie ein gutes Erklärvideo)

1. **Null Vorwissen annehmen.** Kein Begriff wird benutzt, bevor er auf einer eigenen Folie eingeführt wurde. Auch Basics prüfen (Server, Cloud, API). Insider (Personen wie Schmid, Dokumente, Projekte) werden vorgestellt wie in einer Doku.
2. **Ein Gedanke pro Folie.** Maximal 3 Textzeilen plus 1 Visual. Lieber 50 bis 70 leichte Folien als 20 dichte. Die Folienzahl ist egal, die Klarheit nicht.
3. **Gross starten, dann eingrenzen.** Reihenfolge: Warum betrifft uns das (menschlich, ohne Technik) → was ist das Thema überhaupt → eine konkrete Geschichte → die Bausteine einzeln → was heisst das für unser vRv-Projekt → Abschluss.
4. **Ein roter Faden.** Eine konkrete Geschichte am Anfang (bei Modul 5: ein Projekt, das stirbt), auf die jede spätere Folie zurückzeigt ("dieses Werkzeug verhindert Szene 2").
5. **Outline zuerst.** Zeig den Fahrplan früh (Agenda-Folie), und am Ende kehren die Anfangs-Fragen mit Antworten zurück.
6. **Harte Details in den Anhang.** Volltabellen und Nachschlage-Stoff kommen NACH der End-Folie, nicht in die 60 Minuten.
7. **Referentennotizen = komplettes Sprech-Skript.** Taste N zeigt sie. Jede Notiz beginnt mit Zeitmarke und Klick-Anzahl (`[T+12 · 3 Klicks]`), erste Zeile ist der Übergang vom letzten Bild, letzte Zeile kündigt die nächste Folie an.
8. **Hausaufgabe, die Claude nicht machen kann.** Am Ende eine Aufgabe, die nur die Person selbst erledigen kann (eigenes Gerät, eigene Woche, eigene Einschätzung), mit Abgabe im Hub.

## Die Methode, Teil 2: Visuell erzählen (Joaquins Matura-Methode)

9. **Morph statt Schnitt.** Wiederkehrende Elemente (eine Landkarte, ein Werkzeugkasten, Frage-Kacheln) tragen stabile `view-transition-name`-Attribute und wandern oder verwandeln sich beim Folienwechsel. Die Engine im Skelett macht das automatisch, du musst nur die Namen konsistent vergeben. Braucht Chrome/Edge, sonst weicher Blend.
10. **Klick-Builds.** Diagramme bauen sich pro Pfeiltaste auf: Elemente bekommen `class="frag"` und `data-frag="g1"`, `g2`, ... Gleiche Gruppe erscheint zusammen. Die Klick-Anzahl steht in der Notiz und muss mit dem HTML übereinstimmen.
11. **Bilder statt Textwände.** Jede Story- und Konzept-Folie wird von EINEM grossen Visual getragen: gezeichnete SVG-Szenen für die Geschichte, weisse "Papier-Attrappen" (Klasse `paper`) für echte Dokumente, damit sie wie Screenshots wirken.
12. **Look: Aurora-Glass dark.** Dunkler Grund, Aurora-Verläufe, Glas-Karten, Inter-Schrift. Mono-Schrift nur für wörtliche Zitate aus Dokumenten. Alles schon im Skelett-CSS, nichts erfinden.
13. **Entscheidungs-Folien sind Dossiers.** Wenn deine Session einen Team-Entscheid enthält, bekommt er ein volles Dossier: Ausgangslage → Optionen mit Pro und Contra → Herleitung mit belegten Zahlen → Empfehlung + objektives Entscheidungskriterium → wohin das Ergebnis fliesst, plus Log-Satz-Vorlage. Vier dünne Entscheid-Folien reichen nicht.

## Sprachregeln

- Deutsch, du-Form fürs Team, keine Gedankenstriche (kein — und kein –), stattdessen Komma, Doppelpunkt oder Punkt. Bindestriche in Komposita sind okay (30-Minuten-Termin).
- Keine Frankenbeträge oder Zusagen als Fakt zeigen, die das Team noch nicht beschlossen hat.

## Fertig-Checkliste (vor dem Upload prüfen, notfalls Claude prüfen lassen)

- [ ] Kein Begriff vor seiner Einführungs-Folie (Claude kann das automatisch auditieren)
- [ ] Klick-Zahlen in den Notizen stimmen mit den `data-frag`-Gruppen überein
- [ ] Alle Folien im Browser durchgeklickt: nichts läuft über den Folienrand, auch nicht in Zwischen-Klick-Zuständen
- [ ] Notizen (Taste N) sind ein vollständiges Sprech-Skript mit Zeitmarken
- [ ] Anfangs-Fragen kehren am Ende beantwortet zurück
- [ ] Anhang nach der End-Folie, nicht mittendrin
- [ ] Datei ist selbst-enthalten (ein einziges HTML, keine externen Dateien ausser Google Fonts)

## Hochladen

Hub → Lernen → dein Modul → **Material** → bei "Präsentation (HTML-Deck)" die Datei wählen → Hochladen. Ein neuer Upload ersetzt die alte Version. Der "Präsentation"-Button erscheint danach automatisch auf deiner Modul-Karte, gleich wie bei Modul 2 und 5.
