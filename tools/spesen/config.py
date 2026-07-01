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

# OPEN QUESTION for the client (in the follow-up mail): the CHF-50 minimum is
# stated for *Pauschalen*. Whether small *receipted* items (< 50, with a real
# Beleg) should also be swept into the Kaffeekasse is unconfirmed. The bot-spec
# generated from the client's own process said yes; we follow that by default,
# but it is a one-line toggle once Markus confirms.
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
# KNOWN (client stated these explicitly in the interview):
#   - Mittagessen beim Kunden = CHF 30
#   - Frühstück vor 8 Uhr      = CHF 10
# UNKNOWN (built as placeholders, 1 edit each once the Regelwerk arrives):
#   - Abendessen beim Kunden, Autokilometer, SBB-Klasse, Übernachtung
PAUSCHALTARIFE = [
    {
        "code": "mittagessen_kunde",
        "label": "Mittagessen beim Kunden",
        "rate_chf": 30.0,
        "unit": "pauschale",
        "is_placeholder": False,
    },
    {
        "code": "fruehstueck_vor_8",
        "label": "Frühstück vor 8 Uhr",
        "rate_chf": 10.0,
        "unit": "pauschale",
        "is_placeholder": False,
    },
    {
        "code": "abendessen_kunde",
        "label": "Abendessen beim Kunden",
        "rate_chf": None,
        "unit": "pauschale",
        "is_placeholder": True,
    },
    {
        "code": "auto_km",
        "label": "Autokilometer (pro km)",
        "rate_chf": None,
        "unit": "pro_km",
        "is_placeholder": True,
    },
    {
        "code": "uebernachtung",
        "label": "Übernachtungspauschale (pro Nacht)",
        "rate_chf": None,
        "unit": "pro_nacht",
        "is_placeholder": True,
    },
    {
        "code": "sbb_pauschale",
        "label": "SBB-Pauschale",
        "rate_chf": None,
        "unit": "pauschale",
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
