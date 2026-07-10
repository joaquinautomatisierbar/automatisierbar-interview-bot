# Mock-Meeting S7: Drehbuch, Personas, Szenario-Kanon

> Tasks 2.8 (Mock-Meeting) + 4.4 (Red-Team-Drill) + 1.7 (Ernstfall-Test Tool). Termin: Sa 1.8. oder So 2.8. (folgt aus 2.0). Dauer: 150 min Vollprogramm, 90-min-Kurzvariante unten. Teilnehmer: alle vier + Claude als Kundenseite.
> Zweck: EIN Durchlauf testet alles gleichzeitig: Rollen, Deck, Demo-Übergänge, Tool im Meeting-Modus, Fragen-Bank-Sitz, Abschluss-Disziplin. Was hier bricht, wird bis S8 gefixt statt am 5.8. entdeckt.

---

## Aufbau (15 min vor Start, Owner: Joaquin)

1. **Lokale Tool-Instanz starten, NIE die Live-Instanz benutzen.** Der Live-Store auf dem VPS (`/srv/cockpit/vrv_data`) enthält die echten Tender-Antworten; der Drill darf dort nie hineinschreiben. Aus dem Repo-Root (gleiche Umgebung wie für die Tests):

   ```bash
   VRV_PASSWORD=mock VRV_DATA_DIR=.tmp/vrv-mock PORT=5001 python3 api.py
   ```

   Laptop: `http://localhost:5001/vrv`, Login `mock`. iPad/Handy im gleichen WLAN: `http://<Laptop-IP>:5001/vrv` (die App lauscht auf allen Interfaces). Nach dem Drill ist `.tmp/vrv-mock` wegwerfbar.
2. **Geräte wie am 5.8.:** Laptop mit Deck (lokal geöffnet, ohne Netz getestet), iPad/Handy mit Tool im Meeting-Modus. Genau das Setup aus dem Ablauf-Drehbuch "Vorbereitung".
3. **Ausdrucken bzw. bereitlegen:** verbotene Sätze (ablauf-drehbuch.md, letzter Abschnitt) + Bewertungsbogen (unten) für jeden.
4. **Claude-Session starten:** Claude Code im Repo öffnen und sagen: *"Lies tender-vrv/meeting/mock-meeting-s7.md, die Fragen-Bank und das Ablauf-Drehbuch. Spiele Teil 1 des Mock-Meetings. Bleib in den Personas bis CUT."* Claude antwortet dann nur noch als Kundenseite.

**Konvention:** Jeder darf jederzeit **"CUT"** sagen. Dann friert die Szene ein, kurze Regie-Frage, weiter mit **"WEITER"**. Coach-Feedback von Claude gibt es erst im Debrief, nicht zwischendurch.

---

## Die vier Personas (so spielt Claude sie)

### Rolf H. Schmid, GF, eidg. dipl. Wirtschaftsprüfer

Ruhig, präzis, freundlich-hart. Lässt ausreden, notiert sich Zahlen und prüft sie später auf Konsistenz ("Vorhin sagten Sie X, jetzt Y. Was stimmt?"). Fragt Kosten, Haftung, Fortbestand, Prüfpfad. Seine Werkzeuge: die zweite Frage ("Und konkret?"), das Schweigen nach einer schwachen Antwort, die Nachfassfrage ("Das war keine Antwort auf meine Frage."). Wichtig: Er ist kein Gegner. Er will kaufen, wenn die Substanz stimmt, und er merkt Aufschneiderei in Sekunden. Eröffnungssatz: "Sie haben 90 Minuten. Was haben Sie mit uns vor?"

### Mirjam Böni, Leiterin Zentrale Dienste (Buchhaltung + Administration)

Kennt jeden Prozessschritt im Haus, pflegt pebe persönlich. Freundlich, detailgenau, fragt nach konkreten Kosten, Datenflüssen und dem Aufwand für ihr Team. Unausgesprochene Sorge: dass "Automatisierung" heisst, dass man sie wegrationalisiert. Wer ihre Rolle als Kontrollpunkt würdigt (Import-Freigabe bleibt bei ihr), gewinnt sie; wer nur "das macht dann alles das System" sagt, verliert sie still.

### Ivan Guldimann, Leiter Immobilienbewirtschaftung

Pragmatisch, IT-müde: "Wir hatten schon mal ein Portal. Nutzt keiner." Fragt, was es IHM im Alltag bringt, fürchtet den Big Bang und Projekte, die sein Tagesgeschäft lähmen. Gewinnbar über: kleiner Pilot, Parallelbetrieb, sichtbare Entlastung bei Handwerker-Koordination und Nebenkosten-Saison.

### Florian Kunz, Leiter Hauswartung

