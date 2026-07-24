# LinkedIn post images — renderers, specs, when-to-use

> Loaded on demand by `/linkedin-posts` Step 4.5. Each post ships with a ready-to-post image. Style = **deterministic, on-brand cards** in the Automatisierbar terminal aesthetic (NOT AI imagery — for conservative Swiss B2B, AI hero images hurt credibility and need disclosure; clean designed cards read as professional).

## ⭐ Premium-Pipeline für Banner + hochwertige Bilder (2026-07-22, nach Toolchain-Bake-off)

**Pillow/Python-Layouts sind für hochwertige Assets (Profil-Banner, Hero-Grafiken) verboten** — Joaquin: "macht nur mid bilder", alles symmetrisch, blinder Iterations-Loop. Die validierte Pipeline:

1. **HTML/CSS als Design-Medium** (volle Typografie mit echtem Kerning, Grid, Ebenen, Schatten, Grain/Mesh-Gradients). Design-Regeln gegen den "generisch"-Look: Typo-Skala statt geratener Grössen, max. 2 Schriften, **asymmetrisches Layout** (Botschaft links/rechts versetzt, nie zentriert-symmetrisch), Tiefe über Layering (Foto-Cutout + Glow + Grain), 1 Akzentwort in Brand-Grün.
2. **Echte Assets statt Illustration**: echtes Foto (Cutout), echte Produkt-Screenshots, echtes Logo (`static/automatisierbar-logo.svg`). Lokales Background-Removal: `stroniarz/remove-bg` CLI (Apple-Vision-Framework, gratis, <1s) statt harter Kanten.
   **⚠ Gründer-Fotos (Operator-Regel 2026-07-24, nach 5 Fehlversuchen): IMMER die Master-Cutouts aus `references/linkedin/cutouts/` verwenden** (`<name>-duotone.png` für den Aurora-Look, `<name>-natural.png` für alles andere; je Kopf-bis-Hüfte, Schultern komplett, Tommy-Print bei Tej entfernt, saubere Kanten). NIE neu keyen, NIE die alten Scratchpad-Busts oder "PB"-Profilbilder nehmen. Neu erzeugen nur bei neuem Foto-Shooting via `references/linkedin/cutouts/make_cutouts.py` (Quelle: Desktop/Automatisierbar/automatisierbar bilder/IMG_3256=Tej, 3258=Nico, 3263=Patrik, 3264=Joaquin).
3. **Selbst-Verifikations-Loop über chrome-devtools MCP**: `new_page(file://…)` → `resize_page(Zielmasse)` → `take_screenshot` → Bild SELBST ansehen → fixen → reload. **Nie ein Bild präsentieren, das man nicht selbst gesehen hat.** Retina: macOS-Chrome rendert automatisch @2x (1584×396 → 3168×792 PNG); für CLI-Renders `--force-device-scale-factor=2`.
4. Export/Ablage: Quelle (`.html`) neben finalem `.png` versionieren, damit jede Iteration ein Ein-Zeilen-Edit ist.

**Bake-off-Ergebnisse (alle hands-on getestet):** Canva MCP `generate-design` bricht deutsche Komposita mitten im Wort, setzt ungefragt AI-Stock-Personen ein, Template-Autofill ist Enterprise-only, "Canva-Look"-Homogenisierung dokumentiert → nur für schnelle Ideen-Drafts. Figma MCP (`use_figma`) liefert saubere strukturierte Drafts, Iteration aber langsamer als HTML → Nutzen: Template-Ablage/manueller Feinschliff durch Joaquin. AI-Bildgeneration (Gemini-Image auf VPS-Key = free-tier, Limit 0; kein anderer Key vorhanden) → aktuell nicht verfügbar; wäre ohnehin NUR Asset-Quelle für textfreie Hintergründe (Recraft V3 $0.04/Bild wäre erste Wahl, Hex-steuerbar) — Text/Logos IMMER als HTML-Overlay, nie generieren lassen.

