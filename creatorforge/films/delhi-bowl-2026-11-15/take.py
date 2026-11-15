import json, sys
from pathlib import Path
import httpx
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
D = Path(__file__).resolve().parent; A = D / "assets"; A.mkdir(exist_ok=True)
REC = D / "data" / "assets.json"; rec = json.loads(REC.read_text()) if REC.is_file() else {}
def cut(src, out):
    from PIL import Image
    from creatorforge_worker.media import cutouts
    rgb = Image.open(src).convert("RGB"); rgb.thumbnail((1600, 1600))
    m = cutouts._mask(rgb, None, False); b = m.point(lambda v: 255 if v > 128 else 0).getbbox()
    rgba = rgb.copy(); rgba.putalpha(m); rgba.crop(b).save(out); return True
for arg in sys.argv[1:]:
    name, rest = arg.split("="); cand, idx = rest.rsplit(":", 1); docut = name.endswith("+")
    name = name.rstrip("+")
    h = json.loads((D / "data" / "cands" / f"{cand}.json").read_text())[int(idx)]
    (A / f"{name}.jpg").write_bytes(httpx.get(h["largeImageURL"], timeout=90).content)
    ok = cut(A / f"{name}.jpg", A / f"{name}.png") if docut else None
    rec[name] = {"pixabay_id": h["id"], "page": h["pageURL"], "author": h.get("user", ""), "tags": h["tags"][:120], "licence": "Pixabay Content License", "cut": ok}
    REC.write_text(json.dumps(rec, indent=1)); print("ok", name)
