#!/usr/bin/env python3
"""
Render data/contributions.json as a 53-week x 7-day grid of rounded boxes,
styled as a HUD/targeting readout (black + gold — matches the Port-folio
site's aesthetic) instead of the default GitHub green. Reveals once on load
with a diagonal slide-down, then freezes. No looping "glow" — a HUD reads
data, it doesn't idle-animate.
"""
import json
import os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")

# none -> brightest. Bronze/gold ramp instead of GitHub green.
PALETTE = ["#171308", "#4d3d14", "#8a6a1f", "#c9962e", "#f4c542"]
BG = "#0a0a08"
GRID_LINE = "#2a2414"
TEXT_GOLD = "#e8c96b"
TEXT_DIM = "#8a7a4a"
FONT = "'JetBrains Mono','Share Tech Mono',monospace"

CELL = 11
GAP = 4
STEP = CELL + GAP
LEFT_PAD = 34   # room for day-of-week labels
TOP_PAD = 44    # room for title + month labels
RIGHT_PAD = 16
BOTTOM_PAD = 40  # room for legend + stats line

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # sparse, like GitHub's own graph


def load_data():
    with open(DATA_PATH) as f:
        return json.load(f)


def build_weeks(days):
    """Bucket the flat day list into GitHub-style weeks (columns), each a
    list of 7 slots (Sun..Sat), left-padding the first week so it aligns."""
    weeks = []
    week = [None] * 7
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        dow = (dt.weekday() + 1) % 7  # convert Mon=0..Sun=6 -> Sun=0..Sat=6
        if dow == 0 and any(week):
            weeks.append(week)
            week = [None] * 7
        week[dow] = d
    if any(week):
        weeks.append(week)
    return weeks


def month_label_positions(weeks):
    labels = []
    last_month = None
    for wi, week in enumerate(weeks):
        first_real = next((d for d in week if d), None)
        if not first_real:
            continue
        month = int(first_real["date"][5:7])
        if month != last_month:
            labels.append((wi, MONTH_ABBR[month - 1]))
            last_month = month
    return labels


def render(payload):
    days = payload["days"]
    stats = payload["stats"]
    username = payload["username"]
    weeks = build_weeks(days)

    grid_w = len(weeks) * STEP - GAP
    grid_h = 7 * STEP - GAP
    width = LEFT_PAD + grid_w + RIGHT_PAD
    height = TOP_PAD + grid_h + BOTTOM_PAD

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}">'
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="{BG}" rx="6"/>')

    # HUD corner brackets — the signature element
    bl = 14
    for cx, cy, dx, dy in [(6, 6, 1, 1), (width - 6, 6, -1, 1),
                            (6, height - 6, 1, -1), (width - 6, height - 6, -1, -1)]:
        parts.append(
            f'<path d="M{cx} {cy + dy*bl} V{cy} H{cx + dx*bl}" '
            f'stroke="{TEXT_DIM}" stroke-width="1.2" fill="none"/>'
        )

    # Title
    parts.append(
        f'<text x="{LEFT_PAD}" y="20" fill="{TEXT_GOLD}" font-size="12" '
        f'letter-spacing="2">CONTRIBUTIONS.LOG // @{username}</text>'
    )

    # Month labels
    for wi, label in month_label_positions(weeks):
        x = LEFT_PAD + wi * STEP
        parts.append(f'<text x="{x}" y="{TOP_PAD - 10}" fill="{TEXT_DIM}" font-size="9">{label}</text>')

    # Day-of-week labels
    for dow, label in DOW_LABELS.items():
        y = TOP_PAD + dow * STEP + CELL - 1
        parts.append(f'<text x="4" y="{y}" fill="{TEXT_DIM}" font-size="9">{label}</text>')

    # Grid cells, diagonal stagger by (week_index + day_index)
    max_delay_steps = len(weeks) + 7
    total_anim_time = 1.1  # seconds, whole grid finishes revealing by then
    per_step = total_anim_time / max_delay_steps

    cell_defs = []
    idx = 0
    for wi, week in enumerate(weeks):
        for di, d in enumerate(week):
            x = LEFT_PAD + wi * STEP
            y = TOP_PAD + di * STEP
            level = d["level"] if d else 0
            color = PALETTE[min(level, len(PALETTE) - 1)]
            delay = (wi + di) * per_step
            cls = f"c{idx}"
            cell_defs.append(
                f'<rect class="cell {cls}" x="{x}" y="{y - 6}" width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{color}" stroke="{GRID_LINE}" stroke-width="0.5" opacity="0" '
                f'style="animation-delay:{delay:.3f}s"/>'
            )
            idx += 1
    parts.extend(cell_defs)

    # Legend
    ly = TOP_PAD + grid_h + 16
    parts.append(f'<text x="{LEFT_PAD}" y="{ly + 7}" fill="{TEXT_DIM}" font-size="9">Less</text>')
    lx = LEFT_PAD + 34
    for i, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx + i*14}" y="{ly}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
    parts.append(
        f'<text x="{lx + len(PALETTE)*14 + 6}" y="{ly + 7}" fill="{TEXT_DIM}" font-size="9">More</text>'
    )

    # Stats footer
    total = stats["total_contributions"]
    streak = stats["longest_streak"]
    parts.append(
        f'<text x="{width - RIGHT_PAD}" y="{ly + 7}" fill="{TEXT_GOLD}" font-size="9" '
        f'text-anchor="end">{total} contributions // longest streak {streak}d</text>'
    )

    # Animation: reveal once, then freeze (no infinite loop)
    parts.append(
        "<style>"
        ".cell{animation:reveal 0.5s ease-out forwards;}"
        "@keyframes reveal{"
        "0%{opacity:0;transform:translate(-6px,-10px);}"
        "100%{opacity:1;transform:translate(0,0);}"
        "}"
        "</style>"
    )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    payload = load_data()
    svg = render(payload)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
