"""Key frames for 'In Event of Moon Disaster' (visuals before video). Real material only: the memo scans (National
Archives NAID 6922351), NASA TV footage and NASA photographs, all public domain; layout, type and paper are ours."""
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/Forgeos/creatorforge/channels/design_kits/collage")
import collage2 as K
from collage2 import el, STILL

D = Path(__file__).resolve().parent
A = D / "assets"
FONTS = K.FONTS
INKS, ONION, REGO, ABORT, SIG = "#0B0D12", "#F2EEE3", "#8D8A84", "#C8372D", "#FFDD33"
u = lambda name: (A / name).as_uri()

FACES = f"""<style>
@font-face{{font-family:ISerif;src:url({(FONTS / 'instrument-serif-latin-400-normal.woff2').as_uri()})}}
@font-face{{font-family:ISerifI;src:url({(FONTS / 'instrument-serif-latin-400-italic.woff2').as_uri()})}}
@font-face{{font-family:Grotesk;src:url({(FONTS / 'space-grotesk-latin-700-normal.woff2').as_uri()})}}
.chip{{font:500 17px DMono;letter-spacing:2px;text-transform:uppercase;padding:7px 12px}}
.onion{{background:{ONION};box-shadow:0 30px 60px rgba(0,0,0,.55),0 2px 0 rgba(255,255,255,.4) inset}}
.credit{{color:rgba(242,238,227,.62)!important;font-family:DMono!important}}
</style>"""
SPACE = f"background:radial-gradient(ellipse at 50% 40%,#161a24 0%,{INKS} 70%)"


def gate(img, w, h, crop="", label="KODAK 16MM SAFETY FILM · NASA · APOLLO 11"):
    """A 16 mm film gate: sprocket holes on the left, edge code, rounded gate corners."""
    holes = "".join(f'<div style="position:absolute;left:14px;top:{20 + i * 74}px;width:26px;height:36px;border-radius:5px;background:#1d2028"></div>'
                    for i in range(int(h / 74) + 1))
    return (f'<div style="position:relative;width:{w + 90}px;height:{h + 40}px;background:#050608;border-radius:6px">{holes}'
            f'<div style="position:absolute;left:64px;top:20px;width:{w}px;height:{h}px;overflow:hidden;border-radius:14px">'
            f'<img src="{img}" style="width:100%;height:100%;object-fit:cover;{crop};filter:contrast(1.08) brightness(1.05)"></div>'
            f'<div style="position:absolute;left:64px;bottom:2px;font:500 12px DMono;letter-spacing:4px;color:#c98a3a">{label}</div></div>')


def chip(text, bg=ONION, col=INKS):
    return f'<div class="chip" style="background:{bg};color:{col}">{text}</div>'


S = {}

# F1. Footage opening: the first steps, in a 16 mm gate
body = FACES + el(gate(u("moonwalk_47.jpg"), 1300, 950, "object-position:50% 50%;transform:scale(1.34)"), 265, 22, 0, "pop", extra=STILL, z=3)
body += el(chip("JULY 1969 · SEA OF TRANQUILITY"), 360, 880, .4, "wipe", z=6)
body += el(f'<div style="font:500 20px DMono;color:{ONION};letter-spacing:3px">NASA TV · LIVE FROM THE MOON</div>', 1290, 60, .6, "wipe", z=6)
S["f1_footage"] = (body, SPACE, "FOOTAGE: NASA, APOLLO 11 TELEVISION, JULY 1969 (PUBLIC DOMAIN)")

# F2. Evidence: the memo itself, on onionskin, header highlighted
memo = (f'<div class="onion" style="width:860px;height:1128px;overflow:hidden;position:relative">'
        f'<img src="{u("RN100_6-1.jpg")}" style="width:100%;mix-blend-mode:multiply;filter:contrast(1.15) sepia(.12)">'
        f'<div style="position:absolute;left:96px;top:133px;width:452px;height:30px;background:{SIG};mix-blend-mode:multiply;opacity:.85"></div>'
        f'<div style="position:absolute;left:96px;top:170px;width:640px;height:30px;background:{SIG};mix-blend-mode:multiply;opacity:.85"></div></div>')
