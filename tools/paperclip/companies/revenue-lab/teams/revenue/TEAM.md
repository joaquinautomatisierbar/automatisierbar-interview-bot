---
name: Revenue
description: A 3-agent team that stands up a fast-to-revenue productized digital service and earns its first cleared payment — under a hard $300 burn cap, operator as legal/financial shell and decision-gate.
slug: revenue
manager: ../../agents/ceo/AGENTS.md
includes:
  - ../../agents/builder/AGENTS.md
  - ../../agents/finance-ops/AGENTS.md
tags:
  - revenue
  - experiment
  - governed
---

The Revenue team tries to earn one honest dollar from a productized digital service, then —
only if the unit economics are positive and repeatable — scale toward $10k/mo. Led by the
**CEO / Revenue Lead**.

## Flow

```
Operator: "find + sell a productized service"
   │
   ├──► CEO picks ONE offer (library + ICP grounded)
   │     │  ── HALT for operator approval ──
   │     ▼
   ├──► Builder researches demand (read-only) + builds fulfilment asset (INACTIVE)
   │     │            + drafts outreach + landing copy (artifacts only)
   │     ▼
   ├──► Finance-Ops creates Stripe product/price/payment-link (TEST mode)
   │     │  ── HALT before TEST→LIVE ──
   │     ▼
   └──► Operator approves + sends outreach → payment clears → Finance-Ops records revenue
```

## Hard governance (the whole point of this team)

- **$300 lifetime burn cap**, enforced deterministically by `tools/revenue_governor.py`. Trips
  on `spent >= $300` OR `21 days with zero revenue`. On trip: all 3 agents paused + operator paged.
- **Legal-shell:** operator owns entity/Stripe/bank; agents are scoped API callers, never owners.
- **Bike Method Phase 1:** every money/external-trust action halts for operator approval.
- **No agent hires agents.** Team fixed at 3.

## Outside the team

- **The operator (Joaquin)** is the legal/financial shell, the decision-gate on all money +
  external-trust actions, and the one who sends real outbound + closes. Agents prepare; the
  human acts. Reached via the dedicated Revenue Lab Telegram channel.
