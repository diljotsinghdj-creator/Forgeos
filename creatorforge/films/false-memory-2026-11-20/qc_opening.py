"""Checks on the finished opening test (video/false-memory-opening-test.mp4): the file, the exact minute, loudness, where the music is out,
that no caption sits over the list or the test words, and check sheets cut from the finished file.
usage: python3 qc_opening.py [out_dir]"""
import json, re, subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

D = Path(__file__).resolve().parent
V = D / "video"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else V / "qc"
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((V / "shots.json").read_text()); MP4 = V / f"{cfg['slug']}.mp4"; PRE = V / "work" / "premix.mp4"
tl = json.loads((V / "timeline.json").read_text()); by = {r["id"]: r for r in tl}; sh = {s["id"]: s for s in cfg["shots"]}
run = lambda *a: subprocess.run(a, capture_output=True, text=True)

# 1. the file
pr = json.loads(run("ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height,r_frame_rate,sample_rate", "-of", "json", str(MP4)).stdout)
vs = next(s for s in pr["streams"] if s.get("width")); au = next(s for s in pr["streams"] if s.get("sample_rate"))
dur = float(pr["format"]["duration"])
print(f"file: {MP4.name} · {dur:.2f} s · {vs['width']}x{vs['height']} · {vs['r_frame_rate']} fps · {vs['codec_name']} + {au['codec_name']} {au['sample_rate']} Hz · {int(pr['format']['size']) / 1e6:.1f} MB")

# 2. the minute
first = next(r for r in tl if r["page"] == "m_w01"); test = next(r for r in tl if r["page"] == "m_32_test"); third = next(r for r in tl if r["page"] == "t_sleep")
print(f"minute: first word at {first['start']:.3f} s, test at {test['start']:.3f} s, gap {(test['start'] - first['start']) * 24:.2f} frames (1440 = 60 s) · third test word at {third['start']:.2f} s")

# 3. loudness
e = run("ffmpeg", "-nostdin", "-i", str(MP4), "-af", "ebur128=peak=true", "-f", "null", "-").stderr
summary = e[e.rindex("Summary:"):]
print("loudness:", re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1), "LUFS integrated · true peak", re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary).group(1), "dBFS · range", re.search(r"LRA:\s+(-?[\d.]+) LU", summary).group(1), "LU")

# 4. where the music is out: the level in a gap with no voice and no effect, inside and outside the muted stretches
wav = OUT / "mix.wav"; run("ffmpeg", "-nostdin", "-y", "-i", str(MP4), "-vn", "-ac", "1", "-ar", "48000", str(wav))
with wave.open(str(wav)) as w:
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
db = lambda a, b: 20 * np.log10(max(1e-7, float(np.sqrt(np.mean(x[int(a * 48000):int(b * 48000)] ** 2)))))
w3 = next(r for r in tl if r["page"] == "m_w03"); clip = next(r for r in tl if r["page"] == "m_23_clip"); tw2 = next(r for r in tl if r["page"] == "t_door"); hook = tl[0]
print(f"music: quiet gap in the list {db(w3['start'] + .95, w3['start'] + 1.35):.0f} dBFS · after a test word {db(tw2['start'] + 1.2, tw2['start'] + 1.9):.0f} dBFS · "
      f"under the clip (music on) {db(clip['start'] + .6, clip['start'] + 1.6):.0f} dBFS")

# 5. captions: none over the list or the test words (the picture there must match the uncaptioned picture), some elsewhere
def grab(src, t):
    f = OUT / "_f.png"; run("ffmpeg", "-nostdin", "-y", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", str(f))
    return np.asarray(Image.open(f).convert("L"), dtype=np.float64)
box = lambda im: im[880:1012, 300:1620]
worst_plain = 0.0
for r in tl:
    if sh[r["id"]].get("nocap"):
        t = r["start"] + sh[r["id"]].get("pre", 0) + r["vdur"] * .6
        worst_plain = max(worst_plain, float(np.abs(box(grab(MP4, t)) - box(grab(PRE, t))).mean()))
some = []
for r in tl:
    if r["vdur"] > 1.2 and not sh[r["id"]].get("nocap"):
        t = r["start"] + sh[r["id"]].get("pre", 0) + r["vdur"] * .5
        some.append(float(np.abs(box(grab(MP4, t)) - box(grab(PRE, t))).mean()))
print(f"captions: largest difference from the uncaptioned picture over the list and test words {worst_plain:.2f} (0 = none) · over spoken lines elsewhere: median {np.median(some):.1f}, "
      f"{sum(v > 2 for v in some)} of {len(some)} lines carry a caption at their midpoint")

# 6. check sheets from the finished file: three moments of every shot
times = []
for r in tl:
    for f in ((.5,) if r["dur"] < 1.6 else (.15, .6, .97)):
        times.append((r["start"] + min(r["dur"] - .05, r["dur"] * f), r["id"], r["page"]))
W, H, C, R = 512, 288, 5, 5
for k in range(0, len(times), C * R):
    sheet = Image.new("RGB", (W * C, (H + 20) * R), (20, 24, 36)); d = ImageDraw.Draw(sheet)
    for j, (t, sid, pg) in enumerate(times[k:k + C * R]):
        f = OUT / "_g.jpg"; run("ffmpeg", "-nostdin", "-y", "-ss", f"{t:.3f}", "-i", str(MP4), "-frames:v", "1", "-q:v", "3", str(f))
        xx, yy = (j % C) * W, (j // C) * (H + 20)
        sheet.paste(Image.open(f).resize((W, H)), (xx, yy + 20)); d.text((xx + 5, yy + 4), f"{sid} {pg} @ {int(t) // 60}:{t % 60:05.2f}", fill=(240, 244, 248))
    out = OUT / f"final_{k // (C * R) + 1:02d}.jpg"; sheet.save(out, quality=85); print(out)
for f in ("_f.png", "_g.jpg", "mix.wav"):
    (OUT / f).unlink(missing_ok=True)
