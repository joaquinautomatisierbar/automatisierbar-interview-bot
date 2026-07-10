"""config.py — the single edit-point for KnowSpesen domain values.

Everything the client might tweak lives here so a change is one obvious place,
not scattered across modules. When the KnowGravity Regelwerk arrives, the ONLY
edits needed are the `rate_chf`/`is_placeholder` values in PAUSCHALTARIFE below
(or, in prod, a row update in the `pauschaltarife` table — db.seed_pauschalen()
re-syncs from here on every startup for any code with is_placeholder unchanged).

NOTHING here is invented as a hard CHF figure unless the client actually told us:
known per-diems are seeded with a real rate; everything still unknown is marked
is_placeholder=True with rate_chf=None so it can NEVER silently produce a wrong
amount on a client deliverable.
"""

from __future__ import annotations

import re as _re

# --- Kontroll-Bestätigung (attestation on month-close) --------------------------
# Before a KnowBody closes a month, they must TYPE this exact sentence. It is stored
# with their name + timestamp and printed on the PDF + accountant mail, so a wrong
# expense is the submitter's responsibility, not ours. Single source of truth: the
# frontend gets it via /api/spesen/config, the route validates against it, the PDF
# renders it. Verbatim wording is the operator's; edit here to change it everywhere.
ATTESTATION_TEXT = (
    "Ich bestätige hiermit dass ich die Spesen kontrolliert habe, "
    "diese wahrheitsgetreu sind und genehmige diese für die Weiterleitung."
)


def _norm_attest(s: str) -> str:
    """Normalise for a forgiving-but-real comparison: trim, collapse whitespace,
    lowercase. The point is that they actually TYPE the sentence, not that they
    match stray double-spaces or capitalisation."""
    return _re.sub(r"\s+", " ", (s or "").strip().lower())


def attestation_matches(typed: str) -> bool:
    """True if `typed` matches ATTESTATION_TEXT (normalised)."""
    return bool(typed) and _norm_attest(typed) == _norm_attest(ATTESTATION_TEXT)


# --- Global rule (from the interview: Steueramt-Vereinbarung) -------------------
# Pauschalspesen under this amount are not individually reimbursable; they get
# collected in the "Kaffeekasse" and excluded from the monthly ZIP.
MIN_REIMBURSE_CHF = 50.0

# The CHF-50 minimum applies to *receipted* items too, not only Pauschalen: the
# client's own "KNOWEXPENCESS" Spesenaufstellung (references/knowgravity/) prints
# "erst Spesen ab 50.- können ausgewiesen werden" over the receipted-expense table.
# So we keep the sweep on by default; the SharePoint/handling detail for those
# small items is still open with Markus, but that no longer affects this toggle.
KAFFEEKASSE_ALSO_SMALL_RECEIPTS = True


# --- Beleg categories (Kategorie) -----------------------------------------------
# From the interview: Mahlzeit / Transport / Material / Unterkunft / Sonderspese.
CATEGORIES = [
    "Mahlzeit",
    "Transport",
    "Material",
    "Unterkunft",
    "Sonderspese",
]

# Optional free-text sub-category suggestions per category (the field stays free
# text; these only drive a datalist in the UI).
SUBCATEGORY_HINTS = {
    "Mahlzeit": ["Geschäftsessen mit Kunden", "Mittagessen beim Kunden", "Frühstück", "Verpflegung"],
    "Transport": ["SBB / Bahn", "Flug", "Taxi", "Parking", "Auto (km)"],
    "Material": ["Büromaterial", "Software-Lizenz", "Hardware"],
    "Unterkunft": ["Hotel", "Übernachtung"],
    "Sonderspese": ["Lieferantenrechnung", "Diverses"],
}


# --- Payment methods (Zahlungsart) ----------------------------------------------
# From the interview: Firmenkreditkarte, private Kreditkarte, Cash, Revolut,
# and the "Lieferantenrechnung an die Firma" (normaler Rechnungsprozess) path.
# NOTE (2026-07-10): the client's real Spesenaufstellung uses a simpler taxonomy —
# Bar / CC (Credit Card) / EC (EC-Debit). Aligning our list to theirs is a proposed
# change flagged for Markus; left as-is until confirmed so no data model churn.
PAYMENT_METHODS = [
    "Firmenkreditkarte",
    "Privat-Kreditkarte",
    "Privat-Cash",
    "Revolut",
    "Firmenrechnung",
]


