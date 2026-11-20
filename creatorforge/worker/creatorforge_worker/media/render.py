"""Smart Editor / Auto Edit: assembles scene stills, narration, music, transitions, captions
and overlays into the final H.264/AAC MP4 with FFmpeg."""
from __future__ import annotations

import hashlib
import os
import re
import threading
import wave
from dataclasses import dataclass
from pathlib import Path

from . import ff

# 30, or 60 for smoother motion (CF_FPS=60 on the pod): stills, camera moves and graphics render natively at it,
# AI clips are interpolated up to it (media/interp.py).
FPS = 60 if os.environ.get("CF_FPS", "30") == "60" else 30
TRANSITION_S = 0.5  # longest transition; also the tail after the last scene
CHUNK_SHOTS = 60   # longer films are assembled this many shots at a time (memory and time stay bounded)
# Editorial transition vocabulary used by templates and Auto Edit -> (FFmpeg xfade, seconds).
TRANSITIONS = {
    "cut": ("fade", 0.08), "fade": ("fade", 0.5), "dissolve": ("dissolve", 0.5), "dip": ("fadeblack", 0.5),
    "flash": ("fadewhite", 0.3), "slide": ("slideleft", 0.4), "wipe": ("wipeleft", 0.4),
    "whip": ("smoothleft", 0.3), "zoom": ("circleopen", 0.45), "reveal": ("vertopen", 0.45),
    "blur": ("hblur", 0.3),       # the explainer camera-blur whip between two graphics
    "iris": ("circleopen", 0.45),
    "dipcut": ("fadeblack", 0.12),  # the frame darkens for a few frames before a hard cut, so the cut reads as meant
    # paper tear: a wipe whose edge is a ragged strip of torn white paper (drawn over the seam, see render_video)
    "tear": ("wipeleft", 0.45),
    # match cut / zoom-through: the old shot flies in, a quick blend, the new one lands from close (see _segment_args)
    "match": ("fade", 0.22),
    # motivated cuts between graphics (pipeline.motivated_transition picks them from what the two shots are)
    "dive": ("zoomin", 0.45),         # out of a map: the camera dives into the place and lands in the next shot
    "page": ("slideup", 0.4),         # a document or clipping is pushed up off the desk
    "push": ("slideleft", 0.35),      # the same kind of chart again: the next one pushes in beside it
    "drop": ("slidedown", 0.4),       # an evidence card drops over the last
    "squeeze": ("squeezeh", 0.4),     # a comparison closes like a book onto its answer
    # shape morph: the outgoing shot's main shape fills with the signature yellow, morphs into the incoming shot's
    # main shape, and opens onto it (drawn over a plain blend, see _morph_clip)
    "morph": (r"custom:expr=if(gt(P\,0.5)\,A\,B)", 0.5),   # the shots swap at the middle, under the shape
}
MORPH_COLOUR = (0xFF, 0xDD, 0x33)   # the channel's signature yellow
SAMPLE_RATE = 48000
TARGET_LUFS = -14
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
    backdrop: Path | None = None  # explainer looks: a clip plays in a bordered frame on this paper/desk image
    layers: tuple[Path, Path] | None = None  # explainer cut-outs: (desk, sticker) moved at different speeds (2.5D)
    grade: str = ""  # "archive": old-film look (sepia, grain, flicker, soft vignette) for history beats
    marks: Path | None = None  # pen marks / bubbles for this shot (ASS, clip-relative times) drawn ON the picture,
    #                           so they move with it (the cut-out's push-in, or the footage's own motion)
    track: list | None = None  # footage only: [(seconds, dx, dy)] how the picture content moved (pixels)
    morph: Path | None = None  # the shape-morph overlay drawn over the cut INTO this clip (made by render_video)
    exit_zoom: bool = False   # match cut out of this shot: the camera accelerates into it at the end
    enter_zoom: bool = False  # match cut into this shot: it starts close and settles
    stepped: bool = False     # a drawn graphic: played at 12 frames a second, the hand-made look of video essays
    playback: str = ""        # footage only: "freeze" (plays, then holds a frame), "ramp" (fast, then slow), "slow"


# Old film: sepia, a little extra contrast, flicker, moving grain, a soft dark edge.
ARCHIVE = (",colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,"
           "eq=contrast=1.12:brightness='0.025*sin(t*23)+0.015*sin(t*61)':eval=frame,"
           "noise=alls=24:allf=t+u,gblur=sigma=0.6,vignette=angle=PI/3.5")


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


def chapter_music(tracks: list[Path], starts: list[float], total: float, out: Path, cancel: threading.Event) -> None:
    """One music bed that changes track at each chapter (tracks are reused in turn if there are fewer than parts),
    each part fading in over a second while the last fades out."""
    bounds = [0.0] + [max(0.0, s) for s in starts] + [total]
    args, graph, mix = [], [], []
    for i, (a, b) in enumerate(zip(bounds, bounds[1:])):
        if b - a < 1.0:
            continue
        src = tracks[i % len(tracks)]
        n = len(mix)
        args += ["-stream_loop", "-1", "-i", str(src)]
        length = b - a + 1.0
        ms = int(a * 1000)
        graph.append(f"[{n}:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,atrim=0:{length:.3f},"
                     f"afade=t=in:d={0.01 if i == 0 else 1.0},afade=t=out:st={max(0.0, length - 1.0):.3f}:d=1,"
                     f"adelay={ms}|{ms}[p{n}]")
        mix.append(f"[p{n}]")
    graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=longest:normalize=0,atrim=0:{total:.3f}[a]")
    ff.run([*args, "-filter_complex", ";".join(graph), "-map", "[a]", "-ar", str(SAMPLE_RATE),
            "-c:a", "pcm_s16le", str(out)], cancel)


