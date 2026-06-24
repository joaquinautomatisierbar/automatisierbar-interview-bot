# Paperclip — Intro-Call fürs Team (Patrik · Nico · Tej)

**Zielgruppe:** nicht-technische Operator, die Paperclip im Alltag nutzen, um Automationen zu bauen.
**Ziel des Calls:** Am Ende kann jeder von euch (1) ein Resultat aus dem Kunden-Interview in eine fertige Automation verwandeln und (2) eine eigene Idee von Grund auf bauen — mithilfe des Internal Planner, ohne dass Joaquin es für euch macht.
**Dauer:** ca. 35–40 Min. Möglichst praktisch halten. Ein gemeinsamer Live-Build bringt mehr als zehn Slides.

---

## TEIL 1 — Slide-Outline (10 Slides)

Slides sind *Anker*, kein Skript. Eine Idee pro Slide. Das eigentliche Lernen passiert im Live-Demo (Teil 2).

**Slide 1 — Titel**
> «Paperclip: dein KI-Build-Team.»
Untertitel: «Von der Idee → zur fertigen Automation, ohne auf mich zu warten.»

**Slide 2 — Warum es das gibt (das Problem)**
- Bis jetzt läuft jede Automation über Joaquin → er ist der Flaschenhals.
- Paperclip = eine *Firma aus KI-Spezialisten*, an die ihr direkt delegieren könnt.
- Ihr beschreibt, was ihr wollt; das Team plant, baut, testet, dokumentiert und liefert es auf GitHub aus.

**Slide 3 — Das Denkmodell**
- Stellt euch Paperclip wie eine **Agentur vor, die von KI besetzt ist** — nicht wie eine Software, die ihr bedient.
- Ihr seid der *Kunde*. Ihr briefet, prüft das Resultat und bittet um Änderungen — wie eine E-Mail an eine Agentur.
- Ihr müsst **nicht programmieren**. Ihr müsst *klar beschreiben* und *ehrlich prüfen*.

**Slide 4 — Wer im Team ist (die Agenten)**
Die zwei, mit denen ihr am meisten zu tun habt:
- **🧭 Internal Planner** — macht aus einer groben Idee eine saubere, baubare Vorgabe (Spec).
- **🧪 Test Data Generator** — liefert realistische Testdaten, damit ihr eine Automation sicher testen könnt.
Die Build-Crew (arbeitet im Hintergrund, ihr stösst sie nicht von Hand an):
- **Engineer** baut → **QA** testet → **Product Reviewer** prüft, ob es das echte Problem löst → **Release** liefert auf GitHub aus.

**Slide 5 — Zwei Wege, wie ihr es nutzt**
- **Weg A — Aus einem Kunden-Interview** (warmer Start: die Spec existiert schon).
- **Weg B — Aus eurer eigenen Idee** (kalter Start: ihr erstellt die Spec mit dem Internal Planner).
Beide enden gleich: eine fertige Automation auf GitHub, die ihr prüfen und weiter anpassen könnt.

**Slide 6 — Weg A: Interview → Ausgeliefert**
1. Kunde füllt das **Workflow-Interview** aus → daraus entsteht eine Spec.
2. Diese Spec geht als neuer Auftrag in Paperclip.
3. Das Build-Team baut + testet → Resultat landet auf **GitHub**.
4. Ihr prüft es und geht zum **Anpassen zurück in den Chat** («ändere X, füge Y hinzu»).
5. Testen nötig? → fragt den **Test Data Generator** nach Beispieldaten.

**Slide 7 — Weg B: Eure Idee → Gebaut**
1. Öffnet den **Internal Planner**, beschreibt eure Idee in normaler Sprache.
2. Er stellt Rückfragen und schreibt eine saubere Spec (einen «Prompt»).
3. Übergebt diese Spec dem Build-Team **direkt in Paperclip**.
4. Ab da gleich wie Weg A: auf GitHub prüfen, im Chat anpassen, mit Beispieldaten testen.

