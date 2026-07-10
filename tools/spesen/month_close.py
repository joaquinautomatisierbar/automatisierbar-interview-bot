"""month_close.py — turn a KnowBody's month into the deliverable ZIP.

close_month(knowbody_id, jahr_monat, accountant_email) :
  1. read the month's belege (Kaffeekasse already excluded by db.belege_for_month)
  2. aggregate totals + per-category + weiterverrechenbar
  3. render PDF (report_pdf) + Excel (report_excel)
  4. bundle PDF + Excel + renamed receipt images + Begleitmail.txt into one ZIP
  5. finalize_close in a transaction (locks the included belege)
  6. return paths + the accountant email draft

An empty month is allowed (0 belege -> a valid "nichts zu verrechnen" ZIP), matching
the client's wish that everyone can submit a confirmation even with no expenses.
"""

from __future__ import annotations

import os
import re
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from . import db, report_pdf, report_excel, email_draft, capture
except ImportError:  # pragma: no cover - direct-script run
    import db, report_pdf, report_excel, email_draft, capture

TZ = ZoneInfo("Europe/Zurich")


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", (s or "").strip())[:40] or "x"


def build_month_data(knowbody: dict, jahr_monat: str, belege: list, attest: dict | None = None,
                     verpflegung_days: list | None = None, kilometer: dict | None = None,
                     verpflegung_summary: dict | None = None) -> dict:
    total = round(sum(float(b.get("betrag_chf") or 0) for b in belege), 2)
    kat_sums: dict = {}
    for b in belege:
        k = b.get("kategorie") or "Sonstige"
        kat_sums[k] = round(kat_sums.get(k, 0.0) + float(b.get("betrag_chf") or 0), 2)
    weiter = [b for b in belege if b.get("weiterverrechenbar")]
    summe_weiter = round(sum(float(b.get("betrag_chf") or 0) for b in weiter), 2)

    # Verpflegungs-/Kilometerblatt totals (kept separate from receipts; the client
    # sheet totals them independently). A None component means an unknown (placeholder)
    # rate — then the combined payout is left None rather than a guessed number.
    v_total = (verpflegung_summary or {}).get("verpflegung_total_chf")
    km_entsch = ((verpflegung_summary or {}).get("km") or {}).get("entschaedigung_chf")
    if v_total is None or km_entsch is None:
        total_auszahlung = None
    else:
        total_auszahlung = round(total + v_total + km_entsch, 2)

    return {
        "knowbody": {"name": knowbody.get("name", ""), "email": knowbody.get("email", "")},
        "jahr_monat": jahr_monat,
        "erstellt_am": datetime.now(TZ).date().isoformat(),
        "belege": belege,
        "total_chf": total,
        "kategorie_summen": kat_sums,
        "weiterverrechenbar": weiter,
        "summe_weiter_chf": summe_weiter,
        "anzahl": len(belege),
        "attest": attest or None,
        "verpflegung": {"days": verpflegung_days or [], "summary": verpflegung_summary or None},
        "kilometer": kilometer or None,
        "verpflegung_total_chf": v_total,
        "km_entschaedigung_chf": km_entsch,
        "total_auszahlung_chf": total_auszahlung,
    }


def _receipt_arcname(b: dict, nr: int) -> str:
    ext = os.path.splitext(b.get("bild_pfad") or "")[1] or ".jpg"
    datum = _safe(b.get("beleg_datum") or "")
    kat = _safe(b.get("kategorie") or "Beleg")
    betrag = _safe(f"{float(b.get('betrag_chf') or 0):.2f}")
    return f"Belege/{datum}_{kat}_{betrag}CHF_{nr:03d}{ext}"


def close_month(knowbody_id: int, jahr_monat: str, accountant_email: str = "",
                attest: dict | None = None) -> dict:
    kb = db.get_knowbody(knowbody_id)
    if not kb:
        return {"ok": False, "error": "KnowBody nicht gefunden"}

    belege = db.belege_for_month(knowbody_id, jahr_monat, include_kaffeekasse=False)
    v_days = db.list_verpflegung_month(knowbody_id, jahr_monat)
    v_summary = db.compute_verpflegung_summary(knowbody_id, jahr_monat)
    km_row = db.get_kilometer_monat(knowbody_id, jahr_monat)
    month_data = build_month_data(kb, jahr_monat, belege, attest=attest,
                                  verpflegung_days=v_days, kilometer=km_row,
                                  verpflegung_summary=v_summary)

    pdf_path = report_pdf.generate_spesen_pdf(month_data)
    xlsx_path = report_excel.generate_spesen_xlsx(month_data)
    email = email_draft.build_accountant_email(month_data, accountant_email)

    out_dir = os.path.dirname(pdf_path)
    name = _safe(kb.get("name", "KnowBody").replace(" ", "_"))
    zip_path = os.path.join(out_dir, f"Spesenabrechnung_{name}_{jahr_monat}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pdf_path, arcname=os.path.basename(pdf_path))
        zf.write(xlsx_path, arcname=os.path.basename(xlsx_path))
        for nr, b in enumerate((x for x in belege if x.get("bild_pfad")), start=1):
            src = capture.abs_path_for(b["bild_pfad"])
            if os.path.isfile(src):
                zf.writestr(_receipt_arcname(b, nr), open(src, "rb").read())
        zf.writestr("Begleitmail.txt", f"Betreff: {email['subject']}\n\n{email['body']}\n")

    _att = attest or {}
    ma_id = db.finalize_close(
        knowbody_id, jahr_monat,
        summe_chf=month_data["total_chf"],
        summe_weiter_chf=month_data["summe_weiter_chf"],
        anzahl=month_data["anzahl"],
        beleg_ids=[b["id"] for b in belege],
        pdf_pfad=pdf_path, xlsx_pfad=xlsx_path, zip_pfad=zip_path,
        bestaetigung_text=_att.get("text", ""), bestaetigt_von=_att.get("von", ""),
        bestaetigt_am=_att.get("am", ""),
        verpflegung_total_chf=month_data["verpflegung_total_chf"],
        km_entschaedigung_chf=month_data["km_entschaedigung_chf"],
    )

    return {
        "ok": True, "ma_id": ma_id, "zip_path": zip_path, "pdf_path": pdf_path,
        "xlsx_path": xlsx_path, "total_chf": month_data["total_chf"],
        "summe_weiter_chf": month_data["summe_weiter_chf"], "anzahl": month_data["anzahl"],
        "email": email,
    }
