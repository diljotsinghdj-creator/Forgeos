"""BJP IT cell YouTube Short (Trojan Horse, ~45 s): 12 storyboard frames at 1080x1920, drawn as HTML and captured."""
import json, math, sys
from pathlib import Path

ROOT = Path("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media")
F = (ROOT / "vendor" / "fonts").as_posix()
LOGO = json.loads((ROOT / "vendor" / "logos.json").read_text())
STATES = json.loads((ROOT / "states.json").read_text())["India"]
OUT = Path(__file__).parent
SIG, ACC, INK, PAPER, NIGHT = "#FFDD33", "#D7262B", "#141414", "#ECE8DF", "#121417"


def logo(k, size=96):
    m = LOGO[k]
    return (f'<svg width="{size}" height="{size}" viewBox="-6 -6 36 36" style="border-radius:{size*.22}px;background:{m["hex"]};'
            f'box-shadow:0 6px 18px rgba(0,0,0,.25)"><path d="{m["d"]}" fill="#fff"/></svg>')


def india_svg(w, h, hi=None, faint=False, fill="#D8D2C4", hifill=ACC, extra="", box=(68.0, 6.5, 97.5, 37.2)):
    k = math.cos(math.radians((box[1] + box[3]) / 2))
    s = min(w / ((box[2] - box[0]) * k), h / (box[3] - box[1]))
    ox = (w - (box[2] - box[0]) * k * s) / 2
    xy = lambda lo, la: ((lo - box[0]) * k * s + ox, (box[3] - la) * s)
    out = []
    for st in STATES:
        f = hifill if hi and st["n"] == hi else fill
        for r in st["r"]:
            if len(r) > 2:
                pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(*p) for p in r))
                out.append(f'<polygon points="{pts}" fill="{f}" stroke="{PAPER if not faint else "#C9C2B2"}" stroke-width="1.2"/>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(out)}{extra(xy) if callable(extra) else extra}</svg>', xy


CSS = f"""
@font-face{{font-family:Anton;src:url(file://{F}/anton-latin-400-normal.woff2)}}
@font-face{{font-family:Play;src:url(file://{F}/playfair-display-latin-900-normal.woff2)}}
@font-face{{font-family:Inter;font-weight:800;src:url(file://{F}/inter-latin-800-normal.woff2)}}
@font-face{{font-family:Inter;font-weight:600;src:url(file://{F}/inter-latin-600-normal.woff2)}}
@font-face{{font-family:Mono;src:url(file://{F}/jetbrains-mono-latin-700-normal.woff2)}}
*{{margin:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;background:{PAPER};color:{INK};font-family:Inter;position:relative}}
body:after{{content:"";position:absolute;inset:0;pointer-events:none;opacity:.18;mix-blend-mode:multiply;
 background-image:radial-gradient(rgba(0,0,0,.35) .6px,transparent .7px);background-size:5px 5px}}
.dark{{background:{NIGHT};color:#F2EEE6}}
.h{{font:900 92px/1.05 Play;letter-spacing:-.01em}}
.hl{{background:linear-gradient(transparent 14%,{SIG} 14%,{SIG} 90%,transparent 90%);padding:0 .1em;box-decoration-break:clone;-webkit-box-decoration-break:clone;color:{INK}}}
.big{{font:300px/0.9 Anton}}
.lab{{font:800 34px/1.25 Inter;letter-spacing:.06em;text-transform:uppercase}}
.src{{position:absolute;left:70px;right:70px;bottom:330px;font:22px/1.4 Mono;letter-spacing:.06em;opacity:.75;text-transform:uppercase}}
.badge{{position:absolute;left:70px;top:150px;font:24px Mono;letter-spacing:.22em;padding:10px 16px;border:3px solid currentColor}}
.ver{{color:#1F7A4D}} .rep{{color:#B36B00}} .rec{{color:#6A6A6A}} .ev{{color:{ACC}}} .ill{{color:#6A6A6A}}
.dark .ver{{color:#7FD6A6}} .dark .rep{{color:{SIG}}} .dark .rec{{color:#BDB6A8}}
.num{{position:absolute;right:70px;top:150px;font:24px Mono;opacity:.55}}
.tag{{display:inline-block;background:{INK};color:#fff;font:800 30px Inter;letter-spacing:.08em;padding:12px 20px;text-transform:uppercase}}
.phone{{width:520px;height:1040px;border-radius:70px;background:#0E0E10;padding:22px;box-shadow:0 40px 80px rgba(0,0,0,.35)}}
.screen{{width:100%;height:100%;border-radius:52px;overflow:hidden;position:relative}}
"""


def page(body, cls="", n=0, badge=None, src=""):
    b = f'<div class="badge {badge[1]}">● {badge[0]}</div>' if badge else ""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body class="{cls}">'
            f'{b}<div class="num">{n:02d} / 12</div>{body}{f"<div class=src>{src}</div>" if src else ""}</body></html>')


