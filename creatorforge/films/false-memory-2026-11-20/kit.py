"""Frame kit for "Can I Give You a False Memory in 60 Seconds?" (Dragon Psychology, DJ style).

Visual DNA, "the evidence desk" (distinct from every earlier film; recorded in pick.json):
- Surface: a slate cutting mat with a faint cobalt grid, lit from the top left; rigid paper with hard offset shadows.
- Type: Archivo Black (headlines), DM Mono (typewriter and labels), Instrument Serif italic (quotes), Shadows Into Light (pencil).
- Kinetic system: stamp thuds, label-maker tape, typed strips, card flips; five paper treatments for the word list.
- Signature motif: the intake stamp (RECEIVED / FILED / CERTAIN) and exhibit tags; the thin amber 60-second bar.
- Palette: slate #141824, lab-paper #F0F4F8, cobalt #2B6CB0, amber #ED8936 (the one signal). Film accent: sign red #C53030,
  only on road signs, the parked car and red-ink notes. No yellow, no logo, no mascot, no faces.
Pages use the studio timeline (data-anim="kind start end", ?t=0..1), so film_video.py can drive them later."""
import json
import math
import random
from pathlib import Path

D = Path(__file__).resolve().parent
H = D / "html"; H.mkdir(exist_ok=True)
SL, PAPER, CO, AM, RED = "#141824", "#F0F4F8", "#2B6CB0", "#ED8936", "#C53030"
INK, CARD, FOLD, DIM = "#1B2130", "#E7EDF4", "#C9D6E4", "#8FA0B5"
CRED = {c["slug"]: c for c in json.load(open(D / "data" / "photo_credits.json"))}

FONTS = "".join(f"@font-face{{font-family:{n};src:url(/fonts/{f}.woff2)}}" for n, f in (
    ("Black", "archivo-black-latin-400-normal"), ("Mono", "dm-mono-latin-500-normal"), ("Serif", "instrument-serif-latin-400-italic"),
    ("SerifR", "instrument-serif-latin-400-normal"), ("Hand", "shadows-into-light-latin-400-normal"), ("Marker", "permanent-marker-latin-400-normal"),
    ("Bebas", "bebas-neue-latin-400-normal"), ("Plex", "ibm-plex-mono-latin-500-normal")))

MAT = (f"background:{SL};background-image:linear-gradient(rgba(43,108,176,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(43,108,176,.10) 1px,transparent 1px),"
       "linear-gradient(rgba(43,108,176,.22) 2px,transparent 2px),linear-gradient(90deg,rgba(43,108,176,.22) 2px,transparent 2px);"
       "background-size:40px 40px,40px 40px,200px 200px,200px 200px;background-position:-1px -1px")

DEFS = ('<svg width="0" height="0" style="position:absolute"><defs>'
        '<filter id="rough" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="4" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G" result="d"/>'
        '<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="9" result="s"/><feColorMatrix in="s" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -9 5.2" result="m"/>'
        '<feComposite in="d" in2="m" operator="in"/></filter>'
        '<filter id="wob"><feTurbulence type="fractalNoise" baseFrequency=".02" numOctaves="2" seed="7" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="5"/></filter>'
        '</defs></svg>')

GRAIN = ('<svg style="position:absolute;inset:0;pointer-events:none;opacity:.22;mix-blend-mode:multiply;z-index:80" width="1920" height="1080"><filter id="g">'
         '<feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3"/><feColorMatrix values="0 0 0 0 .32 0 0 0 0 .34 0 0 0 0 .4 0 0 0 .55 0"/></filter>'
         '<rect width="1920" height="1080" filter="url(#g)"/></svg>'
         '<div style="position:absolute;inset:0;pointer-events:none;z-index:81;background:radial-gradient(ellipse at 42% 40%,transparent 50%,rgba(6,8,14,.5) 100%)"></div>')

