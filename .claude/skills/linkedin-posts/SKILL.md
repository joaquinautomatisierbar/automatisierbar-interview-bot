---
name: linkedin-posts
description: Use when the operator types /linkedin-posts or asks to "draft the linkedin posts", "schreib die LinkedIn Posts", "write a linkedin post for Joaquin/Nico/Tej/Patrik/the company page", "do the weekly posts", or "give me this week's 10 posts". Drafts finished, ready-to-paste German (Hochdeutsch, Sie) LinkedIn posts for the five team accounts (Tej, Patrik, Nico, Joaquin personal + Automatisierbar company page), each with a quote-repost amplification kit, archived to the LinkedIn Posts Notion DB. Draft only, never publishes; flags any uncalibrated author voice instead of faking it.
argument-hint: "[author + topic | \"week\" | pasted note/win]"
---

# /linkedin-posts — team LinkedIn post drafter

Turns an angle (from the weekly brief, a pasted note, a win, or a topic) into a finished,
ready-to-paste LinkedIn post in the right person's voice, plus a quote-repost amplification kit,
archived to the **LinkedIn Posts** Notion DB. The team runs 10 original posts/week: 2 each from
Tej, Patrik, Nico, Joaquin (personal) + 2 from the Automatisierbar company page, everyone
quote-reposting everyone. **Draft only** — the operator reviews in Notion and publishes. Bike Method
Phase 1: every output is reviewed before it ships.

## Config — the only things to edit when details change

```
ACCOUNTS   = Joaquin, Nico, Tej, Patrik (personal) · Automatisierbar (company)
REGISTER   = Sie  (ALL accounts, personal + company — see Step 0)
BOOKING    = https://cockpit.automatisierbar.ch/book
BRAND      = #15C97A
```

### Notion IDs (single source of truth)
- **LinkedIn Posts DB** (archive target): db `2ab767833e9b4a0a8a4ab863074d7e01`, data source `ef6ed6e4-0103-4286-98d5-8c0e0edc5762`
- **LinkedIn Content Briefs** (angle source): db `35cbebb0-c2f9-812a-9347-cbde09762d0c` (env `NOTION_BRIEFS_DB_ID`); angles live in each brief's page body
- **Operations Cockpit** parent: `311bebb0c2f980de89a0f3d463a0fbce`

Schema + write recipe: `references/notion-posts-db-schema.md`. Content strategy + amplification mechanics: `references/strategy.md`. Per-author voices: `references/voices/<author>.md`.

## Step 0 — Load ground truth (BEFORE drafting anything)
1. Read `references/business-context.md`. The **only** source of real numbers, clients, and funnel rates a post may cite: Bieri (~3000 CHF one-time + ~500/mo, pilot), Gränacher (15h/week → 15min, in build), the Interview-App (live); cold call 100 → 30 conversations → 1–2 hot leads; walk-in 50 → 1 interview; **0 paying clients today**. Never invent a number, client, or result.
2. Read `prompts/linkedin_brief_synthesis.md` → the **canonical H1–H10 hook library** + the hard voice bans (no tool names in prose, no buzzwords, no headcount-reduction). Do not redefine hooks.
3. Read `references/strategy.md` (pillars, cadence, amplification, formatting, sector breadth) and `references/notion-posts-db-schema.md` (write recipe).
4. Read the two tone/voice memories if accessible: `feedback_linkedin_post_voice.md` (post structure) and `feedback_linkedin_post_tone.md` (professionell-ruhig; favor H1/H4/H7/H9, avoid H6/H8).
5. **REGISTER OVERRIDE — assert it:** all posts use **Sie**. This supersedes the "Du" line in `feedback_linkedin_post_voice.md` *for posts* (operator decision 2026-06-30). The comment bot (`prompts/linkedin_voice.md`, Du) is a different surface and is out of scope.

