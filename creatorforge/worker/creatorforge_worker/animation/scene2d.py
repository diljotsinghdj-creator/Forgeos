"""Scenes: a camera, depth layers (parallax), characters and animals, rendered frame by frame to MP4.

Depth works like a real camera moving sideways: a layer at depth z moves 1/z as fast as the ground the characters
stand on and is drawn 1/z the size, with haze increasing with distance. Background layers are painted once as wide
strips at full resolution and slid per frame, so detailed environments stay fast. Frames are drawn at twice the
output size and downscaled (clean anti-aliased lines)."""
from __future__ import annotations

import math
import random
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import rig2d
from .rig2d import smooth


def lerp(a, b, k):
    return a + (b - a) * k


def mixc(a, b, k):
    return tuple(int(lerp(x, y, k)) for x, y in zip(a, b))


@dataclass
class CamKey:
    t: float
    x: float
    y: float = 0.0
    zoom: float = 1.0
    follow: object = None      # a character/animal to track (x offset = x)
    ease: str = "smooth"       # how the camera arrives at this key: "smooth" (eased) or "linear" (dense director keys)


@dataclass
class Layer:
    z: float
    paint: object               # paint(draw, width_px, height_px, world_left, scale, ground_y) on a strip
    span: tuple = (-30.0, 30.0)
    _img: object = None


