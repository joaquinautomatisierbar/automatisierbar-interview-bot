#!/usr/bin/env python3
"""eval_extraction.py — extraction accuracy gate against the REAL provider.

Runs the synthetic corpus (testdata/pdfs/*) through the live LLM and scores
against the goldens (testdata/expected/*). This is the pre-pilot gate: title +
patient fields correct, junk correctly rejected, gates behaving.

COSTS API CREDITS (~1 call per PDF). Repo policy: one sanity case is fine any
time (--only austritt_usz); a full-corpus run is an explicit decision.

ONLY synthetic data ever flows through here — the corpus is fictional by
construction, so this is safe to run on any provider before the client's
Datenschutz sign-off.

Usage:
  python3 tools/praxis_ulrich/eval_extraction.py --only austritt_usz   # sanity (1 call)
  python3 tools/praxis_ulrich/eval_extraction.py                       # full gate (~14 calls)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from praxis_ulrich import config, extractor, pdf_text, titles  # noqa: E402

TESTDATA = Path(_HERE) / "testdata"


def _norm_name(s: str | None) -> str:
    return (s or "").strip().lower()


def score_case(case_id: str, cfg: dict) -> dict:
    blob = (TESTDATA / "pdfs" / f"{case_id}.pdf").read_bytes()
    golden = json.loads((TESTDATA / "expected" / f"{case_id}.json").read_text(encoding="utf-8"))

    text, pages = pdf_text.extract_text(blob)
    images = None
    if pdf_text.is_scanned(text, pages, int(cfg.get("scan_min_chars_per_page", 50))):
        images = pdf_text.render_pages_png(blob, int(cfg.get("vision_max_pages", 3)))
    ex = extractor.extract_befund(text=None if images else text, images=images, cfg=cfg)

    checks: dict[str, bool] = {}
    checks["llm_ok"] = ex["ok"]
    checks["ist_befund"] = ex["ist_befund"] == golden["ist_befund"]

    gate = bool(ex["ist_befund"] and ex["patientinNachname"] and ex["geburtsdatum"])
    checks["gate"] = gate == golden["gate_pass"]

    if golden["ist_befund"] and golden["gate_pass"]:
        if golden.get("lenient_name_order"):
            got = {_norm_name(ex["patientinNachname"]), _norm_name(ex["patientinVorname"])}
            want = {_norm_name(golden["nachname"]), _norm_name(golden["vorname"])}
            checks["name"] = got == want
        else:
            checks["name"] = (_norm_name(ex["patientinNachname"]) == _norm_name(golden["nachname"])
                              and _norm_name(ex["patientinVorname"]) == _norm_name(golden["vorname"]))
        checks["geburtsdatum"] = ex["geburtsdatum"] == golden["geburtsdatum"]
        if golden["berichtsdatum"] is not None:
            checks["berichtsdatum"] = ex["berichtsdatum"] == golden["berichtsdatum"]
        titel, aus_liste = titles.resolve_titel(ex["titel_vorschlag"])
        if golden["titel_erwartet"] is not None:
            checks["titel"] = titel == golden["titel_erwartet"] and aus_liste
        else:
            checks["titel_frei"] = not aus_liste and bool(titel)
        z = ex["zusammenfassung_4z"] or ""
        checks["4zeiler"] = z.count("\n") == 3 and len(z) > 20

    passed = all(checks.values())
    return {"case": case_id, "passed": passed, "checks": checks,
            "extraction": {k: ex[k] for k in ("patientinNachname", "patientinVorname",
                                              "geburtsdatum", "berichtsdatum",
                                              "titel_vorschlag", "confidence", "error")}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="einzelner Case (Sanity, 1 API-Call)")
    args = ap.parse_args(argv)

    cfg = config.load()
    cases = sorted(p.stem for p in (TESTDATA / "pdfs").glob("*.pdf"))
    if args.only:
        if args.only not in cases:
            print(f"unbekannter Case: {args.only} (verfügbar: {', '.join(cases)})")
            return 2
        cases = [args.only]

    print(f"Extraction-Eval — Provider {cfg.get('llm_provider')}, {len(cases)} Case(s)\n")
    results = []
    for c in cases:
        r = score_case(c, cfg)
        results.append(r)
        mark = "✅" if r["passed"] else "❌"
        print(f" {mark} {c}")
        if not r["passed"]:
            bad = [k for k, v in r["checks"].items() if not v]
            print(f"     fehlgeschlagen: {bad}")
            print(f"     extraktion: {json.dumps(r['extraction'], ensure_ascii=False)}")

    ok = sum(1 for r in results if r["passed"])
    print(f"\n{ok}/{len(results)} Cases bestanden.")
    if len(results) > 1:
        print("Pilot-Gate: alle Cases müssen bestehen, insbesondere microsoft_junk "
              "(ist_befund=false) und missing_dob (gate_pass=false).")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
