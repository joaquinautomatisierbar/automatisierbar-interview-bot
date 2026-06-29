---
name: storm
description: Use BEFORE building or executing something, when the operator wants deep, current, multi-angle research to ground the approach — e.g. "before we build X, research the best way to do it", "optimize our SEO, but first go deep on it", "we need a website that converts, research that first", "research the best approach for <new project/feature/tool> before we start", or the operator types /storm <topic>. Runs a STORM pipeline: 4-6 expert lenses research in parallel → contradiction map → synthesis grounded in our business context → adversarial peer review + primary-source verification → a markdown research dossier in research/ that the agent reads before building. Best when the right approach is non-obvious and getting it wrong is expensive. Overkill for a simple factual lookup.
argument-hint: "[topic to research before building]"
---

# STORM — pre-build research

Turns one topic into a **verified, multi-perspective markdown dossier we read before building**. It simulates several expert lenses on the topic in parallel, maps where they contradict each other, synthesizes a recommended approach grounded in our stack + business context, then adversarially peer-reviews its own findings and verifies every citation against its primary source. The output is one `research/<slug>-<date>.md` file with no obvious blind spots and no unchecked claims — built to make the *next* build session pick the best available approach.

Run the full pipeline end to end. Do not shortcut a phase. This is heavier than a quick web lookup — that is the point. Adapted from the STORM method (Stanford) via the storm-research skill in `reference/storm-research-SKILL-original.md`, reskinned for pre-build research with build-oriented lenses, markdown output, and our grounding.

## What this skill is NOT

- **Not `/level-up`.** `/level-up` scopes *one* automation to build. `/storm` produces the research that a build session (or `/level-up`) executes against. Research first, then build.
- **Not the plugin `deep-research`.** That's a single-pipeline web harness. STORM is multi-lens + contradiction-mapped + adversarially verified, and grounded in *our* business.
- **Not an HTML briefing for the operator to admire.** The dossier is build-grade input for the agent. Markdown, recommendation-first, dense, sourced. No styling.
- **Not a factual lookup.** If the answer is one fact, just answer it — don't spin up the council.

## Inputs the skill reads (for "tailored to us")

- `references/business-context.md` — stack lock-in, ICP, team capacity, constraints, targets. Always read this; it makes "Build implications for us" real.
- `references/library/INDEX.md` + the relevant topic file(s) — only when the topic touches offers/leads/conversion/positioning/retention (e.g. "website that converts" → hooks, value equation, proof). Max 2 library files per run; cite source + framework.
- The operator-provided project/topic context, and any open `decisions/log.md` entry the build relates to.
- `reference/storm-research-SKILL-original.md` — the donor prompts (classic-5 preset + verify-agent wording).

## Execution — six phases

### Phase 0 — Scope

1. If `$ARGUMENTS` has the topic, use it. Otherwise ask what we're about to build.
2. State your one-line interpretation and **proceed** — only ask a clarifying question if the topic is genuinely ambiguous in a way that changes the research. Default to proceeding (do not block on questions).
3. Capture the **intent/reader**: name what this research will be used to *build* and for whom (default: "a builder on the Automatisierbar team about to build this"). The "Recommended approach" and "Build implications" sections target this.
4. Read `references/business-context.md` now (and any relevant `references/library/` file if the topic is marketing/conversion-shaped).
5. Derive a kebab-case `topic-slug` for the filename.
6. Pick the council (see **The council** below — default build set unless the topic is strategy/abstract).
7. One-line note in chat: "Running STORM — N lenses in parallel, then verify."

### Phase 1 — Fan-out (parallel lenses)

Spawn the council as **subagents in a single message** so they run concurrently — use the `Agent` tool with `subagent_type: general-purpose` (each has `WebSearch` + `WebFetch`). Give every lens the same `{TOPIC}` + one-line `{TOPIC_FRAME}` (your Phase 0 interpretation), plus its own lens prompt from **The council**.

