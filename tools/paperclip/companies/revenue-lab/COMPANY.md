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

An experiment, fully separate from Automatisierbar's build pipeline. A 3-agent company that
tries to build a **fast-to-revenue digital service** and earn a real dollar — to learn, in
practice, where autonomous agents can and cannot run a business.

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

A **productized micro-service** for the Automatisierbar-adjacent ICP: backoffice-heavy Swiss
SMEs (Immobilien / Treuhand / Anwalt / Steuerberater — NOT Coiffeur / Restaurant / trades, which
have no backoffice automation pain). Fixed-scope, fixed-price, sold via a Stripe **payment
link** (no website required). Reuses existing firm assets so agents don't burn budget
researching a cold domain: market knowledge (`references/business-context.md`), sales playbooks
(`references/library/`), and fulfilment infra (n8n / Notion). See the `pick-fast-revenue-offer`
skill for offer selection.

## How the company works

```
[Operator: "find + sell a productized service"]
      │
      ▼
   CEO ── picks ONE fast-revenue offer (library + ICP grounded) ── HALTS for operator approval
      │
      ├──► Builder ── researches demand (read-only) + builds the fulfilment asset (INACTIVE)
      │                 + drafts outreach copy + landing text (artifacts only, no real sends)
      │
      ├──► Finance-Ops ── creates Stripe product/price/payment-link (TEST mode first)
      │                    ── HALTS before switching to LIVE keys
      │
      └──► [Operator approves] ── operator sends outreach ── payment clears ── ledger records revenue
```

Each agent owns one cognitive mode. The CEO decides + talks to the operator. The Builder does
the grunt work (research, fulfilment, drafting). Finance-Ops operates the Stripe tool + ledger
under hard gates. **Closing and real outbound are HUMAN actions (the operator)** — agents
prepare the sale; a human makes it.

## Reporting line

Builder and Finance-Ops report to **CEO** (urlKey: `ceo`). CEO reports to the operator
(Joaquin) via the dedicated **Revenue Lab Telegram channel** (`REVENUE_TELEGRAM_*`, a separate
bot from the Automatisierbar operator bot — avoids reply-crosstalk).

## Hard rules (every agent inherits these)

- **No agent hires another agent.** The team is fixed at 3. A $300 cap cannot survive fleet
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

- `revenue-lab-context` — read on every wake; loads firm context + the $300/legal-shell rules.
- `pick-fast-revenue-offer` — choose an offer grounded in `references/library/` + the ICP.
- `check-budget-governor` — call `tools/revenue_governor.py` before any spend; respect the cap.
- `stripe-operations` — the allowed Stripe verbs (TEST first) + what is gated/refused.
- `money-halt-protocol` — the money-specific halt-before-acting wrapper (notify + poll).
- `recall-learnings` — load accumulated operator feedback + prior lessons (read-only).

Plus paperclipai-bundled skills wired by `bootstrap-new-agents.sh`
(`paperclipai/paperclip/paperclip` etc.).
