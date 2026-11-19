"""Key frames (16:9) for "Pepper Was Money", draft 4; every piece carries a timeline entry (render any moment with ?t=0..1) (Vox x Johnny Harris). Numbers only from dossier.json."""
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


DESK = "background:#3A2A1C;background-image:repeating-linear-gradient(90deg,rgba(0,0,0,.08) 0 3px,transparent 3px 41px),radial-gradient(ellipse at 40% 40%,#5A4128,#2A1D12 80%)"
img = lambda f, w, h, extra="": f'<img src="/assets/{f}" style="width:{w}px;height:{h}px;object-fit:cover;display:block;{extra}">'
cut = lambda f, w, extra="": f'<img src="/assets/{f}" style="width:{w}px;display:block;filter:drop-shadow(0 22px 22px rgba(0,0,0,.45));{extra}">'

# ---- cold open --------------------------------------------------------------------------------------------------------
put("01_jar", page(a(img("corns_spoon.jpg", 1920, 1080, "filter:brightness(.6) contrast(1.05)"), 0, 0)
                   + A('<div style="font:700 64px/1.1 Caveat;color:#F3EFE6;width:900px;transform:rotate(-2deg)">I\'d never given it a second thought.</div>', 1000, 760, "fade .35 .55")
                   + A(f'<div style="font:500 22px Plex;letter-spacing:4px;color:{SIG}">ON ALMOST EVERY TABLE IN INDIA</div>', 1004, 700, "fade .1 .25"),
                   "#000", "PHOTO: PIXABAY", dark=True))

ransom_rows = [("5,000 lb", "of gold"), ("30,000 lb", "of silver"), ("4,000", "silk tunics"), ("3,000", "scarlet skins"), ("3,000 lb", "of pepper")]
rows = "".join(f'<div data-anim="up {.14 + i * .12:.2f} {.24 + i * .12:.2f}" style="display:flex;gap:28px;font:400 46px/1.55 Playfair;color:#2A2118"><span style="width:250px;text-align:right">{q}</span>'
               f'<span>{hl(w) if "pepper" in w else w}</span></div>' for i, (q, w) in enumerate(ransom_rows))
doc = (f'<div style="width:880px;background:#F4ECD8;padding:56px 64px;box-shadow:0 30px 60px rgba(0,0,0,.6);transform:rotate(-1.5deg)">'
       f'<div style="font:500 18px Plex;letter-spacing:4px;color:#7A6A4A">ROME · 408 CE · THE PRICE OF PEACE</div>'
       f'<div style="font:400 40px/1.3 ISerif;color:#2A2118;margin:16px 0 26px">The city agreed to pay the besieging army:</div>{rows}'
       f'<div style="font:500 15px Plex;color:#7A6A4A;margin-top:24px">From Zosimus, <i>New History</i> 5.41 (Greek, c. 500 CE); English after the 1814 translation and J. B. Bury. Page set in the studio.</div></div>')
put("02_ransom", page(a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0) + A(doc, 120, 150, "up 0 .12")
                      + f'<svg class="a" data-anim="draw .74 .86" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{wobble(590, 652, 230, 40, 4)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
                      + A(cut("scale.png", 640), 1150, 260, "fade 0 .15") + a(cut("corns_spoon.jpg", 1, "display:none"), 0, 0)
                      + A(f'<div style="font:700 56px/1.05 Caveat;color:{SIG};width:520px;transform:rotate(-3deg)">pepper.<br>in a ransom.<br>next to gold.</div>', 150, 860, "fade .88 1"),
                      "#2A1D12", "RANSOM LIST: ZOSIMUS, NEW HISTORY 5.41 (408 CE) · PHOTO: PIXABAY", dark=True))

put("03_title", page(a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
                     + A(cut("scale.png", 760), 580, 120, "fade 0 .25")
                     + A(f'<div style="font:400 210px/0.86 Anton;color:#F3EFE6;text-align:center;width:1920px;text-shadow:0 10px 40px rgba(0,0,0,.6)">PEPPER<br>WAS {hl("<span style=\'color:#141414\'>MONEY</span>")}</div>', 0, 330, "slam .2 .24")
                     + A('<div style="font:400 44px ISerif;color:#E8DCC2;text-align:center;width:1920px">so how does a spice become money?</div>', 0, 900, "fade .6 .8"),
                     "#2A1D12", "PHOTO: PIXABAY", dark=True))

