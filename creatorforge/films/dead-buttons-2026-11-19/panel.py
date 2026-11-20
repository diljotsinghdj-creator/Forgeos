"""The control panel, built in the studio (owner, 2026-11-19: "more real pictures ... less ai"). It replaces the AI plate K1 as the
canvas of the film. Same socket layout as K1 (so frames.py's device coordinates still fit), drawn in HTML/CSS/SVG on a REAL
brushed-steel surface photo (assets/real/metal_texture.jpg, CC BY 2.0, TextureX.com via Openverse), toned to slate.
Paper-collage finish: white sticker edges on every plate, halftone dots, worn-paint chips, rivets, soft flat shadow.
Run: python3 panel.py  ->  assets/studio/panel.jpg (3840x2160, rendered at 2x so the 2.4x screen zooms stay sharp)."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

D = Path(__file__).resolve().parent
OUT = D / "assets" / "studio"; OUT.mkdir(parents=True, exist_ok=True)
SL, PAPER, CO, AM, DEEP = "#141824", "#F0F4F8", "#2B6CB0", "#ED8936", "#0D1320"
TEX = (D / "assets" / "real" / "metal_texture.jpg").as_uri()


def metal(fill, op=.38, blend="overlay"):
    """A flat paint colour with the real brushed-steel photo laid over it (grain, not gloss)."""
    return (f'<div style="position:absolute;inset:0;background:{fill}"></div>'
            f'<div style="position:absolute;inset:0;background:url({TEX}) center/cover;filter:grayscale(1) contrast(.9);opacity:{op};mix-blend-mode:{blend}"></div>')


def rivet(x, y, r=13):
    return (f'<div style="position:absolute;left:{x - r}px;top:{y - r}px;width:{2 * r}px;height:{2 * r}px;border-radius:50%;'
            f'background:radial-gradient(circle at 35% 32%,#E8EDF3 0 18%,#9AA5B6 34%,#4A5568 70%,#232B3A 100%);'
            f'box-shadow:0 3px 4px rgba(0,0,0,.55)"></div>')


def screw(x, y, r=11):
    return (rivet(x, y, r) + f'<div style="position:absolute;left:{x - r * .7:.0f}px;top:{y - 1.5}px;width:{r * 1.4:.0f}px;height:3px;'
            f'background:#1B2230;transform:rotate(35deg)"></div>')


def hole(cx, cy, r):
    return (f'<div style="position:absolute;left:{cx - r}px;top:{cy - r}px;width:{2 * r}px;height:{2 * r}px;border-radius:50%;'
            f'background:radial-gradient(circle at 50% 40%,#1E2638,{DEEP} 70%);box-shadow:inset 0 10px 18px rgba(0,0,0,.8),0 0 0 6px {PAPER}"></div>')


def rect_hole(x0, y0, x1, y1, rad=6):
    return (f'<div style="position:absolute;left:{x0}px;top:{y0}px;width:{x1 - x0}px;height:{y1 - y0}px;border-radius:{rad}px;'
            f'background:linear-gradient(#0A0F1A,#1E2638);box-shadow:inset 0 10px 18px rgba(0,0,0,.8),0 0 0 6px {PAPER}"></div>')


def plate(x0, y0, x1, y1, inner="", style="", rad=26, corners=True):
    """A plate cut out of paper-backed metal: white sticker edge, soft shadow, halftone, screws in the corners."""
    w, h = x1 - x0, y1 - y0
    sc = "".join(screw(x, y) for x, y in ((34, 34), (w - 34, 34), (34, h - 34), (w - 34, h - 34))) if corners else ""
    return (f'<div style="position:absolute;left:{x0 - 12}px;top:{y0 - 12}px;width:{w + 24}px;height:{h + 24}px;border-radius:{rad + 10}px;'
            f'background:{PAPER};box-shadow:0 14px 22px rgba(0,0,0,.55)"></div>'
            f'<div style="position:absolute;left:{x0}px;top:{y0}px;width:{w}px;height:{h}px;border-radius:{rad}px;overflow:hidden">'
            f'{style}<svg style="position:absolute;inset:0" width="{w}" height="{h}"><filter id="w{x0}{y0}"><feTurbulence type="fractalNoise" baseFrequency=".025 .04" numOctaves="4" seed="{x0 % 97}"/>'
            f'<feColorMatrix values="0 0 0 0 .94  0 0 0 0 .95  0 0 0 0 .97  0 0 0 -26 8.0"/></filter><rect width="{w}" height="{h}" filter="url(#w{x0}{y0})" opacity=".6"/></svg>'
            f'<div style="position:absolute;inset:0;background:radial-gradient(rgba(20,24,36,.28) 1.2px,transparent 1.6px) 0 0/7px 7px;mix-blend-mode:multiply"></div>'
            f'<div style="position:absolute;inset:0;box-shadow:inset 0 0 0 3px rgba(255,255,255,.25),inset 0 -8px 14px rgba(0,0,0,.25);border-radius:{rad}px"></div>'
            f'{sc}<div style="position:absolute;left:{-x0}px;top:{-y0}px;width:1920px;height:1080px">{inner}</div></div>')


def arc(cx, cy, r, a0, a1, col, w=34):
    import math
    p = lambda a: (cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a)))
    (x0, y0), (x1, y1) = p(a0), p(a1)
    ticks = "".join(f'<line x1="{cx + (r - w / 2) * math.sin(math.radians(a)):.1f}" y1="{cy - (r - w / 2) * math.cos(math.radians(a)):.1f}" '
                    f'x2="{cx + (r + w / 2) * math.sin(math.radians(a)):.1f}" y2="{cy - (r + w / 2) * math.cos(math.radians(a)):.1f}" stroke="{PAPER}" stroke-width="4"/>'
                    for a in range(a0 + 20, a1, 20))
    return (f'<path d="M{x0:.1f} {y0:.1f} A{r} {r} 0 {1 if a1 - a0 > 180 else 0} 1 {x1:.1f} {y1:.1f}" stroke="{col}" stroke-width="{w}" fill="none" opacity=".92"/>{ticks}')


def build():
    grey = metal("#9AA4B4", .45)
    light = metal("#D5DBE4", .4)
    blue = metal(CO, .45)
    chips = ('<svg style="position:absolute;inset:0" width="1920" height="1080"><filter id="chip"><feTurbulence type="fractalNoise" baseFrequency=".02 .03" numOctaves="4" seed="7"/>'
             '<feColorMatrix values="0 0 0 0 .94  0 0 0 0 .95  0 0 0 0 .97  0 0 0 -24 7.6"/></filter>'
             '<rect width="1920" height="1080" filter="url(#chip)" opacity=".55"/></svg>')
    bluechips = chips.replace('id="chip"', 'id="chip2"').replace("url(#chip)", "url(#chip2)").replace('seed="7"', 'seed="3"').replace("-24 7.6", "-22 7.0")
    svg = lambda s: f'<svg style="position:absolute;left:0;top:0" width="1920" height="1080">{s}</svg>'
    body = (
        # the base sheet: real brushed steel, toned slate, with worn cobalt and paper chips
        metal("#2A3246", .5) +
        f'<div style="position:absolute;inset:0;opacity:.55">{bluechips.replace(".94  0 0 0 0 .95  0 0 0 0 .97", ".17  0 0 0 0 .42  0 0 0 0 .69")}</div>'
        f'<div style="position:absolute;inset:0;opacity:.45">{chips}</div>'
        f'<div style="position:absolute;inset:0;background:radial-gradient(rgba(0,0,0,.35) 1.3px,transparent 1.7px) 0 0/8px 8px;mix-blend-mode:multiply"></div>'
        + "".join(rivet(x, y, 17) for x in (50, 670, 1350, 1870) for y in (35, 1025))
        + "".join(rivet(x, y, 17) for x in (25, 1895) for y in (300, 760))
        # crosswalk box (blue paint over metal), sign window and button hole with amber ring
        + plate(55, 70, 415, 950, rect_hole(125, 195, 350, 585) + svg(f'<circle cx="240" cy="750" r="108" fill="none" stroke="{AM}" stroke-width="20"/>')
                + hole(240, 750, 88) + "".join(hole(x, 750, 12) for x in (118, 362)), blue, 34)
        # lift strip
        + plate(475, 105, 715, 925, hole(597, 430, 58) + hole(597, 620, 58), grey, 24)
        # screen housing, with a vent
        + plate(775, 140, 1445, 520, rect_hole(900, 222, 1228, 425, 4)
                + "".join(f'<div style="position:absolute;left:1262px;top:{y}px;width:76px;height:9px;border-radius:4px;background:#1E2638"></div>' for y in range(240, 405, 18)), light, 30)
        # thermostat plate with a cobalt arc
        + plate(1490, 90, 1865, 490, svg(arc(1680, 300, 135, -125, 125, CO)) + hole(1680, 300, 104), grey, 26)
        # toggle plate
        + plate(780, 588, 1445, 905, "".join(rect_hole(x - 30, 680, x + 30, 820, 6) for x, _ in ((905, 0), (1045, 0), (1185, 0), (1318, 0)))
                + "".join(screw(x, y, 9) for x in (905, 1045, 1185, 1318) for y in (660, 840)), grey, 22)
        # button plate with an amber arc
        + plate(1490, 545, 1865, 945, svg(arc(1680, 760, 135, -125, 125, AM)) + hole(1680, 760, 100), grey, 26)
    )
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{SL};position:relative}}</style></head>'
            f'<body>{body}<svg style="position:absolute;inset:0;pointer-events:none;opacity:.22;mix-blend-mode:multiply" width="1920" height="1080"><filter id="g">'
            f'<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3"/><feColorMatrix values="0 0 0 0 .3 0 0 0 0 .3 0 0 0 0 .35 0 0 0 .6 0"/></filter>'
            f'<rect width="1920" height="1080" filter="url(#g)"/></svg></body></html>')
    src = OUT / "panel.html"; src.write_text(html, encoding="utf-8")
    exe = "/opt/pw-browsers/chromium"
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe, args=["--no-sandbox", "--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        pg.goto(src.as_uri()); pg.wait_for_timeout(800)
        pg.screenshot(path=str(OUT / "panel.jpg"), type="jpeg", quality=90); b.close()
    print("panel", OUT / "panel.jpg")


if __name__ == "__main__":
    build()
