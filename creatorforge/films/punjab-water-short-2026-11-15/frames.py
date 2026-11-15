"""Key frames (9:16, 1080x1920) for the Punjab groundwater Short, one per beat of SCRIPT_PLAN.md.
Every number comes from dossier.json (2025 national assessment unless the frame says otherwise)."""
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
sys.path.insert(0, "/home/user/Forgeos/creatorforge/films/taxonomy-2026-11-15")
import relief                                   # noqa: E402
from taxonomy import icon                       # noqa: E402

H = D / "html"
H.mkdir(exist_ok=True)
SIG, RED, NAVY, PAPER, INK = "#FFDD33", "#C8312B", "#1F2A44", "#F3EEDF", "#1C1C1C"
FONTS = "".join(f"@font-face{{font-family:{n};src:url(/fonts/{f}.woff2)}}" for n, f in (
    ("Anton", "anton-latin-400-normal"), ("Plex", "ibm-plex-mono-latin-500-normal"), ("Caveat", "caveat-latin-700-normal"),
    ("Playfair", "playfair-display-latin-900-normal"), ("ISerif", "instrument-serif-latin-400-italic"), ("Grotesk", "space-grotesk-latin-700-normal")))
GRAIN = ('<svg style="position:absolute;inset:0;pointer-events:none;opacity:.28;mix-blend-mode:multiply" width="1080" height="1920"><filter id="g">'
         '<feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3"/><feColorMatrix values="0 0 0 0 .4 0 0 0 0 .35 0 0 0 0 .3 0 0 0 .5 0"/></filter>'
         '<rect width="1080" height="1920" filter="url(#g)"/></svg>')
SAFE_TOP, SAFE_BOTTOM = 220, 1560          # Shorts UI: keep words between these lines


def page(body, bg=PAPER, src="", dark=False):
    col = "rgba(255,255,255,.62)" if dark else "rgba(20,20,20,.6)"
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:{bg};position:relative}}'
            f'.a{{position:absolute}}</style></head><body>{body}{GRAIN}'
            f'<div class="a" style="left:0;right:0;top:1574px;padding:16px 40px;{"background:linear-gradient(transparent,rgba(0,0,0,.78) 30%)" if dark else ""};font:500 17px/1.5 Plex;letter-spacing:1px;color:{col}">{src}</div>'
            '<script>document.fonts.ready.then(()=>window.READY=true)</script></body></html>')


def a(html, x, y, extra=""):
    return f'<div class="a" style="left:{x}px;top:{y}px;{extra}">{html}</div>'


def kick(t, x=70, y=SAFE_TOP, col=INK):
    return a(f'<div style="font:500 24px Plex;letter-spacing:5px;color:{col}">{t}</div>', x, y)


def put(name, html):
    (H / f"{name}.html").write_text(html, encoding="utf-8")


SRC25 = "SOURCE: DYNAMIC GROUND WATER RESOURCE ASSESSMENT 2025, MINISTRY OF JAL SHAKTI / CGWB, AS REPORTED IN PARLIAMENT REPLIES AND PIB"

# 01 the statement over a real photo of water being drawn
stamp = (f'<div style="border:8px solid {RED};color:{RED};font:400 92px/1 Anton;letter-spacing:6px;padding:8px 26px;transform:rotate(-12deg);opacity:.9;'
         f'mix-blend-mode:multiply">OVERDRAWN</div>')
rows = "".join(f'<div style="display:flex;justify-content:space-between;border-bottom:2px dashed #B9AE95;padding:18px 0;font:500 30px Plex;color:{INK}">'
               f'<span>{k}</span><span style="{st}">{v}</span></div>' for k, v, st in (
                   ("Safe yearly withdrawal", "16.80 BCM", ""), ("Actual yearly withdrawal", "26.27 BCM", f"color:{RED}"),
                   ("Share of safe limit used", "156.36 %", f"background:linear-gradient(transparent 50%,{SIG} 50%,{SIG} 92%,transparent 92%)")))
