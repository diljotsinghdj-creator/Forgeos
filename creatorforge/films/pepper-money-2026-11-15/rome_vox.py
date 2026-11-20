"""The three Rome visuals in the Vox collage grammar: grid paper + grain, a halftone black-and-white cut-out with a white
sticker edge and offset shadow, one bold colour disc, torn-paper strips, highlighter, marker circle and arrows."""
import math
import random
from frames import page, a, put, chapter, hl, wobble, SIG, RED, INK, PARCH, img

PAPER = ("background:#F4EFE6;background-image:linear-gradient(rgba(60,50,30,.07) 2px,transparent 2px),linear-gradient(90deg,rgba(60,50,30,.07) 2px,transparent 2px);"
         "background-size:60px 60px")
HALFTONE = ('<svg width="0" height="0" style="position:absolute"><defs><pattern id="ht" width="7" height="7" patternUnits="userSpaceOnUse">'
            '<circle cx="3.5" cy="3.5" r="1.4" fill="rgba(0,0,0,.35)"/></pattern>'
            '<filter id="sticker"><feMorphology in="SourceAlpha" operator="dilate" radius="9" result="d"/><feFlood flood-color="#FFFFFF"/>'
            '<feComposite in2="d" operator="in" result="w"/><feMerge><feMergeNode in="w"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs></svg>')


def torn(w, h, col, seed, rot=0, inner=""):
    r = random.Random(seed)
    top = " ".join(f"{x}% {r.uniform(0, 6):.1f}%" for x in range(0, 101, 5))
    bot = " ".join(f"{x}% {100 - r.uniform(0, 6):.1f}%" for x in range(100, -1, -5))
    return (f'<div style="width:{w}px;min-height:{h}px;background:{col};clip-path:polygon({top.replace(" ", ",", 0)},{bot});'
            f'transform:rotate({rot}deg);box-shadow:0 10px 18px rgba(0,0,0,.25);padding:34px 40px;box-sizing:border-box">{inner}</div>')


def poly_torn(w, h, col, seed, rot=0, inner=""):
    r = random.Random(seed)
    pts = [f"{x}% {r.uniform(0, 5):.1f}%" for x in range(0, 101, 4)] + [f"{x}% {100 - r.uniform(0, 5):.1f}%" for x in range(100, -1, -4)]
    return (f'<div style="width:{w}px;min-height:{h}px;background:{col};clip-path:polygon({",".join(pts)});transform:rotate({rot}deg);'
            f'padding:40px 46px;box-sizing:border-box">{inner}</div>')


def sticker_img(src, w, extra=""):
    return (f'<div style="position:relative;filter:drop-shadow(14px 16px 0 rgba(20,20,20,.85))"><img src="/assets/{src}" style="width:{w}px;display:block;'
            f'filter:url(#sticker) grayscale(1) contrast(1.25) brightness(1.05);{extra}"></div>')


def arrow(x1, y1, x2, y2, col=RED, bend=-60, w=6):
    mx, my = (x1 + x2) / 2 + bend * .4, (y1 + y2) / 2 + bend
    ang = math.atan2(y2 - my, x2 - mx); h = 26
    return (f'<path d="M{x1} {y1} Q {mx:.0f} {my:.0f} {x2} {y2}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M{x2 - h * math.cos(ang - .45):.0f} {y2 - h * math.sin(ang - .45):.0f} L{x2} {y2} L{x2 - h * math.cos(ang + .45):.0f} {y2 - h * math.sin(ang + .45):.0f}" '
            f'fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>')


# ---- R1 (Vox): bust sticker on an ochre disc, quote on a torn strip ---------------------------------------------------
quote = (f'<div style="font:500 18px Plex;letter-spacing:4px;color:#7A6A4A">PLINY THE ELDER · NATURAL HISTORY 12.14 · c. 77 CE</div>'
         f'<div style="font:400 58px/1.22 ISerif;color:{INK};margin-top:14px">"…we buy them by weight, {hl("just as if they were so much gold or silver.")}"</div>')
