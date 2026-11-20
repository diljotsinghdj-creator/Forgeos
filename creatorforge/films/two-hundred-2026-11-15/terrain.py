"""Heightmaps from the open Terrarium elevation tiles (AWS Open Data; SRTM and other public sources, attribution:
Mapzen / Tilezen). Saves a 16-bit PNG height grid in Web Mercator for a lon/lat box, plus the box in mercator."""
import io, json, math, sys
from pathlib import Path
import httpx, numpy as np
from PIL import Image
D = Path(__file__).resolve().parent
def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y
def heights(name, box, z):
    lon0, lat0, lon1, lat1 = box
    x0, y1 = tile_xy(lon0, lat0, z); x1, y0 = tile_xy(lon1, lat1, z)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    W = (tx1 - tx0 + 1) * 256; H = (ty1 - ty0 + 1) * 256
    big = np.zeros((H, W), np.float32)
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            r = httpx.get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png", timeout=60)
            a = np.asarray(Image.open(io.BytesIO(r.content)).convert("RGB")).astype(np.float32)
            big[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    px0, px1 = int((x0 - tx0) * 256), int((x1 - tx0) * 256); py0, py1 = int((y0 - ty0) * 256), int((y1 - ty0) * 256)
    h = big[py0:py1, px0:px1]
    h = np.clip(h, 0, None)
    meta = {"box": box, "z": z, "w": h.shape[1], "h": h.shape[0], "min": float(h.min()), "max": float(h.max()),
            "source": "Terrarium elevation tiles (Mapzen/Tilezen via AWS Open Data; SRTM and others)"}
    norm = (h - h.min()) / max(1, h.max() - h.min())
    Image.fromarray((norm * 65535).astype(np.uint16)).save(D / "maps" / f"{name}_h.png")
    Image.fromarray((norm * 255).astype(np.uint8)).save(D / "maps" / f"{name}_h8.png")
    (D / "maps" / f"{name}_h.json").write_text(json.dumps(meta))
    print(name, h.shape, meta["min"], meta["max"])
if __name__ == "__main__":
    heights("alps", (7.3, 45.3, 10.6, 47.7), 9)
    heights("canyon", (-113.4, 35.9, -111.7, 36.6), 10)
