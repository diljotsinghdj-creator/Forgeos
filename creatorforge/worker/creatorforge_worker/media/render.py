"""Smart Editor / Auto Edit: assembles scene stills, narration, music, transitions, captions
and overlays into the final H.264/AAC MP4 with FFmpeg."""
from __future__ import annotations

import hashlib
import re
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
    "iris": ("circleopen", 0.45),
    # paper tear: a wipe whose edge is a ragged strip of torn white paper (drawn over the seam, see render_video)
    "tear": ("wipeleft", 0.45),
    # match cut / zoom-through: the old shot flies in, a quick blend, the new one lands from close (see _segment_args)
    "match": ("fade", 0.22),
}
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
    exit_zoom: bool = False   # match cut out of this shot: the camera accelerates into it at the end
    enter_zoom: bool = False  # match cut into this shot: it starts close and settles
    stepped: bool = False     # a drawn graphic: played at 12 frames a second, the hand-made look of video essays


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


def mix_audio(narration: Path, music: Path | None, total: float, out: Path, cancel: threading.Event,
              sfx: list[tuple[Path, float, float]] | None = None, dips: list[tuple[float, float]] | None = None) -> None:
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
                     f"afade=t=in:d=1,afade=t=out:st={fade_out:.3f}:d=2,atrim=0:{total:.3f}"
                     # the music drops away under a chapter card or a big statement, then comes back
                     + (f",volume='if({'+'.join(f'between(t,{a:.2f},{b:.2f})' for a, b in dips)},0.2,1)':eval=frame"
                        if dips else "") + "[m]")
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
    # Every video lands at the loudness social platforms normalise to (-14 LUFS, true peak under -1.5 dB), so it is
    # never quieter than the next video in the feed and never clips.
    level = f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11"
    if len(mix) == 1:
        graph.append(f"[n]{level}[a]")
    else:
        graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,alimiter=limit=0.95,{level}[a]")
    ff.run([*args, "-filter_complex", ";".join(graph), "-map", "[a]", "-t", f"{total:.3f}",
            "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(out)], cancel)


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
        base = (("fps=12," if c.stepped else "") + f"setpts={stretch:.4f}*(PTS-STARTPTS),"
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
        k = len(src) // 2
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
    return (f"[{idx}:v]subtitles=filename='{ass}',colorkey=0xFF00FF:0.28:0.12,format=rgba,"
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
        if grade == "paper":
            # Editorial look: warm printed-paper tone, slightly muted colour, fine paper grain, no heavy vignette.
            graph.append(f"[{last}]eq=contrast=1.05:saturation=0.9,colorbalance=rs=0.04:gs=0.02:bs=-0.05,"
                         f"noise=alls=8:allf=u,format=yuv420p[graded]")
        else:
            tone = "hue=s=0,eq=contrast=1.12:gamma=0.97" if grade == "bw" else "eq=contrast=1.06:saturation=1.08:gamma=0.98"
            graph.append(f"[{last}]{tone},vignette=angle=PI/5,noise=alls={7 if grade == 'bw' else 5}:allf=t+u,"
                         f"format=yuv420p[graded]")
        last = "graded"
    tears, at = [], 0.0
    for i in range(1, len(clips)):
        at += clips[i - 1].duration
        if clips[i].transition == "tear":
            tears.append((at, trans[i][1]))
    tear_input = None
    if tears:
        # one torn-paper strip rides the wipe's seam each time
        tear_input = _tear_strip(width, height, work)
        idx = audio_idx + 1 + (1 if logo is not None else 0)
        sw = int(width * 0.07)
        graph.append(f"[{idx}:v]format=rgba,split={len(tears)}" + "".join(f"[tr{k}]" for k in range(len(tears))))
        for k, (o, d) in enumerate(tears):
            graph.append(f"[{last}][tr{k}]overlay=x='{width}*(1-(t-{o:.3f})/{d:.3f})-{sw // 2}':y=0:"
                         f"enable='between(t,{o:.3f},{o + d:.3f})':eval=frame,format=yuv420p[tear{k}]")
            last = f"tear{k}"
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
    if tear_input is not None:
        args += ["-loop", "1", "-i", str(tear_input)]
    args += ["-filter_complex", ";".join(graph), "-map", f"[{last}]", "-map", f"{audio_idx}:a",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-movflags", "+faststart",
             "-t", f"{total:.3f}", str(out)]
    ff.run(args, cancel, cwd=work)
    return total
