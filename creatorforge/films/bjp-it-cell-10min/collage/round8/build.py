"""The Machine: five stills in the owner's round-8 vocabulary, on the v2 collage kit (motion rules from LottieFiles).
Real material only (source-page scraps, GODL-India cut-outs, public-domain party symbols, Simple Icons logos);
platform cards are labelled recreations with blanked hashtags, never invented posts."""
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/Forgeos/creatorforge/channels/design_kits/collage")
import collage2 as K
from collage2 import el, STILL, INK, RED, SIG, CREAM, KHAKI

D = Path(__file__).resolve().parent
C = D.parent
DOCS = C.parent / "docs"
A = C / "assets"
sys.path.insert(0, str(C))
from build_stills import icon   # Simple Icons (CC0) paths


def scrap_img(name, pos="top", filt="grayscale(1) contrast(1.2)"):
    return f'<img src="{(DOCS / (name + ".png")).as_uri()}" style="width:100%;height:100%;object-fit:cover;object-position:{pos};filter:{filt}">'


S = {}

# R1. Rewind: a clothesline of polaroids, 2026 back to 2007, in window light
items = [(scrap_img("print_malviya", "left top"), "17 AUG 2026<br>Mhaskey named head"),
         (scrap_img("print_swamy", "left top"), "7 SEPT 2020<br>'gone rogue': Swamy"),
         (scrap_img("quint_kota", "left top"), "22 SEPT 2018<br>Kota: 'true or false'"),
         (f'<div style="font:900 120px Playfair;color:{SIG}">2015</div>', "2015<br>Malviya made head"),
         (f'<img src="{(A / "bjp_symbol.png").as_uri()}" style="width:70%;filter:grayscale(1) contrast(1.2)">', "2007<br>IT cell set up")]
body = K.clothesline(items, y=250, sag=110, at0=.3, step=.4, w=300, x0=70, gap=360)
body += el(f'<div style="font:600 30px Bebas;letter-spacing:14px;color:#6b5a45">— &nbsp;REWIND · 19 YEARS&nbsp; —</div>', 700, 70, 0, "wipe", z=6)
body += el(f'<div style="font:italic 900 96px Playfair;color:{INK}">The Machine</div>', 690, 860, 2.2, "slide", z=6)
body += K.micro(1500, 900, ["Every date on this line is from", "a published report; read the", "film's dossier for the sources."], 12, 300, 2.6)
body += K.gobo(.26) + K.flare(1500, 300, 300, 1.8)
S["r1_clothesline"] = (K.studio_paper(), body, "SOURCE PAGES: THEPRINT 2026 & 2020, THE QUINT 2018 (CROPPED SCREENSHOTS) · BJP SYMBOL: PUBLIC DOMAIN FILE, WIKIMEDIA COMMONS")

# R2. Editorial grid poster: giant condensed type behind the cut-out
body = K.index_no("00002", 90, 60) + K.micro(90, 140, ["Kota, Rajasthan · 22.09.2018", "BJP social media volunteers' meeting", "Speaker: Amit Shah, then party president", "Reported by The Quint, 27.09.2018"], 13, 420)
body += el(f'<div style="font:400 360px/0.86 Anton;color:{INK};letter-spacing:-6px">TRUE OR<br><span style="color:{RED}">FALSE</span></div>', 80, 230, .2, "slide", z=3)
body += el(f'<img src="{(A / "shah_cut.png").as_uri()}" style="height:900px">', 1060, 170, .7, "drop", z=6)
body += el(f'<div style="font:600 22px Mono;background:{INK};color:#fff;padding:8px 14px">"WE CAN SPREAD ANY MESSAGE WE WANT, WHETHER IT IS TRUE OR FALSE"</div>', 90, 980, 1.4, "wipe", z=7)
body += el('<div style="font:600 18px Mono;color:#fff;background:#2F6DB5;padding:6px 12px;letter-spacing:3px">REPORTED · THE QUINT</div>', 90, 930, 1.2, "pop", z=7)
body += K.micro(1530, 60, ["Context: reports differ on whether", "he added a caveat that day. Months", "earlier, in Delhi, he reportedly told", "volunteers not to post fake news."], 12, 340, 1.8)
body += K.barcode(1580, 1000, 220, 30, 3, 0)
body += "".join(f'<div class="el" style="left:{x}px;top:{y}px;font:300 34px Inter;color:#777;z-index:4">+</div>' for x, y in ((40, 30), (1860, 30), (40, 1020), (1860, 1020)))
body += K.gobo(.22)
S["r2_poster"] = (K.grid_paper(), body, "PHOTO: GOVT. OF INDIA (GODL-INDIA), AMIT SHAH, FILE PHOTO (RAIGAD), NOT FROM KOTA · QUOTE AS REPORTED BY THE QUINT, 27 SEPT 2018")

