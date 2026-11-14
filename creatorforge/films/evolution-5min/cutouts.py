"""Fossil cut-outs: BiRefNet removes the background; the fossil keeps its real colour (nothing redrawn)."""
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
from PIL import Image, ImageFilter
from creatorforge_worker.media import cutouts
M = Path("/tmp/claude-0/-home-user-Forgeos/4511f341-cf91-5fed-ac10-e7043335b256/scratchpad/models/birefnet-lite.onnx")
A = Path(__file__).resolve().parent / "assets"
for name in sys.argv[1:]:
    src = next((A / (name + e) for e in (".jpg", ".png") if (A / (name + e)).exists()), None)
    if not src: print("missing", name); continue
    rgb = Image.open(src).convert("RGB"); rgb.thumbnail((1600, 1600))
    m = cutouts._mask(rgb, M, False)
    if m is None: print("no mask", name); continue
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    bb = m.point(lambda v: 255 if v > 128 else 0).getbbox()
    out = rgb.copy(); out.putalpha(m); out = out.crop(bb)
    out.save(A / f"{name}_cut.png"); print("cut", name, out.size, round(sum(1 for p in m.getdata() if p > 128) / (m.width * m.height), 2))
