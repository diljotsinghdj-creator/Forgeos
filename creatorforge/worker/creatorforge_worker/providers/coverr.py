"""Coverr: free modern b-roll, checked one chosen clip page at a time.

Why not an automatic source:
- coverr.co/robots.txt disallows its search pages (`*?q=*`).
- The API's free (Demo) tier requires a clickable Coverr logo, and its developer page still says free access is for
  non-commercial use. The newer licence page says commercial use is fine on every tier. Until Coverr settles that in
  writing, the studio does not use the API.

The licence page (coverr.co/license, read 2026-11-14) allows stock-library clips downloaded from the site for
commercial use, YouTube included, with no attribution required (we credit anyway). `check()` refuses:
- Premium clips (they need a paid plan; the watermarked preview "isn't licensed for any use");
- AI-generated clips (the people "aren't real"; our channels never show synthetic footage as real).
"""
from __future__ import annotations

import html
import re

import httpx

UA = "CreatorForge-footage-check/1.0"
_PAGE = re.compile(r"^https://coverr\.co/videos/([a-z0-9-]+)/?$")


def check(page_url: str, timeout: float = 30) -> dict:
    """Read one Coverr clip page and judge that clip only (the page also lists related clips)."""
    m = _PAGE.match(page_url.strip())
    if not m:
        return {"allowed": False, "reason": "not a Coverr video page link", "page": page_url}
    slug = m.group(1)
    r = httpx.get(page_url, headers={"User-Agent": UA}, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    at = r.text.find(f'"slug":"{slug}"')
    if at < 0:
        return {"allowed": False, "reason": "this clip's own record was not found on the page", "page": page_url}
    before, after = r.text[max(0, at - 3000):at], r.text[at:at + 2500]     # this clip's record ends at its slug
    last = lambda pat, s: (re.findall(pat, s) or [None])[-1]
    premium, ai = last(r'"isPremium":(true|false)', before), last(r'"isAiGenerated":(true|false)', before)
    title = html.unescape(last(r'"title":"([^"]+)"', before) or "").strip()
    who = (re.search(r'"contributor":\{[^{}]*?"(?:name|displayName|username)":"([^"]+)"', after) or [None, ""])[1]
    base = {"site": "coverr", "id": slug, "page": page_url, "about": title[:300], "creator": who or "Coverr",
            "credit": f"{who + ' / ' if who else ''}Coverr", "trim": True, "duration": 0.0}
    if premium != "false":
        return {**base, "allowed": False, "reason": "Premium clip (paid plan needed) or its status is unclear"}
    if ai != "false":
        return {**base, "allowed": False, "reason": "AI-generated clip, or its status is unclear: never shown as real footage"}
    url = last(r'"mp4":"(https://cdn\.coverr\.co/[^"]+?\.mp4)"', before)
    if not url:
        return {**base, "allowed": False, "reason": "no MP4 found for this clip"}
    w, h = last(r'"maxWidth":(\d+)', before), last(r'"maxHeight":(\d+)', before)
    return {**base, "allowed": True, "url": url, "width": int(w or 1920), "height": int(h or 1080),
            "licence": "Coverr licence (stock library, free commercial use)", "attribution": "not required (credited anyway)"}
