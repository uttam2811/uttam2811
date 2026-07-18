#!/usr/bin/env python3
"""
Downsample source-prepped.png to a character grid, map each cell's
brightness to a glyph from a density ramp, and wrap each row in a
horizontal clip-path wipe that reveals left-to-right, staggered top to
bottom (a small block "cursor" rides the wipe edge). The whole portrait
prints once and freezes — no looping.

Run: python scripts/make_ascii_svg.py source-prepped.png
Output: avi-ascii.svg (rename the constant below, or pass --out)
"""
import argparse
import os

from PIL import Image
from xml.sax.saxutils import escape

# bright (sparse) -> dark (dense); leading space clears the background
RAMP = " .`:-=+*cs#%@"

COLS = 100
ROWS = 53

FILL = "#f4c542"       # single gold fill — no per-character rainbow
CURSOR_FILL = "#e8e2c8"
BG = "#0a0a08"
FONT = "'JetBrains Mono','Share Tech Mono',monospace"
CHAR_W = 6.2
CHAR_H = 11


def image_to_grid(path: str):
    img = Image.open(path).convert("L").resize((COLS, ROWS))
    pixels = list(img.getdata())
    rows = []
    for r in range(ROWS):
        row_pixels = pixels[r * COLS:(r + 1) * COLS]
        row_chars = []
        for p in row_pixels:
            # p: 0 (black) .. 255 (white). Map white -> ramp[0] (space).
            idx = int((255 - p) / 255 * (len(RAMP) - 1))
            row_chars.append(RAMP[idx])
        rows.append("".join(row_chars))
    return rows


def render(rows, total_anim_time=1.8):
    width = COLS * CHAR_W + 20
    height = ROWS * CHAR_H + 20
    n = len(rows)
    per_row = total_anim_time / max(n, 1)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" font-family="{FONT}">',
        f'<rect width="{width:.0f}" height="{height:.0f}" rx="6" fill="{BG}"/>',
        "<defs>",
    ]

    style_rules = []
    body = []

    for i, row in enumerate(rows):
        y = 14 + i * CHAR_H
        clip_id = f"clip{i}"
        row_width = len(row) * CHAR_W
        delay = i * per_row
        duration = 0.55

        # Clip path that wipes from 0 width to full width
        parts.append(
            f'<clipPath id="{clip_id}"><rect x="10" y="{y-CHAR_H}" width="0" height="{CHAR_H+2}" '
            f'class="wipe wipe{i}"/></clipPath>'
        )

        safe_row = escape(row)
        body.append(
            f'<text x="10" y="{y}" fill="{FILL}" font-size="10" xml:space="preserve" '
            f'clip-path="url(#{clip_id})">{safe_row}</text>'
        )
        # small block cursor riding the wipe edge — a thin rect animated
        # with the same timing, positioned via a companion animate on x
        body.append(
            f'<rect class="cursor cursor{i}" y="{y - CHAR_H + 2}" width="{CHAR_W:.1f}" height="{CHAR_H - 2}" '
            f'fill="{CURSOR_FILL}" opacity="0.85"/>'
        )

        style_rules.append(
            f".wipe{i}{{animation:wipe{i} {duration}s steps(30,end) forwards;animation-delay:{delay:.3f}s;}}"
            f"@keyframes wipe{i}{{from{{width:0;}}to{{width:{row_width:.1f}px;}}}}"
        )
        style_rules.append(
            f".cursor{i}{{animation:cursor{i} {duration}s steps(30,end) forwards, blink 0.5s step-end infinite;"
            f"animation-delay:{delay:.3f}s, {delay:.3f}s;}}"
            f"@keyframes cursor{i}{{from{{x:10px;opacity:0.85;}}"
            f"to{{x:{10+row_width:.1f}px;opacity:0;}}}}"
        )

    parts.append("</defs>")
    parts.extend(body)
    parts.append(
        "<style>@keyframes blink{50%{opacity:0;}}" + "".join(style_rules) + "</style>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo", nargs="?", default="source-prepped.png",
                     help="prepped grayscale photo (output of prep_photo.py)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "uttam-ascii.svg"))
    args = ap.parse_args()

    if not os.path.exists(args.photo):
        print(f"'{args.photo}' not found — run prep_photo.py on your photo first.")
        return

    rows = image_to_grid(args.photo)
    svg = render(rows)
    with open(args.out, "w") as f:
        f.write(svg)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