# ---- 1: the map table ------------------------------------------------------------------------------------------------
pins = [(820, 640, "MALABAR", "the vine grows here"), (520, 420, "RED SEA", ""), (360, 250, "ALEXANDRIA", "")]
pin = lambda x, y: (f'<circle cx="{x}" cy="{y}" r="13" fill="{RED}"/><circle cx="{x - 4}" cy="{y - 4}" r="4" fill="#FF9A90"/>')
string = f'<path d="M820 640 Q 700 520 520 420 Q 430 330 360 250" fill="none" stroke="{RED}" stroke-width="4" stroke-dasharray="1" pathLength="1" opacity=".9"/>'
put("04_maptable", page(a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
                        + a(img("chart.jpg", 1500, 1107, "filter:sepia(.25) contrast(1.05)"), 210, 40, "transform:rotate(-2deg);box-shadow:0 30px 60px rgba(0,0,0,.6)")
                        + f'<svg class="a" data-anim="draw .28 .75" style="left:0;top:0;z-index:30" width="1920" height="1080">{string}</svg>'
                        + "".join(A(f'<svg width="30" height="30" viewBox="{x - 15} {y - 15} 30 30" style="display:block">{pin(x, y)}</svg>', x - 15, y - 15, f"pop {.05 + i * .08:.2f} {.12 + i * .08:.2f}", "z-index:30") for i, (x, y, *_) in enumerate(pins))
                        + A(f'<div style="background:{PARCH};padding:8px 14px;font:700 40px Caveat;color:{INK};transform:rotate(3deg);box-shadow:0 8px 14px rgba(0,0,0,.4)">Malabar: the vine grows here</div>', 860, 660, "drop .1 .2", "z-index:31")
                        + chapter(1, "WHERE IT GROWS")
                        + A(f'<div style="background:{INK};padding:6px 18px;font:700 46px Caveat;color:{SIG};transform:rotate(-2deg);box-shadow:6px 6px 0 rgba(0,0,0,.35)">"I started where the pepper starts. On a map."</div>', 120, 930, "fade .8 .92", "z-index:31"),
                        "#2A1D12", "PINS AND STRING PLACED BY HAND, POSITIONS APPROXIMATE · MAP: LINSCHOTEN, 1596, 'MAP OUTLINING THE MARITIME COASTS OF ARABIA FELIX…', LIBRARY OF CONGRESS (PUBLIC DOMAIN BY AGE) · A DATED HISTORICAL DOCUMENT, NOT A MODERN BOUNDARY", dark=True))

# ---- 1: the vine and the three peppers -------------------------------------------------------------------------------
card = lambda f, t, s, rot, crop="": (f'<div style="width:400px;background:#FBF8F0;padding:14px 14px 18px;transform:rotate({rot}deg);box-shadow:0 18px 30px rgba(0,0,0,.35)">'
                                      f'{img(f, 372, 300, crop)}<div style="font:400 44px Anton;color:{INK};margin-top:10px">{t}</div><div style="font:700 30px Caveat;color:#555">{s}</div></div>')
put("05_three", page(a(img("vine.jpg", 1920, 1080, "filter:brightness(.45) blur(2px)"), 0, 0)
                     + chapter(1, "WHERE IT GROWS")
                     + A(f'<div style="font:400 92px/0.95 Anton;color:#F3EFE6">ONE VINE, THREE PEPPERS</div><div style="font:400 40px ISerif;color:#E8DCC2;margin-top:8px"><i>Piper nigrum</i>, from India\'s Western Ghats</div>', 90, 130, "up 0 .1")
                     + A(card("corns_spoon.jpg", "BLACK", "unripe, dried", -3), 160, 420, "drop .15 .27") + A(card("corns.jpg", "WHITE", "riper, outer skin removed", 2), 760, 400, "drop .4 .52")
                     + A(card("green.jpg", "GREEN", "unripe, preserved", -2), 1360, 430, "drop .65 .77"),
                     "#000", "BOTANY: ROYAL BOTANIC GARDENS KEW, PLANTS OF THE WORLD ONLINE · PHOTOS: PIXABAY", dark=True))

