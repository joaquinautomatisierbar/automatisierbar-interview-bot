# STORM dossier — High-converting website for Automatisierbar (automatisierbar.ch)

- **Intent:** research to ground the build/redesign of automatisierbar.ch — a German-language (Hochdeutsch) site whose job is converting visitors into booked discovery calls / free-pilot signups for a Deutschschweiz AI-automation agency selling to KMU (10–200 employees).
- **Reader:** a builder on the Automatisierbar team about to (re)build the site.
- **Date:** 2026-06-29 · **Council:** Practitioner · State-of-the-art Scout · Skeptic · Economist/ROI · End-user/Customer (build set, 5 lenses)
- **Verification banner:** 20 source-claims verified → **2 fabricated · 7 corrected/re-attributed · 5 demoted (vendor self-data or stale) · 6 confirmed.** The biggest "fact" the first pass produced — a "March 2026 Google update dropping the LCP threshold to 2.0s" — was **fabricated**. See Source audit.
- **Disclosure:** the expert panel is author-built (5 AI lenses, not 5 independent humans). Convergence here is a strong hypothesis, not independent field consensus.

---

## 1. Recommended approach (TL;DR)

For a pre-revenue, **outbound-led** agency, the website is a **trust-confirmation asset**, not a lead channel — prospects hit it *after* Nico/Tej reach them, to decide whether to disqualify you. So do **not** build a fancy multi-page site. Ship **one focused credibility page, fast, on the stack you already run**, and spend your scarce build hours on outbound + harvesting proof.

The order that actually converts this Swiss buyer (all 5 lenses agree):