@dataclass
class Scene:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    ss: int = 2
    ppm: float = 260.0             # pixels per metre at z=1 (output size)
    ground: float = 0.82           # screen fraction where z=1 ground sits
    horizon: float = 0.52
    sky: tuple = ((120, 170, 230), (240, 220, 190))
    floor: tuple | None = None     # ground colour below z=1 line (None: drawn by layers)
    layers: list = field(default_factory=list)       # behind the actors
    front: list = field(default_factory=list)        # in front of the actors
    actors: list = field(default_factory=list)       # Character / Camel
    extras: list = field(default_factory=list)       # Bird etc. (drawn at z=1 sky)
    cams: list = field(default_factory=list)
    audio: list = field(default_factory=list)        # (start, wav)
    overlay: object = None                           # overlay(draw, W, H, t) - titles, captions
    sun: tuple | None = None                         # (screen x frac, screen y frac, radius frac, colour)
    shake: list = field(default_factory=list)        # (t0, t1, amount px)
    shadow_dir: float = 0.25
    motion_blur: int = 0                             # sub-frames averaged per frame (180-degree shutter); 0 = off

    # ---- camera -------------------------------------------------------------------------------------------------
    def camera(self, t: float):
        if not self.cams:
            return 0.0, 0.0, 1.0
        keys = sorted(self.cams, key=lambda k: k.t)

        def pos(k):
            if k.follow is not None:
                return k.follow_x(t) + k.x if hasattr(k, "follow_x") else _actor_x(k.follow, t) + k.x
            return k.x
        if t <= keys[0].t:
            k = keys[0]
            return pos(k), k.y, k.zoom
        for a, b in zip(keys, keys[1:]):
            if a.t <= t <= b.t:
                u = (t - a.t) / max(1e-3, b.t - a.t)
                u = u if b.ease == "linear" else smooth(u)
                return lerp(pos(a), pos(b), u), lerp(a.y, b.y, u), lerp(a.zoom, b.zoom, u)
        k = keys[-1]
        return pos(k), k.y, k.zoom

    # ---- painting -----------------------------------------------------------------------------------------------
    def _strip(self, L: Layer):
        if L._img is None:
            W, H = self.width * self.ss, self.height * self.ss
            scale = self.ppm * self.ss / L.z
            left, right = L.span
            sw = int((right - left) * scale)
            img = Image.new("RGBA", (sw, H), (0, 0, 0, 0))
            gy = self._ground_px(L.z)
            L.paint(ImageDraw.Draw(img, "RGBA"), sw, H, left, scale, gy)
            L._img = img
        return L._img

    def _ground_px(self, z: float) -> float:
        H = self.height * self.ss
        hz, gy = self.horizon * H, self.ground * H
        return hz + (gy - hz) / z

    def _sky(self):
        if not hasattr(self, "_sky_img"):
            W, H = self.width * self.ss, self.height * self.ss
            img = Image.new("RGB", (W, H))
            d = ImageDraw.Draw(img)
            top, bot = self.sky
            hz = int(self.horizon * H)
            for y in range(H):
                d.line([(0, y), (W, y)], fill=mixc(top, bot, min(1.0, y / max(1, hz))))
            if self.sun:
                sx, sy, sr, col = self.sun
                glow = Image.new("L", (W, H), 0)
                gd = ImageDraw.Draw(glow)
                cx, cy, r = sx * W, sy * H, sr * H
                gd.ellipse([cx - r * 4, cy - r * 4, cx + r * 4, cy + r * 4], fill=110)
                glow = glow.filter(ImageFilter.GaussianBlur(r * 1.6))
                img.paste(col, mask=glow)
                d = ImageDraw.Draw(img)
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mixc(col, (255, 255, 240), 0.6))
            self._sky_img = img
        return self._sky_img.copy()

    def frame(self, t: float, dt: float) -> Image.Image:
        W, H, ss = self.width * self.ss, self.height * self.ss, self.ss
        cx, cy, zoom = self.camera(t)
        img = self._sky()
        if getattr(self, "backdrop", None):           # a real photograph as the world the characters walk in
            img = _backdrop(img, self.backdrop, t)
        for L in sorted(self.layers, key=lambda q: -q.z):
            strip = self._strip(L)
            scale = self.ppm * ss / L.z
            off = int((cx - L.span[0]) * scale - W / 2)
            img.paste(strip.crop((off, 0, off + W, H)), (0, int(cy * self.ppm * ss / L.z)), strip.crop((off, 0, off + W, H)))
        d = ImageDraw.Draw(img, "RGBA")
        if self.floor:
            pass
        for a in self.actors:
            a.step(t, dt)

        def to_screen_z(z):
            scale = self.ppm * ss / z
            gy = self._ground_px(z) + cy * scale

            def S(x, y):
                return W / 2 + (x - cx) * scale, gy - y * scale
            return S, scale
        S1, scale1 = to_screen_z(1.0)
        for e in self.extras:
            e.draw(d, S1, scale1, t)
        zs = {id(a): (a.z_at(t) if hasattr(a, "z_at") else getattr(a, "z", 1.0)) for a in self.actors}
        for a in sorted(self.actors, key=lambda q: -zs[id(q)]):
            if getattr(a, "no_shadow", False):
                continue
            S, scale = to_screen_z(zs[id(a)])
            ax = _actor_x(a, t)
            gnd = a.world.ground(ax) if getattr(a, "world", None) is not None else 0.0
            lift = getattr(a, "hip", (0, 0))[1] - gnd - (a.l_thigh + a.l_shin) if hasattr(a, "l_thigh") else 0.0
            w = (0.32 if hasattr(a, "l_thigh") else 1.35) * scale * max(0.45, 1 - max(0.0, lift) * 0.8)
            sx, sy = S(ax + self.shadow_dir * 0.2, gnd)
            d.ellipse([sx - w, sy - w * 0.12, sx + w, sy + w * 0.12], fill=(0, 0, 0, 55))
        for fn in getattr(self, "animated", []):     # living environments behind the cast (water, stars, cells)
            fn(d, W, H, to_screen_z, t, cx)
        style = getattr(self, "style", None)
        figures = []
        for a in sorted(self.actors, key=lambda q: -zs[id(q)]):
            S, scale = to_screen_z(zs[id(a)])
            try:
                a.style = style
            except AttributeError:
                pass
            if hasattr(a, "pose_now"):
                x_ = _actor_x(a, t)
                last = getattr(a, "_last_x", None)
                a._vx = (x_ - last[0]) / (t - last[1]) if last and t > last[1] else 0.0
                a._last_x = (x_, t)
            if isinstance(a, rig2d.Character):
                rig2d.draw(d, a, a.pose(t), S, scale, t)
            elif style is not None and style.shade > 0 and hasattr(a, "pose_now") and style.body != "stick":
                from . import cinematic                 # each figure on its own layer: shaded by its own silhouette
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                a.draw(ImageDraw.Draw(lay, "RGBA"), S, scale, t, overlays=False)
                shaded = cinematic.shade(lay, style, scale * a.H)
                img.paste(shaded, (0, 0), shaded)
                d = ImageDraw.Draw(img, "RGBA")
                figures.append((a, S, scale))
            elif hasattr(a, "pose_now"):
                a.draw(d, S, scale, t, overlays=style is None or style.body == "stick")
                if style is not None and style.body != "stick":
                    figures.append((a, S, scale))
            else:
                a.draw(d, S, scale, t)
        for fn in getattr(self, "animated_front", []):
            fn(d, W, H, to_screen_z, t, cx)
        if style is not None and style.speedlines:
            from . import cinematic
            cinematic.auto_speedlines(d, [a for a, *_ in figures], t, to_screen_z, 1.0)
        ui = None
        if figures:                                    # speech bubbles and symbols: on their own layer, ungraded
            ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            du = ImageDraw.Draw(ui, "RGBA")
            for a, S, scale in figures:
                a.draw(du, S, scale, t, body=False)
        for L in sorted(self.front, key=lambda q: -q.z):
            strip = self._strip(L)
            scale = self.ppm * ss / L.z
            off = int((cx - L.span[0]) * scale - W / 2)
            part = strip.crop((off, 0, off + W, H))
            img.paste(part, (0, int(cy * scale)), part)
        if getattr(self, "light", None) or getattr(self, "weather", None):
            img = _world_fx(img, self, t, to_screen_z, W, H)
        view = (0, 0, W, H)
        if zoom != 1.0 or self.shake:
            amt = sum(a * (1 - (t - t0) / (t1 - t0)) for t0, t1, a in self.shake if t0 <= t <= t1) * ss
            jx, jy = (math.sin(t * 61) * amt, math.cos(t * 47) * amt) if amt else (0, 0)
            if amt:                                   # shaking needs a margin: punch in just enough
                zoom = max(zoom, 1.0 + 2.2 * amt / min(W, H))
            zw, zh = W / zoom, H / zoom
            mx, my = (W - zw) / 2, (H - zh) / 2
            jx, jy = max(-mx, min(mx, jx)), max(-my, min(my, jy))
            box = (W / 2 - zw / 2 + jx, H / 2 - zh / 2 + jy, W / 2 + zw / 2 + jx, H / 2 + zh / 2 + jy)
            img = img.resize((W, H), Image.LANCZOS, box=box)
            if ui is not None:
                ui = ui.resize((W, H), Image.LANCZOS, box=box)
            view = box
        out = img.resize((self.width, self.height), Image.LANCZOS)
        out = _atmosphere(out, getattr(self, "moods", []), t)
        if style is not None:
            from . import cinematic
            out = cinematic.grade(out, style, t, int(round(t * self.fps)))
        if ui is not None:
            small = ui.resize((self.width, self.height), Image.LANCZOS)
            out.paste(small, (0, 0), small)
        if getattr(self, "comic", None):
            from . import cinematic

            def onscreen(x_, y_):                     # through the zoom/shake crop to output pixels
                return ((x_ - view[0]) * W / (view[2] - view[0]) / ss, (y_ - view[1]) * H / (view[3] - view[1]) / ss)

            def where(at):
                if isinstance(at, (list, tuple)):
                    S_, _ = to_screen_z(1.0)
                    return onscreen(*S_(*at))
                J = getattr(at, "_joints", None)
                if J:
                    S_, _ = to_screen_z(getattr(at, "z", 1.0))
                    x_, y_ = onscreen(*S_(*J["head"]))
                    return x_, y_ - 0.12 * self.height
                return None
            out = out.convert("RGBA")
            cinematic.comic_fx(out, self.comic, t, where, style)
            out = out.convert("RGB")
        if getattr(self, "backdrop", None) and self.backdrop.get("credit"):
            _credit(out, self.backdrop["credit"])
        if getattr(self, "tags", None):
            _tags(out, self.tags, t)
        if self.overlay:
            self.overlay(ImageDraw.Draw(out, "RGBA"), self.width, self.height, t)
        return out

    def resize(self, width: int, height: int):
        """Change the output size (e.g. 3840x2160 for 4K) keeping the same framing."""
        self.ppm *= height / self.height
        self.width, self.height = width, height
        self.__dict__.pop("_sky_img", None)
        for L in self.layers + self.front:
            L._img = None
        return self

    def _shot(self, t: float, dt: float, draw: bool = True):
        """One output frame at t: with motion blur, the average of sub-frames across half the frame interval."""
        n = max(1, self.motion_blur)
        if n == 1:
            return self.frame(t, dt) if draw else self._advance(t, dt)
        acc = None
        sub = 0.5 * dt / n
        for k in range(n):
            ts = t - 0.25 * dt + (k + 0.5) * sub
            if not draw:
                self._advance(ts, sub if k else dt - (n - 1) * sub)
                continue
            img = np.asarray(self.frame(ts, sub if k else dt - (n - 1) * sub), dtype=np.uint16)
            acc = img if acc is None else acc + img
        return None if not draw else Image.fromarray((acc // n).astype(np.uint8))

    def _advance(self, t: float, dt: float):
        for a in self.actors:
            a.step(t, dt)

    def render(self, out: Path, seconds: float, android: Path | None = None, audio_wav: Path | None = None,
               chunk: float = 8.0, resume: bool = True) -> Path:
        """Renders to `out` (high-quality master, H.264 High CRF 12) and optionally an Android copy (H.264 Main 4.0,
        AAC, fast start). Frames are written in chunks of `chunk` seconds; if a render is interrupted, running it again
        re-uses the chunks already finished (the characters are simulated through them, not redrawn)."""
        out = Path(out)
        parts = out.parent / (out.stem + "_parts")
        parts.mkdir(parents=True, exist_ok=True)
        n = int(round(seconds * self.fps))
        per = max(1, int(round(chunk * self.fps)))
        dt = 1.0 / self.fps
        files = []
        for c0 in range(0, n, per):
            c1 = min(n, c0 + per)
            part = parts / f"part_{c0:06d}_{c1:06d}.mp4"
            files.append(part)
            if resume and part.exists() and _frames(part) == c1 - c0:
                for i in range(c0, c1):
                    self._shot(i * dt, dt, draw=False)
                continue
            cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                   f"{self.width}x{self.height}", "-r", str(self.fps), "-i", "-",
                   "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-profile:v", "high", "-pix_fmt", "yuv420p",
                   "-tune", "animation", str(part)]
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            for i in range(c0, c1):
                p.stdin.write(self._shot(i * dt, dt).tobytes())
            p.stdin.close()
            if p.wait() != 0:
                part.unlink(missing_ok=True)
                raise RuntimeError("ffmpeg failed")
        lst = parts / "list.txt"
        lst.write_text("".join(f"file '{f.name}'\n" for f in files))
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst)]
        if audio_wav:                                 # exact length: -shortest drops the last frames with -c:v copy
            cmd += ["-i", str(audio_wav), "-map", "0:v", "-map", "1:a", "-af", "apad", "-c:a", "aac", "-b:a", "256k",
                    "-t", f"{(n - 0.5) / self.fps:.6f}"]
        subprocess.run(cmd + ["-c:v", "copy", "-movflags", "+faststart", str(out)], check=True)
        if android:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "libx264", "-profile:v", "main",
                            "-level", "4.0" if self.height <= 1080 else "5.1", "-preset", "medium", "-crf", "20",
                            "-maxrate", "8M" if self.height <= 1080 else "30M", "-bufsize", "16M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                            "-movflags", "+faststart", str(android)], check=True)
        return out


