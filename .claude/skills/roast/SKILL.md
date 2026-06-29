---
name: roast
description: Use when the operator wants to pressure-test, stress-test, or roast a business idea before building it — offers, pricing, guarantees, a new ICP/wedge, a funnel change, a campaign, a product bet — or says "convene the council", "give it to the council", "brutal second opinion", "should I build this", or "/roast". Spins up a 5-persona adversarial council (Contrarian, Expansionist, Logician, Researcher, Buyer) grounded in our own business-context + distilled library, then a Judge returns one GO / RESHAPE / KILL verdict tied to a KPI bucket plus the cheapest 48-hour test to de-risk it. The adversarial front-door before /level-up scopes the build.
argument-hint: "[the idea to roast]"
---

# Roast — the grounded adversarial council

## What this does

Claude's default is to agree with you. `/roast` is the opposite. It convenes five independent persona agents who tear an idea apart from every angle, then a Judge synthesizes one honest verdict. Use it before sinking time and money into the wrong thing.

What makes this version different from a generic roast: it is **grounded in our stack**. Every persona judges against our real funnel numbers, our actual ICP, our pricing hypothesis, and our distilled library of named frameworks — not generic SaaS templates. The verdict ties to one of our three KPI buckets and can be logged to `decisions/log.md` in our format.

`/roast` is the pre-step to `/level-up`: roast decides *whether* an idea is worth pursuing; `/level-up` scopes *what to build* once it survives. A surviving idea's KPI bucket + cheapest-test feed straight into level-up's Method phase.

The council is adversarial on purpose. No persona hedges or stays polite. The point is to surface what you can't see because you're too close to it.

## Step 0 — Load the ground truth (do this BEFORE anything else)

1. **Read `references/business-context.md`.** Extract: the offer & pricing hypothesis (§1), ICP + wedge/spray stance (§2), current funnel rates (§3), team capacity, 6-month targets (§7), strategic priors (§6), and open questions (§9). Note `last_updated` against the `review_cadence` (every 2 weeks). If the doc is stale, don't silently trust it — carry that caveat into the Judge's verdict.
2. **Route to the library** if the idea touches offers/pricing/leads/sales/retention/positioning/validation. Per `.claude/skills/library/SKILL.md`, load **at most 2** `references/library/*.md` topic files and skim their `## Frameworks` sections. For exact wording, you may run `.venv/bin/python tools/library_search.py "<question>" --k 5`. If nothing maps cleanly, skip the library — don't force-fit.
3. **Compose one grounded brief block** (see Step 1) that contains the idea + the extracted business facts + the relevant named frameworks. This same block gets pasted into all five personas so they judge the same thing against the same reality.

## Step 1 — Get the brief

If `$ARGUMENTS` contains the idea, start there. Then ask a tight set of clarifying questions — but **pre-fill from `business-context.md` and do NOT re-ask what we already know.** We already know: ICP is Swiss-German KMU (10–200 staff, backoffice/process pain); motion is cold outreach → workflow interview → pre-built automation → free 2-week pilot → conversion conversation; pricing hypothesis is one-time build fee + monthly retainer; Joaquin is the sole shipping builder at limited hours; zero pilot→paying conversions logged yet.

Ask only the genuinely missing pieces (max 3, one batch). Typically:
1. **What's the actual bet** in one or two sentences (the change being proposed, vs. what we do today)?
2. **What's the trigger** — what made this come up now (a lost deal, a pilot result, a competitor, a hunch)?
3. **What does winning look like** — what number should move, and by when?

If the operator says "just run it," skip the questions and proceed with the brief as-is. Don't over-interrogate. One round, then convene.

Write the final brief into a single short block. It MUST include: (a) the idea in one paragraph, (b) the 4–6 most relevant grounded facts from Step 0 (funnel reality, ICP, pricing hypothesis, capacity constraint, target), and (c) the 1–2 named frameworks pulled from the library, if any. Paste this identical block into all five council members.

## Step 2 — Convene the council (5 agents, in parallel)

