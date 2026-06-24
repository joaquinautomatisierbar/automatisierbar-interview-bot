# Automatisierbar Deck — Design System

Vollständige Token- und Komponenten-Referenz. Beim Bauen `assets/deck-template.html`
kopieren und die `:root`-Variablen unangetastet lassen — sie tragen die ganze Optik.

## Farbtokens

| Token            | Wert                          | Verwendung                                  |
|------------------|-------------------------------|---------------------------------------------|
| `--green`        | `#15C97A`                     | Primary Green: Akzent, Stat-Zahlen, `//`, `→`, Progress |
| `--green-dim`    | `rgba(21,201,122,0.55)`       | sekundäre grüne Linien                       |
| `--green-faint`  | `rgba(21,201,122,0.22)`       | Borders, Corner-Brackets, Dots (inaktiv)     |
| `--green-ghost`  | `rgba(21,201,122,0.05)`       | Panel-Füllung (translucent)                  |
| `--bg`           | `#0C1410`                     | dark green-black Haupt-Hintergrund           |
| `--bg-2`         | `#0A110D`                     | unteres Ende des Gradients                   |
| `--text`         | `#E6F0EA`                     | Haupttext                                    |
| `--text-mute`    | `#6F8A7C`                     | Labels, Meta, Sekundärtext                   |
| `--white`        | `#FFFFFF`                     | Hervorhebung (`<b>` in Listen, Wordmark)     |

Niemals andere Akzentfarben einführen. Grün ist die einzige Akzentfarbe; Hierarchie
entsteht über Helligkeit (white → text → text-mute) und Größe, nicht über Buntheit.

## Typografie

- **Font:** JetBrains Mono (CDN), Fallback `ui-monospace, 'SF Mono', Menlo, Consolas, monospace`.
- Gewichte: 400 (Fließtext/subtitle), 500 (sec-head), 700 (h2, b, brand), 800 (h1, Stat-Zahlen).
- Alles fluid via `clamp()` — nicht durch feste px ersetzen.

## Signatur-Elemente (das macht das Deck aus)

1. **Corner Brackets** — 4 L-förmige Ecken pro Slide (`.corner tl/tr/bl/br`). Immer alle vier setzen.
2. **Section Header** `// 01 — Label` — `//` und Nummer in Grün, Em-Dash + Label in `--text-mute`.
   Nummer = Slide-Sektion, zweistellig (`01`, `02`, …). Cover hat keine.
3. **Big Stat Numbers** — riesige grüne Zahl (`.stat .num`) mit kleinem Label darunter (`.stat .lbl`).
4. **Pfeil-Listen** `→` als Bullet (`ul.arrows`); Schlüsselwort pro Punkt in `<b>` (weiß).
5. **Panels** — translucent grün umrandet, optional `.tag`-Eyebrow in Grün-Caps.
6. **Staggered Reveal** — Elemente bekommen `class="reveal"` + `style="--d:120ms"`.
   Delays in ~80–120 ms Schritten staffeln, nie mehr als ~4–5 Elemente pro Slide animieren.
7. **Footer** — `brand` (links, grün) · `dots` (mitte) · `counter NN / NN` (rechts) · Progress-Bar oben.

## Slide-Typen (im Template als Slide 1–6 vorhanden)

| Typ                | Wann                                  | Bausteine                                  |
|--------------------|---------------------------------------|--------------------------------------------|
| Cover              | immer Slide 1                         | Wordmark, `h1`, `subtitle`. Keine sec-head. |
| Section + Lead     | Kapiteleinstieg / Status              | `sec-head`, `h2`, `lead`                    |
| Stats              | Kennzahlen der Woche                  | `sec-head`, `stat-row` mit 2–4 `stat`       |
| Pfeil-Liste        | Fortschritt / To-dos / Erkenntnisse   | `sec-head`, `h2`, `ul.arrows`               |
| Panels (2/3 Spalt.)| Gegenüberstellung, Blocker vs. Plan   | `sec-head`, `panel-grid cols-2`/`cols-3`    |
| Closing / Next     | letzte Slide                          | `sec-head`, `h1`, `ul.arrows` (Owner/Deadline) |

Slides hinzufügen = `<section class="slide" data-section="NN">…</section>` duplizieren.
Dots, Counter und Progress passen sich automatisch an die Slide-Anzahl an (JS zählt selbst).
Den `<title>` im `<head>` und `id="counter"`-Startwert sind kosmetisch; JS überschreibt den Counter.

## Content-Regeln (Nico-Stil, knapp & faktisch)

- Deutsch, Hochdeutsch, kein Dialekt. Terse, faktisch, kein Marketing-Sprech.
- Keine unbelegten Ergebnis-Claims. Pilot/Projektionen klar als solche kennzeichnen
  (z. B. Bieri Treuhand = Pilot, unbestätigt → „Projektion", nicht „Resultat").
- Human-in-control-Framing wo Automatisierung gezeigt wird („bestätigt per Klick").
- Eine Aussage pro Slide. Lieber mehr Slides als volle Slides.
- Zahlen sprechen lassen: was messbar ist, kommt in eine Stat-Slide, nicht in Prosa.

## Technik

- **Self-contained:** alles in einer `.html`. Einzige externe Abhängigkeit ist die
  Google-Fonts-Verknüpfung; Fallback-Monospace ist gesetzt, also läuft das Deck auch offline.
- **Nav:** ← → / Leertaste / Klick (rechte Hälfte = vor, linke = zurück) / `Home`/`End`. Dots klickbar.
- Keine externen JS-Libs, kein Build-Step. Direkt im Browser öffnen oder präsentieren.
