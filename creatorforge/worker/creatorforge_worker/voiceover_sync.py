"""Put your own voice-over (ElevenLabs or a recording) on a finished production, line for line.

    python -m creatorforge_worker.voiceover_sync <job id> <voice-over.mp3> [--out final.mp4] [--name "in the app"]

The production's pictures were timed to CreatorForge's own narration. This finds where each script line starts in
your voice-over (from its pauses: lines end on the longest pauses, and speech runs at a steady rate in between) and
where it starts in CreatorForge's narration (words.json), then stretches or shrinks each line's stretch of video so
every picture lands on its line, and replaces the audio with your voice-over at -14 LUFS. Captions burned into the
video move with their line. Writes <job>/work/voiceover_sync.json with both timings, so a bad match is easy to see.

Use the same script in both: the voice-over must say the production's lines, in order."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def _letters(s: str) -> int:
    return len(re.sub(r"\s", "", s))


def _pauses(audio: Path, noise_db: float = -38.0, min_s: float = 0.3) -> tuple[list, float]:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(audio), "-af", f"silencedetect=noise={noise_db}dB:d={min_s}",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(audio)], capture_output=True, text=True).stdout)
    gaps = [(a, b) for a, b in zip(st, en) if a > 0.05 and b < dur - 0.05]
    return gaps, dur


def line_starts_in_audio(audio: Path, lines: list[str]) -> tuple[list[float], float]:
    """Where each line starts in a recording: the line breaks are chosen among the pauses so each lands near its
    share of the speaking time (by letters), long pauses preferred (a line ends on a breath)."""
    gaps, dur = _pauses(audio)
    if len(lines) <= 1 or len(gaps) < len(lines) - 1:
        raise ValueError(f"found {len(gaps)} pauses for {len(lines)} lines - is this the right voice-over?")
    segs, t = [], 0.0
    for a, b in gaps:
        segs.append((t, a))
        t = b
    segs.append((t, dur))
    speech = sum(b - a for a, b in segs)

    def speech_pos(x):
        acc = 0.0
        for a, b in segs:
            if x <= a:
                return acc
            if x < b:
                return acc + (x - a)
            acc += b - a
        return acc
    w = [_letters(l) for l in lines]
    tot = sum(w)
    target = [sum(w[:k + 1]) / tot * speech for k in range(len(lines) - 1)]
    pos = [speech_pos(a) for a, _ in gaps]
    K, G, INF = len(lines) - 1, len(gaps), float("inf")
    cost = lambda k, g: (pos[g] - target[k]) ** 2 - 60.0 * (gaps[g][1] - gaps[g][0])  # noqa: E731
    dp = [[INF] * G for _ in range(K)]
    back = [[-1] * G for _ in range(K)]
    for g in range(G):
        dp[0][g] = cost(0, g)
    for k in range(1, K):
        best, bi = INF, -1
        for g in range(G):
            if g > 0 and dp[k - 1][g - 1] < best:
                best, bi = dp[k - 1][g - 1], g - 1
            if bi >= 0:
                dp[k][g], back[k][g] = best + cost(k, g), bi
    g = min(range(G), key=lambda x: dp[K - 1][x])
    pick = [g]
    for k in range(K - 1, 0, -1):
        g = back[k][g]
        pick.append(g)
    pick.reverse()
    return [0.0] + [gaps[p][1] for p in pick], dur


def line_starts_in_words(words: list[dict], lines: list[str]) -> list[float]:
    """Where each line starts in CreatorForge's narration: by word count when the timed words match the script,
    else by each line's share of the letters."""
    counts = [len(l.split()) for l in lines]
    if sum(counts) == len(words):
        idx, starts = 0, []
        for c in counts:
            starts.append(float(words[idx]["start"]))
            idx += c
        return starts
    letters = [_letters(w["text"]) for w in words]
    total = sum(letters) or 1
    w = [_letters(l) for l in lines]
    starts, acc, i = [], 0, 0
    for k in range(len(lines)):
        share = sum(w[:k]) / sum(w) * total
        while i < len(words) - 1 and acc + letters[i] <= share:
            acc += letters[i]
            i += 1
        starts.append(float(words[i]["start"]) if k else 0.0)
    return starts


def _loudnorm(audio: Path, out: Path) -> None:
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(audio), "-af",
                            "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-af",
                    f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                    f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
                    "linear=true", "-ar", "48000", str(out)], check=True)


