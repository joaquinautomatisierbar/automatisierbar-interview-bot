#!/usr/bin/env python3
"""Revenue Lab Stripe tool — legal-shell model: the OPERATOR owns the Stripe account; agents
are scoped API callers that create charge surfaces and read state, never owners.

Hard safety properties (all enforced in code, unit-tested offline in tools/tests/test_stripe_ops.py):
  • Defaults to TEST mode. Refuses LIVE unless STRIPE_LIVE_CONFIRMED=1 AND a real sk_live_ key.
  • Refuses to run a live key sitting in the TEST slot (anti-footgun).
  • Hard-refuses operator-only actions: create_account / Connect onboarding, payout, transfer.
    Moving money OUT and KYC are never agent actions — the operator's hand only.

Keys come from env (bound as secret_ref on the live agent):
  STRIPE_API_KEY_TEST   — test-mode secret key (sk_test_…), used by default
  STRIPE_API_KEY_LIVE   — live-mode secret key (sk_live_…), used ONLY when STRIPE_LIVE_CONFIRMED=1
  STRIPE_LIVE_CONFIRMED — "1" to arm LIVE mode (set only after the operator approves via halt)

CLI:
  python3 tools/stripe_ops.py create-product "<name>" "<description>"
  python3 tools/stripe_ops.py create-price <product_id> <amount_cents> [currency=chf]
  python3 tools/stripe_ops.py create-payment-link <price_id> [quantity=1]
  python3 tools/stripe_ops.py create-invoice <customer_id>
  python3 tools/stripe_ops.py finalize-invoice <invoice_id>
  python3 tools/stripe_ops.py read-balance
  python3 tools/stripe_ops.py list-recent-charges [limit=10]
  python3 tools/stripe_ops.py retrieve-charge <charge_id>
"""
import json
import os
import sys

STRIPE_API = "https://api.stripe.com/v1"
_TEST_PREFIX = "sk_test_"
_LIVE_PREFIX = "sk_live_"


# ── mode resolution (the core safety gate) ───────────────────────────────────
def resolve_mode(env=None):
    """Return ('test'|'live', api_key). Defaults to test; LIVE requires explicit
    confirmation AND a real live key. Raises RuntimeError on any unsafe configuration."""
    env = os.environ if env is None else env
    confirmed = env.get("STRIPE_LIVE_CONFIRMED") == "1"

    if confirmed:
        key = env.get("STRIPE_API_KEY_LIVE")
        if not key:
            raise RuntimeError("STRIPE_LIVE_CONFIRMED=1 but STRIPE_API_KEY_LIVE is not set")
        if not key.startswith(_LIVE_PREFIX):
            raise RuntimeError("STRIPE_LIVE_CONFIRMED=1 but the key is not a live key (sk_live_)")
        return "live", key

    key = env.get("STRIPE_API_KEY_TEST")
    if not key:
        raise RuntimeError(
            "no STRIPE_API_KEY_TEST set. Set a test key, or set STRIPE_LIVE_CONFIRMED=1 "
            "with a live key (only after operator approval).")
    if key.startswith(_LIVE_PREFIX):
        raise RuntimeError("a LIVE key (sk_live_) is in the TEST slot — refusing to run it as test")
    return "test", key


# ── operator-only actions: HARD REFUSED (never agent actions) ─────────────────
def create_account(*_a, **_k):
    raise NotImplementedError(
        "operator-only: creating a Stripe account / Connect onboarding requires human KYC. "
        "Agents never create accounts.")


def payout(*_a, **_k):
    raise NotImplementedError(
        "operator-only: moving money OUT (payout/withdrawal) is never an agent action. "
        "The operator owns the bank; funds leave only by the operator's hand.")


def transfer(*_a, **_k):
    raise NotImplementedError(
        "operator-only: transfers move money and are never an agent action.")


# ── HTTP (requests imported lazily so the guards above test without the dependency) ──
def _request(method, path, data=None, env=None):
    import requests  # lazy: keeps offline guard tests dependency-free
    mode, key = resolve_mode(env)
    resp = requests.request(
        method, f"{STRIPE_API}{path}",
        auth=(key, ""), data=data or {}, timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Stripe {method} {path} -> {resp.status_code}: {resp.text[:300]}")
    out = resp.json()
    out["_stripe_mode"] = mode  # surface which mode the call actually ran in
    return out


# ── allowed verbs ────────────────────────────────────────────────────────────
def create_product(name, description="", env=None):
    return _request("POST", "/products", {"name": name, "description": description}, env)


def create_price(product_id, unit_amount, currency="chf", env=None):
    return _request("POST", "/prices", {
        "product": product_id, "unit_amount": int(unit_amount), "currency": currency,
    }, env)


def create_payment_link(price_id, quantity=1, env=None):
    return _request("POST", "/payment_links", {
        "line_items[0][price]": price_id, "line_items[0][quantity]": int(quantity),
    }, env)


def create_invoice(customer_id, env=None):
    return _request("POST", "/invoices", {"customer": customer_id}, env)


def finalize_invoice(invoice_id, env=None):
    return _request("POST", f"/invoices/{invoice_id}/finalize", {}, env)


def read_balance(env=None):
    return _request("GET", "/balance", None, env)


def list_recent_charges(limit=10, env=None):
    return _request("GET", f"/charges?limit={int(limit)}", None, env)


def retrieve_charge(charge_id, env=None):
    return _request("GET", f"/charges/{charge_id}", None, env)


# ── CLI ──────────────────────────────────────────────────────────────────────
def _cli(argv):
    if not argv:
        print(__doc__)
        return 0
    cmd, a = argv[0], argv[1:]
    try:
        if cmd == "create-product":
            r = create_product(a[0], a[1] if len(a) > 1 else "")
        elif cmd == "create-price":
            r = create_price(a[0], a[1], a[2] if len(a) > 2 else "chf")
        elif cmd == "create-payment-link":
            r = create_payment_link(a[0], a[1] if len(a) > 1 else 1)
        elif cmd == "create-invoice":
            r = create_invoice(a[0])
        elif cmd == "finalize-invoice":
            r = finalize_invoice(a[0])
        elif cmd == "read-balance":
            r = read_balance()
        elif cmd == "list-recent-charges":
            r = list_recent_charges(a[0] if a else 10)
        elif cmd == "retrieve-charge":
            r = retrieve_charge(a[0])
        else:
            print(f"unknown command: {cmd}\n{__doc__}")
            return 2
    except (RuntimeError, NotImplementedError) as e:
        print(f"REFUSED/ERROR: {e}", file=sys.stderr)
        return 1
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