ANIM_JS = """<script>(function(){function run(){const q=new URLSearchParams(location.search);const T=q.has('t')?parseFloat(q.get('t')):1;
const E=x=>1-Math.pow(1-x,3);
document.querySelectorAll('[data-anim]').forEach(el=>{const [k,s0,e0]=el.dataset.anim.split(' ');const s=+s0,e=+e0;
const p=e>s?Math.min(1,Math.max(0,(T-s)/(e-s))):(T>=s?1:0);const v=E(p);const st=el.style;
if(k==='fade')st.opacity=v;
else if(k==='up'){st.opacity=Math.min(1,p*2);st.transform=`translateY(${(1-v)*60}px)`}
else if(k==='drop'){st.opacity=p>0?1:0;st.transform=`translateY(${-(1-v)*140}px)`}
else if(k==='pop'){st.opacity=Math.min(1,p*3);st.transform=`scale(${.4+.6*v+Math.sin(p*Math.PI)*.08})`}
else if(k==='slam'){st.opacity=p>0?1:0;st.transform=`scale(${1+(1-p)*.6})`}
else if(k==='snap')st.opacity=p>=1?1:0;
else if(k==='grow'){st.transformOrigin='50% 100%';st.transform=`scaleY(${v})`}
else if(k==='growx'){st.transformOrigin='0 50%';st.transform=`scaleX(${v})`}
else if(k==='push'){const x=Math.min(1,Math.max(0,(T-s)/(e-s)));st.transform=`scale(${1+.07*x})`;st.transformOrigin=st.transformOrigin||'50% 50%'}
else if(k==='wipe')st.clipPath=`inset(-20px ${(1-v)*100}% -20px -20px)`;
else if(k==='draw')el.querySelectorAll('[pathLength]').forEach(pa=>{pa.style.strokeDasharray=1;pa.style.strokeDashoffset=1-v;pa.style.opacity=p>0?1:0});
else if(k==='count'){el.textContent=(+el.dataset.to*v).toFixed(+(el.dataset.dp||0))}
else if(k==='fill'){const ch=el.children;const n=Math.round(ch.length*v);for(let i=0;i<ch.length;i++)ch[i].style.opacity=i<n?1:0}
else if(k==='hide')st.opacity=p>=1?0:1;
else if(k==='bar'){const x=e>s?Math.min(1,Math.max(0,(T-s)/(e-s))):1;st.width=((+el.dataset.p0+(+el.dataset.p1-+el.dataset.p0)*x)*+el.dataset.w)+'px'}
else if(k==='move'){const x=e>s?Math.min(1,Math.max(0,(T-s)/(e-s))):(T>=s?1:0);st.transform=`translate(${(+el.dataset.dx||0)*(1-x)}px,${(+el.dataset.dy||0)*(1-x)}px)`}
else if(k==='flipout'){st.transform=`scaleX(${1-p})`;st.opacity=p>=1?0:1}
else if(k==='click')st.opacity=p>0?1:0;
else if(k==='type'){const n=+el.dataset.n||1;const x=e>s?Math.min(1,Math.max(0,(T-s)/(e-s))):(T>=s?1:0);const c=Math.floor(x*n+1e-6);st.width=`calc(${c}ch + ${c*(+el.dataset.ls||0)}px)`}
else if(k==='flipin'){st.transform=`scaleX(${p})`;st.opacity=p>0?1:0}});}
document.addEventListener('DOMContentLoaded',run);})()</script>"""


def page(body, src="", bg=MAT, ticks=True):
    """A 1920x1080 frame on the cutting mat. src = the bottom-left source line (mono caps), required on every frame."""
    rule = ""
    if ticks:  # the mat's ruler along the top edge
        rule = "".join(f'<div class="a" style="left:{x + 6}px;top:8px;font:500 12px Plex;letter-spacing:1px;color:rgba(143,160,181,.5)">{x // 40}</div>' for x in range(200, 1920, 200))
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}body{{margin:0;width:1920px;height:1080px;overflow:hidden;{bg};position:relative}}'
            f'.a{{position:absolute}}</style></head><body>{DEFS}{rule}{body}{GRAIN}'
            f'<div class="a" style="left:0;right:0;bottom:0;padding:26px 30px 12px;z-index:90;background:linear-gradient(transparent,rgba(6,8,14,.78) 55%);'
            f'font:500 13px/1.5 Plex;letter-spacing:1.2px;color:rgba(240,244,248,.66)">{src}</div>'
            + ANIM_JS + '<script>document.fonts.ready.then(()=>window.READY=true)</script></body></html>')


def put(name, html):
    (H / f"{name}.html").write_text(html, encoding="utf-8")


def A(html, x, y, anim="snap 0 0", extra=""):
    return f'<div class="a" data-anim="{anim}" style="left:{x}px;top:{y}px;{extra}">{html}</div>'


def a(html, x, y, extra=""):
    return f'<div class="a" style="left:{x}px;top:{y}px;{extra}">{html}</div>'


# ---- paper -----------------------------------------------------------------------------------------------------------------
SH = "box-shadow:16px 20px 0 rgba(5,7,12,.42),0 30px 60px rgba(5,7,12,.5)"   # rigid paper: a hard offset shadow plus a soft one
SH2 = "box-shadow:9px 11px 0 rgba(5,7,12,.4),0 16px 30px rgba(5,7,12,.45)"


