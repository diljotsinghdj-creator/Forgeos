"""Key frames (16:9) for "Why India Is Mocked Online" (working title "Disgust Pays"), Print Facts, owner's draft with research
corrections. Every piece carries a timeline entry (render any moment with ?t=0..1). Numbers only from dossier.json.
Nothing here is a real viral clip, a real person or a copyrighted frame: feeds, posts and phones are drawn in the studio."""
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
from studio import page, A, a, put, hl, wobble, chapter, tape, DESK, BLK, PARCH, RED, SIG, INK, FONTS  # noqa: E402

ACC = "#2E86DE"   # film accent: screen blue (the feed, the phone, the platforms)
CH = "#1E2A26"    # chalkboard (drawn object, not a palette colour)


def tag(text, x, y, rot=-1.5, anim="snap .85 .85", dark=False):
    """Sarcastic caption styled as an archive tag."""
    bg, fg = (INK, PARCH) if not dark else (PARCH, INK)
    return A(f'<div style="background:{bg};color:{fg};border:2px solid {fg};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;'
             f'transform:rotate({rot}deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">{text}</div>', x, y, anim, "z-index:70")


def card(inner, w, x, y, anim, rot=-1.5, bg="#FBF8F0", extra=""):
    return A(f'<div style="width:{w}px;background:{bg};padding:30px 34px;box-shadow:0 20px 36px rgba(0,0,0,.35);transform:rotate({rot}deg)">{inner}</div>', x, y, anim, extra)


def kicker(t, c="#7A6A4A"):
    return f'<div style="font:500 17px Plex;letter-spacing:4px;color:{c}">{t}</div>'


def phone(inner, w=430, h=860, glow=True):
    return (f'<div style="width:{w}px;height:{h}px;border-radius:56px;background:#111;padding:18px;box-sizing:border-box;'
            f'box-shadow:0 30px 70px rgba(0,0,0,.6){",0 0 60px rgba(46,134,222,.35)" if glow else ""}">'
            f'<div style="width:100%;height:100%;border-radius:40px;overflow:hidden;background:#F4F6F8;position:relative">{inner}</div></div>')


def clip(label, h=250, hue="#9AA3AD", blur=True):
    """A drawn stand-in for a viral clip: blurred shapes, never a real frame, never a person."""
    blobs = "".join(f'<div style="position:absolute;left:{x}%;top:{y}%;width:{s}%;height:{s * 1.4:.0f}%;border-radius:40%;background:{c}"></div>'
                    for x, y, s, c in ((8, 30, 26, "#6B5B4B"), (40, 20, 30, "#8C7A60"), (70, 40, 24, "#5A6670"), (25, 60, 40, "#7D6E5C")))
    return (f'<div style="position:relative;height:{h}px;background:{hue};overflow:hidden">'
            f'<div style="position:absolute;inset:0;{"filter:blur(9px)" if blur else ""}">{blobs}</div>'
            f'<div style="position:absolute;left:12px;bottom:10px;background:rgba(0,0,0,.72);color:#fff;font:500 14px Plex;letter-spacing:2px;padding:4px 8px">{label}</div>'
            f'<div style="position:absolute;right:12px;top:10px;color:#fff;font:400 22px Anton">▶</div></div>')


def post(label, views, h=250, cap=""):
    return (f'<div style="background:#fff;margin:0 0 14px;border-bottom:1px solid #DDE2E7">'
            f'<div style="display:flex;align-items:center;gap:10px;padding:10px 12px"><div style="width:34px;height:34px;border-radius:50%;background:#C9D1D9"></div>'
            f'<div style="font:600 15px Plex;color:#333">@account_{abs(hash(label)) % 900 + 100}</div></div>'
            + (f'<div style="padding:0 12px 8px;font:500 15px Plex;color:#333">{cap}</div>' if cap else "")
            + clip(label, h) + f'<div style="padding:8px 12px;font:500 14px Plex;color:#667">♥ {views} · ↻ · 💬</div></div>').replace("💬", "…")


# ==== 1 HOOK =================================================================================================
feed = "".join(post(l, v) for l, v in (("CLIP: TRAFFIC JAM", "1.2M"), ("CLIP: CROWDED TRAIN", "2.8M"), ("CLIP: STREET STALL", "4.1M"), ("CLIP: TRAFFIC JAM (AGAIN)", "3.3M"), ("CLIP: TRAFFIC JAM (AGAIN, AGAIN)", "900K")))
put("01_feed", page(
    a(f'<div style="width:1920px;height:1080px;background:#0E1116"></div>', 0, 0)
    + A(phone(f'<div id="feedroll" data-anim="up 0 1" style="position:absolute;left:0;right:0;top:-40px">{feed}</div>'), 745, 110, "fade 0 .08")
    + "".join(A(f'<div style="background:{ACC};color:#fff;font:500 20px Plex;padding:10px 16px;border-radius:14px;box-shadow:0 10px 20px rgba(0,0,0,.4)">🔔 {t}</div>'.replace("🔔 ", "● "), x, y, f"pop {s} {s + .05}")
              for t, x, y, s in (("4,102 new reactions", 1240, 220, .2), ("Trending: India", 1260, 330, .35), ("You might like: more of this", 1220, 440, .5)))
    + A(f'<div style="font:700 52px/1.1 Caveat;color:#E8EDF2;width:560px;transform:rotate(-2deg)">"If the feed were your only window, you\'d think this was the whole country."</div>', 110, 380, "fade .6 .75")
    + tag("RECONSTRUCTION · CLIPS DRAWN IN THE STUDIO · NO REAL PEOPLE", 110, 840, -1, "fade .05 .1"),
    "#0E1116", "FEED, POSTS AND CLIPS DRAWN IN THE STUDIO AS STAND-INS · NO REAL VIDEO, ACCOUNT OR PERSON IS SHOWN", dark=True))
# video stage (2026-11-20): the feed really scrolls through all five stand-in clips over the first 60% of the timeline
(D / "html" / "01_feed.html").write_text((D / "html" / "01_feed.html").read_text().replace("</body>", "<script>document.addEventListener('DOMContentLoaded',()=>{const q=new URLSearchParams(location.search);const T=q.has('t')?parseFloat(q.get('t')):1;const e=document.getElementById('feedroll');if(e)e.style.top=(-40-Math.min(1,T/.6)*900)+'px'})</script>" + "</body>", 1))

