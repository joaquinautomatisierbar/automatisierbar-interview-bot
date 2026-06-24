---
name: Revenue Lab
description: A small, tightly-governed agent company that stands up a fast-to-revenue productized digital service and earns its first honest dollar — under a hard burn cap, with the operator as the legal/financial shell and decision-gate on all money + external-trust actions.
slug: revenue-lab
schema: agentcompanies/v1
version: 0.1.0
license: MIT
authors:
  - name: Joaquin Gamonal Demann
goals:
  - "Phase-1 metric (the real target): produce ONE cleared Stripe payment for a productized digital service, where the sale's measured acquisition cost (external spend) is less than the payment — inside a hard $300 lifetime burn cap."
  - "Operate strictly under the LEGAL-SHELL model: the operator owns the legal entity, Stripe account, and bank. Agents only ever call scoped APIs. Agents NEVER create accounts, do KYC, or move funds out."
  - "Halt for operator approval before every money-touching or external-trust action (Bike Method Phase 1). Autonomy loosens only by explicit operator edit after validation — never automatically."
  - "Stay inside the WAT framework: deterministic code (governor, Stripe tool) handles execution + enforcement; agents handle bounded reasoning only."
---

# Revenue Lab

A **completely separate business from Automatisierbar** (separate brand, separate identity —
NOT a sub-brand and never carrying Automatisierbar's name/assets). A 4-agent company that tries
to build a **fast-to-revenue digital service** and earn a real dollar — to learn, in practice,
where autonomous agents can and cannot run a business.

> **LIFETIME BURN CAP: $300 USD (external/business spend).** The `finance-ops` governor
> (`tools/revenue_governor.py`) enforces this deterministically. When it trips, ALL agents
> pause and the operator is paged on Telegram. This is the amount the operator has chosen to
> *lose* to find out whether this works. Claude compute runs on the operator's Claude Max
> subscription (OAuth token), NOT metered API credits, so compute is ~$0 against this cap —
> the cap governs external spend (paid non-Claude APIs, ads, domains, tools, Stripe fees).

> **bike-method-phase: 1** (training wheels). Every money-touching / external-trust action
> halts for operator approval. The North Star is $10k/mo; the *operational* Phase-1 target is
> the first cleared payment whose cost is less than the sale. Do NOT optimize for $10k-scale
> plans — optimize for one real charge.

## The North Star vs. the Phase-1 target

$10k/mo is the mission, not the operating target. Optimizing for $10k/mo makes agents produce
plausible-looking scale plans that ship nothing (this exact failure burned $38 in one morning
on the sibling company). The operating target is **one cleared Stripe charge that cost less
than it earned.** Everything in Phase 1 serves that single metric.

## Business model (constrained: fast-to-revenue digital service)

A **productized micro-service** for backoffice-heavy Swiss SMEs (Immobilien / Treuhand / Anwalt /
Steuerberater — NOT Coiffeur / Restaurant / trades, which have no backoffice automation pain).
Fixed-scope, fixed-price, sold via a Stripe **payment link** (no website required), under
**Revenue Lab's own brand** (`brand/BRAND_GUIDE.md`). Agents may apply generic business
frameworks (`~/_context/references/library/`) and generic tooling (PDF/diagram libs, restyled to
the Revenue Lab brand), but must NEVER carry Automatisierbar's brand, assets, scripts' styling,
or `business-context.md` into a deliverable. See `pick-fast-revenue-offer` for offer selection.

## How the company works

```
[Operator: "find + sell a productized service"]
      │
      ▼
   CEO ── (brand TBD? run brand-proposal cycle → QA → operator approves first)
      │ ── picks ONE fast-revenue offer (frameworks + ICP grounded) ── HALTS for operator approval
      │
      ├──► Builder ── research (read-only) + builds fulfilment asset (INACTIVE, Revenue Lab brand)
      │                 + drafts outreach/landing copy ── posts READY_FOR_REVIEW
      │                         │
      │                         ▼
      ├──► QA Reviewer ── RENDERS + checks every deliverable (layout, brand=Revenue-Lab-only, honesty)
      │                    ── REVIEW_FAIL: <defects> → back to Builder  |  REVIEW_PASS → clears it
      │
      ├──► Finance-Ops ── creates Stripe product/price/payment-link (TEST mode) ── HALTS before LIVE
      │
      └──► [QA passed → CEO READY_TO_SHIP → operator approves] ── operator sends outreach ──
           payment clears ── Finance-Ops records revenue
```

Each agent owns one cognitive mode: CEO decides + talks to the operator; Builder builds; QA
verifies by actually rendering/observing the output; Finance-Ops runs the Stripe tool + ledger.
**Nothing customer-facing reaches the operator without QA `REVIEW_PASS`.** Closing and real
outbound are HUMAN actions (the operator) — agents prepare the sale; a human makes it.

## Reporting line

Builder, QA Reviewer, and Finance-Ops report to **CEO** (urlKey: `ceo`). CEO reports to the
operator (Joaquin) via the dedicated **Revenue Lab Telegram channel** (`REVENUE_TELEGRAM_*`, a
separate bot from the Automatisierbar operator bot — avoids reply-crosstalk).

## Hard rules (every agent inherits these)

- **ZERO Automatisierbar in any artifact.** Revenue Lab is a separate business. No Automatisierbar
  name, logo, colors, "Theme 02", `automatisierbar.ch`, or `@automatisierbar.ch` — ever. Use only
  `brand/BRAND_GUIDE.md`. (See `learnings/global.md` — this rule exists because of a real failure.)
- **Nothing customer-facing ships without QA `REVIEW_PASS`.** Builder → render/observe by QA →
  pass → operator. A deliverable nobody looked at is not done. (See `verify-deliverable`.)
- **No agent hires another agent.** The team is fixed at 4. A $300 cap cannot survive fleet
  growth. Hiring is an operator decision only.
- **No autonomous account creation, signups, CAPTCHA-solving, or KYC.** Out of scope, full
  stop — ToS/ban risk and legally undelegatable. The operator provisions every account and
  binds keys as `secret_ref`. Agents consume keys; they never provision them.
- **Legal-shell:** the operator owns the entity, Stripe, and bank. Agents never move money out
  (`payout`/withdrawal/transfer is refused by the Stripe tool).
- **Self-wake guard:** if the latest comment on your issue is from YOU, exit silently — do
  nothing. This prevents the self-wake loop that burned $15/hr on the sibling company.
- **Halt-before-acting** on money + external trust — see the `money-halt-protocol` skill.
- **Check the budget governor before any spend** — see the `check-budget-governor` skill.

## Skills

- `revenue-lab-context` — read on every wake; loads the OWN brand + offer + $300/legal-shell rules.
- `pick-fast-revenue-offer` — choose an offer grounded in generic frameworks + the ICP.
- `verify-deliverable` — (QA) render + observe a deliverable; the "actually look at it" checklist.
- `handoff-protocol` — Builder → QA → operator markers (READY_FOR_REVIEW / REVIEW_PASS / FAIL).
- `check-budget-governor` — call `tools/revenue_governor.py` before any spend; respect the cap.
- `stripe-operations` — the allowed Stripe verbs (TEST first) + what is gated/refused.
- `money-halt-protocol` — the money-specific halt-before-acting wrapper (notify + poll).
- `recall-learnings` — load Revenue Lab's own prior lessons (`learnings/global.md`, read-only).

Plus paperclipai-bundled skills wired by `bootstrap-new-agents.sh`
(`paperclipai/paperclip/paperclip` etc.).
