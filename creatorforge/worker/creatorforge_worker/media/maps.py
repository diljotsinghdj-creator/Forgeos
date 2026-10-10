"""Animated explainer maps (the documentary-map look): the camera eases in from a wide view to the place the line is
about, a country is filled in the highlight colour, cities get a pin and a label that drop in, and a route between
places draws itself on. Written in scripts as a "Map:" line:

    Map: France                          (country highlighted)
    Map: Hong Kong | where the call came (city pinned, optional title)
    Map: London → Paris                  (both pinned, route drawn between them)

Drawn as ASS vector shapes over a paper-tone sea with FFmpeg (no map tiles, works offline). Country shapes and city
positions: Natural Earth (public domain), bundled as world.json."""
from __future__ import annotations

import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from . import ff

THEMES = {
    # sea, land, border, highlight, pin, ink
    "editorial": ("0xD5E1E3", "0xF7F3EA", "0x9AA3A6", "0xF7D62B", "0xD6262B", "0x141414"),
    "investigative": ("0xB9C3B5", "0xEADFC4", "0x8C7F66", "0xC8102E", "0xC8102E", "0x1A1A1A"),
}


@lru_cache(maxsize=1)
def _world() -> dict:
    return json.loads((Path(__file__).with_name("world.json")).read_text(encoding="utf-8"))


def _norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower().replace("&", "and")).strip()


def _find(name: str) -> dict | None:
    """A country (its shapes) or a city (its position) by name."""
    key = _norm(name)
    if not key:
        return None
    aliases = {"uk": "united kingdom", "britain": "united kingdom", "great britain": "united kingdom",
               "england": "united kingdom", "usa": "united states of america", "us": "united states of america",
               "america": "united states of america", "united states": "united states of america"}
    key = aliases.get(key, key)
    w = _world()
    for c in w["countries"]:
        if key in {_norm(a) for a in c["a"]}:
            return {"kind": "country", "name": c["n"], "rings": c["r"]}
    best = None
    for name_, lat, lon, pop, country in w["places"]:
        if _norm(name_) == key and (best is None or pop > best[3]):
            best = (name_, lat, lon, pop)
    if best:
        return {"kind": "city", "name": best[0], "lat": best[1], "lon": best[2]}
    return None


def parse(spec: str) -> dict | None:
    head, _, title = spec.partition("|")
    names = [x.strip() for x in re.split(r"→|->|\bto\b", head) if x.strip()]
    found = [f for f in (_find(n) for n in names[:4]) if f]
    if not found:
        return None
    return {"targets": found, "route": len(found) >= 2 and len(re.findall(r"→|->|\bto\b", head)) >= 1,
            "title": title.strip()}


def _merc(lon: float, lat: float) -> tuple[float, float]:
    lat = max(-80.0, min(80.0, lat))
    return lon, math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def _bounds(targets: list[dict]) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for t in targets:
        if t["kind"] == "country":
            # frame the mainland: the largest shape (France without French Guiana, the US without Hawaii)
            area = lambda r: (max(p[0] for p in r) - min(p[0] for p in r)) * (max(p[1] for p in r) - min(p[1] for p in r))  # noqa: E731
            for ring in [max(t["rings"], key=area)]:
                for lon, lat in ring:
                    x, y = _merc(lon, lat)
                    xs.append(x)
                    ys.append(y)
        else:
            x, y = _merc(t["lon"], t["lat"])
            xs += [x - 4, x + 4]
            ys += [y - 3, y + 3]
    return min(xs), min(ys), max(xs), max(ys)


def _bgr(c: str) -> str:
    return f"&H00{c[6:8]}{c[4:6]}{c[2:4]}"


def _ts(t: float) -> str:
    return f"0:{int(t // 60):02d}:{t % 60:05.2f}"