put("02_receipt", page(
    a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
    + A('<img src="/assets/csoh_title.png" style="width:760px;display:block;box-shadow:0 24px 44px rgba(0,0,0,.6)">', 110, 150, "up 0 .14", "transform:rotate(-2deg)")
    + A('<img src="/assets/csoh_kf.png" style="width:1100px;display:block;box-shadow:0 24px 44px rgba(0,0,0,.6)">', 700, 520, "up .2 .34", "transform:rotate(1deg)")
    + A(f'<div style="width:72px;height:30px;background:{SIG};opacity:.55;mix-blend-mode:multiply"></div>', 1700, 582, "wipe .45 .52", "z-index:31;transform:rotate(1deg)")
    + f'<svg class="a" data-anim="draw .58 .7" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{wobble(1356, 683, 128, 36, 3)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + A(f'<div style="font:700 60px/1.05 Caveat;color:{SIG};transform:rotate(-3deg);width:560px">"I went looking for a number. Somebody had already counted."</div>', 120, 820, "fade .75 .88")
    + tag("RECEIPT · CSOH, 9 JAN 2025", 980, 200, 2, "snap .38 .38"),
    "#2A1D12", "SCREENSHOTS: CSOH, 'ANTI-INDIAN HATE ON X' (9 JAN 2025), CSOHATE.ORG, CAPTURED 17 NOV 2026 · FIGURES CHECKED AGAINST THE REPORT · CSOH IS A US-BASED NON-PROFIT RESEARCH GROUP; SOME IN INDIA CRITICISE ITS WORK AS PARTISAN", dark=True))

tiles = [("23 AUG 2023", "CHANDRAYAAN-3", "soft landing near the Moon's south pole", "ISRO"),
         ("OCT 2026", "25.47 BN", "UPI payments in one month", "NPCI, VIA PRESS"),
         ("2022 COUNT", "3,682", "wild tigers, about 75% of the world's", "NTCA / WII")]
put("03_otherfeed", page(
    a(f'<div style="width:1920px;height:1080px;background:#101317"></div>', 0, 0)
    + A(f'<div style="font:400 84px/1 Anton;color:#F3EFE6">MEANWHILE, OFF THE FEED</div>', 110, 120, "fade 0 .08")
    + "".join(A(f'<div style="width:520px;background:{PARCH};padding:26px 30px;transform:rotate({(-1) ** i * 1.5}deg);box-shadow:0 20px 40px rgba(0,0,0,.5)">{kicker(d)}'
                f'<div style="font:400 72px/1 Anton;color:{INK};margin-top:10px">{n}</div><div style="font:400 34px ISerif;color:#444">{s}</div>'
                f'<div style="font:500 14px Plex;color:#7A6A4A;margin-top:12px">SOURCE: {src}</div>'
                + (f'<img src="/assets/real2/tiger_pb.jpg" style="width:520px;height:170px;object-fit:cover;object-position:80% 35%;display:block;margin-top:14px;filter:saturate(.85)">'
                   f'<div style="font:500 11px Plex;color:#7A6A4A;margin-top:4px">PHOTO: BENGAL TIGER · IGNARTONOSBG / PIXABAY</div>' if i == 2 else "") + '</div>', 110 + i * 590, 400 + (i % 2) * 40, f"slam {.2 + i * .22:.2f} {.23 + i * .22:.2f}")
              for i, (d, n, s, src) in enumerate(tiles))
    + f'<svg class="a" data-anim="draw .78 .86" style="left:0;top:0;z-index:40" width="1920" height="1080"><path d="{wobble(1420, 478, 120, 46, 7)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + tag("NOT TRENDING", 1200, 250, 2, "snap .9 .9"),
    "#101317", "ISRO, CHANDRAYAAN-3 (23 AUG 2023) · NPCI MONTHLY UPI DATA, OCT 2026 (VIA PRESS; CHECK NPCI) · NTCA/WII 'STATUS OF TIGERS' 2022 (RANGE 3,167–3,925) · PHOTO: BENGAL TIGER, IGNARTONOSBG / PIXABAY (PIXABAY CONTENT LICENSE)", dark=True))

put("04_title", page(
    a(f'<div style="width:1920px;height:1080px;background:{BLK};background-image:radial-gradient(rgba(255,255,255,.04) 1px,transparent 1.5px);background-size:5px 5px"></div>', 0, 0)
    + A(f'<div style="font:400 250px/0.85 Anton;color:#F3EFE6;text-align:center;width:1920px">DISGUST<br><span style="display:inline-block;background:{SIG};color:#141414;padding:14px 30px 0;margin-top:24px">PAYS</span></div>', 0, 200, "slam .2 .23")
    + A(f'<div style="font:400 46px ISerif;color:#CFC6B4;text-align:center;width:1920px">why the internet keeps showing you the worst of India</div>', 0, 830, "fade .55 .75")
    + tag("WORKING TITLE", 1500, 140, 2, "snap .4 .4", dark=True),
    BLK, "PRINT FACTS", dark=True))

# ==== 2 CONTEXT: the colonial paper trail =================================================================
from creatorforge_worker.media import maps  # noqa: E402
W = maps._world()["countries"]
X = lambda lon: (lon + 15) * 16.7
Y = lambda lat: (62 - lat) * 16.7
path = lambda rings: "".join("M" + " L".join(f"{X(lo):.0f} {Y(la):.0f}" for lo, la in r) + "Z" for r in rings)
by = {c["n"]: c["r"] for c in W}
land = "".join(f'<path d="{path(c["r"])}" fill="#D9D0BE" stroke="#B9AE98" stroke-width="1"/>' for c in W)
from india_shape import rings as india_rings  # noqa: E402
india = india_rings(20)
put("05_map", page(
    a(f'<div style="width:1920px;height:1080px;background:#BCC6C4"></div>', 0, 0)
    + f'<svg class="a" style="left:0;top:0" width="1920" height="1080">{land}<path d="{path(by["United Kingdom"])}" fill="{INK}"/></svg>'
    + f'<svg class="a" data-anim="fade .55 .7" style="left:0;top:0" width="1920" height="1080">'
      f'<path d="{path(by["Pakistan"] + by["Bangladesh"] + by["Myanmar"])}" fill="{RED}" opacity=".45"/><path d="{path(india)}" fill="{RED}"/></svg>'
    + f'<svg class="a" data-anim="draw .1 .5" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="M{X(-0.13):.0f} {Y(51.5):.0f} Q {X(40):.0f} {Y(62):.0f} {X(88.36):.0f} {Y(22.57):.0f}" pathLength="1" fill="none" stroke="{RED}" stroke-width="5" stroke-dasharray="1"/></svg>'
    + A(f'<div style="background:{PARCH};padding:6px 12px;font:500 18px Plex;letter-spacing:3px;color:{INK}">LONDON</div>', X(-0.13) - 60, Y(51.5) + 20, "fade 0 .1")
    + A(f'<div style="background:{PARCH};padding:6px 12px;font:500 18px Plex;letter-spacing:3px;color:{INK}">CALCUTTA · CAPITAL OF BRITISH INDIA TO 1911</div>', X(88.36) - 520, Y(22.57) + 30, "fade .5 .6", "z-index:31")
    + A(f'<div style="width:560px;background:{PARCH};padding:20px 24px;box-shadow:0 14px 26px rgba(0,0,0,.3);transform:rotate(-1.5deg)">'
        f'<div style="font:400 40px/1.05 Anton;color:{INK}">TWO CENTURIES OF COMPANY AND CROWN RULE</div>'
        f'<div style="font:400 28px ISerif;color:#444;margin-top:6px">deep red: today\'s India · lighter: other lands then under British India</div></div>', 90, 760, "up .7 .82")
    + chapter(1, "THE PAPER TRAIL"),
    "#BCC6C4", "MAP: NATURAL EARTH; INDIA: OFFICIAL BOUNDARY, DATAMEET COMPOSITE (CC BY 4.0) · BRITISH INDIA EXTENT SIMPLIFIED (BURMA SEPARATED 1937; CEYLON WAS A SEPARATE COLONY) · DRAWN IN THE STUDIO"))

