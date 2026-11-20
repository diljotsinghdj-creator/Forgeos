"""The second set of devices (owner's reference batches 3-4): glowing sourced counter, notebook, kinetic type, clock
face, warm haze, stickers, torn hole, archival full-bleed, spotlit evidence board, pinned note, worker bar stack,
satellite route, map diorama, open head, statue. Each draws around real photos; nothing here invents a fact."""
import math
import random
from pathlib import Path

from collage2 import el, STILL, red_string, pin_dot, torn_label

FILMS = Path(__file__).resolve().parent.parent
SIG = "#FFDD33"
FACES2 = "<style>" + "".join(
    f"@font-face{{font-family:{n};src:url({(Path('/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts') / (p + '.woff2')).as_uri()})}}"
    for n, p in (("Caveat", "caveat-latin-700-normal"), ("Shadows", "shadows-into-light-latin-400-normal"), ("ISerifI", "instrument-serif-latin-400-italic"),
                 ("PlayfairI2", "playfair-display-latin-700-italic"), ("Grotesk5", "space-grotesk-latin-500-normal"))) + "</style>"


def H(M):
    """Bind helpers from compose50 (passed in to avoid a circular import)."""
    return M.png, M.jpg, M.fit_box, M.cutimg, M.size_of, M.slug


def outline(col="#EBD9B4", w=7):
    d = [(w, 0), (-w, 0), (0, w), (0, -w), (w * .7, w * .7), (-w * .7, w * .7), (w * .7, -w * .7), (-w * .7, -w * .7)]
    return " ".join(f"drop-shadow({x:.0f}px {y:.0f}px 0 {col})" for x, y in d)


def jag(rnd, n=40, r=1.0, amp=.08):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        k = r * (1 - rnd.uniform(0, amp))
        pts.append(f"{50 + 50 * k * math.cos(a):.1f}% {50 + 50 * k * math.sin(a):.1f}%")
    return ",".join(pts)


def torn_top(rnd, n=16, amp=4):
    top = ",".join(f"{x * 100 / n:.1f}% {rnd.uniform(0, amp):.1f}%" for x in range(n + 1))
    return f"polygon({top},100% 100%,0 100%)"


def star4(x, y, s, col, z=7, at=.6):
    return el(f'<svg width="{s}" height="{s}" viewBox="0 0 100 100"><path d="M50 0 C54 38 62 46 100 50 C62 54 54 62 50 100 C46 62 38 54 0 50 C38 46 46 38 50 0Z" fill="{col}"/></svg>', x, y, at, "pop", z=z)


def autosize(text, width, base, k=.55):
    return int(min(base, width / max(1, len(text) * k)))