def sync(video: Path, words: list[dict], lines: list[str], voice: Path, out: Path, report: Path | None = None) -> dict:
    vo_starts, vo_end = line_starts_in_audio(voice, lines)
    cf_starts = line_starts_in_words(words, lines)
    vdur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(video)], capture_output=True, text=True).stdout)
    tail = min(vdur, float(words[-1]["end"]) + 0.5) if words else vdur   # after the last word: silence, not speech
    cf_bounds = cf_starts + [max(tail, cf_starts[-1] + 0.3)]
    vo_bounds = vo_starts + [vo_end]
    parts, labels = [], []
    for k in range(len(lines)):
        a, b = cf_bounds[k], cf_bounds[k + 1]
        if b - a < 0.05:
            raise ValueError(f"line {k + 1} has no video time - the narration and the script don't match")
        f = (vo_bounds[k + 1] - vo_bounds[k]) / (b - a)
        parts.append(f"[0:v]trim=start={a:.4f}:end={b:.4f},setpts=(PTS-STARTPTS)*{f:.6f}[v{k}]")
        labels.append(f"[v{k}]")
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout.strip() or "30"
    graph = ";".join(parts) + f";{''.join(labels)}concat=n={len(labels)}:v=1:a=0,fps={fps}[v]"
    norm = out.with_name(out.stem + ".voice.wav")
    _loudnorm(voice, norm)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(norm), "-filter_complex"]
    cmd += [graph, "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{vo_end:.3f}", "-movflags", "+faststart",
            str(out)]
    subprocess.run(cmd, check=True)
    norm.unlink(missing_ok=True)
    info = {"lines": [{"line": l, "creatorforge_start": round(c, 2), "voiceover_start": round(v, 2),
                       "stretch": round((vo_bounds[k + 1] - vo_bounds[k]) / (cf_bounds[k + 1] - cf_bounds[k]), 3)}
                      for k, (l, c, v) in enumerate(zip(lines, cf_starts, vo_starts))],
            "voiceover_seconds": round(vo_end, 2), "video_seconds_before": round(vdur, 2), "out": str(out)}
    if report:
        report.write_text(json.dumps(info, indent=1, ensure_ascii=False))
    return info


def main(argv: list[str] | None = None) -> None:
    from .config import Config
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("job")
    ap.add_argument("voiceover")
    ap.add_argument("--out", default="")
    ap.add_argument("--name", default="", help="name in the Asset Library")
    ap.add_argument("--no-library", action="store_true", help="don't add the result to the Asset Library")
    a = ap.parse_args(argv)
    cfg = Config.from_env()
    jdir = cfg.jobs_dir / a.job
    job = json.loads((jdir / "job.json").read_text())
    if job.get("status") != "READY" or not job.get("result"):
        raise SystemExit(f"production {a.job} is not finished yet (status {job.get('status')})")
    lines = [l.strip() for l in (job["spec"].get("script") or "").splitlines() if l.strip()]
    if not lines:
        raise SystemExit("this production was not made from a script (Generate -> Script)")
    words = json.loads((jdir / "words.json").read_text())
    out = Path(a.out) if a.out else jdir / "work" / "voiceover_final.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    info = sync(jdir / job["result"]["file"], words, lines, Path(a.voiceover), out, jdir / "work" / "voiceover_sync.json")
    for k, r in enumerate(info["lines"], 1):
        print(f"{k:2d}  CF {r['creatorforge_start']:6.2f}s -> VO {r['voiceover_start']:6.2f}s  x{r['stretch']:.2f}  "
              f"{r['line'][:50]}")
    print(f"\nDone: {out}  ({info['voiceover_seconds']} s)")
    if not a.no_library:                               # into the Asset Library, so the app can play and save it
        import shutil

        from .api import _check_asset
        from .library import Library
        tmp = out.with_name(out.stem + ".upload.mp4")
        shutil.copyfile(out, tmp)
        name = a.name or f"{job.get('title') or job['spec'].get('idea') or a.job} (own voice-over)"[:80]
        asset = Library(cfg.data_dir / "library", cfg.allow_mock).assets.add("video", name, tmp, ".mp4",
                                                                  lambda p: _check_asset("video", p))
        print(f"In the app: Library -> Assets -> video -> '{name}' (asset {asset['id']})")


if __name__ == "__main__":
    main()
