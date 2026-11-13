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
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(D / "render/list.txt"), "-c", "copy", str(D / "render/picture.mp4")], check=True)
acts = [("hook", 0, starts["K2"]), ("world", starts["K2"], starts["K3"] - starts["K2"]), ("investigation", starts["K3"], starts["L43"] - starts["K3"]),
        ("consequences", starts["L43"], starts["K4"] - starts["L43"]), ("ending", starts["K4"], total - starts["K4"])]
sc = score.compose(acts, "pulse", D / "render/score")
lines = [(s["line"], s["t"]) for s in shots if s["line"]]
args, mix = [], []
for i, (ln, st) in enumerate(lines):
    args += ["-i", str(D / "audio" / f"{ln}.wav")]; ms = int((st + 0.15) * 1000)
    mix.append(f"[{i + 1}:a]adelay={ms}|{ms}[v{i}]")
n = len(lines); args += ["-i", str(sc)]
g = ";".join(mix) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad,atrim=0:{total:.3f},aformat=channel_layouts=stereo,asplit[vo][key];" \
    f"[{n + 1}:a]volume=2.2[m];[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];[vo][md]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5[a]"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(D / "render/picture.mp4"), *args, "-filter_complex", g,
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(D / "render/evolution_5min.mp4")], check=True)
json.dump({"starts": starts, "total": total, "score": score.LAST_HOW}, open(D / "render/timeline_out.json", "w"), indent=1)
print(round(total, 2), score.LAST_HOW)
