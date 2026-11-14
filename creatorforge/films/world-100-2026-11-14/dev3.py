"""Third device set (world-100): before/after slider, night lights, globe, ticket, passport, magnifier, stamp,
clothesline, old TV, triptych, Swiss poster, polaroids, window. Real imagery only; anything illustrative is labelled."""
import json
import math
import random
from pathlib import Path

from collage2 import el, STILL, pin_dot, torn_label, wood
from dev2 import SIG, star4, torn_top, jag, H, outline

D = Path(__file__).resolve().parent
WORLD = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
AFRICA = {"Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cameroon", "Central African Rep.", "Chad", "Congo", "Côte d'Ivoire",
          "Dem. Rep. Congo", "Djibouti", "Egypt", "Eq. Guinea", "Eritrea", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya",
          "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda",
          "S. Sudan", "Senegal", "Sierra Leone", "Somalia", "Somaliland", "South Africa", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "W. Sahara",
          "Zambia", "Zimbabwe", "eSwatini"}


def rings(cc):
    return cc["r"] if isinstance(cc["r"], list) else json.loads(cc["r"])


def map_img(cid, suffix=""):
    return (D / "maps" / f"{cid}{suffix}.jpg").as_uri()


def india_path(P):
    from creatorforge_worker.media import maps
    return "".join("M" + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + "Z" for r in maps._find("India")["rings"] if len(r) > 3)


def big_title(c, x, y, size, col, kcol, width=900, font="Archivo", align="left"):
    return (el(f'<div style="font:400 {size}px/0.95 {font};color:{col};width:{width}px;text-align:{align}">{c[2]}</div>', x, y, .3, "wipe", z=8)
            + el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:{kcol};width:{width}px;text-align:{align};text-transform:uppercase">{c[3]}</div>', x, y + int(size * 1.05 * (1 + (len(c[2]) * size * .55 > width))) + 18, .5, "wipe", z=8))


# ---------------------------------------------------------------------------------------------------------------------
def d_beforeafter(M, c, sc, typ, rnd):
    a = c[5]
    ya, yb = a["dates"][0][:4], a["dates"][1][:4]
    body = el(f'<img src="{map_img(c[0], "_a")}" style="width:1920px;height:1080px;object-fit:cover;filter:contrast(1.1) saturate(1.1)">', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el(f'<div style="width:960px;height:1080px;overflow:hidden"><img src="{map_img(c[0], "_b")}" style="width:1920px;height:1080px;object-fit:cover;margin-left:-960px;filter:contrast(1.1) saturate(1.1)"></div>', 960, 0, .2, "wipe", extra=STILL, z=1)
    body += el('<div style="width:6px;height:1080px;background:#FFF;box-shadow:0 0 18px rgba(0,0,0,.6)"></div>', 957, 0, .25, "pop", z=3)
    body += el('<div style="width:76px;height:76px;border-radius:50%;background:#FFF;box-shadow:0 6px 18px rgba(0,0,0,.5);font:700 30px Inter;color:#141414;display:flex;align-items:center;justify-content:center">◀▶</div>', 922, 502, .3, "pop", z=4)
    for x, yr, at in ((60, ya, .35), (1600, yb, .45)):
        body += el(f'<div style="font:400 120px/1 Anton;color:{SIG};text-shadow:0 4px 20px rgba(0,0,0,.6)">{yr}</div>', x, 60, at, "pop", z=5)
    body += el('<div style="width:1920px;height:360px;background:linear-gradient(0deg,rgba(0,0,0,.75),transparent)"></div>', 0, 720, 0, "pop", extra=STILL, z=2)
    body += el(f'<div style="background:rgba(0,0,0,.55);padding:16px 24px"><div style="font:400 100px/1 Archivo;color:#FFF;white-space:nowrap">{c[2].upper()}</div><div style="font:600 22px Plex;letter-spacing:4px;color:#E6E6E6;margin-top:8px">{c[3].upper()}</div></div>', [40, 1000, 40, 1000][a.get("_k", 0) % 4], [840, 840, 640, 640][a.get("_k", 0) % 4], .5, "wipe", z=6)
    return body, "background:#000"


def d_nightlights(M, c, sc, typ, rnd):
    a = c[5]
    lon0, lat0, lon1, lat1 = a["bbox"]
    body = el(f'<img src="{map_img(c[0])}" style="width:1920px;height:1080px;object-fit:cover;filter:contrast(1.35) brightness(1.15) saturate(1.3)">', 0, 0, 0, "pop", extra=STILL, z=0)
    if a.get("india"):
        from PIL import Image
        with Image.open(D / "maps" / f"{c[0]}.jpg") as im:
            iw, ih = im.size
        k = max(1920 / iw, 1080 / ih); dw, dh = iw * k, ih * k; ox, oy = (1920 - dw) / 2, (1080 - dh) / 2
        P = lambda lo, la: (ox + (lo - lon0) / (lon1 - lon0) * dw, oy + (lat1 - la) / (lat1 - lat0) * dh)
        body += el(f'<svg width="1920" height="1080"><path d="{india_path(P)}" fill="none" stroke="{SIG}" stroke-width="2.5" stroke-opacity=".85"/></svg>', 0, 0, .2, "draw", z=2)
    body += el(f'<div style="font:400 120px/1 ISerifI;color:#FFE9B8;text-shadow:0 0 30px rgba(255,190,90,.7);white-space:nowrap">{c[2]}</div>', 90, 80 if not a.get("india") else 820, .4, "wipe", z=5)
    body += el(f'<div style="font:600 22px Plex;letter-spacing:5px;color:{SIG};white-space:nowrap">{c[3].upper()}</div>', 96, 215 if not a.get("india") else 955, .6, "wipe", z=5)
    return body, "background:#000"


def ortho(lon0, lat0, cx, cy, R):
    l0, p0 = math.radians(lon0), math.radians(lat0)

    def f(lo, la):
        l, p = math.radians(lo), math.radians(la)
        cosc = math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)
        x = cx + R * math.cos(p) * math.sin(l - l0)
        y = cy - R * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0))
        return x, y, cosc > 0
    return f


