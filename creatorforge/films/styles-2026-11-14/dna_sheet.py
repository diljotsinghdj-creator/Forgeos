import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
D = Path(__file__).resolve().parent
kinds = ["seats", "table", "flowchart", "bignumber", "pyramid", "heatmap"]
dnas = ["classic"] + (sys.argv[1].split(",") if len(sys.argv) > 1 else ["blueprint", "riso", "noir"])
w, h, lab = 480, 270, 40
big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
s = Image.new("RGB", (len(dnas) * w, 70 + len(kinds) * h + lab), "#141414")
d = ImageDraw.Draw(s)
d.text((16, 16), "SAME SIX SCENE TYPES · CLASSIC LOOK vs THREE VISUAL DNAs · ILLUSTRATIVE DATA", fill="#FFDD33", font=big)
for j, dn in enumerate(dnas):
    d.text((j * w + 12, 70 - 4 + 8), dn.upper(), fill="#EDEDED", font=big)
for i, k in enumerate(kinds):
    for j, dn in enumerate(dnas):
        f = D / "dna" / f"{k}__{dn}.jpg"
        if f.is_file():
            s.paste(Image.open(f).convert("RGB").resize((w - 4, h - 4)), (j * w + 2, 70 + lab + i * h + 2))
s.save(D / (sys.argv[2] if len(sys.argv) > 2 else "dna_sheet.jpg"), quality=86)
