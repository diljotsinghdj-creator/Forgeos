"""Vox year-in-review techniques (owner's reference, 2026-11-14) applied to The Machine, as stills.
Headline card (exact headline, credited), pink country on a black world with an RGB-split edge, minimal chart on black."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, "/home/user/Forgeos/creatorforge/channels/design_kits/collage")
import collage2 as K
from collage2 import el, STILL
D = Path(__file__).resolve().parent; C = D.parent
PINK = "#F23CA6"
S = {}
# 1. headline card: outlet + exact headline with the key phrase on a pink marker, byline and date, over a dark blurred ground
ground = (C / "drawn" / "kraft_ground.jpg").as_uri()
body = el(f'<div style="width:1920px;height:1080px;background:url({ground}) center/cover;filter:blur(40px) brightness(.2) saturate(.4)"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
body += el('<div style="font:800 30px Inter;letter-spacing:4px;color:#cfcfcf">THEPRINT</div>', 300, 330, .1, "wipe", z=5)
hl = f'<span style="background:{PINK};padding:0 10px">replaced Amit Malviya</span>'
body += el(f'<div style="width:1320px;font:400 78px/1.15 Serif;color:#fff">Why BJP has {hl} as party&#8217;s IT cell chief</div>', 300, 390, .3, "slide", z=5)
body += el('<div style="font:600 26px Inter;color:#a9a9a9">Neelam Pandey | 17 August 2026</div>', 304, 640, .8, "wipe", z=5)
S["v1_headline"] = (body, "background:#111", "HEADLINE AS PUBLISHED BY THEPRINT, 17 AUG 2026 · BACKGROUND: OUR PAINTED GROUND, BLURRED")
# 2. the map: India (official boundary) in pink on a black world, RGB-split edge
W = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
IN = json.load(open(C / "assets" / "india-composite.geojson"))
lon0, lon1, lat0, lat1 = 55.0, 105.0, 0.0, 40.0
k = math.cos(math.radians(20)); s = 1920 / ((lon1 - lon0) * k)
P = lambda lo, la: ((lo - lon0) * k * s, (lat1 - la) * s - 40)
def path(rings, step=1):
    return "".join("M" + " L".join(f"{P(a, b)[0]:.0f} {P(a, b)[1]:.0f}" for a, b in r[::step]) + "Z" for r in rings if len(r) > 3)
world = "".join(path(c["r"]) for c in W["countries"] if c["n"] != "India")
india = "".join(path([poly[0]], max(1, len(poly[0]) // 1500)) for poly in IN["features"][0]["geometry"]["coordinates"] if len(poly[0]) > 60)
svgmap = (f'<svg width="1920" height="1080"><path d="{world}" fill="#2A2A2A" stroke="#3a3a3a" stroke-width="1.5"/>'
          f'<g style="filter:drop-shadow(-5px 0 0 rgba(255,40,60,.85)) drop-shadow(5px 0 0 rgba(40,120,255,.85))"><path d="{india}" fill="{PINK}"/></g></svg>')
body = el(svgmap, 0, 0, 0, "pop", extra=STILL, z=2)
kx, ky = P(75.86, 25.18)
body += el('<div style="font:400 44px Serif;letter-spacing:6px;color:#fff;text-shadow:0 2px 8px #000">INDIA</div>', 880, 700, .3, "pop", z=5)
body += f'<div class="el" style="left:{kx - 9:.0f}px;top:{ky - 9:.0f}px;width:18px;height:18px;border-radius:50%;background:#fff;z-index:6"></div>'
body += el('<div style="font:600 22px Inter;letter-spacing:3px;color:#fff">KOTA · SEPT 2018</div>', kx + 18, ky - 14, .6, "wipe", z=6)
S["v2_map"] = (body, "background:#0B0B0B", "MAP: INDIA BOUNDARY BY DATAMEET (CC BY 4.0), OFFICIAL BOUNDARY; OTHER COUNTRIES: NATURAL EARTH · LOCATION APPROXIMATE")
# 3. minimal chart on black: where the ad money went (the BJP's own report)
bars = [("Media advertising, total", 611.50), ("Google India", 156.95), ("Facebook", 24.63)]
body = el(f'<div style="font:400 54px Serif;color:#fff">Where the <span style="background:{PINK};padding:0 8px">ad money</span> went</div>', 240, 150, .1, "slide", z=5)
body += el('<div style="font:600 22px Inter;color:#8d8d8d">BJP expenditure report to the Election Commission, 2024 Lok Sabha · ₹ crore</div>', 244, 240, .4, "wipe", z=5)
for i, (lab, v) in enumerate(bars):
    w = int(v / 611.5 * 1180); y = 380 + i * 190
    body += el(f'<div style="font:600 26px Inter;color:#cfcfcf">{lab}</div>', 240, y - 46, .5 + i * .3, "wipe", z=5)
    body += el(f'<div style="width:{w}px;height:76px;background:{PINK if i == 0 else "#d9d9d9"}"></div>', 240, y, .6 + i * .3, "wipe", z=5, extra='data-d=".8"')
    body += el(f'<div style="font:700 44px Inter;color:#fff">₹{v:,.2f}</div>', 270 + w, y + 10, 1.2 + i * .3, "pop", z=5)
S["v3_chart"] = (body, "background:#0B0B0B", "SOURCE: BJP EXPENDITURE REPORT TO THE ECI, VIA PTI / SCROLL (31 JAN 2025)")
if __name__ == "__main__":
    (D / "html").mkdir(exist_ok=True)
    for k2, (body, bg, cr) in S.items():
        (D / "html" / f"{k2}.html").write_text(K.page(body, bg, 4, .03, cr), encoding="utf-8")
    print(len(S))
