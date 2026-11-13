"""The Machine, as collage stills (the owner's reference styles: scrapbook build, map desk, editorial poster).

Real material only: credited GODL-India photos of public figures as halftone cut-outs, the parties' public-domain
symbols, platform logos (Simple Icons, CC0; trademarks of their owners, used to identify the platforms), the India
outline from DataMeet (CC BY 4.0, official boundary), and torn scraps of the real source pages. Nothing generated.
"""
import json, math, random
from pathlib import Path

D = Path(__file__).resolve().parent
F = D.parent
A = D / "assets"
SI = Path("/tmp/claude-0/-home-user-Forgeos/4511f341-cf91-5fed-ac10-e7043335b256/scratchpad/bjpc/si/package")
FONTS = Path("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts")
PAPER, INK, RED, SIG, CREAM = "#E9E0CC", "#141414", "#D63A2B", "#FFDD33", "#F4EEDF"
ICONS = {d["slug"] if "slug" in d else d["title"].lower(): d for d in json.load(open(SI / "data/simple-icons.json"))}


def icon(slug, size, col=None):
    svgtxt = (SI / "icons" / f"{slug}.svg").read_text()
    path = svgtxt.split(' d="')[1].split('"')[0]
    hexc = col or "#" + next((d["hex"] for d in ICONS.values() if d.get("slug", d["title"].lower().replace(" ", "")) == slug or d["title"].lower() == slug), "000000")
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24"><path d="{path}" fill="{hexc}"/></svg>'


