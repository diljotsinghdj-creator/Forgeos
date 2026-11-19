"""Key frames (16:9) for "The Buttons That Do Nothing", Dragon Psychology, DJ style (John Oliver script, Vox x Johnny Harris
visuals). Palette: slate #141824, lab-paper #F0F4F8, cobalt #2B6CB0 (structure), amber #ED8936 (the only signal colour). No logo.
Canvas backbone: the K1 control panel (AI plate, finished in the studio); every device, lamp, label, chart and number on it is
drawn here. People are stick figures. Numbers only from dossier.json; items still to check say TO CHECK in the source line.
Helpers are copied (not imported) from the channel's Prophecy film so this film stays self-contained.
Run:  python3 frames.py && python3 shoot_http.py"""
import math
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import studio  # noqa: E402
from studio import A, a, wobble  # noqa: E402

SL, PAPER, CO, AM = "#141824", "#F0F4F8", "#2B6CB0", "#ED8936"
GREY, BODY, DEEP = "#8A94A6", "#3A4456", "#0D1320"
studio.SIG = AM
GRID = (f"background:{PAPER};background-image:linear-gradient(rgba(43,108,176,.10) 1px,transparent 1px),"
        f"linear-gradient(90deg,rgba(43,108,176,.10) 1px,transparent 1px);background-size:40px 40px")
hl = lambda t: f'<span style="background:linear-gradient(transparent 52%,{AM} 52%,{AM} 92%,transparent 92%)">{t}</span>'

AISRC = "AI ILLUSTRATION ({k}): GPT-IMAGE-2.5 VIA ELEVENLABS, OWNER-APPROVED (MASTER_DIRECTIVES 8b/8c), STUDIO FINISH, LOGGED IN DATA/AI_LEDGER.JSON"
PLATES = {"K1": "PANEL", "K2": "OFFICE", "K3": "MIDDLE MANAGER", "K4": "WINDOWSILL"}
DRAWN = "DEVICES, LAMPS, LABELS AND NUMBERS DRAWN IN THE STUDIO"


def page(body, src, bg=SL, dark=True):
    used = [k for k in PLATES if f"/ai/{k}.jpg" in body]
    if used:
        assert "AI ILLUSTRATION" in body, "every AI plate must carry an on-screen AI ILLUSTRATION label"
        src += " · " + AISRC.format(k=", ".join(f"{k} {PLATES[k]}" for k in used))
    return studio.page(body, bg, src, dark=dark, logo=False)


def put(name, html):
    studio.put(name, html)
    NAMES.append(name)


NAMES = []


def LBL(text="AI ILLUSTRATION", x=None, y=None, right=40, bottom=58):
    pos = f"left:{x}px;top:{y}px" if x is not None else f"right:{right}px;bottom:{bottom}px"
    return (f'<div class="a" style="{pos};z-index:85;background:rgba(20,24,36,.86);color:{PAPER};font:500 15px Plex;'
            f'letter-spacing:3px;padding:6px 10px;white-space:nowrap">{text}</div>')


def chapter(n, t):
    return a(f'<div style="background:{PAPER};color:{SL};padding:8px 16px;font:500 20px Plex;letter-spacing:5px;box-shadow:5px 5px 0 rgba(0,0,0,.35)">'
             f'CHAPTER {n} · {t}</div>', 70, 56, "z-index:75")


def tag(text, x, y, rot=-1.5, anim="snap .85 .85", light=False, size=20, amber=False):
    bg, fg = (PAPER, SL) if light else (SL, PAPER)
    if amber:
        bg, fg = AM, SL
    return A(f'<div style="background:{bg};color:{fg};border:2px solid {fg if not amber else SL};padding:8px 14px;font:500 {size}px Plex;'
             f'letter-spacing:4px;transform:rotate({rot}deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">{text}</div>', x, y, anim, "z-index:70")


def card(inner, w, x, y, anim, rot=-1.2, bg="#FFFFFF", extra=""):
    return A(f'<div style="width:{w}px;box-sizing:border-box;background:{bg};padding:26px 30px;box-shadow:0 18px 34px rgba(10,14,24,.45);'
             f'transform:rotate({rot}deg);border-top:8px solid {CO}">{inner}</div>', x, y, anim, "z-index:50;" + extra)


