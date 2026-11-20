"""Key frames (16:9) for "Why Does Landlocked Bolivia Have a Navy?" (Print Facts, draft 1, engine A: Reverse Autopsy).
Every piece carries a timeline entry (render any moment with ?t=0..1). Numbers only from dossier.json; items marked ⚠ there
carry "TO CHECK" in the source line. Maps: Natural Earth admin-0, lakes, rivers, coastline (public domain) and Terrarium
relief (Mapzen/Tilezen, SRTM), drawn in the studio (geo.py, relief.py). AI plates B1-B6 are labelled on screen and logged in
data/ai_ledger.json; every word, number, pin and circle is added by the studio. No flags, emblems, faces or real people drawn.
Run: python3 -I geo.py && python3 -I relief.py (once), then python3 frames.py && python3 shoot_http.py"""
import json
import math
import re
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from studio import page as _page, A as _A, a, put, hl, wobble, tape, PARCH, RED, SIG, INK  # noqa: E402
from geo import P, MW, MH  # noqa: E402

TEAL = "#2C7A8C"     # film accent: water and the missing sea only
DESKC = "#1A1A1A"
OLD = "#EFE3C8"      # aged paper (a cream tone)
S = json.loads((D / "maps" / "shapes.json").read_text())

EXTRA = ("<style>@font-face{font-family:Doc;src:url(/fonts/instrument-serif-latin-400-normal.woff2)}"
         "@font-face{font-family:PlayR;src:url(/fonts/playfair-display-latin-400-normal.woff2)}</style>"
         "<script>document.addEventListener('DOMContentLoaded',()=>{const q=new URLSearchParams(location.search);"
         "const T=q.has('t')?parseFloat(q.get('t')):1;"
         "document.querySelectorAll('[data-win]').forEach(el=>{const[s,e]=el.dataset.win.split(' ').map(Number);el.style.opacity=(T>=s&&T<e)?1:0});"
         "document.querySelectorAll('[data-cam]').forEach(el=>{const[a,b]=el.dataset.cam.split(' ').map(Number);const k=T*T*(3-2*T);"
         "el.style.transform=`scale(${a+(b-a)*k})`});"
         "document.querySelectorAll('[data-peel]').forEach(el=>{const[dx,dy,r,s,e]=el.dataset.peel.split(' ').map(Number);"
         "const p=e>s?Math.min(1,Math.max(0,(T-s)/(e-s))):(T>=s?1:0);const k=1-Math.pow(1-p,3);"
         "el.style.transform=`translate(${dx*k}px,${dy*k}px) rotate(${r*k}deg)`});});</script>")
BAND = a('<div style="width:1920px;height:66px;background:rgba(244,239,230,.92)"></div>', 0, 1014, "z-index:89")
LOGOBACK = a('<div style="width:236px;height:46px;background:rgba(244,239,230,.92);border-radius:4px"></div>', 1640, 34, "z-index:89")
AISRC = "AI ILLUSTRATION (GPT-IMAGE-2.5 VIA ELEVENLABS, OWNER-APPROVED, MASTER_DIRECTIVES 8C; LOGGED IN DATA/AI_LEDGER.JSON), STUDIO-FINISHED · TEXT AND NUMBERS ADDED IN THE STUDIO"
MAPSRC = "MAP: NATURAL EARTH 1:50M ADMIN-0, LAKES, RIVERS, COASTLINE (PUBLIC DOMAIN) · RELIEF: TERRARIUM TILES (MAPZEN/TILEZEN, SRTM), HEIGHT ×6 · DRAWN IN THE STUDIO"


def page(body, src, cam=(1.0, 1.0), origin="50% 50%", bg=DESKC):
    """Every frame: a slow camera push (cam from->to over the shot), a cream band under the source line, logo D on a cream chip."""
    top = "".join(re.findall(r"<!--TOP-->(.*?)<!--/TOP-->", body, re.S))
    body = re.sub(r"<!--TOP-->.*?<!--/TOP-->", "", body, flags=re.S)
    wrap = f'<div class="a" data-cam="{cam[0]} {cam[1]}" style="left:0;top:0;width:1920px;height:1080px;transform-origin:{origin}">{body}</div>'
    return _page(wrap + top + BAND + LOGOBACK + EXTRA, bg, src)


def A(html, x, y, anim, extra=""):
    """Animated piece; a rotation given in `extra` moves to an inner wrapper so the timeline's transform doesn't erase it."""
    m = re.search(r"transform:\s*rotate\(([-\d.]+)deg\);?", extra)
    if m:
        extra = extra.replace(m.group(0), "")
        html = f'<div style="transform:rotate({m.group(1)}deg)">{html}</div>'
    return _A(html, x, y, anim, extra)


# ---- small studio pieces ----------------------------------------------------------------------------------------------
def tag(text, x, y, rot=-1.5, anim="snap .85 .85", size=20):
    """Sarcastic caption styled as an archive tag."""
    return A(f'<div style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 {size}px Plex;letter-spacing:4px;'
             f'transform:rotate({rot}deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">{text}</div>', x, y, anim, "z-index:70")


def label(text, x, y, anim="fade 0 .05", size=18, bg=PARCH, fg=INK, extra=""):
    return A(f'<div style="background:{bg};color:{fg};padding:5px 11px;font:500 {size}px Plex;letter-spacing:3px;box-shadow:0 6px 10px rgba(0,0,0,.3);white-space:nowrap">{text}</div>', x, y, anim, "z-index:60;" + extra)


def card(inner, w, x, y, anim, rot=-1.5, bg="#FBF8F0", pad="28px 32px", z=40):
    return A(f'<div style="width:{w}px;background:{bg};padding:{pad};box-shadow:0 20px 36px rgba(0,0,0,.4);transform:rotate({rot}deg)">{inner}</div>', x, y, anim, f"z-index:{z}")


def kicker(t, c="#7A6A4A", s=17):
    return f'<div style="font:500 {s}px Plex;letter-spacing:4px;color:{c}">{t}</div>'


def AIL(x=60, y=960, t="AI ILLUSTRATION"):
    return "<!--TOP-->" + a(f'<div style="background:rgba(26,26,26,.88);color:{PARCH};font:500 15px Plex;letter-spacing:3px;padding:6px 10px">{t}</div>', x, y, "z-index:85") + "<!--/TOP-->"


def ring(text, anim, seed=1, pad=(16, 12), w=5):
    """A red ink circle drawn around a word, anchored to the word itself."""
    return (f'<span style="position:relative;display:inline-block">{text}<svg data-anim="wipe {anim}" viewBox="0 0 100 100" preserveAspectRatio="none" '
            f'style="position:absolute;left:-{pad[0]}px;top:-{pad[1]}px;width:calc(100% + {2 * pad[0]}px);height:calc(100% + {2 * pad[1]}px);overflow:visible;z-index:5">'
            f'<path d="{wobble(50, 50, 48, 46, seed)}" fill="none" stroke="{RED}" stroke-width="{w}" vector-effect="non-scaling-stroke" stroke-linecap="round"/></svg></span>')


def top(h):
    """Pinned above the camera push (captions that must never crop)."""
    return "<!--TOP-->" + h + "<!--/TOP-->"


def check(x, y, anim="snap .5 .5", t="TO CHECK"):
    return A(f'<div style="border:3px solid {INK};color:{INK};background:rgba(244,239,230,.9);font:500 15px Plex;letter-spacing:3px;padding:3px 9px;transform:rotate(-4deg)">{t}</div>', x, y, anim, "z-index:72")


def circle(cx, cy, rx, ry, anim, seed=1, w=6):
    return f'<svg class="a" data-anim="draw {anim}" style="left:0;top:0;z-index:66" width="1920" height="1080"><path d="{wobble(cx, cy, rx, ry, seed)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="{w}" stroke-linecap="round"/></svg>'


def sweep(x, y, w, h, anim, rot=0):
    return A(f'<div style="width:{w}px;height:{h}px;background:{SIG};opacity:.62;mix-blend-mode:multiply"></div>', x, y, f"wipe {anim}", f"z-index:45;transform:rotate({rot}deg)")


def plate(n, w, h, x, y, anim, rot=-2, pos="50% 50%", zoom=1.0):
    """An AI plate as a collage clipping: white sticker border, hard shadow."""
    return A(f'<div style="background:#fff;padding:10px;box-shadow:14px 16px 0 rgba(0,0,0,.45);transform:rotate({rot}deg)">'
             f'<div style="width:{w}px;height:{h}px;overflow:hidden"><img src="/assets/ai/B{n}.jpg" style="width:{w * zoom:.0f}px;height:{h * zoom:.0f}px;object-fit:cover;object-position:{pos};display:block"></div>'
             f'<div style="position:absolute;left:18px;bottom:18px;background:rgba(26,26,26,.88);color:{PARCH};font:500 13px Plex;letter-spacing:3px;padding:4px 8px">AI ILLUSTRATION</div></div>', x, y, anim, "z-index:30")


def full(n, pos="50% 50%", s=1.0):
    return a(f'<img src="/assets/ai/B{n}.jpg" style="width:1920px;height:1080px;object-fit:cover;object-position:{pos};display:block;transform:scale({s});transform-origin:{pos}">', 0, 0)


CRED = json.loads((D / "data" / "photo_credits.json").read_text())


def credit(key):
    c = CRED[key]
    return f"PHOTO: '{c['title']}' BY {c['author']} ({c['licence']}, VIA {c['via']})".upper()


def photo(key, w, h, x, y, anim, rot=-2, pos="50% 50%", grade="sepia(.18) contrast(1.05) saturate(.85)", cap=None):
    """A real, licensed photo as a collage clipping: white border, hard shadow, halftone, a caption chip."""
    f = CRED[key]["file"]
    capd = (f'<div style="position:absolute;left:18px;bottom:18px;background:rgba(244,239,230,.95);color:{INK};font:500 13px Plex;letter-spacing:2px;padding:4px 8px;max-width:{w - 40}px">{cap}</div>' if cap else "")
    return A(f'<div style="position:relative;background:#fff;padding:10px;box-shadow:14px 16px 0 rgba(0,0,0,.45)">'
             f'<div style="width:{w}px;height:{h}px;overflow:hidden;position:relative"><img src="/{f}" style="width:{w}px;height:{h}px;object-fit:cover;object-position:{pos};display:block;filter:{grade}">'
             f'<div style="position:absolute;inset:0;background-image:radial-gradient(rgba(26,26,26,.18) 1px,transparent 1.6px);background-size:5px 5px;mix-blend-mode:multiply"></div></div>{capd}</div>',
             x, y, anim, f"z-index:30;transform:rotate({rot}deg)")


def fullphoto(key, pos="50% 50%", grade="sepia(.15) contrast(1.05) saturate(.85)"):
    f = CRED[key]["file"]
    return a(f'<img src="/{f}" style="width:1920px;height:1080px;object-fit:cover;object-position:{pos};display:block;filter:{grade}">', 0, 0)


RW = '<svg width="52" height="34" viewBox="0 0 52 34" style="display:block"><path d="M25 3 L3 17 L25 31Z M49 3 L27 17 L49 31Z" fill="currentColor"/></svg>'
FF = '<svg width="52" height="34" viewBox="0 0 52 34" style="display:block"><path d="M3 3 L25 17 L3 31Z M27 3 L49 17 L27 31Z" fill="currentColor"/></svg>'
PLAY = '<svg width="30" height="34" viewBox="0 0 30 34" style="display:block"><path d="M3 3 L27 17 L3 31Z" fill="currentColor"/></svg>'


