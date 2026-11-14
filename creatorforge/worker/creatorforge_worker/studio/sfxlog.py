"""The owner's [SFX_LOG] (creatorforge/channels/VOX_PRODUCTION_SYSTEM.md, section 5): every cut gets a timestamped
foley, room-tone and music cue table, and the mix follows it.

- Foley is low-passed under 800 Hz and lands 2 frames before its cut, so the sound leads the picture.
- A stereo room-tone bed runs under the whole film at -35 dB, so silence never sounds like a dropout.
- Where the music drops out, an analog noise floor (soft crackle) holds the space at -42 dB.

Written as SFX_LOG.md next to PRESHOW.md."""
from __future__ import annotations

from pathlib import Path

from ..media import ff

FOLEY_LOWPASS_HZ = 800
LEAD_FRAMES = 2
ROOM_TONE_DB = -35.0
NOISE_FLOOR_DB = -42.0


def _gain(db: float) -> float:
    return round(10 ** (db / 20), 4)


def treat_foley(hits: list[tuple], fps: int) -> list[tuple]:
    """Each effect 2 frames early and low-passed: (path, start, gain, pan, lowpass Hz)."""
    lead = LEAD_FRAMES / max(1, fps)
    return [(h[0], max(0.0, h[1] - lead), h[2], h[3] if len(h) > 3 else 0.0, FOLEY_LOWPASS_HZ) for h in hits]


def music_drops(timeline: list[dict]) -> list[tuple[float, float]]:
    """Stretches where the score is silent ("-" in the timeline), merged."""
    out: list[list[float]] = []
    for t in timeline:
        if t.get("music") == "-":
            if out and abs(out[-1][1] - t["start"]) < 0.05:
                out[-1][1] = t["end"]
            else:
                out.append([t["start"], t["end"]])
    return [(a, b) for a, b in out if b - a >= 1.0]


def floor_beds(total: float, timeline: list[dict], audio_dir: Path) -> list[tuple]:
    """The room tone under everything, and the noise floor in each music drop, as files for the mixer."""
    audio_dir.mkdir(parents=True, exist_ok=True)
    room = audio_dir / "room_tone.wav"
    # brown noise, band-limited like a quiet room (no hiss, no rumble), decorrelated left and right
    ff.run(["-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.5:seed=7:d={total + 0.5:.2f}",
            "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.5:seed=11:d={total + 0.5:.2f}",
            "-filter_complex", "[0:a][1:a]join=inputs=2:channel_layout=stereo,highpass=f=60,lowpass=f=1800[a]",
            "-map", "[a]", "-ar", "48000", str(room)])
    beds = [(room, 0.0, _gain(ROOM_TONE_DB), 0.0, 0)]
    for k, (a, b) in enumerate(music_drops(timeline)):
        crackle = audio_dir / f"noise_floor_{k}.wav"
        # a vinyl-like floor: pink hiss plus sparse clicks, rolled off at the top
        ff.run(["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.4:seed={k + 3}:d={b - a:.2f}",
                "-f", "lavfi", "-i", f"anoisesrc=color=white:amplitude=1:seed={k + 5}:d={b - a:.2f}",
                "-filter_complex", "[1:a]agate=threshold=0.97:ratio=20,volume=0.6[c];[0:a][c]amix=inputs=2:normalize=0,"
                "lowpass=f=5000,afade=t=in:d=0.3,afade=t=out:st=" + f"{max(0.0, b - a - 0.4):.2f}" + ":d=0.4[a]",
                "-map", "[a]", "-ac", "2", "-ar", "48000", str(crackle)])
        beds.append((crackle, a, _gain(NOISE_FLOOR_DB), 0.0, 0))
    return beds


def _ts(s: float, fps: int) -> str:
    m, r = divmod(max(0.0, s), 60)
    return f"{int(m):02d}:{int(r):02d}:{int(round((r - int(r)) * fps)):02d}"


def markdown(title: str, timeline: list[dict], foley: list[tuple], ambience: list[tuple], floor: list[tuple],
             fps: int, music: str) -> str:
    """The cue table, in time order: what plays, where, how loud and how it is treated."""
    def scene_at(t: float) -> str:
        return next((x["scene"] for x in timeline if x["start"] - 0.2 <= t < x["end"]), timeline[-1]["scene"] if timeline else "-")

    rows = []
    for h in foley:
        rows.append((h[1], scene_at(h[1] + LEAD_FRAMES / fps), "Foley", Path(h[0]).stem, h[2],
                     f"low-passed {FOLEY_LOWPASS_HZ} Hz, {LEAD_FRAMES} frames before the cut"))
    for b in ambience:
        rows.append((b[1], scene_at(b[1]), "Ambience", Path(b[0]).stem.split("_")[0], b[2], "the place's own sound, under the voice"))
    for b in floor:
        if Path(b[0]).stem == "room_tone":
            rows.append((b[1], "all", "Room tone", "stereo room bed", b[2], f"{ROOM_TONE_DB:.0f} dB under the whole film"))
        else:
            rows.append((b[1], scene_at(b[1]), "Noise floor", "analog crackle", b[2], f"{NOISE_FLOOR_DB:.0f} dB while the music is out"))
    prev = None
    for t in timeline:
        mood = t.get("music", "-")
        if mood != prev:
            rows.append((t["start"], t["scene"], "Music", mood if mood != "-" else "drop out", None,
                         f"score: {music}" if mood != "-" else "silence held by the noise floor"))
            prev = mood
    rows.sort(key=lambda r: r[0])
    import math
    L = [f"# SFX log: {title}", "", f"Timecode is mm:ss:ff at {fps} fps. Levels are relative to full scale before the final -14 LUFS "
         "loudness pass.", "", "| Time | Scene | Layer | Cue | Level | Treatment |", "|---|---|---|---|---|---|"]
    for at, sc, layer, cue, g, note in rows:
        lvl = "-" if g is None else (f"{20 * math.log10(g):.0f} dB" if g > 0 else "off")
        L.append(f"| {_ts(at, fps)} | {sc} | {layer} | {cue} | {lvl} | {note} |")
    return "\n".join(L) + "\n"
