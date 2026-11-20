"""Real-image frames that replace the AI plates P2, P3, P4 and P6 (2026-11-19, owner: "more real pictures, animation, motion
graphics etc and less ai"; MASTER_DIRECTIVES 8c "real first"). P5 (the relay) is replaced by the animated map 13a_relay in
motion_maps.py; P1 (the desk) by the drawn walnut desk in frames.py.
Photos: assets/real2/ (Openverse, CC0 / PDM / CC BY), logged in data/photo_credits_2.json and credited in each source line.
Every piece carries a timeline entry (render any moment with ?t=0..1). Numbers only from dossier.json. Run after comedy.py."""
from frames import page, A, a, put, hl, blk, wobble, tape, chapter, DESK, RED, SIG, INK, PARCH

R2 = lambda f: f"/assets/real2/{f}"


def print_(f, w, h, rot, extra="", fit="cover", pos="center"):
    """A photo print on the desk: white border, drop shadow, slight rotation."""
    return (f'<div style="background:#FBF8F0;padding:16px 16px 18px;transform:rotate({rot}deg);box-shadow:0 26px 50px rgba(0,0,0,.6)">'
            f'<img src="{R2(f)}" style="width:{w}px;height:{h}px;object-fit:{fit};object-position:{pos};display:block;{extra}"></div>')


def head(html, x, y, anim="up .1 .25", size=88, col="#F3EFE6"):
    return A(f'<div style="font:400 {size}px/1.12 Anton;color:{col};text-shadow:0 4px 18px rgba(0,0,0,.5)">{html}</div>', x, y, anim, "z-index:30")


def tag(text, x, y, rot=-1.5, anim="snap .85 .85", dark=True):
    bg, fg = (INK, PARCH) if dark else (PARCH, INK)
    return A(f'<div style="background:{bg};color:{fg};border:2px solid {fg};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;'
             f'transform:rotate({rot}deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">{text}</div>', x, y, anim, "z-index:70")


def hand(text, x, y, anim, col=SIG, size=50, rot=-2, w=None):
    return A(f'<div style="font:700 {size}px/1.1 Caveat;color:{col};transform:rotate({rot}deg);{f"width:{w}px" if w else "white-space:nowrap"}">{text}</div>', x, y, anim, "z-index:40")


def circle(cx, cy, rx, ry, anim, col=RED, seed=3, w=6):
    return f'<svg class="a" data-anim="draw {anim}" style="left:0;top:0;z-index:35" width="1920" height="1080"><path d="{wobble(cx, cy, rx, ry, seed)}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}"/></svg>'


def arrow(x1, y1, x2, y2, anim, col=RED, bend=-50):
    import math
    mx, my = (x1 + x2) / 2 + bend * .4, (y1 + y2) / 2 + bend
    ang = math.atan2(y2 - my, x2 - mx); h = 24
    return (f'<svg class="a" data-anim="draw {anim}" style="left:0;top:0;z-index:36" width="1920" height="1080">'
            f'<path d="M{x1} {y1} Q {mx:.0f} {my:.0f} {x2} {y2}" pathLength="1" fill="none" stroke="{col}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M{x2 - h * math.cos(ang - .45):.0f} {y2 - h * math.sin(ang - .45):.0f} L{x2} {y2} L{x2 - h * math.cos(ang + .45):.0f} {y2 - h * math.sin(ang + .45):.0f}" pathLength="1" fill="none" stroke="{col}" stroke-width="6" stroke-linecap="round"/></svg>')


desk = a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)

# P2 -> a real 19th-century engraving: Rome surrounded, 408 (1 · 0:13)
put("02a_siege", page(
    desk
    + A(print_("alaric_engraving.jpg", 1060, 732, -1.5, "filter:sepia(.35) contrast(1.08)"), 90, 170, "up 0 .14")
    + tape(480, 150, -3) + tape(1000, 905, 4)
    + circle(905, 420, 150, 120, ".3 .45", seed=5)
    + hand("the city, behind the army", 760, 230, "fade .42 .5", RED, 40, -3)
    + tag("ROME · 408 CE · UNDER SIEGE", 1260, 140, 2, "snap .08 .08")
    + head(f'ROME IS<br>{blk("SURROUNDED")}', 1250, 260, "up .12 .26", 100)
    + A('<div style="font:400 46px ISerif;color:#E8DCC2">The city is starving.</div>', 1256, 500, "fade .55 .68", "z-index:30")
    + A(f'<div style="background:{PARCH};padding:10px 14px;font:500 15px/1.5 Plex;letter-spacing:2px;color:{INK};box-shadow:0 8px 14px rgba(0,0,0,.4);width:560px">'
        f'"ALARIC" · A 19TH-CENTURY BOOK ENGRAVING · AN ARTIST\'S IMAGINING, DRAWN 1,400 YEARS LATER, NOT A RECORD OF THE SIEGE</div>', 1256, 640, "fade .7 .8", "z-index:31"),
    "#2A1D12", "EVENT: ALARIC'S SIEGE OF ROME, 408 CE (ZOSIMUS, NEW HISTORY 5.41; BURY 1923) · IMAGE: 'ROME - ALARIC', 19TH-C. ENGRAVING VIA HISTORY MAPS / FLICKR (PUBLIC DOMAIN MARK)", dark=True))

