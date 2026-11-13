"""Concat the shot clips, lay each narration line at its shot start (+0.15 s), add the studio score under it, ducked."""
import json, subprocess, sys
from pathlib import Path
D = Path(__file__).resolve().parent
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
from creatorforge_worker.studio import score
durs = json.load(open(D / "durations.json")); ks = list(durs)
starts, t = {}, 0.0
for k in ks: starts[k] = t; t += round(durs[k] * 24) / 24
total = t
(D / "render/list.txt").write_text("".join(f"file '{k}.mp4'\n" for k in ks))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(D / "render/list.txt"), "-c", "copy", str(D / "render/picture.mp4")], check=True)
acts = [("hook", 0, starts["s03"]), ("world", starts["s03"], starts["s08"] - starts["s03"]),
        ("consequences", starts["s08"], starts["s11"] - starts["s08"]), ("ending", starts["s11"], total - starts["s11"])]
sc = score.compose(acts, "pulse", D / "render/score")
args, mix = [], []
vk = [k for k in ks if (D / "audio" / f"{k}.wav").exists()]
for i, k in enumerate(vk):
    args += ["-i", str(D / "audio" / f"{k}.wav")]; ms = int((starts[k] + 0.15) * 1000)
    mix.append(f"[{i + 1}:a]adelay={ms}|{ms}[v{i}]")
n = len(vk); args += ["-i", str(sc)]
g = ";".join(mix) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad,atrim=0:{total:.3f},aformat=channel_layouts=stereo,asplit[vo][key];" \
    f"[{n + 1}:a]volume=2.2[m];[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];[vo][md]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5[a]"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(D / "render/picture.mp4"), *args, "-filter_complex", g,
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(D / "render/panama_60.mp4")], check=True)
json.dump({"starts": starts, "total": total, "score": score.LAST_HOW}, open(D / "render/timeline.json", "w"), indent=1)
print(round(total, 2), score.LAST_HOW)