body = FACES + el(memo, 300, -40, .1, "drop", base="rotate(-2.2deg)", z=4)
body += el(f'<div style="font:700 64px/1.05 Grotesk;color:{ONION};width:560px">July 18, 1969.<br><span style="color:{REGO}">Two days before the landing.</span></div>', 1230, 300, .5, "slide", z=6)
body += el(chip("NATIONAL ARCHIVES · NAID 6922351 · NIXON LIBRARY"), 1230, 560, .9, "wipe", z=6)
body += el(chip("TO: H. R. HALDEMAN · FROM: BILL SAFIRE", SIG), 1230, 612, 1.1, "wipe", z=6)
S["f2_memo"] = (body, SPACE, "DOCUMENT: MEMO, W. SAFIRE TO H. R. HALDEMAN, 18 JULY 1969, PAGE 1 · NATIONAL ARCHIVES (NAID 6922351), USE UNRESTRICTED")

# F3. The title, struck on the typewriter
body = FACES + el(f'<div class="onion" style="width:1920px;height:1080px;opacity:.96"></div>', 0, 0, 0, "pop", extra=STILL, z=1)
body += el(f'<div style="width:1700px;height:300px;overflow:hidden;opacity:.25"><img src="{u("RN100_6-1.jpg")}" style="width:1700px;margin-top:-560px;filter:contrast(1.3)"></div>', 110, 690, 0, "pop", z=2)
letters = "IN EVENT OF MOON DISASTER:"
strike = "".join(f'<span style="display:inline-block;transform:translateY({(-2, 1, -1, 2, 0)[i % 5]}px) rotate({(-.6, .4, 0, .7, -.3)[i % 5]}deg)">{c if c != " " else "&nbsp;"}</span>' for i, c in enumerate(letters))
body += el(f'<div style="font:500 104px DMono;color:{INKS};letter-spacing:2px;text-shadow:0 0 1.5px rgba(11,13,18,.7)">{strike}</div>', 120, 330, .2, "wipe", z=5)
body += el(f'<div style="width:1660px;height:10px;background:{ABORT}"></div>', 124, 480, .9, "wipe", z=5)
body += el(f'<div style="font:700 26px Grotesk;color:{ABORT};letter-spacing:6px">THE TITLE OF THE MEMO, AS TYPED</div>', 124, 260, 1.1, "wipe", z=5)
S["f3_title"] = (body, f"background:{ONION}", "DOCUMENT: MEMO PAGE 1 (NATIONAL ARCHIVES, NAID 6922351), TITLE LINE RESET IN TYPE FOR LEGIBILITY")

# F4. The speech over the real photograph
body = FACES + el(f'<img src="{u("as11-40-5903.jpg")}" style="width:1920px;height:1080px;object-fit:cover;object-position:50% 38%;filter:grayscale(.85) brightness(.55) contrast(1.15)">', 0, 0, 0, "pop", extra=STILL, z=1)
body += el(f'<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(11,13,18,.92) 0%,rgba(11,13,18,.6) 46%,transparent 70%)"></div>', 0, 0, 0, "pop", extra=STILL, z=2)
body += el(f'<div style="font:400 74px/1.12 ISerifI;color:{ONION};width:920px">“Fate has ordained that the men who went to the moon to explore in peace will stay on the moon to rest&nbsp;in&nbsp;peace.”</div>', 120, 250, .3, "slide", z=5)
body += el(chip("THE SPEECH · MEMO PAGE 1", ABORT, ONION), 124, 170, .2, "wipe", z=6)
body += el(f'<div style="font:500 18px DMono;color:{REGO};letter-spacing:2px">NEVER DELIVERED</div>', 124, 760, 1.2, "wipe", z=6)
S["f4_speech"] = (body, SPACE, "PHOTO: NASA AS11-40-5903, EDWIN ALDRIN, 20 JULY 1969 (PUBLIC DOMAIN) · QUOTE: MEMO, 18 JULY 1969 (NATIONAL ARCHIVES)")

# F5. The plan: page 2 as a three-step procedure card
steps = [("01", "PRIOR TO THE PRESIDENT'S STATEMENT", "“The President should telephone each of the widows-to-be.”"),
         ("02", "THE PRESIDENT'S STATEMENT", "“Fate has ordained that the men who went to the moon…”"),
         ("03", "AT THE POINT WHEN NASA ENDS COMMUNICATIONS WITH THE MEN", "“A clergyman should adopt the same procedure as a burial at sea, commending their souls to ‘the deepest of the deep.’”")]
