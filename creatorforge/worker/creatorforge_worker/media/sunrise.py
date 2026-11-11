"""Sunrise and time-zone maps: night shading computed from the real position of the Sun, sweeping across a country
while a clock runs (Pillow + NumPy, offline: Natural Earth outlines bundled in states.json / world.json).

    Sunrise: 21 June 2026 3:50 → 4:40 | IST 5.5 | pins: Dong, Arunachal Pradesh @97.02,28.17; Kutch, Gujarat @68.8,23.8 | title
        the night lifts off the map as the clock runs; each pin shows its own sunrise time once the Sun is up
    Zones: 89.87 | IST-I, UTC+5:30; IST-II, UTC+6:30 | title | note
        the country split at a meridian into two zones, each shaded and labelled

The Sun's elevation is the NOAA general solar position (the equations behind its solar calculator): sunrise at
elevation -0.833° (refraction and the Sun's radius). Only India is mapped for now (its states are bundled)."""
from __future__ import annotations

import json
import math
import re
import subprocess
from datetime import date
from functools import lru_cache
from pathlib import Path

FPS = 24
FONTS = Path(__file__).with_name("vendor") / "fonts"
BOX = (66.0, 6.0, 100.0, 37.6)          # India with its far north-east and the Andaman Islands
LAT0 = 22.0
NIGHT, PAPER, SEA, NEIGH, STATE, EDGE, INK, SUN = ("#13203B", "#F1E8D4", "#C9D8DF", "#E2DBCB", "#B8AC95", "#4A4032",
                                                    "#1B1B1B", "#F29E38")
MONTHS = {m: i + 1 for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"))}


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


@lru_cache(maxsize=16)
def _font(name: str, size: int):
    """A vendored webfont (woff2) as a TrueType font Pillow can draw, converted once."""
    from PIL import ImageFont
    src = FONTS / f"{name}.woff2"
    dst = Path.home() / ".cache" / "creatorforge" / "fonts" / f"{name}.ttf"
    if not dst.is_file():
        from fontTools.ttLib import TTFont
        dst.parent.mkdir(parents=True, exist_ok=True)
        f = TTFont(str(src))
        f.flavor = None
        f.save(str(dst))
    return ImageFont.truetype(str(dst), size)


# ---- the Sun -----------------------------------------------------------------------------------------------------------
def elevation(lon, lat, day: date, utc_hours: float):
    """Solar elevation in degrees (NOAA general solar position); lon/lat may be NumPy arrays."""
    import numpy as np
    n = day.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1 + (utc_hours - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
           - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = utc_hours * 60 + eqt + 4 * np.asarray(lon, dtype=float)
    ha = np.radians(tst / 4 - 180)
    la = np.radians(np.asarray(lat, dtype=float))
    cz = np.sin(la) * math.sin(dec) + np.cos(la) * math.cos(dec) * np.cos(ha)
    return np.degrees(np.arcsin(np.clip(cz, -1, 1)))


def sunrise(lon: float, lat: float, day: date, offset: float) -> float:
    """Local clock hours (UTC + offset) of sunrise, found by bisection on the morning side."""
    lo, hi = 0.0, 12.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if float(elevation(lon, lat, day, mid - offset)) > -0.833:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def clock(h: float) -> tuple[str, str]:
    h %= 24
    hh, mm = int(h), int(round((h - int(h)) * 60))
    if mm == 60:
        hh, mm = hh + 1, 0
    return f"{(hh % 12) or 12}:{mm:02d}", "AM" if hh % 24 < 12 else "PM"


# ---- parsing -------------------------------------------------------------------------------------------------------------
def _time(s: str) -> float | None:
    m = re.match(r"\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*$", s, re.I)
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if (m.group(3) or "").lower() == "pm" else 0) if m.group(3) else int(m.group(1))
    return h + int(m.group(2) or 0) / 60


def _pins(s: str) -> list[dict]:
    out = []
    for x in s.split(";"):
        m = re.match(r"\s*(.+?)\s*@\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*$", x)
        if m:
            out.append({"name": m.group(1).strip(), "lon": float(m.group(2)), "lat": float(m.group(3))})
    return out


def parse(kind: str, spec: str) -> dict | None:
    parts = [p.strip() for p in (spec or "").split("|")]
    opts = {k.strip().lower(): v.strip() for k, _, v in (p.partition(":") for p in parts[1:] if re.match(r"^\w+\s*:", p) and
                                                                       not re.match(r"^(ist|utc)", p, re.I))}
    plain = [p for p in parts[1:] if not (re.match(r"^\w+\s*:", p) and not re.match(r"^(ist|utc)", p, re.I))]
    if kind == "sunrise":
        m = re.match(r"\s*(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})\s+(.+?)\s*(?:(?:→|->|to)\s*(.+))?$", parts[0])
        if not m or m.group(2).lower() not in MONTHS:
            return None
        t0 = _time(m.group(4))
        t1 = _time(m.group(5)) if m.group(5) else t0            # one time: the clock stands still
        if t0 is None or t1 is None or t1 < t0:
            return None
        zone = next((p for p in plain if re.match(r"^[A-Z]{2,4}\s+[+-]?[\d.]+$", p)), "IST 5.5")
        name, off = zone.split()
        rest = [p for p in plain if p != zone]
        return {"type": "sunrise", "day": date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).isoformat(),
                "t0": t0, "t1": t1, "zone": name, "offset": float(off), "pins": _pins(opts.get("pins", "")),
                "clocks": _pins(opts.get("clocks", "")),
                "meridian": float(opts["meridian"]) if re.match(r"^[\d.]+$", opts.get("meridian", "")) else None,
                "title": rest[0] if rest else "", "note": rest[1] if len(rest) > 1 else ""}
    if kind == "zones":
        if not re.match(r"^[\d.]+$", parts[0]):
            return None
        names = [x.strip() for x in (plain[0].split(";") if plain else []) if x.strip()]
        if len(names) != 2:
            return None
        return {"type": "zones", "split": float(parts[0]), "names": names, "title": plain[1] if len(plain) > 1 else "",
                "note": plain[2] if len(plain) > 2 else ""}
    return None