# R3. Dark red cinema: the trend machine, with labelled platform cards
wa = f'<div style="line-height:0">{icon("whatsapp", 44)}</div>'
xx = f'<div style="line-height:0">{icon("x", 40, "#F2F2F2")}</div>'
body = el(f'<div style="font:400 300px/0.85 Anton;color:#FF3B30;text-shadow:0 0 40px rgba(255,40,30,.75),0 0 120px rgba(255,0,0,.45)">75</div>', 120, 140, .2, "pop", z=6)
body += el(f'<div style="font:400 92px/0.9 Anton;color:#F2E9E6">COORDINATED<br>CAMPAIGNS</div>', 130, 420, .6, "slide", z=6)
body += el('<div style="font:600 18px Mono;color:#fff;background:#2F6DB5;padding:6px 12px;letter-spacing:3px">REPORTED · JAKESCH ET AL., CSCW 2021</div>', 130, 640, 1.0, "pop", z=7)
body += K.micro(130, 700, ["600+ public pro-BJP WhatsApp groups studied, 2019", "organiser 'most likely' the party's social media arm", "not confirmed: WhatsApp's anonymity", "campaigns smaller than reported · no evidence of pay"], 14, 620, 1.3, col="#E9C9C4")
body += K.ui_card(wa, "Volunteers' group", ["Post at 9:00 AM", "#__________", "copy · paste · post"], 1080, 120, 560, .9, -3)
body += K.ui_card(xx, "Trending in India", ["#__________ · trending", "#__________ · trending", "#__________ · trending"], 1180, 560, 560, 1.5, 2, dark=True)
body += K.red_string([(980, 330), (1080, 260)], 1.2) + K.red_string([(1360, 520), (1430, 600)], 1.8)
S["r3_redcinema"] = (K.red_cinema(), body, "CARDS: LABELLED ILLUSTRATIONS OF THE FORMAT THE STUDY DESCRIBES, HASHTAGS BLANKED · LOGOS: SIMPLE ICONS (CC0), TRADEMARKS OF META AND X CORP.")

# R4. Vintage desk: the paper trail of money, pinned and strung
aged = "sepia(.55) contrast(1.15) brightness(.97)"
body = el(f'<div style="width:760px;height:430px;overflow:hidden;background:#F3EAD3;box-shadow:12px 18px 28px rgba(0,0,0,.55)">{scrap_img("scroll_1737", "left top", aged)}</div>', 120, 120, .2, "drop", base="rotate(-3deg)", z=5)
body += el(f'<div style="width:700px;height:380px;overflow:hidden;background:#F3EAD3;box-shadow:12px 18px 28px rgba(0,0,0,.55)">{scrap_img("tribune_7113", "left top", aged)}</div>', 1140, 640, .7, "drop", base="rotate(2.5deg)", z=5)
body += K.pin_dot(500, 140) + K.pin_dot(1490, 660)
labels = [("₹1,737.68 cr · declared to the ECI, 2024", 130, 600, -2), ("₹611.50 cr · media advertising", 160, 700, 1), ("₹156.95 cr · Google India  ·  ₹24.63 cr · Facebook", 140, 800, -1),
          ("₹7,113 cr · party funds (EC data)", 1100, 300, 2), ("Congress · ₹857 cr", 1180, 400, -2)]
