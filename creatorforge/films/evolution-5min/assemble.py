"""Concat the shots (timeline order), lay each narration line at its shot's start (+0.15 s), score under it, ducked."""
import json, subprocess, sys
from pathlib import Path
D = Path(__file__).resolve().parent
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
from creatorforge_worker.studio import score
TL = json.load(open(D / "timeline.json")); shots = TL["shots"]
starts, t = {}, 0.0
for s in shots:
    starts[s["shot"]] = t; s["t"] = t; t += round(s["dur"] * 24) / 24
total = t
(D / "render/list.txt").write_text("".join(f"file '{s['shot']}.mp4'\n" for s in shots))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(D / "render/list.txt"), "-c", "copy", str(D / "render/picture_raw.mp4")], check=True)
# optical finish: a soft lens vignette and a touch of halation over the whole film
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(D / "render/picture_raw.mp4"), "-vf",
                "split[a][b];[b]gblur=sigma=18,colorlevels=rimin=0.55:gimin=0.55:bimin=0.55[g];[a][g]blend=all_mode=screen:all_opacity=0.18,vignette=angle=PI/5:mode=forward",
                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(D / "render/picture.mp4")], check=True)
# sound design: cues derived from each shot's own animation events (built-in synthesised SFX, nothing licensed)
import re
from creatorforge_worker.media import sfx_builtin
bank = {p.stem: p for p in sfx_builtin.ensure(D / "render/sfx")}
cues = []
for s in shots:
    h = open(D / "shots" / f"{s['shot']}.html").read()
    mine = [(0.0, "impact_deep" if s["shot"].startswith("K") else "whoosh_paper", -18 if not s["shot"].startswith("K") else -12)]
    for m in re.finditer(r'class="el" data-in="(\w+)" data-at="([\d.]+)"[^>]*>(?:<div class="(\w+)|<img|<svg)?', h):
        k, at, cls = m.group(1), float(m.group(2)), m.group(3) or ""
        if cls == "stamp": mine.append((at, "impact_punch", -14))
        elif cls == "hand": mine.append((at, "scribble_pen", -20))
        elif k == "drop" and cls == "card": mine.append((at, "whoosh_paper", -16))
    mine.sort(); kept = []
    for c in mine:
        if c[0] < s["dur"] - .2 and all(abs(c[0] - k2[0]) > .35 for k2 in kept) and len(kept) < 3: kept.append(c)
    cues += [(s["t"] + at, name, db, s["shot"]) for at, name, db in kept if name in bank]
with open(D / "SFX_LOG.md", "w") as f:
    f.write("# SFX_LOG: evolution-5min\n\nAll sounds are the studio's built-in synthesised effects (ffmpeg, nothing licensed). Cues come from each shot's own animation events.\n\n| time (s) | shot | sound | level |\n|---|---|---|---|\n")
    f.writelines(f"| {t0:.2f} | {sh} | {nm} | {db} dB |\n" for t0, nm, db, sh in cues)
sargs, smix = [], []
for i, (t0, nm, db, _) in enumerate(cues):
    sargs += ["-i", str(bank[nm])]; ms = int(t0 * 1000)
    smix.append(f"[{i}:a]volume={db}dB,adelay={ms}|{ms}[s{i}]")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *sargs, "-filter_complex", ";".join(smix) + ";" + "".join(f"[s{i}]" for i in range(len(cues))) +
                f"amix=inputs={len(cues)}:normalize=0,apad,atrim=0:{total:.3f},aformat=channel_layouts=stereo[a]", "-map", "[a]", "-ar", "48000", str(D / "render/sfx.wav")], check=True)
print(len(cues), "sfx cues")
acts = [("hook", 0, starts["K2"]), ("world", starts["K2"], starts["K3"] - starts["K2"]), ("investigation", starts["K3"], starts["L43"] - starts["K3"]),
        ("consequences", starts["L43"], starts["K4"] - starts["L43"]), ("ending", starts["K4"], total - starts["K4"])]
sc = score.compose(acts, "pulse", D / "render/score")
lines = [(s["line"], s["t"]) for s in shots if s["line"]]
args, mix = [], []
for i, (ln, st) in enumerate(lines):
    args += ["-i", str(D / "audio" / f"{ln}.wav")]; ms = int((st + 0.15) * 1000)
    mix.append(f"[{i + 1}:a]adelay={ms}|{ms}[v{i}]")
n = len(lines); args += ["-i", str(sc), "-i", str(D / "render/sfx.wav")]
g = ";".join(mix) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad,atrim=0:{total:.3f},aformat=channel_layouts=stereo,asplit[vo][key];" \
    f"[{n + 1}:a]volume=2.2[m];[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];[vo][md][{n + 2}:a]amix=inputs=3:normalize=0,loudnorm=I=-15:TP=-1.5[a]"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(D / "render/picture.mp4"), *args, "-filter_complex", g,
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(D / "render/evolution_5min.mp4")], check=True)
json.dump({"starts": starts, "total": total, "score": score.LAST_HOW}, open(D / "render/timeline_out.json", "w"), indent=1)
print(round(total, 2), score.LAST_HOW)
