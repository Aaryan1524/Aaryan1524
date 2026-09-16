"""Turn scan results into the marker blocks of README.md.

Only the regions between markers are rewritten, so anything hand-written
outside them survives a nightly rebuild.
"""

from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, timezone
from html import escape

import render_row
from scan import LAYERS

MARKERS = ["HERO", "FOUNDER", "FLAGSHIPS", "REPOS", "MATRIX", "FOOTER"]


def relative(when: datetime | None, now: datetime) -> str:
    if not when:
        return "no pushes"
    days = (now - when).days
    if days <= 0:
        return "updated today"
    if days == 1:
        return "updated yesterday"
    if days < 14:
        return f"updated {days} days ago"
    if days < 60:
        return f"updated {days // 7} weeks ago"
    if days < 365:
        return f"updated {days // 30} months ago"
    years = days // 365
    return f"updated {years} year{'s' if years > 1 else ''} ago"


def _repo_line(entry: dict, meta: dict, now: datetime) -> str:
    title = entry["title"]
    head = title if meta["private"] else f"[{title}]({meta['html_url']})"
    bits = [f"**{head}**"]
    tail = []
    if entry.get("line"):
        tail.append(entry["line"])
    if meta["private"]:
        tail.append("private")
    if meta["language"]:
        tail.append(meta["language"])
    if meta["stars"] > 0:
        tail.append(f"★ {meta['stars']}")
    if meta["archived"]:
        tail.append("archived")
    tail.append(relative(meta["pushed_at"], now))
    return f"{bits[0]} — " + " · ".join(tail)


def repos_block(groups: list[dict], scanned: dict, now: datetime) -> str:
    """Grouped SVG cards for all repositories by category."""
    grouped: list[str] = []
    for group in groups:
        rows = []
        for entry in group["repos"]:
            meta = scanned.get(entry["repo"])
            if not meta or meta.get("missing"):
                continue
            slug = render_row.slug(entry["title"])
            alt = render_row.alt_text(entry["title"], entry.get("line") or "", meta)
            if meta.get("private"):
                tag = (f'<img src="assets/rows/{slug}.svg" '
                       f'width="100%" alt="{escape(alt, quote=True)}"><br>')
            else:
                tag = (f'<a href="{meta["html_url"]}"><img src="assets/rows/{slug}.svg" '
                       f'width="100%" alt="{escape(alt, quote=True)}"></a><br>')
            rows.append(tag)
        if rows:
            grouped.append(f"#### {group['name']}\n\n" +
                           "\n".join(rows))
    return "\n\n".join(grouped)


def _cell(detected: dict | None, meta: dict, declared: bool) -> str:
    if not detected:
        return "—"
    label = detected["label"]
    dagger = " †" if declared else ""
    if meta["private"] or not detected.get("evidence"):
        # Never expose a private repo's paths, and never link into one.
        return f"{label}{dagger}"
    # Paths like app/api/[...nextauth]/route.ts would break a markdown link.
    safe = urllib.parse.quote(detected["evidence"])
    url = f"{meta['html_url']}/blob/{meta['default_branch']}/{safe}"
    return f"[{label}]({url}){dagger}"


def matrix_block(rows: list[tuple[dict, dict]], now: datetime) -> str:
    header = "| Project | " + " | ".join(LAYERS) + " | Idea → shipped |"
    rule = "|---|" + "---|" * (len(LAYERS) + 1)
    lines = [header, rule]
    for entry, meta in rows:
        title = entry["title"]
        name = title if meta["private"] else f"[{title}]({meta['html_url']})"
        cells = []
        for layer in LAYERS:
            declared = layer in (entry.get("declared") or {})
            cells.append(_cell(meta["detected"].get(layer), meta, declared))
        days = meta.get("shipped_days")
        if days is None:
            shipped = "—"
        else:
            shipped = f"{days} day" + ("" if days == 1 else "s")
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {shipped} |")
    stamp = now.strftime("%Y-%m-%d")
    lines.append("")
    note = f"*Cells detected from source on {stamp}."
    if any("†" in line for line in lines):
        note = (f"*Unmarked cells detected from source on {stamp}. "
                "† declared by me.")
    lines.append(note + "*")
    return "\n".join(lines)


def selected_block(rows: list[tuple[dict, dict, str, str]]) -> str:
    """One linked SVG plate per selected repository."""
    return "\n".join(
        f'<a href="{meta["html_url"]}"><img src="assets/rows/{slug}.svg" '
        f'width="100%" alt="{escape(alt, quote=True)}"></a><br>'
        for _entry, meta, slug, alt in rows
    )


def hero_block(sphere_alt: str, card_alt: str, contrib_alt: str = "") -> str:
    parts = [
        f'<img src="assets/sphere.svg" width="100%" alt="{sphere_alt}">',
        f'<img src="assets/card.svg" width="100%" alt="{card_alt}">',
    ]
    if contrib_alt:
        parts.append(f'<img src="assets/contributions.svg" width="100%" alt="{contrib_alt}">')
    return "\n\n".join(parts)


def cards_block(cards: list[dict]) -> str:
    """Editorial SVG cards gallery. Two cards sit side-by-side at 49% width."""
    out = []
    for card in cards:
        facts = ", ".join(f"{label} {value}"
                          for label, value in (card.get("facts") or []))
        alt = escape(f'{card["title"]}: {card["dek"]} {facts}.', quote=True)
        image = (f'<img src="assets/flagship-{card["key"]}.svg" width="49%" '
                 f'alt="{alt}">')
        href = card.get("url") or card.get("poster")
        out.append(f'<a href="{href}">{image}</a>' if href else image)
    return '<p align="center">\n  ' + "\n  ".join(out) + "\n</p>"


flagships_block = cards_block


def footer_block(stack_line: str, links: dict) -> str:
    stack = " ".join((stack_line or "").split())
    parts = []
    if links.get("site"):
        parts.append(f"[{links['site'].split('//')[-1]}]({links['site']})")
    if links.get("x"):
        parts.append(f"[X]({links['x']})")
    if links.get("linkedin"):
        parts.append(f"[LinkedIn]({links['linkedin']})")
    if links.get("email"):
        parts.append(f"[{links['email']}](mailto:{links['email']})")
    return (f"### Set in\n\n{stack}\n\n"
            f"### Correspondence\n\n" + " · ".join(parts) + "\n\n"
            "### Colophon\n\n"
            "*Plates are SVG, rebuilt nightly by GitHub Actions.*")


def splice(readme: str, name: str, body: str) -> str:
    """Replace one marker block, leaving everything around it untouched."""
    pattern = re.compile(
        rf"(<!-- {name}:START -->)(.*?)(<!-- {name}:END -->)", re.S)
    if not pattern.search(readme):
        raise SystemExit(f"README.md is missing the {name} markers.")
    return pattern.sub(lambda m: f"{m.group(1)}\n\n{body}\n\n{m.group(3)}",
                       readme)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