card = "".join(f'<div style="display:flex;gap:26px;padding:26px 0;border-top:2px solid {INKS}">'
               f'<div style="font:700 56px Grotesk;color:{ABORT};width:90px">{n}</div><div><div style="font:500 18px DMono;letter-spacing:2px;color:{INKS}">{h}</div>'
               f'<div style="font:400 40px/1.15 ISerif;color:{INKS};margin-top:8px;width:760px">{t}</div></div></div>' for n, h, t in steps)
body = FACES + el(f'<div class="onion" style="padding:40px 54px 30px;width:900px"><div style="font:700 30px Grotesk;letter-spacing:5px;color:{INKS};margin-bottom:16px">THE PLAN · MEMO PAGE 2</div>{card}</div>', 120, 70, .2, "drop", base="rotate(-.8deg)", z=5)
body += el(f'<div class="onion" style="width:620px;height:860px;overflow:hidden"><img src="{u("RN100_6-2.jpg")}" style="width:100%;margin-top:-20px;mix-blend-mode:multiply;filter:contrast(1.15) sepia(.12)"></div>', 1190, 120, .6, "drop", base="rotate(2.4deg)", z=4)
body += el(f'<div style="width:470px;height:24px;background:{SIG};mix-blend-mode:multiply;opacity:.8"></div>', 1262, 549, 1.0, "wipe", base="rotate(2.4deg)", z=6)
S["f5_plan"] = (body, SPACE, "DOCUMENT: MEMO PAGES 1 AND 2 (NATIONAL ARCHIVES, NAID 6922351) · HEADINGS AND QUOTES ARE THE MEMO'S OWN WORDS")

# F6. Signature motif: the carbon copy under history (a real corner peel)
W6, H6, X6, Y6 = 1500, 820, 210, 60
A6, B6 = (W6, 120), (380, H6)                               # the fold line


def _reflect(pt, a=A6, b=B6):
    (x, y), (x1, y1), (x2, y2) = pt, a, b
    dx, dy = x2 - x1, y2 - y1
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    px, py = x1 + t * dx, y1 + t * dy
    return 2 * px - x, 2 * py - y


fx, fy = _reflect((W6, H6))
carbon = (f'<div style="width:{W6}px;height:{H6}px;background:#26244a;position:relative;overflow:hidden">'
          f'<div style="position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.035) 0 2px,transparent 2px 5px)"></div>'
          f'<div style="position:absolute;right:60px;bottom:70px;width:640px;text-align:right;font:400 44px/1.25 ISerifI;color:#a9a6ef">“…they will be mourned by a Mother Earth that dared send two of her sons into the unknown.”</div>'
          f'<div style="position:absolute;right:60px;bottom:30px;font:500 16px DMono;letter-spacing:3px;color:#a9a6ef">CARBON · NEVER READ</div></div>')
top = (f'<div style="width:{W6}px;height:{H6}px;clip-path:polygon(0 0,{A6[0]}px 0,{A6[0]}px {A6[1]}px,{B6[0]}px {B6[1]}px,0 {H6}px)">'
       f'<img src="{u("moonwalk_110.jpg")}" style="width:100%;height:100%;object-fit:cover;transform:scale(1.36);filter:contrast(1.1)"></div>')
flap = (f'<svg width="{W6}" height="{H6}" style="overflow:visible"><defs><linearGradient id="fg" x1="1" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="#d9d3c4"/><stop offset="1" stop-color="{ONION}"/></linearGradient>'
        f'<filter id="fs"><feDropShadow dx="-14" dy="-10" stdDeviation="14" flood-opacity=".55"/></filter></defs>'
        f'<polygon points="{A6[0]},{A6[1]} {B6[0]},{B6[1]} {fx:.0f},{fy:.0f}" fill="url(#fg)" filter="url(#fs)"/></svg>')
