"""Paper cut-out props for the evidence desk, drawn in SVG: flat shapes, a white paper edge and a hard shadow.
Nothing here is a real object or a real person; each is a studio drawing in the film's palette."""
import math

from kit import SL, PAPER, CO, AM, RED, INK, CARD, FOLD, DIM

EDGE = 'stroke="#FBFCFE" stroke-width="8" stroke-linejoin="round" paint-order="stroke"'
SHD = "filter:drop-shadow(12px 14px 0 rgba(5,7,12,.42))"


def svg(inner, w, h, extra="", vb=None):
    return f'<svg width="{w}" height="{h}" viewBox="{vb or f"0 0 {w} {h}"}" style="overflow:visible;{SHD};{extra}">{inner}</svg>'


# ---- stationery ---------------------------------------------------------------------------------------------------------------
def pencil(length=520, snapped=False, col=AM):
    """A pencil, top view. snapped = two halves with a splintered break."""
    def half(x0, x1, tip=False, jag=False, rot=0, dy=0):
        body = f'<rect x="{x0}" y="0" width="{x1 - x0}" height="34" fill="{col}" {EDGE}/><rect x="{x0}" y="11" width="{x1 - x0}" height="6" fill="rgba(20,24,36,.18)"/>'
        end = ""
        if tip:
            end = (f'<path d="M{x1} 0 L{x1 + 60} 17 L{x1} 34 Z" fill="#E9D3B8" {EDGE}/><path d="M{x1 + 40} 11 L{x1 + 60} 17 L{x1 + 40} 23 Z" fill="{INK}"/>')
        else:
            end = f'<rect x="{x0 - 44}" y="0" width="44" height="34" fill="{DIM}" {EDGE}/><rect x="{x0 - 70}" y="0" width="30" height="34" rx="8" fill="#E7A9A0" {EDGE}/>'
        j = ""
        if jag:
            jx = x1 if not tip else x0
            j = f'<path d="M{jx} 0 l14 6 l-10 6 l16 5 l-12 7 l12 5 l-20 5 Z" fill="#E9D3B8"/>'
        return f'<g transform="rotate({rot}) translate(0,{dy})">{body}{end}{j}</g>'
    if not snapped:
        return svg(half(70, length - 60, tip=True) + half(70, 71), length + 20, 40)
    mid = length // 2
    return svg(half(70, mid, jag=True, rot=-7) + f'<g transform="translate({mid + 46},-20)">' + half(0, length - mid - 60, tip=True, jag=True, rot=9) + "</g>", length + 60, 140)


def tray(w=1340, h=840):
    """An in-tray seen from above: walls, a ribbed floor, a finger notch in the front wall and a label holder (so it does not read as a screen)."""
    return (f'<div style="width:{w}px;height:{h}px;box-sizing:border-box;border:30px solid #2E3A56;border-bottom-width:48px;background:#1B2334;'
            f'background-image:repeating-linear-gradient(90deg,rgba(240,244,248,.04) 0 2px,transparent 2px 46px);'
            f'box-shadow:inset 20px 24px 0 rgba(0,0,0,.4),16px 20px 0 rgba(5,7,12,.42),0 30px 60px rgba(5,7,12,.5);border-radius:10px;position:relative">'
            f'<div style="position:absolute;left:{w // 2 - 150}px;bottom:-48px;width:240px;height:48px;background:{SL};border-radius:40px 40px 0 0"></div>'
            f'<div style="position:absolute;left:12px;bottom:-41px;background:{CARD};color:{SL};font:500 20px Mono;letter-spacing:5px;padding:3px 14px;border:2px solid {SL}">IN-TRAY</div></div>')


def envelope(w=900, h=560, rot=-3):
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="overflow:visible;transform:rotate({rot}deg);filter:drop-shadow(16px 20px 0 rgba(5,7,12,.42))">'
            f'<rect width="{w}" height="{h}" fill="{CARD}"/><path d="M0 0 L{w / 2} {h * .56} L{w} 0" fill="#F4F7FB" stroke="{FOLD}" stroke-width="4"/>'
            f'<path d="M0 {h} L{w * .36} {h * .42} M{w} {h} L{w * .64} {h * .42}" stroke="{FOLD}" stroke-width="4" fill="none"/>'
            f'<circle cx="{w / 2}" cy="{h * .56}" r="34" fill="{AM}"/><circle cx="{w / 2}" cy="{h * .56}" r="20" fill="none" stroke="{SL}" stroke-width="4"/></svg>')