Every lens returns the **same strict contract**:
1. **CORE POSITION** in 2 sentences (the approach/answer from this lens).
2. **STRONGEST EVIDENCE** — 3-5 bullets, each a concrete data point / tactic / case / benchmark + named source + **URL**.
3. **THE ONE THING** only this lens would tell someone about to build this.
Under ~400 words. **Real, fetched sources only — no invented studies, numbers, or URLs.** Prioritize *recent* sources (last ~12-18 months) — we want the best approach available *now*.

When all lenses return, post a 2-3 line note in chat: which way they converge + the sharpest disagreement. Keep the raw briefs out of chat (the agents already returned them).

### Phase 2 — Contradiction map (inline, no agents)

Working only from the lens briefs, determine:
1. **Direct conflicts** — where two+ lenses claim opposite things. Name the specific clashing claims, not just topics.
2. **Strongest vs weakest evidence** — rank by source hierarchy: *independent/peer-reviewed data > official/first-party data > single benchmark or case > vendor claim > anecdote/analogy*. Say which lens is best-supported and which is weakest, with why.
3. **The resolving question** — the single empirical question that would settle the biggest contradiction.
4. **Universal agreement** — what every lens confirms, even ones that disagree elsewhere. This is the load-bearing, likely-true finding.
5. **The blind spot** — what NO lens addressed. Becomes the "missing lens" + an open question.

This map is raw material for the dossier, not a separate deliverable.

### Phase 3 — Synthesis (grounded + tailored)

1. **Recommended approach** — the bottom line: the best way to build/execute `{TOPIC}` right now, given current best practice + our context. Concrete, ordered, opinionated.
2. **Reliability-ranked key findings** — the most important things now known, highest reliability first. Each carries a 1-10 reliability score (set in Phase 4), supported-by / challenged-by lenses (from the contradiction map), and a source. **Reliability = evidence quality, not how confident a lens sounded** — score on the source hierarchy.
3. **Build implications for us** — translate the findings into concrete next steps for *our* stack/ICP/constraints (read from `references/business-context.md`). This is the part a build session acts on.
4. Note where a `references/library/` framework applies, cited (framework + source).

### Phase 4 — Verify (do not skip)

This is what separates STORM from a normal report. Run it before writing the dossier.

**4a. Self-review (inline).** Score each key finding 1-10 for reliability and justify. Identify the weakest link and what would verify it. Run a bias check (which lens dominated the synthesis, what got underweighted). Name the missing lens. Assign an honest overall grade.

**4b. Verify citations (parallel agents).** Spawn `general-purpose` agents in one message, one per **citation cluster** (group related claims; ~4-6 agents). Each agent prompt (adapted from the donor):

> Independently verify a claim against its PRIMARY source. Be skeptical; do not trust secondary blog summaries or vendor marketing pages. CLAIM: {claim + cited figure/fact + named source + URL}. Find and read the actual primary/authoritative source. Confirm or correct: the real figure/fact as stated at source; the source's title/author/org/date; the basis (independent data, single benchmark, vendor claim, anecdote?); and whether it is current or outdated. For any contested claim, find the strongest credible counter-source. Return: VERDICT = CONFIRMED / PARTIALLY CONFIRMED (list corrections) / UNVERIFIED / FALSE, then the corrected one-line citation with URL, then 2-4 bullets of specifics. Under 280 words.

**4c. Apply corrections.** Before writing the dossier: fix wrong figures/titles/dates/mischaracterizations; downgrade reliability scores where evidence turned out thin; demote vendor/single-source/contested claims into a "Contested signal" note; re-attribute commissioned or single-survey stats honestly; fill a **truthful** verification banner (`N checked, X corrected, Y demoted`) and per-source status tags.

### Phase 5 — Write the dossier

Write to `research/<topic-slug>-YYYY-MM-DD.md` (create `research/` if missing). Use today's date. Then report inline (tight): the file path, the verification tally, the one universal finding, the recommended-approach paragraph, and the open/missing-lens question — and offer "want me to add a lens and run V2?".

## The council

Default = the **build set** (oriented to "what's the best way to build/execute X right now"). Pick 4-6 per topic; add the Architect lens for anything that touches our stack. Lenses are editable presets — adding one is the whole point (borrow expertise, kill blind spots).

