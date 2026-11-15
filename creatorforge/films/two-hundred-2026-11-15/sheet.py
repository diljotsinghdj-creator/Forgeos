"""Contact sheet: python3 sheet.py OUT.jpg pattern [pattern...] (3 columns, 640x360 tiles; 9:16 frames letterboxed)."""
import glob, sys
from PIL import Image, ImageDraw
out, pats = sys.argv[1], sys.argv[2:]
fs = [f for p in pats for f in sorted(glob.glob(f"png/{p}.jpg"))]
W, H, cols = 640, 360, 3
sh = Image.new("RGB", (W * cols, H * ((len(fs) + cols - 1) // cols)), "white"); d = ImageDraw.Draw(sh)
for i, f in enumerate(fs):
    im = Image.open(f); im.thumbnail((W, H)); x, y = (i % cols) * W, (i // cols) * H
    sh.paste(im, (x + (W - im.width) // 2, y + (H - im.height) // 2)); d.rectangle((x, y, x + 200, y + 14), fill="black"); d.text((x + 3, y + 1), f.split("/")[-1][:34], fill="yellow")
sh.save(out, quality=85); print(len(fs))
