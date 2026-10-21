"""The globe fly-in (the documentary-map opener): a 3D globe turns until the place the line is about faces the
viewer, then the camera dives in until the country fills the frame; the country fills in the highlight colour,
cities get a pin, a route between places draws itself on as a great-circle arc. Written in scripts as a "Globe:" line:

    Globe: France                        (spin, dive, France highlighted)
    Globe: Hong Kong | where the call came
    Globe: London → New York             (both pinned, the route drawn between them)

Drawn frame by frame with Pillow (orthographic projection of the bundled Natural Earth shapes, the same world.json
the flat maps use) and encoded with FFmpeg - no map tiles, no GPU, works offline."""
from __future__ import annotations

import math
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from . import ff, maps

FPS = 30
THEMES = {
    # page, ocean, land, border, highlight, pin, ink, glow
    "editorial": ((239, 233, 220), (176, 201, 207), (247, 243, 234), (150, 160, 163), (247, 214, 43), (214, 38, 43),
                  (20, 20, 20), (255, 255, 255)),
    "investigative": ((214, 207, 190), (150, 166, 150), (234, 223, 196), (140, 127, 102), (200, 16, 46), (200, 16, 46),
                      (26, 26, 26), (245, 238, 220)),
}


_DEVANAGARI = re.compile(r"[\u0900-\u097F\uA8E0-\uA8FF]")


def script_of(text: str) -> str:
    """Which font family a label needs: "deva" for Hindi, "symbol" for ₹ and other signs the display font lacks."""
    if _DEVANAGARI.search(text or ""):
        return "deva"
    if any(ord(c) > 0x24F for c in text or ""):
        return "symbol"
    return "latin"