# ---- 2: Pliny's prices -----------------------------------------------------------------------------------------------
bars = [("LONG", 15), ("WHITE", 7), ("BLACK", 4)]
bh = "".join(A(f'<div style="width:220px;height:{v * 34}px;background:{SIG if n == "BLACK" else "#3A3F4B"}"></div>', 900 + i * 300, 900 - v * 34, f"grow {.38 + i * .17:.2f} {.52 + i * .17:.2f}")
             + A(f'<div style="font:400 64px Anton;color:{INK};text-align:center;width:220px">{v}</div>', 900 + i * 300, 900 - v * 34 - 82, f"fade {.5 + i * .17:.2f} {.55 + i * .17:.2f}")
             + a(f'<div style="font:500 24px Plex;letter-spacing:4px;color:{INK};text-align:center;width:220px">{n}</div>', 900 + i * 300, 916)
             for i, (n, v) in enumerate(bars))
put("06_pliny", page(chapter(2, "ROME PAYS BY THE POUND")
                     + A(f'<div style="width:620px;background:#F4ECD8;padding:40px 44px;box-shadow:0 22px 40px rgba(0,0,0,.3);transform:rotate(-2deg)">'
                         f'<div style="font:500 16px Plex;letter-spacing:4px;color:#7A6A4A">PLINY THE ELDER · NATURAL HISTORY 12.14 · c. 77 CE</div>'
                         f'<div style="font:400 40px/1.35 ISerif;color:#2A2118;margin-top:16px">"…we buy them by weight, {hl("just as if they were so much gold or silver.")}"</div></div>', 110, 200, "up 0 .12")
                     + A('<div style="font:700 50px Caveat;color:#7A2A20;transform:rotate(-3deg)">"I went looking for receipts.<br>Rome left some."</div>', 140, 640, "fade .2 .32")
                     + A(f'<div style="font:500 22px Plex;letter-spacing:4px;color:{INK}">DENARII PER ROMAN POUND</div>', 900, 240, "fade .3 .36")
                     + bh + a(f'<div style="width:880px;height:4px;background:{INK}"></div>', 880, 900),
                     PARCH, "PRICES: PLINY, NATURAL HISTORY 12.14 (12.28–29) · TRANSLATION: BOSTOCK &amp; RILEY · BARS FROM ZERO"))

# ---- 2: the myth -----------------------------------------------------------------------------------------------------
sacks = "".join(f'<div style="position:absolute;left:{(i % 28) * 34}px;top:{(i // 28) * 34}px;width:26px;height:26px;border-radius:6px;background:{BLK}"></div>' for i in range(280))
put("07_myth", page(chapter(2, "ROME PAYS BY THE POUND")
                    + a(f'<div style="font:400 84px/0.95 Anton;color:{INK};width:900px">"WORTH ITS WEIGHT IN GOLD"</div>', 90, 140)
                    + A(f'<div style="border:8px solid {RED};color:{RED};font:400 120px/1 Anton;letter-spacing:8px;padding:4px 30px;transform:rotate(-10deg);background:rgba(239,230,210,.7)">MYTH</div>', 1060, 110, "slam .9 .93")
                    + A(cut("gold.png", 300), 110, 420, "pop .1 .2")
                    + A(f'<div style="font:400 56px Anton;color:{INK}">1 POUND OF GOLD</div><div style="font:500 22px Plex;color:#555">≈ 1,125 denarii</div>', 110, 760, "fade .18 .26")
                    + A(f'<div style="font:400 64px Anton;color:{INK}">=</div>', 520, 520, "fade .26 .3")
                    + a(f'<div data-anim="fill .3 .78" style="position:relative;width:960px;height:340px">{sacks}</div>', 640, 400)
                    + A(f'<div style="font:400 56px Anton;color:{INK}">{hl("280")} POUNDS OF BLACK PEPPER</div><div style="font:500 22px Plex;color:#555">at 4 denarii a pound</div>', 640, 760, "fade .76 .82")
                    + A(f'<div style="font:700 46px Caveat;color:#7A2A20;transform:rotate(-2deg)">sold like gold. not priced like gold.</div>', 640, 870, "fade .82 .88"),
                    PARCH, "GOLD: 45 AUREI TO THE ROMAN POUND AFTER NERO, 25 DENARII EACH: OUR CALCULATION · PEPPER: PLINY, NATURAL HISTORY 12.14 · ONE SQUARE = ONE POUND OF PEPPER"))