# P3 -> the real Portus relief (Torlonia collection): what a Roman merchant ship looked like (2 · 1:28)
put("08a_ship", page(
    desk + chapter(2, "ROME PAYS BY THE POUND")
    + A(print_("portus_ship.jpg", 1000, 750, -2, "filter:sepia(.2) contrast(1.06)", pos="50% 40%"), 90, 150, "up 0 .14")
    + tape(420, 132, -4) + tape(900, 905, 3)
    + circle(520, 420, 330, 240, ".32 .48", seed=8)
    + hand("a real one, carved in stone", 1225, 850, "fade .45 .55", SIG, 46, -3)
    + head(f'THE SHIPS THAT<br>{blk("CARRIED IT")}', 1210, 190, "up .1 .24", 92)
    + A(f'<div style="width:620px;background:{PARCH};padding:24px 28px;box-shadow:0 20px 34px rgba(0,0,0,.5);transform:rotate(1.5deg)">'
        f'<div style="font:500 16px Plex;letter-spacing:4px;color:#7A6A4A">THE ROUTE · SUMMER MONSOON</div>'
        f'<svg data-anim="draw .55 .8" width="560" height="90" viewBox="0 0 560 90" style="display:block;margin:10px 0">'
        f'<path d="M20 60 Q 280 0 540 60" pathLength="1" fill="none" stroke="{RED}" stroke-width="6" stroke-dasharray="1"/></svg>'
        f'<div style="display:flex;justify-content:space-between;font:400 46px Anton;color:{INK}"><span>BERENIKE</span><span>{hl("MUZIRIS")}</span></div>'
        f'<div style="font:400 30px ISerif;color:#555">Egypt\'s Red Sea coast → India\'s Malabar coast</div></div>', 1210, 520, "up .48 .6", "z-index:31")
    + tag("FOLLOW THIS SHIP", 1560, 930, -1.5, "snap .86 .86"),
    "#2A1D12", "PHOTO: 'PORTUS RELIEF (TORLONIA MT 430) DETAIL 016', MARK LANDON, CC BY 4.0, VIA WIKIMEDIA COMMONS · A ROMAN MERCHANT SHIP AT ROME'S HARBOUR, NOT A SHIP OF THE INDIA RUN ITSELF · ROUTE: SEE DOSSIER, ROME CHAPTER", dark=True))

# P4 -> a real sack of pepper: a fortune you can carry (3 · 3:12)
put("10a_sack", page(
    a(f'<img src="{R2("pepper_sack.jpg")}" style="width:1920px;height:1080px;object-fit:cover;object-position:50% 45%;display:block;filter:brightness(.55) saturate(.95)">', 0, 0)
    + A('<div style="width:1920px;height:1080px;background:linear-gradient(90deg,rgba(13,12,10,.85) 0,rgba(13,12,10,.55) 40%,transparent 70%)"></div>', 0, 0, "fade 0 .1")
    + chapter(3, "WHAT MAKES MONEY, MONEY")
    + head(f'A FORTUNE YOU<br>CAN CARRY ON<br>{blk("YOUR SHOULDER")}', 110, 170, "up .05 .2", 92)
    + A(f'<div style="font:400 54px Anton;color:{SIG}">✓ 2. SMALL BUT VALUABLE</div>', 114, 520, "slam .3 .33", "z-index:30")
    + circle(1180, 560, 380, 300, ".4 .56", SIG, 11)
    + A(f'<div style="width:640px;background:{PARCH};padding:22px 26px;box-shadow:0 18px 30px rgba(0,0,0,.5);transform:rotate(-2deg)">'
        f'<div style="font:500 16px Plex;letter-spacing:3px;color:#7A6A4A">GERMAN NICKNAME FOR A RICH MERCHANT</div>'
        f'<div style="font:400 72px/1 Anton;color:{INK};margin-top:6px">{hl("PFEFFERSACK")}</div>'
        f'<div style="font:400 34px ISerif;color:#555">literally: "pepper sack"</div></div>', 114, 660, "up .62 .74", "z-index:31")
    + tag("CONTENTS: A FORTUNE (APPROX.)", 1250, 950, 1.5, "snap .88 .88"),
    "#000", "PHOTO: 'SACK OF PICKED PEPPER SPIKES', STEENBERGS, CC BY 2.0, VIA FLICKR (FRESH PEPPER, BEFORE DRYING) · PFEFFERSACK: PORT OF HAMBURG FAQ", dark=True))

# P6 -> real archive art: a pepper grinder, 1936 (4 · 6:17)
put("14a_demotion", page(
    desk + chapter(7, "TOO MUCH PEPPER")
    + A(print_("grinder_nga.jpg", 520, 702, -2.5, "filter:contrast(1.05)"), 140, 150, "up 0 .14")
    + tape(300, 132, -5)
    + A(print_("peppercorns_hubertl.jpg", 420, 324, 4, "filter:contrast(1.05)"), 720, 620, "drop .2 .3")
    + head(f'THE GREATEST<br>DEMOTION IN<br>{blk("CULINARY HISTORY")}', 1220, 150, "up .3 .44", 80)
    + A(f'<div style="font:400 40px/1.2 ISerif;color:#E8DCC2;width:620px">Once paid as rent, ransom and debt. Now it lives in a grinder.</div>', 1224, 500, "fade .5 .62", "z-index:30")
    + arrow(1240, 700, 690, 540, ".62 .74")
    + hand("former currency", 1260, 720, "fade .66 .74", SIG, 52, -3)
    + tag("FORMER CURRENCY · NOW SEASONING", 1220, 930, 2, "snap .86 .86"),
    "#2A1D12", "TREND: 17TH-CENTURY PRICES FELL (ENCYCLOPEDIA.COM) · ART: ALBERT CAMILLI, 'PEPPER GRINDER', c. 1936, INDEX OF AMERICAN DESIGN, NATIONAL GALLERY OF ART (CC0) · PHOTO: 'BLACK PEPPER IMG 4866', HUBERTL, CC BY 4.0, VIA WIKIMEDIA COMMONS", dark=True))
print("real ok")