**Slide 8 — Wie man anpasst (die Schleife)**
- Bauen ist ein *Gespräch*, kein einmaliger Schuss.
- Sei konkret: «Der E-Mail-Betreff ist falsch, er sollte X heissen» schlägt «mach es besser».
- Nach jeder Änderung erneut prüfen. Kleine Schleifen > grosse Neuanläufe.

**Slide 9 — Die 3 Regeln (damit nichts kaputtgeht oder Geld verbrennt)**
1. **Pausiere keine Agenten und entpausiere keine, die du nicht selbst pausiert hast.** Ist etwas pausiert, gibt es einen Grund — frag zuerst nach.
2. **Achte auf die Kosten.** Ein normaler Build kostet ein paar Franken. Läuft etwas lange «im Hintergrund» ohne Resultat → stoppen und melden.
3. **Im Zweifel: stoppen.** Alles, was *echte* Kundendaten betrifft oder *echte* Nachrichten verschickt → zuerst mit Joaquin abklären.

**Slide 10 — Wenn du nicht weiterkommst → melden**
- Paperclip meldet sich auf **Telegram**, wenn es eine menschliche Entscheidung braucht. Antworte darauf.
- Blockiert? Ab damit in den Team-Telegram. Kämpf nicht eine Stunde allein dagegen an.
- Nächster Schritt: Jeder von euch baut diese Woche eine kleine Automation. Beim ersten schaue ich mit euch zusammen.

---

## TEIL 2 — Call-Skript (mit Zeitangaben)

### 0:00–0:03 · Einstieg mit dem «Warum»
> «Bis jetzt seid ihr zu mir gekommen und musstet warten, wenn ihr eine Automation gebraucht habt. Ab heute ist das vorbei. Paperclip ist im Grunde eine KI-Agentur, die ihr direkt briefen könnt. Ihr beschreibt, was ihr wollt, es baut das, testet es und liefert es auf GitHub. Ihr schreibt keinen Code — ihr beschreibt und prüft. Das ist die ganze Aufgabe.»

Erwartung setzen: *«Bis zum Ende dieses Calls hat jeder von euch einen echten Build angestossen.»*

### 0:03–0:07 · Das Denkmodell (Slide 3)
Eine Analogie einhämmern und den ganzen Call wiederverwenden:
> «Behandelt es wie eine E-Mail an eine Dev-Agentur. Ihr seid der Kunde. Ein vager Auftrag gibt ein vages Resultat. Ein klarer Auftrag gibt etwas, das ihr ausliefern könnt. Die Fähigkeit, die ihr heute lernt, ist nicht technisch — es ist *klar briefen* und *ehrlich prüfen*.»

Beruhigen: Man kann durch *Ausprobieren* nichts kaputt machen. Die Schutzgeländer (Limits, Stopps, Pausen) sind genau dafür da, dass ihr experimentieren könnt.

### 0:07–0:12 · Die Agenten kennenlernen (Slide 4)
Nur die zwei vorstellen, die sie selbst steuern:
- **Internal Planner** — «euer Denkpartner. Gib ihm eine chaotische Idee, du bekommst einen sauberen Plan zurück.»
- **Test Data Generator** — «euer Sicherheitsnetz. Willst du eine Automation testen, ohne echte Kundendaten zu nutzen? Frag nach realistischen Testdaten.»

Die Build-Crew erwähnen (Engineer → QA → Reviewer → Release), aber so rahmen: *«die laufen von selbst — die stösst ihr nicht an. Sie sind der Grund, warum ein Build schon getestet und dokumentiert zurückkommt und nicht einfach über den Zaun geworfen wird.»*

### 0:12–0:22 · LIVE-DEMO — Weg B (eigene Idee bauen)
> Live machen. Das ist das Herzstück des Calls. Ein winziges, reales Beispiel nehmen, das alle verstehen — z. B. «wenn ein neuer Lead reinkommt, schick mir eine Telegram-Zusammenfassung».

