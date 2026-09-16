"""assets/rows/<slug>.svg -- one row per selected repo.

A row carries the name, the description in Aaryan's words, a five-cell strip
showing which layers the scanner actually found, the primary language and how
long ago it was pushed. The strip is filled from the same detection that feeds
the evidence table, so the two can never disagree.
"""

from __future__ import annotations

import re
import unicodedata
from xml.sax.saxutils import escape

BG = "#1b1a18"
CREAM = "#e9e3d6"
MUTED = "#8f887c"
DIM = "#5a564e"
STROKE = "#3a3833"
LANG = "#cfc8ba"

SERIF = "Newsreader, Georgia, serif"
MONO = "JetBrains Mono, ui-monospace, monospace"
SANS = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"

W, H = 760, 60
MAX_DESC = 64
BUDGET = 20 * 1024

# Layer order on the strip, and the scanner layer each cell reports on.
CELLS = [
    ("UI", "Interface"),
    ("API", "API"),
    ("DB", "Data"),
    ("AI", "AI"),
    ("OPS", "Deploy"),
]


def slug(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", normalized.lower())).strip("-")


def short_age(days: int | None) -> str:
    if days is None:
        return "—"
    if days <= 0:
        return "today"
    if days < 14:
        return f"{days} d"
    if days < 60:
        return f"{days // 7} wk"
    if days < 365:
        return f"{days // 30} mo"
    return f"{days // 365} yr"


def truncate(text: str, limit: int = MAX_DESC) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _strip(detected: dict, declared: set[str]) -> str:
    out = []
    for i, (label, layer) in enumerate(CELLS):
        x = 470 + i * 29
        hit = detected.get(layer)
        if hit and layer in declared:
            box = (f'<rect x="{x}" y="21" width="26" height="18" rx="3" '
                   f'class="cell-decl-box"/>')
            cls = "cell-decl-text"
        elif hit:
            box = (f'<rect x="{x}" y="21" width="26" height="18" rx="3" '
                   f'class="cell-hit-box"/>')
            cls = "cell-hit-text"
        else:
            box = (f'<rect x="{x}" y="21" width="26" height="18" rx="3" '
                   f'class="cell-dim-box"/>')
            cls = "cell-dim-text"
        out.append(
            box + f'<text x="{x + 13}" y="33.5" text-anchor="middle" '
            f'class="{cls}">{label}</text>'
        )
    return "".join(out)


def render(title: str, description: str, meta: dict,
           declared: set[str] | None = None) -> str:
    detected = {k: v for k, v in (meta.get("detected") or {}).items() if v}
    age = short_age(meta.get("age_days"))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img">',
        '<defs><style>'
        '.plate-bg { fill: #1b1a18; }'
        '.title-text { fill: #e9e3d6; font-family: Newsreader, Georgia, serif; font-size: 19px; }'
        '.desc-text { fill: #8f887c; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; font-size: 12.5px; }'
        '.lang-text { fill: #cfc8ba; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 11px; }'
        '.age-text { fill: #8f887c; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 11px; }'
        '.cell-hit-box { fill: #e9e3d6; }'
        '.cell-hit-text { fill: #1b1a18; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 8.5px; }'
        '.cell-dim-box { fill: none; stroke: #3a3833; }'
        '.cell-dim-text { fill: #5a564e; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 8.5px; }'
        '.cell-decl-box { fill: none; stroke: #e9e3d6; stroke-dasharray: 3 2; }'
        '.cell-decl-text { fill: #e9e3d6; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 8.5px; }'
        '@media (prefers-color-scheme: light) {'
        '.plate-bg { fill: #ede9e0; }'
        '.title-text { fill: #1a1a18; }'
        '.desc-text { fill: #5a564e; }'
        '.lang-text { fill: #4a443b; }'
        '.age-text { fill: #6b655c; }'
        '.cell-hit-box { fill: #1a1a18; }'
        '.cell-hit-text { fill: #ede9e0; }'
        '.cell-dim-box { fill: none; stroke: #cfc8ba; }'
        '.cell-dim-text { fill: #8f887c; }'
        '.cell-decl-box { fill: none; stroke: #1a1a18; }'
        '.cell-decl-text { fill: #1a1a18; }'
        '}'
        '</style></defs>',
        f'<rect width="{W}" height="{H}" rx="10" class="plate-bg"/>',
        f'<text x="22" y="27" class="title-text">{escape(title)}</text>',
        f'<text x="22" y="46" class="desc-text">{escape(truncate(description))}</text>',
        _strip(detected, declared or set()),
        f'<text x="740" y="27" text-anchor="end" class="lang-text">{escape(meta.get("language") or "—")}</text>',
        f'<text x="740" y="46" text-anchor="end" class="age-text">{escape(age)} ↗</text>',
        '</svg>',
    ]
    svg = "\n".join(parts) + "\n"
    if len(svg.encode()) > BUDGET:
        raise SystemExit(f"row {title} is over the 20 KB budget.")
    return svg


def alt_text(title: str, description: str, meta: dict) -> str:
    bits = [title]
    desc = " ".join((description or "").split())
    if desc:
        bits.append(desc)
    if meta.get("language"):
        bits.append(meta["language"])
    return " — ".join(bits[:2]) + (f". {bits[2]}." if len(bits) > 2 else ".")