1. **Secure ONE nameable Swiss case study with a number first** (Bieri or Gränacher: "X Stunden/Woche gespart bei [Prozess]"). This is the real unlock — not design. *"Your promise is not a differentiator. Your proof is."* (Hormozi, Proof Checklist). Today you are 100% Level-1 authority ("you saying it"); one named result jumps you to Level 2–3.
2. **One page, one job:** a concrete KMU back-office *outcome* in the hero (German, Sie, **no "KI-gestützt" buzzwords**) → the named proof + number → "Wie es läuft" (Workflow-Interview → Build → 2-Wochen-Pilot, kostet nichts) → a visible **nDSG / Datenschutz + Impressum + "Daten bleiben in CH/EU"** block → embedded one-click booking.
3. **Reuse, don't rebuild:** point the booking CTA at your existing **cockpit booking flow** (`cockpit.automatisierbar.ch/book` — already does the form→calendar handoff the practitioner says you win or lose on). Use your **terminal/brand design system** (#15C97A, JetBrains Mono — see `automatisierbar-deck`). Add **Plausible** (cookieless, EU-hosted, no consent banner = an nDSG trust win).
4. **Skip** AI personalization, scroll animations, an AI chatbot, stock-AI imagery, and a multi-page nav. They cost time, dent trust with this audience, and their ROI is unproven (see Source audit — the personalization stats mostly didn't survive verification).

Build past a one-pager only when a real outbound prospect tells you the *site* cost you a deal.

---

## 2. Reliability-ranked key findings

| # | Finding | Reliability | Supported by / Challenged by | Source |
|---|---------|:---:|---|---|
| 1 | For an outbound-led early-stage agency, the site's job is **trust-confirmation**, not lead-gen; sequence outbound + proof first | **9/10** | All 5 lenses + business-context §3/§6e / — | Gartner 2025 (61% prefer rep-free); business-context.md |
| 2 | **Proof + clarity beat page-count and polish.** A focused one-pager with a named, specific result out-converts a fancy multi-page brochure | **9/10** | Practitioner, Economist, Skeptic, End-user / SOTA (wants more build) | Unbounce/Heyflow B2B benchmarks; Hormozi Proof Checklist |
| 3 | This Swiss buyer silently disqualifies on **missing Impressum, no nDSG/data-residency answer, vague AI claims, no named local case** | **9/10** | End-user, Skeptic, Practitioner / — | DACH trust research; Forrester 2025 (19% less confident from misleading AI) |
| 4 | **Vague "AI-powered" claims now actively erode trust** (AI-washing perception); lead with the boring concrete outcome instead | **8/10** | Skeptic, End-user / — | Forrester 2025; MMC Ventures (2019) |
| 5 | The **form→embedded-calendar handoff** is the highest-leverage on-page mechanic; keep the qualifier form to 3–4 fields with one KMU-fit question | **7/10** | Practitioner / Economist (says it's not the bottleneck) | Chili Piper 2025 (vendor data); Velocify 391% (~2013, vendor) |
| 6 | **Fancy animations / heavy JS hurt conversion** (layout shift, slow load); a fast, plain page wins | **7/10** | Skeptic, SOTA / — | web.dev CSS Web Vitals; Clutch |
| 7 | Modern light stack + cookieless EU analytics is a real trust/perf lever (Astro-class, Plausible, Cal.com) — but **not** a reason to over-build | **6/10** | SOTA / Economist, Skeptic | Cal.com, Plausible (confirmed); Astro exact figures unverified |
| 8 | **Contested signal — AI personalization "~40% lift" / "+11% geo hero":** did **not** survive verification; treat as unproven, do not build on it | **2/10** | SOTA / verification pass | Mostly unsourced — see Source audit |

---

## 3. Per-lens summaries

- **Practitioner:** Single long-scroll page, outcome-specific hero, dual CTA, repeating Pain→Offer→Proof→CTA rhythm, social proof seeded throughout (not buried). *The one thing:* the form→calendar handoff is where you win or lose — show the embedded slot picker immediately on submit, 3–4 fields max, one qualifier, a verifiable proof element next to the booking CTA.
- **State-of-the-art Scout:** Content-first, near-zero-JS static stack (Astro-class) that's fast; cookieless EU-hosted analytics (Plausible); Cal.com over Calendly for data residency; *pushed* AI server-side personalization — **but that pillar largely failed verification.** *The one thing:* speak to who actually landed and don't lose trust to bloat + consent friction. (Keep the stack/tooling advice; discard the personalization stats.)
- **Skeptic:** The site is almost never the bottleneck at this stage; the likely failure is a slow, AI-gimmick brochure making vague claims a Swiss KMU won't believe. *The one thing:* before any copy/animation, secure (a) one nameable case study with a number, (b) clean nDSG Impressum/Datenschutz + data-residency statement, (c) a human face/photo. Without those three, no design converts this audience.
- **Economist/ROI:** The website is a trust-confirmation asset prospects check after outbound; cap it at one credibility page on a template in <1 day, pour remaining hours into outbound + case studies. *The one thing:* the site doesn't earn the call, it prevents you losing one you already earned.
- **End-user/Customer:** A busy, AI-skeptical, privacy-conscious Swiss KMU owner needs, in 5 seconds: which boring task disappears, one same-size Swiss firm you did it for, a promise their data stays in CH, and a low-risk reversible next step. *The one thing:* "Stop telling me your tech is 'KI-gestützt' — tell me which task disappears, show me a Swiss firm my size, swear my data stays in Switzerland, and let me book 30 minutes for free."

---

## 4. Contradiction map

- **Direct conflict — how much to build:** SOTA Scout says build a modern personalized stack (more surface, leading-edge); Economist + Skeptic say a one-pager in a day, the site isn't the lever. **Stronger side: Economist/Skeptic** — grounded in independent buyer data (Gartner) + your own funnel reality (100% outbound, 0 paying clients), whereas the Scout's "build more" rested partly on personalization stats that failed verification.
- **Direct conflict — is the booking mechanic decisive?** Practitioner says the form→calendar handoff is where you win/lose; Economist says the *call was already earned by outbound*, the page just shouldn't blow it. **Resolution:** both true at different scales — get the handoff right (cheap, reuse cockpit /book), but don't mistake it for the growth lever.
- **Strongest evidence overall:** the Swiss-trust requirements (Impressum/nDSG/named-case) — corroborated across End-user, Skeptic, Practitioner *and* an independent legal fact (nDSG in force 1 Sep 2023, confirmed). **Weakest evidence:** the AI-personalization lift cluster — almost entirely unsourced/misattributed vendor blog numbers.
- **The resolving question:** *Does automatisierbar's pipeline depend on the website at all right now?* Answer from business-context: no — 100% of pipeline is team outbound, site is empty by design. That settles the build-scope debate toward "minimum credible page."
- **Universal agreement (load-bearing, likely true):** **A specific, named, verifiable Swiss proof point + a clear concrete outcome + a visible nDSG/data answer is the conversion lever — far more than design polish or page count.** Every lens said this.
- **The blind spot (no lens covered it):** the actual **German hero copy / hook** and **SEO/organic discovery**. Both deliberately downstream here, but the headline is what converts — see missing-lens note.

---

## 5. Build implications for us (act on these)

1. **Proof first (highest ROI, not a build task).** Get explicit consent from Bieri or Gränacher to name them + publish one number (e.g. "~12 Std./Woche gespart bei [Prozess]"). Capture it raw per the Proof Checklist (show-not-tell, avatar-matched, with the number). This gates the whole page's effectiveness.
2. **One static page, on the stack you already run.** Serve a single page (Flask on Render — your existing deploy-from-GitHub-main flow) using the **`automatisierbar-deck` design system** (#15C97A, JetBrains Mono, dark terminal aesthetic) for visual consistency. No new framework, no multi-page nav, no CMS.
3. **Page skeleton (top→bottom):** hero (one concrete KMU back-office outcome, Hochdeutsch/Sie, zero buzzwords) → named proof + number + human photo → "Wie es läuft" 3 steps (Workflow-Interview → Build → 2-Wochen-Pilot, kostet nichts — mention "kostet nichts" once) → **Datenschutz/nDSG + Impressum + "Ihre Daten bleiben in der CH/EU"** → booking CTA "Erstgespräch buchen".
4. **Reuse the booking flow.** Point the CTA at the existing **`cockpit.automatisierbar.ch/book`** (lead + Termine + confirmation email already built) instead of adding Cal.com. That's the form→calendar handoff the Practitioner flagged — already solved. Keep any pre-form to 3–4 fields + one KMU-fit qualifier.
5. **Analytics:** add **Plausible** (cookieless, EU-hosted, no consent banner) — nDSG-friendly and removes banner friction. Defer PostHog/session-replay until there's real traffic to optimize.
6. **Hard "do not":** no AI personalization, no scroll animations, no AI chatbot, no stock-AI imagery, no "KI-gestützt" hero. (Matches your no-buzzword LinkedIn-tone prior + Boring-is-Beautiful.)
7. **Tie to a KPI:** the only number this page should move is **booked-call rate from outbound-warmed visitors** — instrument it (Plausible goal on the /book confirmation). If it doesn't move that, don't expand the site.

*Frameworks applied:* Three Levels of Authority + 13-Item Proof Checklist + "match claims to proof" (Hormozi, Proof Checklist); Awareness Pyramid places a post-outreach visitor at proof/promise-driven messaging, not curiosity hooks (Hormozi, $100M Leads); Two-Part Hook (call-out + condition) for the hero line.

---

## 6. Pitfalls / what NOT to do

- **Building the page before the named case study exists** → a polished brochure that fails the Swiss trust check silently; you never hear why.
- **Vague "AI-powered" / "KI-gestützt" claims** → reads as AI-washing; Forrester: 19% of buyers less confident due to misleading AI.
- **Scroll/JS animations & heavy stack** → layout shift + slow load → higher bounce, lower conversion.
- **Missing Impressum / Datenschutz / data-residency statement** → silent disqualification by a privacy-conscious Swiss buyer (nDSG in force since 1 Sep 2023).
- **Multi-page brochure with nav** → diffuses the one job; focused single page converts better.
- **Optimizing the site while outbound is the real bottleneck** (business-context §6e: "Outreach > content marketing right now").
- **Redesign churn** → over/under-building traps you in pay-twice rebuild cycles; ship the minimum credible page and iterate from real prospect feedback.

---

## 7. Source audit (verdicts)

**Fabricated / false (do not use):**
- ❌ "March 2026 Google update: LCP good 2.5s→2.0s, INP co-equal, 43% fail, 0.8–4 position drop" — **FALSE/fabricated.** Official thresholds unchanged: LCP ≤2.5s, INP ≤200ms (stable since Mar 2024), CLS ≤0.1. https://developers.google.com/search/docs/appearance/core-web-vitals
- ❌ "Inline embedded scheduler beats popup by 30–40% / +30–70%" — **FALSE/unsourced.** The cited Calendly page makes no such claim; the 30–70% is blog-on-blog with no study. Drop. https://calendly.com/help/embed-options-overview

**Corrected / re-attributed:**
- ✏️ "75% of B2B buyers prefer rep-free" → **61%** (Gartner, 2025-06-25; 67% in a 2026 follow-up). https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-sales-survey-finds-61-percent-of-b2b-buyers-prefer-a-rep-free-buying-experience
- ✏️ "67% rely more on content than on sales reps" → misquote; real: rely more on content **"than a year ago"** (Demand Gen Report Content Preferences Survey).
- ✏️ "MMC Ventures: 40% of AI startups use no real AI" → real but **2019, Europe-scope**, not 2025. https://www.cnbc.com/2019/03/06/40-percent-of-ai-start-ups-in-europe-not-related-to-ai-mmc-report.html
- ✏️ "Personalized CTAs +202%" → real (HubSpot, 330k CTAs) but **observational, not an RCT** (selection bias). https://blog.hubspot.com/marketing/personalized-calls-to-action-convert-better-data
- ✏️ "Dynamic headlines +20–30%" → one A/B test of **+31.4%** over-generalized. https://blog.conversionlab.no/see-how-dynamic-text-on-a-landing-page-increased-conversions-by-31-4/
- ✏️ "First-person CTA +14%" / "outcome verbs +31%" → numbers wrong/misattributed; the real first-person test was +90% on one button (Aagaard/Unbounce); the +31% is the same ConversionLab number laundered onto a different claim. Principle valid, specific numbers not.
- ✏️ "Astro 9KB vs Next.js 463KB" → directionally true (Astro ships far less JS) but **exact figures unverified** (one blog, no methodology; Vercel makes no such claim). Don't quote the numbers.

**Demoted (real but vendor self-data or stale — low trust):**
- ⬇️ Chili Piper "30%→66.7%, +122%" — **vendor's own funnel data**, baseline framing overstates causation. https://www.chilipiper.com/post/form-conversion-rate-benchmark-report
- ⬇️ "391% from sub-minute response" — real but **Velocify (~2013), vendor platform data**; say "up to 391%." https://velocify.com/blog/press-release/infographic-sales-processes-boost-lead-conversion-by-391-percent/
- ⬇️ "AI personalization ~40% lift" / "geo hero +11%" — **unsourced** aggregator blogs; no traceable study.
- ⬇️ "80% of decision-makers use mobile in the journey" — real but **BCG/Google 2017**, dated. https://www.bcg.com/publications/2017/marketing-sales-digital-go-to-market-transformation-mobile-marketing-new-b2b-buyer

**Confirmed:**
- ✅ nDSG/revDSG in force **1 Sep 2023**. https://www.kmu.admin.ch/kmu/en/home/facts-and-trends/digitization/data-protection/new-federal-act-on-data-protection-nfadp.html
- ✅ Forrester 2025: **19%** of buyers less confident due to misleading AI. https://www.digitalcommerce360.com/2025/10/28/forrester-b2b-buyers-demand-proof-not-promises/
- ✅ "73% avoid suppliers sending irrelevant outreach" (Gartner, same 2025 survey; figure correct, originally mis-attributed to Demand Gen Report).
- ✅ Cal.com — open-source (AGPLv3), self-hostable, EU/CH residency, unlimited free event types. https://cal.com/pricing
- ✅ Plausible — cookieless, EU-hosted, no consent banner, GDPR/nDSG-aligned (their pages say "EU," not specifically "Falkenstein"). https://plausible.io/data-policy
- ✅ Focused landing page out-converts sprawling site (Unbounce/Heyflow B2B benchmarks; directional). https://unbounce.com/conversion-rate-optimization/b2b-conversion-rates/

---

## 8. Open questions / missing lens

- **Missing lens #1 — Copywriting/messaging.** No lens wrote the actual German hero hook, which is what converts. Run a V2 **Copy lens** grounded in your LinkedIn voice memories + the library Hooks framework to draft 5 hero variants (call-out + condition for value) for the chosen KMU outcome.
- **Missing lens #2 — SEO/organic discovery.** Deliberately out of scope (you're outbound-led), but if inbound ever matters, add an SEO lens before investing in content.
- **Open Q1 — Which proof?** Will Bieri or Gränacher consent to be named with a number, and when? This gates the whole build.
- **Open Q2 — Which outcome to lead with?** You currently spray across sectors (business-context §2). Pick the single sharpest back-office outcome for the hero, or build it so the hero swaps per campaign — but only after a sector starts converting.
- **Open Q3 — Booking route confirmed?** Recommend reusing `cockpit.automatisierbar.ch/book` over adding Cal.com; confirm the cockpit flow can carry a website lead source cleanly.

---

---

## V2 — Copy lens (added 2026-06-30): German hero variants

Added lens per the §8 missing-lens flag. Grounded in: voice/tone memories (quiet-confident, no imperatives/accusation, value-not-cheap, "kostet Sie nichts" once, no em-dashes) + Two-Part Hook (call-out + condition for value) + Awareness Pyramid (post-outreach visitor is problem/solution-aware → promise/proof-driven, not curiosity) + the Grand Slam Offer wording. **Sie-Form, Hochdeutsch, zero "KI-gestützt" buzzwords.** Each variant uses a different hook archetype so you can A/B (Plausible goal on the /book confirmation).

**Shared trust microcopy** (under every CTA): `Ihre Daten bleiben in der Schweiz. Keine Verpflichtung.`

**V1 — Outcome statement** *(Statement hook · promise-driven · ship-now default)*
> # Der Backoffice-Prozess, der bei Ihnen jede Woche am meisten Zeit kostet, läuft bald automatisch.
> Wir schauen uns Ihre Abläufe an, automatisieren den aufwändigsten und bringen Ihnen eine fertige Lösung zum Testen. Erst wenn sie überzeugt, sprechen wir über alles Weitere.
> **[ Erstgespräch buchen ]**

**V2 — Question** *(Question hook · problem-aware · invites self-recognition)*
> # Wie viele Stunden pro Woche verbringt Ihr Team mit immer den gleichen Handgriffen?
> Wir finden den Prozess, der am meisten Zeit kostet, und bauen Ihnen eine Automatisierung, die Sie zwei Wochen in Ruhe testen. Kostet Sie nichts, bis sie überzeugt.
> **[ Zeigen Sie uns Ihren Prozess ]**

**V3 — Conditional** *(Conditional hook · solution-aware · honest hedge = Swiss-credible)*
> # Wenn ein Prozess in Ihrem Betrieb jede Woche dieselben Stunden verschlingt, können wir ihn wahrscheinlich automatisieren.
> Sie testen die fertige Lösung zwei Wochen in Ihrer eigenen Umgebung. Erst wenn sie wirklich Zeit spart, reden wir weiter.
> **[ Erstgespräch buchen ]**

**V4 — Proof-led observation** *(Narrative hook · proof-driven · SHIP THIS once a case study exists)*
> # Bei {Bieri} haben wir den Prozess automatisiert, der jede Woche {X} Stunden gekostet hat. Denselben blinden Fleck sehen wir in fast jedem KMU.
> Sagen Sie uns, wo bei Ihnen die meiste Zeit verloren geht. Wir bauen eine Lösung, die Sie kostenlos testen, bevor Sie sich entscheiden.
> **[ Erstgespräch buchen ]**

**V5 — Avatar call-out / Label** *(Label hook · cocktail-party call-out to the ICP)*
> # Für Schweizer KMU, die zu viel Zeit mit Excel, E-Mails und Copy-Paste verlieren.
> Wir automatisieren Ihren zeitaufwändigsten Backoffice-Prozess und liefern eine Lösung, die Sie zwei Wochen testen, bevor etwas kostet.
> **[ Erstgespräch buchen ]**

**Copy-lens recommendation:** ship **V1** now (strongest promise-driven opener that needs no proof yet), and the moment Bieri or Gränacher consent to be named with a number, switch the hero to **V4** (proof beats promise per the dossier's #1 finding + the Three Levels of Authority). Keep V2/V3/V5 as the test queue. Per 70-20-10: V1/V4 are your 70% proven-style core; rotate one challenger at a time, judge on booked-call rate, not clicks.

**Note (honesty guardrail):** "läuft bald automatisch" / "automatisiert" are concrete and fine, but don't let the hero imply a result you can't show yet. Until V4's named number is real, V1's promise is a promise, not proof, so pair it with the nDSG/Impressum trust block to carry credibility.

---

*Generated by `/storm` (pre-build research skill). Method: 5 expert lenses → contradiction map → synthesis grounded in `references/business-context.md` + `references/library/` → adversarial primary-source verification (5 verify agents) → V2 Copy lens added on request. Author-built panel; verify load-bearing facts before betting the build on them.*
