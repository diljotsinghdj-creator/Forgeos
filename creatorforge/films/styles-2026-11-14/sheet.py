import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
D = Path(__file__).resolve().parent
F = "/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts/"
NAMES = {"map": "Route map", "globe": "Globe", "fly": "Fly-in (real OpenStreetMap)", "shade": "Shaded countries", "pinmap": "Pin on paper map",
         "route": "Dashed trade route", "clockmap": "Clock map", "heatmap": "Heat map", "arrows": "Movement arrows", "railmap": "Rail / corridor map",
         "sizemap": "True-size overlay", "borders": "Historical borders 1914 → today", "morph": "Zoom-morph", "shrink": "Shrinking shoreline",
         "wash": "State wash", "tiles": "Tile map", "mapdesk": "Map on a desk with props", "flowmap": "3D flow arcs (deck.gl)", "columns": "3D columns on a map",
         "dots": "Proportional dots", "zones": "Time-zone split", "sunrise": "Sunrise sweep (real solar position)", "terrain3d": "3D terrain",
         "satellite": "Satellite before / after"}


def sheet(group, title, cols=4, w=480, h=270):
    fs = sorted((D / group).glob("*.jpg"))
    lab = 34
    rows = (len(fs) + cols - 1) // cols
    s = Image.new("RGB", (cols * w, 70 + rows * (h + lab)), "#141414")
    d = ImageDraw.Draw(s)
    big = ImageFont.truetype(F + "space-grotesk-latin-700-normal.woff2", 30) if False else ImageFont.truetype(F.replace("vendor/fonts/", "vendor/fonts/") + "../fonts/space-grotesk-latin-700-normal.woff2", 30) if False else None
    try:
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    except OSError:
        big = small = ImageFont.load_default()
    d.text((20, 18), title + "   ·   STYLE SAMPLES, ILLUSTRATIVE DATA", fill="#FFDD33", font=big)
    for i, f in enumerate(fs):
        x, y = (i % cols) * w, 70 + (i // cols) * (h + lab)
        s.paste(Image.open(f).convert("RGB").resize((w - 6, h - 6)), (x + 3, y + 3))
        kind = f.stem.split("_", 1)[1]
        d.text((x + 8, y + h + 6), f"{f.stem[:3]}  {NAMES.get(kind, kind)}", fill="#EDEDED", font=small)
    return s


if __name__ == "__main__":
    group, title, out = sys.argv[1], sys.argv[2], sys.argv[3]
    sheet(group, title).save(D / out, quality=88)