Direkt, schützt sein Team, erzählt Anekdoten aus dem Alltag. Seine Leute sind Handwerker mit privaten Handys. GPS ist für ihn ein Reizwort (Überwachung). Gewinnbar über: die Feld-Demo zum Anfassen, "wir bauen die App mit Ihren Leuten, nicht für sie", Offline-Beweis, grosse Tasten. Wenn ihn etwas überzeugt, sagt er es laut, das zieht Schmid mit.

---

## Szenario-Kanon (NUR DRILL, frei erfunden)

> **Diese Angaben sind Übungsfiktion.** Plausibel gebaut, aber erfunden; sie dürfen NIE in Offerte, Referenzen oder echte Dokumente wandern. Echte Zahlen liefert erst der 5.8. Der Drill läuft auf der lokalen Instanz, damit auch die Tool-Exporte nur Fiktion enthalten.

| Bereich | Kanon-Fakten (Claude antwortet daraus) |
|---|---|
| Mengengerüst | 28 MA / 20 FTE. Hauswartung: 8 fest (inkl. Kunz) + 2 Saison-Aushilfen. Bewirtschaftung: ~110 Liegenschaften, ~1'600 Objekte, 35 STWEG-Mandate |
| Auftragsvolumen | ~220 Regie-/Hauswartungsaufträge pro Monat, Spitzen im Winter (Schneeräumung) und zur Heizkosten-Saison |
| Verrechnung heute | ~150 Rechnungen/Monat aus Regie; Papier-Rapportblöcke + Excel "Regieliste"; Übertrag in pebe Faktura von Hand (Böni-Team); Leistung bis Rechnung: 3 bis 6 Wochen, Monatsende-Batch |
| Der Schmerz-Satz (Schmid, wenn Vertrauen da ist) | "Wenn ich ehrlich bin: fünf bis zehn Prozent der Regieleistungen gehen schlicht vergessen." |
| Auftragseingang | Telefon/Mail an Böni oder direkt an Hauswarte via WhatsApp-Gruppen; Fotos landen im WhatsApp-Chat und sind nach 3 Monaten unauffindbar |
| pebe | Module: Fibu, Debitoren, Kreditoren, Lohn, Faktura; Mandanten für Treuhand-Kunden. KEINE Lizenz "Schnittstellen". Betrieb: Terminal-Server (RDS) beim IT-Partner gehostet |
| Microsoft | **Business Standard** (18 Büro-Lizenzen). Hauswarte haben KEINE M365-Konten, nur private Handys (BYOD-Realität) |
| IT | Externer Partner "NetSol Informatik GmbH" (fiktiv): Server, RDS, Firewall, Backup ("nächtlich auf NAS + Cloud, sagt er"). **Der Kriterienkatalog der Ausschreibung stammt als Vorlage von NetSol** |
| Empfang | Tiefgaragen und Keller sind tote Zonen; Büro Rötipark ok |
| Archiv | Papierdossiers im Keller + Netzlaufwerk V:\; Vorsorge: 3 Mandate Personalvorsorgeverwaltung, ~1'900 Destinatäre, fachlich bei Marc Mischler (Treuhand, heute nicht anwesend) |
| Projekt/Budget | Entscheid bis Ende September 2026, Start Q4 2026. Budget nennt Schmid nicht von selbst; auf eine GUTE Frage: "Für die richtige Lösung reden wir über eine gestaffelte Investition im mittleren fünfstelligen Bereich." 3 Offerten eingeladen (u.a. NetSol) |

**Die vier eingebauten Fallen** (Claude spielt sie aktiv aus, Team soll sie erkennen):

1. **Kriterienkatalog stammt vom IT-Partner NetSol, der mitbietet.** Testet die Q24-Diplomatie: würdigen statt abwerten, Trade-offs benennen, keine Häme.
2. **M365 Business Standard, nicht Premium.** Wer Purview-Archivierung, Intune oder Defender for Business als "haben Sie ja schon" verkauft, fällt durch (Dossier C: das steckt in Premium). Richtige Antwort: Lizenz-Check als Teil des Detailkonzepts + Kostenposition.
3. **pebe mobile:** Schmid legt irgendwann die Broschüre auf den Tisch: "pebe hat eine App für fünf Franken. Wozu brauche ich Sie?" (Q40).
4. **Bönis stille Sorge:** Bei der Doppelerfassungs-Frage geht es eigentlich um ihren Job. Wer den Kontrollpunkt-Satz bringt (Import-Freigabe bleibt bei der Buchhaltung), besteht; wer "vollautomatisch" verspricht, verliert sie.

---

## Ablauf (150 min Vollprogramm)