put("06_macaulay", page(
    a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
    + card(kicker("THOMAS BABINGTON MACAULAY · MINUTE ON INDIAN EDUCATION · 2 FEBRUARY 1835")
           + f'<div style="font:400 44px/1.4 ISerif;color:#2A2118;margin-top:20px">"…{hl("a single shelf of a good European library was worth the whole native literature of India and Arabia.")}"</div>'
           + f'<div style="font:400 36px/1.4 ISerif;color:#2A2118;margin-top:26px">"I have no knowledge of either Sanscrit or Arabic."</div>'
           + f'<div style="font:500 15px Plex;color:#7A6A4A;margin-top:22px">Text after the 1835 Minute (Columbia University, Pritchett edition). Page set in the studio.</div>', 1060, 140, 150, "up 0 .15", -1, "#F4ECD8")
    + f'<svg class="a" data-anim="draw .55 .68" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{wobble(490, 390, 345, 40, 6)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + A(f'<div style="background:#fff;padding:12px 12px 16px;box-shadow:12px 14px 0 rgba(0,0,0,.55);transform:rotate(2deg)"><img src="/assets/p_macaulay.jpg" style="width:420px;height:520px;object-fit:cover;object-position:50% 18%;display:block;filter:grayscale(1) contrast(1.1)"></div>', 1360, 250, "up .1 .25", "z-index:25")
    + A(f'<div style="background:{PARCH};padding:6px 12px;font:500 16px Plex;letter-spacing:2px;color:{INK};box-shadow:0 6px 10px rgba(0,0,0,.35);white-space:nowrap">T. B. MACAULAY · ENGRAVING, c. 1840 · PUBLIC DOMAIN</div>', 1300, 830, "fade .15 .25", "z-index:26")
    + tag("AUTHOR'S QUALIFICATIONS: SEE LINE 2", 160, 860, -2, "snap .75 .75")
    + chapter(1, "THE PAPER TRAIL"),
    "#2A1D12", "SOURCE: MACAULAY, MINUTE ON INDIAN EDUCATION (2 FEB 1835), COLUMBIA UNIVERSITY (F. PRITCHETT) · CONFIRMED; PUNCTUATION TO CHECK AGAINST 'SELECTIONS FROM EDUCATIONAL RECORDS' (1920) · PORTRAIT: ENGRAVING, c. 1840, WIKIMEDIA COMMONS (PUBLIC DOMAIN)", dark=True))

put("07_drain", page(
    a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
    + A(f'<div style="width:420px;height:600px;background:linear-gradient(160deg,#7A2A20,#4A1712);box-shadow:0 30px 50px rgba(0,0,0,.6);transform:rotate(-4deg);padding:60px 40px;box-sizing:border-box">'
        f'<div style="font:400 72px/0.95 Anton;color:#E8DCC2">MOTHER<br>INDIA</div><div style="font:500 20px Plex;letter-spacing:3px;color:#E8DCC2;margin-top:20px">KATHERINE MAYO · 1927</div>'
        f'<div style="font:500 13px Plex;color:#C9B9A0;margin-top:300px">COVER DRAWN IN THE STUDIO</div></div>', 150, 220, "up 0 .14")
    + card(kicker("M. K. GANDHI · YOUNG INDIA · SEPTEMBER 1927")
           + f'<div style="font:400 46px/1.35 ISerif;color:#2A2118;margin-top:18px">"…{hl("the report of a drain inspector")} sent out with the one purpose of opening and examining the drains of the country."</div>', 860, 960, 260, "up .3 .45")
    + A(f'<div style="font:700 56px/1.1 Caveat;color:{SIG};transform:rotate(-2deg);width:760px">"He named the genre ninety-eight years before the algorithm did."</div>', 1000, 760, "fade .7 .85")
    + A(f'<div style="background:#fff;padding:12px 12px 16px;box-shadow:12px 14px 0 rgba(0,0,0,.55);transform:rotate(3deg)"><img src="/assets/p_gandhi.jpg" style="width:270px;height:330px;object-fit:cover;object-position:50% 30%;display:block;filter:grayscale(1) contrast(1.1)">'
        f'<div style="font:500 13px Plex;letter-spacing:1px;color:{INK};margin-top:8px">M. K. GANDHI · 1931 · PUBLIC DOMAIN</div></div>', 600, 560, "up .3 .42", "z-index:24")
    + tag("BOOK REVIEW · ONE STAR, APPROX.", 1280, 140, -2, "snap .55 .55")
    + chapter(1, "THE PAPER TRAIL"),
    "#2A1D12", "QUOTE: GANDHI, 'DRAIN INSPECTOR'S REPORT', YOUNG INDIA (SEPT 1927; ISSUE DATE TO CHECK), VIA MKGANDHI.ORG · BOOK: MAYO, MOTHER INDIA (1927) · COVER IS A STUDIO DRAWING · PHOTO: GANDHI, 1931, WIKIMEDIA COMMONS (PUBLIC DOMAIN)", dark=True))