def stamp(seq, mode="rw", sub=None, frozen=False):
    """The crimson date stamp (top-left, all film). seq: [(text, t_start, t_end)] shown in turn (the spin), the last one stays."""
    ic = {"rw": RW, "ff": FF, "play": PLAY, None: ""}[mode]
    out = ""
    for i, (t, s, e) in enumerate(seq):
        last = i == len(seq) - 1
        bg = RED if frozen and last else "rgba(244,239,230,.94)"
        fg = PARCH if frozen and last else RED
        out += (f'<div class="a" data-win="{s} {9 if last else e}" style="left:56px;top:40px;z-index:88;display:flex;align-items:center;gap:14px;'
                f'border:5px solid {RED};background:{bg};color:{fg};padding:8px 20px 6px;transform:rotate(-2.5deg);box-shadow:0 6px 12px rgba(0,0,0,.3)">'
                f'{ic}<div style="font:400 58px/1 Anton;letter-spacing:3px">{t}</div></div>')
    if sub:
        out += a(f'<div style="font:500 15px Plex;letter-spacing:3px;color:{PARCH};background:rgba(26,26,26,.85);padding:4px 10px">{sub}</div>', 62, 140, "z-index:88")
    return "<!--TOP-->" + out + "<!--/TOP-->"


def tickit(t):
    return f'<span style="display:inline-block;width:26px;height:26px;border:3px solid {INK};margin-right:12px;vertical-align:-4px;text-align:center;font:400 22px/22px Anton">✓</span>{t}'


# ---- the light table and the relief ------------------------------------------------------------------------------------
PINS = {"ANTOFAGASTA": (-70.40, -23.65), "CALAMA": (-68.93, -22.46), "TOPÁTER": (-68.93, -22.46), "ARICA": (-70.31, -18.48),
        "LA PAZ": (-68.15, -16.50), "LAKE TITICACA": (-69.35, -15.85), "ILO": (-71.34, -17.64), "TIQUINA": (-68.85, -16.22)}


def _strip_poly():
    c = [P(x, y) for x, y in S["coast_litoral"]]
    inland = [P(x + 1.25, y) for x, y in S["coast_litoral"]][::-1]
    pts = c + inland
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z", "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in c), c[0]


STRIP, COAST, NORTH = _strip_poly()


def strip_svg(state, z, when=(0, 0)):
    """The lost Litoral coast as a separate paper strip (schematic band, ~21-25 S). state: flat | taped | lift | peel | beside.
    The strip moves from its place on the coast to `state` over the shot window `when` (s, e): an animated peel."""
    sw = lambda w: w / z
    nx, ny = NORTH
    dx, dy, r = {"flat": (0, 0, 0), "taped": (0, 0, 0), "lift": (-6, -16, -4), "peel": (-230, -150, -14), "beside": (-330, 40, -7)}[state]
    ghost = (f'<svg class="a" style="left:0;top:0;z-index:4" width="{MW}" height="{MH}"><path d="{STRIP}" fill="rgba(26,26,26,.10)" stroke="{INK}" stroke-width="{sw(2):.2f}" stroke-dasharray="{sw(8):.1f} {sw(6):.1f}"/></svg>'
             if state in ("lift", "peel", "beside") else "")
    blur = {"flat": 3, "taped": 3, "lift": 8, "peel": 22, "beside": 6}[state]
    return (ghost + f'<svg class="a" data-peel="{dx} {dy} {r} {when[0]} {when[1]}" style="left:0;top:0;overflow:visible;z-index:5;transform-origin:{nx:.0f}px {ny:.0f}px;'
            f'filter:drop-shadow({blur / 2:.0f}px {blur:.0f}px {blur / 1.5:.0f}px rgba(0,0,0,.45))" width="{MW}" height="{MH}">'
            f'<path d="{STRIP}" fill="rgba(247,242,232,.8)" stroke="{INK}" stroke-width="{sw(1.5):.2f}"/>'
            f'<path d="{COAST}" fill="none" stroke="{TEAL}" stroke-width="{sw(7):.1f}" stroke-linecap="round"/></svg>')


def table(lon, lat, z, sx=960, sy=560, rivers=False, strip="flat", bolivia=True, panel=True, extra_map="", when=(0, 0)):
    """The cartographer's light table with the relief map placed so (lon, lat) sits at screen (sx, sy) at zoom z.
    Returns (html, proj) where proj(lon, lat) gives screen pixels."""
    mx, my = P(lon, lat)
    L, T = sx - mx * z, sy - my * z
    pr = lambda lo, la: (L + P(lo, la)[0] * z, T + P(lo, la)[1] * z)
    sw = lambda w: f"{w / z:.2f}"
    C = S["countries"]
    fade = "".join(f'<path d="{C[n]}" fill="rgba(244,239,230,.55)"/>' for n in ("Brazil", "Paraguay", "Ecuador", "Colombia", "Uruguay"))
    lines = "".join(f'<path d="{C[n]}" fill="none" stroke="{INK}" stroke-width="{sw(1.6)}" stroke-linejoin="round" opacity=".75"/>' for n in ("Chile", "Peru", "Argentina", "Brazil", "Paraguay"))
    bol = f'<path d="{C["Bolivia"]}" fill="rgba(26,26,26,.05)" stroke="{INK}" stroke-width="{sw(3.6)}" stroke-linejoin="round"/>' if bolivia else ""
    lake = f'<path d="{S["lakes"]["Titicaca"]}" fill="{TEAL}" stroke="{TEAL}" stroke-width="{sw(1.5)}"/>'
    riv = "".join(f'<path d="{d}" fill="none" stroke="{TEAL}" stroke-width="{sw(3.2)}" stroke-linecap="round" pathLength="1"/>' for d in S["rivers"].values()) if rivers else ""
    svg = (f'<svg class="a" style="left:0;top:0" width="{MW}" height="{MH}">{fade}{lines}{bol}{lake}</svg>'
           + (f'<svg class="a" data-anim="draw .1 .55" style="left:0;top:0" width="{MW}" height="{MH}">{riv}</svg>' if rivers else ""))
    pan = ""
    if panel:
        pw, ph = MW * z, MH * z
        pan = (a(f'<div style="width:{pw + 120:.0f}px;height:{ph + 120:.0f}px;background:radial-gradient(ellipse at 50% 50%,#FFFDF6 0%,#F6EEDC 70%,#E8DCC0 100%);'
                 f'box-shadow:0 0 160px 40px rgba(255,240,205,.28),inset 0 0 40px rgba(0,0,0,.12);border-radius:10px"></div>', L - 60, T - 60))
    m = (f'<div class="a" style="left:{L:.1f}px;top:{T:.1f}px;width:{MW}px;height:{MH}px;transform:scale({z});transform-origin:0 0;box-shadow:0 0 0 {6 / z:.1f}px #fff,0 {12 / z:.0f}px {30 / z:.0f}px rgba(0,0,0,.35)">'
         f'<img src="/maps/relief.png" style="width:{MW}px;height:{MH}px;display:block">{svg}'
         + (strip_svg(strip, z, when) if strip else "") + extra_map + '</div>')
    return a(f'<div style="width:1920px;height:1080px;background:{DESKC};background-image:radial-gradient(rgba(255,255,255,.035) 1px,transparent 1.5px);background-size:5px 5px"></div>', 0, 0) + pan + m, pr


def pin(pr, name, text=None, side=1, anim="drop 0 .08", dy=-16, size=18):
    x, y = pr(*PINS[name])
    p = A(f'<svg width="40" height="56" viewBox="0 0 40 56" style="display:block;filter:drop-shadow(3px 5px 3px rgba(0,0,0,.45))"><path d="M20 22 L20 54" stroke="#555" stroke-width="3"/>'
          f'<circle cx="20" cy="16" r="13" fill="{RED}" stroke="#fff" stroke-width="2.5"/><circle cx="16" cy="12" r="4" fill="rgba(255,255,255,.55)"/></svg>', x - 20, y - 54, anim, "z-index:62")
    if text is None:
        text = name
    k, s0, e0 = anim.split()
    lab = "" if text == "" else A(f'<div style="background:{PARCH};padding:4px 10px;font:500 {size}px Plex;letter-spacing:3px;color:{INK};box-shadow:0 6px 10px rgba(0,0,0,.35);white-space:nowrap;'
                                    f'{"" if side > 0 else "transform:translateX(-100%)"}">{text}</div>', x + (22 if side > 0 else -22), y + dy - 40, f"fade {e0} {float(e0) + .04:.2f}", "z-index:61")
    return p + lab


def string(pts, anim="draw .2 .5", dash=False, w=4):
    d = "M" + " Q".join([f"{pts[0][0]:.0f} {pts[0][1]:.0f}"] + [f"{(p[0] + q[0]) / 2:.0f} {(p[1] + q[1]) / 2 + 30:.0f} {q[0]:.0f} {q[1]:.0f}" for p, q in zip(pts, pts[1:])])
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:58" width="1920" height="1080"><path d="{d}" pathLength="1" fill="none" stroke="{RED}" stroke-width="{w}"'
            f' stroke-linecap="round" {"stroke-dasharray=\"0.02 0.015\"" if dash else ""} style="filter:drop-shadow(2px 3px 2px rgba(0,0,0,.35))"/></svg>')


def route(pts, anim="draw .2 .6", col=RED, w=5):
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:57" width="1920" height="1080"><mask id="m{abs(hash(d)) % 9999}"><path d="{d}" pathLength="1" fill="none" stroke="#fff" stroke-width="{w + 4}"/></mask>'
            f'<path d="{d}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/></svg>')


def dashed(pts, anim="draw .2 .6", col=RED, w=5):
    """A dashed route that draws on: a dashed line revealed by a growing mask."""
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    k = abs(hash(d)) % 99999
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:57" width="1920" height="1080"><defs><mask id="mk{k}" maskUnits="userSpaceOnUse"><path d="{d}" pathLength="1" fill="none" stroke="#fff" stroke-width="{w + 10}"/></mask></defs>'
            f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-dasharray="16 12" stroke-linecap="round" mask="url(#mk{k})"/></svg>')


def country_labels(pr, which=("BOLIVIA", "CHILE", "PERU", "ARGENTINA"), size=26, at=None):
    pos = {"BOLIVIA": (-64.6, -16.2), "CHILE": (-70.9, -27.6), "PERU": (-75.0, -10.5), "ARGENTINA": (-63.5, -26.8), "BRAZIL": (-58.5, -10.5),
           "PARAGUAY": (-59.2, -22.6), "PACIFIC OCEAN": (-76.5, -23.5)}
    pos.update(at or {})
    out = ""
    for n in which:
        x, y = pr(*pos[n])
        if n == "PACIFIC OCEAN":
            out += a(f'<div style="font:400 {size + 6}px ISerif;color:{PARCH};letter-spacing:4px;white-space:nowrap;transform:translate(-50%,-50%)">Pacific Ocean</div>', x, y, "z-index:50")
        else:
            out += a(f'<div style="font:400 {size}px Anton;color:{INK};letter-spacing:8px;white-space:nowrap;transform:translate(-50%,-50%);text-shadow:0 0 6px #F4EFE6,0 0 12px #F4EFE6">{n}</div>', x, y, "z-index:50")
    return out