put("r1v", page(
    HALFTONE + a(f'<div style="width:1920px;height:1080px;{PAPER}"></div>', 0, 0)
    + a('<div style="width:620px;height:620px;border-radius:50%;background:#F7D046"></div>', 160, 230)
    + a(f'<div style="width:620px;height:620px;border-radius:50%;background:url(#);background-image:radial-gradient(rgba(0,0,0,.18) 1.6px,transparent 1.8px);background-size:9px 9px"></div>', 160, 230)
    + a(sticker_img("bust.png", 600), 150, 150)
    + chapter(2, "ROME PAYS BY THE POUND")
    + a(poly_torn(900, 300, "#F7F2E6", 11, -1.5, quote), 900, 270)
    + f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{wobble(1440, 470, 250, 52, 3)}" fill="none" stroke="{RED}" stroke-width="6"/>'
      + arrow(1150, 760, 1260, 560, RED, -40) + "</svg>"
    + a(f'<div style="font:700 50px/1.05 Caveat;color:{RED};transform:rotate(-3deg);width:520px">sold like gold. not priced like it.</div>', 960, 760)
    + a(f'<div style="background:{INK};color:#F3EFE6;padding:8px 14px;font:500 16px Plex;letter-spacing:3px;transform:rotate(-2deg)">MARCUS AURELIUS · EMPEROR 161–180 CE</div>', 230, 900)
    + a(f'<div style="font:700 34px Caveat;color:#555;transform:rotate(2deg);width:420px">(no portrait of Pliny survives)</div>', 260, 960),
    "#F4EFE6", "QUOTE: PLINY, NATURAL HISTORY 12.14, TRANSLATION BOSTOCK &amp; RILEY · BUST: PHOTO, PIXABAY (MARCUS AURELIUS), SHOWN IN BLACK AND WHITE · NOTHING DRAWN ON THE FACE"))

# ---- R2 (Vox): the balance as a paper collage, the ratio in giant type -------------------------------------------
coins = "".join(f'<div style="position:absolute;left:{(i % 5) * 34}px;top:{-(i // 5) * 12}px;width:48px;height:18px;border-radius:50%;background:#F2C94C;border:3px solid {INK}"></div>' for i in range(45))
rnd = random.Random(8)
corns = "".join(f'<div style="position:absolute;left:{120 + rnd.gauss(0, 50):.0f}px;top:{-abs(rnd.gauss(0, 26)):.0f}px;width:15px;height:15px;border-radius:50%;background:#231C14"></div>' for _ in range(220))
pan = lambda inner: (f'<div style="position:relative;width:300px;height:60px"><div style="position:absolute;left:0;top:30px;width:300px;height:36px;border-radius:0 0 150px 150px;'
                     f'background:#C9A050;border:5px solid {INK}"></div><div style="position:absolute;left:60px;top:20px">{inner}</div></div>')
put("r2v", page(
    a(f'<div style="width:1920px;height:1080px;{PAPER}"></div>', 0, 0) + chapter(2, "ROME PAYS BY THE POUND")
    + a('<div style="width:1400px;height:14px;background:#141414;border-radius:7px"></div>', 260, 380)
    + a(f'<div style="width:40px;height:470px;background:{INK}"></div>', 940, 380) + a(f'<div style="width:280px;height:30px;background:{INK};border-radius:6px"></div>', 820, 840)
    + a(f'<div style="width:46px;height:46px;border-radius:50%;background:{SIG};border:5px solid {INK}"></div>', 937, 362)
    + "".join(a(f'<div style="width:4px;height:250px;background:{INK};transform:rotate({r}deg);transform-origin:top"></div>', x, 392) for x, r in ((300, 14), (480, -14), (1440, 14), (1620, -14)))
    + a(pan(f'<div style="position:relative;width:180px;height:20px">{coins}</div>'), 240, 620)
    + a(pan(f'<div style="position:relative;width:260px;height:20px;left:-40px">{corns}</div>'), 1380, 620)
    + a(f'<div style="font:400 190px/1 Anton;color:{INK};letter-spacing:-2px">1 : <span style="background:{SIG};padding:0 16px">280</span></div>', 640, 130)
    + a(poly_torn(420, 120, "#F7F2E6", 4, -3, f'<div style="font:400 40px/1 Anton;color:{INK}">1 LB OF GOLD</div><div style="font:500 16px Plex;color:#555;margin-top:6px">45 AUREI ≈ 1,125 DENARII</div>'), 190, 760)
    + a(poly_torn(440, 120, "#F7F2E6", 9, 2, f'<div style="font:400 40px/1 Anton;color:{INK}">280 LB OF PEPPER</div><div style="font:500 16px Plex;color:#555;margin-top:6px">AT 4 DENARII A POUND</div>'), 1320, 760)
    + f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080">{arrow(1300, 300, 1480, 560, RED, -50)}</svg>'
    + a(f'<div style="font:700 50px Caveat;color:{RED};transform:rotate(-4deg)">that much pepper to match it</div>', 1280, 230),
    "#F4EFE6", "BALANCE, COINS AND PEPPERCORNS DRAWN IN THE STUDIO · GOLD: 45 AUREI TO THE POUND AFTER NERO × 25 DENARII, OUR CALCULATION · PEPPER PRICE: PLINY, NATURAL HISTORY 12.14"))