def magnifier(r=170):
    s = r * 2 + 220
    return (f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" style="overflow:visible;filter:drop-shadow(14px 18px 0 rgba(5,7,12,.45))">'
            f'<rect x="{r * 1.62:.0f}" y="{r * 1.62:.0f}" width="250" height="52" rx="26" fill="#28324A" transform="rotate(45 {r * 1.62:.0f} {r * 1.62 + 26:.0f})"/>'
            f'<circle cx="{r}" cy="{r}" r="{r}" fill="rgba(240,244,248,.10)" stroke="{PAPER}" stroke-width="22"/>'
            f'<path d="M{r * .45:.0f} {r * .7:.0f} A{r * .66:.0f} {r * .66:.0f} 0 0 1 {r * .9:.0f} {r * .36:.0f}" fill="none" stroke="rgba(240,244,248,.5)" stroke-width="10" stroke-linecap="round"/></svg>')


def luggage_tag(text, sub="", w=470, h=210, rot=8):
    return (f'<svg width="{w + 150}" height="{h + 40}" viewBox="0 0 {w + 150} {h + 40}" style="overflow:visible;transform:rotate({rot}deg);filter:drop-shadow(10px 12px 0 rgba(5,7,12,.45))">'
            f'<path d="M-140 -70 C-60 -10 -10 60 62 {h / 2 + 20}" fill="none" stroke="{CO}" stroke-width="7"/>'
            f'<path d="M70 20 L{w + 120} 20 L{w + 120} {h + 20} L70 {h + 20} L20 {h / 2 + 20} Z" fill="{CARD}" stroke="#FBFCFE" stroke-width="6"/>'
            f'<circle cx="62" cy="{h / 2 + 20}" r="15" fill="{SL}" stroke="{DIM}" stroke-width="5"/>'
            f'<text x="110" y="{h / 2 + 12}" font-family="Mono" font-size="50" letter-spacing="5" fill="{INK}">{text}</text>'
            f'<text x="112" y="{h / 2 + 68}" font-family="Mono" font-size="30" letter-spacing="6" fill="{CO}">{sub}</text></svg>')


def folders(n=10, w=900, th=74):
    """A stack of study folders seen edge-on, cobalt spines."""
    out = ""
    for i in range(n):
        x = (i * 37) % 60 - 30
        y = (n - 1 - i) * th
        shade = (CO, "#245C97", "#3279BE")[i % 3]
        out += (f'<rect x="{x + 40}" y="{y}" width="{w}" height="{th - 8}" fill="{shade}" {EDGE}/>'
                f'<rect x="{x + 40}" y="{y + th - 20}" width="{w}" height="12" fill="rgba(5,7,12,.25)"/>'
                f'<rect x="{x + 90 + (i * 131) % 500}" y="{y + 16}" width="220" height="30" fill="{CARD}"/>'
                f'<rect x="{x + 100 + (i * 131) % 500}" y="{y + 27}" width="{120 + (i * 53) % 70}" height="8" fill="{DIM}"/>')
    return svg(out, w + 120, n * th)


def bus(w=1500, h=240, riders=9):
    win = ""
    ww = (w - 120) / riders
    for i in range(riders):
        x = 60 + i * ww
        win += (f'<rect x="{x:.0f}" y="46" width="{ww - 18:.0f}" height="130" rx="12" fill="#0D1019"/>'
                f'<circle cx="{x + ww / 2 - 9:.0f}" cy="108" r="30" fill="{DIM}"/><path d="M{x + ww / 2 - 59:.0f} 176 C{x + ww / 2 - 59:.0f} 146 {x + ww / 2 + 41:.0f} 146 {x + ww / 2 + 41:.0f} 176 Z" fill="{DIM}"/>')
    return svg(f'<rect width="{w}" height="{h}" rx="34" fill="{CO}" {EDGE}/>{win}<rect x="0" y="{h - 40}" width="{w}" height="12" fill="rgba(5,7,12,.3)"/>', w, h)


