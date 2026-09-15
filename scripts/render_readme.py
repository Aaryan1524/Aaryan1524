"""Turn scan results into the marker blocks of README.md.

Only the regions between markers are rewritten, so anything hand-written
outside them survives a nightly rebuild.
"""

from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, timezone

from scan import LAYERS

MARKERS = ["HERO", "FLAGSHIPS", "MATRIX", "REPOS", "FOOTER"]


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


def repos_block(groups: list[dict], scanned: dict, archive_days: int,
                now: datetime) -> str:
    live: list[str] = []
    archived: list[str] = []
    for group in groups:
        rows, stale = [], []
        for entry in group["repos"]:
            meta = scanned.get(entry["repo"])
            if not meta or meta.get("missing"):
                continue
            line = _repo_line(entry, meta, now)
            pushed = meta["pushed_at"]
            old = pushed is None or (now - pushed).days > archive_days
            (stale if old or meta["archived"] else rows).append(line)
        if rows:
            live.append(f"##### {group['name']}\n")
            live.append("\n".join(f"- {r}" for r in rows) + "\n")
        if stale:
            archived.append(f"**{group['name']}**\n")
            archived.append("\n".join(f"- {r}" for r in stale) + "\n")

    out = "\n".join(live).rstrip()
    if archived:
        body = "\n".join(archived).rstrip()
        out += ("\n\n<details>\n<summary>Archive — no push in over "
                f"{archive_days} days</summary>\n\n{body}\n\n</details>")
    return out


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


def hero_block(sphere_alt: str, card_alt: str) -> str:
    return (f'<img src="assets/sphere.svg" width="100%" alt="{sphere_alt}">\n\n'
            f'<img src="assets/card.svg" width="100%" alt="{card_alt}">')


def flagships_block(flagships: list[dict], scanned: dict) -> str:
    out = []
    for flag in flagships:
        title = flag["title"]
        meta = scanned.get(flag.get("repo") or "")
        if meta and meta.get("missing"):
            meta = None
        if flag.get("url"):
            head = f"**[{title}]({flag['url']})**"
        elif meta and not meta["private"]:
            head = f"**[{title}]({meta['html_url']})**"
        else:
            head = f"**{title}**"
        note = []
        if flag.get("repo") and (meta is None or meta["private"]):
            note.append("code private")
        elif not flag.get("repo"):
            note.append("research, code private")
        suffix = f" · {' · '.join(note)}" if note else ""
        blurb = " ".join((flag.get("blurb") or "").split())
        out.append(f"{head}{suffix}\n\n{blurb}" if blurb else f"{head}{suffix}")
    return "\n\n".join(out)


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
