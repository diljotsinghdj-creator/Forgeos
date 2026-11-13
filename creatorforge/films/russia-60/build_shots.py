"""Russia, 60 s (scale shock): hand-composed shots in the 'atlas red' kit. Elements enter via data-in/data-at (kit.js)."""
import json, math
from pathlib import Path
D = Path(__file__).resolve().parent; A = (D / "assets").as_uri()
W = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
C = {c["n"]: c["r"] for c in W["countries"]}
sc = {s["id"]: s for s in json.load(open(D / "script.json"))}
SPLIT = {"s10": 4.1, "s11": 3.4}
def dur(i):
    if i in SPLIT: return SPLIT[i]
    if i.endswith("b"): return round(sc[i[:-1]]["sec"] + 0.4 - SPLIT[i[:-1]], 2)
    return round(sc[i]["sec"] + (1.6 if i == "s12" else 0.4), 2)
RED, BLUE, INK, PAPER, SIG, STEEL = "#C8341F", "#2F6DB5", "#15171C", "#ECE6DA", "#FFDD33", "#6E7B85"
# Lambert azimuthal equal-area, centred on Russia: areas stay honest, so Italy and Russia share one scale
L0, P0 = math.radians(100), math.radians(62)
def laea(lon, lat):
    l, p = math.radians(lon), math.radians(lat)
    k = math.sqrt(2 / (1 + math.sin(P0) * math.sin(p) + math.cos(P0) * math.cos(p) * math.cos(l - L0)))
    return k * math.cos(p) * math.sin(l - L0), -k * (math.cos(P0) * math.sin(p) - math.sin(P0) * math.cos(p) * math.cos(l - L0))
RU = [[laea(*pt) for pt in ring] for ring in C["Russia"]]
IT = [[laea(*pt) for pt in ring] for ring in C["Italy"]]
def bounds(rings):
    xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
    return min(xs), min(ys), max(xs), max(ys)
def path(rings, s, ox, oy, ref=None):
    x0, y0, _, _ = ref or bounds(rings)
    return " ".join("M" + " L".join(f"{(x - x0) * s + ox:.1f} {(y - y0) * s + oy:.1f}" for x, y in r) + "Z" for r in rings)
def fit(rings, w, h):
    x0, y0, x1, y1 = bounds(rings); return min(w / (x1 - x0), h / (y1 - y0))
