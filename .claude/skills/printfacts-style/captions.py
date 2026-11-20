#!/usr/bin/env python3
"""House captions: exact word timing (media/wordtimes.py), 4-word groups on a dark box, Anton white with the current
word in signature yellow; then -14 LUFS via ffmpeg-skill. usage: captions.py in.mp4 out.mp4 [shorts|youtube] [script.txt] [printfacts|dragonpsych] [breaks.json] [words.json]
breaks.json (optional): a list of times in seconds that no caption group may span, so a group never shows a word from the far side of that cut
(a test word, a reveal) before it is spoken.
words.json (optional): [[word, start_s, end_s], ...] already timed by the caller (its own script, line by line). The mix is then not transcribed,
so no word can be dropped or misheard."""
import json, subprocess, sys, tempfile, wave
from pathlib import Path
sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
from creatorforge_worker.media.wordtimes import word_times

FONTS = "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts"
SKILL = Path(__file__).resolve().parent.parent / "ffmpeg-skill" / "scripts"
src, out = sys.argv[1], sys.argv[2]
plat = sys.argv[3] if len(sys.argv) > 3 else "youtube"
prompt = Path(sys.argv[4]).read_text() if len(sys.argv) > 4 and sys.argv[4] else ""
chan = sys.argv[5] if len(sys.argv) > 5 else "printfacts"
breaks = sorted(json.loads(Path(sys.argv[6]).read_text())) if len(sys.argv) > 6 and sys.argv[6] else []
SIGNAL = {"printfacts": "&H46D0F7&", "dragonpsych": "&H3689ED&"}[chan]   # ASS colours are BGR: #F7D046, #ED8936
W, H = (1080, 1920) if plat == "shorts" else (1920, 1080)
size, marg = (64, 380) if plat == "shorts" else (54, 90)
tmp = Path(tempfile.mkdtemp())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", str(tmp / "a.wav")], check=True)
given = json.loads(Path(sys.argv[7]).read_text()) if len(sys.argv) > 7 and sys.argv[7] else None
words = [tuple(w) for w in given] if given else word_times(tmp / "a.wav", prompt)
words = [(w, max(s, e - (.35 + .09 * len(w))), e) for w, s, e in words]   # a word cannot start long before it ends: the aligner sometimes stretches a start back across a silence
ts = lambda t: f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
ass = [f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n\n[V4+ Styles]\n"
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
       f"Style: C,Anton,{size},&H00FFFFFF,&H00FFFFFF,&H380C0A0A,&H380C0A0A,0,0,0,0,100,100,1,0,3,14,0,2,60,60,{marg},1\n\n[Events]\n"
       "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"]
centre = lambda k: (words[k][1] + words[k][2]) / 2
groups, cur = [], []          # four words to a group; a group also ends at a break time
for i in range(len(words)):
    if cur and (len(cur) == 4 or any(centre(cur[-1]) < b <= centre(i) for b in breaks)):
        groups.append(cur); cur = []
    cur.append(i)
if cur:
    groups.append(cur)
group_of = {i: g for g in groups for i in g}
for i, (w, s, e) in enumerate(words):
    end = words[i + 1][1] if i + 1 < len(words) and words[i + 1][1] - e < .6 else e + .25
    txt = " ".join(("{\\c" + SIGNAL + "}" + words[j][0] + "{\\c&HFFFFFF&}") if j == i else words[j][0] for j in group_of[i])
    ass.append(f"Dialogue: 0,{ts(s)},{ts(end)},C,,0,0,0,,{txt}\n")
(tmp / "c.ass").write_text("".join(ass))
mid = tmp / "c.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"ass={tmp / 'c.ass'}:fontsdir={FONTS}", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-c:a", "copy", str(mid)], check=True)
subprocess.run([sys.executable, str(SKILL / "loudness.py"), str(mid), "-o", out, "-I", "-14", "--tp", "-1", "--overwrite"], check=True)
print("captions:", len(words), "words ->", out)