stmt = (f'<div style="width:880px;background:{PAPER};padding:46px 50px 40px;box-shadow:0 30px 60px rgba(0,0,0,.55);transform:rotate(-2deg)">'
        f'<div style="font:500 20px Plex;letter-spacing:5px;color:#7A6A4A">STATEMENT OF ACCOUNT · 2025</div>'
        f'<div style="font:400 74px/1 Anton;color:{NAVY};margin:14px 0 22px">PUNJAB · GROUNDWATER</div>{rows}'
        f'<div style="font:500 17px/1.5 Plex;color:#7A6A4A;margin-top:22px">Figures from the 2025 national assessment. Statement laid out in the studio.</div></div>')
put("01_statement", page(
    a('<img src="/assets/pipe.jpg" style="width:1080px;height:1920px;object-fit:cover;filter:brightness(.55) contrast(1.1)">', 0, 0)
    + a(f'<div style="font:400 112px/0.95 Anton;color:#F3EFE6;width:940px">PUNJAB\'S WATER<br>BANK STATEMENT</div>', 70, SAFE_TOP)
    + a(stmt, 100, 640) + a(stamp, 520, 1140),
    "#000", SRC25 + " · PHOTO: PIXABAY", dark=True))

# 02 deposits vs withdrawals, bars from zero
top, base, k = 560, 1440, 880 / 26.27 * .95
dep, wd = 16.80 * k, 26.27 * k
bars = (a(f'<div style="width:300px;height:{dep:.0f}px;background:{NAVY}"></div>', 150, base - dep)
        + a(f'<div style="width:300px;height:{wd:.0f}px;background:{RED}"></div>', 620, base - wd)
        + a(f'<div style="width:300px;text-align:center;font:400 84px Anton;color:{NAVY}">16.80</div>', 150, base - dep - 110)
        + a(f'<div style="width:300px;text-align:center;font:400 84px Anton;color:{RED}">26.27</div>', 620, base - wd - 110)
        + a(f'<div style="width:300px;text-align:center;font:500 26px Plex;letter-spacing:4px;color:{INK}">PUT BACK<br><span style="font-size:18px">safe to draw</span></div>', 150, base + 20)
        + a(f'<div style="width:300px;text-align:center;font:500 26px Plex;letter-spacing:4px;color:{INK}">TAKEN OUT<br><span style="font-size:18px">drawn each year</span></div>', 620, base + 20)
        + a(f'<div style="width:880px;height:4px;background:{INK}"></div>', 100, base)
        + a(f'<div style="border-top:4px dashed {NAVY};width:470px"></div>', 470, base - dep)
        + a(f'<div style="font:700 50px Caveat;color:{RED};transform:rotate(-4deg)">− 9.47 billion m³<br>every year</div>', 640, base - wd - 330))
lines = "".join(f'<div style="position:absolute;left:0;right:0;top:{y}px;border-top:1px solid #D7CDB4"></div>' for y in range(0, 1920, 58))
put("02_columns", page(a(lines, 0, 0, "width:1080px;height:1920px") + a(f'<div style="width:6px;height:1920px;background:#E7A9A3"></div>', 90, 0)
                       + kick("PASSBOOK · BILLION CUBIC METRES A YEAR", 130) + a(f'<div style="font:400 104px/0.95 Anton;color:{NAVY};width:900px">IN · OUT</div>', 126, 270) + bars,
                       PAPER, SRC25 + " · BARS FROM ZERO"))

# 03 the glowing number and the ranking
rank = "".join(a(f'<div style="display:flex;align-items:center;gap:22px"><div style="width:250px;font:500 30px Plex;color:{"#FFF" if i == 0 else "#9AA0AA"};text-align:right">{n}</div>'
                 f'<div style="width:{v * 3.6:.0f}px;height:54px;background:{SIG if i == 0 else "#3A3F4B"};box-shadow:{"0 0 30px rgba(255,221,51,.7)" if i == 0 else "none"}"></div>'
                 f'<div style="font:400 44px Anton;color:{SIG if i == 0 else "#C9CDD6"}">{v:.0f}%</div></div>', 40, 1040 + i * 110)
               for i, (n, v) in enumerate((("PUNJAB", 156.36), ("RAJASTHAN", 147.11), ("HARYANA", 136.75))))
