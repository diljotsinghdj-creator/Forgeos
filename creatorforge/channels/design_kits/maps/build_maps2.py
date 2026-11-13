"""Two more map styles from the owner's round-6 references: a satellite route (Sentinel-2 cloudless, EOX, CC BY 4.0)
and an extruded 3D region map with city tags. Both free; tiles cached under tiles/."""
import json, math, urllib.request
from pathlib import Path
D = Path(__file__).resolve().parent; T = D / "tiles"; T.mkdir(exist_ok=True)
M = Path("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media")
F = M / "vendor" / "fonts"
FONTS = "".join(f"@font-face{{font-family:{n};src:url({(F / f).as_uri()})}}" for n, f in [
    ("Inter", "inter-latin-800-normal.woff2"), ("Oswald", "oswald-latin-600-normal.woff2"), ("Mono", "jetbrains-mono-latin-700-normal.woff2")])
def tile_xy(lon, lat, z):
    n = 2 ** z; return (lon + 180) / 360 * n, (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
def tile(z, x, y):
    f = T / f"s2_{z}_{x}_{y}.jpg"
    if not f.is_file():
        url = f"https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg"
        f.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "CreatorForge/1.0"}), timeout=60).read())
    return f
# A. Panama Canal route on Sentinel-2 imagery (approximate route through the locks and Gatun Lake)
z = 11
route = [(-79.915, 9.385), (-79.92, 9.27), (-79.86, 9.19), (-79.80, 9.14), (-79.70, 9.115), (-79.655, 9.06), (-79.605, 9.02), (-79.59, 8.995), (-79.565, 8.955), (-79.54, 8.89)]
cx, cy = tile_xy(-79.73, 9.14, z)
ox, oy = cx - 960 / 256, cy - 540 / 256
imgs = ""
for tx in range(int(ox) - 1, int(ox + 1920 / 256) + 2):
    for ty in range(int(oy) - 1, int(oy + 1080 / 256) + 2):
        f = tile(z, tx, ty)
        imgs += f"<img src='{f.as_uri()}' style='position:absolute;left:{(tx - ox) * 256:.0f}px;top:{(ty - oy) * 256:.0f}px;width:256px;height:256px'>"
def px(lon, lat):
    x, y = tile_xy(lon, lat, z); return (x - ox) * 256, (y - oy) * 256