def _backdrop(img, bd, t):
    """The photo fills the frame (cover), drifting in slowly (zoom from bd['zoom'][0] to [1] over bd['dur'])."""
    from .props_draw import _image
    W, H = img.size
    pic = _image(bd["image"])
    z0, z1 = bd.get("zoom", (1.0, 1.08))
    z = z0 + (z1 - z0) * min(1.0, t / max(0.1, bd.get("dur", 10.0)))
    s_ = max(W / pic.width, H / pic.height) * z
    w, h = int(pic.width * s_), int(pic.height * s_)
    fx, fy = bd.get("focus", (0.5, 0.4))
    x0 = int(min(max(0, w * fx - W / 2), w - W))
    y0 = int(min(max(0, h * fy - H / 2), h - H))
    big = pic.resize((w, h), Image.LANCZOS)
    img.paste(big.crop((x0, y0, x0 + W, y0 + H)), (0, 0))
    if bd.get("dim"):
        img = Image.blend(img, Image.new("RGB", img.size, (20, 20, 26)), bd["dim"])
    return img


def _credit(img, text):
    from PIL import ImageFont
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(H * 0.024))
    w = d.textlength(text, font=f)
    d.rounded_rectangle([W * 0.02, H * 0.12, W * 0.02 + w + H * 0.03, H * 0.12 + H * 0.045], radius=H * 0.008,
                        fill=(10, 10, 14, 170))
    d.text((W * 0.02 + H * 0.015, H * 0.127), text, font=f, fill=(255, 255, 255))