# ---- R3 (Vox): the Forum as a duotone torn photo, the plan as a pinned card ------------------------------------------
rooms = "".join(f'<rect x="{40 + i * 52}" y="40" width="44" height="60" fill="none" stroke="#7A2A20" stroke-width="3"/><rect x="{40 + i * 52}" y="260" width="44" height="60" fill="none" stroke="#7A2A20" stroke-width="3"/>' for i in range(8))
plan = (f'<svg width="500" height="360" viewBox="0 0 500 360"><rect x="20" y="20" width="460" height="320" fill="none" stroke="{INK}" stroke-width="5"/>{rooms}'
        f'<rect x="150" y="130" width="200" height="100" fill="none" stroke="{INK}" stroke-width="2" stroke-dasharray="8 6"/>'
        f'<text x="250" y="187" text-anchor="middle" font-family="Caveat" font-size="30" fill="{INK}">courtyard</text></svg>')
photo = (f'<div style="position:relative;width:1180px;height:760px;overflow:hidden">{img("forum.jpg", 1180, 760, "filter:grayscale(1) contrast(1.35) brightness(1.05)")}'
         f'<div style="position:absolute;inset:0;background:#F7D046;mix-blend-mode:multiply;opacity:.85"></div>'
         f'<div style="position:absolute;inset:0;background-image:radial-gradient(rgba(0,0,0,.25) 1.5px,transparent 1.8px);background-size:8px 8px"></div></div>')
r = random.Random(21)
clip = ",".join([f"{x}% {r.uniform(0, 3):.1f}%" for x in range(0, 101, 3)] + [f"{100 - r.uniform(0, 2):.1f}% {y}%" for y in range(0, 101, 5)]
                + [f"{x}% {100 - r.uniform(0, 3):.1f}%" for x in range(100, -1, -3)] + [f"{r.uniform(0, 2):.1f}% {y}%" for y in range(100, -1, -5)])
put("r3v", page(
    a(f'<div style="width:1920px;height:1080px;{PAPER}"></div>', 0, 0) + chapter(2, "ROME PAYS BY THE POUND")
    + a(f'<div style="clip-path:polygon({clip});transform:rotate(-2deg)">{photo}</div>', 70, 200)
    + a(f'<div style="font:400 84px/0.92 Anton;color:{INK};white-space:nowrap">A WAREHOUSE<br>JUST FOR {hl("PEPPER")}</div>', 1290, 120)
    + a(f'<div style="width:560px;background:#F7F2E6;padding:22px 26px;box-shadow:12px 14px 0 rgba(20,20,20,.85);transform:rotate(3deg)">'
        f'<div style="font:400 42px/1 Anton;color:{INK}">HORREA PIPERATARIA</div>'
        f'<div style="font:500 16px/1.5 Plex;color:#555;margin:6px 0 10px">built under Domitian (81–96 CE) · remains under the Basilica of Maxentius, at the edge of the Forum</div>{plan}'
        f'<div style="font:500 13px Plex;color:#7A6A4A">SKETCH OF A TYPICAL ROMAN WAREHOUSE PLAN · ILLUSTRATIVE</div></div>', 1290, 420)
    + a('<div style="width:26px;height:26px;border-radius:50%;background:#D93829;box-shadow:0 4px 6px rgba(0,0,0,.4)"></div>', 1560, 404)
    + f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080">{arrow(1270, 820, 1000, 900, RED, 40)}</svg>'
    + a(f'<div style="font:700 46px/1.05 Caveat;color:{RED};transform:rotate(-3deg);width:520px">the remains are still here, under the Forum</div>', 760, 930),
    "#F4EFE6", "PHOTO: THE ROMAN FORUM, PIXABAY, SHOWN IN DUOTONE (THE GENERAL AREA, NOT THE EXACT SPOT) · SITE: PLATNER &amp; ASHBY (1929) · PLAN: ILLUSTRATIVE SKETCH"))
print("ok")
