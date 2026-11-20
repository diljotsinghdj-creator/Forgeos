"""Frames that held AI plates in draft 3.1, rebuilt from REAL photos and motion graphics (owner, 2026-11-19: "we need more real
pictures, animation, motion graphics etc and less ai"; MASTER_DIRECTIVES 8c "Real first"). Runs after frames.py.
The file keeps its name so the build order in films/RESTORE.md still works. No AI plate is used any more: AI1-AI6 are retired in
data/ai_ledger.json. Photos: assets/real2/ (credits in data/photo_credits_2.json, and on screen). Every word, number, tick,
circle, pin and string is drawn by the studio."""
import json
from pathlib import Path
from frames import tag, page, A, a, put, hl, wobble, phone, DESK, RED, SIG, INK, PARCH, ACC  # noqa: F401  (frames.py re-renders first)

D = Path(__file__).resolve().parent
CR = json.load(open(D / "data" / "photo_credits_2.json"))
R = lambda k: f"/assets/real2/{k}"
credit = lambda k: f'{CR[k]["creator"].upper()} / {CR[k]["via"].split(" (")[0].upper()} ({CR[k]["licence"].upper()})'
STICK = "filter:drop-shadow(3px 0 0 #fff) drop-shadow(-3px 0 0 #fff) drop-shadow(0 3px 0 #fff) drop-shadow(0 -3px 0 #fff) drop-shadow(14px 18px 0 rgba(0,0,0,.45))"
desk = a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
tape = lambda x, y, rot, w=140, an="fade 0 0": A(f'<div style="width:{w}px;height:38px;background:rgba(236,226,200,.82);transform:rotate({rot}deg);box-shadow:0 2px 4px rgba(0,0,0,.25)"></div>', x, y, an, "z-index:45")
pin = lambda x, y, c=RED: a(f'<div style="width:22px;height:22px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#fff 0 12%,{c} 30%,#7A1810 100%);box-shadow:3px 5px 4px rgba(0,0,0,.5)"></div>', x - 11, y - 11, "z-index:46")


def print_(k, w, h, x, y, rot, anim, pos="50% 50%", filt="saturate(.85) contrast(1.05)", inner="", z=20):
    """A real photo print on the desk: white border, hard shadow, slow push inside the frame."""
    return A(f'<div style="background:#fff;padding:14px 14px 18px;box-shadow:14px 18px 0 rgba(0,0,0,.45);transform:rotate({rot}deg)">'
             f'<div style="width:{w}px;height:{h}px;overflow:hidden;position:relative"><img data-anim="push 0 1" data-z=".05" src="{R(k + ".jpg")}" '
             f'style="width:{w}px;height:{h}px;object-fit:cover;object-position:{pos};display:block;filter:{filt}">{inner}</div></div>', x, y, anim, f"z-index:{z}")


