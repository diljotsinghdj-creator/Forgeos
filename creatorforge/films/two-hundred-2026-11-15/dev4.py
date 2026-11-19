"""Fourth device set (2026-11-15 reference study), every look rebuilt in the Vox x Johnny Harris grammar:
one sourced idea, real evidence, a map/document/chart, the investigator's hand-made layer (marker, highlighter,
pins, sticky notes, string), a source line, restraint. Vertical looks return a 1080x1920 page (key "V" in assets).
Real people appear only as credited public-domain portraits, in neutral framing, with nothing drawn on faces."""
import json
import math
import random
from pathlib import Path

from collage2 import el, STILL, pin_dot, red_string, torn_label
from dev2 import SIG, star4, torn_top, jag, H, outline

D = Path(__file__).resolve().parent
WORLD = json.load(open("/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
INK, RED, CHALK = "#1C1C1C", "#C8312B", "#ECEADF"


# ---- the investigator's hand-made layer ------------------------------------------------------------------------------
def marker_circle(x, y, w, h, col=RED, at=.7, z=9, rot=-4, sw=7):
    return el(f'<svg width="{w + 40}" height="{h + 40}" style="overflow:visible"><ellipse cx="{w / 2 + 20}" cy="{h / 2 + 20}" rx="{w / 2}" ry="{h / 2}" fill="none" stroke="{col}" '
              f'stroke-width="{sw}" stroke-linecap="round" stroke-dasharray="{3.3 * (w + h)} 9999" transform="rotate({rot} {w / 2 + 20} {h / 2 + 20})" filter="url(#rough)"/></svg>',
              x - 20, y - 20, at, "draw", z=z)


def marker_arrow(x1, y1, x2, y2, col=RED, at=.75, z=9, bend=-80, sw=6):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + bend
    ang = math.atan2(y2 - my, x2 - mx)
    a1 = (x2 - 26 * math.cos(ang - .45), y2 - 26 * math.sin(ang - .45))
    a2 = (x2 - 26 * math.cos(ang + .45), y2 - 26 * math.sin(ang + .45))
    return el(f'<svg width="1920" height="1920" style="overflow:visible"><path d="M{x1} {y1} Q {mx} {my} {x2} {y2} M{a1[0]:.0f} {a1[1]:.0f} L{x2} {y2} L{a2[0]:.0f} {a2[1]:.0f}" '
              f'fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" filter="url(#rough)"/></svg>', 0, 0, at, "draw", z=z)


def sticky(text, x, y, rot=-3, col="#FFE873", w=300, at=.8, z=10, size=40):
    return el(f'<div style="width:{w}px;min-height:{int(w * .78)}px;background:{col};padding:24px 22px;box-sizing:border-box;box-shadow:0 14px 22px rgba(0,0,0,.28);'
              f'font:700 {size}px/1.15 Caveat;color:#1C1C1C;transform:rotate({rot}deg)">{text}</div>', x, y, at, "drop", z=z)


def tape(x, y, rot=-8, w=140, at=.5, z=11):
    return el(f'<div style="width:{w}px;height:38px;background:rgba(235,225,200,.78);box-shadow:0 2px 4px rgba(0,0,0,.15);transform:rotate({rot}deg)"></div>', x, y, at, "pop", z=z)


def src_line(text, dark=False):
    return f'<div class="credit" style="color:{"rgba(255,255,255,.62)" if dark else "rgba(20,20,20,.6)"}">{text}</div>'


def kicker(t, x, y, col=INK, at=.4, z=8, size=22, w=900):
    return el(f'<div style="font:600 {size}px/1.35 Plex;letter-spacing:4px;color:{col};width:{w}px;text-transform:uppercase">{t}</div>', x, y, at, "wipe", z=z)


def headline(t, x, y, size=120, col=INK, font="Anton", at=.3, z=8, w=900, ls=1):
    return el(f'<div style="font:400 {size}px/0.92 {font};color:{col};width:{w}px;letter-spacing:{ls}px">{t}</div>', x, y, at, "wipe", z=z)


def chalk_text(t, x, y, size=46, rot=0, at=.6, z=6, col=CHALK, w=700):
    return el(f'<div style="font:700 {size}px/1.15 Caveat;color:{col};opacity:.92;transform:rotate({rot}deg);width:{w}px;text-shadow:0 0 1px rgba(255,255,255,.4)">{t}</div>', x, y, at, "wipe", z=z)


def img(src, w, h, fit="cover", flt="", extra=""):
    return f'<img src="{src}" style="width:{w}px;height:{h}px;object-fit:{fit};display:block;filter:{flt};{extra}">'


def loc(M, key):
    return (D / "assets" / f"{key}.jpg").as_uri()


def mapimg(name):
    return (D / "maps" / f"{name}.jpg").as_uri()


CHALKBOARD = ("background:#1F2B26;background-image:radial-gradient(ellipse at 40% 35%,rgba(255,255,255,.07),transparent 60%),"
              "repeating-linear-gradient(8deg,rgba(255,255,255,.012) 0 2px,transparent 2px 7px)")
GREENGRID = ("background:#1E4D3A;background-image:linear-gradient(rgba(255,255,255,.10) 2px,transparent 2px),linear-gradient(90deg,rgba(255,255,255,.10) 2px,transparent 2px),"
             "linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:240px 240px,240px 240px,48px 48px,48px 48px")
DOTTED = "background:#F1EDE3;background-image:radial-gradient(rgba(40,30,20,.35) 1.6px,transparent 2px);background-size:56px 56px"
GRID = ("background:#F2EEE4;background-image:linear-gradient(rgba(60,50,40,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(60,50,40,.08) 1px,transparent 1px);"
        "background-size:48px 48px")
DESK = ("background:#3B2A1E;background-image:radial-gradient(ellipse at 50% 40%,#5A4130 0%,#2A1C12 80%),"
        "repeating-linear-gradient(92deg,rgba(0,0,0,.12) 0 3px,transparent 3px 26px)")
AGED = ("background:#E2D3B4;background-image:radial-gradient(ellipse at 30% 20%,rgba(255,255,255,.35),transparent 60%),"
        "radial-gradient(ellipse at 80% 90%,rgba(120,80,30,.25),transparent 55%)")


def gilt(inner, w, h):
    return (f'<div style="position:relative;width:{w}px;height:{h}px;padding:30px;background:linear-gradient(135deg,#8C6A2B,#E5C878 30%,#9C7630 55%,#E9D08C 80%,#7A5A22);'
            f'box-shadow:0 26px 40px rgba(0,0,0,.6),inset 0 0 0 6px rgba(60,40,10,.6),inset 0 0 0 14px rgba(255,230,160,.25)"><div style="width:100%;height:100%;overflow:hidden;'
            f'box-shadow:inset 0 0 30px rgba(0,0,0,.6)">{inner}</div></div>')


# ---- 1 [25D-PORTRAIT-BOARD] ------------------------------------------------------------------------------------------
def d_portrait_board(M, c, sc, typ, rnd):
    a = c[5]
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{CHALKBOARD};z-index:0"></div>'
    # two columns that never reach the frame (720..1260): left 90..650, right 1300..1860
    placed = []
    for i, (t, x, y, r, s) in enumerate(a["notes"]):
        x = min(x, 110) if x < 960 else max(x, 1310)
        s = min(s, int(540 / (.46 * len(t))))
        body += chalk_text(t, x, y, s, r, .2 + .05 * i, z=2, w=560)
        placed.append((x, y, s, len(t)))
    body += el(gilt(img(loc(M, a["loc"]), 420, 520, flt="grayscale(1) sepia(.35) contrast(1.05)"), 480, 580), 720, 170, .3, "drop", z=5)
    body += el(f'<div style="background:#E9DFC9;padding:10px 22px;text-align:center;box-shadow:0 8px 14px rgba(0,0,0,.5)"><div style="font:400 44px/1 Playfair;color:#1C1C1C">{a["name"]}</div>'
               f'<div style="font:500 16px Plex;letter-spacing:4px;color:#6B4A20;margin-top:6px">{a["dates"]}</div></div>', 760, 830, .5, "drop", z=6)
    cx0, cy0 = a["circle"][:2]
    x, y, s, n = min(placed, key=lambda p: (p[0] - cx0) ** 2 + (p[1] - cy0) ** 2)
    hw, hh = min(560, int(.46 * s * n) + 70), s + 56
    body += marker_circle(x - 30, y - 22, hw, hh, SIG, .8, z=7)
    body += chalk_text(a["hand"], x + 10, y + hh + 6, 38, -3, .9, z=7, col=SIG, w=520)
    body += src_line(a["src"], dark=True)
    return body, "background:#1F2B26"


# ---- 3 [3D-MAP-FILL] -------------------------------------------------------------------------------------------------
def country_path(name, P):
    for cc in WORLD["countries"]:
        if cc["n"] == name:
            rings = cc["r"] if isinstance(cc["r"], list) else json.loads(cc["r"])
            return "".join("M" + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + "Z" for r in rings if len(r) > 3)
    raise KeyError(name)


def d_map_fill(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    a = c[5]
    lon0, lat0, lon1, lat1 = a["bbox"]
    P = lambda lo, la: ((lo - lon0) / (lon1 - lon0) * 1920, (lat1 - la) / (lat1 - lat0) * 1080)
    path = country_path(a["country"], P)
    body = el(img(mapimg(c[0]), 1920, 1080, "fill", "saturate(.8) brightness(.8)"), 0, 0, 0, "pop", extra=STILL, z=0)
    body += el(f'<svg width="1920" height="1080"><defs><clipPath id="cp"><path d="{path}"/></clipPath><filter id="gl"><feGaussianBlur stdDeviation="7"/></filter></defs>'
               f'<image href="{jpg(a["texture"])}" x="0" y="0" width="1920" height="1080" preserveAspectRatio="xMidYMid slice" clip-path="url(#cp)" style="filter:saturate(1.2) contrast(1.05)"/>'
               f'<path d="{path}" fill="none" stroke="#FFFFFF" stroke-width="10" opacity=".55" filter="url(#gl)"/><path d="{path}" fill="none" stroke="#FFFFFF" stroke-width="3.5"/></svg>', 0, 0, .2, "pop", z=2)
    lx, ly = P(*a["label_at"])
    body += el(f'<div style="font:600 30px Grotesk;color:#fff;text-shadow:0 2px 10px #000">{a["country_label"]}</div>', lx - 120, ly - 70, .5, "wipe", z=5)
    body += el(f'<div style="display:flex;gap:10px">' + "".join(f'<span style="background:{SIG};color:#141414;font:500 34px DMono;padding:4px 12px">{w}</span>' for w in a["words"]) + "</div>",
               lx - 120, ly - 20, .7, "wipe", z=5)
    ax, ay = P(*a["arrow_from"])
    body += marker_arrow(ax, ay, lx + 40, ly - 80, "#FFFFFF", .8, z=6, bend=-60)
    body += el(f'<div style="background:rgba(10,10,10,.6);padding:16px 22px"><div style="font:400 92px/1 Anton;color:#F3EFE6">{c[2].upper()}</div>'
               f'<div style="font:600 20px Plex;letter-spacing:4px;color:{SIG};margin-top:8px">{c[3].upper()}</div></div>', a.get("tx", 80), a.get("ty", 70), .3, "wipe", z=7)
    body += src_line(a["src"], dark=True)
    return body, "background:#000"


# ---- 4 [2D-BAR-PHOTO] ------------------------------------------------------------------------------------------------
def d_bar_photo(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    a = c[5]
    vals = a["values"]
    n = len(vals)
    vmax = max(v for _, v in vals) * 1.08
    X0, X1, BASE, TOP = 520, 1820, 960, 230
    bw = (X1 - X0) / n
    body = ""
    if a.get("mode") == "over":     # bars rising out of a landscape photo
        body += el(img(jpg(a["photo"]), 1920, 1080, flt="saturate(.85) brightness(.82)"), 0, 0, 0, "pop", extra=STILL, z=0)
        body += el('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(15,12,8,.82) 0%,rgba(15,12,8,.25) 45%,rgba(15,12,8,.1))"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
        for i, (lab, v) in enumerate(vals):
            h = (BASE - TOP) * v / vmax
            x = X0 + i * bw + bw * .14
            body += el(f'<div style="width:{bw * .72:.0f}px;height:{h:.0f}px;background:{SIG if i == n - 1 else "rgba(255,221,51,.72)"};box-shadow:0 0 0 2px rgba(0,0,0,.25)"></div>', x, BASE - h, .2 + .05 * i, "drop", z=3)
            body += el(f'<div style="background:#F3EFE6;padding:4px 8px;font:600 20px Plex;color:#141414;transform:rotate(-2deg);white-space:nowrap">{a["fmt"].format(v)}</div>', x, BASE - h - 44, .5 + .04 * i, "pop", z=4)
            body += el(f'<div style="font:500 20px Plex;color:#F3EFE6;width:{bw * .72:.0f}px;text-align:center">{lab}</div>', x, BASE + 12, .4, "wipe", z=4)
        col, kcol = "#F3EFE6", SIG
    else:                           # one photo sliced into the bars
        body += f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{GRID};z-index:0"></div>'
        for i, (lab, v) in enumerate(vals):
            h = (BASE - TOP) * v / vmax
            x = X0 + i * bw + bw * .08
            w = bw * .84
            body += el(f'<div style="width:{w:.0f}px;height:{h:.0f}px;overflow:hidden;background:url({jpg(a["photo"])});background-size:{X1 - X0}px {BASE - TOP}px;'
                       f'background-position:{-(x - X0):.0f}px {-(BASE - h - TOP):.0f}px;filter:{"none" if i == n - 1 else "grayscale(1) contrast(1.1)"};box-shadow:0 10px 14px rgba(0,0,0,.25)"></div>',
                       x, BASE - h, .15 + .05 * i, "drop", z=3)
            body += el(f'<div style="font:600 21px Plex;color:#141414;width:{w:.0f}px;text-align:center">{a["fmt"].format(v)}</div>', x, BASE - h - 34, .5, "pop", z=4)
            body += el(f'<div style="font:500 20px Plex;color:#444;width:{w:.0f}px;text-align:center">{lab}</div>', x, BASE + 12, .4, "wipe", z=4)
        body += el('<div style="width:1310px;height:3px;background:#141414"></div>', X0, BASE, .1, "wipe", z=4)
        col, kcol = INK, "#B07A00"
    body += headline(c[2].upper(), 90, 90, 104, col, w=420)
    lines = max(1, math.ceil(len(c[2]) * .47 * 104 / 420))
    body += kicker(c[3], 96, 90 + 96 * lines + 26, kcol, w=380)
    body += sticky(a["note"], 100, 640, -4, w=330, size=34)
    body += src_line(a["src"] + " · BARS FROM ZERO", dark=a.get("mode") == "over")
    return body, ("background:#000" if a.get("mode") == "over" else "background:#F2EEE4")


# ---- 5 [25D-SPOT-STICKER] --------------------------------------------------------------------------------------------
def d_spot_sticker(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    ground = a.get("ground", "#24413A")
    body = ""
    for i in range(5):        # scratch-ink discs
        r = rnd.randint(150, 260)
        x, y = rnd.randint(900, 1600), rnd.randint(120, 860)
        body += el(f'<svg width="{2 * r}" height="{2 * r}"><defs><filter id="sc{i}"><feTurbulence type="fractalNoise" baseFrequency="{rnd.uniform(.02, .06):.3f} {rnd.uniform(.3, .6):.2f}" numOctaves="2" seed="{i}"/>'
                   f'<feColorMatrix values="0 0 0 0 .1 0 0 0 0 .1 0 0 0 0 .1 0 0 0 -2.4 1.6"/></filter><clipPath id="cc{i}"><circle cx="{r}" cy="{r}" r="{r}"/></clipPath></defs>'
                   f'<circle cx="{r}" cy="{r}" r="{r}" fill="#E9E4D8"/><rect width="{2 * r}" height="{2 * r}" filter="url(#sc{i})" clip-path="url(#cc{i})"/></svg>', x - r, y - r, .05 * i, "pop", z=1)
    body += el(f'<div style="width:520px;height:520px;border-radius:50%;background:{RED}"></div>', 1080, 280, .2, "pop", z=2)
    w, h = fit_box(a["subject"], 760, 760)
    body += el(f'<img src="{png(a["subject"])}" style="width:{w}px;height:{h}px;filter:grayscale(1) contrast(1.35) {outline("#F7F4EC", 9)} drop-shadow(0 26px 26px rgba(0,0,0,.45))">',
               1340 - w // 2, 540 - h // 2, .35, "drop", z=4)
    body += headline(c[2].upper(), 100, 160, 120, "#F4EFE6", w=700)
    body += kicker(c[3], 106, 160 + 112 * max(1, math.ceil(len(c[2]) * .47 * 120 / 700)) + 26, SIG, w=640)
    body += el(f'<div style="background:#F4EFE6;padding:18px 22px;width:560px;box-shadow:0 12px 20px rgba(0,0,0,.4);transform:rotate(-1.5deg)">'
               f'<div style="font:600 15px Plex;letter-spacing:3px;color:#7A2A20">{a["doc_head"]}</div><div style="font:500 22px/1.45 Plex;color:#1C1C1C;margin-top:8px">'
               f'<span style="background:linear-gradient(transparent 55%,{SIG} 55%,{SIG} 94%,transparent 94%)">{a["doc_line"]}</span></div></div>', 100, 700, .6, "drop", z=6)
    body += pin_dot(380, 712, z=8)
    body += src_line(a["src"], dark=True)
    return body, f"background:{ground}"


# ---- 6 [25D-CHALK-NODE] ----------------------------------------------------------------------------------------------
def d_chalk_node(M, c, sc, typ, rnd):
    png, jpg, *_ = H(M)
    a = c[5]
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{CHALKBOARD};z-index:0"></div>'
    nodes = a["nodes"]
    svg = '<svg width="1920" height="1080"><defs><filter id="ch"><feTurbulence baseFrequency=".9" numOctaves="2"/><feDisplacementMap in="SourceGraphic" scale="4"/></filter></defs>'
    for (p, q, lab) in a["edges"]:
        x1, y1 = nodes[p][:2]; x2, y2 = nodes[q][:2]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{CHALK}" stroke-width="5" opacity=".85" filter="url(#ch)"/>'
        if lab:
            svg += f'<text x="{mx}" y="{my - 12}" font-family="Caveat" font-size="34" fill="{CHALK}" text-anchor="middle" opacity=".9">{lab}</text>'
    body += el(svg + "</svg>", 0, 0, .2, "draw", z=1)
    for i, (k, (x, y, src, cap)) in enumerate(nodes.items()):
        inner = img(src if src.startswith("file:") else (jpg(src) if not src.startswith("@") else loc(M, src[1:])), 220, 170, flt="grayscale(1) contrast(1.1)") if src else ""
        rot = rnd.uniform(-5, 5)
        if inner:
            body += el(f'<div style="background:#F3EFE4;padding:10px 10px 0;box-shadow:0 12px 18px rgba(0,0,0,.5);transform:rotate({rot:.1f}deg)">{inner}'
                       f'<div style="font:700 26px Caveat;color:#1C1C1C;padding:4px 2px 8px;width:220px">{cap}</div></div>', x - 120, y - 110, .3 + .05 * i, "drop", z=4)
        else:
            body += chalk_text(cap, x - 140, y - 30, 48, rot, .3 + .05 * i, z=4, w=320)
    fx, fy = nodes[a["focus"]][:2]
    body += marker_circle(fx - 150, fy - 130, 300, 280, SIG, .9, z=6, sw=6)
    body += headline(c[2].upper(), 70, 76, 84, CHALK, w=1300)
    body += kicker(c[3], 76, 176, SIG, w=1200)
    body += src_line(a["src"], dark=True)
    return body, "background:#1F2B26"


# ---- 7 [25D-STRIPS] --------------------------------------------------------------------------------------------------
def d_strips(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#F2EEE6"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    w, h = fit_box(a["subject"], 760, 1000)
    body += el(f'<img src="{png(a["subject"])}" style="width:{w}px;height:{h}px;filter:grayscale(1) contrast(1.15);clip-path:inset(0 46% 0 0)">', 260, 1080 - h + 20, .1, "pop", z=2)
    x = 260 + int(w * .54)
    for i, (key, cap) in enumerate(a["strips"]):
        sw = 150
        body += el(f'<div style="width:{sw}px;height:{900 - i * 40}px;overflow:hidden;box-shadow:0 8px 14px rgba(0,0,0,.25)">{img(loc(M, key), sw, 900 - i * 40, flt="grayscale(1) contrast(1.15)")}</div>',
                   x + i * (sw + 8), 120 + i * 20, .2 + .08 * i, "drop", z=3)
        body += el(f'<div style="font:500 14px/1.3 Plex;color:#333;width:{sw}px">{cap}</div>', x + i * (sw + 8), 1030 - i * 20 + 4, .5, "wipe", z=4)
    for (dx, dy, r) in ((300, 300, 46), (1220, 760, 90), (180, 830, 20)):
        body += el(f'<div style="width:{2 * r}px;height:{2 * r}px;border-radius:50%;background:{RED}"></div>', dx, dy, .6, "pop", z=5)
    body += el('<svg width="1920" height="1080"><path d="M120 980 L 1840 980 M 1895 120 L 1895 1040" stroke="#C8312B" stroke-width="2"/></svg>', 0, 0, .3, "draw", extra=STILL, z=1)
    tx = x + 5 * 158 + 40
    tl = max(1, math.ceil(len(c[2]) * .47 * 84 / (1880 - tx)))
    body += headline(c[2].upper(), tx, 140, 84, INK, w=1880 - tx)
    body += kicker(c[3], tx + 6, 140 + 78 * tl + 26, RED, w=1860 - tx, size=18)
    body += src_line(a["src"])
    return body, "background:#F2EEE6"


# ---- 8 [25D-MONUMENT-CARD] -------------------------------------------------------------------------------------------
PATTERNS = {"tile": "repeating-conic-gradient(from 45deg,#1F4E79 0 25%,#F2EEE6 0 50%) 0 0/46px 46px",
            "jali": "radial-gradient(circle,#F2EEE6 9px,transparent 10px) 0 0/34px 34px,#7A2A20",
            "zellige": "repeating-linear-gradient(45deg,#0F6E5A 0 12px,#F2EEE6 12px 18px,#C8312B 18px 26px,#F2EEE6 26px 32px)",
            "stripes": "repeating-linear-gradient(90deg,#1C1C1C 0 10px,#E9C46A 10px 22px)"}


def d_monument_card(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{DOTTED};z-index:0"></div>'
    body += el(f'<div style="width:760px;height:380px;border-radius:380px 380px 0 0;background:{a.get("sun", "#F2A541")}"></div>', 760, 300, .1, "pop", z=1)
    w, h = fit_box(a["subject"], 700, 840)
    body += el(cutimg(a["subject"], w, h, grey=True), 1140 - w // 2, 960 - h, .3, "drop", z=4)
    body += el(f'<div style="width:150px;height:560px;background:{PATTERNS[a.get("pattern", "tile")]};box-shadow:0 10px 18px rgba(0,0,0,.25)"></div>', 1500, 360, .45, "drop", z=3)
    body += headline(c[2], 100, 130, 96, INK, "Playfair", w=560)
    kl, cur = 1, 0                                  # word-wrap estimate for the Playfair headline
    for wd in c[2].split():
        ww = len(wd) * .58 * 96 + 24
        if cur and cur + ww > 560:
            kl, cur = kl + 1, 0
        cur += ww
    body += kicker(c[3], 106, 130 + 92 * kl + 20, "#7A2A20", w=520, size=18)
    body += el(f'<div style="font:500 17px/1.6 Plex;color:rgba(28,28,28,.62);width:540px">{a["para"]}</div>', 106, 130 + 92 * kl + 80, .2, "wipe", z=2)
    lon, lat = a["where"]
    # a small locator map with a pin (Natural Earth outlines)
    box = a["locbox"]
    P = lambda lo, la: ((lo - box[0]) / (box[2] - box[0]) * 360, (box[3] - la) / (box[3] - box[1]) * 220)
    lp = ""
    for cc in WORLD["countries"]:
        rings = cc["r"] if isinstance(cc["r"], list) else json.loads(cc["r"])
        for r in rings:
            pts = [P(lo, la) for lo, la in r]
            if all(x < -40 or x > 400 or y < -40 or y > 260 for x, y in pts):
                continue
            lp += '<path d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + 'Z" fill="#D9D1BF" stroke="#8C7B5A" stroke-width=".8"/>'
    px, py = P(lon, lat)
    body += el(f'<div style="background:#F7F3EA;padding:10px;box-shadow:0 10px 16px rgba(0,0,0,.25);transform:rotate(2deg)"><svg width="360" height="220">{lp}'
               f'<circle cx="{px:.0f}" cy="{py:.0f}" r="9" fill="{RED}"/><circle cx="{px:.0f}" cy="{py:.0f}" r="20" fill="none" stroke="{RED}" stroke-width="3"/></svg>'
               f'<div style="font:600 14px Plex;letter-spacing:3px;color:#555;margin-top:6px">{a["place"]}</div></div>', 110, 700, .6, "drop", z=6)
    body += src_line(a["src"])
    return body, "background:#F1EDE3"


# ---- 9 [25D-PORTAL] --------------------------------------------------------------------------------------------------
def d_portal(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#EFE7D6"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    strips = [("#1F6F78", -8, 160, 120, 300, 900), ("#E07A1F", 6, 1240, 80, 260, 980), ("#E9DFC9", -3, 420, 560, 1100, 220), ("#C8312B", 4, 1500, 600, 200, 420)]
    for i, (col, rot, x, y, w, h) in enumerate(strips):
        body += el(f'<div style="width:{w}px;height:{h}px;background:{col};clip-path:polygon({jag(random.Random(i), 30, 1.0, .06)});transform:rotate({rot}deg);opacity:.92"></div>', x, y, .05 * i, "pop", z=1)
    w, h = fit_box(a["frame"], 820, 760)
    body += el(f'<img src="{png(a["frame"])}" style="width:{w}px;height:{h}px;filter:drop-shadow(0 24px 26px rgba(0,0,0,.4))">', 120, 120 + (760 - h) // 2, .2, "drop", z=3)
    cx, cy, r = 1360, 430, 300
    body += el(f'<svg width="1920" height="1080" style="overflow:visible"><path d="M{120 + w * .75:.0f} {120 + 380} Q {(120 + w + cx - r) / 2:.0f} {cy - 160} {cx - r + 10} {cy}" fill="none" stroke="{RED}" stroke-width="4" stroke-dasharray="12 10"/></svg>', 0, 0, .4, "draw", z=4)
    body += el(f'<div style="width:{2 * r}px;height:{2 * r}px;border-radius:50%;overflow:hidden;border:14px solid #1C1C1C;box-shadow:0 20px 30px rgba(0,0,0,.35),inset 0 0 40px rgba(0,0,0,.5)">'
               f'{img(mapimg(c[0]), 2 * r, 2 * r, flt="saturate(1.15) contrast(1.05)")}</div>', cx - r - 14, cy - r - 14, .3, "pop", z=5)
    body += el(f'<div style="background:#141414;color:#F3EFE6;font:500 18px Plex;letter-spacing:3px;padding:8px 14px">{a["what"]}</div>', cx - r + 40, cy + r + 20, .7, "wipe", z=6)
    ts = min(112, int(1000 / (.6 * len(c[2]))))
    body += el(f'<div style="font:400 {ts}px/0.95 Marker;color:#1C1C1C;transform:rotate(-3deg);white-space:nowrap">{c[2]}</div>', 110, 880, .5, "wipe", z=7)
    body += el(f'<div style="width:{min(900, int(len(c[2]) * ts * .58))}px;height:8px;background:{RED};transform:rotate(-3deg)"></div>', 120, 880 + ts + 6, .7, "wipe", z=7)
    body += src_line(a["src"])
    return body, "background:#EFE7D6"


# ---- 10 [25D-PANORAMA] -----------------------------------------------------------------------------------------------
def d_panorama(M, c, sc, typ, rnd):
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#EDEAE3"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    n = len(a["layers"])
    for i, (key, year) in enumerate(a["layers"]):
        x = i * (1920 // n) - 140
        mask = "linear-gradient(90deg,transparent 0%,#000 22%,#000 78%,transparent 100%)"
        body += el(f'<div style="width:{1920 // n + 280}px;height:820px;-webkit-mask-image:{mask};mask-image:{mask}">'
                   f'{img(loc(M, key), 1920 // n + 280, 820, flt="grayscale(1) contrast(1.15) brightness(1.02)")}</div>', x, 200, .15 * i, "pop", z=1 + i)
        body += el(f'<div style="background:#141414;color:{SIG};font:400 44px Anton;padding:4px 16px">{year}</div>', x + 200, 940, .4 + .1 * i, "pop", z=9)
    body += el('<div style="width:1920px;height:1080px;background-image:radial-gradient(rgba(20,20,20,.28) 1.4px,transparent 1.9px);background-size:8px 8px;'
               '-webkit-mask-image:linear-gradient(180deg,transparent 40%,#000);mask-image:linear-gradient(180deg,transparent 40%,#000)"></div>', 0, 0, 0, "pop", extra=STILL, z=8)
    body += el(f'<div style="width:240px;height:240px;border-radius:50%;background:{a.get("accent", SIG)}"></div>', a.get("sun_at", 1560), 80, .5, "pop", z=0)
    body += headline(c[2].upper(), 90, 50, 110, INK, w=1300)
    body += kicker(c[3], 96, 170, RED, w=1200)
    body += src_line(a["src"])
    return body, "background:#EDEAE3"


# ---- 12 [25D-STRIP-MONUMENT] -----------------------------------------------------------------------------------------
def d_strip_monument(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el('<div style="width:1920px;height:1080px;background:#FAF8F3"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    body += el(f'<div style="width:300px;height:640px;overflow:hidden;box-shadow:0 10px 16px rgba(0,0,0,.12)">{img(jpg(a["sky"]), 300, 640)}</div>', 810, 40, .1, "drop", z=1)
    w, h = fit_box(a["subject"], 760, 440)
    y0 = 680 - h
    body += el(cutimg(a["subject"], w, h, extra="filter:saturate(1.1) contrast(1.05)"), 960 - w // 2, y0, .3, "drop", z=4)
    for side, key in (("l", a["left"]), ("r", a["right"])):
        w2, h2 = fit_box(key, 520, 240)
        body += el(cutimg(key, w2, h2, grey=True), (960 - w // 2 - w2 + 60) if side == "l" else (960 + w // 2 - 60), 680 - h2, .2, "drop", z=3)
    body += el(f'<img src="{png(a["subject"])}" style="width:{w}px;height:{h}px;transform:scaleY(-1);opacity:.35;filter:blur(2px) saturate(.8);'
               f'-webkit-mask-image:linear-gradient(0deg,transparent 30%,#000);mask-image:linear-gradient(0deg,transparent 30%,#000)">', 960 - w // 2, 690, .4, "pop", z=2)
    body += el('<div style="width:1920px;height:2px;background:#1C1C1C;opacity:.4"></div>', 0, 684, .2, "wipe", extra=STILL, z=5)
    body += el(f'<div style="font:900 84px/1 Playfair;color:{INK};text-align:center;width:1920px">{c[2]}</div>', 0, 860, .5, "wipe", z=6)
    body += el(f'<div style="font:600 20px Plex;letter-spacing:5px;color:#7A2A20;text-align:center;width:1920px">{c[3].upper()}</div>', 0, 960, .6, "wipe", z=6)
    cw, ch = int(max(160, w * .55)), int(min(220, max(120, h * .35)))
    body += marker_circle(960 - cw // 2, y0 - 30, cw, ch, RED, .85, z=7)
    body += el(f'<div style="font:700 40px Caveat;color:{RED};width:380px">{a["note"]}</div>', 960 + cw // 2 + 30, y0, .9, "wipe", z=7)
    body += src_line(a["src"])
    return body, "background:#FAF8F3"


# ---- 13 [25D-HUD] ----------------------------------------------------------------------------------------------------
def d_hud(M, c, sc, typ, rnd):
    a = c[5]
    body = el(img(mapimg(c[0]), 1920, 1080, flt="saturate(.9) contrast(1.1) brightness(.85)"), 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(0,20,10,.55),transparent 35%,transparent 65%,rgba(0,20,10,.55))"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    g = "#B8F5C8"
    svg = f'<svg width="1920" height="1080" font-family="DMono" fill="{g}">'
    for i in range(0, 1080, 18):
        L = 30 if i % 90 == 0 else 14
        svg += f'<line x1="40" y1="{i}" x2="{40 + L}" y2="{i}" stroke="{g}" stroke-opacity=".7"/><line x1="{1880 - L}" y1="{i}" x2="1880" y2="{i}" stroke="{g}" stroke-opacity=".7"/>'
    for i in range(0, 1920, 24):
        L = 26 if i % 120 == 0 else 10
        svg += f'<line x1="{i}" y1="1040" x2="{i}" y2="{1040 - L}" stroke="{g}" stroke-opacity=".6"/>'
    tx, ty = a["target"]
    svg += (f'<circle cx="{tx}" cy="{ty}" r="150" fill="none" stroke="{g}" stroke-width="2" stroke-dasharray="6 8"/><circle cx="{tx}" cy="{ty}" r="60" fill="none" stroke="{SIG}" stroke-width="3"/>'
            f'<line x1="{tx - 220}" y1="{ty}" x2="{tx - 70}" y2="{ty}" stroke="{g}"/><line x1="{tx + 70}" y1="{ty}" x2="{tx + 220}" y2="{ty}" stroke="{g}"/>'
            f'<line x1="{tx}" y1="{ty - 220}" x2="{tx}" y2="{ty - 70}" stroke="{g}"/><line x1="{tx}" y1="{ty + 70}" x2="{tx}" y2="{ty + 220}" stroke="{g}"/>')
    for i, (k, v) in enumerate(a["readouts"]):
        svg += f'<text x="90" y="{300 + i * 64}" font-size="16" opacity=".75">{k}</text><text x="90" y="{326 + i * 64}" font-size="28">{v}</text>'
    svg += "</svg>"
    body += el(svg, 0, 0, .2, "pop", z=3)
    body += sticky(a["note"], 1480, 700, 3, w=330, size=34)
    body += headline(c[2].upper(), 90, 70, 100, "#F3EFE6", w=1300)
    body += kicker(c[3], 96, 180, SIG, w=1200)
    body += src_line(a["src"], dark=True)
    return body, "background:#000"


# ---- 14 [25D-DOC-BOARD] ----------------------------------------------------------------------------------------------
def d_doc_board(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{GREENGRID};z-index:0"></div>'
    body += el('<div style="width:4px;height:1080px;background:rgba(255,255,255,.55)"></div>', 640, 0, .05, "pop", extra=STILL, z=1)
    body += el('<div style="width:4px;height:1080px;background:rgba(255,255,255,.55)"></div>', 1280, 0, .05, "pop", extra=STILL, z=1)
    body += el(f'<div style="width:520px;height:640px;overflow:hidden;box-shadow:0 18px 28px rgba(0,0,0,.45);border:8px solid #EDE7D8">{img(loc(M, a["portrait"]), 504, 624, flt="grayscale(1) contrast(1.1)")}</div>',
               60, 300, .2, "drop", z=3)
    body += el(f'<div style="font:400 66px/0.95 Anton;color:#F3EFE6;width:520px;text-align:center">{a["name"].upper()}</div>', 60, 90, .3, "wipe", z=4)
    body += marker_arrow(470, 230, 380, 330, "#F3EFE6", .7, z=5, bend=-30)
    body += el(f'<div style="width:440px;height:440px;border-radius:50%;overflow:hidden;border:8px solid #EDE7D8;box-shadow:0 18px 28px rgba(0,0,0,.45)">{img(loc(M, a["round"]), 440, 440, flt="grayscale(1) contrast(1.1)")}</div>',
               740, 260, .35, "drop", z=3)
    body += el(f'<div style="background:#EDE7D8;padding:6px 26px;box-shadow:0 8px 14px rgba(0,0,0,.4)"><div style="font:900 70px/1 Playfair;color:#1C1C1C">{a["year"]}</div>'
               f'<div style="font:600 14px Plex;letter-spacing:3px;color:#7A2A20;text-align:center">{a["year_note"]}</div></div>', 830, 700, .5, "drop", z=5)
    body += el(f'<div style="width:560px;height:820px;overflow:hidden;box-shadow:0 18px 28px rgba(0,0,0,.45);border:8px solid #EDE7D8">{img(mapimg(c[0]), 544, 804, flt="saturate(1.1)")}</div>',
               1320, 140, .45, "drop", z=3)
    px, py = a["sat_pin"]
    body += el(f'<div style="width:30px;height:30px;border-radius:50%;background:{SIG};box-shadow:0 0 0 8px rgba(255,221,51,.35)"></div>', 1328 + px - 15, 148 + py - 15, .6, "pop", z=5)
    left = px > 300                                 # keep the label inside the map card
    body += el(f'<div style="background:#141414;color:{SIG};font:500 18px Plex;letter-spacing:2px;padding:6px 12px;white-space:nowrap">{a["sat_label"]}</div>',
               1328 + px + (-26 if left else 26), 148 + py - 18, .7, "wipe", base="translateX(-100%)" if left else "", z=5)
    body += el(f'<div style="font:600 18px Plex;letter-spacing:4px;color:#CFE3D6">{c[3].upper()}</div>', 740, 960, .7, "wipe", z=5)
    body += src_line(a["src"], dark=True)
    return body, "background:#1E4D3A"


# ---- 15 [2D-DOODLE] --------------------------------------------------------------------------------------------------
def doodles(cx, cy, r, rnd, col=RED):
    out = ""
    for k in range(9):
        ang = rnd.uniform(0, 2 * math.pi)
        x1, y1 = cx + (r + 20) * math.cos(ang), cy + (r + 20) * math.sin(ang)
        x2, y2 = cx + (r + 90) * math.cos(ang), cy + (r + 90) * math.sin(ang)
        out += f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{col}" stroke-width="7" stroke-linecap="round"/>'
    for k in range(2):
        x, y = cx + rnd.choice([-1, 1]) * (r + 60), cy - r + rnd.randint(-40, 60)
        out += f'<path d="M{x} {y} l-30 60 h34 l-24 64 l60 -84 h-34 l24 -40 z" fill="{SIG}" stroke="#1C1C1C" stroke-width="4" stroke-linejoin="round"/>'
    out += f'<path d="M{cx - r - 40} {cy + r + 30} q 60 -30 120 0 t 120 0 t 120 0" fill="none" stroke="#1C1C1C" stroke-width="5" stroke-linecap="round"/>'
    return out


def d_doodle(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{GRID};z-index:0"></div>'
    w, h = fit_box(a["subject"], 620, 620)
    cx, cy = a.get("at", (1240, 560))
    body += el(f'<div style="width:{max(w, h) + 120}px;height:{max(w, h) + 120}px;border-radius:50%;background:{a.get("disc", "#2E86AB")}"></div>', cx - (max(w, h) + 120) // 2, cy - (max(w, h) + 120) // 2, .1, "pop", z=1)
    body += el(cutimg(a["subject"], w, h, grey=a.get("grey", True)), cx - w // 2, cy - h // 2, .25, "drop", z=3)
    body += el(f'<svg width="1920" height="1080" style="overflow:visible">{doodles(cx, cy, max(w, h) // 2, rnd)}</svg>', 0, 0, .55, "draw", z=4)
    if a.get("diagram"):
        x0, y0, lab = a["diagram"]
        body += el(f'<svg width="520" height="300"><rect x="10" y="40" width="200" height="240" fill="none" stroke="#1C1C1C" stroke-width="5"/><rect x="14" y="150" width="192" height="126" fill="#2E86AB"/>'
                   f'<path d="M14 150 q 24 -14 48 0 t 48 0 t 48 0 t 48 0" fill="none" stroke="#1C1C1C" stroke-width="4"/><path d="M230 160 h170 m-24 -18 l24 18 l-24 18" fill="none" stroke="{RED}" stroke-width="6" stroke-linecap="round"/>'
                   f'<text x="240" y="140" font-family="Caveat" font-size="38" fill="#1C1C1C">{lab}</text></svg>', x0, y0, .7, "draw", z=4)
    body += headline(c[2].upper(), 100, 140, 120, INK, w=640)
    body += kicker(c[3], 106, 140 + 120 * (1 + (len(c[2]) > 10)) + 24, RED, w=600)
    body += src_line(a["src"])
    return body, "background:#F2EEE4"


# ---- 17 [3D-MAP-EVENT] -----------------------------------------------------------------------------------------------
PLANE = '<path d="M0 -26 L5 -6 L28 4 L28 9 L5 4 L4 18 L11 24 L11 27 L0 24 L-11 27 L-11 24 L-4 18 L-5 4 L-28 9 L-28 4 L-5 -6 Z" fill="#D8DEE6" stroke="#2A2F36" stroke-width="1.5"/>'
SHIP = '<path d="M-34 -6 L26 -6 L36 0 L26 6 L-34 6 Z" fill="#9AA4AE" stroke="#2A2F36" stroke-width="1.5"/><rect x="-10" y="-12" width="16" height="7" fill="#7D8892"/>'


def d_map_event(M, c, sc, typ, rnd):
    a = c[5]
    body = el(img(mapimg(c[0]), 1920, 1080, flt="saturate(.85) brightness(.82) contrast(1.1)"), 0, 0, 0, "pop", extra=STILL, z=0)
    svg = '<svg width="1920" height="1080" style="overflow:visible">'
    for (kind, x, y, rot) in a["units"]:
        svg += f'<g transform="translate({x},{y}) rotate({rot}) scale(1.3)">{PLANE if kind == "plane" else SHIP}</g>'
    for k in range(a.get("tracers", 10)):
        x, y = rnd.randint(300, 1700), rnd.randint(150, 950)
        ang = rnd.uniform(0, math.pi)
        svg += f'<line x1="{x}" y1="{y}" x2="{x + 50 * math.cos(ang):.0f}" y2="{y + 50 * math.sin(ang):.0f}" stroke="#FF9A3C" stroke-width="3" opacity=".8"/>'
    svg += "</svg>"
    body += el(svg, 0, 0, .3, "pop", z=3)
    for (x, y) in a.get("smoke", []):
        body += el('<div style="width:240px;height:160px;border-radius:50%;background:radial-gradient(ellipse,rgba(230,230,225,.85),transparent 70%);filter:blur(6px)"></div>', x - 120, y - 80, .4, "pop", z=4)
    lx, ly = a["label_at"]
    body += el(f'<div style="font:400 64px Anton;color:rgba(230,240,255,.85);text-shadow:0 0 18px rgba(120,170,255,.6)">{a["place"]}</div>', lx, ly, .5, "wipe", z=5)
    body += el(f'<div style="font:400 58px Anton;color:{SIG};text-shadow:0 0 16px rgba(255,221,51,.8)">{a["date"]}</div>', lx, ly + 80, .6, "wipe", z=5)
    tl = "".join(f'<div style="flex:1;border-left:2px solid #F3EFE6;padding:4px 10px;font:500 16px Plex;color:#F3EFE6">{t}</div>' for t in a["timeline"])
    body += el(f'<div style="display:flex;width:1700px;background:rgba(0,0,0,.55);padding:10px 20px">{tl}</div>', 90, 980, .7, "wipe", z=6)
    body += sticky("positions illustrative", 1560, 70, 4, w=290, size=32)
    body += src_line(a["src"], dark=True)
    return body, "background:#000"


# ---- 18 [3D-FLAG-RIBBON] (paper version) -----------------------------------------------------------------------------
def flag_svg(kind, w=520, h=346):
    if kind == "france":
        inner = f'<rect width="{w / 3}" height="{h}" fill="#1F3A93"/><rect x="{w / 3}" width="{w / 3}" height="{h}" fill="#F4F1EA"/><rect x="{2 * w / 3}" width="{w / 3}" height="{h}" fill="#C8312B"/>'
    elif kind == "italy":
        inner = f'<rect width="{w / 3}" height="{h}" fill="#2E7D32"/><rect x="{w / 3}" width="{w / 3}" height="{h}" fill="#F4F1EA"/><rect x="{2 * w / 3}" width="{w / 3}" height="{h}" fill="#C8312B"/>'
    elif kind == "japan":
        inner = f'<rect width="{w}" height="{h}" fill="#F4F1EA"/><circle cx="{w / 2}" cy="{h / 2}" r="{h * .3}" fill="#BC002D"/>'
    else:  # usa, simplified stripes and canton
        inner = "".join(f'<rect y="{i * h / 13:.1f}" width="{w}" height="{h / 13 + .5:.1f}" fill="{"#B22234" if i % 2 == 0 else "#F4F1EA"}"/>' for i in range(13))
        inner += f'<rect width="{w * .4}" height="{h * 7 / 13:.1f}" fill="#3C3B6E"/>'
    return f'<svg width="{w}" height="{h}" style="filter:sepia(.35) contrast(.95)">{inner}</svg>'


def d_flag_paper(M, c, sc, typ, rnd):
    a = c[5]
    body = f'<div class="el" style="left:0;top:0;width:1920px;height:1080px;{DESK};z-index:0"></div>'
    body += el(f'<div style="clip-path:polygon({jag(random.Random(3), 40, 1.0, .03)});box-shadow:0 20px 30px rgba(0,0,0,.5)">{flag_svg(a["flag"])}</div>', 120, 380, .1, "drop", base="rotate(-6deg)", z=2)
    body += el(f'<div style="background:#F3EFE4;padding:16px 16px 60px;box-shadow:0 24px 34px rgba(0,0,0,.6);transform:rotate(3deg)">{img(loc(M, a["portrait"]), 460, 560, flt="grayscale(1) sepia(.3) contrast(1.05)")}'
               f'<div style="font:700 36px Caveat;color:#1C1C1C;margin-top:12px">{a["name"]}</div></div>', 760, 110, .3, "drop", z=4)
    body += el(f'<div style="width:520px;background:#EDE3C8;padding:26px;box-shadow:0 20px 30px rgba(0,0,0,.55);transform:rotate(-2deg)">{img(loc(M, a["doc"]), 468, 560, "cover", "sepia(.25) contrast(1.05)")}'
               f'<div style="font:600 15px Plex;letter-spacing:3px;color:#5A3A1A;margin-top:12px">{a["doc_cap"]}</div></div>', 1320, 220, .45, "drop", z=3)
    body += tape(860, 90, -10) + tape(1440, 200, 8) + tape(150, 360, -14)
    body += el(f'<div style="background:#141414;padding:14px 22px"><div style="font:400 84px/1 Anton;color:#F3EFE6">{c[2].upper()}</div>'
               f'<div style="font:600 18px Plex;letter-spacing:4px;color:{SIG};margin-top:6px">{c[3].upper()}</div></div>', 100, 860, .6, "wipe", z=6)
    body += src_line(a["src"], dark=True)
    return body, "background:#2A1C12"


# ---- 19 [25D-PORTRAIT-DOC] -------------------------------------------------------------------------------------------
def d_portrait_doc(M, c, sc, typ, rnd):
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    body = el(img(loc(M, a["doc"]), 1920, 1080, "cover", "grayscale(1) contrast(1.15) brightness(1.15) opacity(.55)"), 0, 0, 0, "pop", extra=STILL, z=0)
    body += el('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(240,238,232,.9),rgba(240,238,232,.35) 45%,rgba(240,238,232,.85))"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    hy = a.get("hl_y", 520)
    body += el(f'<div style="width:760px;height:44px;background:{SIG};mix-blend-mode:multiply;opacity:.85"></div>', a.get("hl_x", 1060), hy, .3, "wipe", z=2)
    body += el(f'<div style="background:#D9D6CF;padding:14px;box-shadow:0 26px 36px rgba(0,0,0,.35)">{img(loc(M, a["portrait"]), 560, 680, flt="grayscale(1) contrast(1.1)")}</div>', 420, 230, .4, "drop", z=4)
    if a.get("object"):
        for (x, y, rot) in ((1700, -20, 180), (110, 840, 0)):
            w, h = fit_box(a["object"], 220, 300)
            body += el(cutimg(a["object"], w, h, grey=True), x, y, .6, "drop", base=f"rotate({rot}deg)", z=5)
    body += el(f'<div style="font:400 92px/1 Grotesk;color:#1C1C1C;letter-spacing:-2px">{a["name"]}</div>', 420, 90, .3, "wipe", z=6)
    body += kicker(c[3], 1060, hy + 70, "#7A2A20", w=760, size=18)
    body += src_line(a["src"])
    return body, "background:#F0EEE8"


# ---- 11/4 variants are covered by d_bar_photo; vertical looks -----------------------------------------------------------
def d_v_object_map(M, c, sc, typ, rnd):
    """[V-OBJECT-MAP] 1080x1920: a real object in front of a country silhouette (Natural Earth; India official), stacked phrase, leaves rising."""
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    W, Hh = 1080, 1920
    box = a["box"]
    P = lambda lo, la: ((lo - box[0]) / (box[2] - box[0]) * 1000 + 40, (box[3] - la) / (box[3] - box[1]) * 800 + 380)
    if a["country"] == "India":
        import sys
        sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
        from creatorforge_worker.media import maps
        rings = maps._find("India")["rings"]
        path = "".join("M" + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + "Z" for r in rings if len(r) > 3)
    else:
        path = country_path(a["country"], P)
    body = el(f'<svg width="{W}" height="{Hh}"><path d="{path}" fill="#C9C6BF" stroke="#9A968E" stroke-width="2"/></svg>', 0, 0, .1, "pop", z=1)
    w, h = fit_box(a["subject"], 700, 620)
    body += el(cutimg(a["subject"], w, h, extra="filter:contrast(1.05) drop-shadow(0 30px 30px rgba(0,0,0,.35))"), W // 2 - w // 2, 900, .3, "drop", z=4)
    l1, l2 = a["phrase"]
    body += el(f'<div style="font:900 170px/0.9 Grotesk;color:#1C1C1C;letter-spacing:-6px">{l1}</div>', 120, 200, .4, "wipe", z=5)
    body += el(f'<div style="font:500 70px/1 Grotesk;color:#6B6B6B">{l2}</div>', 520, 360, .55, "wipe", z=5)
    if a.get("leaves"):
        w2, h2 = fit_box(a["leaves"], 1080, 520)
        body += el(cutimg(a["leaves"], w2, h2, grey=True), 0, Hh - h2 + 40, .2, "drop", z=3)
    body += el(f'<div style="background:{SIG};font:600 26px Plex;letter-spacing:4px;padding:8px 16px">{c[3].upper()}</div>', 120, 1560, .7, "wipe", z=6)
    body += el(f'<div style="font:500 14px Plex;color:rgba(0,0,0,.55);width:1000px">{a["src"]}</div>', 40, 1870, 0, "pop", extra=STILL, z=99)
    return body, "background:linear-gradient(180deg,#B9B6AF,#E9E7E1)"


def d_v_depth(M, c, sc, typ, rnd):
    """[V-DEPTH-CROWD] 1080x1920: one sharp animal among many soft ones, one huge blurred in front, sticky note."""
    png, jpg, fit_box, cutimg, size_of, slug = H(M)
    a = c[5]
    W, Hh = 1080, 1920
    body = el('<div style="width:1080px;height:1920px;background:linear-gradient(180deg,#F1F0EC,#DCDAD4)"></div>', 0, 0, 0, "pop", extra=STILL, z=0)
    for i in range(14):
        w, h = fit_box(a["crowd"], 260, 220)
        x, y = rnd.randint(-60, 900), rnd.randint(520, 980)
        body += el(f'<img src="{png(a["crowd"])}" style="width:{w}px;height:{h}px;filter:grayscale(1) blur({rnd.uniform(1.5, 4):.1f}px) brightness(1.05);{"transform:scaleX(-1)" if i % 2 else ""}">', x, y, .05 * i, "pop", z=1 + (y // 100))
    w, h = fit_box(a["hero"], 620, 560)
    body += el(cutimg(a["hero"], w, h, grey=True), W // 2 - w // 2, 640, .4, "drop", z=12)
    w2, h2 = fit_box(a["crowd"], 1500, 1100)
    body += el(f'<img src="{png(a["crowd"])}" style="width:{w2}px;height:{h2}px;filter:grayscale(1) blur(16px) brightness(1.08)">', W // 2 - w2 // 2, 1180, .2, "pop", z=20)
    body += el(f'<div style="width:620px;background:#F7F3E8;padding:20px 26px;box-shadow:0 12px 20px rgba(0,0,0,.2);transform:rotate(-3deg)">'
               f'<div style="font:600 16px Plex;letter-spacing:3px;color:#7A2A20">NOTE TO SELF</div><div style="font:700 70px/1 Caveat;color:#C8312B">{a["note"]}</div></div>', 120, 240, .6, "drop", z=25)
    body += el(f'<div style="font:400 120px/0.9 Anton;color:#1C1C1C;width:900px">{c[2].upper()}</div>', 120, 420, .5, "wipe", z=25)
    body += el(f'<div style="font:500 14px Plex;color:rgba(0,0,0,.55);width:1000px">{a["src"]}</div>', 40, 1870, 0, "pop", extra=STILL, z=99)
    return body, "background:#E5E3DD"


DEV4 = {"portrait_board": d_portrait_board, "map_fill": d_map_fill, "bar_photo": d_bar_photo, "spot_sticker": d_spot_sticker, "chalk_node": d_chalk_node,
        "strips": d_strips, "monument_card": d_monument_card, "portal": d_portal, "panorama": d_panorama, "strip_monument": d_strip_monument, "hud": d_hud,
        "doc_board": d_doc_board, "doodle": d_doodle, "map_event": d_map_event, "flag_paper": d_flag_paper, "portrait_doc": d_portrait_doc,
        "v_object_map": d_v_object_map, "v_depth": d_v_depth}
VERTICAL = {"v_object_map", "v_depth"}