# ======================================================================================================================
# 1 · HOOK AND QUESTION (date stamp: 2026)
# ======================================================================================================================
put("01_navy", page(
    full(1, "50% 60%")
    + top(A(f'<div style="font:400 120px/0.95 Anton;color:{INK};letter-spacing:2px">THIS IS<br>A NAVY.</div>', 70, 200, "slam .05 .08", "z-index:40"))
    + A(f'<div style="width:330px;background:rgba(244,239,230,.94);padding:20px 24px;box-shadow:0 18px 30px rgba(0,0,0,.35);border-left:8px solid {INK}">'
        + kicker("ALTITUDE", INK)
        + f'<div style="display:flex;align-items:baseline;gap:8px;margin-top:6px"><span data-anim="count .35 .85" data-to="3810" style="font:400 92px/1 Anton;color:{INK}">3,810</span><span style="font:400 44px Anton;color:{INK}">M</span></div>'
        + f'<div style="height:240px;margin-top:10px;position:relative;border-left:3px solid {INK}">'
        + "".join(f'<div style="position:absolute;left:0;top:{240 - k * 60}px;width:{18 if k % 2 == 0 else 10}px;border-top:3px solid {INK}"></div>'
                  f'<div style="position:absolute;left:26px;top:{228 - k * 60}px;font:500 16px Plex;color:#444">{k * 1000:,} M</div>' for k in range(0, 4))
        + f'<div data-anim="grow .35 .85" style="position:absolute;left:-14px;bottom:0;width:10px;height:229px;background:{INK}"></div></div>'
        + f'<div style="font:500 15px Plex;letter-spacing:2px;color:#444;margin-top:14px">LAKE TITICACA · PERU–BOLIVIA</div></div>', 1530, 190, "up .25 .35", "z-index:40")
    + A(f'<div style="font:700 58px/1 Caveat;color:{INK};background:rgba(244,239,230,.9);padding:6px 16px;transform:rotate(-2deg)">"Look at the altitude."</div>', 1050, 900, "fade .3 .4", "z-index:40")
    + tag("SEA LEVEL: NOT APPLICABLE", 1090, 800, -2, "snap .9 .9")
    + stamp([("2026", 0, 9)], None) + AIL(70, 950),
    "BOAT: " + AISRC + " · ALTITUDE: BRITANNICA ~3,810 M (WIKIPEDIA 3,812 M), HIGHEST LAKE NAVIGABLE BY LARGE VESSELS · NO FLAGS, NO FACES", cam=(1.08, 1.0)))

# the receipt: a studio reconstruction (no scan yet) of the 1904 treaty, Art. II
bar = lambda w, o=.22: f'<div style="height:14px;width:{w}%;background:rgba(60,45,25,{o});margin:12px 0;border-radius:3px"></div>'
treaty_doc = (
    f'<div style="width:820px;height:900px;box-sizing:border-box;padding:60px 70px;background:{OLD};background-image:radial-gradient(ellipse at 20% 15%,rgba(150,110,50,.16),transparent 45%),'
    f'radial-gradient(ellipse at 85% 90%,rgba(140,100,40,.2),transparent 40%),linear-gradient(180deg,rgba(255,255,255,.2),rgba(120,90,40,.12));'
    f'box-shadow:0 30px 60px rgba(0,0,0,.6),inset 0 0 60px rgba(120,85,30,.25);color:#2A2118;position:relative">'
    f'<div style="text-align:center;font:400 34px/1.15 PlayR;letter-spacing:3px">TRATADO DE PAZ Y AMISTAD</div>'
    f'<div style="text-align:center;font:400 26px/1.3 Doc;margin-top:6px">entre las Repúblicas de Chile y Bolivia</div>'
    f'<div style="text-align:center;font:400 22px Doc;margin-top:4px;color:#5A4A35">Santiago, 20 de octubre de 1904</div>'
    f'<div style="width:120px;border-top:2px solid #5A4A35;margin:24px auto"></div>'
    f'<div style="font:400 24px Doc;letter-spacing:2px">ARTÍCULO I.</div>{bar(96)}{bar(88)}{bar(52)}'
    f'<div style="font:400 24px Doc;letter-spacing:2px;margin-top:26px">ARTÍCULO II.</div>'
    f'<div style="font:400 38px/1.42 Doc;margin-top:8px;text-align:justify">Por el presente Tratado quedan reconocidos del '
    f'{hl("dominio absoluto y")} {ring(hl("perpetuo"), ".5 .62", 4)} {hl("de Chile")} los territorios ocupados por éste en virtud del artículo 2 del Pacto de Tregua de 4 de abril de 1884.</div>'
    f'<div style="font:400 24px Doc;letter-spacing:2px;margin-top:26px">ARTÍCULO III.</div>{bar(94)}{bar(90)}{bar(70)}'
    f'<div style="position:absolute;left:70px;bottom:40px;font:500 13px Plex;letter-spacing:2px;color:#7A6A4A">OTHER ARTICLES NOT REPRODUCED · SET IN THE STUDIO FROM THE PUBLISHED SPANISH TEXT</div></div>')
put("02_receipt", page(
    full(1, "50% 60%") + a('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(26,26,26,.82) 0%,rgba(26,26,26,.7) 45%,rgba(26,26,26,.45) 100%)"></div>', 0, 0)
    + A(treaty_doc, 980, 90, "up 0 .14", "transform:rotate(1.2deg);z-index:30")
    + A(f'<div style="background:{PARCH};border:3px solid {INK};padding:10px 16px;font:500 18px/1.5 Plex;letter-spacing:3px;color:{INK};width:560px;box-shadow:8px 8px 0 rgba(0,0,0,.4);transform:rotate(-1.5deg)">'
        f'RECONSTRUCTION · TEXT OF THE 1904 TREATY, ART. II · SCAN TO BE SOURCED</div>', 120, 250, "snap .12 .12", "z-index:72")
    + A(f'<div style="font:400 78px/1.08 Anton;color:{PARCH}">"ABSOLUTE AND<br><span style="background:{SIG};color:{INK};padding:0 12px">PERPETUAL</span><br>DOMINION"</div>', 120, 440, "up .62 .74", "z-index:40")
    + A(f'<div style="font:400 34px ISerif;color:#E8DFCC;width:700px">Art. II: the coast taken in the war belongs to Chile.</div>', 124, 730, "fade .7 .8", "z-index:40")
    + tag("HEDGING: NONE DETECTED", 124, 830, -2, "snap .88 .88")
    + stamp([("2026", 0, 9)], None) + AIL(70, 950, "BACKGROUND: AI ILLUSTRATION"),
    "TEXT: TREATY OF PEACE AND FRIENDSHIP, CHILE–BOLIVIA, SANTIAGO, 20 OCT 1904, ART. II (SPANISH TEXT) · PAGE TYPESET BY THE STUDIO: A RECONSTRUCTION, NOT A SCAN · SCAN TO BE SOURCED (DIARIO OFICIAL 27 MAR 1905 / FRUS 1905) · ON-SCREEN WORDING TO MATCH THE SCAN: TO CHECK",
    cam=(1.0, 1.06), origin="72% 55%"))

# pull back: the boat on the relief, on the light table
h, pr = table(-67.5, -18.2, 0.5, 960, 540)
tx, ty = pr(*PINS["LAKE TITICACA"])
put("03_lighttable", page(
    h + country_labels(pr, ("BOLIVIA", "CHILE", "PERU", "ARGENTINA", "BRAZIL", "PARAGUAY", "PACIFIC OCEAN"), 22)
    + plate(1, 300, 170, tx - 560, ty - 60, "drop .15 .25", -3)
    + photo("titicaca", 300, 200, tx - 600, ty + 170, "drop .3 .38", 2.5, cap="LAKE TITICACA · REAL PHOTO")
    + string([(tx - 250, ty + 30), (tx, ty)], "draw .3 .4")
    + pin(pr, "LAKE TITICACA", "LAKE TITICACA · ~3,810 M", 1, "drop .25 .3")
    + card(kicker("THE HIGHEST LAKE ON EARTH THAT BIG SHIPS CAN SAIL", INK, 15) + f'<div style="font:400 64px/1 Anton;color:{INK};margin-top:8px">{hl("~3,810 M")} UP</div>', 470, 1340, 640, "up .5 .62", 1.5)
    + stamp([("2026", 0, 9)], None),
    MAPSRC + " · ALTITUDE: BRITANNICA ~3,810 M · BOAT CLIPPING: AI ILLUSTRATION (LOGGED IN DATA/AI_LEDGER.JSON) · " + credit("titicaca"), cam=(1.25, 1.0), origin="45% 30%"))

# follow this line west: no coast, Chile in between, the loose coastline strip
h, pr = table(-69.0, -20.0, 1.3, 1040, 600)
ax, ay = pr(-70.9, -23.0)
put("04_nocoast", page(
    h + country_labels(pr, ("BOLIVIA", "CHILE", "PERU", "ARGENTINA"), 30, {"BOLIVIA": (-65.8, -19.0), "ARGENTINA": (-65.5, -24.4), "PERU": (-72.0, -15.6), "CHILE": (-69.3, -24.6)})
    + pin(pr, "LA PAZ", "LA PAZ", 1, "drop .05 .1") + pin(pr, "LAKE TITICACA", "", 1, "drop .05 .1")
    + label("BOLIVIA'S COAST: 0 KM", 1270, 560, "fade .3 .4", 22, INK, PARCH)
    + A(f'<div style="background:{PARCH};border-left:8px solid {TEAL};padding:8px 14px;font:500 18px/1.4 Plex;letter-spacing:3px;color:{INK};box-shadow:0 8px 14px rgba(0,0,0,.35);width:360px">'
        f'LITORAL · A LOOSE PAPER STRIP<br><span style="font-size:15px;color:#555">APPROX. 1879 BORDER, SCHEMATIC</span></div>', ax - 560, ay - 60, "up .45 .55")
    + string([(ax - 190, ay - 20), (ax + 50, ay - 30)], "draw .5 .6")
    + top(A(f'<div style="font:400 64px/1 Anton;color:{PARCH};text-shadow:0 4px 18px rgba(0,0,0,.6);width:720px">WHY DOES A COUNTRY WITH NO SEA KEEP A NAVY ON A LAKE IN THE CLOUDS?</div>', 70, 190, "up .7 .82", "z-index:70")),
    MAPSRC + " · LITORAL STRIP: SCHEMATIC BAND ALONG THE COAST, ~21–25°S, NOT A SURVEYED BOUNDARY (HISTORICAL BOUNDARY DATA TO PICK: TO CHECK)", cam=(1.0, 1.12), origin="40% 60%"))

h, pr = table(-67.5, -18.2, 0.62, 960, 560)
put("05_title", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.55)"></div>', 0, 0)
    + A(f'<div style="width:1920px;text-align:center;font:400 150px/1.08 Anton;color:{PARCH}">WHY DOES LANDLOCKED<br>BOLIVIA HAVE A <span style="background:{SIG};color:{INK};padding:0 18px">NAVY?</span></div>', 0, 300, "slam .1 .12", "z-index:70")
    + A(f'<div style="width:1920px;text-align:center;font:400 40px ISerif;color:#E8DFCC">Run it backwards. Date by date, to the day the coast went missing.</div>', 0, 700, "fade .45 .6", "z-index:70")
    + stamp([("2026", 0, .3), ("2010", .3, .42), ("1990", .42, .54), ("1970", .54, .66), ("2026", .66, 9)], "rw"),
    MAPSRC + " · PRINT FACTS", cam=(1.0, 1.04)))