**Build set (default):**

1. **THE PRACTITIONER** — `You are THE PRACTITIONER for: {TOPIC} ({TOPIC_FRAME}). You build/run this for a living and care only about what actually works in production right now. Do real web research (recent case studies, operator threads, build write-ups, docs, changelogs — prioritize the last 12-18 months). Surface the proven hands-on approach: what top operators actually do, the workflow that ships results, where it breaks, and the gap between hype and field reality. Return EXACTLY: 1) CORE POSITION in 2 sentences (the approach you'd actually use). 2) STRONGEST EVIDENCE, 3-5 bullets, each a concrete tactic/case/benchmark + named source + URL. 3) THE ONE THING only a hands-on practitioner would tell someone about to build this. Real fetched sources only, no invented URLs. Under 400 words.`

2. **THE STATE-OF-THE-ART SCOUT** — `You are THE STATE-OF-THE-ART SCOUT for: {TOPIC} ({TOPIC_FRAME}). Find the current best-in-class approach and tools as of right now, and what changed recently that makes older advice obsolete. Do real web research (recent releases, leading tools/frameworks, "X vs Y 2026" comparisons, what top players shipped lately). Answer: what is the leading-edge approach today, and what's newly possible that wasn't 12 months ago. Return EXACTLY: 1) CORE POSITION in 2 sentences (the modern best-practice approach). 2) STRONGEST EVIDENCE, 3-5 bullets, each a specific tool/technique/release + named source + URL + date. 3) THE ONE THING about doing this the current way vs the outdated way. Real, fetched, recent sources only. Under 400 words.`

3. **THE SKEPTIC** — `You are THE SKEPTIC for: {TOPIC} ({TOPIC_FRAME}). Someone is about to build this; stop them from making the common mistakes. Build the strongest case for what goes wrong. Do real web research for failure post-mortems, "mistakes to avoid", things that demo well but break in practice, hidden costs, and overhyped approaches. Return EXACTLY: 1) CORE POSITION in 2 sentences (the main way this goes wrong). 2) STRONGEST EVIDENCE, 3-5 bullets, each a concrete failure mode/pitfall/cautionary case + named source + URL. 3) THE ONE THING only a battle-scarred skeptic would warn about before building this. Rigorous, not contrarian for sport. Real sources with URLs. Under 400 words.`

4. **THE ECONOMIST / ROI** — `You are THE ECONOMIST / ROI lens for: {TOPIC} ({TOPIC_FRAME}). You care about effort-vs-payoff and prioritization for a small, time-constrained team. Do real web research for costs, pricing, time-to-value, what moves the needle vs busywork, and where the 80/20 is. Answer: what's actually worth doing (and in what order), and what to skip. Return EXACTLY: 1) CORE POSITION in 2 sentences (the highest-ROI path). 2) STRONGEST EVIDENCE, 3-5 bullets, each with a real number/cost/benchmark/effort estimate + named source + URL. 3) THE ONE THING only someone following the money/effort would say about prioritizing this build. Real figures with URLs. Under 400 words.`

5. **THE END-USER / CUSTOMER** — `You are THE END-USER / CUSTOMER lens for: {TOPIC} ({TOPIC_FRAME}). You sit in the seat of the person on the receiving end (the website visitor, the searcher, the user of the thing being built) — the perspective builders most often forget. Do real web research for UX research, what users/visitors/buyers actually want, conversion/behavior data, complaints, what makes them bounce vs convert. Answer: what the end user actually needs for this to succeed, and where builders optimize for themselves instead of the user. Return EXACTLY: 1) CORE POSITION in 2 sentences (what the user needs). 2) STRONGEST EVIDENCE, 3-5 bullets, each a UX/behavior data point or user-research finding + named source + URL. 3) THE ONE THING only someone in the user's seat would say. Real sources with URLs. Under 400 words.`