def kicker(t, col=CO):
    return f'<div style="font:500 15px Plex;letter-spacing:3px;color:{col}">{t}</div>'


def study(authors, year, journal, extra="", note=""):
    return (kicker("STUDY CARD")
            + f'<div style="font:400 40px/1.05 Anton;color:{SL};margin-top:8px">{authors} · {year}</div>'
            + f'<div style="font:400 26px ISerif;color:{BODY};margin-top:4px">{journal}</div>'
            + (f'<div style="font:500 17px/1.45 Plex;color:{BODY};margin-top:10px">{extra}</div>' if extra else "")
            + (f'<div style="display:inline-block;margin-top:12px;background:{SL};color:{PAPER};font:500 14px Plex;letter-spacing:2px;padding:4px 8px">{note}</div>' if note else ""))


def doc(kick, body, cite):
    return (kicker(kick) + f'<div style="font:400 34px/1.25 ISerif;color:{SL};margin-top:10px">{body}</div>'
            + f'<div style="font:500 15px/1.4 Plex;letter-spacing:2px;color:{BODY};margin-top:14px">{cite}</div>')


def stamp(text, x, y, anim, rot=-10, size=48, dark=False):
    return A(f'<div style="border:7px solid {AM};color:{AM};font:400 {size}px/1 Anton;letter-spacing:3px;padding:6px 18px;transform:rotate({rot}deg);'
             f'white-space:nowrap;background:{"rgba(20,24,36,.88)" if dark else "rgba(255,255,255,.75)"}">{text}</div>', x, y, anim, "z-index:65")


def head(h, x, y, anim="up .05 .18", size=84, col=PAPER, extra=""):
    return A(f'<div style="font:400 {size}px/0.95 Anton;color:{col};text-shadow:0 3px 18px rgba(0,0,0,.45)">{h}</div>', x, y, anim, "z-index:60;" + extra)


def hand(t, x, y, anim, size=54, col=AM, w=520, rot=-3):
    return A(f'<div style="font:700 {size}px/1.05 Caveat;color:{col};width:{w}px;transform:rotate({rot}deg);text-shadow:0 2px 10px rgba(0,0,0,.5)">{t}</div>', x, y, anim, "z-index:60")


def stick(x, y, s=1.0, col=SL, up=False, extra="", w=4):
    arms = (f'<path d="M-18 -8 L0 4 L18 -8" fill="none" stroke="{col}" stroke-width="{w}"/>' if up
            else f'<path d="M-16 22 L0 4 L16 22" fill="none" stroke="{col}" stroke-width="{w}"/>')
    return (f'<g transform="translate({x},{y}) scale({s})" {extra}><circle cx="0" cy="-22" r="11" fill="none" stroke="{col}" stroke-width="{w}"/>'
            f'<line x1="0" y1="-11" x2="0" y2="30" stroke="{col}" stroke-width="{w}"/>{arms}<path d="M-14 62 L0 30 L14 62" fill="none" stroke="{col}" stroke-width="{w}"/></g>')


def svg(inner, extra="", anim=None):
    da = f' data-anim="{anim}"' if anim else ""
    return f'<svg class="a"{da} style="left:0;top:0;{extra}" width="1920" height="1080">{inner}</svg>'


def bars(vals, maxv, h=420, w=150, gap=80, labels=(), cols=(), anims=(), fmt=str, unit_h=None):
    """Bars from zero on one axis. vals in data units; the top of the axis is maxv."""
    out = f'<div style="position:relative;height:{h + 90}px;width:{len(vals) * (w + gap) + gap}px">'
    out += f'<div style="position:absolute;left:0;right:0;top:{h}px;height:4px;background:{SL}"></div>'
    for i, v in enumerate(vals):
        bh = h * v / maxv; x = gap + i * (w + gap)
        out += (f'<div data-anim="{anims[i] if anims else "grow 0 .3"}" style="position:absolute;left:{x}px;top:{h - bh:.0f}px;width:{w}px;height:{bh:.0f}px;background:{cols[i]}"></div>'
                f'<div data-anim="fade {(anims[i].split()[2] if anims else ".3")} {float(anims[i].split()[2]) + .05 if anims else .35:.2f}" style="position:absolute;left:{x - 40}px;width:{w + 80}px;text-align:center;top:{h - bh - 70:.0f}px;font:400 56px Anton;color:{cols[i] if cols[i] == AM else SL}">{fmt(v)}</div>'
                f'<div style="position:absolute;left:{x - 50}px;width:{w + 100}px;text-align:center;top:{h + 16}px;font:500 17px/1.35 Plex;letter-spacing:2px;color:{SL}">{labels[i] if labels else ""}</div>')
    return out + "</div>"