def d_globe(M, c, sc, typ, rnd):
    bg, accent, ink = sc
    a = c[5]
    cx, cy, R = 1280, 540, 450
    f = ortho(a["center"][0], a["center"][1], cx, cy, R)
    paths = ""
    for cc in WORLD["countries"]:
        hl = (a.get("hl") == "africa" and cc["n"] in AFRICA) or cc["n"] == a.get("hl")
        if cc["n"] == "India" and a.get("hl") == "India":
            continue
        for r in rings(cc):
            pts = [f(lo, la) for lo, la in r]
            vis = [(x, y) for x, y, v in pts if v]
            if len(vis) < 3:
                continue
            d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in vis) + "Z"
            paths += f'<path d="{d}" fill="{SIG if hl else "#E9E2D0"}" stroke="#13294B" stroke-width="1"/>'
    if a.get("hl") == "India":
        from creatorforge_worker.media import maps
        for r in maps._find("India")["rings"]:
            vis = [(x, y) for x, y, v in (f(lo, la) for lo, la in r) if v]
            paths += '<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in vis) + f'Z" fill="{SIG}" stroke="#13294B" stroke-width="1.2"/>'
    grat = ""
    for lon in range(-180, 180, 30):
        vis = [(x, y) for x, y, v in (f(lon, la) for la in range(-90, 91, 3)) if v]
        if len(vis) > 2:
            grat += '<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in vis) + '" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="1"/>'
    for lat in range(-60, 61, 30):
        vis = [(x, y) for x, y, v in (f(lo, lat) for lo in range(-180, 181, 3)) if v]
        if len(vis) > 2:
            grat += '<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in vis) + '" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="1"/>'
    ring = ""
    if a.get("ring"):
        RF = [(-70, -50), (-72, -30), (-76, -12), (-80, 0), (-88, 12), (-104, 19), (-116, 31), (-124, 42), (-132, 55), (-150, 60), (-170, 54), (175, 52), (162, 56),
              (155, 50), (148, 44), (142, 39), (139, 34), (131, 30), (125, 23), (121, 13), (125, 4), (131, -4), (148, -7), (163, -14), (178, -19), (178, -32), (175, -40)]
        vis = [(x, y) for x, y, v in (f(lo, la) for lo, la in RF) if v]
        ring = '<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in vis) + '" fill="none" stroke="#FF4B2B" stroke-width="10" stroke-dasharray="2 16" stroke-linecap="round"/>'
    svg = (f'<svg width="1920" height="1080"><defs><radialGradient id="oc" cx="40%" cy="35%"><stop offset="0" stop-color="#2C5AA0"/><stop offset="1" stop-color="#0E2347"/></radialGradient>'
           f'<radialGradient id="sh" cx="35%" cy="30%"><stop offset=".55" stop-color="rgba(0,0,0,0)"/><stop offset="1" stop-color="rgba(0,0,0,.55)"/></radialGradient></defs>'
           f'<circle cx="{cx}" cy="{cy}" r="{R + 40}" fill="rgba(80,140,255,.10)"/><circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#oc)"/>{grat}{paths}{ring}'
           f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#sh)"/></svg>')
    stars = "".join(f'<div class="el" style="left:{rnd.randint(0, 1900)}px;top:{rnd.randint(0, 1070)}px;width:2px;height:2px;background:#fff;opacity:{rnd.uniform(.3, .9):.2f};z-index:0"></div>' for _ in range(120))
    body = stars + el(svg, 0, 0, .1, "pop", z=2)
    body += el(f'<div style="font:400 120px/0.95 Anton;color:#F3EFE6;width:640px">{c[2].upper()}</div>', 110, 330, .4, "wipe", z=6)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:4px;color:{SIG};width:600px">{c[3].upper()}</div>', 116, 330 + (260 if len(c[2]) > 10 else 140), .6, "wipe", z=6)
    return body, "background:radial-gradient(ellipse at 70% 50%,#14213D 0%,#05070D 70%)"


def mini_route(a, w, h):
    lon0, lat0, lon1, lat1 = a["box"]
    P = lambda lo, la: ((lo - lon0) / (lon1 - lon0) * w, (lat1 - la) / (lat1 - lat0) * h)
    svg = f'<svg width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="#E8DFC8"/>'
    for cc in WORLD["countries"]:
        for r in rings(cc):
            pts = [P(lo, la) for lo, la in r]
            if all(x < -50 or x > w + 50 or y < -50 or y > h + 50 for x, y in pts):
                continue
            svg += '<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + 'Z" fill="#CDBF9C" stroke="#8C7B5A" stroke-width=".8"/>'
    pts = [P(lo, la) for lo, la in a["way"]]
    svg += '<path d="M' + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts) + '" fill="none" stroke="#C0262D" stroke-width="4" stroke-dasharray="10 7"/>'
    for x, y in (pts[0], pts[-1]):
        svg += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="#C0262D"/>'
    return svg + "</svg>"


