#!/usr/bin/env python3
"""extract_pdf_text.py — Extract text from a PDF file

Used by the automatisierbar interview bot to read answered question PDFs
sent back by clients via Telegram.

Usage:
  python3 extract_pdf_text.py /path/to/file.pdf
  python3 extract_pdf_text.py --base64 '<base64-encoded-pdf>'

Output: prints extracted text to stdout, one paragraph per line.
Exit code 0 on success, 1 on failure.
"""

import sys
import os
import base64
import tempfile
from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    print("ERROR: pymupdf not installed. Run: pip3 install pymupdf", file=sys.stderr)
    sys.exit(1)


def extract_from_path(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:
            pages.append(f"[Seite {i + 1}]\n{text}")
    doc.close()
    return "\n\n".join(pages)


def extract_from_base64(b64: str) -> str:
    raw = base64.b64decode(b64)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        return extract_from_path(tmp_path)
    finally:
        os.unlink(tmp_path)


def main():
    if len(sys.argv) < 2:
        print("ERROR: provide a file path or --base64 <data>", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--base64":
        if len(sys.argv) < 3:
            print("ERROR: --base64 requires a data argument", file=sys.stderr)
            sys.exit(1)
        text = extract_from_base64(sys.argv[2])
    else:
        path = sys.argv[1]
        if not Path(path).exists():
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        text = extract_from_path(path)

    if not text.strip():
        print("WARNING: no text extracted — PDF may be image-based", file=sys.stderr)
        print("")
    else:
        print(text)


if __name__ == "__main__":
    main()