def music_beats(music: Path, seconds: float = 240.0) -> list[float]:
    """Beat times (s) in a music track: an onset-strength envelope (rising energy, ~23 ms frames), its tempo from
    autocorrelation, then the beat grid that best follows the onsets. [] when the track has no clear pulse."""
    import subprocess
    import numpy as np
    sr, hop = 11025, 256
    try:
        raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-t", f"{seconds:.1f}", "-i", str(music), "-ac", "1",
                              "-ar", str(sr), "-f", "s16le", "-"], capture_output=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if len(x) < sr * 4:
        return []
    n = len(x) // hop
    energy = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-9)
    log_e = np.log(energy)
    onset = np.maximum(0.0, np.diff(log_e, prepend=log_e[0]))
    onset = onset - np.convolve(onset, np.ones(16) / 16, mode="same")
    onset = np.maximum(onset, 0)
    if onset.max() <= 0:
        return []
    fps = sr / hop                                           # envelope frames per second (~43)
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 70)         # 70-180 BPM
    ac = np.correlate(onset, onset, mode="full")[len(onset) - 1:]
    if hi >= len(ac):
        return []
    lag = lo + int(np.argmax(ac[lo:hi]))
    if ac[lag] < 0.1 * ac[0]:
        return []                                            # no steady pulse (ambient, speech)
    # fractional period (parabolic peak), then each predicted beat snaps to the strongest onset near it
    a, b, c = ac[lag - 1], ac[lag], ac[lag + 1] if lag + 1 < len(ac) else ac[lag]
    period = lag + (0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0)
    strong = np.nonzero(onset > 0.5 * onset.max())[0]
    phase = int(strong[0]) % lag if len(strong) else int(np.argmax([onset[p::lag].sum() for p in range(lag)]))
    beats, t, win = [], float(phase), max(1, int(fps * 0.07))
    while t < n:
        i = int(round(t))
        j0, j1 = max(0, i - win), min(n, i + win + 1)
        k = j0 + int(np.argmax(onset[j0:j1])) if j1 > j0 else i
        if onset[k] > 0.3 * onset.max():
            t = float(k)                                     # follow the music
        beats.append(round(float(t) / fps, 3))
        t += period
    return beats


def music_offset(beats: list[float], cuts: list[float], window: float = 0.08) -> float:
    """Where to start the music so the most picture cuts land on a beat (seconds into the track, < one beat)."""
    if len(beats) < 4 or not cuts:
        return 0.0
    period = (beats[-1] - beats[0]) / (len(beats) - 1)
    best, best_hits = 0.0, -1
    import numpy as np
    b = np.array(beats)
    for k in range(int(period / 0.01) + 1):
        off = k * 0.01
        # music time = video time + off; a cut at video time c is on a beat when c + off is near a beat
        hits = sum(1 for c in cuts if np.min(np.abs(b - (c + off))) <= window)
        if hits > best_hits:
            best, best_hits = off, hits
    return round(best, 2)


