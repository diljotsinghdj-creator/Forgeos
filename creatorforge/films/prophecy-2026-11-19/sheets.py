"""Contact sheets for the owner: V5_n (2 columns of 960x540 stills, named) and M_5 (motion builds at four moments).
Run after shoot_http.py; motion stills come from `python3 shoot_http.py name@t ...`."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parent
OUT = D / "sheets"; OUT.mkdir(exist_ok=True)
FONT = "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts"
try:
    F = ImageFont.truetype(next(Path(FONT).glob("*.ttf")).as_posix(), 22)
except Exception:
    F = ImageFont.load_default()
MOTION = ["02_house", "03_metal", "05_timeline", "07_millerites", "08_map", "12_valve", "13_carlsmith", "14_twoclocks",
          "15_box", "20_replications", "22_irony", "22b_textbooks"]
TS = (0.2, 0.45, 0.7, 1.0)


def stills(tag="V5", per=8):
    names = sorted(p.stem for p in (D / "html").glob("*.html"))
    for k in range(0, len(names), per):
        part = names[k:k + per]; rows = (len(part) + 1) // 2
        S = Image.new("RGB", (2 * 960 + 30, rows * 580 + 10), "#141824"); d = ImageDraw.Draw(S)
        for i, n in enumerate(part):
            im = Image.open(D / "png" / f"{n}.jpg").convert("RGB").resize((960, 540), Image.LANCZOS)
            x, y = 10 + (i % 2) * 970, 10 + (i // 2) * 580
            S.paste(im, (x, y)); d.text((x + 4, y + 544), n, fill="#F0F4F8", font=F)
        S.save(OUT / f"{tag}_{k // per + 1}.jpg", quality=85)
    print("stills", len(names))


def motion(tag="M_5"):
    S = Image.new("RGB", (4 * 480 + 50, len(MOTION) * 305 + 10), "#141824"); d = ImageDraw.Draw(S)
    for r, n in enumerate(MOTION):
        for c, t in enumerate(TS):
            im = Image.open(D / "png" / "anim" / f"{n}@{t:.2f}.jpg").convert("RGB").resize((480, 270), Image.LANCZOS)
            x, y = 10 + c * 490, 10 + r * 305
            S.paste(im, (x, y)); d.text((x + 4, y + 272), f"{n} @ {t:.2f}", fill="#F0F4F8", font=F)
    S.save(OUT / f"{tag}.jpg", quality=85); print("motion", len(MOTION))


if __name__ == "__main__":
    if "--list" in sys.argv:
        print(" ".join(f"{n}@{t}" for n in MOTION for t in TS))
    else:
        stills(); motion() if "--stills" not in sys.argv else None
