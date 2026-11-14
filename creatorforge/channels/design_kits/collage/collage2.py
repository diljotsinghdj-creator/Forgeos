"""Collage kit v2: helpers for the owner's round-7/8 reference vocabulary (see STYLE_REFERENCES.md).

Every helper returns HTML for a 1920x1080 page that loads kit2.js. Animated pieces carry data-in/data-at; a still is
the page at t=99. Content stays real: helpers draw frames, light, paper and labels around real material; platform UI
cards are labelled recreations, never fake posts by real people.
"""
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = Path("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts")
INK, RED, SIG, CREAM, KHAKI = "#141414", "#C9302C", "#FFDD33", "#F4EEDF", "#B8A27A"


def fonts_css():
    f = [("Anton", "anton-latin-400-normal"), ("Oswald", "oswald-latin-600-normal"), ("Marker", "permanent-marker-latin-400-normal"),
         ("Playfair", "playfair-display-latin-900-normal"), ("PlayfairI", "playfair-display-latin-700-italic"), ("Archivo", "archivo-black-latin-400-normal"),
         ("Bebas", "bebas-neue-latin-400-normal"), ("Mono", "jetbrains-mono-latin-700-normal"), ("Serif", "dm-serif-display-latin-400-normal"),
         ("Inter", "inter-latin-600-normal"), ("Fraunces", "fraunces-latin-900-normal"), ("DMono", "dm-mono-latin-500-normal")]
    return "".join(f"@font-face{{font-family:{n};src:url({(FONTS / (p + '.woff2')).as_uri()})}}" for n, p in f)