def bubble(text, w=300, h=150, size=70):
    return svg(f'<path d="M20 0 H{w - 20} a20 20 0 0 1 20 20 V{h - 20} a20 20 0 0 1 -20 20 H110 L60 {h + 50} L70 {h} H20 a20 20 0 0 1 -20 -20 V20 a20 20 0 0 1 20 -20 Z" fill="{PAPER}"/>'
               f'<text x="{w / 2}" y="{h / 2 + size * .35:.0f}" text-anchor="middle" font-family="Black" font-size="{size}" fill="{INK}">{text}</text>', w, h + 50)


# ---- the car clip (a paper diorama; the sign is always the give-way triangle) ---------------------------------------------------
def car(col, w=150, h=290):
    return (f'<g><rect x="0" y="0" width="{w}" height="{h}" rx="38" fill="{col}" {EDGE}/>'
            f'<rect x="18" y="{h * .2:.0f}" width="{w - 36}" height="{h * .17:.0f}" rx="10" fill="rgba(13,16,25,.78)"/>'
            f'<rect x="20" y="{h * .68:.0f}" width="{w - 40}" height="{h * .12:.0f}" rx="8" fill="rgba(13,16,25,.7)"/>'
            f'<rect x="14" y="{h * .4:.0f}" width="{w - 28}" height="{h * .25:.0f}" rx="6" fill="rgba(255,255,255,.16)"/>'
            f'<rect x="-10" y="{h * .14:.0f}" width="12" height="46" rx="5" fill="{INK}"/><rect x="{w - 2}" y="{h * .14:.0f}" width="12" height="46" rx="5" fill="{INK}"/>'
            f'<rect x="-10" y="{h * .7:.0f}" width="12" height="46" rx="5" fill="{INK}"/><rect x="{w - 2}" y="{h * .7:.0f}" width="12" height="46" rx="5" fill="{INK}"/></g>')


def give_way(size=150):
    """The give-way (yield) sign: a red-bordered inverted triangle."""
    s = size
    return (f'<g><path d="M0 0 H{s} L{s / 2} {s * .88} Z" fill="{RED}" stroke="#FBFCFE" stroke-width="8" stroke-linejoin="round" paint-order="stroke"/>'
            f'<path d="M{s * .2} {s * .12} H{s * .8} L{s / 2} {s * .65} Z" fill="#FBFCFE"/></g>')


def stop_sign(size=150):
    s = size; k = s * .293
    pts = f"{k},0 {s - k},0 {s},{k} {s},{s - k} {s - k},{s} {k},{s} 0,{s - k} 0,{k}"
    return (f'<g><polygon points="{pts}" fill="{RED}" stroke="#FBFCFE" stroke-width="8" stroke-linejoin="round" paint-order="stroke"/>'
            f'<text x="{s / 2}" y="{s * .62}" text-anchor="middle" font-family="Black" font-size="{s * .3:.0f}" fill="#FBFCFE">STOP</text></g>')