# ======================================================================================================================
# 2 · MAP AND HISTORY: THE REWIND
# ======================================================================================================================
h, pr = table(-66.5, -17.0, 0.9, 960, 560, rivers=False)
idx = lambda big, small, w=640: f'<div style="width:{w}px;height:250px;box-sizing:border-box;background:#FBF8F0;padding:26px 30px;background-image:repeating-linear-gradient(transparent 0 46px,rgba(43,108,176,.0) 46px 47px);border-top:6px solid {RED}">{kicker(small)}<div style="font:400 62px/1.05 Anton;color:{INK};margin-top:14px">{big}</div></div>'
put("06_1963", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.35)"></div>', 0, 0)
    + card(kicker("TYPED INDEX CARD · JANUARY 1963")
           + f'<div style="font:400 86px/1.02 Anton;color:{INK};margin-top:14px"><span style="position:relative">FUERZA {hl("FLUVIAL")}</span><br>Y {hl("LACUSTRE")}</div>'
           + f'<div style="font:400 34px ISerif;color:#444;margin-top:10px">River and Lake Force · 1963</div>', 720, 240, 230, "drop .08 .16", -2, z=40)
    + card(kicker("SECOND CARD · JANUARY 1966") + f'<div style="font:400 52px/1.05 Anton;color:{INK};margin-top:10px">RENAMED: FUERZA NAVAL BOLIVIANA</div>', 640, 300, 650, "drop .2 .28", 1.5, z=41)
    + A(f'<div style="position:relative;background:{TEAL};color:{PARCH};font:400 120px/1 Anton;padding:20px 40px;letter-spacing:10px;box-shadow:0 20px 30px rgba(0,0,0,.45);transform:rotate(4deg)">MAR'
        f'<svg style="position:absolute;left:-10px;top:-10px" width="300" height="180" data-anim="draw .7 .78"><path d="M10 150 L270 20" pathLength="1" stroke="{RED}" stroke-width="14" stroke-linecap="round" fill="none"/></svg></div>', 1260, 330, "drop .55 .62", "z-index:45")
    + label("NOT SEA.", 1300, 560, "snap .8 .8", 26, INK, PARCH)
    + tag("THE NAVY IS YOUNGER THAN THE PROBLEM", 1080, 820, 2, "snap .9 .9")
    + stamp([("2026", 0, .02), ("2000", .02, .04), ("JAN 1963", .04, 9)], "rw"),
    "NAVY HISTORY: WIKIPEDIA 'BOLIVIAN NAVY' (FOUNDED JAN 1963 AS FUERZA FLUVIAL Y LACUSTRE, RENAMED JAN 1966) · TO CHECK AGAINST ARMADA.MIL.BO · CARDS TYPED IN THE STUDIO · " + MAPSRC, cam=(1.0, 1.08), origin="35% 45%"))

sig_doc = (f'<div style="width:880px;box-sizing:border-box;padding:50px 64px 56px;background:{OLD};background-image:radial-gradient(ellipse at 80% 20%,rgba(150,110,50,.18),transparent 50%);'
           f'box-shadow:0 30px 60px rgba(0,0,0,.6),inset 0 0 60px rgba(120,85,30,.25);color:#2A2118">'
           f'{bar(92)}{bar(97)}{bar(64)}'
           f'<div style="font:400 30px/1.45 Doc;margin-top:24px;text-align:right">Santiago, 20 de octubre de 1904.</div>'
           f'<div style="display:flex;justify-content:space-between;margin-top:56px;font:400 34px Doc"><div>{ring("EMILIO BELLO CODESIDO", ".35 .45", 7, (16, 8))}<div style="font:500 14px Plex;letter-spacing:3px;color:#7A6A4A;margin-top:6px">FOR CHILE</div></div>'
           f'<div style="text-align:right">{ring("ALBERTO GUTIÉRREZ", ".42 .52", 3, (16, 8))}<div style="font:500 14px Plex;letter-spacing:3px;color:#7A6A4A;margin-top:6px">FOR BOLIVIA</div></div></div>'
           f'<div style="font:500 13px Plex;letter-spacing:2px;color:#7A6A4A;margin-top:30px">SIGNATURE BLOCK SET IN THE STUDIO · NAMES AND DATE FROM THE TREATY · WORDING TO MATCH THE SCAN</div></div>')
h, pr = table(-66.5, -17.0, 0.9, 960, 560)
put("07_1904", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.35)"></div>', 0, 0)
    + A(sig_doc, 160, 230, "up .05 .18", "transform:rotate(-1.2deg);z-index:30")
    + A(f'<div style="font:400 60px/1 Anton;color:{PARCH};text-align:right;width:600px">TWENTY YEARS AFTER THE SHOOTING STOPPED</div>', 1220, 250, "up .45 .58", "z-index:40")
    + tag("STATUS: ALREADY GONE · NOW IN WRITING", 1120, 820, 2, "snap .85 .85")
    + stamp([("JAN 1963", 0, .04), ("1940", .04, .07), ("20 OCT 1904", .07, 9)], "rw"),
    "TREATY OF PEACE AND FRIENDSHIP, SANTIAGO, 20 OCT 1904, SIGNED BY EMILIO BELLO CODESIDO (CHILE) AND ALBERTO GUTIÉRREZ (BOLIVIA) · SIGNATURE BLOCK TYPESET BY THE STUDIO (RECONSTRUCTION, SCAN TO BE SOURCED) · " + MAPSRC, cam=(1.0, 1.06), origin="30% 60%"))

h, pr = table(-69.3, -22.6, 1.85, 1100, 560, strip="taped")
sx1, sy1 = pr(-70.3, -22.2)
put("08_1884", page(
    h + country_labels(pr, ("BOLIVIA", "ARGENTINA", "PACIFIC OCEAN"), 30)
    + A(f'<div style="width:520px;height:70px;background:rgba(236,226,200,.92);box-shadow:0 3px 6px rgba(0,0,0,.3);font:500 20px/70px Plex;letter-spacing:4px;color:{INK};text-align:center">ADMINISTERED BY CHILE</div>',
        sx1 - 200, sy1 - 30, "drop .3 .36", "transform:rotate(-62deg);z-index:55")
    + card(kicker("PACTO DE TREGUA · VALPARAÍSO") + f'<div style="font:400 80px/1 Anton;color:{INK};margin-top:10px">4 APRIL 1884</div>'
           + f'<div style="font:400 32px/1.25 ISerif;color:#444;margin-top:10px">A truce: the fighting stops. Chile keeps running the coast it holds.</div>', 560, 80, 260, "drop .05 .14", -1.5)
    + tag("TEMPORARY (20 YEARS)", 1180, 830, 2, "snap .85 .85")
    + stamp([("20 OCT 1904", 0, .04), ("1890", .04, .08), ("4 APR 1884", .08, 9)], "rw"),
    "TRUCE (PACTO DE TREGUA), VALPARAÍSO, 4 APR 1884; THE 1904 TREATY FOLLOWED 20 YEARS LATER (SECONDARY SOURCES, SEE DOSSIER) · LITORAL STRIP SCHEMATIC, ~21–25°S · " + MAPSRC, cam=(1.0, 1.1), origin="60% 50%"))

h, pr = table(-69.6, -23.2, 2.1, 1100, 600, strip="lift", when=(.5, .7))
ax, ay = pr(*PINS["ANTOFAGASTA"])
put("09_1879", page(
    h + country_labels(pr, ("PACIFIC OCEAN",), 30)
    + dashed([(ax - 760, ay - 260), (ax - 420, ay - 150), (ax - 160, ay - 40), (ax - 6, ay - 6)], "draw .12 .4")
    + pin(pr, "ANTOFAGASTA", "ANTOFAGASTA · BOLIVIAN PORT IN 1879", 1, "drop .4 .45")
    + label("LANDING · NO RESISTANCE", ax - 700, ay - 330, "fade .2 .3", 20, INK, PARCH)
    + top(A(f'<div style="font:400 74px/1 Anton;color:{PARCH};text-shadow:0 4px 18px rgba(0,0,0,.55);width:640px">THE DAY THE COAST STARTED TO COME OFF THE MAP</div>', 70, 640, "up .65 .78", "z-index:70"))
    + label("LITORAL · APPROX. 1879 BORDER, SCHEMATIC", ax + 120, ay + 190, "fade .5 .6", 16)
    + stamp([("4 APR 1884", 0, .05), ("1883", .05, .1), ("1880", .1, .16), ("14 FEB 1879", .16, 9)], "rw"),
    "14 FEB 1879: CHILEAN FORCES OCCUPY ANTOFAGASTA WITHOUT RESISTANCE (SECONDARY SOURCES, SEE DOSSIER) · ROUTE DRAWN BY HAND, SCHEMATIC · LITORAL STRIP SCHEMATIC · " + MAPSRC, cam=(1.0, 1.1), origin="62% 58%"))

ledger = (f'<div style="width:900px;box-sizing:border-box;padding:40px 50px;background:#F3EAD3;background-image:repeating-linear-gradient(transparent 0 55px,rgba(44,122,140,.22) 55px 57px),'
          f'linear-gradient(90deg,transparent 120px,rgba(217,56,41,.35) 120px 122px,transparent 122px);box-shadow:0 30px 60px rgba(0,0,0,.55);color:#2A2118">'
          f'{kicker("LEDGER · LAW OF 14 FEBRUARY 1878 · BOLIVIA")}'
          f'<div style="font:700 52px/1.15 Caveat;margin-top:26px;padding-left:90px">{hl("10 centavos")} · per quintal</div>'
          f'<div style="font:700 52px/1.15 Caveat;padding-left:90px">on nitrate exported</div>'
          f'<div style="font:500 18px Plex;letter-spacing:2px;color:#555;margin-top:20px;padding-left:90px">COMPAÑÍA DE SALITRES Y FERROCARRIL DE ANTOFAGASTA</div>'
          f'<div style="font:500 18px Plex;letter-spacing:2px;color:#555;margin-top:6px;padding-left:90px">1 QUINTAL ≈ 46 KG</div></div>')
COIN = (f'<svg width="150" height="150" viewBox="0 0 150 150" style="filter:drop-shadow(8px 10px 0 rgba(0,0,0,.4))"><circle cx="75" cy="75" r="66" fill="#C9C1AE" stroke="#fff" stroke-width="6"/>'
        f'<circle cx="75" cy="75" r="52" fill="none" stroke="#8E8572" stroke-width="3"/><text x="75" y="92" text-anchor="middle" font-family="Anton" font-size="52" fill="{INK}">10¢</text></svg>')
h, pr = table(-66.5, -17.0, 0.9, 960, 560)
put("10_1878", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.35)"></div>', 0, 0)
    + photo("humberstone", 720, 400, 1080, 160, "drop .25 .33", 2.5, "50% 8%", cap="A NITRATE WORKS IN THE ATACAMA, TODAY: HUMBERSTONE (RUINS) · REAL PHOTO")
    + A(ledger, 110, 300, "up .02 .14", "transform:rotate(-1.5deg);z-index:35")
    + A(COIN, 1240, 600, "drop .5 .56", "z-index:46")
    + circle(1315, 675, 100, 100, ".6 .7", 9)
    + tag("PRICE: 10 CENTAVOS · TOTAL COST: SEE REST OF FILM", 760, 860, -1.5, "snap .85 .85")
    + stamp([("14 FEB 1879", 0, .06), ("1878", .06, 9)], "rw"),
    "TAX: BOLIVIAN LAW OF 14 FEB 1878, 10 CENTAVOS PER QUINTAL OF NITRATE EXPORTED BY THE CSFA (SECONDARY SOURCES) · UNIT: SPANISH QUINTAL ≈ 46 KG: TO CHECK · LEDGER WRITTEN IN THE STUDIO · " + credit("humberstone"),
    cam=(1.0, 1.07), origin="40% 50%"))

