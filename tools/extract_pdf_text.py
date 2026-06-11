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


def extract_from_base64(b64: str, suffix: str = ".pdf") -> str:
    raw = base64.b64decode(b64)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        return extract_from_path(tmp_path)
    finally:
        os.unlink(tmp_path)


def main():
    args = sys.argv[1:]
    suffix = ".pdf"
    if "--format" in args:
        i = args.index("--format")
        fmt = args[i + 1].lstrip(".")
        suffix = f".{fmt}"
        del args[i:i + 2]

    if not args:
        print("ERROR: provide a file path or --base64 <data> [--format epub|pdf|mobi]", file=sys.stderr)
        sys.exit(1)

    if args[0] == "--base64":
        if len(args) < 2:
            print("ERROR: --base64 requires a data argument", file=sys.stderr)
            sys.exit(1)
        text = extract_from_base64(args[1], suffix=suffix)
    else:
        path = args[0]
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
