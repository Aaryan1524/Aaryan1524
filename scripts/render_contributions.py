"""assets/contributions.svg -- GitHub activity grid plate.

Renders GitHub contribution calendar boxes in the profile aesthetic:
charcoal background (#1b1a18) in dark mode, and warm cream paper (#ede9e0)
with dark ink text in light mode via prefers-color-scheme.
"""

from __future__ import annotations

from datetime import datetime

import ghapi

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


def level_for_count(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 3:
        return 1
    if count <= 9:
        return 2
    if count <= 19:
        return 3
    return 4


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
        '<defs>\n<style>\n'
        '  .plate-bg { fill: #1b1a18; }\n'
        '  .title-text { fill: #e9e3d6; font-family: Newsreader, Georgia, serif; font-size: 17px; }\n'
        '  .dot-text { fill: #5a564e; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 11px; }\n'
        '  .sub-text { fill: #a8a193; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 11.5px; }\n'
        '  .muted-text { fill: #8f887c; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 10px; }\n'
        '  .month-text { fill: #8f887c; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 9.5px; }\n'
        '  .dim-text { fill: #5a564e; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 9px; }\n'
        '  .lvl-0 { fill: #232220; stroke: #34322e; }\n'
        '  .lvl-1 { fill: #4a443b; }\n'
        '  .lvl-2 { fill: #7e7464; }\n'
        '  .lvl-3 { fill: #b8ad99; }\n'
        '  .lvl-4 { fill: #e9e3d6; }\n'
        '  @media (prefers-color-scheme: light) {\n'
        '    .plate-bg { fill: #ede9e0; }\n'
        '    .title-text { fill: #1a1a18; }\n'
        '    .dot-text { fill: #8f887c; }\n'
        '    .sub-text { fill: #5a564e; }\n'
        '    .muted-text { fill: #6b655c; }\n'
        '    .month-text { fill: #6b655c; }\n'
        '    .dim-text { fill: #8f887c; }\n'
        '    .lvl-0 { fill: #ded9cd; stroke: #cfc8ba; }\n'
        '    .lvl-1 { fill: #b8ad99; }\n'
        '    .lvl-2 { fill: #857a6b; }\n'
        '    .lvl-3 { fill: #544e43; }\n'
        '    .lvl-4 { fill: #1a1a18; }\n'
        '  }\n'
        '</style>\n</defs>\n',
        f'<rect width="{W}" height="{H}" rx="12" class="plate-bg"/>\n',
        # Header (left)
        f'<text x="28" y="33" class="title-text">Contributions'
        f'<tspan class="dot-text"> · </tspan>'
        f'<tspan class="sub-text">{total:,} in the last year</tspan></text>\n',
    ]

    # Legend (right) aligned to x=732
    more_x = 732
    legend_y = 23
    swatches_end = more_x - 34
    swatches_start = swatches_end - (5 * 9 + 4 * 3)
    less_x = swatches_start - 8

    parts.append(
        f'<text x="{less_x}" y="31" text-anchor="end" class="muted-text">Less</text>\n'
    )
    for i in range(5):
        sx = swatches_start + i * 12
        parts.append(
            f'<rect x="{sx}" y="{legend_y}" width="9" height="9" rx="2" class="lvl-{i}"/>\n'
        )
    parts.append(
        f'<text x="{more_x}" y="31" text-anchor="end" class="muted-text">More</text>\n'
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
            f'<text x="42" y="{ly:.1f}" text-anchor="end" class="dim-text">{label}</text>\n'
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
                        f'<text x="{mx}" y="53" class="month-text">{month_name}</text>\n'
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
            lvl = level_for_count(count)
            parts.append(
                f'<rect x="{bx}" y="{by}" width="{box_size}" height="{box_size}" '
                f'rx="2" class="lvl-{lvl}"/>\n'
            )

    parts.append('</svg>\n')
    svg = "".join(parts)
    if len(svg.encode()) > BUDGET:
        raise SystemExit(f"contributions.svg is over the {BUDGET // 1024} KB budget.")
    return svg, total


def alt_text(total: int) -> str:
    return f"GitHub contribution calendar: {total:,} contributions in the last year."