def d_ticket(M, c, sc, typ, rnd):
    bg, accent, ink = sc
    a = c[5]
    tw, th = 1500, 560
    notch = f"radial-gradient(circle at 0 50%,transparent 34px,#F1E8D2 35px) left/51% 100% no-repeat,radial-gradient(circle at 100% 50%,transparent 34px,#F1E8D2 35px) right/51% 100% no-repeat"
    inner = (f'<div style="position:relative;width:{tw}px;height:{th}px;background:{notch};filter:drop-shadow(0 30px 40px rgba(0,0,0,.45))">'
             f'<div style="position:absolute;left:40px;top:40px;width:620px;height:{th - 80}px;overflow:hidden;border:2px solid #8C7B5A">{mini_route(a, 620, th - 80)}</div>'
             f'<div style="position:absolute;left:700px;top:50px;font:600 20px Plex;letter-spacing:5px;color:#8C7B5A">FROM</div>'
             f'<div style="position:absolute;left:700px;top:80px;font:400 96px/1 Anton;color:#141414">{a["from"]}</div>'
             f'<div style="position:absolute;left:700px;top:200px;font:600 20px Plex;letter-spacing:5px;color:#8C7B5A">TO</div>'
             f'<div style="position:absolute;left:700px;top:230px;font:400 96px/1 Anton;color:#C0262D">{a["to"]}</div>'
             f'<div style="position:absolute;left:700px;top:360px;font:500 20px Plex;letter-spacing:3px;color:#3A3A3A;width:560px">VIA {a["via"]}</div>'
             f'<div style="position:absolute;left:700px;top:440px;width:300px;height:56px;background:repeating-linear-gradient(90deg,#141414 0 3px,transparent 3px 7px,#141414 7px 9px,transparent 9px 13px)"></div>'
             f'<div style="position:absolute;left:1240px;top:0;width:0;height:{th}px;border-left:4px dashed #B8A27A"></div>'
             f'<div style="position:absolute;left:1270px;top:60px;width:200px;font:400 40px/1 Anton;color:#141414;transform:rotate(90deg);transform-origin:0 0;left:1420px">ADMIT ONE</div>'
             f'<div style="position:absolute;left:1290px;top:440px;font:600 13px Plex;letter-spacing:2px;color:#8C7B5A;width:180px">ILLUSTRATIVE TICKET</div></div>')
    body = el(inner, 210, 300, .2, "drop", base=f"rotate({rnd.choice([-3, -2, 2, 3])}deg)", z=4)
    body += el(f'<div style="font:400 92px/1 PlayfairI2;color:{ink}">{c[2]}</div>', 210, 90, .4, "wipe", z=6)
    body += el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:{accent}">{c[3].upper()}</div>', 216, 205, .6, "wipe", z=6)
    body += star4(1700, 140, 70, SIG)
    return body, f"background:{bg}"