6. **THE ARCHITECT / INTEGRATOR** *(add for stack-touching topics)* — `You are THE ARCHITECT / INTEGRATOR for: {TOPIC} ({TOPIC_FRAME}). You judge feasibility and fit within our existing stack: n8n, Flask on Render, Notion, Claude API, Telegram, GitHub. Do real web research for integration approaches, APIs/webhooks, maintainability, and what plays well with this stack vs what creates lock-in or ops burden. Answer: how to build this so it fits our stack and stays maintainable. Return EXACTLY: 1) CORE POSITION in 2 sentences (the architecture/approach that fits). 2) STRONGEST EVIDENCE, 3-5 bullets, each a specific integration/API/pattern + named source + URL. 3) THE ONE THING only someone who has to maintain this would say. Real sources with URLs. Under 400 words.`

**Classic-5 preset** (use for abstract/strategy/"is this real" topics, not build-how-to): Practitioner, Academic, Skeptic, Economist, Historian — exact prompts in `reference/storm-research-SKILL-original.md`.

To add a lens: write one more prompt block in the same contract and include it in the Phase 1 fan-out. That's the operator's "spin up a 6th lens, run V2" loop.

## Output: the dossier

`research/<slug>-YYYY-MM-DD.md`, recommendation-first, in this order:

1. **Header** — topic, intent ("research for building X"), date, council used, **verification banner** (`N checked, X corrected, Y demoted`), and a one-line disclosure that the panel is author-built.
2. **Recommended approach (TL;DR)** — the bottom line up front.
3. **Reliability-ranked key findings** — each: claim · reliability (n/10) · supported-by / challenged-by · source URL.
4. **Per-lens summaries** — what each lens surfaced (CORE POSITION + the one thing).
5. **Contradiction map** — conflicts + which side has stronger evidence + the resolving question + universal agreement.
6. **Build implications for us** — concrete, ordered next steps tailored to our stack/ICP/constraints.
7. **Pitfalls / what NOT to do** — from the skeptic.
8. **Source audit** — every citation: CONFIRMED / CORRECTED / DEMOTED, with URL.
9. **Open questions / missing lens** — what wasn't covered + what to research next.

## Guardrails (non-negotiable)

- **Real research only.** Every lens and citation traces to a real, fetched source. No invented studies, numbers, or URLs. If a figure can't be verified, demote or cut it — never paper over it.
- **Verification is mandatory.** A dossier without Phase 4 is not a STORM dossier. The verification banner must be truthful.
- **The panel is author-built.** Disclose it in the dossier. Agreement across our own lenses is a strong hypothesis, not independent field consensus.
- **Reliability = evidence quality, not confidence.** Score on the source hierarchy.
- **Recency is first-class.** Lenses must prioritize current sources; the verify pass guards against stale/hallucinated citations.
- **Hard cost cap.** ~9-11 agents per run (≤6 lenses + one verifier per citation cluster). Do not fan wider. This is bounded + user-invoked, so it fits the Paperclip budget policy — but it is NOT a cheap call; don't run it for trivial lookups.
- **Tailored, not generic.** Always read `references/business-context.md`. A dossier whose "Build implications" could apply to any company hasn't done its job.

## Output contract

Every `/storm` run produces:
1. **One `research/<slug>-<date>.md` dossier** — the 9-section structure above, post-verification.
2. **A tight chat close** — file path, verification tally, the universal finding, the recommended-approach paragraph, the open/missing-lens question, and an offer to run V2 with an added lens.

## Verification (cold-test cases)

- **Trigger test.** "Before we build the new landing page, research the best approach first" and `/storm landing page that converts` both invoke this skill (not a plain web search, not `/level-up`).
- **Real-research test.** Every finding in the dossier has a fetched URL; the verify pass actually changed at least one score or demoted at least one source on a real run (if nothing ever gets corrected, the verify pass isn't doing its job).
- **Tailoring test.** "Build implications for us" references our actual stack/ICP/constraints from `references/business-context.md`, not generic advice.
- **Lens-extensibility test.** "Add an SEO-specialist lens and run V2" works by adding one prompt block to the Phase 1 fan-out and re-running.
- **Restraint test.** A trivial factual question ("what port does Flask default to") gets answered directly, not turned into a 10-agent STORM run.