Spin up **all five agents in parallel in a single message** (one `Agent` call each, `subagent_type: general-purpose`). Paste the same grounded brief into each, then give each its persona mandate below.

Each council member must return: a one-line stance, their 3–5 sharpest points, the single most important thing the operator must hear, and a 1–10 score on their own dimension (1 = walk away, 10 = no-brainer).

**1. The Contrarian (Red Team)**
> You are the Contrarian on an idea council for a Swiss automation agency (Automatisierbar). Assume this idea fails. Find the fatal flaws, the fastest way it dies, and the load-bearing assumptions that are probably wrong — judged against the agency's CURRENT reality in the brief: zero pilot→paying conversions logged yet, a single shipping builder at limited hours, no proof assets / case studies, untested pricing. Be ruthless and specific. No hedging, no "but it could work." Attack the weakest points. THE BRIEF: [brief]

**2. The Expansionist (Bull)**
> You are the Expansionist on an idea council for a Swiss automation agency (Automatisierbar). Make the strongest possible case FOR this idea — but a case that fits the agency's REAL capacity and 6-month targets in the brief, not a fantasy 10x. Find the biggest realistic upside, the adjacent unlocks, the leverage the operator isn't seeing given what they already have (n8n stack, walk-in motion, library of frameworks). Be specific about where the real money and leverage could be. THE BRIEF: [brief]

**3. The Logician (First principles)**
> You are the Logician on an idea council. Use NO outside research and NO web. Reason purely from first principles: does the core mechanism make sense, do the incentives line up, does the unit math even work in theory given the pricing hypothesis and funnel numbers in the brief? Strip it to fundamentals and tell us if it holds together. THE BRIEF: [brief]

**4. The Researcher (Evidence + frameworks)**
> You are the Researcher on an idea council. Use web search for real-world evidence: comparable Swiss/DACH automation agencies or competitors, what comparable services charge, demand signals, whether this is validated or contradicted by what's already out there. ALSO apply the named frameworks included in the brief (e.g. Hormozi's Value Equation, Core Four, CLOSER, the Proof Checklist) and judge the idea against them, citing framework + source. Cite what you find. Is the real world — and the playbook — saying yes or no? THE BRIEF: [brief]

**5. The Buyer (Voice of customer)**
> You are the Buyer on an idea council. Role-play the EXACT target customer: the owner or operations lead of a Swiss-German-speaking KMU (10–200 employees) with repetitive backoffice work. React as them, in first person. You may answer in German for authenticity (Hochdeutsch, Sie-Form). IMPORTANT: if you write in German, use NO em-dashes or en-dashes (—, –) anywhere — use commas, colons, or periods instead; keep normal compound hyphens (e.g. 30-Minuten-Termin). Would you actually pay for this? What's your real objection? What would make you choose a competitor or just keep doing it the old way? What price feels right, and what would make you say yes? Be the honest, slightly skeptical buyer, not a cheerleader. THE BRIEF: [brief]

## Step 3 — The Judge delivers the verdict

Once all five return, YOU act as the Judge. Read every council member's findings, weigh them, and synthesize one decisive verdict. Do not just average the scores. Name the real tension between the personas and resolve it.

Fold in the **economics lens** yourself, grounded in our actual numbers — not generic pricing. Use the real pricing hypothesis (one-time build fee + monthly retainer; the Bieri reference ~3000 CHF + ~500 CHF/month), the real funnel (100 calls → ~30 conversations → 1–2 hot leads; 50 walk-ins → ~1 interview; pilot→paying still TBD), and the real capacity constraint (sole builder, limited hours).

Output the verdict in this exact shape:

