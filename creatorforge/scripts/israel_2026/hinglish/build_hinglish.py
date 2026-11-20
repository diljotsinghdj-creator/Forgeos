"""Builds the Hinglish version from the English script (A_...txt, made by parts/build.py) and lines_*.txt:
every spoken line is swapped for its Hinglish line (same order, same pictures, graphics and citations).
Writes A_Hinglish script, render/R1-R6 and B storyboard into this folder, and checks CreatorForge's limits.
Run from creatorforge/worker:  python ../scripts/israel_2026/hinglish/build_hinglish.py"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.abspath(os.path.join(ROOT, "..", "..", "worker")))
from creatorforge_worker.director import parse_script, ProductionSpec   # noqa: E402

WPS = 2.5   # CreatorForge's timing assumption (words a second)
lines = {}
for f in ("lines_1.txt", "lines_2.txt"):
    for l in open(os.path.join(HERE, f), encoding="utf-8"):
        if l.strip():
            n, t = l.rstrip("\n").split("|", 1)
            lines[int(n)] = t.strip()
assert sorted(lines) == list(range(1, len(lines) + 1)), "line numbers must run 1..N"

CHAPTERS = {
    "Part 1 | What Actually Happened": "Part 1 | Asal Mein Hua Kya",
    "Part 2 | The Survivor": "Part 2 | Netanyahu: Jo Har Baar Bach Nikalte Hain",
    "Part 3 | The Machine": "Part 3 | Israel Ki Siyasi Machine",
    "Part 4 | Gaza, the West Bank, and the People Not on the Ballot": "Part 4 | Gaza, West Bank Aur Woh Log Jo Ballot Par Nahin The",
    "Part 5 | The Kingmakers": "Part 5 | Kingmakers",
    "Part 6 | Money, Missiles, and the Man in Washington": "Part 6 | Paisa, Missiles Aur Washington Wale Sahab",
    "Part 7 | Five Ways This Ends": "Part 7 | Yeh Khel Paanch Tarah Khatam Ho Sakta Hai",
    "Part 8 | What It Settled": "Part 8 | Aakhir Tay Kya Hua",
}
NAME = "Israel 2026 Woh Chunav Jisne Kuch Tay Nahin Kiya"
HOOK = "On-screen hook: 120 सीटें। सरकार के लिए 61। कोई नहीं पहुँचा।"
TITLE = "Title: Israel 2026: Woh Chunav Jisne Kuch Tay Nahin Kiya | Netanyahu vs Eisenkot Explained"
TAGS = "Tags: #Israel #IsraelElection #Netanyahu #Eisenkot #Knesset #Gaza #Hindi #Hinglish"

eng = open(os.path.join(ROOT, "A_Script_Israel_2026_The_Election_That_Settled_Nothing.txt"), encoding="utf-8").read()
blocks = re.split(r"\n\s*\n", eng.strip())
out_blocks, n = [], 0
for b in blocks:
    ls = b.strip().splitlines()
    if ls[0].startswith("Israel 2026 The"):                      # header block
        src = next(l for l in ls if l.startswith("Source:"))
        out_blocks.append("\n".join([NAME, HOOK, TITLE, TAGS, src]))
        continue
    if ls[0].startswith("Chapter:"):
        key = ls[0].split(":", 1)[1].strip()
        ls[0] = "Chapter: " + CHAPTERS[key]
        out_blocks.append(ls[0])
        ls = ls[1:]
        if not ls:
            continue
    n += 1
    ls[0] = lines[n]
    out_blocks.append("\n".join(ls))
assert n == len(lines), (n, len(lines))
full = "\n\n".join(out_blocks) + "\n"
open(os.path.join(HERE, "A_Hinglish_Script_Israel_2026.txt"), "w", encoding="utf-8").write(full)

# render parts: same chapter boundaries as the English version
cuts = ["Chapter: " + CHAPTERS[k] for k in ("Part 2 | The Survivor", "Part 4 | Gaza, the West Bank, and the People Not on the Ballot",
        "Part 5 | The Kingmakers", "Part 6 | Money, Missiles, and the Man in Washington", "Part 7 | Five Ways This Ends")]
pieces, rest = [], full
for c in cuts:
    a, b = rest.split(c, 1)
    pieces.append(a)
    rest = c + b
pieces.append(rest)
names = ["R1_Cold_Open_aur_Part_1", "R2_Part_2_aur_3", "R3_Part_4_Gaza_aur_West_Bank", "R4_Part_5_Kingmakers",
         "R5_Part_6_Paisa_Missiles_Washington", "R6_Part_7_aur_8"]
os.makedirs(os.path.join(HERE, "render"), exist_ok=True)
board, chapters, problems, t0 = [], [], [], 0.0
for i, (nm, body) in enumerate(zip(names, pieces), 1):
    text = body if i == 1 else (f"{NAME} - part {i} of 6\n{HOOK}\n{TITLE} (part {i}/6)\n{TAGS}\n\n" + body)
    open(os.path.join(HERE, "render", nm + ".txt"), "w", encoding="utf-8").write(text)
    clean, _ = parse_script(text)
    try:
        ProductionSpec.from_dict({"script": text})
    except Exception as e:                                       # noqa: BLE001
        problems.append(f"{nm}: {e}")
    words = len(clean.split())
    if len(text) > 20000 or words / WPS > 900:
        problems.append(f"{nm}: {len(text)} chars, {words / WPS / 60:.1f} min")
    board.append(f"\n==================== RENDER {i}: {nm}  ({words} words, ~{words / WPS / 60:.1f} min, {len(text)} chars) ====================")
    for blk in re.split(r"\n\s*\n", body):
        ls = [l for l in blk.strip().splitlines() if l.strip()]
        if not ls or ls[0].startswith(NAME):
            continue
        if ls[0].startswith("Chapter:"):
            m, s = divmod(int(t0), 60)
            chapters.append(f"{m}:{s:02d} {ls[0].split(':', 1)[1].strip().replace(' | ', ': ')}")
            board.append(f"\n[{m}:{s:02d}]  CHAPTER CARD  {ls[0].split(':', 1)[1].strip()}")
            ls = ls[1:]
            if not ls:
                continue
        w = len(ls[0].split())
        h, r = divmod(int(t0), 3600)
        m, s = divmod(r, 60)
        board.append(f"\n[{h}:{m:02d}:{s:02d}]  ({w / WPS:.0f}s)  VO: {ls[0]}")
        board += ["            " + d for d in ls[1:]]
        t0 += w / WPS
chapters.insert(0, "0:00 Cold open: 120 seats, sarkar zero")
head = ("B - TIMESTAMPED STORYBOARD (HINGLISH)\nIsrael 2026: Woh Chunav Jisne Kuch Tay Nahin Kiya\n"
        f"Times at CreatorForge's 2.5 words a second. Total ~{t0 / 60:.1f} min. Real Hindi narration timing varies -\n"
        "re-time chapters after the final edit. Pictures, graphics and citations are the same as the English version.\n")
open(os.path.join(HERE, "B_Hinglish_Storyboard.txt"), "w", encoding="utf-8").write(head + "\n".join(board) + "\n")
open(os.path.join(HERE, "chapters_hinglish.txt"), "w", encoding="utf-8").write("\n".join(chapters) + "\n")
print(f"{n} lines, ~{t0 / 60:.1f} min")
print("\n".join(chapters))
print("\n".join(b for b in board if b.startswith("\n====")))
print("PROBLEMS:", problems or "none")
