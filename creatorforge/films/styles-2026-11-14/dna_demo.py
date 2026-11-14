import json, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
D = Path(__file__).resolve().parent
items = dict(json.load(open(D / "all_kinds.json")))
KINDS = ["seats", "table", "flowchart", "bignumber", "pyramid"]
SPECS = {k: items[k] for k in KINDS}
SPECS["heatmap"] = "India 1.9, China 8.0, USA 14.9, Brazil 2.2, Germany 8.1 | A value per country | tonnes"
DNAS = ["classic"] + (sys.argv[1].split(",") if len(sys.argv) > 1 else ["blueprint", "riso", "noir"])


def one(job):
    kind, dna = job
    from creatorforge_worker.media import vox
    work = D / "work" / f"dna_{dna}_{kind}"
    work.mkdir(parents=True, exist_ok=True)
    out = work / f"{kind}.mp4"
    theme = "editorial@yellow/archive/" + ("" if dna == "classic" else f"/dna:{dna}")
    try:
        vox.render(kind, SPECS[kind], theme, 1280, 720, 5.0, out, work, lib=D / "work" / "cutouts", fetch=True)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip() or 5)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur * .86:.2f}", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(D / "dna" / f"{kind}__{dna}.jpg")], check=True)
        return kind, dna, "ok"
    except Exception as e:  # noqa: BLE001
        return kind, dna, f"FAILED {type(e).__name__}: {str(e)[:150]}"


if __name__ == "__main__":
    jobs = [(k, d) for k in SPECS for d in DNAS]
    with ProcessPoolExecutor(3) as ex:
        for r in ex.map(one, jobs):
            print(*r, flush=True)
