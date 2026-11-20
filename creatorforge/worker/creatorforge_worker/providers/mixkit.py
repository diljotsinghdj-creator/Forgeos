"""Mixkit (Envato): free modern b-roll, but only clip by clip, chosen by a person.

Why not an automatic search source like the others: Mixkit's User Terms forbid "scripts or bots to mass download
Items" and use of the site "in any way not expressly permitted". So the studio never searches or crawls Mixkit. The
owner (or Claude, on the owner's request) picks a clip page, and `check()` reads that one page.

Two licences exist and the page says which one applies:
- Stock Video Free License: YouTube, commercial and monetised use allowed, attribution not required (we credit anyway).
- Stock Video Restricted License: personal projects only, "never ... a monetized YouTube video". Refused here.
"""
from __future__ import annotations

import re

import httpx

UA = "CreatorForge-footage-check/1.0"
_PAGE = re.compile(r"^https://mixkit\.co/free-stock-video/[a-z0-9-]+-(\d+)/?$")


def check(page_url: str, timeout: float = 30) -> dict:
    """Read one Mixkit clip page. Returns the clip dict the studio uses, with `allowed` False (and a reason) unless
    the page names the Free licence."""
    m = _PAGE.match(page_url.strip())
    if not m:
        return {"allowed": False, "reason": "not a Mixkit stock-video page link", "page": page_url}
    vid = m.group(1)
    r = httpx.get(page_url, headers={"User-Agent": UA}, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    lic = re.findall(r'data-license="(video\w+)"', r.text)
    title = re.sub(r"\s*-\s*Free Stock Video.*$", "", (re.search(r"<title>(.*?)</title>", r.text, re.S) or [None, ""])[1]).strip()
    base = {"site": "mixkit", "id": vid, "page": page_url, "about": title[:300], "creator": "Mixkit",
            "credit": "Mixkit", "trim": True, "duration": 0.0}
    if not lic:
        return {**base, "allowed": False, "reason": "the page names no licence; not used"}
    if lic[0] != "videoFree":
        return {**base, "allowed": False, "licence": "Mixkit Stock Video Restricted License",
                "reason": "Restricted licence: personal projects only, monetised YouTube not allowed"}
    return {**base, "allowed": True, "licence": "Mixkit Stock Video Free License",
            "attribution": "not required (credited anyway)",
            # 1080 is the master (~30-45 MB); 720 is a light copy for previews
            "url": f"https://assets.mixkit.co/videos/{vid}/{vid}-1080.mp4", "width": 1920, "height": 1080,
            "preview": f"https://assets.mixkit.co/videos/{vid}/{vid}-720.mp4"}
