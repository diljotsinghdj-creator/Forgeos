"""Compose the 50 collages (16:9) in the owner's reference vocabulary. Eight devices; each piece gets its own colour
scheme, type pairing and placement, and neighbours never share a device or scheme."""
import json
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/Forgeos/creatorforge/channels/design_kits/collage")
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
import collage2 as K
from collage2 import el, STILL
from concepts import C

D = Path(__file__).resolve().parent
A = D / "assets"
REC = json.loads((D / "data" / "assets.json").read_text())
SIG = "#FFDD33"
F = K.FONTS
FACES = "<style>" + "".join(f"@font-face{{font-family:{n};src:url({(F / (p + '.woff2')).as_uri()})}}" for n, p in (
    ("Plex", "ibm-plex-mono-latin-500-normal"), ("Grotesk", "space-grotesk-latin-700-normal"), ("ISerif", "instrument-serif-latin-400-normal"),
    ("FrauncesI", "fraunces-latin-400-italic"))) + "</style>"
SCHEMES = [("#9E1B22", "#F2C200", "#F4EFE6"), ("#0F0F10", "#FF6A1A", "#F4EFE6"), ("#F4F2EA", "#E5A91A", "#141414"), ("#14304F", "#F2C200", "#F4EFE6"),
           ("#1E5E4E", "#F4D35E", "#F4EFE6"), ("#E8E1D3", "#D7262B", "#141414"), ("#2B2D42", "#EF8354", "#F4EFE6"), ("#5C1A33", "#F7B32B", "#F4EFE6"),
           ("#0B3C5D", "#F2545B", "#F4EFE6"), ("#3D2C8D", "#FFD23F", "#F4EFE6"), ("#EDE6DA", "#2E86AB", "#141414"), ("#1B1B1B", "#E63946", "#F4EFE6"),
           ("#F1E3C8", "#3A7D44", "#141414"), ("#22333B", "#E9C46A", "#F4EFE6"), ("#B23A48", "#FCD581", "#F4EFE6"), ("#EAEAEA", "#FF4F00", "#141414")]
TYPES = [("400 {s}px/0.92 Anton", "Plex"), ("900 {s}px/0.95 Playfair", "Mono"), ("700 {s}px/0.95 Grotesk", "Plex"), ("400 {s}px/0.95 Bebas", "DMono"),
         ("400 {s}px/1 ISerif", "Plex"), ("400 {s}px/0.95 Archivo", "Mono"), ("600 {s}px/0.95 Oswald", "DMono"), ("400 {s}px/1 FrauncesI", "Grotesk")]
HAND_ROT = {}        # per hand asset: degrees so the fingers point down at the subject (set after looking at the cut-outs)


def slug(q):
    return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:48]


def png(q):
    p = A / f"{slug(q)}.png"
    return p.as_uri() if p.is_file() else None


def jpg(q):
    p = A / f"{slug(q)}.jpg"
    return p.as_uri() if p.is_file() else None


def size_of(q):
    from PIL import Image
    p = A / f"{slug(q)}.png"
    with Image.open(p) as im:
        return im.size


def fit_box(q, maxw, maxh):
    w, h = size_of(q)
    k = min(maxw / w, maxh / h)
    return int(w * k), int(h * k)


def cutimg(q, w, h, grey=False, extra=""):
    flt = "grayscale(1) contrast(1.25) brightness(1.03)" if grey else "saturate(1.1) contrast(1.05)"
    return f'<img src="{png(q)}" style="width:{w}px;height:{h}px;display:block;filter:{flt} drop-shadow(0 18px 22px rgba(0,0,0,.38));{extra}">'


def title(t, k, typ, size, col, kcol, width, align="left"):
    font, kfont = typ
    s = int(min(size, width / max(1, len(max(t.split(), key=len)) * .62)))
    return (f'<div style="width:{width}px;text-align:{align}"><div style="font:{font.format(s=s)};color:{col};text-transform:uppercase">{t}</div>'
            f'<div style="font:500 22px {kfont};letter-spacing:3px;color:{kcol};margin-top:14px;text-transform:uppercase">{k}</div></div>')


def clouds(rnd, n=3, col="rgba(255,255,255,.85)"):
    out = ""
    for _ in range(n):
        x, y, w, rot = rnd.randint(-200, 1500), rnd.randint(80, 700), rnd.randint(700, 1300), rnd.randint(-28, 12)
        out += f'<div class="el" style="left:{x}px;top:{y}px;width:{w}px;height:90px;background:radial-gradient(ellipse at center,{col} 0%,transparent 70%);filter:blur(14px);transform:rotate({rot}deg);z-index:7;pointer-events:none"></div>'
    return out


