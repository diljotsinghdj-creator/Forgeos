"""Hand-composed shots for the 30-second US midterms film (editorial-shards kit). Each shot is one HTML page; every
element carries its entrance (data-in / data-at), so the approved still is also the animated shot."""
from pathlib import Path
D = Path(__file__).resolve().parent
A = (D / "assets").as_uri()
HEAD = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../kit.css"><script src="../kit.js"></script></head>
<body data-dur="{dur}" data-push="{push}"><svg width="0" height="0" style="position:absolute"><filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="{seed}"/><feColorMatrix values="0 0 0 0 .35  0 0 0 0 .3  0 0 0 0 .25  0 0 0 .35 0"/></filter>
<filter id="torn"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="4" seed="{seed}"/><feDisplacementMap in="SourceGraphic" scale="20"/></filter></svg>
<div id="cam">"""
TAIL = """</div><svg class="grain" width="1920" height="1080"><rect width="1920" height="1080" filter="url(#grain)"/></svg>{credit}</body></html>"""
def shard(pts, col, at, frm="l", extra=""):
    return f'<svg class="el" data-in="slide" data-from="{frm}" data-at="{at}" style="inset:0" width="1920" height="1080"><polygon points="{pts}" fill="{col}" {extra}/></svg>'
def ground(at, y=1000):
    return (f'<svg class="el" data-in="draw" data-at="{at}" data-d=".7" data-breathe="0" style="inset:0" width="1920" height="1080">'
            f'<path d="M110 {y} C 520 {y-24}, 900 {y+12}, 1400 {y-14} S 1800 {y-4}, 1880 {y-8}" stroke="#111" stroke-width="7" fill="none" stroke-linecap="round"/></svg>')
def cut(img, x, y, h, at, kind="drop", extra=""):
    return f'<img class="el cut" data-in="{kind}" data-at="{at}" src="{A}/{img}" style="left:{x}px;top:{y}px;height:{h}px;{extra}">'
def text(html, x, y, at, kind="pop", style="", cls="", base=""):
    return f'<div class="el {cls}" data-in="{kind}" data-at="{at}" data-base="{base}" style="left:{x}px;top:{y}px;{style}">{html}</div>'
def credit(t):
    return f'<div class="credit">{t}</div>'
CAP = "PHOTO: CAROL M. HIGHSMITH / LIBRARY OF CONGRESS"
shots = {}
# 1 hook: the date
shots["s01_hook"] = dict(dur=3.2, push=.06, credit=CAP, body=
    shard("560,90 1240,40 1330,860 640,930", "#E8551E", .0) + shard("1240,180 1800,120 1760,820 1330,860", "#2B57A8", .1, "r")
    + shard("1180,60 1290,48 1320,480 1210,500", "#111", .2, "t") + ground(.3)
    + cut("capitol.png", 640, 210, 800, .35)
    + text('<div class="serif" style="font-size:230px;color:#2B57A8">Nov 3</div>', 70, 70, .55, "slide")
    + text('<div class="serif" style="font-size:230px;color:#E8551E">2026</div>', 70, 270, .7, "slide")
    + text('<div class="tag">Midterm elections · USA</div>', 82, 520, .9, "wipe", base="rotate(-2deg)"))
# 2 the Senate before: 53 to 47, seats as paper dots in a hemicycle
import math
dots = []
n, rows = 100, [16, 19, 21, 22, 22]
k = 0
for r, cnt in enumerate(rows):
    R = 250 + r * 62
    for j in range(cnt):
        a = math.pi * (j + .5) / cnt
        x, y = 1320 - R * math.cos(a), 900 - R * math.sin(a)
        dots.append((a, x, y))
dots.sort(key=lambda d: d[0])
svg = ['<svg class="el" data-in="pop" data-at=".4" data-breathe="0" style="inset:0" width="1920" height="1080">']
for i, (a, x, y) in enumerate(dots):
    col = "#E8551E" if i < 53 else "#2B57A8"
    svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="23" fill="{col}" filter="url(#torn)"/>')
svg.append('</svg>')
shots["s02_senate_before"] = dict(dur=3.6, push=.04, credit="", body=
    shard("40,40 700,0 760,330 90,380", "#111", 0) + "".join(svg)
    + text('<div class="serif" style="font-size:120px;color:#EEE7D8">Going in</div>', 80, 90, .15, "slide")
    + text('<div class="serif" style="font-size:260px;color:#E8551E">53</div>', 90, 430, .9, "pop")
    + text('<div class="serif" style="font-size:260px;color:#2B57A8">47</div>', 420, 430, 1.1, "pop")
    + text('<div class="tag">Senate · Republicans · Democrats and allies</div>', 96, 720, 1.3, "wipe")
    + text('<div class="marker" style="font-size:48px;transform:rotate(-4deg)">51 needed for control</div>', 1050, 960, 1.6, "wipe")
    + ground(.2, 930))
# 3 both houses flipped: Trump, scattered letters
letters = "".join(text(f'<div class="serif" style="font-size:260px;color:#111">{c}</div>', x, y, .35 + i * .08, "drop")
                  for i, (c, x, y) in enumerate(zip("FLIPPED", [60, 230, 380, 470, 640, 810, 980], [210, 250, 190, 260, 200, 245, 195])))
shots["s03_flipped"] = dict(dur=3.4, push=.05, credit="PHOTO: DANIEL TOROK / WHITE HOUSE (PUBLIC DOMAIN)", body=
    shard("1100,60 1880,20 1900,1060 1180,1080", "#E8551E", 0, "r") + shard("0,640 900,560 980,1080 0,1080", "#2B57A8", .1)
    + letters + cut("trump.png", 1180, 160, 920, .2, "slide")
    + text('<div class="tag">House + Senate · 3 November 2026</div>', 80, 760, 1.0, "wipe", base="rotate(-2deg)"))
# 4 the Senate line: 51
shots["s04_fiftyone"] = dict(dur=3.0, push=.06, credit=CAP, body=
    shard("200,120 1100,60 1180,980 260,1040", "#E8551E", 0) + shard("1190,420 1450,520 1190,620", "#111", .3, "r")
    + text('<div class="serif" style="font-size:720px;color:#2B57A8;filter:url(#torn)">51</div>', 300, 120, .15, "pop")
    + cut("capitol.png", 1350, 470, 520, .45)
    + text('<div class="marker" style="font-size:54px;transform:rotate(-5deg)">the line for control: passed</div>', 1090, 250, .9, "wipe")
    + ground(.2, 1010))
# 5 Kansas, 1932: big letters on a yellow disc (Kupang reference), the state in blue paper
kansas = '<svg class="el" data-in="drop" data-at=".3" style="left:700px;top:520px" width="620" height="330"><polygon points="0,0 560,0 575,22 605,45 612,330 0,330" fill="#2B57A8" filter="url(#torn)"/></svg>'
kl = "".join(text(f'<div class="serif" style="font-size:210px;color:#111">{c}</div>', x, y, .55 + i * .07, "pop")
              for i, (c, x, y) in enumerate(zip("KANSAS", [420, 650, 880, 1100, 1300, 1500], [150, 230, 140, 220, 150, 235])))
shots["s05_kansas"] = dict(dur=3.4, push=.05, credit="", body=
    '<div class="el" data-in="pop" data-at="0" style="left:560px;top:80px;width:900px;height:900px;border-radius:50%;background:#FFDD33"></div>'
    + kansas + kl
    + text('<div class="serif" style="font-size:260px;color:#E8551E">1932</div>', 80, 700, 1.2, "slide")
    + text('<div class="tag">First Democratic senator since</div>', 92, 640, 1.0, "wipe", base="rotate(-2deg)")
    + text('<div class="marker" style="font-size:46px;transform:rotate(-6deg)">Kansas, 2026</div>', 1460, 860, 1.5, "wipe"))
# 6 the echo: Bush, 2006
shots["s06_bush2006"] = dict(dur=3.8, push=.05, credit="PHOTO: ERIC DRAPER / WHITE HOUSE (PUBLIC DOMAIN)", body=
    text('<div class="serif" style="font-size:420px;color:#E8551E">2006</div>', 70, 250, 0, "slide")
    + shard("1060,140 1700,80 1780,1080 1100,1080", "#2B57A8", .15, "r")
    + cut("bush.png", 1080, 210, 870, .35)
    + text('<div class="tag">Last Republican president to lose both houses</div>', 90, 860, .9, "wipe", base="rotate(-2deg)")
    + text('<div class="marker" style="font-size:60px;transform:rotate(-6deg)">we have seen this before</div>', 130, 120, 1.3, "wipe"))
# 7 2006 House: 232 -> 202, torn paper bars
shots["s07_house2006"] = dict(dur=3.6, push=.04, credit="DATA: 2006 HOUSE RESULTS · PHOTO: ERIC DRAPER (PD)", body=
    shard("40,60 560,20 620,350 90,390", "#2B57A8", 0)
    + text('<div class="serif" style="font-size:150px;color:#EEE7D8">2006</div>', 80, 90, .1, "slide")
    + '<svg class="el" data-in="slide" data-from="b" data-at=".3" style="inset:0" width="1920" height="1080"><g filter="url(#torn)"><rect x="760" y="196" width="250" height="784" fill="#E8551E"/></g></svg>'
    + '<svg class="el" data-in="slide" data-from="b" data-at=".45" style="inset:0" width="1920" height="1080"><g filter="url(#torn)"><rect x="1130" y="298" width="250" height="682" fill="#2B57A8"/></g></svg>'
    + '<svg class="el" data-in="draw" data-at="1.2" style="inset:0" width="1920" height="1080"><path d="M1130 196 H1380 V298 H1130 Z" fill="none" stroke="#111" stroke-width="4" stroke-dasharray="14 10"/></svg>'
    + text('<div class="serif" style="font-size:150px;color:#111">232</div>', 770, 50, .6, "pop")
    + text('<div class="serif" style="font-size:150px;color:#EEE7D8">202</div>', 1140, 300, .8, "pop")
    + text('<div class="marker" style="font-size:60px;color:#E8551E;transform:rotate(-5deg)">&minus;30</div>', 1180, 205, 1.4, "pop")
    + text('<div style="font:900 78px Playfair;line-height:1;color:#111"><span class="hl" data-in="sweep" data-at="1.6">Thirty seats</span><br>gone</div>', 70, 430, .9, "slide")
    + text('<div style="font:800 22px Inter;letter-spacing:3px">REPUBLICAN HOUSE SEATS, 2006</div>', 72, 620, 1.1, "wipe")
    + shard("1500,520 1860,470 1880,1000 1460,1000", "#E8551E", .2, "r") + cut("bush.png", 1440, 470, 540, .6)
    + ground(.2, 985))
# 8 the pattern: 18 of 20 midterms (ticket stubs, vintage reference)
tix = []
for i in range(20):
    c, r = i % 5, i // 5
    x, y = 840 + c * 205, 140 + r * 215
    lost = (1946 + 4 * i) not in (1998, 2002)
    tix.append(f'<div class="el" data-in="drop" data-at="{.2 + i * .05:.2f}" style="left:{x}px;top:{y}px;width:180px;height:190px;background:#F4EEDD;'
               f'box-shadow:6px 8px 0 rgba(0,0,0,.18);border:2px dashed #b9ab88;transform:rotate({(i * 37 % 7) - 3}deg)">'
               f'<div style="font:800 15px Inter;letter-spacing:2px;color:#6a5f4c;margin:14px">MIDTERM</div>'
               f'<div style="font:900 44px Playfair;margin:0 14px">{1946 + 4 * i}</div>'
               + (f'<div style="position:absolute;left:18px;bottom:20px;font:800 30px Inter;color:#E8551E;border:4px solid #E8551E;padding:2px 10px;transform:rotate(-12deg)">LOST</div>' if lost else
                  f'<div style="position:absolute;left:18px;bottom:22px;font:800 24px Inter;color:#2B57A8">HELD</div>')
               + '</div>')
shots["s08_pattern"] = dict(dur=4.2, push=.03, credit="COUNT: AL JAZEERA, NOVEMBER 2026", body=
    "".join(tix)
    + text('<div class="serif" style="font-size:300px;color:#E8551E">18</div>', 80, 160, 1.4, "pop")
    + text('<div class="serif" style="font-size:140px;color:#111">of 20</div>', 120, 470, 1.6, "pop")
    + text('<div class="tag">The president\'s party lost House seats</div>', 90, 660, 1.8, "wipe", base="rotate(-2deg)")
    + text('<div class="marker" style="font-size:46px;transform:rotate(-4deg)">midterms 1946 to 2022</div>', 110, 760, 2.1, "wipe"))
# 9 twenty years apart: Bush and Trump, both years
shots["s09_echo"] = dict(dur=3.6, push=.05, credit="PHOTOS: ERIC DRAPER (PD) · DANIEL TOROK / WHITE HOUSE (PD) · CAROL M. HIGHSMITH / LIBRARY OF CONGRESS", body=
    shard("520,120 1130,60 1250,820 610,900", "#E8551E", 0) + shard("1180,200 1760,140 1700,760 1290,820", "#2B57A8", .1, "r")
    + shard("1030,90 1150,70 1190,520 1080,540", "#111", .2, "t") + shard("330,540 640,470 700,980 360,1040", "#2B57A8", .15)
    + ground(.25) + cut("bush.png", 360, 360, 660, .3) + cut("capitol.png", 860, 640, 380, .45) + cut("trump.png", 1190, 150, 880, .4, "slide")
    + text('<div class="serif" style="font-size:190px;color:#2B57A8">2006</div>', 70, 70, .6, "slide")
    + text('<div class="serif" style="font-size:190px;color:#E8551E">2026</div>', 70, 225, .75, "slide")
    + text('<div style="font:900 64px Playfair;line-height:1.02;color:#111"><span class="hl" data-in="sweep" data-at="1.3">Both houses.</span><br>Again.</div>', 78, 410, .95, "slide")
    + text('<div class="marker" style="font-size:46px;background:#EEE7D8;padding:2px 14px;transform:rotate(-7deg)">twenty years apart &rarr;</div>', 880, 560, 1.5, "wipe"))
# 10 the end line
shots["s10_end"] = dict(dur=3.4, push=.03, credit=CAP, body=
    shard("1380,560 1880,500 1900,1080 1420,1080", "#2B57A8", 0, "r") + shard("1500,90 1880,40 1860,420", "#E8551E", .1, "r")
    + cut("capitol.png", 1430, 470, 560, .2)
    + text('<div style="font:900 132px Playfair;line-height:.98;color:#111;width:1250px">Twenty years on, the midterms <span class="hl" data-in="sweep" data-at="1.4">rhymed.</span></div>', 110, 250, .4, "slide")
    + ground(.3, 1000))
for name, s in shots.items():
    (D / "shots" / f"{name}.html").write_text(HEAD.format(dur=s["dur"], push=s["push"], seed=hash(name) % 97) + s["body"]
                                               + TAIL.format(credit=credit(s["credit"]) if s["credit"] else ""), encoding="utf-8")
print(len(shots), "shots")
