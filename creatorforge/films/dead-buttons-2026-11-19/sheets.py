"""Contact sheets for QA: python3 sheets.py  ->  sheets/V2_n.jpg (2 columns, 960x540 thumbnails, 6 per sheet) and
python3 sheets.py motion a b c d  ->  sheets/M_2.jpg (each frame at t = 0.2 / 0.45 / 0.7 / 1.0, from png/anim/)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parent
S = D / "sheets"; S.mkdir(exist_ok=True)
F = "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts"
try:
    font = ImageFont.truetype(f"{F}/../../vendor/fonts/IBMPlexMono-Medium.ttf", 22)
except Exception:
    font = ImageFont.load_default(size=22)


def sheet(items, out, cols=2):
    W, H, L = 960, 540, 40
    rows = (len(items) + cols - 1) // cols
    im = Image.new("RGB", (cols * W + (cols + 1) * 10, rows * (H + L) + 10), "#141824"); d = ImageDraw.Draw(im)
    for k, (name, path) in enumerate(items):
        x, y = 10 + (k % cols) * (W + 10), 10 + (k // cols) * (H + L)
        im.paste(Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS), (x, y + L - 6))
        d.text((x + 4, y + 4), name, fill="#F0F4F8", font=font)
    im.save(out, quality=86); print("sheet", out.name)


PFX = "V2"     # second pass (2026-11-19): less AI, more real
MOUT = "M_2"
if len(sys.argv) > 2 and sys.argv[1] == "pick":   # python3 sheets.py pick out.jpg 06_x 08_y ...  (QA of a few frames)
    sheet([(n, D / "png" / f"{n}.jpg") for n in sys.argv[3:]], Path(sys.argv[2]))
elif len(sys.argv) > 1 and sys.argv[1] == "motion":
    items = [(f"{n} @ t={t}", D / "png" / "anim" / f"{n}@{t:.2f}.jpg") for n in sys.argv[2:] for t in (.2, .45, .7, 1.0)]
    sheet(items, S / f"{MOUT}.jpg", cols=4)
else:
    pngs = sorted((D / "png").glob("*.jpg"))
    for i in range(0, len(pngs), 6):
        sheet([(p.stem, p) for p in pngs[i:i + 6]], S / f"{PFX}_{i // 6 + 1}.jpg")