def reel(caption_rows=True):
    bars = "".join(f'<div style="height:{h}px;width:14px;background:{SIG};border-radius:7px"></div>'
                   for h in (60, 120, 90, 180, 140, 220, 160, 100, 200, 130, 70, 150, 110, 190, 80))
    return f"""<div class="screen" style="background:linear-gradient(160deg,#FF4F9A,#7B2FF7 55%,#1D1D6B)">
 <div style="position:absolute;top:120px;left:0;right:0;text-align:center;font:110px/1 Anton;color:#fff;transform:rotate(-4deg)">♪ ♫ ♪</div>
 <div style="position:absolute;top:330px;left:40px;right:40px;display:flex;gap:10px;align-items:center;justify-content:center;height:240px">{bars}</div>
 <div style="position:absolute;left:36px;right:110px;bottom:120px">
   <div style="height:26px;width:85%;background:#fff;border-radius:13px;margin-bottom:16px"></div>
   <div style="height:26px;width:60%;background:#fff;opacity:.8;border-radius:13px;margin-bottom:16px"></div>
   <div style="height:22px;width:40%;background:#fff;opacity:.55;border-radius:11px"></div></div>
 <div style="position:absolute;right:26px;bottom:150px;display:flex;flex-direction:column;gap:46px;align-items:center">
   {''.join(f'<div style="width:62px;height:62px;border-radius:50%;background:rgba(255,255,255,.9)"></div>' for _ in range(3))}</div>
</div>"""


