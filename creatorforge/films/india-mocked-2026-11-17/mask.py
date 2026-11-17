"""Country mask on the heightmap grid (Natural Earth outlines from the studio's world.json), and lon/lat -> uv."""
import json, math
from pathlib import Path
from PIL import Image, ImageDraw
D = Path(__file__).resolve().parent
W = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
def merc(lon, lat):
    return (lon + 180) / 360, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2
def uv(name, lon, lat):
    m = json.loads((D / "maps" / f"{name}_h.json").read_text())
    lon0, lat0, lon1, lat1 = m["box"]
    x0, y0 = merc(lon0, lat1); x1, y1 = merc(lon1, lat0); x, y = merc(lon, lat)
    return (x - x0) / (x1 - x0), (y - y0) / (y1 - y0)
def mask(name, country):
    m = json.loads((D / "maps" / f"{name}_h.json").read_text())
    im = Image.new("L", (m["w"], m["h"]), 0); d = ImageDraw.Draw(im)
    for cc in W["countries"]:
        if cc["n"] != country:
            continue
        rings = cc["r"] if isinstance(cc["r"], list) else json.loads(cc["r"])
        for r in rings:
            d.polygon([(u * m["w"], v * m["h"]) for u, v in (uv(name, lo, la) for lo, la in r)], fill=255)
    im.save(D / "maps" / f"{name}_mask.png")
if __name__ == "__main__":
    mask("alps", "Switzerland")
    Image.new("L", (10, 10), 255).save(D / "maps" / "canyon_mask.png")
