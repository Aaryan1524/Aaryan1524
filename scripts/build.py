#!/usr/bin/env python3
"""Rebuild the profile page from projects.yml and what the code actually shows.

  python scripts/build.py           write assets/ and the README marker blocks
  python scripts/build.py --check   fail if a rebuild would change anything

Locally:  export PROFILE_SCAN_TOKEN=$(gh auth token)
"""

from __future__ import annotations

import html
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

import render_card
import render_flagship
import render_readme
import render_row
import render_sphere
import scan

ROOT = Path(__file__).resolve().parent.parent
BORN = 2004


def load(name: str) -> dict:
    with (ROOT / name).open() as handle:
        return yaml.safe_load(handle)


def version_string(entries: list[dict], scanned: dict, owner: str,
                   now: datetime) -> str:
    major = now.year - BORN
    recent = now - timedelta(days=30)
    minor = sum(
        1 for entry in entries
        if (meta := scanned.get(entry["repo"]))
        and not meta.get("missing")
        and meta["pushed_at"]
        and meta["pushed_at"] > recent
    )
    patch = scan.commits_this_year(owner)
    return f"v{major}.{minor}.{patch}"


def scan_report(entries: list[dict], scanned: dict, conflicts: list[str],
                now: datetime) -> str:
    """Hygiene notes for Aaryan. Never rendered on the page."""
    lines = [
        "# Scan report",
        "",
        f"Generated {now.strftime('%Y-%m-%d')} by `scripts/build.py`.",
        "This file is for me, not for visitors. Nothing here is published.",
        "",
        "## Listed repos needing attention",
        "",
    ]
    flagged = 0
    for entry in entries:
        meta = scanned.get(entry["repo"])
        notes = []
        if not meta or meta.get("missing"):
            notes.append("not found through the API (renamed, deleted, or the "
                         "token cannot see it)")
        else:
            if not meta["has_readme"]:
                notes.append("no README")
            if not meta["description"]:
                notes.append("no repo description")
            if not meta["topics"]:
                notes.append("no topics")
            if meta["archived"]:
                notes.append("archived on GitHub")
            if not entry.get("line"):
                notes.append("no blurb in projects.yml, so the line renders bare")
        if notes:
            flagged += 1
            lines.append(f"- **{entry['repo']}** — " + "; ".join(notes))
    if not flagged:
        lines.append("- Nothing flagged.")

    lines += ["", "## Detection conflicts", ""]
    lines += [f"- {c}" for c in conflicts] or ["- None."]
    return "\n".join(lines) + "\n"


def write(path: Path, text: str, changed: list[str]) -> None:
    current = path.read_text() if path.exists() else None
    if current != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        changed.append(str(path.relative_to(ROOT)))


