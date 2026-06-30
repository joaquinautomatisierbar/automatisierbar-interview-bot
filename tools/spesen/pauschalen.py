"""pauschalen.py — the per-diem (Pauschale) engine. Pure + offline-testable.

Two jobs:
  1. resolve_pauschale(tariff, menge)  -> the CHF amount for a flat / per-km /
     per-night tariff, OR a clear "Tarif folgt" signal for an unknown (placeholder)
     rate so a wrong number can never reach a client deliverable.
  2. is_kaffeekasse(betrag_chf, ist_pauschale) -> the CHF-50 minimum rule: items
     below the threshold are Kaffeekasse and get excluded from the monthly ZIP.

Kept free of any DB import: routes pass a tariff dict (a DB row or a config row),
so tests run with plain dicts and no database.
"""

from __future__ import annotations

try:
    from . import config
except ImportError:  # pragma: no cover - direct-script run
    import config


def is_kaffeekasse(betrag_chf, ist_pauschale: bool = False) -> bool:
    """True if this item is a Kaffeekasse candidate (excluded from the ZIP).

    - A Pauschale below CHF 50 is never individually reimbursable (Steueramt rule)
      -> always Kaffeekasse.
    - A receipted item below CHF 50 -> Kaffeekasse only if the client wants small
      receipts swept too (config.KAFFEEKASSE_ALSO_SMALL_RECEIPTS, default True).
    - A None amount (placeholder pauschale, no rate yet) -> not Kaffeekasse; it is
      handled separately and excluded as a placeholder.
    """
    if betrag_chf is None:
        return False
    try:
        amt = float(betrag_chf)
    except (TypeError, ValueError):
        return False
    if amt >= config.MIN_REIMBURSE_CHF:
        return False
    if ist_pauschale:
        return True
    return bool(config.KAFFEEKASSE_ALSO_SMALL_RECEIPTS)


def resolve_pauschale(tariff: dict, menge=1.0) -> dict:
    """Compute the CHF amount for a tariff dict {code,label,rate_chf,unit,is_placeholder}.

    Returns:
      {ok, is_placeholder, betrag_chf, label, unit, rate_chf, menge, error}
    - Unknown/placeholder rate -> ok=False, is_placeholder=True, betrag_chf=None,
      error="Tarif folgt …" (caller must NOT include it with a guessed amount).
    - 'pro_km'/'pro_nacht' -> rate * menge; 'pauschale' -> rate (menge ignored).
    """
    if not tariff:
        return {"ok": False, "is_placeholder": False, "betrag_chf": None,
                "label": "", "unit": "", "rate_chf": None, "menge": menge,
                "error": "Unbekannter Pauschal-Typ"}

    label = tariff.get("label", "")
    unit = tariff.get("unit", "pauschale")
    rate = tariff.get("rate_chf", None)
    is_ph = bool(tariff.get("is_placeholder")) or rate is None

    if is_ph:
        return {"ok": False, "is_placeholder": True, "betrag_chf": None,
                "label": label, "unit": unit, "rate_chf": None, "menge": menge,
                "error": "Tarif folgt (Regelwerk ausstehend)"}

    try:
        rate = float(rate)
    except (TypeError, ValueError):
        return {"ok": False, "is_placeholder": True, "betrag_chf": None,
                "label": label, "unit": unit, "rate_chf": None, "menge": menge,
                "error": "Tarif ungültig"}

    if unit in ("pro_km", "pro_nacht"):
        try:
            m = float(menge)
        except (TypeError, ValueError):
            m = 1.0
        if m <= 0:
            m = 1.0
        betrag = round(rate * m, 2)
    else:
        m = 1.0
        betrag = round(rate, 2)

    return {"ok": True, "is_placeholder": False, "betrag_chf": betrag,
            "label": label, "unit": unit, "rate_chf": rate, "menge": m, "error": None}


def resolve_by_code(code: str, menge=1.0, tariffs: list | None = None) -> dict:
    """Convenience: look the tariff up by code (from a provided list of DB rows, or
    config.PAUSCHALTARIFE) then resolve it."""
    source = tariffs if tariffs is not None else config.PAUSCHALTARIFE
    tariff = next((t for t in source if t.get("code") == code), None)
    return resolve_pauschale(tariff or {}, menge=menge)
