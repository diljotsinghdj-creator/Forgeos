"""Contact sheets of the opening in look 2: the last frame of the chosen shots, as the camera frames them.
usage: python3 preview.py   (shoots video/preview/<shot>_<frame>.jpg)   then   python3 look2_sheets.py   ->   sheets/LOOK2_01.jpg ..."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parent
PV = D / "video" / "preview"
FONTS = Path("/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts")
PICK = ["0.01", "0.02", "0.03", "0.04", "0.05", "0.06", "0.07", "0.08", "0.09", "0.10", "0.22", "0.23", "0.25", "0.26", "0.28", "0.30", "0.32",
        "0.34", "0.37", "0.38", "0.40", "0.42", "0.44", "0.45", "0.46", "0.47", "0.49"]       # one frame per idea; the other 23 shots are further words of the list or a second beat on the same page
W, H, C, R, BAR = 853, 480, 3, 3, 46
SL, PAPER, AM = (20, 24, 36), (240, 244, 248), (237, 137, 54)


def font(size):
    for name in ("dm-mono-latin-500-normal.ttf", "DMMono-Medium.ttf"):
        if (FONTS / name).is_file():
            return ImageFont.truetype(str(FONTS / name), size)
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
    except OSError:
        return ImageFont.load_default()


shots = {s["id"]: s for s in json.loads((D / "video" / "shots.json").read_text())["shots"]}
tl = {r["id"]: r for r in json.loads((D / "video" / "timeline.json").read_text())}
f = font(19)
tiles = []
for sid in PICK:
    frames = sorted(PV.glob(f"{sid}_*.jpg"))
    assert frames, f"no preview frame for shot {sid}: run preview.py first"
    t = tl[sid]["start"] + tl[sid]["dur"]; line = shots[sid]["vo"] or "(silent)"
    tiles.append((frames[-1], f"{int(t) // 60}:{t % 60:04.1f}  {line[:62]}{'…' if len(line) > 62 else ''}"))
(D / "sheets").mkdir(exist_ok=True)
for k in range(0, len(tiles), C * R):
    part = tiles[k:k + C * R]; rows = -(-len(part) // C)
    sh = Image.new("RGB", (W * C, (H + BAR) * rows), SL); d = ImageDraw.Draw(sh)
    for j, (file, text) in enumerate(part):
        x, y = (j % C) * W, (j // C) * (H + BAR)
        sh.paste(Image.open(file).convert("RGB").resize((W, H), Image.LANCZOS), (x, y + BAR))
        d.rectangle((x, y, x + W - 1, y + BAR - 1), fill=SL); d.rectangle((x + 10, y + 12, x + 16, y + BAR - 12), fill=AM); d.text((x + 26, y + 12), text, fill=PAPER, font=f)
    out = D / "sheets" / f"LOOK2_{k // (C * R) + 1:02d}.jpg"; sh.save(out, quality=90); print(out.name, sh.size, len(part), "frames")
