"""The production run: from a dossier and a screenplay to a finished, reviewed documentary and every deliverable.

    produce(screenplay.json, dossier.json, out_dir)

Steps (the order of the master directive; a step that finds an error stops the film rather than shipping it):
  1  check the research dossier                    research/dossier.md, dossier.json
  2  editorial review of the screenplay            writing/editorial_review.md (figures, sources, attribution, structure)
  3  art direction, against the studio history     writing/art_direction.md
  4  narration audio, one file per scene           audio/narration/S01.wav..., audio/narration.wav
  5  the master timeline from the real audio       timeline/timeline.json, .csv, .md
  6  every scene drawn                             scenes/S01_*.mp4
  7  storyboard                                    storyboard/storyboard.md, sheet.png
  8  score, effects, ambience, mix                 audio/score.wav, audio/mix.wav
  9  the edit                                      video/<id>.mp4
  10 captions                                      captions/<id>.srt, .vtt
  11 quality control and the watch-through         qc/report.md, qc/review_sheet.png
  12 thumbnail, SEO, cutdowns                      promo/thumbnail.png, seo.md, cutdown_*.mp4
  13 deliverables index                            README.md
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path

from ..media import ambience, ff, motion, quality, render, scene3d, sfx, sfx_builtin, vox
from . import artdirection, score, voice, writer
from .dossier import Dossier, figures_in

LEAD_S = 0.18          # air before each line
MIN_SLOT = 2.6         # a graphic needs this long to read, however short its line


def asset_sources() -> list[tuple[str, str]]:
    """Photo and footage sources on this worker: the keys in its environment, then the keyless ones."""
    out = []
    for name, keys in (("unsplash", ("UNSPLASH_KEY", "CF_UNSPLASH_KEY")), ("pixabay", ("PIXABAY_KEY", "CF_PIXABAY_KEY")),
                       ("pexels", ("PEXELS_KEY", "CF_PEXELS_KEY"))):
        k = next((os.environ[x] for x in keys if os.environ.get(x)), "")
        if k:
            out.append((name, k))
    if os.environ.get("CF_FREE_STOCK", "1") != "0":
        # no keys needed: real archives first (people, places and events as they were), then Openverse
        out += [("wikimedia", ""), ("nasa", ""), ("loc", ""), ("smithsonian", ""), ("europeana", ""), ("archive", ""), ("openverse", "")]
        if os.environ.get("FLICKR_KEY"):
            out.insert(-2, ("flickr", os.environ["FLICKR_KEY"]))
    return out


class ProductionStopped(RuntimeError):
    pass


def _ts(x: float, srt: bool = True) -> str:
    h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", "," if srt else ".")


def _mmss(x: float) -> str:
    return f"{int(x // 60)}:{int(x % 60):02d}"


def _kind(graphic: str) -> str:
    return graphic.split(":", 1)[0].strip().lower()


def _spec(graphic: str) -> str:
    return graphic.split(":", 1)[1].strip() if ":" in graphic else ""


def _frame(video: Path, t: float, out: Path, width: int = 640) -> Path:
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{max(0.0, t):.2f}", "-i", str(video), "-frames:v", "1",
                    "-vf", f"scale={width}:-2", str(out)], check=True, timeout=120)
    return out


def _sheet(images: list[Path], labels: list[str], out: Path, cols: int = 4) -> Path | None:
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(p).convert("RGB") for p in images if p.is_file()]
    if not ims:
        return None
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + 28)), "#202020")
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sheet)
    for i, (im, lb) in enumerate(zip(ims, labels)):
        x, y = (i % cols) * w, (i // cols) * (h + 28)
        sheet.paste(im.resize((w, h)), (x, y + 28))
        d.text((x + 6, y + 5), lb[:90], fill="#FFFFFF", font=font)
    sheet.save(out)
    return out


PLAIN_CUTS = ["blur", "dipcut", "whip"]      # unmotivated seams: a camera-blur whip, a dip cut, a smooth slide


def _render_scene(kind, spec, theme, w, h, seconds, out, work, fps, layout, fetch, lib):
    if kind == "key":
        from ..media import composite
        return composite.render(spec, w, h, seconds, out, fps)
    if kind in scene3d.KINDS:
        return scene3d.render(kind, spec, theme, w, h, seconds, out, work, fps=fps)
    if kind in vox.KINDS:
        return vox.render(kind, spec, theme, w, h, seconds, out, work, lib=lib, fetch=fetch, fps=fps, layout=layout)
    if kind in ("sunrise", "zones"):
        # the Sun's real position over the country, or its time zones (media/sunrise.py)
        from ..media import sunrise as _sun
        plan = _sun.parse(kind, spec)
        if plan is None:
            raise ProductionStopped(f"{kind}: can't read '{spec[:60]}'")
        return _sun.render(plan, w, h, seconds, out, fps)
    if kind in ("globe", "map"):
        # the globe fly-in and the flat map, drawn offline from the bundled Natural Earth shapes
        from ..media import globe as _globe, maps as _maps
        plan = _maps.parse(spec)
        if plan is None:
            raise ProductionStopped(f"{kind}: the map doesn't know the place in '{spec[:60]}'")
        return (_globe if kind == "globe" else _maps).render(plan, theme, w, h, seconds, out, work)
    if kind in motion.KINDS:
        return motion.render(kind, spec, theme, w, h, seconds, out, work, fps=fps)
    from ..media import cards                              # chat, social, quote, document...: the card renderer
    return cards.render(kind, spec, theme, w, h, seconds, out, work)


def _directed(graphic: str, ad: dict, scene: dict) -> str:
    """The graphic line with the art direction applied: the shot's camera, the film's map treatment."""
    kind, spec = _kind(graphic), _spec(graphic)
    if kind in vox.KINDS:
        cam = scene.get("camera") or artdirection.camera_for(ad, kind)
        if cam in vox.CAMERAS and not re.search(r"\|\s*camera\s*:", spec):
            spec += f" | camera: {cam}"
        if kind in ("route", "pinmap") and not re.search(r"\|\s*(atlas|pen)\s*(\||$)", spec):
            spec += {"atlas": " | atlas", "pen": " | pen", "relief": " | atlas"}.get(ad.get("map_style"), "")
    return f"{graphic.split(':', 1)[0]}: {spec}"


def captions(scenes: list[dict], timeline: list[dict], max_chars: int = 42) -> list[tuple[float, float, str]]:
    """Caption cues from the real audio: each line split into short phrases, timed by the voice's own pauses
    (a cue ends where the narrator breathes) and, between pauses, by the share of characters."""
    cues = []
    for s, t in zip(scenes, timeline):
        words = s["narration"].split()
        chunks, cur = [], ""
        for wd in words:
            if cur and len(cur) + 1 + len(wd) > max_chars:
                chunks.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
            if re.search(r"[.?!;:,]$", wd) and len(cur) > max_chars * .55:
                chunks.append(cur)
                cur = ""
        if cur:
            chunks.append(cur)
        start, speech = t["start"] + LEAD_S, t["speech_s"]
        total = sum(len(c) for c in chunks) or 1
        breaths = [a + b / 2 for a, b in t.get("pauses", [])]
        at = 0.0
        for c in chunks:
            end = at + speech * len(c) / total
            near = [p for p in breaths if abs(p - end) < 0.7 and p > at + 0.6]
            if near:
                end = min(near, key=lambda p: abs(p - end))
            cues.append((start + at, start + min(speech, max(end, at + 0.6)), c))
            at = end
    return cues


def _write_captions(cues, base: Path) -> tuple[Path, Path]:
    srt = base.with_suffix(".srt")
    srt.write_text("\n".join(f"{i}\n{_ts(a)} --> {_ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1)), encoding="utf-8")
    vtt = base.with_suffix(".vtt")
    vtt.write_text("WEBVTT\n\n" + "\n".join(f"{_ts(a, False)} --> {_ts(b, False)}\n{t}\n" for a, b, t in cues), encoding="utf-8")
    return srt, vtt


def _ass(cues, w: int, h: int, out: Path) -> Path:
    fs = int(h * 0.034 if h > w else h * 0.05)
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, "
            "PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
            "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Cap,DejaVu Sans,%d,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96141414,1,0,0,0,100,100,0,0,3,%d,0,2,60,60,%d,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n") % (
        w, h, fs, max(4, fs // 6), int(h * 0.2 if h > w else h * 0.07))

    def t(x):
        return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
    out.write_text(head + "\n".join(f"Dialogue: 0,{t(a)},{t(b)},Cap,,0,0,0,,{c}" for a, b, c in cues), encoding="utf-8")
    return out


def _cuts(video: Path) -> list[float]:
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "info", "-i", str(video), "-vf", "select='gt(scene,0.12)',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True, timeout=1800)
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def _gray(video: Path, t: float):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(0.0, t):.2f}", "-i", str(video), "-frames:v", "1",
                          "-vf", "scale=96:54", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, timeout=60).stdout
    return np.frombuffer(raw, np.uint8).astype("float32") if raw else None


def produce(screenplay: Path | str, dossier: Path | str, out_dir: Path | str, size: tuple[int, int] = (1920, 1080), fps: int = 24,
            data_dir: Path | str | None = None, fetch: bool = False, lib: Path | None = None, cutdown_size=(1080, 1920),
            progress=print) -> dict:
    out = Path(out_dir)
    dirs = {k: out / k for k in ("research", "writing", "audio", "scenes", "storyboard", "timeline", "captions", "video", "promo", "qc")}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    work = out / ".work"
    work.mkdir(exist_ok=True)
    data = Path(data_dir) if data_dir else out / ".studio"
    sp = json.loads(Path(screenplay).read_text(encoding="utf-8"))
    dos = Dossier.load(dossier)
    film = sp.get("id") or re.sub(r"\W+", "-", sp.get("title", "film").lower()).strip("-")
    report: dict = {"film": film, "title": sp.get("title", ""), "steps": []}

    def step(name, **kw):
        report["steps"].append({"step": name, **kw})
        progress(f"[{len(report['steps']):02d}] {name}" + (f": {kw.get('note', '')}" if kw.get("note") else ""))

    # 0 the owner's gates (studio/gates.py): an engine the owner picked, and evidence before explanation
    from . import gates
    gated = gates.applies(sp)
    gate_issues: list[dict] = []
    # the studio's memory of past films lives in the repository for the channels, never in a throwaway output folder
    hdir = Path(os.environ["CF_STUDIO_HISTORY"]) if os.environ.get("CF_STUDIO_HISTORY") else gates.HISTORY_DIR if gated else data

    def gate_stop(found: list[dict]):
        gate_issues.extend(found)
        (dirs["writing"] / "gates.md").write_text("# Gates\n\n" + "\n".join(f"- **{i['level']}** gate {i['gate']} {i['scene']}: {i['problem']}"
                                                                         for i in gate_issues) + "\n", encoding="utf-8")
        if [i for i in found if i["level"] == "error"]:
            raise ProductionStopped(gates.stop_message(found))

    if gated:
        gate_stop(gates.check_pick(sp) + gates.check_evidence(sp))
        step("gates 1 and 3", note="engine picked by the owner; evidence before explanation")

    # 1 research dossier
    di = dos.check()
    (dirs["research"] / "dossier.md").write_text(dos.to_markdown(), encoding="utf-8")
    (dirs["research"] / "dossier.json").write_text(json.dumps(dos.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    if [i for i in di if i["level"] == "error"]:
        raise ProductionStopped("dossier: " + "; ".join(f"{i['claim']}: {i['problem']}" for i in di if i["level"] == "error"))
    step("research dossier checked", note=f"{len(dos.claims)} claims, {sum(len(c.sources) for c in dos.claims.values())} sources")

    # 2 editorial review
    from . import brainlog
    log = Path(os.environ.get("CF_BRAIN_LOG") or brainlog.DEFAULT)
    issues = writer.check(sp, dos) + writer.novelty(sp, (brainlog.used(log) if log.exists() else []) + [x for x in artdirection.history(hdir) if x.get("id") != film])
    rev = ["# Editorial review", "", f"Film: {sp.get('title')}", ""]
    rev += ["## Problems", ""] + ([f"- **{i['level']}** {i['scene']}: {i['problem']}" for i in issues] or ["- none"])
    rev += ["", "## Evidence per scene", "", "| Scene | Figures said or shown | Claims | Status |", "|---|---|---|---|"]
    for s in sp["scenes"]:
        figs = sorted(set(figures_in(s["narration"]) + figures_in(_spec(s["graphic"]))))
        rev.append(f"| {s['id']} | {', '.join(figs) or '-'} | {', '.join(s.get('claims', [])) or '-'} | "
                   + ", ".join(dos.claims[c].status for c in s.get("claims", []) if c in dos.claims) + " |")
    (dirs["writing"] / "editorial_review.md").write_text("\n".join(rev), encoding="utf-8")
    if [i for i in issues if i["level"] == "error"]:
        raise ProductionStopped("editorial review: " + "; ".join(f"{i['scene']}: {i['problem']}" for i in issues if i["level"] == "error"))
    step("editorial review passed", note=f"{len([i for i in issues if i['level'] == 'warning'])} warnings")
    (dirs["writing"] / "concept.md").write_text(
        f"# {sp.get('title')}\n\n" + "\n".join(f"- **{k.replace('_', ' ').capitalize()}**: {v}" for k, v in sp.get("concept", {}).items()),
        encoding="utf-8")
    (dirs["writing"] / "screenplay.md").write_text(writer.screenplay_markdown(sp, dos), encoding="utf-8")
    shutil.copy(screenplay, dirs["writing"] / "screenplay.json")

    # 3 art direction
    hist = [x for x in artdirection.history(hdir) if x.get("id") != film]
    ad = artdirection.direct(film, sp.get("title", film), sp.get("genre", ""), sp.get("concept", {}), sp["scenes"], hist, sp.get("art"))
    (dirs["writing"] / "art_direction.md").write_text(artdirection.to_markdown(ad), encoding="utf-8")
    (dirs["writing"] / "art_direction.json").write_text(json.dumps(ad, ensure_ascii=False, indent=1), encoding="utf-8")
    step("art direction", note=f"{ad['look']} / {ad['accent']} / {ad['cinematography']} / {ad['rhythm']} / {ad['music']}")
    if gated:
        gate_stop(gates.check_seen(sp, ad["look"], gates.seen()))
        step("gate 2", note="nothing the owner has already seen is repeated")

    # 3a the variation ledger: the variable layer chosen from the subject and away from the channel's last films
    from . import variation
    vledger = variation.Ledger(Path(os.environ.get("CF_VARIATION_LEDGER") or hdir / "variation_ledger.json"))
    vprev = [r for r in vledger.rows(None if sp.get("sample_for") else sp.get("channel", ""))   # samples: against everything shown
             if r.get("film") != film]                                   # a re-render is never compared with itself
    vp = variation.plan(sp, vprev)
    if not (sp.get("art") or {}).get("accent"):
        ad["accent"] = vp["accent"]                      # the palette hue comes from the subject, a third of the wheel away
    vissues = variation.check(sp, vp, vprev)
    (dirs["writing"] / "variation.md").write_text(variation.markdown(vp, vissues), encoding="utf-8")
    if [i for i in vissues if i["level"] == "error"]:
        raise ProductionStopped("variation: " + "; ".join(f"{i['scene']}: {i['problem']}" for i in vissues if i["level"] == "error"))
    step("variation plan", note=f"lead {vp['lead']} + {vp['support']}, hue {vp['hue']:.0f}°, opening {vp['opening']}, {vp['family']}")

    # 3b visual decisions and assets: every line's options weighed; photographs and footage found, scored, licensed
    from . import assets as _assets
    from . import decide
    ledger = _assets.Ledger(Path(os.environ.get("CF_ASSET_LEDGER") or data / "assets" / "ledger.json"))
    os.environ["CF_ASSET_LEDGER"] = str(ledger.path)
    srcs = asset_sources()
    decisions, prev_kinds, prev_pic = [], [], None
    for s in sp["scenes"]:
        d = decide.choose(s["narration"], s, prev_kinds)
        used = s["graphic"]
        v = s.get("visual")
        if v and (d["chosen"] or {}).get("treatment") in ("photo", "footage", "combo") or (v or {}).get("force"):
            need = _assets.Need(scene=s["id"], film=film, subject=v.get("subject", ""), kind=v.get("kind", "photo"), place=v.get("place", ""),
                                era=v.get("era"), purpose=v.get("purpose", "location"), specific=bool(v.get("specific")),
                                queries=v.get("queries", []), orientation="portrait" if size[1] > size[0] else "landscape", min_side=min(size))
            rec, rep = (None, {"reason": "no photo or footage sources on this worker"}) if not srcs else \
                _assets.select(need, srcs, data / "assets" / "files", ledger, ad["palette"], prev_pic, size)
            d["asset_search"] = rep
            if rec:
                head = "Footage" if rec["type"] == "video" else "Photo"
                opts = [f"asset:{rec['id']}", v.get("move", "push" if head == "Photo" else ""), v.get("title", "")]
                for k in ("annotate", "then", "frame", "grade", "at", "light", "in", "speed"):
                    if v.get(k):
                        opts.append(f"{k}: {v[k]}")
                if rec.get("illustrative") or rec.get("illustrative_reason"):
                    opts.append("illustrative")
                used = f"{head}: " + " | ".join(o for o in opts if o)
                s["graphic"] = used
                prev_pic = Path(rec["file"])
        prev_kinds.append(_kind(used))
        decisions.append((s["id"], s["narration"], d, used))
    (dirs["writing"] / "visual_decisions.md").write_text(decide.to_markdown(decisions), encoding="utf-8")
    ledger.export(film, dirs["research"] / "assets.csv")
    step("visual decisions", note=f"{sum(1 for x in decisions if _kind(x[3]) in ('photo', 'photos', 'footage'))} photo / footage shots, "
                                  f"{len(srcs)} asset sources")

    # 4 narration, one file per scene
    ndir = dirs["audio"] / "narration"
    ndir.mkdir(exist_ok=True)
    engine = ""
    timeline: list[dict] = []
    at = 0.0
    kinds = [_kind(s["graphic"]) for s in sp["scenes"]]
    layouts = vox.plan_layouts(kinds, vox._seed("studio", film))
    for i, s in enumerate(sp["scenes"]):
        wav = ndir / f"{s['id']}.wav"
        secs, engine = voice.synth(s["narration"], wav, voice=sp.get("voice", "am_michael"), speed=voice.speed_for(s.get("delivery", "")),
                                   lang=sp.get("lang", "en-us"), guide=sp.get("pronunciation", {}), delivery=s.get("delivery", ""))
        pause = float(s.get("pause", 0.45)) * float(ad["breath"])
        slot = round(max(MIN_SLOT, LEAD_S + secs + pause), 3)
        timeline.append({"scene": s["id"], "act": s["act"], "start": round(at, 3), "end": round(at + slot, 3), "speech_s": round(secs, 3),
                         "narration": s["narration"], "audio": str(wav.relative_to(out)), "pauses": voice.pauses_in(wav)})
        at += slot
    # narration tracks start each line LEAD_S into its slot
    padded = []
    for s, t in zip(sp["scenes"], timeline):
        p = work / f"lead_{s['id']}.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(out / t["audio"]), "-af", f"adelay={int(LEAD_S * 1000)}",
                        "-ar", "48000", "-ac", "1", str(p)], check=True)
        padded.append(p)
    tail = render.TRANSITION_S
    total = at + tail
    narr = dirs["audio"] / "narration.wav"
    render.narration_track(padded, [t["end"] - t["start"] for t in timeline], tail, narr)
    step("narration recorded", note=f"{engine}, {at:.1f}s")

    # 5 the master timeline
    theme = f"editorial~0@{ad['accent']}/{ad['look']}/"
    transitions = []
    for i, s in enumerate(sp["scenes"]):
        from ..pipeline import motivated_transition
        tr = s.get("transition") or ("cut" if i == 0 else motivated_transition(kinds[i - 1], kinds[i]))
        prev = transitions[-1] if transitions else ""
        if not tr or (tr == prev and tr in PLAIN_CUTS and not s.get("transition")):
            # no cause on screen (or the same plain cut again): rotate, so one cut never plays twice in a row
            fam = [x for x in variation.FAMILIES.get(vp["family"], ()) if x in render.TRANSITIONS]
            pool = fam if len(fam) >= 2 else PLAIN_CUTS            # the film's transition family first
            tr = next(x for x in pool[i % len(pool):] + pool if x != prev)
        transitions.append(tr if tr in render.TRANSITIONS else "blur")
    fams = [variation.family_of(t) for t in transitions[1:]] or ["hard cuts"]
    vp["family"] = max(set(fams), key=fams.count)            # the family the film actually uses
    if vprev and vprev[-1].get("family") == vp["family"]:
        raise ProductionStopped(f"variation: transition family '{vp['family']}' was the last film's")
    # real recorded effects from Freesound (CC0 / CC-BY) when the pod has a key; the built-in set otherwise
    from ..providers import freesound
    fs_dir = data / "sfx_freesound"
    if freesound.key():
        freesound.fill_bank(fs_dir)
    bank = sfx.SfxBank.load(str(fs_dir) if fs_dir.is_dir() else "", sfx_builtin.ensure(data / "sfx_builtin"))
    if (fs_dir / "CREDITS.txt").is_file():
        shutil.copy(fs_dir / "CREDITS.txt", dirs["audio"] / "sfx_credits.txt")
    hits = sfx.place(bank, transitions, [t["end"] - t["start"] for t in timeline], [], film)
    beds = ambience.place(data / "ambience", [(t["start"], t["end"] - t["start"], kinds[i], _spec(sp["scenes"][i]["graphic"]), False)
                                              for i, t in enumerate(timeline)])
    for i, (s, t) in enumerate(zip(sp["scenes"], timeline)):
        g = _directed(s["graphic"], ad, s)
        t.update({"visual": g, "kind": kinds[i], "layout": layouts[i] or "-", "transition_in": transitions[i],
                  "camera": (re.search(r"\|\s*camera\s*:\s*(\w+)", g) or [None, "orbit" if kinds[i] in scene3d.KINDS else "drawn"])[1],
                  "animation": "stepped 12 fps" if ad["stepped"] and kinds[i] not in scene3d.KINDS else f"{fps} fps",
                  "onscreen": " / ".join(p.strip() for p in _spec(g).split("|")[:3] if p.strip() and ":" not in p)[:120],
                  "sfx": [Path(h[0]).stem for h in hits if t["start"] - 0.4 <= h[1] < t["end"]],
                  "ambience": [Path(b[0]).stem.split("_")[0] for b in beds if b[1] < t["end"] and b[1] + 0.1 >= t["start"] - 0.2],
                  "music": score.ACT_MOOD.get(s["act"], "inquiry") if ad["music"] != "sparse" or s["act"] in ("hook", "discovery", "ending") else "-",
                  "sources": [src["url"] for c in s.get("claims", []) if c in dos.claims for src in dos.claims[c].sources][:4],
                  "claims": s.get("claims", [])})
    (dirs["timeline"] / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")
    cols = ["scene", "act", "start", "end", "narration", "audio", "visual", "kind", "layout", "camera", "animation", "onscreen", "sfx",
            "ambience", "music", "transition_in", "sources"]
    with open(dirs["timeline"] / "timeline.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(cols)
        for t in timeline:
            wr.writerow([("; ".join(t[c]) if isinstance(t[c], list) else t[c]) for c in cols])
    md = ["# Master timeline", "", "| Scene | Time | Narration | Visual | Camera | In | Sound | Sources |", "|---|---|---|---|---|---|---|---|"]
    for t in timeline:
        md.append(f"| {t['scene']} | {_mmss(t['start'])}-{_mmss(t['end'])} | {t['narration']} | `{t['visual'][:70]}` | {t['camera']} | "
                  f"{t['transition_in']} | {', '.join(t['sfx'] + t['ambience']) or '-'} / {t['music']} | {len(t['sources'])} |")
    (dirs["timeline"] / "timeline.md").write_text("\n".join(md), encoding="utf-8")
    step("master timeline", note=f"{len(timeline)} scenes from the measured audio")
    if gated:
        gate_stop(gates.check_pacing(timeline, kinds))
        step("gate 4", note=f"no shot holds too long (mean {sum(t['end'] - t['start'] for t in timeline) / max(1, len(timeline)):.1f}s)")

    # 6 every scene drawn
    w, h = size
    clips = []
    for i, t in enumerate(timeline):
        seconds = (t["end"] - t["start"]) + render.TRANSITION_S + 0.2
        mp4 = dirs["scenes"] / f"{t['scene']}_{t['kind']}.mp4"
        progress(f"    drawing {t['scene']} {t['kind']} ({seconds:.1f}s)")
        _render_scene(t["kind"], _spec(t["visual"]), theme, w, h, seconds, mp4, work, fps, layouts[i], fetch, lib)
        paper, _ = vox.paper(vox.look_of(theme)["paper"], w, h, work)
        clips.append(render.Clip(paper, t["end"] - t["start"], "static", t["transition_in"], mp4, ff.duration(mp4),
                                 stepped=bool(ad["stepped"]) and t["kind"] not in scene3d.KINDS))
    for t in timeline:                       # what was done to each photograph, in its ledger history
        if t["kind"] in ("photo", "footage"):
            from ..media import photo as _photo
            pl = _photo.parse(t["kind"], _spec(t["visual"]))
            if pl and str(pl.get("path", "")).startswith("asset:"):
                try:
                    pl = _photo.prepare(pl, work, None, w, h)
                    for m in pl.get("mods", []) + [f"camera: {pl.get('move', '')}", f"grade: {pl.get('grade', 'none')}"] + \
                            ([f"annotated: {len(pl['annotate'])} marks"] if pl.get("annotate") else []):
                        ledger.modified(pl["path"].split(":", 1)[1], f"{film}/{t['scene']}: {m}")
                except Exception:  # noqa: BLE001 - the history is a record, never a reason to fail the film
                    pass
    ledger.export(film, dirs["research"] / "assets.csv")
    step("scenes drawn", note=f"{len(clips)} scenes at {w}x{h}")

    # 7 storyboard
    frames = []
    for t in timeline:
        mp4 = dirs["scenes"] / f"{t['scene']}_{t['kind']}.mp4"
        frames.append(_frame(mp4, (t["end"] - t["start"]) * 0.72, dirs["storyboard"] / f"{t['scene']}.png", 480))
    _sheet(frames, [f"{t['scene']} {_mmss(t['start'])} {t['kind']}" for t in timeline], dirs["storyboard"] / "sheet.png")
    sb = ["# Storyboard", ""]
    for t, f in zip(timeline, frames):
        sb += [f"## {t['scene']} · {_mmss(t['start'])}-{_mmss(t['end'])} · {t['act']}", "", f"![{t['scene']}]({f.name})", "",
               f"**Narration:** {t['narration']}", "", f"**Visual:** `{t['visual']}`", "",
               f"**Camera:** {t['camera']} · **Layout:** {t['layout']} · **Animation:** {t['animation']} · **Cut in:** {t['transition_in']}", ""]
    (dirs["storyboard"] / "storyboard.md").write_text("\n".join(sb), encoding="utf-8")
    step("storyboard")

    # 8 score, effects, ambience, mix
    acts, cur = [], None
    for t in timeline:
        if t["act"] != cur:
            acts.append([t["act"], t["start"], 0.0])
            cur = t["act"]
        acts[-1][2] = t["end"] - acts[-1][1]
    acts[-1][2] += tail
    track = sp.get("music_track")
    if track and Path(track).is_file():
        music = score.from_track(Path(track), total, dirs["audio"])      # a licensed track the creator chose
    else:
        music = score.compose([tuple(a) for a in acts], ad["music"], dirs["audio"])
    mix = dirs["audio"] / "mix.wav"
    render.mix_audio(narr, music, total, mix, threading.Event(), sfx=sorted(hits + beds, key=lambda x: x[1]))
    step("sound", note=f"score ({ad['music']}, {score.LAST_HOW or 'none'}), {len(hits)} effects ({bank.describe()}), {len(beds)} ambience beds")

    # 9 the edit
    final = dirs["video"] / f"{film}.mp4"
    expected = render.render_video(clips, mix, None, w, h, final, work, threading.Event(), grade=ad.get("grade", ""))
    step("edit rendered", note=f"{expected:.1f}s")

    # 10 captions
    cues = captions(sp["scenes"], timeline)
    srt, vtt = _write_captions(cues, dirs["captions"] / film)
    step("captions", note=f"{len(cues)} cues")

    # 11 quality control and the watch-through
    qc = quality.check(final, expected, [], expected_size=(w, h))
    # three key frames (opening, climax, ending) beside the last three films': if they could be swapped, redesign
    mid = lambda t: (t["start"] + t["end"]) / 2
    roles = [str(s.get("role", "")).lower() for s in sp["scenes"]]
    ci = roles.index("climax") if "climax" in roles else len(timeline) // 2
    kf, kprob = variation.keyframes(final, [mid(timeline[0]), mid(timeline[ci]), mid(timeline[-1])],
                                    vledger.path.parent / "keyframes" / film, vprev, dirs["qc"] / "keyframes_compare.png")
    vissues += kprob
    if gated:   # key frames that could be swapped with a piece the owner has seen fail gate 2 (reported in PRESHOW.md)
        gate_issues += [{"gate": 2, "level": "error", "scene": "key frames", "problem": k["problem"]} for k in kprob]
    starts = [t["start"] for t in timeline]
    found = _cuts(final)
    drift = [d for d in (min((abs(c - s) for c in found), default=9.9) for s in starts[1:]) if d < 1.0]
    review, problems = [], []
    prev = None
    for t in timeline:
        mid = (t["start"] + t["end"]) / 2
        g = _gray(final, mid)
        if g is None:
            problems.append(f"{t['scene']}: no frame at {mid:.1f}s")
            continue
        if g.std() < 12:
            problems.append(f"{t['scene']}: the frame at {mid:.1f}s is nearly flat")
        if prev is not None and abs(g - prev).mean() < 4:
            problems.append(f"{t['scene']}: looks the same as the scene before")
        prev = g
        review.append(_frame(final, mid, dirs["qc"] / f"watch_{t['scene']}.png", 480))
    _sheet(review, [f"{t['scene']} @{_mmss((t['start'] + t['end']) / 2)}: {t['narration'][:60]}" for t in timeline], dirs["qc"] / "review_sheet.png")
    worst = max(drift) if drift else 0.0
    if worst > 0.35:
        problems.append(f"a cut lands {worst:.2f}s away from its line")
    qmd = ["# Quality control", "", f"Film: {final.name} · {expected:.1f}s · {w}x{h}", "", "## Finished film", ""]
    qmd += [f"- {'OK  ' if c['ok'] else 'FAIL'} {c['name']}: {c['detail']}" for c in qc["checks"]]
    qmd += ["", "## Watch-through (a frame from the middle of every scene, compared with the one before)", ""]
    qmd += [f"- {p}" for p in problems] or ["- every scene shows a distinct, readable picture"]
    # what the viewer reads: each scene page measured its own text once everything had landed (motion.capture)
    small, cut, over = [], [], []
    for t in timeline:
        for f in dirs["scenes"].glob(f"{t['scene']}_*.qa.json"):
            try:
                q = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
            small += [f"{t['scene']}: {x}" for x in q.get("text_below_floor", [])]
            cut += [f"{t['scene']}: {x}" for x in q.get("text_cut_off", [])]
            over += [f"{t['scene']}: {x}" for x in q.get("text_overlap", [])]
    qmd += ["", "## On-screen text (phone test)", ""]
    qmd += [f"- too small to read on a phone: {x}" for x in small] + [f"- cut off at the frame edge: {x}" for x in cut]
    qmd += [f"- words on top of other words: {x}" for x in over]
    problems += [f"text overlap in {x}" for x in over]
    if not small and not cut and not over:
        qmd += ["- every line is at least 2.6% of the frame's short side and inside the frame"]
    phone = [_frame(final, (t["start"] + t["end"]) / 2, dirs["qc"] / f"phone_{t['scene']}.png", 360) for t in timeline]
    _sheet([p for p in phone if p], [t["scene"] for t in timeline], dirs["qc"] / "phone_sheet.png")
    qmd += ["", "Phone-width contact sheet: qc/phone_sheet.png (every scene at 360 px wide)."]
    qmd += ["", "## Sync", "", f"{len(drift)} of {len(starts) - 1} cuts measured; worst {worst:.2f}s, mean "
            f"{(sum(drift) / len(drift)) if drift else 0:.2f}s from the spoken line", "",
            "## Facts", "", "Every figure said or shown is in the evidence its scene cites (editorial review passed)."]
    (dirs["qc"] / "report.md").write_text("\n".join(qmd), encoding="utf-8")
    report["qc"] = {"film": qc, "watch": problems, "sync_worst_s": round(worst, 3)}
    step("quality control", note=("clean" if qc["passed"] and not problems else f"{len(qc['warnings']) + len(problems)} to look at"))

    # 12 thumbnail, SEO, cutdowns
    if sp.get("thumbnail"):
        tk, ts = _kind(sp["thumbnail"]), _spec(sp["thumbnail"]) + " | exit: none | camera: still"
        tmp = work / "thumb.mp4"
        _render_scene(tk, ts if tk in vox.KINDS else _spec(sp["thumbnail"]), theme, 1280, 720, 3.0, tmp, work, 12, "base", fetch, lib)
        _frame(tmp, 2.7, dirs["promo"] / "thumbnail.png", 1280)
    chapters, last = [], None
    names = sp.get("act_titles", {})
    for t in timeline:
        if t["act"] != last:
            chapters.append(f"{_mmss(t['start'])} {names.get(t['act'], t['act'].title())}")
            last = t["act"]
    srcs = []
    for c in dos.claims.values():
        for s in c.sources:
            if s.get("url") and s["url"] not in [x[1] for x in srcs]:
                srcs.append((s.get("title") or s["url"], s["url"]))
    seo = sp.get("seo", {})
    title = seo.get("title") or sp.get("title")
    desc = [seo.get("description") or sp.get("concept", {}).get("logline", ""), "", sp.get("concept", {}).get("central_question", ""), "",
            "Chapters", *chapters, "", "Sources", *[f"- {a}: {b}" for a, b in srcs], "",
            "How this film was made: maps are drawn from public-domain outlines (Natural Earth) and open elevation data; "
            "every chart shows figures from the sources above; reconstructions are drawn and labelled; narration voice: "
            + engine + "."]
    tags = seo.get("keywords") or []
    (dirs["promo"] / "seo.md").write_text(f"# SEO\n\n## Title\n\n{title}\n\n## Description\n\n" + "\n".join(desc)
                                          + "\n\n## Keywords and tags\n\n" + ", ".join(tags), encoding="utf-8")
    (dirs["promo"] / "seo.json").write_text(json.dumps({"title": title, "description": "\n".join(desc), "tags": tags}, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    made = []
    # each cutdown in 9:16 (Shorts, Reels, TikTok) and, when the screenplay asks ("aspects": ["9:16", "1:1"]), in 1:1;
    # every scene is drawn again at that shape (laid out for it), never cropped out of the 16:9 film
    shapes = {"9:16": tuple(cutdown_size), "1:1": (cutdown_size[0], cutdown_size[0]), "4:5": (cutdown_size[0], cutdown_size[0] * 5 // 4)}
    jobs = []
    for n, cd in enumerate(sp.get("cutdowns", []), 1):
        asp = [a for a in (cd.get("aspects") or sp.get("cutdown_aspects") or ["9:16"]) if a in shapes]
        for a in asp or ["9:16"]:
            jobs.append((n if a == "9:16" else f"{n}_{a.replace(':', 'x')}", cd, a))
    for k, cd, aspect in jobs:
        cw, chh = shapes[aspect]
        ids = [x for x in cd.get("scenes", []) if any(t["scene"] == x for t in timeline)]
        if not ids:
            continue
        sub = [t for t in timeline if t["scene"] in ids]
        cclips, wavs, slots = [], [], []
        for t in sub:
            idx = next(i for i, x in enumerate(timeline) if x["scene"] == t["scene"])
            mp4 = work / f"cut{k}_{t['scene']}.mp4"
            sec = (t["end"] - t["start"]) + render.TRANSITION_S + 0.2
            _render_scene(t["kind"], _spec(t["visual"]), theme, cw, chh, sec, mp4, work, fps, layouts[idx], fetch, lib)
            paper, _ = vox.paper(vox.look_of(theme)["paper"], cw, chh, work)
            cclips.append(render.Clip(paper, t["end"] - t["start"], "static", "cut" if not cclips else t["transition_in"], mp4, ff.duration(mp4),
                                      stepped=bool(ad["stepped"]) and t["kind"] not in scene3d.KINDS))
            wavs.append(work / f"lead_{t['scene']}.wav")
            slots.append(t["end"] - t["start"])
        ctot = sum(slots) + tail
        cn = work / f"cut{k}_narr.wav"
        render.narration_track(wavs, slots, tail, cn)
        cm = score.compose([("hook", 0.0, ctot)], "drone", work / f"cut{k}_score")
        cmix = work / f"cut{k}_mix.wav"
        render.mix_audio(cn, cm, ctot, cmix, threading.Event())
        raw = work / f"cut{k}_raw.mp4"
        render.render_video(cclips, cmix, None, cw, chh, raw, work / f"cut{k}", threading.Event(), grade="")
        ccues, at2 = [], 0.0
        for t in sub:
            for a, b, c in cues:
                if t["start"] <= a < t["end"]:
                    ccues.append((a - t["start"] + at2, b - t["start"] + at2, c))
            at2 += t["end"] - t["start"]
        ass = _ass(ccues, cw, chh, work / f"cut{k}.ass")
        dst = dirs["promo"] / f"cutdown_{k}.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(raw), "-vf", f"ass={ass}", "-c:a", "copy",
                        "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(dst)], check=True, timeout=1800)
        _write_captions(ccues, dirs["promo"] / f"cutdown_{k}")
        made.append({"file": dst.name, "title": cd.get("title", ""), "scenes": ids, "seconds": round(ctot, 1), "aspect": aspect})
    (dirs["promo"] / "cutdowns.md").write_text("# Social cutdowns\n\n" + "\n".join(f"- **{m['file']}** ({m['seconds']}s, {m['aspect']}, captions burned in): "
                                                                                   f"{m['title']}; scenes {', '.join(m['scenes'])}" for m in made),
                                               encoding="utf-8")
    step("thumbnail, SEO and cutdowns", note=f"{len(made)} cutdowns")

    # narration script with the final timestamps; asset list; history; index
    (dirs["writing"] / "narration_script.md").write_text(writer.narration_markdown(sp, timeline), encoding="utf-8")
    audit = writer.retention_audit(sp, timeline)
    (dirs["writing"] / "retention_audit.md").write_text(writer.retention_markdown(sp, audit), encoding="utf-8")
    report["retention"] = {"weakest": [w["scene"] for w in audit["weakest"]], "no_interrupt": len(audit["no_interrupt"])}
    assets = ["# Visual assets", "", "| Scene | Asset | Kind | Made from |", "|---|---|---|---|"]
    for t in timeline:
        made_from = ("Natural Earth outlines" if t["kind"] in ("shrink", "pinmap", "route", "heatmap", "arrows", "railmap", "sizemap", "morph")
                     else "open elevation tiles (AWS Terrain)" if t["kind"] == "terrain3d"
                     else "three.js scene" if t["kind"] in scene3d.KINDS else "drawn in the engine")
        assets.append(f"| {t['scene']} | scenes/{t['scene']}_{t['kind']}.mp4 | {t['kind']} | {made_from} |")
    (dirs["writing"] / "asset_list.md").write_text("\n".join(assets), encoding="utf-8")
    vledger.add(variation.row(film, sp, vp, kf, [Path(b[0]).stem for b in beds], round(expected / max(1, len(timeline)), 2)))
    (dirs["writing"] / "variation.md").write_text(variation.markdown(vp, vissues), encoding="utf-8")
    (dirs["writing"] / "variation_ledger.md").write_text(vledger.markdown(), encoding="utf-8")
    artdirection.remember(hdir, {"id": film, "title": sp.get("title"), "channel": sp.get("channel", ""), "engine": sp.get("engine", ""),
                                 "hook_mechanism": sp.get("hook_mechanism", ""), "metaphors": list(sp.get("metaphors", [])), **{k: ad[k] for k in ("look", "accent", "cinematography", "maps",
                                                                                              "infographics", "animation", "rhythm", "music", "grade")},
                                 "kinds": kinds})
    deliver = [("1. Research dossier with source links", "research/dossier.md"), ("2. Documentary concept", "writing/concept.md"),
               ("3. Complete final script", "writing/screenplay.md"), ("4. Separate narration script", "writing/narration_script.md"),
               ("5. Narration audio", "audio/narration.wav"), ("6. Scene-by-scene storyboard", "storyboard/storyboard.md"),
               ("7. Art direction document", "writing/art_direction.md"), ("8. Visual asset list", "writing/asset_list.md"),
               ("9. Map and infographic assets", "scenes/"), ("10. Animation and motion-graphics assets", "scenes/"),
               ("11. Complete editing timeline", "timeline/timeline.csv"), ("12. Captions / subtitles", f"captions/{film}.srt"),
               ("13. Finished documentary", f"video/{film}.mp4"), ("14. Thumbnail", "promo/thumbnail.png"), ("15. SEO title", "promo/seo.md"),
               ("16. Description", "promo/seo.md"), ("17. Keywords and tags", "promo/seo.md"), ("18. Social cutdowns", "promo/cutdowns.md")]
    idx = [f"# {sp.get('title')}", "", sp.get("concept", {}).get("logline", ""), "", f"Running time {_mmss(expected)} · {w}x{h} · {fps} fps",
           "", "| Deliverable | File | Present |", "|---|---|---|"]
    for name, rel in deliver:
        idx.append(f"| {name} | {rel} | {'yes' if (out / rel).exists() else 'NO'} |")
    idx += ["", "Also: writing/editorial_review.md, writing/retention_audit.md, writing/variation.md, qc/keyframes_compare.png, qc/report.md, qc/review_sheet.png, timeline/timeline.md"]
    (out / "README.md").write_text("\n".join(idx), encoding="utf-8")
    report.update({"file": str(final), "seconds": round(expected, 1), "art": ad, "deliverables_missing":
                   [n for n, r in deliver if not (out / r).exists()]})
    (dirs["qc"] / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    step("deliverables", note="all present" if not report["deliverables_missing"] else f"missing: {report['deliverables_missing']}")
    # 14 gate 5: the pre-show list, read by the owner with the video; the piece now counts as seen
    if gated:
        extra = {"symbols": gates.missing_symbols(sp), "editorial": issues, "variation": vissues,
                 "qc": list(qc.get("warnings", [])) + problems, "weakest": report.get("retention", {}).get("weakest", []),
                 "brainlog": gates.brainlog_rules(log)}
        (out / "PRESHOW.md").write_text(gates.preshow(sp, gate_issues, timeline, kinds, report, extra), encoding="utf-8")
        report["preshow"] = str(out / "PRESHOW.md")
        gates.record(gates.entry(sp, "sample" if sp.get("sample_for") else "film", ad["look"]))
        step("gate 5", note="PRESHOW.md written: send it with the video")
    return report
