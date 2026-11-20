"""Sea routes: the way a ship actually goes. A route between two ports is found over a half-degree grid of the
oceans (land from the bundled Natural Earth outlines), through the Suez and Panama canals and the narrow straits,
keeping a little off the coasts. No network, no extra data.

    path("Shanghai port lon/lat", "Rotterdam lon/lat") -> [[lon, lat], ...]  (smoothed; [] when no sea way exists)
"""
from __future__ import annotations

import heapq
import math
from functools import lru_cache

STEP = 0.5
NX, NY = int(360 / STEP), int(180 / STEP)
JMIN, JMAX = int((90 - 68) / STEP), int((90 + 58) / STEP)      # rows between 68°N and 58°S
# water that a half-degree grid closes: canals and straits, as (lon, lat) cells to open
OPEN = [  # Suez canal and the Gulf of Suez
    *[(32.5, y / 2) for y in range(55, 64)], (32.75, 29.5), (33.0, 28.5), (33.25, 28.0), (33.5, 27.75),
    # Panama canal
    (-79.9, 9.4), (-79.75, 9.1), (-79.5, 8.9), (-79.5, 8.6),
    # Bosporus and Dardanelles
    (29.1, 41.2), (29.0, 41.0), (28.9, 40.9), (27.5, 40.6), (26.7, 40.4), (26.3, 40.1),
    (26.9, 40.7), (27.3, 40.7), (27.3, 40.3), (26.9, 40.3), (26.2, 40.3), (26.2, 39.8),
    # Malacca and Singapore straits
    (103.5, 1.2), (104.0, 1.25), (102.5, 2.0), (101.5, 2.6), (103.25, 1.5), (102.75, 1.75), (102.0, 2.25), (101.0, 2.9),
    # Bab-el-Mandeb, Hormuz, Gibraltar, Dover, Oresund
    (43.3, 12.6), (43.5, 12.4), (56.4, 26.5), (-5.6, 35.95), (-5.3, 36.0), (1.4, 51.0), (12.7, 55.7), (12.8, 56.0)]


def _cell(lon: float, lat: float) -> tuple[int, int]:
    return int((lon + 180) / STEP) % NX, min(NY - 1, max(0, int((90 - lat) / STEP)))


def _centre(i: int, j: int) -> tuple[float, float]:
    return -180 + (i + .5) * STEP, 90 - (j + .5) * STEP


@lru_cache(maxsize=1)
def _grid():
    """(water mask, coast mask): numpy bool arrays [NY, NX]."""
    import numpy as np
    from PIL import Image, ImageDraw
    from . import maps
    k = 4                                              # draw finer, then a cell is land when most of it is
    im = Image.new("L", (NX * k, NY * k), 0)
    d = ImageDraw.Draw(im)
    for c in maps._world()["countries"]:
        for r in c["r"]:
            if len(r) >= 3:
                d.polygon([((x + 180) / STEP * k, (90 - y) / STEP * k) for x, y in r], fill=255)
    land = np.asarray(im.resize((NX, NY), Image.BOX), np.float32) > 110
    water = ~land
    for lon, lat in OPEN:
        i, j = _cell(lon, lat)
        water[j, i] = True
    near = np.zeros_like(water)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            near |= ~np.roll(np.roll(water, dj, 0), di, 1)
    return water, near & water


def _snap(i: int, j: int, water) -> tuple[int, int] | None:
    """The nearest water cell to a port (ports sit on land cells)."""
    for r in range(0, 14):
        best = None
        for dj in range(-r, r + 1):
            for di in range(-r, r + 1):
                if max(abs(di), abs(dj)) != r:
                    continue
                jj, ii = j + dj, (i + di) % NX
                if 0 <= jj < NY and water[jj, ii]:
                    d2 = di * di + dj * dj
                    if best is None or d2 < best[0]:
                        best = (d2, ii, jj)
        if best:
            return best[1], best[2]
    return None


@lru_cache(maxsize=256)
def path(lon1: float, lat1: float, lon2: float, lat2: float) -> tuple[tuple[float, float], ...]:
    water, coast = _grid()
    a, b = _snap(*_cell(lon1, lat1), water), _snap(*_cell(lon2, lat2), water)
    if a is None or b is None:
        return ()

    def h(i, j):
        x1, y1 = _centre(i, j)
        x2, y2 = _centre(*b)
        dx = min(abs(x1 - x2), 360 - abs(x1 - x2)) * math.cos(math.radians((y1 + y2) / 2))
        return math.hypot(dx, y1 - y2)

    best = {a: 0.0}
    came: dict = {}
    heap = [(h(*a), 0.0, a)]
    while heap:
        _, g, cur = heapq.heappop(heap)
        if cur == b:
            break
        if g > best.get(cur, 1e18):
            continue
        i, j = cur
        kx = max(.08, math.cos(math.radians(90 - (j + .5) * STEP)))
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            jj, ii = j + dj, (i + di) % NX
            if not (JMIN <= jj <= JMAX) or not water[jj, ii]:      # ships don't cross the polar ice
                continue
            step = math.hypot(di * kx, dj) * STEP * (1.6 if coast[jj, ii] else 1.0)   # sea room, but straits stay open
            ng = g + step
            if ng < best.get((ii, jj), 1e18):
                best[(ii, jj)] = ng
                came[(ii, jj)] = cur
                heapq.heappush(heap, (ng + h(ii, jj), ng, (ii, jj)))
    if b not in came and a != b:
        return ()
    cells = [b]
    while cells[-1] != a:
        cells.append(came[cells[-1]])
    pts = [_centre(i, j) for i, j in reversed(cells)]
    # unwrap across the date line so the line doesn't jump the whole map
    out = [pts[0]]
    for x, y in pts[1:]:
        px = out[-1][0]
        while x - px > 180:
            x -= 360
        while x - px < -180:
            x += 360
        out.append((x, y))
    end = lon2
    while end - out[-1][0] > 180:
        end -= 360
    while end - out[-1][0] < -180:
        end += 360
    out = [(lon1, lat1)] + out[1:-1:3] + [(end, lat2)] if len(out) > 6 else [(lon1, lat1), (end, lat2)]
    for _ in range(2):                                 # round the grid's corners
        sm = [out[0]]
        for p, q in zip(out, out[1:]):
            sm += [(p[0] * .75 + q[0] * .25, p[1] * .75 + q[1] * .25), (p[0] * .25 + q[0] * .75, p[1] * .25 + q[1] * .75)]
        out = sm + [out[-1]]
    return tuple((round(x, 2), round(y, 2)) for x, y in out)


def crosses_land(pts) -> float:
    """Share of a path's points that lie on land (0 = all at sea), ends ignored."""
    water, _ = _grid()
    mid = list(pts)[3:-3]
    if not mid:
        return 0.0
    return sum(1 for x, y in mid if not water[_cell(x, y)[1], _cell(x, y)[0]]) / len(mid)