def road_scene(car_y=560, bump=False, w=1500, h=860, ring_sign=False, drive=None):
    """Top view: a side road (the blue car's) meeting a main road. The give-way triangle stands at the junction, upper right of the side road."""
    road = "#3A4764"
    dash = "".join(f'<rect x="{w * .42 - 5:.0f}" y="{y}" width="10" height="44" fill="rgba(240,244,248,.6)"/>' for y in range(330, h, 96))
    dash2 = "".join(f'<rect x="{x}" y="151" width="60" height="10" fill="rgba(240,244,248,.6)"/>' for x in range(30, w, 130))
    kerb = (f'<path d="M0 262 H{w * .42 - 140:.0f} V{h} M{w * .42 + 140:.0f} {h} V262 H{w}" fill="none" stroke="#FBFCFE" stroke-width="7" stroke-dasharray="26 10"/>'
            f'<path d="M0 50 H{w}" fill="none" stroke="#FBFCFE" stroke-width="7" stroke-dasharray="26 10"/>')
    sign = f'<g transform="translate({w * .42 + 190:.0f},300)"><rect x="66" y="120" width="18" height="120" fill="{DIM}"/>{give_way(150)}</g>'
    bay = (f'<rect x="{w * .42 - 176:.0f}" y="52" width="352" height="158" fill="none" stroke="rgba(240,244,248,.75)" stroke-width="6" stroke-dasharray="20 12"/>'
           f'<text x="{w * .42 + 214:.0f}" y="140" font-family="Black" font-size="64" fill="rgba(240,244,248,.75)">P</text>')
    tree = lambda x, y, r: f'<circle cx="{x}" cy="{y}" r="{r}" fill="#9DB2CA" stroke="#FBFCFE" stroke-width="6"/><circle cx="{x - r * .25:.0f}" cy="{y - r * .2:.0f}" r="{r * .5:.0f}" fill="#B9CBDE"/>'
    scenery = (tree(150, 420, 70) + tree(300, 620, 54) + tree(120, 740, 60) + tree(w - 150, 380, 66) + tree(w - 330, 470, 50)
               + f'<rect x="330" y="330" width="170" height="150" fill="#C9D6E4" stroke="#FBFCFE" stroke-width="6"/><rect x="352" y="352" width="126" height="106" fill="none" stroke="#9DB2CA" stroke-width="5"/>')
    parked = bay + f'<g transform="translate({w * .42 - 75:.0f},-27) rotate(90 75 145)">{car(RED, 150, 290)}</g>'
    blue = f'<g transform="translate({w * .42 - 75:.0f},{car_y})">{car(CO, 150, 290)}</g>'
    if drive:  # (dy, t_start, t_end, t_bump): the car runs up the side road from dy lower, at constant speed, and bumps the parked car
        dy, a0, a1, tb = drive
        blue = f'<g transform="translate({w * .42 - 75:.0f},{car_y})"><g data-anim="move {a0} {a1}" data-dy="{dy}">{car(CO, 150, 290)}</g></g>'
    stars = ""
    if bump:
        cx, cy = w * .42, car_y - 6
        stars = "".join(f'<line x1="{cx + 70 * math.cos(a):.0f}" y1="{cy + 26 * math.sin(a):.0f}" x2="{cx + 150 * math.cos(a):.0f}" y2="{cy + 60 * math.sin(a) - 30:.0f}" stroke="{AM}" stroke-width="9" stroke-linecap="round"/>'
                        for a in (math.radians(d) for d in (200, 225, 250, 290, 315, 340)))
        if drive:
            stars = f'<g data-anim="slam {drive[3]} {drive[3]}">{stars}</g>'
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="display:block">'
            f'<rect width="{w}" height="{h}" fill="{CARD}"/><rect x="0" y="50" width="{w}" height="212" fill="{road}"/>'
            f'<rect x="{w * .42 - 140:.0f}" y="262" width="280" height="{h - 262}" fill="{road}"/>{dash}{dash2}{kerb}{scenery}{sign}{parked}{blue}{stars}</svg>')


# ---- act 1-5 props ---------------------------------------------------------------------------------------------------------------
import json
import random

JACKET = "#28324A"


def camera(w=820):
    h = round(w * .62)
    return svg(f'<rect x="{w * .12:.0f}" y="0" width="{w * .2:.0f}" height="{h * .14:.0f}" fill="{DIM}" {EDGE}/><rect x="{w * .7:.0f}" y="{h * .02:.0f}" width="{w * .12:.0f}" height="{h * .12:.0f}" rx="8" fill="{AM}" {EDGE}/>'
               f'<rect x="0" y="{h * .12:.0f}" width="{w}" height="{h * .88:.0f}" rx="26" fill="{JACKET}" {EDGE}/><rect x="0" y="{h * .12:.0f}" width="{w}" height="{h * .2:.0f}" rx="26" fill="{FOLD}"/>'
               f'<rect x="0" y="{h * .26:.0f}" width="{w}" height="{h * .06:.0f}" fill="{FOLD}"/><rect x="{w * .06:.0f}" y="{h * .17:.0f}" width="{w * .16:.0f}" height="{h * .1:.0f}" rx="6" fill="{INK}"/>'
               f'<circle cx="{w / 2}" cy="{h * .62:.0f}" r="{h * .33:.0f}" fill="{DIM}" stroke="#FBFCFE" stroke-width="8"/><circle cx="{w / 2}" cy="{h * .62:.0f}" r="{h * .25:.0f}" fill="{INK}"/>'
               f'<circle cx="{w / 2}" cy="{h * .62:.0f}" r="{h * .15:.0f}" fill="#0B0D14" stroke="{CO}" stroke-width="10"/><circle cx="{w / 2 - h * .07:.0f}" cy="{h * .55:.0f}" r="{h * .035:.0f}" fill="rgba(240,244,248,.7)"/>'
               f'<text x="{w * .76:.0f}" y="{h * .26:.0f}" font-family="Mono" font-size="{w * .03:.0f}" letter-spacing="4" fill="{INK}">RECORD</text>', w, h)