def font_file(kind: str = "latin") -> str:
    """The bold font file for a script: Archivo Black (Latin), DejaVu Sans Bold (₹ and signs), a Devanagari font
    (Lohit/Noto, installed on the pod) for Hindi. PIL has no font fallback, so the wrong one draws boxes."""
    names = {"latin": ("Archivo Black", "DejaVu Sans:bold"), "symbol": ("DejaVu Sans:bold",),
             "deva": (":lang=hi:weight=bold", ":lang=hi", "DejaVu Sans:bold")}[kind]
    for name in names:
        try:
            path = subprocess.run(["fc-match", "-f", "%{file}", name], capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        if not path:
            continue
        if name == "Archivo Black" and "Archivo" not in path:
            continue
        if name.startswith(":lang=hi") and not _covers(path, "\u0915"):
            continue
        return path
    return ""


@lru_cache(maxsize=16)
def _covers(path: str, ch: str) -> bool:
    try:
        from fontTools.ttLib import TTFont
        with TTFont(path, fontNumber=0, lazy=True) as f:
            return ord(ch) in (f.getBestCmap() or {})
    except ImportError:
        return True               # can't check: trust fontconfig's language match
    except Exception:  # noqa: BLE001 - unreadable font
        return False


@lru_cache(maxsize=24)
def _font_kind(size: int, kind: str):
    from PIL import ImageFont
    path = font_file(kind)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _font(size: int, text: str = ""):
    """The label font at `size`, chosen for the text it will draw (Hindi gets a Devanagari font)."""
    return _font_kind(size, script_of(text))


def _ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def _centre(targets: list[dict]) -> tuple[float, float, float]:
    """(lon, lat) the camera ends on, and the angular size (radians) of what it frames."""
    lons, lats = [], []
    for t in targets:
        if t["kind"] == "country":
            area = lambda r: (max(p[0] for p in r) - min(p[0] for p in r)) * (max(p[1] for p in r) - min(p[1] for p in r))  # noqa: E731
            ring = max(t["rings"], key=area)          # the mainland: France without French Guiana
            lons += [p[0] for p in ring]
            lats += [p[1] for p in ring]
        else:
            lons.append(t["lon"])
            lats.append(t["lat"])
    lon = (min(lons) + max(lons)) / 2
    lat = (min(lats) + max(lats)) / 2
    # never closer than a region: a lone city keeps its neighbours in view (and the coarse world shapes stay smooth)
    floor = 30.0 if all(t["kind"] == "city" for t in targets) and len(targets) == 1 else 12.0
    span = max((max(lons) - min(lons)) * math.cos(math.radians(lat)), max(lats) - min(lats), floor)
    return lon, lat, math.radians(span)


def _project(lon, lat, lon0, lat0, r, cx, cy):
    """Orthographic projection of numpy arrays; points on the far side are pulled onto the rim (so shapes that
    cross the horizon stay closed)."""
    import numpy as np
    la, lo = np.radians(lat), np.radians(lon - lon0)
    p0 = math.radians(lat0)
    x = np.cos(la) * np.sin(lo)
    y = math.cos(p0) * np.sin(la) - math.sin(p0) * np.cos(la) * np.cos(lo)
    vis = math.sin(p0) * np.sin(la) + math.cos(p0) * np.cos(la) * np.cos(lo)
    back = vis < 0
    if back.any():
        n = np.hypot(x[back], y[back]) + 1e-9
        x[back], y[back] = x[back] / n, y[back] / n
    return cx + r * x, cy - r * y, vis


def render(plan: dict, theme: str, width: int, height: int, seconds: float, out: Path, work: Path) -> Path:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    page, ocean, land, border, hi, pin, ink, glow = THEMES.get(theme, THEMES["editorial"])
    seconds = max(2.0, seconds)
    frames = int(round(seconds * FPS))
    tall = height > width
    cx, cy = width / 2, height * (0.40 if tall else 0.5)
    lon1, lat1, span = _centre(plan["targets"])
    lon0, lat0 = lon1 + 75.0, max(-30.0, min(40.0, lat1 * 0.4 + 10))     # starts a quarter-turn away
    r0 = min(width, height) * 0.40
    r1 = max(r0 * 1.2, min(width, height * 0.55) * 0.62 / max(span, 0.05))
    spin_end, dive_from, dive_end = 0.55, 0.30, 0.78                     # share of the clip
    hi_names = {t["name"] for t in plan["targets"] if t["kind"] == "country"}
    world = maps._world()
    shapes = []
    for c in world["countries"]:
        for ring in c["r"]:
            a = np.asarray(ring, dtype=float)
            if len(a) >= 3:
                shapes.append((c["n"] in hi_names, a[:, 0], a[:, 1]))
    grat = [(np.full(181, float(lo)), np.linspace(-90, 90, 181)) for lo in range(-180, 180, 30)]
    grat += [(np.linspace(-180, 180, 361), np.full(361, float(la))) for la in range(-60, 90, 30)]
    cities = [t for t in plan["targets"] if t["kind"] == "city"]
    every = str(plan)   # one font for all the labels, chosen for their script (Hindi, ₹ ...)
    label_font, title_font = _font(int(min(width, height) * 0.045), every), _font(int(min(width, height) * 0.05), every)
    work.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-nostdin", "-v", "error", "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(FPS), "-i", "-",
                             "-vf", "noise=alls=6:allf=t+u,vignette=angle=PI/6,format=yuv420p", "-c:v", "libx264",
                             "-preset", "veryfast", "-crf", "18", str(out)],
                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for f in range(frames):
            t = f / max(1, frames - 1)
            spin = _ease(t / spin_end)
            lon_c = lon0 + (lon1 - lon0) * spin
            lat_c = lat0 + (lat1 - lat0) * spin
            dive = _ease((t - dive_from) / (dive_end - dive_from))
            r = r0 * (r1 / r0) ** dive
            fill_in = _ease((t - dive_end + 0.06) / 0.12)
            im = Image.new("RGB", (width, height), page)
            d = ImageDraw.Draw(im)
            if r < max(width, height) * 1.5:          # the rim and its soft glow, while the globe still fits
                halo = Image.new("L", (width, height), 0)
                ImageDraw.Draw(halo).ellipse((cx - r * 1.04, cy - r * 1.04, cx + r * 1.04, cy + r * 1.04), fill=150)
                halo = halo.filter(ImageFilter.GaussianBlur(max(4, r * 0.05)))
                im.paste(Image.new("RGB", (width, height), glow), (0, 0), halo)
                d = ImageDraw.Draw(im)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ocean)
            for glon, glat in grat:
                x, y, vis = _project(glon, glat, lon_c, lat_c, r, cx, cy)
                pts = [(float(a), float(b)) for a, b, v in zip(x, y, vis) if v > 0]
                if len(pts) > 1:
                    d.line(pts, fill=tuple(int(o * 0.9 + 255 * 0.1) for o in ocean), width=max(1, width // 900))
            # thin borders on the whole globe, bolder once the camera is close
            line_w = max(1, int(min(width, height) / 700 * min(3.0, max(1.0, r / (min(width, height) * 1.2)))))
            for highlight, lo, la in shapes:
                x, y, vis = _project(lo, la, lon_c, lat_c, r, cx, cy)
                if vis.max() <= 0:
                    continue
                if x.max() < -50 or x.min() > width + 50 or y.max() < -50 or y.min() > height + 50:
                    continue
                col = land
                if highlight:
                    col = tuple(int(a + (b - a) * fill_in) for a, b in zip(land, hi))
                d.polygon(list(zip(x.tolist(), y.tolist())), fill=col)
                # borders only where the coast faces us (the far side, pulled onto the rim, gets no outline)
                run: list[tuple[float, float]] = []
                for px_, py_, v in zip(x.tolist(), y.tolist(), (vis > 0.12).tolist()):
                    if v:
                        run.append((px_, py_))
                    elif run:
                        if len(run) > 1:
                            d.line(run, fill=border, width=line_w)
                        run = []
                if len(run) > 1:
                    d.line(run + ([(float(x[0]), float(y[0]))] if vis[0] > 0.12 and vis[-1] > 0.12 else []), fill=border,
                           width=line_w)
            landed = fill_in > 0.01
            pts = []
            for c in cities:
                x, y, vis = _project(np.array([c["lon"]]), np.array([c["lat"]]), lon_c, lat_c, r, cx, cy)
                pts.append((float(x[0]), float(y[0]), float(vis[0]) > 0))
            if plan.get("route") and len(cities) >= 2 and landed:
                a, b = cities[0], cities[-1]
                n = 60
                k = max(1, int(n * _ease((t - dive_end) / 0.18)))
                lo_arc, la_arc = _great_circle(a["lon"], a["lat"], b["lon"], b["lat"], n)
                x, y, vis = _project(lo_arc[:k + 1], la_arc[:k + 1], lon_c, lat_c, r, cx, cy)
                if k >= 1:
                    d.line(list(zip(x.tolist(), y.tolist())), fill=pin, width=max(4, width // 260), joint="curve")
            for (x, y, vis), c in zip(pts, cities):
                if not vis or not landed:
                    continue
                pr = max(9, int(min(width, height) * 0.014)) * (0.4 + 0.6 * fill_in)
                d.ellipse((x - pr, y - pr, x + pr, y + pr), fill=pin, outline=(255, 255, 255), width=max(3, int(pr // 3)))
                if fill_in > 0.6:
                    _tag(d, c["name"].upper(), x + pr * 2.2 if x < width * 0.7 else x - pr * 2.2, y, label_font, ink,
                         right=x >= width * 0.7)
            if not cities and fill_in > 0.6:
                for tg in plan["targets"]:
                    lon_l, lat_l, _ = _centre([tg])
                    x, y, vis = _project(np.array([lon_l]), np.array([lat_l]), lon_c, lat_c, r, cx, cy)
                    if vis[0] > 0:
                        _tag(d, tg["name"].upper(), float(x[0]), float(y[0]), label_font, ink, centre=True)
            if plan.get("title") and t > 0.04:
                _banner(d, plan["title"].upper(), width / 2, height * 0.08, title_font, ink, hi)
            proc.stdin.write(im.tobytes())
        proc.stdin.close()
        proc.wait(timeout=600)
    except (BrokenPipeError, subprocess.TimeoutExpired) as e:
        proc.kill()
        raise ff.MediaError(f"globe render failed: {e}") from e
    if proc.returncode != 0:
        raise ff.MediaError(f"globe render failed: {(proc.stderr.read() if proc.stderr else b'').decode(errors='replace')[-400:]}")
    return out


def _great_circle(lon1, lat1, lon2, lat2, n):
    import numpy as np
    p1, p2 = np.radians([lat1, lat2])
    l1, l2 = np.radians([lon1, lon2])
    a = np.array([math.cos(p1) * math.cos(l1), math.cos(p1) * math.sin(l1), math.sin(p1)])
    b = np.array([math.cos(p2) * math.cos(l2), math.cos(p2) * math.sin(l2), math.sin(p2)])
    w = math.acos(max(-1.0, min(1.0, float(a @ b)))) or 1e-6
    ts = np.linspace(0, 1, n + 1)
    pts = (np.sin((1 - ts) * w)[:, None] * a + np.sin(ts * w)[:, None] * b) / math.sin(w)
    return np.degrees(np.arctan2(pts[:, 1], pts[:, 0])), np.degrees(np.arcsin(np.clip(pts[:, 2], -1, 1)))


def _tag(d, text, x, y, font, ink, right=False, centre=False):
    """A place name on a white label."""
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    w, h = r - l, b - t
    pad = max(6, h // 3)
    x0 = x - w / 2 if centre else (x - w if right else x)
    y0 = y - h / 2
    d.rectangle((x0 - pad, y0 - pad, x0 + w + pad, y0 + h + pad), fill=(255, 255, 255))
    d.text((x0 - l, y0 - t), text, font=font, fill=ink)


def _banner(d, text, x, y, font, ink, mark):
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    w, h = r - l, b - t
    pad = max(8, h // 3)
    d.rectangle((x - w / 2 - pad, y - pad, x + w / 2 + pad, y + h + pad), fill=mark)
    d.text((x - w / 2 - l, y - t), text, font=font, fill=ink)