GRADES = {"day": (1.0, 1.0, 1.0), "dawn": (1.04, 0.9, 0.8), "dusk": (1.0, 0.76, 0.6), "night": (0.34, 0.42, 0.68),
          "storm": (0.62, 0.66, 0.74)}


def _grade(keys, t):
    """Time-of-day colour at t from [(t, kind)], blended over 1.5 s; returns (rgb multipliers, darkness 0..1)."""
    keys = sorted(keys)
    cur = GRADES[keys[0][1]]
    for k, (tk, kind) in enumerate(keys):
        if t >= tk:
            prev = GRADES[keys[k - 1][1]] if k else GRADES[kind]
            u = min(1.0, (t - tk) / 1.5)
            cur = tuple(p + (c - p) * u for p, c in zip(prev, GRADES[kind]))
    dark = max(0.0, 1.0 - sum(cur) / 3)
    return cur, dark


def _world_fx(img, sc, t, to_screen_z, W, H):
    """Light and weather over the world (under the captions): the time of day grades the picture, lamps (any
    library asset with a 'light' part, or sc.lights) glow as it gets dark, rain/snow fall at the wind's slant,
    a storm flashes lightning. Particles are seeded per index, so a frame always looks the same (resumable)."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    dark = 0.0
    if getattr(sc, "light", None):
        g, dark = _grade(sc.light, t)
        a *= np.array(g, dtype=np.float32)
    if dark > 0.12:                                   # light sources
        lights = list(getattr(sc, "lights", []))
        for p in sc.actors:
            if getattr(p, "kind", "") == "shape":
                for part in p.data.get("parts", []):
                    if part.get("id") == "light" and part.get("shape") == "circle":
                        x, y, _ = p.pos(t)
                        lights.append((x + part["c"][0], y + part["c"][1], 2.6, (255, 214, 140), getattr(p, "z", 1.0)))
        if lights:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            add = np.zeros_like(a)
            for x, y, r, col, z in lights:
                S, scale = to_screen_z(z)
                sx, sy = S(x, y)
                rad = r * scale
                if sx < -rad or sx > W + rad:
                    continue
                f = np.clip(1.0 - np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2) / rad, 0, 1) ** 2
                add += f[..., None] * np.array(col, dtype=np.float32) * 0.55 * min(1.0, dark * 1.6)
            a = a + add * (1.2 - a / 255.0)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    for t0, t1, kind, k in getattr(sc, "weather", []):
        if not t0 <= t <= t1:
            continue
        w = min(1.0, (t - t0) / 1.0, (t1 - t) / 1.0) * k
        wind = getattr(sc, "wind", 0.0)
        if kind in ("rain", "storm"):
            n = int(260 * w * (W / 1920))
            for i in range(n):
                h = (i * 2654435761) % 4294967296 / 4294967296.0
                h2 = (i * 40503 + 17) % 9973 / 9973.0
                x0 = h * W * 1.2 - W * 0.1
                y0 = (h2 * H + t * H * 1.6) % (H * 1.1) - H * 0.05
                L = H * 0.035
                d.line([(x0, y0), (x0 + (wind + 0.12) * L, y0 + L)], fill=(205, 215, 235, int(150 * w)),
                       width=max(1, W // 960))
            if kind == "storm":                       # lightning: two quick flashes now and then
                ph = (t * 0.23) % 1.0
                if ph < 0.012 or 0.03 < ph < 0.04:
                    img = Image.blend(img, Image.new("RGB", img.size, (245, 248, 255)), 0.55 * w)
                    d = ImageDraw.Draw(img, "RGBA")
        elif kind == "snow":
            for i in range(int(160 * w * (W / 1920))):
                h = (i * 2654435761) % 4294967296 / 4294967296.0
                h2 = (i * 40503 + 17) % 9973 / 9973.0
                x0 = (h * W + math.sin(t * 0.8 + i) * W * 0.01 + wind * t * W * 0.05) % W
                y0 = (h2 * H + t * H * 0.12) % H
                r = max(1.5, W / 640) * (0.6 + h2)
                d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=(255, 255, 255, int(220 * w)))
        elif kind == "wind":                          # blown dust and leaves
            for i in range(int(40 * w * (W / 1920))):
                h = (i * 2654435761) % 4294967296 / 4294967296.0
                h2 = (i * 40503 + 17) % 9973 / 9973.0
                x0 = (h * W + t * W * 0.5 * (0.6 + h2)) % (W * 1.1) - W * 0.05
                y0 = H * (0.25 + 0.6 * h2) + math.sin(t * 3 + i) * H * 0.02
                d.line([(x0, y0), (x0 + W * 0.02, y0 + H * 0.004)], fill=(150, 130, 90, int(140 * w)),
                       width=max(1, W // 640))
    return img


def _atmosphere(img, moods, t):
    """Scene-wide mood: 'anxious' drains colour, darkens the edges and pulses like a heartbeat; 'calm' warms and
    softens. Eased in and out over half a second."""
    for t0, t1, mood in moods:
        if not (t0 <= t <= t1):
            continue
        w = min(1.0, (t - t0) / 0.5, (t1 - t) / 0.5)
        a = np.asarray(img, dtype=np.float32)
        H, W = a.shape[:2]
        if mood == "anxious":
            grey = a.mean(axis=2, keepdims=True)
            a = a + (grey - a) * 0.55 * w
            yy, xx = np.mgrid[0:H, 0:W]
            r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
            beat = 0.5 + 0.5 * max(0.0, math.sin(t * 2 * math.pi * 1.6)) ** 6
            v = np.clip((r - 0.55) / 0.6, 0, 1) * (0.55 + 0.2 * beat) * w
            a = a * (1 - v[..., None])
        elif mood == "calm":
            a = a * (1 - 0.12 * w) + np.array([255, 236, 200], dtype=np.float32) * 0.12 * w
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return img


def _tags(img, tags, t):
    """A persistent badge (Illustration / Satire / Reconstruction) top-right while that visual is on screen."""
    from PIL import ImageFont
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size
    shown = [lab for t0, t1, lab in tags if t0 <= t <= t1 and lab]
    for i, lab in enumerate(dict.fromkeys(shown)):
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(H * 0.026))
        w = d.textlength(lab.upper(), font=f)
        x1, y0 = W * 0.98, H * 0.035 + i * H * 0.06
        d.rounded_rectangle([x1 - w - H * 0.03, y0, x1, y0 + H * 0.048], radius=H * 0.01, fill=(180, 40, 40, 210))
        d.text((x1 - w - H * 0.015, y0 + H * 0.008), lab.upper(), font=f, fill=(255, 255, 255))


def _frames(path: Path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return int(r.stdout.strip().split(",")[0])
    except ValueError:
        return -1


def _actor_x(a, t):
    if hasattr(a, "hips_x"):
        return a.hips_x(t)
    return a.body_x(t)


# ---- environments ------------------------------------------------------------------------------------------------
def _ridge(rng, left, right, step, base, amp, rough=0.55):
    xs, ys = [], []
    x, y = left, base
    while x <= right + step:
        xs.append(x)
        y = base + amp * (0.5 * math.sin(x * 0.21 + rng.random()) + 0.35 * math.sin(x * 0.53) + rough * (rng.random() - 0.5))
        ys.append(y)
        x += step
    return list(zip(xs, ys))


def desert(scene: Scene, seed: int = 7):
    """Golden-hour desert: far violet mountains, warm mid ranges, dunes, rippled sand, rocks and scrub in front."""
    rng = random.Random(seed)
    scene.sky = ((70, 110, 185), (250, 196, 140))
    scene.sun = (0.78, 0.43, 0.05, (255, 210, 140))
    span = (-40.0, 60.0)
    haze = (246, 200, 160)

    def mountains(z, base, amp, col, step):
        pts = _ridge(rng, span[0] * 2, span[1] * 2, step, base, amp)

        def paint(d, w, h, left, scale, gy):
            poly = [((x - left) * scale, gy - y * scale) for x, y in pts]
            poly = [(0, h)] + [(max(-50, min(w + 50, x)), y) for x, y in poly] + [(w, h)]
            d.polygon(poly, fill=mixc(col, haze, min(0.75, z / 14)))
            for x, y in pts[::3]:                      # light on the sunny faces
                px, py = (x - left) * scale, gy - y * scale
                d.line([(px, py), (px + step * scale * 0.6, py + amp * scale * 0.5)],
                       fill=mixc(col, (255, 230, 190), 0.25) + (90,), width=max(2, int(scale * 0.05)))
        return paint
    scene.layers.append(Layer(14.0, mountains(14, 5.5, 4.5, (120, 95, 140), 2.2), span))
    scene.layers.append(Layer(7.0, mountains(7, 2.6, 2.4, (176, 112, 82), 1.6), span))

    def dunes(d, w, h, left, scale, gy):
        pts = [(x / 10, 0.55 + 0.45 * math.sin(x / 10 * 0.6 + 1.3) + 0.25 * math.sin(x / 10 * 1.7))
               for x in range(int(span[0] * 10), int(span[1] * 10))]
        poly = [(0, h)] + [((x - left) * scale, gy - y * scale) for x, y in pts] + [(w, h)]
        d.polygon(poly, fill=(226, 166, 104))
        for x, y in pts[::6]:
            px, py = (x - left) * scale, gy - y * scale
            d.line([(px, py + 6), (px + scale * 0.5, py + scale * 0.12)], fill=(240, 190, 130, 120),
                   width=max(2, int(scale * 0.03)))
    scene.layers.append(Layer(3.2, dunes, span))

    def ground(d, w, h, left, scale, gy):
        d.rectangle([0, gy - 2, w, h], fill=(236, 190, 128))
        for k in range(int(w / (scale * 0.6))):
            x = k * scale * 0.6 + rng.random() * scale * 0.4
            y = gy + rng.random() * (h - gy)
            d.arc([x - scale * 0.5, y - scale * 0.05, x + scale * 0.5, y + scale * 0.06], 200, 340,
                  fill=(214, 166, 104, 160), width=max(2, int(scale * 0.012)))
        for k in range(int((span[1] - span[0]) / 3)):
            x = (span[0] + k * 3 + rng.random() * 2.5 - left) * scale
            r = scale * (0.08 + rng.random() * 0.12)
            d.ellipse([x - r, gy - r * 0.5, x + r, gy + r * 0.45], fill=(150, 112, 80))
        for k in range(int((span[1] - span[0]) / 7)):
            x = (span[0] + k * 7 + rng.random() * 5 - left) * scale
            for b in range(7):
                a = math.pi * (1.1 + 0.8 * b / 6)
                d.line([(x, gy + 2), (x + math.cos(a) * scale * 0.35, gy + math.sin(a) * scale * 0.35)],
                       fill=(120, 100, 55), width=max(2, int(scale * 0.02)))
    scene.layers.append(Layer(1.0, ground, span))

    def fore(d, w, h, left, scale, gy):
        for k in range(int((span[1] - span[0]) / 5)):
            x = (span[0] + k * 5 + rng.random() * 3 - left) * scale
            y = h - rng.random() * scale * 0.2
            r = scale * (0.25 + rng.random() * 0.3)
            d.ellipse([x - r * 1.4, y - r, x + r * 1.4, y + r], fill=(122, 82, 52))
            d.ellipse([x - r * 1.0, y - r * 0.9, x + r * 0.6, y - r * 0.2], fill=(150, 104, 66))
    scene.front.append(Layer(0.55, fore, span))


def park(scene: Scene, seed: int = 4):
    """A city park: skyline, trees, a path, a bench and a lamp."""
    rng = random.Random(seed)
    scene.sky = ((110, 170, 235), (215, 235, 250))
    span = (-25.0, 25.0)

    def skyline(d, w, h, left, scale, gy):
        x = 0
        while x < w:
            bw = scale * (1.2 + rng.random() * 2.2)
            bh = scale * (3 + rng.random() * 9)
            col = mixc((120, 140, 170), (190, 205, 225), 0.55 + rng.random() * 0.2)
            d.rectangle([x, gy - bh, x + bw, gy], fill=col)
            for wy in range(int(gy - bh + scale * 0.5), int(gy - scale * 0.3), int(scale * 0.7)):
                for wx in range(int(x + scale * 0.3), int(x + bw - scale * 0.3), int(scale * 0.55)):
                    d.rectangle([wx, wy, wx + scale * 0.22, wy + scale * 0.3], fill=mixc(col, (255, 255, 255), 0.3))
            x += bw + scale * rng.random() * 0.3
    scene.layers.append(Layer(9.0, skyline, span))

    def trees(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.2, w, h], fill=(120, 175, 95))
        for k in range(int((span[1] - span[0]) / 2.6)):
            x = (span[0] + k * 2.6 + rng.random() * 1.5 - left) * scale
            d.rectangle([x - scale * 0.08, gy - scale * 1.4, x + scale * 0.08, gy], fill=(110, 80, 60))
            for b in range(5):
                bx = x + (rng.random() - 0.5) * scale * 1.0
                by = gy - scale * (1.6 + rng.random() * 0.9)
                r = scale * (0.55 + rng.random() * 0.35)
                d.ellipse([bx - r, by - r, bx + r, by + r], fill=mixc((70, 140, 70), (110, 170, 90), rng.random()))
    scene.layers.append(Layer(3.5, trees, span))

    def lawn(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.15, w, h], fill=(132, 190, 104))
        d.rectangle([0, gy - scale * 0.06, w, gy + scale * 0.28], fill=(222, 210, 185))
        for k in range(int(w / (scale * 0.12))):
            x = k * scale * 0.12 + rng.random() * scale * 0.1
            y = gy + scale * (0.4 + rng.random() * 1.3)
            d.line([(x, y), (x + scale * 0.03, y - scale * 0.08)], fill=(100, 160, 80), width=max(2, int(scale * 0.012)))
        bx = (3.6 - left) * scale                     # bench
        d.rectangle([bx - scale * 0.9, gy - scale * 0.5, bx + scale * 0.9, gy - scale * 0.42], fill=(140, 90, 55))
        d.rectangle([bx - scale * 0.9, gy - scale * 0.85, bx + scale * 0.9, gy - scale * 0.72], fill=(150, 98, 60))
        for lx in (-0.8, 0.8):
            d.rectangle([bx + lx * scale - scale * 0.04, gy - scale * 0.5, bx + lx * scale + scale * 0.04, gy],
                        fill=(60, 60, 65))
        lx = (-4.5 - left) * scale                    # lamp
        d.rectangle([lx - scale * 0.04, gy - scale * 3.0, lx + scale * 0.04, gy], fill=(55, 60, 70))
        d.ellipse([lx - scale * 0.2, gy - scale * 3.25, lx + scale * 0.2, gy - scale * 2.9], fill=(255, 235, 170))
    scene.layers.append(Layer(1.0, lawn, span))


def studio(scene: Scene, paper=(248, 245, 236)):
    """A clean paper set for minimalist explainers: soft vignette, a ground line, nothing else."""
    scene.sky = (paper, mixc(paper, (220, 214, 200), 0.6))
    span = (-25.0, 25.0)

    def floor(d, w, h, left, scale, gy):
        d.rectangle([0, gy, w, h], fill=mixc(paper, (205, 198, 182), 0.5))
        d.line([(0, gy), (w, gy)], fill=(60, 60, 64), width=max(2, int(scale * 0.012)))
    scene.layers.append(Layer(1.0, floor, span))
