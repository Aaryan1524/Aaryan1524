"""assets/contributions.svg -- GitHub activity grid plate.

Renders GitHub contribution calendar boxes in the profile aesthetic:
charcoal background (#1b1a18), monospace/serif typography, and warm cream gradient.
"""

from __future__ import annotations

from datetime import datetime

import ghapi

BG = "#1b1a18"
CREAM = "#e9e3d6"
MUTED = "#8f887c"
DIM = "#5a564e"
STROKE = "#34322e"
EMPTY = "#232220"
SUBTITLE = "#a8a193"

LEVEL_COLORS = [
    EMPTY,      # Level 0 (0 commits)
    "#4a443b",  # Level 1 (1-3)
    "#7e7464",  # Level 2 (4-9)
    "#b8ad99",  # Level 3 (10-19)
    "#e9e3d6",  # Level 4 (20+)
]

SERIF = "Newsreader, Georgia, serif"
MONO = "JetBrains Mono, ui-monospace, monospace"

W, H = 760, 170
BUDGET = 150 * 1024

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          firstDay
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def color_for_count(count: int) -> tuple[str, bool]:
    """Returns (fill_color, has_stroke)."""
    if count <= 0:
        return EMPTY, True
    if count <= 3:
        return LEVEL_COLORS[1], False
    if count <= 9:
        return LEVEL_COLORS[2], False
    if count <= 19:
        return LEVEL_COLORS[3], False
    return LEVEL_COLORS[4], False


def fetch_calendar(owner: str) -> dict | None:
    data = ghapi.graphql(QUERY, {"login": owner})
    if not isinstance(data, dict):
        return None
    try:
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except (KeyError, TypeError):
        return None


def render(owner: str, cached_cal: dict | None = None) -> tuple[str, int]:
    """Renders the SVG plate and returns (svg_string, total_contributions)."""
    cal = cached_cal or fetch_calendar(owner)
    if not cal:
        total = 0
        weeks = []
    else:
        total = cal.get("totalContributions", 0)
        weeks = cal.get("weeks", [])

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img">\n',
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>\n',
        # Header (left)
        f'<text x="28" y="33" font-family="{SERIF}" font-size="17" fill="{CREAM}">Contributions'
        f'<tspan font-family="{MONO}" font-size="11" fill="{DIM}"> · </tspan>'
        f'<tspan font-family="{MONO}" font-size="11.5" fill="{SUBTITLE}">{total:,} in the last year</tspan></text>\n',
    ]

    # Legend (right) aligned to x=732
    # Layout: Less [5 swatches: width 9, gap 3] More
    more_x = 732
    legend_y = 23
    swatches_end = more_x - 34
    swatches_start = swatches_end - (5 * 9 + 4 * 3)
    less_x = swatches_start - 8

    parts.append(
        f'<text x="{less_x}" y="31" text-anchor="end" font-family="{MONO}" '
        f'font-size="10" fill="{MUTED}">Less</text>\n'
    )
    for i, col in enumerate(LEVEL_COLORS):
        sx = swatches_start + i * 12
        stroke_attr = f' stroke="{STROKE}"' if i == 0 else ''
        parts.append(
            f'<rect x="{sx}" y="{legend_y}" width="9" height="9" rx="2" fill="{col}"{stroke_attr}/>\n'
        )
    parts.append(
        f'<text x="{more_x}" y="31" text-anchor="end" font-family="{MONO}" '
        f'font-size="10" fill="{MUTED}">More</text>\n'
    )

    # Weekday labels on left
    grid_top = 64
    x_start = 50
    box_size = 10
    step = 13

    day_labels = [("Mon", 1), ("Wed", 3), ("Fri", 5)]
    for label, day_idx in day_labels:
        ly = grid_top + day_idx * step + 8.5
        parts.append(
            f'<text x="42" y="{ly:.1f}" text-anchor="end" font-family="{MONO}" '
            f'font-size="9" fill="{DIM}">{label}</text>\n'
        )

    # Month labels above columns
    last_month = None
    for w_idx, week in enumerate(weeks):
        first_day_str = week.get("firstDay", "")
        if first_day_str:
            try:
                dt = datetime.strptime(first_day_str, "%Y-%m-%d")
                month = dt.month
                if month != last_month and w_idx < 50:
                    mx = x_start + w_idx * step
                    month_name = MONTH_NAMES[month - 1]
                    parts.append(
                        f'<text x="{mx}" y="53" font-family="{MONO}" font-size="9.5" '
                        f'fill="{MUTED}">{month_name}</text>\n'
                    )
                    last_month = month
            except ValueError:
                pass

    # Grid of boxes
    for w_idx, week in enumerate(weeks):
        for day in week.get("contributionDays", []):
            w_day = day.get("weekday", 0)
            count = day.get("contributionCount", 0)
            bx = x_start + w_idx * step
            by = grid_top + w_day * step
            fill, has_stroke = color_for_count(count)
            stroke_attr = f' stroke="{STROKE}"' if has_stroke else ''
            parts.append(
                f'<rect x="{bx}" y="{by}" width="{box_size}" height="{box_size}" '
                f'rx="2" fill="{fill}"{stroke_attr}/>\n'
            )

    parts.append('</svg>\n')
    svg = "".join(parts)
    if len(svg.encode()) > BUDGET:
        raise SystemExit(f"contributions.svg is over the {BUDGET // 1024} KB budget.")
    return svg, total


def alt_text(total: int) -> str:
    return f"GitHub contribution calendar: {total:,} contributions in the last year."
