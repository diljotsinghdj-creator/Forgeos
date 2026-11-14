"""python -m creatorforge_worker.studio <screenplay.json> <dossier.json> <out_dir> [1920x1080] [fps]"""
import sys
from pathlib import Path

from .produce import ProductionStopped, produce

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__)
        sys.exit(2)
    size = tuple(int(x) for x in (a[3] if len(a) > 3 else "1920x1080").split("x"))
    try:
        rep = produce(Path(a[0]), Path(a[1]), Path(a[2]), size=size, fps=int(a[4]) if len(a) > 4 else 24)
    except ProductionStopped as e:
        print("STOPPED:", e)
        sys.exit(1)
    print("done:", rep["file"], rep["seconds"], "s; missing:", rep["deliverables_missing"] or "nothing")
