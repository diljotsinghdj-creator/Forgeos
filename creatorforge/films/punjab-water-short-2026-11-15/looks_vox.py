"""The two reference looks with the Vox layer added: marker circle, arrows, highlighter, sticky note, taped evidence
card and leader-line callouts. Numbers only from dossier.json. Writes look_dark_vox and look_holo_vox."""
import math
import random
from pathlib import Path
from new_pages import STATES, P

H = Path("html")
SIG, RED, INK = "#FFDD33", "#E5483C", "#141414"
FONT = ("<style>@font-face{font-family:Caveat;src:url(/fonts/caveat-latin-700-normal.woff2)}"
        "@font-face{font-family:Marker;src:url(/fonts/permanent-marker-latin-400-normal.woff2)}"
        "@font-face{font-family:AntonX;src:url(/fonts/anton-latin-400-normal.woff2)}"
        "@font-face{font-family:PlexX;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}</style>")


def wobble_ellipse(cx, cy, rx, ry, seed=1, turns=1.12):
    r = random.Random(seed); pts = []
    for i in range(80):
        a = -0.6 + 2 * math.pi * turns * i / 79
        k = 1 + r.uniform(-.025, .025)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def arrow(x1, y1, x2, y2, col, bend=-80, w=6):
    mx, my = (x1 + x2) / 2 + bend * .5, (y1 + y2) / 2 + bend
    ang = math.atan2(y2 - my, x2 - mx); h = 26
    a1 = (x2 - h * math.cos(ang - .45), y2 - h * math.sin(ang - .45)); a2 = (x2 - h * math.cos(ang + .45), y2 - h * math.sin(ang + .45))
    return (f'<path d="M{x1} {y1} Q {mx:.0f} {my:.0f} {x2} {y2}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M{a1[0]:.0f} {a1[1]:.0f} L{x2} {y2} L{a2[0]:.0f} {a2[1]:.0f}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


def tape(x, y, rot):
    return f'<div style="position:absolute;left:{x}px;top:{y}px;width:150px;height:40px;background:rgba(236,226,200,.82);transform:rotate({rot}deg);box-shadow:0 2px 4px rgba(0,0,0,.25)"></div>'


def sticky(x, y, rot, html, w=330):
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;background:#FFE873;padding:22px 24px;transform:rotate({rot}deg);'
            f'box-shadow:0 14px 22px rgba(0,0,0,.45);font:700 40px/1.12 Caveat;color:{INK}">{html}</div>')


def statement_card(x, y, rot):
    rows = "".join(f'<div style="display:flex;justify-content:space-between;border-bottom:2px dashed #B9AE95;padding:9px 0;font:500 22px PlexX;color:{INK}">'
                   f'<span>{k}</span><span style="{st}">{v}</span></div>' for k, v, st in (
                       ("Safe to draw", "16.80 BCM", ""), ("Drawn", "26.27 BCM", f"color:{RED}"),
                       ("Share used", "156 %", f"background:linear-gradient(transparent 45%,{SIG} 45%,{SIG} 92%,transparent 92%)")))
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:460px;background:#F3EEDF;padding:22px 26px;transform:rotate({rot}deg);box-shadow:0 20px 34px rgba(0,0,0,.55)">'
            f'<div style="font:500 15px PlexX;letter-spacing:3px;color:#7A6A4A">PUNJAB · GROUNDWATER · 2025</div>{rows}'
            f'<div style="font:500 13px PlexX;color:#7A6A4A;margin-top:8px">2025 national assessment (Jal Shakti/CGWB)</div></div>')


def inject(page, overlay, title_fix=None):
    s = (H / f"{page}.html").read_text()
    if title_fix:
        for a, b in title_fix:
            assert a in s, a
            s = s.replace(a, b)
    s = s.replace("</body>", FONT + f'<div style="position:absolute;left:0;top:0;width:1080px;height:1920px;pointer-events:none;z-index:50">{overlay}</div></body>', 1)
    return s


