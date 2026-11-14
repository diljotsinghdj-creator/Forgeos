"""Where a cut-out failed, turn the photo into a torn-edge card (RGBA) so the collage still reads as paper."""
import json, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
D = Path(__file__).resolve().parent
rec = json.loads((D / "data" / "assets.json").read_text())
for s, r in rec.items():
    if r.get("cut") is False:
        im = Image.open(D / "assets" / f"{s}.jpg").convert("RGB"); im.thumbnail((1400, 1400))
        w, h = im.size; rnd = random.Random(s)
        m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
        pts = [(x, rnd.randint(0, 18)) for x in range(0, w + 1, 24)] + [(w - rnd.randint(0, 18), y) for y in range(0, h + 1, 24)] + \
              [(x, h - rnd.randint(0, 18)) for x in range(w, -1, -24)] + [(rnd.randint(0, 18), y) for y in range(h, -1, -24)]
        d.polygon(pts, fill=255)
        im.putalpha(m.filter(ImageFilter.GaussianBlur(.8)))
        im.save(D / "assets" / f"{s}.png"); r["cut"] = "card"
        print("card", s)
(D / "data" / "assets.json").write_text(json.dumps(rec, indent=1))
