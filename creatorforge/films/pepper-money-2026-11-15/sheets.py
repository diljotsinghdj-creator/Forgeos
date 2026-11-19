"""Contact sheets for QA (2026-11-19, pass 5: less AI, more real):
  python3 sheets.py          -> sheets/V5_n.jpg (the film's frames in story order, 2 columns, 960x540, 6 per sheet)
  python3 sheets.py motion   -> sheets/M_5.jpg  (4 builds at t = 0.2 / 0.45 / 0.7 / 1.0, from png/anim/)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parent
S = D / "sheets"; S.mkdir(exist_ok=True)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
except Exception:
    font = ImageFont.load_default(size=22)

# the film in story order: (frame, beat label, kind) kind: R real material, M motion build, A AI plate
FILM = [
    ("01_jar", "1 HOOK · the pepper on your table", "R M"), ("02a_siege", "1 HOOK · Rome surrounded (real engraving)", "R M"),
    ("c02b_receipt", "1 HOOK · smash-zoom receipt", "R"), ("c02_ransom", "1 HOOK · ITEM 5: SEASONING", "R M"),
    ("03_title", "1 HOOK · title", "R M"), ("04_maptable", "2 CONTEXT · map table, Malabar", "R M"),
    ("05_three", "2 CONTEXT · one vine, three peppers", "R M"), ("s1_a", "2 CONTEXT · monsoon (start)", "R M"),
    ("08a_ship", "2 CONTEXT · the Portus relief ship", "R M"), ("s1_b", "2 CONTEXT · monsoon (crossing)", "R M"),
    ("s1_c", "2 CONTEXT · home loaded", "R M"), ("r1v", "2 CONTEXT · Pliny's words", "R"),
    ("06_pliny", "2 CONTEXT · Pliny's prices", "R M"), ("07_myth", "2 CONTEXT · MYTH: weight in gold", "R M"),
    ("r2v", "2 CONTEXT · 1 : 280", ""), ("08_drain", "2 CONTEXT · 50 million sesterces", "M"),
    ("c_r3v", "2 CONTEXT · Department of Pepper", "R"), ("09_papyrus", "2 CONTEXT · the receipt (papyrus)", "M"),
    ("10_rules", "3 MECHANICS · three rules of money", "R M"), ("10a_sack", "3 MECHANICS · a real sack of pepper", "R M"),
    ("c11_rents", "3 MECHANICS · rents + the trousers", "R M"), ("12_charter", "3 MECHANICS · Kent charter", "M"),
    ("s2_a", "3 MECHANICS · follow the price", "R M"), ("s2_b", "3 MECHANICS · Red Sea", "R M"),
    ("s2_c", "3 MECHANICS · ~25x by Europe", "R M"), ("c13_markup", "3 MECHANICS · markup on the map table", "R M"),
    ("13a_relay", "3 MECHANICS · relay race (animated map)", "R M"), ("13b_shift", "4 STAKES · the relay bypassed (animated map)", "R M"),
    ("s3_a", "4 STAKES · Gama leaves Lisbon", "R M"), ("s3_b", "4 STAKES · rounding the Cape", "R M"),
    ("c_s3_c", "4 STAKES · Calicut · unverified brag", "R M"), ("c14_fall", "4 STAKES · too much pepper + peppercorn law", "R M"),
    ("14a_demotion", "4 STAKES · the demotion (NGA grinder)", "R M"), ("15a_world", "5 SYNTHESIS · who grows it now (animated map)", "R M"),
    ("16_kochi", "5 SYNTHESIS · Kochi ₹695/kg", "R M"), ("17_end", "5 SYNTHESIS · the question", "R M"),
]


def sheet(items, out, cols=2):
    W, H, L = 960, 540, 40
    rows = (len(items) + cols - 1) // cols
    im = Image.new("RGB", (cols * W + (cols + 1) * 10, rows * (H + L) + 10), "#1A1A1A"); d = ImageDraw.Draw(im)
    for k, (name, path) in enumerate(items):
        x, y = 10 + (k % cols) * (W + 10), 10 + (k // cols) * (H + L)
        d.rectangle([x, y, x + W, y + L - 6], fill="#F7D046")
        im.paste(Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS), (x, y + L - 6))
        d.text((x + 6, y + 5), name, fill="#1A1A1A", font=font)
    im.save(out, quality=86); print("sheet", out.name)


if len(sys.argv) > 1 and sys.argv[1] == "motion":
    names = sys.argv[2:] or ["13a_relay", "13b_shift", "15a_world", "08a_ship"]
    items = [(f"{n} @ t={t}", D / "png" / "anim" / f"{n}@{t:.2f}.jpg") for n in names for t in (.2, .45, .7, 1.0)]
    sheet(items, S / "M_5.jpg", cols=4)
else:
    for i in range(0, len(FILM), 6):
        sheet([(f"{i + k + 1:02d} · {lab}", D / "png" / f"{n}.jpg") for k, (n, lab, _) in enumerate(FILM[i:i + 6])], S / f"V5_{i // 6 + 1}.jpg")
    n = len(FILM); r = sum("R" in k for *_, k in FILM); m = sum("M" in k for *_, k in FILM); ai = sum("A" in k for *_, k in FILM)
    print(f"frames {n} · AI {ai} · real material {r} ({100 * r / n:.0f}%) · motion builds {m}")