HEAD = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Anton;src:url({(FONTS / 'anton-latin-400-normal.woff2').as_uri()})}}
@font-face{{font-family:Oswald;src:url({(FONTS / 'oswald-latin-600-normal.woff2').as_uri()})}}
@font-face{{font-family:Marker;src:url({(FONTS / 'permanent-marker-latin-400-normal.woff2').as_uri()})}}
@font-face{{font-family:Playfair;src:url({(FONTS / 'playfair-display-latin-900-normal.woff2').as_uri()})}}
@font-face{{font-family:Archivo;src:url({(FONTS / 'archivo-black-latin-400-normal.woff2').as_uri()})}}
@font-face{{font-family:Bebas;src:url({(FONTS / 'bebas-neue-latin-400-normal.woff2').as_uri()})}}
@font-face{{font-family:Mono;src:url({(FONTS / 'jetbrains-mono-latin-700-normal.woff2').as_uri()})}}
@font-face{{font-family:Serif;src:url({(FONTS / 'dm-serif-display-latin-400-normal.woff2').as_uri()})}}
body{{margin:0;width:1920px;height:1080px;overflow:hidden;font-family:Oswald;color:{INK}}}
.a{{position:absolute}}
.ledger{{background:{PAPER};background-image:repeating-linear-gradient(0deg,transparent 0 46px,rgba(40,80,120,.16) 46px 48px),linear-gradient(90deg,transparent 0 120px,rgba(200,60,50,.35) 120px 123px,transparent 123px)}}
.tag{{font-family:Anton;letter-spacing:1px;text-transform:uppercase;padding:6px 18px 4px;white-space:nowrap}}
.stamp{{font-family:Bebas;letter-spacing:6px;border:7px solid {RED};color:{RED};padding:4px 22px 0;mix-blend-mode:multiply;opacity:.92}}
.chip{{font-family:Mono;font-size:20px;letter-spacing:3px;padding:6px 12px;color:#fff;white-space:nowrap}}
.marker{{font-family:Marker;white-space:nowrap}}
.credit{{position:absolute;left:24px;bottom:12px;font:600 12px Mono;letter-spacing:1px;color:rgba(20,20,20,.62);text-transform:uppercase;max-width:1860px}}
.tape{{position:absolute;width:150px;height:44px;background:rgba(244,232,170,.82);box-shadow:0 1px 2px rgba(0,0,0,.15)}}
</style></head><body class="{{cls}}" style="{{bg}}"><svg width="0" height="0" style="position:absolute">
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="3" seed="9"/><feColorMatrix values="0 0 0 0 .3  0 0 0 0 .26  0 0 0 0 .2  0 0 0 .38 0"/></filter>
<filter id="rough"><feTurbulence type="fractalNoise" baseFrequency=".04" numOctaves="4" seed="3"/><feDisplacementMap in="SourceGraphic" scale="14"/></filter>
<filter id="halftone"><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncR type="discrete" tableValues="0 .25 .55 .85 1"/><feFuncG type="discrete" tableValues="0 .25 .55 .85 1"/><feFuncB type="discrete" tableValues="0 .25 .55 .85 1"/></feComponentTransfer></filter>
</svg>"""
TAIL = """<svg class="a" style="inset:0;pointer-events:none;opacity:.55" width="1920" height="1080"><rect width="1920" height="1080" filter="url(#grain)"/></svg>
<div class="a" style="inset:0;pointer-events:none;background:radial-gradient(ellipse at 50% 50%,transparent 55%,rgba(30,20,10,.35) 100%)"></div>{credit}</body></html>"""


def torn_clip(seed, jag=14, steps=26):
    """A clip-path polygon with torn edges (percentages)."""
    r = random.Random(seed)
    pts = []
    for i in range(steps + 1):
        pts.append((i / steps * 100, r.uniform(0, jag / 10)))
    for i in range(steps + 1):
        pts.append((100 - r.uniform(0, jag / 10), i / steps * 100))
    for i in range(steps, -1, -1):
        pts.append((i / steps * 100, 100 - r.uniform(0, jag / 10)))
    for i in range(steps, -1, -1):
        pts.append((r.uniform(0, jag / 10), i / steps * 100))
    return "polygon(" + ",".join(f"{x:.1f}% {y:.1f}%" for x, y in pts) + ")"


def scrap(img, x, y, w, rot=0, crop=1.0, seed=1, gray=True, z=1, shadow=True):
    """A torn scrap of a real source page (halftone grey)."""
    from PIL import Image
    iw, ih = Image.open(img).size
    h = int(w * ih / iw * crop)
    f = "filter:grayscale(1) contrast(1.25) brightness(1.03);" if gray else ""
    sh = "filter:drop-shadow(8px 12px 0 rgba(0,0,0,.22))" if shadow else ""
    return (f'<div class="a" style="left:{x}px;top:{y}px;transform:rotate({rot}deg);z-index:{z};{sh}"><div style="width:{w}px;height:{h}px;overflow:hidden;clip-path:{torn_clip(seed)};background:#fff">'
            f'<img src="{Path(img).as_uri()}" style="width:{w}px;display:block;{f}"></div></div>')


def cut(img, x, y, h, rot=0, z=2, shadow="10px 14px 0 rgba(0,0,0,.25)"):
    return f'<img class="a" src="{Path(img).as_uri()}" style="left:{x}px;top:{y}px;height:{h}px;transform:rotate({rot}deg);z-index:{z};filter:drop-shadow({shadow})">'


def ransom(text, x, y, size, seed=4, z=5):
    r = random.Random(seed)
    fonts = ["Anton", "Playfair", "Archivo", "Bebas", "Serif", "Mono", "Marker"]
    bgs = [CREAM, "#fff", SIG, INK, RED, "#D9D2C2"]
    out = ""
    cx = x
    for ch in text:
        if ch == " ":
            cx += size * .45
            continue
        fnt, bg = r.choice(fonts), r.choice(bgs)
        col = "#fff" if bg in (INK, RED) else INK
        rot = r.uniform(-9, 9)
        s = size * r.uniform(.85, 1.12)
        out += f'<div class="a" style="left:{cx:.0f}px;top:{y + r.uniform(-12, 12):.0f}px;z-index:{z};transform:rotate({rot:.1f}deg);background:{bg};color:{col};font-family:{fnt};font-size:{s:.0f}px;line-height:1;padding:6px 10px;box-shadow:3px 4px 0 rgba(0,0,0,.25)">{ch}</div>'
        cx += s * (.62 if fnt in ("Anton", "Bebas", "Oswald") else .78) + 12
    return out


def tag(text, x, y, size, bg=INK, col="#fff", rot=0, z=6, font="Anton"):
    return f'<div class="a tag" style="left:{x}px;top:{y}px;font-family:{font};font-size:{size}px;background:{bg};color:{col};transform:rotate({rot}deg);z-index:{z};clip-path:{torn_clip(int(x + y), 6, 10)}">{text}</div>'


CHIPS = {"VERIFIED": "#1F8A70", "REPORTED": "#2F6DB5", "ALLEGATION": RED, "OPINION": "#7A5BBF", "RESPONSE": "#555"}


def chip(kind, x, y, extra="", z=7):
    return f'<div class="a chip" style="left:{x}px;top:{y}px;background:{CHIPS[kind]};z-index:{z}">{kind}{(" · " + extra) if extra else ""}</div>'


def stamp(text, x, y, size, rot=-8, z=8, col=RED):
    return f'<div class="a stamp" style="left:{x}px;top:{y}px;font-size:{size}px;transform:rotate({rot}deg);z-index:{z};border-color:{col};color:{col}">{text}</div>'


def shard(pts, col, z=0):
    return f'<svg class="a" style="inset:0;z-index:{z}" width="1920" height="1080"><polygon points="{pts}" fill="{col}"/></svg>'


def disc(x, y, r, col, z=0):
    return f'<div class="a" style="left:{x - r}px;top:{y - r}px;width:{2 * r}px;height:{2 * r}px;border-radius:50%;background:{col};z-index:{z}"></div>'


def splat(x, y, s, col=INK, seed=1, z=1):
    r = random.Random(seed)
    blobs = "".join(f'<circle cx="{x + r.gauss(0, s * .5):.0f}" cy="{y + r.gauss(0, s * .5):.0f}" r="{abs(r.gauss(s * .12, s * .08)):.0f}" fill="{col}"/>' for _ in range(22))
    return f'<svg class="a" style="inset:0;z-index:{z}" width="1920" height="1080"><circle cx="{x}" cy="{y}" r="{s * .45:.0f}" fill="{col}"/>{blobs}</svg>'


def doodle(d, col=INK, w=7, z=9):
    return f'<svg class="a" style="inset:0;z-index:{z};overflow:visible" width="1920" height="1080"><path d="{d}" stroke="{col}" stroke-width="{w}" fill="none" stroke-linecap="round" stroke-linejoin="round" filter="url(#rough)"/></svg>'


def logo_badge(slug, x, y, size, z=7, rot=0, bg="#fff"):
    return f'<div class="a" style="left:{x}px;top:{y}px;padding:{size * .18:.0f}px;background:{bg};border-radius:50%;transform:rotate({rot}deg);z-index:{z};box-shadow:5px 7px 0 rgba(0,0,0,.25);line-height:0">{icon(slug, size)}</div>'


# India outline, official boundary (DataMeet composite, CC BY 4.0), equirectangular with cos(lat) scaling
def india_path(x0, y0, w):
    g = json.load(open(A / "india-composite.geojson"))
    polys = g["features"][0]["geometry"]["coordinates"]
    lon0, lon1, lat0, lat1 = 68.0, 97.5, 6.5, 37.2
    k = math.cos(math.radians(22))
    sx = w / ((lon1 - lon0) * k)
    def P(lon, lat):
        return x0 + (lon - lon0) * k * sx, y0 + (lat1 - lat) * sx
    d = ""
    for poly in polys:
        ring = poly[0]
        if len(ring) < 60:
            continue
        step = max(1, len(ring) // 900)
        pts = ring[::step]
        d += "M" + " L".join(f"{P(a, b)[0]:.1f} {P(a, b)[1]:.1f}" for a, b in pts) + "Z"
    return d, P


def page(name, cls, bg, body, credit):
    (D / "stills" / f"{name}.html").write_text(HEAD.replace("{cls}", cls).replace("{bg}", bg) + body + TAIL.replace("{credit}", f'<div class="credit">{credit}</div>'), encoding="utf-8")


DOCS = F / "docs"
S = {}
GODL = "PHOTO: GOVT. OF INDIA (GODL-INDIA) VIA WIKIMEDIA COMMONS"

# 1. The handover: scrapbook build
S["c01_handover"] = ("ledger", "",
    shard("0,0 760,0 520,1080 0,1080", INK, 0)
    + scrap(DOCS / "print_malviya.png", 880, 120, 960, -2, .62, 11, z=2)
    + '<div class="tape" style="left:860px;top:100px;transform:rotate(-12deg);z-index:3"></div><div class="tape" style="left:1760px;top:110px;transform:rotate(14deg);z-index:3"></div>'
    + f'<div class="a" style="left:90px;top:120px;z-index:4;font-family:Anton;font-size:260px;color:{SIG};line-height:.9">17</div>'
    + f'<div class="a" style="left:96px;top:370px;z-index:4;font-family:Anton;font-size:110px;color:#fff;line-height:.9">AUGUST<br>2026</div>'
    + tag("Amit Malviya", 900, 560, 70, CREAM, INK, -3) + doodle("M890 610 L1340 600", RED, 12) + doodle("M900 640 Q1100 560 1330 590", RED, 9)
    + tag("Deepak Mhaskey", 960, 700, 84, SIG, INK, 2)
    + doodle("M1440 610 C1520 640 1520 700 1460 730", INK, 6) + doodle("M1450 715 l20 22 l10 -28", INK, 6)
    + stamp("no reason given", 1180, 860, 64, -6)
    + chip("VERIFIED", 880, 70, "THEPRINT, 17 AUG 2026")
    + f'<div class="a" style="left:100px;top:700px;z-index:4">{logo_badge("whatsapp", 70, 0, 0, 4, -8)}</div>'
    + splat(420, 900, 160, RED, 4, 1),
    "SOURCE: THEPRINT, 17 AUG 2026 (SCREENSHOT) · NO PHOTO OF EITHER OFFICIAL IS USED")

# 2. Map desk: India (official boundary) with pinned scraps and red string
d, P = india_path(560, 70, 820)
cities = [("Kota", 75.86, 25.18, "32 lakh in WhatsApp groups (UP), cited at Kota, 2018", "REPORTED"), ("Patna · Bihar", 85.14, 25.59, "72,000 planned groups, 2020", "REPORTED"),
          ("Bengaluru · Karnataka", 77.59, 12.97, "150,000 WhatsApp workers, 2023", "REPORTED"), ("Mandi", 76.93, 31.71, "400+ BJP-run groups, 2024", "REPORTED"),
          ("Raipur · Chhattisgarh", 81.63, 21.25, "Mhaskey's home turf", "REPORTED"), ("New Delhi", 77.21, 28.61, "national IT cell", "VERIFIED")]
side = [(90, 140), (1480, 160), (100, 760), (90, 420), (1480, 560), (1480, 860)]
body = f'<svg class="a" style="inset:0;z-index:1" width="1920" height="1080"><path d="{d}" fill="#D8CCB0" stroke="#6B5B44" stroke-width="3"/><path d="{d}" fill="none" stroke="rgba(0,0,0,.25)" stroke-width="10" transform="translate(8 10)" opacity=".35"/></svg>'
strings = ""
for i, ((name, lon, lat, note, kind), (sx, sy)) in enumerate(zip(cities, side)):
    px, py = P(lon, lat)
    strings += f'<path d="M{px:.0f} {py:.0f} Q{(px + sx + 170) / 2:.0f} {(py + sy + 60) / 2 + 40:.0f} {sx + 170} {sy + 60}" stroke="{RED}" stroke-width="3.5" fill="none"/><circle cx="{px:.0f}" cy="{py:.0f}" r="12" fill="{RED}" stroke="#fff" stroke-width="3"/>'
    body += (f'<div class="a" style="left:{sx}px;top:{sy}px;width:340px;background:{CREAM};padding:14px 16px 16px;z-index:5;transform:rotate({[-3, 2, -2, 3, -1, 2][i]}deg);box-shadow:6px 9px 0 rgba(0,0,0,.2)">'
             f'<div style="font-family:Anton;font-size:34px;line-height:1">{name}</div><div style="font:600 20px Oswald;margin-top:6px;line-height:1.2">{note}</div>'
             f'<div class="chip" style="display:inline-block;margin-top:10px;background:{CHIPS[kind]}">{kind}</div></div>')
body += f'<svg class="a" style="inset:0;z-index:4" width="1920" height="1080">{strings}</svg>'
body += logo_badge("whatsapp", 1180, 640, 64, 6, 8) + stamp("the machine", 640, 950, 70, -4, 6, INK)
S["c02_mapdesk"] = ("", f"background:#B9A27E;background-image:radial-gradient(ellipse at 50% 45%,#D6C29C 0%,#B39A72 70%,#8E7754 100%)", body,
                    "MAP: INDIA BOUNDARY BY DATAMEET (CC BY 4.0), FOLLOWING THE OFFICIAL BOUNDARY · SOURCES: THE QUINT, THEPRINT, WASHINGTON POST, REST OF WORLD, OUTLOOK · LOCATIONS APPROXIMATE")

# 3. Kota: Shah cut-out + ransom 'true or false'
S["c03_kota"] = ("", f"background:{SIG}",
    disc(1380, 520, 430, INK, 0) + shard("0,820 1920,700 1920,1080 0,1080", RED, 0)
    + "{SHAH_CUT}"
    + f'<div class="a" style="left:120px;top:170px;z-index:6;font-family:Anton;font-size:52px">"WE CAN SPREAD ANY MESSAGE WE WANT,</div>'
    + f'<div class="a" style="left:120px;top:240px;z-index:6;font-family:Anton;font-size:52px">WHETHER IT IS</div>'
    + ransom("TRUE OR FALSE", 120, 330, 96, 7) + f'<div class="a" style="left:880px;top:340px;z-index:6;font-family:Anton;font-size:90px">"</div>'
    + chip("REPORTED", 120, 120, "THE QUINT, 27 SEPT 2018 · AMIT SHAH, THEN BJP PRESIDENT, AT KOTA")
    + scrap(DOCS / "quint_kota.png", 120, 560, 640, 2, .5, 5, z=4)
    + tag("32 lakh in WhatsApp groups", 140, 900, 54, INK, SIG, -2) + logo_badge("whatsapp", 820, 880, 70, 7, 10)
    + tag("caveat? reports differ · earlier, in Delhi: 'don't post fake news'", 980, 980, 30, CREAM, INK, 1),
    GODL + " (AMIT SHAH, FILE PHOTO, RAIGAD; NOT FROM KOTA) · QUOTE: THE QUINT, 27 SEPT 2018 · CONTEXT: BLOOMBERG, THE WIRE")

# 4. How a message moves: paper flow
steps = [("bjp_symbol", "Central IT cell", "New Delhi"), (None, "State units", "e.g. Bihar: 9,500 IT cell heads"), (None, "Booth 'pramukhs'", "~9 lakh planned, 2019"), ("whatsapp", "WhatsApp groups", "72,000 planned in Bihar alone")]
body = ""
for i, (lg, t, sub) in enumerate(steps):
    x = 80 + i * 460
    col = [CREAM, "#fff", CREAM, "#fff"][i]
    body += (f'<div class="a" style="left:{x}px;top:{300 + (i % 2) * 60}px;width:360px;height:380px;background:{col};z-index:3;transform:rotate({[-2, 2, -1, 3][i]}deg);box-shadow:8px 12px 0 rgba(0,0,0,.25);clip-path:{torn_clip(40 + i, 10, 12)};padding:30px;box-sizing:border-box">'
             f'<div style="font-family:Anton;font-size:52px;line-height:1">{t}</div><div style="font:600 26px Oswald;margin-top:14px">{sub}</div></div>')
    if lg == "whatsapp":
        body += logo_badge("whatsapp", x + 120, 560 + (i % 2) * 60, 90, 6, -6)
    elif lg:
        body += f'<img class="a" src="{(A / "bjp_symbol.png").as_uri()}" style="left:{x + 110}px;top:{540}px;width:150px;z-index:6;filter:grayscale(1) contrast(1.2) drop-shadow(5px 7px 0 rgba(0,0,0,.25))">'
    if i < 3:
        body += doodle(f"M{x + 370} {480 + (i % 2) * 60} C{x + 410} {440} {x + 430} {520} {x + 455} {480 + ((i + 1) % 2) * 60}", RED, 10) + doodle(f"M{x + 435} {470 + ((i + 1) % 2) * 60} l22 12 l-20 16", RED, 10)
body += ransom("HOW IT TRAVELS", 80, 90, 92, 12) + chip("REPORTED", 80, 240, "THEPRINT; CARAVAN; MULTIPLE REPORTS (2019-20)") + stamp("party's own numbers", 1180, 820, 60, 4, 8, INK)
S["c04_flow"] = ("ledger", "", body, "ILLUSTRATION OF REPORTED STRUCTURE · SYMBOL: BJP (PUBLIC DOMAIN FILE, WIKIMEDIA COMMONS) · WHATSAPP LOGO: SIMPLE ICONS (CC0), TRADEMARK OF META")

# 5. Money: editorial poster, paper bars with logos
bars = [("TOTAL DECLARED, 2024 LS", 1737.68, INK, None), ("MEDIA ADVERTISING", 611.50, RED, None), ("GOOGLE INDIA", 156.95, "#fff", "google"), ("FACEBOOK", 24.63, "#fff", "facebook")]
body = disc(1560, 300, 260, SIG, 0) + f'<div class="a" style="left:1350px;top:170px;z-index:3;font-family:Anton;font-size:130px;line-height:.9">₹1,737<br><span style="font-size:60px">CRORE</span></div>'
for i, (lab, v, col, lg) in enumerate(bars):
    w = max(60, int(v / 1737.68 * 860))
    y = 300 + i * 170
    body += (f'<div class="a" style="left:120px;top:{y}px;width:{w}px;height:110px;background:{col};z-index:3;clip-path:{torn_clip(90 + i, 8, 14)};box-shadow:6px 8px 0 rgba(0,0,0,.2);border:{"3px solid #141414" if col == "#fff" else "0"}"></div>'
             f'<div class="a" style="left:{140 + w + (110 if lg else 0)}px;top:{y + 20}px;z-index:4;font-family:Anton;font-size:56px">₹{v:,.2f} cr</div><div class="a" style="left:124px;top:{y - 40}px;z-index:4;font:600 26px Mono;letter-spacing:2px">{lab}</div>')
    if lg:
        body += f'<div class="a" style="left:{140 + w + 16}px;top:{y + 18}px;z-index:5;line-height:0">{icon(lg, 72)}</div>'
body += chip("VERIFIED", 120, 120, "THE BJP'S OWN EXPENDITURE REPORT TO THE ELECTION COMMISSION") + scrap(DOCS / "scroll_1737.png", 1300, 640, 520, 4, .55, 22, z=4)
S["c05_money"] = ("", f"background:{CREAM}", body, "SOURCE: BJP EXPENDITURE REPORT TO THE ECI, VIA PTI / SCROLL (31 JAN 2025) · LOGOS: SIMPLE ICONS (CC0), TRADEMARKS OF GOOGLE AND META")

# 6. The label: X logo, torn 'video frame', stamp
body = shard("0,0 1920,0 1920,380 0,520", INK, 0)
body += f'<div class="a" style="left:140px;top:110px;z-index:3;line-height:0">{icon("x", 150, "#fff")}</div>'
body += f'<div class="a" style="left:330px;top:120px;z-index:3;font-family:Anton;font-size:96px;color:#fff">DECEMBER 2020</div>'
body += f'<div class="a" style="left:420px;top:420px;width:1080px;height:560px;background:#2A2A2A;z-index:2;clip-path:{torn_clip(61, 8, 16)};box-shadow:10px 14px 0 rgba(0,0,0,.3)"></div>'
body += f'<div class="a" style="left:470px;top:470px;width:980px;height:460px;z-index:3;background:repeating-linear-gradient(90deg,#3A3A3A 0 12px,#333 12px 24px)"></div>'
body += f'<div class="a" style="left:640px;top:880px;width:640px;height:14px;background:#666;z-index:4"></div><div class="a" style="left:640px;top:880px;width:200px;height:14px;background:{RED};z-index:5"></div>'
body += tag("clip posted: part of a longer video", 520, 520, 40, CREAM, INK, -2) + stamp("manipulated media", 650, 650, 92, -7)
body += chip("VERIFIED", 140, 300, "TWITTER'S LABEL, AS REPORTED: FIRST IN INDIA") + scrap(DOCS / "quint_label.png", 1380, 560, 470, 5, .55, 30, z=6)
body += tag("Twitter: 'declined to give details'", 1300, 960, 34, SIG, INK, -2)
S["c06_label"] = ("", f"background:{PAPER}", body, "ILLUSTRATION (NOT THE FOOTAGE) · SOURCE: THE QUINT, 2 DEC 2020; FACT-CHECKS BY ALT NEWS, BOOM · X LOGO: SIMPLE ICONS (CC0), TRADEMARK OF X CORP.")

# 7. Trend machine: WhatsApp logos funnel into # trends
body = ""
r = random.Random(5)
for i in range(60):
    body += f'<div class="a" style="left:{80 + (i % 10) * 70 + r.uniform(-8, 8):.0f}px;top:{250 + (i // 10) * 80 + r.uniform(-8, 8):.0f}px;z-index:3;line-height:0;transform:rotate({r.uniform(-15, 15):.0f}deg)">{icon("whatsapp", 50)}</div>'
body += doodle("M820 300 L1100 520 L820 740", INK, 9) + doodle("M840 520 L1100 520", INK, 6)
for i in range(12):
    body += f'<div class="a" style="left:{1180 + (i % 3) * 230}px;top:{230 + (i // 3) * 150}px;z-index:4;font-family:Anton;font-size:64px;background:{[SIG, "#fff", CREAM][i % 3]};padding:4px 14px;transform:rotate({r.uniform(-5, 5):.0f}deg);box-shadow:4px 6px 0 rgba(0,0,0,.2)">#</div>'
body += f'<div class="a" style="left:1160px;top:860px;z-index:5;line-height:0">{icon("x", 70)}</div>' + tag("75 coordinated campaigns", 1260, 862, 52, INK, SIG, -1)
body += tag("600+ public pro-BJP WhatsApp groups", 80, 860, 44, INK, "#fff", 1) + ransom("TREND MACHINE", 80, 80, 86, 21)
body += chip("REPORTED", 80, 200, "JAKESCH ET AL., CSCW 2021 · ORGANISER 'MOST LIKELY' THE PARTY'S SOCIAL MEDIA ARM, NOT CONFIRMED")
body += tag("smaller than reported · no evidence anyone was paid", 260, 960, 32, CREAM, INK, 0)
S["c07_trends"] = ("ledger", "", body, "SOURCE: JAKESCH, GARIMELLA, ECKLES, NAAMAN, CSCW 2021 (ARXIV 2104.13259) · LOGOS: SIMPLE ICONS (CC0), TRADEMARKS OF META AND X CORP. · ONE ICON = 10 GROUPS")

# 8. Swamy: halftone cut-out + 'gone rogue' scrap
S["c08_swamy"] = ("", f"background:{RED}",
    shard("1100,0 1920,0 1920,1080 1350,1080", INK, 0) + disc(560, 560, 360, CREAM, 0)
    + "{SWAMY_CUT}"
    + ransom("GONE ROGUE", 1060, 300, 92, 33) + f'<div class="a" style="left:1700px;top:300px;z-index:6;font-family:Anton;font-size:90px;color:#fff">"</div>'
    + f'<div class="a" style="left:1080px;top:200px;z-index:6;font-family:Anton;font-size:56px;color:#fff">"THE BJP IT CELL HAS</div>'
    + chip("OPINION", 1080, 140, "SUBRAMANIAN SWAMY, BJP MP · 7 SEPT 2020")
    + scrap(DOCS / "print_swamy.png", 1100, 580, 700, -3, .5, 44, z=4)
    + tag("the party kept Malviya", 1140, 920, 56, SIG, INK, 2),
    GODL + " (SUBRAMANIAN SWAMY, OFFICIAL PORTRAIT, CUT-OUT) · SOURCE: SWAMY ON TWITTER, 7 SEPT 2020, VIA THEPRINT")

# 9. Not a one-party story: both symbols, identical treatment
body = shard("0,0 960,0 960,1080 0,1080", CREAM, 0) + shard("960,0 1920,0 1920,1080 960,1080", "#D9D2C2", 0)
body += f'<img class="a" src="{(A / "bjp_symbol.png").as_uri()}" style="left:330px;top:150px;width:300px;z-index:3;filter:grayscale(1) contrast(1.2) drop-shadow(8px 10px 0 rgba(0,0,0,.2))">'
body += f'<img class="a" src="{(A / "inc_symbol.png").as_uri()}" style="left:1290px;top:150px;width:300px;z-index:3;filter:grayscale(1) contrast(1.2) drop-shadow(8px 10px 0 rgba(0,0,0,.2))">'
body += tag("BJP", 420, 480, 60) + tag("Congress", 1330, 480, 60)
body += (f'<div class="a" style="left:120px;top:600px;width:720px;z-index:4;font:600 30px Oswald;line-height:1.35">{icon("facebook", 40)} &nbsp;2019: Facebook removes 15 items linked to IT firm Silver Touch, which ran a pro-BJP page<br>'
         f'{icon("x", 36)} &nbsp;2020, 2021: posts by Malviya and Patra labelled manipulated</div>')
body += (f'<div class="a" style="left:1080px;top:600px;width:720px;z-index:4;font:600 30px Oswald;line-height:1.35">{icon("facebook", 40)} &nbsp;2019: Facebook removes 687 pages and accounts linked to the Congress IT cell<br>'
         f'&#9632; &nbsp;2024: Telangana Congress social media workers arrested over a doctored Amit Shah video</div>')
body += ransom("NOT A ONE-PARTY STORY", 330, 900, 70, 51)
body += chip("VERIFIED", 120, 560, "META NEWSROOM 1 APR 2019; SCROLL MAY 2024") + chip("REPORTED", 1080, 560, "SILVER TOUCH PAGE LINK, AS REPORTED")
S["c09_bothsides"] = ("", "", body, "SYMBOLS: BJP AND INC (PUBLIC DOMAIN FILES, WIKIMEDIA COMMONS), SAME SIZE AND TREATMENT · LOGOS: SIMPLE ICONS (CC0) · SOURCES: META NEWSROOM; THE QUINT; SCROLL")

# 10. Tek Fog: retracted
S["c10_tekfog"] = ("", f"background:{INK}",
    scrap(DOCS / "scroll_wire_retract.png", 260, 160, 1200, -2, .62, 70, z=2)
    + f'<div class="a" style="left:180px;top:620px;z-index:4;font-family:Anton;font-size:220px;color:#fff;text-decoration:line-through;text-decoration-color:{RED};text-decoration-thickness:22px">TEK FOG</div>'
    + stamp("retracted", 1120, 640, 120, -10, 6, RED) + tag("not evidence · not used in this film", 200, 920, 46, SIG, INK, -1)
    + chip("VERIFIED", 260, 100, "THE WIRE TOOK THE STORY DOWN, 23 OCT 2022, SAYING IT WAS DECEIVED"),
    "SOURCE: SCROLL, 23 OCT 2022 (SCREENSHOT) · MALVIYA SAID HE WOULD SUE (THE NEWS MINUTE)")

# 11. Who checks?
S["c11_whochecks"] = ("ledger", "",
    disc(1450, 520, 380, SIG, 0)
    + scrap(DOCS / "livelaw_fcu.png", 980, 300, 860, 3, .48, 80, z=3)
    + ransom("WHO CHECKS?", 100, 160, 130, 61)
    + f'<div class="a" style="left:110px;top:430px;z-index:5;font-family:Anton;font-size:84px;line-height:1">fact-check unit</div>' + doodle("M100 480 L800 470", RED, 14)
    + tag("Bombay High Court · Sept 2024 · struck down", 110, 560, 46, INK, "#fff", -1)
    + "".join(f'<div class="a" style="left:{110 + i * 0}px;top:{690 + i * 70}px;z-index:5;font-family:Anton;font-size:52px">{t}</div>' for i, t in enumerate(("platforms", "fact-checkers", "courts · rival parties")))
    + chip("VERIFIED", 110, 640, "KUNAL KAMRA V. UNION OF INDIA")
    + logo_badge("x", 1720, 860, 44, 7, 6) + logo_badge("facebook", 1600, 880, 44, 7, -6) + logo_badge("whatsapp", 1480, 900, 44, 7, 4),
    "SOURCE: LIVELAW (SEPT 2024, SCREENSHOT) · LOGOS: SIMPLE ICONS (CC0), TRADEMARKS OF THEIR OWNERS")

if __name__ == "__main__":
    import sys
    (D / "stills").mkdir(exist_ok=True)
    shah = A / "shah_cut.png"
    swamy = A / "swamy_cut.png"
    for name, (cls, bg, body, cr) in S.items():
        body = body.replace("{SHAH_CUT}", cut(shah, 1020, 120, 860, 0, 3) if shah.exists() else "")
        body = body.replace("{SWAMY_CUT}", cut(swamy, 330, 260, 640, 0, 3) if swamy.exists() else "")
        page(name, cls, bg, body, cr)
    print(len(S), "stills")
