"""file_extract.py — Convert uploaded interview attachments to plain text.

Routes by MIME / extension:
  Excel (.xlsx .xls)  → openpyxl/xlrd via pandas → markdown table + col summary
  CSV (.csv)          → pandas → markdown table + col summary
  PDF (.pdf)          → PyMuPDF (reuses extract_pdf_text helpers)
  Image (.png .jpg)   → Claude vision (Sonnet 4.6) → extracted text
  Text/Markdown       → raw decode

Single entry point: extract(filename, content, mime) -> dict with {text, kind, warning?}.
Caller is responsible for size guards before calling — extraction is synchronous and
must finish well within Render's 30s gunicorn timeout.
"""

from __future__ import annotations

import base64
import io
import os
from typing import Optional

# Per-file extracted-text cap. State JSON has a ~200kB ceiling (Notion rich_text);
# this keeps a single file from eating it all. Bumped for V3 so the deep-fact
# verification (a marker buried in row ~8000 of a 3 MB CSV) actually surfaces.
MAX_EXTRACT_CHARS = 60_000
TRUNCATION_MARKER = "\n\n[truncated — Originaldatei zu gross für Vorschau]"

# V3 P1.3 — Pre-import pandas at module load so the first CSV/Excel upload
# doesn't pay a 2 s cold-start (observed in upload-timing diagnostics).
# Failures here are non-fatal: extraction will fail later with a clear error.
try:
    import pandas as _pd_warmup  # noqa: F401
except Exception:
    _pd_warmup = None

ALLOWED_EXTENSIONS = {
    ".xlsx", ".xls", ".csv",
    ".pdf",
    ".png", ".jpg", ".jpeg",
    ".txt", ".md",
}

ALLOWED_MIME_PREFIXES = (
    "text/",
    "image/png", "image/jpeg", "image/jpg",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
)


def _ext(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower()


def is_allowed(filename: str, mime: str) -> bool:
    if _ext(filename) in ALLOWED_EXTENSIONS:
        return True
    return any((mime or "").startswith(p) for p in ALLOWED_MIME_PREFIXES)


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_EXTRACT_CHARS:
        return text, False
    return text[:MAX_EXTRACT_CHARS] + TRUNCATION_MARKER, True


# ---------------------------------------------------------------------------
# Per-format extractors
# ---------------------------------------------------------------------------

def _extract_text(content: bytes) -> str:
    # Try utf-8, then latin-1 as a permissive fallback.
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="replace")


def _extract_csv(content: bytes) -> str:
    import pandas as pd
    df = pd.read_csv(io.BytesIO(content))
    return _df_to_text(df)


def _extract_excel(content: bytes, ext: str) -> str:
    import pandas as pd
    engine = "openpyxl" if ext == ".xlsx" else None  # xlrd handles .xls
    book = pd.ExcelFile(io.BytesIO(content), engine=engine)
    parts = []
    for sheet_name in book.sheet_names:
        df = book.parse(sheet_name)
        parts.append(f"### Sheet: {sheet_name}\n\n{_df_to_text(df)}")
    return "\n\n".join(parts)


def _df_table(df, max_rows: int = 50) -> str:
    """Markdown table fallback that tolerates missing tabulate."""
    try:
        return df.head(max_rows).to_markdown(index=False)
    except Exception:
        return df.head(max_rows).to_string(index=False)