chalk = lambda t, s, x, y, an, c="#ECEADF": A(f'<div style="font:{s}px/1 Marker;color:{c};opacity:.92">{t}</div>', x, y, an)
put("08_worlds", page(
    a(f'<div style="width:1920px;height:1080px;background:{CH};background-image:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1.5px);background-size:6px 6px"></div>', 0, 0)
    + chalk("FIRST WORLD", 64, 140, 220, "fade .05 .12") + chalk("US + allies", 34, 150, 300, "fade .08 .14", "#BFC7C2")
    + chalk("SECOND WORLD", 64, 720, 220, "fade .15 .22") + chalk("Soviet bloc", 34, 730, 300, "fade .18 .24", "#BFC7C2")
    + chalk("THIRD WORLD", 64, 1320, 220, "fade .25 .32") + chalk("not aligned with either", 34, 1330, 300, "fade .28 .34", "#BFC7C2")
    + A(f'<div style="font:500 22px Plex;letter-spacing:4px;color:{SIG}">ALFRED SAUVY · L\'OBSERVATEUR · 14 AUG 1952</div>', 1330, 360, "fade .3 .36")
    + f'<svg class="a" data-anim="draw .45 .6" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="M1600 420 Q 1560 560 1460 640" pathLength="1" fill="none" stroke="{SIG}" stroke-width="6"/></svg>'
    + chalk('later, in Western usage: "poor"', 50, 820, 640, "fade .6 .7", SIG)
    + tag("DEFINITION UPDATED WITHOUT NOTICE", 820, 820, -2, "snap .9 .9"),
    CH, "TERM: ALFRED SAUVY, 'TROIS MONDES, UNE PLANÈTE', L'OBSERVATEUR, 14 AUG 1952 (VIA BRITANNICA) · CHALKBOARD DRAWN IN THE STUDIO", dark=True))

# ==== the 2016 data drop (TRAI) ==========================================================================
COST = [('2014', 268.97), ('2015', 226.8), ('2016', 75.57), ('2017', 19.35), ('2018', 11.78), ('2019', 11.17), ('2020', 10.9)]
bars_ = "".join(A(f'<div style="width:96px;height:{v / 268.97 * 480:.0f}px;background:{SIG if y == "2020" else ("#3A3F4B" if y != "2016" else RED)}"></div>', 760 + i * 150, 880 - v / 268.97 * 480, f"grow {.15 + i * .07:.2f} {.24 + i * .07:.2f}")
                + A(f'<div style="font:400 40px Anton;color:{INK};width:96px;text-align:center">₹{v:.0f}</div>', 760 + i * 150, 880 - v / 268.97 * 480 - 52, f"fade {.22 + i * .07:.2f} {.26 + i * .07:.2f}")
                + a(f'<div style="font:500 20px Plex;color:#555;width:96px;text-align:center">{y}</div>', 760 + i * 150, 892) for i, (y, v) in enumerate(COST))
put("08b_data", page(
    chapter(2, "WHAT THE FEED PAYS FOR")
    + A(f'<div style="font:400 84px/0.95 Anton;color:{INK};width:620px">DATA GOT CHEAP.<br>{hl("INDIA CAME ONLINE.")}</div>', 110, 150, "up 0 .1")
    + A(f'<div style="font:500 22px Plex;letter-spacing:3px;color:#555;width:600px">WHAT A GB OF MOBILE DATA COST, ON AVERAGE (₹)</div>', 112, 390, "fade .08 .14")
    + bars_ + a(f'<div style="width:1060px;height:4px;background:{INK}"></div>', 740, 880)
    + A(f'<div style="background:{PARCH};padding:8px 14px;font:700 34px Caveat;color:{RED};transform:rotate(-3deg);box-shadow:0 8px 14px rgba(0,0,0,.2);white-space:nowrap">2016: a new 4G network, Jio, launches with free data</div>', 980, 300, "drop .3 .38", "z-index:31")
    + card(f'<div style="font:500 17px Plex;letter-spacing:3px;color:#7A6A4A">INTERNET SUBSCRIBERS, 2014 → 2020</div><div style="font:400 84px/1 Anton;color:{INK};margin-top:8px">239M → <span data-anim="count .62 .85" data-to="776">776</span>M</div>', 560, 110, 500, "up .6 .7", -1.5)
    + tag("SLIDE TITLE (REAL): \"EXTRAORDINARY ACHIEVEMENTS OF INDIA\"", 940, 215, -1.5, "snap .9 .9"),
    PARCH, "SOURCE: TRAI, PRESENTATION ON THE TELECOM SECTOR (31 MAY 2021), 'DATA COST TO SUBSCRIBER PER GB' AND INTERNET SUBSCRIBERS, TRAI.GOV.IN · CONFIRMED · JIO LAUNCH, SEPT 2016: WELL-ESTABLISHED · BARS START AT ZERO"))

# ==== 3 MECHANICS ==========================================================================================
put("09_dial", page(
    a(f'<div style="width:1920px;height:1080px;background:#0E1116;background-image:linear-gradient(rgba(46,134,222,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(46,134,222,.08) 1px,transparent 1px);background-size:48px 48px"></div>', 0, 0)
    + chapter(2, "WHAT THE FEED PAYS FOR")
    + f'<svg class="a" style="left:0;top:0" width="1920" height="1080"><path d="M300 760 A 360 360 0 0 1 1020 760" fill="none" stroke="#2A3340" stroke-width="60"/>'
      f'<path d="M300 760 A 360 360 0 0 1 1020 760" fill="none" stroke="{ACC}" stroke-width="6" stroke-dasharray="4 16"/>'
      f'<text x="330" y="520" font-family="Plex" font-size="24" fill="#AFC3D6" letter-spacing="3">JOY</text><text x="600" y="380" font-family="Plex" font-size="24" fill="#AFC3D6" letter-spacing="3">SADNESS</text>'
      f'<text x="880" y="520" font-family="Plex" font-size="24" fill="{SIG}" letter-spacing="3">OUTRAGE</text></svg>'
    + A(f'<div style="width:330px;height:12px;background:{RED};border-radius:6px;transform-origin:0 50%;transform:rotate(-20deg)"></div>', 660, 754, "fade 0 .05")
    + A(f'<div style="width:40px;height:40px;border-radius:50%;background:#E8EDF2;margin:-14px 0 0 -20px"></div>', 660, 760, "fade 0 .05")
    + A(f'<div style="font:400 40px Anton;color:#E8EDF2;text-align:center;width:720px">EMOTIONAL RESPONSE</div>', 300, 820, "fade 0 .1")
    + card(kicker("RATHJE, VAN BAVEL &amp; VAN DER LINDEN · PNAS · JUNE 2021")
           + f'<div style="font:400 34px/1.3 ISerif;color:{INK};margin-top:12px">2.73 million posts studied. Every word about the "other side" raised the odds of a share by about</div>'
           + f'<div style="font:400 150px/1 Anton;color:{INK};margin-top:6px">{hl("67%")}</div>', 640, 1160, 220, "up .35 .5", 1.5)
    + tag("NEEDLE: NOT DESIGNED TO STOP", 1180, 860, -2, "snap .8 .8", True),
    "#0E1116", "SOURCE: RATHJE ET AL., 'OUT-GROUP ANIMOSITY DRIVES ENGAGEMENT ON SOCIAL MEDIA', PNAS 118 (2021), US POLITICS DATA · DIAL IS AN ILLUSTRATION", dark=True))

