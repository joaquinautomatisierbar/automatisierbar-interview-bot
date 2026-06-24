#!/usr/bin/env python3
"""Render a PDF to one PNG per page so an agent (or human) can actually LOOK at it.

The QA Reviewer runs this, then Reads each PNG to verify layout/brand/legibility — because a
PDF you have not seen is unreviewed. Tries multiple backends so it works wherever it runs:
  1. PyMuPDF (fitz)         — pip install pymupdf
  2. pdftoppm (poppler)     — system package poppler-utils
  3. pdf2image + Pillow     — pip install pdf2image

Usage:
  python3 tools/render_pdf.py <file.pdf> [--dpi 150] [--out <dir>]
Writes <stem>.p1.png, <stem>.p2.png, ... next to the PDF (or in --out). Prints the PNG paths.
"""
import os
import subprocess
import sys


def _out_paths(pdf, out_dir, n):
    stem = os.path.splitext(os.path.basename(pdf))[0]
    return [os.path.join(out_dir, f"{stem}.p{i+1}.png") for i in range(n)]


def render(pdf, dpi=150, out_dir=None):
    pdf = os.path.abspath(pdf)
    if not os.path.exists(pdf):
        raise FileNotFoundError(pdf)
    out_dir = out_dir or os.path.dirname(pdf)
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(pdf))[0]

    # 1. PyMuPDF
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf)
        paths = []
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for i, page in enumerate(doc):
            p = os.path.join(out_dir, f"{stem}.p{i+1}.png")
            page.get_pixmap(matrix=mat).save(p)
            paths.append(p)
        return paths
    except ImportError:
        pass

    # 2. pdftoppm (poppler)
    if subprocess.run(["which", "pdftoppm"], capture_output=True).returncode == 0:
        prefix = os.path.join(out_dir, f"{stem}.p")
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, prefix.rstrip("p") + "page"],
                       check=True, capture_output=True)
        # pdftoppm names files like <prefix>-1.png; normalize to <stem>.pN.png
        produced = sorted(f for f in os.listdir(out_dir)
                          if f.startswith(f"{stem}.ppage") and f.endswith(".png"))
        paths = []
        for i, f in enumerate(produced):
            dst = os.path.join(out_dir, f"{stem}.p{i+1}.png")
            os.replace(os.path.join(out_dir, f), dst)
            paths.append(dst)
        if paths:
            return paths

    # 3. pdf2image
    try:
        from pdf2image import convert_from_path
        imgs = convert_from_path(pdf, dpi=dpi)
        paths = _out_paths(pdf, out_dir, len(imgs))
        for img, p in zip(imgs, paths):
            img.save(p, "PNG")
        return paths
    except ImportError:
        pass

    raise RuntimeError(
        "no PDF render backend available — install one of: pymupdf, poppler-utils (pdftoppm), pdf2image")


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    pdf = argv[0]
    dpi = 150
    out_dir = None
    if "--dpi" in argv:
        dpi = int(argv[argv.index("--dpi") + 1])
    if "--out" in argv:
        out_dir = argv[argv.index("--out") + 1]
    paths = render(pdf, dpi=dpi, out_dir=out_dir)
    print(f"rendered {len(paths)} page(s):")
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