> **⚠️ Operator override for PERSONAL value/educational posts (2026-07-18):** Joaquin rejected the terminal-style cards/carousels for his personal value posts ("fett NEF"). For those, build a **dense, light, Eric-Partaker-style cheat sheet** instead: self-contained HTML → headless Chrome screenshot (`--force-device-scale-factor=2`, `print-color-adjust: exact` on `*`; weasyprint is broken on this Mac). Working template: `linkedin_images/KW-29/vier-eimer-cheatsheet.html` (1440×1800 → 2880×3600 PNG + @page PDF; warm paper bg, 4 pastel column cards, Charter title, Avenir Next body, inline-SVG icons, byline Joaquin only, no company branding). Terminal cards below remain the default for company-page posts.
>
> **⚠️ Update 2026-07-24 — Diagramm-Metapher-Standard für Konzept-Posts + AI-Slop-Verbot.** Ein minimalistisches Statement-Card (Treppe, viel Weissraum) wurde hart abgelehnt ("sieht aus wie der grösste AI Slob"). Für Konzept-/Reihenfolge-/Vergleichs-Posts (EIN Gedanke, nicht 4 parallele Spalten) gilt die KW-30-Linie als validierter Standard — Referenzen `linkedin_images/KW-30/zonen-prozesse.html`, `cost-of-change.html`, `joaquin-trichter.html`:
> fetter Condensed-Uppercase-Titel zweifarbig (schwarz + 1 Akzentwort), Subtitle-Promise, EINE zentrale Diagramm-Metapher (Trichter/Zonen/Kurve) statt Text-Layout, farbige Stufen-Chips, Serif-Kursiv-Zitate, seitliche Erklär-Blöcke mit ehrlichen Beispiel-Pills, EINE satte Akzentfarbe nur auf der Pointe (Isolations-Effekt), handgezeichnetes Marker-Element, Follow-Footer (Grün-Glow-Avatar `KW-30/joaquin-face.png` + Name) + automatisierbar.ch-Brandline.
> Komposition **symmetrisch** (Diagramm zentriert, Erklär-Blöcke Zickzack), Text darf Boxen nicht sprengen (Pills ~29px), nichts Tragendes im äusseren 10%-Rand.
> **Pflicht-Checks:** Render selbst ansehen + Thumbnail-Test bei ~350-430px Feed-Breite (Titel + Chips müssen lesbar bleiben).
> **Verboten (AI-Slop-Tells):** leere Quote-/Statement-Cards, zentrierte Leere als Fake-Premium, Gradients, Glassmorphism, Neon-Glows. Bei Design-Ablehnung: Deep Research (eigene approved Sheets + extern), dann NEU bauen, nicht am abgelehnten Entwurf schrauben.
> **Inhalts-Regel fürs 3-Stufen-Framework:** KI-Stufe immer mit Kriterium zeigen — Stufe 2 „läuft nach klaren Regeln im Hintergrund", Stufe 3 „erst wenn Entscheiden gefragt ist" (KI nur für nicht-deterministisches Einschätzen; O-Ton Operator 2026-07-24).

## Two renderers (both Pillow-only, run with the repo venv)

Run with `.venv/bin/python3` (the renderers use Pillow + bundled JetBrains Mono in `tools/assets/fonts/`; **no Cairo / no network / no AI / no cost**). Brand palette + corner-bracket terminal look are hardcoded.

### 1. Single card — `tools/render_linkedin_image.py`
```bash
echo '<spec-json>' | .venv/bin/python3 tools/render_linkedin_image.py -o <out.png>
# or: .venv/bin/python3 tools/render_linkedin_image.py -i spec.json -o out.png
```
Spec:
```json
{
  "headline": "≤6 words — the load-bearing number/claim",   // required
  "subtitle": "≤10 words — sector / context",               // optional
  "label":    "automatisierbar",        // top-left // meta (optional, default none)
  "tag":      "KW-27 · proof",          // top-right small tag (optional)
  "palette":  "green-on-deep",          // default green-on-deep
  "aspect":   "portrait",               // portrait(1080x1350, default) | square(1200x1200) | landscape(1200x627)
  "branding": "logo"                    // logo(default) | wordmark | none
}
```
The renderer auto-wraps + auto-fits the headline (no clipping) — **do not pad text to fill; give it the tight claim.**