put("03_glow", page(kick("SHARE OF THE SAFE LIMIT USED, 2025", 70, SAFE_TOP, "#9AA0AA")
                    + a(f'<div style="font:400 330px/1 Anton;color:{SIG};text-shadow:0 0 40px rgba(255,221,51,.65),0 0 120px rgba(255,180,0,.35)">156%</div>', 60, 330)
                    + a('<div style="font:400 64px/1.05 ISerif;color:#E8E4DA;width:900px">the highest of any state</div>', 74, 760)
                    + a('<div style="border-top:2px dashed #555;width:540px"></div>', 312, 1020) + a('<div style="font:500 18px Plex;color:#777">100% = SAFE LIMIT</div>', 312 + 360, 990)
                    + rank, "#07080C", SRC25 + " · BARS FROM ZERO", dark=True))

# 05 satellite with GRACE readout and India's official outline
from creatorforge_worker.media import maps  # noqa: E402
box = (67, 21, 81, 35)
P = lambda lo, la: ((lo - box[0]) / (box[2] - box[0]) * 1080, (box[3] - la) / (box[3] - box[1]) * 1080)
ind = "".join('<path d="M' + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + 'Z" fill="none" stroke="#FFFFFF" stroke-width="2.5" opacity=".85"/>'
              for r in maps._find("India")["rings"] if len(r) > 3)
hud = "".join(f'<div style="font:500 20px Plex;letter-spacing:3px;color:#9FD3C7;margin-top:18px">{k}</div><div style="font:500 34px Plex;color:#EAF6F2">{v}</div>'
              for k, v in (("MISSION", "NASA GRACE"), ("PERIOD", "AUG 2002 – OCT 2008"), ("STUDY AREA", "RAJASTHAN, PUNJAB,<br>HARYANA, DELHI"), ("LOST", "109 km³")))
put("05_orbit", page(a('<img src="/maps/nw_india.jpg" style="width:1080px;height:1080px;object-fit:cover;filter:saturate(.95) contrast(1.1) brightness(.85)">', 0, 420)
                     + a(f'<svg width="1080" height="1080">{ind}<circle cx="{P(75.3, 30.9)[0]:.0f}" cy="{P(75.3, 30.9)[1]:.0f}" r="20" fill="none" stroke="{SIG}" stroke-width="5"/></svg>', 0, 420)
                     + a(f'<div style="background:{SIG};color:#111;font:500 22px Plex;letter-spacing:3px;padding:6px 12px">PUNJAB</div>', P(75.3, 30.9)[0] + 30, 420 + P(75.3, 30.9)[1] - 20)
                     + a(f'<div style="font:400 96px/0.95 Anton;color:#F3EFE6;width:960px">SEEN FROM ORBIT</div>', 70, SAFE_TOP)
                     + a(f'<div style="background:rgba(5,15,14,.82);border:2px solid #2E6F64;padding:20px 30px 26px;width:600px">{hud}</div>', 70, 1110)
                     + a('<div style="font:400 140px/1 Anton;color:#FFDD33;text-shadow:0 0 30px rgba(255,221,51,.6)">−109 km³</div>', 470, 1450 - 40, "display:none"),
                     "#030405", "DATA: RODELL, VELICOGNA &amp; FAMIGLIETTI, NATURE 460, 999–1002 (2009) · IMAGERY: NASA BLUE MARBLE NG VIA GIBS (PUBLIC DOMAIN) · INDIA: OFFICIAL BOUNDARY",
                     dark=True))

