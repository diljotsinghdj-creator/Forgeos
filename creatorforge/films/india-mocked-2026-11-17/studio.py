"""Studio helpers for "Why India Is Mocked Online" (16:9): page, positioned pieces with timeline entries (?t=0..1), logo D, grain."""
import json
import math
import random
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
sys.path.insert(0, "/home/user/forgeos/creatorforge/films/taxonomy-2026-11-15")
sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
H = D / "html"; H.mkdir(exist_ok=True)
BLK, PARCH, RED, SIG, INK = "#1A1A1A", "#F4EFE6", "#D93829", "#F7D046", "#1A1A1A"
FONTS = "".join(f"@font-face{{font-family:{n};src:url(/fonts/{f}.woff2)}}" for n, f in (
    ("Anton", "anton-latin-400-normal"), ("Plex", "ibm-plex-mono-latin-500-normal"), ("Caveat", "caveat-latin-700-normal"),
    ("Playfair", "playfair-display-latin-900-normal"), ("ISerif", "instrument-serif-latin-400-italic"), ("Grotesk", "space-grotesk-latin-700-normal"),
    ("Marker", "permanent-marker-latin-400-normal")))
GRAIN = ('<svg style="position:absolute;inset:0;pointer-events:none;opacity:.26;mix-blend-mode:multiply;z-index:80" width="1920" height="1080"><filter id="g">'
         '<feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3"/><feColorMatrix values="0 0 0 0 .4 0 0 0 0 .35 0 0 0 0 .3 0 0 0 .5 0"/></filter>'
         '<rect width="1920" height="1080" filter="url(#g)"/></svg>'
         '<div style="position:absolute;inset:0;pointer-events:none;z-index:81;background:radial-gradient(ellipse at 50% 48%,transparent 55%,rgba(20,14,8,.42) 100%)"></div>')


def logo_d(s=1.0, dark=True):
    fg = "#F3EFE6" if dark else INK
    return (f'<div style="display:inline-flex;align-items:center;gap:{8 * s:.0f}px;white-space:nowrap"><div style="font:700 {26 * s:.0f}px/1 Grotesk;color:{fg}">'
            f'PRINT <span style="color:{INK};background:linear-gradient(100deg,transparent 2%,{SIG} 4%,{SIG} 94%,transparent 97%);padding:0 {5 * s:.0f}px">FACTS</span></div>'
            f'<svg width="{26 * s:.0f}" height="{23 * s:.0f}" viewBox="0 0 34 30"><path d="M3 16 L12 25 L31 4" fill="none" stroke="{SIG}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')


def page(body, bg=PARCH, src="", dark=False, logo=True):
    if "AI1.jpg" in body:
        src += " · DESK: AI ILLUSTRATION"
    col = "rgba(255,255,255,.62)" if dark else "rgba(20,20,20,.6)"
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{bg};position:relative}}'
            f'.a{{position:absolute}}</style></head><body>{body}{GRAIN}'
            + (f'<div class="a" style="right:56px;top:44px;z-index:90">{logo_d(1.0, dark)}</div>' if logo else "")
            + f'<div class="a" style="left:0;right:0;bottom:0;padding:12px 30px;z-index:90;{"background:linear-gradient(transparent,rgba(0,0,0,.6) 40%)" if dark else ""};'
              f'font:500 13px/1.5 Plex;letter-spacing:1px;color:{col}">{src}</div>'
            + ANIM_JS + '<script>document.fonts.ready.then(()=>window.READY=window.READY||!window.WAIT)</script></body></html>')


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
else if(k==='wipe')st.clipPath=`inset(-20px ${(1-v)*100}% -20px -20px)`;
else if(k==='draw')el.querySelectorAll('[pathLength]').forEach(pa=>{pa.style.strokeDasharray=1;pa.style.strokeDashoffset=1-v;pa.style.opacity=p>0?1:0});
else if(k==='flow')el.querySelectorAll('path').forEach(pa=>{pa.style.strokeDashoffset=-(T*s)})
else if(k==='count'){el.textContent=Math.round(+el.dataset.to*v).toLocaleString('en-US')}
else if(k==='fill'){const ch=el.children;const n=Math.round(ch.length*v);for(let i=0;i<ch.length;i++)ch[i].style.opacity=i<n?1:0}});}
document.addEventListener('DOMContentLoaded',run);})()</script>"""


def A(html, x, y, anim, extra=""):
    """A positioned piece with a timeline entry: anim = "kind start end", t from 0 to 1 over the shot."""
    return f'<div class="a" data-anim="{anim}" style="left:{x}px;top:{y}px;{extra}">{html}</div>'


def a(html, x, y, extra=""):
    return f'<div class="a" style="left:{x}px;top:{y}px;{extra}">{html}</div>'


def put(name, html):
    (H / f"{name}.html").write_text(html, encoding="utf-8")


def hl(t):
    return f'<span style="background:linear-gradient(transparent 50%,{SIG} 50%,{SIG} 92%,transparent 92%)">{t}</span>'


def wobble(cx, cy, rx, ry, seed=1):
    r = random.Random(seed); pts = []
    for i in range(80):
        t = -.5 + 2 * math.pi * 1.1 * i / 79; k = 1 + r.uniform(-.03, .03)
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    return "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)


def chapter(n, t):
    return a(f'<div style="background:{INK};color:{PARCH};padding:8px 16px;font:500 20px Plex;letter-spacing:5px">CHAPTER {n} · {t}</div>', 70, 60)


def tape(x, y, rot):
    return a(f'<div style="width:150px;height:40px;background:rgba(236,226,200,.85);transform:rotate({rot}deg);box-shadow:0 2px 4px rgba(0,0,0,.25)"></div>', x, y, "z-index:20")


DESK = "background:#3A2A1C url(/assets/ai/AI1.jpg) center/cover"  # AI·1 walnut desk plate (owner, 2026-11-19; MASTER_DIRECTIVES 8c), studio-finished by ai_finish.py
img = lambda f, w, h, extra="": f'<img src="/assets/{f}" style="width:{w}px;height:{h}px;object-fit:cover;display:block;{extra}">'
cut = lambda f, w, extra="": f'<img src="/assets/{f}" style="width:{w}px;display:block;filter:drop-shadow(0 22px 22px rgba(0,0,0,.45));{extra}">'

