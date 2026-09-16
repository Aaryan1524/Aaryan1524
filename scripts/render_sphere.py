"""assets/sphere.svg -- the hero plate.

A Fibonacci sphere of dots rotating about its vertical axis, with skill labels
riding the points and fading out as they pass behind. GitHub renders SVG as an
image: no JavaScript, no hover, so the motion is SMIL and the first frame has
to stand on its own as a still.
"""

from __future__ import annotations

import math
from xml.sax.saxutils import escape

BG = "#1b1a18"
CREAM = "#e9e3d6"
SERIF_2 = "#a8a193"
MUTED = "#8f887c"

SERIF = "Newsreader, Georgia, serif"
MONO = "JetBrains Mono, ui-monospace, monospace"

W, H = 760, 470
CX, CY, R = 380, 215, 125
TILT = 0.35
DUR = "40s"
BUDGET = 150 * 1024
N, K = 160, 30
MAX_LABELS = 12

# Labels fade out towards the left and right edges of the sphere as well as
# towards the back, so they stay in a front-centre band and can never reach
# the names sitting at x=28 and x=732.
BAND = 0.62


def _round(value: float) -> str:
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def _frames(index: int, n: int, k_count: int):
    """Screen position, depth and horizontal offset across a full rotation."""
    y = 1 - 2 * (index + 0.5) / n
    r = math.sqrt(max(0.0, 1 - y * y))
    phi = index * math.pi * (3 - math.sqrt(5))
    out = []
    for k in range(k_count + 1):  # last frame repeats the first, so it loops
        theta = phi + 2 * math.pi * k / k_count
        x = r * math.cos(theta)
        z = r * math.sin(theta)
        y2 = y * math.cos(TILT) - z * math.sin(TILT)
        z2 = y * math.sin(TILT) + z * math.cos(TILT)
        out.append((CX + R * x, CY - R * y2, z2, x))
    return out


def _label_opacity(z2: float, x: float) -> float:
    """Front-centre band only: dark at the back, gone at the left and right."""
    edge = max(0.0, 1 - (x / BAND) ** 2)
    return max(0.0, z2) * edge


def _animate(attr: str, values: list[str]) -> str:
    return (f'<animate attributeName="{attr}" values="{";".join(values)}" '
            f'dur="{DUR}" repeatCount="indefinite"/>')


def _build(skills: list[str], version: str, n: int, k_count: int) -> str:
    labels_wanted = skills[:MAX_LABELS]
    label_at = {}
    if labels_wanted:
        lo, hi = 0.14, 0.86
        for j, skill in enumerate(labels_wanted):
            share = (j + 0.5) / len(labels_wanted)
            label_at[min(n - 1, int((lo + (hi - lo) * share) * n))] = skill

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img">',
        '<defs><style>'
        '.plate-bg { fill: #1b1a18; }'
        '.meta-text { fill: #8f887c; font-family: JetBrains Mono, ui-monospace, monospace; font-size: 12px; }'
        '.name-text { fill: #a8a193; font-family: Newsreader, Georgia, serif; font-style: italic; font-size: 42px; }'
        '.sphere-dot { fill: #e9e3d6; }'
        '.skill-label { fill: #e9e3d6; font-family: Newsreader, Georgia, serif; font-style: italic; font-size: 14px; }'
        '.tagline-text { fill: #e9e3d6; font-family: Newsreader, Georgia, serif; font-size: 28px; }'
        '.subline-text { fill: #8f887c; font-family: Newsreader, Georgia, serif; font-style: italic; font-size: 17px; }'
        '@media (prefers-color-scheme: light) {'
        '.plate-bg { fill: #ede9e0; }'
        '.meta-text { fill: #6b655c; }'
        '.name-text { fill: #5a564e; }'
        '.sphere-dot { fill: #1a1a18; }'
        '.skill-label { fill: #1a1a18; }'
        '.tagline-text { fill: #1a1a18; }'
        '.subline-text { fill: #6b655c; }'
        '}'
        '</style></defs>',
        f'<rect width="{W}" height="{H}" rx="14" class="plate-bg"/>',
        f'<text x="28" y="34" class="meta-text">aaryan1524 · miami</text>',
        f'<text x="732" y="34" text-anchor="end" class="meta-text">{escape(version)} · est. 2004</text>',
        f'<text x="28" y="228" class="name-text">Aaryan</text>',
        f'<text x="732" y="228" text-anchor="end" class="name-text">Gajula</text>',
        '<g>',
    ]

    labels = []
    for i in range(n):
        frames = _frames(i, n, k_count)
        xs = [_round(f[0]) for f in frames]
        ys = [_round(f[1]) for f in frames]
        ops = [_round(0.12 + 0.88 * (f[2] + 1) / 2) for f in frames]
        dot_r = "2.2" if i in label_at else "1.5"
        parts.append(
            f'<circle cx="{xs[0]}" cy="{ys[0]}" r="{dot_r}" class="sphere-dot" '
            f'opacity="{ops[0]}">'
            + _animate("cx", xs) + _animate("cy", ys) + _animate("opacity", ops)
            + '</circle>'
        )
        if i in label_at:
            lx = [_round(f[0] + 8) for f in frames]
            ly = [_round(f[1] + 5) for f in frames]
            lo = [_round(_label_opacity(f[2], f[3])) for f in frames]
            labels.append(
                f'<text x="{lx[0]}" y="{ly[0]}" class="skill-label" '
                f'opacity="{lo[0]}">'
                + _animate("x", lx) + _animate("y", ly) + _animate("opacity", lo)
                + escape(label_at[i]) + '</text>'
            )

    parts.append("".join(labels))
    parts.append('</g>')
    parts.append(
        f'<text x="380" y="400" text-anchor="middle" class="tagline-text">I build the whole thing.</text>'
    )
    parts.append(
        f'<text x="380" y="432" text-anchor="middle" class="subline-text">'
        'Interface to infrastructure.</text>'
    )
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def render(skills: list[str], version: str) -> str:
    svg = _build(skills, version, N, K)
    if len(svg.encode()) > BUDGET:
        raise SystemExit(
            f"sphere.svg is {len(svg.encode()) // 1024} KB, over the 150 KB "
            "budget. Lower N or K in render_sphere.py.")
    return svg


def alt_text(skills: list[str]) -> str:
    listed = ", ".join(skills[:MAX_LABELS])
    return (f"Aaryan Gajula. I build the whole thing, interface to "
            f"infrastructure. A rotating sphere of dots labelled with the "
            f"tools I work in: {listed}.")