# ---- drawing --------------------------------------------------------------------------------------------------------------
def _geometry(width: int, height: int):
    """Map placement: India fills the right of the frame (the clock and title take the left), equirectangular at 22°N."""
    k_lon = math.cos(math.radians(LAT0))
    w_deg, h_deg = (BOX[2] - BOX[0]) * k_lon, BOX[3] - BOX[1]
    tall = height > width
    area_w, area_h = (width * 0.96, height * 0.6) if tall else (width * 0.62, height * 0.9)
    s = min(area_w / w_deg, area_h / h_deg)
    ox = (width - w_deg * s) / 2 if tall else width * 0.36 + (width * 0.62 - w_deg * s) / 2
    oy = height * 0.36 if tall else (height - h_deg * s) / 2

    def xy(lon, lat):
        return ox + (lon - BOX[0]) * k_lon * s, oy + (BOX[3] - lat) * s
    return xy, s, (ox, oy, ox + w_deg * s, oy + h_deg * s)


@lru_cache(maxsize=1)
def _shapes():
    here = Path(__file__)
    states = json.loads(here.with_name("states.json").read_text(encoding="utf-8"))["India"]
    world = json.loads(here.with_name("world.json").read_text(encoding="utf-8"))["countries"]
    near = [c for c in world if c["n"] != "India" and any(BOX[0] - 8 < p[0] < BOX[2] + 8 and BOX[1] - 8 < p[1] < BOX[3] + 8
                                                         for r in c["r"] for p in r[::5])]
    return states, near