body = FACES + el(carbon, X6, Y6, 0, "pop", extra=STILL, z=2) + el(top, X6, Y6, .2, "pop", extra=STILL, z=3)
body += el(flap, X6, Y6, .6, "pop", z=4)
body += el(f'<div style="font:500 18px DMono;letter-spacing:3px;color:{ONION};background:rgba(11,13,18,.7);padding:6px 10px">HISTORY · TOP COPY</div>', X6 + 40, Y6 + 40, .4, "wipe", z=6)
body += el(f'<div style="font:700 56px Grotesk;color:{ONION}">History had a second draft.</div>', X6, Y6 + H6 + 34, .9, "wipe", z=6)
S["f6_carbon"] = (body, SPACE, "FOOTAGE: NASA, APOLLO 11 TELEVISION · CARBON: OUR ILLUSTRATION OF THE SPEECH TEXT (MEMO PAGE 1, NATIONAL ARCHIVES)")

# F7. Two timelines: the real mission clock against the 'if' branch
days = [("16 JUL", "Launch · 9:32 a.m. EDT", 180), ("20 JUL", "Eagle lands", 760), ("21 JUL", "Ascent engine fires · 124 h 22 min", 1060), ("24 JUL", "Splashdown", 1700)]
track = (f'<svg width="1920" height="1080"><line x1="180" y1="520" x2="1700" y2="520" stroke="{ONION}" stroke-width="6"/>'
         + "".join(f'<circle cx="{x}" cy="520" r="16" fill="{SIG if d == "21 JUL" else ONION}"/>' for d, _, x in days) + "</svg>")
body = FACES + el(track, 0, 0, .2, "draw", z=3)
branch = f'<svg width="1920" height="1080"><path d="M1060 520 C 1160 520 1200 760 1320 790 L 1640 790" stroke="{ABORT}" stroke-width="5" fill="none" stroke-dasharray="18 14"/></svg>'
body += el(branch, 0, 0, .9, "pop", z=2)      # dashed: the plan that was never carried out (no draw-on, which would make it solid)
for d, lab, x in days:
    body += el(f'<div style="font:700 44px Grotesk;color:{ONION}">{d}</div><div style="font:500 18px DMono;color:{REGO};letter-spacing:1px;white-space:nowrap">{lab.upper()}</div>', x - 30, 380, .4, "slide", z=5)
body += el(f'<div style="font:500 18px DMono;color:{ABORT};letter-spacing:2px;width:560px">IF THE ENGINE HAD FAILED:<br>THE CALLS · THE STATEMENT · THE CUT-OFF</div>', 1190, 820, 1.0, "wipe", z=5)
body += el(f'<div style="font:400 66px ISerifI;color:{ONION}">What happened, and what was written.</div>', 180, 150, .1, "slide", z=5)
body += el(chip("MISSION CLOCK · NASA", ONION), 180, 640, .8, "wipe", z=5)
S["f7_timelines"] = (body, SPACE, "SOURCE: NASA, APOLLO 11 MISSION OVERVIEW (LAUNCH, LANDING, ASCENT AT 124 H 22 MIN, SPLASHDOWN) · DASHED: THE MEMO'S PLAN, NEVER CARRIED OUT")

# F8. Payoff: Earth over the lunar limb, the memo's last line
body = FACES + el(f'<img src="{u("as11-44-6549.jpg")}" style="width:1920px;height:1080px;object-fit:cover;object-position:50% 60%">', 0, 0, 0, "pop", extra=STILL, z=1)
body += el(f'<div style="width:1920px;height:1080px;background:linear-gradient(0deg,rgba(11,13,18,.92) 0%,rgba(11,13,18,.35) 45%,transparent 70%)"></div>', 0, 0, 0, "pop", extra=STILL, z=2)
body += el(f'<div style="font:400 70px/1.12 ISerifI;color:{ONION};width:1500px">“…some corner of another world that is forever mankind.”</div>', 210, 720, .3, "slide", z=5)
body += el(f'<div style="font:700 30px Grotesk;color:{SIG};letter-spacing:5px">THE SPEECH WAS NEVER READ.</div>', 214, 940, 1.0, "wipe", z=5)
S["f8_payoff"] = (body, SPACE, "PHOTO: NASA AS11-44-6549, EARTH OVER THE LUNAR HORIZON, APOLLO 11 (PUBLIC DOMAIN) · QUOTE: MEMO PAGE 2, NATIONAL ARCHIVES")

if __name__ == "__main__":
    out = D / "stills" / "html"
    out.mkdir(parents=True, exist_ok=True)
    for k, (body, bg, cr) in S.items():
        (out / f"{k}.html").write_text(K.page(body, bg, 5, .03, cr), encoding="utf-8")
    print(len(S), "frames")
