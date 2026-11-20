"""BiRefNet cut-out (studio cutouts module)."""
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
def cut(src: Path, out: Path):
    from PIL import Image
    from creatorforge_worker.media import cutouts
    with Image.open(src) as im:
        rgb = im.convert("RGB")
    rgb.thumbnail((1400, 1400))
    m = cutouts._mask(rgb, None, False)
    if m is None:
        return False
    bbox = m.point(lambda v: 255 if v > 128 else 0).getbbox()
    if not bbox:
        return False
    rgba = rgb.copy(); rgba.putalpha(m); rgba.crop(bbox).save(out)
    return True
