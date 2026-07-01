#!/usr/bin/env python3
"""
render_linkedin_carousel.py — Deterministic LinkedIn document-carousel renderer.

Renders a list of slides into the Automatisierbar terminal aesthetic (reuses
build_card() from render_linkedin_image.py for pixel-identical brand styling),
then assembles them into ONE PDF (a LinkedIn "document" post, the highest-
engagement format) plus the individual slide PNGs.

Usage:
    python3 tools/render_linkedin_carousel.py --input carousel.json --output out.pdf

Input JSON schema:
{
  "palette": "green-on-deep | white-on-black | deep-on-light | light-on-green",  (default green-on-deep)
  "label":   "top-left // meta on every slide, e.g. automatisierbar",            (optional)
  "slides": [                                          (5-7 recommended)
    { "headline": "≤6 words", "subtitle": "≤12 words" },   (title slide first)
    ...
    { "headline": "Erstgespräch buchen", "subtitle": "cockpit.automatisierbar.ch/book" }  (CTA last)
  ]
}

Each slide is portrait 1080x1350. A "NN/total" counter is placed top-right.
First + last slides carry the logo; middle slides carry the wordmark.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# same-dir import (sys.path[0] is tools/ when run as a script)
from render_linkedin_image import build_card


def build_slides(spec: dict):
    palette = spec.get("palette") or "green-on-deep"
    label = spec.get("label") or "automatisierbar"
    slides = spec.get("slides") or []
    if not slides:
        raise ValueError("'slides' must be a non-empty list")
    n = len(slides)
    pages = []
    for i, s in enumerate(slides):
        card = {
            "headline": s.get("headline", ""),
            "subtitle": s.get("subtitle", ""),
            "label": s.get("label", label),
            "tag": f"{i + 1:02d}/{n:02d}",
            "palette": s.get("palette", palette),
            "aspect": "portrait",
            "branding": "logo" if i in (0, n - 1) else "wordmark",
        }
        if not str(card["headline"]).strip():
            raise ValueError(f"slide {i + 1} is missing 'headline'")
        pages.append(build_card(card))
    return pages


def render_carousel(spec: dict, output_path: str) -> int:
    pages = build_slides(spec)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # PDF (LinkedIn document post)
    pages[0].save(
        out, format="PDF", save_all=True, append_images=pages[1:], resolution=150.0
    )

    # individual slide PNGs (for an image-carousel alternative)
    png_dir = out.with_suffix("")
    png_dir = png_dir.parent / f"{png_dir.name}_slides"
    png_dir.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(pages):
        p.save(png_dir / f"slide_{i + 1:02d}.png", format="PNG", optimize=True)

    print(
        f"wrote {out}  ({len(pages)} slides, PDF) + PNGs in {png_dir}/",
        file=sys.stderr,
    )
    return len(pages)


def _read_input(path: str | None) -> dict:
    if path and path != "-":
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--input", "-i", default="-", help="JSON file path, or '-' for stdin")
    p.add_argument("--output", "-o", required=True, help="PDF output path")
    args = p.parse_args()
    try:
        spec = _read_input(args.input)
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        print(f"ERROR: bad input: {exc}", file=sys.stderr)
        return 2
    try:
        render_carousel(spec, args.output)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: render failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
