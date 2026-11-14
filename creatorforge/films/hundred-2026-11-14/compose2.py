"""100 images, no two alike. Each image draws its own combination of seven dimensions: frame, image treatment,
surface, type pairing, layout, prop and a palette built from its own hue. The planner guarantees that no two images
share the same (frame, treatment, surface, type pairing) and that neighbours never share a frame, surface or pairing.
Text stays to the theme title, its kicker and the archive record. No charts, no AI imagery."""
import colorsys
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/Forgeos/creatorforge/channels/design_kits/collage")
import collage2 as K
from collage2 import el, STILL
from compose import FACES, credit, prep, rec
from topics import DP, PF

D = Path(__file__).resolve().parent
SIG = "#FFDD33"
EXTRA = "<style>" + "".join(f"@font-face{{font-family:{n};src:url({(K.FONTS / (p + '.woff2')).as_uri()})}}" for n, p in (
    ("Mukta", "mukta-devanagari-800-normal"), ("FrauncesI", "fraunces-latin-400-italic"), ("DMSerif", "dm-serif-display-latin-400-normal"))) + "</style>"
POSTER = ('<svg width="0" height="0" style="position:absolute"><filter id="post"><feComponentTransfer><feFuncR type="discrete" tableValues="0 .33 .66 1"/>'
          '<feFuncG type="discrete" tableValues="0 .33 .66 1"/><feFuncB type="discrete" tableValues="0 .33 .66 1"/></feComponentTransfer></filter></svg>')

FRAMES = ["rect", "polaroid", "disc", "arch", "torn", "gate", "oval", "stamp", "ticket", "stack", "bleed", "mirror"]
TREAT = ["natural", "halftone", "duotone", "riso", "greyhi", "sepia", "cyanotype", "posterize", "tint"]
SURF = ["kraft", "cream", "grid", "cork", "slate", "solid", "newsprint", "blueprint", "linen", "black"]
TYPE = [("Anton", "400", "Plex", .42), ("Playfair", "900", "Mono", .56), ("Bebas", "400", "DMono", .38), ("Fraunces", "900", "Inter", .6),
        ("DMSerif", "400", "Oswald", .5), ("ISerif", "400", "Plex", .45), ("Grotesk", "700", "DMono", .56), ("Archivo", "400", "Caveat", .66),
        ("Oswald", "600", "Kalam", .46), ("PlayfairI", "700", "Bebas", .5), ("Marker", "400", "Mono", .6), ("ISerifI", "400", "Grotesk", .42),
        ("Mukta", "800", "Plex", .55), ("FrauncesI", "400", "Oswald", .48)]
LAYOUT = ["left", "right", "centre", "top", "behind", "corner"]
PROPS = ["none", "tape", "pin", "clip", "postmark", "ruler", "highlight", "index"]


def palette(i):
    """A hue of its own per image (golden-ratio spacing), with ink, paper and accent derived from it."""
    h = (i * 0.61803398875) % 1
    rgb = lambda hh, l, s: "#%02x%02x%02x" % tuple(int(c * 255) for c in colorsys.hls_to_rgb(hh, l, s))
    return {"accent": rgb(h, .5, .72), "dark": rgb(h, .14, .45), "light": rgb((h + .08) % 1, .9, .45), "mid": rgb(h, .32, .4)}


def surface(kind, p):
    return {"kraft": "background:#C9A97A", "cream": "background:#F2ECDF",
            "grid": "background:#F4F2EA;background-image:linear-gradient(rgba(0,0,0,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.07) 1px,transparent 1px);background-size:36px 36px",
            "cork": "background:#9A6B3F;background-image:radial-gradient(rgba(0,0,0,.14) 1px,transparent 1px);background-size:8px 8px",
            "slate": "background:#2B2F36", "solid": f"background:{p['light']}",
            "newsprint": "background:#E9E4D6;background-image:repeating-linear-gradient(0deg,rgba(0,0,0,.035) 0 1px,transparent 1px 4px)",
            "blueprint": "background:#123B6B;background-image:linear-gradient(rgba(255,255,255,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.12) 1px,transparent 1px);background-size:40px 40px",
            "linen": "background:#E6DFD1;background-image:repeating-linear-gradient(45deg,rgba(0,0,0,.03) 0 2px,transparent 2px 6px),repeating-linear-gradient(-45deg,rgba(0,0,0,.03) 0 2px,transparent 2px 6px)",
            "black": "background:#0D0D0E"}[kind]