# ---- 03b · the tiger that lost to a traffic jam (1 · 0:53): real Sundarbans mangrove print + real Bengal tiger cut-out ----------
put("03b_tiger", page(
    desk
    + print_("mangrove", 1240, 746, 90, 150, -1.5, "up 0 .12", "50% 60%")
    + tape(560, 130, -3, 140, "up 0 .12") + tape(1250, 880, 4, 140, "up 0 .12")
    + A(f'<img src="{R("tiger_ka_cut.png")}" style="height:640px;display:block;{STICK}">', 470, 330, "up .12 .3", "z-index:30")
    + A(f'<div style="background:#fff;border-radius:18px;padding:16px 30px;box-shadow:8px 10px 0 rgba(0,0,0,.4);display:flex;align-items:center;gap:18px">'
        f'<div style="font:400 40px Anton;color:#9AA3AD">▶</div><div style="font:400 92px/1 Anton;color:{INK}">0 VIEWS</div></div>', 900, 230, "slam .34 .36", "z-index:40;transform:rotate(3deg)")
    + f'<svg class="a" data-anim="draw .4 .5" style="left:0;top:0;z-index:41" width="1920" height="1080"><path d="{wobble(1110, 300, 240, 78, 9)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="7"/>'
      f'<path d="M940 380 Q 860 430 790 470" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/><path d="M806 446 L786 474 L820 476" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + A(f'<div style="background:{PARCH};padding:20px 28px;box-shadow:14px 18px 0 rgba(0,0,0,.45);transform:rotate(-1.5deg)"><div style="font:500 16px Plex;letter-spacing:3px;color:#7A6A4A">NTCA / WII · STATUS OF TIGERS 2022</div>'
        f'<div style="font:400 104px/0.95 Anton;color:{INK}">{hl("3,682")}</div><div style="font:400 34px/1.1 Anton;color:{INK}">WILD TIGERS · ABOUT 75% OF THE WORLD\'S</div></div>', 1340, 560, "up .5 .62", "z-index:42")
    + tape(1500, 540, -6, 120, "up .5 .62")
    + tag("NOT TRENDING · LOST TO A TRAFFIC JAM", 1250, 900, 2, "snap .8 .8")
    + a(f'<div style="background:{PARCH};padding:4px 10px;font:500 14px Plex;letter-spacing:2px;color:{INK};white-space:nowrap">REAL PHOTOS · SUNDARBANS MANGROVE · BENGAL TIGER, KARNATAKA</div>', 110, 916, "z-index:43"),
    "#2A1D12", "TIGER COUNT: NTCA/WII 'STATUS OF TIGERS' 2022 (3,682; RANGE 3,167–3,925) · PHOTOS: TIGER, " + credit("tiger_ka") + " · MANGROVE ROOTS, SUNDARBANS, "
    + credit("mangrove") + " · BADGE, CIRCLE AND ARROW DRAWN IN THE STUDIO", dark=True))

# ---- 11b · the outrage slot machine (3 · 4:44): a real slot-machine photo, reels relabelled by the studio --------------------------
reels = "".join(f'<div data-anim="slam {s:.2f} {s + .02:.2f}" style="position:absolute;left:{x}%;top:33%;width:10.5%;height:14%;background:#FBF8F0;display:flex;align-items:center;justify-content:center;'
                f'font:400 30px/1 Anton;color:{RED};box-shadow:inset 0 0 0 3px {INK}">OUTRAGE</div>' for x, s in ((31.2, .3), (43.0, .42), (54.6, .54)))
put("11b_slot", page(
    desk
    + print_("slots", 1100, 619, 760, 150, 1.5, "up 0 .12", "50% 50%", "saturate(.55) sepia(.15) contrast(1.05)", reels)
    + tape(1180, 130, -4, 140, "up 0 .12") + tape(1700, 760, 3, 140, "up 0 .12")
    + A(f'<div style="font:400 84px/0.95 Anton;color:#F3EFE6;text-shadow:0 4px 16px #000">THE INSULT<br>GETS A<br><span style="display:inline-block;margin-top:14px;background:{SIG};color:{INK};padding:4px 12px 0;text-shadow:none">SALARY</span></div>', 90, 150, "up .62 .74", "z-index:30")
    + A(f'<div style="background:{INK};color:{SIG};font:400 64px/1 Anton;padding:10px 18px;letter-spacing:4px;border:3px solid {PARCH}">4,100,000</div>', 90, 520, "slam .66 .68", "z-index:30")
    + A(f'<div style="background:{PARCH};padding:16px 20px;font:500 22px/1.5 Plex;color:{INK};width:480px;box-shadow:10px 12px 0 rgba(0,0,0,.4);transform:rotate(-1deg)">Since Oct 2024, X pays creators by engagement from Premium users.</div>', 90, 640, "fade .74 .84", "z-index:30")
    + f'<svg class="a" data-anim="draw .7 .8" style="left:0;top:0;z-index:41" width="1920" height="1080"><path d="M430 560 Q 640 520 860 420" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + tag("REAL MACHINE · REELS RELABELLED · VIEW COUNT ILLUSTRATIVE", 760, 860, -1.5, "snap .2 .2"),
    "#2A1D12", "PAYOUT RULE: TECHCRUNCH, 9 OCT 2024 · CONFIRMED · VIEW COUNT ILLUSTRATIVE · PHOTO: SLOT MACHINE, " + credit("slots") + "; REEL LABELS ADDED IN THE STUDIO", dark=True))

