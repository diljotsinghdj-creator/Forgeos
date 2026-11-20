"""Faces for "Why India Is Mocked Online": the faces grid (real photos, credited) and the named achievers.
Real people only from credited public-domain or licensed photos, framed neutrally, nothing drawn on faces."""
import json
import sys
from pathlib import Path
D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from studio import page, A, a, put, hl, chapter, PARCH, RED, SIG, INK  # noqa: E402

CR = json.load(open(D / "data" / "face_credits.json"))
ORDER = ["H1", "O7", "H3", "H9", "O14", "H10", "O26", "H11", "O22", "H17", "O3", "O24"]
POS = {"H1": "50% 25%", "H3": "50% 22%", "H9": "50% 35%", "H10": "50% 25%", "H11": "50% 30%", "H17": "70% 40%", "O3": "50% 20%", "O7": "50% 35%",
       "O14": "55% 35%", "O22": "40% 40%", "O24": "62% 35%", "O26": "45% 25%"}
tiles = ""
for i, k in enumerate(ORDER):
    c, r = i % 6, i // 6
    x, y = 110 + c * 290, 330 + r * 340
    who = CR[k]["user"] or "unknown"
    tiles += A(f'<div style="background:#fff;padding:10px 10px 12px;box-shadow:10px 12px 0 rgba(0,0,0,.45);transform:rotate({(-2, 1.5, -1, 2, -1.5, 1)[i % 6]}deg)">'
               f'<img src="/assets/f_{k}.jpg" style="width:240px;height:250px;object-fit:cover;object-position:{POS[k]};display:block">'
               f'<div style="font:500 11px Plex;letter-spacing:1px;color:#555;margin-top:6px;white-space:nowrap;overflow:hidden;width:240px">{CR[k]["source"].upper()} · {who[:18]} · {CR[k]["licence"]}</div></div>',
               x, y, f"pop {.12 + i * .055:.2f} {.18 + i * .055:.2f}")
put("18c_faces", page(
    tiles + chapter(6, "FIXING THE FEED")
    + A(f'<div style="font:400 84px/0.95 Anton;color:{INK}">ABOUT 1.4 BILLION PEOPLE.</div><div style="font:400 40px ISerif;color:#444;margin-top:6px">The feed keeps showing you the same four clips.</div>', 110, 110, "up 0 .1")
    + A(f'<div style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;box-shadow:6px 6px 0 rgba(0,0,0,.35);transform:rotate(2deg);white-space:nowrap">VIRAL POTENTIAL: TRAGICALLY LOW</div>', 1300, 140, "snap .88 .88", "z-index:70"),
    PARCH, "PHOTOS: PIXABAY (PIXABAY CONTENT LICENSE) AND FLICKR VIA OPENVERSE (CC BY 2.0), CREDITED ON EACH PHOTO · REAL PEOPLE, SHOWN AS PHOTOGRAPHED; NOTHING ADDED TO ANY FACE · POPULATION: UN WORLD POPULATION PROSPECTS (ABOUT 1.4 BILLION)"))

# named achievers: Kalpana Chawla + pageant winners (added when their photos are in assets/a_*.jpg)
ach = [("p_chawla.jpg", "KALPANA CHAWLA", "First Indian-born woman in space, 1997", "NASA · PUBLIC DOMAIN")]
meta = D / "data" / "achievers.json"
if meta.is_file():
    ach += [tuple(x) for x in json.load(open(meta))]
cards = ""
n = len(ach)
w = min(400, int(1680 / n) - 40)
for i, (f, name, what, cred) in enumerate(ach):
    x = (1920 - n * (w + 40) + 40) // 2 + i * (w + 40)
    cards += A(f'<div style="width:{w}px;background:#fff;padding:12px 12px 16px;box-shadow:12px 14px 0 rgba(0,0,0,.45);transform:rotate({(-1.5, 1.5)[i % 2]}deg)">'
               f'<img src="/assets/{f}" style="width:{w}px;height:{int(w * 1.15)}px;object-fit:cover;object-position:50% 22%;display:block">'
               f'<div style="font:400 {38 if w > 300 else 30}px/1 Anton;color:{INK};margin-top:10px">{name}</div><div style="font:400 24px/1.15 ISerif;color:#444;margin-top:4px">{what}</div>'
               f'<div style="font:500 11px Plex;letter-spacing:1px;color:#777;margin-top:8px">{cred}</div></div>', x, 300, f"up {.15 + i * .12:.2f} {.27 + i * .12:.2f}")
put("18b_achievers", page(
    cards + chapter(6, "FIXING THE FEED")
    + A(f'<div style="font:400 84px/0.95 Anton;color:{INK}">NAMED, NOT VIRAL</div>', 110, 120, "up 0 .1")
    + A(f'<div style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;box-shadow:6px 6px 0 rgba(0,0,0,.35);transform:rotate(-1.5deg);white-space:nowrap">ALGORITHM\'S VERDICT: NOT DISGUSTING ENOUGH</div>', 1060, 140, "snap .88 .88", "z-index:70"),
    PARCH, "PHOTOS: NASA (PUBLIC DOMAIN) VIA WIKIMEDIA COMMONS; OTHERS CREDITED ON EACH CARD · SHOWN AS FACTUAL, CAPTIONED ACHIEVEMENTS; NO ENDORSEMENT IMPLIED"))
print("ok")