def _base(width: int, height: int, xy, zones: dict | None = None):
    from PIL import Image, ImageDraw
    states, near = _shapes()
    im = Image.new("RGB", (width, height), SEA)
    d = ImageDraw.Draw(im)
    for c in near:
        for r in c["r"]:
            if len(r) > 2:
                d.polygon([xy(*p) for p in r], fill=NEIGH, outline="#CFC6B3")
    for st in states:
        fill = PAPER
        if zones:
            cx = sum(p[0] for r in st["r"] for p in r) / max(1, sum(len(r) for r in st["r"]))
            fill = zones["east"] if cx > zones["split"] else zones["west"]
        for r in st["r"]:
            if len(r) > 2:
                d.polygon([xy(*p) for p in r], fill=fill, outline=STATE)
    return im


def _tag(d, text, x, y, font, fg, bg, anchor="lm", pad=None):
    pad = pad or max(4, font.size // 4)
    b = d.textbbox((x, y), text, font=font, anchor=anchor)
    d.rectangle([b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad], fill=bg)
    d.text((x, y), text, font=font, fill=fg, anchor=anchor)
    return b


def _title(d, text, width, height, tall):
    if not text:
        return
    f = _font("playfair-display-latin-900-normal", int(min(width, height) * (0.05 if tall else 0.046)))
    x, y = (width / 2, height * 0.07) if tall else (width * 0.05, height * 0.1)
    _tag(d, text.upper(), x, y, f, "#FFFFFF", INK, anchor="mm" if tall else "lm", pad=int(f.size * 0.35))


def _ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def _pipe(width, height, out: Path, fps: int = FPS):
    return subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-nostdin", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
                             "-vf", "noise=alls=5:allf=t+u,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
                             "-crf", "18", str(out)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def render(plan: dict, width: int, height: int, seconds: float, out: Path, fps: int = FPS) -> Path:
    import numpy as np
    from PIL import Image, ImageDraw
    tall = height > width
    xy, scale, (mx0, my0, mx1, my1) = _geometry(width, height)
    frames = max(2, int(round(max(1.5, seconds) * fps)))
    proc = _pipe(width, height, out, fps)
    U = min(width, height)
    small = _font("inter-latin-800-normal", int(U * 0.026))
    mono = _font("jetbrains-mono-latin-700-normal", int(U * 0.02))
    try:
        if plan["type"] == "zones":
            zcol = {"west": "#F1E8D4", "east": "#F6C77A", "split": plan["split"]}
            base = _base(width, height, xy, zcol)
            plain = _base(width, height, xy)
            for f in range(frames):
                t = f / (frames - 1)
                k = _ease((t - 0.08) / 0.25)                      # the proposed zones colour in, no pop
                im = Image.blend(plain, base, k) if k < 1 else base.copy()
                d = ImageDraw.Draw(im)
                gx, _ = xy(plan["split"], 0)
                grow = _ease(t / 0.35)
                y0, y1 = my0 + (my1 - my0) * 0.02, my0 + (my1 - my0) * (0.02 + 0.96 * grow)
                for y in np.arange(y0, y1, U * 0.02):
                    d.line([(gx, y), (gx, min(y1, y + U * 0.011))], fill=INK, width=max(2, U // 360))
                big = _font("anton-latin-400-normal", int(U * 0.05))
                a = int(255 * _ease((t - 0.3) / 0.2))
                if a > 0:
                    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
                    ld = ImageDraw.Draw(lay)
                    wx, wy = xy(77.5, 21.5)
                    ex, ey = xy(94.5, 23.6)
                    _tag(ld, plan["names"][0].upper(), wx, wy, big, INK, (255, 255, 255, 235), anchor="mm")
                    _tag(ld, plan["names"][1].upper(), gx + U * 0.03, my0 + (my1 - my0) * 0.62, big, "#FFFFFF", INK, anchor="lm")
                    lay.putalpha(lay.getchannel("A").point(lambda v: v * a // 255))
                    im.paste(lay, (0, 0), lay)
                    d = ImageDraw.Draw(im)
                    d.text((gx, my0 - U * 0.005), f"{int(plan['split'])}°{round(plan['split'] % 1 * 60):02d}′E",
                           font=mono, fill=INK, anchor="mb")
                _title(d, plan["title"], width, height, tall)
                if plan.get("note"):
                    d.text((width * 0.05, height * 0.93), plan["note"].upper(), font=mono, fill=INK, anchor="lm")
                proc.stdin.write(np.asarray(im, dtype=np.uint8).tobytes())
            return _finish(proc, out)

        day = date.fromisoformat(plan["day"])
        base = np.asarray(_base(width, height, xy), dtype=np.float32)
        # the borders stay drawn over the night, so the country reads at any hour
        states, near = _shapes()
        lines = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lines)
        for st in states:
            for r in st["r"]:
                if len(r) > 2:
                    ld.line([xy(*q) for q in r] + [xy(*r[0])], fill=(232, 224, 205, 70), width=1)
        for c in near:
            for r in c["r"]:
                if len(r) > 2:
                    ld.line([xy(*q) for q in r] + [xy(*r[0])], fill=(232, 224, 205, 45), width=1)
        land = Image.new("L", (width, height), 0)
        lnd = ImageDraw.Draw(land)
        for st in states:
            for r in st["r"]:
                if len(r) > 2:
                    lnd.polygon([xy(*q) for q in r], fill=255)
        india = np.asarray(land, dtype=np.float32)[..., None] / 255
        # the Sun is computed on a coarse grid of the frame (lon/lat per pixel), then smoothed up to full size
        gw, gh = width // 4, height // 4
        xs = (np.arange(gw) + 0.5) * width / gw
        ys = (np.arange(gh) + 0.5) * height / gh
        k_lon = math.cos(math.radians(LAT0))
        lons = BOX[0] + (xs - mx0) / (scale * k_lon)
        lats = BOX[3] - (ys - my0) / scale
        LON, LAT = np.meshgrid(lons, lats)
        night = np.array(_hex(NIGHT), dtype=np.float32)
        sun = np.array(_hex(SUN), dtype=np.float32)
        rises = [sunrise(p["lon"], p["lat"], day, plan["offset"]) for p in plan["pins"]]
        bigf = _font("anton-latin-400-normal", int(U * (0.15 if not tall else 0.12)))
        ampm = _font("anton-latin-400-normal", int(U * 0.05))
        dayf = _font("inter-latin-800-normal", int(U * 0.03))
        for f in range(frames):
            t = f / (frames - 1)
            h = plan["t0"] + (plan["t1"] - plan["t0"]) * min(1.0, max(0.0, (t - 0.05) / 0.62))   # the clock runs, then holds on the result
            el = elevation(LON, LAT, day, h - plan["offset"])
            a = np.clip((-el - 0.833 + 0.8) / 7.0, 0, 1) * 0.86             # civil twilight fades the night out
            glow = np.clip(1 - np.abs(el + 0.833) / 0.9, 0, 1) * 0.85       # the sunrise line, warm
            A = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((width, height), Image.BILINEAR), dtype=np.float32)[..., None] / 255
            G = np.asarray(Image.fromarray((glow * 255).astype(np.uint8)).resize((width, height), Image.BICUBIC), dtype=np.float32)[..., None] / 255
            frame = base * (1 - A) + night * A
            frame = frame * (1 - G * 0.55) + sun * (G * 0.55)
            frame = frame + india * A * 26                                 # land a shade lighter than sea at night
            im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
            im.paste(lines, (0, 0), lines)
            d = ImageDraw.Draw(im)
            if plan.get("meridian") is not None:
                gx, _ = xy(plan["meridian"], 0)
                for y in np.arange(my0, my1, U * 0.02):
                    d.line([(gx, y), (gx, y + U * 0.011)], fill="#FFFFFF", width=max(2, U // 400))
                _tag(d, f"{plan['meridian']}°E · {plan['zone']}", gx, my0 + U * 0.03, mono, INK, "#FFFFFF", anchor="mm")
            for p in plan.get("clocks", []):
                # one clock face per city, all reading the same time: lit where the Sun is up, dark where it is not
                px, py = xy(p["lon"], p["lat"])
                lit = float(elevation(p["lon"], p["lat"], day, h - plan["offset"])) > -0.833
                rad = U * 0.05
                face, hand = ("#FFFFFF", INK) if lit else (NIGHT, "#FFFFFF")
                d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=face, outline=SUN if lit else "#FFFFFF", width=max(3, U // 260))
                for k in range(12):                                   # the hour marks
                    q = math.radians(k * 30)
                    r0, r1 = rad * (0.72 if k % 3 else 0.62), rad * 0.86
                    d.line([(px + math.sin(q) * r0, py - math.cos(q) * r0), (px + math.sin(q) * r1, py - math.cos(q) * r1)],
                           fill=hand, width=max(2, U // (260 if k % 3 else 200)))
                ang_m = math.radians((h % 1) * 360 - 90)
                ang_h = math.radians(((h % 12) / 12) * 360 - 90)
                d.line([(px, py), (px + math.cos(ang_h) * rad * 0.5, py + math.sin(ang_h) * rad * 0.5)], fill=hand, width=max(4, U // 150))
                d.line([(px, py), (px + math.cos(ang_m) * rad * 0.78, py + math.sin(ang_m) * rad * 0.78)], fill=hand, width=max(3, U // 220))
                _tag(d, p["name"].upper(), px, py + rad + U * 0.025, small, INK if lit else "#FFFFFF", "#FFFFFF" if lit else NIGHT, anchor="mm")
            for p, r in zip(plan["pins"], rises):
                px, py = xy(p["lon"], p["lat"])
                up = h >= r
                rad = U * 0.012
                d.ellipse([px - rad * 1.8, py - rad * 1.8, px + rad * 1.8, py + rad * 1.8], outline=SUN if up else "#FFFFFF", width=max(2, U // 300))
                d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=SUN if up else "#FFFFFF")
                left = p["lon"] < 80
                lx = px + (U * 0.04 if left else -U * 0.04)
                anchor = "lm" if left else "rm"
                _tag(d, p["name"].upper(), lx, py - U * 0.022, small, INK, "#FFFFFF", anchor=anchor)
                if up:
                    hh, ap = clock(r)
                    _tag(d, f"SUNRISE {hh} {ap}", lx, py + U * 0.03, small, INK, SUN, anchor=anchor)
            hh, ap = clock(h)
            if tall:
                cx, cy = width / 2, height * 0.2
                d.rounded_rectangle([width * 0.18, height * 0.12, width * 0.82, height * 0.3], radius=U * 0.02, fill=PAPER)
                d.text((cx, cy), hh, font=bigf, fill=INK, anchor="mm")
                d.text((cx, cy + U * 0.1), f"{ap} · {plan['zone']}", font=ampm, fill=INK, anchor="mm")
            else:
                cx, cy = width * 0.05, height * 0.42
                d.rounded_rectangle([cx - U * 0.03, height * 0.2, width * 0.3, height * 0.6], radius=U * 0.012, fill=PAPER)
                d.text((cx, cy), hh, font=bigf, fill=INK, anchor="ls")
                d.text((cx + U * 0.005, cy + U * 0.07), f"{ap} · {plan['zone']}", font=ampm, fill=INK, anchor="ls")
                d.text((cx + U * 0.005, cy + U * 0.13), day.strftime("%-d %B").upper(), font=dayf, fill="#5A5246", anchor="ls")
            _title(d, plan["title"], width, height, tall)
            d.text((width * 0.05, height * 0.95), (plan.get("note") or "SUN POSITIONS: NOAA SOLAR EQUATIONS").upper(),
                   font=mono, fill="#D9D2C2", anchor="lm")
            proc.stdin.write(np.asarray(im, dtype=np.uint8).tobytes())
        return _finish(proc, out)
    except BaseException:
        proc.kill()
        raise


def _finish(proc, out: Path) -> Path:
    proc.stdin.close()
    err = proc.stderr.read().decode(errors="replace")
    if proc.wait() != 0:
        from .ff import MediaError
        raise MediaError(f"sunrise render failed: {err[-400:]}")
    return out
