"""currency.py — foreign-currency -> CHF at the receipt date. Pure-ish + mockable.

Primary source: frankfurter.dev (ECB reference rates, keyless, historical date).
  GET https://api.frankfurter.dev/v1/{YYYY-MM-DD}?base=EUR&symbols=CHF
  -> {"amount":1,"base":"EUR","date":"2026-01-20","rates":{"CHF":0.95}}
ECB has no weekend/holiday fix, so frankfurter returns the latest prior business
day; we keep its returned `date` as the effective Kursdatum.

If the lookup fails for any reason, convert_to_chf returns ok=False with
betrag_chf=None so the route falls back to manual CHF entry (mandatory fallback,
never a silent zero). All HTTP goes through _fetch_json so tests monkeypatch it
and never touch the network.
"""

from __future__ import annotations

import json
import urllib.request

FRANKFURTER_BASE = "https://api.frankfurter.dev/v1"
HTTP_TIMEOUT = 8


def _fetch_json(url: str) -> dict:
    """GET a URL and parse JSON. Raises on any HTTP/parse error (caller catches).
    Isolated so tests can monkeypatch it with a fixture."""
    req = urllib.request.Request(url, headers={"User-Agent": "KnowSpesen/1.0"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def convert_to_chf(amount, currency: str, date: str) -> dict:
    """Convert `amount` in `currency` to CHF using the rate at `date` (YYYY-MM-DD).

    Returns:
      {ok, betrag_chf, wechselkurs, kurs_quelle, kurs_datum, error}
    - currency == CHF -> identity, no network.
    - success -> ok=True, betrag_chf rounded to 2 dp, wechselkurs + effective date.
    - failure -> ok=False, betrag_chf=None, error set (route asks for manual CHF).
    """
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        return {"ok": False, "betrag_chf": None, "wechselkurs": None,
                "kurs_quelle": None, "kurs_datum": None, "error": "Betrag ungültig"}

    cur = (currency or "CHF").strip().upper()
    if cur == "CHF":
        return {"ok": True, "betrag_chf": round(amt, 2), "wechselkurs": 1.0,
                "kurs_quelle": "DIREKT_CHF", "kurs_datum": date, "error": None}

    d = (date or "").strip()
    url = f"{FRANKFURTER_BASE}/{d}?base={cur}&symbols=CHF"
    try:
        data = _fetch_json(url)
        rate = (data.get("rates") or {}).get("CHF")
        if rate is None:
            return {"ok": False, "betrag_chf": None, "wechselkurs": None,
                    "kurs_quelle": None, "kurs_datum": None,
                    "error": f"Kein CHF-Kurs für {cur} am {d}"}
        rate = float(rate)
        return {"ok": True, "betrag_chf": round(amt * rate, 2), "wechselkurs": rate,
                "kurs_quelle": "frankfurter.dev", "kurs_datum": data.get("date") or d,
                "error": None}
    except Exception as e:  # network down, 404, bad JSON -> manual fallback
        return {"ok": False, "betrag_chf": None, "wechselkurs": None,
                "kurs_quelle": None, "kurs_datum": None,
                "error": f"Wechselkurs nicht verfügbar: {type(e).__name__}"}
