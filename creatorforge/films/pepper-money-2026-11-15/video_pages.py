"""Video-stage pages (2026-11-20), built from the already-built key frames in html/ so the house shell (fonts, grain, logo,
source line, timeline script) is identical. Run after the normal build order (RESTORE.md), from inside the film folder.
  v16_kochi    16_kochi with the sack photo blurred (printed trade names on the burlap), sharp only on the pepper itself
  v18_globe    18_globe without the globe kit's stray "GLOBE · 0%" readout
  v_pepperers  name cards for the Pepperers -> Grocers' Company line (dossier numbers[14])
  v_race       date stamps for "then the race was on" (dossier numbers[18], [20])
No AI, no new numbers: every date is in dossier.json."""
import re
from pathlib import Path

H = Path(__file__).resolve().parent / "html"
PARCH, RED, SIG, INK = "#F4EFE6", "#D93829", "#F7D046", "#1A1A1A"
GRAIN_AT = '<svg style="position:absolute;inset:0;pointer-events:none;opacity:.26'


def shell(src, body, source_line):
    """The built page `src` with its pieces swapped for `body` and its source line for `source_line`."""
    s = (H / f"{src}.html").read_text()
    i, j = s.index("<body>") + 6, s.index(GRAIN_AT)
    s = s[:i] + body + s[j:]
    return re.sub(r'(letter-spacing:1px;color:[^"]*">)[^<]*(</div><script>)', lambda m: m.group(1) + source_line + m.group(2), s, count=1)


def A(html, x, y, anim, extra=""):
    return f'<div class="a" data-anim="{anim}" style="left:{x}px;top:{y}px;{extra}">{html}</div>'


def tag(text, x, y, rot, anim):
    return A(f'<div style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;'
             f'transform:rotate({rot}deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">{text}</div>', x, y, anim, "z-index:70")


# ---- v16_kochi: blur the burlap print, keep the pepper sharp ----------------------------------------------------------------
s = (H / "16_kochi.html").read_text()
m = re.search(r'<img src="/assets/sacks\.jpg" style="([^"]*)">', s)
sharp = (f'<img src="/assets/sacks.jpg" style="{m.group(1)};position:absolute;left:0;top:0;'
         f'-webkit-mask-image:radial-gradient(ellipse 200px 170px at 1445px 640px,#000 45%,transparent 100%);'
         f'mask-image:radial-gradient(ellipse 200px 170px at 1445px 640px,#000 45%,transparent 100%)">')
s = s.replace(m.group(0), f'<img src="/assets/sacks.jpg" style="{m.group(1).replace("filter:", "filter:blur(16px) ")};transform:scale(1.04)">' + sharp, 1)
s = s.replace("PHOTO: PIXABAY (SPICE SACKS, ILLUSTRATIVE)", "PHOTO: PIXABAY (SPICE SACKS, ILLUSTRATIVE; SACK PRINT BLURRED)")
(H / "v16_kochi.html").write_text(s)

# ---- v18_globe ----------------------------------------------------------------------------------------------------------------
s = (H / "18_globe.html").read_text()
(H / "v18_globe.html").write_text(s.replace(">GLOBE · 0%</div>", "></div>"))

# ---- shared desk + chapter chip (taken from the built charter page) -----------------------------------------------------------
s = (H / "12_charter.html").read_text()
i = s.index("<body>") + 6
desk = s[i:s.index('<div class="a" data-anim=', i)]          # the walnut desk and the chapter chip, as built


def card(kicker, big, small, w=640):
    return (f'<div style="width:{w}px;background:{PARCH};padding:28px 34px;box-shadow:0 20px 34px rgba(0,0,0,.5)">'
            f'<div style="font:500 18px Plex;letter-spacing:4px;color:#7A6A4A">{kicker}</div><div style="font:400 84px/1 Anton;color:{INK};margin-top:8px">{big}</div>'
            f'<div style="font:400 34px ISerif;color:#555">{small}</div></div>')


body = (desk
        + A(f'<div style="font:400 88px/1 Anton;color:#F3EFE6;text-shadow:0 4px 18px rgba(0,0,0,.5)">THE PEPPER DEALERS OF LONDON</div>', 120, 150, "up 0 .1")
        + A(f'<div style="transform:rotate(-2deg)">{card("LONDON · RECORDED 1180", "THE PEPPERERS", "the city’s pepper dealers, organised")}</div>', 130, 360, "drop .14 .26")
        + f'<svg class="a" data-anim="draw .45 .62" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="M860 520 Q 960 440 1070 560 M1030 548 L1070 560 L1064 518" '
          f'pathLength="1" fill="none" stroke="{RED}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        + A(f'<div style="transform:rotate(1.5deg)">{card("LONDON · 1376", "THE GROCERS’ COMPANY", "the same trade, under a new name")}</div>', 1090, 470, "drop .62 .74")
        + tag("STATUS: STILL EXISTS", 1380, 760, -2, "snap .88 .88"))
(H / "v_pepperers.html").write_text(shell("12_charter", body, "SOURCE: WORSHIPFUL COMPANY OF GROCERS, COMPANY HISTORY (PEPPERERS RECORDED 1180; GROCERS 1376) · CARDS SET IN THE STUDIO"))

# ---- v_race: four date stamps on the desk -------------------------------------------------------------------------------------
desk6 = desk.replace("CHAPTER 4 · PAYING THE RENT IN PEPPER", "CHAPTER 6 · THE SHORTCUT")
stamps = [("20 MAY 1498", "GAMA REACHES THE COAST<br>NEAR CALICUT", .12), ("c. 1500", "CASA DA ÍNDIA,<br>LISBON", .32),
          ("1600", "ENGLISH EAST INDIA<br>COMPANY CHARTERED", .52), ("1602", "DUTCH COMPANY<br>(VOC)", .72)]
body = (desk6 + A(f'<div style="font:400 100px/1 Anton;color:#F3EFE6;text-shadow:0 4px 18px rgba(0,0,0,.5)">THEN THE RACE '
                  f'<span style="background:{SIG};color:{INK};padding:0 12px">WAS ON</span></div>', 120, 170, "up 0 .08")
        + A(f'<div style="width:1680px;height:4px;background:{PARCH}"></div>', 120, 520, "wipe .08 .8"))
for k, (date, what, at) in enumerate(stamps):
    x = 120 + k * 430
    body += A(f'<div style="width:16px;height:16px;border-radius:50%;background:{RED};border:2px solid #fff"></div>', x - 2, 512, f"pop {at:.2f} {at + .05:.2f}", "z-index:31")
    body += A(f'<div style="border:5px solid {RED};color:{RED};padding:6px 16px;font:400 80px/1 Anton;transform:rotate({(-3, 2, -2, 3)[k]}deg);'
              f'background:rgba(244,239,230,.94);white-space:nowrap;display:inline-block">{date}</div>', x, 570, f"slam {at + .03:.2f} {at + .06:.2f}", "z-index:32")
    body += A(f'<div style="font:500 22px/1.5 Plex;letter-spacing:3px;color:#F3EFE6">{what}</div>', x + 4, 712, f"fade {at + .06:.2f} {at + .12:.2f}")
(H / "v_race.html").write_text(shell("12_charter", body, "DATES: FORDHAM MODERN SOURCEBOOK (GAMA, 20 MAY 1498; SOME SAY 17/18 MAY) · INFOPEDIA (CASA DA ÍNDIA, c. 1500) · EIC CHARTERED 31 DEC 1600 · VOC MARCH 1602"))
print("ok: v16_kochi v18_globe v_pepperers v_race")
