"""Extra pages for the video (2026-11-20). Run after frames.py:  python3 video/pages.py   (from the film folder)

1. 14_peel_v, 24_icj_v: the approved key frames 14 and 24 with the SAME pieces, only their timeline order changed so the
   pieces arrive in the order the approved voiceover names them (14: figures, beach/lake tag, Ancon card, 1904 card, same-date
   tag; 24: 'coffee sometime' tag before the two governments' reaction tabs). Nothing is added or removed.
2. 24a_filing: one new studio page for script rows 4 · 6:59-7:22 (the 2013 application, the argument, Chile's objection, the
   2015 ruling on it), which had no key frame. Film helpers only, dates only from dossier.json, labelled studio cards, no AI.
"""
import sys
from pathlib import Path

D = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(D))
import frames as F  # noqa: E402  (also rebuilds the 26 approved pages, unchanged)

H = D / "html"


def retime(src, dst, swaps):
    s = (H / f"{src}.html").read_text(encoding="utf-8")
    for marker, old, new in swaps:
        i = s.index(marker)
        j = s.rfind('data-anim="', 0, i)
        assert s[j:j + 11 + len(old)] == f'data-anim="{old}', (marker, s[j:j + 40])
        s = s[:j] + f'data-anim="{new}' + s[j + 11 + len(old):]
    (H / f"{dst}.html").write_text(s, encoding="utf-8")


retime("14_peel", "14_peel_v", [
    ("OF COAST</div>", "up .55 .68", "up .55 .62"),
    ("BOLIVIA HAD A BEACH", "snap .92 .92", "snap .66 .66"),
    ("TREATY OF ANCÓN · PERU–CHILE", "drop .62 .68", "drop .72 .78"),
    ("PEACE AND FRIENDSHIP · BOLIVIA–CHILE", "drop .7 .76", "drop .8 .86"),
    ("SAME DATE · DIFFERENT DECADE", "snap .82 .82", "snap .93 .93"),
])
retime("24_icj", "24_icj_v", [
    ("RULING: NO OBLIGATION", "snap .9 .9", "snap .7 .7"),
    ("BOLIVIA: KEEP TALKING", "fade .7 .75", "fade .9 .93"),
    ("CHILE: DIALOGUE YES", "fade .76 .8", "fade .95 .98"),
])

INK, PARCH, RED, TEAL = F.INK, F.PARCH, F.RED, F.TEAL
note = lambda rot, x, y, anim: F.A(
    f'<div style="width:360px;height:250px;box-sizing:border-box;padding:26px 28px;background:{F.OLD};box-shadow:0 14px 26px rgba(0,0,0,.45);transform:rotate({rot}deg)">'
    f'{F.kicker("DIPLOMATIC NOTE")}{F.bar(92)}{F.bar(84)}{F.bar(96)}{F.bar(58)}</div>', x, y, anim, "z-index:28")
h, pr = F.table(-66.5, -17.0, 0.9, 960, 560)
F.put("24a_filing", F.page(
    h + F.a('<div style="width:1920px;height:1080px;background:rgba(26,26,26,.5)"></div>', 0, 0)
    + note(-7, 880, 150, "drop .3 .35") + note(3, 1150, 130, "drop .34 .39") + note(11, 1420, 170, "drop .38 .43")
    + F.label("BOLIVIA'S ARGUMENT: DECADES OF TALKS CREATED A DUTY TO KEEP TALKING", 900, 440, "fade .42 .5", 17)
    + F.A(f'<div style="font:500 14px Plex;letter-spacing:2px;color:{PARCH};background:rgba(26,26,26,.85);padding:4px 9px">NOTES: BLANK STAND-INS, NOT REPRODUCED</div>', 1420, 96, "fade .4 .45", "z-index:60")
    + F.card(F.kicker("APPLICATION · INTERNATIONAL COURT OF JUSTICE · THE HAGUE")
             + f'<div style="font:400 84px/1 Anton;color:{INK};margin-top:12px">BOLIVIA v. CHILE</div>'
             + f'<div style="font:400 44px/1.12 Anton;color:{INK};margin-top:14px">{F.hl("OBLIGATION TO NEGOTIATE")}<br>ACCESS TO THE PACIFIC OCEAN</div>'
             + f'<div style="font:500 14px Plex;letter-spacing:2px;color:#7A6A4A;margin-top:18px">FILED 24 APRIL 2013 · STUDIO CARD, NOT THE COURT PAGE</div>', 640, 110, 230, "up .06 .16", -1.5, z=40)
    + F.card(F.kicker("PRELIMINARY OBJECTION · CHILE · WRITTEN PLEADING, 15 JUL 2014")
             + f'<div style="font:400 58px/1.05 Anton;color:{INK};margin-top:12px">THE COURT CANNOT HEAR THIS: THE 1904 TREATY SETTLED IT</div>'
             + f'<div style="font:500 14px Plex;letter-spacing:2px;color:#7A6A4A;margin-top:16px">CHILE\'S ARGUMENT, SUMMARISED · STUDIO CARD</div>'
             + f'<div data-anim="slam .8 .83" style="position:absolute;left:120px;top:150px"><div style="border:7px solid {RED};color:{RED};background:rgba(244,239,230,.9);font:400 46px/1.05 Anton;padding:10px 20px;transform:rotate(-7deg);letter-spacing:3px;white-space:nowrap">OBJECTION REJECTED · CASE PROCEEDS</div></div>',
             700, 980, 560, "up .55 .65", 1.5, bg="#EFE7D6", z=42)
    + F.stamp([("1992", 0, .03), ("2000", .03, .05), ("24 APR 2013", .05, .72), ("24 SEP 2015", .72, 9)], "ff"),
    "ICJ, OBLIGATION TO NEGOTIATE ACCESS TO THE PACIFIC OCEAN (BOLIVIA v. CHILE): APPLICATION FILED 24 APR 2013; CHILE'S PRELIMINARY OBJECTION (WRITTEN PLEADING 15 JUL 2014); "
    "OBJECTION REJECTED, JURISDICTION FOUND, 24 SEP 2015 (ICJ CASE 153 PAGE) · CARDS SET IN THE STUDIO, NOT COURT PAGES · " + F.MAPSRC, cam=(1.0, 1.05), origin="50% 50%"))
print("video pages: 14_peel_v, 24_icj_v, 24a_filing")
