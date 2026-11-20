"""Key frames (16:9) for "The Buttons That Do Nothing", Dragon Psychology, DJ style (John Oliver script, Vox x Johnny Harris
visuals). Palette: slate #141824, lab-paper #F0F4F8, cobalt #2B6CB0 (structure), amber #ED8936 (the only signal colour). No logo.
Canvas backbone: the control panel, built in the studio by panel.py on a REAL brushed-steel photo (it replaced the AI plate K1,
owner 2026-11-19: "more real pictures ... less ai"); every device, lamp, label, chart and number on it is drawn here, and real
photos sit in its sockets and on its cards. The only AI plate left is K3 (a metaphor). People are stick figures. Numbers only from dossier.json; items still to check say TO CHECK in the source line.
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
PLATES = {"K3": "MIDDLE MANAGER"}   # K1, K2 and K4 retired 2026-11-19 (see data/ai_ledger.json)
PANEL_SRC = "PANEL: DRAWN IN THE STUDIO ON A REAL BRUSHED-STEEL PHOTO (TEXTUREX.COM, CC BY 2.0, VIA OPENVERSE)"
DRAWN = "DEVICES, LAMPS, LABELS AND NUMBERS DRAWN IN THE STUDIO"


def page(body, src, bg=SL, dark=True):
    used = [k for k in PLATES if f"/ai/{k}.jpg" in body]
    if used:
        assert "AI ILLUSTRATION" in body, "every AI plate must carry an on-screen AI ILLUSTRATION label"
        src += " · " + AISRC.format(k=", ".join(f"{k} {PLATES[k]}" for k in used))
    assert "/ai/K1" not in body and "/ai/K2" not in body and "/ai/K4" not in body, "retired AI plate used"
    if "studio/panel.jpg" in body:
        src += " · " + PANEL_SRC
    return studio.page(body, bg, src, dark=dark, logo=False)


def put(name, html):
    studio.put(name, html)
    NAMES.append(name)


NAMES = []


def LBL(text="AI ILLUSTRATION", x=None, y=None, right=40, bottom=84):
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
    floors = [(0, 215, "6"), (1, 215, "5"), (0, 272, "4"), (1, 272, "3"), (0, 329, "2"), (1, 329, "1")]
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


def rig(inner, html="", s=1.0, cx=960, cy=540, dim=0.0, anim=None, extra="", push=.04):
    """The studio panel + devices as one rigid piece, framed by a camera at scale s centred on panel point (cx, cy).
    push = a slow camera push-in over the shot (camera feel), 0 for a locked-off shot."""
    tx, ty = 960 - cx * s, 540 - cy * s
    da = f' data-anim="{anim}"' if anim else ""
    cam = f'<div class="a" data-anim="push 0 1" data-k="{push}" style="left:0;top:0;width:1920px;height:1080px">' if push else ""
    return cam + (f'<div class="a"{da} style="left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;transform:translate({tx:.0f}px,{ty:.0f}px) scale({s});{extra}">'
            f'<img src="/assets/studio/panel.jpg" style="position:absolute;left:0;top:0;width:1920px;height:1080px">'
            f'<svg style="position:absolute;left:0;top:0" width="1920" height="1080">{inner}</svg>{html}'
            + (f'<div style="position:absolute;left:-2000px;top:-2000px;width:6000px;height:6000px;background:rgba(14,18,28,{dim})"></div>' if dim else "")
            + '</div>') + ("</div>" if push else "")


PANEL_LBL = ""   # the panel is studio-drawn now: no AI label; its texture photo is credited in the source line

# ==== REAL PHOTOS AND REAL MAPS =============================================================================================
import json as _json  # noqa: E402
import random  # noqa: E402

CRED = {c["slug"]: c for c in _json.loads((D / "data" / "photo_credits.json").read_text(encoding="utf-8"))}


def pcred(slug):
    c = CRED[slug]
    t = c["title"] if len(c["title"]) < 58 else c["title"][:55] + "…"
    return f'PHOTO: "{t.upper()}" BY {c["author"].upper()}, {c["licence"]}, VIA OPENVERSE ({c["finish"].upper()})'


def photo(slug, w, h, x, y, anim, rot=0, pos="50% 50%", cap=True, extra="", zoom=1.0, drift=None, tape=True):
    """A real photo print, taped down (investigator layer). drift = (dx, dy): cut-out parallax over the shot."""
    c = CRED[slug]
    capt = (f'<div style="font:500 13px/1.35 Plex;letter-spacing:2px;color:{SL};margin-top:8px;width:{w}px">{c["on_screen_caption"]}<br>'
            f'<span style="color:{BODY}">PHOTO: {c["author"].upper()} · {c["licence"]}</span></div>') if cap else ""
    tp = (f'<div style="position:absolute;left:{w / 2 - 60:.0f}px;top:-18px;width:130px;height:36px;background:rgba(236,232,220,.82);'
          f'transform:rotate({-rot * 2 - 3:.1f}deg);box-shadow:0 2px 4px rgba(0,0,0,.25)"></div>') if tape else ""
    out = A(f'<div style="position:relative;background:#fff;padding:12px 12px 14px;box-shadow:0 22px 40px rgba(0,0,0,.5);transform:rotate({rot}deg)">{tp}'
             f'<div style="width:{w}px;height:{h}px;overflow:hidden"><img src="/assets/real/{slug}.jpg" style="width:100%;height:100%;object-fit:cover;object-position:{pos};'
             f'transform:scale({zoom});transform-origin:{pos};display:block"></div>{capt}</div>', x, y, anim, "z-index:45;" + extra)
    if drift:
        out = f'<div class="a" data-anim="drift 0 1" data-dx="{drift[0]}" data-dy="{drift[1]}" style="left:0;top:0;z-index:45">{out}</div>'
    return out


def ring(cx, cy, rx, ry, anim, seed=3, w=8):
    """Investigator layer: a hand-drawn amber circle (frame coords)."""
    return svg(f'<g data-anim="{anim}"><path d="{wobble(cx, cy, rx, ry, seed)}" fill="none" stroke="{AM}" stroke-width="{w}" stroke-linecap="round" pathLength="1"/></g>', "z-index:72")


def arrow(x0, y0, x1, y1, anim, bend=40, w=8):
    """Investigator layer: a hand-drawn amber arrow from (x0, y0) to (x1, y1)."""
    mx, my = (x0 + x1) / 2 - bend * (y1 - y0) / max(1, math.hypot(x1 - x0, y1 - y0)), (y0 + y1) / 2 + bend * (x1 - x0) / max(1, math.hypot(x1 - x0, y1 - y0))
    ang = math.atan2(y1 - my, x1 - mx)
    hx = lambda da: (x1 - 34 * math.cos(ang + da), y1 - 34 * math.sin(ang + da))
    (ax, ay), (bx_, by_) = hx(.5), hx(-.5)
    return svg(f'<g data-anim="{anim}"><path d="M{x0:.0f} {y0:.0f} Q{mx:.0f} {my:.0f} {x1:.0f} {y1:.0f}" fill="none" stroke="{AM}" stroke-width="{w}" stroke-linecap="round" pathLength="1"/>'
               f'<path d="M{ax:.0f} {ay:.0f} L{x1:.0f} {y1:.0f} L{bx_:.0f} {by_:.0f}" fill="none" stroke="{AM}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></g>', "z-index:72")


def plate_print(k, w, x, y, anim, rot=-1.5, label="AI ILLUSTRATION", extra=""):
    h = round(w * 9 / 16)
    return A(f'<div style="position:relative;background:#fff;padding:12px;box-shadow:0 22px 40px rgba(0,0,0,.5);transform:rotate({rot}deg)">'
             f'<img src="/assets/ai/{k}.jpg" style="width:{w}px;height:{h}px;display:block">'
             f'<div style="position:absolute;left:24px;bottom:24px;background:rgba(20,24,36,.86);color:{PAPER};font:500 14px Plex;letter-spacing:3px;padding:5px 9px">{label}</div></div>',
             x, y, anim, "z-index:44;" + extra)


_NYC = _json.loads((D / "maps" / "midtown.geojson").read_text(encoding="utf-8"))["features"]
LON0, LON1, LAT0, LAT1 = -73.996, -73.968, 40.7506, 40.7638
NYC_SRC = "MAP: NYC STREET CENTERLINE (CSCL), NYC OPEN DATA, MIDTOWN MANHATTAN"


def nyc_xy(lon, lat, W=1640, H=1015):
    return (lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H


def nyc_streets(col="#4F8FD6", w=7, op=.95):
    d = []
    for f in _NYC:
        for line in f["geometry"]["coordinates"]:
            d.append("M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in (nyc_xy(*p) for p in line)))
    return f'<path d="{" ".join(d)}" fill="none" stroke="{col}" stroke-width="{w}" opacity="{op}" stroke-linecap="round"/>'


def nyc_nodes():
    import collections
    c = collections.Counter()
    for f in _NYC:
        for line in f["geometry"]["coordinates"]:
            for p in (line[0], line[-1]):
                c[(round(p[0], 4), round(p[1], 4))] += 1
    pts = [nyc_xy(*k) for k, v in c.items() if v >= 3]
    return sorted([p for p in pts if 10 < p[0] < 1630 and 10 < p[1] < 1005], key=lambda p: (p[0] + p[1]))


NODES = nyc_nodes()


def nyc_dots(live_share, dead_col=GREY, live_col=AM, appear="fill .05 .3", turn="fill .45 .7", r=12, seed=4):
    """Every intersection gets a dot; a share turns 'dead'. ILLUSTRATIVE pattern: the real share, not the real locations."""
    rnd = random.Random(seed); live = set(rnd.sample(range(len(NODES)), round(len(NODES) * live_share)))
    allg = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{live_col}"/>' for x, y in NODES)
    dead = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r + 1}" fill="{dead_col}"/>' for i, (x, y) in enumerate(NODES) if i not in live)
    return f'<g data-anim="{appear}">{allg}</g><g data-anim="{turn}">{dead}</g>'


def screen_svg(inner, bg="#0F1B2E"):
    x0, y0, x1, y1 = SCR
    return (f'<svg x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" viewBox="0 0 1640 1015" preserveAspectRatio="xMidYMid slice">'
            f'<rect width="1640" height="1015" fill="{bg}"/>{inner}</svg>')


_NE = _json.loads((D / "maps" / "ne_50m_admin_0_countries.geojson").read_text(encoding="utf-8"))["features"]
NE_SRC = "MAP: NATURAL EARTH 1:50M (PUBLIC DOMAIN)"


def locator(bbox, focus, pin, pin_label, W=1640, H=1015):
    lon0, lon1, lat0, lat1 = bbox
    k = math.cos(math.radians((lat0 + lat1) / 2))
    sx = W / ((lon1 - lon0) * k); sy = H / (lat1 - lat0); s = min(sx, sy)
    ox = (W - (lon1 - lon0) * k * s) / 2; oy = (H - (lat1 - lat0) * s) / 2
    P = lambda lon, lat: (ox + (lon - lon0) * k * s, oy + (lat1 - lat) * s)
    out = ""
    for f in _NE:
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        d = ""
        for poly in polys:
            ring = poly[0]
            if not any(lon0 - 5 < p[0] < lon1 + 5 and lat0 - 5 < p[1] < lat1 + 5 for p in ring):
                continue
            d += "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in (P(*p) for p in ring)) + "Z"
        if d:
            hit = f["properties"]["ADMIN"] == focus
            out += f'<path d="{d}" fill="{CO if hit else "#24314A"}" stroke="{PAPER if hit else "#3A4A66"}" stroke-width="{4 if hit else 2}" opacity="{1 if hit else .9}"/>'
    px, py = P(*pin)
    out += (f'<g data-anim="pop .3 .4"><circle cx="{px:.0f}" cy="{py:.0f}" r="60" fill="{AM}" opacity=".35"/><circle cx="{px:.0f}" cy="{py:.0f}" r="26" fill="{AM}" stroke="{PAPER}" stroke-width="6"/></g>'
            f'<text x="{px + 50:.0f}" y="{py + 22:.0f}" font-family="Anton" font-size="86" fill="{PAPER}" data-anim="fade .4 .5">{pin_label}</text>')
    return out


def screen_rig(content, dim=0.35, s=2.4, fx=560, extra_svg="", html=""):
    cx = 1064 + (960 - fx) / s
    return rig(devices(screen_content=screen_svg(content), button=True, lamp_states=("on", "on", "on")) + extra_svg, html, s=s, cx=cx, cy=323, dim=dim)


def scr_label(t, fx=560):   # label under the zoomed screen (frame coords)
    return A(f'<div style="background:{SL};color:{PAPER};font:500 16px Plex;letter-spacing:3px;padding:5px 10px;white-space:nowrap">{t}</div>', fx - 380, 800, "fade .1 .2", "z-index:60")


# ==== 1 HOOK: THE TRAP =====================================================================================================
BACKDROP = a(f'<div style="width:1920px;height:1080px;background:{SL};overflow:hidden"><img src="/assets/studio/panel.jpg" style="width:5760px;height:3240px;margin:-1700px 0 0 -1500px;filter:blur(6px) brightness(.38);opacity:.9"></div>', 0, 0)


def trap(lamp_states, html="", glow=True, extra_svg="", breathe=None, flare=None):
    inner = DEFS + big_button(glow=glow, breathe=breathe, flare=flare) + lamps(lamp_states) + extra_svg
    return BACKDROP + rig(inner, html, s=2.0, cx=1680, cy=740, extra="clip-path:inset(545px 55px 135px 1490px round 26px)")


TRAP_SRC = "THE VIEWER TRAP ([SIMULATE]): THE LAMPS RUN ON A TIMER KEYED TO THE NARRATION, NOT TO THE VIEWER · BUTTON AND LAMPS DRAWN IN THE STUDIO"
TRAP_LBL = ""

put("01_press", page(
    trap((.82, "off", "off"), breathe=".0 .5")
    + A(f'<div style="font:400 92px/0.95 Anton;color:{PAPER}">PRESS IT.</div><div style="font:400 64px/1.1 ISerif;color:#C9D3E0;margin-top:10px">In your head.</div>', 110, 330, "up .08 .2", "z-index:60")
    + tag("YOUR BUTTON · PRESS WHEN READY", 640, 970, 0, "up .2 .3", light=True)
    + A(f'<div style="font:500 24px/1.6 Plex;letter-spacing:3px;color:{PAPER};width:460px">[WAIT 3.5 S]<br><span style="color:{AM}">LAMP 1 → +3.5 S</span></div>', 1420, 420, "fade .3 .4", "z-index:60")
    + tag("INPUT RECEIVED", 1420, 560, 2, "snap .86 .86", amber=True) + TRAP_LBL,
    TRAP_SRC))

put("02_again", page(
    trap(("on", .78, "off"))
    + A(f'<div style="font:400 64px/1.1 ISerif;color:#C9D3E0">"Again.<br>Take your time.<br><span style="color:{PAPER}">Whenever you like.</span>"</div>', 110, 330, "fade .05 .2", "z-index:60")
    + A(f'<div style="font:500 24px/1.6 Plex;letter-spacing:3px;color:{PAPER};width:460px">[WAIT 4.0 S]<br><span style="color:{AM}">LAMP 2 → +4.0 S</span></div>', 1420, 420, "fade .3 .4", "z-index:60")
    + hand("Lovely. Very responsive, this button.", 1400, 560, "fade .85 .92", 46, AM, 440, 2) + TRAP_LBL,
    TRAP_SRC))

put("03_now", page(
    trap(("on", "on", .62), flare=".5")
    + A(f'<div style="font:400 64px/1.1 ISerif;color:#C9D3E0">"One last time.<br>Press it…</div>', 110, 330, "fade .05 .2", "z-index:60")
    + A(f'<div style="font:400 150px/1 Anton;color:{AM}">NOW.</div>', 110, 520, "slam .5 .52", "z-index:60")
    + A(f'<div style="font:500 24px/1.6 Plex;letter-spacing:3px;color:{PAPER};width:460px">[WAIT 1.2 S]<br><span style="color:{AM}">LAMP 3 → JUST AFTER "NOW"</span></div>', 1420, 420, "fade .3 .4", "z-index:60")
    + tag("EXHIBIT A · YOUR FEELING", 1420, 580, -3, "snap .85 .85", amber=True) + TRAP_LBL,
    TRAP_SRC))

# pull-out: the button is one control on a big panel
qmarks = [(235, 70, 235, 0), (597, 105, 597, 0), (1110, 140, 1110, 0), (1680, 90, 1680, 0)]
wires = "".join(f'<path d="M{x0} {y0} L{x1} {y1 + (30 if y1 == 0 else -30)}" stroke="{CO}" stroke-width="7" stroke-dasharray="14 10" fill="none"/>'
                f'<text x="{x1 + 14}" y="{(y1 + 72) if y1 == 0 else (y1 - 40)}" font-family="Anton" font-size="56" fill="{AM}">?</text>' for x0, y0, x1, y1 in qmarks)
put("04_panel", page(
    '<div class="a" data-anim="zoom 0 .3" data-from="2" data-o="2400px 980px" style="left:0;top:0;width:1920px;height:1080px">'
    + rig(devices(("on", "on", "on"), drop=.3, screen_content=screen_svg(nyc_streets(op=.85))) + "".join(outline(d, f"draw {.62 + i * .04:.2f} {.7 + i * .04:.2f}") for i, d in enumerate(("crosswalk", "lift", "thermo")))
        + f'<g data-anim="fade .8 .88">{wires}</g>', anim=None, push=0) + '</div>'
    + tag("CROSSWALK", 80, 960, 0, "snap .64 .64", light=True) + tag("LIFT", 500, 960, 0, "snap .68 .68", light=True)
    + tag("THERMOSTAT", 1530, 40, 0, "snap .72 .72", light=True) + tag("YOUR BUTTON", 1590, 505, 0, "snap .3 .3", amber=True)
    + tag("SCREEN: REAL MIDTOWN STREETS", 880, 50, 0, "snap .5 .5", light=True, size=16)
    + A(f'<div style="background:{SL};border:3px solid {AM};padding:14px 22px;font:700 46px/1.1 Caveat;color:{AM};width:600px;box-shadow:0 14px 30px rgba(0,0,0,.5)">So how many of them are actually wired to anything?</div>', 790, 450, "up .82 .9", "z-index:66") + PANEL_LBL,
    "PANEL WITH " + DRAWN + " · THE DEVICES STAND FOR REAL ONES SHOWN LATER IN REAL PHOTOS · SCREEN: " + NYC_SRC))

put("05_title", page(
    rig(devices(("on", "on", "on"), screen_content=screen_svg(nyc_streets(op=.85))), dim=.72, push=.06)
    + A(f'<div style="width:1260px;height:420px;background:{PAPER};border:6px solid {SL};box-shadow:0 30px 60px rgba(0,0,0,.6);outline:3px solid {PAPER};outline-offset:10px"></div>', 330, 250, "pop .05 .15", "z-index:58")
    + A(f'<div style="font:400 150px/0.9 Anton;color:{SL};letter-spacing:2px;width:1260px;text-align:center">THE BUTTONS</div>', 333, 300, "slam .18 .2", "z-index:60")
    + A(f'<div style="font:400 150px/0.9 Anton;color:{SL};letter-spacing:2px;width:700px;text-align:right">THAT DO</div>', 290, 445, "slam .3 .32", "z-index:60")
    + A(f'<div style="font:400 150px/0.9 Anton;color:{AM};letter-spacing:2px">NOTHING</div>', 1020, 445, "slam .45 .47", "z-index:60")
    + A(f'<div style="width:520px;height:16px;background:{AM}"></div>', 1025, 590, "wipe .55 .7", "z-index:59")
    + A(f'<div style="font:500 20px Plex;letter-spacing:6px;color:{PAPER};text-align:center;width:1920px">DRAGON PSYCHOLOGY · WE CHECK THE SCIENCE</div>', 0, 880, "fade .4 .5", "z-index:60") + PANEL_LBL,
    "TITLE PLATE SET IN THE STUDIO (KINETIC TYPE, WORD BY WORD) · SCREEN: " + NYC_SRC))

# ==== 2 MAP AND HISTORY ====================================================================================================
put("06_crosswalk", page(
    rig(devices(("on", "on", "on")), s=1.25, cx=744, cy=510, dim=.3)
    + chapter(2, "WHERE THE DEAD BUTTONS ARE")
    + photo("nyc_wait_sign", 360, 470, 700, 150, "up .05 .18", -3, "50% 45%", drift=(-26, -8))
    + photo("push_sign", 440, 470, 1170, 170, "up .14 .26", 2.5, "33% 40%", drift=(30, 6))
    + ring(1322, 300, 95, 115, "draw .3 .4", 5) + arrow(1640, 110, 1440, 220, "draw .32 .4", -30)
    + card(doc("THE NEW YORK TIMES · 27 FEB 2004", f'"For Exercise in New York Futility, {hl("Push Button")}"', "BY MICHAEL LUO · HEADLINE QUOTED AS PUBLISHED"),
           980, 700, 770, "up .4 .55", -1)
    + A(f'<div style="background:{SL};padding:8px 16px;font:700 46px Caveat;color:{AM};white-space:nowrap">Look closely at its face.</div>', 110, 945, "fade .02 .12", "z-index:66") + PANEL_LBL,
    "HEADLINE: NYT, 27 FEB 2004 (MICHAEL LUO), AS REPRODUCED BY REASON 2004 · " + pcred("nyc_wait_sign") + " · " + pcred("push_sign")))

units = 65   # 3,250 buttons, one square per 50: 50 dead (2,500), 15 working (750)
sq = "".join(f'<div style="width:40px;height:40px;box-sizing:border-box;{"background:" + CO if i >= 50 else "border:4px solid " + GREY}"></div>' for i in range(units))
put("07_count", page(
    screen_rig(nyc_streets() + nyc_dots(750 / 3250), dim=.45)
    + chapter(2, "WHERE THE DEAD BUTTONS ARE")
    + scr_label("MIDTOWN MANHATTAN · REAL STREETS · DOTS ILLUSTRATIVE, NOT REAL BUTTONS")
    + card(kicker("NEW YORK CITY · CITY FIGURES, 2004 (VIA THE NYT)")
           + f'<div style="font:400 30px ISerif;color:{BODY};margin-top:8px">walk buttons left on the streets: <span style="font:400 44px Anton;color:{SL}" data-anim="count .05 .3" data-to="3250">3,250</span></div>'
           + f'<div style="display:grid;grid-template-columns:repeat(13,40px);gap:8px;margin:20px 0 16px" data-anim="fill .1 .45">{sq}</div>'
           + f'<div style="display:flex;gap:40px;align-items:flex-end"><div><div style="font:400 96px/0.9 Anton;color:{AM}"><span data-anim="count .45 .7" data-to="2500">2,500</span>+</div>'
             f'<div style="font:500 17px Plex;letter-spacing:2px;color:{SL}">▢ DID NOTHING AT ALL</div></div>'
             f'<div><div style="font:400 60px/0.9 Anton;color:{CO}">~750</div><div style="font:500 17px Plex;letter-spacing:2px;color:{SL}">■ STILL WORKED</div></div></div>'
           + f'<div style="font:500 14px Plex;letter-spacing:2px;color:{BODY};margin-top:14px">1 SQUARE = 50 BUTTONS · ~750 = 3,250 MINUS "MORE THAN 2,500"</div>', 760, 1080, 150, "up .02 .15", 1)
    + tag("ODDS BUTTON IS REAL (2004): UNDER 1 IN 4", 1110, 860, -1.5, "snap .85 .85") + PANEL_LBL,
    "COUNT: NYT 27 FEB 2004, CITY FIGURES, AS QUOTED BY REASON 2004 (TO CHECK: EXACT WORDING AGAINST THE NYT ARCHIVE) · " + NYC_SRC + "; DOT SHARE = 750 OF 3,250, PATTERN ILLUSTRATIVE"))

put("08_placebo", page(
    rig(devices(("on", "on", "on")), dim=.55)
    + chapter(2, "WHERE THE DEAD BUTTONS ARE")
    + photo("dead_button", 440, 560, 110, 170, "up .02 .15", -2.5, "80% 75%")
    + ring(420, 680, 52, 52, "draw .82 .9", 9) + arrow(800, 760, 500, 700, "draw .86 .93", 40)
    + card(kicker("THE NEW YORK TIMES · 2004 · QUOTED")
           + f'<div style="font:400 40px/1.2 ISerif;color:{SL};margin-top:10px">"More than 2,500 of the 3,250 walk buttons that still exist function essentially as {hl("mechanical placebos")}, city figures show."</div>', 820, 700, 150, "up .12 .25", 1)
    + A(f'<div style="width:380px;background:{PAPER};border:3px dashed {SL};padding:18px 22px;transform:rotate(-6deg);box-shadow:0 12px 26px rgba(0,0,0,.45)">'
        f'<div style="font:500 14px Plex;letter-spacing:3px;color:{CO}">Rx · DISPENSED BY THE CITY</div><div style="font:400 44px/1 Anton;color:{SL};margin-top:6px">TAKE ONE PRESS<br>AS NEEDED</div><div style="font:500 13px Plex;letter-spacing:2px;color:{BODY};margin-top:8px">SIGHT GAG · ILLUSTRATION</div></div>', 230, 220, "slam .55 .56", "z-index:66")
    + tag("INSTALLED: WHEN TRAFFIC WAS MUCH LIGHTER", 820, 560, 1, "snap .7 .7", light=True)
    + A(f'<div style="font:400 34px/1.3 ISerif;color:{PAPER};width:840px;background:rgba(20,24,36,.92);padding:20px 26px;border-left:8px solid {CO}">Then the signals moved onto central, computer-controlled timing. The buttons stayed on the poles, <span style="color:{AM}">connected to nothing.</span></div>', 820, 660, "fade .8 .9", "z-index:60")
    + PANEL_LBL,
    "QUOTE: NYT 27 FEB 2004 AS REPRODUCED BY REASON 2004 (TO CHECK: WORDING) · 'WHEN TRAFFIC WAS MUCH LIGHTER': NYC DOT OFFICIAL, PARAPHRASE · " + pcred("dead_button") + " (NOT A NYC BUTTON)"))

put("09_london", page(
    screen_rig(locator((-11, 3, 49.5, 59.5), "United Kingdom", (-0.1276, 51.5072), "LONDON"), dim=.45)
    + chapter(2, "WHERE THE DEAD BUTTONS ARE") + scr_label("LOCATOR · " + NE_SRC)
    + photo("london_pelican", 330, 430, 1060, 120, "up .1 .22", -2, "60% 70%", zoom=1.9)
    + card(kicker("TfL · VIA BBC NEWS · 2013") + f'<div style="font:400 30px/1.3 ISerif;color:{SL};margin-top:8px">At most London junctions, the button <b>does</b> control the green man. If nobody presses, the lights skip the walking part.</div>',
           450, 1440, 130, "up .25 .38", 1.5)
    + card(kicker("DEPARTMENT FOR TRANSPORT · VIA BBC NEWS · 2013") + f'<div style="font:400 32px/1.3 ISerif;color:{SL};margin-top:8px">At busy junctions the crossing "may be programmed to come up every time {hl("even if no-one presses")} the button".</div>',
           800, 1060, 720, "up .5 .62", -1)
    + tag("LIKE A WAITER WHO BRINGS THE BILL REGARDLESS", 160, 900, -1.5, "snap .88 .88", light=True) + PANEL_LBL,
    "TfL AND DfT: BBC NEWS MAGAZINE 2013, VIA MIRRORS (DATED 2013; REFRESH BEFORE AIR) · " + pcred("london_pelican") + " · " + NE_SRC))

put("10_sydney", page(
    screen_rig(locator((112, 155, -44, -10), "Australia", (151.2093, -33.8688), "SYDNEY"), dim=.45)
    + chapter(2, "WHERE THE DEAD BUTTONS ARE") + scr_label("LOCATOR · " + NE_SRC)
    + photo("sydney_street", 500, 330, 1060, 110, "up .1 .22", 2, "50% 60%")
    + card(kicker("TRANSPORT FOR NSW · MARCH 2020") + f'<div style="font:400 52px/1 Anton;color:{SL};margin-top:8px">CBD CROSSINGS {hl("AUTOMATED")}</div>'
           + f'<div style="font:400 28px/1.3 ISerif;color:{BODY};margin-top:8px">so nobody had to touch the buttons during COVID.</div>', 700, 1060, 680, "up .3 .42", -1.2)
    + A(f'<div style="width:270px;height:270px;border-radius:50%;background:{SL};border:10px solid {PAPER};box-shadow:0 18px 30px rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;transform:rotate(-8deg)">'
        f'<div style="font:400 42px/1 Anton;color:{PAPER};text-align:center">BUTTON<br>STATUS:<br><span style="color:{AM}">ON LEAVE</span><div style="font:500 11px Plex;letter-spacing:2px;margin-top:8px">SIGHT GAG</div></div></div>', 1600, 380, "slam .7 .71", "z-index:66")
    + PANEL_LBL,
    "TRANSPORT FOR NSW 2020/2021; TIME OUT SYDNEY; GOVERNMENT NEWS · BUTTON COVERS: SMH VIA INKL (TO CHECK: DATE) · " + pcred("sydney_street") + " · " + NE_SRC))

put("11_lift", page(
    rig(devices(("on", "on", "on"), close_glow=True, smudges=3), s=1.5, cx=1037, cy=520, dim=.35)
    + chapter(2, "WHERE THE DEAD BUTTONS ARE")
    + photo("lift_buttons", 330, 440, 570, 150, "up .05 .18", -2.5, "50% 80%", drift=(-18, 0))
    + card(kicker("LAW CARD") + f'<div style="font:400 44px/1.05 Anton;color:{SL};margin-top:6px">AMERICANS WITH DISABILITIES ACT · 1990</div>', 820, 1000, 110, "up .15 .27", 1.2)
    + card(kicker("2010 ADA STANDARDS FOR ACCESSIBLE DESIGN · §407.3.5 DOOR DELAY")
           + f'<div style="font:400 36px/1.3 ISerif;color:{SL};margin-top:10px">"… remain fully open in response to a car call for {hl("3 seconds minimum")}."</div>'
           + f'<div style="font:400 120px/1 Anton;color:{AM};margin-top:6px">3 S <span style="font:400 32px Anton;color:{SL}">MINIMUM, DOORS FULLY OPEN</span></div>', 820, 1000, 300, "up .35 .5", -1)
    + tag("USER ACTIVATION CANNOT REDUCE THE MINIMUM (PARAPHRASE)", 1000, 790, -1, "snap .75 .75", light=True)
    + tag("OTHER SIDE: IT WORKS, AFTER THE WAIT", 1000, 870, 1, "snap .88 .88") + PANEL_LBL,
    "2010 ADA STANDARDS §407.3.5 (PRIMARY); US ACCESS BOARD GUIDE CH. 4 (PRIMARY) · OTHER SIDE: NATIONAL ELEVATOR INDUSTRY, INC. VIA ABC7 · " + pcred("lift_buttons") + ""))

put("12_lift_split", page(
    rig(devices(("on", "on", "on"), close_glow=True), s=1.5, cx=1037, cy=520, dim=.55)
    + A(f'<div style="width:6px;height:700px;background:{PAPER}"></div>', 1257, 200, "wipe 0 .1", "z-index:55")
    + photo("lift_panel", 340, 560, 80, 40, "up .02 .14", -2, "50% 55%", drift=(-16, 0))
    + head("PLACEBO?", 840, 200, "fade .05 .12", 90) + head("DELAYED?", 1340, 200, "fade .05 .12", 90, AM)
    + card(kicker("NEII · VIA THE NEW YORK TIMES · 2016 · PARAPHRASE") + f'<div style="font:400 30px/1.3 ISerif;color:{SL};margin-top:8px">Working close buttons were {hl("phased out")} after the 1990 law.</div>', 380, 840, 340, "up .2 .32", -1)
    + card(kicker("SAME TRADE GROUP · VIA ABC7") + f'<div style="font:400 30px/1.3 ISerif;color:{SL};margin-top:8px">"People think it is merely a placebo button and it\'s not."</div>'
           + f'<div style="margin-top:16px;height:22px;background:#DCE3EC;position:relative"><div data-anim="wipe .5 .8" style="position:absolute;inset:0;background:{CO}"></div></div>'
           + f'<div style="font:500 14px Plex;letter-spacing:2px;color:{SL};margin-top:6px">LEGAL WAIT → THEN ▶◀ CLOSES</div>', 420, 1340, 340, "up .35 .47", 1)
    + tag("BUTTON BEHAVIOUR: SET BY THE CUSTOMER", 1000, 820, -1.5, "snap .85 .85", light=True) + PANEL_LBL,
    "NEII (KAREN PENAFIEL) VIA NYT 2016 AS REPORTED BY CBS BOSTON/AOL (TO CHECK: WORDING) · ABC7 · OTIS VIA AOL/YAHOO (OWNER SETS THE BEHAVIOUR) · " + pcred("lift_panel")))

dots70 = "".join(f'<div style="width:30px;height:30px;border-radius:50%;background:{AM if i < 51 else CO}"></div>' for i in range(70))
put("13_office", page(
    rig(devices(("on", "on", "on")), s=1.6, cx=1680, cy=300, dim=.6)
    + chapter(2, "WHERE THE DEAD BUTTONS ARE")
    + photo("office_cubicle", 840, 470, 70, 150, "up .02 .15", -1.5, "50% 55%", drift=(-24, 0))
    + card(kicker("THE WALL STREET JOURNAL · JAN 2003 · REPORTED") + f'<div style="font:400 32px/1.3 ISerif;color:{SL};margin-top:8px">Many office thermostats are {hl("fakes")}: plastic boxes on the wall, so people feel they\'ve changed the temperature.</div>', 760, 120, 700, "up .2 .32", 1)
    + photo("placebo_thermo", 270, 360, 990, 110, "up .1 .22", 2.5, "50% 70%")
    + card(kicker("ACHR NEWS · 'PLACEBO STATS' · 2003") + f'<div style="font:400 84px/0.9 Anton;color:{AM};margin-top:6px">51 <span style="font:400 40px Anton;color:{SL}">OF 70</span></div>'
           + f'<div style="font:400 24px/1.25 ISerif;color:{BODY}">said yes, they had installed dummy thermostats</div>'
           + f'<div style="display:grid;grid-template-columns:repeat(10,30px);gap:8px;margin-top:14px" data-anim="fill .35 .6">{dots70}</div>'
           + f'<div style="display:inline-block;margin-top:14px;background:{SL};color:{PAPER};font:500 17px Plex;letter-spacing:3px;padding:6px 10px">INFORMAL WEB POLL</div>', 500, 1360, 110, "up .3 .42", -1)
    + card(kicker("ACHR NEWS · ITS OWN DESCRIPTION") + f'<div style="font:400 28px/1.3 ISerif;color:{SL};margin-top:8px">comfort for occupants {hl("without giving them a direct interface")} to the mechanical system</div>', 560, 1300, 690, "up .6 .72", 1.2)
    + tag("SAMPLE: 70 · METHOD: WHOEVER CLICKED", 940, 960, -1.5, "snap .88 .88", light=True) + PANEL_LBL,
    "WSJ JAN 2003 (JARED SANDBERG), VIA NPR 15-16 JAN 2003 (TO CHECK: DATE) · ACHR NEWS 'PLACEBO STATS', ~31 MAR 2003 (TO CHECK: PAGE, DATE AND WORDING) · " + pcred("placebo_thermo") + " · " + pcred("office_cubicle")))

# ==== 3 MECHANICS ==========================================================================================================
put("14_langer", page(
    rig(devices(("on", "on", "on")), dim=.76)
    + chapter(3, "WHY PRESSING FEELS GOOD")
    + card(study("ELLEN LANGER", "1975", "Journal of Personality and Social Psychology 32(2): 311–328", '"THE ILLUSION OF CONTROL" · SIX STUDIES', "LOTTERY STUDY: N = 53"), 820, 110, 170, "up .02 .15", -1.5)
    + card(kicker("HER DEFINITION, RIGHT HERE") + f'<div style="font:400 44px/1.3 ISerif;color:{SL};margin-top:10px">"an expectancy of a personal success probability {hl("inappropriately higher")} than the objective probability would warrant"</div>', 900, 900, 330, "up .2 .35", 1.2)
    + tag("TRANSLATION: VIBES ≠ ODDS", 1060, 840, -2, "snap .6 .6", amber=True)
    + A(f'<div style="width:640px;height:230px;background:rgba(20,24,36,.92);border-top:6px solid {CO};padding:18px 24px;box-sizing:border-box"><div style="font:500 16px Plex;letter-spacing:3px;color:{PAPER}">LANGER\'S SKILL CUES: LUCK BORROWS THE COSTUME OF SKILL</div></div>', 110, 500, "fade .66 .7", "z-index:58")
    + "".join(tag(t, (140, 360, 140, 410)[i], (570, 570, 645, 645)[i], [-3, 2, -1, 3][i], f"snap {.7 + i * .05:.2f} {.7 + i * .05:.2f}", light=True) for i, t in enumerate(("CHOICE", "FAMILIARITY", "INVOLVEMENT", "COMPETITION"))) + PANEL_LBL,
    "LANGER (1975) JPSP 32(2):311-328, AS QUOTED IN REVIEWS (PMC9292938; CLARK & WOHL 2021) · SKILL CUES: LANGER 1975 AS SUMMARISED BY CLARK & WOHL 2021"))

tick = lambda v: f'<div style="position:absolute;left:-70px;top:{430 - v * 43}px;font:500 16px Plex;color:{SL}">${v}</div><div style="position:absolute;left:0;right:0;top:{430 - v * 43 + 10}px;border-top:1px dashed rgba(20,24,36,.25)"></div>'
ticket = lambda x, y, r, s: A(f'<div style="width:120px;height:170px;background:#fff;border:3px solid {SL};transform:rotate({r}deg);box-shadow:4px 6px 0 rgba(0,0,0,.3);position:relative">'
                              f'<svg width="120" height="130" viewBox="0 0 120 130"><circle cx="60" cy="38" r="20" fill="{SL}"/><path d="M28 120 Q60 54 92 120 Z" fill="{SL}"/></svg>'
                              f'<div style="font:500 13px Plex;letter-spacing:2px;color:{SL};text-align:center">$1 TICKET</div></div>', x, y, f"drop {s} {s + .06:.2f}", "z-index:56")
put("15_lottery", page(
    rig(devices(("on", "on", "on")), dim=.62)
    + chapter(3, "WHY PRESSING FEELS GOOD")
    + card(f'<div style="display:flex;gap:40px">'
           f'<div style="width:520px">{kicker("RECONSTRUCTION · LANGER 1975, LOTTERY STUDY")}<div style="font:400 50px/1 Anton;color:{SL};margin-top:8px">WHAT WOULD YOU SELL YOUR TICKET BACK FOR?</div>'
           f'<div style="font:400 28px/1.3 ISerif;color:{BODY};margin-top:12px">Same price. Same odds. Same draw. Office workers either picked their own card or were handed one.</div>'
           f'<div style="display:flex;gap:20px;margin-top:20px;font:400 40px Anton;color:{SL}"><div>N = 26<div style="font:500 15px Plex;letter-spacing:2px">HANDED ONE</div></div><div style="font:400 40px Anton;color:{CO}">=</div><div>N = 27<div style="font:500 15px Plex;letter-spacing:2px">CHOSE</div></div></div></div>'
           f'<div style="position:relative;width:560px;height:520px;margin-left:80px"><div style="position:absolute;left:0;right:0;top:0;height:440px">{"".join(tick(v) for v in (0, 2, 4, 6, 8, 10))}</div>'
           f'<div style="position:absolute;left:0;right:0;top:440px;height:4px;background:{SL}"></div>'
           f'<div data-anim="grow .2 .4" style="position:absolute;left:60px;top:{440 - 1.96 * 43:.0f}px;width:170px;height:{1.96 * 43:.0f}px;background:{CO}"></div>'
           f'<div data-anim="grow .45 .7" style="position:absolute;left:310px;top:{440 - 8.67 * 43:.0f}px;width:170px;height:{8.67 * 43:.0f}px;background:{AM}"></div>'
           f'<div data-anim="fade .38 .42" style="position:absolute;left:40px;width:210px;text-align:center;top:{440 - 1.96 * 43 - 74:.0f}px;font:400 60px Anton;color:{SL}">$1.96</div>'
           f'<div data-anim="fade .68 .72" style="position:absolute;left:290px;width:210px;text-align:center;top:{440 - 8.67 * 43 - 74:.0f}px;font:400 60px Anton;color:{AM}">$8.67</div>'
           f'<div style="position:absolute;left:40px;width:210px;text-align:center;top:456px;font:500 16px Plex;letter-spacing:2px;color:{SL}">HANDED A TICKET</div>'
           f'<div style="position:absolute;left:290px;width:210px;text-align:center;top:456px;font:500 16px Plex;letter-spacing:2px;color:{SL}">PICKED THEIR OWN</div></div></div>',
           1320, 300, 170, "up .02 .15", 0)
    + photo("lottery_ticket", 300, 190, 110, 770, "up .05 .15", -4, "50% 50%", cap=False, drift=(-14, 0))
    + A(f'<div style="font:500 14px/1.4 Plex;letter-spacing:2px;color:{PAPER};width:520px">A MODERN LOTTERY TICKET, NOT LANGER&#39;S 1975 ONES<br>PHOTO: {CRED["lottery_ticket"]["author"].upper()} · {CRED["lottery_ticket"]["licence"]}</div>', 470, 905, "fade .12 .2", "z-index:60")
    + tag("PREMIUM: POINTING", 1190, 430, -4, "slam .86 .87")
    + PANEL_LBL,
    "LANGER 1975 LOTTERY: N = 27 CHOSE / 26 ASSIGNED; MEAN RESALE ASKED $8.67 VS $1.96 VIA PMC5399809 (TO CHECK: AGAINST THE ORIGINAL JPSP TABLE AND EXPERIMENT NUMBER) · BARS FROM ZERO · " + pcred("lottery_ticket")))

# [TRAP REVEAL]: the button plate swings open on its hinge
SWING_JS = """<script>(function(){const q=new URLSearchParams(location.search);const T=q.has('t')?parseFloat(q.get('t')):1;
document.querySelectorAll('[data-swing]').forEach(el=>{const [s,e,deg]=el.dataset.swing.split(' ').map(Number);const p=Math.min(1,Math.max(0,(T-s)/(e-s)));
const v=1-Math.pow(1-p,3);el.style.transform=`rotateY(${-deg*v}deg)`})})()</script>"""
CAV = (580, 150, 1330, 950)   # cavity, frame coords (the button plate at 2x)
bx, by = 960, 580             # button terminal position (frame)
lx = [(1557, 672), (1680, 612), (1803, 672)]
LF = [(960 + (x - 1680) * 2, 540 + (y - 740) * 2) for x, y in lx]
drum_x, drum_y = 960, 830
door_face = (f'<div style="position:absolute;inset:0;background:url(/assets/studio/panel.jpg) -2980px -1090px/3840px 2160px;border-radius:26px"></div>'
             f'<svg style="position:absolute;left:0;top:0" width="750" height="800" viewBox="1490 545 375 400">{DEFS}{big_button()}{lamps(("on", "on", "on"))}</svg>')
mech = (
    f'<rect x="{CAV[0]}" y="{CAV[1]}" width="{CAV[2] - CAV[0]}" height="{CAV[3] - CAV[1]}" rx="26" fill="{DEEP}"/>'
    + "".join(f'<line x1="{CAV[0]}" y1="{y}" x2="{CAV[2]}" y2="{y}" stroke="{CO}" stroke-width="1" opacity=".25"/>' for y in range(CAV[1] + 40, CAV[3], 40))
    + "".join(f'<circle cx="{x}" cy="{y}" r="44" fill="#26314A" stroke="{CO}" stroke-width="5"/><circle cx="{x}" cy="{y}" r="10" fill="{PAPER}"/>' for x, y in LF)
    + "".join(f'<g data-anim="draw {.35 + i * .06:.2f} {.5 + i * .06:.2f}"><path d="M{x} {y + 44} C {x} {y + 200}, {drum_x - 120 + i * 120} {drum_y - 180}, {drum_x - 120 + i * 120} {drum_y - 64}" stroke="{CO}" stroke-width="9" fill="none" pathLength="1"/></g>' for i, (x, y) in enumerate(LF))
    + f'<rect x="{drum_x - 210}" y="{drum_y - 64}" width="420" height="128" rx="20" fill="#A9B4C4" stroke="{PAPER}" stroke-width="4"/>'
    + "".join(f'<line x1="{drum_x - 190 + k * 38}" y1="{drum_y - 60}" x2="{drum_x - 190 + k * 38}" y2="{drum_y + 60}" stroke="#7D8899" stroke-width="3"/>' for k in range(11))
    + "".join(f'<rect x="{drum_x - 132 + i * 120}" y="{drum_y - 40 + i * 22}" width="24" height="30" rx="5" fill="{AM}"/>' for i in range(3))
    + f'<text x="{drum_x}" y="{drum_y + 104}" text-anchor="middle" font-family="Plex" font-size="20" letter-spacing="4" fill="{PAPER}">CAM TIMER · TURNS ON A SCHEDULE</text>'
    + f'<circle cx="{bx}" cy="{by}" r="70" fill="#5A6578"/><circle cx="{bx}" cy="{by}" r="44" fill="#7D8899"/><rect x="{bx - 12}" y="{by - 12}" width="24" height="24" fill="{PAPER}"/>'
    + f'<g data-anim="draw .62 .72"><path d="{wobble(bx, by, 112, 104, 7)}" fill="none" stroke="{AM}" stroke-width="9" stroke-linecap="round" pathLength="1"/></g>')
tape_rows = [("LAMP 1", "+3.5 S", "after 'when you're ready'"), ("LAMP 2", "+4.0 S", "after 'whenever you like'"), ("LAMP 3", '"NOW"', "+1.2 s, because I said when")]
tape = "".join(f'<div data-anim="up {.72 + i * .07:.2f} {.8 + i * .07:.2f}" style="display:flex;align-items:baseline;gap:18px;padding:12px 0;border-bottom:2px dashed {GREY}">'
               f'<div style="font:500 20px Plex;letter-spacing:3px;color:{SL};width:100px">{a_}</div><div style="font:400 54px Anton;color:{AM};width:150px">{b}</div>'
               f'<div style="font:400 24px ISerif;color:{BODY}">{c}</div></div>' for i, (a_, b, c) in enumerate(tape_rows))
put("16_reveal", page(
    BACKDROP + svg(mech)
    + a(f'<div style="perspective:1800px;width:750px;height:800px"><div data-swing=".05 .3 118" style="position:relative;width:750px;height:800px;transform-origin:0 50%;transform-style:preserve-3d"><div style="position:absolute;inset:0;backface-visibility:hidden;box-shadow:0 30px 60px rgba(0,0,0,.6);border-radius:26px">{door_face}</div><div style="position:absolute;inset:0;backface-visibility:hidden;transform:rotateY(180deg);border-radius:26px;background:#3A4456;border:10px solid #5A6578;box-sizing:border-box;display:flex;align-items:center;justify-content:center;font:500 22px Plex;letter-spacing:5px;color:{PAPER}">BACK OF THE PANEL</div></div></div>', 580, 150, "z-index:30")
    + hand("No wire.", 1080, 470, "fade .68 .76", 64, AM, 300, -4)
    + photo("signal_cabinet", 470, 320, 60, 480, "up .55 .66", -2, "50% 50%", drift=(-14, 0))
    + A(f'<div style="width:470px;font:700 40px/1.05 Caveat;color:{AM};transform:rotate(-2deg);background:rgba(20,24,36,.85);padding:8px 14px">The real crossing version: the timing lives in a box like this.</div>', 60, 330, "fade .6 .7", "z-index:60")
    + A(f'<div style="font:400 30px/1.2 Anton;color:{PAPER};letter-spacing:2px">[TRAP REVEAL]</div><div style="font:400 64px/1 Anton;color:{PAPER};margin-top:8px">THE BUTTON WAS<br>NEVER <span style="color:{AM}">CONNECTED</span></div>', 1390, 160, "up .3 .42", "z-index:60")
    + A(f'<div style="width:470px;background:{PAPER};padding:14px 22px;box-shadow:0 18px 34px rgba(0,0,0,.45);border-top:8px solid {CO}">{kicker("THE TIMER TAPE")}{tape}</div>', 1390, 420, "up .68 .74", "z-index:60")
    + SWING_JS + TRAP_LBL,
    "STUDIO RECONSTRUCTION OF OUR OWN TRAP: THE TIMES ARE THE SCRIPT'S [WAIT] CUES · CAM TIMER, WIRES AND TERMINAL DRAWN IN THE STUDIO · " + pcred("signal_cabinet")))

sand = (stick(300, 614, 3.0, SL, False)
        + f'<rect x="230" y="800" width="560" height="22" fill="{SL}"/>'
        + f'<rect x="440" y="770" width="220" height="28" rx="12" fill="{PAPER}" stroke="{SL}" stroke-width="5"/><rect x="446" y="754" width="208" height="16" fill="{CO}"/>'
        + f'<rect x="440" y="720" width="220" height="34" rx="14" fill="{PAPER}" stroke="{SL}" stroke-width="5" data-anim="drop .5 .6"/>'
        + f'<path d="M348 680 L450 652" stroke="#A9B4C4" stroke-width="12" stroke-linecap="round"/>')
put("17_sandwich", page(
    trap((.3, .5, .7)) .replace('left:0;top:0;width:1920px', 'left:420px;top:0;width:1920px', 1)
    + A(f'<div style="width:760px;height:620px;background:{PAPER};box-shadow:0 22px 40px rgba(0,0,0,.5);transform:rotate(-1.5deg);border-top:8px solid {CO}"></div>', 70, 260, "up 0 .1", "z-index:40")
    + A(f'<svg width="900" height="900" viewBox="0 0 900 900">{sand}</svg>', 70, -20, "fade .05 .15", "z-index:41")
    + A(f'<div style="font:400 58px/1 Anton;color:{SL};width:700px">EVERY LAMP WOULD HAVE LIT<br>IF YOU\'D BEEN MAKING <span style="color:{AM}">A SANDWICH</span>.</div>', 110, 290, "up .1 .22", "z-index:42")
    + A(f'<div style="font:500 16px Plex;letter-spacing:3px;color:{SL}">ILLUSTRATION · STICK FIGURE, BACK TURNED</div>', 110, 840, "fade .1 .2", "z-index:42")
    + tag("LAMPS: ON SCHEDULE", 1480, 90, -1.5, "snap .75 .75", amber=True) + TRAP_LBL,
    "SIGHT GAG (ILLUSTRATION) · LAMPS ON THE TRAP'S TIMER: +3.5 S, +4.0 S, +1.2 S"))

stickies = "".join(A(f'<div style="width:220px;height:150px;background:{PAPER};box-shadow:0 10px 20px rgba(0,0,0,.4);transform:rotate({r}deg);display:flex;align-items:center;justify-content:center">'
                     f'<div style="border:5px solid {AM};color:{AM};font:400 40px Anton;padding:4px 12px;transform:rotate(-8deg)">APPROVED</div></div>', x, y, f"drop {s} {s + .06:.2f}", "z-index:50")
                   for x, y, r, s in ((1100, 560, -4, .4), (1350, 590, 5, .5), (1600, 555, -2, .6)))
put("18_manager", page(
    a('<img src="/assets/ai/K3.jpg" style="width:1920px;height:1080px;display:block">', 0, 0)
    + chapter(3, "WHY PRESSING FEELS GOOD")
    + A(f'<div style="width:760px;background:rgba(240,244,248,.95);padding:28px 34px;box-shadow:0 18px 34px rgba(10,14,24,.45);border-top:8px solid {CO}">'
        f'{kicker("METAPHOR, NOT ANATOMY")}<div style="font:400 72px/0.95 Anton;color:{SL};margin-top:8px">MEET YOUR BRAIN,<br>{hl("MIDDLE MANAGER")}</div>'
        f'<div style="font:400 30px/1.3 ISerif;color:{BODY};margin-top:14px">It sees an action, then a result, and signs off: "Great work, team." It doesn\'t check the wiring. It checks the timing.</div></div>',
        1080, 130, "up .05 .2", "z-index:48")
    + stickies + tag("DEPARTMENT: CREDIT-TAKING · HEADCOUNT: 1", 1180, 790, -1.5, "snap .85 .85")
    + LBL("AI ILLUSTRATION · METAPHOR, NOT ANATOMY", 70, 960),
    "METAPHOR FOR ACTION-OUTCOME CREDIT (ILLUSION OF CONTROL; LANGER 1975) · FACELESS FIGURE, NO REAL PERSON"))

# ==== 4 STAKES =============================================================================================================
put("19_replication", page(
    rig(devices(("on", "on", "on")), dim=.66)
    + chapter(4, "WE CHECK THE SCIENCE")
    + card(study("LANGER", "1975", "J. Personality & Social Psychology", "THE LOTTERY: OFFICE WORKERS, 1970s")
           + f'<div style="font:400 80px/1 Anton;color:{AM};margin-top:10px">N = 53</div>', 520, 90, 170, "up .02 .15", -1.5)
    + card(study("KLUSOWSKI, SMALL & SIMMONS", "2021", "Psychological Science 32(2): 159–172")
           + f'<div style="display:flex;gap:30px;margin-top:12px"><div style="font:400 64px/1 Anton;color:{SL}"><span data-anim="count .2 .4" data-to="17">17</span><div style="font:500 14px Plex;letter-spacing:2px">EXPERIMENTS</div></div>'
             f'<div style="font:400 64px/1 Anton;color:{SL}">N = <span data-anim="count .2 .45" data-to="10825">10,825</span><div style="font:500 14px Plex;letter-spacing:2px">~11,000 PEOPLE</div></div></div>'
           + f'<div style="font:400 26px/1.3 ISerif;color:{BODY};margin-top:10px">Choice rarely made people feel luckier, unless it really did improve their odds.</div>', 640, 660, 150, "up .15 .28", 1)
    + stamp("REPLICATION: CHOICE ≠ CONFIDENCE (MOSTLY)", 560, 660, "slam .5 .52", -4, 40)
    + card(study("STEFAN & DAVID", "2013", "J. Applied Social Psychology", "META-ANALYSIS · POOLED STUDIES")
           + f'<div style="font:400 72px/1 Anton;color:{AM};margin-top:10px">d = 0.62</div>'
           + f'<div style="position:relative;height:56px;margin-top:10px;border-bottom:3px solid {SL}">'
             f'<div data-anim="wipe .74 .84" style="position:absolute;left:{0.49 / 1.0 * 400:.0f}px;width:{(0.75 - 0.49) * 400:.0f}px;top:22px;height:10px;background:{CO}"></div>'
             f'<div data-anim="pop .82 .88" style="position:absolute;left:{0.62 * 400 - 12:.0f}px;top:15px;width:24px;height:24px;border-radius:50%;background:{AM}"></div>'
             + "".join(f'<div style="position:absolute;left:{v * 400:.0f}px;top:58px;font:500 13px Plex;color:{SL};transform:translateX(-50%)">{v:g}</div>' for v in (0, .5, 1.0))
           + f'</div><div style="font:500 14px Plex;letter-spacing:2px;color:{BODY};margin-top:24px">95% CI 0.49–0.75</div>'
           + f'<div style="display:inline-block;margin-top:10px;background:{AM};color:{SL};font:500 16px Plex;letter-spacing:2px;padding:5px 9px">TO CHECK: JOURNAL AND d</div>', 470, 1360, 170, "up .6 .72", 1.5)
    + A(f'<div style="border-top:6px solid {CO};width:1700px;padding-top:12px;font:400 56px Anton;color:{PAPER};text-align:center">REAL · SMALLER · <span style="color:{AM}">DEPENDS</span></div>', 110, 830, "wipe .82 .95", "z-index:60") + PANEL_LBL,
    "LANGER 1975 (N = 27 + 26) · KLUSOWSKI, SMALL & SIMMONS 2021, PSYCH. SCIENCE 32(2):159-172 (ABSTRACT) · STEFAN & DAVID 2013 META-ANALYSIS, d = 0.62, 95% CI 0.49-0.75 (TO CHECK: JOURNAL AND CI)"))

waves = "".join(f'<path d="M{x} 170 l20 -50 l20 90 l20 -110 l20 120 l20 -80 l20 40" stroke="{CO}" stroke-width="6" fill="none" data-anim="fade {.05 + k * .05:.2f} {.1 + k * .05:.2f}"/>' for k, x in enumerate((140, 300, 460)))
put("20_glass", page(
    rig(devices(("on", "on", "on")), dim=.66)
    + chapter(4, "WE CHECK THE SCIENCE")
    + A(f'<div style="width:780px;height:560px;background:{PAPER};box-shadow:0 22px 40px rgba(0,0,0,.5);border-top:8px solid {CO}"></div>', 90, 150, "up 0 .1", "z-index:40")
    + A(f'<svg width="780" height="560">{waves}{stick(220, 360, 1.5, SL)}{stick(560, 360, 1.5, SL)}'
        f'<rect x="590" y="420" width="140" height="16" fill="{SL}"/><circle cx="660" cy="402" r="22" fill="{AM}" stroke="{SL}" stroke-width="4"/>'
        f'<rect x="170" y="420" width="140" height="16" fill="{SL}"/></svg>', 90, 150, "fade .05 .15", "z-index:41")
    + tag("PLEASE DON'T", 690, 470, 4, "snap .3 .3", light=True)
    + A(f'<div style="font:500 16px Plex;letter-spacing:3px;color:{SL}">RECONSTRUCTION · STICK FIGURES · UNPREDICTABLE NOISE</div>', 120, 650, "fade .1 .2", "z-index:42")
    + card(study("GLASS & SINGER", "1972", "Urban Stress · Academic Press", "A BUTTON THAT COULD STOP THE NOISE, AND A REQUEST NOT TO PRESS IT. ALMOST NOBODY PRESSED IT.", "N: NOT IN OUR SOURCES (TO CHECK)")
           + f'<div style="position:relative;height:230px;margin-top:18px;border-bottom:4px solid {SL}">'
             f'<div data-anim="grow .4 .6" style="position:absolute;left:40px;bottom:0;width:150px;height:190px;background:{AM}"></div><div data-anim="grow .4 .6" style="position:absolute;left:260px;bottom:0;width:150px;height:110px;background:{CO}"></div></div>'
           + f'<div style="display:flex;font:500 15px Plex;letter-spacing:2px;color:{SL};margin-top:8px"><div style="width:220px;padding-left:30px">WITH BUTTON</div><div>NO BUTTON</div></div>'
           + f'<div style="display:inline-block;margin-top:10px;background:{SL};color:{PAPER};font:500 15px Plex;letter-spacing:2px;padding:4px 8px">LATER TASKS · DIRECTION ONLY, NO VALUES</div>', 860, 960, 150, "up .2 .32", 1)
    + stamp("AFTER-EFFECTS NOT REPLICATED", 1080, 840, "slam .75 .77", -5, 42, True)
    + tag("SAME DEPARTMENT AS THE CROSSWALK", 120, 780, -1.5, "snap .9 .9", amber=True) + PANEL_LBL,
    "GLASS & SINGER, URBAN STRESS (ACADEMIC PRESS 1972), VIA SECONDARY SUMMARIES (TO CHECK: TASK DETAILS) · NON-REPLICATION WITH CONSENT PROCEDURES: CITATION TO CHECK · BARS SHOW DIRECTION ONLY"))

put("21_plant", page(
    A('<img src="/assets/real/windowsill.jpg" style="width:1920px;height:1080px;object-fit:cover;display:block;filter:brightness(.62)">', 0, 0, "push 0 1", "transform-origin:75% 50%")
    + chapter(4, "WE CHECK THE SCIENCE")
    + card(study("LANGER & RODIN", "1976", "JPSP 34(2): 191–198 · a Connecticut nursing home", "ONE FLOOR: A TALK ABOUT TAKING CHARGE, AND EACH RESIDENT CHOSE A PLANT. THE OTHER: PLANTS TOO, CARED FOR BY STAFF (TO CHECK).")
           + f'<div style="font:400 64px/1 Anton;color:{AM};margin-top:8px">N = 91</div>', 700, 110, 150, "up .05 .18", -1.2)
    + card(kicker("RODIN & LANGER · 1977 · 18-MONTH FOLLOW-UP") + f'<div style="font:400 30px/1.3 ISerif;color:{SL};margin-top:8px">reported fewer deaths in the take-charge group. <span style="color:{BODY}">(No numbers: not verified.)</span></div>', 700, 110, 610, "up .3 .42", 1)
    + card(kicker("CAVEATS", AM) + f'<div style="font:400 36px/1.1 Anton;color:{SL};margin-top:6px">{hl("CONFOUND")}: THE FLOORS GOT DIFFERENT SPEECHES</div>'
           + f'<div style="font:400 26px/1.3 ISerif;color:{BODY};margin-top:8px">and the authors warned that too much responsibility can hurt.</div>', 560, 1240, 560, "up .5 .62", -1.5)
    + A(f'<div style="width:280px;background:{PAPER};border:3px dashed {SL};padding:14px 18px;transform:rotate(7deg);box-shadow:0 12px 26px rgba(0,0,0,.45)"><div style="font:500 14px Plex;letter-spacing:3px;color:{CO}">Rx</div><div style="font:400 64px/1 Anton;color:{SL}">1 FERN</div><div style="font:500 13px Plex;letter-spacing:2px;color:{BODY}">NOBODY SHOULD PRESCRIBE THIS</div></div>', 1420, 190, "slam .85 .86", "z-index:66")
    + LBL("PHOTO: A WINDOWSILL TODAY, NOT THE 1976 HOME", 1240, 960),
    "LANGER & RODIN (1976) JPSP 34(2):191-198, N = 91 (SECONDARY SUMMARIES) · RODIN & LANGER (1977) JPSP 35(12) · CAVEATS: SECONDARY CRITIQUES AND THE AUTHORS' DISCUSSION · Rx: SIGHT GAG · " + pcred("windowsill") + " (NOT THE STUDY'S HOME)"))

rings = "".join(f'<circle cx="230" cy="300" r="{r}" fill="none" stroke="{CO}" stroke-width="7" data-anim="fade {.4 + i * .08:.2f} {.46 + i * .08:.2f}"/>' for i, r in enumerate((130, 175, 220)))
aps = (f'<svg width="460" height="600" viewBox="0 0 460 600">{rings}<rect x="140" y="110" width="180" height="380" rx="24" fill="{PAPER}" stroke="{SL}" stroke-width="6"/>'
       f'<circle cx="230" cy="300" r="70" fill="{AM}" stroke="{SL}" stroke-width="6"/><path d="M190 300 L262 300 M240 274 L268 300 L240 326" stroke="{SL}" stroke-width="12" fill="none" stroke-linecap="round"/>'
       f'<rect x="185" y="400" width="90" height="56" rx="6" fill="{SL}"/><text x="230" y="436" text-anchor="middle" font-family="Plex" font-size="18" fill="{PAPER}">TICK</text></svg>')
put("22_court", page(
    screen_rig(nyc_streets(op=.6) + nyc_dots(.04, dead_col="#3A4A66", live_col=CO, appear="fill .02 .2", turn="fill .25 .45"), dim=.45)
    + chapter(4, "WE CHECK THE SCIENCE") + scr_label("REAL STREETS: NYC OPEN DATA · DOTS ILLUSTRATIVE")
    + A(f'<div style="font:400 120px/1 Anton;color:{AM};text-shadow:0 4px 20px rgba(0,0,0,.7)">95%+</div><div style="font:500 18px/1.4 Plex;letter-spacing:2px;color:{PAPER};width:560px">OF SIGNALLED INTERSECTIONS: NOTHING TO TELL A BLIND PEDESTRIAN WHEN TO WALK</div>', 200, 360, "fade .45 .55", "z-index:62")
    + card(kicker("COURT CARD · S.D.N.Y. · 20 OCT 2020") + f'<div style="font:400 40px/1.05 Anton;color:{SL};margin-top:6px">ACB OF NEW YORK v. CITY OF NEW YORK</div>'
           + f'<div style="font:400 26px/1.3 ISerif;color:{BODY};margin-top:6px">The city\'s crosswalks broke the disability law.</div>', 760, 1090, 100, "up .1 .22", 1)
    + card(kicker("REMEDIAL ORDER · DEC 2021") + f'<div style="font:400 64px/1 Anton;color:{SL};margin-top:6px">~<span data-anim="count .3 .5" data-to="10000">10,000</span> <span style="font:400 30px Anton">INTERSECTIONS</span></div>'
           + f'<div style="font:400 24px ISerif;color:{BODY}">with accessible signals by the early 2030s</div>'
           + f'<div style="display:inline-block;margin-top:8px;background:{AM};color:{SL};font:500 15px Plex;letter-spacing:2px;padding:4px 8px">TO CHECK: 9,000 MORE VS 10,000 TOTAL</div>', 560, 1090, 390, "up .3 .42", -1)
    + A(f'<div style="width:560px;background:{SL};border:3px solid {PAPER};padding:20px 26px;box-shadow:0 18px 34px rgba(0,0,0,.45)"><div style="font:500 15px Plex;letter-spacing:3px;color:{PAPER}">NYC DOT · 2024</div>'
        f'<div style="font:400 110px/1 Anton;color:{AM}" data-anim="count .6 .8" data-to="855">855</div><div style="font:500 16px Plex;letter-spacing:2px;color:{PAPER}">INTERSECTIONS FITTED IN ONE YEAR</div>'
        f'<div style="margin-top:14px;height:18px;background:#26314A;position:relative"><div data-anim="wipe .8 .9" style="position:absolute;left:0;top:0;bottom:0;width:{855 / 10000 * 100:.1f}%;background:{AM}"></div></div>'
        f'<div style="font:500 13px Plex;letter-spacing:2px;color:{PAPER};margin-top:6px">855 OF ~10,000 · ~12 YEARS AT THAT PACE (OUR ARITHMETIC)</div></div>', 1090, 700, "up .58 .66", "z-index:60")
    + A(aps.replace('width="460" height="600"', 'width="230" height="300"'), 1680, 690, "pop .35 .45", "z-index:61") + PANEL_LBL,
    "ACB OF NEW YORK v. CITY OF NEW YORK, S.D.N.Y. OPINION 20 OCT 2020 (PRIMARY) · REMEDIAL ORDER DEC 2021: COURTHOUSE NEWS, ROUTE FIFTY (TO CHECK: COUNT) · 855 IN 2024: NYC STREETS PLAN UPDATE (PRIMARY) · " + NYC_SRC + " · APS BUTTON DRAWN"))

put("23_fire", page(
    rig(devices(("on", "on", "on"), close_glow=True), s=1.8, cx=897, cy=520, dim=.35)
    + chapter(4, "WE CHECK THE SCIENCE")
    + A(f'<svg width="260" height="120" viewBox="0 0 260 120"><circle cx="50" cy="60" r="44" fill="{AM}" stroke="{SL}" stroke-width="6"/><circle cx="50" cy="60" r="14" fill="{SL}"/>'
        f'<rect x="90" y="48" width="150" height="24" fill="{AM}" stroke="{SL}" stroke-width="5"/><rect x="190" y="72" width="16" height="26" fill="{AM}" stroke="{SL}" stroke-width="5"/><rect x="220" y="72" width="14" height="18" fill="{AM}" stroke="{SL}" stroke-width="5"/></svg>', 120, 720, "pop .2 .3", "z-index:60;transform:rotate(-20deg)")
    + A(f'<div style="font:500 16px Plex;letter-spacing:3px;color:{PAPER}">FIRE KEY · ILLUSTRATION</div>', 130, 870, "fade .3 .4", "z-index:60")
    + photo("lift_buttons", 300, 380, 560, 170, "up .05 .16", 2, "50% 85%", drift=(14, 0))
    + card(kicker("CODE CARD · ASME A17.1 / CSA B44") + f'<div style="font:400 50px/1 Anton;color:{SL};margin-top:8px">FIREFIGHTERS\' PHASE II</div>'
           + f'<div style="font:400 34px/1.3 ISerif;color:{SL};margin-top:10px">Open power doors close only by {hl("continuous pressure on the door-close button")}.</div>', 820, 1000, 200, "up .15 .28", 1)
    + tag("DOOR CLOSE · ON CALL FOR EMERGENCIES ONLY", 1000, 640, -1.5, "slam .8 .81", amber=True) + PANEL_LBL,
    "ASME A17.1 PHASE II TEXT AS QUOTED BY IUEC ALERT AND A 2007 CODE EXTRACT (STANDARD ITSELF PAYWALLED) · ADA STANDARDS INCORPORATE ASME A17.1-2000 WITH ADDENDA · " + pcred("lift_buttons")))

# ==== 5 SYNTHESIS ==========================================================================================================
put("24_recap", page(
    rig(devices(("on", "on", "on"), close_glow=True, screen_content=screen_svg(nyc_streets(op=.85) + nyc_dots(750 / 3250, appear="fill 0 .01", turn="fill 0 .01")))
        + "".join(outline(d, "draw 0 .01") for d in ("crosswalk", "lift", "thermo", "button")), dim=.2)
    + photo("push_sign", 200, 150, 300, 560, "drop .05 .12", -4, "33% 40%", cap=False)
    + photo("lift_panel", 150, 200, 690, 600, "drop .15 .22", 3, "50% 55%", cap=False)
    + photo("placebo_thermo", 150, 200, 1330, 230, "drop .25 .32", -3, "50% 70%", cap=False)
    + tag("NYC 2004 · MOSTLY DEAD", 60, 300, -3, "snap .1 .1") + tag("LONDON · MOSTLY LIVE", 70, 370, 2, "snap .18 .18") + tag("SYDNEY · AUTO BY DAY", 60, 440, -1, "snap .26 .26", amber=True)
    + tag("WORKS · AFTER THE WAIT", 420, 960, 1.5, "snap .36 .36", light=True)
    + tag("51 OF 70 · INFORMAL POLL", 1500, 520, -2, "snap .46 .46", light=True)
    + tag("TIMER", 1610, 880, 3, "snap .56 .56", amber=True)
    + A(f'<div style="background:{PAPER};padding:22px 30px;box-shadow:0 18px 34px rgba(0,0,0,.5);border-top:8px solid {CO}"><div style="font:400 50px/1 Anton;color:{SL}">BEFORE YOU PRESS,<br>ASK WHAT IT\'S {hl("WIRED TO")}.</div>'
        f'<div style="font:500 17px Plex;letter-spacing:3px;color:{BODY};margin-top:12px">TIMER · SENSOR · PERSON · FACILITIES (HOPEFUL)</div></div>', 800, 400, "up .7 .82", "z-index:66")
    + PANEL_LBL,
    "RECAP OF CHAPTERS 2-4: NYT 2004; TfL/DfT VIA BBC 2013; TRANSPORT FOR NSW 2020; ADA §407.3.5 AND NEII VIA ABC7; ACHR NEWS 2003 (INFORMAL POLL) · " + DRAWN
    + " · PHOTOS: ERIC FISCHER, NSEIKA, EL CAJON YACHT CLUB (ALL CC BY 2.0, VIA OPENVERSE) · SCREEN: " + NYC_SRC))

put("25_last", page(
    trap(("off", "off", "off"), breathe=".0 .6")
    + A(f'<div style="font:400 52px/1.15 ISerif;color:#C9D3E0;width:450px">"Press it one more time. Whenever you\'re ready."</div>', 90, 300, "fade .02 .15", "z-index:60")
    + A(f'<div style="font:500 24px/1.6 Plex;letter-spacing:3px;color:{PAPER};width:460px">[WAIT 4.0 S]<br>NO CLICK. NO LAMP.</div>', 1420, 420, "fade .3 .4", "z-index:60")
    + A(f'<div style="font:400 86px/1 Anton;color:{PAPER}">NOTHING.</div><div style="font:400 40px/1.2 ISerif;color:#C9D3E0;margin-top:8px">Slightly offended?<br><span style="color:{AM}">Notice that.</span></div>', 110, 600, "up .7 .8", "z-index:60")
    + tag("EXHIBIT B · ALSO YOUR FEELING", 1330, 560, 2, "snap .88 .88", amber=True) + TRAP_LBL,
    TRAP_SRC + " · THIS TIME THE TIMER IS OFF"))

put("26_pause", page(
    rig(devices(("off", "off", "off"), glow=False), dim=.92)
    + svg(f'<g data-anim="draw .3 .55"><path d="M104 928 C 60 928, 40 860, -10 850" stroke="#4F8FD6" stroke-width="12" fill="none" pathLength="1"/></g>'
          f'<g data-anim="fade .5 .7"><circle cx="150" cy="930" r="90" fill="{AM}" opacity=".45" filter="url(#g2)"/></g>'
          f'<defs><filter id="g2" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="18"/></filter></defs>'
          f'<rect x="110" y="880" width="26" height="96" rx="5" fill="{AM}"/><rect x="164" y="880" width="26" height="96" rx="5" fill="{AM}"/>', "z-index:60")
    + A(f'<div style="font:400 60px/1.2 ISerif;color:#C9D3E0;text-align:center;width:1920px">To be fair, one button in this film worked every single time.</div>', 0, 300, "fade 0 .15", "z-index:60")
    + A(f'<div style="font:400 120px/1 Anton;color:{PAPER};text-align:center;width:1920px">THAT ONE WAS ALWAYS CONNECTED.<br><span style="color:{AM}">TO YOU.</span></div>', 0, 470, "up .6 .75", "z-index:60")
    + A(f'<div style="font:500 18px Plex;letter-spacing:4px;color:{PAPER}">← THE PAUSE BUTTON (GENERIC ICON, NO PLATFORM LOGO)</div>', 260, 915, "fade .55 .65", "z-index:60") + PANEL_LBL,
    "DRAGON PSYCHOLOGY · SOURCES IN THE DESCRIPTION · GENERIC PAUSE ICON DRAWN IN THE STUDIO"))

if __name__ == "__main__":
    for f in (D / "html").glob("*.html"):
        if f.stem not in NAMES:
            f.unlink()
    print(len(NAMES), "frames:", " ".join(NAMES))
