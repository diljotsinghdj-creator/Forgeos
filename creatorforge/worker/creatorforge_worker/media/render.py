"""Smart Editor / Auto Edit: assembles scene stills, narration, music, transitions, captions
and overlays into the final H.264/AAC MP4 with FFmpeg."""
from __future__ import annotations

import hashlib
import threading
import wave
from dataclasses import dataclass
from pathlib import Path

from . import ff

FPS = 30
TRANSITION_S = 0.5  # longest transition; also the tail after the last scene
# Editorial transition vocabulary used by templates and Auto Edit -> (FFmpeg xfade, seconds).
TRANSITIONS = {
    "cut": ("fade", 0.08), "fade": ("fade", 0.5), "dissolve": ("dissolve", 0.5), "dip": ("fadeblack", 0.5),
    "flash": ("fadewhite", 0.3), "slide": ("slideleft", 0.4), "wipe": ("wipeleft", 0.4),
    "whip": ("smoothleft", 0.3), "zoom": ("circleopen", 0.45), "reveal": ("vertopen", 0.45),
}
SAMPLE_RATE = 48000
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")


@dataclass
class Clip:
    image: Path
    duration: float  # time this scene owns on the timeline (narration + breathing room)
    camera: str
    transition: str  # transition INTO this clip (ignored for the first clip)
    video: Path | None = None  # AI-generated or imported clip; when absent the still gets camera motion
    video_duration: float | None = None
    reveal: str = ""  # animated looks: "draw" (white -> line sketch -> picture) or "sketch" (line art -> picture)


def _reveal(kind: str) -> str:
    """Filter chain that makes a shot look drawn on: its own edges as dark lines on white, blended into the picture
    over the first second. Applied on the same timeline as the shot, so camera motion continues smoothly."""
    if kind not in ("draw", "sketch"):
        return ""
    ramp = lambda t0, d: f"clip((T-{t0})/{d},0,1)"  # noqa: E731
    show = ramp(0.45, 0.45) if kind == "draw" else ramp(0.15, 0.45)
    lines = (f"(255*(1-{ramp(0.0, 0.4)})+A*{ramp(0.0, 0.4)})" if kind == "draw" else "A")
    return (f",format=gbrp,split[rv_a][rv_b];[rv_a]edgedetect=low=0.08:high=0.25,format=gbrp,negate[rv_s];"
            f"[rv_s][rv_b]blend=all_expr='{lines}*(1-{show})+B*{show}'")


# Retention: TTS engines pad every line with silence and some pause too long between sentences. Cut the lead-in,
# shorten any pause over 0.25 s to 0.15 s, and drop the tail, so the voice flows like a real creator's edit.
TIGHTEN = ("silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=-1:stop_duration=0.25"
           ":stop_threshold=-45dB:stop_silence=0.15")


