---
name: revenue-lab-context
description: >
  Load Revenue Lab's OWN context — its brand, offer, $300 cap, legal-shell, halt policy, and
  prior learnings — before any reasoning. Use on every heartbeat. Revenue Lab is a SEPARATE
  business: it must never carry Automatisierbar's brand, assets, or contact.
---

# Revenue Lab Context

Revenue Lab is a **completely separate business from Automatisierbar.** Load these before
reasoning. Company root on the VPS: `~/_context/tools/paperclip/companies/revenue-lab/`
(on the operator's Mac: the same path under the repo).

## Required reads (every heartbeat)

1. **`COMPANY.md`** (this company's) — mission, the $300 cap, legal-shell rules, the offer
   (Prozess-Audit Bericht), the ICP (backoffice-heavy Swiss SMEs: Treuhand / Anwalt /
   Immobilien / Steuerberater), the agent roster + flow. Your operating manual.
2. **`brand/BRAND_GUIDE.md`** — the ONLY brand source for customer-facing artifacts. If its
   fields are still `TBD`, the brand-proposal cycle must run first — do NOT generate any
   customer artifact against an undefined brand.
3. **`learnings/global.md`** — what prior runs got wrong (and the binding rules that came out of
   it). Read it so you don't repeat a known mistake. Also load via `recall-learnings`.

## Generic resources you MAY use (not brand-bearing)

- **`~/_context/references/library/INDEX.md`** — the distilled Hormozi / Testing-Business-Ideas
  frameworks (Value Equation, Fast-Cash, Concierge MVP, etc.). These are generic business
  frameworks, safe to apply. They are NOT a brand source.
- Generic tooling under `~/_context/tools/` (e.g. PDF/diagram libraries) — usable ONLY if you
  restyle output to the Revenue Lab brand. Never emit Automatisierbar styling.

## The non-negotiables

- **ZERO Automatisierbar.** No Automatisierbar name, logo, colors, violet/blueprint "Theme 02",
  `automatisierbar.ch` domain, or `@automatisierbar.ch` email in ANY artifact. Do NOT read
  Automatisierbar's brand guides or `business-context.md` as if they were Revenue Lab's — they
  are a different company's. QA fails any bleed.
- **$300 lifetime cap on external/business spend.** Compute is on the Claude Max plan (~$0).
  Before ANY spend, run `check-budget-governor`.
- **Legal-shell:** operator owns entity/Stripe/bank; you are a scoped API caller; never create
  accounts, do KYC, or move money out.
- **Nothing customer-facing ships without QA.** Builder → `READY_FOR_REVIEW` → QA renders +
  checks → `REVIEW_PASS` → operator go-live gate. (See `handoff-protocol`, `verify-deliverable`.)
- **Halt before** any money-touching / external-trust action (`money-halt-protocol`).
- **Self-wake guard:** if the latest comment on your issue is from you, exit silently.
- **Optimize for the first cleared payment**, not $10k-scale plans.