DARK_SURF = {"slate", "blueprint", "black"}


def picture(treat, im, p, w, h, pos="50% 45%"):
    """The image, w x h, in its treatment (CSS and blend layers only; the halftone is pre-drawn)."""
    base = f'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{pos}'
    if treat == "halftone":
        inner = f'<img src="{im["ht"]}" style="{base};background:#fff">'
    elif treat == "duotone":
        inner = (f'<img src="{im["grey"]}" style="{base};filter:contrast(1.15)"><div style="position:absolute;inset:0;background:{p["light"]};mix-blend-mode:multiply"></div>'
                 f'<div style="position:absolute;inset:0;background:{p["dark"]};mix-blend-mode:lighten"></div>')
    elif treat == "riso":
        ink = lambda col, dx, dy, op: (f'<div style="position:absolute;left:{dx}px;top:{dy}px;width:{w}px;height:{h}px;mix-blend-mode:multiply;opacity:{op}">'
                                       f'<img src="{im["grey"]}" style="{base};filter:contrast(1.7)"><div style="position:absolute;inset:0;background:{col};mix-blend-mode:screen"></div></div>')
        inner = f'<div style="position:absolute;inset:0;background:#F6F1E7"></div>{ink(p["accent"], 0, 0, 1)}{ink(p["dark"], 12, 9, .85)}'
    elif treat == "cyanotype":
        inner = (f'<img src="{im["grey"]}" style="{base};filter:contrast(1.2)"><div style="position:absolute;inset:0;background:#DCE8F4;mix-blend-mode:multiply"></div>'
                 f'<div style="position:absolute;inset:0;background:#0E3466;mix-blend-mode:lighten"></div>')
    elif treat == "tint":
        inner = f'<img src="{im["web"]}" style="{base}"><div style="position:absolute;inset:0;background:{p["accent"]};mix-blend-mode:multiply;opacity:.35"></div>'
    else:
        flt = {"natural": "none", "greyhi": "grayscale(1) contrast(1.45)", "sepia": "sepia(.85) contrast(1.1) brightness(.98)",
               "posterize": "url(#post) saturate(1.3)"}[treat]
        inner = f'<img src="{im["web"]}" style="{base};filter:{flt}">'
    return f'<div style="position:relative;width:{w}px;height:{h}px;overflow:hidden;isolation:isolate">{inner}</div>'


