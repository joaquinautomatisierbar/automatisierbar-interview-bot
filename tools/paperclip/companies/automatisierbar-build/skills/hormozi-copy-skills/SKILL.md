---
name: hormozi-copy-skills
description: >
  Actionable rules distilled from the Hormozi Hooks Playbook + Leads book +
  Positioning material, applied to B2B personal-brand LinkedIn copy. Used by
  PR Director, Copy Writer, and Hook Strategist in the Marketing department.
---

# Hormozi Copy Skills (LinkedIn personal-brand variant)

The Marketing department writes copy grounded in the Hormozi book library at `~/_context/references/library/`. Don't try to apply every Hormozi framework — this skill picks the subset that actually works for Swiss B2B personal-brand posts to KMU decision-makers.

## What to read

For copy work, you need three files:

1. `~/_context/references/library/leads-and-acquisition.md` — Hooks Playbook (H1-H10 + 121 hook examples), Core Four lead methods, Hook→Retain→Reward arc, 70-20-10 rule
2. `~/_context/references/library/positioning-and-proof.md` — avatar definition, proof asset hierarchy, brand positioning
3. `~/_context/prompts/linkedin_brief_synthesis.md` — Joaquin's specific voice constraints (no buzzwords, Hochdeutsch, Du-Form, numbers-first, max 800 words for briefs)

## Tone constraint (HARD — read this FIRST, before picking a hook)

**No confrontational, imperative, or "zugespitzt" framing.** Learned from real user feedback (2026-05-17, AUT-5): four drafts rejected with "ich mag die linkedin posts nicht, sie sind sehr zugespitzt und unfreundlich". Worst offender: "Hör auf, deine Anwälte für Dokumentenverwaltung zu bezahlen" — imperative + finger-pointing reads as aggressive to Swiss KMU owners and kills trust before it builds.

**AVOID:**

- Imperative openers: "Hör auf …", "Du solltest aufhören …", "Wenn du noch X machst, dann …", "Es ist Zeit, mit X aufzuhören."
- Accusation framing: "Dein Team verschwendet …", "Ihr habt ein Problem mit …", "Das ist nicht akzeptabel."
- Hard contrasts that punch down at the reader's status quo: "während andere noch manuell …", "die Konkurrenz hat das längst gelöst", "deine Mitbewerber sind schon weiter."

**PREFER:**

- Quiet-confident observation: "Letzte Woche bei einer Treuhand-Kanzlei …", "Was uns nach 200 Calls aufgefallen ist …" — story-first, conclusion-implied.
- Inclusive language: "Wir sehen das immer wieder", "Vielleicht kennst du das auch", "Bei uns hat das so funktioniert" — invites reader in.
- Honest vulnerability over provocation: "Wir haben einen Kunden verloren weil …" (H9) lands better than "Hör auf X" (H8).

**Tone target:** "professionell-ruhig" — a calm operator sharing observations, not a challenger trying to provoke a click.

## The Hook Library (H1-H10) — reweighted after AUT-5

Copy Writer must open every post with one of these. **Lean hard on H1/H3/H4/H7/H9; use H2/H5/H6 carefully; H8 NEVER as imperative**. Hook Strategist scores against this:

