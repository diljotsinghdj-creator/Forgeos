"""Render one still of every visual kind the studio can draw, maps first. Each sample uses the studio's own example
line (illustrative data: style samples, not sourced facts) and rotates through the house looks so they don't all
share one face. Each kind renders a short clip with the real renderer; the still is taken near its end."""
import json
import subprocess
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
D = Path(__file__).resolve().parent
LOOKS = ['archive', 'newsprint', 'kraft', 'chart', 'sepia', 'engraving', 'field', 'editorial', 'intel', 'declassified', 'swiss', 'noir']

MAPS = [
    ("map", "London → New York | The Atlantic crossing"),
    ("globe", "India | Where it sits on the globe"),
    ("fly", "Kota | Flying in"),
    ("shade", "UK 40%, France 25%, Spain 12%, Germany 30% | Shaded by a number"),
    ("pinmap", "Moynaq | A town on the old shore"),
    ("route", "Mumbai → Dubai → London | A trade route | ship"),
    ("clockmap", "Mumbai 9:30, Delhi 9:30, Kolkata 9:30, Guwahati 9:30 | One country, one clock | IST"),
    ("heatmap", "India 1.9, China 8.0, USA 14.9, Brazil 2.2, Germany 8.1 | A value per country | tonnes"),
    ("arrows", "Lisbon → Goa; Amsterdam → Jakarta; London → Kolkata | Trading companies at sea"),
    ("railmap", "Delhi - Kanpur - Patna - Kolkata; Delhi - Jaipur - Ahmedabad - Mumbai | Freight corridors"),
    ("sizemap", "India vs Germany | How big is it really?"),
    ("borders", "1914 → today | Europe | The map before the war"),
    ("morph", "India → drop → Bihar | Where the water goes"),
    ("shrink", "Aral Sea | 1960 -> today | The sea that left | pins: Moynaq, Aralsk"),
    ("wash", "Bihar, Jharkhand, West Bengal | hi: Bihar | East India | note"),
    ("tiles", "Bihar | 72 | 1 tile = 1,000 groups | Bihar: *72,000* groups"),
    ("mapdesk", "Switzerland | gold bars + banknote + rubber stamp | NEUTRALITY | Europe, 1934 | arrows: 6"),
    ("flowmap", "China → Netherlands 120, China → USA 90, India → UAE 40 | Container trade | million tonnes"),
    ("columns", "India 1.43, China 1.41, USA 0.34 | Population | billion"),
    ("dots", "Tokyo 37, Delhi 32, Shanghai 29, Dhaka 23 | The biggest cities | million people"),
    ("zones", "89.87 | IST-I, UTC+5:30; IST-II, UTC+6:30 | Two clocks for one country"),
    ("sunrise", "21 June 2026 3:50 → 4:40 | IST 5.5 | pins: Dong, Arunachal Pradesh @97.02,28.17; Kutch, Gujarat @68.8,23.8 | Sunrise across India"),
    ("terrain3d", "Mount Everest | The roof of the world | 40 km"),
    ("satellite", "Aral Sea | 2000 vs 2020"),
]


def render_one(job):
    i, kind, spec, group = job
    from creatorforge_worker.media import vox, maps, globe, scene3d, motion, cards
    look = LOOKS[i % len(LOOKS)]
    theme = f"editorial@yellow/{look}/"
    work = D / "work" / kind
    work.mkdir(parents=True, exist_ok=True)
    out = work / f"{kind}.mp4"
    W, H, secs = 1280, 720, 5.0
    try:
        if kind in ("map", "globe"):
            plan = maps.parse(spec)
            (globe.render if kind == "globe" else maps.render)(plan, theme, W, H, secs, out, work)
        elif kind == "shade":
            maps.render(maps.parse_shade(spec), theme, W, H, secs, out, work)
        elif kind == "fly":
            from creatorforge_worker.media import flyover
            try:
                flyover.render(flyover.parse(spec), theme, W, H, secs, out, work)
            except Exception:  # noqa: BLE001 - the studio falls back to the flat animated map the same way
                maps.render(maps.parse(spec), theme, W, H, secs, out, work)
        elif kind in ("zones", "sunrise"):
            from creatorforge_worker.media import sunrise
            sunrise.render(sunrise.parse(kind, spec), theme, W, H, secs, out, work)
        elif kind in scene3d.KINDS:
            scene3d.render(kind, spec, theme, W, H, secs, out, work)
        elif kind in vox.KINDS or kind in vox.DATAMAP_KINDS:
            vox.render(kind, spec, theme, W, H, secs, out, work, lib=D / "work" / "cutouts", fetch=True)
        elif kind in motion.KINDS:
            motion.render(kind, spec, "editorial", W, H, secs, out, work)
        else:
            cards.render(kind, spec, "editorial", W, H, secs, out, work)
        png = D / group / f"{i + 1:03d}_{kind}.jpg"
        png.parent.mkdir(exist_ok=True)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                   capture_output=True, text=True).stdout.strip() or secs)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur * .86:.2f}", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(png)], check=True)
        return kind, "ok", look
    except Exception as e:  # noqa: BLE001
        return kind, f"FAILED: {type(e).__name__}: {str(e)[:160]}", look


if __name__ == "__main__":
    group = sys.argv[1] if len(sys.argv) > 1 else "maps"
    items = MAPS if group == "maps" else json.loads((D / "all_kinds.json").read_text())
    jobs = [(i, k, s, group) for i, (k, s) in enumerate(items)]
    res = {}
    with ProcessPoolExecutor(3) as ex:
        for kind, status, look in ex.map(render_one, jobs):
            res[kind] = {"status": status, "look": look}
            print(kind, status, look, flush=True)
    (D / f"{group}_results.json").write_text(json.dumps(res, indent=1))