# ---- 2: the drain ----------------------------------------------------------------------------------------------------
put("08_drain", page(chapter(2, "ROME PAYS BY THE POUND")
                     + A(f'<div style="font:400 40px ISerif;color:#CFC6B4">Every year, Pliny says, India took at least</div>', 130, 260, "fade 0 .1")
                     + a(f'<div style="font:400 230px/1 Anton;color:{SIG};text-shadow:0 0 40px rgba(247,208,70,.5)"><span data-anim="count .1 .6" data-to="50000000">50,000,000</span></div><div data-anim="fade .58 .66" style="font:400 64px Anton;color:#F3EFE6">SESTERCES</div>', 120, 330)
                     + A(f'<div style="font:500 24px/1.5 Plex;color:#CFC6B4;width:640px">out of the Roman Empire, "sold with us at a hundred times its prime cost".</div>', 120, 760, "fade .66 .8")
                     + A(f'<div style="font:500 20px Plex;letter-spacing:4px;color:{SIG}">INDIA ALONE · NATURAL HISTORY 6.26</div>', 1250, 300, "fade .8 .9")
                     + a(cut("corns_spoon.jpg", 1, "display:none"), 0, 0),
                     "#0D0C0A", "SOURCE: PLINY, NATURAL HISTORY 6.26 (6.101), FORDHAM ANCIENT HISTORY SOURCEBOOK · AN OLDER TRANSLATION READS 550 MILLION; MODERN READINGS GIVE 50 MILLION", dark=True))

# ---- 2: the receipt (Muziris papyrus) --------------------------------------------------------------------------------
papy = (f'<div style="width:760px;height:600px;background:linear-gradient(135deg,#C9A970,#B48E52 60%,#A57E44);box-shadow:0 26px 50px rgba(0,0,0,.55);transform:rotate(2deg);'
        f'clip-path:polygon(2% 4%,30% 0,62% 3%,98% 1%,100% 40%,97% 70%,99% 97%,60% 100%,25% 96%,0 99%,3% 60%,0 30%);position:relative">'
        + "".join(f'<div style="position:absolute;left:{60 + (i % 3) * 8}px;top:{60 + i * 34}px;width:{560 + random.Random(i).randint(-80, 60)}px;height:6px;background:rgba(60,40,15,.45);border-radius:3px"></div>' for i in range(15))
        + f'<div style="position:absolute;left:40px;bottom:24px;font:500 16px Plex;color:#3A2A12;background:rgba(244,236,216,.85);padding:6px 10px">RECONSTRUCTION · THE ORIGINAL IS P.Vindob. G 40822, AUSTRIAN NATIONAL LIBRARY</div></div>')
put("09_papyrus", page(a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0) + chapter(2, "ROME PAYS BY THE POUND")
                       + A(papy, 120, 220, "up 0 .15")
                       + A(f'<div style="font:700 64px/1.05 Caveat;color:{SIG};transform:rotate(-3deg)">"And then I found this."</div>', 1000, 170, "fade .2 .3")
                       + A(f'<div style="width:760px;background:{PARCH};padding:30px 34px;box-shadow:0 20px 34px rgba(0,0,0,.5)">'
                           f'<div style="font:500 18px Plex;letter-spacing:4px;color:#7A6A4A">ONE SHIP FROM MUZIRIS · 2ND CENTURY CE</div>'
                           f'<div style="font:400 84px/1 Anton;color:{INK};margin-top:10px">≈ 1,150 TALENTS</div><div style="font:400 34px ISerif;color:#555">close to seven million drachmas</div>'
                           f'<div style="display:flex;height:46px;margin-top:22px;background:#BDB4A0"><div data-anim="wipe .58 .78" style="width:66%;background:{SIG}"></div></div>'
                           f'<div style="font:500 18px Plex;color:#555;margin-top:8px">PEPPER: AT LEAST ⅔ (A SCHOLARLY ESTIMATE)</div></div>', 1000, 360, "up .36 .5") + tape(1300, 342, -4).replace('class="a"', 'class="a" data-anim="fade .48 .52"', 1),
                       "#2A1D12", "THE MUZIRIS PAPYRUS: DE ROMANIS (ISAW PAPERS 8; OUP 2020); CASSON, ZPE 1990 · VALUE READINGS 1,151–1,155 TALENTS · PAPYRUS SHOWN AS A STUDIO RECONSTRUCTION", dark=True))