# --- Currencies offered in the dropdown -----------------------------------------
# CHF first (default). frankfurter.dev (ECB) covers all of these.
CURRENCIES = ["CHF", "EUR", "USD", "GBP"]


# --- Pauschaltarife (per-diem rates) --------------------------------------------
# code        machine key (also stored on the beleg)
# label       what the KnowBody sees
# rate_chf    fixed CHF amount (None = UNKNOWN, awaiting Regelwerk)
# unit        'pauschale' (flat) | 'pro_km' | 'pro_nacht'
# is_placeholder  True  -> rate unknown; UI shows "Tarif folgt", excluded from totals
#
# KNOWN — confirmed by the client's own example sheets (references/knowgravity/,
# "Km_Verpflegungs-Spesen_2026_MS.pdf"), 2026-07-10:
#   - Mittagessen              = CHF 30   (interview)
#   - Frühstück (Start <07:30) = CHF 10   (interview; sheet trigger column "<07:30")
#   - Nachtessen (Arbeit >19:30) = CHF 30 (sheet column header "SFr. 30")
#   - Autokilometer            = CHF 0.70/km (derived: 200.00 CHF / 286 km); Firma-
#                                Anteil = 5/7 der Monats-km (KM_FIRMA_FACTOR below)
# STILL UNKNOWN (placeholder until the written Reglement arrives):
#   - Übernachtung (no data in the examples)
# REMOVED: sbb_pauschale — Markus confirmed SBB e-tickets are used directly as a
#   receipt (a normal Beleg via PDF upload), so there is no SBB per-diem. Pruned
#   from any existing DB in db._migrate().
PAUSCHALTARIFE = [
    {
        "code": "mittagessen_kunde",
        "label": "Mittagessen",
        "rate_chf": 30.0,
        "unit": "pauschale",
        "is_placeholder": False,
    },
    {
        "code": "fruehstueck_vor_8",
        "label": "Frühstück (Start vor 07:30)",
        "rate_chf": 10.0,
        "unit": "pauschale",
        "is_placeholder": False,
    },
    {
        "code": "abendessen_kunde",
        "label": "Nachtessen (Arbeit über 19:30)",
        "rate_chf": 30.0,
        "unit": "pauschale",
        "is_placeholder": False,
    },
    {
        "code": "auto_km",
        "label": "Autokilometer (pro km)",
        "rate_chf": 0.70,
        "unit": "pro_km",
        "is_placeholder": False,
    },
    {
        "code": "uebernachtung",
        "label": "Übernachtungspauschale (pro Nacht)",
        "rate_chf": None,
        "unit": "pro_nacht",
        "is_placeholder": True,
    },
]


def pauschale_by_code(code: str) -> dict | None:
    """Look up a tariff config row by code, or None."""
    for t in PAUSCHALTARIFE:
        if t["code"] == code:
            return t
    return None


def known_categories() -> set:
    return set(CATEGORIES)


def known_payment_methods() -> set:
    return set(PAYMENT_METHODS)


# --- Verpflegungs- & Kilometerblatt (monthly per-diem grid) ---------------------
# Mirrors the client's "Verpflegungs- und Kilometerspesen" sheet. All CHF figures
# resolve through PAUSCHALTARIFE above (never hardcoded), so a rate change is still
# one edit in this file.
#
# Meal slot -> PAUSCHALTARIFE code. The grid engine (verpflegung.py) looks up the
# rate + is_placeholder by these codes, so a placeholder meal shows a count but
# never a guessed CHF amount.
VERPFLEGUNG_MEALS = {
    "fruehstueck": "fruehstueck_vor_8",   # earned when the workday starts before 07:30
    "mittag": "mittagessen_kunde",         # midday meal
    "nacht": "abendessen_kunde",           # earned when work runs past 19:30
}

# How each claimed meal is covered on the sheet (VISA = company card, Bar = cash,
# KS = Kaffeekasse). Validated at the route and enforced by a CHECK in db.py.
DECKUNG_OPTIONS = ["VISA", "Bar", "KS"]

# Kilometer: the company-reimbursed share defaults to 5/7 of the month's total km
# (per the client sheet: "Gefahrene Kilometer Firma (5/7)"), overridable per month.
# The per-km rate is the auto_km PAUSCHALTARIFE row.
KM_CODE = "auto_km"
KM_FIRMA_FACTOR = 5 / 7
