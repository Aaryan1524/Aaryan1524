"""assets/flagship-<key>.svg -- one card per flagship.

Two of these sit side by side under the hero. Everything on a card comes from
projects.yml: there is no scanned content here, because neither flagship is a
public repo whose source could be read.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

BG = "#1b1a18"
CREAM = "#e9e3d6"
SERIF_2 = "#a8a193"
MUTED = "#8f887c"
STROKE = "#3a3833"

SERIF = "Newsreader, Georgia, serif"
MONO = "JetBrains Mono, ui-monospace, monospace"
SANS = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"

W, H = 380, 260
MAX_FACTS = 3
MAX_FACT_CHARS = 28
FACT_Y = (170, 193, 216)
BUDGET = 150 * 1024


def render(flag: dict, number: int) -> str:
    facts = (flag.get("facts") or [])[:MAX_FACTS]
    for label, value in facts:
        if len(str(value)) > MAX_FACT_CHARS:
            raise SystemExit(
                f"flagship {flag['key']}: fact {label!r} is "
                f"{len(str(value))} characters, over the {MAX_FACT_CHARS} "
                f"the card can hold: {value!r}")

    # A flagship with nowhere to point says so rather than showing a dead link.
    has_link = bool(flag.get("url") or flag.get("poster"))
    link_label = flag["link_label"] if has_link else "poster in progress"
    link_fill = CREAM if has_link else MUTED

    title_size = 38
    if len(flag["title"]) > 18:
        title_size = 26
    elif len(flag["title"]) > 14:
        title_size = 31

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img">',
        '<defs><style>'
        '.plate-bg { fill: #1b1a18; }'
        '.meta-text { fill: #8f887c; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 11px; }'
        f'.title-text {{ fill: #e9e3d6; font-family: Newsreader, Georgia, serif; font-size: {title_size}px; }}'
        '.dek-text { fill: #a8a193; font-family: Newsreader, Georgia, serif; font-style: italic; font-size: 17px; }'
        '.rule-line { stroke: #3a3833; }'
        '.fact-label { fill: #8f887c; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 11px; }'
        '.fact-value { fill: #e9e3d6; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; font-size: 13px; }'
        '.link-active { fill: #e9e3d6; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 12px; }'
        '.link-dim { fill: #8f887c; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 12px; }'
        '@media (prefers-color-scheme: light) {'
        '.plate-bg { fill: #ede9e0; }'
        '.meta-text { fill: #6b655c; }'
        '.title-text { fill: #1a1a18; }'
        '.dek-text { fill: #5a564e; }'
        '.rule-line { stroke: #dcd6cb; }'
        '.fact-label { fill: #6b655c; }'
        '.fact-value { fill: #1a1a18; }'
        '.link-active { fill: #1a1a18; }'
        '.link-dim { fill: #6b655c; }'
        '}'
        '</style></defs>',
        f'<rect width="{W}" height="{H}" rx="14" class="plate-bg"/>',
        f'<text x="24" y="34" class="meta-text">{escape(flag["tag"])}</text>',
        f'<text x="356" y="34" text-anchor="end" class="meta-text">{number:02d}</text>',
        f'<text x="24" y="92" class="title-text">{escape(flag["title"])}</text>',
        f'<text x="24" y="120" class="dek-text">{escape(flag["dek"])}</text>',
        f'<line x1="24" y1="142" x2="356" y2="142" class="rule-line"/>',
    ]
    for (label, value), y in zip(facts, FACT_Y):
        parts.append(
            f'<text x="24" y="{y}" class="fact-label">{escape(str(label))}</text>'
            f'<text x="92" y="{y}" class="fact-value">{escape(str(value))}</text>'
        )
    link_class = "link-active" if has_link else "link-dim"
    parts.append(
        f'<text x="356" y="240" text-anchor="end" class="{link_class}">{escape(link_label)}</text>'
    )
    parts.append('</svg>')
    svg = "\n".join(parts) + "\n"
    if len(svg.encode()) > BUDGET:
        raise SystemExit(f"flagship-{flag['key']}.svg is over 150 KB.")
    return svg


def alt_text(flag: dict) -> str:
    facts = ", ".join(f"{label} {value}"
                      for label, value in (flag.get("facts") or []))
    return f'{flag["title"]}: {flag["dek"]} {facts}.'


def href(flag: dict) -> str | None:
    """Where the card links, or None when it should not be wrapped at all."""
    return flag.get("url") or flag.get("poster") or None