# ---- 13b · the drain inspector, gone digital (4 · 5:36): a real drain photo, posted from a verified account (drawn phone) ---------
tick = '<svg width="30" height="30" viewBox="0 0 24 24" style="vertical-align:-6px"><circle cx="12" cy="12" r="11" fill="#1D9BF0"/><path d="M7 12.5 L10.4 15.8 L17.2 8.6" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
prof = (f'<div style="padding:22px 18px 10px;display:flex;align-items:center;gap:12px"><div style="width:52px;height:52px;border-radius:50%;background:#C9D1D9"></div>'
        f'<div><div style="font:600 22px Plex;color:#222">Drain Inspector {tick}</div><div style="font:500 16px Plex;color:#778">@drain_inspector · since 1927</div></div></div>'
        f'<div style="padding:4px 18px 12px;font:500 19px/1.4 Plex;color:#333">Inspected the country again today. Found: one drain. Posting it.</div>'
        f'<img src="{R("drain.jpg")}" style="width:100%;height:470px;object-fit:cover;display:block">'
        f'<div style="padding:10px 18px;font:500 17px Plex;color:#667">♥ 3.3M · ↻ 900K · …</div>')
put("13b_inspector", page(
    desk
    + A(phone(prof, 470, 860), 1240, 110, "up 0 .14", "z-index:20")
    + A(f'<div style="font:400 92px/0.95 Anton;color:#F3EFE6;text-shadow:0 4px 16px #000">THE DRAIN<br>INSPECTOR HAS<br><span style="display:inline-block;margin-top:14px;background:{SIG};color:{INK};padding:4px 12px 0;text-shadow:none">GONE DIGITAL</span></div>', 110, 150, "up .1 .25", "z-index:30")
    + A(f'<div style="background:#F4ECD8;width:560px;padding:22px 26px;box-shadow:14px 18px 0 rgba(0,0,0,.45);transform:rotate(-1.5deg)">'
        f'<div style="font:500 15px Plex;letter-spacing:3px;color:#7A6A4A">M. K. GANDHI · YOUNG INDIA · 15 SEP 1927</div>'
        f'<div style="font:400 34px/1.3 ISerif;color:#2A2118;margin-top:10px">"…the report of a drain inspector…"</div></div>', 110, 520, "up .35 .48", "z-index:30")
    + tape(300, 500, -4, 120, "up .35 .48")
    + A(f'<div style="font:700 58px/1.1 Caveat;color:{SIG};transform:rotate(-2deg)">"Now with a blue tick."</div>', 720, 760, "fade .55 .65", "z-index:30")
    + f'<svg class="a" data-anim="draw .5 .6" style="left:0;top:0;z-index:41" width="1920" height="1080"><path d="{wobble(1566, 166, 58, 34, 4)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/>'
      f'<path d="M990 780 Q 1150 700 1250 560" pathLength="1" fill="none" stroke="{RED}" stroke-width="6"/></svg>'
    + tag("CALLBACK · GANDHI ON 'MOTHER INDIA', 1927", 110, 900, -1.5, "snap .8 .8")
    + tag("ACCOUNT AND POST DRAWN · DRAIN PHOTO REAL", 1180, 990, 1, "snap .2 .2"),
    "#2A1D12", "QUOTE: M. K. GANDHI, 'DRAIN INSPECTOR'S REPORT', YOUNG INDIA, 15 SEP 1927 · PHONE, ACCOUNT AND COUNTS DRAWN IN THE STUDIO, NOT A REAL ACCOUNT · PHOTO: STREET STORM DRAIN, " + credit("drain"), dark=True))

# ---- 19b · the 'not interested' button (5 · 8:30): real hands on a real phone, the menu drawn on its screen ----------------------
menu = "".join(f'<div style="padding:15px 14px;font:500 19px Plex;color:#222;border-bottom:1px solid #E3E6EA;{"background:#EAF2FB" if i == 0 else ""}">{t}</div>'
               for i, t in enumerate(("Not interested", "Follow", "Mute", "Report")))