def sheet(inner, w, h=None, rot=0.0, bg=PAPER, pad=40, sh=SH, extra=""):
    hh = f"height:{h}px;" if h else ""
    return f'<div style="width:{w}px;{hh}box-sizing:border-box;background:{bg};padding:{pad}px;{sh};transform:rotate({rot}deg);position:relative;{extra}">{inner}</div>'


def icard(inner, w, h, rot=0.0, pad=40, line=54, top=92, extra=""):
    """An index card: cobalt ruled lines under one heavier head rule."""
    bg = (f"background:{PAPER};background-image:linear-gradient({CO} 0 3px,transparent 3px),repeating-linear-gradient(transparent 0 {line - 2}px,rgba(43,108,176,.28) {line - 2}px {line}px);"
          f"background-size:100% {top}px,100% {line}px;background-position:0 {top - 3}px,0 {top}px;background-repeat:no-repeat,repeat-y")
    return (f'<div style="width:{w}px;height:{h}px;box-sizing:border-box;{bg};padding:{pad}px;{SH};transform:rotate({rot}deg);position:relative;border-radius:6px;{extra}">{inner}</div>')


def tape(w=170, rot=-4, col="rgba(214,224,236,.78)"):
    return f'<div style="width:{w}px;height:42px;background:{col};transform:rotate({rot}deg);box-shadow:0 3px 6px rgba(0,0,0,.3)"></div>'


def sticky(t, w=250, rot=4, size=46, col=INK, bg="#F7CFA5"):
    return (f'<div style="width:{w}px;min-height:{int(w * .8)}px;box-sizing:border-box;background:{bg};padding:22px 20px;transform:rotate({rot}deg);'
            f'box-shadow:8px 12px 0 rgba(5,7,12,.38);font:400 {size}px/1.05 Hand;color:{col}">{t}</div>')


def clip(x, y, rot=12):
    """A paper clip."""
    return a(f'<svg width="54" height="120" viewBox="0 0 54 120" style="transform:rotate({rot}deg);filter:drop-shadow(3px 4px 0 rgba(0,0,0,.35))">'
             f'<path d="M12 96 V30 a15 15 0 0 1 30 0 V92 a10 10 0 0 1 -20 0 V40" fill="none" stroke="#B9C4D2" stroke-width="6" stroke-linecap="round"/></svg>', x, y, "z-index:55")


# ---- type ------------------------------------------------------------------------------------------------------------------
def big(t, size, col=PAPER, lh=.92, font="Black", ls=-1, extra=""):
    return f'<div style="font:400 {size}px/{lh} {font};color:{col};letter-spacing:{ls}px;white-space:nowrap;text-transform:uppercase;{extra}">{t}</div>'


def mono(t, size=22, col=INK, ls=2, lh=1.35, w=None, extra=""):
    ww = f"width:{w}px;" if w else "white-space:nowrap;"
    return f'<div style="font:500 {size}px/{lh} Mono;color:{col};letter-spacing:{ls}px;{ww}{extra}">{t}</div>'


def tag(t, size=20, inv=False, rot=0.0, amber=False):
    """An archival tag: mono caps in a sharp box. Used for dates, exhibits and sarcastic captions alike."""
    bg, fg = (PAPER, SL) if inv else (SL, PAPER)
    if amber:
        bg, fg = AM, SL
    return (f'<div style="display:inline-block;background:{bg};color:{fg};border:2px solid {fg if not amber else SL};font:500 {size}px Mono;letter-spacing:{max(2, size // 6)}px;'
            f'padding:{size // 3}px {size // 1.6:.0f}px;white-space:nowrap;transform:rotate({rot}deg);box-shadow:6px 7px 0 rgba(5,7,12,.45);text-transform:uppercase">{t}</div>')


def hand(t, size=56, col=INK, rot=-2, w=None, font="Hand"):
    ww = f"width:{w}px;" if w else "white-space:nowrap;"
    return f'<div style="font:400 {size}px/1.08 {font};color:{col};{ww}transform:rotate({rot}deg)">{t}</div>'


def quote(t, size=64, col=INK, w=1100):
    return f'<div style="font:400 {size}px/1.12 Serif;color:{col};width:{w}px">{t}</div>'


def hl(t, col=AM):
    """A highlighter sweep over a phrase."""
    return f'<span style="background:linear-gradient(transparent 14%,{col} 14%,{col} 90%,transparent 90%);padding:0 6px;margin:0 -6px">{t}</span>'


