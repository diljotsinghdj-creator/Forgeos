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
# water
for k, y in enumerate((700, 735)):
    S.append((wob([(x, y + 10 * math.sin(x / 55 + k)) for x in range(160, 1500, 30)], 1.5), BLUE, 4 - k))
# boat hull, tilted, half under the water
cx, cy = 820, 660
hull = rot([(560, 600), (600, 690), (1040, 690), (1090, 600), (560, 600)], cx, cy, -14)
S.append((wob(hull), INK, 5))
mast = rot([(820, 600), (820, 380)], cx, cy, -14); S.append((wob(mast), INK, 5))
sail = rot([(830, 390), (990, 580), (830, 580)], cx, cy, -14); S.append((wob(sail + [sail[0]]), INK, 4))
# water inside the hull (hatching)
for i in range(6):
    a = rot([(640 + i * 60, 640), (690 + i * 60, 682)], cx, cy, -14); S.append((wob(a, 1), BLUE, 3))
# coins falling into the boat
for i, (x, y) in enumerate(((1200, 260), (1260, 360), (1180, 450))):
    S.append((wob(arc(x, y, 34, 34, 0, 360, 36), 1.2), INK, 4))
    S.append((wob([(x - 8, y - 14), (x - 8, y + 14)], .8), INK, 3))
    S.append((wob([(x + 6, y - 14), (x + 6, y + 14)], .8), INK, 3))
# arrow from coins to boat
S.append((wob([(1150, 480), (1060, 540), (1000, 560)], 1.5), RED, 4))
S.append((wob([(1015, 535), (1000, 560), (1030, 566)], 1), RED, 4))
# underline for the note
S.append((wob([(1100, 862), (1600, 852)], 1.5), RED, 5))

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
<div style="position:absolute;left:160px;top:70px;font:500 18px Plex;letter-spacing:5px;color:#8A8A8A">DRAGON PSYCHOLOGY · SKETCHBOOK · PAGE 03</div>
{reveal("The Sunk Cost", f_title, "font:400 96px Marker;color:#1C1C1C", 160, 110)}
{reveal("why we keep bailing out a boat that is already going down", min(1, progress / .3), "font:700 44px Caveat;color:#555", 166, 245)}
<svg width="1920" height="1080" style="position:absolute;left:0;top:0">{svg}{pen}</svg>
{reveal("money already spent is gone either way", f_note, "font:700 50px Caveat;color:#C8312B", 1100, 790)}
{reveal("the only question is: what next?", f_note, "font:700 44px Caveat;color:#1C1C1C", 1100, 880)}
<div style="position:absolute;left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.4)">DRAWN STROKE BY STROKE IN THE STUDIO · FRAME AT {int(progress * 100)}%</div>
<script>document.fonts.ready.then(()=>window.READY=true)</script></body></html>"""


if __name__ == "__main__":
    for p in (.62, 1.0):
        (D / "html" / f"draw_sunkcost_{int(p * 100):03d}.html").write_text(page(p, None))
