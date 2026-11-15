import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
from creatorforge_worker.media import maps
D = Path(__file__).resolve().parent
def merc(lon, lat): return (lon + 180) / 360, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2
def uv(name, lon, lat):
    m = json.loads((D / "maps" / f"{name}_h.json").read_text()); lon0, lat0, lon1, lat1 = m["box"]
    x0, y0 = merc(lon0, lat1); x1, y1 = merc(lon1, lat0); x, y = merc(lon, lat)
    return (x - x0) / (x1 - x0), (y - y0) / (y1 - y0)
def india(name):
    m = json.loads((D / "maps" / f"{name}_h.json").read_text())
    im = Image.new("L", (m["w"], m["h"]), 0); d = ImageDraw.Draw(im)
    rings = maps._find("India")["rings"]          # the studio's official boundary
    for r in rings: d.polygon([(u * m["w"], v * m["h"]) for u, v in (uv(name, lo, la) for lo, la in r)], fill=255)
    im.save(D / "maps" / f"{name}_mask.png")
    return [[uv(name, lo, la) for lo, la in r] for r in rings if len(r) > 3]
if __name__ == "__main__":
    json.dump(india("north"), open(D / "maps" / "north_india_uv.json", "w"))
