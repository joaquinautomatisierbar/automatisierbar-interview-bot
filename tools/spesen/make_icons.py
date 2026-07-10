"""make_icons.py — generate the KnowSpesen PWA icons (KnowGravity petrol + white feather).

Run once: python3 tools/spesen/make_icons.py
Composites the KnowGravity feather mark (static/knowgravity-mark.png), recoloured to a
clean white silhouette, onto a deep-petrol tile. Writes static/spesen-icon-{192,512,
maskable}.png. Reproducible, committed alongside the PNGs.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw

PETROL = (0, 64, 64, 255)          # #004040 — KnowGravity deep petrol
WHITE = (255, 255, 255, 255)
STATIC = Path(__file__).resolve().parents[2] / "static"
MARK = STATIC / "knowgravity-mark.png"


def _white_feather(box: int) -> Image.Image:
    """Load the KnowGravity feather and return it as a white silhouette (alpha kept),
    scaled to fit a `box`×`box` square while preserving aspect ratio."""
    src = Image.open(MARK).convert("RGBA")
    # Trim to the mark's bounding box so scaling ignores transparent margins.
    bbox = src.getbbox()
    if bbox:
        src = src.crop(bbox)
    # Fit within the box, preserving aspect ratio.
    src.thumbnail((box, box), Image.LANCZOS)
    # Recolour every visible pixel to white; keep the original alpha as the shape.
    r, g, b, a = src.split()
    white = Image.new("RGBA", src.size, WHITE)
    white.putalpha(a)
    return white


def make(size: int, maskable: bool) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if maskable:
        d.rectangle([0, 0, size, size], fill=PETROL)      # full-bleed safe zone
        feather = _white_feather(int(size * 0.52))
    else:
        r = int(size * 0.22)
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=PETROL)
        feather = _white_feather(int(size * 0.62))
    # Centre the feather.
    fx = (size - feather.width) // 2
    fy = (size - feather.height) // 2
    img.alpha_composite(feather, (fx, fy))
    return img


def main():
    os.makedirs(STATIC, exist_ok=True)
    make(512, False).save(STATIC / "spesen-icon-512.png")
    make(192, False).save(STATIC / "spesen-icon-192.png")
    make(512, True).save(STATIC / "spesen-icon-maskable.png")
    print("wrote:", *(p.name for p in sorted(STATIC.glob("spesen-icon-*.png"))))


if __name__ == "__main__":
    main()
