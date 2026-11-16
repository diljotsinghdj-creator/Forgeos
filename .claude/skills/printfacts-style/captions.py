#!/usr/bin/env python3
"""House captions: exact word timing (media/wordtimes.py), 4-word groups on a dark box, Anton white with the current
word in signature yellow; then -14 LUFS via ffmpeg-skill. usage: captions.py in.mp4 out.mp4 [shorts|youtube] [script.txt] [printfacts|dragonpsych]"""
import subprocess, sys, tempfile, wave
from pathlib import Path
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
from creatorforge_worker.media.wordtimes import word_times

FONTS = "/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts"
SKILL = Path(__file__).resolve().parent.parent / "ffmpeg-skill" / "scripts"
src, out = sys.argv[1], sys.argv[2]
plat = sys.argv[3] if len(sys.argv) > 3 else "youtube"
prompt = Path(sys.argv[4]).read_text() if len(sys.argv) > 4 and sys.argv[4] else ""
chan = sys.argv[5] if len(sys.argv) > 5 else "printfacts"
SIGNAL = {"printfacts": "&H46D0F7&", "dragonpsych": "&H3689ED&"}[chan]   # ASS colours are BGR: #F7D046, #ED8936
W, H = (1080, 1920) if plat == "shorts" else (1920, 1080)
size, marg = (64, 380) if plat == "shorts" else (54, 90)
tmp = Path(tempfile.mkdtemp())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", str(tmp / "a.wav")], check=True)
words = word_times(tmp / "a.wav", prompt)
ts = lambda t: f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
ass = [f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n\n[V4+ Styles]\n"
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
       f"Style: C,Anton,{size},&H00FFFFFF,&H00FFFFFF,&HD20C0A0A,&HD20C0A0A,0,0,0,0,100,100,1,0,3,14,0,2,60,60,{marg},1\n\n[Events]\n"
       "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"]
for i, (w, s, e) in enumerate(words):
    g0 = i - i % 4; grp = words[g0:g0 + 4]
    end = words[i + 1][1] if i + 1 < len(words) and words[i + 1][1] - e < .6 else e + .25
    txt = " ".join(("{\\c" + SIGNAL + "}" + x + "{\\c&HFFFFFF&}") if g0 + j == i else x for j, (x, _, _) in enumerate(grp))
    ass.append(f"Dialogue: 0,{ts(s)},{ts(end)},C,,0,0,0,,{txt}\n")
(tmp / "c.ass").write_text("".join(ass))
mid = tmp / "c.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"ass={tmp / 'c.ass'}:fontsdir={FONTS}", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-c:a", "copy", str(mid)], check=True)
subprocess.run([sys.executable, str(SKILL / "loudness.py"), str(mid), "-o", out, "-I", "-14", "--tp", "-1", "--overwrite"], check=True)
print("captions:", len(words), "words ->", out)