# ==== THE PANEL (K1) ======================================================================================================
# Socket geometry, measured on K1 (1920x1080).
CW_WIN, CW_BTN = (125, 195, 350, 585), (240, 750)          # crosswalk box: sign window, round button hole
LIFT_X, LIFT_OPEN, LIFT_CLOSE = 597, (597, 430), (597, 620)  # lift panel
SCR = (900, 222, 1228, 425)                                  # small map screen (with a tuning knob over the vent)
KNOB = (1300, 318)
THERMO = (1680, 300)                                         # round thermostat
TOGGLES = [(905, 750), (1045, 750), (1185, 750), (1318, 750)]
BTN = (1680, 760)                                            # the big amber button
LAMPS = [(1557, 672), (1680, 612), (1803, 672)]              # three lamps on the amber arc above it
DEV_BOX = {"crosswalk": (55, 70, 415, 950), "lift": (475, 105, 715, 925), "screen": (775, 140, 1445, 520),
           "thermo": (1490, 90, 1865, 490), "toggles": (780, 588, 1445, 905), "button": (1490, 545, 1865, 945)}

DEFS = (f'<defs><filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="14"/></filter>'
        f'<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000" flood-opacity=".45"/></filter></defs>')


def lamp(x, y, state="off", r=24):
    off = f'<circle cx="{x}" cy="{y}" r="{r + 6}" fill="{DEEP}"/><circle cx="{x}" cy="{y}" r="{r}" fill="#26314A" stroke="{CO}" stroke-width="4"/>'
    on = (f'<circle cx="{x}" cy="{y}" r="{r * 2}" fill="{AM}" opacity=".55" filter="url(#glow)"/>'
          f'<circle cx="{x}" cy="{y}" r="{r}" fill="{AM}" stroke="#FFD2A8" stroke-width="3"/><circle cx="{x - r * .3:.0f}" cy="{y - r * .3:.0f}" r="{r * .3:.0f}" fill="#FFE3C8" opacity=".8"/>')
    if state == "off":
        return off
    if state == "on":
        return off + on
    return off + f'<g data-anim="snap {state} {state}">{on}</g>'   # state = the moment it lights


def big_button(x=BTN[0], y=BTN[1], r=80, glow=True, breathe=None, flare=None):
    g = f'<circle cx="{x}" cy="{y}" r="{r * 1.45:.0f}" fill="{AM}" opacity=".45" filter="url(#glow)"/>' if glow else ""
    if breathe:
        g = f'<g data-anim="fade {breathe}">{g}</g>'
    if flare:
        g += f'<g data-anim="snap {flare} {flare}"><circle cx="{x}" cy="{y}" r="{r * 2:.0f}" fill="{AM}" opacity=".6" filter="url(#glow)"/></g>'
    return (g + f'<circle cx="{x}" cy="{y + 6}" r="{r + 8}" fill="#7A3A0E"/><circle cx="{x}" cy="{y}" r="{r + 8}" fill="#B65A18"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{AM}"/><ellipse cx="{x - r * .28:.0f}" cy="{y - r * .38:.0f}" rx="{r * .42:.0f}" ry="{r * .22:.0f}" fill="#FFE3C8" opacity=".45"/>')