def render(plan: dict, theme: str, width: int, height: int, seconds: float, out: Path, work: Path) -> Path:
    sea, land, border, hi, pin, ink = THEMES.get(theme, THEMES["editorial"])
    seconds = max(1.5, seconds)
    zoom_t = round(min(1.6, seconds * 0.45), 2)
    x0, y0, x1, y1 = _bounds(plan["targets"])
    # The final view: the targets with margin, fitted to the frame's shape (a little high on tall frames).
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    span_x = max(x1 - x0, 8.0) * 1.6
    span_y = max(y1 - y0, 6.0) * 1.6
    aspect = width / height
    if span_x / span_y < aspect:
        span_x = span_y * aspect
    else:
        span_y = span_x / aspect
    scale = width / span_x
    proj = lambda lon, lat: ((_merc(lon, lat)[0] - cx) * scale + width / 2,  # noqa: E731
                             height * (0.46 if height > width else 0.5) - (_merc(lon, lat)[1] - cy) * scale)
    start = 0.33                                                   # the camera starts 3x wider, then eases in
    wide = (span_x / start, span_y / start)
    hi_names = {t["name"] for t in plan["targets"] if t["kind"] == "country"}
    font = "Archivo Black"
    size = int(min(width, height) * 0.045)
    org = f"\\org({width / 2:.0f},{height * (0.46 if height > width else 0.5):.0f})"
    zoom = f"\\fscx{start * 100:.0f}\\fscy{start * 100:.0f}\\t(0,{int(zoom_t * 1000)},0.6,\\fscx100\\fscy100)"
    end = _ts(seconds)
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
             "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
             "MarginR, MarginV, Encoding",
             f"Style: M,DejaVu Sans,20,{_bgr(land)},{_bgr(land)},{_bgr(border)},&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
             f"Style: L,{font},{size},{_bgr(ink)},{_bgr(ink)},&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,{max(6, size // 4)},0,"
             f"5,0,0,0,1", "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    view = (cx - wide[0] / 2, cx + wide[0] / 2, cy - wide[1] / 2, cy + wide[1] / 2)
    for c in _world()["countries"]:
        shapes = []
        for ring in c["r"]:
            pts = [_merc(lon, lat) for lon, lat in ring]
            if max(p[0] for p in pts) < view[0] or min(p[0] for p in pts) > view[1] or \
                    max(p[1] for p in pts) < view[2] or min(p[1] for p in pts) > view[3]:
                continue
            xy = [proj(lon, lat) for lon, lat in ring]
            shapes.append(f"m {xy[0][0]:.0f} {xy[0][1]:.0f} l " + " ".join(f"{x:.0f} {y:.0f}" for x, y in xy[1:]))
        if not shapes:
            continue
        fill = hi if c["n"] in hi_names else land
        # highlighted countries fill in after the camera lands
        fx = f"\\1c{_bgr(land)}&\\t({int(zoom_t * 900)},{int(zoom_t * 1000) + 300},\\1c{_bgr(fill)}&)" if fill != land else ""
        lines.append(f"Dialogue: {2 if fill != land else 1},{_ts(0)},{end},M,,0,0,0,,{{\\an7\\pos(0,0){org}{zoom}"
                     f"\\p1\\bord{max(1, width // 900)}\\shad0\\3c{_bgr(border)}&{fx}}}{' '.join(shapes)}")
    cities = [t for t in plan["targets"] if t["kind"] == "city"]
    pts = [proj(t["lon"], t["lat"]) for t in cities]
    land_t = zoom_t + 0.15
    if plan["route"] and len(pts) >= 2:
        (ax, ay), (bx, by) = pts[0], pts[-1]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        nx, ny = -(by - ay), bx - ax                              # bow the route like a flight path
        cxp, cyp = mx + nx * 0.18, my + ny * 0.18 - abs(bx - ax) * 0.12
        curve = [((1 - t) ** 2 * ax + 2 * (1 - t) * t * cxp + t * t * bx, (1 - t) ** 2 * ay + 2 * (1 - t) * t * cyp + t * t * by)
                 for t in (i / 24 for i in range(25))]
        path = curve + curve[-2::-1]
        shape = f"m {path[0][0]:.0f} {path[0][1]:.0f} l " + " ".join(f"{x:.0f} {y:.0f}" for x, y in path[1:])
        lo, hi_x = (min(ax, bx), max(ax, bx))
        sweep = (f"\\clip({lo - 20:.0f},0,{lo - 19:.0f},{height})\\t({int(land_t * 1000)},{int((land_t + 0.9) * 1000)},"
                 f"\\clip({lo - 20:.0f},0,{hi_x + 20:.0f},{height})") if ax <= bx else \
                (f"\\clip({hi_x + 19:.0f},0,{hi_x + 20:.0f},{height})\\t({int(land_t * 1000)},{int((land_t + 0.9) * 1000)},"
                 f"\\clip({lo - 20:.0f},0,{hi_x + 20:.0f},{height})")
        lines.append(f"Dialogue: 3,{_ts(0)},{end},M,,0,0,0,,{{\\an7\\pos(0,0){sweep})\\p1\\bord{max(4, width // 320)}"
                     f"\\shad0\\1a&HFF&\\3c{_bgr(pin)}&\\blur0.6}}{shape}")
        land_t += 0.9
    for i, ((px, py), t) in enumerate(zip(pts, cities)):
        at = land_t if plan["route"] else zoom_t + 0.1 + i * 0.25
        r = max(9, int(min(width, height) * 0.014))
        dot = (f"m {px - r:.0f} {py:.0f} b {px - r:.0f} {py - r:.0f} {px + r:.0f} {py - r:.0f} {px + r:.0f} {py:.0f} "
               f"b {px + r:.0f} {py + r:.0f} {px - r:.0f} {py + r:.0f} {px - r:.0f} {py:.0f}")
        drop = f"\\fscx40\\fscy40\\t(0,160,\\fscx115\\fscy115)\\t(160,240,\\fscx100\\fscy100)\\org({px:.0f},{py:.0f})"
        lines.append(f"Dialogue: 4,{_ts(at)},{end},M,,0,0,0,,{{\\an7\\pos(0,0){drop}\\p1\\bord{max(3, r // 3)}\\shad0"
                     f"\\1c{_bgr(pin)}&\\3c&HFFFFFF&}}{dot}")
        side = 1 if px < width * 0.7 else -1
        lx = px + side * r * 2.2
        lines.append(f"Dialogue: 5,{_ts(at + 0.12)},{end},L,,0,0,0,,{{\\an{4 if side > 0 else 6}\\pos({lx:.0f},{py:.0f})"
                     f"\\fad(120,0)\\fs{int(size * 0.8)}}}{t['name'].upper()}")
    for t in plan["targets"]:
        if t["kind"] == "country" and not cities:
            bx0, by0, bx1, by1 = _bounds([t])
            px, py = proj(*_inv(((bx0 + bx1) / 2, (by0 + by1) / 2)))
            lines.append(f"Dialogue: 5,{_ts(zoom_t + 0.3)},{end},L,,0,0,0,,{{\\an5\\pos({px:.0f},{py:.0f})\\fad(150,0)}}"
                         f"{t['name'].upper()}")
    if plan.get("title"):
        lines.append(f"Dialogue: 6,{_ts(0.2)},{end},L,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{height * 0.08:.0f})"
                     f"\\fad(200,0)\\3c&H002BD6F7&\\4c&H002BD6F7&}}{plan['title'].upper()}")
    work.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines) + "\n"
    ass = work / f"map_{hashlib.sha256(text.encode()).hexdigest()[:12]}.ass"
    ass.write_text(text, encoding="utf-8")
    vf = (f"subtitles=filename='{ass}',noise=alls=7:allf=t+u,vignette=angle=PI/6,format=yuv420p")
    ff.run(["-f", "lavfi", "-i", f"color=c={sea}:s={width}x{height}:d={seconds:.2f}:r=30", "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
    return out


def _inv(xy: tuple[float, float]) -> tuple[float, float]:
    """Mercator (x, y) back to (lon, lat)."""
    x, y = xy
    return x, math.degrees(2 * math.atan(math.exp(math.radians(y))) - math.pi / 2)