half = lambda who, line, src, bg: (f'<div style="width:760px;height:440px;box-sizing:border-box;background:{bg};padding:40px 44px">{kicker(who, INK, 22)}'
                                   f'<div style="font:400 58px/1.05 Anton;color:{INK};margin-top:22px">{line}</div><div style="font:500 15px/1.5 Plex;letter-spacing:2px;color:#555;margin-top:26px">{src}</div></div>')
h, pr = table(-66.5, -17.0, 0.9, 960, 560)
put("11_sides", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.45)"></div>', 0, 0)
    + A(f'<div style="font:400 66px/1 Anton;color:{PARCH}">WAS THE TAX FAIR? BOTH SIDES</div>', 180, 150, "fade 0 .08", "z-index:40")
    + A(half("CHILE'S SIDE", f"THE 1874 TREATY: NO NEW TAXES ON CHILEAN COMPANIES FOR {hl('25 YEARS')}", "1874 BOUNDARY TREATY · ARTICLE NUMBER TO CHECK", "#FBF8F0"), 180, 280, "wipe .1 .3", "z-index:40")
    + A(half("BOLIVIA'S SIDE", "A SOVEREIGN STATE MAY TAX ITS OWN SOIL. THIS WAS BOLIVIAN SOIL.", "BOLIVIA'S ARGUMENT, AS SUMMARISED BY HISTORIANS", "#EFE7D6"), 960, 280, "wipe .45 .65", "z-index:40")
    + a(f'<div style="width:6px;height:480px;background:{INK}"></div>', 957, 260, "z-index:41")
    + stamp([("1878", 0, 9)], "rw"),
    "1874 BOUNDARY TREATY, BOLIVIA–CHILE: TAXES ON CHILEAN PERSONS, INDUSTRIES AND CAPITAL FIXED FOR 25 YEARS (SECONDARY; ARTICLE NUMBER TO CHECK) · BOTH POSITIONS AS ARGUED, NOT A VERDICT · " + MAPSRC))

h, pr = table(-69.6, -23.2, 2.1, 1350, 560, strip="lift")
put("12_trigger", page(
    h + a('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(26,26,26,.55) 0%,rgba(26,26,26,.35) 55%,transparent 75%)"></div>', 0, 0)
    + pin(pr, "ANTOFAGASTA", "LANDING · 14 FEB 1879", 1, "drop 0 .05")
    + A(f'<div style="position:relative;width:640px;height:330px;box-sizing:border-box;background:#F3EAD3;padding:30px 40px;box-shadow:0 26px 50px rgba(0,0,0,.55);'
        f'background-image:repeating-linear-gradient(transparent 0 55px,rgba(44,122,140,.22) 55px 57px)">{kicker("LEDGER · THE COMPANY REFUSED TO PAY")}'
        f'<div style="font:700 46px/1.2 Caveat;color:#2A2118;margin-top:14px">property to be seized and auctioned</div>'
        f'<div data-anim="slam .25 .28" style="position:absolute;left:110px;top:165px"><div style="border:7px solid {RED};color:{RED};font:400 52px/1 Anton;padding:10px 20px;transform:rotate(-8deg);letter-spacing:3px;white-space:nowrap">AUCTION · 14 FEB 1879</div></div></div>', 120, 230, "up 0 .1", "z-index:40")
    + A(f'<div style="font:400 62px/1.02 Anton;color:{PARCH};width:700px">SAME DAY.<br><span style="color:{SIG}">THE TRIGGER WAS AN AUCTION.</span></div>', 124, 620, "up .5 .62", "z-index:40")
    + A(f'<div style="font:400 30px/1.3 ISerif;color:#E8DFCC;width:700px">Historians list deeper causes: nitrate and guano wealth, a secret 1873 alliance, a long-disputed border.</div>', 126, 790, "fade .65 .78", "z-index:40")
    + stamp([("1878", 0, .55), ("14 FEB 1879", .55, 9)], "rw", frozen=True),
    "CSFA REFUSED THE TAX; BOLIVIA SET AN AUCTION OF ITS PROPERTY FOR 14 FEB 1879, THE DAY CHILE OCCUPIED ANTOFAGASTA · DEEPER CAUSES PER HISTORIANS (SECONDARY, SEE DOSSIER) · " + MAPSRC, cam=(1.0, 1.06), origin="30% 50%"))

# ======================================================================================================================
# 3 · MECHANICS: FORWARD AGAIN
# ======================================================================================================================
put("13_topater", page(
    full(2, "50% 50%")
    + a(f'<div style="width:1920px;height:300px;background:linear-gradient(rgba(244,239,230,.0),rgba(26,26,26,.0))"></div>', 0, 0)
    + A(f'<div style="width:560px;background:rgba(244,239,230,.95);padding:24px 30px;box-shadow:0 18px 30px rgba(0,0,0,.4);border-left:8px solid {INK}">'
        f'{kicker("FIRST ARMED CLASH OF THE WAR", INK)}<div style="font:400 66px/1 Anton;color:{INK};margin-top:10px">EDUARDO ABAROA</div>'
        f'<div style="font:500 22px Plex;letter-spacing:3px;color:{INK};margin-top:10px">d. 23 MAR 1879 · TOPÁTER, NEAR CALAMA</div>'
        f'<div style="font:400 28px/1.3 ISerif;color:#444;margin-top:12px">A civilian, killed defending the bridge.</div></div>', 70, 640, "up .3 .45", "z-index:40")
    + A(f'<svg width="48" height="70" viewBox="0 0 48 70" style="filter:drop-shadow(3px 5px 3px rgba(0,0,0,.45))"><path d="M10 6 L10 68" stroke="#444" stroke-width="4"/><path d="M12 6 L44 14 L12 24Z" fill="{RED}" stroke="#fff" stroke-width="2"/></svg>', 1000, 290, "drop .6 .66", "z-index:45")
    + label("23 MAR", 1048, 292, "fade .62 .7", 20, RED, PARCH)
    + label("TOPÁTER · NEAR CALAMA", 1180, 220, "fade .15 .25", 20)
    + stamp([("14 FEB 1879", 0, .08), ("23 MAR 1879", .08, 9)], "play") + AIL(1600, 950),
    "BATTLE OF TOPÁTER, NEAR CALAMA, 23 MAR 1879: FIRST ARMED CLASH; EDUARDO ABAROA KILLED (SECONDARY SOURCES) · NO PORTRAIT DRAWN · BRIDGE AND SILHOUETTES: " + AISRC, cam=(1.0, 1.06), origin="60% 40%"))

h, pr = table(-67.0, -18.8, 0.68, 900, 560, strip="peel", when=(.15, .5))
put("14_peel", page(
    h + country_labels(pr, ("BOLIVIA", "CHILE", "PERU", "ARGENTINA", "BRAZIL"), 24, {"PERU": (-74.0, -11.5), "BRAZIL": (-59.0, -12.0)})
    + pin(pr, "TOPÁTER", "", 1, "drop 0 .05")
    + label("TARAPACÁ · PERU'S LOST PROVINCE", pr(-69.6, -19.9)[0] + 30, pr(-69.6, -19.9)[1] - 10, "fade .1 .2", 16)
    + label("LITORAL · APPROX. 1879 BORDER, SCHEMATIC", pr(-76.6, -26.6)[0], pr(-76.6, -26.6)[1], "fade .4 .5", 16)
    + A(f'<div style="background:{PARCH};padding:14px 22px;box-shadow:0 14px 24px rgba(0,0,0,.4);transform:rotate(-3deg);border-top:6px solid {TEAL}"><div style="font:400 54px/1 Anton;color:{INK}">{hl("~400 KM")} OF COAST</div>'
        f'<div style="font:400 54px/1 Anton;color:{INK}">~120,000 KM²</div><div style="font:500 15px Plex;letter-spacing:3px;color:#555;margin-top:8px">BOLIVIAN GOVERNMENT FIGURES</div></div>', 70, 230, "up .55 .68", "z-index:60")
    + card(kicker("TREATY OF ANCÓN · PERU–CHILE") + f'<div style="font:400 64px/1 Anton;color:{INK};margin-top:8px">{hl("20 OCT")} 1883</div>', 420, 1380, 300, "drop .62 .68", 2)
    + card(kicker("PEACE AND FRIENDSHIP · BOLIVIA–CHILE") + f'<div style="font:400 64px/1 Anton;color:{INK};margin-top:8px">{hl("20 OCT")} 1904</div>', 420, 1400, 520, "drop .7 .76", -2)
    + tag("SAME DATE · DIFFERENT DECADE", 1380, 740, 2, "snap .82 .82")
    + tag("BOLIVIA HAD A BEACH. NOW IT HAS A LAKE.", 70, 900, -1.5, "snap .92 .92")
    + stamp([("23 MAR 1879", 0, .1), ("1884", .1, 9)], "ff"),
    "LITORAL: ~400 KM OF COAST, ~120,000 KM² (BOLIVIAN GOVERNMENT FIGURES, REPORTED: TO CHECK) · STRIP SCHEMATIC, ~21–25°S, NOT A SURVEYED BOUNDARY · TREATY OF ANCÓN 20 OCT 1883 · " + MAPSRC,
    cam=(1.0, 1.05)))

h, pr = table(-69.2, -17.6, 2.0, 1150, 520)
ar, lp = pr(*PINS["ARICA"]), pr(*PINS["LA PAZ"])
rail = [ar, pr(-69.9, -18.1), pr(-69.5, -17.7), pr(-69.1, -17.3), pr(-68.7, -16.9), lp]
put("15_railway", page(
    h + country_labels(pr, ("BOLIVIA", "CHILE", "PERU"), 30, {"BOLIVIA": (-67.4, -18.4), "CHILE": (-69.6, -19.4), "PERU": (-71.2, -16.4)})
    + dashed(rail, "draw .2 .55", INK, 6)
    + pin(pr, "ARICA", "ARICA", -1, "drop .1 .15") + pin(pr, "LA PAZ", "LA PAZ", 1, "drop .5 .55") + pin(pr, "LAKE TITICACA", "", 1, "drop .5 .55")
    + label("BOLIVIAN SECTION → BOLIVIA · 15 YRS AFTER COMPLETION", 980, 900, "fade .6 .7", 18)
    + card(kicker("TAB III · ART. III") + f'<div style="font:400 40px/1.3 Doc;color:#2A2118;margin-top:10px">…unir {hl("el puerto de Arica con el Alto de La Paz")} por un ferrocarril…</div>'
           + f'<div style="font:500 15px Plex;letter-spacing:2px;color:#555;margin-top:12px">BUILT BY CHILE, AT ITS OWN EXPENSE</div>', 560, 70, 200, "up 0 .12", -1.5, OLD)
    + card(kicker("TAB IV · ART. IV") + f'<div style="font:400 72px/1 Anton;color:{INK};margin-top:10px">{ring("£300,000", ".82 .9", 3, (22, 10))}</div><div style="font:500 17px Plex;letter-spacing:2px;color:#555;margin-top:8px">STERLING · TWO INSTALMENTS OF £150,000</div>', 440, 120, 640, "up .7 .8", 1.5, OLD)
    + stamp([("1884", 0, .08), ("1904", .08, 9)], "ff"),
    "1904 TREATY ART. III (ARICA–ALTO DE LA PAZ RAILWAY, BOLIVIAN SECTION TO BOLIVIA 15 YEARS AFTER COMPLETION) AND ART. IV (£300,000 IN TWO INSTALMENTS) · LINES QUOTED FROM THE PUBLISHED TEXT, SET IN THE STUDIO · RAIL LINE DRAWN SCHEMATICALLY · " + MAPSRC,
    cam=(1.0, 1.06), origin="65% 45%"))