def crosswalk(cover=False, dark=False):
    x0, y0, x1, y1 = CW_WIN; bx, by = CW_BTN
    sign = (f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{PAPER}"/>'
            f'<rect x="{x0 + 10}" y="{y0 + 10}" width="{x1 - x0 - 20}" height="{y1 - y0 - 20}" fill="none" stroke="{SL}" stroke-width="3"/>'
            + "".join(f'<text x="{(x0 + x1) / 2}" y="{y0 + 70 + i * 52}" text-anchor="middle" font-family="Anton" font-size="{44 if i in (1, 4) else 34}" fill="{SL}">{t}</text>'
                      for i, t in enumerate(("PUSH", "BUTTON", "FOR", "WALK", "SIGNAL")))
            + f'<path d="M{bx - 30} {y1 - 62} L{bx + 22} {y1 - 62} M{bx + 6} {y1 - 78} L{bx + 24} {y1 - 62} L{bx + 6} {y1 - 46}" stroke="{SL}" stroke-width="6" fill="none"/>')
    btn = (f'<circle cx="{bx}" cy="{by}" r="86" fill="{DEEP}"/><circle cx="{bx}" cy="{by}" r="74" fill="#A9B4C4"/><circle cx="{bx}" cy="{by}" r="56" fill="#DCE3EC"/>'
           f'<circle cx="{bx}" cy="{by}" r="56" fill="none" stroke="#7D8899" stroke-width="3"/>')
    if dark:
        btn += f'<circle cx="{bx}" cy="{by}" r="56" fill="{DEEP}" opacity=".55"/>'
    return sign + btn


def lift(close_glow=False, smudges=0):
    out = ""
    floors = [(0, 170, "6"), (1, 170, "5"), (0, 240, "4"), (1, 240, "3"), (0, 310, "2"), (1, 310, "1")]
    for c, y, n in floors:
        x = LIFT_X - 38 + c * 76
        out += (f'<circle cx="{x}" cy="{y}" r="25" fill="{DEEP}"/><circle cx="{x}" cy="{y}" r="21" fill="{PAPER}"/>'
                f'<text x="{x}" y="{y + 9}" text-anchor="middle" font-family="Anton" font-size="24" fill="{SL}">{n}</text>')
    for (x, y), kind in ((LIFT_OPEN, "open"), (LIFT_CLOSE, "close")):
        glow = close_glow and kind == "close"
        out += (f'<circle cx="{x}" cy="{y}" r="58" fill="{DEEP}"/>' + (f'<circle cx="{x}" cy="{y}" r="70" fill="{AM}" opacity=".5" filter="url(#glow)"/>' if glow else "")
                + f'<circle cx="{x}" cy="{y}" r="48" fill="{AM if glow else PAPER}" stroke="#7D8899" stroke-width="3"/>')
        if kind == "open":   # <| |>
            out += f'<path d="M{x - 6} {y - 16} L{x - 26} {y} L{x - 6} {y + 16} Z M{x + 6} {y - 16} L{x + 26} {y} L{x + 6} {y + 16} Z" fill="{SL}"/>'
        else:                # |> <|
            out += f'<path d="M{x - 26} {y - 16} L{x - 6} {y} L{x - 26} {y + 16} Z M{x + 26} {y - 16} L{x + 6} {y} L{x + 26} {y + 16} Z" fill="{SL}"/>'
    for i in range(smudges):
        sx, sy = LIFT_CLOSE[0] - 18 + i * 18, LIFT_CLOSE[1] - 10 + (i % 2) * 18
        out += f'<g data-anim="pop {.3 + i * .15:.2f} {.38 + i * .15:.2f}"><ellipse cx="{sx}" cy="{sy}" rx="15" ry="19" fill="{AM}" opacity=".55" transform="rotate({-20 + i * 20} {sx} {sy})"/></g>'
    out += "".join(f'<rect x="{LIFT_X - 40 + c * 52}" y="{y}" width="28" height="28" rx="4" fill="{DEEP}" opacity=".6"/>' for c in range(3) for y in (730, 800))
    return out


