"""Compose 100 Vox-style images from the fetched records. Twelve treatments, rotated so neighbours never share one.
Text is the theme title, its kicker, and the archive record as the credit. No charts, no AI imagery."""
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, "/home/user/Forgeos/creatorforge/channels/design_kits/collage")
import collage2 as K
from collage2 import el, STILL
from topics import DP, PF

D = Path(__file__).resolve().parent
F = K.FONTS
SIG = "#FFDD33"
rec = json.loads((D / "data" / "records.json").read_text())
FACES = "<style>" + "".join(f"@font-face{{font-family:{n};src:url({(F / (p + '.woff2')).as_uri()})}}" for n, p in (
    ("Plex", "ibm-plex-mono-latin-500-normal"), ("Caveat", "caveat-latin-700-normal"), ("Grotesk", "space-grotesk-latin-700-normal"),
    ("ISerif", "instrument-serif-latin-400-normal"), ("ISerifI", "instrument-serif-latin-400-italic"), ("Kalam", "kalam-latin-700-normal"),
    ("Shadows", "shadows-into-light-latin-400-normal"))) + "</style>"


def prep(tid):
    """Web copy (max 1600 px), a halftone copy and a high-contrast grey copy of each image."""
    src = D / "img" / f"{tid}.jpg"
    out = {}
    im = Image.open(src).convert("RGB")
    im.thumbnail((1600, 1600))
    p = D / "img" / f"{tid}_web.jpg"
    im.save(p, quality=88)
    out["web"] = p.as_uri()
    g = ImageOps.autocontrast(im.convert("L"), cutoff=1)
    gp = D / "img" / f"{tid}_grey.jpg"
    g.save(gp, quality=88)
    out["grey"] = gp.as_uri()
    step = 7                                       # dots drawn at about display size (images show ~1100 px wide)
    gd = g.resize((1100, max(1, int(g.height * 1100 / g.width))))
    small = gd.resize((max(1, gd.width // step), max(1, gd.height // step)))
    ht = Image.new("L", (small.width * step, small.height * step), 255)
    dr = ImageDraw.Draw(ht)
    px = small.load()
    for y in range(small.height):
        for x in range(small.width):
            r = (1 - px[x, y] / 255) ** 1.1 * step * .58
            if r > .4:
                cx, cy = x * step + step / 2, y * step + step / 2
                dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    hp = D / "img" / f"{tid}_ht.png"
    ht.save(hp)
    out["ht"] = hp.as_uri()
    out["w"], out["h"] = im.size
    return out


def credit(r):
    bits = [r["title"], r.get("date") or "", r.get("maker") or "", r["source"], r["licence"]]
    return " · ".join(b.strip() for b in bits if b and b.strip()).upper()[:230]


def title_block(t, k, font, size, col, kfont="Plex", ksize=24, kcol=None, width=900, align="left"):
    return (f'<div style="width:{width}px;text-align:{align}"><div style="font:{font};font-size:{size}px;line-height:.95;color:{col}">{t}</div>'
            f'<div style="font:500 {ksize}px {kfont};letter-spacing:2px;color:{kcol or col};margin-top:18px;text-transform:uppercase">{k}</div></div>')


# ---- twelve treatments: each returns (body, background) ------------------------------------------------------------
def t_kraft(r, im, rnd):
    tape = lambda x, y, rot: el(f'<div style="width:170px;height:46px;background:rgba(236,226,190,.82);box-shadow:0 2px 4px rgba(0,0,0,.15)"></div>', x, y, .4, "pop", base=f"rotate({rot}deg)", z=8)
    body = el(f'<div style="width:980px;height:760px;overflow:hidden;background:#fff;padding:0;box-shadow:0 22px 40px rgba(60,40,10,.45)"><img src="{im["ht"]}" style="width:100%;height:100%;object-fit:cover"></div>', 110, 150, .1, "drop", base="rotate(-1.6deg)", z=5)
    body += tape(90, 130, -12) + tape(960, 880, 9)
    body += el(title_block(r["theme"], r["kicker"], "400 150px Anton", 150, "#1b1b1b", width=700), 1150, 300, .5, "wipe", z=6)
    body += el(f'<div style="width:520px;height:16px;background:{SIG}"></div>', 1150, 600, .8, "wipe", z=5)
    return body, "background:#C9A97A"


def t_duotone(r, im, rnd):
    dark, light = rnd.choice([("#0E2A47", "#F2C14E"), ("#2B0F3A", "#FF8A6B"), ("#062F2A", "#E9D985"), ("#3A0D0D", "#F4D6A8")])
    body = el(f'<div style="width:1920px;height:1080px;position:relative;isolation:isolate"><img src="{im["grey"]}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:contrast(1.15)">'
              f'<div style="position:absolute;inset:0;background:{light};mix-blend-mode:multiply"></div><div style="position:absolute;inset:0;background:{dark};mix-blend-mode:lighten"></div>'
              f'<div style="position:absolute;inset:0;background:linear-gradient(0deg,{dark} 0%,transparent 55%)"></div></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    body += el(title_block(r["theme"].upper(), r["kicker"], "400 200px Anton", 200, light, width=1700), 110, 640, .3, "wipe", z=6)
    return body, f"background:{dark}"


def t_board(r, im, rnd):
    pol = K.polaroid(f'<img src="{im["web"]}" style="width:100%;height:100%;object-fit:cover;filter:sepia(.25) contrast(1.05)">', r["title"][:38], w=640, rot=-3, at=.1, x=180, y=120, z=6)
    card = el(f'<div style="background:#fbf8ef;padding:28px 34px;width:600px;box-shadow:0 12px 24px rgba(0,0,0,.35)">{title_block(r["theme"], r["kicker"], "400 84px Playfair", 84, "#141414", width=600)}</div>', 1080, 300, .6, "drop", base="rotate(2deg)", z=6)
    return pol + card + K.pin_dot(500, 130) + K.pin_dot(1380, 310) + K.red_string([(500, 130), (1380, 310)], .9), "background:#9A6B3F;background-image:radial-gradient(rgba(0,0,0,.12) 1px,transparent 1px);background-size:9px 9px"


def t_newsprint(r, im, rnd):
    cols = "".join(f'<div style="height:14px;background:#c9c4b8;margin:10px 0;width:{rnd.randint(70, 100)}%"></div>' for _ in range(26))
    body = el(f'<div style="font:900 128px/0.95 Playfair;color:#141414;width:1700px;border-bottom:6px double #141414;padding-bottom:16px">{r["theme"]}</div>', 110, 70, .1, "wipe", z=5)
    body += el(f'<div style="font:500 24px Plex;letter-spacing:3px;color:#141414">{r["kicker"].upper()}</div>', 112, 280, .3, "wipe", z=5)
    body += el(f'<div style="width:1080px;height:640px;overflow:hidden"><img src="{im["ht"]}" style="width:100%;height:100%;object-fit:cover"></div>', 110, 340, .2, "pop", z=4)
    body += el(f'<div style="width:520px">{cols}</div>', 1260, 350, 0, "pop", extra=STILL, z=3)
    return body, "background:#EDE8DC"


def t_riso(r, im, rnd):
    a, b = rnd.choice([("#FF48B0", "#0078BF"), ("#FF6C2F", "#3255A4"), ("#00A95C", "#FF48B0")])
    ink = lambda col, dx, dy, op: (f'<div style="position:absolute;left:{dx}px;top:{dy}px;width:1140px;height:860px;mix-blend-mode:multiply;opacity:{op}">'
                                   f'<img src="{im["grey"]}" style="width:100%;height:100%;object-fit:cover;filter:contrast(1.7) brightness(1.05)">'
                                   f'<div style="position:absolute;inset:0;background:{col};mix-blend-mode:screen"></div></div>')
    body = el(f'<div style="position:relative;width:1170px;height:890px;isolation:isolate">{ink(a, 0, 0, 1)}{ink(b, 22, 16, .9)}</div>', 110, 100, .1, "pop", z=3)
    body += el(title_block(r["theme"], r["kicker"], "700 96px Grotesk", 96, b, width=560), 1320, 360, .5, "wipe", z=6)
    return body, "background:#F6F1E7"


def t_blueprint(r, im, rnd):
    grid = "background:#123B6B;background-image:linear-gradient(rgba(255,255,255,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.12) 1px,transparent 1px);background-size:40px 40px"
    body = el(f'<div style="width:980px;height:700px;border:12px solid #f4f4f0;overflow:hidden"><img src="{im["grey"]}" style="width:100%;height:100%;object-fit:cover;filter:contrast(1.1)"></div>', 120, 190, .1, "pop", z=4)
    body += el(f'<svg width="1920" height="1080"><path d="M1110 330 L1240 330 M1110 760 L1240 760" stroke="#f4f4f0" stroke-width="3" stroke-dasharray="10 8"/><circle cx="1110" cy="330" r="8" fill="{SIG}"/></svg>', 0, 0, .6, "draw", z=5)
    body += el(title_block(r["theme"], r["kicker"], "400 100px Bebas", 100, "#f4f4f0", "Plex", 22, SIG, width=560), 1260, 300, .4, "slide", z=6)
    body += el(f'<div style="font:500 18px Plex;color:#9fc0e6;letter-spacing:2px">FIG. {rnd.randint(1, 99):02d} · {r["source"].upper()}</div>', 120, 140, .3, "wipe", z=6)
    return body, grid


def t_museum(r, im, rnd):
    w = 760 if im["h"] > im["w"] else 1000
    h = int(w * im["h"] / im["w"])
    if h > 820:
        w, h = int(w * 820 / h), 820
    frame = f'<div style="padding:26px;background:linear-gradient(135deg,#7a5a2a,#c9a45a 40%,#7a5a2a);box-shadow:0 40px 60px rgba(0,0,0,.6)"><img src="{im["web"]}" style="width:{w}px;height:{h}px;object-fit:cover;display:block"></div>'
    body = el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 38% 30%,rgba(255,240,200,.35),transparent 55%)"></div>', 0, 0, 0, "pop", extra=STILL, z=2)
    body += el(frame, 140, (1080 - h) // 2 - 26, .1, "pop", z=4)
    label = (f'<div style="background:#f5f2ea;padding:30px 34px;width:470px;box-shadow:0 8px 16px rgba(0,0,0,.4)"><div style="font:400 64px/1 ISerif;color:#141414">{r["theme"]}</div>'
             f'<div style="font:400 30px ISerifI;color:#444;margin-top:12px">{r["kicker"]}</div><div style="height:2px;background:#141414;margin:22px 0"></div>'
             f'<div style="font:500 15px/1.5 Plex;color:#333">{r["title"][:90]}<br>{(r.get("date") or "")[:40]}</div></div>')
    body += el(label, 1340, 380, .5, "drop", z=6)
    return body, "background:#3E4A3D"


def t_contact(r, im, rnd):
    frames = "".join(f'<div style="width:420px;height:300px;overflow:hidden;border:4px solid #111"><img src="{im["grey"]}" style="width:100%;height:100%;object-fit:cover;object-position:{p};filter:contrast(1.15)"></div>'
                     for p in ("20% 50%", "50% 50%", "80% 50%"))
    body = el(f'<div style="display:flex;gap:18px;background:#111;padding:40px 30px">{frames}</div>', 140, 300, .1, "pop", z=4)
    body += el('<svg width="480" height="360"><ellipse cx="240" cy="180" rx="226" ry="166" stroke="#E2451D" stroke-width="8" fill="none"/></svg>', 568, 270, .6, "draw", z=6)
    body += el(f'<div style="font:700 70px Caveat;color:#E2451D">{r["theme"]}</div><div style="font:500 22px Plex;color:#ddd;letter-spacing:2px">{r["kicker"].upper()}</div>', 150, 720, .8, "wipe", z=6)
    body += el('<div style="font:500 16px Plex;color:#c98a3a;letter-spacing:6px">▸ 14A  ▸ 15  ▸ 15A  KODAK SAFETY FILM</div>', 170, 280, .3, "wipe", z=6)
    return body, "background:#1d1d1f"


def t_sunburst(r, im, rnd):
    col = rnd.choice(["#E8571E", "#2E6E73", "#B3263E", "#D99A1E"])
    body = K.sunburst(960, 560, 1500, col, 44, 0, 1)
    body += K.disc_frame(f'<img src="{im["grey"]}" style="width:100%;height:100%;object-fit:cover;filter:contrast(1.2)">', 960, 520, 330, "#F1E7D2", .2)
    body += el(f'<div style="background:#F1E7D2;padding:10px 40px 18px;font:900 96px Playfair;color:#141414;text-align:center;white-space:nowrap">{r["theme"]}</div>', 960, 900, .5, "slide", base="translateX(-50%)", z=8)
    return body, "background:#F1E7D2"


def t_loupe(r, im, rnd):
    body = el(f'<div style="width:1920px;height:1080px;overflow:hidden"><img src="{im["web"]}" style="width:100%;height:100%;object-fit:cover;filter:brightness(.35) grayscale(.6)"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
    body += el(f'<div style="width:520px;height:520px;border-radius:50%;overflow:hidden;border:14px solid #e8e2d4;box-shadow:0 30px 60px rgba(0,0,0,.6)"><img src="{im["web"]}" style="width:1920px;height:1080px;object-fit:cover;margin-left:-700px;margin-top:-280px;transform:scale(1.3);transform-origin:960px 540px"></div>', 700, 280, .3, "pop", z=5)
    body += el(f'<div style="width:40px;height:220px;background:#2b2b2b;border-radius:20px"></div>', 1170, 740, .3, "pop", base="rotate(-40deg)", z=4)
    body += el(title_block(r["theme"], r["kicker"], "400 110px Serif", 110, "#f4efe4", "Plex", 22, SIG, width=560), 110, 120, .5, "slide", z=6)
    return body, "background:#000"


def t_mirror(r, im, rnd):
    half = f'<div style="width:760px;height:900px;overflow:hidden"><img src="{im["grey"]}" style="width:1520px;height:900px;object-fit:cover;filter:contrast(1.15)"></div>'
    body = el(half, 200, 90, .1, "pop", z=3) + el(f'<div style="transform:scaleX(-1)">{half}</div>', 960, 90, .3, "pop", z=3)
    body += el('<div style="width:6px;height:900px;background:#F4F1EA"></div>', 957, 90, .5, "pop", z=5)
    body += el(f'<div style="background:#F4F1EA;padding:12px 30px;font:400 76px ISerif;color:#141414;white-space:nowrap">{r["theme"]}</div>', 960, 880, .7, "wipe", base="translateX(-50%)", z=6)
    return body, "background:#141414"


def t_inkblot(r, im, rnd):
    pts = []
    for _ in range(26):
        x, y, s = rnd.randint(0, 520), rnd.randint(-380, 380), rnd.randint(20, 120)
        pts.append(f'<ellipse cx="{960 - x}" cy="{540 + y}" rx="{s}" ry="{int(s * rnd.uniform(.6, 1.4))}"/><ellipse cx="{960 + x}" cy="{540 + y}" rx="{s}" ry="{int(s * rnd.uniform(.6, 1.4))}"/>')
    blot = f'<svg width="1920" height="1080"><filter id="b"><feTurbulence baseFrequency=".02" numOctaves="3"/><feDisplacementMap in="SourceGraphic" scale="40"/></filter><g fill="#1a1a1a" filter="url(#b)" opacity=".92">{"".join(pts)}</g></svg>'
    body = el(blot, 0, 0, .1, "pop", z=2)
    body += el(f'<div style="width:420px;height:540px;border-radius:50%;overflow:hidden;border:10px solid #EFE9DC"><img src="{im["web"]}" style="width:100%;height:100%;object-fit:cover"></div>', 750, 230, .4, "pop", z=5)
    body += el(f'<div style="font:400 74px Kalam;color:#8E1B1B;white-space:nowrap">{r["theme"]}</div>', 960, 60, .6, "wipe", base="translateX(-50%)", z=6)
    body += el(f'<div style="font:500 22px Plex;letter-spacing:3px;color:#333;white-space:nowrap">{r["kicker"].upper()}</div>', 960, 990, .8, "wipe", base="translateX(-50%)", z=6)
    return body, "background:#EFE9DC"


T_PF = [t_kraft, t_duotone, t_board, t_newsprint, t_riso, t_blueprint, t_contact, t_sunburst, t_loupe]
T_DP = [t_museum, t_mirror, t_inkblot, t_duotone, t_riso, t_loupe, t_sunburst, t_kraft, t_contact]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    plan = {}
    for rows, ts in ((PF, T_PF), (DP, T_DP)):
        for i, (tid, *_x) in enumerate(rows):
            if tid not in rec:
                continue
            if only and tid not in only:
                continue
            t = ts[i % len(ts)]
            rnd = random.Random(tid)
            im = prep(tid)
            body, bg = t(rec[tid], im, rnd)
            (D / "html" / f"{tid}.html").write_text(K.page(FACES + body, bg, 5, .03, credit(rec[tid])), encoding="utf-8")
            plan[tid] = t.__name__
    (D / "data" / "treatments.json").write_text(json.dumps(plan, indent=1))
    print(len(plan), "pages")