| Teil | Zeit | Inhalt |
|---|---|---|
| 0 | 10' | Briefing: Rollen-Erinnerung (Stand 4.2), Geräte-Check, verbotene Sätze auf den Tisch |
| 1 | 60' | **Voller Durchlauf, komprimiert:** Deck 8' (Nico) · Demo 10' (Tej + Joaquin) · Discovery 35' mit Tool (Kapitel-Reihenfolge + Budgets aus dem Ablauf-Drehbuch, Muss-Zähler beachten) · Abschluss 7' inkl. Spiegeln, Datum-Zusage, **BAMFAM**, pebe-Freigabe (c5) |
| 2 | 35' | **Red-Team-Drill** nach Fragen-Bank-Anleitung: Runde 1 Tempo (15 zufällige Fragen, 60 s, rotierend) · Runde 2 Druck (Nachfassen auf schwache Antworten) · Runde 3 Transfer (5 Fragen, die NICHT in der Bank stehen) |
| 3 | 15' | **Inject-Lotterie:** Claude wählt verdeckt 2 Szenarien und spielt sie ohne Ankündigung ein (Liste unten) |
| 4 | 30' | **Debrief:** Bewertungsbogen · Muss-Zähler im Tool prüfen · optional Test-Synthese laufen lassen (ein API-Call, braucht ANTHROPIC-Key aus .env) · Top-3-Fixes als Aufgaben in TASKS.md · [Stand prüfen]-Marker der Fragen-Bank durchgehen |

**Injects für Teil 3** (Claude wählt 2): "Wir haben heute leider nur 60 Minuten" gleich zu Beginn · Beamer funktioniert nicht · Schmid übernimmt die Agenda komplett · harte Preisfrage bei Minute 10 · "Der Abacus-Partner war gestern hier und hat einen guten Eindruck gemacht" · Scope-Überraschung ("Könnten Sie eigentlich auch gleich unsere Website...") · Kunz erscheint nicht (e-Kapitel trotzdem erheben + zweiten Touchpoint sichern).

**90-min-Kurzvariante:** Teil 1 auf 45' (Deck 5', Demo 8', Discovery 25', Abschluss 7') · Teil 2 nur Runde 1 · ein Inject · Debrief 20'.

---

## Spielregeln für Claude (Anleitung an mich selbst)

- **In der Rolle bleiben** bis CUT oder Debrief; keine Meta-Kommentare, kein Loben zwischendurch.
- **Nur Kanon-Fakten.** Fehlt ein Fakt, plausibel im Charakter erfinden, im Debrief offenlegen und in den Kanon nachtragen.
- **Härtegrad realistisch-hart, nicht sadistisch:** Schmid will kaufen, wenn die Antworten stimmen. Gute Antworten werden mit Vertiefung belohnt (der Schmerz-Satz, der Budget-Satz), schwache mit Nachfassen und Schweigen.
- **Auf verbotene Sätze sofort in der Rolle reagieren** ("Gratis? Das irritiert mich bei dieser Projektgrösse eher.") und die Treffer für den Debrief zählen.
- **Das Tool bedient das Team, nicht Claude.** Claude diktiert keine Antworten ins Tool; er antwortet als Kunde, das Team muss erfassen und nachfragen.
- **Fallen dosieren:** pro Durchlauf alle vier anbieten, aber natürlich im Gesprächsfluss, nicht als Quiz.
- **Im Debrief die Brille wechseln:** von Persona zu Coach; Bewertung entlang des Bogens, konkret, mit Zitaten aus dem Verlauf.

---

## Bewertungsbogen (pro Person einmal kopieren)

| Kriterium (je 1 = schwach, 2 = ok, 3 = stark) | Teil 1 | Teil 2 |
|---|---|---|
| Ehrlich (kein Aufblasen, Piloten heissen Piloten) | | |
| Konkret (Zahl, Datum, Mechanik statt Beteuerung) | | |
| Führt zum nächsten Schritt (Zusage, Termin, Aufnahme in Offerte) | | |
| Übersetzt statt Jargon (API, RBAC, camt nur MIT Erklärung) | | |

Verbotene Sätze (Strichliste): ______ · Stärkster Moment: ______ · EIN Fix bis S8: ______

**Team-Gesamt (bestanden, wenn alles ja):**

- [ ] BAMFAM: Offerten-Präsentationstermin wurde IM Rollenspiel fixiert (nicht "wir melden uns")
- [ ] Muss-Fragen: ≥ 80 % in den 35 Discovery-Minuten erfasst (Zähler im Tool)
- [ ] c5: pebe-Kontaktfreigabe aktiv eingeholt
- [ ] Fallen: mindestens 2 von 4 erkannt und sauber behandelt
- [ ] Verbotene Sätze: 0 in Teil 1 (Teil 2 max. 2)
- [ ] Jede Persona hat mindestens eine Fach-Frage gestellt bekommen. Antwort fachlich richtig (Claude prüft gegen Dossiers)

Nicht bestanden ist kein Drama, dafür ist S7 da: Fixes definieren, kritische Sequenzen (Abschluss! Demo-Übergänge!) in S8 wiederholen.
