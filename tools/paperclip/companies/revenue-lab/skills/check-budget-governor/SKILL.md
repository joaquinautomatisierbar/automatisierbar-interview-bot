---
name: check-budget-governor
description: >
  Read the Revenue Lab budget governor BEFORE any spend, and record spend/revenue after money
  moves. Enforces the $300 lifetime cap + the 21-day-zero-revenue kill-switch. Use whenever an
  action would cost money or whenever a real payment clears.
---

# Check Budget Governor

The governor (`tools/revenue_governor.py`) is the deterministic guardrail for the $300 cap. It
is NOT an agent — it is code. Your job is to consult it before spending and feed it after money
moves. Never spend "around" it.

## Before ANY external/business spend

```bash
python3 tools/revenue_governor.py status
```

This prints `status`, `spent_usd`, `revenue_usd`, `remaining_usd`, and days-elapsed. Then, in
code or via the CLI, check headroom for your specific spend:

```bash
python3 tools/revenue_governor.py can-spend <estimated_usd>
# exits 0 + prints "OK <remaining>" if allowed; exits 1 + reason if not
```

If `status != active` (tripped/paused) or `can-spend` says no → **STOP. Do not spend.** Tell
the CEO and the operator. Compute is on the Claude Max plan (~$0), so this is only for
external/business costs (paid APIs, ads, domains, tools, Stripe fees).

## After money moves

- **Spend happened:** `python3 tools/revenue_governor.py record-spend <id> <category> <usd> "<note>"`
  (categories: `tools` | `ads` | `stripe_fee` | `other`). Idempotent by `<id>`.
- **Real payment cleared (Finance-Ops only, after operator-approved LIVE):**
  `python3 tools/revenue_governor.py record-revenue <id> <usd> <stripe_charge_id> "<note>"`.

## The kill-switch (know what trips it)

The governor auto-trips and pauses ALL agents when **`spent_usd >= 300`** OR
**`days_elapsed >= 21 AND revenue_usd == 0`**. The second (time/value) trip is the primary
safety: it stops a fleet that's busy producing nothing on "free" subscription compute. If you
ever see `status` is tripped, confirm the pause ran and notify the operator — do not un-pause
without an explicit operator instruction.

## $5-per-issue sub-cap

`python3 tools/revenue_governor.py issue-spend <issue_id>` sums spend on one issue. If an issue
crosses $5 with no artifact/answer/progress, stop and halt to the operator (the CLAUDE.md rule).