for i, (t, x, y, r) in enumerate(labels):
    body += K.torn_label(t, x, y, 30, CREAM, INK, r, 1.0 + i * .35, seed=20 + i)
body += K.red_string([(500, 140), (900, 420), (1490, 660)], 2.6)
body += el(f'<div style="font:italic 900 80px Playfair;color:#F3EAD3;text-shadow:3px 4px 0 rgba(0,0,0,.4)">the paper trail</div>', 1180, 110, 2.0, "slide", z=6)
body += el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse at 30% 25%,rgba(255,200,120,.22) 0%,transparent 45%)"></div>', 0, 0, 0, "pop", extra=STILL, z=60)
S["r4_desk"] = (K.wood(), body, "SOURCE PAGES: SCROLL 31 JAN 2025 (BJP'S EXPENDITURE REPORT VIA PTI), THE TRIBUNE 29 JAN 2025 (EC DATA) · CROPPED SCREENSHOTS, AGED FOR THE DESK LOOK")

# R5. Sunburst world: not a one-party story (both symbols, identical engraving treatment)
body = K.sunburst(560, 520, 1300, "#E8571E", 44, 0, 1) + K.sunburst(1360, 520, 1300, "#2E6E73", 44, 0, 1)
body += el('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,transparent 49.6%,#F1E7D2 49.6% 50.4%,transparent 50.4%)"></div>', 0, 0, 0, "pop", extra=STILL, z=2)
floor = 'background:conic-gradient(#141414 25%,#F1E7D2 0 50%,#141414 0 75%,#F1E7D2 0) 0 0/90px 90px;transform:perspective(700px) rotateX(62deg);transform-origin:50% 0'
body += f'<div class="el" style="left:-400px;top:780px;width:2720px;height:700px;{floor};z-index:3"></div>'
for x, f, lab in ((380, "bjp_symbol.png", "BJP"), (1180, "inc_symbol.png", "CONGRESS")):
    body += K.disc_frame(f'<img src="{(A / f).as_uri()}" style="width:62%;filter:grayscale(1) contrast(1.35)">', x + 180, 470, 200, "#F1E7D2", .3 if x < 1000 else .6)
    body += el(f'<div style="font:600 34px Bebas;letter-spacing:10px;color:{INK};background:#F1E7D2;padding:6px 18px">{lab}</div>', x + 120, 700, 1.0, "pop", z=7)
body += el(f'<div style="font:italic 900 96px Playfair;color:#F1E7D2;background:{INK};padding:6px 34px 14px">Not a one-party story.</div>', 400, 50, 1.4, "slide", z=8)
body += K.torn_label("2019 · Facebook removes 687 items linked to the Congress IT cell, and 15 linked to Silver Touch", 210, 900, 24, CREAM, INK, -1, 2.0, z=9, seed=40)
body += K.torn_label("2024 · Telangana Congress social media workers arrested over a doctored video", 330, 980, 24, CREAM, INK, 1, 2.4, z=9, seed=41)
S["r5_sunburst"] = ("background:#F1E7D2", body, "SYMBOLS: BJP AND INC (PUBLIC DOMAIN FILES, WIKIMEDIA COMMONS), IDENTICAL TREATMENT · SOURCES: META NEWSROOM 1 APR 2019; THE QUINT; SCROLL MAY 2024")

if __name__ == "__main__":
    (D / "html").mkdir(exist_ok=True)
    for k, (bg, body, cr) in S.items():
        (D / "html" / f"{k}.html").write_text(K.page(body, bg, 5, .04, cr), encoding="utf-8")
    print(len(S), "stills")