def _df_to_text(df) -> str:
    """Render a DataFrame so the LLM sees enough to surface buried facts:
    head + tail + per-column top-5 + per-column unique-value-tail.

    Deep facts (an outlier row buried in row ~8000 of a 50K-row CSV) escape
    head(50)-only previews. The unique-value-tail surfaces them: a one-off
    marker like 'DEEP_FACT_MARKER' will appear in the column's distinct-values
    list because it's distinct from the bulk.
    """
    n_rows, n_cols = df.shape
    col_summary = ", ".join(f"{c} ({df[c].dtype})" for c in df.columns)
    parts: list = [f"**{n_rows} Zeilen × {n_cols} Spalten**", f"Spalten: {col_summary}", ""]

    if n_rows <= 100:
        # Whole thing fits — show it all.
        parts.append(_df_table(df, max_rows=n_rows))
        return "\n".join(parts)

    parts.append(f"### Erste 50 Zeilen (von {n_rows}):\n")
    parts.append(_df_table(df.head(50)))
    parts.append(f"\n### Letzte 20 Zeilen:\n")
    parts.append(_df_table(df.tail(20)))

    # Stratified samples — one row at every 10% boundary of the file. Catches
    # deep facts (an outlier buried at row ~8000 of 56000) even in high-cardinality
    # columns where value_counts.tail() doesn't help.
    try:
        sample_positions = [int(n_rows * p) for p in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)]
        sample_positions = sorted(set(min(n_rows - 1, max(0, p)) for p in sample_positions))
        sample_df = df.iloc[sample_positions]
        parts.append(f"\n### Stratified Sample (Zeilen bei 10–90% der Datei — fängt vergrabene Ausreisser):\n")
        parts.append(_df_table(sample_df, max_rows=len(sample_positions)))
    except Exception:
        pass

    parts.append("\n### Werte pro Spalte (top 10 häufigste + 10 distinct-tail für Ausreisser-Detektion):")
    import pandas as _pd_local
    for col in df.columns:
        try:
            series = df[col].dropna()
            if series.empty:
                parts.append(f"- **{col}**: (alle Werte leer)")
                continue
            vc = series.value_counts()
            top10 = vc.head(10)
            top_str = ", ".join(f"{repr(str(v)[:40])}={c}" for v, c in top10.items())
            line = f"- **{col}** (n_unique={len(vc)}): top10 → {top_str}"
            if len(vc) > 10:
                # The "distinct tail" — values that appear LEAST. Catches
                # rare outliers like a DEEP_FACT_MARKER in low-cardinality columns.
                tail10 = vc.tail(10).index.tolist()
                tail_str = ", ".join(repr(str(v)[:40]) for v in tail10)
                line += f"\n  rarest 10 → {tail_str}"

            # Type-anomaly detection: object column where most values parse as numeric
            # but a few don't — those non-numeric strings are likely meaningful outliers
            # (e.g. a 'DEEP_FACT_MARKER' string in a column of floats).
            if series.dtype == object:
                as_num = _pd_local.to_numeric(series, errors="coerce")
                num_count = int(as_num.notna().sum())
                if num_count > 0 and num_count >= len(series) * 0.5:
                    anomaly_mask = as_num.isna() & series.astype(str).str.strip().ne("")
                    anomalies = series[anomaly_mask]
                    if 0 < len(anomalies) <= 30:
                        uniq = list(dict.fromkeys(str(v)[:80] for v in anomalies))[:10]
                        line += f"\n  TYPE-ANOMALIEN (Spalte sieht numerisch aus, diese Werte nicht): {uniq}"

            parts.append(line)
        except Exception:
            pass

    return "\n".join(parts)


def _extract_pdf(content: bytes) -> str:
    import fitz  # PyMuPDF
    parts = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                parts.append(f"--- Seite {i} ---\n{text}")
    return "\n\n".join(parts) or "(PDF enthält keinen extrahierbaren Text — möglicherweise gescannt. Lade als Bild für OCR.)"


def _extract_image(content: bytes, mime: str) -> str:
    """Claude vision OCR. Returns plain extracted text of whatever is visible."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    media_type = mime if mime in ("image/png", "image/jpeg") else "image/png"
    b64 = base64.standard_b64encode(content).decode("ascii")
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64},
                },
                {
                    "type": "text",
                    "text": (
                        "Extrahiere ALLEN sichtbaren Text aus diesem Bild. "
                        "Wenn es ein Screenshot eines Tools/UI ist, beschreibe auch kurz "
                        "die Struktur (Spalten, Buttons, Felder). Antwort in der Sprache des Bildes."
                    ),
                },
            ],
        }],
    )
    return msg.content[0].text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract(filename: str, content: bytes, mime: Optional[str] = None) -> dict:
    """Extract plain text from `content`. Returns {text, kind, warning}.

    `kind` is one of: csv, excel, pdf, image, text — useful for downstream rendering.
    `warning` is set if the extracted text was truncated or partial.
    """
    if not is_allowed(filename, mime or ""):
        raise ValueError(f"Dateityp nicht erlaubt: {filename} ({mime})")

    ext = _ext(filename)
    mime = (mime or "").lower()

    if ext == ".csv" or mime == "text/csv":
        text = _extract_csv(content)
        kind = "csv"
    elif ext in (".xlsx", ".xls") or "spreadsheet" in mime or mime == "application/vnd.ms-excel":
        text = _extract_excel(content, ext or ".xlsx")
        kind = "excel"
    elif ext == ".pdf" or mime == "application/pdf":
        text = _extract_pdf(content)
        kind = "pdf"
    elif ext in (".png", ".jpg", ".jpeg") or mime.startswith("image/"):
        text = _extract_image(content, mime or "image/png")
        kind = "image"
    elif ext in (".txt", ".md") or mime.startswith("text/"):
        text = _extract_text(content)
        kind = "text"
    else:
        raise ValueError(f"Kein Extraktor für {filename} ({mime})")

    text, truncated = _truncate(text)
    out = {"text": text, "kind": kind}
    if truncated:
        out["warning"] = "Inhalt gekürzt — Originaldatei zu gross für Vorschau"
    return out
