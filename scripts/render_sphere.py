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

W, H = 640, 400
CX, CY, R = 320, 200, 140
TILT = 0.35
DUR = "40s"
BUDGET = 150 * 1024

# Point count and keyframe count trade smoothness against file size. The first
# pair whose output fits the budget wins, so the choice is deterministic.
PROFILES = [(200, 36), (180, 32), (160, 30), (140, 28), (120, 24)]


def _round(value: float) -> str:
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def _frames(index: int, n: int, k_count: int):
    """Screen position and depth for one point across a full rotation."""
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
        out.append((CX + R * x, CY - R * y2, z2))
    return out


def _animate(attr: str, values: list[str]) -> str:
    return (f'<animate attributeName="{attr}" values="{";".join(values)}" '
            f'dur="{DUR}" repeatCount="indefinite"/>')


def _build(skills: list[str], version: str, n: int, k_count: int) -> str:
    # Labels ride a mid-latitude band. Points near the poles hardly move and
    # crowd each other, which made the still frame unreadable.
    label_at = {}
    if skills:
        lo, hi = 0.14, 0.86
        for j, skill in enumerate(skills):
            share = (j + 0.5) / len(skills)
            label_at[min(n - 1, int((lo + (hi - lo) * share) * n))] = skill

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img">',
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>',
        f'<text x="14" y="26" font-family="{MONO}" font-size="11" fill="{MUTED}">'
        'aaryan1524 · miami</text>',
        f'<text x="626" y="26" text-anchor="end" font-family="{MONO}" '
        f'font-size="11" fill="{MUTED}">{escape(version)} · est. 2004</text>',
        f'<text x="14" y="214" font-family="{SERIF}" font-style="italic" '
        f'font-size="44" fill="{SERIF_2}">Aaryan</text>',
        f'<text x="626" y="214" text-anchor="end" font-family="{SERIF}" '
        f'font-style="italic" font-size="44" fill="{SERIF_2}">Gajula</text>',
        '<g>',
    ]

    labels = []
    for i in range(n):
        frames = _frames(i, n, k_count)
        xs = [_round(f[0]) for f in frames]
        ys = [_round(f[1]) for f in frames]
        ops = [_round(0.12 + 0.88 * (f[2] + 1) / 2) for f in frames]
        parts.append(
            f'<circle cx="{xs[0]}" cy="{ys[0]}" r="1.6" fill="{CREAM}" '
            f'opacity="{ops[0]}">'
            + _animate("cx", xs) + _animate("cy", ys) + _animate("opacity", ops)
            + '</circle>'
        )
        if i in label_at:
            # Labels sit just off their dot and only show on the front half.
            lx = [_round(f[0] + 6) for f in frames]
            ly = [_round(f[1] + 4) for f in frames]
            lo = [_round(max(0.0, f[2])) for f in frames]
            labels.append(
                f'<text x="{lx[0]}" y="{ly[0]}" font-family="{SERIF}" '
                f'font-style="italic" font-size="13" fill="{CREAM}" '
                f'opacity="{lo[0]}">'
                + _animate("x", lx) + _animate("y", ly) + _animate("opacity", lo)
                + escape(label_at[i]) + '</text>'
            )

    parts.append("".join(labels))
    parts.append('</g>')
    parts.append(
        f'<text x="320" y="366" text-anchor="middle" font-family="{SERIF}" '
        f'font-size="24" fill="{CREAM}">I build the whole thing.</text>'
    )
    parts.append(
        f'<text x="320" y="386" text-anchor="middle" font-family="{SERIF}" '
        f'font-style="italic" font-size="14" fill="{MUTED}">'
        'Interface to infrastructure.</text>'
    )
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def render(skills: list[str], version: str) -> str:
    for n, k_count in PROFILES:
        svg = _build(skills, version, n, k_count)
        if len(svg.encode()) <= BUDGET:
            return svg
    return svg


def alt_text(skills: list[str]) -> str:
    listed = ", ".join(skills)
    return (f"Aaryan Gajula. I build the whole thing, interface to "
            f"infrastructure. A rotating sphere of dots labelled with the "
            f"tools I work in: {listed}.")
