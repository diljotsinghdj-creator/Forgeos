"""Collage kit, look 2 of the false-memory film (2026-11-20, after the owner rejected look 1).

The owner's references (STYLE_REFERENCES.md): "Collage, not graphics." Real photographs and engravings cut out in black and
white, on paper, with one accent; pieces drop, slide and stamp in one by one until the frame is dense; the camera never sits still.

  ground    pale lab-paper studio sweep with real paper fibre and drifting window-light shadows; the room goes dark for the test
  pieces    real cut-outs (assets/real2, made by cut2.py): halftone, white sticker edge, hard offset shadow
  colour    cobalt discs and blocks behind subjects; amber on the one thing that matters; sign red on the sign, the parked car, red marker
  type      Bebas Neue giant caps that sit behind the subject, Fraunces for the punch word, DM Mono labels, Permanent Marker notes
  motion    every piece arrives with an overshoot and then boils at 12 fps; discs turn; shadows drift
"""
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageOps

from kit import DEFS, FONTS as FONTS1, stamp   # the rubber stamp and its ink filter carry over from look 1

D = Path(__file__).resolve().parent
H = D / "html"; H.mkdir(exist_ok=True)
R2 = D / "assets" / "real2"
SL, PAPER, CO, AM, RED, WHITE = "#141824", "#F0F4F8", "#2B6CB0", "#ED8936", "#C53030", "#FBFCFE"
CRED = {c["slug"]: c for c in json.loads((D / "data" / "photo_credits2.json").read_text())}
SIZE = {f.stem: Image.open(f).size for f in R2.glob("*.png")} | {f.stem: Image.open(f).size for f in R2.glob("*.jpg")}

# the paper texture, once light (to multiply onto the pale ground) and once dark (to screen onto slate)
if not (R2 / "paper_light.jpg").is_file():
    g = ImageOps.autocontrast(Image.open(R2 / "paper.jpg").convert("L"), cutoff=1)
    g.point(lambda v: int(196 + v * 59 / 255)).save(R2 / "paper_light.jpg", quality=90)
    g.point(lambda v: int(v * 70 / 255)).save(R2 / "paper_dark.jpg", quality=90)

FONTS = FONTS1 + "".join(f"@font-face{{font-family:{n};src:url(/fonts/{f}.woff2)}}" for n, f in (
    ("Fraunces9", "fraunces-latin-900-normal"), ("FrauncesI", "fraunces-latin-400-italic"), ("Inter8", "inter-latin-800-normal"), ("Inter4", "inter-latin-400-normal")))

