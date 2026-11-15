"""Rome visuals, each at two or three moments of its animation:
  R1 the marble bust (Marcus Aurelius, the age of the Muziris papyrus) with Pliny's words typing beside it
  R2 Roman coins vs pepper on the balance scale: peppercorns pour in until 280 lb balance one pound of gold
  R3 the Horrea Piperataria: a hand-drawn outline over a real photo of the Roman Forum"""
import random
from frames import page, a, put, chapter, hl, SIG, RED, INK, PARCH, DESK, BLK, cut, img

# ---- R1: the bust and Pliny's words -----------------------------------------------------------------------------------
QUOTE = "…we buy them by weight, just as if they were so much gold or silver."
for tag, k in (("a", 30), ("b", len(QUOTE))):
    typed = QUOTE[:k]
    shown = typed.replace("just as if they were so much gold or silver.", hl("just as if they were so much gold or silver.")) if k == len(QUOTE) else typed + '<span style="color:#FFDD33">▍</span>'
    put(f"r1_{tag}", page(
        a('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 30% 45%,#3A2E22 0%,#120E0A 70%)"></div>', 0, 0)
        + a(cut("bust.png", 640 if tag == "a" else 680, "filter:grayscale(.15) contrast(1.05) drop-shadow(0 30px 40px rgba(0,0,0,.7))"), 120 if tag == "a" else 90, 140 if tag == "a" else 110)
        + chapter(2, "ROME PAYS BY THE POUND")
        + a(f'<div style="font:500 20px Plex;letter-spacing:4px;color:{SIG}">PLINY THE ELDER · NATURAL HISTORY 12.14 · c. 77 CE</div>'
            f'<div style="font:400 64px/1.25 ISerif;color:#F3EFE6;margin-top:20px;width:860px">"{shown}"</div>', 920, 300)
        + a(f'<div style="background:{PARCH};padding:8px 14px;font:500 16px Plex;letter-spacing:2px;color:{INK};box-shadow:0 8px 14px rgba(0,0,0,.4)">MARCUS AURELIUS, EMPEROR 161–180 CE · MARBLE BUST</div>', 150, 930)
        + a('<div style="font:700 40px/1.1 Caveat;color:#CFC6B4;width:640px;transform:rotate(-2deg)">Rome in the century of the Muziris papyrus. No portrait of Pliny survives.</div>', 920, 760),
        "#120E0A", "QUOTE: PLINY, NATURAL HISTORY 12.14, TRANSLATION BOSTOCK &amp; RILEY · BUST: PHOTO, PIXABAY (MARCUS AURELIUS, AS TAGGED) · NOTHING DRAWN ON THE FACE", dark=True))

# ---- R2: gold vs pepper on a studio-drawn balance -------------------------------------------------------------------
import math
rnd = random.Random(5)
def balance(tilt, n_corns, falling):
    cx, cy, L, drop = 960, 300, 460, 330
    t = math.radians(tilt)
    lx, ly = cx - L * math.cos(t), cy - L * math.sin(t)
    rx, ry = cx + L * math.cos(t), cy + L * math.sin(t)
    pan = lambda x, y: (f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x - 120:.0f}" y2="{y + drop:.0f}" stroke="#B88A3A" stroke-width="3"/>'
                        f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + 120:.0f}" y2="{y + drop:.0f}" stroke="#B88A3A" stroke-width="3"/>'
                        f'<path d="M{x - 150:.0f} {y + drop:.0f} Q {x:.0f} {y + drop + 70:.0f} {x + 150:.0f} {y + drop:.0f} Z" fill="#C9A050" stroke="#7A5A1E" stroke-width="4"/>')
    gold = "".join(f'<ellipse cx="{lx - 60 + (i % 5) * 30:.0f}" cy="{ly + drop - 8 - (i // 5) * 9:.0f}" rx="16" ry="6" fill="#F2C94C" stroke="#9A7A1E" stroke-width="2"/>' for i in range(45))
    corns = ""
    for i in range(n_corns):
        x = rx + rnd.gauss(0, 46); y = ry + drop - 6 - abs(rnd.gauss(0, 22)) - (rnd.random() * falling)
        r = rnd.uniform(5, 7.5)
        corns += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#2A2018"/><circle cx="{x - r * .3:.0f}" cy="{y - r * .3:.0f}" r="{r * .35:.1f}" fill="#5A4A38"/>'
    stream = f'<path d="M{rx:.0f} 60 L{rx:.0f} {ry + drop - 60:.0f}" stroke="#2A2018" stroke-width="12" stroke-dasharray="5 14" opacity=".75"/>' if falling else ""
    return (f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080">'
            f'<rect x="{cx - 14}" y="{cy}" width="28" height="560" fill="#8A6424"/><path d="M{cx - 180} 880 L{cx + 180} 880 L{cx + 120} 840 L{cx - 120} 840 Z" fill="#7A5A1E"/>'
            f'<line x1="{lx:.0f}" y1="{ly:.0f}" x2="{rx:.0f}" y2="{ry:.0f}" stroke="#C9A050" stroke-width="16" stroke-linecap="round"/><circle cx="{cx}" cy="{cy}" r="22" fill="#E2B85A" stroke="#7A5A1E" stroke-width="4"/>'
            f'{pan(lx, ly)}{pan(rx, ry)}{gold}{corns}{stream}</svg>'), (lx, ly + drop), (rx, ry + drop)
