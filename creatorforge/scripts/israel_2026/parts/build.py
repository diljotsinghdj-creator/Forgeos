"""Builds the Israel 2026 package from the part files:
  A_Script_...txt            the full script (one file, for reading and for ElevenLabs)
  render/R1..R6_*.txt        CreatorForge render parts (each under 20,000 characters and 15 minutes)
  B_Storyboard_Timestamped.txt   every spoken line with its start time, pictures and graphics
  chapters.txt               YouTube chapter list, used in H_YouTube_Package.txt
Run from the worker folder:  python ../scripts/israel_2026/parts/build.py
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, os.path.abspath(os.path.join(OUT, "..", "..", "worker")))
sys.path.insert(0, HERE)
from creatorforge_worker.director import parse_script, ProductionSpec   # noqa: E402
from inserts import INSERTS                                             # noqa: E402

WPM = 150          # CreatorForge narration pace at voice speed 1.0 (2.5 words a second)
NAME = "Israel 2026 The Election That Settled Nothing"
SHORT_HEAD = ("On-screen hook: 120 seats. 61 to govern. Nobody got there.\n"
              "Title: Israel 2026: The Election That Settled Nothing ({part})\n"
              "Tags: #Israel #IsraelElection #Netanyahu #Eisenkot #Knesset\n")

def load(name):
    t = open(os.path.join(HERE, name), encoding="utf-8").read()
    for anchor, block in INSERTS.get(name, []):
        assert t.count(anchor) == 1, (name, anchor)
        i = t.index(anchor)
        t = t[:i] + block + t[i:]
    return t

FIXES = [("He was prime minister in 2021, in the only Israeli government that ever had an Arab party inside it, Ra'am. It lasted about a year.",
          "He became prime minister in 2021, in the only Israeli government that ever had an Arab party inside it, Ra'am. His premiership lasted about a year.")]

parts = {n: load(n) for n in ["p1.txt", "p2.txt", "p3.txt", "p4.txt", "p5.txt"]}
for a, b in FIXES:
    for n, t in parts.items():
        if a in t:
            parts[n] = t.replace(a, b)
p4a, p4b = parts["p4.txt"].split("\nChapter: Part 6 |", 1)
p4b = "\nChapter: Part 6 |" + p4b
full = parts["p1.txt"] + parts["p2.txt"] + parts["p3.txt"] + p4a + p4b + parts["p5.txt"]
open(os.path.join(OUT, "A_Script_Israel_2026_The_Election_That_Settled_Nothing.txt"), "w", encoding="utf-8").write(full)

renders = [("R1_Cold_Open_and_Part_1", parts["p1.txt"]),
           ("R2_Parts_2_and_3", parts["p2.txt"]),
           ("R3_Part_4_Gaza_and_West_Bank", parts["p3.txt"]),
           ("R4_Part_5_Kingmakers", p4a),
           ("R5_Part_6_Money_Missiles_Washington", p4b),
           ("R6_Parts_7_and_8_Scenarios_and_Close", parts["p5.txt"])]
os.makedirs(os.path.join(OUT, "render"), exist_ok=True)
t0 = 0.0
board, chapters, problems = [], [], []
for i, (fname, body) in enumerate(renders, 1):
    text = body if i == 1 else f"{NAME} - part {i} of 6\n" + SHORT_HEAD.format(part=f"part {i} of 6") + body
    path = os.path.join(OUT, "render", fname + ".txt")
    open(path, "w", encoding="utf-8").write(text)
    clean, meta = parse_script(text)
    try:
        ProductionSpec.from_dict({"script": text})
    except Exception as e:                       # noqa: BLE001
        problems.append(f"{fname}: {e}")
    words = len(clean.split())
    mins = words / WPM
    if len(text) > 20000 or mins > 15:
        problems.append(f"{fname}: {len(text)} chars, {mins:.1f} min")
    board.append(f"\n==================== RENDER {i}: {fname}  ({words} words, ~{mins:.1f} min, {len(text)} chars) ====================")
    # walk the blocks: spoken line + its direction lines
    for block in re.split(r"\n\s*\n", body):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        if lines[0].startswith("Chapter:"):
            title = lines[0].split(":", 1)[1].strip()
            m, s = divmod(int(t0), 60)
            chapters.append(f"{m}:{s:02d} {title.replace(' | ', ': ')}")
            board.append(f"\n[{m}:{s:02d}]  CHAPTER CARD  {title}")
            lines = lines[1:]
            if not lines:
                continue
        spoken = lines[0]
        if re.match(r"^(On-screen hook|Title|Tags|Source|Israel 2026 The)", spoken):
            continue
        dirs = lines[1:]
        w = len(spoken.split())
        m, s = divmod(int(t0), 60)
        h, m2 = divmod(m, 60)
        stamp = f"{h}:{m2:02d}:{s:02d}"
        board.append(f"\n[{stamp}]  ({w / WPM * 60:.0f}s)  VO: {spoken}")
        for d in dirs:
            board.append(f"            {d}")
        t0 += w / WPM * 60
if t0:
    chapters.insert(0, "0:00 Cold open: 120 seats, no government")
total_m = t0 / 60
head = (f"B - TIMESTAMPED STORYBOARD\nIsrael 2026: The Election That Settled Nothing\n"
        f"Generated from the script by parts/build.py at {WPM} words a minute (CreatorForge voice speed 1.0).\n"
        f"Total narration: ~{total_m:.1f} min. With the ElevenLabs voice, times shift: re-run voiceover_sync per render part.\n"
        "Each [h:mm:ss] is when the line starts. Pictures under a line are shown in turn while it is spoken.\n")
open(os.path.join(OUT, "B_Storyboard_Timestamped.txt"), "w", encoding="utf-8").write(head + "\n".join(board) + "\n")
open(os.path.join(HERE, "chapters.txt"), "w", encoding="utf-8").write("\n".join(chapters) + "\n")
print(f"total ~{total_m:.1f} min")
print("\n".join(chapters))
print("PROBLEMS:", problems or "none")