JS = """<script>(function(){function run(){const q=new URLSearchParams(location.search);const T=q.has('t')?parseFloat(q.get('t')):1;
const E=x=>1-Math.pow(1-x,3),B=x=>{const c=1.70158;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const R=(k,s)=>{const v=Math.sin(k*12.9898+s*78.233)*43758.5453;return v-Math.floor(v)};
document.querySelectorAll('[data-anim]').forEach((el,i)=>{const [k0,s0,e0]=el.dataset.anim.split(' ');const k=k0.replace(/^q(?=slam|drop|pop|snap)/,'');const s=+s0,e=+e0,d=el.dataset,st=el.style;
const x=e>s?Math.min(1,Math.max(0,(T-s)/(e-s))):(T>=s?1:0),v=E(x);
if(k==='fade')st.opacity=v;
else if(k==='up'){st.opacity=Math.min(1,x*2);st.transform=`translateY(${(1-v)*60}px)`}
else if(k==='drop'){const b=B(x);st.opacity=x>0?1:0;st.transform=`translate(${(+d.dx||0)*(1-b)}px,${(d.dy!==undefined?+d.dy:-140)*(1-b)}px)`}
else if(k==='pop'){st.opacity=Math.min(1,x*4);st.transform=`scale(${x>0?.55+.45*B(x):.55})`}
else if(k==='slam'){st.opacity=x>0?1:0;st.transform=`scale(${1+(1-x)*.6})`}
else if(k==='snap')st.opacity=x>=1?1:0;
else if(k==='click')st.opacity=x>0?1:0;
else if(k==='hide')st.opacity=x>=1?0:1;
else if(k==='grow'){st.transformOrigin='50% 100%';st.transform=`scaleY(${v})`}
else if(k==='growx'){st.transformOrigin='0 50%';st.transform=`scaleX(${v})`}
else if(k==='wipe')st.clipPath=`inset(-20px ${(1-v)*100}% -20px -20px)`;
else if(k==='draw')el.querySelectorAll('[pathLength]').forEach(pa=>{pa.style.strokeDasharray=1;pa.style.strokeDashoffset=1-v;pa.style.opacity=x>0?1:0});
else if(k==='count')el.textContent=(+d.to*v).toFixed(+(d.dp||0));
else if(k==='fill'){const ch=el.children;const n=Math.round(ch.length*v);for(let j=0;j<ch.length;j++)ch[j].style.opacity=j<n?1:0}
else if(k==='bar')st.width=((+d.p0+(+d.p1-+d.p0)*x)*+d.w)+'px';
else if(k==='move')st.transform=`translate(${(+d.dx||0)*(1-x)}px,${(+d.dy||0)*(1-x)}px)`;
else if(k==='drift')st.transform=`translate(${(+d.dx||0)*x}px,${(+d.dy||0)*x}px)`;
else if(k==='spin')st.transform=`rotate(${(+d.deg||40)*x}deg)`;
else if(k==='sway')st.transform=`rotate(${(+d.a||1)*Math.sin(6.2832*(+d.f||2)*T+i)}deg)`;
else if(k==='boil'){if(T>=s){const n=+d.n||40,kk=Math.floor(T*n),px=+d.px||1.5;st.transform=`translate(${(R(kk,i)-.5)*2*px}px,${(R(kk,i+7)-.5)*2*px}px) rotate(${(R(kk,i+13)-.5)*2*(+d.a||.4)}deg)`}}
else if(k==='type'){const n=+d.n||1;const c=Math.floor(x*n+1e-6);st.width=`calc(${c}ch + ${c*(+d.ls||0)}px)`}
else if(k==='flipout'){st.transform=`scaleX(${1-x})`;st.opacity=x>=1?0:1}
else if(k==='flipin'){st.transform=`scaleX(${x})`;st.opacity=x>0?1:0}
else if(k==='push')st.transform=`scale(${1+.07*x})`;
else if(k==='num')el.textContent=Math.floor(+d.from+(+d.to-+d.from)*x);
else if(k==='turn')st.transform=`rotate(${+d.a0+(+d.a1-+d.a0)*x}deg)`;
});}document.addEventListener('DOMContentLoaded',run);})()</script>"""

SHADOW = "filter:drop-shadow(9px 11px 0 rgba(20,24,36,.2)) drop-shadow(0 16px 22px rgba(20,24,36,.18))"
SH = "box-shadow:9px 11px 0 rgba(20,24,36,.2),0 16px 26px rgba(20,24,36,.2)"


def page(body, src="", dark=False, gobo=True):
    """One 1920x1080 frame. Light: the studio sweep. Dark: the same room with the lights down, for the test."""
    if dark:
        ground = (f'<div class="a" style="inset:0;background:radial-gradient(ellipse at 50% 44%,#232A3C 0%,{SL} 58%,#0B0E16 100%)"></div>'
                  '<img class="a" src="/assets/real2/paper_dark.jpg" style="left:0;top:0;width:1920px;height:1080px;object-fit:cover;mix-blend-mode:screen;opacity:.5">')
        ink = "rgba(240,244,248,.6)"
    else:
        ground = ('<div class="a" style="inset:0;background:radial-gradient(ellipse at 36% 38%,#FAFBFD 0%,#EEF2F7 46%,#D9E1EB 100%)"></div>'
                  '<img class="a" src="/assets/real2/paper_light.jpg" style="left:0;top:0;width:1920px;height:1080px;object-fit:cover;mix-blend-mode:multiply;opacity:.6">')
        if gobo:   # window-blind shadows crossing the paper, drifting through the shot
            ground += ('<div class="a" data-anim="drift 0 1" data-dx="110" data-dy="34" style="left:-520px;top:-420px;width:3000px;height:1900px;mix-blend-mode:multiply;filter:blur(20px);'
                       'background:repeating-linear-gradient(104deg,transparent 0 180px,rgba(20,24,36,.085) 180px 262px,transparent 262px 318px,rgba(20,24,36,.055) 318px 356px)"></div>')
        ink = "rgba(20,24,36,.62)"
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{SL if dark else PAPER};position:relative}}'
            f'.a{{position:absolute}}img{{user-select:none}}</style></head><body>{DEFS}{ground}{body}'
            f'<div class="a" style="inset:0;pointer-events:none;z-index:88;background:radial-gradient(ellipse at 50% 50%,transparent 58%,rgba(20,24,36,{.34 if dark else .15}) 100%)"></div>'
            f'<div class="a" style="left:30px;bottom:12px;z-index:90;font:500 13px/1.4 Plex;letter-spacing:1.2px;color:{ink};max-width:1500px">{src}</div>'
            + JS + '<script>document.fonts.ready.then(()=>Promise.all([...document.images].map(i=>i.decode().catch(()=>0)))).then(()=>window.READY=true)</script></body></html>')


