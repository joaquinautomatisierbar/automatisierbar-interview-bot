"""pdf_text.py — PDF text extraction + scanned-PDF detection for the Befund-Automat.

Text path (fast, free): PyMuPDF with [Seite N] markers, adapted from
tools/extract_pdf_text.py. Scanned path: if the average extractable text per
page is below a threshold, the PDF is treated as image-only and the first N
pages are rendered to PNG for the vision fallback in extractor.py.

All functions take bytes (attachments never touch disk before filing) and
never raise — a broken PDF yields ("", 0) / [] and the pipeline records a
clean failure (no flag, mail untouched).
"""

from __future__ import annotations


def extract_text(pdf_bytes: bytes) -> tuple[str, int]:
    """(text with page markers, page_count). ("", 0) on any error."""
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for i, page in enumerate(doc):
            t = page.get_text("text").strip()
            if t:
                pages.append(f"[Seite {i + 1}]\n{t}")
        n = doc.page_count
        doc.close()
        return "\n\n".join(pages), n
    except Exception:
        return "", 0


def is_scanned(text: str, page_count: int, min_chars_per_page: int = 50) -> bool:
    """True if the PDF has (nearly) no text layer -> vision fallback."""
    if page_count <= 0:
        return False  # broken PDF is a failure, not a scan
    return (len(text) / page_count) < min_chars_per_page


def render_pages_png(pdf_bytes: bytes, max_pages: int = 3, dpi: int = 150) -> list[bytes]:
    """First max_pages pages as PNG bytes for the vision path. [] on error."""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        out = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi)
            out.append(pix.tobytes("png"))
        doc.close()
        return out
    except Exception:
        return []
