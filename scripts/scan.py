"""Read each listed repo and work out what it actually proves.

Nothing here is self-reported. Every table cell comes back with the path of the
file that demonstrates it, so the README can link to the evidence.
"""

from __future__ import annotations

import fnmatch
import urllib.parse
from datetime import datetime, timezone

import ghapi

LAYERS = ["Interface", "API", "Data", "AI", "Deploy"]

# Vendored trees. Some repos have a virtualenv or node_modules committed, and
# a manifest in there proves nothing about what the author wrote.
VENDORED = (
    ".venv/", "venv/", "env/", "node_modules/", "vendor/", "site-packages/",
    "dist/", "build/", ".next/", "__pycache__/", "Pods/", "target/",
    "xcuserdata/", ".idea/", "Carthage/",
)


def _vendored(path: str) -> bool:
    return any(part in path for part in VENDORED)


def _iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _match(paths: list[str], pattern: str) -> str | None:
    """First path matching the glob. Bare names also match at the root."""
    for path in paths:
        if fnmatch.fnmatch(path, pattern):
            return path
        if "/" not in pattern and fnmatch.fnmatch(path.rsplit("/", 1)[-1], pattern):
            return path
    return None


def repo_meta(owner_repo: str) -> dict | None:
    payload = ghapi.get(f"/repos/{owner_repo}")
    if not isinstance(payload, dict) or "full_name" not in payload:
        return None
    language = payload.get("language")
    return {
        "full_name": payload["full_name"],
        "private": bool(payload.get("private")),
        "archived": bool(payload.get("archived")),
        "language": language,
        "stars": payload.get("stargazers_count", 0),
        "pushed_at": _iso(payload.get("pushed_at")),
        "created_at": _iso(payload.get("created_at")),
        "default_branch": payload.get("default_branch") or "main",
        "description": payload.get("description") or "",
        "topics": sorted(payload.get("topics") or []),
        "html_url": payload.get("html_url", ""),
        "has_readme": None,  # filled by scan_repo once the tree is known
    }


def manifests(owner_repo: str, paths: list[str], ref: str, rules: dict) -> dict[str, str]:
    """Contents of every dependency manifest in the repo, keyed by path."""
    wanted = set(rules.get("manifests", []))
    found = {}
    for path in paths:
        name = path.rsplit("/", 1)[-1]
        if name in wanted:
            text = ghapi.file_text(owner_repo, path, ref)
            if text:
                found[path] = text
    return found


def detect(paths: list[str], manifest_text: dict[str, str], rules: dict) -> dict:
    """Run the layer rules. Returns {layer: {"label", "evidence"}}."""
    result: dict[str, dict | None] = {}
    for layer in LAYERS:
        result[layer] = None
        for rule in rules["layers"].get(layer, []):
            token = rule.get("manifest")
            if token:
                for path in sorted(manifest_text):
                    if token.lower() in manifest_text[path].lower():
                        result[layer] = {"label": rule["label"], "evidence": path}
                        break
            elif rule.get("path"):
                hit = _match(paths, rule["path"])
                if hit:
                    needed = rule.get("requires_any")
                    if needed and not any(_match(paths, p) for p in needed):
                        continue
                    result[layer] = {"label": rule["label"], "evidence": hit}
            if result[layer]:
                break
    return result


def deploy_paths(paths: list[str], rules: dict) -> list[str]:
    """Real paths in the repo that count as deploy evidence, at any depth."""
    names = rules.get("deploy_evidence", [])
    hits = set()
    for path in paths:
        for name in names:
            if path == name or path.endswith("/" + name) or path.startswith(name + "/"):
                hits.add(path)
    return sorted(hits)


def shipped_days(owner_repo: str, rules: dict, created: datetime | None,
                 paths: list[str]) -> int | None:
    """Days from first commit to the first sign the thing was deployed.

    End is the earlier of the first commit that added a deploy file and the
    first release. Never hand-picked, never filtered.
    """
    first = ghapi.last_page_item(f"/repos/{owner_repo}/commits")
    start = None
    if first:
        start = _iso(first.get("commit", {}).get("author", {}).get("date"))
    start = start or created
    if not start:
        return None

    ends: list[datetime] = []
    for path in deploy_paths(paths, rules):
        quoted = urllib.parse.quote(path)
        commit = ghapi.last_page_item(f"/repos/{owner_repo}/commits?path={quoted}")
        if commit:
            when = _iso(commit.get("commit", {}).get("author", {}).get("date"))
            if when:
                ends.append(when)
    releases = ghapi.get(f"/repos/{owner_repo}/releases?per_page=100")
    if isinstance(releases, list):
        for release in releases:
            when = _iso(release.get("published_at"))
            if when:
                ends.append(when)
    if not ends:
        return None
    return max(0, (min(ends) - start).days)


def scan_repo(entry: dict, rules: dict, want_matrix: bool) -> dict:
    """Everything the renderer needs about one repo."""
    owner_repo = entry["repo"]
    meta = repo_meta(owner_repo)
    if meta is None:
        return {"repo": owner_repo, "missing": True}

    paths = [p for p in ghapi.tree(owner_repo, meta["default_branch"])
             if not _vendored(p)]
    meta["has_readme"] = any(
        p.lower().startswith("readme") for p in paths if "/" not in p
    )
    meta["missing"] = False

    if want_matrix:
        text = manifests(owner_repo, paths, meta["default_branch"], rules)
        meta["detected"] = detect(paths, text, rules)
        meta["shipped_days"] = shipped_days(
            owner_repo, rules, meta["created_at"], paths)
    else:
        meta["detected"] = {layer: None for layer in LAYERS}
        meta["shipped_days"] = None
    return meta


def commits_this_year(owner: str) -> int:
    """Authored commits in the current calendar year, for the PATCH number."""
    year = datetime.now(timezone.utc).year
    query = f"author:{owner}+author-date:>={year}-01-01"
    payload = ghapi.get(f"/search/commits?q={query}&per_page=1")
    if isinstance(payload, dict):
        return int(payload.get("total_count", 0))
    return 0