# ---- 3: the three rules ----------------------------------------------------------------------------------------------
rule = lambda n, t, s: (f'<div data-anim="up {.12 + n * .2:.2f} {.22 + n * .2:.2f}" style="display:flex;align-items:center;gap:26px;margin-bottom:34px"><svg data-anim="draw {.24 + n * .2:.2f} {.3 + n * .2:.2f}" width="70" height="62" viewBox="0 0 34 30"><path d="M3 16 L12 25 L31 4" pathLength="1" fill="none" stroke="{SIG}" stroke-width="5" stroke-linecap="round"/></svg>'
                        f'<div><div style="font:400 64px/1 Anton;color:#F3EFE6">{n}. {t}</div><div style="font:400 34px ISerif;color:#CFC6B4">{s}</div></div></div>')
put("10_rules", page(a(f'<div style="width:1920px;height:1080px;background:#22302A;background-image:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1.5px);background-size:6px 6px"></div>', 0, 0)
                     + chapter(3, "WHAT MAKES MONEY, MONEY")
                     + A(f'<div style="font:700 56px Caveat;color:#ECEADF">What does money need to do?</div>', 120, 170, "fade 0 .1")
                     + a(rule(1, "IT LASTS", "dried pepper keeps for years") + rule(2, "SMALL BUT VALUABLE", "a sack is a fortune you can carry") + rule(3, "EVERYONE ACCEPTS IT", "and everybody wanted pepper"), 120, 300)
                     + a(cut("corns.png", 520), 1260, 380),
                     "#22302A", "EXPLAINER DRAWN IN THE STUDIO · PHOTO: PIXABAY", dark=True))

# ---- 4: the rent timeline --------------------------------------------------------------------------------------------
tl = [("c.1000", "LONDON", "10 lb pepper owed to the king at Christmas and Easter"), ("1156", "GENOA", "a debt payable in pepper or in coin"),
      ("1194", "RAMSEY ABBEY", "rent: 1,000 eels, 2 lb pepper, 2 lb ginger, scarlet trousers"), ("c.1270", "KENT", "half a pound of pepper a year for land"),
      ("1286", "SCOTLAND", "a deal settled with one pound of pepper")]
row = "".join(A(f'<div style="width:300px"><div style="width:22px;height:22px;border-radius:50%;background:{RED};margin-bottom:16px"></div>'
                f'<div style="font:400 50px Anton;color:{INK}">{y}</div><div style="font:500 20px Plex;letter-spacing:3px;color:#7A2A20">{p}</div>'
                f'<div style="font:700 34px/1.1 Caveat;color:#333;margin-top:6px">{t}</div></div>', 110 + i * 350, 600, f"up {.16 + i * .15:.2f} {.24 + i * .15:.2f}") for i, (y, p, t) in enumerate(tl))
put("11_rents", page(chapter(4, "PAYING THE RENT IN PEPPER")
                     + A(f'<div style="font:400 92px/0.95 Anton;color:{INK};width:1300px">NOT BOUGHT WITH MONEY.<br>{hl("PAID AS MONEY.")}</div>', 110, 160, "up 0 .1")
                     + A(f'<div style="width:1700px;height:4px;background:{INK}"></div>', 110, 610, "wipe .12 .85") + row
                     + A(cut("ginger.png", 260), 1560, 300, "pop .46 .54"),
                     PARCH, "SOURCES: ANGLO-SAXON LONDON TOLL CODE ('IV ÆTHELRED', DATE DISPUTED); HUNT ET AL., DOC. 10.1 (GENOA 1156); BBC HISTORY MAGAZINE (RAMSEY 1194); BODLEIAN CHARTER 113275 (KENT); PEOPLE OF MEDIEVAL SCOTLAND (1286) · PHOTO: PIXABAY"))