Jeden Schritt laut erklären:
1. **Internal Planner** öffnen. Die Idee in ein, zwei normalen Sätzen eintippen.
2. Ihn seine Rückfragen stellen lassen — wie ein normales Gespräch beantworten. *Hinweis: «Seht ihr, wie er die Spec aus mir herauszieht? Das ist die Arbeit, die ich früher im Kopf gemacht habe.»*
3. Die fertige Spec zeigen. «Das ist jetzt baubar.»
4. Dem Build-Team übergeben. Zeigen, dass es jetzt *in Arbeit* ist — und dass man weggehen kann; es braucht keine Aufsicht.
5. (Falls ein früherer Build fertig ist) **GitHub** öffnen und zeigen, wie ein fertiges Resultat aussieht.

Immer wieder betonen: *«Achtet drauf — ich schreibe keinen Code.»*

### 0:22–0:28 · Weg A — die Interview-Abkürzung (Slide 6)
> «Weg B ist für eure eigenen Ideen. Weg A ist noch einfacher — wenn es eine *Kunden*-Automation ist, hat das Workflow-Interview die Spec bereits für euch geschrieben.»

Den Ablauf auf Whiteboard-Niveau durchgehen: Interview → Spec → Build-Team → GitHub → ihr prüft → im Chat anpassen. Die **Anpass-Schleife** betonen (Slide 8): Bauen ist ein Gespräch. Zeigen, wie man eine Änderung in normaler Sprache anfordert, und wie man mit dem **Test Data Generator** prüft, bevor etwas Echtes berührt wird.

### 0:28–0:33 · Die 3 Regeln (Slide 9)
Hier langsamer werden — das ist der Teil, der die Firma schützt.
1. Entpausiere nichts, was du nicht selbst pausiert hast.
2. Achte auf die Kosten — normal sind ein paar Franken; «läuft die ganze Nacht ohne Resultat» ist ein Warnsignal, stoppen.
3. Echte Kundendaten oder echte ausgehende Nachrichten → zuerst mit mir abklären.
> «Das ist keine Bürokratie. Wir haben schon zweimal Geld verbrannt, weil Agenten sich selbst in Schleifen geschickt haben. Die Geländer sind der Grund, warum ihr *frei* experimentieren könnt.»

### 0:33–0:38 · Wenn du nicht weiterkommst + Aufgabe (Slide 10)
- Paperclip meldet sich auf **Telegram**, wenn es euch braucht. Antwortet darauf.
- Länger als ein paar Minuten blockiert? Ab in den Team-Chat. Nicht festbeissen.
- **Hausaufgabe:** Jeder von euch liefert diese Woche eine kleine Automation aus. Beim ersten sitze ich mit dir zusammen. Will jemand gleich jetzt eine Idee übernehmen?

### 0:38–0:40 · Fragen / Puffer
Fragen aufnehmen. Mit diesem Satz abschliessen: *«Ihr müsst nicht technisch sein. Ihr müsst klar sein. Den Rest erledigt das System.»*

---

## TEIL 3 — Spickzettel zum Mitnehmen

> Ausdrucken / in Notion einfügen. Das ist, worauf sie tatsächlich zurückgreifen.

### Was ist Paperclip?
Ein KI-Build-Team. Ihr briefet es in normaler Sprache; es plant, baut, testet, dokumentiert und liefert Automationen auf GitHub aus. **Ihr programmiert nicht — ihr beschreibt und prüft.**

### Die zwei Agenten, die ihr steuert
| Agent | Wann nutzen… | Was du machst |
|---|---|---|
| 🧭 **Internal Planner** | Du hast eine Idee, aber keine klare Spec | Idee beschreiben, Rückfragen beantworten, sauberen baubaren Plan erhalten |
| 🧪 **Test Data Generator** | Du willst ohne echte Daten testen | Nach realistischen Testdaten für deine Automation fragen |

