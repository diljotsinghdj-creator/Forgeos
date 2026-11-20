"""Real recorded sound effects from Freesound (freesound.org), commercially usable licences only.

    fill_bank(folder, key) -> {"added": n, "credits": [...]}    folder gets <role>_fs<id>.mp3 files for media/sfx.py

Only Creative Commons 0 (no attribution needed) and Creative Commons Attribution sounds are taken; Attribution
sounds are credited in the film's description (CREDITS.txt next to them). Non-commercial and Sampling+ licences are
never downloaded. The key is a free Freesound API key in the pod's environment (FREESOUND_KEY or CF_FREESOUND_KEY).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://freesound.org/apiv2/search/text/"
# one search per sound role in media/sfx.py (names start with the role so SfxBank files them)
ROLE_QUERIES = {"whoosh": ["whoosh transition", "paper swoosh"], "hit": ["paper stamp", "soft impact thud"],
                "pop": ["pop click ui", "paper tap"], "riser": ["cinematic riser"], "scribble": ["marker pen writing paper"],
                "projector": ["film projector loop"]}
OK_LICENCES = ("publicdomain/zero", "licenses/by/")          # CC0 and CC-BY (any version); not by-nc, not sampling+
HTTP = None        # tests set a callable(url) -> bytes


def key() -> str:
    return os.environ.get("FREESOUND_KEY") or os.environ.get("CF_FREESOUND_KEY") or ""


def _get(url: str, timeout: int = 30) -> bytes:
    if HTTP is not None:
        return HTTP(url)
    req = urllib.request.Request(url, headers={"User-Agent": "creatorforge-worker"})
    with urllib.request.urlopen(req, timeout=timeout) as r:     # noqa: S310 - freesound.org only
        return r.read()


def licence_ok(lic: str) -> bool:
    lic = (lic or "").lower()
    return any(x in lic for x in OK_LICENCES) and "-nc" not in lic and "sampling" not in lic


def search(query: str, api_key: str, n: int = 6, max_seconds: float = 6.0) -> list[dict]:
    q = {"query": query, "page_size": n, "token": api_key, "sort": "rating_desc",
         "filter": f'duration:[0.1 TO {max_seconds}] license:("Creative Commons 0" OR "Attribution")',
         "fields": "id,name,license,username,previews,duration,url"}
    data = json.loads(_get(API + "?" + urllib.parse.urlencode(q)))
    return [r for r in data.get("results", []) if licence_ok(r.get("license", "")) and (r.get("previews") or {}).get("preview-hq-mp3")]


def fill_bank(folder: Path, api_key: str | None = None, per_role: int = 3) -> dict:
    api_key = api_key or key()
    if not api_key:
        return {"added": 0, "credits": [], "why": "no Freesound key (FREESOUND_KEY) in the pod's environment"}
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    cred_file = folder / "credits.json"
    credits = json.loads(cred_file.read_text(encoding="utf-8")) if cred_file.is_file() else []
    have = {c["file"] for c in credits}
    added = 0
    for role, queries in ROLE_QUERIES.items():
        got = len([f for f in folder.glob(f"{role}_fs*.mp3")])
        for q in queries:
            if got >= per_role:
                break
            try:
                results = search(q, api_key)
            except Exception:  # noqa: BLE001 - one failed search leaves the built-in sounds in place
                continue
            for r in results:
                if got >= per_role:
                    break
                f = folder / f"{role}_fs{r['id']}.mp3"
                if f.name in have:
                    continue
                try:
                    f.write_bytes(_get(r["previews"]["preview-hq-mp3"], timeout=60))
                except Exception:  # noqa: BLE001
                    continue
                credits.append({"file": f.name, "title": r.get("name", ""), "author": r.get("username", ""),
                                "licence": r.get("license", ""), "url": r.get("url", ""),
                                "attribution": "publicdomain/zero" not in r.get("license", "").lower()})
                have.add(f.name)
                got += 1
                added += 1
    cred_file.write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"\"{c['title']}\" by {c['author']} ({c['licence']}) {c['url']}" for c in credits if c["attribution"]]
    (folder / "CREDITS.txt").write_text("Sound effects from freesound.org:\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return {"added": added, "credits": credits}