def put(name, html):
    (H / f"{name}.html").write_text(html, encoding="utf-8")


def A(html, x, y, anim="snap 0 0", extra="", data=""):
    return f'<div class="a" data-anim="{anim}" {data} style="left:{x}px;top:{y}px;{extra}">{html}</div>'


def a(html, x, y, extra=""):
    return f'<div class="a" style="left:{x}px;top:{y}px;{extra}">{html}</div>'


def W(html, anim, data="", extra=""):
    """A second motion on the same piece (a piece that drops in, then boils)."""
    return f'<div data-anim="{anim}" {data} style="{extra}">{html}</div>'


def credit(*slugs):
    """The source line for the real pieces on a frame."""
    seen, out = set(), []
    for s in slugs:
        c = CRED[s]; who = (c["author"] or c["source"]).upper(); lic = c["licence"].replace("Pixabay Content License", "PIXABAY LICENCE").upper()
        key = (who, lic)
        if key not in seen:
            seen.add(key); out.append(f"{who}, {lic}")
    return "REAL PIECES: " + " · ".join(out)


# ---- real pieces -------------------------------------------------------------------------------------------------------------
def cut(slug, w, x, y, anim="snap 0 0", rot=0.0, z=30, flip=False, boil=None, data="", shadow=True):
    """A real cut-out, w px wide. boil = the timeline moment from which it jitters like stop-motion paper."""
    iw, ih = SIZE[slug]; h = round(w * ih / iw)
    img = f'<img src="/assets/real2/{slug}.png" style="width:{w}px;height:{h}px;display:block;{"transform:scaleX(-1);" if flip else ""}{SHADOW if shadow else ""}">'
    if boil is not None:
        img = W(img, f"boil {boil:.4f} 1", 'data-a=".3" data-px="1.2" data-n="46"')
    return f'<div class="a" data-anim="{anim}" {data} style="left:{x}px;top:{y}px;z-index:{z}"><div style="transform:rotate({rot}deg)">{img}</div></div>'


def hgt(slug, w):
    return round(w * SIZE[slug][1] / SIZE[slug][0])


def plate(slug, w, h, rot=0.0, pos="50% 50%", cap="", border=14, tp=True, tint=""):
    """A real photo as a print on the paper: white border, tape, a typed caption strip."""
    capd = f'<div style="position:absolute;left:{border}px;bottom:{border - 2}px;font:500 14px Mono;letter-spacing:2px;color:#5B6880">{cap}</div>' if cap else ""
    tape_ = f'<div style="position:absolute;left:{w // 2 - 70}px;top:-20px;width:170px;height:40px;background:rgba(237,137,54,.55);transform:rotate({-rot * 2 - 3}deg)"></div>' if tp else ""
    over = f'<div style="position:absolute;inset:0;background:{tint};mix-blend-mode:multiply"></div>' if tint else ""
    return (f'<div style="position:relative;background:{WHITE};padding:{border}px {border}px {border + (26 if cap else 0)}px;{SH};transform:rotate({rot}deg)">'
            f'<div style="position:relative;overflow:hidden;width:{w}px;height:{h}px"><img src="/assets/real2/{slug}.jpg" style="width:{w}px;height:{h}px;object-fit:cover;object-position:{pos};display:block">{over}</div>{capd}{tape_}</div>')