def mix_audio(narration: Path, music: Path | None, total: float, out: Path, cancel: threading.Event,
              sfx: list[tuple[Path, float, float]] | None = None, dips: list[tuple[float, float]] | None = None,
              music_start: float = 0.0) -> None:
    """Narration + optional music bed (ducked under the voice) + optional timed sound effects."""
    sfx = sfx or []
    args = ["-i", str(narration)]
    graph = [f"[0:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,apad,atrim=0:{total:.3f}"
             + (",asplit=2[n][key]" if music is not None else "[n]")]
    mix = ["[n]"]
    idx = 1
    if music is not None:
        fade_out = max(0.0, total - 2.0)
        args += ["-stream_loop", "-1"] + (["-ss", f"{music_start:.2f}"] if music_start > 0 else []) + ["-i", str(music)]
        graph.append(f"[{idx}:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,volume=0.35,"
                     f"afade=t=in:d=1,afade=t=out:st={fade_out:.3f}:d=2,atrim=0:{total:.3f}"
                     # the music drops away under a chapter card or a big statement, then comes back
                     + (f",volume='if({'+'.join(f'between(t,{a:.2f},{b:.2f})' for a, b in dips)},0.2,1)':eval=frame"
                        if dips else "") + "[m]")
        graph.append("[m][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]")
        mix.append("[duck]")
        idx += 1
    for k, hit in enumerate(sfx):
        path, at, gain = hit[:3]
        pan = hit[3] if len(hit) > 3 else 0.0     # stereo place: -1 left .. 1 right, or "lr" / "rl" to travel across
        if at >= total:
            continue
        ms = int(at * 1000)
        args += ["-i", str(path)]
        if pan in ("lr", "rl"):
            a, b = ("cos", "sin") if pan == "lr" else ("sin", "cos")
            place = (f",channelsplit=channel_layout=stereo[pl{k}][pr{k}];"
                     f"[pl{k}]volume='1.3*{a}(PI/2*min(1,t/0.55))':eval=frame[ql{k}];"
                     f"[pr{k}]volume='1.3*{b}(PI/2*min(1,t/0.55))':eval=frame[qr{k}];"
                     f"[ql{k}][qr{k}]join=inputs=2:channel_layout=stereo")
        elif isinstance(pan, (int, float)) and abs(pan) > 0.01:
            import math
            th = (max(-1.0, min(1.0, float(pan))) + 1) * math.pi / 4          # equal-power pan
            place = f",pan=stereo|c0={math.cos(th) * 1.414:.3f}*c0|c1={math.sin(th) * 1.414:.3f}*c1"
        else:
            place = ""
        lp = hit[4] if len(hit) > 4 and hit[4] else 0          # a low-pass in Hz (the owner's foley rule: under 800 Hz)
        graph.append(f"[{idx}:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,volume={gain:.4f}{place}"
                     + (f",lowpass=f={int(lp)}" if lp else "") + f",adelay={ms}|{ms}[s{k}]")
        mix.append(f"[s{k}]")
        idx += 1
    # Every video lands at the loudness social platforms normalise to (-14 LUFS, true peak under -1.5 dB), so it is
    # never quieter than the next video in the feed and never clips.
    level = f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11"
    if len(mix) == 1:
        graph.append(f"[n]{level}[a]")
    else:
        graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,alimiter=limit=0.95,{level}[a]")
    ff.run([*args, "-filter_complex", ";".join(graph), "-map", "[a]", "-t", f"{total:.3f}",
            "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(out)], cancel)


def levels(audio: Path, start: float, seconds: float, rate: int = 12) -> list[float]:
    """How loud a stretch of audio is, `rate` times a second, 0..1 (for graphics that move with the voice)."""
    import subprocess
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(0.0, start):.3f}", "-t", f"{max(0.1, seconds):.3f}",
                          "-i", str(audio), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True, timeout=120).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    step = 8000 // rate
    if len(a) < step:
        return []
    rms = np.sqrt((a[: len(a) // step * step].reshape(-1, step) ** 2).mean(axis=1))
    top = float(np.percentile(rms, 95)) or 1.0
    return [round(float(min(1.0, v / top)), 2) for v in rms]


def _motion(camera: str, frames: int) -> str:
    c = camera.lower()
    if c == "slidein":   # a whole-frame still can't slide in (nothing beside it): it lands like "settle"
        c = "settle"
    d = max(frames - 1, 1)
    # Emotion effects (input is a 4x canvas, so 40 px here = 10 px on screen).
    if c == "shake":   # reveal: quick punch-in with a short, decaying camera shake
        return (f"z='min(1.16,1+0.02*on)':x='iw/2-(iw/zoom/2)+if(lt(on,18),(18-on)*2.4*sin(on*2.9),0)'"
                f":y='ih/2-(ih/zoom/2)+if(lt(on,18),(18-on)*2.0*cos(on*3.7),0)'")
    if c == "settle":  # explainer cut: the frame lands slightly close, eases back in a quarter second, then drifts in
        return (f"z='if(lt(on,8),1.07-0.07*on/8,1+0.05*(on-8)/{max(d - 8, 1)})'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
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
        timing, after = f"setpts={stretch:.4f}*(PTS-STARTPTS)", ""
        vd = c.video_duration or 0.0
        if c.playback == "freeze" and not c.stepped:
            # freeze frame: the shot plays, stops dead on a frame with a camera-flash blink and drains to near
            # black-and-white while the narration makes its point
            hold = round(min(length * 0.55, max(0.4, vd - 0.1)) if vd else length * 0.55, 3)
            timing = f"setpts=PTS-STARTPTS,trim=duration={hold},setpts=PTS-STARTPTS"
            after = (f",tpad=stop_mode=clone:stop_duration={length:.3f},"
                     f"eq=brightness='if(between(t,{hold},{hold + 0.1:.3f}),0.22,0)':saturation='if(gte(t,{hold}),0.25,1)':eval=frame")
            boomerang = False
        elif c.playback == "ramp" and not c.stepped and vd >= 1.0:
            # speed ramp: the first stretch races by at 2.5x, then time stretches out to 0.6x for the moment itself
            a = round(min(vd * 0.45, length * 1.2), 3)
            if a + (length - a / 2.5) * 0.6 <= vd + 0.05:
                timing = f"setpts='if(lt(T,{a}),T/2.5,{a / 2.5:.4f}+(T-{a})/0.6)/TB',minterpolate=fps={FPS}:mi_mode=blend"
                boomerang = False
        elif c.playback == "slow" and not c.stepped and vd >= length * 0.5 - 0.05:
            timing = f"setpts=2.0*(PTS-STARTPTS),minterpolate=fps={FPS}:mi_mode=blend"     # half speed, frames blended
            boomerang = False
        base = (("fps=12," if c.stepped else "") + f"{timing},"
                f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,crop={width}:{height},"
                f"unsharp=5:5:0.6:5:5:0.0,setsar=1,fps={FPS}{after}")
        if boomerang:
            vf = (f"[0:v]{base},split[f][b];[b]reverse[r];[f][r]concat=n=2:v=1:a=0,fps={FPS},settb=1/{FPS},"
                  f"tpad=stop_mode=clone:stop_duration={length:.3f},trim=end_frame={frames},setpts=PTS-STARTPTS,"
                  f"format=yuv420p[v]")
        else:
            vf = (f"[0:v]{base},tpad=stop_mode=clone:stop_duration={length:.3f},"
                  f"trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p[v]")
        src = ["-i", str(c.video)]
        if c.backdrop is not None:
            # Explainer looks: the footage plays as a framed print on the paper/desk, not edge to edge.
            from . import layout
            bw, bh = layout.video_box(width, height)
            vf = vf.replace(f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,crop={width}:{height}",
                            f"scale={bw}:{bh}:force_original_aspect_ratio=increase:flags=lanczos,crop={bw}:{bh}")
            vf = vf.replace(",format=yuv420p[v]", ",format=rgb24[vin]")
            vf += (f";[1:v]fps={FPS},trim=end_frame={frames},setpts=PTS-STARTPTS[bgv];"
                   + layout.video_graph(width, height, "vin", "bgv", "v"))
            src += ["-loop", "1", "-i", str(c.backdrop)]
    elif c.marks is not None and c.layers is not None and c.camera in ("settle", "punch", "slidein"):
        # 2.5D with pen marks: the marks are drawn onto the cut-out layer before it moves, so a circle stays on its
        # subject through the push-in (the way a motion designer would parent it).
        length = frames / FPS
        d = max(frames - 1, 1)
        sw, sh = width * 2, height * 2
        side = 1 if int(hashlib.sha256(str(c.layers[1]).encode()).hexdigest(), 16) % 2 else -1
        zb = f"1+0.03*on/{d}" if c.camera != "punch" else "min(1.05,1+0.008*on)"
        zf = (f"if(lt(on,8),1.09-0.09*on/8,1+0.085*(on-8)/{max(d - 8, 1)})" if c.camera != "punch"
              else "min(1.2,1+0.035*on)")
        drift = f"{side}*iw*0.012*on/{d}"
        vf = (f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,crop={sw}:{sh},setsar=1,"
              f"zoompan=z='{zb}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={FPS},"
              f"trim=end_frame={frames},setpts=PTS-STARTPTS[bgm];"
              + _marks_layer(c.marks, 2, sw, sh, length) +
              f"[1:v]format=rgba,scale={sw}:{sh}:flags=lanczos,setsar=1,fps={FPS}[fgs];"
              f"[fgs][mk]overlay=format=auto,format=yuva444p,"
              f"zoompan=z='{zf}':x='iw/2-(iw/zoom/2)+{drift}':y='ih/2-(ih/zoom/2)':d=1:s={width}x{height}:fps={FPS},"
              f"format=yuva444p,trim=end_frame={frames},setpts=PTS-STARTPTS[fgm];"
              f"[bgm][fgm]overlay=format=auto,format=yuv420p[v]")
        src = ["-i", str(c.layers[0]), "-loop", "1", "-t", f"{length + 0.1:.3f}", "-i", str(c.layers[1]),
               "-f", "lavfi", "-i", f"color=c=0xFF00FF:s={sw}x{sh}:r={FPS}:d={length + 0.1:.3f}"]
    elif c.marks is not None and c.video is None:
        # a still with pen marks: marks drawn onto the picture first, then the camera moves both together
        length = frames / FPS
        sw, sh = width * 2, height * 2
        vf = (f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,crop={sw}:{sh},setsar=1,"
              f"fps={FPS},format=rgba[img];" + _marks_layer(c.marks, 1, sw, sh, length) +
              f"[img][mk]overlay=format=auto,format=yuv444p,"
              f"zoompan={_motion(c.camera, frames)}:d=1:s={width}x{height}:fps={FPS},"
              f"trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p[v]")
        src = ["-loop", "1", "-t", f"{length + 0.1:.3f}", "-i", str(c.image),
               "-f", "lavfi", "-i", f"color=c=0xFF00FF:s={sw}x{sh}:r={FPS}:d={length + 0.1:.3f}"]
    elif c.layers is not None and c.camera == "slidein":
        # Johnny Harris photo entrance: the cut-out slides in from the side with motion blur that clears as it
        # lands (a projector click is added in the sound design), then drifts like the 2.5D shots.
        d = max(frames - 1, 1)
        sw, sh = width * 2, height * 2
        zf = f"if(lt(on,10),1.04-0.04*on/10,1+0.07*(on-10)/{max(d - 10, 1)})"
        slide = f"{int(width * 0.22)}*pow(max(0,1-n/10),3)"
        vf = (f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,crop={sw}:{sh},setsar=1,"
              f"zoompan=z='1+0.03*on/{d}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={FPS},"
              f"trim=end_frame={frames},setpts=PTS-STARTPTS[bgm];"
              f"[1:v]format=yuva444p,scale={sw}:{sh}:flags=lanczos,setsar=1,"
              f"zoompan=z='{zf}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={FPS},"
              f"format=yuva444p,trim=end_frame={frames},setpts=PTS-STARTPTS,split[fs][fb];"
              f"[fb]gblur=sigma={max(4, width // 90)},fade=t=out:st=0:d=0.33:alpha=1[fbb];"
              f"[fs][fbb]overlay=format=auto[fgm];"
              f"[bgm][fgm]overlay=x='{slide}':y=0:eval=frame:format=auto,format=yuv420p[v]")
        src = ["-i", str(c.layers[0]), "-i", str(c.layers[1])]
    elif c.layers is not None and c.camera in ("settle", "punch"):
        # 2.5D depth: the desk drifts slowly while the cut-out lands and pushes in faster and slides a touch, so a
        # still photo reads as filmed with depth (the way video essays animate cut-outs). 2x canvases keep it smooth.
        d = max(frames - 1, 1)
        sw, sh = width * 2, height * 2
        side = 1 if int(hashlib.sha256(str(c.layers[1]).encode()).hexdigest(), 16) % 2 else -1
        if c.camera == "punch":
            zb, zf = "min(1.05,1+0.008*on)", "min(1.2,1+0.035*on)"
        else:
            zb = f"1+0.03*on/{d}"
            zf = f"if(lt(on,8),1.09-0.09*on/8,1+0.085*(on-8)/{max(d - 8, 1)})"
        drift = f"{side}*iw*0.012*on/{d}"
        vf = (f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,crop={sw}:{sh},setsar=1,"
              f"zoompan=z='{zb}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={FPS},"
              f"trim=end_frame={frames},setpts=PTS-STARTPTS[bgm];"
              f"[1:v]format=yuva444p,scale={sw}:{sh}:flags=lanczos,setsar=1,"
              f"zoompan=z='{zf}':x='iw/2-(iw/zoom/2)+{drift}':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={FPS},"
              f"format=yuva444p,trim=end_frame={frames},setpts=PTS-STARTPTS[fgm];"
              f"[bgm][fgm]overlay=format=auto,format=yuv420p[v]")
        src = ["-i", str(c.layers[0]), "-i", str(c.layers[1])]
    else:
        # zoompan moves in whole input pixels; on a 4x canvas each step is a quarter output pixel, so slow
        # push-ins and pans glide instead of shaking. (Scaled once per still, so it's cheap.)
        sw, sh = width * 4, height * 4
        vf = (f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,crop={sw}:{sh},setsar=1,"
              f"zoompan={_motion(c.camera, frames)}:d={frames}:s={width}x{height}:fps={FPS},"
              f"trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p[v]")
        src = ["-i", str(c.image)]
    if c.marks is not None and c.video is not None:
        # footage: the marks ride on the picture's own motion (measured beforehand), so a circle follows its subject
        length = frames / FPS
        k = src.count("-i")             # the marks layer is the next input
        xs, ys = _track_expr(c.track or [], length)
        vf = vf.replace("format=yuv420p[v]", "format=yuv420p[vm]", 1)
        vf += (";" + _marks_layer(c.marks, k, width, height, length, label="mkf") +
               f"[vm][mkf]overlay=x='{xs}':y='{ys}':eval=frame:format=auto,format=yuv420p[v]")
        src += ["-f", "lavfi", "-i", f"color=c=0xFF00FF:s={width}x{height}:r={FPS}:d={length + 0.1:.3f}"]
    if (c.exit_zoom or c.enter_zoom) and c.video is None:
        tail_f = max(4, min(14, frames // 3))
        factor = ""
        if c.exit_zoom:
            factor += f"*(1+1.4*pow(max(0,(on-{frames - tail_f})/{tail_f}),2))"
        if c.enter_zoom:
            factor += "*(1+0.6*pow(max(0,1-on/12),2))"
        vf = re.sub(r"zoompan=z='([^']*)'", lambda m: f"zoompan=z='({m.group(1)}){factor}'", vf)
    if c.reveal:
        vf = vf.replace(",format=yuv420p[v]", _reveal(c.reveal) + ",format=yuv420p[v]")
    if c.grade == "archive":
        vf = vf.replace(",format=yuv420p[v]", ARCHIVE + ",format=yuv420p[v]")
    return [*src, "-filter_complex", vf, "-map", "[v]", "-an", "-frames:v", str(frames), "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p"]


def _marks_layer(ass: Path, idx: int, w: int, h: int, length: float, label: str = "mk") -> str:
    """[label]: the shot's pen marks on a transparent layer. libass draws onto a key colour, which is then keyed out
    (it can't write transparency itself)."""
    return (f"[{idx}:v]{ff.ass_filter(ass)},colorkey=0xFF00FF:0.28:0.12,format=rgba,"
            f"trim=duration={length + 0.05:.3f},setpts=PTS-STARTPTS[{label}];")


def _track_expr(track: list, length: float) -> tuple[str, str]:
    """Piecewise-linear overlay x/y expressions from [(t, dx, dy)] keyframes."""
    if not track:
        return "0", "0"
    pts = [(0.0, 0.0, 0.0)] + [p for p in track if 0 < p[0] < length]
    def build(i: int, axis: int) -> str:
        if i >= len(pts) - 1:
            return f"{pts[-1][axis]:.1f}"
        (t0, *v0), (t1, *v1) = pts[i], pts[i + 1]
        a, b = v0[axis - 1], v1[axis - 1]
        seg = f"{a:.1f}+({b - a:.1f})*(t-{t0:.2f})/{max(t1 - t0, 0.01):.2f}"
        return f"if(lt(t,{t1:.2f}),{seg},{build(i + 1, axis)})"
    return build(0, 1), build(0, 2)


def track_motion(video: Path, length: float, box: tuple[int, int], cancel: threading.Event | None = None) -> list:
    """How the content of a clip moves: global shift every 0.1 s by phase correlation on small grey frames, scaled
    to the size the clip is shown at. Good enough to keep a circle on a panning subject; [] if it can't be read."""
    import subprocess
    try:
        import numpy as np
    except ImportError:
        return []
    sw, sh = 160, max(2, int(160 * box[1] / box[0]) // 2 * 2)
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-t", f"{length:.2f}", "-vf",
                              f"fps=10,scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},format=gray",
                              "-f", "rawvideo", "-"], capture_output=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    n = len(raw) // (sw * sh)
    if n < 2:
        return []
    frames = np.frombuffer(raw[: n * sw * sh], np.uint8).reshape(n, sh, sw).astype(np.float32)
    win = np.outer(np.hanning(sh), np.hanning(sw))
    out, x, y = [], 0.0, 0.0
    scale = box[0] / sw
    prev = np.fft.fft2(frames[0] * win)
    for i in range(1, n):
        cur = np.fft.fft2(frames[i] * win)
        r = prev * np.conj(cur)
        r /= np.abs(r) + 1e-9
        corr = np.abs(np.fft.ifft2(r))
        py, px = np.unravel_index(int(np.argmax(corr)), corr.shape)
        dy, dx = (py if py < sh // 2 else py - sh), (px if px < sw // 2 else px - sw)
        if abs(dx) <= sw // 6 and abs(dy) <= sh // 6:      # ignore cuts and jumps
            x, y = x - dx * scale, y - dy * scale
        out.append((i / 10, round(float(x), 1), round(float(y), 1)))
        prev = cur
    return out


def _tear_strip(width: int, height: int, work: Path) -> Path:
    """A vertical strip of torn white paper (both edges ragged, fibres on the edge, a soft shadow) as a PNG."""
    out = work / f"tear_{width}x{height}.png"
    if out.is_file():
        return out
    import random
    from PIL import Image, ImageDraw, ImageFilter
    sw = int(width * 0.07)
    rnd = random.Random(7)
    im = Image.new("RGBA", (sw, height), (0, 0, 0, 0))
    left, right, y = [], [], 0
    while y <= height:
        left.append((sw * 0.32 + rnd.uniform(-sw * 0.14, sw * 0.1), y))
        right.append((sw * 0.68 + rnd.uniform(-sw * 0.1, sw * 0.14), y))
        y += rnd.randint(6, 18)
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(x + 6, y) for x, y in left] + [(x + 6, y) for x, y in right[::-1]], fill=(0, 0, 0, 110))
    im = Image.alpha_composite(im, shadow.filter(ImageFilter.GaussianBlur(5)))
    ImageDraw.Draw(im).polygon(left + right[::-1], fill=(250, 248, 242, 255))
    work.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return out


def _logo_still(path: Path, width: int, opacity: float, work: Path) -> Path:
    """The brand logo as one ready-made PNG: turned upright (phone photos carry a rotation tag), RGBA, scaled to its
    final width, transparency baked in. A looping JPEG straight from the phone made the final render fail on some
    FFmpeg builds ("Error reinitializing filters")."""
    from PIL import Image, ImageOps
    with Image.open(path) as src:
        im = ImageOps.exif_transpose(src).convert("RGBA")
    h = max(2, round(im.height * width / max(1, im.width)) // 2 * 2)
    im = im.resize((max(2, width), h), Image.LANCZOS)
    alpha = im.getchannel("A").point(lambda a: int(a * max(0.0, min(1.0, opacity))))
    im.putalpha(alpha)
    work.mkdir(parents=True, exist_ok=True)
    out = work / "logo_still.png"
    im.save(out)
    return out


def _segments(jobs: list[tuple[Clip, int]], width: int, height: int, work: Path,
              cancel: threading.Event, progress=None) -> list[Path]:
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

    todo = list(dict(plan).items())
    done = [0]
    lock = threading.Lock()

    def make(item):
        dst, args = item
        if not (dst.is_file() and dst.stat().st_size > 1000):
            tmp = dst.with_name(dst.stem + ".part.mp4")
            ff.run([*args, str(tmp)], cancel)
            tmp.replace(dst)
        with lock:
            done[0] += 1
            if progress and (done[0] % 10 == 0 or done[0] == len(todo)):
                progress(f"Rendering shots {done[0]}/{len(todo)}")

    with ThreadPoolExecutor(max_workers=max(2, min(8, (os.cpu_count() or 2) // 2))) as pool:
        # identical shots share one segment file: make each file once, or two jobs race on the same temp file
        for _ in pool.map(make, todo):   # re-raises the first failure (or Cancelled)
            pass
    return [dst for dst, _ in plan]


def render_video(clips: list[Clip], audio: Path, captions: Path | None, width: int, height: int,
                 out: Path, work: Path, cancel: threading.Event,
                 logo: tuple[Path, str, float] | None = None, grade: str = "film", progress=None) -> float:
    """Returns the expected duration of the rendered file. progress(message) is told what step it is on (a long
    film spends many minutes here, so the app shows "Joining part 3 of 8" instead of a frozen bar)."""
    tail = TRANSITION_S if len(clips) > 1 else 0.0
    trans = [TRANSITIONS.get(c.transition, TRANSITIONS["fade"]) for c in clips]
    for i in range(1, len(clips)):
        if clips[i].transition == "match":
            clips[i - 1].exit_zoom, clips[i].enter_zoom = True, True
    # Pass 1: every shot becomes its own short, uniform segment (same size, fps, pixel format), several at a time.
    # One FFmpeg graph holding a hundred stills on a 4x canvas plus stock clips of mixed sizes is slow, needs a
    # lot of memory, and can crash when a clip changes size mid-stream; small separate jobs avoid all three, and a
    # retry reuses the segments that were already made.
    jobs = []
    for i, c in enumerate(clips):
        # Each clip overlaps the next by the incoming transition's length (the last one by the tail).
        overlap = trans[i + 1][1] if i + 1 < len(clips) else tail
        jobs.append((c, max(2, round((c.duration + overlap) * FPS))))
    segments = _segments(jobs, width, height, work, cancel, progress)
    for i in range(1, len(clips)):
        if clips[i].transition == "morph":
            try:
                clips[i].morph = _morph_clip(segments[i - 1], clips[i - 1].duration, segments[i], trans[i][1],
                                             width, height, work / f"morph_{i:03d}", cancel)
            except Exception:              # no clear shape to read: the cut stays a plain blend
                clips[i].morph = None
    total = sum(c.duration for c in clips) + tail
    if len(clips) <= CHUNK_SHOTS:
        _compose(clips, trans, segments, audio, captions, width, height, out, work, cancel, logo, grade,
                 t0=0.0, length=total, fade_out=True)
        return total
    # Long films (a 45-60 min documentary has 400+ shots): one graph holding every shot needs over 14 GB of memory
    # and runs past the time limit. Assemble ~CHUNK_SHOTS shots at a time instead (video only, each with its own
    # transitions, grade, logo and captions at the right film time), join the pieces without re-encoding, and add
    # the full soundtrack once. The seam between two pieces is a straight cut.
    parts, t0 = [], 0.0
    groups = [list(range(i, min(i + CHUNK_SHOTS, len(clips)))) for i in range(0, len(clips), CHUNK_SHOTS)]
    for g, idx in enumerate(groups):
        if progress:
            progress(f"Joining part {g + 1} of {len(groups)} (long film)")
        last_group = g == len(groups) - 1
        length = sum(clips[i].duration for i in idx) + (tail if last_group else 0.0)
        part = work / f"part_{g:03d}.mp4"
        sub_trans = [trans[i] for i in idx]
        _compose([clips[i] for i in idx], sub_trans, [segments[i] for i in idx], None, captions, width, height,
                 part, work, cancel, logo, grade, t0=t0, length=length, fade_out=last_group)
        parts.append(part)
        t0 += length
    if progress:
        progress("Adding the soundtrack to the full film")
    listing = work / "parts.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    ff.run(["-f", "concat", "-safe", "0", "-i", str(listing.resolve()), "-i", str(Path(audio).resolve()),
            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE),
            "-movflags", "+faststart", "-t", f"{total:.3f}", str(Path(out).resolve())], cancel, cwd=work)
    return total


def _shape(rgb, small: int = 4):
    """The main shape of a frame, as a boolean mask at 1/small size: pixels that differ from the page (the median
    of the border), the largest connected part, holes filled. None when nothing clear stands out."""
    import numpy as np
    from scipy import ndimage
    a = rgb[::small, ::small].astype(np.float32)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    diff = np.sqrt(((a - bg) ** 2).sum(axis=2)) > 42
    diff = ndimage.binary_opening(diff, iterations=2)
    lab, n = ndimage.label(diff)
    if n == 0:
        return None
    sizes = ndimage.sum(diff, lab, range(1, n + 1))
    big = lab == (int(np.argmax(sizes)) + 1)
    big = ndimage.binary_fill_holes(ndimage.binary_closing(big, iterations=3))
    frac = big.mean()
    return big if 0.015 < frac < 0.85 else None


def _morph_clip(seg_a: Path, t_a: float, seg_b: Path, dur: float, width: int, height: int, out_dir: Path,
                cancel: threading.Event) -> Path:
    """PNG frames (RGBA) of a yellow shape that takes the outgoing frame's main shape, morphs (signed distance
    interpolation) into the incoming frame's main shape, and fades as the new shot settles. A frame with no clear
    shape morphs to or from a centred disc."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for seg, t in ((seg_a, t_a), (seg_b, dur)):
        png = out_dir / f"src_{len(frames)}.png"
        ff.run(["-ss", f"{max(0.0, t):.3f}", "-i", str(Path(seg).resolve()), "-frames:v", "1", "-y", str(png.resolve())], cancel)
        frames.append(np.asarray(Image.open(png).convert("RGB").resize((width, height))))
    small = 4
    yy, xx = np.mgrid[0:frames[0][::small, ::small].shape[0], 0:frames[0][::small, ::small].shape[1]]

    def disc():
        cy, cx = yy.shape[0] / 2, yy.shape[1] / 2
        return (yy - cy) ** 2 + (xx - cx) ** 2 < (min(yy.shape) * .22) ** 2
    masks = [m if m is not None else disc() for m in (_shape(f, small) for f in frames)]
    sdf = [ndimage.distance_transform_edt(~m) - ndimage.distance_transform_edt(m) for m in masks]
    n = max(2, round(dur * FPS))
    col = np.array(MORPH_COLOUR, dtype=np.float32)
    for k in range(n):
        t = k / (n - 1)
        e = t * t * (3 - 2 * t)
        d = (1 - e) * sdf[0] + e * sdf[1]
        inside = 1 / (1 + np.exp(np.clip(d * 1.6, -30, 30)))            # soft, anti-aliased edge
        env = min(1.0, 3.2 * min(t, 1 - t) + 0.12)                       # rises fast, holds, opens onto the new shot
        a = Image.fromarray((inside * env * 255).astype(np.uint8)).resize((width, height), Image.BILINEAR)
        rgba = np.dstack([np.broadcast_to(col, (height, width, 3)), np.asarray(a, dtype=np.float32)]).astype(np.uint8)
        Image.fromarray(rgba, "RGBA").save(out_dir / f"m_{k:03d}.png")
    return out_dir


def _optical_mask(width: int, height: int, work: Path) -> Path:
    """The optical finish's edge mask as one raw yuv444p frame: 0 in the centre, rising to 155 (about 60%) over the
    outer third, the same value in all three planes (the expression the per-frame geq used to evaluate)."""
    import numpy as np
    out = work / f"optical_mask_{width}x{height}.yuv"
    if not out.is_file():
        y, x = np.mgrid[0:height, 0:width].astype(np.float32)
        r = np.hypot(x - width / 2, y - height / 2) / np.hypot(width / 2, height / 2)
        m = np.clip(155 * (r - 0.66) / 0.34, 0, 155).astype(np.uint8)
        out.write_bytes(np.concatenate([m.ravel()] * 3).tobytes())
    return out


def _compose(clips: list[Clip], trans: list, segments: list[Path], audio: Path | None, captions: Path | None,
             width: int, height: int, out: Path, work: Path, cancel: threading.Event,
             logo: tuple[Path, str, float] | None, grade: str, t0: float, length: float, fade_out: bool) -> None:
    """One FFmpeg graph: the shots joined with their transitions, the grade, logo, captions and (when audio is
    given) the soundtrack. t0 is where these shots sit in the whole film, so captions line up; length is the cut."""
    args: list[str] = []
    graph: list[str] = []
    for i, seg in enumerate(segments):
        # many inputs: one decoder thread each keeps memory low; -reinit_filter 0: a frame that differs from the
        # first one (size, pixel format) is converted in place instead of rebuilding the whole graph mid-render
        args += ["-threads", "1", "-reinit_filter", "0", "-i", str(seg.resolve())]
        graph.append(f"[{i}:v]settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    last = "v0"
    offset = 0.0
    for i in range(1, len(clips)):
        offset += clips[i - 1].duration
        name, dur = trans[i]
        graph.append(f"[{last}][v{i}]xfade=transition={name}:duration={dur}:offset={offset:.3f}[x{i}]")
        last = f"x{i}"
    morphs, mo_at = [], 0.0
    for i in range(1, len(clips)):
        mo_at += clips[i - 1].duration
        if clips[i].morph is not None:
            morphs.append((mo_at, clips[i].morph))
    total = length
    audio_idx = len(clips)
    nxt = len(clips) + (1 if audio is not None else 0)   # index of the next extra input
    optical = grade.endswith("+optical")
    grade = grade.removesuffix("+optical")
    if grade:
        # One consistent "film" look over every shot: a touch of contrast and colour, soft vignette, fine grain.
        # "bw": the writer asked for a black-and-white look - AI shots and stock footage are matched to it.
        looks = {   # a film's own colour grade (the art direction picks one)
            "warm": "eq=contrast=1.05:saturation=1.04:gamma=0.98,colorbalance=rs=0.05:gs=0.01:bs=-0.06:rm=0.03:bm=-0.03",
            "cool": "eq=contrast=1.06:saturation=0.92,colorbalance=rs=-0.04:bs=0.05:rh=-0.02:bh=0.03",
            "bleach": "eq=contrast=1.18:saturation=0.62:gamma=0.97",
            "neutral": "eq=contrast=1.03:saturation=1.0"}
        if grade in looks:
            graph.append(f"[{last}]{looks[grade]},vignette=angle=PI/5,noise=alls=5:allf=t+u,format=yuv420p[graded]")
        elif grade == "paper":
            # Editorial look: warm printed-paper tone, slightly muted colour, fine paper grain, no heavy vignette.
            graph.append(f"[{last}]eq=contrast=1.05:saturation=0.9,colorbalance=rs=0.04:gs=0.02:bs=-0.05,"
                         f"noise=alls=8:allf=u,format=yuv420p[graded]")
        else:
            tone = "hue=s=0,eq=contrast=1.12:gamma=0.97" if grade == "bw" else "eq=contrast=1.06:saturation=1.08:gamma=0.98"
            graph.append(f"[{last}]{tone},vignette=angle=PI/5,noise=alls={7 if grade == 'bw' else 5}:allf=t+u,"
                         f"format=yuv420p[graded]")
        last = "graded"
    if optical:
        # The owner's optical finish (VOX_PRODUCTION_SYSTEM.md section 4): a 1 px print-registration offset between the
        # colour plates, a soft radial vignette, and a paper grain that is swapped every 10 frames instead of every
        # frame, so it reads as printed texture, not video noise.
        swap = max(1.0, FPS / 10)
        graph.append(f"color=c=0x808080:s={width}x{height}:r={swap:g}:d={length + 1:.3f},noise=alls=28:allf=t,"
                     f"gblur=sigma=0.7,fps={FPS},format=yuv420p[ograin]")
        # lens character only at the edges (PremiumBeat's recipe: chromatic split + blur 3.5 with a feathered centre
        # mask): the centre stays sharp and true
        ring = "clip(155*(hypot(X-W/2,Y-H/2)/hypot(W/2,H/2)-0.66)/0.34,0,155)"   # outer third only, at most 60%: corner labels stay readable
        # the mask never changes: drawn once here (numpy) and looped, instead of ffmpeg's per-pixel geq on every
        # frame (that alone took ~20 minutes for a one-minute film on 4 cores)
        mask_file = _optical_mask(width, height, work)
        graph.append(f"[{last}]format=yuv444p,split[oa][ob0];[ob0]rgbashift=rh=2:bh=-2:edge=smear,gblur=sigma=3.5[oblur];"
                     f"[MASKIN]format=yuv444p,trim=duration={length + 1:.3f},setpts=PTS-STARTPTS[omask];"
                     f"[oa][oblur][omask]maskedmerge,format=yuv420p,vignette=angle=PI/6[oshift]")
        graph.append("[oshift][ograin]blend=all_mode=overlay:all_opacity=0.10:shortest=1,format=yuv420p[optic]")
        last = "optic"
    tears, at = [], 0.0
    for i in range(1, len(clips)):
        at += clips[i - 1].duration
        if clips[i].transition == "tear":
            tears.append((at, trans[i][1]))
    tear_input = None
    if tears:
        # one torn-paper strip rides the wipe's seam each time
        tear_input = _tear_strip(width, height, work)
        idx = nxt + (1 if logo is not None else 0)
        sw = int(width * 0.07)
        graph.append(f"[{idx}:v]format=rgba,split={len(tears)}" + "".join(f"[tr{k}]" for k in range(len(tears))))
        for k, (o, d) in enumerate(tears):
            graph.append(f"[{last}][tr{k}]overlay=x='{width}*(1-(t-{o:.3f})/{d:.3f})-{sw // 2}':y=0:"
                         f"enable='between(t,{o:.3f},{o + d:.3f})':eval=frame:eof_action=repeat,format=yuv420p[tear{k}]")
            last = f"tear{k}"
    if morphs:
        # each shape morph rides its cut: its frames start at the cut's offset (-itsoffset) and pass through after
        base = nxt + (1 if logo is not None else 0) + (1 if tear_input is not None else 0)
        for k, (o, mdir) in enumerate(morphs):
            graph.append(f"[{base + k}:v]format=rgba,setpts=PTS-STARTPTS+{o:.3f}/TB[mk{k}]")
            graph.append(f"[{last}][mk{k}]overlay=eof_action=pass:repeatlast=0,format=yuv420p[mo{k}]")
            last = f"mo{k}"
    if logo is not None:
        # Brand watermark: about 14% of the frame width, in a corner, slightly transparent. Captions go on top.
        path, pos, opacity = logo
        m = int(min(width, height) * 0.035)
        x, y = (v.format(m=m) for v in LOGO_XY.get(pos, LOGO_XY["top-right"]))
        logo_png = _logo_still(path, int(width * 0.14) // 2 * 2, opacity, work)
        graph.append(f"[{nxt}:v]format=rgba[logo]")
        # one still frame, held for the whole video (eof_action=repeat)
        graph.append(f"[{last}][logo]overlay=x={x}:y={y}:eof_action=repeat,format=yuv420p[vlogo]")
        last = "vlogo"
    if captions is not None:
        # captions are timed for the whole film: a later piece of a long film shifts its clock to film time first
        shift = (f"setpts=PTS+{t0:.3f}/TB,", ",setpts=PTS-STARTPTS") if t0 else ("", "")
        graph.append(f"[{last}]{shift[0]}{ff.ass_filter(captions.name)}{shift[1]}[vout]")
        last = "vout"
    if fade_out and total > 3:
        # the ending fades to black over the last second instead of stopping dead
        graph.append(f"[{last}]fade=t=out:st={total - 1.0:.3f}:d=1[vend]")
        last = "vend"
    if audio is not None:
        args += ["-i", str(audio)]
    if logo is not None:
        args += ["-i", str(logo_png)]
    if tear_input is not None:
        args += ["-i", str(tear_input)]
    for _, mdir in morphs:
        args += ["-framerate", str(FPS), "-i", str((mdir / "m_%03d.png").resolve())]
    if optical:
        mask_idx = args.count("-i")
        args += ["-stream_loop", "-1", "-f", "rawvideo", "-pix_fmt", "yuv444p", "-s", f"{width}x{height}",
                 "-framerate", str(FPS), "-i", str(mask_file.resolve())]
        graph = [g.replace("[MASKIN]", f"[{mask_idx}:v]") for g in graph]
    # -filter_complex_threads: every filter in a graph otherwise gets a thread per CPU core. With ~200 shots that
    # was over a thousand threads on 4 cores, and tens of thousands on a GPU server that shows 64+ cores, which
    # ran into the thread limit ("Failed to configure output pad ... Resource temporarily unavailable").
    args += ["-filter_complex_threads", "2",
             "-filter_complex", ";".join(graph), "-map", f"[{last}]"]
    if audio is not None:
        args += ["-map", f"{audio_idx}:a"]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    args += ["-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE)] if audio is not None else ["-an"]
    args += ["-movflags", "+faststart", "-t", f"{total:.3f}", str(out)]
    ff.run(args, cancel, cwd=work)
