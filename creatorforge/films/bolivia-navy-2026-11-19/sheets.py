"""Contact sheets for QA: V1_n.jpg (2 columns, 960x540 thumbnails with names, 6 per sheet) and M_1.jpg (motion: frames x moments).
Usage: python3 sheets.py            -> stills
       python3 sheets.py M 01_navy 09_1879 14_peel 20_rivers   -> motion sheet from png/anim/<name>@t.jpg"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parent
OUT = D / "sheets"; OUT.mkdir(exist_ok=True)
FONT = "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts"
try:
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 26)
except OSError:
    F = ImageFont.load_default()
TW, TH, LAB = 960, 540, 40


def sheet(items, cols, path, tw=TW, th=TH):
    rows = (len(items) + cols - 1) // cols
    im = Image.new("RGB", (cols * tw, rows * (th + LAB)), "#202020")
    dr = ImageDraw.Draw(im)
    for i, (name, f) in enumerate(items):
        x, y = (i % cols) * tw, (i // cols) * (th + LAB)
        im.paste(Image.open(f).convert("RGB").resize((tw, th)), (x, y + LAB))
        dr.text((x + 10, y + 6), name, fill="#F4EFE6", font=F)
    im.save(path, quality=86)
    print("sheet", path.name, len(items))


if len(sys.argv) > 1 and sys.argv[1] == "M":
    ts = (0.2, 0.45, 0.7, 1.0)
    items = [(f"{n} @ {t}", D / "png" / "anim" / f"{n}@{t:.2f}.jpg") for n in sys.argv[2:] for t in ts]
    sheet(items, 4, OUT / "M_1.jpg", 480, 270)
else:
    pngs = sorted((D / "png").glob("*.jpg"))
    for k in range(0, len(pngs), 6):
        sheet([(p.stem, p) for p in pngs[k:k + 6]], 2, OUT / f"V1_{k // 6 + 1}.jpg")