coin = lambda n, x, c, lab, an: A(
    "".join(f'<div style="width:150px;height:30px;border-radius:50%;background:{c};border:3px solid #1A1A1A;margin-top:-14px"></div>' for _ in range(n))
    + f'<div style="font:400 44px Anton;color:{INK};text-align:center;width:150px;margin-top:16px;white-space:nowrap">{lab}</div>', x, 780 - n * 16, an)
put("10_angry", page(
    chapter(2, "WHAT THE FEED PAYS FOR")
    + A(f'<div style="font:400 84px/0.95 Anton;color:{INK}">HOW MUCH IS ONE<br>ANGRY FACE WORTH?</div>', 110, 160, "up 0 .1")
    + coin(1, 900, "#C9D1D9", "LIKE = 1", "pop .2 .28") + coin(5, 1200, SIG, "ANGRY = 5", "pop .4 .5")
    + A(f'<div style="font:400 120px Anton;color:{RED}">×5</div>', 1420, 520, "slam .55 .57")
    + A(f'<div style="font:500 22px/1.5 Plex;color:#444;width:640px">Facebook\'s feed weighted every emoji reaction, "angry" included, at five times a like from 2017. The angry weight was cut, and reached zero by the end of 2020.</div>', 110, 520, "fade .65 .8")
    + tag("RECEIPT · THE FACEBOOK PAPERS", 110, 820, -2, "snap .85 .85"),
    PARCH, "SOURCE: WASHINGTON POST, 'FIVE POINTS FOR ANGER, ONE FOR A LIKE' (26 OCT 2021), FROM INTERNAL DOCUMENTS · REPORTED · COUNTER-VIEW: CATO NOTES 'ANGRY' WAS THE LEAST-USED REACTION · COINS DRAWN IN THE STUDIO"))

slot = lambda n: "".join(f'<span style="display:inline-block;background:#111;color:{SIG};font:400 50px/1 Anton;padding:6px 8px;margin:0 2px">{d}</span>' for d in n).join(('<div style="white-space:nowrap">', '</div>'))
put("11_repost", page(
    a(f'<div style="width:1920px;height:1080px;background:#0E1116"></div>', 0, 0) + chapter(2, "WHAT THE FEED PAYS FOR")
    + A(phone(post("CLIP: A MARKET STREET", "212", 330), 420, 640, False), 220, 200, "up 0 .12")
    + A(f'<div style="font:500 20px Plex;letter-spacing:3px;color:#AFC3D6;text-align:center;width:420px">THE ORIGINAL · AN ORDINARY VLOG</div>', 220, 860, "fade .05 .15")
    + f'<svg class="a" data-anim="draw .2 .35" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="M680 520 Q 820 420 960 520" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/><path d="M940 500 L962 522 L934 532" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + A(phone(post("CLIP: SAME MARKET STREET", "4.1M", 330, '<span style="background:#222;color:#222">[CAPTION MOCKING INDIANS]</span> 🤢'.replace(" 🤢", "")), 420, 640), 1000, 200, "up .3 .42")
    + A(f'<div style="font:500 20px Plex;letter-spacing:3px;color:#AFC3D6;text-align:center;width:420px">THE REPOST · CAPTION BLACKED OUT</div>', 1000, 860, "fade .35 .45")
    + A(slot("4,100,000"), 1450, 420, "slam .6 .62")
    + A(f'<div style="font:500 20px/1.5 Plex;color:#E8EDF2;width:420px">Since Oct 2024, X pays creators by engagement from Premium users.</div>', 1450, 540, "fade .7 .8")
    + tag("ILLUSTRATIVE · DRAWN", 1450, 700, 2, "snap .3 .3"),
    "#0E1116", "PAYOUT RULE: TECHCRUNCH, 9 OCT 2024 · CONFIRMED · POSTS, VIEW COUNTS AND CAPTION ARE ILLUSTRATIVE STAND-INS, NOT A REAL CASE", dark=True))

shares = [("45%", 45, "call South Asians \"invaders\", \"job thieves\" or a demographic threat", "OF POSTS"), ("~30%", 30, "use a single slur, one CNN traces back to 4chan", "OF POSTS"),
          ("+171%", 0, "rise in hygiene-based insults: the fastest-growing kind", "GROWTH")]
rows_ = ""
for i, (n, v, t, unit) in enumerate(shares):
    y, s0 = 470 + i * 160, .3 + i * .17
    rows_ += A(f'<div style="font:400 96px/1 Anton;color:{RED};width:300px">{n}</div>', 112, y, f"up {s0:.2f} {s0 + .06:.2f}")
    rows_ += A(f'<div style="font:400 36px/1.2 ISerif;color:{INK};width:1300px">{t}</div>', 440, y + 4, f"fade {s0:.2f} {s0 + .08:.2f}")
    if v:   # share of all posts: a 0-100% track, the share wiping in
        rows_ += a(f'<div style="width:1000px;height:26px;background:#E2DACB"></div>', 440, y + 62)
        rows_ += A(f'<div style="width:{v * 10}px;height:26px;background:{RED if i == 0 else INK}"></div>', 440, y + 62, f"wipe {s0 + .04:.2f} {s0 + .14:.2f}")
        rows_ += a(f'<div style="font:500 16px Plex;color:#7A6A4A">100%</div>', 1452, y + 64)
    else:   # growth: before (1x) and after (2.71x) bars
        rows_ += A(f'<div style="width:300px;height:26px;background:#9A9284"></div>', 440, y + 62, f"wipe {s0 + .02:.2f} {s0 + .06:.2f}")
        rows_ += A(f'<div style="width:813px;height:26px;background:{SIG}"></div>', 440, y + 96, f"wipe {s0 + .06:.2f} {s0 + .16:.2f}")
        rows_ += a(f'<div style="font:500 16px Plex;color:#7A6A4A;white-space:nowrap">BEFORE · AFTER (×2.71)</div>', 1270, y + 98)