def disc(x, y, r, col, z=2):
    return f'<div class="el" style="left:{x - r}px;top:{y - r}px;width:{2 * r}px;height:{2 * r}px;border-radius:50%;background:{col};z-index:{z}"></div>'


def hand(q, x, y, h, rot):
    w0, h0 = size_of(q)
    w = int(h * w0 / h0)
    return el(f'<img src="{png(q)}" style="height:{h}px;width:{w}px;filter:grayscale(1) contrast(1.2) drop-shadow(0 24px 26px rgba(0,0,0,.35));transform:rotate({rot}deg)">', x, y, .5, "drop", z=9)


# ---- devices ---------------------------------------------------------------------------------------------------------
def d_hand(c, sc, typ, rnd):
    bg, accent, ink = sc
    a = c[5]
    grid = "background:#F4F2EA;background-image:linear-gradient(rgba(0,0,0,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.12) 1px,transparent 1px);background-size:54px 54px"
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{grid};z-index:0"></div>'
    body += el(f'<div style="width:1920px;height:330px;overflow:hidden"><img src="{jpg(a["ground"])}" style="width:100%;height:100%;object-fit:cover;filter:saturate(1.6) hue-rotate({rnd.choice([0, 25, 160, 200])}deg) contrast(1.1)"></div>', 0, 750, 0, "pop", extra=STILL, z=3)
    cx = rnd.choice([1180, 1240, 1300])
    body += disc(cx, 610, 300, accent, 2)
    w, h = fit_box(a["subject"], 520, 560)
    body += el(cutimg(a["subject"], w, h), cx - w // 2, 800 - h + 40, .2, "slide", z=6)
    hh = 520
    body += hand(a["hand"], cx - 160, max(-120, 800 - h - hh + 40), hh, HAND_ROT.get(slug(a["hand"]), 180))
    body += el(title(c[2], c[3], typ, 150, "#141414", accent, 620), 110, 170, .4, "wipe", z=8)
    return body, "background:#F4F2EA"


def d_sundisc(c, sc, typ, rnd):
    bg, accent, ink = sc
    a = c[5]
    body = disc(1180, 520, 400, accent, 2)
    body += el('<div style="width:1920px;height:230px;background:#2A2A2A"><div style="position:absolute;top:110px;width:1920px;height:8px;background:repeating-linear-gradient(90deg,#e8e8e8 0 90px,transparent 90px 170px)"></div></div>', 0, 850, 0, "pop", extra=STILL, z=3)
    w, h = fit_box(a["subject"], 520, 640)
    body += el(cutimg(a["subject"], w, h, grey=True), 1010 - w // 2 + 60, 880 - h, .2, "slide", z=6)
    if png(a.get("second", "")):
        w2, h2 = fit_box(a["second"], 380, 520)
        body += el(cutimg(a["second"], w2, h2, grey=True), 1420 - w2 // 2, 880 - h2, .35, "slide", z=5)
    body += clouds(rnd, 3)
    body += el(title(c[2], c[3], typ, 140, ink, accent, 640), 110, 160, .4, "wipe", z=8)
    return body, f"background:{bg}"


def d_diorama(c, sc, typ, rnd):
    bg, accent, ink = sc
    a = c[5]
    body = ""
    if png(a.get("facade", "")):
        fw, fh = fit_box(a["facade"], 1300, 640)
        body += el(cutimg(a["facade"], fw, fh), 1920 - fw - 60, 700 - fh, .1, "pop", z=2)
    body += el(f'<div style="width:1920px;height:120px;background:{accent}"></div>', 0, 700, 0, "pop", extra=STILL, z=3)
    w, h = fit_box(a["subject"], 560, 420)
    sx = rnd.choice([560, 700, 820])
    body += el(cutimg(a["subject"], w, h), sx, 760 - h + 20, .3, "drop", z=6)
    body += hand(a["hand"], sx - 260, 760 - h - 420, 520, HAND_ROT.get(slug(a["hand"]), 150))
    body += el(title(c[2], c[3], typ, 120, ink, accent, 900), 110, 860, .5, "wipe", z=8)
    return body, f"background:{bg if bg not in ('#F4F2EA', '#E8E1D3', '#EDE6DA', '#F1E3C8', '#EAEAEA') else '#141414'}"


def d_scale(c, sc, typ, rnd):
    bg, accent, ink = sc
    a = c[5]
    body = el(f'<div style="width:1920px;height:1080px"><img src="{jpg(a["ground"])}" style="width:100%;height:100%;object-fit:cover;filter:grayscale(.6) contrast(1.1) brightness(.7)"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    body += el(f'<div style="width:1920px;height:1080px;background:{accent};mix-blend-mode:multiply;opacity:.55"></div>', 0, 0, 0, "pop", extra=STILL, z=2)
    w, h = fit_box(a["subject"], 900, 820)
    body += el(cutimg(a["subject"], w, h), 1060, 980 - h, .2, "drop", z=5)
    if png(a.get("tiny", "")):
        tw, th = fit_box(a["tiny"], 260, 130)
        body += el(cutimg(a["tiny"], tw, th, grey=True), 900, 980 - th, .5, "pop", z=6)
    body += el(title(c[2], c[3], typ, 150, "#F7F2E8", SIG, 800), 110, 160, .4, "wipe", z=8)
    return body, "background:#111"


def d_split(c, sc, typ, rnd):
    bg, accent, ink = sc
    a = c[5]
    body = el(f'<div style="width:960px;height:1080px;background:{accent}"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    body += el(f'<div style="width:960px;height:1080px;background:{bg}"></div>', 960, 0, 0, "pop", extra=STILL, z=1)
    for q, x0, grey in ((a["subject"], 480, True), (a.get("second", ""), 1440, False)):
        if png(q):
            w, h = fit_box(q, 620, 620)
            body += el(cutimg(q, w, h, grey=grey), x0 - w // 2, 520 - h // 2 - 40, .2, "pop", z=5)
    body += el(f'<div style="background:#141414;color:#F4EFE6;padding:14px 34px;white-space:nowrap">{title(c[2], c[3], typ, 92, "#F4EFE6", SIG, 1300, "center")}</div>', 960, 840, .5, "wipe", base="translateX(-50%)", z=8)
    return body, "background:#111"


def d_torn(c, sc, typ, rnd):
    bg, accent, ink = sc
    a = c[5]
    w, h = fit_box(a["subject"], 1500, 900)
    body = el(cutimg(a["subject"], w, h, grey=True), 960 - w // 2, 540 - h // 2, .1, "pop", z=2)
    pts = ",".join(f"{x}% {rnd.uniform(0, 7):.1f}%" for x in range(0, 101, 5)) + "," + ",".join(f"{x}% {100 - rnd.uniform(0, 7):.1f}%" for x in range(100, -1, -5))
    body += el(f'<div style="width:2100px;height:330px;background:{accent};clip-path:polygon({pts});filter:drop-shadow(0 12px 18px rgba(0,0,0,.4))"></div>', -90, 520, .3, "wipe", base="rotate(-4deg)", z=5)
    if png(a.get("second", "")):
        w2, h2 = fit_box(a["second"], 360, 300)
        body += el(cutimg(a["second"], w2, h2), 1380, 540 - h2 // 2 + 40, .5, "drop", z=7)
    body += el(title(c[2], c[3], typ, 150, "#141414" if accent in ("#F2C200", "#FFD23F", "#F4D35E", "#FCD581", "#E9C46A", "#F7B32B") else "#F4EFE6", "#141414", 1100), 150, 560, .6, "wipe", base="rotate(-4deg)", z=8)
    return body, f"background:{bg}"


def _proj(lo, la, box, W=1920, H=1080):
    lon0, lat0, lon1, lat1 = box
    k = min(W / (lon1 - lon0), H / (lat1 - lat0))
    ox = (W - (lon1 - lon0) * k) / 2
    oy = (H - (lat1 - lat0) * k) / 2
    return ox + (lo - lon0) * k, oy + (lat1 - la) * k


def d_routemap(c, sc, typ, rnd):
    """A dark halftone country on grey, a white swath, a red marker route that wiggles to a blue pulse dot."""
    from creatorforge_worker.media import maps
    a = c[5]
    W = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
    if a["country"] == "World":
        box = (-20, -5, 135, 62)
        names = None
    else:
        f = maps._find(a["country"])
        pts = [p for r in f["rings"] for p in r]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        box = (min(xs) - 6, min(ys) - 3, max(xs) + 6, max(ys) + 3)
        names = {a["country"]}
    paths = []
    for cc in W["countries"]:
        rings = cc["r"] if isinstance(cc["r"], list) else json.loads(cc["r"])
        dpath = "".join("M" + " L".join("%.1f %.1f" % _proj(lo, la, box) for lo, la in r) + "Z" for r in rings if len(r) > 3)
        main = names is None or cc["n"] in names
        paths.append((dpath, main))
    svg = ('<svg width="1920" height="1080"><defs><pattern id="ht" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4.5" cy="4.5" r="3.3" fill="#2B2B2B"/></pattern>'
           '<filter id="rough"><feTurbulence baseFrequency=".9" numOctaves="2"/><feDisplacementMap in="SourceGraphic" scale="6"/></filter></defs>')
    for dpath, main in paths:
        svg += f'<path d="{dpath}" fill="{"url(#ht)" if main else "#CFCFCF"}" stroke="#ECECEC" stroke-width="1" filter="url(#rough)"/>'
    pa, pb = maps._find(a["from"]), maps._find(a["to"])
    way = [(pa["lon"], pa["lat"]), (pb["lon"], pb["lat"])]
    if a["country"] == "World":
        way = [(121.5, 31.2), (115, 10), (103.8, 1.3), (80, 6), (52, 13), (43, 12.6), (32.5, 30), (20, 35), (-6, 36), (-10, 44), (4.5, 51.9)]
    pts = [_proj(lo, la, box) for lo, la in way]
    rng = random.Random(c[0])
    dstr = f"M{pts[0][0]:.0f} {pts[0][1]:.0f}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for t in (.33, .66, 1.0):
            x, y = x0 + (x1 - x0) * t + rng.uniform(-40, 40) * (t < 1), y0 + (y1 - y0) * t + rng.uniform(-60, 60) * (t < 1)
            dstr += f" T{x:.0f} {y:.0f}" if t < 1 else f" L{x:.0f} {y:.0f}"
    svg += f'<path d="{dstr}" fill="none" stroke="#E5252A" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>'
    bx, by = pts[-1]
    svg += f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="130" fill="none" stroke="#2F8BE6" stroke-opacity=".25" stroke-width="16"/><circle cx="{bx:.0f}" cy="{by:.0f}" r="40" fill="#2F8BE6"/></svg>'
    body = el(svg, 0, 0, 0, "pop", extra=STILL, z=2)
    body += el(f'<div style="font:600 26px Plex;color:#2B2B2B;background:#F2F2F2;padding:4px 10px">{a["from"].upper()}</div>', pts[0][0] + 20, pts[0][1] - 50, .4, "wipe", z=6)
    body += el(f'<div style="font:600 26px Plex;color:#fff;background:#2F8BE6;padding:4px 10px">{a["to"].upper()}</div>', bx + 54, by - 20, .6, "wipe", z=6)
    if png(a.get("skyline", "")):
        sw, sh = fit_box(a["skyline"], 900, 360)
        body += el(f'<img src="{png(a["skyline"])}" style="width:{sw}px;height:{sh}px;filter:grayscale(1) contrast(1.4) brightness(.8);opacity:.85;mask-image:linear-gradient(0deg,transparent,#000 40%)">', 40, 1080 - sh, .2, "pop", z=3)
    body += el('<div style="width:1920px;height:1080px;backdrop-filter:blur(3px);mask-image:radial-gradient(ellipse at 55% 50%,transparent 45%,#000 85%)"></div>', 0, 0, 0, "pop", extra=STILL, z=5)
    body += el(title(c[2], c[3], typ, 110, "#141414", "#E5252A", 780), 1060, 90, .5, "wipe", z=8)
    return body, "background:#DADADA"


def d_satellite(c, sc, typ, rnd):
    from creatorforge_worker.media import maps
    a = c[5]
    lon0, lat0, lon1, lat1 = a["bbox"]
    img = (D / "maps" / f"{c[0]}.jpg").as_uri()
    body = el(f'<div style="width:1920px;height:1080px;overflow:hidden"><img src="{img}" style="width:100%;height:100%;object-fit:cover"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    if a["country"] == "India":       # the official boundary (studio's world map), drawn over the imagery
        from PIL import Image
        with Image.open(D / "maps" / f"{c[0]}.jpg") as im:
            iw, ih = im.size
        k = max(1920 / iw, 1080 / ih)
        dw, dh = iw * k, ih * k
        offx, offy = (1920 - dw) / 2, (1080 - dh) / 2
        P = lambda lo, la: (offx + (lo - lon0) / (lon1 - lon0) * dw, offy + (lat1 - la) / (lat1 - lat0) * dh)
        rings = maps._find("India")["rings"]
        dpath = "".join("M" + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + "Z" for r in rings if len(r) > 3)
        body += el(f'<svg width="1920" height="1080"><path d="{dpath}" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-opacity=".9" style="filter:drop-shadow(0 0 8px rgba(255,255,255,.8))"/></svg>', 0, 0, .2, "draw", z=3)
        flag = ('<svg width="150" height="100" viewBox="0 0 150 100"><rect width="150" height="33.3" fill="#FF9933"/><rect y="33.3" width="150" height="33.4" fill="#FFFFFF"/>'
                '<rect y="66.7" width="150" height="33.3" fill="#138808"/><circle cx="75" cy="50" r="14" fill="none" stroke="#000080" stroke-width="2"/>'
                + "".join(f'<line x1="75" y1="50" x2="{75 + 14 * math.cos(i * math.pi / 12):.2f}" y2="{50 + 14 * math.sin(i * math.pi / 12):.2f}" stroke="#000080" stroke-width=".8"/>' for i in range(24))
                + '<circle cx="75" cy="50" r="2.6" fill="#000080"/></svg>')
        body += el(f'<div style="box-shadow:0 8px 20px rgba(0,0,0,.5)">{flag}</div>', 885, 180, .4, "pop", z=6)
        lab_y = 300
    else:
        lab_y = 420
    col = {"India": "#22C55E", "Egypt": "#38BDF8", "Nepal": "#F8FAFC", "Chad": "#F59E0B"}[a["country"]]
    label = c[2]
    body += el(f'<div style="font:400 120px Archivo;color:#0B0B0B;-webkit-text-stroke:0;text-shadow:0 0 0 #000;white-space:nowrap;'
               f'paint-order:stroke fill;-webkit-text-stroke:10px {col};letter-spacing:2px">{label}</div>', 960, lab_y, .5, "pop", base="translateX(-50%)", z=7)
    body += el(f'<div style="font:600 24px Plex;color:#F4F4F4;letter-spacing:4px;text-shadow:0 2px 6px #000;white-space:nowrap">{c[3].upper()}</div>', 960, lab_y + 150, .7, "wipe", base="translateX(-50%)", z=7)
    return body, "background:#000"


DEV = {"hand": d_hand, "sundisc": d_sundisc, "diorama": d_diorama, "scale": d_scale, "split": d_split, "torn": d_torn, "routemap": d_routemap, "satellite": d_satellite}


def credit(c):
    a = c[5]
    if c[4] == "satellite":
        return "IMAGERY: NASA BLUE MARBLE NEXT GENERATION VIA GIBS (PUBLIC DOMAIN)" + (" · INDIA: OFFICIAL BOUNDARY" if a["country"] == "India" else "")
    srcs = [REC.get(slug(q), {}) for r, q in a.items() if isinstance(q, str) and r not in ("country", "from", "to")]
    who = sorted({s.get("author", "") for s in srcs if s})
    m = "MAP: NATURAL EARTH, INDIA OFFICIAL BOUNDARY · " if c[4] == "routemap" else ""
    return (m + "PHOTOS: PIXABAY (" + ", ".join(w for w in who if w)[:120] + ") · PIXABAY CONTENT LICENSE").upper()


if __name__ == "__main__":
    only = set(sys.argv[1:])
    out = D / "html"
    out.mkdir(exist_ok=True)
    plan = {}
    for i, c in enumerate(C):
        if only and c[0] not in only:
            continue
        sc = SCHEMES[(i * 7) % len(SCHEMES)]
        typ = TYPES[(i * 3) % len(TYPES)]
        rnd = random.Random(c[0])
        try:
            body, bg = DEV[c[4]](c, sc, typ, rnd)
        except Exception as e:  # noqa: BLE001
            print("SKIP", c[0], type(e).__name__, e)
            continue
        (out / f"{i + 1:02d}_{c[0]}.html").write_text(K.page(FACES + body, bg, 5, .03, credit(c)), encoding="utf-8")
        plan[c[0]] = {"device": c[4], "scheme": sc, "type": typ}
    (D / "data" / "plan.json").write_text(json.dumps(plan, indent=1))
    print(len(plan), "pages")
