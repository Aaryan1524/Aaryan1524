"""assets/card.svg -- the chat card that answers whoever is reading.

Three audiences share one 18 second loop, mirroring the onboarding card on
tevarta.com. Group one is opaque at rest so the still frame reads correctly.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

BG = "#1b1a18"
CREAM = "#e9e3d6"
SERIF_2 = "#a8a193"
MUTED = "#8f887c"
FIELD = "#232220"
FIELD_STROKE = "#34322e"
TAG_STROKE = "#3a3833"
TAG_TEXT = "#cfc8ba"

SERIF = "Newsreader, Georgia, serif"
MONO = "JetBrains Mono, ui-monospace, monospace"

W, H = 640, 220
DUR = "18s"

# Each group holds the stage for about a third of the loop, with a short
# crossfade between them. Values and keyTimes come in pairs.
CYCLE = [
    ("1;1;0;0;1", "0;0.305;0.333;0.972;1"),
    ("0;0;1;1;0;0", "0;0.305;0.333;0.638;0.666;1"),
    ("0;0;1;1;0", "0;0.638;0.666;0.972;1"),
]


def _avatar(cx: int, cy: int) -> str:
    return (f'<circle cx="{cx}" cy="{cy}" r="14" fill="{CREAM}"/>'
            f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" '
            f'font-family="{SERIF}" font-size="12" fill="{BG}">AG</text>')


def _tags(tags: list[str], x0: int, y: int) -> str:
    out = []
    x = x0
    for tag in tags:
        width = round(len(tag) * 6.7 + 22)
        if x + width > W - 20:  # wrap rather than run off the plate
            x = x0
            y += 28
        out.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="22" rx="11" '
            f'fill="none" stroke="{TAG_STROKE}"/>'
            f'<text x="{x + width / 2:.0f}" y="{y + 15}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="11" fill="{TAG_TEXT}">'
            f'{escape(tag)}</text>'
        )
        x += width + 8
    return "".join(out)


def _group(entry: dict, values: str, key_times: str, rest: str) -> str:
    return (
        f'<g opacity="{rest}">'
        f'<animate attributeName="opacity" values="{values}" '
        f'keyTimes="{key_times}" dur="{DUR}" repeatCount="indefinite"/>'
        f'<text x="20" y="26" font-family="{MONO}" font-size="11" fill="{MUTED}">'
        f'{escape(entry["audience"])}</text>'
        + _avatar(34, 58) +
        f'<text x="58" y="63" font-family="{SERIF}" font-style="italic" '
        f'font-size="15" fill="{SERIF_2}">What brings you here?</text>'
        f'<rect x="20" y="80" width="600" height="34" rx="8" fill="{FIELD}" '
        f'stroke="{FIELD_STROKE}"/>'
        f'<text x="36" y="102" font-family="{SERIF}" font-size="14" '
        f'fill="{CREAM}">{escape(entry["question"])}</text>'
        + _avatar(34, 140) +
        f'<text x="58" y="145" font-family="{SERIF}" font-size="15" '
        f'fill="{CREAM}">{escape(entry["reply"])}</text>'
        + _tags(entry["tags"], 20, 168) +
        '</g>'
    )


def render(entries: list[dict]) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img">',
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>',
    ]
    for index, entry in enumerate(entries[:3]):
        values, key_times = CYCLE[index]
        parts.append(_group(entry, values, key_times, "1" if index == 0 else "0"))
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def alt_text(entries: list[dict]) -> str:
    lines = []
    for entry in entries[:3]:
        lines.append(f'{entry["audience"]}: "{entry["question"]}" — '
                     f'{entry["reply"]} ({", ".join(entry["tags"])})')
    return "A chat card cycling through three answers. " + " ".join(lines)