put("12_count", page(
    chapter(3, "THE COUNT")
    + A(f'<div style="font:400 84px/0.95 Anton;color:{INK}">~<span data-anim="count .02 .26" data-to="542360">542,360</span> POSTS<br>{hl("IN 18 MONTHS")}</div>', 110, 150, "up 0 .1")
    + A(f'<div style="font:500 22px Plex;letter-spacing:3px;color:#555">ANTI-SOUTH ASIAN HATE ON X · JAN 2025 – JUN 2026</div>', 112, 360, "fade .08 .15")
    + rows_
    + f'<svg class="a" data-anim="draw .84 .92" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{wobble(262, 528, 150, 58, 11)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + tag("THE INTERNET, KEEPING RECEIPTS ON ITSELF", 1180, 160, 2, "snap .88 .88"),
    PARCH, "SOURCE: CSOH, 'THE RISING TIDE OF ANTI-SOUTH ASIAN HATE IN THE UNITED STATES' (28 SEP 2026), CSOHATE.ORG · CHECKED AGAINST THE REPORT 17 NOV 2026 · AN NGO REPORT, NOT PEER-REVIEWED · SHARES MAY OVERLAP; BARS START AT ZERO"))

ev = [("DEC 2024", "H-1B fight on X", .1), ("JUL 2025", "Tallaght, Dublin: assault recorded as racially motivated", .3), ("AUG 2025", "Australia: rally flyers single out Indian migration", .5),
      ("2025", "Canada: police-reported hate crimes vs South Asians 324 → 483", .7)]
MX = lambda lo: 110 + (lo + 130) / 290 * 1700
MY = lambda la: 250 + (70 - la) / 120 * 703
pins13 = [(-77.04, 38.9, "DEC 2024", "H-1B fight on X", .18, (-280, 70)), (-6.37, 53.29, "JUL 2025", "Tallaght, Dublin: assault recorded as racially motivated", .34, (40, 20)),
          (151.2, -33.87, "AUG 2025", "Australia: rally flyers single out Indian migration", .5, (-430, -190)), (-75.7, 45.42, "2025", "Canada: police-reported hate crimes vs South Asians 324 → 483", .66, (-290, -150))]
ring13 = "".join("M" + " L".join(f"{MX(lo):.0f} {MY(la):.0f}" for lo, la in r) + "Z" for r in india_rings(20))
string13 = "M" + " Q ".join(f"{MX(lo):.0f} {MY(la):.0f}" if i == 0 else f"{(MX(pins13[i - 1][0]) + MX(lo)) / 2:.0f} {(MY(pins13[i - 1][1]) + MY(la)) / 2 + 60:.0f} {MX(lo):.0f} {MY(la):.0f}" for i, (lo, la, *_ ) in enumerate(pins13))
put("13_timing", page(
    a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0) + chapter(4, "WHERE IT LANDS")
    + A(f'<div style="background:#fff;padding:12px;box-shadow:16px 20px 0 rgba(0,0,0,.45);transform:rotate(-.6deg)"><div style="width:1700px;height:703px;overflow:hidden;position:relative">'
        f'<img data-anim="push 0 1" data-z=".04" src="/maps/bluemarble_world.jpg" style="position:absolute;left:-293px;top:-117px;width:2110px;height:1055px;filter:saturate(.7) sepia(.25) brightness(.95)"></div></div>', 98, 238, "up 0 .1")
    + f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{ring13}" fill="{SIG}" fill-opacity=".35" stroke="{SIG}" stroke-width="2"/>'
      f'<g data-anim="draw .2 .8"><path d="{string13}" pathLength="1" fill="none" stroke="{RED}" stroke-width="4"/></g></svg>'
    + A(f'<div style="background:{INK};color:{PARCH};padding:3px 8px;font:500 14px Plex;letter-spacing:2px">INDIA</div>', MX(79) - 30, MY(18), "fade .05 .12", "z-index:31")
    + "".join(A(f'<div style="width:24px;height:24px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#fff 0 12%,{RED} 30%,#7A1810 100%);box-shadow:3px 5px 4px rgba(0,0,0,.5)"></div>', MX(lo) - 12, MY(la) - 12, f"drop {s0:.2f} {s0 + .05:.2f}", "z-index:40")
              + A(f'<div style="width:330px;background:{PARCH};padding:10px 14px;box-shadow:8px 10px 0 rgba(0,0,0,.4);transform:rotate({(-1) ** k * 1.5}deg)"><div style="font:400 36px Anton;color:{INK}">{d}</div>'
                  f'<div style="font:400 24px/1.15 ISerif;color:#333">{t}</div></div>', MX(lo) + ox, MY(la) + oy, f"up {s0 + .03:.2f} {s0 + .1:.2f}", "z-index:41")
              for k, (lo, la, d, t, s0, (ox, oy)) in enumerate(pins13))
    + A(f'<div style="font:400 72px/0.95 Anton;color:#F3EFE6;text-shadow:0 4px 16px #000">SAME MONTHS, <span style="display:inline-block;margin-top:14px;background:{SIG};color:{INK};padding:4px 12px 0;text-shadow:none">SAME HEADLINES</span></div>', 520, 110, "up 0 .1", "z-index:50")
    + tag("POLICY ARGUMENT", 150, 650, -1.5, "snap .3 .3", True) + tag("ETHNIC SLURS", 420, 655, 1.5, "snap .32 .32").replace(f"background:{INK}", f"background:{RED}")  # script 4 · 5:46: the visa fight is kept apart from the hostility
    + tag("TIMING, NOT CAUSE · NO STUDY LINKS A POST TO AN ATTACK", 980, 990, 1.5, "snap .9 .9"),
    "#2A1D12", "MAP: NASA BLUE MARBLE NEXT GENERATION (PUBLIC DOMAIN) · INDIA: OFFICIAL BOUNDARY, DATAMEET (CC BY 4.0) · PINS APPROXIMATE · SOURCES: CNBC 27 DEC 2024 · IRISH TIMES 26 JUL 2025 (GARDAÍ) · AL JAZEERA 1 SEP 2025 · STATISTICS CANADA TABLE 6 (22 JUL 2026; 2024 REVISED TO 324) · CONFIRMED", dark=True))