def manager(sheet_text="MINUTES", desk=False, w=760, h=900, stamp_text=None):
    """The middle manager: a paper cut-out figure with no face. At a podium by default; desk=True seats him behind a big desk."""
    arm = (f'<path d="M455 300 L610 170" fill="none" stroke="#FBFCFE" stroke-width="92" stroke-linecap="round"/><path d="M455 300 L610 170" fill="none" stroke="{JACKET}" stroke-width="76" stroke-linecap="round"/>'
           f'<circle cx="618" cy="160" r="36" fill="{FOLD}" stroke="#FBFCFE" stroke-width="8"/>')
    paper = ""
    if sheet_text:
        paper = (f'<g transform="rotate(9 640 60)"><rect x="560" y="-90" width="230" height="290" fill="{PAPER}" {EDGE}/><text x="675" y="-36" text-anchor="middle" font-family="Black" font-size="34" fill="{INK}">{sheet_text}</text>'
                 + "".join(f'<rect x="586" y="{-6 + i * 30}" width="{178 - (i * 37) % 60}" height="8" fill="{DIM}"/>' for i in range(6)) + (f'<g transform="rotate(-14 675 110)"><rect x="590" y="78" width="170" height="54" fill="none" stroke="{AM}" stroke-width="7"/><text x="675" y="118" text-anchor="middle" font-family="Black" font-size="30" fill="{AM}">{stamp_text}</text></g>' if stamp_text else "") + '</g>')
    body = (f'<path d="M180 330 C180 270 250 250 330 250 C410 250 480 270 480 330 L520 700 L140 700 Z" fill="{JACKET}" {EDGE}/>'
            f'<path d="M280 252 L330 380 L380 252 Z" fill="{PAPER}"/><path d="M316 290 L344 290 L356 430 L330 470 L304 430 Z" fill="{AM}"/>'
            f'<rect x="300" y="200" width="60" height="64" fill="{FOLD}"/><circle cx="330" cy="140" r="82" fill="{FOLD}" stroke="#FBFCFE" stroke-width="8"/>')
    if desk:
        front = (f'<rect x="-40" y="560" width="840" height="60" fill="#3279BE" {EDGE}/><rect x="0" y="620" width="760" height="280" fill="{CO}" {EDGE}/>'
                 f'<rect x="250" y="500" width="260" height="62" fill="{PAPER}" {EDGE}/><text x="380" y="544" text-anchor="middle" font-family="Mono" font-size="30" letter-spacing="4" fill="{INK}">MEMORY</text>'
                 f'<rect x="560" y="430" width="90" height="130" fill="{DIM}" {EDGE}/><path d="M605 430 C560 330 520 300 500 250 M605 430 C610 320 640 290 660 220 M605 430 C660 350 700 340 730 300" fill="none" stroke="#3E8F6B" stroke-width="22" stroke-linecap="round"/>')
    else:
        front = (f'<rect x="60" y="560" width="560" height="340" fill="{CO}" {EDGE}/><rect x="30" y="530" width="620" height="46" fill="#3279BE" {EDGE}/>'
                 f'<rect x="210" y="650" width="260" height="62" fill="{PAPER}"/><text x="340" y="694" text-anchor="middle" font-family="Mono" font-size="28" letter-spacing="3" fill="{INK}">MEMORY DEPT.</text>')
    return svg(arm + paper + body + front, w, h, vb=f"-60 -110 {w + 140} {h + 120}")


def chair(w=300, h=520):
    return svg(f'<rect x="40" y="0" width="200" height="250" rx="18" fill="{DIM}" {EDGE}/><rect x="20" y="250" width="240" height="46" rx="10" fill="{FOLD}" {EDGE}/>'
               f'<rect x="40" y="296" width="18" height="220" fill="{DIM}"/><rect x="222" y="296" width="18" height="220" fill="{DIM}"/>', w, h)