def framed(frame, pic, w, h, p, rnd):
    """Wrap the picture in its frame; returns html and the frame's outer size."""
    if frame == "polaroid":
        return f'<div style="background:#fbfaf6;padding:22px 22px 86px;box-shadow:0 18px 34px rgba(0,0,0,.4)">{pic}</div>', w + 44, h + 108
    if frame == "disc":
        return f'<div style="width:{w}px;height:{w}px;border-radius:50%;overflow:hidden;border:16px solid #F1E7D2;box-shadow:0 20px 40px rgba(0,0,0,.4)">{pic}</div>', w + 32, w + 32
    if frame == "arch":
        return f'<div style="border-radius:{w // 2}px {w // 2}px 0 0;overflow:hidden;box-shadow:0 22px 40px rgba(0,0,0,.4);border:12px solid {p["mid"]}">{pic}</div>', w + 24, h + 24
    if frame == "torn":
        pts = ",".join(f"{x}% {rnd.uniform(0, 2.4):.1f}%" for x in range(0, 101, 4)) + "," + ",".join(f"{x}% {100 - rnd.uniform(0, 2.4):.1f}%" for x in range(100, -1, -4))
        return f'<div style="filter:drop-shadow(0 14px 18px rgba(0,0,0,.4))"><div style="clip-path:polygon({pts})">{pic}</div></div>', w, h
    if frame == "gate":
        holes = "".join(f'<div style="position:absolute;left:12px;top:{16 + k * 64}px;width:22px;height:30px;border-radius:4px;background:#2a2c33"></div>' for k in range(h // 64 + 1))
        return (f'<div style="position:relative;background:#060708;padding:18px 18px 18px 56px;border-radius:6px">{holes}<div style="border-radius:12px;overflow:hidden">{pic}</div>'
                f'<div style="position:absolute;left:56px;bottom:0;font:500 11px DMono;letter-spacing:4px;color:#c98a3a">KODAK SAFETY FILM · {rnd.randint(10, 36)}A</div></div>'), w + 74, h + 36
    if frame == "oval":
        return f'<div style="border-radius:50%;overflow:hidden;border:10px solid {p["light"]};box-shadow:0 18px 30px rgba(0,0,0,.35)">{pic}</div>', w + 20, h + 20
    if frame == "stamp":
        mask = "radial-gradient(circle at 10px 10px,transparent 7px,#000 7.5px) -10px -10px/20px 20px"
        paper = f'<div style="position:absolute;inset:0;background:#fbfaf6;-webkit-mask:{mask};mask:{mask}"></div>'   # holes show only in the margin
        return (f'<div style="position:relative;padding:24px;filter:drop-shadow(0 10px 14px rgba(0,0,0,.35))">{paper}'
                f'<div style="position:relative">{pic}</div></div>'), w + 48, h + 48
    if frame == "ticket":
        return (f'<div style="display:flex;filter:drop-shadow(0 14px 20px rgba(0,0,0,.35))"><div style="background:#fbf6e8;padding:20px">{pic}</div>'
                f'<div style="background:#fbf6e8;width:90px;border-left:4px dashed {p["mid"]};display:flex;align-items:center;justify-content:center;writing-mode:vertical-rl;'
                f'font:500 18px DMono;letter-spacing:4px;color:{p["mid"]}">ADMIT ONE · No {rnd.randint(1000, 9999)}</div></div>'), w + 134, h + 40
    if frame == "stack":
        return (f'<div style="position:relative"><div style="position:absolute;left:26px;top:22px;width:{w}px;height:{h}px;background:#e9e4d8;transform:rotate(4deg);box-shadow:0 10px 20px rgba(0,0,0,.3)"></div>'
                f'<div style="position:absolute;left:-14px;top:10px;width:{w}px;height:{h}px;background:#f3efe6;transform:rotate(-3deg);box-shadow:0 10px 20px rgba(0,0,0,.3)"></div>'
                f'<div style="position:relative;box-shadow:0 14px 26px rgba(0,0,0,.4)">{pic}</div></div>'), w, h
    return f'<div style="box-shadow:0 22px 44px rgba(0,0,0,.42)">{pic}</div>', w, h          # rect


def fit(text, width, base, factor):
    return int(max(40, min(base, width / max(1, len(text) * factor * 1.22))))   # 22% safety margin


def build(i, tid, r, combo):
    frame, treat, surf, tp, lay, prop = combo
    p = palette(i)
    rnd = random.Random(tid)
    im = prep(tid)
    dark = surf in DARK_SURF
    ink, sub = ("#F3EFE6", "#BFB8AA") if dark else ("#151515", "#4a4a4a")
    if surf == "solid":
        ink, sub = p["dark"], p["mid"]
    tf, tw, kf, cw = TYPE[tp]
    body, bg = "", surface(surf, p)

    def title(x, y, width, base=150, align="left", col=None, z=6):
        size = fit(r["theme"], width, base, cw)
        t = f'<div style="font:{tw} {size}px/0.95 {tf};color:{col or ink};text-align:{align};width:{width}px">{r["theme"]}</div>'
        k = f'<div style="font:500 22px/1.3 {kf};letter-spacing:2px;color:{p["accent"] if not dark else SIG};text-transform:uppercase;text-align:{align};width:{width}px;margin-top:16px">{r["kicker"]}</div>'
        return el(t + k, x, y, .4, "wipe", z=z), size

    if frame in ("bleed", "mirror"):
        pic = picture(treat, im, p, 1920, 1080) if frame == "bleed" else (
            f'<div style="display:flex">{picture(treat, im, p, 960, 1080, "30% 45%")}<div style="transform:scaleX(-1)">{picture(treat, im, p, 960, 1080, "30% 45%")}</div></div>')
        body += el(pic, 0, 0, 0, "pop", extra=STILL, z=1)
        body += el(f'<div style="width:1920px;height:1080px;background:linear-gradient({ {"left": "90deg", "right": "270deg", "top": "180deg"}.get(lay, "0deg") },{p["dark"]}ee 0%,{p["dark"]}55 45%,transparent 70%)"></div>', 0, 0, 0, "pop", extra=STILL, z=2)
        if frame == "mirror":
            body += el('<div style="width:5px;height:1080px;background:#F4F1EA"></div>', 957, 0, .3, "pop", z=3)
        tx, ty, tw_, al = {"left": (110, 360, 820, "left"), "right": (990, 360, 820, "right"), "top": (110, 90, 1400, "left"),
                           "behind": (110, 640, 1700, "left"), "corner": (110, 760, 1100, "left"), "centre": (310, 700, 1300, "center")}[lay]
        t, _ = title(tx, ty, tw_, 190, al, "#F7F2E8")
        body += t
        return body, f"background:{p['dark']}"

    # image box per layout
    portrait = im["h"] > im["w"] * 1.05
    if lay in ("left", "right"):
        w, h = (620, 820) if portrait else (980, 700)
        if frame in ("disc",):
            w = h = 700
        x = 130 if lay == "left" else 1920 - 130 - w
        y = (1080 - h) // 2 - 10
        tx, ty, tw_ = (x + w + 110, 330, 1920 - (x + w + 110) - 110) if lay == "left" else (130, 330, x - 240)
        al = "left"
    elif lay == "centre":
        w, h = (560, 700) if portrait else (900, 620)
        if frame == "disc":
            w = h = 640
        x, y = (1920 - w) // 2, 70
        tx, ty, tw_, al = 260, y + h + 70, 1400, "center"
    elif lay == "top":
        w, h = 1500, 600
        if frame == "disc":
            w = h = 620
        x, y = (1920 - w) // 2, 60
        tx, ty, tw_, al = (1920 - 1500) // 2, y + h + 70, 1500, "left"
    elif lay == "behind":
        w, h = (560, 760) if portrait else (900, 640)
        if frame == "disc":
            w = h = 660
        x, y = 980, (1080 - h) // 2
        tx, ty, tw_, al = 100, 180, 1700, "left"
    else:  # corner
        w, h = (700, 920) if portrait else (1180, 820)
        if frame == "disc":
            w = h = 820
        x, y = 1920 - w - 110, 70
        tx, ty, tw_, al = 110, 700, max(560, 1920 - w - 330), "left"
    if frame == "ticket":
        w = min(w, 1920 - x - 240) if lay != "right" else w
    pic = picture(treat, im, p, w, h)
    html, fw, fh = framed(frame, pic, w, h, p, rnd)
    rot = rnd.choice([-2.2, -1.2, 0, 1.4, 2.4]) if frame in ("polaroid", "stamp", "stack", "torn", "ticket", "rect") else 0
    body += el(html, x, y, .1, "drop", base=f"rotate({rot}deg)", z=4)
    if lay == "behind":
        words = r["theme"].upper().split()
        longest = max(words, key=len)
        size = int(min(230, fit(longest, 800, 260, cw * 1.15), 820 / (len(words) * .95)))
        body += el(f'<div style="font:{tw} {size}px/0.92 {tf};color:{p["accent"]};width:820px;text-transform:uppercase">{"<br>".join(words)}</div>', 100, 140, .2, "wipe", z=3)
        body += el(f'<div style="font:500 24px/1.3 {kf};letter-spacing:2px;color:{ink};text-transform:uppercase;width:760px">{r["kicker"]}</div>', 104, 900, .6, "wipe", z=6)
    else:
        t, _ = title(tx, ty, tw_, 160, al)
        body += t

    # one prop
    if prop == "tape":
        for (dx, dy, rr) in ((-40, -18, -14), (fw - 120, fh - 24, 10)):
            body += el('<div style="width:160px;height:42px;background:rgba(236,226,190,.85);box-shadow:0 2px 4px rgba(0,0,0,.15)"></div>', x + dx, y + dy, .5, "pop", base=f"rotate({rr}deg)", z=8)
    elif prop == "pin":
        body += K.pin_dot(x + fw // 2, y + 8)
    elif prop == "clip":
        body += el(f'<svg width="60" height="140"><path d="M20 130 V30 a14 14 0 0 1 28 0 V110 a8 8 0 0 1 -16 0 V40" stroke="#8d9097" stroke-width="5" fill="none"/></svg>', x + 60, y - 50, .5, "pop", z=8)
    elif prop == "postmark":
        yr = (r.get("date") or "")[:4]
        body += el(f'<div style="width:190px;height:190px;border-radius:50%;border:5px solid {p["accent"]};display:flex;align-items:center;justify-content:center;'
                   f'font:700 30px Mono;color:{p["accent"]};opacity:.8;transform:rotate(-14deg)">{yr if yr.isdigit() else "ARCHIVE"}</div>', x + fw - 150, y + fh - 150, .7, "pop", z=8)
    elif prop == "ruler":
        ticks = "".join(f'<div style="position:absolute;left:{k * 20}px;top:0;width:2px;height:{24 if k % 5 == 0 else 12}px;background:{ink}"></div>' for k in range(fw // 20 + 1))
        body += el(f'<div style="position:relative;width:{fw}px;height:26px">{ticks}</div>', x, y + fh + 26, .6, "wipe", z=6)
    elif prop == "highlight" and lay != "behind":
        body += el(f'<div style="width:{min(520, tw_)}px;height:18px;background:{SIG}"></div>', tx if al != "center" else (1920 - 520) // 2, ty - 34, .7, "wipe", z=5)
    elif prop == "index":
        body += K.index_no(f"{i + 1:03d}", x, y - 70) + K.barcode(x + fw - 190, y + fh + 20, 180, 30, i, .6)
    return body, bg


def plan(n, seed=11, banned=None):
    """Choose a combination for each image: all (frame, treatment, surface, type) tuples distinct; neighbours differ
    in frame, surface and type pairing; every dimension spread evenly."""
    rnd = random.Random(seed)
    used, out = set(), []
    count = {d: {} for d in range(6)}
    dims = [FRAMES, TREAT, SURF, list(range(len(TYPE))), LAYOUT, PROPS]
    for i in range(n):
        best = None
        for _ in range(4000):
            c = tuple(rnd.choice(d) for d in dims)
            if c[0] in ("bleed", "mirror") and c[4] not in ("left", "right", "top", "behind", "corner", "centre"):
                continue
            key = c[:4]
            if key in used:
                continue
            if out and (c[0] == out[-1][0] or c[2] == out[-1][2] or c[3] == out[-1][3] or c[1] == out[-1][1] or c[4] == out[-1][4]):
                continue
            if banned and c[1] in banned[i]:
                continue
            if c[0] in ("bleed", "mirror") and c[1] == "halftone":
                continue                                            # full-bleed halftone is unreadable at this size
            score = sum(count[d].get(c[d], 0) for d in range(6))
            if best is None or score < best[0]:
                best = (score, c)
        c = best[1]
        used.add(c[:4])
        for d in range(6):
            count[d][c[d]] = count[d].get(c[d], 0) + 1
        out.append(c)
    return out


if __name__ == "__main__":
    order = [t[0] for t in PF] + [t[0] for t in DP]
    banned = []
    for tid in order:
        st = prep(tid)
        b = set()
        if st["mean"] > 150 or st["mean"] < 75 or st["std"] < 62:
            b |= {"halftone", "riso"}                       # pale or flat images turn to mud in dot screens
        if st["mean"] < 80:
            b |= {"halftone", "cyanotype", "duotone"}       # very dark images lose their subject in these
        banned.append(b)
    combos = plan(len(order), banned=banned)
    # images that read badly in a dot screen even with good statistics: swap only their treatment, keeping every tuple unique
    for tid in ("ice", "canal"):
        k = order.index(tid)
        taken = {c[:4] for c in combos}
        for t in ("cyanotype", "greyhi", "duotone", "natural", "sepia"):
            c = list(combos[k]); c[1] = t
            if tuple(c[:4]) not in taken and t != combos[k][1]:
                combos[k] = tuple(c)
                break
    for f in (D / "html").glob("*.html"):
        f.unlink()
    meta = {}
    only = set(sys.argv[1:])
    for i, (tid, c) in enumerate(zip(order, combos)):
        meta[tid] = dict(zip(("frame", "treatment", "surface", "type", "layout", "prop"), c))
        if only and tid not in only:
            continue
        body, bg = build(i, tid, rec[tid], c)
        (D / "html" / f"{i + 1:03d}_{tid}.html").write_text(K.page(FACES + EXTRA + POSTER + body, bg, 5, .03, credit(rec[tid])), encoding="utf-8")
    (D / "data" / "combos.json").write_text(json.dumps(meta, indent=1))
    keys = [tuple(m[k] for k in ("frame", "treatment", "surface", "type")) for m in meta.values()]
    print(len(meta), "planned ·", len(set(keys)), "distinct (frame, treatment, surface, type) ·",
          len(set(tuple(m.values()) for m in meta.values())), "distinct full combinations")
