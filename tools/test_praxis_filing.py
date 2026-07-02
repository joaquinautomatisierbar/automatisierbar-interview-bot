#!/usr/bin/env python3
"""Offline tests for praxis_ulrich.filing — atomic hotfolder writes, collisions,
GDT sidecar stub, dry-run sink, factory.

Run: python3 tools/test_praxis_filing.py
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BEFUND_DATA_DIR", tempfile.mkdtemp(prefix="befund_fil_"))

from praxis_ulrich import filing  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        FAILS.append(name)


HOT = Path(tempfile.mkdtemp(prefix="befund_hot_"))
PDF = b"%PDF-1.4 inhalt"

# --- HotfolderSink ----------------------------------------------------------------
sink = filing.HotfolderSink(str(HOT))
r = sink.file(PDF, "Urinkultur 06-2026_Muster_Maria.pdf")
check("Ablage ok", r.ok and Path(r.final_path).exists())
check("Inhalt korrekt", Path(r.final_path).read_bytes() == PDF)
check("kein .part übrig", not list(HOT.glob("*.part")))

r2 = sink.file(PDF, "Urinkultur 06-2026_Muster_Maria.pdf")
check("Kollision -> _2", r2.ok and r2.final_path.endswith("_2.pdf"))
r3 = sink.file(PDF, "Urinkultur 06-2026_Muster_Maria.pdf")
check("Kollision -> _3", r3.ok and r3.final_path.endswith("_3.pdf"))

r = filing.HotfolderSink(str(HOT / "gibtsnicht")).file(PDF, "x.pdf")
check("fehlender Ordner -> ok=False, kein Raise", not r.ok and "existiert nicht" in r.error)

# --- GdtSink ------------------------------------------------------------------------
gdt = filing.GdtSink(str(HOT))
meta = {"nachname": "Muster", "vorname": "Maria", "geburtsdatum": "12.03.1985",
        "dokumenttitel": "Urinkultur 06/2026", "berichtsdatum": "10.06.2026",
        "institution": "Synlab"}
r = gdt.file(PDF, "NIPT V-Natal 06-2026_Muster_Maria.pdf", meta)
check("GDT: PDF abgelegt", r.ok)
sidecar = Path(r.final_path).with_suffix(".meta.txt")
check("GDT: Sidecar existiert", sidecar.exists())
sc = sidecar.read_text(encoding="utf-8")
check("GDT: Sidecar-Felder", "PatientinNachname: Muster" in sc and "Geburtsdatum: 12.03.1985" in sc
      and "Dokumenttitel: Urinkultur 06/2026" in sc)

# --- DryRunSink -----------------------------------------------------------------------
dr = filing.DryRunSink()
r = dr.file(PDF, "test.pdf", {"nachname": "X"})
check("DryRun ok + aufgezeichnet", r.ok and dr.calls[0]["filename"] == "test.pdf")
check("DryRun schreibt nichts", not (HOT / "test.pdf").exists())
dr_fail = filing.DryRunSink(fail=True)
check("DryRun fail-Modus", not dr_fail.file(PDF, "x.pdf").ok)

# --- make_sink --------------------------------------------------------------------------
check("factory hotfolder", isinstance(filing.make_sink({"sink": "hotfolder", "hotfolder_path": str(HOT)}),
                                      filing.HotfolderSink))
s = filing.make_sink({"sink": "hotfolder+gdt", "hotfolder_path": str(HOT)})
check("factory gdt", isinstance(s, filing.GdtSink))
check("factory dryrun", isinstance(filing.make_sink({"sink": "dryrun"}), filing.DryRunSink))

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("alle Tests grün ✅")
