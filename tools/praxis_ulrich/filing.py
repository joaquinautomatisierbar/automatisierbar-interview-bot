"""filing.py — the FilingSink interface + implementations.

The sink is the ONLY place that knows where a filed PDF ends up. Aeskulap's
real import interface is pending Kern Concept AG's answer, so:

  HotfolderSink   MVP: write into a watched/import directory. Two-step write
                  (.part -> os.replace) so a watcher can never grab a
                  half-written file. Filename collisions get _2, _3, ...
  GdtSink         HotfolderSink + a metadata sidecar per PDF. The sidecar
                  CONTENT is a stub behind _sidecar_content() until Kern
                  Concept confirms the exact GDT Satzart/format — swapping
                  the format later touches exactly that one function.
  DryRunSink      records calls, writes nothing. Used by the dev harness,
                  --dry-run, and as the escalation mode after any
                  wrong-patient event during the pilot.

file() never raises: FilingResult(ok=False, error=...) on any problem.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FilingResult:
    ok: bool
    final_path: str = ""
    error: str = ""


def _unique_path(directory: Path, filename: str) -> Path:
    """foo.pdf -> foo_2.pdf -> foo_3.pdf ... first non-existing wins."""
    p = directory / filename
    if not p.exists():
        return p
    stem, suffix = p.stem, p.suffix
    for i in range(2, 1000):
        cand = directory / f"{stem}_{i}{suffix}"
        if not cand.exists():
            return cand
    raise OSError(f"kein freier Dateiname für {filename}")


class HotfolderSink:
    def __init__(self, hotfolder: str):
        self.dir = Path(hotfolder)

    def file(self, pdf_bytes: bytes, filename: str, meta: dict | None = None) -> FilingResult:
        try:
            if not self.dir.is_dir():
                return FilingResult(False, error=f"Hotfolder existiert nicht: {self.dir}")
            target = _unique_path(self.dir, filename)
            part = target.with_suffix(target.suffix + ".part")
            part.write_bytes(pdf_bytes)
            os.replace(part, target)  # atomic on same volume — watcher-safe
            return FilingResult(True, final_path=str(target))
        except Exception as e:
            return FilingResult(False, error=f"Ablage fehlgeschlagen: {e!r}")


class GdtSink(HotfolderSink):
    """Hotfolder + Metadaten-Sidecar. Format PENDING Kern Concept AG."""

    def file(self, pdf_bytes: bytes, filename: str, meta: dict | None = None) -> FilingResult:
        res = super().file(pdf_bytes, filename, meta)
        if not res.ok:
            return res
        try:
            sidecar = Path(res.final_path).with_suffix(".meta.txt")
            sidecar.write_text(_sidecar_content(meta or {}, Path(res.final_path).name),
                               encoding="utf-8")
            return res
        except Exception as e:
            # PDF liegt korrekt — Sidecar-Fehler ist kein Ablage-Fehler, nur Log.
            print(f"[befund-filing] Sidecar fehlgeschlagen: {e!r}", flush=True)
            return res


def _sidecar_content(meta: dict, pdf_name: str) -> str:
    """STUB until Kern Concept confirms the import format (GDT 2.1/3.0 Satzart,
    field IDs, encoding). Currently a human/machine-readable key-value file so
    the on-site fallback (manual drag into Aeskulap) still has all context."""
    lines = [
        f"PDF: {pdf_name}",
        f"PatientinNachname: {meta.get('nachname', '')}",
        f"PatientinVorname: {meta.get('vorname', '')}",
        f"Geburtsdatum: {meta.get('geburtsdatum', '')}",
        f"Dokumenttitel: {meta.get('dokumenttitel', '')}",
        f"Berichtsdatum: {meta.get('berichtsdatum', '')}",
        f"AbsenderInstitution: {meta.get('institution', '')}",
    ]
    return "\n".join(lines) + "\n"


@dataclass
class DryRunSink:
    calls: list = field(default_factory=list)
    fail: bool = False  # tests + escalation drills

    def file(self, pdf_bytes: bytes, filename: str, meta: dict | None = None) -> FilingResult:
        self.calls.append({"filename": filename, "bytes": len(pdf_bytes), "meta": meta or {}})
        if self.fail:
            return FilingResult(False, error="DryRun: simulierter Ablage-Fehler")
        return FilingResult(True, final_path=f"<dryrun>/{filename}")


def make_sink(cfg: dict):
    kind = (cfg.get("sink") or "hotfolder").lower()
    if kind == "dryrun":
        return DryRunSink()
    if kind == "hotfolder+gdt":
        return GdtSink(cfg.get("hotfolder_path") or "")
    return HotfolderSink(cfg.get("hotfolder_path") or "")
