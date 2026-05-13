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
# this keeps a single file from eating it all.
MAX_EXTRACT_CHARS = 30_000
TRUNCATION_MARKER = "\n\n[truncated — Originaldatei zu gross für Vorschau]"

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


def _df_to_text(df) -> str:
    """Render a DataFrame as: column summary + first 50 rows as markdown table."""
    n_rows, n_cols = df.shape
    col_summary = ", ".join(f"{c} ({df[c].dtype})" for c in df.columns)
    head = df.head(50)
    try:
        table = head.to_markdown(index=False)
    except Exception:
        # tabulate not installed → fall back to to_string
        table = head.to_string(index=False)
    suffix = ""
    if n_rows > 50:
        suffix = f"\n\n_(zeigt erste 50 von {n_rows} Zeilen)_"
    return f"**{n_rows} Zeilen × {n_cols} Spalten**\nSpalten: {col_summary}\n\n{table}{suffix}"


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