def screen(content=""):
    x0, y0, x1, y1 = SCR
    lines = "".join(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{CO}" stroke-width="1" opacity=".35"/>' for y in range(y0 + 20, y1, 20))
    lines += "".join(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="{CO}" stroke-width="1" opacity=".35"/>' for x in range(x0 + 20, x1, 20))
    kx, ky = KNOB
    return (f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#0F1B2E"/>{lines}{content}'
            f'<circle cx="{kx}" cy="{ky}" r="40" fill="{DEEP}"/><circle cx="{kx}" cy="{ky}" r="33" fill="{PAPER}"/><line x1="{kx}" y1="{ky}" x2="{kx + 16}" y2="{ky - 24}" stroke="{SL}" stroke-width="6" stroke-linecap="round"/>')


def thermostat(temp="21°", needle=-20):
    x, y = THERMO
    ticks = "".join(f'<line x1="{x + 70 * math.sin(math.radians(a_)):.1f}" y1="{y - 70 * math.cos(math.radians(a_)):.1f}" x2="{x + 82 * math.sin(math.radians(a_)):.1f}" '
                    f'y2="{y - 82 * math.cos(math.radians(a_)):.1f}" stroke="{SL}" stroke-width="3"/>' for a_ in range(-120, 121, 20))
    return (f'<circle cx="{x}" cy="{y}" r="100" fill="{DEEP}"/><circle cx="{x}" cy="{y}" r="92" fill="{PAPER}"/>{ticks}'
            f'<circle cx="{x}" cy="{y}" r="58" fill="#DCE3EC"/><text x="{x}" y="{y + 16}" text-anchor="middle" font-family="Anton" font-size="46" fill="{SL}">{temp}</text>'
            f'<line x1="{x + 60 * math.sin(math.radians(needle)):.1f}" y1="{y - 60 * math.cos(math.radians(needle)):.1f}" x2="{x + 88 * math.sin(math.radians(needle)):.1f}" '
            f'y2="{y - 88 * math.cos(math.radians(needle)):.1f}" stroke="{CO}" stroke-width="7" stroke-linecap="round"/>')


def toggles(states=(1, 0, 1, 0)):
    out = ""
    for (x, y), s in zip(TOGGLES, states):
        dy = -1 if s else 1
        out += (f'<rect x="{x - 20}" y="{y - 52}" width="40" height="104" rx="6" fill="{DEEP}"/><circle cx="{x}" cy="{y}" r="14" fill="#A9B4C4"/>'
                f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + dy * 46}" stroke="{PAPER}" stroke-width="14" stroke-linecap="round"/>')
    return out


def lamps(states=("off", "off", "off"), r=24):
    return "".join(lamp(x, y, s, r) for (x, y), s in zip(LAMPS, states))


def outline(dev, anim="draw .2 .4", col=CO, w=8):
    x0, y0, x1, y1 = DEV_BOX[dev]
    return f'<g data-anim="{anim}"><rect x="{x0 - 8}" y="{y0 - 8}" width="{x1 - x0 + 16}" height="{y1 - y0 + 16}" rx="18" fill="none" stroke="{col}" stroke-width="{w}" pathLength="1"/></g>'


def devices(lamp_states=("off", "off", "off"), drop=None, extra="", screen_content="", button=True, **kw):
    """All studio devices in K1 coordinates. drop = start time for the staggered 12-frame drop-in, or None."""
    parts = [("crosswalk", crosswalk(kw.get("cover", False), kw.get("cw_dark", False))), ("lift", lift(kw.get("close_glow", False), kw.get("smudges", 0))),
             ("screen", screen(screen_content)), ("thermo", thermostat()), ("toggles", toggles())]
    out = DEFS
    for i, (_, p) in enumerate(parts):
        out += f'<g data-anim="drop {drop + i * .06:.2f} {drop + i * .06 + .08:.2f}">{p}</g>' if drop is not None else p
    if button:
        out += big_button(glow=kw.get("glow", True)) + lamps(lamp_states)
    return out + extra


def rig(inner, html="", s=1.0, cx=960, cy=540, dim=0.0, anim=None, extra=""):
    """The panel (K1 + studio devices) as one rigid piece, framed by a camera at scale s centred on K1 point (cx, cy)."""
    tx, ty = 960 - cx * s, 540 - cy * s
    da = f' data-anim="{anim}"' if anim else ""
    return (f'<div class="a"{da} style="left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;transform:translate({tx:.0f}px,{ty:.0f}px) scale({s});{extra}">'
            f'<img src="/assets/ai/K1.jpg" style="position:absolute;left:0;top:0;width:1920px;height:1080px">'
            f'<svg style="position:absolute;left:0;top:0" width="1920" height="1080">{inner}</svg>{html}'
            + (f'<div style="position:absolute;left:-2000px;top:-2000px;width:6000px;height:6000px;background:rgba(14,18,28,{dim})"></div>' if dim else "")
            + '</div>')


PANEL_LBL = LBL("AI ILLUSTRATION · PANEL")