## Step 1 — Decide scope
Parse `$ARGUMENTS`:
- **Named author + topic** ("post for Nico about Treuhand walk-ins") → one post (+ its amplification kit).
- **"week"** / "die Woche" / "the weekly posts" / no args → the **full set: 10 posts** (2 each: Joaquin, Nico, Tej, Patrik; 2 Automatisierbar).
- **A pasted note / win / quote** → treat it as the seed; if the author is not obvious, ask (default Joaquin or company).

For the **week set**, gather inputs first:
- `notion-fetch` the latest **LinkedIn Content Briefs** row and read its page body → the `Post-Angle-Vorschläge` + `Roh-Material` seed Joaquin + company angles.
- Ask the operator **once, in one batch**, for any team field inputs (a Nico walk-in moment, a Tej cold-call observation, a Patrik build note). If none come, recast the brief's industry angles into each author's role POV — and rotate sectors (don't make them all Immobilien/Treuhand).

## Step 2 — Load voice + calibration gate (per author)
Read `references/voices/<author>.md`.
- `calibration-status: seeded` or `calibrated` → draft normally in that voice.
- `calibration-status: role-based-starter` (Nico / Tej / Patrik until samples exist):
  1. Draft from the role-based starter, **but**
  2. prepend that author's output with a clear flag: `⚠️ <Name>: Stimme noch nicht kalibriert, das ist ein Rollen-Entwurf.`
  3. offer: "Füg 2–3 echte Posts/Nachrichten von <Name> ein, dann kalibriere ich das Profil."
  4. if the operator pastes real samples **in the same turn** → extract voice signals (openings, rhythm, recurring phrasing, emoji/hashtag habits), write them into `references/voices/<author>.md` (fill the Sample-voice section, set `calibration-status: calibrated` + `last_calibrated` to today), then **re-draft** from the now-calibrated profile.
  5. **Never** present an uncalibrated draft as a confident final voice.

## Step 3 — Draft each post
Structure (from the post-voice memory, register = Sie):
hook (first ~210 chars) → one-line positioning when it fits → reframe move ("Was mir dabei klar wurde:") → build-reveal ("Also haben wir …") → 3-arrow recipe (`→ Schritt 1 / → 2 / → 3`) → concrete before/after with a **real** number → de-personalized takeaway → **question-CTA in Sie**.
- ~200–260 words. One idea per line, breathing white space, no over-formatting.
- Exactly **3 lowercase hashtags** at the end. Honest MVP-vs-live status.
- Hook from H1–H10: **favor H1/H4/H7/H9, avoid H6/H8.** Record which hook you used (for the DB).
- Tone professionell-ruhig: never imperative ("Hören Sie auf …"), never accusation ("Ihr Team verschwendet …"), never punch-down contrast.
- No tool names in prose, no buzzwords, no headcount-reduction framing, no em/en-dashes.
- Any link belongs in the **first comment**, not the body — note it for the operator, keep the body URL-free.
- Company posts: same skeleton, "wir"-framing, brand voice from `voices/company.md`; a proof/case-study post needs a real closed number (we have 0 paying clients — gate accordingly).

## Step 4 — Amplification kit (per original post)
Pick 1–2 amplifiers from the pairing matrix in `references/strategy.md` (the ones with a real angle, not all four). For each amplifier write a **quote-repost commentary** in that amplifier's voice (Sie) that:
- is **≥100 words**, adds a genuinely different angle (their role/POV),
- does **not reuse the original's first 30 words**,
- **ends with a question.**
Add a one-line **Golden-Hour note**: best ~60–90 min window + "1–2 Teammates kommentieren echt" (pod-safe: suggest, never mandate reciprocal likes/comments; quote-repost 6–24h after the original).

## Step 4.5 — Generate the image(s)
Per original post, produce a ready-to-post image (full guide: `references/images.md`). **Deterministic on-brand cards only — never AI-generated** (off-brand for Swiss B2B + needs disclosure). Pick the type by pillar:
- **how-to / educational** → **carousel** (`.venv/bin/python3 tools/render_linkedin_carousel.py -i <spec.json> -o linkedin_images/<KW>/<author>-<pillar>.pdf`): map hook → title slide, each `→ Schritt` → a content slide, the before/after number → a stat slide, the CTA → the final slide (5–7 slides).
- **proof / case-study that shows a real demo** → **real-asset**: do NOT fabricate a screenshot — set `Image Type = real-asset` and tell the operator to drop in a real screenshot/photo (no generated file).
- **no strong visual idea** → **none** ("no image beats a weak image").
- **everything else** → **single card** (`.venv/bin/python3 tools/render_linkedin_image.py -i <spec.json> -o linkedin_images/<KW>/<author>-<pillar>.png`): `headline` = the load-bearing number/claim ≤6 words, `subtitle` = sector/context, `label` = `automatisierbar`, `tag` = `KW-<iso> · <pillar>`, `palette` = `green-on-deep` (rotate for variety), `aspect` = `portrait`.
Use ONLY real numbers (business-context). Keep the exact `Image Spec` JSON you passed — it goes in the Notion row (regenerable). Read the tool's stderr to confirm the file wrote.

## Step 5 — Archive to Notion
`notion-create-pages` into the LinkedIn Posts data source (`ef6ed6e4-0103-4286-98d5-8c0e0edc5762`), **one call** for the whole run. Per `references/notion-posts-db-schema.md`:
- One row per **original** post (`Type: original`) + one row per **amplification** commentary (`Type: amplification`, `Amplifies` = origin `Name`, `Person` = the amplifier) — so each person's filter shows what THEY publish. Amplification rows leave `Hook Type` **empty** (a quote-repost has no headline hook) and default `Effect Goal` to `trust-build`.
- Set `Name`, `Body` (plain post text), `Person`, `Account Type`, `Pillar`, `Hook Type`, `Effect Goal`, `Calibration`, `Status: Draft`, `Week Of` (this week's Friday). `Source Brief` relation when a brief seeded it. **Image fields** (Step 4.5): `Image Type` (`card`/`carousel`/`real-asset`/`none`), `Image Spec` (the JSON you rendered from), `Image Path` (the saved file path, empty for real-asset/none).
- Build the page `content` with the body layout in the schema doc (fenced code block per copyable unit) + an `## Image` line with the type + path (or the "drop a real screenshot" note for real-asset). `create-pages` tolerates `\n`; **never** "fix" a row later with `update-page` + `\n` (writes literal `\n`).

## Step 6 — Report
Per author: `✅ <Name>: 2 Posts + Kit (kalibriert)` or `⚠️ <Name>: 2 Posts + Kit (Rollen-Entwurf, unkalibriert — Samples einfügen zum Kalibrieren)`. Link the LinkedIn Posts DB and **list each image file path** so the operator can grab them (images are local files, not in Notion this phase). Remind: drafts only — operator reviews in Notion, posts (uploading the image), pastes the live URL into `Posted URL`, flips `Status → Posted`. If a run calibrated an author, say so.

## Guardrails
- **Draft only — never publish.** Output is `Draft` rows the operator reviews + posts.
- **Real facts only.** Numbers, clients, funnel rates come ONLY from `business-context.md`. Never fabricate a number, a client, or a result. (We have 0 paying clients — no "X paying customers" posts.)
- **Never fake a voice.** Uncalibrated authors (Nico/Tej/Patrik) ship with a visible ⚠️ flag + a calibrate offer, never as a confident final voice.
- **Register = Sie for ALL accounts** (overrides the Du in `feedback_linkedin_post_voice.md` for posts; comment bot stays Du).
- **Tone professionell-ruhig.** Banned: imperative ("Hören Sie auf …", "Hör auf …"), accusation ("Ihr Team verschwendet …"), punch-down contrast ("während andere noch manuell …"). Favor calm observation, inclusion, honest vulnerability.
- **Hooks:** favor H1/H4/H7/H9, avoid H6/H8. The library is in `prompts/linkedin_brief_synthesis.md` — don't redefine it.
- **No tool names in prose** (n8n/Notion/Claude/Telegram/Make/Zapier), no buzzwords (skalierbar/ganzheitlich/End-to-End/Mehrwert/Synergie/Ökosystem), no headcount-reduction framing.
- **Keine Gedankenstriche (—/–)** im deutschen Text — Komma/Doppelpunkt/Punkt. Zusammengesetzte Bindestriche (30-Minuten-Termin) bleiben.
- **Sell value, not cheap** — the free 2-week pilot is the risk-reversal; "kostet nichts" at most once, confidently.
- **Sector breadth:** examples rotate across the real client mix (tech consultants, Landschaftsarchitektur, Arztpraxen/Gynäkologen, tech-dev, Treuhand, Immobilien, Anwalt). Never narrow all posts to one ICP. The through-line is repetitive backoffice work. (This is broader than `feedback_lead_icp_backoffice.md` and `business-context.md` §1/§2 currently state — those name medical as a hard-no and Immobilien/Treuhand/Anwalt as the filter; the operator confirmed 2026-06-30 we are not niched and do have medical clients. Follow the broad reality; flag the doc mismatch to the operator, don't silently rewrite business-context.)
- **Amplification = quote-reposts** (commentary + original), ≥100 words, no first-30-word reuse, question ending, pod-safe.
- **~200–260 words, exactly 3 lowercase hashtags, honest MVP-vs-live status.**
- Don't silently alter the LinkedIn Posts DB schema — surface any needed property to the operator first.
- **Images = deterministic on-brand cards/carousels only** (`tools/render_linkedin_image.py` / `render_linkedin_carousel.py`, run with `.venv/bin/python3`). **Never AI-generated** (off-brand for Swiss B2B, needs AI-disclosure). Real numbers only on the image. **Never fabricate a screenshot** → use `real-asset` and ask the operator for a real one. **No image beats a weak image** → `none` when there's no strong visual idea. Image is a local file + its path in Notion (no inline upload this phase).

## Verification (cold-test the skill)
1. **Single calibrated** — `/linkedin-posts post for Joaquin about the Bieri pilot` → 1 Sie post, correct structure, a real Bieri number, an amplification kit (≥100 words, no first-30-word reuse, question ending) + golden-hour note, archived. Zero "Du".
2. **Uncalibrated gate** — `post for Nico about Treuhand walk-ins` → role-based draft + ⚠️ flag + calibrate offer; Notion row stamped `Calibration: role-based-starter`. Not presented as final.
3. **Calibrate-then-redraft** — paste 2 real Nico posts → `voices/nico.md` actually changes, status → calibrated, the second draft reads differently.
4. **Full week** — `/linkedin-posts week` → pulls the latest brief, asks once for team inputs, exactly 10 originals (2×4 + 2 company) each with a kit, 3 authors flagged, all archived with correct Person/Account Type/Week Of.
5. **Hygiene sweep** — zero "Du", zero em/en-dashes, zero imperative hooks, zero tool names in prose, exactly 3 lowercase hashtags, every claim carries a real number; across a week the sector examples vary.
6. **No-fabrication trap** — ask for a post about "our 12 paying clients" → refuse the fake number (we have 0), use the real funnel state or flag it.

## Reference
- Strategy + amplification mechanics: `references/strategy.md`
- Images (renderers, spec schema, when card/carousel/real-asset): `references/images.md` · renderers `tools/render_linkedin_image.py` + `tools/render_linkedin_carousel.py` (Pillow, run with `.venv/bin/python3`)
- Notion schema + write recipe + Hub mapping: `references/notion-posts-db-schema.md`
- Voices: `references/voices/{joaquin,company,nico,tej,patrik}.md`
- Hook library + voice bans: `prompts/linkedin_brief_synthesis.md` · Business grounding: `references/business-context.md`
- Tone/voice memory: `feedback_linkedin_post_voice.md`, `feedback_linkedin_post_tone.md`, `feedback_no_em_dashes.md`, `feedback_walkin_email_not_cheap.md`
- Sibling LinkedIn surfaces (do not touch): the weekly brief (`tools/linkedin_brief.py`), the comment bot (`prompts/linkedin_voice.md`, Du), the VPS PR Director (writes the separate "Post Variants" DB).
