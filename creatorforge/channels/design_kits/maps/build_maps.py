"""Eight map styles over different regions, drawn from Natural Earth (public domain) in plain SVG/HTML.
Approval stills for the map kit; every element can carry data-in/data-at like the film kits."""
import json, math
from pathlib import Path
D = Path(__file__).resolve().parent
M = Path("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media")
W = json.load(open(M / "world.json")); C = {c["n"]: c["r"] for c in W["countries"]}
ST = json.load(open(M / "states.json"))
F = M / "vendor" / "fonts"
FONTS = "".join(f"@font-face{{font-family:{n};src:url({(F / f).as_uri()})}}" for n, f in [
    ("Playfair", "playfair-display-latin-900-normal.woff2"), ("Inter", "inter-latin-800-normal.woff2"),
    ("Mono", "jetbrains-mono-latin-700-normal.woff2"), ("Anton", "anton-latin-400-normal.woff2"),
    ("Marker", "permanent-marker-latin-400-normal.woff2"), ("Caveat", "caveat-latin-700-normal.woff2"),
    ("Oswald", "oswald-latin-600-normal.woff2"), ("DMSerif", "dm-serif-display-latin-400-normal.woff2")])
def rings(g):
    while isinstance(g, list) and g and isinstance(g[0], list) and isinstance(g[0][0], list) and isinstance(g[0][0][0], list):
        g = [r for p in g for r in p]
    return g
