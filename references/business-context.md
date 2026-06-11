---
doc: business-context
owner: Joaquin Gamonal
last_updated: 2026-05-04
review_cadence: every 2 weeks
status: v1 — filled, baseline established
---

# Automatisierbar — Business Context

> **Purpose.** Load-bearing context for Claude Code (and any future operator) when answering strategic questions like "should I raise prices," "is this lead a fit," "should I build X workflow next." If a fact would change the answer to a question like that, it belongs in here.
>
> **Maintenance.** Bump `last_updated` and skim every section every 2 weeks. Stale numbers here cause stale advice everywhere downstream.

---

## 1. Offer & Delivery

### Status
Pre-revenue. Two pilots in active build (Bieri, Gränacher) as of 2026-05-04. Targeting **5 paying clients by 2026-05-30**.

### Sales motion (canonical 7-step)

1. **Cold outreach** via walk-in (preferred), cold call, WhatsApp, or email (rare). Walk-ins use Nico door-to-door; cold calls use the [KW-16 Cold-Calling script](https://www.notion.so/sexyjoaquin/KW-16-Cold-Calling-33ebebb0c2f9808fbca0fb94b262df44?v=33cbebb0c2f9808896d0000c7929ef26&source=copy_link).
2. **Qualify** — if the company sounds like a fit, propose a follow-up call to scope an automatable process.
3. **Workflow Interview call** — run prospect through the [Workflow Interview Bot](https://automatisierbar-interview-bot.onrender.com); bot generates a structured prompt.
4. **Build** — prompt feeds into Claude Code, automation gets built *before* the pilot meeting (pre-commitment).
5. **Present built automation** — recontact, schedule meeting, demo it live.
6. **Free 2-week pilot** — automation runs in the client's environment, captures time-saved data.
7. **Conversion conversation** — present pilot data, propose one-time build fee + monthly retainer. Yes → paying client.

### Productized packages
None. All work is custom, project-by-project, scoped via the workflow interview.

### Pricing model (working hypothesis, untested)

- **Primary structure:** one-time build fee + monthly retainer.
- **Long-term aspiration:** % of measured savings as the retainer (e.g. ~25% of CHF/month saved). Not yet validated — flagged for `library`-skill consult once Bieri/Gränacher land.
- **Bieri reference deal (TBC ~2026-05-18):** ~3000 CHF one-time + ~500 CHF/month.
- **Day rate / project floor:** TBD — set after first 2–3 closes.
- **Average deal size / range:** TBD — no closes yet.
- **Payment terms:** TBD.

### Delivery

- **Builder:** Joaquin (sole shipping builder until ~2026-06-19; Tej and Patrik are still ramping on AI automation).
- **Client-facing owner:** whoever opens the prospect (cold call / walk-in / interview) stays as relationship owner.
- **Handover format:** TBD — current default is "Nico installs in person, then reactive support if it breaks." Decide formally after Bieri/Gränacher.
- **Post-launch support:** Implicit in the monthly retainer. Specifics TBD.

### Guarantee / commitment
**TBD** — pending dedicated session using the `library` skill (Hormozi value-equation framework). Need a documented promise + failure remedy before scaling beyond first 2 pilots.

### Tech stack we commit to

- **Infra we build on:** n8n (primary, hosted at oojoaquin.app.n8n.cloud), Notion, Make, Zapier, Render, GitHub, GitLab, Trigger.dev, Microsoft 365 ecosystem, Claude API.
- **Client-system integrations:** determined per-engagement (Bieri/Gränacher specifics emerging).
- **Trajectory:** n8n-heavy today, Trigger.dev adoption starting; mix may shift over time.

### Tech stack we WON'T touch

- **Hard no:** Regulated domains we have no qualification for (medical PHI, banking core systems, FINMA-regulated).
- **Soft no (case-by-case):** Anything without an API or webhook (workarounds may exist).
- **TBD:** Direct DB access to client systems we can't audit.

---

## 2. ICP

### Wedge or spray
**Spray, not wedge.** Currently calling all KMU backend processes across multiple sectors (Immobilien, Treuhand, Rechtsbranche, Landschaftsarchitektur, Landwirtschaft, others). Too early to wedge — let conversion data pick the sector.

### Primary target
Swiss-German-speaking **Klein- bis Mittelgrosse Unternehmen (KMU)**, ~10–200 employees, Deutschschweiz. Targeting documented backend processes that are repetitive, time-consuming, and run on tools with APIs/webhooks.

### Geography
**Deutschschweiz only.** Currently active in Aargau and Zürich. No Romandie / Ticino expansion before 2026-12-31.

### Decision-maker title
Asking for "the decision-maker" / Geschäftsführer / Inhaber, but in practice talking to whoever picks up.

### Disqualifiers (hard "not a fit")

- **Regulated domains:** medical PHI, banking core systems, FINMA-regulated.
- **On-prem-only / no-API stacks:** soft no, evaluate case-by-case.
- **Other formal disqualifiers:** none yet — taking everyone to the workflow interview at this stage.

### One-sentence ICP statement
> Swiss-German-speaking KMU (10–200 employees, Deutschschweiz) with a documented backend process that's repetitive, time-consuming, and runs on tools with APIs/webhooks (Microsoft 365, Google Workspace, common SaaS). We disqualify on regulated domains (medical/banking core/FINMA) and on-prem-only stacks.

---

## 3. Funnel Reality

### Outreach capacity (per week)

- **Nico:** full-time. Targeting 100 walk-ins/week + 50–100 cold calls. ~200 outreach attempts/week ceiling.
- **Joaquin:** 0–100/week (capped at 16h/week by military service until 2026-06-19).
- **Tej:** 10–30 calls/day during zivildienst.
- **Patrik:** ~5h/week, Saturdays only (military recruit). Builds-only learning, no outreach.
- **Cumulative outreach (cold calls + walk-ins) to date:** ~250.

### Funnel rates

- **Cold call:** 100 calls → 30 conversations (30%) → 1–2 hot leads (1–2% of calls / 3–7% of conversations). 7min per call.
- **Walk-in:** 50 walk-ins → 1 workflow interview (~2%). 15min per walk-in. Higher trust depth, deeper funnel position per encounter than cold calls.
- **Workflow interview → pilot started:** TBD — instrument from Bieri/Gränacher.
- **Pilot → paying client:** TBD — no conversions yet.
- **Average sales cycle (first touch → signed):** TBD — Bieri/Gränacher will be first datapoints.

### Pipeline state (as of 2026-05-04)

- **Hot leads:** 10
- **Pilots in build:** 2 (Bieri, Gränacher)
- **Paying clients:** 0
- **Cumulative revenue:** 0 CHF
- **MRR:** 0 CHF

### LinkedIn

- 1 post/week, 0 conversions. Joaquin started ~2026-04-27. Not a real channel yet.
- No Sales Navigator.

### Inbound / referral / network

- **Inbound (website automatisierbar.ch):** 0/month. Site intentionally empty until first client proof.
- **Referral / warm intro:** 0 to date.
- **100% of pipeline = team outbound.**

### Voice agent gate

- **Threshold (as of 2026-05-04):** ≥1000 transcripts + ≥10 hot leads.
- **Target date:** 2026-05-16.
- **Current progress:** ~40 transcripts / 10 hot leads. Hot-leads bar already met; transcript bar is the binding constraint.
- **Math note:** at current ~18 transcripts/week pace, 1000 by 2026-05-16 is mathematically improbable — flagged in §9 for either timeline revision, threshold revision, or surge plan.

### Hot-lead definition
Post-conversation prospect who agreed to the workflow interview (or showed strong buying signals warranting the second meeting). One step further down the funnel than "had a conversation." Used as the metric in §3 funnel rates.

---

## 4. Lead Supply Chain

### Outbound list source

- **Primary:** self-built scraping automation in n8n. Currently low quality — flagged as improvement candidate.
- **Cost per lead:** DIY (time only, no $ spend).
- **Refresh cadence:** continuous (whenever Joaquin runs the scraper).
- **Phone number enrichment:** Google Maps scrape + custom phone-enrichment bot.

### Walk-ins

- **Owner:** Nico, primary motion.
- **Rate:** ~100 walk-ins/week target.
- **Conversion:** 1 in 50 walk-ins → workflow interview.

### LinkedIn

- **Sales Navigator:** No.
- **Activity:** Joaquin ~1 post/week; ~7 days into the channel.
- **Strategy:** dormant — invest more once first client proof exists.

### Inbound

- **Website (automatisierbar.ch):** empty by design until first client proof.
- **SEO:** none.
- **Paid ads:** none.

### Referral

- **Formal program:** none.
- **Accidental referrals to date:** none.

---

## 5. Team & Time

### Roles (current)

- **Joaquin Gamonal** — co-founder; builder + ops + brand/infra + decision lead. **16h/week now**, full-time from 2026-06-19. Sole shipping builder until Tej/Patrik ramp.
- **Nicolas Widmer** — co-founder; outbound owner (calls + walk-ins) + sales conversations + script ownership. **Full-time** today.
- **Tej Kasarkod** — co-founder; learning AI automation; calls 10–30/day during zivildienst. Not yet shipping builds.
- **Patrik** — co-founder; military recruit, 5h/week (Saturdays). Learning AI automation only. Will be free post-2026-06-19.

### Time blocks (calendar facts that govern everything)

- **Now → 2026-06-19:** Joaquin/Tej/Patrik on RS/Zivildienst. Only Nico is full-time. Joaquin is the build bottleneck at 16h/week.
- **2026-06-19 → 2026-09-07:** All four founders free. **~11 weeks of full-team availability — peak founder-hour window of the year.** Doubles as ramp time for Tej/Patrik on builds.
- **From 2026-09-07:** All four start University of St. Gallen (HSG), living together.

### Decision-making

- **Joaquin decides by default.** "Leader" framing.
- **Important decisions:** majority vote among the 4.
- **Pricing / structure / organization:** Joaquin solo.

### Legal entity

- **Status:** not registered. Operating informally.
- **Trigger to form GmbH:** first 20'000 CHF cumulative revenue.

---

## 6. Strategic Priors (decided — don't re-litigate without surfacing)

a. **Outreach channel hierarchy:** walk-ins (preferred) → cold calls → WhatsApp → email (rare). *Reason:* walk-ins convert deeper per minute (1 interview per 50 walk-ins vs. 1–2 hot leads per 100 cold calls) and build qualitatively stronger trust in Swiss SME context. Cold calls remain primary fallback when walk-ins aren't viable due to team-member constraint (Tej/Joaquin/Patrik can't walk in during service).

b. **Spray across all KMU backend processes — no sector wedge yet.** *Reason:* too early to wedge; let conversion data identify the sector once 5+ deals have closed. Avoid premature focus that closes off learning.

c. **Free 2-week pilot before any pricing conversation.** *Reason:* every prospect gets it. Generates time-saved data as ammo for pricing + de-risks the buying decision for the client.

d. **Quick win first → expand into "AI partner" later.** *Reason:* until a working automation lives in the client's environment, Automatisierbar is "strangers with a project." Prove value with a small win, then earn the right to embed deeper.

e. **Outreach > content marketing right now.** *Reason:* website empty by design until first client proof; LinkedIn dormant. Content has 6-month payback that pre-revenue can't afford.

f. **Schweizerdeutsch primary on calls; Hochdeutsch acceptable for phone clarity.** *Reason:* trust signal in Swiss SME context. Hochdeutsch tolerated because phone audio sometimes makes dialect harder to understand.

g. **n8n primary platform; Trigger.dev adoption starting.** *Reason:* per operator-principles + current build pattern. Watch the mix — may shift toward Trigger.dev as Joaquin's familiarity grows.

h. **Service business now, product later.** *Reason:* need 10+ delivered projects to know what to productize; premature product = building in the dark.

i. **Boring is Beautiful — deterministic > AI.** *Reason:* per operator-principles. AI/agents only when deterministic genuinely can't do it.

---

## 7. 6-Month Horizon (target: 2026-11-04)

### Revenue trajectory

- **Q2 (by 2026-05-30):** 5 paying clients.
- **Q3 (by ~2026-09-30):** 20'000 CHF MRR.
- **Q4 (by 2026-12-31):** **250'000 CHF MRR.**

### Growth thesis
Outreach is the *only* current bottleneck. Build/maintain capacity is high (especially post-2026-06-19 with full team). Once first clients land → referrals + LinkedIn proof + warm-lead engine → exponential. Plus all 4 go full-time post-2026-06-19. The entry product is low-ticket; "AI Partner" expansion = much higher LTV per client than single automations.

### Key milestones in window

- **2026-05-16:** Voice agent gate target (1000 transcripts + 10 hot leads). Hot-leads bar already met; transcript bar improbable on current pace.
- **2026-05-30:** 5 paying clients.
- **2026-06-19:** Joaquin/Tej/Patrik free → full-team full-time.
- **2026-09-07:** HSG starts; founders living together.
- **First 20'000 CHF cumulative revenue:** GmbH formation triggered.

### Hire/no-hire
**No hires planned** in 6-month window. 4 founders only.

### Productized offer
**No.** Stay fully custom. Re-litigate in Q3 once 5+ delivered builds give product-shape data (flagged in §9).

### Geography
**Deutschschweiz only** until 2026-12-31. No Romandie / Ticino / DE-AT.

---

## 8. Constraints

### Budget

- **Monthly tool spend ceiling:** uncapped. Currently 135 CHF/month.
- **One-time experiment budget:** <200 CHF Joaquin auto-decides; >300 CHF requires founders' discussion.

### Legal / compliance

- **nDSG:** all client data stays in EU/CH where possible.
- **Bank/payment data:** never stored long-term, never logged in transcripts.
- **Specific client contracts mandating CH-only:** none yet (no signed clients).

### Time

- See §5 for hard time blocks (Joaquin/Tej/Patrik service end 2026-06-19; HSG starts 2026-09-07).
- Nico outreach capacity: ~200 attempts/week ceiling.

### Tooling lock-in we accept

- Notion (Operations Cockpit), n8n (oojoaquin.app.n8n.cloud), Claude API, Telegram (internal bots), Render, GitHub, GitLab, Trigger.dev, Microsoft 365.
- Switching cost is real; don't propose migrations without a 10x reason.

---

## 9. Open Questions / Known Unknowns

1. **Handover artifact at end of pilot** — what does the client physically receive (Loom + runbook + training? Just verbal handoff?)? Decide after Bieri/Gränacher land.
2. **Post-pilot close rate** — instrument from Bieri/Gränacher conversion outcomes; needed to validate Q3/Q4 trajectory.
3. **Pricing/guarantee policy + value-stack design** — dedicated session using `library` skill, after first paying client.
4. **"Won't touch" — direct DB access to client systems** — policy not yet decided.
5. **Walk-ins as formal primary wedge** — confirm in §6 once 4+ more weeks of comparison data.
6. **Build capacity ceiling test** — measure when 3+ active pilots collide pre-2026-06-19. Joaquin = sole shipping builder.
7. **Q4 250k MRR trajectory** — re-litigate productization decision in Q3 once 5+ delivered. Math implies either ~50–100 clients × small retainer OR ~10–20 clients × AI-Partner-sized retainer.
8. **Cost-per-unconverted-build** — measure Joaquin's hours invested in pre-pilot builds that don't convert post-pilot. If high, may need to gate the build step behind some commitment signal.
9. **Voice agent gate rationale + math** — why did the bar move from 100 → 1000 transcripts? Document the reasoning. And: at current ~18 transcripts/week, 1000 by 2026-05-16 is mathematically impossible. Either revise the date, the threshold, or specify a surge plan.

---

## Appendix — Quick reference

- **Domain:** automatisierbar.ch
- **Brand color:** #15C97A
- **n8n:** oojoaquin.app.n8n.cloud
- **Notion parent:** Operations Cockpit
- **Lead DB:** Interview Datenbank
- **Live workflows:** LinkedIn Engagement Bot, Telegram Interview Bot
- **In build:** Cold-Call Analytics Pipeline (3 workflows, Phase 2)
- **Workflow Interview Bot:** https://automatisierbar-interview-bot.onrender.com
- **Cold-Calling Script:** [KW-16 Notion page](https://www.notion.so/sexyjoaquin/KW-16-Cold-Calling-33ebebb0c2f9808fbca0fb94b262df44?v=33cbebb0c2f9808896d0000c7929ef26&source=copy_link)
- **Operator email (work):** joaquin@automatisierbar.ch
- **Operator email (Claude Code config):** sexyjoaquin15@gmail.com
