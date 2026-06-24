---
name: automatisierbar-deck
description: Build Automatisierbar slide decks in the signature terminal aesthetic — self-contained single-file HTML decks with a dark green-black background, JetBrains Mono, #15C97A accent, "// 01 —" section headers, corner brackets, big green stat numbers, "→" arrow lists, translucent bordered panels, a progress bar, dots, staggered reveals, and arrow-key/click navigation. Use this skill whenever building any Automatisierbar presentation, slide deck, or weekly SITREP/Wochenrapport, or whenever the user asks for a deck, slides, status report, strategy presentation, or pitch in the Automatisierbar style. This is the established default format for ALL Automatisierbar presentations — reach for it even if the user just says "mach ein Deck", "SITREP", "slides" or "Präsentation" without naming the style explicitly. Text content is German, terse, factual.
---

# Automatisierbar Deck

Erzeugt Präsentationen im Automatisierbar-Hausstil: ein einzelnes, self-contained
HTML-File mit Terminal-Ästhetik (dunkles Grün-Schwarz, JetBrains Mono, grüne Akzente,
Corner-Brackets, gestaffelte Reveals, Pfeil-Navigation). Das ist das Standardformat für
alle Automatisierbar-Decks und Wochen-SITREPs.

## Workflow

1. **Inhalt klären, nicht überfragen.** Wenn der Auftrag konkret ist (z. B. „SITREP KW 25"),
   direkt bauen und sinnvolle Annahmen treffen. Fehlende Zahlen als Platzhalter (`XX`) setzen
   und am Ende kurz benennen, was noch einzutragen ist — statt mit Rückfragen zu blockieren.

2. **Design-System laden.** `references/design-system.md` lesen — Farbtokens, Slide-Typen,
   Content-Regeln. Beim Bauen werden die `:root`-Variablen NIE verändert.

3. **Template kopieren.** `assets/deck-template.html` ist ein vollständiges, lauffähiges Deck
   mit den sechs Standard-Slide-Typen (Cover, Section+Lead, Stats, Pfeil-Liste, Panels,
   Closing). Es ist die Quelle der Wahrheit für Markup und Mechanik — niemals Optik aus dem
   Gedächtnis neu erfinden, immer aus dem Template ableiten.

4. **Befüllen statt umbauen.** Pro Slide nur Texte, Zahlen und `data-section`-Nummer ersetzen.
   Mehr Slides = `<section class="slide" data-section="NN">…</section>` duplizieren; Dots,
   Counter und Progress-Bar zählen sich automatisch hoch. Reveal-Delays (`--d`) in ~80–120 ms
   Schritten staffeln, max. ~4–5 animierte Elemente pro Slide.

5. **Schreiben wie Automatisierbar.** Deutsch, Hochdeutsch, knapp, faktisch. Eine Aussage pro
   Slide. Messbares in Stat-Slides, nicht in Prosa. Keine unbelegten Result-Claims; Piloten
   und Hochrechnungen klar als Projektion kennzeichnen. Human-in-control-Framing bei
   Automatisierungs-Themen („bestätigt per Klick").

6. **Ausliefern.** Deck als einzelne `.html` mit sprechendem Namen (z. B. `sitrep-kw25.html`)
   in den Output-Ort der jeweiligen Umgebung schreiben:
   - **Claude Code (lokal):** in den Projekt-Output-Ordner (`.tmp/decks/` oder einen vom User
     genannten Pfad) schreiben und den klickbaren Dateipfad nennen, damit der User es im Browser öffnet.
   - **Paperclip-Agent (VPS):** ins Issue-Workspace schreiben und im Handoff-Kommentar referenzieren/attachen.
   - **claude.ai:** nach `/mnt/user-data/outputs/` schreiben und via `present_files` zeigen.

   Danach kurz nennen, welche Platzhalter (`XX`) noch zu füllen sind. Keine langen Nachreden.

## Slide-Typen

Im Template als Slide 1–6 enthalten — Details und Markup-Bausteine in
`references/design-system.md`:

- **Cover** (immer Slide 1): Wordmark + `h1` + `subtitle`, keine Section-Nummer.
- **Section + Lead**: `// NN —` Header, `h2`, ein `lead`-Satz.
- **Stats**: 2–4 große grüne Zahlen mit kleinen Labels.
- **Pfeil-Liste**: `→`-Bullets, Schlüsselwort je Punkt in weißem `<b>`.
- **Panels**: 2- oder 3-spaltige translucent-grüne Karten, optional grüner `tag`-Eyebrow.
- **Closing / Next**: großer Fokus-Satz + Owner/Deadline-Liste.

## Nicht verhandelbar

- Genau eine Akzentfarbe: `#15C97A`. Keine zusätzlichen Buntfarben einführen.
- JetBrains Mono überall. Self-contained: alles in einer `.html`, kein Build-Step, keine JS-Libs.
- Corner-Brackets auf jeder Slide (alle vier). Section-Header im Format `// NN — Label`.
- Navigation per Pfeiltasten + Klick muss funktionieren — aus dem Template übernehmen, nicht kürzen.

## Export / Portabilität

Der Skill ist ein reiner Ordner (`SKILL.md` + `assets/` + `references/`) ohne Laufzeit-
Abhängigkeiten und damit direkt portabel:

- **Claude Code:** Ordner nach `~/.claude/skills/automatisierbar-deck/` legen (global) oder
  ins Projekt unter `.claude/skills/`. Wird automatisch als Skill erkannt.
- **Paperclip:** den Ordner als Skill in das Agent-OS-Repo aufnehmen, dort wo die übrigen
  Skills liegen. Da keine Skripte ausgeführt werden, genügt das reine Ablegen der Dateien.
- Die mitgelieferte `.skill`-Datei ist ein ZIP des Ordners — zum Installieren entpacken bzw.
  in claude.ai direkt hochladen.
