---
name: stripe-operations
description: >
  The allowed Stripe verbs for Revenue Lab Finance-Ops, what is gated behind a halt, and what
  the tool refuses outright (account creation, KYC, payouts). Use before operating Stripe. The
  operator owns the Stripe account; you are a scoped API caller.
---

# Stripe Operations (legal-shell model)

`tools/stripe_ops.py` wraps the Stripe API. **The operator owns the account.** You create
charge surfaces and read state; you never own, withdraw, or onboard. The tool itself enforces
this — do not try to work around a refusal.

## Mode: TEST by default, LIVE only when triple-gated

- The tool reads `STRIPE_API_KEY_TEST` / `STRIPE_API_KEY_LIVE` from env (bound as `secret_ref`).
- It **defaults to TEST** and **refuses LIVE unless `STRIPE_LIVE_CONFIRMED=1`** is set.
- LIVE also requires an operator `yes` via `money-halt-protocol` first. Three independent gates.

## Allowed verbs (TEST first; LIVE only after operator approval)

```bash
python3 tools/stripe_ops.py create-product "<name>" "<description>"
python3 tools/stripe_ops.py create-price <product_id> <amount_cents> [currency=chf]
python3 tools/stripe_ops.py create-payment-link <price_id> [quantity=1]
python3 tools/stripe_ops.py create-invoice <customer> '<line_items_json>'
python3 tools/stripe_ops.py read-balance
python3 tools/stripe_ops.py list-recent-charges [limit=10]
python3 tools/stripe_ops.py retrieve-charge <charge_id>
```

After a real charge clears, verify with `retrieve-charge`, then record it via the
`check-budget-governor` skill (`record-revenue`).

## REFUSED outright (the tool raises — these are operator-only, by design)

- ❌ `create_account` / Stripe Connect onboarding — account + KYC are human actions.
- ❌ any KYC / identity verification.
- ❌ `payout` / withdrawal / transfer — moving money OUT is never an agent action.

## Gated behind a halt (use `money-halt-protocol` first)

- Switching TEST → LIVE (set `STRIPE_LIVE_CONFIRMED=1` only after the operator says yes).
- Creating the first LIVE payment surface for an offer.
- Any charge/invoice above CHF 200.

## Workflow for a new offer (typical)

1. (TEST) create-product → create-price → create-payment-link. Open the link; pay with Stripe
   test card `4242 4242 4242 4242` to confirm it works.
2. Report the working TEST link to the CEO.
3. Only when the operator approves go-live: halt → on `yes`, set `STRIPE_LIVE_CONFIRMED=1`, bind
   the LIVE key, recreate the product/price/link in LIVE, hand the LIVE link to the operator.
