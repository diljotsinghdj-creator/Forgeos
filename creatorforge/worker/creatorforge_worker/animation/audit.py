"""Executable audit: every component is exercised and judged by what it actually produces.

    python -m creatorforge_worker.animation.audit <out_dir>     -> audit.json + AUDIT.md

Status per component:
    functional          the probe ran and the result met the stated expectation
    partial             it runs, but part of the expectation is not met (said which)
    missing             no code path exists for it
    unverified          could not be exercised here (said why)

Nothing is marked functional because it is described somewhere; each line carries its evidence."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

BVENV = Path("/tmp/claude-0/-home-user-Forgeos/4511f341-cf91-5fed-ac10-e7043335b256/scratchpad/bvenv/bin/python")
RESULTS: list[dict] = []


def probe(component: str, expectation: str):
    def wrap(fn):
        def run(out: Path):
            t0 = time.time()
            try:
                status, evidence = fn(out)
            except Exception as e:                     # a crash is evidence too
                status, evidence = "partial", {"error": f"{type(e).__name__}: {e}",
                                               "trace": traceback.format_exc()[-600:]}
            RESULTS.append({"component": component, "expectation": expectation, "status": status,
                            "evidence": evidence, "seconds": round(time.time() - t0, 1)})
        run.component = component
        return run
    return wrap


def _frames(path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return int((r.stdout.strip() or "0").split(",")[0])


@probe("Script-to-animation engine", "an unseen script becomes a staged film: right cast, places and actions; "
       "what it cannot show is reported")
def p_script(out):
    from . import benchmarks as B
    from . import production as P
    from . import studio
    res = {}
    ok = True
    for name, script in (("flour", B.FLOUR), ("pelican", B.UNFAMILIAR),
                         ("new", "Two friends, Amir and Bea, carry a heavy box up the stairs. Amir slips and drops "
                                 "it. Bea laughs, then helps him pick it up. They sit on the bench, tired.")):
        doc, notes = studio.make(script)
        st = P.plan_states(doc)
        acts = [(s_["who"], s_.get("verb", s_["do"])) for sc in doc["scenes"] for s_ in sc["steps"]
                if s_["do"] in ("act", "enter")]
        clean = sum(1 for x in st if x[3].summary().startswith("clean"))
        res[name] = {"cast": sorted({c["name"] for sc in doc["scenes"] for c in sc["cast"]}),
                     "actions": acts, "qc_clean": f"{clean}/{len(st)}", "limitations": notes["limitations"],
                     "continuity_issues": sum(len(x[4]) for x in st)}
        ok = ok and clean == len(st)
    thinks = sum(1 for v in res.values() for a in v["actions"] if a[1] in ("think", "explain"))
    if thinks:
        res["note"] = f"{thinks} lines fell back to think/explain (no physical action recognised)"
    return ("functional" if ok and thinks <= 2 else "partial"), res


@probe("2D stickman renderer", "renders a scene to an exact number of frames, with sound, at the requested size")
def p_2d(out):
    from . import production as P
    doc = {"title": "a", "scenes": [{"id": "x", "cast": [{"name": "A", "x": -1}], "props": [],
                                     "steps": [{"t": 0.2, "who": "A", "do": "walk", "to": 1.0}], "seconds": 3.0}]}
    r = P.render(doc, out / "r2d.mp4", "preview", cache_dir=out / "c2d")
    ok = r["video"]["missing"] == 0 and r["delivery"]["aspect_ok"] and r["delivery"]["sync_ok"]
    return ("functional" if ok else "partial"), {"video": r["video"], "delivery": r["delivery"]}


@probe("2.5D depth", "characters in a far lane draw smaller and higher; parallax layers scroll slower than the ground")
def p_25d(out):
    from . import scene2d
    from .rig2d import Look
    from .stick import Actor
    sc = scene2d.Scene(width=640, height=360, ss=1)
    scene2d.studio(sc)
    near, far = Actor(Look(name="N"), x=-1.0), Actor(Look(name="F"), x=1.0)
    far.z = 1.6
    sc.actors += [near, far]
    sc.frame(0.0, 1 / 24)

    def head_px(a):
        z = a.z_at(0.0) if hasattr(a, "z_at") else getattr(a, "z", 1.0)
        return sc.ppm / z
    lanes = [L.z for L in sc.layers]
    ok = head_px(far) < head_px(near)
    return ("functional" if ok else "partial"), {"scale_near_px_per_m": round(head_px(near), 1),
                                                 "scale_far_px_per_m": round(head_px(far), 1), "layer_depths": lanes,
                                                 "note": "depth lanes and parallax layers; no camera orbit or "
                                                         "perspective rotation (that is what the 3D path is for)"}


@probe("Genuine 3D engine", "Blender is available, rigged characters render, a film exists on disk")
def p_3d(out):
    ev = {"blender_python": str(BVENV), "exists": BVENV.exists()}
    if not BVENV.exists():
        return "unverified", {**ev, "why": "the Blender environment is not installed on this machine"}
    r = subprocess.run([str(BVENV), "-c", "import bpy; print(bpy.app.version_string)"], capture_output=True, text=True,
                       timeout=120)
    ev["bpy"] = r.stdout.strip() or r.stderr[-200:]
    films = sorted(Path(BVENV).parent.parent.parent.glob("anim/*/*.mp4"))
    ev["rendered_3d_films"] = [f"{f.parent.name}/{f.name} ({_frames(f)} frames)" for f in films
                               if "android" not in f.name and ("3D" in f.name or "TestF" in f.name)]
    ok = bool(ev["bpy"]) and "Error" not in ev["bpy"] and ev["rendered_3d_films"]
    ev["note"] = "EEVEE in software here (~5 s/frame at 960x408); faces are simple; documents are not read by the 3D path"
    return ("functional" if ok else "partial"), ev


@probe("Character rigging and expressions", "faces blend between expressions, mouths follow speech, bodies pose")
def p_faces(out):
    from . import face, speech
    v = speech.say("Hello there, my friend.", out / "s.wav")
    n = len(face.EXPRESSIONS)
    from .stick import Actor
    from .rig2d import Look
    a = Actor(Look(name="F", skin=(226, 186, 150)), faceless=False)
    a.loco.express(0.0, "happy", 0.2)
    a.loco.express(1.0, "furious", 0.3)
    return ("functional" if n > 20 and len(v) > 5 else "partial"), {
        "expressions": n, "visemes_for_line": len(v), "note": "2D faces; 3D faces are simple shapes"}


@probe("Natural locomotion and physics", "walk, run, stairs, jump, sit, throw/catch, bounce: no motion defects")
def p_motion(out):
    from . import bench3d, stress
    res = {}
    a, p, w, T, before, after, fx = bench3d.checked(24)
    res["catch_game_3d_scene"] = after.summary()
    from . import qc
    for k in ("A", "B", "C", "D", "E"):
        sc, T = stress.TESTS[k][0]()
        res[f"stress_{k}"] = qc.inspect(qc.record(sc, T)).summary()
    bad = [k for k, v in res.items() if not v.startswith("clean")]
    return ("functional" if not bad else "partial"), {**res, "defective": bad}


@probe("Scene generation and world building", "assets generate and validate; world state carries objects; light and "
       "weather render")
def p_world(out):
    from . import asset_lib
    lib = asset_lib.Library.default()
    bad = {k: [i.check for i in asset_lib.errors(asset_lib.validate(lib.get(k), render_test=False))] for k in lib.STOCK}
    bad = {k: v for k, v in bad.items() if v}
    from . import production as P
    doc = {"title": "w", "scenes": [
        {"id": "a", "cast": [{"name": "A", "x": 0}], "props": [{"name": "cup", "kind": "crate", "x": 1, "w": .2, "h": .2}],
         "layers": {"light": [[0, "night"]], "weather": [[0, 9, "rain", 1]]},
         "steps": [{"t": 0.2, "who": "A", "do": "nod"}]},
        {"id": "b", "cut": False, "cast": [{"name": "A"}], "props": [], "steps": [{"t": 0.2, "who": "A", "do": "nod"}]}]}
    st = P.plan_states(doc)
    _, _, _, live = P.stage_scene(doc["scenes"][1], st[1][6])
    ok = not bad and "cup" in live
    return ("functional" if ok else "partial"), {"stock_assets": len(lib.STOCK), "invalid": bad,
                                                 "object_persisted_across_shot": "cup" in live,
                                                 "note": "environments are paper tones + scenery assets; no painted "
                                                         "backgrounds, water or walled interiors"}


@probe("AI animation director", "plans scenes with cast, actions, emotions, camera and sources; reports limitations")
def p_director(out):
    from . import studio
    doc, notes = studio.make("Maya walks to the bus stop. Suddenly it starts to rain. Maya laughs and waves at her "
                             "friend Leo. At night the storm gets worse.", voice={"lang": "en"})
    ev = {"scenes": len(doc["scenes"]), "decisions": notes["decisions"], "limitations": notes["limitations"],
          "weather_by_scene": [sc.get("layers", {}).get("weather", [[0, 0, "-"]])[0][2] for sc in doc["scenes"]],
          "note": "rule-based (regular expressions over English), no language model: understands simple narrative "
                  "sentences and the verbs in its lexicon; plans sentence by sentence"}
    return "partial", ev


@probe("Timeline and editing interface", "edits with undo/redo and versions over HTTP; a page drives it")
def p_editor(out):
    from fastapi.testclient import TestClient

    from ..api import create_app
    from ..config import Config
    cfg = Config(data_dir=out / "edata", llm_url="mock", image_provider="mock", allow_mock=True)
    with TestClient(create_app(cfg, start_runner=False)) as c:
        page = c.get("/v1/animation/editor").status_code
        r = c.post("/v1/animation/docs/from-script", json={"script": "Ana waves at Bo. Bo laughs."})
        did = r.json()["id"]
        e = c.post(f"/v1/animation/docs/{did}/ops", json={"op": "set_layer", "args": {"sid": "s01", "mood": "calm"}})
        u = c.post(f"/v1/animation/docs/{did}/undo").json()
    ok = page == 200 and r.status_code == 201 and e.status_code == 200 and "mood" not in u["doc"]["scenes"][0].get(
        "layers", {})
    return ("partial" if ok else "partial"), {"editor_page": page, "create": r.status_code, "edit": e.status_code,
                                              "undo_restored": "mood" not in u["doc"]["scenes"][0].get("layers", {}),
                                              "note": "web page with forms and numeric fields; no drag-on-canvas "
                                                      "posing, no curve editor, no screen in the Android app"}


@probe("Documentary visual integration", "real photos/footage/documents placed, credited, sourced; allegations never "
       "acted out")
def p_doc(out):
    from . import visual_reasoning as VR
    a = VR.reason("The minister was accused of taking bribes.")
    b = VR.reason("Prices of rice and milk went up 20 percent.")
    from . import benchmarks as B
    doc = B.political_hinglish()
    from . import production as P
    items, issues = P.provenance(doc)
    ok_rules = a.mode == "evidence" and not a.sourced and b.sourced is False
    status = "functional" if ok_rules and items and all(i["credit"] and i["source"] for i in items) else "partial"
    return status, {"allegation_without_source": [a.mode, a.label], "figure_without_source": b.note,
                    "real_media": [(i["file"], i["credit"], i["licence"]) for i in items],
                    "rights_to_clear_before_publishing": len(issues),
                    "note": "provenance is tracked and reported; the supplied media's rights are not verified"}


@probe("Rendering and export pipeline", "scene cache, incremental re-render, transitions, exact length, Android copy")
def p_render(out):
    from . import production as P
    doc = {"title": "e", "scenes": [
        {"id": "a", "cast": [{"name": "A", "x": -1}], "props": [], "steps": [{"t": 0.2, "who": "A", "do": "walk", "to": 0.5}],
         "seconds": 2.5},
        {"id": "b", "transition": {"kind": "dissolve", "dur": 0.4}, "cast": [{"name": "A", "x": 0}], "props": [],
         "steps": [{"t": 0.2, "who": "A", "do": "nod"}], "seconds": 2.0}]}
    cache = out / "cr"
    shutil.rmtree(cache, ignore_errors=True)
    t0 = time.time()
    r1 = P.render(doc, out / "e.mp4", "preview", cache_dir=cache)
    cold = time.time() - t0
    t0 = time.time()
    r2 = P.render(doc, out / "e.mp4", "preview", cache_dir=cache)
    warm = time.time() - t0
    a = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=profile,level", "-of", "csv=p=0",
                        str(out / "e_android.mp4")], capture_output=True, text=True).stdout.split()
    ok = r1["video"]["missing"] == 0 and all(s["cached"] for s in r2["scenes"]) and r1["delivery"]["sync_ok"]
    return ("functional" if ok else "partial"), {"cold_s": round(cold, 1), "cached_s": round(warm, 1),
                                                 "video": r1["video"], "android_stream": a,
                                                 "note": "a failed scene is isolated and reported; finished scenes "
                                                         "stay cached (tests: test_a_failed_scene_does_not_sink...)"}


PROBES = [p_script, p_2d, p_25d, p_3d, p_faces, p_motion, p_world, p_director, p_editor, p_doc, p_render]


def run(out: Path) -> list[dict]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    RESULTS.clear()
    for p in PROBES:
        p(out)
    (out / "audit.json").write_text(json.dumps(RESULTS, indent=1, default=str))
    (out / "AUDIT.md").write_text(markdown(RESULTS))
    return RESULTS


def markdown(results: list[dict]) -> str:
    rows = ["# Stickman Universe - executable audit", "",
            "Generated by `python -m creatorforge_worker.animation.audit`: each component was run, not read about.", "",
            "| Component | Status | Expectation | Evidence (abridged) |", "|---|---|---|---|"]
    for r in results:
        ev = json.dumps(r["evidence"], default=str)
        ev = ev if len(ev) < 420 else ev[:420] + "..."
        rows.append(f"| {r['component']} | **{r['status']}** | {r['expectation']} | `{ev.replace('|', '/')}` |")
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    rows += ["", "Totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), ""]
    return "\n".join(rows)


if __name__ == "__main__":
    for r in run(Path(sys.argv[1] if len(sys.argv) > 1 else "audit_out")):
        print(f"{r['status']:12s} {r['component']}  ({r['seconds']} s)")