# ---- dark satellite + Vox layer -------------------------------------------------------------------------------------
xs = [P(lo, la)[0] for r in STATES["Punjab"] for lo, la in r]; ys = [P(lo, la)[1] for r in STATES["Punjab"] for lo, la in r]
cx, cy, rx, ry = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (max(xs) - min(xs)) / 2 + 40, (max(ys) - min(ys)) / 2 + 40
svg = (f'<svg width="1080" height="1920" style="position:absolute;left:0;top:0">'
       f'<path d="{wobble_ellipse(cx, cy, rx, ry, 3)}" fill="none" stroke="{SIG}" stroke-width="8" stroke-linecap="round" opacity=".95"/>'
       + arrow(300, 1240, int(cx - rx * .55), int(cy + ry * .6), SIG, bend=40)
       + arrow(860, 690, int(cx + rx * .25), int(cy - ry * .78), "#FFFFFF", bend=-30, w=5) + "</svg>")
ov = (svg
      + sticky(640, 470, 3, "Rivers: water on top.<br><span style=\"color:#B3261E\">Overdraft: water below.</span>", 380)
      + statement_card(60, 1230, -4) + tape(230, 1214, -6)
      + f'<div style="position:absolute;left:{int(min(cx + rx - 170, 760))}px;top:{int(cy + ry + 6)}px;font:700 46px Caveat;color:{SIG};transform:rotate(-3deg);white-space:nowrap">Punjab (India)</div>')
s = inject("look_dark_b", ov, [(
    f'<div style="font:400 110px/0.95 Anton;color:{SIG};width:940px;letter-spacing:2px">ONE OVERDRAFT.</div>',
    f'<div style="font:400 110px/0.95 Anton;color:{INK};width:940px;letter-spacing:2px"><span style="background:linear-gradient(transparent 8%,{SIG} 8%,{SIG} 96%,transparent 96%);padding:0 10px">ONE OVERDRAFT.</span></div>')])
(H / "look_dark_vox.html").write_text(s)

# ---- hologram + Vox layer -------------------------------------------------------------------------------------------
grid = "".join(f'<div style="position:absolute;left:{(i % 17) * 22}px;top:{(i // 17) * 22}px;width:17px;height:17px;background:{RED if i < 111 else "#8F8A80"}"></div>' for i in range(153))
card = (f'<div style="position:absolute;left:60px;top:1150px;width:430px;background:#F3EEDF;padding:24px 26px 26px;transform:rotate(-3deg);box-shadow:0 22px 36px rgba(0,0,0,.6)">'
        f'<div style="font:400 50px/1 AntonX;color:{INK}">111 OF 153 BLOCKS</div><div style="font:400 30px/1.1 AntonX;color:{RED};margin:4px 0 14px">PUMP MORE THAN IS SAFE</div>'
        f'<div style="position:relative;height:200px">{grid}</div>'
        f'<div style="font:500 13px PlexX;color:#7A6A4A;margin-top:6px">ONE SQUARE = ONE BLOCK · 2025 NATIONAL ASSESSMENT</div></div>')
callout = (f'<svg width="1080" height="1920" style="position:absolute;left:0;top:0">'
           f'<circle cx="760" cy="560" r="11" fill="{SIG}"/><circle cx="760" cy="560" r="26" fill="none" stroke="{SIG}" stroke-width="3"/>'
           f'<path d="M760 560 L860 470 L1020 470" fill="none" stroke="{SIG}" stroke-width="3"/>'
           + arrow(560, 1290, 640, 975, SIG, bend=-50) + "</svg>"
           f'<div style="position:absolute;left:870px;top:420px;font:500 20px/1.3 PlexX;letter-spacing:3px;color:{SIG};width:200px;text-align:left">HIMALAYA<br><span style="color:#CFFFF5">THE RIVERS<br>START HERE</span></div>')
ov2 = (callout + card + tape(170, 1132, 5)
       + sticky(600, 1210, 4, "Plenty on the surface…<br><span style=\"color:#B3261E\">overdrawn underneath.</span>", 400)
       + f'<div style="position:absolute;left:470px;top:905px;font:700 44px Caveat;color:#CFFFF5;transform:rotate(-4deg)">the plains pump from below</div>')
s = inject("look_holo_b", ov2, [("FIVE RIVERS</div>", f'<span style="background:linear-gradient(transparent 55%,rgba(255,221,51,.85) 55%,rgba(255,221,51,.85) 92%,transparent 92%)">FIVE RIVERS</span></div>')])
(H / "look_holo_vox.html").write_text(s)
print("ok")