art = lambda n, body, w=780: (f'<div style="width:{w}px;box-sizing:border-box;padding:40px 48px;background:{OLD};background-image:radial-gradient(ellipse at 80% 20%,rgba(150,110,50,.18),transparent 50%);'
                              f'box-shadow:0 26px 50px rgba(0,0,0,.6),inset 0 0 50px rgba(120,85,30,.22);color:#2A2118"><div style="font:400 26px Doc;letter-spacing:2px">ARTÍCULO {n}.</div>'
                              f'<div style="font:400 38px/1.4 Doc;margin-top:10px">{body}</div></div>')
h, pr = table(-66.5, -17.0, 0.9, 960, 560)
put("16_forever", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.5)"></div>', 0, 0)
    + A(art("II", "…quedan reconocidos del dominio absoluto y " + ring("perpetuo", ".4 .5", 2) + " de Chile los territorios ocupados…"), 120, 210, "up 0 .12", "transform:rotate(-1.5deg);z-index:30")
    + A(art("VI", "…reconoce en favor de Bolivia, " + ring("a perpetuidad", ".55 .65", 8) + ", el más amplio y libre derecho de tránsito comercial por su territorio y puertos del Pacífico."), 1000, 260, "up .15 .27", "transform:rotate(1.5deg);z-index:30")
    + A(f'<div style="font:400 30px Plex;letter-spacing:4px;color:{PARCH};width:780px">FOR CHILE: THE LAND</div>', 140, 560, "fade .45 .5", "z-index:40")
    + A(f'<div style="font:400 30px Plex;letter-spacing:4px;color:{PARCH};width:780px">FOR BOLIVIA: THE PASSAGE ACROSS IT</div>', 1020, 640, "fade .6 .65", "z-index:40")
    + A(f'<div style="font:400 110px/1 Anton;color:{PARCH};width:1920px;text-align:center">THE TREATY USES <span style="background:{SIG};color:{INK};padding:0 14px">FOREVER</span> TWICE</div>', 0, 800, "slam .78 .8", "z-index:60")
    + stamp([("1904", 0, 9)], "ff"),
    "1904 TREATY, ART. II ('DOMINIO ABSOLUTO Y PERPETUO') AND ART. VI ('A PERPETUIDAD, EL MÁS AMPLIO Y LIBRE DERECHO DE TRÁNSITO COMERCIAL…') · LINES SET IN THE STUDIO FROM THE PUBLISHED TEXT (RECONSTRUCTION; WORDING TO MATCH THE SCAN: TO CHECK)"))

HOUSE = (f'<svg width="560" height="520" viewBox="0 0 560 520"><defs><pattern id="ht" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4.5" cy="4.5" r="2" fill="rgba(26,26,26,.28)"/></pattern></defs>'
         f'<g style="filter:drop-shadow(14px 16px 0 rgba(0,0,0,.5))"><path d="M30 230 L280 30 L530 230 L530 500 L30 500Z" fill="#fff"/>'
         f'<path d="M48 236 L280 52 L512 236 L512 484 L48 484Z" fill="#EDE5D3"/><path d="M48 236 L280 52 L512 236 L512 484 L48 484Z" fill="url(#ht)"/>'
         f'<rect x="110" y="300" width="110" height="100" fill="{PARCH}" stroke="{INK}" stroke-width="5"/><path d="M165 300 V400 M110 350 H220" stroke="{INK}" stroke-width="4"/>'
         f'<rect x="330" y="320" width="100" height="164" fill="#B9AE98" stroke="{INK}" stroke-width="5"/><circle cx="412" cy="404" r="7" fill="{INK}"/>'
         f'<path d="M48 236 L280 52 L512 236" fill="none" stroke="{INK}" stroke-width="7"/></g></svg>')
HALL = (f'<svg width="900" height="260" viewBox="0 0 900 260"><g style="filter:drop-shadow(14px 16px 0 rgba(0,0,0,.5))"><path d="M0 40 L900 0 L900 260 L0 220Z" fill="#fff"/>'
        f'<path d="M14 52 L886 16 L886 244 L14 210Z" fill="#E3D9C3"/><path d="M14 52 L886 16 L886 244 L14 210Z" fill="url(#ht)"/>'
        + "".join(f'<path d="M{x} {52 - x * .041:.0f} L{x} {210 + x * .038:.0f}" stroke="rgba(26,26,26,.35)" stroke-width="3"/>' for x in range(120, 880, 120))
        + f'<path d="M14 130 L886 130" stroke="rgba(26,26,26,.25)" stroke-width="3" stroke-dasharray="20 16"/></g></svg>')
put("17_hallway", page(
    a(f'<div style="width:1920px;height:1080px;background:{PARCH}"></div>', 0, 0)
    + A(HOUSE, 160, 300, "drop .05 .1")
    + A(HALL, 700, 560, "drop .35 .4")
    + label("THE HOUSE · SOLD", 220, 250, "snap .12 .12", 22, INK, PARCH)
    + A(f'<div style="display:flex;align-items:center;gap:0;transform:rotate(-3deg)"><div style="background:{SIG};color:{INK};font:400 64px/1 Anton;padding:14px 24px;box-shadow:8px 8px 0 rgba(0,0,0,.4);letter-spacing:3px">YOURS FOREVER</div>'
        f'<svg width="90" height="150" viewBox="0 0 90 150" style="margin-left:-10px;margin-top:120px"><path d="M20 0 Q 30 80 45 130 M15 100 L45 140 L75 100" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/></svg></div>', 900, 300, "slam .55 .58", "z-index:60")
    + label("THE HALLWAY", 1450, 850, "snap .45 .45", 22, INK, PARCH)
    + A(f'<div style="font:400 40px/1.25 ISerif;color:{INK};width:720px">Like selling your house and getting, in writing, eternal rights to the hallway.</div>', 1080, 150, "fade .65 .75")
    + tag("ILLUSTRATION · STUDIO CUT-OUT", 120, 900, -1.5, "snap .02 .02", 16)
    + tag("TO BE FAIR TO THE HALLWAY: IT'S A BUSY ONE", 700, 900, 1.5, "snap .9 .9")
    + stamp([("1904", 0, 9)], "ff"),
    "ILLUSTRATION (STUDIO CUT-OUT, NOT A REAL PLACE): THE 1904 TREATY'S ART. II (LAND, 'PERPETUO') VS ART. VI (TRANSIT, 'A PERPETUIDAD') · OUR SIMILE, NOT A LEGAL READING", cam=(1.0, 1.04)))

put("18_arica", page(
    fullphoto("arica", "50% 60%") + a('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(244,239,230,.96) 0%,rgba(244,239,230,.93) 38%,rgba(244,239,230,0) 55%)"></div>', 0, 0)
    + A(f'<div style="font:400 72px/0.98 Anton;color:{INK};width:680px">THE RAILWAY OPENS · {hl("1913")}</div>', 80, 170, "up .02 .12", "z-index:40")
    + photo("rail", 520, 264, 1180, 140, "drop .08 .18", 2, cap="FCALP LOCOMOTIVE · ARICA–LA PAZ RAILWAY · HISTORIC PHOTO, DATE TO CHECK")
    + A(f'<div style="width:660px">{kicker("BOLIVIAN SHARE OF CARGO THROUGH ARICA PORT · 2023", INK, 16)}'
        f'<div style="position:relative;height:90px;margin-top:16px;background:#C8C2B6"><div data-anim="wipe .3 .6" style="position:absolute;left:0;top:0;bottom:0;width:76%;background:{SIG}"></div>'
        f'<div style="position:absolute;left:0;top:-6px;bottom:-6px;border-left:4px solid {INK}"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font:500 16px Plex;color:#444;margin-top:8px"><span>0%</span><span>100%</span></div>'
        f'<div style="display:flex;align-items:center;gap:30px"><div style="font:400 120px/1 Anton;color:{INK};margin-top:8px">~<span data-anim="count .3 .6" data-to="76">76</span>%</div>'
        f'<div style="border:3px solid {INK};font:500 15px Plex;letter-spacing:3px;padding:3px 9px;transform:rotate(-4deg)">REPORTED · TO CHECK</div></div>'
        f'<div style="font:400 30px ISerif;color:#444">about three-quarters of what moves through the port is Bolivian</div></div>', 80, 330, "fade .2 .3", "z-index:40")
    + top(label("ARICA PORT, CHILE · REAL PHOTO, 2008", 1420, 960, "fade 0 .05", 14))
    + tag("ACCESS: YES · OWNERSHIP: NO", 80, 880, -1.5, "snap .88 .88")
    + stamp([("1904", 0, .1), ("1913", .1, .5), ("2023", .5, 9)], "ff"),
    "RAILWAY INAUGURATED 1913 (MEMORIA CHILENA; EXACT DATE TO CHECK) · CARGO: PUERTO ARICA VIA MUNDOMARÍTIMO, 2023, ~76% BOLIVIAN (REPORTED; REFRESH: TO CHECK) · BAR FROM ZERO · "
    + credit("rail") + " · " + credit("arica"), cam=(1.0, 1.05), origin="20% 50%"))

pos = lambda who, lines, src, bg, top: (f'<div style="width:700px;box-sizing:border-box;background:{bg};padding:36px 42px;border-top:10px solid {top}">{kicker(who, INK, 22)}'
                                        + "".join(f'<div data-anim="snap {s} {s}" style="font:400 52px/1.15 Anton;color:{INK};margin-top:14px">{tickit(l)}</div>' for l, s in lines)
                                        + f'<div style="font:500 15px/1.5 Plex;letter-spacing:2px;color:#555;margin-top:24px">SOURCE: {src}</div></div>')
h, pr = table(-66.5, -17.0, 0.9, 960, 560)
put("19_positions", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.45)"></div>', 0, 0)
    + A(pos("CHILE'S POSITION", (("VALID TREATY", .15), ("RATIFIED", .22), ("TRANSIT GRANTED", .29)), "CHILE'S ICJ PRELIMINARY OBJECTION (WRITTEN PLEADING 15 JUL 2014)", "#FBF8F0", INK), 150, 200, "up 0 .1", "transform:rotate(-1.5deg);z-index:40")
    + A(pos("BOLIVIA'S POSITION", (("SIGNED AFTER DEFEAT", .55), ("UNDER PRESSURE", .62), ("UNJUST", .69)), "BOLIVIAN GOVERNMENT (ATTRIBUTED), INCL. CLAIMS THAT CHILE BREACHES ART. VI", "#EFE7D6", INK), 1070, 240, "up .4 .5", "transform:rotate(1.5deg);z-index:40")
    + A(f'<div style="font:400 140px/1 Anton;color:{RED};text-shadow:0 6px 18px rgba(0,0,0,.5)">?</div>', 920, 720, "pop .8 .86", "z-index:50")
    + A(f'<div style="background:{PARCH};padding:10px 18px;font:500 20px Plex;letter-spacing:3px;color:{INK};box-shadow:0 8px 14px rgba(0,0,0,.4)">ART. VI · "LIBRE"? BOTH SIDES DISPUTE IT</div>', 700, 880, "fade .82 .9", "z-index:50")
    + stamp([("1904", 0, .5), ("TODAY", .5, 9)], "ff"),
    "CHILE: 1904 TREATY VALID, FREELY CONCLUDED, RATIFIED, TRANSIT HONOURED (CHILE'S OWN FILING; DATE TO CHECK) · BOLIVIA: IMPOSED AFTER DEFEAT, UNJUST (ATTRIBUTED TO THE BOLIVIAN GOVERNMENT) · BOTH SHOWN, NO VERDICT · " + MAPSRC))