screen = (f'<div style="position:absolute;left:675px;top:52px;width:325px;height:604px;background:#F4F6F8;border-radius:10px;overflow:hidden">'
          f'<div style="height:250px;background:#9AA3AD;position:relative"><div style="position:absolute;left:10px;bottom:10px;background:rgba(0,0,0,.72);color:#fff;font:500 13px Plex;padding:3px 7px">CLIP: HATE-BAIT</div></div>'
          f'<div data-anim="pop .25 .33" style="margin:-120px 18px 0;position:relative;background:#fff;border-radius:12px;box-shadow:0 10px 24px rgba(0,0,0,.35);overflow:hidden">{menu}</div></div>')
put("19b_button", page(
    a('<div style="width:1920px;height:1080px;background:#0E1116"></div>', 0, 0)
    + A(f'<div style="position:relative;width:1300px"><img src="{R("thumbs_cut.png")}" style="width:1300px;display:block;filter:drop-shadow(0 30px 40px rgba(0,0,0,.6))">{screen}</div>', 520, 200, "up 0 .16", "z-index:20")
    + f'<svg class="a" data-anim="draw .38 .48" style="left:0;top:0;z-index:41" width="1920" height="1080"><path d="{wobble(1358, 410, 180, 42, 2)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="7"/></svg>'
    + A(f'<div style="background:#fff;padding:12px 22px;font:400 50px/1 Anton;color:{INK};letter-spacing:2px;box-shadow:8px 8px 0 rgba(0,0,0,.4);transform:rotate(-3deg)">NOT INTERESTED</div>', 1320, 150, "slam .5 .52", "z-index:45")
    + A(f'<div style="font:400 84px/0.95 Anton;color:#F3EFE6">THE CHEAPEST<br>GOOD MANNERS<br><span style="display:inline-block;margin-top:14px;background:{SIG};color:{INK};padding:4px 12px 0;text-shadow:none">ON THE INTERNET</span></div>', 110, 160, "up .6 .72", "z-index:30")
    + A(f'<div style="font:700 48px/1.1 Caveat;color:{SIG};transform:rotate(-2deg);width:560px">"One thumb. No speech required."</div>', 110, 560, "fade .72 .84", "z-index:30")
    + tag("SOUND: ONE HEAVY THUNK", 110, 860, -1.5, "snap .52 .52", True)
    + tag("REAL HANDS AND PHONE · SCREEN DRAWN", 1340, 980, 1.5, "snap .1 .1"),
    "#0E1116", "PHOTO: HANDS AND SMARTPHONE, " + credit("thumbs") + ", CUT OUT IN THE STUDIO · MENU AND POST ON THE SCREEN DRAWN, MODELLED ON A GENERIC SOCIAL APP · NOT A SCREEN RECORDING", dark=True))

# ---- 20b · the editing table (5 · 8:33): 12 real frames of India on film strips, snipped away one by one down to one drain -------
REEL = [("ladakh", "ZANSKAR MEETS INDUS · LADAKH"), ("varanasi", "THE GANGA · VARANASI"), ("kerala", "BACKWATERS · KERALA"), ("thar", "THAR DESERT · JAISALMER"),
        ("mumbai", "SEA LINK · MUMBAI"), ("drain", "A STREET DRAIN"), ("ghats", "SAHYADRI · MAHARASHTRA"), ("taj", "TAJ MAHAL · AGRA"),
        ("hampi", "VIRUPAKSHA · HAMPI"), ("meghalaya", "HILLS · SHILLONG"), ("goa", "SUNSET · GOA"), ("mangrove", "MANGROVES · SUNDARBANS")]