# ---- flat paper shapes -----------------------------------------------------------------------------------------------------------
def disc(d, col=CO, extra=""):
    return f'<div style="width:{d}px;height:{d}px;border-radius:50%;background:{col};{extra}"></div>'


def ring(d, col=SL, dash="18 16", w=5):
    """A dashed orbit ring (it turns slowly when its holder carries a spin)."""
    return (f'<svg width="{d}" height="{d}" viewBox="0 0 {d} {d}"><circle cx="{d / 2}" cy="{d / 2}" r="{d / 2 - w}" fill="none" stroke="{col}" stroke-width="{w}" stroke-dasharray="{dash}" stroke-linecap="round"/></svg>')


def dots(w, h, col=SL, cell=16, r=2.6, op=.5):
    return f'<div style="width:{w}px;height:{h}px;opacity:{op};background-image:radial-gradient({col} {r}px,transparent {r + .6}px);background-size:{cell}px {cell}px"></div>'


def torn(w, h, col=WHITE, seed=1, extra=""):
    """A strip of torn paper: straight long edges, ragged ends and a slightly ragged top and bottom."""
    r = random.Random(seed); n = 16
    top = [(i / n * 100, r.uniform(0, 7)) for i in range(n + 1)]; bot = [(100 - i / n * 100, 100 - r.uniform(0, 7)) for i in range(n + 1)]
    pts = ",".join(f"{x:.1f}% {y:.1f}%" for x, y in top + bot)
    return f'<div style="width:{w}px;height:{h}px;background:{col};clip-path:polygon({pts});{extra}"></div>'


def block(w, h, col=CO, rot=0.0, extra=""):
    return f'<div style="width:{w}px;height:{h}px;background:{col};transform:rotate({rot}deg);{extra}"></div>'


# ---- type ------------------------------------------------------------------------------------------------------------------------
def bebas(t, size, col=SL, ls=2, lh=.86, extra=""):
    return f'<div style="font:400 {size}px/{lh} Bebas;color:{col};letter-spacing:{ls}px;white-space:nowrap;text-transform:uppercase;{extra}">{t}</div>'


def serif(t, size, col=SL, italic=False, lh=1.0, extra=""):
    return f'<div style="font:{"400" if italic else "900"} {size}px/{lh} {"FrauncesI" if italic else "Fraunces9"};color:{col};white-space:nowrap;letter-spacing:-.5px;{extra}">{t}</div>'


def label(t, size=22, bg=SL, fg=PAPER, rot=0.0):
    """A typed label in a sharp box: dates, exhibits, dry asides."""
    return (f'<div style="display:inline-block;background:{bg};color:{fg};font:500 {size}px Mono;letter-spacing:{max(2, size // 7)}px;padding:{size // 3}px {size * .62:.0f}px;white-space:nowrap;'
            f'transform:rotate({rot}deg);box-shadow:5px 6px 0 rgba(20,24,36,.22);text-transform:uppercase">{t}</div>')


def marker(t, size=60, col=SL, rot=-3.0, font="Marker"):
    return f'<div style="font:400 {size}px/1.05 {font};color:{col};white-space:nowrap;transform:rotate({rot}deg)">{t}</div>'


def mono(t, size=24, col=SL, ls=2, extra=""):
    return f'<div style="font:500 {size}px/1.35 Mono;color:{col};letter-spacing:{ls}px;white-space:nowrap;{extra}">{t}</div>'


def hl(t, col=AM):
    return f'<span style="background:linear-gradient(transparent 12%,{col} 12%,{col} 90%,transparent 90%);padding:0 6px;margin:0 -6px">{t}</span>'


def tape(w=170, rot=-4.0, col="rgba(237,137,54,.6)"):
    return f'<div style="width:{w}px;height:40px;background:{col};transform:rotate({rot}deg);box-shadow:0 2px 4px rgba(20,24,36,.2)"></div>'


