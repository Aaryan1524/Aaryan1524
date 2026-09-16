"""assets/card.svg -- the chat card that answers whoever is reading.

Three audiences share one 18 second loop, mirroring the onboarding card on
tevarta.com. Slides fade fully out before the next fades in, so two answers are
never on screen together. Each answer is revealed by animating the width of its
own clip rect, which reads as the line typing itself in.

GitHub renders SVG as an image, so the motion is SMIL and the still frame has
to stand on its own: slide one's base attributes are its settled state, and the
other two start hidden.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

BG = "#1b1a18"
CREAM = "#e9e3d6"
SERIF_2 = "#a8a193"
MUTED = "#8f887c"
BUBBLE = "#2a2926"
STROKE = "#3a3833"
TAG_TEXT = "#cfc8ba"

SERIF = "Newsreader, Georgia, serif"
MONO = "JetBrains Mono, ui-monospace, monospace"
SANS = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"

W, H = 760, 250
DUR = "18s"
BUDGET = 150 * 1024
RIGHT = 728          # right edge of the question bubble
CLIP_X, CLIP_Y, CLIP_H = 84, 136, 44
CLIP_W = 660

# Per slide: when the group is visible, when the answer types in, and when the
# tags appear. Values and keyTimes always come in pairs.
TIMING = [
    {
        "group": ("0;1;1;0;0", "0;0.03;0.303;0.333;1"),
        "clip": ("0;0;660;660", "0;0.04;0.10;1"),
        "tags": ("0;0;1;1", "0;0.10;0.13;1"),
    },
    {
        "group": ("0;0;1;1;0;0", "0;0.333;0.363;0.636;0.666;1"),
        "clip": ("0;0;660;660", "0;0.373;0.433;1"),
        "tags": ("0;0;1;1", "0;0.433;0.463;1"),
    },
    {
        "group": ("0;0;1;1;0", "0;0.666;0.696;0.97;1"),
        "clip": ("0;0;660;660", "0;0.706;0.766;1"),
        "tags": ("0;0;1;1", "0;0.766;0.796;1"),
    },
]


def _animate(attr: str, values: str, key_times: str) -> str:
    return (f'<animate attributeName="{attr}" values="{values}" '
            f'keyTimes="{key_times}" dur="{DUR}" repeatCount="indefinite"/>')


def _bubble_width(text: str) -> float:
    return len(text) * 8.2 + 36


def _tag_width(text: str) -> float:
    return len(text) * 7.3 + 24


def _progress(index: int) -> str:
    out = []
    for slot, x in enumerate((664, 688, 712)):
        cls = "prog-active" if slot == index else "prog-dim"
        out.append(f'<rect x="{x}" y="33" width="18" height="2" class="{cls}"/>')
    return "".join(out)


def _tags(tags: list[str]) -> str:
    out = []
    x = 84.0
    for tag in tags:
        width = _tag_width(tag)
        out.append(
            f'<rect x="{x:.0f}" y="194" width="{width:.0f}" height="28" '
            f'rx="14" class="tag-box"/>'
            f'<text x="{x + width / 2:.0f}" y="212" text-anchor="middle" '
            f'class="tag-text">'
            f'{escape(tag)}</text>'
        )
        x += width + 8
    return "".join(out)


def _slide(index: int, entry: dict) -> str:
    timing = TIMING[index]
    first = index == 0
    clip_id = f"type{index}"

    question = entry["question"]
    bubble_w = _bubble_width(question)
    bubble_x = RIGHT - bubble_w

    group_values, group_times = timing["group"]
    clip_values, clip_times = timing["clip"]
    tag_values, tag_times = timing["tags"]

    return (
        f'<clipPath id="{clip_id}">'
        f'<rect x="{CLIP_X}" y="{CLIP_Y}" width="{CLIP_W if first else 0}" '
        f'height="{CLIP_H}">{_animate("width", clip_values, clip_times)}</rect>'
        f'</clipPath>'
        f'<g opacity="{1 if first else 0}">'
        + _animate("opacity", group_values, group_times) +
        f'<text x="32" y="38" font-size="12" '
        f'class="muted-text">{escape(entry["audience"])}</text>'
        + _progress(index) +
        f'<text x="{RIGHT}" y="72" text-anchor="end" '
        f'font-size="11" class="muted-text">you</text>'
        f'<rect x="{bubble_x:.0f}" y="82" width="{bubble_w:.0f}" height="40" '
        f'rx="20" class="bubble-bg"/>'
        f'<text x="{bubble_x + 18:.0f}" y="108" '
        f'class="bubble-text">{escape(question)}</text>'
        f'<circle cx="52" cy="160" r="18" class="avatar-circle"/>'
        f'<text x="52" y="165" text-anchor="middle" '
        f'class="avatar-text">AG</text>'
        f'<g clip-path="url(#{clip_id})">'
        f'<text x="84" y="168" '
        f'class="answer-text">{escape(entry["answer"])}</text></g>'
        f'<g opacity="{1 if first else 0}">'
        + _animate("opacity", tag_values, tag_times)
        + _tags(entry["tags"]) +
        '</g></g>'
    )


def render(entries: list[dict]) -> str:
    if len(entries) != 3:
        raise SystemExit("card.svg requires exactly three slides.")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img">',
        '<defs><style>'
        '.plate-bg { fill: #1b1a18; }'
        '.muted-text { fill: #8f887c; font-family: JetBrains Mono, ui-monospace, monospace; }'
        '.bubble-bg { fill: #2a2926; stroke: #3a3833; }'
        '.bubble-text { fill: #e9e3d6; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; font-size: 16px; }'
        '.avatar-circle { fill: #e9e3d6; }'
        '.avatar-text { fill: #1b1a18; font-family: Newsreader, Georgia, serif; font-size: 14px; font-weight: 600; }'
        '.answer-text { fill: #e9e3d6; font-family: Newsreader, Georgia, serif; font-size: 22px; }'
        '.tag-box { fill: none; stroke: #3a3833; }'
        '.tag-text { fill: #cfc8ba; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 12px; }'
        '.prog-active { fill: #e9e3d6; }'
        '.prog-dim { fill: #3a3833; }'
        '@media (prefers-color-scheme: light) {'
        '.plate-bg { fill: #ede9e0; }'
        '.muted-text { fill: #6b655c; }'
        '.bubble-bg { fill: #dfd9cd; stroke: #cfc8ba; }'
        '.bubble-text { fill: #1a1a18; }'
        '.avatar-circle { fill: #1a1a18; }'
        '.avatar-text { fill: #ede9e0; }'
        '.answer-text { fill: #1a1a18; }'
        '.tag-box { stroke: #cfc8ba; }'
        '.tag-text { fill: #4a443b; }'
        '.prog-active { fill: #1a1a18; }'
        '.prog-dim { fill: #cfc8ba; }'
        '}'
        '</style></defs>',
        f'<rect width="{W}" height="{H}" rx="14" class="plate-bg"/>',
    ]
    for index, entry in enumerate(entries[:3]):
        parts.append(_slide(index, entry))
    parts.append('</svg>')
    svg = "\n".join(parts) + "\n"
    if len(svg.encode()) > BUDGET:
        raise SystemExit("card.svg is over the 150 KB budget.")
    return svg


def alt_text(entries: list[dict]) -> str:
    lines = []
    for entry in entries[:3]:
        lines.append(f'{entry["audience"]}, "{entry["question"]}" — '
                     f'{entry["answer"]} ({", ".join(entry["tags"])})')
    return ("A card cycling through three answers, one per audience. "
            + " ".join(lines))