def d_passport(M, c, sc, typ, rnd):
    a = c[5]
    guil = "background:#DCE8E2;background-image:repeating-radial-gradient(circle at 30% 40%,rgba(40,90,80,.10) 0 2px,transparent 2px 9px),repeating-linear-gradient(35deg,rgba(40,90,80,.06) 0 1px,transparent 1px 6px)"
    page = lambda: f'<div style="width:760px;height:900px;{guil};box-shadow:inset 0 0 40px rgba(0,0,0,.12)"></div>'
    body = el(f'<div style="display:flex;filter:drop-shadow(0 30px 40px rgba(0,0,0,.45))">{page()}<div style="width:8px;background:#9FB8AE"></div>{page()}</div>', 192, 90, .1, "drop", base="rotate(-2deg)", z=2)
    body += el('<div style="font:600 22px Plex;letter-spacing:8px;color:#2D5A50">VISAS</div>', 260, 120, .2, "pop", z=3)
    inks = ["#1F4E9B", "#B3261E", "#2E7D32", "#6A1B9A", "#C2410C", "#0F766E"]
    spots = [(300, 210), (700, 520), (330, 640), (1060, 220), (1350, 560), (1060, 720)]
    for i, ((x, y), city) in enumerate(zip(spots, a["cities"])):
        col = inks[i % len(inks)]
        rot = rnd.uniform(-18, 18)
        shape = ("border-radius:50%;width:260px;height:260px" if i % 3 == 0 else "border-radius:14px;width:320px;height:190px" if i % 3 == 1 else "border-radius:50% / 40%;width:300px;height:210px")
        stamp = (f'<div style="{shape};border:6px double {col};color:{col};display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:.85;transform:rotate(0)"><div style="font:600 16px Plex;letter-spacing:4px">ENTRY</div><div style="font:400 50px/1 Anton;letter-spacing:2px">{city}</div>'
                 f'<div style="font:600 16px Plex;letter-spacing:3px">★ ★ ★</div></div>')
        body += el(stamp, x, y, .3 + .08 * i, "pop", base=f"rotate({rot:.0f}deg)", z=4)
    body += el(f'<div style="background:#141414;padding:16px 26px"><div style="font:400 72px/1 Anton;color:#F3EFE6">{c[2].upper()}</div><div style="font:600 20px Plex;letter-spacing:4px;color:{SIG};margin-top:8px">{c[3].upper()} · ILLUSTRATIVE STAMPS</div></div>', 1180, 900, .7, "wipe", z=6)
    return body, "background:#2A2622"


