"""Pages added at "go": the animated opening (five rivers flowing), the free-power card (beat 7a) and the canal shot (9b)."""
import json
from PIL import Image
from frames import page, a, put, SIG, RED, NAVY, PAPER, INK, SAFE_TOP, maps, SRC25
import mask as M

R = json.load(open("data/rivers.json"))["rivers"]
FIVE = ["Jhelum", "Chenab", "Ravi", "Beas", "Sutlej"]
STATES = {s["n"]: s["r"] for s in json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/states.json"))["India"]}
INDIA = [r for r in maps._find("India")["rings"] if len(r) > 3]
BOX = (71.2, 29.0, 77.4, 34.6)
LABEL = {"Jhelum": (73.3, 33.4), "Chenab": (74.3, 32.75), "Ravi": (74.9, 32.2), "Beas": (76.0, 31.85), "Sutlej": (75.4, 30.9)}
SRCR = "RIVERS: NATURAL EARTH 10M CENTERLINES (PUBLIC DOMAIN)"
S2 = "IMAGERY: SENTINEL-2 CLOUDLESS 2016 BY EOX (S2MAPS.EU), CONTAINS MODIFIED COPERNICUS SENTINEL DATA 2016, CC BY 4.0"
H8 = Image.open("maps/rivers5_h8.png").convert("L")


def height(lo, la):
    u, v = M.uv("rivers5", lo, la)
    x = min(H8.width - 1, max(0, int(u * (H8.width - 1)))); y = min(H8.height - 1, max(0, int(v * (H8.height - 1))))
    return H8.getpixel((x, y))


def downstream(line):
    """Orient a centreline from its higher end (source side) to its lower end, so the flow runs the right way."""
    return line if height(*line[0]) >= height(*line[-1]) else line[::-1]


P = lambda lo, la: ((lo - BOX[0]) / (BOX[2] - BOX[0]) * 1080, 330 + (BOX[3] - la) / (BOX[3] - BOX[1]) * 1148)
ring = lambda rings, **st: "".join('<path d="M' + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + 'Z" ' +
                                   " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in st.items()) + "/>" for r in rings if len(r) > 3)
riv = ""
for i, n in enumerate(FIVE):
    for line in R[n]:
        d = "M" + " L".join("%.1f %.1f" % P(lo, la) for lo, la in downstream(line))
        riv += (f'<path class="rg" data-i="{i}" d="{d}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" fill="none" stroke="#5EC8FF" stroke-width="16" opacity=".35" filter="url(#bl)"/>'
                f'<path class="rv" data-i="{i}" d="{d}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" fill="none" stroke="#5EC8FF" stroke-width="5" stroke-linecap="round"/>'
                f'<path class="fl" data-i="{i}" d="{d}" pathLength="1" stroke-dasharray="0.012 0.045" stroke-dashoffset="0" fill="none" stroke="#E8F8FF" stroke-width="3" stroke-linecap="round" opacity="0"/>')
labs = "".join(f'<div class="a lab" data-i="{i}" style="left:{P(*LABEL[n])[0] - 50:.0f}px;top:{P(*LABEL[n])[1] - 18:.0f}px;opacity:0;background:rgba(0,0,0,.65);color:#BFE8FF;'
               f'font:500 20px Plex;letter-spacing:3px;padding:3px 8px">{n.upper()}</div>' for i, n in enumerate(FIVE))
put("01_rivers", page(
    a('<img src="/maps/s2_rivers.jpg" style="width:1080px;height:1148px;filter:brightness(.72) contrast(1.1) saturate(.9)">', 0, 330)
    + '<svg class="a" data-keep="1" style="left:0;top:0" width="1080" height="1920"><defs><filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>'
      '<clipPath id="k"><rect x="0" y="330" width="1080" height="1148"/></clipPath></defs><g clip-path="url(#k)">'
    + ring(INDIA, fill="none", stroke="#FFFFFF", stroke_width=2, opacity=.55)
    + ring(STATES["Punjab"], id="pun", fill="rgba(200,49,43,0)", stroke="#FFFFFF", stroke_width=4) + riv + "</g></svg>" + labs
    + a(f'<div style="font:400 104px/0.95 Anton;color:#F3EFE6;width:940px">THE LAND OF<br>FIVE RIVERS</div>', 70, SAFE_TOP, "")
    + f'<div class="a" id="banner" style="left:70px;top:1330px;opacity:0"><div style="background:{RED};color:#fff;padding:14px 22px;transform:rotate(-2deg)">'
      f'<div style="font:400 72px/1 Anton">AND STILL IN THE RED</div><div style="font:500 22px Plex;letter-spacing:3px;color:#FFE3E0;margin-top:6px">PUMPS 156% OF ITS SAFE GROUNDWATER LIMIT</div></div></div>',
    "#000", SRC25 + " · " + SRCR + " · " + S2 + " · INDIA: OFFICIAL BOUNDARY; PUNJAB: NATURAL EARTH", dark=True)
    .replace("</body>", """<script>window.CUSTOM=function(t,sec){
 const q=t;
 document.querySelectorAll('.rv,.rg').forEach(p=>{const i=+p.dataset.i;const s=Math.max(0,Math.min(1,(q-0.04-i*0.07)/0.22));p.setAttribute('stroke-dashoffset',(1-s).toFixed(3))});
 document.querySelectorAll('.fl').forEach(p=>{const i=+p.dataset.i;const s=(q-0.04-i*0.07)/0.22;p.setAttribute('opacity',s>=1?'.85':'0');p.setAttribute('stroke-dashoffset',(-sec*0.09).toFixed(4))});
 document.querySelectorAll('.lab').forEach(e=>{const i=+e.dataset.i;e.style.opacity=(q-0.04-i*0.07)/0.22>=1?1:0});
 document.getElementById('pun').setAttribute('fill','rgba(200,49,43,'+(q>0.66?0.22:0)+')');
 document.getElementById('banner').style.opacity=q>0.7?1:0;};</script></body>"""))

# 7a: free power since 1997, over the photo of water pouring from a pipe
put("07a_power", page(a('<img src="/assets/pipe.jpg" style="width:1080px;height:1920px;object-fit:cover;filter:brightness(.5) contrast(1.1)">', 0, 0)
                      + a(f'<div style="font:400 100px/0.95 Anton;color:#F3EFE6;width:940px">SO WHY KEEP<br>WITHDRAWING?</div>', 70, SAFE_TOP)
                      + a(f'<div style="background:{SIG};color:#111;padding:18px 26px;transform:rotate(-2deg)"><div style="font:500 24px Plex;letter-spacing:4px">SINCE 1997</div>'
                          f'<div style="font:400 120px/0.95 Anton">FREE POWER</div><div style="font:500 30px Plex;letter-spacing:3px">FOR FARM PUMPS</div></div>', 120, 760)
                      + a(f'<div style="font:700 50px/1.15 Caveat;color:#F3EFE6;width:800px">the pump costs nothing to run, so it runs</div>', 130, 1160),
                      "#000", "FREE FARM POWER IN PUNJAB SINCE 1997 (SOURCES DATE IT TO LATE 1996 OR JAN 1997): TRIBUNE EXPLAINERS · PHOTO: PIXABAY", dark=True))

# 9b: canals
put("09b_canal", page(a('<img src="/assets/canal.jpg" style="width:1080px;height:1920px;object-fit:cover;filter:saturate(1.05) brightness(.8)">', 0, 0)
                      + a(f'<div style="font:400 100px/0.95 Anton;color:#F3EFE6;width:940px;text-shadow:0 4px 20px rgba(0,0,0,.5)">CANALS TAKE<br>SOME OF THE LOAD</div>', 70, SAFE_TOP)
                      + a(f'<div style="background:rgba(10,20,30,.78);padding:18px 24px;width:880px;font:500 28px/1.5 Plex;color:#E8F2FF">'
                          f'Punjab\'s 2024-25 groundwater report credits more canal irrigation for the drop in pumping.</div>', 70, 980),
                      "#000", "SOURCE: 'GROUND WATER RESOURCES OF PUNJAB STATE 2024-25', AS REPORTED BY THE TRIBUNE · PHOTO: PIXABAY (ILLUSTRATIVE CANAL)", dark=True))
print("ok")
