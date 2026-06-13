#!/usr/bin/env python3
"""Tests for tools/stripe_ops.py — the legal-shell Stripe guards.

Safety-critical, all offline (no network, no real keys): proves the tool defaults to TEST,
refuses LIVE unless explicitly confirmed, refuses to run a live key in the test slot, and
hard-refuses account-creation / payouts (operator-only actions). Run:

    python3 tools/tests/test_stripe_ops.py     # exit 0 = all pass, 1 = failure
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # tools/
import stripe_ops as so

fails = []
def chk(label, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + label + (f"  {extra}" if extra else ""))
    if not cond:
        fails.append(label)

def raises(fn, exc):
    try:
        fn()
        return False
    except exc:
        return True
    except Exception:
        return False

TEST = "sk_test_abc123"
LIVE = "sk_live_xyz789"

# ── mode resolution ──────────────────────────────────────────────────────────
mode, key = so.resolve_mode({"STRIPE_API_KEY_TEST": TEST})
chk("only TEST key → test mode", mode == "test" and key == TEST, f"{mode},{key}")

# LIVE key present but NOT confirmed → must fall back to TEST (the core safety property)
mode, key = so.resolve_mode({"STRIPE_API_KEY_TEST": TEST, "STRIPE_API_KEY_LIVE": LIVE})
chk("LIVE key present, unconfirmed → still test", mode == "test" and key == TEST, f"{mode},{key}")

# LIVE confirmed + LIVE key → live mode
mode, key = so.resolve_mode({"STRIPE_API_KEY_LIVE": LIVE, "STRIPE_LIVE_CONFIRMED": "1"})
chk("LIVE key + confirmed → live mode", mode == "live" and key == LIVE, f"{mode},{key}")

# LIVE confirmed but NO live key → error (don't silently use test in 'live' intent)
chk("LIVE confirmed but no live key → raises",
    raises(lambda: so.resolve_mode({"STRIPE_API_KEY_TEST": TEST, "STRIPE_LIVE_CONFIRMED": "1"}), RuntimeError))

# no keys at all → error
chk("no keys → raises", raises(lambda: so.resolve_mode({}), RuntimeError))

# anti-footgun: a live key sitting in the TEST slot must be refused
chk("live key in TEST slot → raises",
    raises(lambda: so.resolve_mode({"STRIPE_API_KEY_TEST": LIVE}), RuntimeError))

# anti-footgun: confirmed-live but the 'live' key is actually a test key → refused
chk("test key in LIVE slot (confirmed) → raises",
    raises(lambda: so.resolve_mode({"STRIPE_API_KEY_LIVE": TEST, "STRIPE_LIVE_CONFIRMED": "1"}), RuntimeError))

# ── hard refusals (operator-only actions) ────────────────────────────────────
chk("create_account → NotImplementedError", raises(lambda: so.create_account("Acme"), NotImplementedError))
chk("payout → NotImplementedError", raises(lambda: so.payout(1000), NotImplementedError))
chk("transfer → NotImplementedError", raises(lambda: so.transfer(1000, "acct_x"), NotImplementedError))

# ── summary ──────────────────────────────────────────────────────────────────
print()
if fails:
    print(f"❌ {len(fails)} FAILED: {fails}")
    sys.exit(1)
print("✅ all stripe_ops guard tests passed")
