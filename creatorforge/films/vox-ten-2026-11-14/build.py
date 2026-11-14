"""Ten Print Facts key frames, each with its own Visual DNA, each built on a real primary source fetched on
2026-11-14 (see dossier.json). Visuals only: no video."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/Forgeos/creatorforge/channels/design_kits/collage")
import collage2 as K
from collage2 import el, STILL

D = Path(__file__).resolve().parent
A, DATA = D / "assets", D / "data"
F = K.FONTS
u = lambda n: (A / n).as_uri()
SIG = "#FFDD33"


def faces(*pairs):
    return "<style>" + "".join(f"@font-face{{font-family:{n};src:url({(F / (p + '.woff2')).as_uri()})}}" for n, p in pairs) + "</style>"


EXTRA = faces(("Plex", "ibm-plex-mono-latin-500-normal"), ("Caveat", "caveat-latin-700-normal"), ("Kalam", "kalam-latin-700-normal"),
              ("Mukta", "mukta-devanagari-800-normal"), ("Grotesk", "space-grotesk-latin-700-normal"), ("ISerif", "instrument-serif-latin-400-normal"))
W = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
raw = json.load(open(DATA / "raw.json"))


def world_path(lon0, lon1, lat0, lat1, w, h, skip=()):
    """Equirectangular outline of every country in a lon/lat window, scaled to w x h."""
    sx, sy = w / (lon1 - lon0), h / (lat1 - lat0)
    out = []
    for c in W["countries"]:
        if c["n"] in skip:
            continue
        rings = c["r"] if isinstance(c["r"], list) else json.loads(c["r"])
        for r in rings:
            if len(r) > 3:
                out.append("M" + " L".join(f"{(lo - lon0) * sx:.1f} {(lat1 - la) * sy:.1f}" for lo, la in r) + "Z")
    return "".join(out), (lambda lo, la: ((lo - lon0) * sx, (lat1 - la) * sy))


S = {}

# 1 LOUISIANA PURCHASE · 1803 ledger: Playfair + Plex Mono, parchment / iron-gall / wax red, receipt motif
INK1, PARCH, WAX = "#3B2A1A", "#EDE3CC", "#9E1B1B"
body = EXTRA + el(f'<div style="width:620px;height:990px;overflow:hidden;box-shadow:0 26px 50px rgba(59,42,26,.45)"><img src="{u("louisiana_doc.jpg")}" style="width:100%;filter:sepia(.25) contrast(1.1)"></div>', 110, 45, .1, "drop", base="rotate(-2deg)", z=4)
body += el(f'<div style="font:900 190px/0.9 Playfair;color:{INK1}">$15<br>million</div>', 860, 110, .4, "slide", z=5)
receipt = (f'<div style="width:620px;background:#fbf6ea;padding:26px 32px;font:500 24px/1.9 Plex;color:{INK1};box-shadow:0 16px 30px rgba(59,42,26,.3);'
           f'clip-path:polygon(0 0,100% 0,100% 94%,96% 100%,92% 94%,88% 100%,84% 94%,80% 100%,76% 94%,72% 100%,68% 94%,64% 100%,60% 94%,56% 100%,52% 94%,48% 100%,44% 94%,40% 100%,36% 94%,32% 100%,28% 94%,24% 100%,20% 94%,16% 100%,12% 94%,8% 100%,4% 94%,0 100%)">'
           f'TREATY WITH FRANCE ........ 30 APR 1803<br>LAND WEST OF THE MISSISSIPPI<br>AREA .................. 828,000 SQ MI<br>'
           f'<span class="hl" style="--hl:100%">PRICE ................. $15,000,000</span><br>RESULT ..... THE U.S. DOUBLED ITS SIZE</div>')
body += el(receipt, 880, 560, .8, "drop", base="rotate(1.5deg)", z=6)
body += el(f'<div style="width:118px;height:118px;border-radius:50%;background:radial-gradient(circle at 38% 35%,#c33 0%,{WAX} 55%,#5e0e0e 100%);box-shadow:0 6px 14px rgba(0,0,0,.4)"></div>', 600, 880, 1.2, "pop", z=7)
S["01_louisiana"] = (body, f"background:{PARCH}", "DOCUMENT: LOUISIANA PURCHASE TREATY, 30 APRIL 1803, FINAL PAGE · NATIONAL ARCHIVES (NAID 299807, USE UNRESTRICTED) · FIGURES: NARA MILESTONE DOCUMENTS")

# 2 19TH AMENDMENT · suffrage sash: DM Serif + Oswald, purple / white / gold, 36-of-48 tally
PUR, GOLD = "#5B2A86", "#D4A017"
tiles = "".join(f'<div style="width:96px;height:96px;background:{GOLD if i == 35 else (PUR if i < 35 else "transparent")};border:3px solid {PUR};'
                f'display:flex;align-items:center;justify-content:center;font:600 30px Oswald;color:{"#fff" if i < 35 else (PUR if i > 35 else "#2a1540")}">{i + 1}</div>' for i in range(48))
body = EXTRA + el(f'<div style="display:grid;grid-template-columns:repeat(8,96px);gap:12px">{tiles}</div>', 760, 150, .3, "pop", z=5)
body += el(f'<div style="width:600px;height:897px;overflow:hidden;box-shadow:0 20px 40px rgba(0,0,0,.25)"><img src="{u("nineteenth_doc.jpg")}" style="width:100%"></div>', 90, 70, .1, "drop", base="rotate(-1.5deg)", z=4)
body += el(f'<div style="font:400 54px/1.05 Serif;color:{PUR};width:420px">36 of 48 states had to say yes.</div>', 760, 30, .5, "wipe", z=6)
body += el(f'<div style="background:{GOLD};padding:10px 18px;font:600 26px Oswald;letter-spacing:2px;color:#2a1540">No. 36 · TENNESSEE · 18 AUGUST 1920</div>', 760, 900, 1.0, "wipe", z=7)
body += el(f'<div style="font:600 22px Oswald;letter-spacing:3px;color:{PUR}">THREE-FOURTHS OF THE STATES</div>', 762, 850, 1.2, "wipe", z=6)
body += el(f'<div style="width:1920px;height:26px;background:repeating-linear-gradient(90deg,{PUR} 0 640px,#fff 640px 1280px,{GOLD} 1280px 1920px)"></div>', 0, 1054, 0, "pop", extra=STILL, z=3)
S["02_nineteenth"] = (body, "background:#F6F2EA", "DOCUMENT: JOINT RESOLUTION PROPOSING THE 19TH AMENDMENT, 1919 · NATIONAL ARCHIVES (NAID 596314, USE UNRESTRICTED) · RATIFICATION FACTS: NARA MILESTONE DOCUMENTS")

# 3 MARSHALL PLAN · cargo stencil: Bebas + Plex Mono, kraft / olive / stencil black, crate-label motif
OLIVE, KRAFT = "#4B5320", "#C9A97A"
d, P = world_path(-13, 36, 34, 62, 1150, 760)
mapsvg = f'<svg width="1150" height="760"><path d="{d}" fill="{OLIVE}" fill-opacity=".85" stroke="{KRAFT}" stroke-width="1.2"/></svg>'
body = EXTRA + el(mapsvg, 720, 150, 0, "pop", extra=STILL, z=2)
body += el(f'<svg width="760" height="200"><path d="M0 150 C 240 30 520 20 740 90" stroke="#141414" stroke-width="5" fill="none" stroke-dasharray="20 12"/><polygon points="740,90 712,66 706,100" fill="#141414"/></svg>', 0, 500, .3, "pop", z=4)
body += el('<div style="font:500 20px Plex;color:#141414;letter-spacing:2px">FROM THE UNITED STATES</div>', 40, 700, .5, "wipe", z=5)
crate = (f'<div style="width:620px;padding:24px 30px;border:6px solid #141414;background:rgba(201,169,122,.92);font:400 76px/0.95 Bebas;color:#141414;letter-spacing:4px">'
         f'$13.3 BILLION<div style="font:500 22px/1.5 Plex;letter-spacing:2px;margin-top:10px">FOR EUROPEAN RECOVERY · APPROPRIATED OVER FOUR YEARS · ACT SIGNED 3 APRIL 1948</div></div>')
body += el(crate, 80, 750, .7, "drop", base="rotate(-1.2deg)", z=6)
body += el(f'<div style="width:360px;height:540px;overflow:hidden;box-shadow:0 16px 30px rgba(0,0,0,.35)"><img src="{u("marshall_doc.jpg")}" style="width:100%"></div>', 120, 40, .2, "drop", base="rotate(2deg)", z=5)
S["03_marshall"] = (body, f"background:{KRAFT}", "DOCUMENT: ECONOMIC COOPERATION ACT OF 1948 (MARSHALL PLAN) · NATIONAL ARCHIVES (NAID 299857, USE UNRESTRICTED) · FIGURE: NARA MILESTONE DOCUMENTS · MAP: NATURAL EARTH")

# 4 GERRYMANDER · woodcut and red marker: Playfair + Caveat, bone / black / vermilion, annotation motif
VERM = "#E2451D"
body = EXTRA + el(f'<div style="width:700px;height:924px;overflow:hidden;box-shadow:0 20px 40px rgba(0,0,0,.3)"><img src="{u("gerrymander.jpg")}" style="width:100%;filter:contrast(1.25)"></div>', 160, 70, .1, "pop", z=4)
body += el(f'<svg width="700" height="924"><path d="M215 64 C 330 58 420 62 500 60" stroke="{VERM}" stroke-width="8" fill="none" stroke-linecap="round"/></svg>', 160, 70, .6, "draw", z=6)
body += el(f'<div style="font:900 120px/0.92 Playfair;color:#141414">A district<br>drawn as<br>a monster.</div>', 980, 130, .3, "wipe", z=5)
body += el(f'<div style="font:700 52px/1.1 Caveat;color:{VERM};width:760px">“a new species of monster, which appeared in Essex South District”</div>', 990, 600, .9, "wipe", z=6)
body += el('<div style="font:600 20px Mono;letter-spacing:2px;color:#141414">MASSACHUSETTS · 1812 · THE ORIGINAL CARTOON</div>', 992, 820, 1.1, "wipe", z=6)
S["04_gerrymander"] = (body, "background:#EFE9DC", "CARTOON: 'THE GERRY-MANDER', 1812 · LIBRARY OF CONGRESS PRINTS & PHOTOGRAPHS (2022637334), PUBLIC DOMAIN BY AGE · QUOTE: ITS PRINTED TITLE")

# 5 ARAL SEA · salt crust: Oswald + Plex Mono, salt white / ochre / teal, split-wipe motif
TEAL = "#1E7F79"
pair = u("GSFC_20171208_Archive_e000965.jpg")                       # left half 2014, right half 2000 (NASA caption)
half = lambda left_pct: f'<div style="width:880px;height:880px;overflow:hidden;position:relative"><img src="{pair}" style="position:absolute;height:880px;left:{left_pct}px"></div>'
body = EXTRA + el(half(-880), 70, 140, .1, "pop", z=4) + el(half(0), 970, 140, .4, "wipe", z=4)
body += el('<div style="width:8px;height:880px;background:#fff;box-shadow:0 0 18px rgba(0,0,0,.5)"></div>', 956, 140, .5, "pop", z=6)
body += el(f'<div style="font:600 60px Oswald;color:#fff;text-shadow:0 2px 10px #000">2000</div>', 100, 160, .3, "wipe", z=7)
body += el(f'<div style="font:600 60px Oswald;color:#fff;text-shadow:0 2px 10px #000">2014</div>', 1000, 160, .6, "wipe", z=7)
body += el(f'<div style="font:600 46px Oswald;color:#3a2f22;letter-spacing:1px">Once the fourth-largest lake in the world</div>', 70, 40, .2, "slide", z=7)
body += el(f'<div style="background:{TEAL};color:#fff;padding:6px 12px;font:500 18px Plex;letter-spacing:1px">BLACK LINE: THE SHORE IN 1960</div>', 1440, 980, 1.0, "wipe", z=7)
S["05_aral"] = (body, "background:#E9E2D2", "IMAGES: NASA TERRA / MODIS, 2000 AND 2014, WITH THE 1960 SHORELINE (NASA GSFC_20171208_ARCHIVE_E000965, PUBLIC DOMAIN)")

# 6 US DEBT · banknote engraving: DM Serif + JetBrains Mono, banknote green / cream / seal red, counter motif
GRN, CRM = "#2F5D50", "#F1EDE0"
dn = raw["debt_now"]
hist = [(r["record_date"][:4], float(r["tot_pub_debt_out_amt"])) for r in raw["debt_hist"]] + [(dn["record_date"][:4], float(dn["tot_pub_debt_out_amt"]))]
guill = "repeating-radial-gradient(circle at 50% 120%,transparent 0 6px,rgba(47,93,80,.09) 6px 7px)"
body = EXTRA + el(f'<div style="width:1920px;height:1080px;background:{guill}"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
body += el(f'<div style="font:500 22px Mono;letter-spacing:4px;color:{GRN}">TOTAL PUBLIC DEBT OUTSTANDING · {dn["record_date"]}</div>', 110, 80, .1, "wipe", z=5)
amt = f'${float(dn["tot_pub_debt_out_amt"]):,.2f}'
body += el(f'<div style="font:400 104px Serif;color:#16302a;letter-spacing:-1px">{amt}</div>', 100, 120, .3, "wipe", z=5)
mx = max(v for _, v in hist)
for i, (y, v) in enumerate(hist):
    h = int(v / mx * 520)
    body += el(f'<div style="width:260px;height:{h}px;background:repeating-linear-gradient(0deg,{GRN} 0 10px,#3d7465 10px 12px);box-shadow:0 10px 20px rgba(0,0,0,.25)"></div>', 160 + i * 420, 930 - h, .5 + i * .25, "wipe", z=4, extra='data-from="bottom"')
    body += el(f'<div style="font:400 44px/1.2 Serif;color:#16302a">${v / 1e12:.1f}T <span style="font:500 22px Mono;color:{GRN}">{y}</span></div>', 160 + i * 420, 940, .8 + i * .25, "pop", z=5)
body += el(f'<div style="border:3px solid {GRN};color:{GRN};padding:10px 14px;font:500 18px/1.5 Mono;width:430px">HELD BY THE PUBLIC ${float(dn["debt_held_public_amt"]) / 1e12:.2f}T<br>INTRAGOVERNMENTAL ${float(dn["intragov_hold_amt"]) / 1e12:.2f}T</div>', 1380, 80, 1.4, "wipe", z=6)
S["06_debt"] = (body, f"background:{CRM}", "DATA: U.S. TREASURY, FISCAL DATA, 'DEBT TO THE PENNY' (FIRST BUSINESS DAY OF 2000, 2010, 2020; LATEST 12 NOV 2026)")

# 7 INDIA vs CHINA · census ledger: Mukta + Kalam, indigo / chalk / red pencil, crossover-ring motif
IND, CHB, RP = "#1F2A5A", "#8B8FA8", "#D64534"
pop = {}
for c, y, v in raw["pop"]:
    pop.setdefault(c, {})[int(y)] = v
yrs = sorted(set(pop["IND"]) & set(pop["CHN"]))
x0, x1, y0, y1 = 140, 1500, 960, 260
lo, hi = 0.4e9, 1.5e9
X = lambda y: x0 + (y - yrs[0]) / (yrs[-1] - yrs[0]) * (x1 - x0)
Y = lambda v: y0 - (v - lo) / (hi - lo) * (y0 - y1)
line = lambda c: "M" + " L".join(f"{X(y):.1f} {Y(pop[c][y]):.1f}" for y in yrs)
cx, cy = X(2021), Y(pop["IND"][2021])
chart = (f'<svg width="1920" height="1080"><g stroke="#cfcab9" stroke-width="1">' + "".join(f'<line x1="{x0}" x2="{x1}" y1="{Y(v):.0f}" y2="{Y(v):.0f}"/>' for v in (0.5e9, 1e9, 1.5e9)) + "</g>"
         f'<path d="{line("CHN")}" stroke="{CHB}" stroke-width="7" fill="none"/><path d="{line("IND")}" stroke="{IND}" stroke-width="9" fill="none"/>'
         f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="46" stroke="{RP}" stroke-width="6" fill="none"/></svg>')
body = EXTRA + el(chart, 0, 0, .2, "draw", z=3)
for v, lab in ((0.5e9, "0.5 bn"), (1e9, "1.0 bn"), (1.5e9, "1.5 bn")):
    body += el(f'<div style="font:500 18px Plex;color:#6b6b6b">{lab}</div>', 40, Y(v) - 12, 0, "pop", extra=STILL, z=4)
body += el(f'<div style="font:800 64px Mukta;color:{IND}">India</div>', 1530, Y(pop["IND"][yrs[-1]]) - 80, .8, "wipe", z=5)
body += el(f'<div style="font:800 64px Mukta;color:{CHB}">China</div>', 1530, Y(pop["CHN"][yrs[-1]]) + 0, .9, "wipe", z=5)
body += el(f'<div style="font:700 44px/1.1 Kalam;color:{RP};width:440px;text-align:right">2021: India passes China</div>', cx - 520, cy - 150, 1.2, "wipe", z=6)
body += el(f'<div style="font:800 58px Mukta;color:{IND}">The crossover</div><div style="font:500 20px Plex;color:#444">Population, {yrs[0]}–{yrs[-1]}, World Bank estimates</div>', 140, 60, .1, "wipe", z=5)
for y in (1960, 1980, 2000, 2020):
    body += el(f'<div style="font:500 18px Plex;color:#6b6b6b">{y}</div>', X(y) - 22, 975, 0, "pop", extra=STILL, z=4)
S["07_population"] = (body, "background:#F3F0E6", f"DATA: WORLD BANK, SP.POP.TOTL (UN WORLD POPULATION PROSPECTS BASED), CC BY 4.0 · 2021: INDIA {pop['IND'][2021] / 1e9:.3f} BN, CHINA {pop['CHN'][2021] / 1e9:.3f} BN")

# 8 CO2 · chart recorder: Archivo Black + JetBrains Mono, recorder green grid / pen violet, pen-trace motif
co2 = raw["co2"]
x0, x1, y0, y1 = 120, 1560, 960, 200
X = lambda y: x0 + (y - co2[0][0]) / (co2[-1][0] - co2[0][0]) * (x1 - x0)
Y = lambda v: y0 - (v - 300) / (440 - 300) * (y0 - y1)
grid = "background-image:linear-gradient(rgba(60,140,90,.35) 1px,transparent 1px),linear-gradient(90deg,rgba(60,140,90,.35) 1px,transparent 1px),linear-gradient(rgba(60,140,90,.18) 1px,transparent 1px),linear-gradient(90deg,rgba(60,140,90,.18) 1px,transparent 1px);background-size:100px 100px,100px 100px,20px 20px,20px 20px"
trace = "M" + " L".join(f"{X(y):.1f} {Y(v):.1f}" for y, v in co2)
body = EXTRA + el(f'<div style="width:1920px;height:1080px;{grid}"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
body += el(f'<svg width="1920" height="1080"><path d="{trace}" stroke="#5B2C83" stroke-width="7" fill="none" stroke-linecap="round"/></svg>', 0, 0, .2, "draw", z=4)
body += el(f'<div style="width:22px;height:22px;border-radius:50%;background:#5B2C83;box-shadow:0 0 0 6px rgba(91,44,131,.25)"></div>', X(co2[-1][0]) - 11, Y(co2[-1][1]) - 11, 1.4, "pop", z=5)
body += el(f'<div style="font:400 150px Archivo;color:#1b1b1b;line-height:.9">{co2[-1][1]:.0f}<span style="font-size:48px"> ppm</span></div><div style="font:700 22px Mono;color:#2c5e3f">CO₂ AT MAUNA LOA, ANNUAL MEAN, {co2[-1][0]}</div>', 1180, 700, 1.0, "wipe", z=6)
body += el(f'<div style="font:700 22px Mono;color:#2c5e3f">{co2[0][0]}: {co2[0][1]:.1f} PPM</div>', 120, Y(co2[0][1]) + 24, .3, "wipe", z=6)
body += el('<div style="font:400 58px Archivo;color:#1b1b1b">The pen has never turned down.</div>', 120, 70, .1, "wipe", z=6)
for v in (320, 360, 400, 440):
    body += el(f'<div style="font:700 18px Mono;color:#2c5e3f">{v} ppm</div>', 30, Y(v) - 12, 0, "pop", extra=STILL, z=6)
S["08_co2"] = (body, "background:#F4F7EE", "DATA: NOAA GLOBAL MONITORING LABORATORY, MAUNA LOA ANNUAL MEAN CO2 (CO2_ANNMEAN_MLO.TXT), FETCHED 14 NOV 2026")

# 9 NUCLEAR WARHEADS · dot census: Anton + DM Mono, charcoal / bone / alert orange, one-dot-per-warhead motif
groups = [(2100, "#FF6B1A", "ON HIGH ALERT ≈2,100"), (3912 - 2100, "#F2EEE6", "DEPLOYED 3,912"), (9745 - 3912, "#8E8A82", "MILITARY STOCKPILES 9,745"), (12187 - 9745, "#3A3936", "RETIRED, AWAITING DISMANTLEMENT")]
js = ("<canvas id='c' width='1120' height='900'></canvas><script>(function(){var c=document.getElementById('c').getContext('2d');"
      f"var g={json.dumps([[n, col] for n, col, _ in groups])};var i=0,cols=140,p=8;"
      "g.forEach(function(x){for(var k=0;k<x[0];k++){var r=Math.floor(i/cols),q=i%cols;c.fillStyle=x[1];c.beginPath();c.arc(q*p+4,r*p+4,2.6,0,6.3);c.fill();i++;}});})();</script>")
body = EXTRA + el(js, 760, 110, 0, "pop", extra=STILL, z=4)
body += el('<div style="font:400 150px/0.9 Anton;color:#F2EEE6">12,187</div><div style="font:500 22px DMono;color:#bdb8ad;letter-spacing:2px;margin-top:10px">NUCLEAR WARHEADS<br>NINE COUNTRIES · START OF 2026<br>ONE DOT = ONE WARHEAD</div>', 90, 120, .2, "wipe", z=6)
leg = "".join(f'<div style="display:flex;align-items:center;gap:14px;margin:10px 0"><div style="width:22px;height:22px;border-radius:50%;background:{col}"></div><div style="font:500 22px DMono;color:#e8e3d8">{lab}</div></div>' for _, col, lab in groups)
body += el(leg, 90, 520, .6, "wipe", z=6)
body += el('<div style="font:500 20px DMono;color:#FF6B1A;width:540px">THE UNITED STATES AND RUSSIA HOLD ≈86% OF THE TOTAL</div>', 90, 820, 1.0, "wipe", z=6)
S["09_nuclear"] = (body, "background:#17181A", "ESTIMATES: FEDERATION OF AMERICAN SCIENTISTS, STATUS OF WORLD NUCLEAR FORCES 2026 (KRISTENSEN, KORDA, JOHNS, KNIGHT-BOYLE) · COUNTS ARE ESTIMATES")

# 10 MILITARY SPENDING · war-room table: Oswald + Inter, slate navy / brass, proportional-disc motif
rows = json.load(open(DATA / "milex_countries.json"))
d, P = world_path(-170, 190, -58, 82, 1920, 940, skip=("Antarctica",))
discs = ""
for iso, yr, v, name, la, lo in rows[:40]:
    x, y = P(lo, la)
    r = math.sqrt(v / 1004.9e9) * 150
    discs += f'<circle cx="{x:.0f}" cy="{y + 70:.0f}" r="{max(r, 3):.1f}" fill="#C9A24A" fill-opacity=".78" stroke="#F5E3B0" stroke-width="1.5"/>'
body = EXTRA + el(f'<svg width="1920" height="1080"><g transform="translate(0,70)"><path d="{d}" fill="#26344A" stroke="#3B4C66" stroke-width="1"/></g>{discs}</svg>', 0, 0, 0, "pop", extra=STILL, z=2)
labels = {"USA": (-330, -40), "CHN": (110, -60), "RUS": (100, -40), "GBR": (-330, -40), "IND": (-40, 70), "DEU": (-20, -120)}
for iso, yr, v, name, la, lo in rows[:8]:
    if iso in labels:
        x, y = P(lo, la)
        dx, dy = labels[iso]
        nm = {"Russian Federation": "Russia"}.get(name, name)
        body += el(f'<div style="font:600 30px Oswald;color:#F5E3B0;white-space:nowrap;text-shadow:0 2px 6px #000">{nm} <span style="font:600 26px Inter;color:#fff">${v / 1e9:,.1f} bn</span></div>', x + dx, y + 70 + dy, .5, "pop", z=6)
world = json.load(open(DATA / "milex.json"))["WLD"]
body += el(f'<div style="font:600 64px Oswald;color:#fff">Who spends on armies</div><div style="font:600 22px Inter;color:#C9A24A">{world[0]} · WORLD TOTAL ${world[1] / 1e12:.2f} TRILLION · DISC AREA = SPENDING</div>', 60, 20, .1, "wipe", z=7)
S["10_milex"] = (body, "background:#141C28", "DATA: WORLD BANK, MS.MIL.XPND.CD (FROM SIPRI), CC BY 4.0 · DISCS AT CAPITAL CITIES · MAP: NATURAL EARTH")

if __name__ == "__main__":
    out = D / "html"
    out.mkdir(exist_ok=True)
    for k, (body, bg, cr) in S.items():
        (out / f"{k}.html").write_text(K.page(body, bg, 5, .03, cr), encoding="utf-8")
    print(len(S))