# ---- 4: the Kent charter ---------------------------------------------------------------------------------------------
charter = (f'<div style="width:820px;height:560px;background:#EADFC4;box-shadow:0 26px 50px rgba(0,0,0,.55);transform:rotate(-2deg);position:relative;padding:60px 70px;box-sizing:border-box">'
           + "".join(f'<div style="height:7px;background:rgba(60,40,20,.38);border-radius:3px;margin-bottom:22px;width:{88 + random.Random(i + 9).randint(-8, 8)}%"></div>' for i in range(12))
           + f'<div style="position:absolute;right:60px;bottom:-40px;width:110px;height:110px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#C0392B,#7B1D14)"></div>'
           + f'<div style="position:absolute;left:30px;bottom:18px;font:500 15px Plex;color:#3A2A12">RECONSTRUCTION · THE ORIGINAL IS BODLEIAN CHARTER 113275</div></div>')
put("12_charter", page(a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0) + chapter(4, "PAYING THE RENT IN PEPPER")
                       + A(charter, 120, 230, "up 0 .15")
                       + f'<svg class="a" data-anim="draw .25 .42" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{wobble(520, 560, 300, 50, 7)}" pathLength="1" fill="none" stroke="{SIG}" stroke-width="6"/></svg>'
                       + A(f'<div style="width:700px;background:{PARCH};padding:30px 34px;box-shadow:0 20px 34px rgba(0,0,0,.5)">'
                           f'<div style="font:500 18px Plex;letter-spacing:4px;color:#7A6A4A">KENT · c. 1270</div><div style="font:400 72px/1 Anton;color:{INK};margin-top:8px">RENT: ½ LB OF PEPPER</div>'
                           f'<div style="font:400 34px ISerif;color:#555">a year, for a plot of land, granted to Tonbridge Priory</div></div>', 1080, 300, "up .48 .6")
                       + A(f'<div style="font:700 56px/1.1 Caveat;color:{SIG};transform:rotate(-2deg);width:700px">"I looked it up: the charter still exists. It\'s in Oxford."</div>', 1090, 620, "fade .74 .86"),
                       "#2A1D12", "SOURCE: BODLEIAN LIBRARY, MEDIEVAL CHARTERS, CHARTER 113275 (DATE c. 1270, MARKED UNCERTAIN) · CHARTER SHOWN AS A STUDIO RECONSTRUCTION", dark=True))

# ---- 5: the markup on the map table ---------------------------------------------------------------------------------
tag = lambda x, y, t, rot, an="fade 0 0": A(f'<div style="background:{PARCH};padding:8px 14px;font:700 40px Caveat;color:{INK};transform:rotate({rot}deg);box-shadow:0 8px 14px rgba(0,0,0,.4);white-space:nowrap">{t}</div>', x, y, an, "z-index:31")
put("13_markup", page(a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
                      + a(img("chart.jpg", 1500, 1107, "filter:sepia(.25) contrast(1.05) brightness(.9)"), 210, 40, "transform:rotate(-2deg);box-shadow:0 30px 60px rgba(0,0,0,.6)")
                      + f'<svg class="a" data-anim="draw .05 .62" style="left:0;top:0;z-index:30" width="1920" height="1080">'
                        f'<path d="M820 640 Q 700 520 520 420 Q 430 330 360 250 Q 300 160 230 110" pathLength="1" fill="none" stroke="{RED}" stroke-width="4" opacity=".9"/>{"".join(pin(x, y) for x, y, *_ in pins)}{pin(230, 110)}</svg>'
                      + tag(860, 650, "Calicut: ~3 ducats", 3, "drop .08 .16") + tag(380, 290, "Alexandria → Venice: 42 → 56", 2, "drop .4 .48") + tag(110, 140, "Europe: ~80 ducats", -3, "drop .6 .68")
                      + chapter(5, "THE MARKUP")
                      + A(f'<div style="background:{SIG};color:{INK};padding:14px 22px;transform:rotate(-2deg)"><div style="font:400 64px/1 Anton">~25× ON THE WAY</div>'
                          f'<div style="font:500 18px Plex;letter-spacing:3px">PER HUNDREDWEIGHT, 15TH CENTURY (UNESCO ESTIMATE)</div></div>', 1140, 820, "slam .74 .77", "z-index:31"),
                      "#2A1D12", "PRICES: UNESCO SILK ROADS, 'THE ARAB MONOPOLY' (ESTIMATE); LANE, JOURNAL OF ECONOMIC HISTORY 28 (1968), 1497 · MAP: LINSCHOTEN 1596, LIBRARY OF CONGRESS", dark=True))