### Bauen: zwei Wege
**Weg A — Aus einem Kunden-Interview (Spec existiert schon)**
1. Kunde füllt das **Workflow-Interview** aus → Spec entsteht automatisch
2. Build-Team baut + testet → landet auf **GitHub**
3. Prüfen → Änderungen **im Chat** anfordern
4. Testen nötig? → den **Test Data Generator** nach Beispieldaten fragen

**Weg B — Aus eurer eigenen Idee (ihr erstellt die Spec)**
1. **Internal Planner** öffnen → eure Idee beschreiben
2. Seine Rückfragen beantworten → er schreibt die Spec
3. Spec dem Build-Team **in Paperclip** übergeben
4. Auf GitHub prüfen → im Chat anpassen → mit Beispieldaten testen

### Wie man gut briefet (die einzige echte Fähigkeit)
- **Sei konkret.** «E-Mail-Betreff soll `Neuer Lead: {name}` sein» > «mach die E-Mail schöner».
- **Eine Änderung aufs Mal** beim Anpassen. Kleine Schleifen schlagen grosse Neuanläufe.
- **Prüfe ehrlich.** Wenn etwas falsch ist, sag genau *was* falsch ist. Das System kann keine Gedanken lesen, reagiert aber gut auf klares Feedback.

### Die 3 Regeln
1. ⛔ **Entpausiere keine Agenten, die du nicht selbst pausiert hast** — frag zuerst.
2. 💰 **Achte auf die Kosten** — normaler Build = ein paar Franken. «Läuft ewig, kein Resultat» = stoppen + melden.
3. 🚦 **Echte Kundendaten oder echte ausgehende Nachrichten?** → stoppen und zuerst mit Joaquin abklären.

### Wenn du nicht weiterkommst
- Paperclip meldet sich auf **Telegram**, wenn es eine Entscheidung braucht — antworte darauf.
- Länger als ein paar Minuten blockiert? Ab in den **Team-Telegram**. Nicht allein festbeissen.

---

## Anhang — Unter der Haube (optional, nur falls jemand fragt «wie funktioniert das wirklich?»)

Brauchst du im Call wahrscheinlich nicht, steht aber hier, damit du nicht überrascht wirst:

- **Die Build-Pipeline:** CEO leitet den Auftrag weiter → CTO plant → Engineer baut → QA testet (geht bei Fehler zurück, max. ~8-mal) → Product Reviewer prüft, ob das echte Problem gelöst wird (max. ~3 Schleifen) → Release liefert auf GitHub aus. Harte Limits sorgen dafür, dass ein hängender Auftrag stoppt und Joaquin meldet, statt endlos zu schleifen.
- **Warum Agenten nicht von selbst laufen:** Frühere Versionen liessen Agenten auf ihre eigenen Kommentare aufwachen → Endlosschleifen → Geld verbrannt. Jetzt laufen Agenten nur, wenn sie ausdrücklich angestossen werden. Das ist das Sicherheitsmodell, kein Fehler.
- **Telegram-Brücke:** Team-Chat-Nachrichten können den CEO-Agenten anstossen; Antworten der Agenten kommen zurück auf Telegram. Eine Nachricht = ein Lauf = begrenzte Kosten.
- **Wo die Dinge liegen:** Konfiguration + Pipeline in [tools/paperclip/](.), das laufende System auf dem VPS. Joaquin betreibt die technische Ebene (Orchestrator, Bootstrap, Zugangsdaten) — das Team fasst diese Ebene nicht an.

*Referenz-Docs für Joaquin: [pipeline.config.json](pipeline.config.json), [orchestrator.js](orchestrator.js), [NEXT_SESSION_PLAN.md](NEXT_SESSION_PLAN.md), [scripts/bootstrap-new-agents.sh](scripts/bootstrap-new-agents.sh).*