def main() -> int:
    check_only = "--check" in sys.argv
    config = load("projects.yml")
    rules = load("detect_rules.yml")
    now = render_readme.now_utc()

    owner = config["owner"]
    settings = config.get("settings", {})
    declared_mode = settings.get("table_mode") == "declared"

    entries = [e for group in config["groups"] for e in group["repos"]]
    flag_entries = [
        {"repo": f["repo"], "title": f["title"], "line": "", "in_matrix": True}
        for f in config["flagships"] if f.get("repo")
    ]

    scanned: dict[str, dict] = {}
    conflicts: list[str] = []
    selected = [entry for entry in entries if entry.get("selected")]
    if len(selected) > 6:
        raise SystemExit("At most six repos may be marked selected: true.")
    for entry in selected:
        if not " ".join((entry.get("line") or "").split()):
            raise SystemExit(f"Selected repo needs a description: {entry['repo']}")

    for entry in flag_entries + entries:
        if entry["repo"] in scanned:
            continue
        needs_detection = bool(entry.get("in_matrix") or entry.get("selected"))
        meta = scan.scan_repo(entry, rules, needs_detection)
        if not meta.get("missing"):
            # A declared value always wins. Disagreements go to the report,
            # never to the page.
            for layer, value in (entry.get("declared") or {}).items():
                found = meta["detected"].get(layer)
                if found and found["label"] != value:
                    conflicts.append(
                        f"{entry['repo']} · {layer}: declared `{value}`, "
                        f"scan found `{found['label']}` in `{found['evidence']}`")
                meta["detected"][layer] = {"label": value, "evidence": None}
            if declared_mode:
                for layer in scan.LAYERS:
                    if layer not in (entry.get("declared") or {}):
                        meta["detected"][layer] = None
        scanned[entry["repo"]] = meta

    for flag in config["flagships"]:
        if flag.get("repo") and scanned[flag["repo"]].get("missing"):
            raise SystemExit(
                f"Flagship scan unavailable: {flag['repo']}. "
                "Set PROFILE_SCAN_TOKEN with access to the private repo.")

    version = version_string(entries, scanned, owner, now)
    changed: list[str] = []

    skills = config.get("skills", [])
    sphere = render_sphere.render(skills, version)
    card = render_card.render(config.get("card", []))
    write(ROOT / "assets" / "sphere.svg", sphere, changed)
    write(ROOT / "assets" / "card.svg", card, changed)
    for number, flag in enumerate(config["flagships"], start=1):
        write(ROOT / "assets" / f"flagship-{flag['key']}.svg",
              render_flagship.render(flag, number), changed)

    matrix_rows = [
        (entry, scanned[entry["repo"]])
        for entry in flag_entries + entries
        if entry.get("in_matrix")
        and not scanned[entry["repo"]].get("missing")
    ]
    # Evidence is intentionally narrow: rows need at least three real or
    # explicitly declared layers to make an end-to-end claim.
    matrix_rows = [row for row in matrix_rows if sum(
        bool(row[1]["detected"].get(layer)) for layer in scan.LAYERS) >= 3]
    # Most recently pushed first, so the table opens on current work.
    matrix_rows.sort(key=lambda row: row[1]["pushed_at"] or now, reverse=True)

    selected_rows = []
    for entry in selected:
        meta = scanned[entry["repo"]]
        if meta.get("missing"):
            raise SystemExit(f"Selected repo scan unavailable: {entry['repo']}")
        if not meta.get("language"):
            raise SystemExit(f"Selected repo needs a detected language: {entry['repo']}")
        meta["age_days"] = ((now - meta["pushed_at"]).days
                            if meta.get("pushed_at") else None)
        slug = render_row.slug(entry["title"])
        row_svg = render_row.render(
            entry["title"], entry["line"], meta,
            set((entry.get("declared") or {}).keys()))
        write(ROOT / "assets" / "rows" / f"{slug}.svg", row_svg, changed)
        selected_rows.append((entry, meta, slug, render_row.alt_text(
            entry["title"], entry["line"], meta)))

    readme = (ROOT / "README.md").read_text()
    readme = render_readme.splice(readme, "HERO", render_readme.hero_block(
        html.escape(render_sphere.alt_text(skills), quote=True),
        html.escape(render_card.alt_text(config.get("card", [])), quote=True)))
    readme = render_readme.splice(readme, "FLAGSHIPS",
                                  render_readme.flagships_block(config["flagships"]))
    readme = render_readme.splice(readme, "SELECTED",
                                  render_readme.selected_block(selected_rows))
    readme = render_readme.splice(readme, "REPOS", render_readme.repos_block(
        config["groups"], scanned, now))
    readme = render_readme.splice(readme, "MATRIX",
                                  render_readme.matrix_block(matrix_rows, now))
    readme = render_readme.splice(readme, "FOOTER",
                                  render_readme.footer_block(
                                      config.get("stack_line", ""),
                                      config.get("links", {})))
    write(ROOT / "README.md", readme, changed)
    write(ROOT / "scan-report.md",
          scan_report(entries, scanned, conflicts, now), changed)

    if check_only and changed:
        print("Rebuild would change: " + ", ".join(changed))
        return 1
    print(f"{version} · sphere {len(sphere.encode()) // 1024} KB · "
          f"card {len(card.encode()) // 1024} KB · "
          f"{len(matrix_rows)} matrix rows")
    print("changed: " + (", ".join(changed) if changed else "nothing"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
