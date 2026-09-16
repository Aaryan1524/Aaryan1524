"""Thin GitHub REST client for the profile build.

Reads PROFILE_SCAN_TOKEN (a read-only fine-grained PAT that can see private
repos) and falls back to GITHUB_TOKEN, which in Actions only sees this repo.
Responses are cached in-process so a repo's tree is fetched once per run.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
_cache: dict[str, object] = {}


def token(required: bool = True) -> str:
    for name in ("PROFILE_SCAN_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(name)
        if value:
            return value
    if required:
        sys.exit("No token. Set PROFILE_SCAN_TOKEN (locally: export "
                 "PROFILE_SCAN_TOKEN=$(gh auth token)).")
    return ""


def _request(path: str, accept: str = "application/vnd.github+json"):
    """GET path, returning (payload, headers). None payload means 404."""
    url = path if path.startswith("http") else f"{API}{path}"
    headers = {
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "aaryan1524-profile-build",
    }
    # Public repos remain useful without a local credential. The profile build
    # still fails for a configured private repo, rather than silently omitting
    # its evidence, so scheduled builds must retain PROFILE_SCAN_TOKEN.
    if auth := token(required=False):
        headers["Authorization"] = f"Bearer {auth}"
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode()), dict(resp.headers)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429) and attempt < 3:
                # Secondary rate limit. Back off and try again.
                time.sleep(2 ** attempt * 5)
                continue
            if exc.code in (404, 409, 451):
                return None, {}
            raise
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise
    return None, {}


def get(path: str):
    """Cached GET returning just the payload."""
    if path not in _cache:
        _cache[path] = _request(path)[0]
    return _cache[path]


def last_page_item(path: str):
    """First item chronologically from a paginated, newest-first endpoint.

    GitHub's commit list is newest first, so the oldest commit is the single
    item on the last page. Ask for one per page and follow the Link header.
    """
    joiner = "&" if "?" in path else "?"
    first, headers = _request(f"{path}{joiner}per_page=1")
    if not first:
        return None
    link = headers.get("Link", "")
    last_url = None
    for part in link.split(","):
        if 'rel="last"' in part:
            last_url = part.split(";")[0].strip().strip("<>")
    if not last_url:
        return first[0] if isinstance(first, list) and first else None
    payload, _ = _request(last_url)
    if isinstance(payload, list) and payload:
        return payload[-1]
    return None


def file_text(owner_repo: str, path: str, ref: str) -> str:
    """Decoded file contents, or empty string if absent or binary."""
    quoted = urllib.parse.quote(path)
    payload = get(f"/repos/{owner_repo}/contents/{quoted}?ref={ref}")
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        return ""
    try:
        return base64.b64decode(payload["content"]).decode("utf-8", "replace")
    except Exception:
        return ""


def tree(owner_repo: str, ref: str) -> list[str]:
    """Every file path in the repo at ref, sorted for reproducibility."""
    payload = get(f"/repos/{owner_repo}/git/trees/{urllib.parse.quote(ref)}?recursive=1")
    if not isinstance(payload, dict):
        return []
    return sorted(
        node["path"] for node in payload.get("tree", []) if node.get("type") == "blob"
    )


def graphql(query: str, variables: dict | None = None) -> dict | None:
    """POST query to the GitHub GraphQL API."""
    url = f"{API}/graphql"
    data = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "aaryan1524-profile-build",
        "Content-Type": "application/json",
    }
    if auth := token(required=False):
        headers["Authorization"] = f"Bearer {auth}"
    req = urllib.request.Request(url, data=data, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
    return None

