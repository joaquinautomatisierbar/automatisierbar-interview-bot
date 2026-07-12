# Handout-Guide: So baust du dein Session-Handout (mit Vorlage)

> Für Nico (Modul 4), Tej (Modul 1 + 6) und Patrik (Modul 3). Auch diesen Guide kannst du **direkt deinem Claude Code geben**: zusammen mit deinem Primer und deinem fertigen Deck entsteht daraus das Handout in einem Rutsch. Damit alle Handouts im Hub gleich aussehen, sind Titelzeile und Pflicht-Abschnitte fix vorgegeben. Der Inhalt dazwischen ist frei.

## So gehst du vor (4 Schritte)

1. **Gib Claude Code drei Dinge:** diesen Guide, dein fertiges Deck (oder den Primer) als Stoffquelle, und den Prompt unten.
2. **Prüfe:** Titelzeile, Pflicht-Abschnitte und Abgabe-Zeile exakt nach Vorlage? Hausaufgabe wirklich nicht an Claude delegierbar?
3. **PDF erzeugen lassen:** Claude baut aus dem Markdown eine A4-Druckfassung (Print-HTML → headless Chrome → PDF). Einfach im Prompt mitbestellen.
4. **Beides hochladen:** Hub → Lernen → dein Modul → **Material** → "Handout (Markdown)" und "Handout (PDF)".

## Prompt-Vorlage (kopieren, anpassen, an Claude Code schicken)

```
Baue mir das Handout zu meiner Team-Session [DEIN THEMA] nach der Vorlage in
guide-handout.md (angehängt), halte Titelzeile, Pflicht-Abschnitte und
Abgabe-Zeile exakt ein. Stoffquelle: mein Deck / Primer (angehängt).
Die Hausaufgabe muss so gebaut sein, dass Claude sie NICHT für die Person
erledigen kann (eigenes Gerät, eigene Einschätzung, eigene Woche).
Erzeuge zusätzlich eine A4-PDF-Druckfassung mit ausfüllbaren Feldern.
Abgabefrist: [DATUM, siehe Team-Kalender], 18:00.
```

## Feste Regeln (für Einheitlichkeit)

- **Titelzeile:** `# Modul N · [Thema]: Handout & Hausaufgabe` als allererste Zeile.
- **Untertitel direkt darunter:** eine Blockquote-Zeile mit Session-Nummer, Referent und Abgabefrist, zum Beispiel: `> Session 4 · Patrik · Abgabe: So 26.7., 18:00 im Hub`.
- **Pflicht-Abschnitte in dieser Reihenfolge** (Überschriften wörtlich so):
  1. `## Falls du nur 5 Minuten hast` : die 3 bis 5 Kernaussagen der Session in einem Absatz.
  2. `## Spickzettel` : Tabellen/Listen zum Nachschlagen, gegliedert nach den Teilen des Decks.
  3. `## Hausaufgabe` : nummerierte Aufgaben, siehe Regeln unten.
  4. `## Warum ohne Claude` : zwei, drei Sätze, warum diese Aufgabe nur die Person selbst machen kann.
- **Abgabe-Zeile** (wörtlich, am Ende des Hausaufgaben-Abschnitts): `**Abgabe: [Tag] [Datum], 18:00** im Hub → Lernen → Modul N → Abgaben.`
- **Sprache:** Deutsch, du-Form, keine Gedankenstriche (kein — und kein –), Komma/Doppelpunkt/Punkt stattdessen. Komposita-Bindestriche sind okay.
- **Hausaufgaben-Regeln:** (a) nicht an Claude delegierbar, (b) echter Nutzen für die vRv-Vorbereitung, nicht Trockenübung, (c) in 45 bis 90 Minuten machbar, (d) eine freiwillige Extra-Aufgabe ist erlaubt und wird als solche markiert.

## Copy-paste-Vorlage

```markdown
# Modul N · [Thema]: Handout & Hausaufgabe

> Session N · [Referent] · Abgabe: [Tag] [Datum], 18:00 im Hub

## Falls du nur 5 Minuten hast

[3 bis 5 Kernaussagen als ein kompakter Absatz. Was muss hängen bleiben,
wenn jemand nur diesen Abschnitt liest?]

## Spickzettel

### [Teil 1 des Decks]
| Begriff | In einem Satz |
|---|---|
| [Begriff] | [Erklärung] |

### [Teil 2 des Decks]
[Tabellen oder Listen, frei nach Stoff]

## Hausaufgabe

**Aufgabe A · [Name] (ca. XX min)**
1. [Schritt]
2. [Schritt]

**Aufgabe B · [Name] (ca. XX min)**
1. [Schritt]

**Extra (freiwillig, +XX min):** [Aufgabe]

**Abgabe: [Tag] [Datum], 18:00** im Hub → Lernen → Modul N → Abgaben.

## Warum ohne Claude

[Zwei, drei Sätze: warum kann nur die Person selbst diese Aufgabe machen,
und was bringt sie dem Team fürs vRv-Projekt?]
```

## Hochladen

Hub → Lernen → dein Modul → **Material**: die `.md`-Datei bei "Handout (Markdown)", das PDF bei "Handout (PDF)". Ein neuer Upload ersetzt die alte Version. Die Buttons "Handout" und "PDF" erscheinen danach automatisch auf deiner Modul-Karte.