put("14_classifier", page(
    a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0) + chapter(4, "WHERE IT LANDS")
    + card(kicker("THE FACEBOOK PAPERS · TEST ACCOUNT, KERALA · FROM 4 FEB 2019")
           + f'<div style="font:400 40px/1.35 ISerif;color:#2A2118;margin-top:16px">Three weeks of following recommendations filled the feed with hate. Much of it was "{hl("never flagged or actioned")}": there were no classifiers for Hindi or Bengali.</div>'
           + f'<div style="font:500 16px Plex;color:#7A6A4A;margin-top:18px">Facebook says Hindi classifiers came in 2018 and Bengali in 2020. Content was domestic hate, not foreign mockery.</div>', 860, 120, 210, "up 0 .15", -1.5, "#F4ECD8")
    + card(kicker("CSOH · JAN 2025") + f'<div style="font:400 120px/1 Anton;color:{INK}">125 <span style="font-size:60px">OF</span> 128</div><div style="font:400 34px ISerif;color:#444">of the anti-Indian posts it logged were still live on 3 Jan 2025</div>', 700, 1100, 520, "up .4 .55", 2)
    + tag("MODERATION STATUS: PENDING SINCE 2019", 160, 860, -2, "snap .75 .75"),
    "#2A1D12", "SOURCES: AL JAZEERA (25 OCT 2021) AND AP ON THE HAUGEN DOCUMENTS · REPORTED; FACEBOOK'S RESPONSE QUOTED · CSOH (9 JAN 2025) · CHECKED AGAINST THE REPORT", dark=True))

# ==== the other side ========================================================================================
side = [("19%", "of households had no toilet facility", "NFHS-5, 2019–21"), ("6th of 143", "most polluted country by PM2.5", "IQAir 2025"),
        ("19.8%", "of food samples failed a standard (not all unsafe)", "FSSAI, 2023-24"), ("69%", "of Indians met a tech-support scam in a year: the world's highest", "Microsoft, 2021")]