for tag, n, fall, tilt, count in (("a", 0, 0, -12, "0"), ("b", 120, 200, -6, "140"), ("c", 260, 0, 0, "280")):
    svg, (glx, gly), (prx, pry) = balance(tilt, n, fall)
    put(f"r2_{tag}", page(
        a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0) + chapter(2, "ROME PAYS BY THE POUND") + svg
        + a(f'<div style="font:400 46px/1 Anton;color:#F3EFE6;text-align:center;width:420px">45 GOLD AUREI</div><div style="font:500 18px Plex;color:#CFC6B4;text-align:center;width:420px;margin-top:6px">= 1 ROMAN POUND OF GOLD ≈ 1,125 DENARII</div>', glx - 210, gly + 70)
        + a(f'<div style="background:{SIG};color:{INK};padding:8px 16px;font:400 64px/1 Anton;text-align:center">{count} LB</div><div style="font:500 18px Plex;color:#F3EFE6;text-align:center;margin-top:6px">OF BLACK PEPPER, 4 DENARII A POUND</div>', prx - 170, pry + 70)
        + (a(f'<div style="font:700 56px Caveat;color:{SIG};transform:rotate(-3deg)">balanced. sold like gold, not priced like gold.</div>', 520, 120) if tag == "c" else ""),
        "#2A1D12", "BALANCE, COINS AND PEPPERCORNS DRAWN IN THE STUDIO · GOLD: 45 AUREI TO THE POUND AFTER NERO × 25 DENARII, OUR CALCULATION · PEPPER PRICE: PLINY, NATURAL HISTORY 12.14",
        dark=True))

# ---- R3: the pepper warehouses: the Forum photo + a labelled plan sketch ----------------------------------------------
for tag, draw in (("a", 0.0), ("b", 0.6), ("c", 1.0)):
    rooms = "".join(f'<rect x="{40 + i * 52}" y="40" width="44" height="60" fill="none" stroke="#7A2A20" stroke-width="3"/><rect x="{40 + i * 52}" y="260" width="44" height="60" fill="none" stroke="#7A2A20" stroke-width="3"/>' for i in range(8))
    plan = (f'<svg width="500" height="360" viewBox="0 0 500 360"><rect x="20" y="20" width="460" height="320" fill="none" stroke="{INK}" stroke-width="5" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1 - draw:.2f}"/>'
            + (rooms + f'<rect x="150" y="130" width="200" height="100" fill="none" stroke="{INK}" stroke-width="2" stroke-dasharray="8 6"/><text x="250" y="187" text-anchor="middle" font-family="Caveat" font-size="30" fill="{INK}">courtyard</text>' if draw >= .6 else "")
            + "</svg>")
    put(f"r3_{tag}", page(
        a(img("forum.jpg", 1920, 1080, "filter:brightness(.72) saturate(.9)"), 0, 0) + chapter(2, "ROME PAYS BY THE POUND")
        + a(f'<div style="font:400 92px/0.95 Anton;color:#F3EFE6;text-shadow:0 4px 20px rgba(0,0,0,.6)">A WAREHOUSE<br>JUST FOR PEPPER</div>', 80, 130)
        + a(f'<div style="background:{PARCH};padding:20px 24px;box-shadow:0 18px 30px rgba(0,0,0,.55);transform:rotate(-2deg)"><div style="font:400 44px/1 Anton;color:{INK}">HORREA PIPERATARIA</div>'
            f'<div style="font:500 17px/1.5 Plex;color:#555;margin:6px 0 10px">built under Domitian (81–96 CE) · remains under the<br>Basilica of Maxentius, at the edge of the Roman Forum</div>{plan}'
            f'<div style="font:500 14px Plex;color:#7A6A4A">SKETCH OF A TYPICAL ROMAN WAREHOUSE PLAN · ILLUSTRATIVE, NOT THIS BUILDING\'S SURVEY</div></div>', 1250, 300)
        + (a(f'<div style="font:700 48px/1.1 Caveat;color:{SIG};transform:rotate(-2deg);width:560px">"Their remains are still there, under the Forum."</div>', 110, 820) if draw >= 1 else ""),
        "#000", "PHOTO: THE ROMAN FORUM, PIXABAY (THE GENERAL AREA, NOT THE EXACT SPOT) · SITE: PLATNER &amp; ASHBY, TOPOGRAPHICAL DICTIONARY OF ANCIENT ROME (1929) · PLAN: ILLUSTRATIVE SKETCH",
        dark=True))
print("ok")