def stamp(t, size=110, rot=-8, col=AM, sub=""):
    """A rubber stamp: rough inked edges, a double border."""
    s = f'<div style="font:400 {size * 2 // 3}px/1 Black;letter-spacing:6px;margin-top:8px;text-align:center">{sub}</div>' if sub else ""
    return (f'<div style="transform:rotate({rot}deg);filter:url(#rough)"><div style="border:{max(6, size // 12)}px solid {col};outline:{max(3, size // 30)}px solid {col};outline-offset:{max(5, size // 14)}px;'
            f'color:{col};font:400 {size}px/1 Black;letter-spacing:2px;padding:{size // 7}px {size // 3}px {size // 9}px;white-space:nowrap;text-transform:uppercase">{t}{s}</div></div>')


# ---- evidence --------------------------------------------------------------------------------------------------------------
def study(authors, year, journal, n="", note="", w=620, rot=-1.5):
    """A study card: authors, year, journal, sample size. Every claim on screen carries one."""
    nn = f'<div style="font:500 20px Mono;letter-spacing:2px;color:{INK};margin-top:14px">{n}</div>' if n else ""
    nt = f'<div style="display:inline-block;margin-top:14px;background:{SL};color:{PAPER};font:500 15px Mono;letter-spacing:2px;padding:5px 10px">{note}</div>' if note else ""
    return (f'<div style="width:{w}px;box-sizing:border-box;background:{PAPER};padding:24px 28px 26px;{SH2};transform:rotate({rot}deg);border-left:14px solid {CO};position:relative">'
            f'<div style="font:500 16px Mono;letter-spacing:5px;color:{CO}">STUDY CARD</div>'
            f'<div style="font:400 44px/1.02 Black;color:{INK};margin-top:10px;text-transform:uppercase;letter-spacing:-.5px">{authors}</div>'
            f'<div style="font:400 34px/1.1 Serif;color:#33405A;margin-top:8px">{journal}, {year}</div>{nn}{nt}</div>')


def photo(slug, w, h, rot=-1.5, pos="50% 50%", cap=None, tp=True, anim=None, border=14):
    """A real photo as a print on the desk: white border, tape, a halftone screen, its caption and credit."""
    c = CRED[slug]
    cap = c["on_screen_caption"] if cap is None else cap
    ht = ('<div style="position:absolute;inset:0;background-image:radial-gradient(rgba(20,24,36,.34) 1.1px,transparent 1.5px);background-size:5px 5px;mix-blend-mode:multiply"></div>')
    im = f'<img src="/assets/real/{slug}.jpg" style="width:{w}px;height:{h}px;object-fit:cover;object-position:{pos};display:block">'
    if anim:
        im = f'<div data-anim="{anim}" style="width:{w}px;height:{h}px">{im}</div>'
    tp_ = f'<div style="position:absolute;left:{w // 2 - 70}px;top:-22px">{tape(170, -rot * 2 - 3)}</div>' if tp else ""
    capd = (f'<div style="position:absolute;left:{border}px;bottom:{border + 34}px;background:rgba(20,24,36,.9);color:{PAPER};font:500 15px Mono;letter-spacing:2px;padding:6px 10px">{cap}</div>' if cap else "")
    return (f'<div style="position:relative;background:#FBFCFE;padding:{border}px {border}px {border + 34}px;{SH};transform:rotate({rot}deg)">'
            f'<div style="position:relative;overflow:hidden;width:{w}px;height:{h}px">{im}{ht}</div>{capd}{tp_}'
            f'<div style="position:absolute;left:{border}px;bottom:9px;font:500 12px Plex;letter-spacing:1px;color:#5B6880">PHOTO: {c["author"].upper()} · {c["licence"]}</div></div>')


def full(slug, pos="50% 50%", dim=.0, anim="push 0 1"):
    """A real photo full frame, with a halftone screen."""
    return (f'<div class="a" style="left:0;top:0;width:1920px;height:1080px;overflow:hidden"><div data-anim="{anim}" style="width:1920px;height:1080px">'
            f'<img src="/assets/real/{slug}.jpg" style="width:1920px;height:1080px;object-fit:cover;object-position:{pos};display:block"></div>'
            '<div style="position:absolute;inset:0;background-image:radial-gradient(rgba(20,24,36,.4) 1.2px,transparent 1.6px);background-size:6px 6px;mix-blend-mode:multiply"></div>'
            f'<div style="position:absolute;inset:0;background:rgba(20,24,36,{dim})"></div></div>')


def credit(slug):
    c = CRED[slug]
    return f'PHOTO: {c["author"].upper()}, {c["licence"]}'


