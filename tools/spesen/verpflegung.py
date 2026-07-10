"""verpflegung.py — the monthly Verpflegungs- & Kilometerspesen engine. Pure + offline.

Mirrors the client's "Verpflegungs- und Kilometerspesen" sheet: per-day meal
per-diems (Frühstück / Mittag / Nacht), each with a coverage marker (VISA/Bar/KS),
plus a monthly Kilometer block (Stand Anfang/Ende -> Total -> Firma-Anteil 5/7 ->
Entschädigung at the per-km rate).

Every CHF figure resolves through the tariffs (config.PAUSCHALTARIFE or a DB row
list) via pauschalen.resolve_by_code — NEVER hardcoded — so a placeholder rate
yields a count but no guessed amount (same guarantee as pauschalen.py). Kept free of
any DB import so tests run with plain dicts.
"""

from __future__ import annotations

try:
    from . import config, pauschalen
except ImportError:  # pragma: no cover - direct-script run
    import config, pauschalen


def _deckung_breakdown(day_rows: list, claim_key: str, deckung_key: str) -> dict:
    """Count, over the claimed days, how each meal was covered (VISA/Bar/KS)."""
    out = {opt: 0 for opt in config.DECKUNG_OPTIONS}
    for r in day_rows:
        if r.get(claim_key):
            d = r.get(deckung_key)
            if d in out:
                out[d] += 1
    return out


def compute_verpflegung_summary(day_rows: list, km_row: dict | None,
                                tariffs: list | None = None,
                                km_factor: float | None = None) -> dict:
    """Aggregate a month of day rows + the km row into per-meal + km totals.

    day_rows: dicts with fr_claimed/fr_deckung, mi_claimed/mi_deckung,
              na_claimed/na_deckung (attendance flags are ignored for the money).
    km_row:   dict with km_start, km_end, km_firma_override (or None / missing).

    Guarantee: a CLAIMED meal (or km) whose rate is still a placeholder makes its
    own total None AND poisons the affected grand total to None, so a wrong CHF
    amount can never reach a deliverable. A meal with count 0 never poisons.
    """
    day_rows = day_rows or []
    if km_factor is None:
        km_factor = config.KM_FIRMA_FACTOR

    meals: dict = {}
    verpflegung_total = 0.0
    verpflegung_known = True  # flips False if a claimed meal has an unknown rate
    slots = [
        ("fruehstueck", "fr_claimed", "fr_deckung"),
        ("mittag", "mi_claimed", "mi_deckung"),
        ("nacht", "na_claimed", "na_deckung"),
    ]
    for slot, claim_key, deckung_key in slots:
        code = config.VERPFLEGUNG_MEALS.get(slot)
        resolved = pauschalen.resolve_by_code(code, tariffs=tariffs)
        rate = resolved.get("rate_chf")
        is_ph = bool(resolved.get("is_placeholder")) or rate is None
        count = sum(1 for r in day_rows if r.get(claim_key))
        if count == 0:
            total = 0.0
        elif is_ph:
            total = None
            verpflegung_known = False
        else:
            total = round(count * float(rate), 2)
            verpflegung_total = round(verpflegung_total + total, 2)
        meals[slot] = {
            "count": count,
            "rate_chf": rate,
            "total_chf": total,
            "is_placeholder": is_ph,
            "deckung": _deckung_breakdown(day_rows, claim_key, deckung_key),
        }
    verpflegung_total_chf = verpflegung_total if verpflegung_known else None

    km = _compute_km(km_row, tariffs, km_factor)

    # Grand total: None if any known component is unknown (poisoned), else the sum.
    if verpflegung_total_chf is None or km["entschaedigung_chf"] is None:
        gesamt = None
    else:
        gesamt = round(verpflegung_total_chf + km["entschaedigung_chf"], 2)

    return {
        "meals": meals,
        "verpflegung_total_chf": verpflegung_total_chf,
        "km": km,
        "gesamttotal_chf": gesamt,
    }


def _num(v):
    """Parse to float or None (blank/garbage -> None)."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _compute_km(km_row: dict | None, tariffs: list | None, km_factor: float) -> dict:
    """Kilometer block: Total = Ende - Anfang; Firma = override or Total*factor
    (rounded to whole km, as on the client sheet); Entschädigung = Firma * rate."""
    resolved = pauschalen.resolve_by_code(config.KM_CODE, tariffs=tariffs)
    rate = resolved.get("rate_chf")
    rate_is_ph = bool(resolved.get("is_placeholder")) or rate is None

    row = km_row or {}
    start = _num(row.get("km_start"))
    end = _num(row.get("km_end"))
    override = _num(row.get("km_firma_override"))

    total = None
    if start is not None and end is not None and end >= start:
        total = round(end - start)

    if override is not None:
        firma = round(override)
    elif total is not None:
        firma = round(total * km_factor)
    else:
        firma = None

    # No km driven -> nothing to reimburse (0, not "unknown"). Km driven but rate
    # still a placeholder -> None (poison). Otherwise firma * rate.
    if not firma:  # None or 0
        entschaedigung = 0.0
    elif rate_is_ph:
        entschaedigung = None
    else:
        entschaedigung = round(firma * float(rate), 2)

    return {
        "start": start,
        "end": end,
        "total": total,
        "firma": firma,
        "firma_is_override": override is not None,
        "rate_chf": rate,
        "is_placeholder": rate_is_ph,
        "entschaedigung_chf": entschaedigung,
    }