def merc(lon, lat): return math.radians(lon), math.log(math.tan(math.pi / 4 + math.radians(max(-85, min(85, lat))) / 2))
class Frame:
    """Fit a lon/lat box into a pixel box with a projection."""
    def __init__(s, box, px, proj=merc):
        s.proj = proj; (a, b), (c, d) = proj(box[0], box[1]), proj(box[2], box[3])
        s.x0, s.x1, s.y0, s.y1 = min(a, c), max(a, c), min(b, d), max(b, d)
        s.px = px; s.k = min((px[2]) / (s.x1 - s.x0), (px[3]) / (s.y1 - s.y0))
    def xy(s, lon, lat):
        x, y = s.proj(lon, lat); return s.px[0] + (x - s.x0) * s.k, s.px[1] + (s.y1 - y) * s.k
    def d(s, rs):
        out = []
        for r in rings(rs):
            if len(r) < 3: continue
            q = [s.xy(*p) for p in r]
            if any(abs(q[i][0] - q[i - 1][0]) > 900 for i in range(1, len(q))): continue   # skip dateline wraps
            out.append("M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in q) + "Z")
        return " ".join(out)
def page(body, bg, extra_css=""):
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTS}body{{margin:0;width:1920px;height:1080px;overflow:hidden;"
            f"background:{bg};position:relative;font-family:Inter}}.abs{{position:absolute}}{extra_css}</style></head><body>{body}"
            "<svg class='abs' style='inset:0;pointer-events:none;opacity:.5' width='1920' height='1080'><filter id='g'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3'/>"
            "<feColorMatrix values='0 0 0 0 .3  0 0 0 0 .27  0 0 0 0 .22  0 0 0 .3 0'/></filter><rect width='1920' height='1080' filter='url(#g)'/></svg></body></html>")
def cities(names):
    P = {p[0]: (p[2], p[1]) for p in W["places"]}
    return [(n, P[n]) for n in names if n in P]
def arc(f, a, b, lift=.22):
    (x1, y1), (x2, y2) = f.xy(*a), f.xy(*b); mx, my = (x1 + x2) / 2, (y1 + y2) / 2; L = math.hypot(x2 - x1, y2 - y1)
    return f"M{x1:.0f} {y1:.0f} Q{mx:.0f} {my - L * lift:.0f} {x2:.0f} {y2:.0f}", (x1, y1), (x2, y2)
out = {}
# 1 EUROPE / AFRICA / ASIA: antique paper chart on a table, a dashed sea route with a ship, compass, tilted camera
f = Frame((-25, 62, 90, -40), (60, 60, 1700, 860))
land = "".join(f"<path d='{f.d(r)}' fill='#D9C59A' stroke='#7A6440' stroke-width='1.3'/>" for n, r in C.items())
route = [(-9.1, 38.7), (-17, 14), (-10, -5), (12, -30), (20, -35.5), (40, -25), (52, -5), (62, 8), (75.8, 11.3)]
rp = "M" + " L".join(f"{f.xy(*p)[0]:.0f} {f.xy(*p)[1]:.0f}" for p in route)
grid = "".join(f"<path d='M{x} 0 V1000' stroke='#7A6440' stroke-width='.7' opacity='.35'/>" for x in range(40, 1800, 110))
out["01_antique_table_europe_africa"] = page(
    f"<div class='abs' style='inset:0;perspective:1600px;perspective-origin:50% 20%'><div class='abs' style='left:110px;top:60px;width:1700px;height:980px;"
    f"transform:rotateX(38deg) rotateZ(-3deg);background:#EBDDB8;box-shadow:0 70px 90px rgba(0,0,0,.45);border:14px solid #6B5332'>"
    f"<svg width='1700' height='980'><rect width='1700' height='980' fill='#C9D5CB'/>{grid}{land}<path d='{rp}' stroke='#8B1E1E' stroke-width='5' fill='none' stroke-dasharray='16 12'/>"
    f"<circle cx='1500' cy='820' r='70' fill='none' stroke='#7A6440' stroke-width='3'/><path d='M1500 740 L1515 820 L1500 900 L1485 820 Z' fill='#7A6440'/></svg></div></div>"
    "<div class='abs' style='left:70px;top:40px;font:58px DMSerif;color:#F1E6CC;text-shadow:0 2px 8px rgba(0,0,0,.6)'>Lisbon to Calicut</div>"
    "<div class='abs' style='left:74px;top:120px;font:26px Caveat;color:#F1E6CC'>antique chart on a table · ship route · compass</div>", "#3B2A1C")
# 2 EAST ASIA: dark satellite war map, glowing province borders, red territory, triangle marker, dashed ring, leader line
f = Frame((97, 45, 125, 18), (180, 40, 1560, 1000))
chn = ST.get("China", [])
prov = "".join(f"<path d='{f.d(s['r'])}' fill='#0F2A22' stroke='#4FE3B0' stroke-width='1.2' opacity='.95'/>" for s in chn)
hl = next((s for s in chn if s["n"].lower().startswith("jiangxi")), None)
hld = f.d(hl["r"]) if hl else ""
_jp = [p for r in rings(hl["r"]) for p in r] if hl else [(116, 27.5)]
jx, jy = f.xy(sum(p[0] for p in _jp) / len(_jp), sum(p[1] for p in _jp) / len(_jp))
nb = "".join(f"<path d='{f.d(r)}' fill='#0B1F19' stroke='#2A6B55' stroke-width='1'/>" for n, r in C.items() if n != "China")
out["02_war_map_east_asia"] = page(
    f"<svg class='abs' style='inset:0' width='1920' height='1080'><defs><filter id='gl'><feGaussianBlur stdDeviation='5'/></filter></defs>"
    f"<rect width='1920' height='1080' fill='#06120E'/>{nb}{prov}<path d='{hld}' fill='#E0301E' opacity='.85'/><path d='{hld}' fill='none' stroke='#FF6A4D' stroke-width='6' filter='url(#gl)'/>"
    f"<circle cx='{jx:.0f}' cy='{jy:.0f}' r='190' fill='none' stroke='#E9F5EF' stroke-width='4' stroke-dasharray='18 14'/>"
    f"<path d='M{jx:.0f} {jy - 34:.0f} L{jx + 32:.0f} {jy + 24:.0f} L{jx - 32:.0f} {jy + 24:.0f} Z' fill='#E0301E' stroke='#fff' stroke-width='3'/><path d='M{jx + 40:.0f} {jy:.0f} L{jx + 260:.0f} {jy - 120:.0f} H{jx + 420:.0f}' stroke='#E9F5EF' stroke-width='3' fill='none'/></svg>"
    f"<div class='abs' style='left:{jx + 270:.0f}px;top:{jy - 170:.0f}px;font:30px Oswald;color:#E9F5EF;letter-spacing:3px'>JIANGXI</div>"
    "<div class='abs' style='left:70px;top:50px;font:54px Oswald;color:#4FE3B0;letter-spacing:4px'>EAST ASIA · PROVINCES</div>"
    "<div class='abs' style='left:74px;top:120px;font:24px Mono;color:#9BCDBB'>dark satellite war map · glowing borders · territory · ring</div>", "#06120E")
# 3 SOUTH AMERICA: editorial-shards choropleth, Brazil's states in the kit palette, newsprint, serif title
f = Frame((-82, 13, -34, -56), (900, 40, 900, 1000))
br = ST.get("Brazil", [])
tints = ["#E8551E", "#F08A5D", "#2B57A8", "#6F8FCB", "#111"]
sa = "".join(f"<path d='{f.d(r)}' fill='#E3D6BC' stroke='#EEE7D8' stroke-width='2'/>" for n, r in C.items())
brs = "".join(f"<path d='{f.d(s['r'])}' fill='{tints[(i * 7) % 5]}' stroke='#EEE7D8' stroke-width='2'/>" for i, s in enumerate(br))
out["03_shards_south_america"] = page(
    f"<svg class='abs' style='inset:0' width='1920' height='1080'><polygon points='820,80 1500,30 1580,900 900,980' fill='#2B57A8' opacity='.15'/>{sa}{brs}</svg>"
    "<div class='abs' style='left:70px;top:70px;font:150px Playfair;line-height:.85;color:#111'>Brazil,<br><span style='color:#E8551E'>state</span><br>by state</div>"
    "<div class='abs' style='left:76px;top:520px;background:#111;color:#EEE7D8;font:22px Inter;letter-spacing:3px;padding:10px 16px'>EDITORIAL SHARDS · CHOROPLETH</div>"
    "<div class='abs' style='left:80px;top:620px;font:44px Marker;transform:rotate(-4deg)'>every state, one palette</div>", "#EEE7D8")
# 4 AFRICA: minimal Vox map, one accent, everything else quiet, leader-line labels
f = Frame((-20, 38, 55, -36), (560, 30, 1100, 1020))
af = ["Nigeria", "Ethiopia", "Egypt", "Dem. Rep. Congo", "South Africa", "Kenya"]
lay = "".join(f"<path d='{f.d(r)}' fill='{'#FFDD33' if n in af else '#D8D2C6'}' stroke='#F6F3EC' stroke-width='1.6'/>" for n, r in C.items())
labs = ""
for n, (dx, dy) in zip(af, [(-330, -40), (260, -60), (230, -150), (-380, 40), (-300, 60), (300, 40)]):
    pts = [p for r in rings(C[n]) for p in r]; cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    x, y = f.xy(cx, cy)
    labs += (f"<svg class='abs' style='inset:0' width='1920' height='1080'><path d='M{x:.0f} {y:.0f} L{x + dx:.0f} {y + dy:.0f}' stroke='#111' stroke-width='2.5'/><circle cx='{x:.0f}' cy='{y:.0f}' r='6'/></svg>"
             f"<div class='abs' style='left:{x + dx - (150 if dx < 0 else 0):.0f}px;top:{y + dy - 34:.0f}px;font:26px Inter;color:#111;width:150px;text-align:{'right' if dx < 0 else 'left'}'>{n.replace('Dem. Rep. Congo', 'DR Congo').upper()}</div>")
out["04_minimal_africa"] = page(f"<svg class='abs' style='inset:0' width='1920' height='1080'>{lay}</svg>{labs}"
    "<div class='abs' style='left:70px;top:60px;font:64px Inter;color:#111;letter-spacing:-1px'>Six countries, one accent</div>"
    "<div class='abs' style='left:72px;top:150px;font:24px Inter;color:#7a7266;letter-spacing:2px'>MINIMAL VOX MAP · ONE ACCENT · LEADER LABELS</div>", "#F6F3EC")
# 5 MIDDLE EAST: shipping lanes as glowing arcs on navy, a strait highlighted
f = Frame((20, 42, 80, 5), (120, 60, 1680, 980))
me = "".join(f"<path d='{f.d(r)}' fill='#22324A' stroke='#5F7EA8' stroke-width='1'/>" for n, r in C.items())
hub = (56.3, 26.6)
lanes = [(hub, (72.8, 19.0)), (hub, (39.2, 21.5)), (hub, (32.3, 31.2)), (hub, (51.5, 25.3)), (hub, (47.9, 29.4)), (hub, (66.9, 24.9))]
arcs = "".join(f"<path d='{arc(f, a, b, .28)[0]}' stroke='#FFB347' stroke-width='4' fill='none' filter='url(#gl2)'/><path d='{arc(f, a, b, .28)[0]}' stroke='#FFE2B0' stroke-width='1.6' fill='none'/>" for a, b in lanes)
hx, hy = f.xy(*hub)
out["05_arcs_middle_east"] = page(
    f"<svg class='abs' style='inset:0' width='1920' height='1080'><defs><filter id='gl2'><feGaussianBlur stdDeviation='4'/></filter></defs><rect width='1920' height='1080' fill='#0C1626'/>{me}{arcs}"
    f"<circle cx='{hx:.0f}' cy='{hy:.0f}' r='18' fill='#FFB347'/><circle cx='{hx:.0f}' cy='{hy:.0f}' r='46' fill='none' stroke='#FFB347' stroke-width='3' opacity='.6'/></svg>"
    f"<div class='abs' style='left:{hx + 60:.0f}px;top:{hy + 20:.0f}px;font:30px Oswald;color:#FFE2B0;letter-spacing:3px'>STRAIT OF HORMUZ</div>"
    "<div class='abs' style='left:70px;top:50px;font:56px Oswald;color:#FFE2B0;letter-spacing:3px'>THE GULF · ROUTES OUT</div>"
    "<div class='abs' style='left:72px;top:120px;font:24px Mono;color:#9CB0CC'>night map · glowing arcs · a pulsing hub</div>", "#0C1626")
# 6 OCEANIA: torn newsprint map with tape and pinned city stickers (archive collage)
f = Frame((110, -8, 156, -45), (380, 120, 1300, 860))
au = C.get("Australia")
pins = "".join(f"<svg class='abs' style='inset:0' width='1920' height='1080'><circle cx='{f.xy(*p)[0]:.0f}' cy='{f.xy(*p)[1]:.0f}' r='14' fill='#B3261E' stroke='#fff' stroke-width='4'/></svg>"
               f"<div class='abs' style='left:{f.xy(*p)[0] + 22:.0f}px;top:{f.xy(*p)[1] - 22:.0f}px;background:#F4EEDD;font:22px Mono;padding:6px 10px;box-shadow:4px 5px 0 rgba(0,0,0,.2);transform:rotate(-3deg)'>{n.upper()}</div>"
               for n, p in cities(["Sydney", "Perth", "Darwin", "Melbourne", "Brisbane", "Adelaide"]))
cols = "".join(f"<text x='{x}' y='{y}' font-family='Mono' font-size='13' fill='#000' opacity='.22'>THE NATION · WEATHER · MARKETS · SPORT · LETTERS</text>" for x in range(0, 1920, 520) for y in range(30, 1080, 26))
out["06_torn_newsprint_oceania"] = page(
    f"<svg class='abs' style='inset:0' width='1920' height='1080'><defs><filter id='tr'><feTurbulence type='fractalNoise' baseFrequency='.03' numOctaves='4'/><feDisplacementMap in='SourceGraphic' scale='26'/></filter>"
    f"<pattern id='nw' width='1920' height='1080' patternUnits='userSpaceOnUse'><rect width='1920' height='1080' fill='#E9E2D2'/>{cols}</pattern></defs>"
    f"<g filter='url(#tr)'><path d='{f.d(au)}' fill='url(#nw)' stroke='#111' stroke-width='3'/></g></svg>"
    "<div class='abs' style='left:820px;top:140px;width:170px;height:46px;background:rgba(235,225,190,.8);transform:rotate(-14deg)'></div>"
    "<div class='abs' style='left:1280px;top:700px;width:170px;height:46px;background:rgba(235,225,190,.8);transform:rotate(22deg)'></div>"
    + pins + "<div class='abs' style='left:70px;top:60px;font:90px Anton;color:#111'>AUSTRALIA</div>"
    "<div class='abs' style='left:74px;top:170px;font:26px Caveat;color:#B3261E'>torn from the paper · taped · pinned cities</div>", "#CDBF9F")
# 7 CANADA: blueprint
f = Frame((-141, 70, -52, 41), (100, 120, 1720, 900))
ca = "".join(f"<path d='{f.d(s['r'])}' fill='none' stroke='#E8F1FF' stroke-width='1.6'/>" for s in ST.get("Canada", []))
bgrid = "".join(f"<path d='M{x} 0 V1080' stroke='#E8F1FF' stroke-width='.6' opacity='.25'/>" for x in range(0, 1920, 48)) + "".join(f"<path d='M0 {y} H1920' stroke='#E8F1FF' stroke-width='.6' opacity='.25'/>" for y in range(0, 1080, 48))
out["07_blueprint_canada"] = page(f"<svg class='abs' style='inset:0' width='1920' height='1080'><rect width='1920' height='1080' fill='#1D4E8F'/>{bgrid}{ca}</svg>"
    "<div class='abs' style='left:70px;top:900px;border:3px solid #E8F1FF;padding:14px 22px;font:28px Mono;color:#E8F1FF'>DWG. CANADA · PROVINCES &amp; TERRITORIES · SCALE 1:20M</div>"
    "<div class='abs' style='left:70px;top:50px;font:64px Mono;color:#E8F1FF'>CANADA</div>", "#1D4E8F")
# 8 WORLD: globe (orthographic) with glowing arcs between cities
lam0, phi0 = math.radians(20), math.radians(25)
def ortho(lon, lat):
    l, p = math.radians(lon), math.radians(lat)
    c = math.sin(phi0) * math.sin(p) + math.cos(phi0) * math.cos(p) * math.cos(l - lam0)
    x = math.cos(p) * math.sin(l - lam0); y = math.cos(phi0) * math.sin(p) - math.sin(phi0) * math.cos(p) * math.cos(l - lam0)
    return x, y, c
R, CX, CY = 470, 960, 560
def gd(rs):
    out = []
    for r in rings(rs):
        q = [ortho(*p) for p in r]
        if sum(1 for _, _, c in q if c > 0) < len(q) * .6: continue
        out.append("M" + " L".join(f"{CX + x * R:.0f} {CY - y * R:.0f}" for x, y, c in q) + "Z")
    return " ".join(out)
gl = "".join(f"<path d='{gd(r)}' fill='#2E6A4A' stroke='#9FD7B8' stroke-width='.8'/>" for n, r in C.items())
cs = cities(["London", "New York", "Lagos", "Mumbai", "Cairo", "Moscow", "Nairobi", "Dubai", "Paris", "Beijing"])
def gp(p):
    x, y, c = ortho(*p); return CX + x * R, CY - y * R, c
arcs = ""
for i in range(len(cs) - 1):
    (a, pa), (b, pb) = cs[i], cs[i + 1]
    x1, y1, c1 = gp(pa); x2, y2, c2 = gp(pb)
    if c1 > 0 and c2 > 0:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2; L = math.hypot(x2 - x1, y2 - y1)
        arcs += f"<path d='M{x1:.0f} {y1:.0f} Q{mx:.0f} {my - L * .35:.0f} {x2:.0f} {y2:.0f}' stroke='#7FD3FF' stroke-width='3' fill='none' filter='url(#gl3)'/><circle cx='{x1:.0f}' cy='{y1:.0f}' r='6' fill='#fff'/>"
out["08_globe_world"] = page(
    f"<svg class='abs' style='inset:0' width='1920' height='1080'><defs><radialGradient id='oc' cx='40%' cy='35%'><stop offset='0' stop-color='#2B6CB0'/><stop offset='1' stop-color='#0B2545'/></radialGradient>"
    f"<filter id='gl3'><feGaussianBlur stdDeviation='2.5'/></filter><radialGradient id='at'><stop offset='.86' stop-color='#7FD3FF' stop-opacity='0'/><stop offset='1' stop-color='#7FD3FF' stop-opacity='.45'/></radialGradient></defs>"
    f"<rect width='1920' height='1080' fill='#050A14'/><circle cx='{CX}' cy='{CY}' r='{R + 30}' fill='url(#at)'/><circle cx='{CX}' cy='{CY}' r='{R}' fill='url(#oc)'/>{gl}{arcs}</svg>"
    "<div class='abs' style='left:70px;top:50px;font:56px Oswald;color:#DDF2FF;letter-spacing:3px'>ONE WORLD, TEN CITIES</div>"
    "<div class='abs' style='left:72px;top:120px;font:24px Mono;color:#8FB3CF'>orthographic globe · atmosphere · glowing arcs</div>", "#050A14")
for k, v in out.items():
    (D / f"{k}.html").write_text(v, encoding="utf-8")
print(len(out))