def to_pcm(src: Path, dst: Path, cancel: threading.Event | None = None, tighten: bool = True, speed: float = 1.0) -> None:
    chain = ([TIGHTEN] if tighten else []) + ([f"atempo={speed:.3f}"] if abs(speed - 1.0) > 0.01 else [])
    af = ["-af", ",".join(chain)] if chain else []
    ff.run(["-i", str(src), *af, "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)], cancel)


def narration_track(pcm_wavs: list[Path], durations: list[float], tail: float, out: Path) -> None:
    """Concatenates per-scene narration, padding each scene with silence to its slot length."""
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        for src, d in zip(pcm_wavs, durations):
            with wave.open(str(src), "rb") as r:
                frames = r.readframes(r.getnframes())
            slot = int(round(d * SAMPLE_RATE)) * 2
            w.writeframes(frames[:slot] + b"\x00" * max(0, slot - len(frames)))
        w.writeframes(b"\x00" * int(round(tail * SAMPLE_RATE)) * 2)


def pick_music(music_dir: str, mood: str, seed: str) -> Path | None:
    """Chooses a track from the local royalty-free library, preferring filenames that match the mood."""
    if not music_dir:
        return None
    root = Path(music_dir)
    if not root.is_dir():
        return None
    tracks = sorted(p for p in root.rglob("*") if p.suffix.lower() in AUDIO_EXT and p.is_file())
    if not tracks:
        return None
    words = {w for w in mood.lower().replace(",", " ").split() if len(w) > 2}
    scored = sorted(tracks, key=lambda p: -sum(w in p.stem.lower() for w in words))
    best = sum(w in scored[0].stem.lower() for w in words)
    pool = [p for p in scored if sum(w in p.stem.lower() for w in words) == best] if best else tracks
    return pool[int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(pool)]


def mix_audio(narration: Path, music: Path | None, total: float, out: Path, cancel: threading.Event,
              sfx: list[tuple[Path, float, float]] | None = None) -> None:
    """Narration + optional music bed (ducked under the voice) + optional timed sound effects."""
    sfx = sfx or []
    args = ["-i", str(narration)]
    graph = [f"[0:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,apad,atrim=0:{total:.3f}"
             + (",asplit=2[n][key]" if music is not None else "[n]")]
    mix = ["[n]"]
    idx = 1
    if music is not None:
        fade_out = max(0.0, total - 2.0)
        args += ["-stream_loop", "-1", "-i", str(music)]
        graph.append(f"[{idx}:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,volume=0.35,"
                     f"afade=t=in:d=1,afade=t=out:st={fade_out:.3f}:d=2,atrim=0:{total:.3f}[m]")
        graph.append("[m][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]")
        mix.append("[duck]")
        idx += 1
    for k, (path, at, gain) in enumerate(sfx):
        if at >= total:
            continue
        ms = int(at * 1000)
        args += ["-i", str(path)]
        graph.append(f"[{idx}:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,volume={gain:.2f},"
                     f"adelay={ms}|{ms}[s{k}]")
        mix.append(f"[s{k}]")
        idx += 1
    if len(mix) == 1:
        graph.append("[n]anull[a]")
    else:
        graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,alimiter=limit=0.95[a]")
    ff.run([*args, "-filter_complex", ";".join(graph), "-map", "[a]", "-t", f"{total:.3f}",
            "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(out)], cancel)


def _motion(camera: str, frames: int) -> str:
    c = camera.lower()
    d = max(frames - 1, 1)
    # Emotion effects (input is a 4x canvas, so 40 px here = 10 px on screen).
    if c == "shake":   # reveal: quick punch-in with a short, decaying camera shake
        return (f"z='min(1.16,1+0.02*on)':x='iw/2-(iw/zoom/2)+if(lt(on,18),(18-on)*2.4*sin(on*2.9),0)'"
                f":y='ih/2-(ih/zoom/2)+if(lt(on,18),(18-on)*2.0*cos(on*3.7),0)'")
    if c == "punch":   # shock word: fast zoom-in that lands and holds
        return "z='min(1.18,1+0.03*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if "pull" in c or "zoom out" in c or "dolly out" in c:
        return f"z='1.15-0.15*on/{d}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if "pan left" in c or "truck left" in c:
        return f"z='1.12':x='(iw-iw/zoom)*(1-on/{d})':y='ih/2-(ih/zoom/2)'"
    if "pan right" in c or "truck right" in c or "pan" in c:
        return f"z='1.12':x='(iw-iw/zoom)*on/{d}':y='ih/2-(ih/zoom/2)'"
    if "static" in c or "locked" in c:
        return f"z='1.04':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    return f"z='1+0.15*on/{d}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"  # default: slow push in


LOGO_XY = {"top-right": ("W-w-{m}", "{m}"), "top-left": ("{m}", "{m}"),
           "bottom-right": ("W-w-{m}", "H-h-{m}"), "bottom-left": ("{m}", "H-h-{m}")}


def _segment_args(c: Clip, frames: int, width: int, height: int) -> list[str]:
    if c.video is not None:
        # Fit the clip to the slot: cover-crop; a clip shorter than its slot is slowed gently (max 1.25x), and
        # if that's still short it plays forward then backward (boomerang) instead of freezing on its last frame.
        length = frames / FPS
        stretch = min(1.25, length / c.video_duration) if c.video_duration and c.video_duration < length else 1.0
        boomerang = bool(c.video_duration) and c.video_duration * stretch < length - 0.05
        # AI clips come out at ~480-720p: upscale with lanczos, then a light unsharp mask so they don't look soft.
        base = (f"setpts={stretch:.4f}*(PTS-STARTPTS),"
                f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,crop={width}:{height},"
                f"unsharp=5:5:0.6:5:5:0.0,setsar=1,fps={FPS}")
        if boomerang:
            vf = (f"[0:v]{base},split[f][b];[b]reverse[r];[f][r]concat=n=2:v=1:a=0,fps={FPS},settb=1/{FPS},"
                  f"tpad=stop_mode=clone:stop_duration={length:.3f},trim=end_frame={frames},setpts=PTS-STARTPTS,"
                  f"format=yuv420p[v]")
        else:
            vf = (f"[0:v]{base},tpad=stop_mode=clone:stop_duration={length:.3f},"
                  f"trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p[v]")
        src = ["-i", str(c.video)]
    else:
        # zoompan moves in whole input pixels; on a 4x canvas each step is a quarter output pixel, so slow
        # push-ins and pans glide instead of shaking. (Scaled once per still, so it's cheap.)
        sw, sh = width * 4, height * 4
        vf = (f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,crop={sw}:{sh},setsar=1,"
              f"zoompan={_motion(c.camera, frames)}:d={frames}:s={width}x{height}:fps={FPS},"
              f"trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p[v]")
        src = ["-i", str(c.image)]
    if c.reveal:
        vf = vf.replace(",format=yuv420p[v]", _reveal(c.reveal) + ",format=yuv420p[v]")
    return [*src, "-filter_complex", vf, "-map", "[v]", "-an", "-frames:v", str(frames), "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p"]


def _segments(jobs: list[tuple[Clip, int]], width: int, height: int, work: Path,
              cancel: threading.Event) -> list[Path]:
    import os
    from concurrent.futures import ThreadPoolExecutor
    work.mkdir(parents=True, exist_ok=True)
    plan = []
    for c, frames in jobs:
        args = _segment_args(c, frames, width, height)
        src = c.video or c.image
        stamp = f"{src.stat().st_size}:{src.stat().st_mtime_ns}" if src.is_file() else ""
        key = hashlib.sha256(("|".join(args) + stamp).encode()).hexdigest()[:20]
        plan.append((work / f"seg_{key}.mp4", args))

    def make(item):
        dst, args = item
        if dst.is_file() and dst.stat().st_size > 1000:
            return
        tmp = dst.with_name(dst.stem + ".part.mp4")
        ff.run([*args, str(tmp)], cancel)
        tmp.replace(dst)

    with ThreadPoolExecutor(max_workers=max(2, min(8, (os.cpu_count() or 2) // 2))) as pool:
        for _ in pool.map(make, plan):   # re-raises the first failure (or Cancelled)
            pass
    return [dst for dst, _ in plan]


def render_video(clips: list[Clip], audio: Path, captions: Path | None, width: int, height: int,
                 out: Path, work: Path, cancel: threading.Event,
                 logo: tuple[Path, str, float] | None = None, grade: str = "film") -> float:
    """Returns the expected duration of the rendered file."""
    tail = TRANSITION_S if len(clips) > 1 else 0.0
    trans = [TRANSITIONS.get(c.transition, TRANSITIONS["fade"]) for c in clips]
    # Pass 1: every shot becomes its own short, uniform segment (same size, fps, pixel format), several at a time.
    # One FFmpeg graph holding a hundred stills on a 4x canvas plus stock clips of mixed sizes is slow, needs a
    # lot of memory, and can crash when a clip changes size mid-stream; small separate jobs avoid all three, and a
    # retry reuses the segments that were already made.
    jobs = []
    for i, c in enumerate(clips):
        # Each clip overlaps the next by the incoming transition's length (the last one by the tail).
        overlap = trans[i + 1][1] if i + 1 < len(clips) else tail
        jobs.append((c, max(2, round((c.duration + overlap) * FPS))))
    segments = _segments(jobs, width, height, work, cancel)
    args: list[str] = []
    graph: list[str] = []
    for i, seg in enumerate(segments):
        args += ["-threads", "1", "-i", str(seg.resolve())]   # many inputs: one decoder thread each keeps memory low
        graph.append(f"[{i}:v]settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    last = "v0"
    offset = 0.0
    for i in range(1, len(clips)):
        offset += clips[i - 1].duration
        name, dur = trans[i]
        graph.append(f"[{last}][v{i}]xfade=transition={name}:duration={dur}:offset={offset:.3f}[x{i}]")
        last = f"x{i}"
    total = sum(c.duration for c in clips) + tail
    audio_idx = len(clips)
    if grade:
        # One consistent "film" look over every shot: a touch of contrast and colour, soft vignette, fine grain.
        # "bw": the writer asked for a black-and-white look - AI shots and stock footage are matched to it.
        tone = "hue=s=0,eq=contrast=1.12:gamma=0.97" if grade == "bw" else "eq=contrast=1.06:saturation=1.08:gamma=0.98"
        graph.append(f"[{last}]{tone},vignette=angle=PI/5,noise=alls={7 if grade == 'bw' else 5}:allf=t+u,format=yuv420p[graded]")
        last = "graded"
    if logo is not None:
        # Brand watermark: about 14% of the frame width, in a corner, slightly transparent. Captions go on top.
        path, pos, opacity = logo
        m = int(min(width, height) * 0.035)
        x, y = (v.format(m=m) for v in LOGO_XY.get(pos, LOGO_XY["top-right"]))
        graph.append(f"[{audio_idx + 1}:v]scale={int(width * 0.14) // 2 * 2}:-2,format=rgba,"
                     f"colorchannelmixer=aa={opacity:.2f}[logo]")
        graph.append(f"[{last}][logo]overlay=x={x}:y={y}:shortest=1,format=yuv420p[vlogo]")
        last = "vlogo"
    if captions is not None:
        graph.append(f"[{last}]subtitles=filename={captions.name}[vout]")
        last = "vout"
    args += ["-i", str(audio)]
    if logo is not None:
        args += ["-loop", "1", "-i", str(logo[0])]
    args += ["-filter_complex", ";".join(graph), "-map", f"[{last}]", "-map", f"{audio_idx}:a",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-movflags", "+faststart",
             "-t", f"{total:.3f}", str(out)]
    ff.run(args, cancel, cwd=work)
    return total
