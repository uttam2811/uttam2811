#!/usr/bin/env python3
"""
Hand-authored neofetch-style panel: a title bar, then colored key/value rows.
Content lives here (not in the heatmap, which already covers the GitHub
stats) — this is for the story numbers can't tell. Each line fades + slides
in on a short stagger. Set STATIC=1 to emit a frozen frame (no animation
delays) for local Quick Look previews.
"""
import os
from xml.sax.saxutils import escape

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

BG = "#0a0a08"
BORDER = "#3a3316"
GOLD = "#f4c542"
GOLD_DIM = "#c9962e"
TEXT = "#e8e2c8"
TEXT_DIM = "#8a7a4a"
FONT = "'JetBrains Mono','Share Tech Mono',monospace"

WIDTH = 490
LINE_H = 22
TOP_PAD = 46
LEFT_PAD = 20

ROWS = [
    ("Now", "MSc Robotics Engineering — UE Potsdam, Sep 2026"),
    ("Prev", "B.Tech EEE — Amrita Vishwa Vidyapeetham"),
    ("Stack", "ROS2 · Gazebo · C++ · Python · OpenCV · YOLOv8"),
    ("Highlights", "Internships @ Bosch · Eaton · L&T EduTech"),
]


def render():
    height = TOP_PAD + len(ROWS) * LINE_H + 30
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="{FONT}">'
    )
    parts.append(f'<rect width="{WIDTH}" height="{height}" rx="6" fill="{BG}" stroke="{BORDER}"/>')

    # title bar, like a terminal chrome strip
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="28" rx="6" fill="{BORDER}" opacity="0.4"/>')
    for i, cx in enumerate([16, 32, 48]):
        parts.append(f'<circle cx="{cx}" cy="14" r="4" fill="{GOLD_DIM}" opacity="{0.9 - i*0.2}"/>')
    parts.append(
        f'<text x="{WIDTH/2}" y="18" fill="{TEXT_DIM}" font-size="10" text-anchor="middle" '
        f'letter-spacing="2">uttam@github</text>'
    )

    # HUD corner brackets to match the heatmap's signature
    bl = 12
    for cx, cy, dx, dy in [(6, 34, 1, 1), (WIDTH - 6, 34, -1, 1)]:
        parts.append(
            f'<path d="M{cx} {cy + dy*bl} V{cy} H{cx + dx*bl}" stroke="{TEXT_DIM}" '
            f'stroke-width="1" fill="none"/>'
        )

    n = len(ROWS)
    total_anim_time = 0.9
    per_step = total_anim_time / max(n, 1)

    for i, (key, value) in enumerate(ROWS):
        y = TOP_PAD + i * LINE_H
        delay = 0 if STATIC else i * per_step
        opacity = "1" if STATIC else "0"
        style = "" if STATIC else f' style="animation-delay:{delay:.3f}s"'
        safe_key, safe_value = escape(key), escape(value)
        parts.append(
            f'<g class="row" opacity="{opacity}"{style}>'
            f'<text x="{LEFT_PAD}" y="{y}" fill="{GOLD}" font-size="12" font-weight="600">{safe_key}</text>'
            f'<text x="{LEFT_PAD + 100}" y="{y}" fill="{TEXT}" font-size="12">{safe_value}</text>'
            f'</g>'
        )

    # divider + footer line, like a HUD readout signature
    fy = TOP_PAD + n * LINE_H + 14
    parts.append(f'<line x1="{LEFT_PAD}" y1="{fy - 12}" x2="{WIDTH - LEFT_PAD}" y2="{fy - 12}" '
                 f'stroke="{BORDER}" stroke-width="1"/>')
    parts.append(
        f'<text x="{LEFT_PAD}" y="{fy}" fill="{TEXT_DIM}" font-size="9">'
        f'status: preparing for Potsdam · building in ROS2/Gazebo</text>'
    )

    if not STATIC:
        parts.append(
            "<style>"
            ".row{animation:fadeIn 0.4s ease-out forwards;}"
            "@keyframes fadeIn{"
            "0%{opacity:0;transform:translateX(-8px);}"
            "100%{opacity:1;transform:translateX(0);}"
            "}"
            "</style>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    svg = render()
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH} (static={STATIC})")


if __name__ == "__main__":
    main()