def d_lens(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    a = c[5]
    src = jpg(a["paper"])
    body = el(f'<img src="{src}" style="width:1920px;height:1080px;object-fit:cover;filter:sepia(.45) contrast(1.05) brightness(.8)">', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 62% 48%,transparent 30%,rgba(10,6,2,.75) 85%)"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    lx, ly = a.get("at", (1180, 460)); r, z = 290, 2.4
    lens = (f'<div style="position:relative;width:{2 * r}px;height:{2 * r}px">'
            f'<div style="position:absolute;inset:0;border-radius:50%;background:url({src}) no-repeat;background-size:{1920 * z}px {1080 * z}px;background-position:{-(lx * z - r)}px {-(ly * z - r)}px;filter:sepia(.25) contrast(1.15) saturate(1.2);box-shadow:inset 0 0 40px rgba(0,0,0,.45)"></div>'
            f'<div style="position:absolute;inset:-26px;border-radius:50%;border:26px solid #2B2B2B;box-shadow:0 30px 40px rgba(0,0,0,.6),inset 0 0 0 4px #777"></div>'
            f'<div style="position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle at 30% 25%,rgba(255,255,255,.45),transparent 30%)"></div>'
            f'<div style="position:absolute;left:{2 * r - 20}px;top:{2 * r - 20}px;width:60px;height:320px;background:linear-gradient(90deg,#3A2A1A,#6B4A2A,#3A2A1A);border-radius:20px;transform:rotate(-45deg);transform-origin:30px 0"></div></div>')
    body += el(lens, lx - r, ly - r, .3, "pop", z=4)
    TX = 100 if lx > 960 else 1060
    body += el(f'<div style="font:900 120px/0.95 Playfair;color:#F4E9D2;width:780px;text-shadow:0 6px 20px rgba(0,0,0,.7)">{c[2]}</div>', TX, 120, .4, "wipe", z=6)
    body += el(f'<div style="font:400 46px ISerifI;color:{SIG};text-shadow:0 2px 10px rgba(0,0,0,.9),0 0 3px #000">{c[3]}</div>', TX + 6, 400 if len(c[2]) > 12 else 270, .6, "wipe", z=6)
    return body, "background:#140C05"


def d_stamp(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    bg, accent, ink = sc
    a = c[5]
    W_, H_ = 760, 900
    perf = "radial-gradient(circle,transparent 9px,#FBF8F0 10px) -15px -15px/30px 30px"
    stamp = (f'<div style="position:relative;width:{W_}px;height:{H_}px;background:{perf};padding:36px;box-sizing:border-box;filter:drop-shadow(0 26px 30px rgba(0,0,0,.4))">'
             f'<div style="position:relative;width:100%;height:100%;overflow:hidden;background:#FBF8F0;border:2px solid #FBF8F0">'
             f'<img src="{jpg(a["ground"])}" style="width:100%;height:78%;object-fit:cover;filter:saturate(1.15) contrast(1.05)">'
             f'<div style="position:absolute;left:16px;top:14px;font:400 40px/1 Anton;color:#FFF;text-shadow:0 2px 8px rgba(0,0,0,.6);letter-spacing:2px">{a["country"]}</div>'
             f'<div style="padding:18px 16px 0;font:900 52px/1 Playfair;color:#141414">{c[2]}</div></div></div>')
    k = a.get("_k", 0) % 3
    sx, tx, ty = [(980, 110, 200), (140, 1000, 200), (580, 110, 60)][k]
    body = el(stamp, sx, 90 if k < 2 else 150, .2, "drop", base=f"rotate({rnd.choice([-4, 3, 5])}deg)", z=3)
    waves = "".join(f'<path d="M0 {40 + i * 34} Q 60 {20 + i * 34} 120 {40 + i * 34} T 240 {40 + i * 34} T 360 {40 + i * 34} T 480 {40 + i * 34} T 600 {40 + i * 34}" fill="none" stroke="#2A2A2A" stroke-width="5" opacity=".55"/>' for i in range(5))
    body += el(f'<svg width="900" height="260">{waves}<circle cx="760" cy="110" r="100" fill="none" stroke="#2A2A2A" stroke-width="5" opacity=".55"/>'
               f'<text x="760" y="104" text-anchor="middle" font-family="Plex" font-size="20" fill="#2A2A2A" opacity=".7">PRINT FACTS</text><text x="760" y="134" text-anchor="middle" font-family="Plex" font-size="16" fill="#2A2A2A" opacity=".7">2026</text></svg>', sx - 200, 520, .5, "pop", z=4)
    if k < 2:
        body += el(f'<div style="font:400 140px/0.92 Anton;color:{ink};width:760px">{c[2].upper()}</div>', tx, ty, .3, "wipe", z=5)
        body += el(f'<div style="font:600 24px Plex;letter-spacing:4px;color:{accent if accent != bg else SIG};width:700px">{c[3].upper()} · ILLUSTRATIVE STAMP</div>', tx + 6, 560, .5, "wipe", z=5)
    else:
        body += el(f'<div style="font:400 120px/0.92 Anton;color:{ink};width:440px">{c[2].upper()}</div>', 1420, 220, .3, "wipe", z=5)
        body += el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:{accent if accent != bg else SIG};width:400px">{c[3].upper()} · ILLUSTRATIVE STAMP</div>', 1426, 560, .5, "wipe", z=5)
    return body, f"background:{bg};background-image:radial-gradient(rgba(0,0,0,.05) 1px,transparent 1.5px);background-size:6px 6px"


def d_clothesline(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    bg, accent, ink = sc
    a = c[5]
    body = el('<svg width="1920" height="400"><path d="M-40 120 Q 960 300 1960 120" stroke="#5B4632" stroke-width="5" fill="none"/></svg>', 0, 0, 0, "pop", extra=STILL, z=2)
    for i, q in enumerate(a["photos"]):
        x = 150 + i * 560
        t = (x + 230) / 1920
        y = 120 + 4 * t * (1 - t) * 180 - 20
        rot = [-5, 3, -2][i % 3]
        cap = q.split()[0].capitalize() + " " + " ".join(q.split()[1:])
        card = (f'<div style="position:relative;width:460px;background:#FBFAF6;padding:16px 16px 0;box-shadow:0 20px 30px rgba(0,0,0,.35)">'
                f'<div style="position:absolute;left:205px;top:-34px;width:34px;height:70px;background:linear-gradient(90deg,#C89B63,#E2BB85,#C89B63);border-radius:4px"></div>'
                f'<img src="{jpg(q)}" style="width:428px;height:428px;object-fit:cover;display:block">'
                f'<div style="font:700 34px Caveat;color:#333;padding:10px 4px 16px">{cap}</div></div>')
        body += el(card, x, y, .2 + .15 * i, "drop", base=f"rotate({rot}deg)", z=3 + i)
    body += el(f'<div style="font:400 96px/1 Anton;color:{ink}">{c[2].upper()}</div>', 110, 900, .7, "wipe", z=8)
    body += el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:{accent if accent != bg else SIG}">{c[3].upper()}</div>', 1000, 940, .8, "wipe", z=8)
    return body, f"background:{bg}"


def d_tv(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    a = c[5]
    wall = "background:" + ["#2F5D50", "#7A3B2E"][a.get("_k", 0) % 2] + ";background-image:repeating-linear-gradient(90deg,rgba(255,255,255,.05) 0 40px,transparent 40px 80px)"
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{wall};z-index:0"></div>'
    body += el('<div style="width:1920px;height:260px;background:#6B4A2A;box-shadow:inset 0 10px 20px rgba(0,0,0,.4)"></div>', 0, 860, 0, "pop", extra=STILL, z=1)
    tv = ('<div style="position:relative;width:1080px;height:760px;background:linear-gradient(180deg,#B5652B,#8A4A1E);border-radius:60px;box-shadow:0 40px 60px rgba(0,0,0,.5),inset 0 0 0 10px #6E3A16">'
          f'<div style="position:absolute;left:60px;top:60px;width:760px;height:600px;border-radius:70px / 50px;overflow:hidden;background:#111;box-shadow:inset 0 0 60px rgba(0,0,0,.9)">'
          f'<img src="{jpg(a["ground"])}" style="width:100%;height:100%;object-fit:cover;filter:saturate(1.2) contrast(1.1)">'
          '<div style="position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,0,0,.25) 0 2px,transparent 2px 5px)"></div>'
          '<div style="position:absolute;inset:0;background:radial-gradient(ellipse at 30% 20%,rgba(255,255,255,.25),transparent 45%),radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,.6))"></div>'
          '<div style="position:absolute;left:30px;top:26px;background:#E11D2E;color:#FFF;font:700 26px Inter;padding:4px 14px;letter-spacing:2px">● LIVE</div></div>'
          '<div style="position:absolute;left:860px;top:110px;width:140px;height:140px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#EEE,#888);box-shadow:0 6px 10px rgba(0,0,0,.4)"></div>'
          '<div style="position:absolute;left:880px;top:300px;width:100px;height:100px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#EEE,#888)"></div>'
          '<div style="position:absolute;left:870px;top:450px;width:120px;height:180px;background:repeating-linear-gradient(0deg,#3A1E0A 0 4px,transparent 4px 12px)"></div>'
          '<div style="position:absolute;left:180px;top:760px;width:40px;height:100px;background:#3A1E0A;transform:skewX(12deg)"></div><div style="position:absolute;left:860px;top:760px;width:40px;height:100px;background:#3A1E0A;transform:skewX(-12deg)"></div></div>')
    flip = a.get("_k", 0) % 2 == 1
    TVX, TX = (80, 1260) if flip else (760, 100)
    body += el('<svg width="600" height="300"><path d="M300 290 L120 20 M300 290 L520 40" stroke="#222" stroke-width="7"/><circle cx="300" cy="290" r="26" fill="#333"/></svg>', TVX + 240, -10, .1, "pop", z=2)
    body += el(tv, TVX, 140, .2, "drop", z=3)
    body += el(f'<div style="font:400 120px/0.92 Bebas;color:#F4EEDF;width:560px">{c[2].upper()}</div>', TX, 220, .4, "wipe", z=6)
    body += el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:{SIG};width:540px">{c[3].upper()}</div>', TX + 6, 480, .6, "wipe", z=6)
    return body, "background:#2F5D50"


def d_triptych(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    bg, accent, ink = sc
    a = c[5]
    caps = [x.strip() for x in c[3].split(",")]
    body = ""
    for i, q in enumerate(a["photos"]):
        clip = f"polygon({','.join(f'{rnd.uniform(0, 3):.1f}% {y}%' for y in range(0, 101, 10))},{','.join(f'{100 - rnd.uniform(0, 3):.1f}% {y}%' for y in range(100, -1, -10))})"
        body += el(f'<div style="width:660px;height:1180px;clip-path:{clip};overflow:hidden;box-shadow:0 0 30px rgba(0,0,0,.5)"><img src="{jpg(q)}" style="width:100%;height:100%;object-fit:cover;filter:saturate(1.15) contrast(1.05)"></div>',
                   -20 + i * 640, -50, .1 + .12 * i, "drop", base=f"rotate({[-1.5, 1, -1][i]}deg)", z=2 + i)
        if i < len(caps):
            body += torn_label(caps[i].upper(), 60 + i * 640, 120, 34, "#F4EEDF", "#141414", rot=[-3, 2, -2][i], at=.6 + .1 * i, z=8, font="Mono", seed=i + 3)
    body += el(f'<div style="width:1920px;background:#141414;padding:26px 0;text-align:center"><span style="font:400 110px/1 Anton;color:#F4EEDF;letter-spacing:3px">{c[2].upper()}</span></div>', 0, 780, .5, "wipe", z=7)
    body += el(f'<div style="width:240px;height:14px;background:{SIG}"></div>', 840, 770, .6, "wipe", z=8)
    return body, "background:#141414"


def d_swiss(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    bg, accent, ink = sc
    a = c[5]
    col = rnd.choice(["#E3342F", "#1D4ED8", "#F59E0B", "#0F766E"])
    body = el(f'<div style="width:1920px;height:1080px;background:#EFEDE6"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    k = a.get("_k", 0) % 3
    PX, PW, PH, PY = [(880, 1040, 1080, 0), (0, 1000, 1080, 0), (0, 1920, 560, 520)][k]
    TXT = [90, 1060, 90][k]
    body += el(f'<div style="width:{PW}px;height:{PH}px;overflow:hidden;position:relative"><img src="{jpg(a["ground"])}" style="width:100%;height:100%;object-fit:cover;filter:grayscale(1) contrast(1.6) brightness(1.05)">'
               f'<div style="position:absolute;inset:0;background:{col};mix-blend-mode:multiply"></div>'
               f'<div style="position:absolute;inset:0;background-image:radial-gradient(rgba(0,0,0,.35) 1.4px,transparent 1.8px);background-size:7px 7px"></div></div>', PX, PY, .1, "pop", extra=STILL, z=1)
    if k < 2:
        body += el(f'<div style="font:800 170px/0.86 Inter;color:#111;letter-spacing:-8px;width:800px">{c[2]}</div>', TXT, 120, .3, "wipe", z=4)
        body += el('<div style="width:760px;height:6px;background:#111"></div>', TXT + 6, 640, .4, "wipe", z=4)
        body += el(f'<div style="font:500 26px/1.3 Inter;color:#111;width:340px">{c[3]}</div>', TXT + 6, 670, .5, "wipe", z=4)
        body += el(f'<div style="font:500 18px/1.6 Plex;color:#555;width:300px">PRINT FACTS<br>WORLD SERIES<br>NO. {rnd.randint(10, 99)}</div>', TXT + 430, 670, .55, "wipe", z=4)
        body += el(f'<div style="width:120px;height:120px;border-radius:50%;background:{SIG}"></div>', TXT + 6, 880, .6, "pop", z=4)
    else:
        body += el(f'<div style="font:800 260px/0.86 Inter;color:#111;letter-spacing:-12px;white-space:nowrap">{c[2]}</div>', 80, 120, .3, "wipe", z=4)
        body += el(f'<div style="font:500 26px/1.3 Inter;color:#111;width:420px">{c[3]}</div>', 1400, 160, .5, "wipe", z=4)
        body += el(f'<div style="width:120px;height:120px;border-radius:50%;background:{SIG}"></div>', 1700, 330, .6, "pop", z=4)
    return body, "background:#EFEDE6"


def d_polaroids(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    a = c[5]
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{wood()};z-index:0"></div>'
    flip = a.get("_k", 0) % 2 == 1
    spots = [(820, 90, -8), (1300, 140, 6), (900, 560, 4), (1380, 600, -5)]
    if flip:
        spots = [(x - 760, y, r) for x, y, r in spots]
    for i, (q, (x, y, rot)) in enumerate(zip(a["photos"], spots)):
        cap = " ".join(w for w in q.split() if w not in ("sign", "vintage"))
        card = (f'<div style="width:420px;background:#FBFAF6;padding:18px 18px 0;box-shadow:0 22px 32px rgba(0,0,0,.5)"><img src="{jpg(q)}" style="width:384px;height:384px;object-fit:cover;display:block;filter:sepia(.25) saturate(1.1) contrast(1.05)">'
                f'<div style="font:700 36px Caveat;color:#2A2A2A;padding:10px 2px 16px">{cap}</div></div>')
        body += el(card, x, y, .15 + .15 * i, "drop", base=f"rotate({rot}deg)", z=3 + i)
    body += el(f'<div style="background:#F4EEDF;padding:24px 34px;transform:rotate(-3deg);box-shadow:0 14px 24px rgba(0,0,0,.45)"><div style="font:400 {min(110, int(700 / (len(c[2]) * .62)))}px/1 Marker;color:#141414;white-space:nowrap">{c[2]}</div>'
               f'<div style="font:600 22px Plex;letter-spacing:4px;color:#7A2A20;margin-top:6px">{c[3].upper()}</div></div>', 1100 if flip else 90, 380, .7, "drop", z=9)
    body += el(f'<div style="width:200px;height:60px;background:rgba(255,221,51,.75);transform:rotate(-8deg)"></div>', 1210 if flip else 120, 350, .8, "pop", z=10)
    return body, "background:#4A2F1A"


def d_window(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    a = c[5]
    if c[0] == "nighttrain":
        body = el('<div style="width:1920px;height:1080px;background:linear-gradient(180deg,#5A2E1C,#3A1D12)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
        win = (f'<div style="position:relative;width:1240px;height:720px;border-radius:40px;border:34px solid #B8B2A6;box-shadow:inset 0 0 0 6px #6F6A60,0 30px 50px rgba(0,0,0,.5);overflow:hidden">'
               f'<img src="{jpg(a["ground"])}" style="width:100%;height:100%;object-fit:cover;filter:brightness(.55) saturate(.8) hue-rotate(190deg) contrast(1.1);transform:scale(1.15);transform-origin:30% 50%">'
               '<div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,255,255,0) 0%,rgba(255,255,255,.10) 40%,rgba(255,255,255,0) 60%)"></div>'
               '<div style="position:absolute;left:0;right:0;top:340px;height:6px;background:#8D877C"></div></div>')
        body += el(win, 560, 160, .1, "pop", z=2)
        body += el('<div style="width:520px;height:1080px;background:repeating-linear-gradient(90deg,#7B2D26 0 30px,#6A241E 30px 60px);box-shadow:20px 0 40px rgba(0,0,0,.5)"></div>', 0, 0, .1, "slide", z=3)
        tx, tcol = 1250, "#F4EEDF"
        body += el(f'<div style="font:400 100px/0.95 ISerifI;color:{tcol};text-shadow:0 4px 20px rgba(0,0,0,.6);white-space:nowrap">{c[2]}</div>', 620, 920, .4, "wipe", z=6)
        body += el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:{SIG}">{c[3].upper()}</div>', 1300, 960, .6, "wipe", z=6)
        return body, "background:#3A1D12"
    body = el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 60% 50%,#F2F1EC 0%,#C9C7C0 80%)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    win = (f'<div style="position:relative;width:640px;height:880px;border-radius:300px;background:#DDDBD4;box-shadow:inset 0 10px 30px rgba(0,0,0,.25),0 0 0 30px #E7E5DE,0 0 0 34px #BEBBB2">'
           f'<div style="position:absolute;left:50px;top:50px;width:540px;height:780px;border-radius:260px;overflow:hidden;box-shadow:inset 0 0 40px rgba(0,0,0,.4)">'
           f'<img src="{jpg(a["ground"])}" style="width:100%;height:100%;object-fit:cover;filter:saturate(1.15)">'
           '<div style="position:absolute;left:0;top:0;width:100%;height:30%;background:linear-gradient(180deg,#E9E7E0,#D6D3CA);box-shadow:0 8px 14px rgba(0,0,0,.25)"></div>'
           '<div style="position:absolute;inset:0;background:radial-gradient(ellipse at 30% 30%,rgba(255,255,255,.25),transparent 40%)"></div></div></div>')
    body += el(win, 1120, 100, .1, "pop", z=2)
    body += el(f'<div style="font:400 140px/0.9 Anton;color:#1C1C1C;width:820px">{c[2].upper()}</div>', 120, 300, .3, "wipe", z=5)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:4px;color:#555;width:760px">{c[3].upper()}</div>', 126, 300 + (290 if len(c[2]) > 11 else 150), .5, "wipe", z=5)
    body += el(f'<div style="width:90px;height:90px;border-radius:50%;background:{SIG}"></div>', 126, 760, .6, "pop", z=5)
    return body, "background:#D9D7D0"


DEV3 = {"beforeafter": d_beforeafter, "nightlights": d_nightlights, "globe": d_globe, "ticket": d_ticket, "passport": d_passport, "lens": d_lens, "stamp": d_stamp,
        "clothesline": d_clothesline, "tv": d_tv, "triptych": d_triptych, "swiss": d_swiss, "polaroids": d_polaroids, "window": d_window}