CUT_ORDER = [0, 11, 3, 8, 1, 10, 6, 4, 9, 2, 7]   # every frame but the drain (index 5), in the order the feed snips them
FW, FH, GX, GY, CX, RY = 318, 212, 110, 150, 352, 262
strips = "".join(a(f'<div style="width:{4 * CX + 24}px;height:{FH + 44}px;background:#141210;box-shadow:12px 16px 0 rgba(0,0,0,.45);'
                   f'background-image:repeating-linear-gradient(90deg,#E8E0CC 0 14px,transparent 14px 34px),repeating-linear-gradient(90deg,#E8E0CC 0 14px,transparent 14px 34px);'
                   f'background-size:100% 10px,100% 10px;background-position:0 6px,0 {FH + 28}px;background-repeat:repeat-x"></div>', GX - 16, GY - 22 + r * RY, "z-index:10")
                 for r in range(3))
cells = ""
for i, (k, lab) in enumerate(REEL):
    c, r = i % 4, i // 4
    x, y = GX + c * CX, GY + r * RY
    body = (f'<div style="width:{FW}px;height:{FH}px;overflow:hidden;position:relative;outline:3px solid #000"><img src="{R(k + ".jpg")}" style="width:100%;height:100%;object-fit:cover;display:block;filter:saturate(.9)">'
            f'<div style="position:absolute;left:0;bottom:0;background:rgba(10,10,10,.72);color:#F3EFE6;font:500 12px Plex;letter-spacing:2px;padding:3px 7px">{lab}</div></div>')
    if i == 5:
        cells += a(body, x, y, "z-index:20")
    else:
        s = .12 + CUT_ORDER.index(i) * .045
        mark = f'<div data-anim="snap {s - .015:.3f} {s - .015:.3f}" style="position:absolute;left:-6px;top:-20px;width:5px;height:{FH + 40}px;background:{RED}"></div>'
        cells += A(f'<div style="position:relative">{body}{mark}</div>', x, y, f"out {s:.3f} {s + .06:.3f}", f"z-index:20;transform-origin:50% 0")
dx, dy = GX + 1 * CX, GY + 1 * RY
put("20b_edit", page(
    desk + strips + cells
    + A(f'<div style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:10px 16px;font:500 22px Plex;letter-spacing:4px;white-space:nowrap">FRAMES LEFT: '
        f'<span data-anim="countdown .12 .62" data-from="12" data-to="1" style="color:{SIG}">1</span></div>', 1570, 130, "fade 0 .05", "z-index:60;transform:rotate(1.5deg)")
    + f'<svg class="a" data-anim="draw .66 .74" style="left:0;top:0;z-index:50" width="1920" height="1080"><path d="{wobble(dx + FW / 2, dy + FH / 2, FW * .68, FH * .72, 5)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="8"/></svg>'
    + A(f'<div style="background:{PARCH};padding:20px 28px;box-shadow:14px 18px 0 rgba(0,0,0,.45);transform:rotate(-1.5deg)"><div style="font:400 66px/1 Anton;color:{INK}">1.4 BILLION PEOPLE</div>'
        f'<div style="font:400 66px/1 Anton;color:{RED}">→ ONE FRAME</div></div>', 1010, 560, "up .74 .86", "z-index:55")
    + tape(1180, 540, -5, 120, "up .74 .86")
    + tag("FINAL CUT: ONE DRAIN", 1080, 840, -2, "snap .88 .88")
    + a(f'<div style="background:{INK};color:{PARCH};padding:8px 16px;font:500 20px Plex;letter-spacing:5px">CHAPTER 6 · FIXING THE FEED</div>', 70, 60),
    "#2A1D12", "POPULATION: UN WORLD POPULATION PROSPECTS (ABOUT 1.4 BILLION; CHECK LATEST) · 12 REAL PHOTOS: PIXABAY (PIXABAY CONTENT LICENSE): HEARTOGRAPHY, OREOTIKII, ALLEPPEYHOUSEBOATCLUB, RAVENDRASINGH, YOGENDRAS31, ANKITA_GKD, YOSRATAWAKOL, TRAVELPHOTOGRAPHER, MOBILEPHOTOGRAPHY_TAREQ, SUMIT_T, SARANGIB · DRAIN: FRIED DOUGH, FLICKR (PUBLIC DOMAIN MARK) · FILM STRIPS AND CUTS DRAWN IN THE STUDIO", dark=True))
print("real frames ok")
