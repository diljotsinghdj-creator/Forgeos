"""Sharp satellite base for small areas: EOX Sentinel-2 cloudless 2016 (s2maps.eu, CC BY 4.0; contains modified Copernicus
Sentinel data 2016). Tiles are stitched in Web Mercator and resampled to an equirectangular bbox like the GIBS images."""
import io, json, math, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx, numpy as np
from PIL import Image

D = Path(__file__).resolve().parent
URL = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg"
CREDIT = "IMAGERY: SENTINEL-2 CLOUDLESS 2016 BY EOX IT SERVICES (S2MAPS.EU), CONTAINS MODIFIED COPERNICUS SENTINEL DATA 2016, CC BY 4.0"
def mx(lon, z): return (lon + 180) / 360 * 2 ** z * 256
def my(lat, z): return (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2 ** z * 256
def tile(z, x, y):
    for _ in range(3):
        try:
            r = httpx.get(URL.format(z=z, x=x, y=y), timeout=60)
            if r.status_code == 200: return np.asarray(Image.open(io.BytesIO(r.content)).convert("RGB"))
        except Exception: pass
    return np.zeros((256, 256, 3), np.uint8)
def make(cid, bbox, W=2400):
    lon0, lat0, lon1, lat1 = bbox
    z = min(13, max(5, round(math.log2(W * 360 / (256 * (lon1 - lon0))))))
    x0, x1 = int(mx(lon0, z) // 256), int(mx(lon1, z) // 256); y0, y1 = int(my(lat1, z) // 256), int(my(lat0, z) // 256)
    big = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3), np.uint8)
    jobs = [(tx, ty) for tx in range(x0, x1 + 1) for ty in range(y0, y1 + 1)]
    with ThreadPoolExecutor(8) as ex:
        for (tx, ty), a in zip(jobs, ex.map(lambda t: tile(z, *t), jobs)):
            big[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = a
    H = round(W * (lat1 - lat0) / (lon1 - lon0) / math.cos(math.radians((lat0 + lat1) / 2)))
    xs = (np.array([mx(lon0 + (lon1 - lon0) * i / (W - 1), z) for i in range(W)]) - x0 * 256).astype(int).clip(0, big.shape[1] - 1)
    ys = (np.array([my(lat1 - (lat1 - lat0) * j / (H - 1), z) for j in range(H)]) - y0 * 256).astype(int).clip(0, big.shape[0] - 1)
    Image.fromarray(big[ys][:, xs]).save(D / "maps" / f"{cid}.jpg", quality=90)
    print(cid, z, len(jobs), "tiles", (W, H), flush=True)
if __name__ == "__main__":
    make("ganga", (76.5, 21.0, 93.5, 31.2))
