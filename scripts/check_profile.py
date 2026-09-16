#!/usr/bin/env python3
"""Check the profile artifacts that are too easy to regress by hand."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

import render_row
import render_sphere

ROOT = Path(__file__).resolve().parent.parent
SVG_LIMIT = 150 * 1024
ROW_LIMIT = 20 * 1024


def fail(message: str) -> None:
    raise SystemExit(f"profile check: {message}")


def sphere_labels_clear(skills: list[str]) -> None:
    """Check the four specified keyframes against conservative name bounds."""
    names = ((28, 170), (590, 732))
    labels = skills[:render_sphere.MAX_LABELS]
    if not labels:
        return
    lo, hi = 0.14, 0.86
    indexed = [min(render_sphere.N - 1, int(
        (lo + (hi - lo) * (index + .5) / len(labels)) * render_sphere.N))
        for index in range(len(labels))]
    for frame in (0, 9, 18, 27):
        for index, skill in zip(indexed, labels):
            x, y, z, raw_x = render_sphere._frames(
                index, render_sphere.N, render_sphere.K)[frame]
            if render_sphere._label_opacity(z, raw_x) <= 0:
                continue
            left, right = x + 8, x + 8 + len(skill) * 8.5
            # Text baselines share the names' vertical band only near y=228.
            vertical_overlap = (y + 5 - 14) < 236 and (y + 5) > 185
            if vertical_overlap and any(left < end and right > start
                                        for start, end in names):
                fail(f"sphere label {skill!r} overlaps a name at frame {frame}")


def main() -> int:
    config = yaml.safe_load((ROOT / "projects.yml").read_text())
    readme = (ROOT / "README.md").read_text()
    if "Founder of Te Vārtā · CS at FIU '27 · SWE intern at CoOrdio Health, summer 2026." not in readme:
        fail("the required one-line introduction is missing")
    if "What brings you here?" in readme:
        fail("removed card prompt is still present")
    if readme.count("<details>") != 1:
        fail("README must contain only the collapsed evidence section")
    if "<summary>Evidence: where each layer was detected</summary>" not in readme:
        fail("evidence section is not collapsed")
    matrix = re.search(r"<!-- MATRIX:START -->(.*?)<!-- MATRIX:END -->",
                       readme, re.S)
    if not matrix:
        fail("evidence marker block is missing")
    for row in matrix.group(1).splitlines():
        if not row.startswith("| ") or row.startswith("| Project "):
            continue
        cells = row.split("|")[2:7]
        if sum(cell.strip() != "—" for cell in cells) < 3:
            fail("evidence table contains a row with fewer than three layers")

    sphere = ROOT / "assets" / "sphere.svg"
    card = ROOT / "assets" / "card.svg"
    contributions = ROOT / "assets" / "contributions.svg"
    for path in [sphere, card, contributions, *(ROOT / "assets" / f"flagship-{f['key']}.svg"
                                 for f in config["flagships"])]:
        if not path.exists() or path.stat().st_size >= SVG_LIMIT:
            fail(f"missing or oversized SVG: {path.relative_to(ROOT)}")
    if 'viewBox="0 0 760 470"' not in sphere.read_text():
        fail("sphere canvas is not 760×470")
    if len(re.findall(r"<circle ", sphere.read_text())) != 160:
        fail("sphere does not have 160 dots")
    for path in (ROOT / "assets" / "rows").glob("*.svg"):
        if path.stat().st_size >= ROW_LIMIT:
            fail(f"oversized work row: {path.relative_to(ROOT)}")

    repos_markup = re.search(
        r"<!-- REPOS:START -->(.*?)<!-- REPOS:END -->", readme, re.S)
    if not repos_markup:
        fail("repos marker block is missing")
    for group in config["groups"]:
        for repo in group["repos"]:
            slug = render_row.slug(repo["title"])
            row = ROOT / "assets" / "rows" / f"{slug}.svg"
            if not row.exists():
                fail(f"missing work row: {row.relative_to(ROOT)}")
            expected_href = f'href="https://github.com/{repo["repo"]}"'
            expected_src = f'assets/rows/{slug}.svg'
            if expected_href not in repos_markup.group(1) or expected_src not in repos_markup.group(1):
                fail(f"repo is missing its link or image in README: {slug}")

    card_text = card.read_text()
    for values, times in (
        ("0;1;1;0;0", "0;0.03;0.303;0.333;1"),
        ("0;0;1;1;0;0", "0;0.333;0.363;0.636;0.666;1"),
        ("0;0;1;1;0", "0;0.666;0.696;0.97;1"),
    ):
        if f'values="{values}" keyTimes="{times}" dur="18s"' not in card_text:
            fail("card slide timing differs from the specification")
    sphere_labels_clear(config.get("skills", []))
    print("profile artifact checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
