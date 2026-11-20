"""Delhi, The Bowl: the 2D frames (satellite evidence, before/after, 494, collages, closing line)."""
from pathlib import Path
D = Path(__file__).resolve().parent
SIG = "#FFDD33"
BOX = (70.5, 24.0, 90.5, 33.5)
def xy(lon, lat): return (lon - BOX[0]) / (BOX[2] - BOX[0]) * 1920, (BOX[3] - lat) / (BOX[3] - BOX[1]) * 1080
HEAD = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:Anton;src:url(/fonts/anton-latin-400-normal.woff2)}@font-face{font-family:Plex;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}
@font-face{font-family:ISerif;src:url(/fonts/instrument-serif-latin-400-italic.woff2)}@font-face{font-family:Playfair;src:url(/fonts/playfair-display-latin-900-normal.woff2)}
@font-face{font-family:Caveat;src:url(/fonts/caveat-latin-700-normal.woff2)}@font-face{font-family:Grotesk;src:url(/fonts/space-grotesk-latin-700-normal.woff2)}
body{margin:0;width:1920px;height:1080px;overflow:hidden;position:relative;BG} .a{position:absolute}
.grain{position:absolute;inset:0;pointer-events:none;opacity:.25;mix-blend-mode:overlay;z-index:50}
.cr{position:absolute;left:24px;bottom:14px;font:500 12px Plex;letter-spacing:1px;z-index:60}
</style></head><body>"""
TAIL = """<svg class="grain" width="1920" height="1080"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="3"/></filter><rect width="1920" height="1080" filter="url(#g)"/></svg>
<script>document.fonts.ready.then(()=>window.READY=true)</script></body></html>"""
def page(bg, body): return HEAD.replace("BG", bg) + body + TAIL
dx, dy = xy(77.21, 28.61)
pin = lambda x, y, lab, sub: (f'<div class="a" style="left:{x - 14}px;top:{y - 14}px;width:28px;height:28px;border-radius:50%;background:{SIG};box-shadow:0 0 0 8px rgba(255,221,51,.35),0 0 24px #000"></div>'
                              f'<div class="a" style="left:{x + 30}px;top:{y - 40}px;background:#141414;padding:8px 14px"><div style="font:400 40px/1 Anton;color:{SIG}">{lab}</div><div style="font:500 14px Plex;letter-spacing:3px;color:#ddd">{sub}</div></div>')
F = {}
F["01_from_space"] = page("background:#000", f'<img class="a" src="/maps/igp_2024-11-14_fill.jpg" style="left:0;top:0;width:1920px;height:1080px;object-fit:fill;filter:contrast(1.08)">'
    + pin(dx, dy, "DELHI", "14 NOV 2024")
    + f'<div class="a" style="left:1180px;top:640px;width:640px;background:rgba(10,10,10,.6);padding:24px 30px"><div style="font:600 18px Plex;letter-spacing:5px;color:{SIG}">NASA SATELLITE · 14 NOVEMBER 2024</div>'
      '<div style="font:400 92px/0.95 Anton;color:#F3EFE6;margin-top:10px">A BLANKET OVER THE PLAINS</div><div style="font:400 40px ISerif;color:#E8E1D0;margin-top:8px">haze and fog over the whole of north India</div></div>'
    + '<div class="cr" style="color:rgba(255,255,255,.7)">NASA GIBS · MODIS TERRA TRUE COLOUR, GAPS FILLED FROM MODIS AQUA (SAME DAY) · PUBLIC DOMAIN</div>')
F["02_before_after"] = page("background:#000", '<img class="a" src="/maps/igp_2024-10-03_fill.jpg" style="left:0;top:0;width:1920px;height:1080px">'
    '<div class="a" style="left:960px;top:0;width:960px;height:1080px;overflow:hidden"><img src="/maps/igp_2024-11-14_fill.jpg" style="width:1920px;height:1080px;margin-left:-960px"></div>'
    '<div class="a" style="left:957px;top:0;width:6px;height:1080px;background:#fff;box-shadow:0 0 18px rgba(0,0,0,.6)"></div>'
    '<div class="a" style="left:922px;top:502px;width:76px;height:76px;border-radius:50%;background:#fff;font:700 30px Grotesk;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 18px rgba(0,0,0,.5)">◀▶</div>'
    f'<div class="a" style="left:60px;top:50px;font:400 110px/1 Anton;color:{SIG};text-shadow:0 4px 18px rgba(0,0,0,.7)">3 OCT</div><div class="a" style="left:1640px;top:50px;font:400 110px/1 Anton;color:{SIG};text-shadow:0 4px 18px rgba(0,0,0,.7)">14 NOV</div>'
    + pin(dx, dy, "DELHI", "") + '<div class="a" style="left:60px;bottom:70px;background:rgba(0,0,0,.6);padding:16px 24px"><div style="font:400 90px/1 Anton;color:#F3EFE6">SAME PLACE. SIX WEEKS LATER.</div>'
    '<div style="font:500 20px Plex;letter-spacing:4px;color:#E6E6E6;margin-top:8px">NORTH INDIA FROM ORBIT, 2024</div></div>'
    '<div class="cr" style="color:rgba(255,255,255,.7)">NASA GIBS · MODIS TERRA TRUE COLOUR (GAPS FROM MODIS AQUA), 3 OCT AND 14 NOV 2024 · PUBLIC DOMAIN</div>')
F["06_number_494"] = page("background:radial-gradient(ellipse at 30% 50%,#2A2420 0%,#0D0B0A 75%)",
    '<svg class="a" style="left:220px;top:210px" width="680" height="680"><circle cx="340" cy="340" r="330" fill="none" stroke="#E9E4DA" stroke-opacity=".7" stroke-width="3" stroke-dasharray="14 12"/></svg>'
    '<img class="a" src="/assets/mask.png" style="left:300px;top:330px;width:520px;filter:grayscale(.6) drop-shadow(0 20px 26px rgba(0,0,0,.6))">'
    f'<div class="a" style="left:1000px;top:250px;font:600 26px Plex;letter-spacing:5px;color:{SIG}">DELHI · 18 NOVEMBER 2024</div>'
    '<div class="a" style="left:990px;top:290px;font:400 330px/1 Anton;color:#FF8A1E;text-shadow:0 0 22px rgba(255,138,30,.85),0 0 70px rgba(255,90,0,.5)">494</div>'
    '<div class="a" style="left:1000px;top:640px;width:820px;font:400 50px/1.1 ISerif;color:#F3EFE6">the day\'s average air quality index. The scale\'s top band, "severe", starts at 401.</div>'
    '<div class="a" style="left:1000px;top:800px;width:820px;font:500 18px Plex;letter-spacing:2px;color:#9C958A;border-top:1px solid #4a453f;padding-top:12px">SOURCE: CPCB DELHI/NCR AQI BULLETIN, 18 NOV 2024 (24-HOUR AVERAGE)</div>'
    '<div class="cr" style="color:rgba(255,255,255,.45)">PHOTO: PIXABAY (PIXABAY CONTENT LICENSE)</div>')
F["07_every_november"] = page("background:#B9A88A",
    '<div class="a" style="left:880px;top:90px;width:820px;height:820px;border-radius:50%;background:radial-gradient(circle,#F4E3C0 0%,#E9C98E 45%,rgba(233,201,142,0) 72%)"></div>'
    '<div class="a" style="left:0;top:820px;width:1920px;height:260px;background:#8E7F68"></div>'
    '<img class="a" src="/assets/indiagate.png" style="left:960px;top:240px;height:620px;filter:grayscale(1) contrast(1.2) brightness(1.02) drop-shadow(0 20px 26px rgba(0,0,0,.35))">'
    + "".join(f'<div class="a" style="left:{x}px;top:{y}px;width:{w}px;height:110px;background:radial-gradient(ellipse,rgba(235,225,205,.85),transparent 70%);filter:blur(16px);transform:rotate({r}deg);z-index:5"></div>'
              for x, y, w, r in ((-100, 520, 1500, -4), (700, 640, 1400, 3), (200, 300, 1200, -8), (900, 420, 1300, 6)))
    + '<div class="a" style="left:110px;top:150px;z-index:8"><div style="font:400 72px ISerif;color:#2A2420">every</div><div style="font:400 210px/0.86 Anton;color:#2A2420">NOVEMBER</div>'
      '<div style="font:500 22px Plex;letter-spacing:5px;color:#5A3A1A;margin-top:18px">INDIA GATE, NEW DELHI</div></div>'
    + '<div class="cr" style="color:rgba(0,0,0,.5)">PHOTO: PIXABAY (PIXABAY CONTENT LICENSE) · HAZE ADDED IN THE STUDIO</div>')
F["08_street"] = page("background:#2A1A10", '<img class="a" src="/assets/street.jpg" style="left:-2%;top:-2%;width:104%;height:104%;object-fit:cover;filter:sepia(.4) saturate(.9) contrast(.85) brightness(1.05) blur(1.5px)">'
    '<div class="a" style="left:0;top:0;width:1920px;height:1080px;background:linear-gradient(0deg,rgba(30,14,4,.8),rgba(200,170,120,.25) 60%,rgba(230,210,170,.45))"></div>'
    '<div class="a" style="left:120px;top:690px;font:400 150px/1 ISerif;color:#FFF4E2;text-shadow:0 6px 30px rgba(0,0,0,.5)">The air stays put</div>'
    f'<div class="a" style="left:126px;top:870px;font:600 24px Plex;letter-spacing:5px;color:{SIG}">FALLING TEMPERATURES AND SLOW WINDS · NASA EARTH OBSERVATORY</div>'
    '<div class="cr" style="color:rgba(255,255,255,.55)">PHOTO: A DELHI STREET, PIXABAY (PIXABAY CONTENT LICENSE) · GRADE ADDED IN THE STUDIO</div>')
F["09_where_it_sits"] = page("background:#EFEEE9;background-image:linear-gradient(rgba(0,0,0,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.06) 1px,transparent 1px);background-size:80px 80px",
    '<div class="a" style="left:190px;top:250px;font:400 120px/1 ISerif;color:#161616">What Delhi burns</div>'
    '<div class="a" style="left:190px;top:390px;font:400 170px/1 Anton;color:#E63946">MATTERS.</div>'
    '<div class="a" style="left:190px;top:600px;font:400 120px/1 ISerif;color:#161616">So does where it</div>'
    f'<div class="a" style="left:190px;top:730px;font:700 150px/1 Caveat;color:#161616"><span style="background:linear-gradient(transparent 55%,{SIG} 55%,{SIG} 92%,transparent 92%);padding:0 12px">sits.</span></div>'
    '<img class="a" src="/assets/indiagate.png" style="left:1340px;top:300px;height:560px;filter:grayscale(1) contrast(1.2) drop-shadow(0 18px 20px rgba(0,0,0,.3));transform:rotate(-4deg)">'
    '<div class="cr" style="color:rgba(0,0,0,.45)">PRINT FACTS · THE BOWL</div>')
if __name__ == "__main__":
    for k, v in F.items():
        (D / "html" / f"{k}.html").write_text(v)