put("15_drains", page(
    chapter(5, "CONCEDE THE DRAINS")
    + A(f'<div style="font:400 84px/0.95 Anton;color:{INK}">THE PROBLEMS<br>{hl("ARE REAL")}</div>', 110, 150, "up 0 .1")
    + A(f'<div style="font:400 36px/1.3 ISerif;color:#444;width:600px">India\'s own surveys and regulators keep these numbers.</div>', 112, 400, "fade .1 .2")
    + "".join(A(f'<div style="width:500px;background:#FBF8F0;padding:22px 26px;box-shadow:0 14px 26px rgba(0,0,0,.18);transform:rotate({(-1) ** i * 1.2}deg)">'
                f'<div style="font:400 70px/1 Anton;color:{INK}">{n}</div><div style="font:400 30px/1.2 ISerif;color:#333">{t}</div><div style="font:500 15px Plex;color:#7A6A4A;margin-top:8px">{s}</div></div>',
                740 + (i % 2) * 570, 170 + (i // 2) * 360, f"up {.2 + i * .15:.2f} {.3 + i * .15:.2f}") for i, (n, t, s) in enumerate(side))
    + f'<svg class="a" data-anim="draw .3 .4" style="left:0;top:0;z-index:40" width="1920" height="1080"><path d="{wobble(818, 216, 92, 36, 12)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + a(f'<div style="width:130px;height:36px;background:rgba(236,226,200,.85);transform:rotate(-6deg);box-shadow:0 2px 4px rgba(0,0,0,.25)"></div>', 1380, 150, "z-index:41")
    + A(f'<div style="font:700 50px/1.1 Caveat;color:#7A2A20;transform:rotate(-2deg);width:600px">"The drains exist. The feed just never shows anything else."</div>', 110, 700, "fade .85 .95"),
    PARCH, "SOURCES: NFHS-5 VIA DECCAN HERALD (MAY 2022) · IQAIR WORLD AIR QUALITY REPORT 2025 VIA THE WIRE (REPORTED) · FSSAI, LOK SABHA REPLY (OTHER REPLIES DIFFER) · MICROSOFT GLOBAL TECH SUPPORT SCAM RESEARCH 2021"))

stamps = [("AI-GENERATED", "Correctiv, 13 May 2026"), ("SCRIPTED", "BOOM, 2022 clip"), ("NOT FROM INDIA", "BOOM")]
put("16_fakes", page(
    a(f'<div style="width:1920px;height:1080px;background:#0E1116"></div>', 0, 0) + chapter(5, "CONCEDE THE DRAINS")
    + A(f'<div style="font:400 72px/1 Anton;color:#F3EFE6">AND SOME OF THE "PROOF" ISN\'T</div>', 110, 140, "fade 0 .1")
    + "".join(A(f'<div style="width:500px;position:relative">{clip("VIRAL “DIRTY FOOD” CLIP", 300, "#7C8590")}'
                f'<div style="position:absolute;left:40px;top:90px;border:7px solid {RED};color:{RED};font:400 54px/1 Anton;padding:6px 18px;transform:rotate(-9deg);background:rgba(244,239,230,.85)">{s}</div>'
                f'<div style="font:500 17px Plex;letter-spacing:2px;color:#AFC3D6;margin-top:12px">FACT-CHECK: {src}</div></div>', 110 + i * 590, 330, f"pop {.2 + i * .2:.2f} {.27 + i * .2:.2f}")
              for i, (s, src) in enumerate(stamps))
    + tag("CLIPS DRAWN AS STAND-INS · ORIGINALS NOT REPUBLISHED", 110, 860, -1.5, "fade .05 .1"),
    "#0E1116", "FACT-CHECKS: CORRECTIV (13 MAY 2026); BOOM LIVE (PANI PURI CLIP SCRIPTED; 'POTHOLE WATER' VIDEO NOT FROM INDIA); THE QUINT · CONFIRMED · NO SHARE OF FAKES IS CLAIMED", dark=True))

# ==== 5 SYNTHESIS =========================================================================================
put("17_sowhat", page(
    a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0) + chapter(6, "FIXING THE FEED")
    + A(f'<div style="width:620px;background:#F4ECD8;padding:30px 34px;box-shadow:0 20px 36px rgba(0,0,0,.45);transform:rotate(-2deg)">'
        f'<div style="font:700 54px/1.15 Caveat;color:{RED}">"The drains exist. The feed just never shows anything else."</div></div>', 160, 300, "fade 0 .05", "z-index:20")
    + A(f'<div style="font:400 120px/1.12 Anton;color:#F3EFE6">HERE\'S WHAT<div style="margin-top:26px">IT <span style="background:{SIG};color:{INK};padding:0 14px;display:inline-block;line-height:1">LEAVES OUT</span></div></div>', 980, 330, "up .45 .6", "z-index:30")
    + tag("OUTSIDE THE FRAME", 984, 740, 2, "snap .75 .75", True),
    "#2A1D12", "BRIDGE TO THE SYNTHESIS · NOTE AND DESK DRAWN IN THE STUDIO", dark=True))

put("18_softpower", page(
    chapter(6, "FIXING THE FEED")
    + card(kicker("ACADEMY AWARDS · 12 MARCH 2023") + f'<div style="font:400 92px/1 Anton;color:{INK};margin-top:10px">"NAATU NAATU"</div>'
           + f'<div style="font:400 36px ISerif;color:#444">from RRR · Best Original Song</div>', 720, 130, 260, "up .05 .18", -2)
    + card(kicker("NPCI · OCTOBER 2026") + f'<div style="font:400 120px/1 Anton;color:{INK};margin-top:10px">{hl("25.47 BN")}</div>'
           + f'<div style="font:400 36px ISerif;color:#444">UPI payments in a single month</div>', 720, 1000, 300, "up .35 .48", 1.5)
    + tag("SOFT POWER · NO CLIPS REQUIRED", 760, 840, -1.5, "snap .8 .8"),
    PARCH, "SOURCES: OSCARS.ORG (95TH ACADEMY AWARDS) · CONFIRMED · NPCI UPI PRODUCT STATISTICS, OCT 2026 VIA FREE PRESS JOURNAL · REPORTED; CHECK NPCI · NO FILM FOOTAGE OR POSTER USED"))

menu = "".join(f'<div style="padding:16px 22px;font:500 22px Plex;color:#222;border-bottom:1px solid #E3E6EA{";background:#EAF2FB" if i == 0 else ""}">{t}</div>'
               for i, t in enumerate(("Not interested in this post", "Follow @account", "Mute", "Report post")))
put("19_notinterested", page(
    a(f'<div style="width:1920px;height:1080px;background:#0E1116"></div>', 0, 0) + chapter(6, "FIXING THE FEED")
    + A(phone(post("CLIP: HATE-BAIT", "2.2M", 330, '<span style="background:#222;color:#222">[CAPTION MOCKING INDIANS]</span>') +
              f'<div data-anim="pop .3 .38" style="position:absolute;right:20px;top:60px;width:330px;background:#fff;border-radius:14px;box-shadow:0 12px 30px rgba(0,0,0,.35);overflow:hidden">{menu}</div>', 440, 820), 300, 150, "fade 0 .08")
    + A(f'<svg width="54" height="64" viewBox="0 0 27 32"><path d="M2 2 L2 26 L8 20 L13 30 L17 28 L12 18 L21 18 Z" fill="#fff" stroke="#111" stroke-width="2"/></svg>', 530, 260, "up .5 .6", "z-index:60")
    + A(f'<div style="font:700 64px/1.1 Caveat;color:{SIG};width:720px;transform:rotate(-2deg)">"The algorithm only serves what you keep eating."</div>', 1000, 360, "fade .7 .85")
    + tag("SOUND: ONE HEAVY THUNK", 1000, 700, 1.5, "snap .62 .62", True),
    "#0E1116", "MENU AND POST DRAWN IN THE STUDIO, MODELLED ON A GENERIC SOCIAL APP · NOT A SCREEN RECORDING", dark=True))

EX = lambda lo: 1380 + (lo - 68) * 13.5
EY = lambda la: 470 + (37.5 - la) * 13.5
ring20 = "".join("M" + " L".join(f"{EX(lo) - 1340:.0f} {EY(la) - 430:.0f}" for lo, la in r) + "Z" for r in india_rings(20))
put("20_end", page(
    a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
    + A(f'<div style="background:#EFE7D2;padding:0;box-shadow:14px 18px 0 rgba(0,0,0,.45);transform:rotate(2deg);width:500px;height:520px">'
        f'<svg width="500" height="520"><path d="{ring20}" fill="{RED}" fill-opacity=".85" stroke="{INK}" stroke-width="1.5"/></svg>'
        f'<div style="position:absolute;left:14px;bottom:10px;font:500 12px Plex;letter-spacing:2px;color:#7A6A4A">INDIA · OFFICIAL BOUNDARY</div></div>', 1340, 430, "up .25 .4", "z-index:15")
    + a(f'<div style="width:140px;height:38px;background:rgba(236,226,200,.82);transform:rotate(-8deg)"></div>', 1520, 420, "z-index:16")
    + card(f'<div style="font:400 58px/1.3 ISerif;color:#2A2118">India isn\'t a caricature. It\'s a country of about 1.4 billion people that the feed keeps editing down to one drain.</div>', 1100, 110, 110, "up 0 .2", -1, "#F4ECD8", "z-index:20")
    + A(f'<div style="font:700 60px/1.1 Caveat;color:{SIG};transform:rotate(-2deg)">"Gandhi already reviewed it. In 1927. One star."</div>', 140, 720, "fade .5 .7", "z-index:30")
    + f'<svg class="a" data-anim="draw .6 .78" style="left:0;top:0;z-index:31" width="1920" height="1080"><path d="M{EX(77.2):.0f} {EY(28.6):.0f} Q 1100 760 980 800" pathLength="1" fill="none" stroke="{RED}" stroke-width="4"/></svg>'
    + A(f'<div style="width:24px;height:24px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#fff 0 12%,{RED} 30%,#7A1810 100%);box-shadow:3px 5px 4px rgba(0,0,0,.5)"></div>', EX(77.2) - 12, EY(28.6) - 12, "drop .55 .6", "z-index:32")
    + tag("CALLBACK · SEE: DRAIN INSPECTOR, 1927", 200, 880, -2, "snap .85 .85"),
    "#2A1D12", "POPULATION: UN WORLD POPULATION PROSPECTS (ABOUT 1.4 BILLION; CHECK LATEST) · INDIA: OFFICIAL BOUNDARY, DATAMEET (CC BY 4.0) · PRINT FACTS · SOURCES IN THE DESCRIPTION", dark=True))
print("ok")
