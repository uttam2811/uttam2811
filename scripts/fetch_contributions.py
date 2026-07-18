#!/usr/bin/env python3
"""
Scrape the public contribution calendar HTML fragment GitHub itself uses
(no GraphQL API, no personal access token) and write data/contributions.json
with raw days plus a few derived stats (streaks, best day, monthly totals).
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GITHUB_PROFILE_USER", "uttam2811")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    days = []
    for td in cells:
        date = td.get("data-date")
        level = int(td.get("data-level", 0))
        tooltip = soup.find(attrs={"for": td.get("id")})
        count = 0
        if tooltip and tooltip.text:
            text = tooltip.text.strip()
            if text.split()[0].isdigit():
                count = int(text.split()[0])
        days.append({"date": date, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] for d in days)

    # current streak: walk back from the most recent day
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak anywhere in the window
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = {}
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly,
    }


def main():
    days = fetch_days()
    if not days:
        print("No contribution cells found — GitHub markup may have changed.", file=sys.stderr)
        sys.exit(1)

    stats = derive_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {len(days)} days, {stats['total_contributions']} contributions -> {OUT_PATH}")


if __name__ == "__main__":
    main()