# ---- 7: too much pepper + the peppercorn rent -----------------------------------------------------------------------
pts = [(0, 100), (1, 104), (2, 98), (3, 92), (4, 80), (5, 66), (6, 58), (7, 52)]
X = lambda i: 120 + i * 110; Y = lambda v: 860 - v * 3
line = "M" + " L".join(f"{X(i)} {Y(v)}" for i, v in pts)
put("14_fall", page(chapter(7, "TOO MUCH PEPPER")
                    + A(f'<div style="font:400 92px/0.95 Anton;color:{INK};width:900px">MORE SHIPS,<br>MORE PEPPER,<br>{hl("LOWER PRICES")}</div>', 110, 150, "up 0 .1")
                    + f'<svg class="a" data-anim="draw .12 .5" style="left:0;top:0" width="1920" height="1080"><path d="{line}" pathLength="1" fill="none" stroke="{RED}" stroke-width="7"/>'
                      f'<line x1="110" y1="860" x2="920" y2="860" stroke="{INK}" stroke-width="3"/></svg>'
                    + a(f'<div style="font:500 18px Plex;letter-spacing:3px;color:#555">ILLUSTRATIVE TREND · 1500s → 1600s</div>', 120, 880)
                    + A(f'<div style="width:760px;background:#FBF9F3;padding:36px 40px;box-shadow:0 22px 40px rgba(0,0,0,.25);transform:rotate(1.5deg)">'
                        f'<div style="font:500 16px Plex;letter-spacing:3px;color:#7A6A4A">LEASEHOLD REFORM (GROUND RENT) ACT 2022 · UK</div>'
                        f'<div style="font:400 44px/1.3 ISerif;color:{INK};margin-top:14px">a "peppercorn rent" means {hl("an annual rent of one peppercorn")}</div>'
                        f'<div style="font:700 36px/1.15 Caveat;color:#7A2A20;margin-top:22px">"…even if the person paid doesn\'t like pepper." Chappell v Nestlé, 1960</div></div>', 1040, 260, "up .52 .64")
                    + A(cut("corns.png", 160), 1650, 760, "pop .64 .72"),
                    PARCH, "TREND: PRICES FELL IN THE 1600s (ENCYCLOPEDIA.COM, 'SPICES AND THE SPICE TRADE'); LINE IS ILLUSTRATIVE, NOT A PRICE SERIES · LAW: LEGISLATION.GOV.UK, UKPGA 2022 c. 1; CHAPPELL &amp; CO v NESTLÉ [1960] AC 87"))

# ---- 8: today -------------------------------------------------------------------------------------------------------
prod = [("VIETNAM", 257), ("BRAZIL", 126.5), ("INDONESIA", 70.2), ("INDIA (FAO)", 65.7)]
bub = ""
xs = [110, 640, 1000, 1290]
for i, (n, v) in enumerate(prod):
    dia = 2 * math.sqrt(v) * 13.5
    bub += A(f'<div style="width:{dia:.0f}px;height:{dia:.0f}px;border-radius:50%;background:{SIG if i == 0 else "#3A3F4B"};display:flex;align-items:center;justify-content:center;'
             f'font:400 {40 if i == 0 else 26}px Anton;color:{INK if i == 0 else "#F3EFE6"}">{v:.0f}k t</div><div style="font:500 20px Plex;letter-spacing:3px;color:#F3EFE6;margin-top:10px">{n}</div>',
             xs[i], 300 + (440 - dia), f"pop {.15 + i * .15:.2f} {.25 + i * .15:.2f}")