| Hook | Pattern | Example for our ICP | Weight |
|---|---|---|---|
| **H1** | Concrete number + outcome | "5 Stunden pro Woche. Das ist der Output unserer letzten Treuhand-Automation." | ✅ preferred |
| **H2** | Contrarian / counter-intuitive | "Die meisten Treuhand-Büros automatisieren das Falsche." | ⚠️ careful — must not slip into accusation, frame as our observation not their failure |
| **H3** | Question that surfaces the pain | "Wann hast du das letzte Mal eine ganze Stunde mit Beleg-Sortierung verbracht?" | ✅ preferred |
| **H4** | Story/anecdote opener | "Tej saß letzte Woche bei einer Anwaltskanzlei in Baden, und ihre Eingangs-Mail war im Chaos." | ✅ preferred (story = least confrontational) |
| **H5** | Future-pacing | "In 6 Monaten wirst du nie wieder eine Mahnung manuell schreiben." | ⚠️ frame as observation not promise |
| **H6** | Reverse / "wrong about" | "Ich hatte unrecht über Voll-Automatisierung." | ⚠️ only when WE were wrong about something — never positioning the reader as wrong |
| **H7** | Specific listicle promise | "3 Prozesse, die jede Treuhand-Kanzlei diese Woche automatisieren kann (ohne IT-Projekt):" | ✅ preferred |
| **H8** | Customer-quote citation | "'KMU haben kein Tool-Problem, sondern ein Prozess-Problem' — was wir nach 200 Calls gelernt haben." | ❌ NEVER imperative ("Hör auf X"). Customer-quote framing only. |
| **H9** | Behind-the-scenes / vulnerable | "Wir haben gerade einen Kunden verloren, weil wir zu schnell automatisiert haben." | ✅ preferred for opinion posts |
| **H10** | If/then conditional | "Wenn dein Team mehr als 4h pro Woche mit E-Mail-Triage verbringt, lies das hier." | ✅ neutral, OK |

## Hook → Retain → Reward arc

Every post should follow this 3-beat structure (one beat per ~3 sentences):

1. **Hook** (1-2 sentences) — one of H1-H10
2. **Retain** (2-4 sentences) — the concrete anecdote/story/recipe that pays off the hook
3. **Reward** (1-2 sentences) — the lesson + question-CTA

Skip the arc and the post reads as "an opinion floating in space."

## 70-20-10 rule

Across the 5-7 weekly variants:

- 70% educational (process, recipe, observation, mistake)
- 20% proof (named-customer case study, screenshot, before/after)
- 10% direct/promotional (offer mention — only when there's natural pull)

If you have 7 variants, that's ~5 educational, ~1-2 proof, ~0-1 promotional. Reject more than 1 promotional.

## Voice + format rules (LOCKED)

From `prompts/linkedin_brief_synthesis.md`:

- Hochdeutsch, Du-Form (NEVER Sie except in customer-direct-quote contexts)
- Max 1300 chars per post (LinkedIn allows 3000, engagement drops past ~1500)
- Every post carries ≥1 concrete number (CHF, time, count, %)
- No buzzwords: skalierbar, ganzheitlich, End-to-End, Mehrwert, Synergie, KPI-driven, datengetrieben
- No tool names in prose (n8n, Notion, Claude, Apify, Telegram — those live in Roh-Material section)
- No headcount/FTE replacement framing ("Zeit zurück für Mandantenarbeit", not "ersetzt Mitarbeiter")
- Swiss references OK (Treuhand, Mandantenarbeit, Beleg-Eingang) — Schwyzerdütsch NO
- Question-CTA at the end (no "Tell me in the comments!" — too American)

## Proof asset hierarchy

When choosing what to anchor an anecdote in (most→least powerful):

1. **Named-customer case** ("Anwaltskanzlei Müller in Baden") — strongest, requires Joaquin/Tej OK
2. **Numbered observation across multiple cases** ("In 14 von 18 Treuhand-Interviews war Beleg-Eingang das Problem")
3. **Concrete time/CHF figure from one build** ("4h gespart pro Woche bei CHF 70/h = CHF 1.213/Monat")
4. **General reference to "ein Klient diese Woche"** — weak, use only if you have nothing else

If you can't anchor with at least #3, the post probably isn't worth shipping this week — skip it, save the angle for a future brief.

## What this skill does NOT do

- It does NOT have access to live Notion data — you query Notion via API for the brief content.
- It does NOT generate hooks for you — you pick from the H1-H10 library above using examples in `leads-and-acquisition.md`.
- It does NOT enforce length limits at the API level — you check character counts yourself.
- It does NOT replace `~/_context/prompts/linkedin_brief_synthesis.md` — that's the canonical voice doc; this skill is the additional Hormozi-grounded copy-craft layer.