# ======================================================================================================================
# 4 · STAKES: WHAT A NAVY DOES AT 3,800 M
# ======================================================================================================================
def _arc(r0, r1, a0, a1):
    p = lambda r, t: f"{95 + r * math.cos(math.radians(t)):.1f} {95 + r * math.sin(math.radians(t)):.1f}"
    return f"M{p(r1, a0)} A{r1} {r1} 0 0 1 {p(r1, a1)} L{p(r0, a1)} A{r0} {r0} 0 0 0 {p(r0, a0)}Z"


RING = (f'<svg width="190" height="190" viewBox="0 0 190 190" style="filter:drop-shadow(10px 12px 0 rgba(0,0,0,.45))">'
        f'<path d="M95 3 A92 92 0 1 1 94.9 3Z M95 47 A48 48 0 1 0 95.1 47Z" fill="#fff" fill-rule="evenodd"/>'
        f'<path d="M95 11 A84 84 0 1 1 94.9 11Z M95 55 A40 40 0 1 0 95.1 55Z" fill="{PARCH}" fill-rule="evenodd"/>'
        + "".join(f'<path d="{_arc(40, 84, a0, a0 + 40)}" fill="{INK}" opacity=".85"/>' for a0 in (0, 90, 180, 270))
        + '</svg>')
h, pr = table(-64.5, -15.2, 1.0, 900, 560, rivers=True, strip="beside")
tq = pr(*PINS["TIQUINA"])
put("20_rivers", page(
    h + country_labels(pr, ("BOLIVIA", "PERU", "BRAZIL", "PARAGUAY"), 26, {"PERU": (-71.5, -13.0)})
    + pin(pr, "TIQUINA", "TIQUINA · MAIN LAKE BASE", -1, "drop .55 .6")
    + photo("tiquina", 380, 250, tq[0] - 470, tq[1] + 70, "drop .6 .68", -2, cap="STRAIT OF TIQUINA · REAL PHOTO")
    + label("~5,000 PERSONNEL · REPORTED", tq[0] - 380, tq[1] + 10, "fade .6 .66", 18, INK, PARCH)
    + "".join(label(t, x, y, f"drop {s} {s + .05}", 20, PARCH, INK, f"border-left:8px solid {TEAL}") for t, x, y, s in (("PATROL & SMUGGLING", 1040, 300, .3), ("SUPPLIES", 1150, 470, .38), ("FLOOD RESCUE", 1020, 640, .46)))
    + dashed([(tq[0] + 10, tq[1] + 10), (1300, 760), (1600, 820), (1950, 860)], "draw .66 .8", INK, 5)
    + label("TRAINING ABROAD · REPORTED (E.G. ARGENTINA)", 1180, 900, "fade .75 .8", 16)
    + A(RING, 1600, 640, "drop .82 .86", "z-index:62")
    + tag("SALT WATER: BORROWED", 1430, 560, 2, "snap .9 .9")
    + label("SWIM RING: ILLUSTRATION", 1560, 840, "fade .82 .86", 13)
    + check(560, 960, "snap .6 .6", "~5,000 · TRAINING ABROAD: TO CHECK")
    + stamp([("TODAY", 0, 9)], "ff"),
    "ROLES: WIRED 2018, NBC NEWS/AP 2007 (REPORTED) · TIQUINA BASE: WIKIPEDIA, AVAUNT · ~5,000 PERSONNEL AND TRAINING ON ARGENTINE SHIPS: REPORTED, TO CHECK · RIVERS: NATURAL EARTH · " + credit("tiquina") + " · " + MAPSRC, cam=(1.0, 1.05), origin="60% 50%"))

CHAIR = (f'<svg width="200" height="300" viewBox="0 0 200 300" style="filter:drop-shadow(12px 14px 0 rgba(0,0,0,.45))"><path d="M40 10 h120 v150 h-120z M30 160 h140 v24 h-140z M40 184 v110 M160 184 v110 M44 260 h112" '
         f'fill="#fff" stroke="#fff" stroke-width="18" stroke-linejoin="round"/><path d="M40 10 h120 v150 h-120z" fill="#B48A5A" stroke="{INK}" stroke-width="6"/><path d="M30 160 h140 v24 h-140z" fill="#9C7449" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M40 184 v110 M160 184 v110 M44 260 h112" stroke="{INK}" stroke-width="10"/></svg>')
CAL = (f'<div style="width:250px;background:#fff;box-shadow:10px 12px 0 rgba(0,0,0,.4);text-align:center"><div style="background:{INK};color:{PARCH};font:500 22px Plex;letter-spacing:6px;padding:10px">MARCH</div>'
       f'<div style="font:400 150px/1.1 Anton;color:{INK};position:relative">23</div></div>')
put("21_diadelmar", page(
    full(5, "50% 50%")
    + a('<div style="width:1920px;height:230px;background:linear-gradient(rgba(244,239,230,.9),rgba(244,239,230,0))"></div>', 0, 0)
    + A(CHAIR, 1430, 560, "slam .55 .58", "z-index:40")
    + A(CAL, 1560, 170, "drop .02 .1", "transform:rotate(3deg);z-index:42")
    + A(f'<svg width="48" height="70" viewBox="0 0 48 70" style="filter:drop-shadow(3px 5px 3px rgba(0,0,0,.45))"><path d="M10 6 L10 68" stroke="#444" stroke-width="4"/><path d="M12 6 L44 14 L12 24Z" fill="{RED}" stroke="#fff" stroke-width="2"/></svg>', 1760, 150, "drop .1 .16", "z-index:44")
    + A(f'<div style="background:rgba(244,239,230,.95);padding:20px 28px;box-shadow:0 16px 28px rgba(0,0,0,.35);border-left:8px solid {INK}">{kicker("EVERY 23 MARCH · THE DATE OF TOPÁTER", INK)}'
        f'<div style="font:400 84px/1 Anton;color:{INK};margin-top:8px">DÍA DEL MAR</div><div style="font:400 32px ISerif;color:#444">The Day of the Sea · Plaza Abaroa, La Paz</div></div>', 70, 250, "up .15 .28", "z-index:40")
    + tag("GUEST OF HONOUR: THE PACIFIC · RSVP: NO", 940, 900, -1.5, "snap .82 .82")
    + label("CHAIR: ILLUSTRATION", 1450, 520, "fade .58 .62", 13)
    + stamp([("TODAY", 0, 9)], "ff") + AIL(70, 950),
    "DÍA DEL MAR: EVERY 23 MARCH, CLOSING A SEMANA DEL MAR; MAIN CEREMONY AT PLAZA ABAROA, LA PAZ; THE NAVY MARCHES (SECONDARY, SEE DOSSIER; CONFIRM 2026 DATES) · NO PEOPLE, FLAGS OR EMBLEMS · WREATH AND PODIUM: " + AISRC, cam=(1.0, 1.06), origin="40% 60%"))

const_doc = (f'<div style="width:900px;box-sizing:border-box;padding:56px 66px;background:#FAF7F0;box-shadow:0 30px 60px rgba(0,0,0,.6);color:#222">'
             f'<div style="font:400 26px/1.2 PlayR;letter-spacing:3px;text-align:center">CONSTITUCIÓN POLÍTICA DEL ESTADO</div>'
             f'<div style="font:400 22px Doc;text-align:center;color:#555;margin-top:6px">Bolivia, 2009</div><div style="width:120px;border-top:2px solid #777;margin:24px auto"></div>'
             f'{bar(90, .14)}{bar(70, .14)}<div style="font:700 26px Doc;margin-top:26px">Artículo 267.</div>'
             f'<div style="font:400 40px/1.45 Doc;margin-top:8px">El Estado boliviano declara su derecho {hl("irrenunciable e imprescriptible")} sobre el territorio que le dé acceso al océano Pacífico y su espacio marítimo.</div>'
             f'{bar(94, .14)}{bar(60, .14)}<div style="font:500 13px Plex;letter-spacing:2px;color:#777;margin-top:20px">PAGE SET IN THE STUDIO FROM THE PUBLISHED TEXT · OTHER LINES NOT REPRODUCED</div></div>')
h, pr = table(-66.5, -17.0, 0.9, 960, 560)
put("22_art267", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.5)"></div>', 0, 0)
    + A(const_doc, 110, 160, "up 0 .12", "transform:rotate(-1deg);z-index:30")
    + A(f'<div style="font:400 72px/1 Anton;color:{PARCH};width:760px">CANNOT BE WAIVED.<br>CANNOT EXPIRE.</div>', 1100, 200, "up .4 .52", "z-index:40")
    + A(art("II · 1904", "…dominio absoluto y " + ring("perpetuo", ".72 .8", 5) + " de Chile…", 640), 1150, 520, "up .6 .7", "transform:rotate(2deg);z-index:35")
    + tag("A FOREVER, ANSWERED WITH A FOREVER", 1100, 860, 1.5, "snap .88 .88")
    + stamp([("TODAY", 0, .2), ("2009", .2, 9)], "ff"),
    "CONSTITUTION OF BOLIVIA (2009), ART. 267 (TEXT VIA CONSTITUTE PROJECT; PAGE TYPESET BY THE STUDIO, CAPTURE OF THE PDF PAGE STILL TO DO) · 1904 TREATY, ART. II (RECONSTRUCTION) · " + MAPSRC))

