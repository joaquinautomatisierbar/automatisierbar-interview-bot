# LinkedIn content strategy — Automatisierbar team

> Loaded on demand by `/linkedin-posts`. Grounds the drafting in current (2025–26) B2B LinkedIn best-practice + our own business-context. Numbers below are research-backed directional benchmarks, not guarantees.

## The play
10 original posts / week: **2 each** from Tej, Patrik, Nico, Joaquin (personal profiles) **+ 2** from the Automatisierbar company page. Everyone **quote-reposts** each other's posts to amplify reach (reposts are amplification, not part of the 10).

## Why this shape
- **Personal >> company reach** (~5–10x; company-page reach fell 60%+ in 2024–26). So 8 personal + 2 company is correctly weighted: personal profiles are the reach + lead engine; the company page is the credibility/proof surface.
- **2 posts/person/week** sits in the optimal 2–5 band and earns "active" algorithmic status. One strong post beats five mediocre ones. **Patrik's quota is soft** (~5h/week) — one honest post is a fine week.

## Pillars (target mix across the 10)
~50% educational/how-to · 20% perspective/observation (data-grounded, never accusatory) · 15% proof/case-study · 15% human/build-in-public.

Pillar values used in the Notion DB: `build-in-public`, `how-to`, `proof-story`, `industry-observation`, `lesson`, `team-culture`, `announcement`.

Per-author ownership:
| Author | Owns | Raw material |
|---|---|---|
| Joaquin | build-in-public, how-to, proof-story | the weekly brief (his build signals), decisions log |
| Nico | industry-observation (field stories), team-culture | his calls + walk-ins (pasted) |
| Tej | industry-observation ("what N calls taught"), lesson | his calls + learning (pasted) |
| Patrik | build-in-public, lesson (weekend builds) | his learning (pasted) |
| Automatisierbar | proof-story (gated on real proof), industry-observation, announcement | brief + client wins |

## Sector breadth — NOT one ICP
We are not niched. Real clients/pipeline span tech consultants, Landschaftsarchitektur, Arztpraxen/Gynäkologen, tech-dev companies, Treuhand, Immobilien, Anwalt, and more. The shared hook is **repetitive backoffice work worth automating**, not an industry. **Rotate sector examples across a week** — never let all 10 posts skew to Immobilien/Treuhand. (Note: this is broader than `feedback_lead_icp_backoffice.md` and `business-context.md` currently say — see SKILL.md guardrails.)

## Hooks
Use the H1–H10 library — the canonical definitions live in `prompts/linkedin_brief_synthesis.md` (do not redefine them here). **Favor H1 (number), H4 (story), H7 (cocktail-party/term-first), H9 (vulnerability/list).** **Avoid H6 (confession-provocation) and H8 (command)** — Swiss B2B punishes finger-pointing (per `feedback_linkedin_post_tone.md`). The DB stores the chosen hook as `Hook Type` (H1…H10).

## Formatting rules (enforced on every draft)
- **Hook in the first ~210 characters** (before the "see more" fold). 60–70% never expand — the hook decides reach.
- Body **~200–260 words** (≈ 1,300–1,900 chars). One idea per line, breathing white space.
- **No over-formatting** (no unicode-bold per line, no emoji-per-line) — it reads as AI and gets skipped.
- **Links go in the first comment, not the body** (body links cost ~18–50% reach). The post body has no URL; note the link for the operator to drop as comment #1.
- **Soft CTA only**: a genuine question or "schreiben Sie mir", never a hard pitch.
- Exactly **3 lowercase hashtags** at the end. Honest MVP-vs-live status. Sie. No em/en-dashes.

## Amplification (the "everyone reposts everyone" mechanic, done right)
- Use **quote-reposts with 100+ words of unique commentary**, never bare 1-click reposts. A quote-repost with real added perspective gets ~4x a bare repost and reads as near-original.
- Each amplifier's commentary must: (a) **not reuse the original's first 30 words**, (b) add a genuinely different angle (their own POV/role), (c) **end with a question**, (d) be in that amplifier's voice + Sie.
- **Pairing matrix** (pick 1–2 amplifiers per post, the ones with a real angle):
  | Original by | Natural amplifiers | Angle they add |
  |---|---|---|
  | Joaquin (build/proof) | Nico, company | Nico = the field/client side; company = the proof framing |
  | Nico (field story) | Joaquin, Tej | Joaquin = what it means for the build; Tej = the call-front echo |
  | Tej (calls/learning) | Nico, Joaquin | Nico = closing side; Joaquin = builder's take |
  | Patrik (weekend build) | Joaquin, Tej | Joaquin = the bigger system; Tej = learner solidarity |
  | Company (case-study) | Joaquin, Nico | personal proof voice on top of the brand post |
- **Don't have all four amplify every post** — sample the strongest. Blanket round-robin reads as a pod.
- **Golden hour:** post, then have 1–2 teammates genuinely engage (a real comment, not just a like) in the first ~60–90 min. 3+ early commenters ≈ ~5x amplification. **Pod-safe:** suggest engagement, never mandate reciprocal likes/comments. LinkedIn actively penalizes coordinated pods.
- **Cadence:** quote-repost 6–24h *after* the original (staggered, not instant).

## DACH nuance
Hochdeutsch (no dialect in writing). Proof over hype (Swiss skepticism toward unproven automation claims — lead with a real named number). Data-residency/nDSG visible for the company account. Understated, precise, calm. **Sie** for all accounts.

## Images (every post ships with one — full guide in `references/images.md`)
Research-backed for conservative Swiss/DACH B2B:
- **Format ranking:** document/PDF **carousel** (highest engagement + saves) > single branded **card** > authentic real photo/screenshot > **no image** > weak/generic/AI image. "No image beats a weak image."
- **AI hero images hurt credibility** here (read as generic; LinkedIn now requires AI-disclosure). We use **deterministic, on-brand cards/carousels only** (the terminal aesthetic), never AI generation.
- **Per-pillar default:** how-to / educational → **carousel**; proof/case-study with a real demo → **real screenshot** (don't fabricate one); no strong visual idea → **none**; everything else → **single card**.
- **Specs (handled by the renderers):** single card portrait 1080×1350 (or square 1200×1200); carousel = portrait 1080×1350 PDF, 5–7 slides, ~80px safe margin, one idea per slide, mobile-legible. Headline ≤6 words, number-forward.
- **Real numbers only** on images (business-context). Rotate palettes across the week for variety; `green-on-deep` is the house default.