def flashbulb(s=360):
    rays = "".join(f'<line x1="{s / 2 + s * .36 * math.cos(math.radians(d)):.0f}" y1="{s * .38 + s * .36 * math.sin(math.radians(d)):.0f}" x2="{s / 2 + s * .52 * math.cos(math.radians(d)):.0f}" y2="{s * .38 + s * .52 * math.sin(math.radians(d)):.0f}" stroke="{AM}" stroke-width="12" stroke-linecap="round"/>'
                   for d in range(200, 345, 18))
    return svg(f'{rays}<circle cx="{s / 2}" cy="{s * .38:.0f}" r="{s * .3:.0f}" fill="{FOLD}" {EDGE}/><circle cx="{s / 2}" cy="{s * .38:.0f}" r="{s * .2:.0f}" fill="{DIM}"/>'
               f'<circle cx="{s / 2}" cy="{s * .38:.0f}" r="{s * .11:.0f}" fill="#FFFFFF"/><rect x="{s * .42:.0f}" y="{s * .66:.0f}" width="{s * .16:.0f}" height="{s * .34:.0f}" rx="8" fill="{JACKET}" {EDGE}/>', s, s)


def banknote(w=520, h=250, rot=-8):
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="overflow:visible;transform:rotate({rot}deg);filter:drop-shadow(12px 14px 0 rgba(5,7,12,.42))">'
            f'<rect width="{w}" height="{h}" fill="{CARD}" stroke="#FBFCFE" stroke-width="8"/><rect x="18" y="18" width="{w - 36}" height="{h - 36}" fill="none" stroke="{CO}" stroke-width="5"/>'
            f'<ellipse cx="{w / 2}" cy="{h / 2}" rx="{h * .34:.0f}" ry="{h * .36:.0f}" fill="none" stroke="{CO}" stroke-width="6"/><ellipse cx="{w / 2}" cy="{h / 2}" rx="{h * .24:.0f}" ry="{h * .26:.0f}" fill="{CO}" opacity=".25"/>'
            f'<text x="44" y="78" font-family="Black" font-size="54" fill="{CO}">20</text><text x="{w - 44}" y="{h - 36}" text-anchor="end" font-family="Black" font-size="54" fill="{CO}">20</text>'
            f'<text x="{w / 2}" y="{h / 2 + 14}" text-anchor="middle" font-family="Mono" font-size="30" letter-spacing="5" fill="{INK}">BET</text></svg>')


def room(w=860, h=560):
    """A living room, drawn in line: the room you can still see."""
    s = f'fill="none" stroke="{CO}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round" pathLength="1"'
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 860 560" style="display:block;background:{PAPER}">'
            f'<path d="M30 430 H830" {s}/><path d="M90 90 H330 V290 H90 Z M210 90 V290 M90 190 H330" {s}/>'
            f'<path d="M430 320 H760 V430 H430 Z M430 320 C430 250 760 250 760 320 M400 350 H430 V430 H400 Z M760 350 H790 V430 H760 Z" {s}/>'
            f'<path d="M520 110 H700 V230 H520 Z M560 230 L540 270 M660 230 L680 270 M610 110 L580 60 M610 110 L650 50" {s}/>'
            f'<path d="M60 500 H800 M120 470 H740" {s}/><path d="M360 150 L420 120 L420 260 L360 290 Z" {s}/>'
            f'<circle cx="595" cy="305" r="44" fill="{INK}"/><path d="M520 430 C520 366 670 366 670 430 Z" fill="{INK}"/></svg>')


def box(w=760, h=500, label="106 ANSWERS · JAN 1986"):
    return svg(f'<rect x="20" y="90" width="{w - 40}" height="{h - 90}" fill="{CO}" {EDGE}/><rect x="0" y="0" width="{w}" height="130" fill="#3279BE" {EDGE}/>'
               f'<rect x="{w / 2 - 70}" y="46" width="140" height="40" rx="20" fill="{SL}"/><rect x="{w / 2 - 300}" y="220" width="600" height="150" fill="{PAPER}" {EDGE}/>'
               f'<text x="{w / 2}" y="286" text-anchor="middle" font-family="Mono" font-size="30" letter-spacing="2" fill="{INK}">{label}</text>'
               f'<text x="{w / 2}" y="340" text-anchor="middle" font-family="Mono" font-size="24" letter-spacing="5" fill="{CO}">HANDWRITTEN</text>', w, h)


def fingerprint(cx, cy, r=90, col=AM, rot=0):
    arcs = "".join(f'<ellipse cx="{cx}" cy="{cy + i * 3}" rx="{r * k:.0f}" ry="{r * k * 1.25:.0f}" fill="none" stroke="{col}" stroke-width="7" stroke-dasharray="{60 + i * 22} {14 + i * 3}" opacity=".9"/>' for i, k in enumerate((.15, .3, .45, .6, .75, .9)))
    return f'<g transform="rotate({rot} {cx} {cy})">{arcs}</g>'


