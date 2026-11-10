#!/usr/bin/env python3
"""Render an animated, dark-mode GitHub contribution graph as a self-contained SVG.

Usage: python3 assets/build_contrib.py <contributions.json> <output.svg>
The JSON file is the raw response of:

  gh api graphql -f query='query { user(login:"roarscarch") {
    contributionsCollection { contributionCalendar {
      totalContributions
      weeks { contributionDays { date contributionCount weekday } }
    } } } }'
"""
import json
import sys
from datetime import date

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LEVELS = ["#0d1524", "#0b3a49", "#087d95", "#00b6d6", "#67ecff"]


def level(count):
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 11:
        return 3
    return 4


def render(data, updated):
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    total = cal["totalContributions"]

    days = [d for w in weeks for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]
    active = sum(1 for c in counts if c > 0)
    peak = max(counts) if counts else 0

    streak = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            streak += 1
        else:
            break

    start_x, grid_y = 96, 148
    pitch, cell = 16, 13

    cells = []
    month_labels = []
    last_month = None
    for wi, week in enumerate(weeks):
        wdays = week["contributionDays"]
        if wdays:
            month = int(wdays[0]["date"][5:7])
            if month != last_month:
                month_labels.append(
                    f'  <text x="{start_x + wi * pitch}" y="134" '
                    f'font-family="{MONO}" font-size="9.5" fill="#5c7391" '
                    f'letter-spacing="0.5">{MONTHS[month - 1]}</text>'
                )
                last_month = month
        for day in wdays:
            x = start_x + wi * pitch
            y = grid_y + day["weekday"] * pitch
            lv = level(day["contributionCount"])
            cells.append(
                f'  <rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{LEVELS[lv]}">'
                f'<title>{day["date"]}: {day["contributionCount"]}</title></rect>'
            )

    if days:
        last = days[-1]
        lx = start_x + (len(weeks) - 1) * pitch
        ly = grid_y + last["weekday"] * pitch
        cells.append(
            f'  <rect x="{lx - 1}" y="{ly - 1}" width="{cell + 2}" height="{cell + 2}" '
            f'rx="4" fill="none" stroke="#00e5ff" stroke-width="1.2" opacity="0.9">'
            f'<animate attributeName="opacity" values="0.9;0.25;0.9" dur="3s" '
            f'repeatCount="indefinite"/></rect>'
        )

    weekday_labels = []
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        weekday_labels.append(
            f'  <text x="86" y="{grid_y + row * pitch + 11}" text-anchor="end" '
            f'font-family="{MONO}" font-size="9" fill="#42566f">{name}</text>'
        )

    legend_colors = "".join(
        f'<rect x="{148 + i * 17}" y="270" width="13" height="13" rx="3" fill="{c}"/>'
        for i, c in enumerate(LEVELS)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 300" width="1200" height="300" role="img" aria-label="GitHub contribution telemetry: {total} contributions in the last year">
  <defs>
    <linearGradient id="num" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#eafdff"/>
      <stop offset="1" stop-color="#67ecff"/>
    </linearGradient>
    <radialGradient id="cglow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#00e5ff" stop-opacity="0.14"/>
      <stop offset="1" stop-color="#00e5ff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="cbar" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#00e5ff"/>
      <stop offset="1" stop-color="#8b5cf6"/>
    </linearGradient>
  </defs>

  <rect x="1" y="1" width="1198" height="298" rx="18" fill="#070c16" stroke="#16233b"/>
  <rect x="1" y="1" width="1198" height="298" rx="18" fill="url(#cglow)"/>
  <rect x="1" y="1" width="4" height="298" rx="2" fill="url(#cbar)"/>

  <text x="32" y="38" font-family="{MONO}" font-size="11" fill="#00e5ff" letter-spacing="3">// CONTRIBUTION TELEMETRY</text>
  <text x="32" y="90" font-family="{SANS}" font-size="44" font-weight="800" fill="url(#num)">{total}</text>
  <text x="34" y="110" font-family="{MONO}" font-size="9.5" fill="#5c7391" letter-spacing="1.5">CONTRIBUTIONS IN THE LAST YEAR</text>

  <g text-anchor="middle" font-family="{MONO}">
    <text x="1010" y="62" font-size="9.5" fill="#42566f" letter-spacing="1.5">STREAK</text>
    <text x="1010" y="90" font-size="22" font-weight="700" fill="#e8f1ff">{streak}<tspan font-size="12" fill="#7d8da6">d</tspan></text>
    <text x="1085" y="62" font-size="9.5" fill="#42566f" letter-spacing="1.5">PEAK DAY</text>
    <text x="1085" y="90" font-size="22" font-weight="700" fill="#e8f1ff">{peak}</text>
    <text x="1160" y="62" font-size="9.5" fill="#42566f" letter-spacing="1.5">ACTIVE</text>
    <text x="1160" y="90" font-size="22" font-weight="700" fill="#e8f1ff">{active}</text>
  </g>

{chr(10).join(month_labels)}
{chr(10).join(weekday_labels)}
{chr(10).join(cells)}

  <text x="96" y="281" font-family="{MONO}" font-size="9" fill="#42566f" letter-spacing="1.5">LESS</text>
  {legend_colors}
  <text x="{148 + len(LEVELS) * 17 + 4}" y="281" font-family="{MONO}" font-size="9" fill="#42566f" letter-spacing="1.5">MORE</text>
  <text x="1168" y="281" text-anchor="end" font-family="{MONO}" font-size="9" fill="#374a63" letter-spacing="1.2">UPDATED {updated}</text>
</svg>'''


MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "Inter,'Segoe UI',Helvetica,Arial,sans-serif"

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        payload = json.load(f)
    today = date.today().isoformat()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(render(payload, today))
    print(f"wrote {dst}")
