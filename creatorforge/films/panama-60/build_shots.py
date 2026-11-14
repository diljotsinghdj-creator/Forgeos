"""Panama, 60 s: twelve hand-composed shots in the 'water' kit. Each element enters via data-in/data-at (kit.js)."""
import json, math
from pathlib import Path
D = Path(__file__).resolve().parent; A = (D / "assets").as_uri()
MAPS = Path("/home/user/Forgeos/creatorforge/channels/design_kits/maps")
sc = {s["id"]: s for s in json.load(open(D / "script.json"))}
SPLIT = {"s08": 3.3}
def dur(i):
    if i in SPLIT: return SPLIT[i]
    if i.endswith("b"): return round(sc[i[:-1]]["sec"] + 0.45 - SPLIT[i[:-1]], 2)
    return round(sc[i]["sec"] + (1.8 if i == "s12" else 0.45), 2)
HEAD = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../kit.css"><script src="../kit.js"></script></head>
<body data-dur="{dur}" data-push="{push}" style="background:{bg}"><svg width="0" height="0" style="position:absolute">
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="5"/><feColorMatrix values="0 0 0 0 .3  0 0 0 0 .28  0 0 0 0 .22  0 0 0 .32 0"/></filter>
<filter id="torn"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="4" seed="7"/><feDisplacementMap in="SourceGraphic" scale="30"/></filter></svg><div id="cam">"""
TAIL = """</div><svg class="grain" width="1920" height="1080"><rect width="1920" height="1080" filter="url(#grain)"/></svg>{credit}</body></html>"""
def el(html, x, y, at, k="pop", style="", base="", extra=""):
    return f'<div class="el" data-in="{k}" data-at="{at}" data-base="{base}" style="left:{x}px;top:{y}px;{style}" {extra}>{html}</div>'
def svg(body, at, k="pop", extra=""):
    return f'<svg class="el" data-in="{k}" data-at="{at}" style="inset:0" width="1920" height="1080" {extra}>{body}</svg>'
def ship(x, y, s=1.0, col="#14212B"):
    # a container ship side view, bow to the right
    return (f'<g transform="translate({x},{y}) scale({s})"><path d="M0 40 L300 40 L280 72 L18 72 Z" fill="{col}"/>'
            + "".join(f'<rect x="{30 + i * 26}" y="{18 - (i % 3) * 4}" width="22" height="{22 + (i % 3) * 4}" fill="{["#D9663A", "#2A8C9E", "#F1E9D8", "#FFDD33"][i % 4]}" stroke="{col}" stroke-width="2"/>' for i in range(8))
            + f'<rect x="250" y="0" width="26" height="40" fill="#F1E9D8" stroke="{col}" stroke-width="3"/><rect x="256" y="6" width="14" height="6" fill="{col}"/></g>')
LOC = "PHOTO: LIBRARY OF CONGRESS (PUBLIC DOMAIN)"
S2 = "SATELLITE: SENTINEL-2 CLOUDLESS 2016 BY EOX (CC BY 4.0), CONTAINS MODIFIED COPERNICUS SENTINEL DATA"
shots = {}
import re
m = (MAPS / "09_satellite_route_panama.html").read_text()
imgs = "".join(re.findall(r"<img src='[^']+' style='position:absolute;[^']+'>", m))
dpath = re.search(r"<path d='(M[^']+)' stroke='#FFC86B'", m).group(1)
pts = [tuple(map(float, p.split())) for p in dpath[1:].split(" L")]
# s01 opening on the map: zoomed satellite on Pedro Miguel, pin, then the real 1914 print drops in (evidence first)
pm = pts[int(len(pts) * 0.8)]
shots["s01"] = dict(bg="#000", push=.06, credit=LOC + " · S.S. ANCON, 15 AUG 1914 · " + S2, body=
    f'<div class="el" data-in="pop" data-at="0" data-d=".01" data-breathe="0" data-jit="0" style="inset:0;transform-origin:{pm[0]:.0f}px {pm[1]:.0f}px" data-base="translate({560 - pm[0]:.0f}px,{540 - pm[1]:.0f}px) scale(2.6)"><div style="position:absolute;inset:0;filter:saturate(.8) contrast(1.08) brightness(.62)">{imgs}</div></div>'
    + svg('<circle cx="560" cy="540" r="22" fill="#FFDD33" stroke="#14212B" stroke-width="6"/><circle cx="560" cy="540" r="54" fill="none" stroke="#FFDD33" stroke-width="4"/>', .1)
    + el('<div class="cap" style="font-size:28px;color:#fff;background:#14212B;padding:6px 12px">Pacific-side locks · today</div>', 250, 610, .3, "wipe")
    + el(f'<div class="print"><img src="{A}/ancon_1914.jpg" style="width:860px;filter:sepia(.35) contrast(1.08)"></div>', 860, 120, .5, "drop", base="rotate(-3deg)")
    + el('<div class="tape" style="transform:rotate(-20deg)"></div>', 840, 110, .9) + el('<div class="tape" style="transform:rotate(24deg)"></div>', 1660, 100, .95)
    + el('<div class="stamp" style="font-size:72px;transform:rotate(-8deg);background:#F1E9D8">15 AUG 1914</div>', 1240, 760, 1.6)
    + el('<div class="note" style="font-size:58px;color:#FFDD33;transform:rotate(-5deg)">the first ship through</div>', 900, 900, 2.2, "wipe"))
# s02 satellite route: Colón to Balboa (Sentinel-2 tiles from the map kit)
shots["s02"] = dict(bg="#000", push=.07, credit=S2 + " · ROUTE APPROXIMATE", body=
    f'<div class="el" data-in="pop" data-at="0" data-d=".01" data-breathe="0" data-jit="0" style="inset:0;filter:saturate(.85) contrast(1.08) brightness(.8)">{imgs}</div>'
    + f'<svg class="el" data-in="draw" data-at=".3" data-d="2.4" data-jit="0" data-breathe="0" style="inset:0" width="1920" height="1080"><path d="{dpath}" stroke="#FFDD33" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    + svg(f'<circle cx="{pts[0][0]:.0f}" cy="{pts[0][1]:.0f}" r="16" fill="#D9663A" stroke="#fff" stroke-width="5"/>', .2)
    + svg(f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1]:.0f}" r="16" fill="#fff" stroke="#14212B" stroke-width="5"/>', 2.6)
    + el('<div class="cap" style="font-size:24px;color:#fff">Caribbean</div>', pts[0][0] + 30, pts[0][1] - 16, .3, "wipe")
    + el('<div class="cap" style="font-size:24px;color:#fff">Pacific</div>', pts[-1][0] + 30, pts[-1][1] - 16, 2.7, "wipe")
    + el('<div class="serif" style="font-size:150px;color:#fff">82 km</div>', 70, 60, .8, "slide")
    + el('<div class="note" style="font-size:52px;color:#FFDD33">ocean to ocean</div>', 80, 220, 1.4, "wipe"))
# s03 they climb it: the colour 1913 view of Pedro Miguel, rust shard, huge serif
shots["s03"] = dict(bg="#F1E9D8", push=.05, credit=LOC + " · PEDRO MIGUEL LOCKS, c.1913", body=
    svg('<polygon points="900,60 1860,20 1880,1000 980,1060" fill="#D9663A"/>', 0, "slide", 'data-from="r"')
    + el(f'<div class="print" style="padding:16px 16px 16px"><img src="{A}/pedromiguel_color.jpg" style="width:820px"></div>', 1000, 150, .2, "drop", base="rotate(2deg)")
    + el('<div class="serif" style="font-size:150px">They don\'t<br>sail across.</div>', 80, 180, .4, "slide")
    + el('<div class="serif" style="font-size:190px;color:#D9663A"><span class="hl" data-in="sweep" data-at="2.0">They climb.</span></div>', 80, 560, 1.4, "pop"))
# s04 the locks as a staircase (cross-section): sea -> three steps -> lake at +26 m -> three steps -> sea
steps = [(0, 0), (1, 1), (2, 2), (3, 3)]
sx, sw, sh = 160, 220, 120
water = ""
for i in range(4):   # up from the Caribbean
    water += f'<rect class="el" data-in="slide" data-from="b" data-at="{.2 + i * .25:.2f}" x="{sx + i * sw}" y="{860 - i * sh}" width="{sw}" height="{i * sh + 60}" fill="#2A8C9E"/>'
water += f'<rect class="el" data-in="slide" data-from="b" data-at="1.2" x="{sx + 4 * sw}" y="{860 - 3 * sh}" width="260" height="{3 * sh + 60}" fill="#2A8C9E"/>'
for i in range(3, -1, -1):   # down to the Pacific
    water += f'<rect class="el" data-in="slide" data-from="b" data-at="{1.4 + (3 - i) * .2:.2f}" x="{sx + 4 * sw + 260 + (3 - i) * 170}" y="{860 - i * sh}" width="170" height="{i * sh + 60}" fill="#2A8C9E"/>'
shots["s04"] = dict(bg="#F1E9D8", push=.04, credit="ILLUSTRATIVE CROSS-SECTION, NOT TO SCALE · DATA: WIKIPEDIA, BRITANNICA", body=
    f'<svg class="el" data-in="pop" data-at="0" data-breathe="0" data-jit="0" style="inset:0" width="1920" height="1080">{water}'
    f'<path d="M{sx} 860 H1860" stroke="#14212B" stroke-width="3" stroke-dasharray="10 8"/>'
    f'<g class="el" data-in="slide" data-from="l" data-at="1.6">{ship(sx + 3 * sw + 30, 860 - 3 * sh - 72, .9)}</g></svg>'
    + el('<div class="cap" style="font-size:24px">sea level</div>', 170, 880, .4, "wipe")
    + el('<div class="cap" style="font-size:26px;color:#0E4D64">Gatun Lake</div>', sx + 4 * sw + 30, 860 - 3 * sh + 30, 1.4, "wipe")
    + svg(f'<path d="M{sx + 4 * sw + 240} 860 V{860 - 3 * sh}" stroke="#D9663A" stroke-width="6"/><path d="M{sx + 4 * sw + 226} {860 - 3 * sh + 18} L{sx + 4 * sw + 240} {860 - 3 * sh} L{sx + 4 * sw + 254} {860 - 3 * sh + 18}" stroke="#D9663A" stroke-width="6" fill="none"/>', 1.9, "draw")
    + el('<div class="serif" style="font-size:150px;color:#D9663A">+26 m</div>', 1290, 300, 2.1, "pop")
    + el('<div class="serif" style="font-size:96px">Three steps up</div>', 80, 70, .1, "slide"))
# s05 photo-filled type: GATUN with the lake inside the letters
shots["s05"] = dict(bg="#F1E9D8", push=.05, credit=S2, body=
    el(f'<div style="font:520px DMSerif;letter-spacing:-10px;line-height:1;background:url({A}/gatun_s2.jpg) center/cover;-webkit-background-clip:text;background-clip:text;color:transparent;filter:saturate(1.35) contrast(1.15) brightness(1.15)">GATUN</div>', 150, 180, .1, "pop")
    + el('<div class="cap" style="font-size:34px;color:#0E4D64">a man-made lake · fresh water</div>', 170, 800, .9, "wipe")
    + el('<div class="note" style="font-size:54px;color:#D9663A">26 m above the sea</div>', 1180, 820, 1.5, "wipe"))
# s06 object infographic: a glass of water bigger than the ship
shots["s06"] = dict(bg="#F1E9D8", push=.04, credit="AVERAGE PER TRANSIT · SOURCES: WIKIPEDIA, WATERWORLD", body=
    svg('<path d="M1060 140 L1700 140 L1640 980 L1120 980 Z" fill="#E6EEF0" stroke="#14212B" stroke-width="8"/>', 0, "drop")
    + '<svg class="el" data-in="slide" data-from="b" data-at=".6" data-d="1.6" style="inset:0" width="1920" height="1080"><defs><clipPath id="g"><path d="M1060 140 L1700 140 L1640 980 L1120 980 Z"/></clipPath></defs><rect x="1000" y="260" width="800" height="740" fill="#2A8C9E" opacity=".85" clip-path="url(#g)"/></svg>'
    + svg(ship(1180, 190, 1.3), 1.6, "drop")
    + el('<div class="serif" style="font-size:170px;color:#0E4D64">200,000,000</div>', 70, 260, .4, "slide")
    + el('<div class="cap" style="font-size:40px">litres of fresh water</div>', 80, 450, .9, "wipe")
    + el('<div class="note" style="font-size:64px;transform:rotate(-4deg)">every ship, every crossing</div>', 70, 560, 1.6, "wipe"))
# s07 units: 80 Olympic pools
pools = "".join(f'<div class="el" data-in="pop" data-at="{.2 + i * .022:.3f}" data-d=".2" style="left:{110 + (i % 16) * 106}px;top:{330 + (i // 16) * 120}px;width:92px;height:96px;background:#2A8C9E;border:4px solid #F1E9D8;outline:2px solid #0E4D64;background-image:repeating-linear-gradient(90deg,transparent 0 16px,rgba(255,255,255,.55) 16px 18px)"></div>' for i in range(80))
shots["s07"] = dict(bg="#F1E9D8", push=.03, credit="COMPUTED: 200 MILLION L / 2.5 MILLION L PER OLYMPIC POOL", body=
    pools + el('<div class="serif" style="font-size:130px">≈ 80 Olympic pools</div>', 100, 90, .1, "slide")
    + el('<div class="note" style="font-size:66px;transform:rotate(-4deg)">per ship</div>', 1500, 940, 2.0, "wipe"))
# s08 torn strip reveal: the lake, drained of colour; October 2023
shots["s08"] = dict(bg="#3A2E22", push=.06, credit=S2 + " (2016 IMAGE, TINTED) · SOURCE: PANAMA CANAL AUTHORITY", body=
    el(f'<img src="{A}/gatun_s2.jpg" style="width:1920px;height:1080px;object-fit:cover;filter:sepia(.8) saturate(.6) contrast(1.05) brightness(.85)">', 0, 0, 0, "pop", extra='data-breathe="0" data-jit="0"')
    + svg('<g filter="url(#torn)" transform="rotate(-5 960 540)"><rect x="-120" y="370" width="2160" height="330" fill="#F1E9D8"/></g><g filter="url(#torn)" transform="rotate(-5 960 540)"><rect x="-120" y="392" width="2160" height="286" fill="#D9663A"/></g>', .5, "slide")
    + el('<div class="serif" style="font-size:190px;color:#F1E9D8">October 2023</div>', 230, 400, 1.0, "pop", base="rotate(-5deg)")
    + el('<div class="cap" style="font-size:36px;color:#F1E9D8;background:#14212B;padding:10px 18px">the driest October on record for the canal\'s watershed</div>', 260, 760, 1.8, "wipe"))
# s08b a real cut: close on the tinted lake, the record called out (no new fact, the same claim P6)
shots["s08b"] = dict(bg="#3A2E22", push=.08, credit=S2 + " (2016 IMAGE, TINTED) · SOURCE: PANAMA CANAL AUTHORITY", body=
    el(f'<img src="{A}/gatun_s2.jpg" style="width:1920px;height:1080px;object-fit:cover;transform:scale(1.8);transform-origin:30% 60%;filter:sepia(.85) saturate(.5) brightness(.7)">', 0, 0, 0, "pop", extra='data-breathe="0" data-jit="0" data-d=".01"')
    + el('<div class="serif" style="font-size:150px;color:#F1E9D8;line-height:1.05">The driest<br>October <span class="hl" data-in="sweep" data-at=".9" data-d=".9" style="color:#14212B">on record</span></div>', 140, 260, .1, "slide")
    + el('<div class="cap" style="font-size:32px;color:#F1E9D8">the canal\'s watershed · Panama Canal Authority</div>', 150, 760, .6, "wipe"))
# s09 ships as bars: 36 on a normal day, 22 in December 2023
fl = ""
for i in range(36):
    x, y = 120 + (i % 12) * 140, 300 + (i // 12) * 150
    keep = i < 22
    fl += f'<g class="el" data-in="pop" data-at="{.15 + i * .03:.2f}" data-d=".2">{ship(x, y, .42, "#14212B" if keep else "#B8AE9A")}</g>'
    if not keep:
        fl += f'<path class="el" data-in="draw" data-at="{2.4 + (i - 22) * .04:.2f}" d="M{x - 4} {y + 40} L{x + 130} {y + 4}" stroke="#D9663A" stroke-width="7"/>'
shots["s09"] = dict(bg="#F1E9D8", push=.03, credit="SOURCE: PANAMA CANAL AUTHORITY, ADVISORY A-54-2023", body=
    svg(fl, 0, "pop", 'data-breathe="0" data-jit="0"')
    + el('<div class="serif" style="font-size:120px">36 <span style="font-size:60px">a day, normally</span></div>', 120, 90, .1, "slide")
    + el('<div class="serif" style="font-size:120px;color:#D9663A">22 <span style="font-size:60px">in December 2023</span></div>', 1000, 820, 2.3, "pop"))
# s10 the authority's own words, highlighted (document)
shots["s10"] = dict(bg="#E7DCC2", push=.04, credit="PANAMA CANAL AUTHORITY, PRESS RELEASE, 15 DECEMBER 2023", body=
    el('<div style="width:1300px;background:#FBF8F1;padding:60px 70px;box-shadow:14px 18px 0 rgba(0,0,0,.16);font:44px/1.55 DMSerif;color:#14212B">'
       'October 2023 marked the driest October on record for the Canal Watershed. ... '
       '<span class="hl" data-in="sweep" data-at="1.4" data-d="1.4">This year marks the first time the Canal has ever had to restrict transits.</span></div>', 300, 210, .1, "drop", base="rotate(-1.5deg)")
    + el('<div class="cap" style="font-size:28px">Panama Canal Authority · 15 Dec 2023</div>', 320, 860, .8, "wipe")
    + el('<div class="stamp" style="font-size:54px;transform:rotate(7deg)">first time ever</div>', 1380, 120, 2.6))
# s11 rain returns: 22 -> 24, rain doodles
rain = "".join(f'<path class="el" data-in="draw" data-at="{.3 + k * .05:.2f}" d="M{200 + (k * 137) % 1500} {120 + (k * 61) % 260} l-26 70" stroke="#2A8C9E" stroke-width="7" stroke-linecap="round"/>' for k in range(26))
shots["s11"] = dict(bg="#F1E9D8", push=.05, credit="SOURCE: PANAMA CANAL AUTHORITY", body=
    svg(rain, 0, "pop", 'data-breathe="0"')
    + el('<div class="serif" style="font-size:420px;color:#0E4D64"><span class="el" data-in="count" data-from0="22" data-to="24" data-at=".8" data-d="1.2" style="position:static">24</span></div>', 620, 380, .3, "pop")
    + el('<div class="cap" style="font-size:40px">ships a day · from January 2024</div>', 640, 820, 1.4, "wipe")
    + el('<div class="note" style="font-size:60px;transform:rotate(-5deg)">rain, at last</div>', 1320, 420, 1.9, "wipe"))
# s12 finale: the 1914 ship and the rain line
shots["s12"] = dict(bg="#0E4D64", push=.05, credit=LOC + " · S.S. ANCON, 1914", body=
    svg('<polygon points="1100,0 1920,0 1920,1080 1250,1080" fill="#D9663A"/>', 0, "slide", 'data-from="r"')
    + el(f'<div class="print"><img src="{A}/ancon_1914.jpg" style="width:640px;filter:sepia(.4)"></div>', 1180, 230, .2, "drop", base="rotate(3deg)")
    + el('<div class="serif" style="font-size:120px;color:#F1E9D8;width:980px">A shortcut for the world\'s ships,</div>', 90, 230, .5, "slide")
    + el('<div class="serif" style="font-size:120px;color:#FFDD33;width:980px">filled by Panama\'s rain.</div>', 90, 560, 1.4, "slide"))
order = sorted(shots, key=lambda k: (int(k[1:3]), k))
shots = {k: shots[k] for k in order}
for k, s in shots.items():
    (D / "shots" / f"{k}.html").write_text(HEAD.format(dur=dur(k), push=s["push"], bg=s["bg"]) + s["body"] + TAIL.format(credit=f'<div class="credit">{s["credit"]}</div>' if s["credit"] else ""), encoding="utf-8")
json.dump({k: dur(k) for k in shots}, open(D / "durations.json", "w"))
print(len(shots), "shots", round(sum(dur(k) for k in shots), 1), "s")