def evidence_bag(w=620, h=780, prints=()):
    p = "".join(fingerprint(x, y, r, AM, rot) for x, y, r, rot in prints)
    return svg(f'<rect x="0" y="0" width="{w}" height="{h}" rx="18" fill="rgba(240,244,248,.13)" stroke="{PAPER}" stroke-width="8"/><rect x="0" y="0" width="{w}" height="150" rx="18" fill="{PAPER}"/>'
               f'<rect x="0" y="120" width="{w}" height="34" fill="{CO}"/><text x="34" y="78" font-family="Black" font-size="64" fill="{INK}">EVIDENCE</text>'
               f'<text x="36" y="110" font-family="Mono" font-size="20" letter-spacing="4" fill="{CO}">HANDLE AS LITTLE AS POSSIBLE</text>'
               f'<path d="M40 {h - 60} L{w * .3:.0f} {h * .3:.0f}" stroke="rgba(240,244,248,.35)" stroke-width="10" stroke-linecap="round"/>{p}', w, h)


def monitor(w=420):
    return svg(f'<rect x="0" y="0" width="{w}" height="{w * .8:.0f}" rx="24" fill="#D5DCE6" {EDGE}/><rect x="{w * .09:.0f}" y="{w * .08:.0f}" width="{w * .82:.0f}" height="{w * .56:.0f}" rx="18" fill="{INK}"/>'
               f'<rect x="{w * .14:.0f}" y="{w * .14:.0f}" width="{w * .5:.0f}" height="14" fill="{CO}"/><rect x="{w * .14:.0f}" y="{w * .22:.0f}" width="{w * .34:.0f}" height="14" fill="{DIM}"/>'
               f'<circle cx="{w * .86:.0f}" cy="{w * .72:.0f}" r="10" fill="{AM}"/><rect x="{w * .3:.0f}" y="{w * .8:.0f}" width="{w * .4:.0f}" height="{w * .1:.0f}" fill="#B9C4D2" {EDGE}/>'
               f'<rect x="{w * .14:.0f}" y="{w * .9:.0f}" width="{w * .72:.0f}" height="{w * .07:.0f}" rx="8" fill="#D5DCE6" {EDGE}/>', w, round(w * .98))


def phone(w=190):
    return svg(f'<rect x="0" y="0" width="{w}" height="{w * 2.05:.0f}" rx="34" fill="{INK}" {EDGE}/><rect x="12" y="14" width="{w - 24}" height="{w * 2.05 - 28:.0f}" rx="24" fill="{CO}"/>'
               f'<rect x="{w * .32:.0f}" y="24" width="{w * .36:.0f}" height="20" rx="10" fill="{INK}"/><circle cx="{w / 2}" cy="{w * 1.02:.0f}" r="{w * .22:.0f}" fill="rgba(240,244,248,.85)"/>', w, round(w * 2.05))


def boxing_ring(w=1500, h=700):
    posts = "".join(f'<rect x="{x}" y="60" width="44" height="{h - 60}" fill="{DIM}" {EDGE}/>' for x in (0, w - 44))
    ropes = "".join(f'<line x1="22" y1="{y}" x2="{w - 22}" y2="{y}" stroke="{CO}" stroke-width="16"/>' for y in (140, 300, 460))
    return svg(f'<rect x="-30" y="{h - 70}" width="{w + 60}" height="70" fill="{CARD}" {EDGE}/>{posts}{ropes}', w, h)


def floorplan(w=820, h=560):
    """A mall floor plan with a route that wanders off (illustration)."""
    shops = "".join(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="{FOLD}" stroke="{CO}" stroke-width="5"/>' for x, y, ww, hh in
                    ((30, 30, 200, 150), (250, 30, 150, 150), (420, 30, 220, 150), (660, 30, 130, 150), (30, 380, 150, 150), (200, 380, 240, 150), (460, 380, 160, 150), (640, 380, 150, 150)))
    route = f'<path d="M110 290 C200 240 260 330 340 280 S470 230 520 300 S600 350 560 250 S700 220 760 320" fill="none" stroke="{AM}" stroke-width="10" stroke-dasharray="24 16" stroke-linecap="round" pathLength="1"/>'
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 820 560" style="display:block;background:{PAPER}"><rect x="8" y="8" width="804" height="544" fill="none" stroke="{INK}" stroke-width="8"/>{shops}{route}'
            f'<circle cx="110" cy="290" r="16" fill="{AM}"/><text x="30" y="352" font-family="Mono" font-size="22" letter-spacing="3" fill="{INK}">MAIN CONCOURSE</text></svg>')


