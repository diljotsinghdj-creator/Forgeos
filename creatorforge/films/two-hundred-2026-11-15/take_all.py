"""Download every photo picked by eye (picks.txt: query=candidate-file:index) and cut out the ones that need it."""
import json, re
from pathlib import Path
import httpx
from concepts import C
from fetch_assets import cut, A, REC
D = Path(__file__).resolve().parent
A.mkdir(exist_ok=True)
rec = json.loads(REC.read_text()) if REC.is_file() else {}
CUT = {"subject", "second", "hand", "tiny", "facade"}
need_cut = set()
for c in C:
    for r, q in c[5].items():
        if r in CUT and isinstance(q, str):
            need_cut.add(q)
slug = lambda q: re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:48]
for line in open(D / "picks.txt"):
    if "=" not in line:
        continue
    q, pick = line.strip().split("=", 1)
    s = slug(q)
    if s in rec and (A / f"{s}.jpg").is_file() and (q not in need_cut or (A / f"{s}.png").is_file()):
        continue
    cand, idx = pick.rsplit(":", 1)
    h = json.loads((D / "data" / "cands" / f"{cand}.json").read_text())[int(idx)]
    (A / f"{s}.jpg").write_bytes(httpx.get(h["largeImageURL"], timeout=90).content)
    ok = None
    if q in need_cut:
        (A / f"{s}.png").unlink(missing_ok=True)
        ok = cut(A / f"{s}.jpg", A / f"{s}.png")
    rec[s] = {"query": q, "picked_from": f"{cand}#{idx}", "pixabay_id": h["id"], "page": h["pageURL"], "author": h.get("user", ""), "tags": h.get("tags", "")[:120],
              "licence": "Pixabay Content License (free for commercial use, no attribution required)", "cut": ok, "chosen_by_eye": True}
    REC.write_text(json.dumps(rec, indent=1))
    print("ok", q, "| cut" if ok else ("| CUT FAILED" if ok is False else ""), flush=True)