# 06 a sack of paddy and the water behind one kilo: 30 buckets of 100 litres
bk = "".join(a(icon("bucket", 66, "#2F6FB5", 1.8), 120 + (i % 6) * 140, 1075 + (i // 6) * 88) for i in range(30))
put("06_litres", page(kick("ONE KILO OF PADDY", 70, SAFE_TOP)
                      + a(f'<div style="font:400 210px/0.9 Anton;color:{NAVY}">~3,000</div><div style="font:400 64px/1 Anton;color:{NAVY}">LITRES OF WATER</div>', 66, 270)
                      + a('<img src="/assets/ricesack.png" style="width:420px;transform:rotate(4deg);filter:drop-shadow(0 20px 22px rgba(0,0,0,.35))">', 600, 600)
                      + bk + a('<div style="font:700 44px Caveat;color:#2F6FB5">each bucket = 100 litres</div>', 130, 1512)
                      + a(f'<div style="font:500 20px/1.5 Plex;color:#555;width:900px">ICAR estimate for flooded paddy: ~3,333 L/kg; other estimates range from about 1,500 to 4,500.</div>', 70, 950),
                      "#F1ECE0", "SOURCE: INDIAN FARMING (ICAR) · PHOTO: PIXABAY"))

# 07 why: the chain on a chalkboard
chalk = "#ECEADF"
nodes = [("bolt", "FREE POWER", "for farm pumps, since 1997", 140, 470), ("droplet", "PUMPS RUN", "water drawn from below", 560, 690),
         ("plant", "PADDY", "the thirstiest crop", 140, 910), ("building-bank", "GOVT BUYS IT", "at a fixed price (MSP)", 560, 1130), ("repeat", "MORE PADDY", "next season", 140, 1350)]
nd = ""
for i, (ic, t, s, x, y) in enumerate(nodes):
    hot = t == "GOVT BUYS IT" or t == "FREE POWER"
    nd += a(f'<div style="display:flex;gap:18px;align-items:center;border:3px solid {chalk};padding:16px 22px;width:340px;background:rgba(255,255,255,.04)">{icon(ic, 58, SIG if hot else chalk, 1.6)}'
            f'<div><div style="font:400 40px/1 Anton;color:{SIG if hot else chalk}">{t}</div><div style="font:700 28px Caveat;color:#CFCBBF">{s}</div></div></div>', x, y)
arrows = "".join(f'<path d="M{x1 + 200} {y1 + 120} Q {(x1 + x2) / 2 + 230} {(y1 + y2) / 2 + 60} {x2 + 200} {y2 - 6}" fill="none" stroke="{chalk}" stroke-width="4" stroke-dasharray="14 10"/>'
                 for (_, _, _, x1, y1), (_, _, _, x2, y2) in zip(nodes, nodes[1:]))
board = "background:#22302A;background-image:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1.5px);background-size:6px 6px"
put("07_chain", page(a(f'<div style="width:1080px;height:1920px;{board}"></div>', 0, 0) + a(f'<svg width="1080" height="1920">{arrows}</svg>', 0, 0) + nd
                     + a(f'<div style="font:400 100px/0.95 Anton;color:{chalk};width:940px">WHY KEEP<br>WITHDRAWING?</div>', 70, SAFE_TOP - 10),
                     "#22302A", "SOURCES: TRIBUNE EXPLAINERS ON PUNJAB'S FARM-POWER SUBSIDY; CENTRE'S PADDY PROCUREMENT RELEASES · DIAGRAM DRAWN IN THE STUDIO, SIMPLIFIED", dark=True))

# 08 the farmers' side: two ledger cards
card = lambda t, l1, l2, col, rot: (f'<div style="width:430px;background:#FBF8F0;padding:26px 28px;box-shadow:0 18px 30px rgba(0,0,0,.25);transform:rotate({rot}deg);'
                                    f'background-image:repeating-linear-gradient(0deg,transparent 0 45px,#D9E3F2 45px 46px)"><div style="font:400 58px/1 Anton;color:{col}">{t}</div>'
                                    f'<div style="font:700 40px/1.2 Caveat;color:{INK};margin-top:14px">{l1}</div><div style="font:700 34px/1.2 Caveat;color:#555;margin-top:10px">{l2}</div></div>')
put("08_farmers", page(a(f'<div style="background:{NAVY};color:#fff;font:500 24px Plex;letter-spacing:5px;padding:10px 18px">THE FARMERS\' SIDE</div>', 70, SAFE_TOP)
                       + a(f'<div style="font:400 104px/0.95 Anton;color:{NAVY};width:900px">THE SAFEST BET</div>', 66, 300)
                       + a(card("PADDY", "a buyer is all but guaranteed", "govt procurement at MSP", "#2E7D32", -3), 70, 560)
                       + a(card("MAIZE", "often sold below its support price", "few assured buyers", RED, 3), 560, 640)
                       + a('<img src="/assets/corn.png" style="width:560px;transform:rotate(-14deg);filter:drop-shadow(0 20px 20px rgba(0,0,0,.3))">', 420, 1080)
                       + a('<img src="/assets/ricesack.png" style="width:380px;filter:drop-shadow(0 20px 20px rgba(0,0,0,.3))">', 60, 1080),
                       "#EFE9DC", "SOURCES: MONGABAY INDIA (2023); DOWN TO EARTH ON ICAR'S 2021 POLICY PAPER; THE WIRE · PHOTOS: PIXABAY"))

# 09 the trend: stage of extraction 2017-2025
pts = [(2017, 165.77), (2020, 164.42), (2022, 165.99), (2023, 163.76), (2024, 156.87), (2025, 156.36)]
X = lambda y: 120 + (y - 2017) / 8 * 840
Y = lambda v: 1300 - (v - 0) / 180 * 700
path = "M" + " L".join(f"{X(y):.0f} {Y(v):.0f}" for y, v in pts)
dots = "".join(f'<circle cx="{X(y):.0f}" cy="{Y(v):.0f}" r="{12 if y >= 2023 else 9}" fill="{SIG if y >= 2023 else NAVY}" stroke="{NAVY}" stroke-width="3"/>'
               f'<text x="{X(y):.0f}" y="{Y(v) - 28:.0f}" text-anchor="middle" font-family="Plex" font-size="26" fill="{INK}">{v:.0f}%</text>'
               f'<text x="{X(y):.0f}" y="1350" text-anchor="middle" font-family="Plex" font-size="24" fill="#666">{y}</text>' for y, v in pts)
grid = (f'<line x1="120" y1="{Y(100):.0f}" x2="960" y2="{Y(100):.0f}" stroke="#2E7D32" stroke-width="3" stroke-dasharray="12 8"/>'
        f'<text x="960" y="{Y(100) + 40:.0f}" text-anchor="end" font-family="Plex" font-size="22" fill="#2E7D32">100% = SAFE LIMIT</text>'
        f'<line x1="120" y1="1300" x2="960" y2="1300" stroke="{INK}" stroke-width="3"/>')
put("09_trend", page(a('<img src="/assets/canal.jpg" style="width:1080px;height:420px;object-fit:cover;filter:saturate(.9)">', 0, 1440 - 40, "display:none")
                     + kick("SHARE OF THE SAFE LIMIT USED, PUNJAB", 70, SAFE_TOP)
                     + a(f'<div style="font:400 100px/0.95 Anton;color:{NAVY};width:940px">SHRINKING,<br>SLOWLY</div>', 66, 270)
                     + a(f'<svg width="1080" height="1920"><path d="{path}" fill="none" stroke="{NAVY}" stroke-width="7"/>{grid}{dots}</svg>', 0, 0)
                     + a(f'<div style="font:700 46px Caveat;color:{RED};transform:rotate(-3deg)">canals now water more fields</div>', 470, Y(156) + 60),
                     PAPER, "SOURCES: CGWB ASSESSMENTS 2017–2024 (VIA RBI HANDBOOK OF STATISTICS ON INDIAN STATES; CGWB PUNJAB 2024 REPORT); 2025 NATIONAL ASSESSMENT · AXIS FROM ZERO"))

# 10 the warning, attributed, over cracked earth
quote = (f'<div style="width:880px;background:#F7F2E6;padding:44px 48px;box-shadow:0 26px 50px rgba(0,0,0,.5);transform:rotate(1.5deg)">'
         f'<div style="font:400 58px/1.15 Playfair;color:{INK}">“Punjab will be rendered a desert within 25 years if the exploitation of its underground water resources continues at the current rate.”</div>'
         f'<div style="font:500 22px/1.5 Plex;letter-spacing:2px;color:#6B5B3A;margin-top:26px">— 2019 DRAFT REPORT, CENTRAL GROUND WATER BOARD, NORTH-WESTERN REGION, AS REPORTED BY THE TRIBUNE AND MONGABAY</div></div>')
put("10_warning", page(a('<img src="/assets/cracked.jpg" style="width:1080px;height:1920px;object-fit:cover;filter:sepia(.3) brightness(.7)">', 0, 0)
                       + a(f'<div style="font:400 100px/0.95 Anton;color:#F3EFE6;width:940px">THE WARNING</div>', 70, SAFE_TOP) + a(quote, 100, 520)
                       + a(f'<div style="border:6px solid {RED};color:{RED};background:rgba(247,242,230,.85);font:400 70px/1 Anton;letter-spacing:6px;padding:6px 22px;transform:rotate(-10deg)">DRAFT</div>', 640, 1230),
                       "#000", "QUOTE AS REPORTED: THE TRIBUNE (2019), MONGABAY INDIA (2019) · A DRAFT, NOT A FINAL REPORT · PHOTO: PIXABAY", dark=True))

# 11 the tubewell cutaway: the water table steps down, the pipe gets longer
lay = "".join(f'<rect x="0" y="{y}" width="1080" height="{h}" fill="{c}"/>' for y, h, c in ((560, 180, "#8B6B45"), (740, 300, "#A9875C"), (1040, 560, "#7B5E3E")))
wt = "".join(f'<line x1="0" y1="{y}" x2="1080" y2="{y}" stroke="#4FA3E0" stroke-width="{6 if i == 3 else 3}" stroke-dasharray="{"none" if i == 3 else "16 10"}" opacity="{1 if i == 3 else .55}"/>'
             f'<text x="1040" y="{y - 12}" text-anchor="end" font-family="Plex" font-size="24" fill="#DDEEFF">{lab}</text>'
             for i, (y, lab) in enumerate(((820, "water table, earlier"), (930, ""), (1040, ""), (1150, "water table, later"))))
water = '<rect x="0" y="1150" width="1080" height="450" fill="#2F6FB5" opacity=".45"/>'
pipe = (f'<rect x="510" y="440" width="60" height="760" fill="#9AA3AD" stroke="#4A525A" stroke-width="4"/><rect x="440" y="440" width="200" height="90" rx="10" fill="{NAVY}"/>'
        f'<text x="540" y="498" text-anchor="middle" font-family="Anton" font-size="40" fill="#fff">PUMP</text>'
        f'<rect x="510" y="1040" width="60" height="160" fill="{SIG}" stroke="#4A525A" stroke-width="4"/>')
steps = "".join(f'<path d="M300 {y1} L300 {y2}" stroke="{RED}" stroke-width="5" marker-end="url(#ah)"/>' for y1, y2 in ((830, 915), (940, 1025), (1050, 1135)))
put("11_tubewell", page(a(f'<svg width="1080" height="1920"><defs><marker id="ah" markerWidth="12" markerHeight="12" refX="6" refY="6" orient="auto"><path d="M0 0 L12 6 L0 12" fill="{RED}"/></marker></defs>'
                          f'<rect x="0" y="0" width="1080" height="560" fill="#E9E1CF"/><rect x="0" y="540" width="1080" height="24" fill="#5E8C3A"/>{lay}{water}{wt}{steps}{pipe}</svg>', 0, 0)
                        + a(f'<div style="font:400 100px/0.95 Anton;color:{NAVY};width:940px">DEEPER<br>EVERY YEAR</div>', 70, SAFE_TOP)
                        + a(f'<div style="font:700 50px Caveat;color:{RED}">~0.5 m a year</div>', 330, 940)
                        + a(f'<div style="font:700 36px Caveat;color:#FFF;width:380px">the pipe has to reach further</div>', 610, 1210),
                        PAPER, "RATE: CGWB DATA TO 2017 (≈0.49 M/YR); PAU STUDY 1988–2016 (≈51 CM/YR) · CUTAWAY DRAWN IN THE STUDIO, NOT TO SCALE"))

# 12 end card: the closed passbook
put("12_end", page(a(f'<div style="width:760px;height:980px;background:{NAVY};border-radius:18px;box-shadow:0 40px 80px rgba(0,0,0,.6);transform:rotate(-3deg)">'
                     f'<div style="padding:70px 60px"><div style="font:500 24px Plex;letter-spacing:6px;color:#C9D2E8">PASSBOOK</div>'
                     f'<div style="font:400 92px/0.95 Anton;color:#F3EFE6;margin-top:16px">PUNJAB<br>GROUNDWATER</div>'
                     f'<div style="margin-top:300px;font:500 26px Plex;letter-spacing:5px;color:#C9D2E8">CLOSING BALANCE</div>'
                     f'<div style="font:400 200px/1 Anton;color:{SIG};text-shadow:0 0 40px rgba(255,221,51,.5)">?</div></div></div>', 160, 300)
                   + a(f'<div style="font:400 60px/1.15 ISerif;color:#F3EFE6;width:940px;text-align:center">A bank allows an overdraft.<br>An aquifer doesn\'t.</div>', 70, 1320)
                   + a(f'<div style="background:{SIG};color:#111;font:400 50px/1.1 Anton;padding:14px 26px;text-align:center;width:880px">WHAT SHOULD PUNJAB GROW INSTEAD?</div>', 76, 1470),
                   "#0E1220", "PRINT FACTS · SOURCES IN THE DESCRIPTION", dark=True))

# 04 relief of Punjab (lit) + 153 blocks, 111 over-exploited (unit grid, not placed on the map)
card = lambda t, s: (f'<div style="background:#EFE6D2;padding:10px 16px;box-shadow:0 12px 20px rgba(0,0,0,.6);text-align:center">'
                     f'<div style="font:400 34px/1 Anton;color:#141414">{t}</div><div style="font:500 14px Plex;letter-spacing:3px;color:#7A2A20;margin-top:4px">{s}</div></div>')
grid153 = "".join(f'<div style="position:absolute;left:{(i % 17) * 56}px;top:{(i // 17) * 56}px;width:44px;height:44px;background:{RED if i < 111 else "#3A3F4B"};'
                  f'{"box-shadow:0 0 12px rgba(200,49,43,.7)" if i < 111 else ""}"></div>' for i in range(153))
cfg = {"exag": 5, "base": "#24282E", "hot": "#C8312B", "peak": "#FF8A7A", "grid": "#3A1010", "line": "#FFFFFF", "fog": [120, 300], "bg": "#05060A",
       "bloom": [0.5, 0.4, 0.62], "glow": 0.8, "cam": [0, 120, 80], "look": [0, 0, 20], "fov": 34, "route": [],
       "pins": [{"lon": 75.85, "lat": 30.9, "html": card("LUDHIANA", "PUNJAB")}],
       "overlay": f'<div style="position:absolute;left:70px;top:{SAFE_TOP}px"><div style="font:400 100px/0.95 Anton;color:#F3EFE6;width:940px">111 OF 153<br>BLOCKS OVERDRAWN</div></div>'
                  f'<div style="position:absolute;left:70px;top:1100px;width:960px;height:500px">{grid153}</div>'
                  f'<div style="position:absolute;left:70px;top:1480px;font:500 20px Plex;letter-spacing:2px;color:#C9CDD6">ONE SQUARE = ONE ASSESSMENT BLOCK · RED = OVER-EXPLOITED · SQUARES NOT PLACED ON THE MAP</div>'
                  f'<div style="position:absolute;left:40px;right:40px;top:1590px;font:500 17px/1.5 Plex;letter-spacing:1px;color:rgba(255,255,255,.6)">{SRC25} · PUNJAB LIT ON REAL TERRAIN (TERRARIUM TILES, SRTM; HEIGHTS EXAGGERATED 5×) · STATE BOUNDARY: NATURAL EARTH</div>'}
html = relief.page("punjab", cfg)
html = html.replace("1920", "__W__").replace("1080", "1920").replace("__W__", "1080")
put("04_blocks", html)
print(sorted(p.name for p in H.iterdir()))
