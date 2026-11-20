"""Stroke-by-stroke drawing: hand-wobbled ink paths revealed in order with a pen at the tip. A frame is the drawing
at progress p (0..1). Objects only, no faces."""
import math, random
from pathlib import Path
D = Path(__file__).resolve().parent
rnd = random.Random(7)


def wob(pts, amp=2.2, step=10):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / step))
        for i in range(n):
            t = i / n
            out.append((x0 + (x1 - x0) * t + rnd.uniform(-amp, amp) * .5, y0 + (y1 - y0) * t + rnd.uniform(-amp, amp) * .5))
    out.append(pts[-1])
    return out


def arc(cx, cy, rx, ry, a0, a1, n=40):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def length(p):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(p, p[1:]))


def rot(pts, cx, cy, deg):
    a = math.radians(deg)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in pts]


# strokes: (points, colour, width)
INK, RED, BLUE = "#1C1C1C", "#C8312B", "#2457C5"
S = []
for ox in (300, 1060):                       # two small charts: height (up) against temperature (right)
    S.append((wob([(ox, 380), (ox, 900), (ox + 560, 900)], 1.4), INK, 4))
    S.append((wob([(ox - 14, 400), (ox, 378), (ox + 14, 400)], 1), INK, 4))
    S.append((wob([(ox + 540, 886), (ox + 562, 900), (ox + 540, 914)], 1), INK, 4))
# ordinary day: cooler with height (line leans left as it rises)
S.append((wob([(300 + 470, 880), (300 + 330, 700), (300 + 190, 520), (300 + 90, 410)], 1.6), BLUE, 6))
# inversion: cool at the ground, warmer above (bends right), then cooler again
S.append((wob([(1060 + 170, 880), (1060 + 260, 780), (1060 + 430, 690), (1060 + 330, 560), (1060 + 180, 420)], 1.6), RED, 6))
# smoke dots: rising high on the left, stuck low on the right
import random as _r
rr = _r.Random(3)
for i in range(16):
    x, y = 300 + rr.randint(60, 420), rr.randint(430, 860)
    S.append((wob(arc(x, y, 9, 9, 0, 360, 10), .6), "#6E6760", 3))
for i in range(16):
    x, y = 1060 + rr.randint(60, 460), rr.randint(740, 870)
    S.append((wob(arc(x, y, 9, 9, 0, 360, 10), .6), "#6E6760", 3))
# the lid bracket on the right chart
S.append((wob([(1060 + 470, 640), (1060 + 520, 640), (1060 + 520, 730), (1060 + 470, 730)], 1), RED, 5))
TOTAL = sum(length(p) for p, c, w in S)


def page(progress, words):
    target = TOTAL * progress
    acc, svg, tip = 0, "", None
    for p, c, w in S:
        L = length(p)
        if acc >= target:
            break
        shown = min(L, target - acc)
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in p)
        svg += f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{L:.1f}" stroke-dashoffset="{L - shown:.1f}"/>'
        if shown < L:   # the tip
            s = 0
            for a, b in zip(p, p[1:]):
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                if s + seg >= shown:
                    t = (shown - s) / seg; tip = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t); break
                s += seg
        acc += L
    pen = ""
    if tip and progress < 1:
        x, y = tip
        pen = (f'<g transform="translate({x:.0f},{y:.0f}) rotate(-38)"><polygon points="0,0 -10,-34 10,-34" fill="#E9C99A" stroke="#1C1C1C" stroke-width="2"/>'
               f'<polygon points="0,0 -4,-12 4,-12" fill="#1C1C1C"/><rect x="-11" y="-250" width="22" height="216" rx="4" fill="#2457C5" stroke="#122C66" stroke-width="2"/>'
               f'<rect x="-11" y="-264" width="22" height="16" rx="3" fill="#F2B6B0" stroke="#1C1C1C" stroke-width="2"/></g>')
    paper = ("background:#FBF8F0;background-image:linear-gradient(90deg,transparent 118px,#E7A9A3 118px,#E7A9A3 121px,transparent 121px),"
             "repeating-linear-gradient(0deg,transparent 0 47px,#D9E3F2 47px 48px)")
    reveal = lambda txt, frac, style, x, y: (f'<div style="position:absolute;left:{x}px;top:{y}px;white-space:nowrap;overflow:hidden;width:{int(frac * 100)}%;max-width:1500px;{style}">{txt}</div>' if frac > 0 else "")
    f_title = min(1, progress / .18); f_note = max(0, min(1, (progress - .8) / .2))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Caveat;src:url(/fonts/caveat-latin-700-normal.woff2)}}@font-face{{font-family:Plex;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}}
@font-face{{font-family:Marker;src:url(/fonts/permanent-marker-latin-400-normal.woff2)}}
body{{margin:0;width:1920px;height:1080px;overflow:hidden;{paper}}}</style></head><body>
<div style="position:absolute;left:160px;top:70px;font:500 18px Plex;letter-spacing:5px;color:#8A8A8A">PRINT FACTS · THE BOWL · NOTES</div>
{reveal("Upside-down air", f_title, "font:400 96px Marker;color:#1C1C1C", 160, 110)}
{reveal("height ↑   temperature →", min(1, progress / .3), "font:700 40px Caveat;color:#555", 166, 245)}
<svg width="1920" height="1080" style="position:absolute;left:0;top:0">{svg}{pen}</svg>
{reveal("ordinary day: colder as you go up, smoke rises", min(1, progress / .5), "font:700 40px Caveat;color:#2457C5", 300, 930)}
{reveal("inversion: a warm layer on top", f_note, "font:700 40px Caveat;color:#C8312B", 1060, 930)}
{reveal("the lid", f_note, "font:700 46px Caveat;color:#C8312B", 1600, 660)}
<div style="position:absolute;left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.4)">SKETCH, NOT DATA · DRAWN STROKE BY STROKE IN THE STUDIO · THE IDEA: NASA EARTH OBSERVATORY, 3 NOV 2024</div>
<script>document.fonts.ready.then(()=>window.READY=true)</script></body></html>"""


if __name__ == "__main__":
    (D / "html" / "05_upside_down_air.html").write_text(page(1.0, None))