# ---- paper you can write on ---------------------------------------------------------------------------------------------------------
def card(inner, w, h, rot=0.0, lines=True, pad=30, extra=""):
    """An index card: ruled in cobalt, one heavier head rule."""
    line = max(34, h // 7)
    bg = (f"background-color:{WHITE};background-image:linear-gradient({CO} 0 3px,transparent 3px),repeating-linear-gradient(transparent 0 {line - 2}px,rgba(43,108,176,.26) {line - 2}px {line}px);"
          f"background-size:100% {int(line * 1.5)}px,100% {line}px;background-position:0 {int(line * 1.5) - 3}px,0 {int(line * 1.5)}px;background-repeat:no-repeat,repeat-y;") if lines else f"background:{WHITE};"
    return f'<div style="width:{w}px;height:{h}px;box-sizing:border-box;{bg}padding:{pad}px;{SH};transform:rotate({rot}deg);position:relative;border-radius:5px;{extra}">{inner}</div>'


def sheet(inner, w, h=None, rot=0.0, pad=44, bg=WHITE, extra=""):
    hh = f"height:{h}px;" if h else ""
    return f'<div style="width:{w}px;{hh}box-sizing:border-box;background:{bg};padding:{pad}px;{SH};transform:rotate({rot}deg);position:relative;{extra}">{inner}</div>'


CENTER = lambda inner: f'<div style="display:flex;align-items:center;justify-content:center;height:100%;width:100%">{inner}</div>'


def word(t, w, h, col=SL, share=.84):
    """A word typed on a card, as big as the card allows (DM Mono: 0.6 em a letter)."""
    n = len(t); ls = .09
    size = int(min(h * .56, w * share / (n * .6 + (n - 1) * ls)))
    return f'<div style="font:500 {size}px/1 Mono;color:{col};letter-spacing:{size * ls:.0f}px;margin-right:-{size * ls:.0f}px;white-space:nowrap">{t}</div>'


def typed(t, size, ls, anim, col=SL):
    """A mono line typed on, key by key."""
    return (f'<div style="font:500 {size}px/1.35 Mono;color:{col};letter-spacing:{ls}px;white-space:nowrap;height:{size * 1.35:.0f}px">'
            f'<span data-anim="{anim}" data-n="{len(t)}" data-ls="{ls}" style="display:inline-block;overflow:hidden;white-space:nowrap;vertical-align:top">{t}</span></div>')


# ---- the investigator's hand: marker arrows and rings, drawn on ----------------------------------------------------------------------
def wobble(cx, cy, rx, ry, seed=1, turns=1.08):
    r = random.Random(seed); pts = []
    for i in range(80):
        t = -.6 + 2 * math.pi * turns * i / 79; k = 1 + r.uniform(-.025, .025)
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    return "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)


def loop(cx, cy, rx, ry, anim, col=RED, w=9, seed=3):
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:62;pointer-events:none" width="1920" height="1080">'
            f'<path d="{wobble(cx, cy, rx, ry, seed)}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/></svg>')


def arrow(x1, y1, x2, y2, anim, col=SL, w=8, bend=50):
    ang = math.atan2(y2 - y1, x2 - x1)
    hx, hy = x2 - 30 * math.cos(ang - .5), y2 - 30 * math.sin(ang - .5); kx, ky = x2 - 30 * math.cos(ang + .5), y2 - 30 * math.sin(ang + .5)
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:62;pointer-events:none" width="1920" height="1080">'
            f'<path d="M{x1} {y1} Q {(x1 + x2) / 2 + bend * math.sin(ang):.0f} {(y1 + y2) / 2 - bend * math.cos(ang):.0f} {x2} {y2}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M{hx:.0f} {hy:.0f} L{x2} {y2} L{kx:.0f} {ky:.0f}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def sparks(cx, cy, anim, col=AM, r0=60, r1=130, n=7, w=10):
    """Marker strokes around a bump."""
    out = "".join(f'<line x1="{cx + r0 * math.cos(t):.0f}" y1="{cy + r0 * math.sin(t):.0f}" x2="{cx + r1 * math.cos(t):.0f}" y2="{cy + r1 * math.sin(t):.0f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
                  for t in (math.radians(200 + i * 140 / (n - 1)) for i in range(n)))
    return f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:64;pointer-events:none" width="1920" height="1080">{out}</svg>'