```
## THE VERDICT: GO / RESHAPE / KILL
Confidence: [low / medium / high]

**The call in one line:** [the decision, plainly]

**Why:** [2-3 sentences resolving the council's tension]

**KPI bucket:** [exactly one of: Get more customers / Make each customer worth more / Cut costs]
**Metric it moves:** [the specific number — e.g. pilot→paying conversion rate, hot-leads/week, build hours per pilot]

**Biggest risk:** [the single thing most likely to kill it]
**Biggest upside:** [the strongest reason to do it]

**Money read:** [grounded in our real pricing + funnel: rough revenue impact, realistic time-to-first-dollar, whether the sole builder can ship it fast]

**The cheapest 48-hour test:** [the smallest, fastest thing to validate the riskiest
assumption BEFORE building anything — prefer tests that ride our existing motion
(a walk-in batch, a handful of cold calls, one pilot tweak) over net-new infra]

**If RESHAPE:** [the specific pivot that fixes the fatal flaw while keeping the upside]

**Caveats:** [if business-context.md was stale, or a key number was TBD, say what the verdict is blind to]
```

Then list the five council scores in one line: `Contrarian X/10 · Expansionist X/10 · Logician X/10 · Researcher X/10 · Buyer X/10`.

## Step 4 — Offer to log the decision (confirm before writing)

After the verdict, **offer** to append it to `decisions/log.md`:

> "Want me to log this verdict to decisions/log.md?"

- **Default is chat-only.** Do NOT write to `decisions/log.md` (or anything else) unless the operator says yes. This respects the halt-before-acting policy in `CLAUDE.md` — strategic writes are confirmed, never automatic.
- **On a yes,** append one entry in the file's exact format (use today's date):

```
## YYYY-MM-DD — [Roast] <short title>

**Decision:** <the GO/RESHAPE/KILL call in one line>

**Why:** **Bucket: <Get more customers | Make each customer worth more | Cut costs>.** **Metric: <specific metric>.** <2-3 lines of reasoning grounded in the framework + funnel reality that drove the verdict>

**Alternatives considered:** <what the idea originally was, or the rejected variants>

**Owner:** Joaquin
```

Keep the bold **Bucket:** and **Metric:** callouts — the log treats them as first-class (see the Lead Scraper v2 entry as the model). Three lines per field max.

## Rules

- **Always run Step 0 first.** A roast that isn't grounded in our funnel/ICP/pricing is just generic chat — that's what we're replacing.
- Every persona stays in character. None hedges or softens. The value is in the friction.
- The Judge must make an actual call. "It depends" is not a verdict. Pick GO, RESHAPE, or KILL and own it.
- **The KPI bucket + metric are mandatory** in the verdict (mirrors `/level-up` and `operator-principles.md` §8). If the idea can't be tied to a number, that itself is a strong KILL/RESHAPE signal — say so.
- The cheapest 48-hour test is the most important output. Prefer tests that ride our existing motion (walk-ins, cold calls, an active pilot) over building anything new.
- Cite library frameworks by name + source when the Researcher or Judge leans on them ("per Hormozi's Value Equation in *$100M Offers*").
- **Never write without confirmation.** Chat-only by default; `decisions/log.md` only on an explicit yes.
- Keep the final verdict skimmable. The council does the depth; the Judge does the decision.

## Verification (cold-test cases)

- **Grounded happy path.** `/roast retainer-only pricing for the pilot`. Expected: loads business-context (references ICP/funnel/zero-conversions), pulls `offers-and-pricing.md` with a cited framework, spawns 5 council agents in parallel, Judge returns GO/RESHAPE/KILL + a named KPI bucket + metric + a cheapest-test that uses the existing pilot, + the 5-score line.
- **No-args cold test.** `/roast` with no idea. Expected: asks the ≤3 clarifying questions but does NOT re-ask facts already in business-context (must not ask "who is your ICP" or "how do you price").
- **Logging gate.** After any verdict, expected: offers to log and does NOT touch `decisions/log.md` until the operator says yes; on yes, the appended entry matches the file format (date header, bold Bucket + Metric, Owner: Joaquin).
- **German hygiene.** If the Buyer answers in German, expected: no em-dashes/en-dashes anywhere in that copy.
- **Stale-context flag.** If `business-context.md` `last_updated` is well past the 2-week cadence, expected: the verdict's Caveats line says what it's blind to rather than trusting stale numbers.
