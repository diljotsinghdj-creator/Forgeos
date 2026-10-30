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
                u = smooth((t - a.t) / max(1e-3, b.t - a.t))
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
        for a in sorted(self.actors, key=lambda q: -getattr(q, "z", 1.0)):
            if getattr(a, "no_shadow", False):
                continue
            S, scale = to_screen_z(getattr(a, "z", 1.0))
            ax = _actor_x(a, t)
            gnd = a.world.ground(ax) if getattr(a, "world", None) is not None else 0.0
            lift = getattr(a, "hip", (0, 0))[1] - gnd - (a.l_thigh + a.l_shin) if hasattr(a, "l_thigh") else 0.0
            w = (0.32 if hasattr(a, "l_thigh") else 1.35) * scale * max(0.45, 1 - max(0.0, lift) * 0.8)
            sx, sy = S(ax + self.shadow_dir * 0.2, gnd)
            d.ellipse([sx - w, sy - w * 0.12, sx + w, sy + w * 0.12], fill=(0, 0, 0, 55))
        for a in sorted(self.actors, key=lambda q: -getattr(q, "z", 1.0)):
            S, scale = to_screen_z(getattr(a, "z", 1.0))
            if isinstance(a, rig2d.Character):
                rig2d.draw(d, a, a.pose(t), S, scale, t)
            else:
                a.draw(d, S, scale, t)
        for L in sorted(self.front, key=lambda q: -q.z):
            strip = self._strip(L)
            scale = self.ppm * ss / L.z
            off = int((cx - L.span[0]) * scale - W / 2)
            part = strip.crop((off, 0, off + W, H))
            img.paste(part, (0, int(cy * scale)), part)
        if zoom != 1.0 or self.shake:
            amt = sum(a * (1 - (t - t0) / (t1 - t0)) for t0, t1, a in self.shake if t0 <= t <= t1) * ss
            jx, jy = (math.sin(t * 61) * amt, math.cos(t * 47) * amt) if amt else (0, 0)
            zw, zh = W / zoom, H / zoom
            box = (W / 2 - zw / 2 + jx, H / 2 - zh / 2 + jy, W / 2 + zw / 2 + jx, H / 2 + zh / 2 + jy)
            img = img.resize((W, H), Image.LANCZOS, box=box)
        out = img.resize((self.width, self.height), Image.LANCZOS)
        if self.overlay:
            self.overlay(ImageDraw.Draw(out, "RGBA"), self.width, self.height, t)
        return out

    def render(self, out: Path, seconds: float, android: Path | None = None, audio_wav: Path | None = None) -> Path:
        """Renders to `out` (high-quality master, H.264 High CRF 12) and optionally an Android copy (H.264 Main 4.0,
        1080p, AAC, fast start)."""
        out = Path(out)
        n = int(round(seconds * self.fps))
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
               f"{self.width}x{self.height}", "-r", str(self.fps), "-i", "-"]
        if audio_wav:
            cmd += ["-i", str(audio_wav)]
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "12", "-profile:v", "high", "-pix_fmt", "yuv420p",
                "-tune", "animation"]
        if audio_wav:
            cmd += ["-c:a", "aac", "-b:a", "256k", "-shortest"]
        cmd += ["-movflags", "+faststart", str(out)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        dt = 1.0 / self.fps
        for i in range(n):
            p.stdin.write(self.frame(i * dt, dt).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg failed")
        if android:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "libx264", "-profile:v", "main",
                            "-level", "4.0", "-preset", "medium", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                            "-movflags", "+faststart", str(android)], check=True)
        return out


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