### 2. Carousel (document post) — `tools/render_linkedin_carousel.py`
```bash
.venv/bin/python3 tools/render_linkedin_carousel.py -i carousel.json -o <out.pdf>
```
Outputs a single **PDF** (the LinkedIn document post, highest-engagement format) + the slide PNGs in `<out>_slides/`. Spec:
```json
{
  "palette": "green-on-deep",
  "label":   "automatisierbar",
  "slides": [
    {"headline": "…", "subtitle": "…"},   // slide 1 = title
    {"headline": "…", "subtitle": "…"},   // content slides
    {"headline": "Erstgespräch buchen", "subtitle": "cockpit.automatisierbar.ch/book"}  // last = CTA
  ]
}
```
5–7 slides. Each slide is portrait 1080×1350 with a `NN/total` counter; first + last carry the logo.

## Palettes
`green-on-deep` (default — green headline on dark green-black, the terminal look) · `white-on-black` (off-white headline, green subtitle) · `deep-on-light` (deep-green on off-white, for a lighter variant) · `light-on-green` (deep-green on solid #15C97A, bold accent). Rotate palettes across a week for variety, but `green-on-deep` is the house default.

## When to use which (per the post's pillar)
| Post pillar / type | Image | Why |
|---|---|---|
| build-in-public, industry-observation, lesson, team-culture, announcement | **single card** | one claim/number, fast, on-brand |
| **how-to / educational** (the "3-Schritte" / "5 Prozesse" posts) | **carousel** | document carousels are the highest-engagement LinkedIn format |
| **proof / case-study with a real demo** | **real-asset** | don't fake a screenshot — tell the operator to drop in a real screenshot/photo; set `Image Type = real-asset`, no generated file |
| a post with no strong visual idea | **none** | "no image beats a weak image" — set `Image Type = none` |

## Deriving the spec from a finished post
- **Card:** `headline` = the post's load-bearing number/claim distilled to ≤6 words (e.g. "3000 Franken einmalig", "15 Stunden pro Woche zurück", "100 Anrufe, 1 Muster"); `subtitle` = the sector/context (e.g. "Treuhand, Belegerfassung"); `label` = `automatisierbar`; `tag` = `KW-<iso> · <pillar>`; `palette` rotates (company → `green-on-deep`); `aspect` = `portrait`.
- **Carousel (how-to):** map the post's structure to slides — hook → title slide; each `→ Schritt` of the 3-arrow recipe → one content slide; the before/after number → a stat slide; the takeaway/CTA → the final slide (CTA = booking link). Keep each slide to one idea, ≤6-word headline.
- **Real numbers only** (from business-context: Bieri ~3000 CHF + ~500/mo, Gränacher 15h→15min, the funnel rates). Never invent a number for the image.

## Output location + delivery
Save to `linkedin_images/<KW-iso>/<author>-<pillar>.png` (cards) or `.pdf` (carousels) at the repo root (gitignored, regenerable from the stored Image Spec). **Notion accepts external image URLs only, not local uploads**, so this phase stores the *local file path* + the *Image Spec JSON* in the post's Notion row; the operator opens the file and uploads it to LinkedIn. (Native inline preview arrives with the Hub cutover — MinIO presigned attachments, already built in M5c.)

## Bonus asset (not yet runnable here)
`tools/render_n8n_workflow_diagram.py` (from the same AUT-46 commit) renders a clean process/automation-flow diagram — a great image for a build/how-to post. **It is still SVG/cairosvg-based, so it does NOT run in this x86_64 venv** (same Cairo arch issue that moved the card renderer to Pillow). It needs the same Pillow port before use; until then, skip it or render a carousel/diagram-style card instead.
