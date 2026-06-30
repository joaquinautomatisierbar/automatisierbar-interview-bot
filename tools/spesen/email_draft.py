"""email_draft.py — the ready-to-send accountant mail shown on month-close.

The KnowBody sends the ZIP themselves via Outlook (client's explicit wish), so we
just hand them a finished draft: subject + body + a mailto: link they can tap.
German, Sie-Form, no em-dashes (house style).
"""

from __future__ import annotations

import urllib.parse

_MONTHS_DE = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
              "August", "September", "Oktober", "November", "Dezember"]


def _month_label(jm: str) -> str:
    try:
        y, m = jm.split("-")
        return f"{_MONTHS_DE[int(m)]} {y}"
    except Exception:
        return jm


def _chf(n) -> str:
    try:
        return f"{float(n or 0):,.2f}".replace(",", "'")
    except (TypeError, ValueError):
        return "0.00"


def build_accountant_email(month_data: dict, accountant_email: str = "") -> dict:
    """Return {to, subject, body, mailto}. accountant_email may be empty (the
    KnowBody fills the recipient in Outlook); the rest is ready to paste."""
    d = month_data
    name = (d.get("knowbody") or {}).get("name", "")
    monat = _month_label(d.get("jahr_monat", ""))
    anzahl = d.get("anzahl", 0)
    total = _chf(d.get("total_chf"))
    weiter = float(d.get("summe_weiter_chf") or 0)

    subject = f"Spesenabrechnung {name} {monat}"

    lines = [
        "Guten Tag",
        "",
        f"anbei meine Spesenabrechnung für {monat}.",
        "",
        f"Anzahl Belege: {anzahl}",
        f"Total: CHF {total}",
    ]
    if weiter > 0:
        lines.append(f"Davon weiterverrechenbar an Kunden: CHF {_chf(weiter)}")
    lines += [
        "",
        "Im ZIP finden Sie die PDF-Abrechnung, eine Excel-Übersicht und alle "
        "Originalbelege.",
        "",
        "Freundliche Grüsse",
        name,
    ]
    body = "\n".join(lines)

    query = urllib.parse.urlencode({"subject": subject, "body": body}, quote_via=urllib.parse.quote)
    mailto = f"mailto:{accountant_email}?{query}"

    return {"to": accountant_email, "subject": subject, "body": body, "mailto": mailto}