pts = [px(*p) for p in route]
d = "M" + " L".join(f"{a:.0f} {b:.0f}" for a, b in pts)
(ax, ay), (bx, by) = pts[0], pts[-1]
A = (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTS}body{{margin:0;width:1920px;height:1080px;overflow:hidden;position:relative;background:#000}}"
     f".abs{{position:absolute}}.pin{{font:22px Inter;letter-spacing:3px;color:#fff;text-shadow:0 2px 6px rgba(0,0,0,.8)}}</style></head><body>"
     f"<div class='abs' style='inset:0;filter:saturate(.85) contrast(1.08) brightness(.82)'>{imgs}</div>"
     f"<svg class='abs' style='inset:0' width='1920' height='1080'><defs><filter id='gw'><feGaussianBlur stdDeviation='6'/></filter></defs>"
     f"<path d='{d}' stroke='#FFB347' stroke-width='14' fill='none' filter='url(#gw)' opacity='.8'/><path d='{d}' stroke='#FFC86B' stroke-width='6' fill='none' stroke-linecap='round' stroke-linejoin='round'/>"
     f"<circle cx='{ax:.0f}' cy='{ay:.0f}' r='14' fill='#E8551E' stroke='#fff' stroke-width='5'/><circle cx='{bx:.0f}' cy='{by:.0f}' r='14' fill='#fff' stroke='#111' stroke-width='5'/></svg>"
     f"<div class='abs pin' style='left:{ax + 26:.0f}px;top:{ay - 14:.0f}px'>COLÓN · CARIBBEAN</div>"
     f"<div class='abs pin' style='left:{bx + 26:.0f}px;top:{by - 14:.0f}px'>BALBOA · PACIFIC</div>"
     "<div class='abs' style='left:70px;top:60px;font:64px Oswald;color:#fff;letter-spacing:3px;text-shadow:0 3px 10px rgba(0,0,0,.7)'>THE PANAMA CANAL</div>"
     "<div class='abs' style='left:72px;top:150px;background:#FFC86B;color:#111;font:24px Inter;letter-spacing:3px;padding:10px 16px'>ABOUT 80 KM · OCEAN TO OCEAN</div>"
     "<div class='abs' style='right:28px;bottom:16px;font:13px Inter;color:#ddd;letter-spacing:1px'>SENTINEL-2 CLOUDLESS 2016 BY EOX (CC BY 4.0), CONTAINS MODIFIED COPERNICUS SENTINEL DATA · ROUTE APPROXIMATE</div>"
     "</body></html>")
(D / "09_satellite_route_panama.html").write_text(A, encoding="utf-8")
# B. Extruded 3D region map: Australia's states and territories as thick white slabs, orange city tags
ST = json.load(open(M / "states.json"))["Australia"]
def rings(g):
    while isinstance(g, list) and g and isinstance(g[0], list) and isinstance(g[0][0], list) and isinstance(g[0][0][0], list):
        g = [r for p in g for r in p]
    return g
def mer(lon, lat): return lon, math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
xs = [mer(*p)[0] for s in ST for r in rings(s["r"]) for p in r]; ys = [mer(*p)[1] for s in ST for r in rings(s["r"]) for p in r]
W, H = 1180, 930; k = min(W / (max(xs) - min(xs)), H / (max(ys) - min(ys)))
def xy(lon, lat):
    x, y = mer(lon, lat); return (x - min(xs)) * k, (max(ys) - y) * k
def dd(rs): return " ".join("M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in (xy(*p) for p in r)) + "Z" for r in rings(rs) if len(r) > 2)
paths = "".join(f"<path d='{dd(s['r'])}'/>" for s in ST)
layers = "".join(f"<svg class='abs' style='left:0;top:0;transform:translateZ({-i * 6}px)' width='{W}' height='{H}'><g fill='{'#FFFFFF' if i == 0 else '#B9CCE0'}' stroke='{'#9DB5CF' if i == 0 else 'none'}' stroke-width='2'>{paths}</g></svg>" for i in range(14, -1, -1))
cities = [("SYDNEY", 151.21, -33.87), ("MELBOURNE", 144.96, -37.81), ("BRISBANE", 153.03, -27.47), ("PERTH", 115.86, -31.95), ("ADELAIDE", 138.6, -34.93), ("DARWIN", 130.84, -12.46), ("HOBART", 147.33, -42.88), ("ALICE SPRINGS", 133.88, -23.7)]
tags = "".join(f"<div class='abs' style='left:{xy(lo, la)[0]:.0f}px;top:{xy(lo, la)[1]:.0f}px;transform:translateZ(30px) rotateX(-52deg) translate(-50%,-110%)'>"
               f"<div style='background:#F28C28;color:#fff;font:22px Inter;letter-spacing:2px;padding:8px 14px;border-radius:6px;white-space:nowrap;box-shadow:0 6px 14px rgba(0,0,0,.25)'>{n}</div></div>"
               f"<div class='abs' style='left:{xy(lo, la)[0] - 8:.0f}px;top:{xy(lo, la)[1] - 8:.0f}px;width:16px;height:16px;border-radius:50%;background:#F28C28;transform:translateZ(2px)'></div>" for n, lo, la in cities)
B = (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTS}body{{margin:0;width:1920px;height:1080px;overflow:hidden;position:relative;"
     f"background:radial-gradient(circle at 50% 40%,#E6EEF6,#B9C9DA)}}.abs{{position:absolute}}</style></head><body>"
     f"<div class='abs' style='inset:0;perspective:1800px;perspective-origin:50% 0%'><div class='abs' style='left:400px;top:70px;width:{W}px;height:{H}px;transform-style:preserve-3d;transform:rotateX(52deg) rotateZ(-8deg)'>"
     f"<div class='abs' style='left:30px;top:60px;width:{W}px;height:{H}px;transform:translateZ(-60px);filter:blur(30px);background:radial-gradient(ellipse,rgba(40,70,110,.35),transparent 65%)'></div>"
     f"{layers}{tags}</div></div>"
     "<div class='abs' style='left:70px;top:60px;font:60px Oswald;color:#1D3557;letter-spacing:3px'>AUSTRALIA · STATES</div>"
     "<div class='abs' style='left:72px;top:138px;font:22px Mono;color:#4B6584'>extruded 3D map · glide camera · city tags</div>"
     "<div class='abs' style='right:28px;bottom:16px;font:13px Inter;color:#4B6584;letter-spacing:1px'>MAP: NATURAL EARTH (PUBLIC DOMAIN)</div></body></html>")
(D / "10_extruded_3d_australia.html").write_text(B, encoding="utf-8")
print("ok")
