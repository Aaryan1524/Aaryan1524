#!/usr/bin/env python3
"""Fail the build if any link in README.md 404s.

Catches the two mistakes that are easy to make by hand: a repo that was
renamed, and an evidence path built against the wrong default branch.
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import ghapi

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")


# LinkedIn returns 999 to anything that is not a browser. It is not a 404.
TOLERATED = {999, 403, 405, 429}


def _try(url: str, method: str) -> int:
    request = urllib.request.Request(url, method=method, headers={
        "User-Agent": "aaryan1524-profile-build",
    })
    auth = ghapi.token(required=False)
    if auth and url.startswith("https://github.com/"):
        request.add_header("Authorization", f"Bearer {auth}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0


def status(url: str) -> int:
    code = _try(url, "HEAD")
    if code == 0 or code >= 400:
        # Some hosts refuse HEAD but serve GET perfectly well.
        code = _try(url, "GET") or code
    return code


def main() -> int:
    urls = sorted(set(LINK.findall((ROOT / "README.md").read_text())))
    bad = []
    for url in urls:
        code = status(url)
        if code >= 400 or code == 0:
            if code in TOLERATED:
                print(f"{code:>4}  {url}  (bot-blocked, not treated as broken)")
                continue
            bad.append((url, code))
        print(f"{code or 'ERR':>4}  {url}")
    if bad:
        print(f"\n{len(bad)} broken link(s):", file=sys.stderr)
        for url, code in bad:
            print(f"  {code} {url}", file=sys.stderr)
        return 1
    print(f"\n{len(urls)} links, all resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
