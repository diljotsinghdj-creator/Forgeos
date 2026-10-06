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


def to_pcm(src: Path, dst: Path, cancel: threading.Event | None = None) -> None:
    ff.run(["-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)], cancel)


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
    if "pull" in c or "zoom out" in c or "dolly out" in c:
        return f"z='1.15-0.15*on/{d}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if "pan left" in c or "truck left" in c:
        return f"z='1.12':x='(iw-iw/zoom)*(1-on/{d})':y='ih/2-(ih/zoom/2)'"
    if "pan right" in c or "truck right" in c or "pan" in c:
        return f"z='1.12':x='(iw-iw/zoom)*on/{d}':y='ih/2-(ih/zoom/2)'"
    if "static" in c or "locked" in c:
        return f"z='1.04':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    return f"z='1+0.15*on/{d}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"  # default: slow push in


def render_video(clips: list[Clip], audio: Path, captions: Path | None, width: int, height: int,
                 out: Path, work: Path, cancel: threading.Event) -> float:
    """Returns the expected duration of the rendered file."""
    tail = TRANSITION_S if len(clips) > 1 else 0.0
    trans = [TRANSITIONS.get(c.transition, TRANSITIONS["fade"]) for c in clips]
    args: list[str] = []
    graph: list[str] = []
    for i, c in enumerate(clips):
        # Each clip overlaps the next by the incoming transition's length (the last one by the tail).
        overlap = trans[i + 1][1] if i + 1 < len(clips) else tail
        frames = max(2, round((c.duration + overlap) * FPS))
        if c.video is not None:
            # Fit the clip to the slot: cover-crop, hold the last frame if the model's clip is shorter.
            length = frames / FPS
            # A clip shorter than its slot is slowed gently (max 1.6x) before holding the last frame,
            # so motion keeps going instead of freezing.
            stretch = min(1.6, length / c.video_duration) if c.video_duration and c.video_duration < length else 1.0
            args += ["-i", str(c.video)]
            graph.append(f"[{i}:v]setpts={stretch:.4f}*(PTS-STARTPTS),"
                         f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                         f"setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration={length:.3f},"
                         f"trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
            continue
        args += ["-i", str(c.image)]
        sw, sh = int(width * 1.5) // 2 * 2, int(height * 1.5) // 2 * 2
        graph.append(f"[{i}:v]scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},setsar=1,"
                     f"zoompan={_motion(c.camera, frames)}:d={frames}:s={width}x{height}:fps={FPS},"
                     f"trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    last = "v0"
    offset = 0.0
    for i in range(1, len(clips)):
        offset += clips[i - 1].duration
        name, dur = trans[i]
        graph.append(f"[{last}][v{i}]xfade=transition={name}:duration={dur}:offset={offset:.3f}[x{i}]")
        last = f"x{i}"
    total = sum(c.duration for c in clips) + tail
    if captions is not None:
        graph.append(f"[{last}]subtitles=filename={captions.name}[vout]")
        last = "vout"
    audio_idx = len(clips)
    args += ["-i", str(audio), "-filter_complex", ";".join(graph), "-map", f"[{last}]", "-map", f"{audio_idx}:a",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-movflags", "+faststart",
             "-t", f"{total:.3f}", str(out)]
    ff.run(args, cancel, cwd=work)
    return total