# ---------------------------------------------------------------------------------------------------------------------
def d_counter(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 30% 50%,#26221E 0%,#0D0C0B 75%)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    flip = a.get("_k", 0) % 2 == 1
    cx, cy, r = (1360 if flip else 560), 560, 330
    TX = 110 if flip else 1000
    body += el(f'<svg width="{2 * r + 20}" height="{2 * r + 20}"><circle cx="{r + 10}" cy="{r + 10}" r="{r}" fill="none" stroke="#E9E4DA" stroke-opacity=".7" stroke-width="3" stroke-dasharray="14 12"/></svg>', cx - r - 10, cy - r - 10, .1, "draw", z=2)
    w, h = fit_box(a["subject"], 470, 470)
    body += el(cutimg(a["subject"], w, h), cx - w // 2, cy - h // 2, .2, "pop", z=5)
    s = autosize(a["number"], 860, 250, .62)
    body += el(f'<div style="font:600 26px Plex;letter-spacing:4px;color:{SIG};text-transform:uppercase">{c[2]}</div>', TX, 290, .3, "wipe", z=6)
    body += el(f'<div style="font:400 {s}px/1 Anton;color:#FF8A1E;text-shadow:0 0 18px rgba(255,138,30,.85),0 0 60px rgba(255,90,0,.55);white-space:nowrap">{a["number"]}</div>', TX, 350, .4, "pop", z=6)
    body += el(f'<div style="font:400 50px/1.1 ISerifI;color:#F3EFE6;width:860px">{c[3]}</div>', TX, 360 + s + 20, .6, "wipe", z=6)
    body += el(f'<div style="font:500 18px Plex;letter-spacing:2px;color:#9C958A;border-top:1px solid #4a453f;padding-top:12px;width:860px">SOURCE: {a["src"]}</div>', TX, 360 + s + 110, .7, "wipe", z=6)
    return body, "background:#0D0C0B"


def d_notebook(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el(f'<div style="width:1920px;height:1080px;overflow:hidden"><img src="{jpg(a["paper"])}" style="width:100%;height:100%;object-fit:cover;filter:saturate(.6) brightness(1.06) contrast(1.05)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    w, h = fit_box(a["subject"], 460, 460)
    sx, sy = 1300, 560 - h // 2 + 40
    body += el(cutimg(a["subject"], w, h), sx, sy, .2, "drop", z=5)
    s = autosize(a["word"], 900, 210, .42)
    body += el(f'<div style="font:700 {s}px/1 Caveat;color:#2A2A2A;white-space:nowrap;transform:rotate(-4deg)">{a["word"]}</div>', 170, 430, .4, "wipe", z=6)
    x0, y0 = 170 + min(900, len(a["word"]) * s * .42) * .6, 430 + s + 30
    path = f"M{x0:.0f} {y0:.0f} C {x0 + 200:.0f} {y0 + 160:.0f}, {sx - 220} {sy + h + 60}, {sx - 30} {sy + h * .6:.0f}"
    body += el(f'<svg width="1920" height="1080"><defs><marker id="ah" markerWidth="16" markerHeight="16" refX="8" refY="8" orient="auto"><path d="M0 0 L16 8 L0 16" fill="none" stroke="#2A2A2A" stroke-width="3"/></marker></defs>'
               f'<path d="{path}" fill="none" stroke="#2A2A2A" stroke-width="5" stroke-linecap="round" marker-end="url(#ah)" filter="url(#rough)"/></svg>', 0, 0, .6, "draw", z=4)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:4px;color:#2A2A2A"><span class="hl" style="padding:0 6px">{c[2].upper()}</span></div>', 170, 180, .2, "wipe", z=6)
    body += el(f'<div style="font:400 44px Caveat;color:#5A5A5A">{c[3]}</div>', 170, 240, .3, "wipe", z=6)
    return body, "background:#F2F0EA"


def d_kinetic(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    bg, accent, ink = sc
    a = c[5]
    grid = "background:#EFEEE9;background-image:linear-gradient(rgba(0,0,0,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.06) 1px,transparent 1px);background-size:80px 80px"
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{grid};z-index:0"></div>'
    l1, l2, l3 = a["lines"]
    ys = (250, 420, 640)
    for y in (ys[0] + 120, ys[1] + 170, ys[2] + 100):
        body += el(f'<div style="width:1920px;height:0;border-top:2px dashed rgba(40,90,200,.35)"></div>', 0, y, .05, "wipe", extra=STILL, z=1)
    body += el('<div style="width:0;height:1080px;border-left:2px dashed rgba(40,90,200,.35)"></div>', 190, 0, .05, "wipe", extra=STILL, z=1)
    body += el(f'<div style="font:400 150px/1 ISerifI;color:#161616">{l1}</div>', 200, ys[0], .2, "wipe", z=5)
    body += el(f'<div style="font:400 200px/1 Anton;color:{accent if accent not in (SIG,) else "#E63946"};letter-spacing:2px">{l2}</div>', 200, ys[1], .45, "pop", z=5)
    body += el(f'<div style="font:400 130px/1 Caveat;color:#161616"><span class="hl" style="padding:0 10px">{l3}</span></div>', 200, ys[2], .7, "wipe", z=5)
    w, h = fit_box(a["subject"], 560, 560)
    body += el(cutimg(a["subject"], w, h), 1560 - w // 2, 520 - h // 2, .3, "drop", base="rotate(-8deg)", z=4)
    body += star4(1240, 200, 70, SIG) + star4(1700, 820, 44, "#161616", at=.8)
    body += el(f'<div style="font:500 20px Plex;letter-spacing:4px;color:#555">{c[2].upper()} · {c[3].upper()}</div>', 200, 900, .8, "wipe", z=5)
    return body, "background:#EFEEE9"


def d_clockface(M, c, sc, typ, rnd):
    a = c[5]
    cx, cy, r = 1340, 520, 330
    nums = "".join(f'<text x="{cx + (r - 62) * math.sin(i * math.pi / 6):.0f}" y="{cy - (r - 62) * math.cos(i * math.pi / 6) + 18:.0f}" text-anchor="middle" font-family="Inter" font-size="52" fill="#1A1A1A">{i if i else 12}</text>' for i in range(12))
    ticks = "".join(f'<line x1="{cx + (r - 22) * math.sin(i * math.pi / 30):.1f}" y1="{cy - (r - 22) * math.cos(i * math.pi / 30):.1f}" x2="{cx + (r - (34 if i % 5 else 44)) * math.sin(i * math.pi / 30):.1f}" y2="{cy - (r - (34 if i % 5 else 44)) * math.cos(i * math.pi / 30):.1f}" stroke="#1A1A1A" stroke-width="{4 if i % 5 == 0 else 2}"/>' for i in range(60))
    th, tm = a.get("time", (2, 3))                   # the time the clock shows, set per frame
    hh_ang, mm_ang = (th % 12) * 30 + tm * .5, tm * 6
    hand = lambda ang, L, wd, col: f'<line x1="{cx}" y1="{cy}" x2="{cx + L * math.sin(math.radians(ang)):.0f}" y2="{cy - L * math.cos(math.radians(ang)):.0f}" stroke="{col}" stroke-width="{wd}" stroke-linecap="round"/>'
    svg = (f'<svg width="1920" height="1080"><circle cx="{cx}" cy="{cy + 14}" r="{r + 26}" fill="rgba(0,0,0,.18)" filter="blur(14px)" style="filter:blur(14px)"/>'
           f'<circle cx="{cx}" cy="{cy}" r="{r + 24}" fill="#D8D8D8"/><circle cx="{cx}" cy="{cy}" r="{r + 8}" fill="#9A9A9A"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="#FAFAF7"/>'
           f'{ticks}{nums}{hand(hh_ang, 170, 12, "#1A1A1A")}{hand(mm_ang, 250, 8, "#1A1A1A")}{hand(200, 270, 3, "#D7262B")}<circle cx="{cx}" cy="{cy}" r="12" fill="#1A1A1A"/></svg>')
    grid = "background:#F1EEE7;background-image:linear-gradient(rgba(0,0,0,.07) 2px,transparent 2px),linear-gradient(90deg,rgba(0,0,0,.07) 2px,transparent 2px);background-size:120px 120px"
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{grid};z-index:0"></div>'
    body += el(svg, 0, 0, .1, "pop", z=3)
    ws = min(250, int(800 / (.47 * len(a["word"]))))
    body += el(f'<div style="font:400 {ws}px/1 Anton;color:#D7262B;letter-spacing:6px;white-space:nowrap">{a["word"]}</div>', 150, 300 + (250 - ws) // 2, .3, "pop", z=5)
    ss = min(96, int(790 / (.42 * len(a["small"]))))
    body += el(f'<div style="font:700 {ss}px/1 Caveat;color:#1A1A1A;white-space:nowrap">{a["small"]}</div>', 170, 570, .55, "wipe", z=5)
    body += el(f'<div style="font:500 22px Plex;letter-spacing:4px;color:#444;width:640px">{c[2].upper()}<br><span style="color:#888">{c[3].upper()}</span></div>', 170, 760, .7, "wipe", z=5)
    body += star4(1700, 150, 90, SIG) + star4(1040, 860, 46, "#D7262B", at=.75) + star4(960, 210, 34, "#1A1A1A", at=.8)
    return body, "background:#F1EEE7"


def d_haze(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el(f'<div style="width:1920px;height:1080px;overflow:hidden"><img src="{jpg(a["ground"])}" style="width:104%;height:104%;margin:-2%;object-fit:cover;filter:sepia(.35) saturate(1.25) contrast(.92) brightness(1.02) blur(2px)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 70% 20%,rgba(255,196,120,.75) 0%,rgba(255,150,80,.25) 35%,transparent 70%);mix-blend-mode:screen"></div>', 0, 0, 0, "pop", extra=STILL, z=2)
    body += el('<div style="width:1920px;height:1080px;background:linear-gradient(0deg,rgba(30,12,4,.75) 0%,transparent 55%)"></div>', 0, 0, 0, "pop", extra=STILL, z=3)
    k = a.get("_k", 0) % 3
    tx, ty = [(130, 690), (130, 110), (900, 690)][k]
    body += el(f'<div style="font:400 160px/1 ISerifI;color:#FFF4E2;text-shadow:0 6px 30px rgba(0,0,0,.45);white-space:nowrap">{c[2]}</div>', tx, ty, .4, "wipe", z=6)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:5px;color:{SIG}">{c[3].upper()}</div>', tx + 6, ty + 190, .6, "wipe", z=6)
    return body, "background:#1E0F06"


def d_sticker(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    ground = "background:#A9773F;background-image:radial-gradient(rgba(60,30,8,.35) 2.2px,transparent 2.6px);background-size:12px 12px"
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{ground};z-index:0"></div>'
    body += el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 60% 45%,rgba(255,220,160,.35),transparent 65%)"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    w2, h2 = fit_box(a["second"], 440, 340)
    body += el(f'<img src="{png(a["second"])}" style="width:{w2}px;height:{h2}px;filter:grayscale(1) contrast(1.2) {outline()} drop-shadow(0 18px 18px rgba(0,0,0,.4));transform:rotate(-5deg)">', 140, 640, .2, "drop", z=4)
    w, h = fit_box(a["subject"], 900, 470)
    sx, sy = 860, 470
    body += el(f'<img src="{png(a["subject"])}" style="width:{w}px;height:{h}px;filter:saturate(1.15) {outline()} drop-shadow(0 24px 24px rgba(0,0,0,.45));transform:rotate(3deg)">', sx, sy, .4, "drop", z=5)
    loop = f'<svg width="{w + 200}" height="{h + 200}"><ellipse cx="{(w + 200) / 2}" cy="{(h + 200) / 2}" rx="{w / 2 + 70}" ry="{h / 2 + 60}" fill="none" stroke="{SIG}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{3.0 * (w + h) + 300} 9999" transform="rotate(-6 {(w + 200) / 2} {(h + 200) / 2})" filter="url(#rough)"/></svg>'
    body += el(loop, sx - 100, sy - 100, .7, "draw", z=6)
    pts = [(140 + w2 + 10, 640 + h2 // 2), (sx - 40, sy + h // 2 + 20)]
    body += el(f'<svg width="1920" height="1080"><path d="M{pts[0][0]} {pts[0][1]} Q {(pts[0][0] + pts[1][0]) / 2} {pts[0][1] - 180} {pts[1][0]} {pts[1][1]}" fill="none" stroke="#F4EEDF" stroke-width="6" stroke-dasharray="4 14" stroke-linecap="round"/></svg>', 0, 0, .55, "draw", z=3)
    body += torn_label(a.get("tag", c[2].split()[-1].upper()), 1180, 980, 44, "#F4EEDF", "#141414", rot=-3, at=.8, z=8, font="Archivo", seed=4)
    body += el(f'<div style="font:400 150px/0.92 Archivo;color:#F4EEDF;text-shadow:0 6px 0 rgba(60,30,8,.6)">{c[2].upper()}</div>', 120, 120, .3, "wipe", z=7)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:5px;color:#2B1606">{c[3].upper()}</div>', 128, 400, .5, "wipe", z=7)
    return body, "background:#A9773F"


def d_tornhole(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el(f'<div style="width:1920px;height:1080px;overflow:hidden"><img src="{jpg(a["subject"])}" style="width:100%;height:100%;object-fit:cover;filter:saturate(1.1) contrast(1.08)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    flip = a.get("_k", 0) % 2 == 1
    hx, hy, hw, hh = (80 if flip else 1020), 120, 820, 760
    OX = 900 if flip else 0
    poly = jag(rnd, 46, 1.0, .12)
    paper = ("background:#EDE6D6;background-image:radial-gradient(rgba(120,100,70,.08) 1px,transparent 1.5px);background-size:6px 6px")
    pts = []
    for i in range(46):
        ang = 2 * math.pi * i / 46
        k = 1 - rnd.uniform(0, .12)
        pts.append((hx + hw / 2 + hw / 2 * k * math.cos(ang), hy + hh / 2 + hh / 2 * k * math.sin(ang)))
    P = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    svg = ('<svg width="1920" height="1080"><defs><mask id="hole"><rect width="1920" height="1080" fill="#fff"/><polygon points="' + P + '" fill="#000"/></mask>'
           '<pattern id="pp" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#EDE6D6"/><circle cx="3" cy="3" r=".9" fill="rgba(120,100,70,.12)"/></pattern>'
           '<filter id="sh"><feDropShadow dx="0" dy="0" stdDeviation="9" flood-opacity=".6"/></filter></defs>'
           f'<polygon points="{P}" fill="none" stroke="#FBF7EE" stroke-width="16" filter="url(#rough)"/>'
           '<rect width="1920" height="1080" fill="url(#pp)" mask="url(#hole)" filter="url(#sh)"/></svg>')
    body += el(svg, 0, 0, .1, "pop", extra=STILL, z=2)
    if png(a.get("second", "")):
        w2, h2 = fit_box(a["second"], 380, 300)
        body += el(cutimg(a["second"], w2, h2), -60, 1080 - h2 + 40, .5, "drop", base="rotate(14deg)", z=5)
    body += el(f'<div style="width:560px;height:46px;background:{SIG}"></div>', OX + 120, 470, .3, "wipe", z=3)
    body += el(f'<div style="width:380px;height:46px;background:{SIG}"></div>', OX + 120, 650, .4, "wipe", z=3)
    words = c[2].split()
    lead, rest = (" ".join(words[:2]), " ".join(words[2:])) if len(words) > 2 else (words[0] if len(words) > 1 else "", " ".join(words[1:]) if len(words) > 1 else words[0])
    body += el(f'<div style="font:400 120px/1 ISerifI;color:#141414">{lead}</div>', OX + 140, 300, .3, "wipe", z=4)
    body += el(f'<div style="font:900 140px/0.95 Playfair;color:#141414;width:820px">{rest.upper()}</div>', OX + 130, 420, .45, "pop", z=4)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:5px;color:#5A5040">{c[3].upper()}</div>', OX + 140, 760, .6, "wipe", z=4)
    # editorial poster details: issue line, crop marks, a barcode-like rule and a small index (decoration, no claims)
    body += el('<div style="font:600 16px Plex;letter-spacing:4px;color:#5A5040;width:1700px;display:flex;justify-content:space-between"><span>PRINT FACTS · WORLD</span><span>NO. 01</span></div>', 120, 60, .2, "wipe", z=4)
    body += el('<div style="width:200px;height:44px;background:repeating-linear-gradient(90deg,#141414 0 3px,transparent 3px 6px,#141414 6px 7px,transparent 7px 11px)"></div>', OX + 140, 920, .5, "pop", z=4)
    for x, y in ((60, 40), (1840, 40), (60, 1020), (1840, 1020)):
        body += el('<div style="font:300 34px Inter;color:#5A5040">+</div>', x, y, .1, "pop", extra=STILL, z=4)
    return body, "background:#EDE6D6"


def d_archival(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    from PIL import Image
    with Image.open(Path(jpg(a["loc"])[7:])) as im:
        w0, h0 = im.size
    if h0 > w0:
        flip = len(c[0]) % 2 == 0
        ph = 940
        pw = int(ph * w0 / h0)
        body = el(f'<div style="background:#F3EFE4;padding:20px 20px 70px;box-shadow:0 30px 50px rgba(0,0,0,.6)"><img src="{jpg(a["loc"])}" style="width:{pw}px;height:{ph - 90}px;object-fit:cover;display:block;filter:grayscale(1) contrast(1.1) sepia(.15)"></div>', 140 if flip else 1100, 60, .1, "drop", base=f"rotate({-2.5 if flip else 2.5}deg)", z=3)
        tx = 980 if flip else 110
        body += el(f'<div style="font:900 130px/0.95 Playfair;color:#F3EFE4;width:880px">{c[2]}</div>', tx, 260, .3, "wipe", z=5)
        body += el(f'<div style="font:600 24px Plex;letter-spacing:4px;color:#141414;background:{SIG};padding:8px 14px;display:inline-block">{c[3].upper()}</div>', tx + 6, 640, .5, "wipe", z=5)
        body += el('<div style="font:600 18px Plex;letter-spacing:3px;color:#BFB6A4">LIBRARY OF CONGRESS</div>', tx + 6, 720, .6, "wipe", z=5)
        return body, "background:#1E1A16;background-image:radial-gradient(ellipse at 60% 40%,#3A3128,#141110 75%)"
    body = el(f'<div style="width:1920px;height:1080px;overflow:hidden"><img src="{jpg(a["loc"])}" style="width:112%;height:120%;margin:-3.5% 0 0 -6%;object-fit:cover;filter:grayscale(1) contrast(1.12) sepia(.12)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(0,0,0,.72) 0%,transparent 48%)"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    body += el(f'<div style="font:900 132px/0.95 Playfair;color:#F7F2E8;width:980px">{c[2]}</div>', 120, 300, .3, "wipe", z=5)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:4px;color:#141414;background:{SIG};padding:8px 14px;display:inline-block">{c[3].upper()}</div>', 124, 640, .5, "wipe", z=5)
    body += el('<div style="font:600 18px Plex;letter-spacing:3px;color:#F7F2E8;border:2px solid #F7F2E8;padding:8px 12px;transform:rotate(-3deg)">LIBRARY OF CONGRESS</div>', 1360, 80, .6, "pop", z=5)
    return body, "background:#000"


DOCS = {"louisiana": ("vox-ten-2026-11-14/assets/louisiana_doc.jpg", "1803"), "nineteenth": ("vox-ten-2026-11-14/assets/nineteenth_doc.jpg", "1919"),
        "marshall": ("vox-ten-2026-11-14/assets/marshall_doc.jpg", "1948"), "moonmemo": ("moon-disaster-60/assets/RN100_6-1.jpg", "1969")}


def d_spotboard(M, c, sc, typ, rnd):
    a = c[5]
    cork = "background:#A87B4C;background-image:radial-gradient(rgba(60,35,15,.35) 1.4px,transparent 1.8px),radial-gradient(rgba(230,190,140,.25) 1.2px,transparent 1.6px);background-size:7px 7px,11px 11px;background-position:0 0,3px 5px"
    body = el(f'<div style="width:1760px;height:960px;{cork};border:22px solid #4A3424;box-shadow:0 30px 60px rgba(0,0,0,.6)"></div>', 80, 60, 0, "pop", extra=STILL, z=0)
    spots = [(240, 200, -6), (720, 170, 4), (1200, 230, -3), (1450, 470, 6)]
    pins = []
    for i, ((x, y, rot), key) in enumerate(zip(spots, a["docs"])):
        if key in DOCS:
            p, year = DOCS[key]
            src = (FILMS / p).as_uri()
        else:                                    # a Library of Congress item downloaded for this film
            src = (M.A / f"{key}.jpg").as_uri(); year = a["years"][i]
        body += el(f'<div style="background:#F6F1E6;padding:12px;box-shadow:0 14px 24px rgba(0,0,0,.45);transform:rotate({rot}deg)"><img src="{src}" style="width:300px;height:390px;object-fit:cover;object-position:top;display:block;filter:sepia(.15) contrast(1.05)"></div>', x, y, .15 + .15 * len(pins), "drop", z=3)
        body += torn_label(year, x + 40, y + 400, 34, SIG, "#141414", rot=rot, at=.5 + .1 * len(pins), z=6, font="Mono", seed=len(pins) + 2)
        pins.append((x + 162, y + 18))
    body += red_string(pins, at=.7, z=5)
    for x, y in pins:
        body += pin_dot(x, y, z=7)
    body += el(f'<div style="background:#F6F1E6;padding:22px 30px;box-shadow:0 12px 22px rgba(0,0,0,.45);transform:rotate(-2deg)"><div style="font:400 92px/1 Marker;color:#141414">{c[2]}</div><div style="font:600 22px Plex;letter-spacing:4px;color:#7A2A20;margin-top:10px">{c[3].upper()}</div></div>', 220, 700, .4, "drop", z=6)
    body += el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse 52% 60% at 50% 46%,transparent 0%,rgba(0,0,0,.25) 55%,rgba(0,0,0,.88) 100%)"></div>', 0, 0, 0, "pop", extra=STILL, z=20)
    return body, "background:#0A0806"


def d_pinnote(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    grid = "background:#ECECEA;background-image:linear-gradient(rgba(0,0,0,.09) 2px,transparent 2px),linear-gradient(90deg,rgba(0,0,0,.09) 2px,transparent 2px);background-size:110px 110px"
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{grid};z-index:0"></div>'
    body += el('<div style="width:1920px;height:1080px;background:linear-gradient(115deg,transparent 40%,rgba(0,0,0,.10) 55%,transparent 70%)"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    pw, ph = 760, 820
    px, py = 580, 150
    paper = f'<img src="{png(a["paper"])}" style="width:{pw}px;height:{ph}px;object-fit:fill;filter:sepia(.25) drop-shadow(0 26px 26px rgba(0,0,0,.35))">' if png(a.get("paper", "")) else f'<div style="width:{pw}px;height:{ph}px;background:#E9E1CD"></div>'
    body += el(paper, px, py, .1, "drop", base="rotate(-5deg)", z=3)
    body += el('<svg width="1920" height="1080"><path d="M960 190 L 0 120" stroke="#C0262D" stroke-width="10"/><path d="M960 190 L 1920 330" stroke="#C0262D" stroke-width="10"/></svg>', 0, 0, .3, "draw", z=2)
    body += pin_dot(960, 190, z=8)
    s = autosize(a["word"], 600, 150, .5)
    body += el(f'<div style="font:700 {s}px/1 Caveat;color:#C0262D;transform:rotate(-8deg)">{a["word"]}</div>', 720, 470, .5, "wipe", z=6)
    body += el(f'<div style="font:500 26px Plex;color:#3A3A3A;letter-spacing:3px;transform:rotate(-8deg)">{a["small"].upper()}</div>', 740, 430, .4, "wipe", z=6)
    if png(a.get("second", "")):
        w2, h2 = fit_box(a["second"], 460, 460)
        body += el(cutimg(a["second"], w2, h2), 1380, 60, .6, "slide", base="rotate(28deg)", z=7)
    clip = '<svg width="120" height="260" viewBox="0 0 120 260"><path d="M30 230 V60 a30 30 0 0 1 60 0 V200 a18 18 0 0 1 -36 0 V80" fill="none" stroke="#8A8F96" stroke-width="9" stroke-linecap="round"/></svg>'
    body += el(clip, 380, 700, .7, "pop", base="rotate(-35deg)", z=7)
    body += el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:#141414;background:{SIG};padding:8px 14px">{c[3].upper()}</div>', 1380, 900, .8, "wipe", z=8)
    return body, "background:#ECECEA"


def d_barstack(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    ground = "background:#E2AE45;background-image:radial-gradient(rgba(150,90,10,.35) 2px,transparent 2.4px);background-size:11px 11px"
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{ground};z-index:0"></div>'
    body += el(f'<div style="width:2000px;height:420px;background:{SIG};clip-path:{torn_top(rnd, 24, 6)}"></div>', -40, 560, 0, "pop", extra=STILL, z=1)
    tops = []
    if a.get("values"):                              # real numbers only, bars from zero
        vmax = max(v for _, v, _ in a["values"]) * 1.1
        x = 420
        for i, (lab, v, txt) in enumerate(a["values"]):
            hgt = int(470 * v / vmax)
            col = ("#2E4A7D", "#E9573F")[i == len(a["values"]) - 1]
            body += el(f'<div style="width:300px;height:{hgt}px;background:{col};clip-path:{torn_top(random.Random(i), 10, 3)};box-shadow:0 10px 20px rgba(0,0,0,.3)"></div>', x, 1080 - hgt, .1 + .1 * i, "drop", z=3)
            ty = 1080 - hgt + 30 if hgt > 220 else 1080 - hgt - 150   # short bar: numbers sit above it
            tc = "#F4EEDF" if hgt > 220 else "#141414"
            body += el(f'<div style="font:400 64px Archivo;color:{tc};width:300px;text-align:center">{txt}</div>', x, ty, .5, "pop", z=4)
            body += el(f'<div style="font:600 20px Plex;color:{tc};width:300px;text-align:center;letter-spacing:2px">{lab}</div>', x, ty + 80, .5, "pop", z=4)
            tops.append((x + 35, 1080 - hgt))
            x += 360
    else:                                            # no data: a plain paper pedestal, not a chart
        body += el(f'<div style="width:380px;height:300px;background:#E9573F;clip-path:{torn_top(random.Random(3), 10, 3)};box-shadow:0 10px 20px rgba(0,0,0,.3)"></div>', 900, 780, .1, "drop", z=3)
        tops.append((975, 780))
    tx, ty = tops[-1]
    w, h = fit_box(a["subject"], 260, 330)
    body += el(cutimg(a["subject"], w, h, grey=True, extra=f"filter:grayscale(1) contrast(1.2) {outline('#F4EEDF', 6)} drop-shadow(0 14px 16px rgba(0,0,0,.4))"), tx + 115 - w // 2, ty - h + 14, .6, "drop", z=6)
    if png(a.get("second", "")):
        w2, h2 = fit_box(a["second"], 460, 420)
        body += el(cutimg(a["second"], w2, h2), 1420, 1080 - h2 - 30, .7, "slide", base="rotate(-8deg)", z=5)
    body += torn_label("more", 1180, 960, 56, "#F4EEDF", "#141414", rot=-2, at=.85, z=8, font="Archivo", seed=9)
    body += el(f'<div style="font:400 120px/0.92 Archivo;color:#141414;width:900px">{c[2].upper()}</div>', 100, 90, .3, "wipe", z=7)
    body += el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:#3B2A08">{c[3].upper()}</div>', 104, 330, .5, "wipe", z=7)
    if a.get("src"):
        body += el(f'<div style="font:500 14px/1.5 Plex;letter-spacing:1px;color:#3B2A08;width:640px">{a["src"]}</div>', 104, 372, .5, "wipe", z=7)
    return body, "background:#E2AE45"


def d_satroute(M, c, sc, typ, rnd):
    a = c[5]
    lon0, lat0, lon1, lat1 = a["bbox"]
    P = lambda lo, la: ((lo - lon0) / (lon1 - lon0) * 1920, (lat1 - la) / (lat1 - lat0) * 1080)
    img = (Path(__file__).resolve().parent / "maps" / f"{c[0]}.jpg").as_uri()
    body = el(f'<img src="{img}" style="width:1920px;height:1080px;display:block;filter:saturate(1.15) contrast(1.12)">', 0, 0, 0, "pop", extra=STILL, z=0)
    pts = [P(lo, la) for lo, la in a["route"]]
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    body += el(f'<svg width="1920" height="1080"><path d="{d}" fill="none" stroke="#FFC23D" stroke-width="16" stroke-opacity=".35" stroke-linejoin="round" style="filter:blur(4px)"/>'
               f'<path d="{d}" fill="none" stroke="#FFC23D" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg>', 0, 0, .3, "draw", z=3)
    for (x, y), lab, at in ((pts[0], a["from"], .3), (pts[-1], a["to"], .9)):
        body += el('<div style="width:34px;height:34px;border-radius:50%;background:#FF5A1F;border:6px solid #FFF;box-shadow:0 0 0 10px rgba(255,90,31,.35)"></div>', x - 23, y - 23, at, "pop", z=5)
        body += el(f'<div style="font:400 40px Archivo;color:#FFF;text-shadow:0 3px 10px rgba(0,0,0,.8);white-space:nowrap">{lab}</div>', x + 40, y - 26, at + .1, "wipe", z=5)
    mx = sum(x for x, y in pts) / len(pts); my = sum(y for x, y in pts) / len(pts)
    tx = 110 if mx > 960 else min(1060, 1920 - int(len(c[2]) * 54) - 120)
    ty = 800 if my < 540 else 110
    body += el(f'<div style="background:rgba(10,10,10,.55);padding:18px 26px"><div style="font:400 76px/1 Archivo;color:#FFF;white-space:nowrap">{c[2].upper()}</div>'
               f'<div style="font:600 22px Plex;letter-spacing:5px;color:{SIG};white-space:nowrap;margin-top:12px">{c[3].upper()}</div></div>', tx, ty, .4, "wipe", z=6)
    return body, "background:#000"


def d_mapdiorama(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 50% 70%,#5A3E26 0%,#22160D 70%)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el(f'<div style="width:1920px;height:1080px;perspective:1300px"><div style="position:absolute;left:210px;top:330px;width:1500px;height:980px;transform:rotateX(56deg) rotateZ(-6deg);transform-origin:50% 50%;box-shadow:0 40px 80px rgba(0,0,0,.7)">'
               f'<img src="{jpg(a["paper"])}" style="width:100%;height:100%;object-fit:cover;filter:sepia(.55) contrast(1.05) brightness(.95)"></div></div>', 0, 0, .05, "pop", extra=STILL, z=1)
    w, h = fit_box(a["subject"], 760, 480)
    body += el(cutimg(a["subject"], w, h, extra="filter:sepia(.35) saturate(1.1) contrast(1.05) drop-shadow(0 30px 24px rgba(0,0,0,.55))"), 1000 - w // 2, 760 - h, .4, "drop", z=4)
    if png(a.get("second", "")):
        w2, h2 = fit_box(a["second"], 360, 300)
        body += el(cutimg(a["second"], w2, h2, extra="filter:sepia(.35) drop-shadow(0 22px 18px rgba(0,0,0,.55))"), 1430, 840 - h2, .6, "drop", z=5)
    body += el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 55% 55%,rgba(255,200,120,.22),transparent 55%);mix-blend-mode:screen"></div>', 0, 0, 0, "pop", extra=STILL, z=6)
    body += el(f'<div style="font:900 130px/0.95 Playfair;color:#F2E6CF;text-shadow:0 6px 20px rgba(0,0,0,.6)">{c[2]}</div>', 110, 90, .3, "wipe", z=7)
    body += el(f'<div style="font:400 48px ISerifI;color:{SIG}">{c[3]}</div>', 116, 230, .5, "wipe", z=7)
    return body, "background:#22160D"


def d_openhead(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#F7F5F0"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:700px;height:700px;border-radius:50%;background:#F25C05"></div>', 1060, 60, .1, "pop", z=1)
    words = c[2].upper().split()
    body += el(f'<div style="font:400 {min(108, int(560 / (max(len(w) for w in words) * .86)))}px/0.95 Archivo;color:#FFF;width:560px;text-align:center">{"<br>".join(words)}</div>', 1130, 250, .5, "wipe", z=2)
    w, h = fit_box(a["subject"], 640, 820)
    bx, by = 520, 1080 - h + 40
    cut = .40
    src = png(a["subject"])
    flt = "grayscale(1) contrast(1.2) drop-shadow(0 20px 22px rgba(0,0,0,.35))"
    body += el(f'<img src="{src}" style="width:{w}px;height:{h}px;filter:{flt};clip-path:inset({cut * 100:.0f}% 0 0 0)">', bx, by, .1, "pop", z=4)
    body += el(f'<div style="width:{w * .62:.0f}px;height:70px;border-radius:50%;background:#F25C05;box-shadow:inset 0 10px 20px rgba(0,0,0,.35)"></div>', bx + w * .19, by + h * cut - 35, .2, "pop", z=5)
    w2, h2 = fit_box(a["second"], 420, 380)
    body += el(cutimg(a["second"], w2, h2), bx + w // 2 - w2 // 2 + 60, by + h * cut - h2 + 40, .45, "drop", base="rotate(-24deg)", z=6)
    body += el(f'<img src="{src}" style="width:{w}px;height:{h}px;filter:{flt};clip-path:inset(0 0 {(1 - cut) * 100:.0f}% 0)">', bx, by, .3, "pop", base=f"translate(-150px,-{int(h * cut * .9)}px) rotate(-24deg)", z=7)
    body += star4(bx + w + 40, by + h * cut - 120, 60, SIG, z=8)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:5px;color:#141414">{c[3].upper()}</div>', 1140, 820, .7, "wipe", z=8)
    return body, "background:#F7F5F0"


def d_statue(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#F6EFE2"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<svg width="1920" height="1080"><path d="M-40 360 C 220 120, 420 120, 520 320 S 900 780, 1240 520 S 1700 260, 1980 470" fill="none" stroke="#A3121B" stroke-width="9" stroke-linecap="round"/></svg>', 0, 0, .2, "draw", z=1)
    w, h = fit_box(a["subject"], 760, 1040)
    sx, sy = 200, 1080 - h + 60
    body += el(cutimg(a["subject"], w, h, grey=True), sx, sy, .1, "drop", z=3)
    w2, h2 = fit_box(a["second"], 300, 300)
    body += el(cutimg(a["second"], w2, h2), sx + w - 40, sy + int(h * .36), .5, "pop", base="rotate(-8deg)", z=5)
    body += el(f'<div style="font:700 120px/0.95 Grotesk;color:#141414;letter-spacing:-3px;text-align:right;width:900px">{c[2].lower()}</div>', 900, 260, .4, "wipe", z=6)
    body += el(f'<div style="font:400 64px/1 ISerifI;color:#141414;text-align:right;width:900px"><span class="hl" style="padding:0 8px">{c[3]}</span></div>', 900, 560, .6, "wipe", z=6)
    return body, "background:#F6EFE2"


DEV2 = {"counter": d_counter, "notebook": d_notebook, "kinetic": d_kinetic, "clockface": d_clockface, "haze": d_haze, "sticker": d_sticker,
        "tornhole": d_tornhole, "archival": d_archival, "spotboard": d_spotboard, "pinnote": d_pinnote, "barstack": d_barstack,
        "satroute": d_satroute, "mapdiorama": d_mapdiorama, "openhead": d_openhead, "statue": d_statue}


# ---- batch 5 (owner's references, 2026-11-14 evening) -----------------------------------------------------------------
RANSOM = [("#E63946", "#FFF"), ("#F4EEDF", "#141414"), ("#2E86AB", "#FFF"), ("#FFDD33", "#141414"), ("#141414", "#F4EEDF"), ("#3A7D44", "#FFF")]
FONTS_R = ["Anton", "Playfair", "Archivo", "Bebas", "Mono", "Serif"]


def ransom(word, size, seed):
    r = random.Random(seed)
    out = ""
    for i, ch in enumerate(word):
        bg, fg = RANSOM[(i + seed) % len(RANSOM)]
        out += (f'<span style="display:inline-block;background:{bg};color:{fg};font:400 {int(size * r.uniform(.85, 1.1))}px/1 {FONTS_R[(i * 2 + seed) % len(FONTS_R)]};'
                f'padding:6px 10px;margin:0 3px;transform:rotate({r.uniform(-8, 8):.1f}deg);box-shadow:0 4px 8px rgba(0,0,0,.25)">{ch}</span>')
    return out


def bolt(x, y, s, rot, at=.7, z=7):
    return el(f'<svg width="{s}" height="{s * 1.4:.0f}" viewBox="0 0 50 70"><path d="M30 0 L8 38 H24 L16 70 L44 26 H28 Z" fill="#141414" stroke="#FFF" stroke-width="3"/></svg>', x, y, at, "pop", base=f"rotate({rot}deg)", z=z)


def d_ransom(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#E4E1DA;background-image:radial-gradient(rgba(0,0,0,.05) 1px,transparent 1.4px);background-size:5px 5px"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    grid = "background-image:linear-gradient(#333 1.5px,transparent 1.5px),linear-gradient(90deg,#333 1.5px,transparent 1.5px);background-size:62px 62px;opacity:.6"
    body += el(f'<div style="width:560px;height:620px;{grid}"></div>', 980, 110, .05, "pop", extra=STILL, z=1)
    body += el('<div style="width:440px;height:440px;border-radius:50%;background:#C8333A"></div>', 740, 190, .1, "pop", z=2)
    body += el('<svg width="900" height="420"><polygon points="450,0 900,420 0,420" fill="#B56A63" opacity=".85"/><polygon points="450,0 900,420 0,420" fill="url(#dots)"/>'
               '<defs><pattern id="dots" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="5" cy="5" r="2.6" fill="#141414" opacity=".5"/></pattern></defs></svg>', 510, 560, .15, "pop", z=2)
    w2, h2 = fit_box(a["second"], 420, 460)
    body += el(cutimg(a["second"], w2, h2, grey=True), 960 - w2 // 2, 400 - h2 // 2, .25, "pop", z=3)
    w, h = fit_box(a["subject"], 520, 300)
    body += el(cutimg(a["subject"], w, h), 960 - w // 2, 600 - h // 2, .4, "drop", z=4)
    paper = f"clip-path:polygon({jag(rnd, 30, 1.0, .1)})"
    body += el(f'<div style="width:620px;height:220px;background:#FFF;{paper}"></div>', 650, 760, .5, "pop", z=5)
    body += el(f'<div style="width:560px;height:170px;background:#C8333A;{paper};display:flex;align-items:center;justify-content:center">{ransom(a["word"], min(110, int(470 / max(1, len(a["word"])) / .95)), 3)}</div>', 680, 785, .6, "pop", z=6)
    body += bolt(560, 260, 70, -20) + bolt(1460, 640, 56, 25, .8) + star4(1500, 160, 60, SIG)
    body += el(f'<div style="font:400 80px/1 ISerifI;color:#141414">{c[2]}</div>', 110, 120, .3, "wipe", z=7)
    body += el(f'<div style="font:600 22px Plex;letter-spacing:4px;color:#555;width:420px">{c[3].upper()}</div>', 114, 220, .5, "wipe", z=7)
    return body, "background:#E4E1DA"


def d_placards(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el(f'<div style="width:1920px;height:1080px;overflow:hidden"><img src="{jpg(a["ground"])}" style="width:100%;height:100%;object-fit:cover;filter:grayscale(1) contrast(1.35) brightness(1.05)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:1920px;height:1080px;background:#1F3B8C;mix-blend-mode:screen;opacity:.85"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    body += el('<div style="width:1920px;height:1080px;background-image:radial-gradient(rgba(10,20,60,.45) 1.6px,transparent 2px);background-size:7px 7px"></div>', 0, 0, 0, "pop", extra=STILL, z=2)
    for i, (t, x, y, rot) in enumerate(zip(a["signs"], (1080, 1380), (420, 160), (-14, 12))):
        sign = (f'<div style="position:relative;width:520px"><div style="position:absolute;left:240px;top:250px;width:30px;height:700px;background:#8A6A44"></div>'
                f'<div style="position:relative;background:#EDF1F6;border:12px solid #1A2340;padding:30px 20px;font:400 104px/0.95 Anton;color:#1A2340;text-align:center;box-shadow:0 20px 30px rgba(0,0,0,.35)">{t}</div></div>')
        body += el(sign, x, y, .3 + .2 * i, "drop", base=f"rotate({rot}deg)", z=4 + i)
    body += el(f'<div style="font:400 150px/0.9 Archivo;color:#FFF;text-shadow:0 8px 0 #1A2340">{c[2].upper()}</div>', 110, 700, .5, "wipe", z=8)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:5px;color:#141414;background:{SIG};padding:8px 14px;display:inline-block">{c[3].upper()}</div>', 116, 880, .7, "wipe", z=8)
    return body, "background:#1F3B8C"


def d_postcard(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#BFE3EA;background-image:radial-gradient(rgba(40,110,140,.35) 2px,transparent 2.4px);background-size:12px 12px"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse 30% 14% at 30% 30%,rgba(255,255,255,.9),transparent),radial-gradient(ellipse 26% 10% at 75% 22%,rgba(255,255,255,.85),transparent)"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    body += el(f'<div style="width:2000px;height:420px;overflow:hidden;clip-path:{torn_top(rnd, 30, 5)}"><img src="{jpg(a["ground"])}" style="width:100%;height:100%;object-fit:cover;filter:saturate(1.2)"></div>', -40, 680, .05, "pop", extra=STILL, z=2)
    is_card = M.REC.get(slug(a["subject"]), {}).get("cut") == "card"
    w, h = fit_box(a["subject"], 820 if is_card else 520, 520 if is_card else 600)
    body += el(cutimg(a["subject"], w, h), 1840 - w if is_card else 1240, 90, .3, "drop", base="rotate(3deg)" if is_card else "", z=4)
    body += el(f'<div style="background:#141414;color:#EDEDED;font:500 44px DMono;padding:10px 20px;clip-path:polygon({torn_top(rnd, 18, 8)[8:-1]});white-space:nowrap">{a["label"]}</div>', 100, 120, .2, "wipe", z=6)
    body += el(f'<div style="background:#F4F1EA;padding:8px 26px 2px;transform:rotate(-3deg);box-shadow:0 10px 18px rgba(0,0,0,.3)"><div style="font:400 170px/1 Anton;font-style:italic;color:#141414;transform:skewX(-8deg)">{c[2].upper()}</div></div>', 100, 520, .45, "drop", z=7)
    body += el(f'<div style="background:#3B2A20;padding:8px 22px;transform:rotate(2deg)"><div style="font:400 60px/1 Serif;color:#F4EEDF">{c[3]}</div></div>', 460, 760, .6, "drop", z=8)
    body += star4(980, 200, 60, SIG)
    return body, "background:#BFE3EA"


def d_engraving(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    holes = "".join(f'<div style="position:absolute;left:{x}px;top:{y}px;width:44px;height:26px;background:#F4EEDF;border-radius:4px"></div>' for x in range(60, 1860, 90) for y in (34, 1020))
    body = el(f'<div style="width:1920px;height:1080px;background:#0E0E0E">{holes}</div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:1700px;height:860px;background:#E9DFC9;border-radius:40px;overflow:hidden;background-image:radial-gradient(rgba(120,90,50,.1) 1px,transparent 1.5px);background-size:5px 5px"></div>', 110, 110, 0, "pop", extra=STILL, z=1)
    body += disc(560, 470, 250, "#D94B3B", 2) + disc(1280, 330, 70, "#3D63A6", 2) + disc(1560, 520, 60, SIG, 2)
    body += el('<svg width="1700" height="300"><path d="M0 220 C 300 120, 600 300, 900 200 S 1500 140, 1700 230 V300 H0Z" fill="#4D74B3"/></svg>', 110, 680, .1, "pop", extra=STILL, z=2)
    w, h = fit_box(a["figs"][0], 480, 520)
    body += el(cutimg(a["figs"][0], w, h, grey=True), 560 - w // 2, 880 - h, .3, "drop", z=4)
    w2, h2 = fit_box(a["figs"][1], 620, 500)
    body += el(cutimg(a["figs"][1], w2, h2, grey=True), 1150, 880 - h2, .45, "drop", z=4)
    body += el(f'<div style="font:900 96px/1 Playfair;color:#141414">{c[2]}</div>', 180, 150, .5, "wipe", z=6)
    body += el(f'<div style="font:400 40px ISerifI;color:#5A3A20">{c[3]}</div>', 186, 255, .6, "wipe", z=6)
    return body, "background:#0E0E0E"


def d_handstack(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#2B2A2E"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += disc(1120, 470, 340, "#E7B53C", 1)
    body += el('<div style="width:520px;height:600px;background:#A48C78;border-radius:260px 260px 0 0"></div>', 860, 560, .05, "pop", z=1)
    w2, h2 = fit_box(a["second"], 620, 330)
    body += el(cutimg(a["second"], w2, h2, grey=True), 1120 - w2 // 2, 1060 - h2, .2, "drop", z=3)
    w, h = fit_box(a["subject"], 420, 520)
    body += el(cutimg(a["subject"], w, h, grey=True), 1120 - w // 2, 1060 - h2 - h + 40, .4, "drop", z=4)
    w0, h0 = size_of(a["hand"])
    hh = 560
    hw = int(hh * w0 / h0)
    img = png(a["hand"])
    body += el(f'<img src="{img}" style="height:{hh}px;width:{hw}px;filter:grayscale(1) contrast(1.2) drop-shadow(0 24px 26px rgba(0,0,0,.4));transform:rotate(160deg)">', 1120 - hw // 2 + 60, 1060 - h2 - h - hh + 120, .55, "drop", z=6)
    body += el(f'<img src="{img}" style="height:{hh - 80}px;width:{int((hh - 80) * w0 / h0)}px;filter:grayscale(1) contrast(1.2) drop-shadow(0 24px 26px rgba(0,0,0,.4));transform:scaleX(-1) rotate(-70deg)">', 1380, 620, .7, "slide", z=6)
    body += el(f'<div style="font:400 130px/0.92 Bebas;color:#F4EEDF;width:600px">{c[2].upper()}</div>', 110, 160, .3, "wipe", z=7)
    body += el(f'<div style="font:600 24px Plex;letter-spacing:5px;color:{SIG}">{c[3].upper()}</div>', 116, 420, .5, "wipe", z=7)
    return body, "background:#2B2A2E"


def disc(x, y, r, col, z=2):
    return f'<div class="el" style="left:{x - r}px;top:{y - r}px;width:{2 * r}px;height:{2 * r}px;border-radius:50%;background:{col};z-index:{z}"></div>'


DEV2.update({"ransom": d_ransom, "placards": d_placards, "postcard": d_postcard, "engraving": d_engraving, "handstack": d_handstack})