put("15_today", page(chapter(8, "PEPPER TODAY")
                     + a(f'<div style="font:400 84px/0.95 Anton;color:#F3EFE6">WHO GROWS IT NOW</div><div style="font:400 36px ISerif;color:#CFC6B4">tonnes, 2023</div>', 110, 130)
                     + bub
                     + A(f'<div style="width:520px;background:{PARCH};padding:22px 26px;box-shadow:0 18px 30px rgba(0,0,0,.5);transform:rotate(-2deg)">'
                         f'<div style="font:500 16px Plex;letter-spacing:3px;color:#7A6A4A">INSIDE INDIA · SPICES BOARD, 2023-24</div>'
                         f'<div style="font:400 50px/1.05 Anton;color:{INK};margin-top:8px">KARNATAKA ~71%<br>KERALA ~22%</div>'
                         f'<div style="font:700 32px Caveat;color:#7A2A20">pepper began in Kerala. Karnataka grows most now.</div></div>', 1300, 140, "up .78 .9"),
                     "#0D0C0A", "WORLD: FAO (ITEM 0687) VIA TRIDGE, 2023 · INDIA: SPICES BOARD (125,000 t, 2023-24); FAO GIVES ~66,000 t FOR INDIA: THE SOURCES DIFFER · CIRCLE AREA ∝ TONNES", dark=True))

put("16_kochi", page(a(img("sacks.jpg", 1920, 1080, "filter:brightness(.62) saturate(1.05)"), 0, 0) + chapter(8, "PEPPER TODAY")
                     + A(f'<div style="background:{SIG};color:{INK};padding:18px 28px;transform:rotate(-2deg)"><div style="font:500 22px Plex;letter-spacing:4px">KOCHI · BLACK PEPPER · WHOLESALE</div>'
                         f'<div style="font:400 150px/1 Anton">₹695 / KG</div><div style="font:500 20px Plex;letter-spacing:2px">UNGARBLED, 22 AUG 2026 · "INDICATIVE"</div></div>', 120, 560, "slam .45 .48")
                     + A(f'<div style="font:700 56px/1.1 Caveat;color:#F3EFE6;width:760px;transform:rotate(-2deg)">Rome once paid a ransom with this.</div>', 1060, 220, "fade .12 .28"),
                     "#000", "PRICE: SPICES BOARD INDIA, 'SPICE MARKET' WEEKLY, 22.08.2026 (LATEST INDEXED; REFRESH BEFORE AIR) · PHOTO: PIXABAY (SPICE SACKS, ILLUSTRATIVE)", dark=True))

put("17_end", page(a(img("corns_spoon.jpg", 1920, 1080, "filter:brightness(.38) contrast(1.05)"), 0, 0)
                   + A(f'<div style="font:400 44px ISerif;color:#E8DCC2;width:1300px">It lasts. It\'s worth a lot for its size. Everyone agrees to want it.</div>', 120, 300, "fade .05 .22")
                   + A(f'<div style="background:{SIG};color:{INK};padding:18px 30px;font:400 72px/1.05 Anton;width:1300px">WHAT ARE WE TREATING AS MONEY TODAY THAT PEOPLE WILL ONE DAY FIND JUST AS STRANGE?</div>', 120, 470, "wipe .35 .6"),
                   "#000", "PRINT FACTS · SOURCES IN THE DESCRIPTION · PHOTO: PIXABAY", dark=True))

# ---- 6: the globe (route round Africa) -------------------------------------------------------------------------------
from taxonomy import globe
route = [(-9.14, 38.72), (-17.0, 14.0), (-5.0, -15.0), (18.47, -36.0), (40.1, -3.2), (75.78, 11.25)]
g = globe(0.0, 20, route, [], "THE LONG WAY ROUND", "Lisbon to Calicut, 1497–98",
          "ROUTE APPROXIMATE, DRAWN THROUGH WAYPOINTS (LISBON · CAPE VERDE · CAPE OF GOOD HOPE · MALINDI · CALICUT) · IMAGERY: NASA BLUE MARBLE NG VIA GIBS (PUBLIC DOMAIN) · ARRIVAL 20 MAY 1498 (MOST SOURCES)",
          labels=[(-9.14, 38.72, "LISBON"), (75.78, 11.25, "CALICUT (KOZHIKODE)"), (18.47, -34.36, "CAPE OF GOOD HOPE")])
g = g.replace("</body>", f'<style>{FONTS}</style><div style="position:absolute;right:56px;top:44px;z-index:90">{logo_d(1.0)}</div>'
              f'<div style="position:absolute;left:90px;top:330px;z-index:6;font:700 46px/1.1 Caveat;color:{SIG};width:520px;transform:rotate(-2deg)">"On my map, the string has to go the long way round."</div></body>', 1)
put("18_globe", g)
print(sorted(p.name for p in H.iterdir()))