RB = bounds(RU)
HEAD = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../kit.css"><script src="../kit.js"></script></head>
<body data-dur="{dur}" data-push="{push}" style="background:{bg}"><svg width="0" height="0" style="position:absolute">
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="3" seed="11"/><feColorMatrix values="0 0 0 0 .2  0 0 0 0 .2  0 0 0 0 .2  0 0 0 .3 0"/></filter></svg><div id="cam">"""
TAIL = """</div><svg class="grain" width="1920" height="1080"><rect width="1920" height="1080" filter="url(#grain)"/></svg>{credit}</body></html>"""
def el(html, x, y, at, k="pop", style="", base="", extra=""):
    return f'<div class="el" data-in="{k}" data-at="{at}" data-base="{base}" style="left:{x}px;top:{y}px;{style}" {extra}>{html}</div>'
def svg(body, at, k="pop", extra=""):
    return f'<svg class="el" data-in="{k}" data-at="{at}" style="inset:0;overflow:visible" width="1920" height="1080" {extra}>{body}</svg>'
def rule(x, y, w, at, col=INK, h=14, rot=-8):
    return el(f'<div style="width:{w}px;height:{h}px;background:{col}"></div>', x, y, at, "wipe", base=f"rotate({rot}deg)")
IMF = "SOURCE: IMF WORLD ECONOMIC OUTLOOK, OCTOBER 2026"
NE = "MAP: NATURAL EARTH, EQUAL-AREA PROJECTION"
shots = {}
# s01 the evidence: the IMF's own chart, Russia's line meeting Italy's
shots["s01"] = dict(bg=PAPER, push=.06, credit=IMF + " · DATAMAPPER, GDP AT CURRENT PRICES (SCREENSHOT)", body=
    '<div class="el dots" data-in="pop" data-at="0" data-d=".01" data-breathe="0" data-jit="0" style="inset:0"></div>'
    + el(f'<div class="print"><img src="{A}/imf_trend.png" style="width:1560px;display:block"></div>', 170, 250, .05, "drop", base="rotate(-1.5deg)")
    + el('<div class="tape" style="transform:rotate(-14deg)"></div>', 140, 235, .45) + el('<div class="tape" style="transform:rotate(12deg)"></div>', 1640, 230, .5)
    + svg('<ellipse cx="1050" cy="452" rx="120" ry="62" fill="none" stroke="#FFDD33" stroke-width="10" transform="rotate(-8 1050 452)"/>', 1.4, "draw")
    + el('<div class="hand" style="font-size:66px;transform:rotate(-6deg)">almost met</div>', 1180, 120, 2.0, "wipe")
    + el('<div class="lab" style="font-size:44px">The world\'s economies · IMF</div>', 170, 110, .3, "wipe"))
# s02 who is who: the chart again, pushed in, labels
shots["s02"] = dict(bg=PAPER, push=.1, credit=IMF + " · DATAMAPPER (SCREENSHOT)", body=
    el(f'<div class="print"><img src="{A}/imf_trend.png" style="width:2600px;display:block"></div>', -620, -150, 0, "pop", extra='data-d=".01" data-breathe="0"', base="rotate(-1.5deg)")
    + el(f'<div class="h" style="font-size:120px;color:#fff;background:{BLUE};padding:14px 30px">Italy</div>', 120, 650, .3, "slide")
    + el(f'<div class="h" style="font-size:120px;color:#fff;background:{RED};padding:14px 30px">Russia</div>', 1180, 760, 1.4, "slide", extra='data-from="r"')
    + el('<div class="hand" style="font-size:58px;color:#15171C;background:#FFDD33;padding:0 18px">largest country on Earth</div>', 1180, 940, 2.0, "wipe"))
# s03 the map: Russia, equal-area, 17.1 million km2, eleven time zones
s3 = fit(RU, 1500, 640); rp = path(RU, s3, 210, 150)
clocks = "".join(el(f'<div class="mono" style="width:132px;text-align:center;font-size:26px;color:#fff;background:{INK if 0 < i < 10 else RED};padding:8px 0">{8 + i:02d}:00</div>', 110 + i * 156, 880, 1.6 + i * .06, "pop") for i in range(11))
shots["s03"] = dict(bg=PAPER, push=.05, credit=NE + " · AREA: CIA WORLD FACTBOOK", body=
    f'<svg class="el" data-in="draw" data-at=".05" data-d="1.4" data-breathe="0" data-jit="0" style="inset:0" width="1920" height="1080"><path d="{rp}" fill="none" stroke="{INK}" stroke-width="3"/></svg>'
    + svg(f'<path d="{rp}" fill="{RED}"/>', 1.0, "pop", 'data-breathe="0"')
    + el('<div class="h" style="font-size:118px;color:#fff;text-shadow:6px 6px 0 #15171C"><span class="el" data-in="count" data-from0="0" data-to="17" data-at=".9" data-d="1.0" style="position:static">17</span>.1 MILLION KM²</div>', 520, 380, .9, "pop")
    + el('<div class="lab" style="font-size:34px">Kaliningrad</div>', 110, 830, 1.6, "wipe") + el('<div class="lab" style="font-size:34px">Kamchatka</div>', 1640, 830, 2.3, "wipe")
    + clocks + el('<div class="lab" style="font-size:40px;background:#FFDD33;padding:2px 14px">11 time zones</div>', 830, 960, 2.4, "wipe"))
# s04 Italy, at the same scale, then 57 of them
s4 = fit(RU, 1060, 560); ref = RB
italy_on_map = path(IT, s4, 640, 520)
ib = bounds(IT); si = fit(IT, 62, 80); ic = path(IT, si, 0, 0)
grid = "".join(f'<g transform="translate({1180 + (i % 8) * 84},{230 + (i // 8) * 102})"><g class="el" data-in="pop" data-at="{.9 + i * .025:.3f}" data-d=".18"><path d="{ic}" fill="{BLUE}"/></g></g>' for i in range(57))
shots["s04"] = dict(bg=PAPER, push=.04, credit=NE + " · COMPUTED: 17,098,242 ÷ 301,340 KM² (CIA WORLD FACTBOOK) = 56.7", body=
    svg(f'<path d="{path(RU, s4, 80, 260)}" fill="#E2B8AE" stroke="{RED}" stroke-width="3"/>', 0, "pop", 'data-d=".01" data-breathe="0" data-jit="0"')
    + svg(f'<path d="{italy_on_map}" fill="{BLUE}"/>', .3, "pop")
    + el('<div class="hand" style="font-size:44px;color:#2F6DB5">Italy, same scale</div>', 560, 800, .5, "wipe")
    + svg(grid, 0, "pop", 'data-breathe="0" data-jit="0"')
    + el('<div class="h" style="font-size:150px;color:#2F6DB5">× 57</div>', 700, 60, 1.0, "pop"))
# s05 the twist: shapes unequal, money equal
s5 = fit(RU, 900, 470)
shots["s05"] = dict(bg=PAPER, push=.04, credit=IMF + " · GDP AT CURRENT PRICES, 2026 PROJECTION", body=
    svg(f'<path d="{path(RU, s5, 40, 120)}" fill="{RED}" opacity=".18"/><path d="{path(IT, s5, 1620, 640, bounds(IT))}" fill="{BLUE}" opacity=".35"/>', 0, "pop", 'data-d=".01" data-breathe="0" data-jit="0"')
    + el(f'<div style="width:300px;height:{int(2.861 * 200)}px;background:{RED}"></div>', 380, 1000 - int(2.861 * 200), .3, "slide", extra='data-from="b"')
    + el(f'<div style="width:300px;height:{int(2.702 * 200)}px;background:{BLUE}"></div>', 1240, 1000 - int(2.702 * 200), .5, "slide", extra='data-from="b"')
    + el('<div class="mono" style="font-size:58px;color:#fff">$2.86T</div>', 410, 1000 - int(2.861 * 200) + 30, 1.0, "wipe")
    + el('<div class="mono" style="font-size:58px;color:#fff">$2.70T</div>', 1270, 1000 - int(2.702 * 200) + 30, 1.1, "wipe")
    + svg(f'<path d="M300 {1000 - 600} H1640" stroke="{INK}" stroke-width="4" stroke-dasharray="16 12"/>', 1.5, "draw")
    + el('<div class="lab" style="font-size:40px;background:#FFDD33;padding:2px 14px">$3 trillion</div>', 1660, 375, 1.8, "wipe")
    + el('<div class="h" style="font-size:96px">Under $3 trillion each</div>', 80, 60, .1, "slide"))
# s06 people: one figure = 5 million
def person(x, y, col):
    return f'<circle cx="{x + 18}" cy="{y + 14}" r="13" fill="{col}"/><rect x="{x + 2}" y="{y + 32}" width="32" height="42" rx="12" fill="{col}"/>'
ppl = ""
for i in range(29):
    ppl += f'<g class="el" data-in="pop" data-at="{.3 + i * .05:.2f}" data-d=".2">{person(120 + (i % 15) * 52, 300 + (i // 15) * 96, RED)}</g>'
for i in range(12):
    ppl += f'<g class="el" data-in="pop" data-at="{2.6 + i * .05:.2f}" data-d=".2">{person(120 + (i % 15) * 52, 640 + (i // 15) * 96, BLUE)}</g>'
shots["s06"] = dict(bg=PAPER, push=.03, credit=IMF + " · POPULATION 2026: RUSSIA 143.4 M, ITALY 58.9 M · ONE FIGURE = 5 MILLION", body=
    svg(ppl, 0, "pop", 'data-breathe="0" data-jit="0"')
    + el('<div class="h" style="font-size:110px;color:#C8341F">143 million</div>', 1000, 300, .3, "slide", extra='data-from="r"')
    + el('<div class="h" style="font-size:110px;color:#2F6DB5">59 million</div>', 1000, 640, 2.6, "slide", extra='data-from="r"')
    + el('<div class="lab" style="font-size:44px">Same-sized economies. How many share them?</div>', 120, 120, .1, "wipe"))
# s07 per person: two bars and counters
shots["s07"] = dict(bg=INK, push=.04, credit=IMF + " · GDP PER PERSON, CURRENT PRICES, 2026 PROJECTION", body=
    el('<div class="lab" style="font-size:46px;color:#ECE6DA">GDP per person, a year</div>', 120, 110, .1, "wipe")
    + el(f'<div style="width:{int(19953 / 46000 * 1500)}px;height:150px;background:{RED}"></div>', 120, 330, .3, "wipe")
    + el(f'<div style="width:1500px;height:150px;background:{BLUE}"></div>', 120, 620, .6, "wipe", extra='data-d=".9"')
    + el('<div class="h" style="font-size:120px;color:#ECE6DA">$<span class="el" data-in="count" data-from0="0" data-to="20000" data-comma="1" data-at=".3" data-d="1.2" style="position:static">20,000</span></div>', 820, 345, .3, "pop")
    + el('<div class="h" style="font-size:120px;color:#fff">$<span class="el" data-in="count" data-from0="0" data-to="46000" data-comma="1" data-at=".6" data-d="1.4" style="position:static">46,000</span></div>', 150, 635, .6, "pop")
    + el('<div class="lab" style="font-size:40px;color:#C8341F">Russia</div>', 120, 280, .3, "wipe") + el('<div class="lab" style="font-size:40px;color:#7FA8DD">Italy</div>', 120, 570, .6, "wipe"))
# s08 the other side: purchasing power ranking
ppp = [("China", 44555), ("United States", 32642), ("India", 19193), ("Russia", 7543), ("Japan", 7324)]
rows = ""
for i, (n, v) in enumerate(ppp):
    me = n == "Russia"
    rows += el(f'<div class="mono" style="font-size:40px;width:60px">{i + 1}</div>', 130, 270 + i * 140, .2 + i * .15, "wipe")
    rows += el(f'<div class="lab" style="font-size:54px;{"background:#FFDD33;padding:0 12px" if me else ""}">{n}</div>', 220, 262 + i * 140, .2 + i * .15, "wipe")
    rows += el(f'<div style="width:{int(v / 44555 * 1050)}px;height:56px;background:{RED if me else STEEL}"></div>', 720, 268 + i * 140, .3 + i * .15, "wipe")
shots["s08"] = dict(bg=PAPER, push=.04, credit=IMF + " · GDP BASED ON PURCHASING-POWER PARITY, 2026 PROJECTION", body=
    rows + el('<div class="h" style="font-size:88px">By purchasing power</div>', 120, 80, .05, "slide")
    + el('<div class="hand" style="font-size:56px;transform:rotate(-5deg)">what money buys at home</div>', 1180, 120, 1.3, "wipe"))
# s09 the leader: Kremlin.ru photo, cut out (background removed, face unaltered), timeline of 25+ years
yrs = "".join(f'<text x="{780 + (y - 1999) * 37}" y="985" font-family="Mono" font-size="22" fill="#15171C" text-anchor="middle">{y}</text>' for y in (1999, 2008, 2012, 2026))
shots["s09"] = dict(bg=PAPER, push=.05, credit="PHOTO: KREMLIN.RU, 2 SEPT 2025 (CC BY 4.0), BACKGROUND REMOVED · ACTING PRESIDENT FROM 31 DEC 1999; PRIME MINISTER 2008–2012", body=
    svg('<polygon points="0,0 820,0 620,1080 0,1080" fill="#C8341F"/>', 0, "slide", 'data-from="l" data-breathe="0"')
    + el(f'<img src="{A}/putin_cut.png" style="width:640px;filter:drop-shadow(14px 16px 0 rgba(21,23,28,.85))">', 60, 230, .2, "slide", extra='data-from="b" data-jit="0"')
    + el('<div class="h" style="font-size:150px">25+ years</div>', 820, 160, .5, "slide", extra='data-from="r"')
    + el('<div class="lab" style="font-size:54px">Vladimir Putin · president or prime minister</div>', 830, 360, .9, "wipe")
    + svg(f'<rect x="780" y="900" width="{9 * 37}" height="40" fill="#15171C"/><rect x="{780 + 9 * 37}" y="900" width="{4 * 37}" height="40" fill="#6E7B85"/><rect x="{780 + 13 * 37}" y="900" width="{14 * 37}" height="40" fill="#15171C"/>{yrs}', 1.3, "wipe")
    + el('<div class="hand" style="font-size:40px;color:#6E7B85">prime minister</div>', 1060, 840, 2.0, "wipe")
    + el('<div class="lab" style="font-size:30px;color:#fff">President</div>', 800, 905, 1.6, "wipe") + el('<div class="lab" style="font-size:30px;color:#fff">President</div>', 1290, 905, 1.8, "wipe"))
# s10 / s10b the budget's oil and gas share: a 10x10 waffle, 30 -> 23
def waffle(n_on, at0, col_on):
    out = ""
    for i in range(100):
        r, c = divmod(i, 10); on = (9 - r) * 10 + c < n_on
        out += f'<rect class="el" data-in="pop" data-at="{at0 + i * .008:.3f}" data-d=".15" x="{1060 + c * 74}" y="{180 + r * 74}" width="64" height="64" fill="{col_on if on else "#D6CEBF"}"/>'
    return out
shots["s10"] = dict(bg=PAPER, push=.03, credit="SOURCE: RUSSIAN FINANCE MINISTRY VIA INTERFAX AND TASS · 2024: 11.13 OF 36.71 TRILLION ROUBLES", body=
    svg(waffle(30, .2, INK), 0, "pop", 'data-breathe="0" data-jit="0"')
    + el('<div class="h" style="font-size:100px">Oil + gas</div>', 110, 200, .1, "slide")
    + el('<div class="lab" style="font-size:44px">share of federal budget revenue</div>', 115, 320, .4, "wipe")
    + el('<div class="h" style="font-size:250px">30%</div>', 110, 450, .9, "pop") + el('<div class="mono" style="font-size:44px">2024</div>', 120, 720, 1.1, "wipe"))
shots["s10b"] = dict(bg=PAPER, push=.03, credit="SOURCE: FINANCE MINISTER ANTON SILUANOV, AS REPORTED BY TASS AND INTERFAX · 2025: 8.48 TRILLION ROUBLES", body=
    svg(waffle(23, 0, RED), 0, "pop", 'data-d=".01" data-breathe="0" data-jit="0"')
    + el('<div class="h" style="font-size:100px">Oil + gas</div>', 110, 200, 0, "pop", extra='data-d=".01"')
    + el('<div class="h" style="font-size:250px;color:#C8341F">23%</div>', 110, 450, .2, "pop") + el('<div class="mono" style="font-size:44px">2025</div>', 120, 720, .3, "wipe")
    + el('<div class="stamp" style="font-size:56px;transform:rotate(-7deg)">Finance ministry</div>', 120, 820, .9))
# s11 / s11b military spending: 7.5% of GDP (SIPRI), then the classified part as redaction bars
shots["s11"] = dict(bg=INK, push=.05, credit="SOURCE: SIPRI, 27 APRIL 2026 · ESTIMATE: $190 BILLION IN 2025", body=
    svg(f'<circle cx="1400" cy="560" r="300" fill="#2A2D34"/><path d="M1400 560 L1400 260 A300 300 0 0 1 {1400 + 300 * math.sin(2 * math.pi * .075):.1f} {560 - 300 * math.cos(2 * math.pi * .075):.1f} Z" fill="{SIG}"/>', .2, "pop")
    + el('<div class="h" style="font-size:230px;color:#FFDD33">7.5%</div>', 110, 330, .4, "pop")
    + el('<div class="lab" style="font-size:52px;color:#ECE6DA">of GDP on the military, 2025</div>', 120, 600, .8, "wipe")
    + el('<div class="lab" style="font-size:36px;color:#6E7B85">SIPRI estimate</div>', 120, 680, 1.1, "wipe"))
bars = ""
for i in range(9):
    w = [1250, 1180, 1290, 900, 1220, 1150, 1260, 1000, 820][i]
    red = i not in (0, 5)
    bars += f'<rect x="300" y="{250 + i * 64}" width="{w}" height="30" fill="{INK if red else "#B9B2A5"}"/>'
    if red: bars += f'<rect class="el" data-in="wipe" data-at="{.2 + i * .1:.2f}" x="290" y="{240 + i * 64}" width="{w + 20}" height="50" fill="{INK}"/>'
shots["s11b"] = dict(bg=PAPER, push=.04, credit="SOURCE: SIPRI · CLASSIFIED SHARE OF RUSSIA'S 'NATIONAL DEFENCE' BUDGET ≈ 79% IN 2025 (SIPRI ESTIMATE) · ILLUSTRATION", body=
    el('<div style="width:1400px;height:700px;background:#fff;box-shadow:14px 16px 0 rgba(21,23,28,.85)"></div>', 240, 200, 0, "pop", extra='data-d=".01" data-breathe="0"')
    + svg(bars, 0, "pop", 'data-breathe="0" data-jit="0"')
    + el('<div class="stamp" style="font-size:80px;transform:rotate(-9deg);background:rgba(236,230,218,.6)">Classified</div>', 1180, 120, 1.3)
    + el('<div class="h" style="font-size:80px">≈ 79% of it</div>', 250, 930, 1.6, "slide"))
# s12 finale: the whole country, and an economy the size of Italy's
s12 = fit(RU, 1700, 720)
shots["s12"] = dict(bg=RED, push=.05, credit=NE + " · " + IMF, body=
    svg(f'<path d="{path(RU, s12, 110, 230)}" fill="#A22816"/>', 0, "pop", 'data-d=".01" data-breathe="0" data-jit="0"')
    + svg(f'<path d="{path(IT, s12, 1640, 800, bounds(IT))}" fill="{BLUE}" stroke="#fff" stroke-width="3"/>', 1.5, "pop") + el('<div class="hand" style="font-size:42px;color:#fff">Italy, same scale</div>', 1460, 990, 1.7, "wipe")
    + el('<div class="h" style="font-size:110px;color:#fff">The largest country on Earth.</div>', 110, 70, .2, "slide")
    + el('<div class="h" style="font-size:110px;color:#15171C"><span class="hl" data-in="sweep" data-at="2.0" data-d=".8">An economy the size of Italy\'s.</span></div>', 110, 520, 1.6, "slide", extra='data-from="r"'))
order = sorted(shots, key=lambda k: (int(k[1:3]), k)); shots = {k: shots[k] for k in order}
for k, s in shots.items():
    (D / "shots" / f"{k}.html").write_text(HEAD.format(dur=dur(k), push=s["push"], bg=s["bg"]) + s["body"] + TAIL.format(credit=f'<div class="credit">{s["credit"]}</div>'), encoding="utf-8")
json.dump({k: dur(k) for k in shots}, open(D / "durations.json", "w"))
print(len(shots), "shots", round(sum(dur(k) for k in shots), 1), "s", {k: dur(k) for k in shots})