def slide_mount(n, s=230):
    return svg(f'<rect width="{s}" height="{s}" rx="10" fill="{CARD}" {EDGE}/><rect x="{s * .14:.0f}" y="{s * .2:.0f}" width="{s * .72:.0f}" height="{s * .5:.0f}" fill="{INK}"/>'
               f'<rect x="{s * .2:.0f}" y="{s * .48:.0f}" width="{s * .6:.0f}" height="{s * .16:.0f}" fill="#3A4764"/><rect x="{s * .44:.0f}" y="{s * .36:.0f}" width="{s * .14:.0f}" height="{s * .2:.0f}" rx="6" fill="{CO}"/>'
               f'<text x="{s * .14:.0f}" y="{s * .88:.0f}" font-family="Mono" font-size="{s * .1:.0f}" letter-spacing="3" fill="{INK}">SLIDE {n}</text>', s, s)


def squiggles(lines, w, seed=1, col=INK, lh=58, sw=4):
    """Stand-in handwriting: loops that read as writing but say nothing, so no answer is invented."""
    r = random.Random(seed); out = ""
    for i in range(lines):
        x, y, d = 0.0, i * lh + lh * .6, ""
        lim = w * r.uniform(.55, 1.0)
        while x < lim:
            wl = r.uniform(50, 150); d += f"M{x:.0f} {y:.0f} "
            n = int(wl / 13)
            d += "".join(f"q {6 + r.uniform(-2, 2):.0f} {-r.uniform(10, 26):.0f} 13 0 " if k % 2 == 0 else f"q {6:.0f} {r.uniform(4, 12):.0f} 13 0 " for k in range(n))
            x += wl + r.uniform(18, 34)
        out += f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
    return f'<svg width="{w}" height="{lines * lh}" viewBox="0 0 {w} {lines * lh}" style="display:block">{out}</svg>'


def nc_map(w=1300, h=640):
    """North Carolina and its neighbours from Natural Earth state shapes; a pin on Burlington."""
    S = {s["n"]: s["r"] for s in json.load(open("/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/states.json"))["United States of America"]}
    lo0, lo1, la0, la1 = -85.0, -75.0, 33.4, 37.6
    px = lambda lo, la: ((lo - lo0) / (lo1 - lo0) * w, (la1 - la) / (la1 - la0) * h)
    pth = lambda rings: "".join("M" + " L".join("%.1f %.1f" % px(lo, la) for lo, la in r) + "Z" for r in rings)
    others = "".join(f'<path d="{pth(S[n])}" fill="#232B3E" stroke="#4A5670" stroke-width="2"/>' for n in ("Virginia", "South Carolina", "Tennessee", "Georgia", "Kentucky", "West Virginia") if n in S)
    bx, by = px(-79.4378, 36.0957)
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="display:block;background:#0F1420"><defs><clipPath id="nc"><rect width="{w}" height="{h}"/></clipPath></defs><g clip-path="url(#nc)">{others}'
            f'<path d="{pth(S["North Carolina"])}" fill="{CARD}" stroke="{CO}" stroke-width="5"/>'
            f'<text x="{px(-80.9, 35.42)[0]:.0f}" y="{px(-80.9, 35.42)[1]:.0f}" font-family="Mono" font-size="34" letter-spacing="10" fill="{CO}">NORTH CAROLINA</text>'
            f'<text x="{px(-79.6, 37.2)[0]:.0f}" y="{px(-79.6, 37.2)[1]:.0f}" font-family="Mono" font-size="22" letter-spacing="8" fill="#5D6B86">VIRGINIA</text>'
            f'<text x="{px(-82.2, 34.0)[0]:.0f}" y="{px(-82.2, 34.0)[1]:.0f}" font-family="Mono" font-size="22" letter-spacing="8" fill="#5D6B86">SOUTH CAROLINA</text>'
            f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="34" fill="none" stroke="{AM}" stroke-width="6"/><circle cx="{bx:.0f}" cy="{by:.0f}" r="15" fill="{AM}" stroke="{SL}" stroke-width="5"/></g></svg>'), (bx, by)
