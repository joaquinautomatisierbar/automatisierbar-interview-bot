"""make_icons.py — generate the KnowSpesen PWA icons (navy + white receipt glyph).

Run once: python3 tools/spesen/make_icons.py
Writes static/spesen-icon-{192,512,maskable}.png. Reproducible, committed alongside
the PNGs so the brand mark can be regenerated.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw

NAVY = (27, 42, 74, 255)
WHITE = (255, 255, 255, 255)
STATIC = Path(__file__).resolve().parents[2] / "static"


def _receipt(draw: ImageDraw.ImageDraw, S: int, scale: float):
    """Draw a centred white receipt glyph with navy 'text' lines + zigzag bottom."""
    cx = cy = S / 2
    w = S * 0.40 * scale
    h = S * 0.52 * scale
    left, right = cx - w / 2, cx + w / 2
    top = cy - h / 2
    teeth = 6
    tooth_w = w / teeth
    tooth_h = h * 0.05
    base = cy + h / 2 - tooth_h

    pts = [(left, top), (right, top)]
    x = right
    pts.append((x, base))
    down = True
    for i in range(teeth):
        x -= tooth_w
        y = base + tooth_h if down else base
        pts.append((x, y))
        down = not down
    pts.append((left, base))
    draw.polygon(pts, fill=WHITE)

    # navy 'text' lines
    line_h = max(3, int(S * 0.018))
    pad = w * 0.16
    lx0, lx1 = left + pad, right - pad
    ys = [top + h * 0.22, top + h * 0.40, top + h * 0.58]
    widths = [1.0, 1.0, 0.62]
    for y, ww in zip(ys, widths):
        draw.rounded_rectangle(
            [lx0, y, lx0 + (lx1 - lx0) * ww, y + line_h],
            radius=line_h / 2, fill=NAVY)


def make(size: int, maskable: bool) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if maskable:
        d.rectangle([0, 0, size, size], fill=NAVY)   # full-bleed safe zone
        _receipt(d, size, scale=0.74)
    else:
        r = int(size * 0.22)
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=NAVY)
        _receipt(d, size, scale=1.0)
    return img


def main():
    os.makedirs(STATIC, exist_ok=True)
    make(512, False).save(STATIC / "spesen-icon-512.png")
    make(192, False).save(STATIC / "spesen-icon-192.png")
    make(512, True).save(STATIC / "spesen-icon-maskable.png")
    print("wrote:", *(p.name for p in sorted(STATIC.glob("spesen-icon-*.png"))))


if __name__ == "__main__":
    main()
