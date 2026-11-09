"""The acceptance film: one short documentary that uses every production discipline, built by the engine's own
modules and then checked discipline by discipline. It needs no network, no GPU and no keys, so it runs anywhere the
worker runs (the narration is spoken by FFmpeg's flite voice; on the pod the same storyboard goes through the real
voice and word alignment).

    python -m creatorforge_worker.acceptance <out_dir> [1280x720] [fps]

Writes <out_dir>/acceptance.mp4 and <out_dir>/acceptance_report.json, prints the report, and exits 1 if any
discipline that can run here failed. Disciplines that need the pod (archive footage, depth-map camera moves,
street-level and satellite maps, real cut-out photos) are listed as "pod-only", never as passed.

Every figure in the storyboard was checked (see SOURCES); figures that are estimates carry an ESTIMATE badge.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import wave
from pathlib import Path

from . import pipeline
from .media import ambience, ff, motion, quality, render, scene3d, sfx, sfx_builtin, vox

SOURCES = ["Wikipedia: Suez Canal; 2021 Suez Canal obstruction", "Port Economics, Management and Policy: Blockage of the Suez Canal",
           "Arab News, 25 Mar 2021 (headline quoted)"]
ACCENT, LOOK = "red", "newsprint"

# (what is said, graphic kind, graphic line, the discipline it proves)
STORYBOARD = [
    ("In March twenty twenty one, one ship brought one of the world's busiest shortcuts to a stop.",
     "title3d", "STUCK | Suez Canal · March 2021", "3d"),
    ("This is the Suez Canal, in Egypt. It opened on the seventeenth of November, eighteen sixty nine.",
     "pinmap", "Egypt | The Suez Canal | atlas | marker: opened 1869 | badge: verified", "maps"),
    ("It is the short way by sea between Asia and Europe.",
     "route", "Shanghai → Singapore → Rotterdam | Asia to Europe by sea | ship | atlas", "maps"),
    ("On the twenty third of March, a container ship called Ever Given, four hundred metres long, ran aground and blocked it.",
     "hero", "ship | EVER GIVEN | 400 m long · 20,000 containers | 23 March 2021 | badge: reported | fx: dust", "2.5d"),
    ("One ship. Six days.", "statement", "One *ship*. Six *days*.", "kinetic"),
    ("By the twenty eighth of March, at least three hundred and sixty nine ships were waiting.",
     "table", "Fact, Figure | Ship length, 400 m; Days blocked, 6; Ships waiting, 369 | The blockage in numbers | "
              "Wikipedia; Port Economics | highlight: 3 | badge: reported", "infographics"),
    ("Arab News put it this way. A tenth of world trade, halted.",
     "newscard", "2021 | Tenth of world trade halted as container ship blocks Suez Canal | 25 March 2021 | newspaper | "
                 "Arab News | badge: reported", "evidence"),
    ("One widely reported estimate put the goods held up at nine point six billion dollars a day.",
     "bignumber", "$9.6 bn | cash | of goods held up each day | One estimate | badge: estimate", "infographics"),
    ("Goods go from the factory, to the port, through the canal, to Europe. Block one link, and everything behind it waits.",
     "flowchart", "Factory → Port → Suez Canal (blocked) → Europe | One blocked link", "infographics"),
    ("The other way is round Africa. From the Arabian Sea to London, that adds about eight thousand nine hundred kilometres.",
     "route", "Mumbai → Cape Town → London | The long way round | ship | atlas | pen | marker: +8,900 km", "maps"),
    ("A ship like this is a stack. The bridge, thousands of containers, the deck, the hull, and the engine.",
     "explode", "Container ship | Bridge, Containers, Deck, Hull, Engine | What ran aground", "3d"),
    ("Factories, shops, shipping lines and insurers all lean on one narrow strip of water.",
     "linkmap", "Suez Canal | Factories: exports; Shops: stock; Shipping lines: schedules; Insurers: claims | Who depends on it",
     "infographics"),
    ("On the twenty ninth of March, the ship was freed.", "calendar", "29 MAR 2021 | Freed", "kinetic"),
    ("One ship, six days. The world's shortcuts are narrow.",
     "endcard", "One ship, six days | The world's shortcuts are narrow | Sources: Wikipedia · Port Economics · Arab News", "sources"),
]
POD_ONLY = {"archival footage": "needs archive footage or photos (Wikimedia / Internet Archive): no network here",
            "depth-map camera move": "needs the Depth Anything model on the pod",
            "street-level and satellite maps": "need map tiles (MapLibre) on the pod",
            "real cut-out photographs": "need the photo sources; drawn illustrations stand in here",
            "word-level alignment": "needs WhisperX on the pod GPU; cuts here land on measured line timings"}


def speak(text: str, out: Path) -> float:
    """Narration for one line (flite via FFmpeg): 48 kHz mono PCM. Returns its length in seconds."""
    safe = text.replace("\\", " ").replace("'", "’").replace(":", ",").replace("%", " percent")
    r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"flite=text='{safe}':voice=slt",
                        "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(out)],
                       capture_output=True, timeout=120)
    if r.returncode != 0 or not out.is_file():
        raise RuntimeError(f"narration failed: {r.stderr.decode()[-200:]}")
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def _draw(kind: str, spec: str, theme: str, w: int, h: int, seconds: float, out: Path, work: Path, fps: int, lay: str) -> Path:
    if kind in scene3d.KINDS:
        return scene3d.render(kind, spec, theme, w, h, seconds, out, work, fps=fps)
    if kind in vox.KINDS:
        return vox.render(kind, spec, theme, w, h, seconds, out, work, fetch=False, fps=fps, layout=lay)
    return motion.render(kind, spec, theme, w, h, seconds, out, work, fps=fps)


def _cuts(video: Path) -> list[float]:
    """Times where the picture changes shot (FFmpeg scene detection)."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "info", "-i", str(video), "-vf", "select='gt(scene,0.12)',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True, timeout=900)
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def build(out_dir: Path, size: tuple[int, int] = (1280, 720), fps: int = 24) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "work"
    work.mkdir(exist_ok=True)
    w, h = size
    theme = f"editorial~0@{ACCENT}/{LOOK}/"
    kinds = [k for _, k, _, _ in STORYBOARD]
    layouts = vox.plan_layouts(kinds, vox._seed("acceptance"))
    paper, _ = vox.paper(vox.look_of(theme)["paper"], w, h, work)
    wavs, slots, clips, scenes = [], [], [], []
    for i, (text, kind, spec, discipline) in enumerate(STORYBOARD):
        wav = work / f"line_{i:02d}.wav"
        spoken = speak(text, wav)
        slot = round(spoken + 0.35, 3)                       # the line, then a breath
        mp4 = work / f"scene_{i:02d}_{kind}.mp4"
        error = ""
        try:
            _draw(kind, spec, theme, w, h, slot + render.TRANSITION_S + 0.2, mp4, work, fps, layouts[i])
        except Exception as e:  # noqa: BLE001 - recorded, and the discipline fails
            error = str(e)[:200]
        prev = kinds[i - 1] if i else ""
        cut = "cut" if not i else (pipeline.motivated_transition(prev, kind) or "blur")
        if not error:
            clip = render.Clip(paper, slot, "static", cut, mp4, ff.duration(mp4), stepped=kind not in scene3d.KINDS)
        else:
            clip = render.Clip(paper, slot, "static", cut)
        clips.append(clip)
        wavs.append(wav)
        slots.append(slot)
        scenes.append({"n": i + 1, "kind": kind, "discipline": discipline, "spoken_s": round(spoken, 2), "slot_s": slot,
                       "cut_in": cut, "layout": layouts[i], "error": error})
    tail = render.TRANSITION_S
    total = sum(slots) + tail
    narr = work / "narration.wav"
    render.narration_track(wavs, slots, tail, narr)
    bank = sfx.SfxBank.load("", sfx_builtin.ensure(out_dir / "sfx"))
    hits = sfx.place(bank, [c.transition for c in clips], slots, [], "acceptance")
    at, shots = 0.0, []
    for (_, kind, spec, _), slot in zip(STORYBOARD, slots):
        shots.append((at, slot, kind, spec, False))
        at += slot
    beds = ambience.place(out_dir / "ambience", shots)
    audio = work / "mix.wav"
    cancel = threading.Event()
    render.mix_audio(narr, None, total, audio, cancel, sfx=sorted(hits + beds, key=lambda x: x[1]))
    final = out_dir / "acceptance.mp4"
    expected = render.render_video(clips, audio, None, w, h, final, work, cancel, grade="")

    # ---- the checks, one discipline at a time ----
    starts = [round(sum(slots[:i]), 3) for i in range(len(slots))]
    found = _cuts(final)
    drift = [min((abs(c - s) for c in found), default=9.9) for s in starts[1:]]
    q = quality.check(final, expected, [], expected_size=(w, h))
    by: dict[str, list] = {}
    for s in scenes:
        by.setdefault(s["discipline"], []).append(s)

    def ok(d):
        return bool(by.get(d)) and not any(s["error"] for s in by[d])
    names = {"maps": "animated maps (pin map, two sea routes)", "infographics": "infographics (table, big number, flow, links)",
             "kinetic": "kinetic typography", "evidence": "document evidence with attribution",
             "2.5d": "2.5D layered composition with particles", "3d": "genuine 3D (title, exploded view)",
             "sources": "source citations (end card, badges)"}
    disciplines = [{"name": names[d], "status": "pass" if ok(d) else "FAIL",
                    "detail": ", ".join(f"{s['kind']}" + (f" ({s['error']})" if s["error"] else "") for s in by.get(d, []))}
                   for d in names]
    disciplines.append({"name": "motivated transitions", "status": "pass" if len({c.transition for c in clips}) >= 4 else "FAIL",
                        "detail": " ".join(c.transition for c in clips[1:])})
    disciplines.append({"name": "sound design (cues + ambient beds)", "status": "pass" if hits and beds else "FAIL",
                        "detail": f"{len(hits)} cues, {len(beds)} beds"})
    worst = max(drift) if drift else 0.0
    disciplines.append({"name": "narration sync (cut vs. spoken line)", "status": "pass" if worst <= 0.35 else "FAIL",
                        "detail": f"worst cut {worst:.2f}s from its line, mean {sum(drift) / max(1, len(drift)):.2f}s"})
    disciplines.append({"name": "finished film quality", "status": "pass" if q["passed"] else "FAIL",
                        "detail": "; ".join(q["warnings"]) or f"{len(q['checks'])} checks clean"})
    disciplines += [{"name": k, "status": "pod-only", "detail": v} for k, v in POD_ONLY.items()]
    report = {"file": str(final), "seconds": round(expected, 2), "size": [w, h], "look": LOOK, "accent": ACCENT,
              "sources": SOURCES, "scenes": scenes, "disciplines": disciplines, "quality": q,
              "passed": not any(d["status"] == "FAIL" for d in disciplines)}
    (out_dir / "acceptance_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    return report


def main(argv: list[str]) -> int:
    out = Path(argv[1] if len(argv) > 1 else "acceptance_out")
    size = tuple(int(x) for x in (argv[2] if len(argv) > 2 else "1280x720").split("x"))
    rep = build(out, size, int(argv[3]) if len(argv) > 3 else 24)
    for d in rep["disciplines"]:
        print(f"{d['status']:9} {d['name']}: {d['detail']}")
    print(("PASSED" if rep["passed"] else "FAILED"), rep["file"], f"{rep['seconds']}s")
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
