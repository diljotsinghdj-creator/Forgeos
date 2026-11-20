"""Download the photo a person picked from a candidate sheet and file it under the concept's search (cut out too)."""
import json, sys
from pathlib import Path
import httpx
from fetch_assets import cut, slug, A, REC
rec = json.loads(REC.read_text()) if REC.is_file() else {}
D = Path(__file__).resolve().parent
for arg in sys.argv[1:]:
    q, pick = arg.split("=")
    cand, idx = pick.rsplit(":", 1)
    h = json.loads((D / "data" / "cands" / f"{cand}.json").read_text())[int(idx)]
    s = slug(q)
    (A / f"{s}.jpg").write_bytes(httpx.get(h["largeImageURL"], timeout=60).content)
    (A / f"{s}.png").unlink(missing_ok=True)
    ok = cut(A / f"{s}.jpg", A / f"{s}.png")
    rec[s] = {"query": q, "picked_from": f"{cand}#{idx}", "pixabay_id": h["id"], "page": h["pageURL"], "author": h.get("user", ""), "tags": h.get("tags", ""),
              "licence": "Pixabay Content License (free for commercial use, no attribution required)", "cut": ok, "chosen_by_eye": True}
    REC.write_text(json.dumps(rec, indent=1))
    print("ok", q, "<-", cand, idx, h.get("tags", "")[:40])