h, pr = table(-71.0, -17.7, 3.0, 1250, 500, panel=False)
ilo = pr(*PINS["ILO"])
bx0, bx1 = pr(-71.36, -17.66), pr(-71.33, -17.71)
put("23_boliviamar", page(
    fullphoto("ilo", "50% 60%")
    + label("THE COAST AT ILO, PERU · REAL PHOTO (CC0) · NOT THE BOLIVIAMAR STRIP ITSELF", 1040, 960, "fade 0 .05", 14)
    + A(f'<div style="width:560px;height:400px;overflow:hidden;border:10px solid #fff;box-shadow:14px 16px 0 rgba(0,0,0,.45);position:relative;background:{DESKC}">'
        f'<div style="position:absolute;left:{-(1250 - 280) + 0:.0f}px;top:{-(500 - 200):.0f}px;width:1920px;height:1080px">{h}'
        f'<svg class="a" style="left:0;top:0;z-index:60" width="1920" height="1080"><path d="M{ilo[0] - 4:.0f} {ilo[1] + 22:.0f} l -10 0 l 0 44 l 10 0" fill="none" stroke="{TEAL}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" transform="rotate(-30 {ilo[0]:.0f} {ilo[1]:.0f})"/></svg>'
        f'{pin(pr, "ILO", "ILO · PERU", 1, "drop 0 .01")}</div></div>', 70, 170, "up .05 .18", "transform:rotate(-2deg);z-index:40")
    + A(f'<div style="background:rgba(244,239,230,.96);padding:18px 26px;box-shadow:0 14px 24px rgba(0,0,0,.35);border-left:8px solid {TEAL}">{kicker("1992 · PERU GRANTS BOLIVIA A STRIP OF BEACH NEAR ILO", INK, 15)}'
        f'<div style="font:400 62px/1 Anton;color:{INK};margin-top:8px">BOLIVIAMAR</div><div style="font:400 38px/1.1 Anton;color:{INK}">{hl("~5 KM")} OF BEACH · 99 YEARS, RENEWABLE</div></div>', 70, 640, "up .3 .42", "z-index:42")
    + tag("BEACH · STATUS: STILL BEACH", 1180, 200, 2, "snap .85 .85")
    + check(1240, 290, "snap .86 .86", "'STILL MOSTLY SAND': TO CHECK")
    + label("INSET: SCHEMATIC BRACKET", 90, 590, "fade .2 .3", 13)
    + stamp([("2009", 0, .1), ("1992", .1, 9)], "ff"),
    "BOLIVIAMAR: 1992 PERU–BOLIVIA AGREEMENT, ~5 KM BEACH SOUTH OF ILO, 99 YEARS RENEWABLE; 2010 PROTOCOL; FACILITIES LARGELY NEVER BUILT (REPORTED: TO CHECK) · INSET BRACKET SCHEMATIC · " + credit("ilo") + " · INSET: NATURAL EARTH + TERRARIUM RELIEF, DRAWN IN THE STUDIO"))

icj = (f'<div style="width:860px;box-sizing:border-box;padding:46px 56px;background:#FBFAF6;box-shadow:0 30px 60px rgba(0,0,0,.6);color:#222">'
       f'<div style="font:400 24px/1.2 PlayR;letter-spacing:3px;text-align:center">INTERNATIONAL COURT OF JUSTICE</div>'
       f'<div style="font:400 22px Doc;text-align:center;color:#555;margin-top:6px">Obligation to Negotiate Access to the Pacific Ocean (Bolivia v. Chile) · Judgment of 1 October 2018</div>'
       f'<div style="width:120px;border-top:2px solid #777;margin:22px auto"></div>'
       f'<div style="font:400 34px/1.4 Doc">The Court, {ring(hl("by twelve votes to three"), ".3 .4", 6, (14, 8))}, finds that Chile did not undertake a legal obligation to negotiate a sovereign access to the Pacific Ocean for Bolivia.</div>'
       f'<div style="font:400 22px Doc;color:#555;margin-top:18px">Para. 176 (summary): the finding should not be understood as precluding the parties from continuing their dialogue and exchanges, in a {hl("spirit of good neighbourliness")}.</div>'
       f'<div style="font:500 13px Plex;letter-spacing:2px;color:#777;margin-top:18px">STUDIO SUMMARY CARD, NOT THE JUDGMENT PAGE · WORDING TO CHECK ON THE ICJ PDF</div></div>')
vbar = lambda n, v, s: (f'<div style="display:flex;flex-direction:column;align-items:center;gap:8px"><div style="font:400 64px/1 Anton;color:{PARCH}">{v}</div>'
                        f'<div data-anim="grow {s} {s + .12}" style="width:120px;height:{v * 34}px;background:#B8B2A6"></div><div style="font:500 16px Plex;letter-spacing:3px;color:{PARCH};text-align:center;width:150px">{n}</div></div>')
h, pr = table(-66.5, -17.0, 0.9, 960, 560)
put("24_icj", page(
    h + a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.55)"></div>', 0, 0)
    + A(icj, 100, 170, "up 0 .12", "transform:rotate(-1deg);z-index:30")
    + A(f'<div style="display:flex;align-items:flex-end;gap:40px;border-bottom:4px solid {PARCH};padding:0 20px">{vbar("JUDGES: NO OBLIGATION", 12, .4)}{vbar("JUDGES: DISSENT", 3, .45)}</div>', 1110, 160, "fade .38 .42", "z-index:40")
    + check(1500, 170, "snap .5 .5", "12–3 · PARA. 176: TO CHECK")
    + label("BOLIVIA: KEEP TALKING", 1080, 720, "fade .7 .75", 20, PARCH, INK, f"border-left:8px solid {TEAL}")
    + label("CHILE: DIALOGUE YES · SOVEREIGNTY NO", 1080, 780, "fade .76 .8", 20, PARCH, INK, f"border-left:8px solid {INK}")
    + tag("RULING: NO OBLIGATION · SUGGESTION: COFFEE SOMETIME", 600, 900, -1.5, "snap .9 .9")
    + stamp([("24 APR 2013", 0, .1), ("24 SEP 2015", .1, .2), ("1 OCT 2018", .2, 9)], "ff"),
    "ICJ, OBLIGATION TO NEGOTIATE ACCESS TO THE PACIFIC OCEAN (BOLIVIA v. CHILE): FILED 24 APR 2013; OBJECTION REJECTED 24 SEP 2015; JUDGMENT 1 OCT 2018, 12–3 (SECONDARY: AL JAZEERA, BIOBIOCHILE; PDF NOT YET READ: TO CHECK) · REACTIONS ATTRIBUTED TO THE GOVERNMENTS (MERCOPRESS, OCT 2018) · BARS FROM ZERO, NO SIDE COLOURED"))

# ======================================================================================================================
# 5 · SYNTHESIS
# ======================================================================================================================
h, pr = table(-67.5, -19.6, 0.5, 960, 470, strip="beside", rivers=True)
pts = [pr(*PINS[n]) for n in ("ANTOFAGASTA", "TOPÁTER", "ARICA", "LA PAZ", "LAKE TITICACA")]
rc = lambda t, w=230: f'<div style="width:{w}px;height:120px;box-sizing:border-box;background:{OLD};padding:14px 16px;box-shadow:0 12px 20px rgba(0,0,0,.45);font:500 15px/1.35 Plex;letter-spacing:2px;color:{INK}">{t}</div>'
put("25_answer", page(
    h + "".join(pin(pr, n, n if n != "TOPÁTER" else "TOPÁTER · 23 MAR", 1, "drop 0 .02", size=14) for n in ("ANTOFAGASTA", "TOPÁTER", "ARICA", "LA PAZ", "ILO"))
    + pin(pr, "LAKE TITICACA", "", 1, "drop 0 .02")
    + string(pts, "draw .05 .3", w=3)
    + plate(1, 220, 124, pts[-1][0] + 40, pts[-1][1] - 210, "drop .02 .06", -3)
    + "".join(A(rc(t), 90 + i * 250, 800, f"up {s} {s + .06}", f"transform:rotate({(-1) ** i * 2}deg);z-index:55") for i, (t, s) in enumerate(
        (("1878 · 10 CENTAVOS PER QUINTAL", .3), ("14 FEB 1879 · AUCTION / LANDING", .36), ("1884 · TRUCE", .42), ("1904 · ART. II 'PERPETUO'", .48), ("1904 · ART. VI 'A PERPETUIDAD'", .54), ("2009 · ART. 267", .6), ("2018 · ICJ 12–3", .66))))
    + top(A(f'<div style="background:#FBF8F0;padding:18px 24px;box-shadow:0 16px 26px rgba(0,0,0,.45);transform:rotate(2deg);width:250px"><div style="font:700 40px/1 Caveat;color:{INK}">OUR READING</div>'
        f'<div style="font:400 36px/1.2 ISerif;color:{INK};margin-top:8px">a sentence in the constitution that learned to march</div></div>', 1600, 400, "up .75 .85", "z-index:60"))
    + top(A(f'<div style="font:400 52px/1 Anton;color:{PARCH};width:300px">GEOGRAPHY<br>+ <span style="color:{SIG}">PAPERWORK</span></div>', 1610, 200, "fade .1 .2", "z-index:60"))
    + stamp([("TODAY", 0, 9)], None),
    "RECEIPTS AS IN THE FILM (SEE DOSSIER; ⚠ ITEMS TO CHECK) · 'OUR READING' IS LABELLED OPINION · LITORAL STRIP SCHEMATIC · BOAT CLIPPING: AI ILLUSTRATION · " + MAPSRC, cam=(1.0, 1.08), origin="40% 35%"))

put("26_end", page(
    fullphoto("titicaca", "50% 40%") + a('<div style="width:1920px;height:1080px;background:linear-gradient(rgba(26,26,26,.55),rgba(26,26,26,.2) 70%)"></div>', 0, 0)
    + A(f'<div style="width:420px;background:rgba(244,239,230,.95);padding:22px 26px;box-shadow:0 18px 30px rgba(0,0,0,.35);border-left:8px solid {INK}">'
        + kicker("ALTITUDE", INK) + f'<div style="font:400 92px/1 Anton;color:{INK}">3,810 M</div>'
        + f'<div style="border-top:3px solid {INK};margin:14px 0"></div>' + kicker("COAST", INK)
        + f'<div style="font:400 92px/1 Anton;color:{INK}"><span data-anim="count .2 .35" data-to="0">0</span> KM</div></div>', 1440, 180, "up 0 .1", "z-index:40")
    + A(f'<div style="font:400 92px/0.98 Anton;color:{PARCH};text-shadow:0 4px 18px rgba(0,0,0,.6);width:1180px">MOST NAVIES MEASURE DEPTH.<br>THIS ONE MEASURES HOW LONG<br>A COUNTRY CAN <span style="background:{SIG};color:{INK};padding:0 12px;text-shadow:none">REMEMBER.</span></div>', 70, 220, "up .4 .55", "z-index:40")
    + A(f'<div style="display:flex;flex-direction:column;gap:12px;align-items:flex-start">'
        f'<div style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 22px Plex;letter-spacing:4px;box-shadow:6px 6px 0 rgba(0,0,0,.35)">SEA LEVEL: NOT APPLICABLE</div>'
        f'<div data-anim="wipe .7 .85" style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 22px Plex;letter-spacing:4px;box-shadow:6px 6px 0 rgba(0,0,0,.35)">MEMORY: 1879 → TODAY</div></div>', 80, 760, "snap .6 .6", "z-index:70;transform:rotate(-1.5deg)")
    + A(f'<svg width="48" height="70" viewBox="0 0 48 70" style="filter:drop-shadow(3px 5px 3px rgba(0,0,0,.45))"><path d="M10 6 L10 68" stroke="#444" stroke-width="4"/><path d="M12 6 L44 14 L12 24Z" fill="{RED}" stroke="#fff" stroke-width="2"/></svg>', 1360, 640, "drop .85 .9", "z-index:45")
    + label("EVERY 23 MARCH, MEASURED AGAIN", 1410, 650, "fade .88 .95", 18, RED, PARCH)
    + label("LAKE TITICACA · REAL PHOTO", 1560, 960, "fade 0 .05", 14)
    + stamp([("TODAY", 0, 9)], None),
    "CALLBACK · ALTITUDE: BRITANNICA ~3,810 M · COAST: 0 KM (LANDLOCKED SINCE THE 1904 TREATY) · DÍA DEL MAR 23 MARCH · " + credit("titicaca"), cam=(1.06, 1.0)))

print("frames ok:", len(list((D / "html").glob("*.html"))))