def frames():
    out = []
    # 01 the harmless thing
    out.append(page(f"""
<div style="position:absolute;top:260px;left:70px;right:70px" class="h">Just a <span class="hl">catchy reel</span>?</div>
<div class="phone" style="position:absolute;left:280px;top:470px;transform:rotate(-3deg) scale(.86);transform-origin:50% 0">{reel()}</div>""",
        n=1, badge=("RECREATION", "rec"), src="A recreated reel: no real post is shown"))
    # 02 the evidence: the party's own upload
    out.append(page(f"""
<div style="position:absolute;top:250px;left:70px;right:70px" class="h" >The party's <span class="hl">own upload</span>, 2018</div>
<div style="position:absolute;left:70px;right:70px;top:620px;height:540px;border:5px dashed #F2EEE6;border-radius:18px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;background:#1C1F24">
  {logo('youtube',120)}
  <div class="lab" style="text-align:center;color:#F2EEE6">EVIDENCE SLOT<br><span style="font-weight:600;opacity:.8;text-transform:none;letter-spacing:.02em">BJP upload · Kota · 22 Sep 2018 · at 26:30</span></div></div>
<div style="position:absolute;left:70px;right:70px;top:1210px;font:600 44px/1.35 Inter;color:#F2EEE6">
  <div style="font:26px Mono;opacity:.6;margin-bottom:12px">[EXACT HINDI WORDS FROM THE VIDEO]</div>
  “…any message can go viral, <span class="hl">true or false</span>…”<br>
  <span style="font-size:32px;opacity:.75">Amit Shah, then BJP president, to social media volunteers. He added it shouldn't be done (reported).</span></div>""",
        "dark", 2, ("VERIFIED", "ver"), "The Quint; The Wire; The Logical Indian (caveat)"))
    # 03 the phone breaks open
    layers = [("THE POST", "your screen", "#2A2A2E"), ("THE SIGN-OFF", "one official, every post (Delhi)", "#3A3A40"),
              ("THE DESIGN", "about 20 designers and cartoonists (UP)", "#4A4A52"), ("THE THEME", "a 25-member core team (UP)", "#5A5A64")]
    lay = "".join(f"""<div style="position:absolute;left:560px;top:{420 + i * 270}px;width:400px;height:200px;border-radius:30px;background:{c};
  transform:perspective(1400px) rotateX(58deg) rotateZ(-28deg);box-shadow:0 30px 50px rgba(0,0,0,.5);border:3px solid {'%s' % (SIG if i == 0 else '#8A8A94')}"></div>
<div style="position:absolute;left:70px;top:{470 + i * 270}px" ><span class="tag" style="background:{SIG if i == 0 else '#F2EEE6'};color:{INK}">{t}</span>
  <div style="font:600 30px Inter;margin-top:12px;color:#F2EEE6;max-width:430px">{d}</div></div>""" for i, (t, d, c) in enumerate(layers))
    out.append(page(f"""<div style="position:absolute;top:240px;left:70px;right:70px;color:#F2EEE6" class="h">Break it <span class="hl">open</span></div>{lay}""",
                    "dark", 3, ("REPORTED", "rep"), "Newslaundry reporting on the UP and Delhi units"))
    # 04 one sign-off
    cards = "".join(f'<div style="position:absolute;left:{120 + i * 170}px;top:{1080 - abs(i - 2) * 30}px;width:150px;height:200px;background:#fff;border-radius:14px;box-shadow:0 10px 20px rgba(0,0,0,.18);transform:rotate({(i - 2) * 4}deg)"><div style="margin:18px;height:90px;background:#D8D2C4;border-radius:8px"></div><div style="margin:0 18px;height:14px;background:#BBB;border-radius:7px"></div></div>' for i in range(5))
    out.append(page(f"""<div style="position:absolute;top:260px;left:70px;right:70px" class="h">Every post,<br><span class="hl">one sign&#8209;off</span></div>
{cards}
<div style="position:absolute;left:300px;top:700px;width:480px;height:260px;border:12px solid {ACC};color:{ACC};font:120px/240px Anton;text-align:center;transform:rotate(-8deg);letter-spacing:.06em">APPROVED</div>
<div class="lab" style="position:absolute;left:70px;right:70px;top:1380px">In Delhi, one official signs off every post</div>""",
                    n=4, badge=("REPORTED", "rep"), src="Newslaundry"))
    # 05 the booth network, planned
    svg, xy = india_svg(900, 1000, faint=True, fill="#D9D3C5")
    out.append(page(f"""<div style="position:absolute;top:240px;left:70px;right:70px" class="h">A phone volunteer at <span class="hl">every booth</span></div>
<div style="position:absolute;left:90px;top:560px;opacity:.9">{svg}</div>
<div style="position:absolute;left:70px;top:820px" class="big">900,000</div>
<div class="lab" style="position:absolute;left:70px;right:70px;top:1110px">booth volunteers <span class="hl">planned</span> for 2019</div>
<div style="position:absolute;left:70px;right:70px;top:1240px;font:600 30px Inter;opacity:.75">One report said nearly 1 lakh. These are plans, not counts.</div>""",
                    n=5, badge=("REPORTED", "rep"), src="Down To Earth; Oneindia; Latestly"))
    # 06 Bihar, tiled with groups
    def bihar_icons(xy):
        # 72 small chat icons placed inside Bihar's outline: 1 icon = 1,000 groups (illustrative placement)
        st = next(s for s in STATES if s["n"] == "Bihar")
        ring = max(st["r"], key=len)
        pts = [xy(*p) for p in ring]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        def inside(x, y):
            c = False
            for i in range(len(pts)):
                (x1, y1), (x2, y2) = pts[i], pts[i - 1]
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    c = not c
            return c
        cand, step = [], 33.0
        y = min(ys) + step / 2
        while y < max(ys):
            x = min(xs) + step / 2
            while x < max(xs):
                if inside(x, y):
                    cand.append((x, y))
                x += step
            y += step
        keep = [cand[round(i * (len(cand) - 1) / 71)] for i in range(72)] if len(cand) >= 72 else cand   # spread across the state
        out = [f'<rect x="{x-12:.1f}" y="{y-9:.1f}" width="24" height="18" rx="6" fill="{SIG}" stroke="{INK}" stroke-width="2"/>'
               f'<path d="M{x-6:.1f} {y+9:.1f} l-3 6 l9 -6z" fill="{INK}"/>' for x, y in keep]
        return f'<g>{"".join(out)}</g><text x="{min(xs):.0f}" y="{min(ys)-24:.0f}" font-family="Inter" font-weight="800" font-size="40">BIHAR</text>'
    svg, xy = india_svg(940, 760, hi="Bihar", fill="#D9D3C5", hifill="#2B2B2B", extra=bihar_icons, box=(82.6, 23.4, 89.2, 28.2))
    out.append(page(f"""<div style="position:absolute;top:240px;left:70px;right:70px" class="h">Bihar, 2020: <span class="hl">72,000</span> groups</div>
<div style="position:absolute;left:70px;top:470px;overflow:hidden;width:940px;height:760px">{svg}</div>
<div style="position:absolute;right:90px;top:1110px">{logo('whatsapp',100)}</div>
<div class="lab" style="position:absolute;left:70px;right:70px;top:1310px;font-size:30px">72,000 WhatsApp groups planned, 9,500 IT cell heads <span style="opacity:.6">(party leaders to ThePrint)</span><br>Over 1 lakh formed <span style="opacity:.6">(state convenor to Caravan)</span></div>
<div style="position:absolute;left:70px;top:1250px;font:24px Mono;opacity:.7">1 TILE = 1,000 GROUPS · PLACEMENT ILLUSTRATIVE</div>""",
                    n=6, badge=("REPORTED", "rep"), src="ThePrint; The Caravan"))
    # 07 seventeen fact-checks
    fan = "".join(f'<div style="position:absolute;left:{70 + (i % 4) * 238}px;top:{500 + (i // 4) * 158}px;width:220px;height:140px;background:#fff;border-radius:12px;box-shadow:0 6px 14px rgba(0,0,0,.14);transform:rotate({((i * 37) % 7) - 3}deg)"><div style="margin:20px 18px 0;height:12px;background:#CCC;border-radius:6px"></div><div style="margin:10px 18px;height:12px;width:55%;background:#DDD;border-radius:6px"></div><div style="position:absolute;right:12px;bottom:12px;border:4px solid {ACC};color:{ACC};font:26px Anton;padding:0 8px;transform:rotate(-6deg)">{"FALSE" if i % 2 else "MISLEADING"}</div></div>' for i in range(17))
    out.append(page(f"""<div style="position:absolute;top:240px;left:70px;right:70px" class="h">Flagged <span class="hl">17 times</span></div>
{fan}
<div class="lab" style="position:absolute;left:70px;right:70px;top:1340px">Posts by the IT cell's then-head flagged false or misleading by fact-checkers</div>""",
                    n=7, badge=("REPORTED", "rep"), src="The News Minute tally, 2020"))
    # 08 the other side: junk news on both sides
    def grid(k, label):
        cells = "".join(f'<div style="width:34px;height:52px;border-radius:7px;background:{SIG if i < k else "#CFC8B8"};border:2px solid {INK if i < k else "transparent"}"></div>' for i in range(100))
        return f'<div><div style="display:grid;grid-template-columns:repeat(10,34px);gap:7px">{cells}</div><div class="big" style="font-size:130px;margin-top:24px">{k}<span style="font-size:60px"> IN 100</span></div><div class="lab" style="font-size:28px">{label}</div></div>'
    out.append(page(f"""<div style="position:absolute;top:240px;left:70px;right:70px" class="h">It isn't <span class="hl">one party</span></div>
<div style="position:absolute;left:70px;right:70px;top:560px;display:flex;justify-content:space-between">{grid(28, "pro-BJP pages")}{grid(21, "pro-Congress pages")}</div>
<div style="position:absolute;right:70px;top:150px;transform:translateY(60px)">{logo('facebook',90)}</div>
<div class="lab" style="position:absolute;left:70px;right:70px;top:1420px;font-size:30px">Shared news links rated 'junk news' on Facebook pages, 2019 election</div>""",
                    n=8, badge=("REPORTED", "rep"), src="Oxford Internet Institute, 2019"))
    # 09 the other side: arrests over a doctored video
    out.append(page(f"""<div style="position:absolute;top:300px;left:70px" class="big" >MAY<br>2024</div>
<div style="position:absolute;top:900px;left:70px;right:70px;font:900 66px/1.15 Play">Police arrest Congress social-media workers over a <span class="hl">doctored video</span> of Amit Shah</div>
<div style="position:absolute;top:1300px;left:70px;right:70px;font:600 32px/1.4 Inter;opacity:.85">Released on bail; no court finding yet.<br>Congress president Kharge said the BJP was the expert in fake videos.</div>""",
                    n=9, badge=("VERIFIED", "ver"), src="Business Today; Scroll"))
    # 10 the money, from the party's own filing
    rows = [("Total election spending", "₹1,737.68 cr", False), ("Media advertisement", "₹611.50 cr", False),
            ("Google India", "₹156.95 cr", True), ("Facebook", "₹24.63 cr", True)]
    tr = "".join(f'<div style="display:flex;justify-content:space-between;padding:26px 30px;border-bottom:2px solid #D6D0C3;font:600 38px Inter"><span>{a}</span><span style="font:44px Anton;{"background:" + SIG + ";padding:0 10px" if h else ""}">{b}</span></div>' for a, b, h in rows)
    out.append(page(f"""<div style="position:absolute;top:240px;left:70px;right:70px" class="h">The party's <span class="hl">own filing</span>, 2024</div>
<div style="position:absolute;left:70px;right:70px;top:620px;background:#FBF9F4;box-shadow:0 20px 40px rgba(0,0,0,.15);transform:rotate(-1.5deg)">
 <div style="padding:30px;font:24px Mono;letter-spacing:.1em;border-bottom:3px solid {INK}">EXPENDITURE STATEMENT TO THE ELECTION COMMISSION · RECREATED</div>{tr}</div>
<div style="position:absolute;left:70px;top:1330px;display:flex;gap:30px">{logo('google',100)}{logo('facebook',100)}</div>""",
                    n=10, badge=("VERIFIED", "ver"), src="BJP's statement to the Election Commission; Scroll; ThePrint/PTI"))
    # 11 the new style
    out.append(page(f"""<div style="position:absolute;top:240px;left:70px;right:70px" class="h">New chief.<br><span class="hl">New beat.</span></div>
<div class="phone" style="position:absolute;left:280px;top:500px;transform:rotate(3deg) scale(.82);transform-origin:50% 0">{reel()}</div>
<div class="lab" style="position:absolute;left:70px;right:70px;top:1420px;font-size:28px;background:#ECE8DF;padding:10px 0">17 Aug 2026: new IT cell chief · since then: memes, rap, slang</div>""",
                    n=11, badge=("REPORTED", "rep"), src="Newslaundry, Aug and Oct 2026"))
    # 12 the question
    out.append(page(f"""<div style="position:absolute;top:560px;left:70px;right:70px;font:900 132px/1.05 Play"><span class="hl">Who made</span> the last reel you shared?</div>""",
                    n=12))
    return out


if __name__ == "__main__":
    for i, h in enumerate(frames(), 1):
        (OUT / f"f{i:02d}.html").write_text(h, encoding="utf-8")
    print("ok")