def page(body, bg="", dur=5, push=.04, credit="", cls=""):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fonts_css()}
body{{margin:0;width:1920px;height:1080px;overflow:hidden;font-family:Inter;color:{INK};{bg}}}
#cam{{position:absolute;inset:0;transform-origin:50% 50%}} .el{{position:absolute}}
.mono{{font-family:Mono;letter-spacing:1px}} .cap{{font-family:Bebas;letter-spacing:4px}}
.credit{{position:absolute;left:24px;bottom:12px;font:600 12px Mono;letter-spacing:1px;color:rgba(20,20,20,.6);text-transform:uppercase;max-width:1860px;z-index:99}}
.hl{{background:linear-gradient(transparent 55%,{SIG} 55%,{SIG} 94%,transparent 94%);background-size:var(--hl,100%) 100%;background-repeat:no-repeat}}
</style><script src="{(HERE / 'kit2.js').as_uri()}"></script></head>
<body class="{cls}" data-dur="{dur}" data-push="{push}"><svg width="0" height="0" style="position:absolute">
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="3" seed="12"/><feColorMatrix values="0 0 0 0 .28  0 0 0 0 .25  0 0 0 0 .2  0 0 0 .34 0"/></filter>
<filter id="rough"><feTurbulence type="fractalNoise" baseFrequency=".04" numOctaves="4" seed="3"/><feDisplacementMap in="SourceGraphic" scale="12"/></filter></svg>
<div id="cam">{body}</div>
<svg class="el" style="inset:0;pointer-events:none;opacity:.5;z-index:90" width="1920" height="1080"><rect width="1920" height="1080" filter="url(#grain)"/></svg>
<div class="el" style="inset:0;pointer-events:none;z-index:91;background:radial-gradient(ellipse at 50% 48%,transparent 52%,rgba(20,14,8,.38) 100%)"></div>
{f'<div class="credit">{credit}</div>' if credit else ''}</body></html>"""


def el(html, x, y, at=0, k="pop", style="", base="", extra="", z=5):
    return f'<div class="el" data-in="{k}" data-at="{at}" data-base="{base}" style="left:{x}px;top:{y}px;z-index:{z};{style}" {extra}>{html}</div>'


STILL = 'data-d=".01" data-breathe="0" data-jit="0" data-shadow="0"'


def gobo(op=.30, z=80, angle=0):
    """Window-blind light: soft dark bands drifting across the paper (multiply)."""
    bands = "repeating-linear-gradient(90deg,transparent 0 150px,rgba(40,30,20,.85) 150px 210px)"
    return f'<div class="gobo" style="position:absolute;left:-300px;top:-200px;width:2600px;height:1500px;background:{bands};filter:blur(22px);opacity:{op};mix-blend-mode:multiply;z-index:{z};pointer-events:none;transform:skewX(-18deg)"></div>'


def flare(x, y, r=260, at=0, z=81):
    return el(f'<div style="width:{2 * r}px;height:{2 * r}px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.95) 0%,rgba(255,250,230,.45) 18%,transparent 62%);mix-blend-mode:screen"></div>', x - r, y - r, at, "pop", z=z)


def micro(x, y, lines, size=11, width=260, at=0, z=4, col="#3a3a3a"):
    """Editorial micro-typography: a tiny column of real text (from the dossier), poster-style."""
    return el(f'<div style="width:{width}px;font:600 {size}px/1.35 Inter;color:{col};text-transform:uppercase;letter-spacing:.5px">{"<br>".join(lines)}</div>', x, y, at, "wipe", z=z)


def barcode(x, y, w=180, h=34, seed=1, at=0, z=4):
    r = random.Random(seed)
    bars, cx = "", 0
    while cx < w:
        bw = r.choice((1, 1, 2, 3))
        if r.random() > .35:
            bars += f'<rect x="{cx}" y="0" width="{bw}" height="{h}" fill="{INK}"/>'
        cx += bw + 1
    return el(f'<svg width="{w}" height="{h}">{bars}</svg>', x, y, at, "wipe", z=z)


def index_no(text, x, y, size=44, at=0, z=4):
    return el(f'<div style="font:italic 900 {size}px Playfair;color:{INK}">{text}</div>', x, y, at, "wipe", z=z)


def grid_paper():
    return ('background:#ECEBE7;background-image:linear-gradient(rgba(0,0,0,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.07) 1px,transparent 1px);'
            'background-size:56px 56px')


def studio_paper():
    return "background:radial-gradient(ellipse at 45% 35%,#F2F1EE 0%,#DEDCD7 60%,#C9C6BF 100%)"


def wood():
    return ("background:#5A3B22;background-image:repeating-linear-gradient(92deg,rgba(0,0,0,.18) 0 3px,transparent 3px 22px),"
            "repeating-linear-gradient(88deg,rgba(255,220,170,.06) 0 2px,transparent 2px 37px),radial-gradient(ellipse at 50% 40%,#7A5230 0%,#4A2F1A 75%,#2A1A0E 100%)")


def red_cinema():
    return "background:radial-gradient(ellipse at 50% 38%,#5A0D10 0%,#2A0608 55%,#0E0203 100%)"


def disc_frame(inner, cx, cy, r, col=KHAKI, at=0, z=5, k="pop"):
    return el(f'<div style="width:{2 * r}px;height:{2 * r}px;border-radius:50%;background:{col};display:flex;align-items:center;justify-content:center;overflow:hidden">{inner}</div>', cx - r, cy - r, at, k, z=z)


def polaroid(inner_html, caption, w=300, rot=0, at=0, x=0, y=0, z=6, k="drop", cap_font="Mono", pin=None):
    """A polaroid: real image/scrap inside, typewriter caption."""
    pin_html = f'<div style="position:absolute;left:{w / 2 - 12}px;top:-14px;width:24px;height:24px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#ff7a6e,{RED} 60%,#6d1410);box-shadow:2px 3px 3px rgba(0,0,0,.4)"></div>' if pin else ""
    return el(f'<div style="position:relative;width:{w}px;background:#FBFAF6;padding:14px 14px 0">{pin_html}<div style="width:{w - 28}px;height:{w - 28}px;overflow:hidden;background:#222;display:flex;align-items:center;justify-content:center">{inner_html}</div>'
              f'<div style="font:600 18px {cap_font};letter-spacing:.5px;padding:14px 2px 18px;line-height:1.3">{caption}</div></div>', x, y, at, k, base=f"rotate({rot}deg)", z=z)


def clothesline(items, y=170, sag=90, at0=.2, step=.45, w=290, x0=120, gap=370):
    """A string with polaroids hanging on pegs. items: (inner_html, caption)."""
    n = len(items)
    x1 = x0 + (n - 1) * gap + w
    line = el(f'<svg width="1920" height="400" style="overflow:visible"><path d="M-40 {y - 60} Q 960 {y + sag} 1960 {y - 60}" stroke="#6b5a45" stroke-width="3" fill="none"/></svg>', 0, 0, 0, "pop", extra=STILL, z=5)
    out = line
    for i, (inner, cap) in enumerate(items):
        cx = x0 + i * gap + w / 2
        u = (cx + 40) / 2000
        sy = (1 - u) ** 2 * (y - 60) + 2 * (1 - u) * u * (y + sag) + u ** 2 * (y - 60)
        rot = [-4, 3, -2, 4, -3, 2][i % 6]
        out += el('<div style="width:22px;height:54px;background:linear-gradient(90deg,#C9A36B,#E2C48F 50%,#B88E55);border-radius:3px;box-shadow:2px 3px 3px rgba(0,0,0,.35)"></div>', cx - 11, sy - 18, at0 + i * step, "drop", z=8)
        out += polaroid(inner, cap, w, rot, at0 + i * step, cx - w / 2, sy + 10, z=7)
    return out


def pin_dot(x, y, z=9):
    return f'<div class="el" style="left:{x - 12}px;top:{y - 12}px;width:24px;height:24px;border-radius:50%;z-index:{z};background:radial-gradient(circle at 35% 35%,#ff7a6e,{RED} 60%,#6d1410);box-shadow:2px 3px 3px rgba(0,0,0,.4)"></div>'


def red_string(pts, at=0, z=8, col=RED):
    d = "M" + " L".join(f"{x} {y}" for x, y in pts)
    return f'<svg class="el" data-in="draw" data-at="{at}" data-d="1.0" style="inset:0;z-index:{z};overflow:visible" width="1920" height="1080"><path d="{d}" stroke="{col}" stroke-width="3.5" fill="none" filter="url(#rough)"/></svg>'


def torn_label(text, x, y, size=30, bg=CREAM, col=INK, rot=0, at=0, z=7, font="Mono", seed=1):
    r = random.Random(seed)
    pts = [(0, r.uniform(0, 8)) for _ in range(1)]
    clip = "polygon(" + ",".join([f"{i * 5}% {r.uniform(0, 9):.0f}%" for i in range(21)] + [f"{100 - i * 5}% {100 - r.uniform(0, 9):.0f}%" for i in range(21)]) + ")"
    return el(f'<div style="font:600 {size}px {font};background:{bg};color:{col};padding:16px 26px;clip-path:{clip};white-space:nowrap">{text}</div>', x, y, at, "slide", base=f"rotate({rot}deg)", z=z)


def ui_card(platform_svg, title, rows, x, y, w=560, at=0, rot=0, z=7, k="slide", dark=False):
    """A labelled recreation of a platform UI card (generic content, marked ILLUSTRATION)."""
    bg, fg, sub = ("#1E1E1E", "#F2F2F2", "#9a9a9a") if dark else ("#FFFFFF", "#141414", "#777")
    body = "".join(f'<div style="margin-top:12px;padding:12px 16px;border-radius:14px;background:{"#2A2A2A" if dark else "#F1F1F1"};font:600 22px Inter;color:{fg}">{r}</div>' for r in rows)
    return el(f'<div style="width:{w}px;background:{bg};border-radius:22px;padding:22px 24px;box-shadow:0 30px 60px rgba(0,0,0,.45)">'
              f'<div style="display:flex;align-items:center;gap:14px">{platform_svg}<div style="font:800 26px Inter;color:{fg}">{title}</div>'
              f'<div style="margin-left:auto;font:600 13px Mono;color:{sub};letter-spacing:2px">ILLUSTRATION</div></div>{body}</div>', x, y, at, k, base=f"rotate({rot}deg)", z=z)


def sunburst(cx, cy, r, col="#E8571E", n=48, at=0, z=1, k="pop"):
    rays = ""
    for i in range(n):
        if i % 2:
            continue
        import math
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        rays += f'<path d="M{cx} {cy} L{cx + r * math.cos(a0):.0f} {cy + r * math.sin(a0):.0f} L{cx + r * math.cos(a1):.0f} {cy + r * math.sin(a1):.0f} Z" fill="{col}"/>'
    return f'<svg class="el" data-in="{k}" data-at="{at}" data-shadow="0" style="inset:0;z-index:{z};overflow:visible" width="1920" height="1080">{rays}</svg>'


def dissolve_img(src, x, y, w, h, at=0, cell=48, col="#ECEBE7", z=5, seed=4, style=""):
    """An image revealed by a pixel dissolve (cells of the ground colour vanish in random order)."""
    r = random.Random(seed)
    cells = "".join(f'<div class="cell" data-o="{r.random():.3f}" style="position:absolute;left:{cx * cell}px;top:{cy * cell}px;width:{cell + 1}px;height:{cell + 1}px;background:{col}"></div>'
                    for cy in range(int(h / cell) + 1) for cx in range(int(w / cell) + 1))
    return (el(f'<img src="{Path(src).as_uri()}" style="width:{w}px;height:{h}px;object-fit:cover;display:block;{style}">', x, y, 0, "pop", extra=STILL, z=z)
            + f'<div class="el" data-in="dissolve" data-at="{at}" data-d="1.2" data-breathe="0" data-jit="0" data-shadow="0" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;overflow:hidden;z-index:{z + 1}">{cells}</div>')


def falling(items_html, n=14, seed=7, z=40):
    r = random.Random(seed)
    kids = "".join(f'<div style="position:absolute;left:{r.uniform(0, 1860):.0f}px;top:0" data-v="{r.uniform(120, 260):.0f}" data-y0="{r.uniform(-700, 600):.0f}" data-r="{r.uniform(-40, 40):.0f}" data-spin="{r.uniform(-60, 60):.0f}">{r.choice(items_html)}</div>' for _ in range(n))
    return f'<div class="fall" style="position:absolute;inset:0;z-index:{z};pointer-events:none">{kids}</div>'