# ---- marks -----------------------------------------------------------------------------------------------------------------
def wobble(cx, cy, rx, ry, seed=1, turns=1.08):
    r = random.Random(seed); pts = []
    for i in range(80):
        t = -.6 + 2 * math.pi * turns * i / 79; k = 1 + r.uniform(-.025, .025)
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    return "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)


def ring(cx, cy, rx, ry, anim="draw .5 .7", col=AM, w=9, seed=3):
    """The marker ring, drawn on."""
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:62;pointer-events:none" width="1920" height="1080">'
            f'<path d="{wobble(cx, cy, rx, ry, seed)}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/></svg>')


def arrow(x1, y1, x2, y2, anim="draw .5 .7", col=AM, w=8, bend=50):
    ang = math.atan2(y2 - y1, x2 - x1)
    hx, hy = x2 - 30 * math.cos(ang - .5), y2 - 30 * math.sin(ang - .5)
    kx, ky = x2 - 30 * math.cos(ang + .5), y2 - 30 * math.sin(ang + .5)
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:62;pointer-events:none" width="1920" height="1080">'
            f'<path d="M{x1} {y1} Q {(x1 + x2) / 2 + bend * math.sin(ang):.0f} {(y1 + y2) / 2 - bend * math.cos(ang):.0f} {x2} {y2}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M{hx:.0f} {hy:.0f} L{x2} {y2} L{kx:.0f} {ky:.0f}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def strike(w, col=CO, h=14, rot=-2):
    return f'<div style="position:absolute;left:-12px;top:50%;width:{w + 24}px;height:{h}px;background:{col};transform:rotate({rot}deg);filter:url(#wob)"></div>'


# ---- people (cut-out silhouettes; never a face) --------------------------------------------------------------------------------
def bust(x, y, s=1.0, col=INK, extra=""):
    """A head-and-shoulders silhouette, 100x120 at s=1, origin top left."""
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s})" {extra}><circle cx="50" cy="30" r="26" fill="{col}"/>'
            f'<path d="M4 120 C4 84 24 66 50 66 C76 66 96 84 96 120 Z" fill="{col}"/></g>')


def crowd(cols, rows, w, h, lit=(), col=DIM, lit_col=AM, anim=None, s=None):
    """A grid of busts; lit = indexes drawn in the signal colour. Returns an svg sized w x h."""
    cw, ch = w / cols, h / rows
    s = s or min(cw / 110, ch / 130)
    out = ""
    for i in range(cols * rows):
        x, y = (i % cols) * cw + (cw - 100 * s) / 2, (i // cols) * ch + (ch - 120 * s) / 2
        out += bust(x, y, s, lit_col if i in lit else col)
    an = f' data-anim="{anim}"' if anim else ""
    return f'<svg width="{w}" height="{h}"{an}>{out}</svg>'


# ---- charts (bars from zero; the one key value in amber) ---------------------------------------------------------------------
def bars(vals, labels, maxv, w=150, h=420, gap=70, cols=None, unit="%", size=74, dark=True, anims=None):
    fg = PAPER if dark else INK
    out = ""
    for i, v in enumerate(vals):
        col = (cols[i] if cols else AM)
        bh = max(4, round(h * v / maxv))
        an = f' data-anim="{anims[i]}"' if anims else ""
        out += (f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:{h + 110}px;width:{w}px">'
                f'<div style="font:400 {size}px/1 Black;color:{col};margin-bottom:10px">{v:g}{unit}</div>'
                f'<div{an} style="width:{w}px;height:{bh}px;background:{col}"></div></div>')
    lab = "".join(f'<div style="width:{w}px;text-align:center;font:500 24px/1.25 Mono;letter-spacing:2px;color:{fg};text-transform:uppercase">{l}</div>' for l in labels)
    return (f'<div><div style="display:flex;gap:{gap}px;align-items:flex-end;border-bottom:5px solid {fg}">{out}</div>'
            f'<div style="display:flex;gap:{gap}px;margin-top:12px">{lab}</div></div>')


def bar60(p, y=1012):
    """The thin amber 60-second bar: a bar, never a clock face."""
    return (a(f'<div style="width:1760px;height:14px;background:rgba(240,244,248,.14);border:2px solid rgba(240,244,248,.35);box-sizing:border-box"></div>', 80, y, "z-index:85")
            + a(f'<div style="width:{1756 * p:.0f}px;height:10px;background:{AM}"></div>', 82, y + 2, "z-index:86")
            + a(f'<div style="font:500 15px Mono;letter-spacing:3px;color:{AM}">60 S</div>', 1850, y - 4, "z-index:86"))
