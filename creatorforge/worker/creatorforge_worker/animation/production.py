"""Productions: an editable document, an editor with history, and scene-level rendering.

The document (plain JSON) is the whole film:

    {"title", "fps", "scenes": [
       {"id", "name", "place": "studio|outdoors|indoors", "seconds": optional, "cut": true|false,
        "cast":  [{"name", "body": [r,g,b], "height", "skin", "faceless", "x", "facing", "personality"}],
        "props": [{"name", "kind", "x", "y", "w", "h", "asset": optional library id, "z"}],
        "world": {"platforms": [[x0, x1, top]], "stairs": [[x0, steps, rise, run, landing]]},
        "camera": {"style": "explainer|comedy|drama|action|satire", "keys": optional [[t, x, cy, zoom]]},
        "layers": {"paper": [r,g,b], "mood": optional, "caption": optional text},
        "steps": [ {"t": seconds | "+gap" (after the previous step), "who", "do", ...args} ]}]}

Steps ("do"): walk, run, turn, jump, climb, sit, crawl, trip, pick_up, put_down, throw (to), catch, push, point,
comfort (to), step_back, nod, posture, symbol, move (a prop: a car drives, a dog trots), gesture (name), feel
(emotion, dur), express (face, blend), look (at), say (text, offset, pace), line (dialogue through
performance.perform), pose (keyed pose: {"keys": [[dt, {field: value}, ease]]}), visual (a narration line staged
by visual_reasoning, with its sources), caption, and comedy beats (double_take, slow_burn, deadpan, pratfall,
take, button). A scene with "footage" (path, start, dur, credit) is real footage, framed and credited.

Editing (`Editor`): every change is an operation - add/move/delete scenes, insert/update/delete steps, set a key
pose, shift lip sync, set an expression, set camera keys or style, set a layer, replace an asset, change cast -
with undo, redo and saved versions you can go back to. The user keeps control of everything the automatic
director produced: the director writes steps, a person edits them.

Rendering (`render`): scenes are staged in order (each starts from the world state the last one ended in, so
props in hand and positions carry over), checked (QC + continuity), then rendered one by one or in parallel,
each cached by a hash of its content and incoming state - an unchanged scene is never rendered twice. Preview
quality (480p, no supersampling) for fast iteration; final quality (1080p, supersampled, motion blur) for
delivery; an Android-compatible copy is always written."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from . import comedy as C
from . import motions as M
from . import qc, rig2d, worldstate
from .stick import World

QUALITY = {"preview": dict(width=854, height=480, ss=1, blur=0, fps=24),
           "final": dict(width=1920, height=1080, ss=2, blur=2, fps=30)}


# ---- the editor ---------------------------------------------------------------------------------------------------------
class Editor:
    def __init__(self, doc: dict, history_dir: Path | None = None):
        self.doc = copy.deepcopy(doc)
        self._undo: list[tuple[str, dict]] = []
        self._redo: list[tuple[str, dict]] = []
        self.history_dir = Path(history_dir) if history_dir else None

    # every operation goes through here: snapshot, apply, remember
    def _op(self, label: str, fn):
        before = copy.deepcopy(self.doc)
        fn(self.doc)
        self._undo.append((label, before))
        self._redo.clear()
        return self

    def undo(self) -> str:
        if not self._undo:
            return ""
        label, before = self._undo.pop()
        self._redo.append((label, copy.deepcopy(self.doc)))
        self.doc = before
        return label

    def redo(self) -> str:
        if not self._redo:
            return ""
        label, after = self._redo.pop()
        self._undo.append((label, copy.deepcopy(self.doc)))
        self.doc = after
        return label

    def history(self) -> list[str]:
        return [label for label, _ in self._undo]

    def _scene(self, d, sid):
        return next(s for s in d["scenes"] if s["id"] == sid)

    # scenes
    def add_scene(self, scene: dict, at: int | None = None):
        return self._op(f"add scene {scene['id']}",
                        lambda d: d["scenes"].insert(len(d["scenes"]) if at is None else at, copy.deepcopy(scene)))

    def move_scene(self, sid: str, to: int):
        def f(d):
            s = self._scene(d, sid)
            d["scenes"].remove(s)
            d["scenes"].insert(to, s)
        return self._op(f"move scene {sid} to {to}", f)

    def delete_scene(self, sid: str):
        return self._op(f"delete scene {sid}", lambda d: d["scenes"].remove(self._scene(d, sid)))

    # steps
    def insert_step(self, sid: str, index: int, step: dict):
        return self._op(f"insert step in {sid}", lambda d: self._scene(d, sid)["steps"].insert(index, dict(step)))

    def update_step(self, sid: str, index: int, **changes):
        return self._op(f"edit step {index} of {sid}", lambda d: self._scene(d, sid)["steps"][index].update(changes))

    def delete_step(self, sid: str, index: int):
        return self._op(f"delete step {index} of {sid}", lambda d: self._scene(d, sid)["steps"].pop(index))

    def set_pose(self, sid: str, who: str, t: float, keys: list):
        """A keyed pose: keys = [[dt, {field: value}, ease]] (fields: lean, head, au, al, bu, bl, lu, ll, mu, ml,
        dx, y, squash, feet, hands)."""
        return self.insert_step(sid, len(self._scene(self.doc, sid)["steps"]),
                                {"t": t, "who": who, "do": "pose", "keys": keys})

    def set_expression(self, sid: str, who: str, t: float, face: str, blend: float = 0.25):
        return self.insert_step(sid, len(self._scene(self.doc, sid)["steps"]),
                                {"t": t, "who": who, "do": "express", "face": face, "blend": blend})

    def shift_lipsync(self, sid: str, index: int, offset: float):
        return self._op(f"lip sync {offset:+.2f}s on step {index} of {sid}",
                        lambda d: self._scene(d, sid)["steps"][index].update(offset=offset))

    # camera, layers, cast, assets
    def set_camera(self, sid: str, style: str | None = None, keys: list | None = None):
        def f(d):
            cam = self._scene(d, sid).setdefault("camera", {})
            if style:
                cam["style"] = style
            if keys is not None:
                cam["keys"] = keys
        return self._op(f"camera of {sid}", f)

    def set_layer(self, sid: str, **layers):
        return self._op(f"layers of {sid}", lambda d: self._scene(d, sid).setdefault("layers", {}).update(layers))

    def set_cast(self, sid: str, name: str, **changes):
        return self._op(f"cast {name} in {sid}",
                        lambda d: next(c for c in self._scene(d, sid)["cast"] if c["name"] == name).update(changes))

    def replace_asset(self, sid: str, prop: str, asset_id: str):
        return self._op(f"replace {prop} with asset {asset_id}",
                        lambda d: next(p for p in self._scene(d, sid)["props"] if p["name"] == prop).update(asset=asset_id))

    # versions
    def save_version(self, message: str) -> str:
        if self.history_dir is None:
            raise ValueError("no history directory")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        body = json.dumps(self.doc, sort_keys=True, indent=1)
        vid = time.strftime("%Y%m%d-%H%M%S") + "-" + hashlib.sha1(body.encode()).hexdigest()[:8]
        (self.history_dir / f"{vid}.json").write_text(body)
        idx = self.history_dir / "versions.json"
        log = json.loads(idx.read_text()) if idx.exists() else []
        log.append({"id": vid, "message": message, "ops": self.history()})
        idx.write_text(json.dumps(log, indent=1))
        return vid

    def versions(self) -> list[dict]:
        idx = self.history_dir / "versions.json"
        return json.loads(idx.read_text()) if idx.exists() else []

    def restore(self, vid: str):
        doc = json.loads((self.history_dir / f"{vid}.json").read_text())
        return self._op(f"restore version {vid}", lambda d: (d.clear(), d.update(doc)))


# ---- staging -------------------------------------------------------------------------------------------------------------
def _world(spec: dict) -> World:
    w = World()
    for x0, x1, top in spec.get("platforms", []):
        w.platforms.append((x0, x1, top))
    for x0, n, rise, run, landing in spec.get("stairs", []):
        w.stairs(x0, int(n), rise, run, landing=landing)
    return w


def stage_scene(scene: dict, state: worldstate.WorldState, fps: int = 30, quality: str = "final"):
    """(Scene, seconds, actors, props) for one scene, continuing from `state`."""
    from . import performance as PF
    from . import scene2d
    from .asset_lib import Library
    from .behaviour import PERSONALITIES
    from .stick_demos import _caption
    from .timing import PROFILES
    Q = QUALITY[quality]
    layers = scene.get("layers", {})
    sc = scene2d.Scene(width=Q["width"], height=Q["height"], fps=Q["fps"], ss=Q["ss"],
                       ppm=230 * Q["height"] / 1080, ground=0.8, horizon=0.6)
    sc.motion_blur = Q["blur"]
    scene2d.studio(sc, paper=tuple(layers.get("paper", {"outdoors": (232, 238, 226), "indoors": (246, 242, 234)}
                                       .get(scene.get("place"), (240, 242, 246)))))
    w = _world(scene.get("world", {}))
    cast = []
    anchor = next((c["x"] for c in scene.get("cast", []) if isinstance(c.get("x"), (int, float))), None)
    if anchor is None:
        anchor = next((state.entities[c["name"]].x for c in scene.get("cast", []) if c["name"] in state.entities
                       and state.entities[c["name"]].kind == "actor"), 0.0)
    for c in scene.get("cast", []):
        if c.get("x") == "offstage":                  # someone who walks in later: waits out of shot
            c = {**c, "x": anchor + 6.5, "facing": -1}
        look = rig2d.Look(name=c["name"], body=tuple(c["body"]) if c.get("body") else None, line=1.0,
                          height=c.get("height", 1.75), skin=tuple(c["skin"]) if c.get("skin") else (255, 255, 255))
        spec = {"name": c["name"], "look": look, "faceless": c.get("faceless", True), "seed": len(cast)}
        if scene.get("cut", True) or c["name"] not in state.entities:
            spec.update({k: c[k] for k in ("x", "facing") if k in c})
        cast.append(spec)
    lib = Library.default()
    props = []
    for p in scene.get("props", []):
        p = dict(p)
        if p.get("asset"):                              # a library id, or a description to generate
            aid = p["asset"] if p["asset"] in lib.items else lib.obtain(p["asset"])[0]
            spec = lib.prop_spec(aid)
            spec["data"] = {**spec["data"], **p.get("data", {}), "flip": p.get("flip", 1.0)}
            p.update({k: v for k, v in spec.items() if k not in p or k in ("kind", "data")})
            uses = lib.get(aid).get("uses", [])
            if "z" not in p and ("background" in uses or "stand_near" in uses) and "carry" not in uses:
                p["z"] = 1.5                              # scenery stands in a lane behind the characters
        props.append(p)
    actors, live = worldstate.seed(state, cast, props, world=w, carry=not scene.get("cut", True))
    sc.show = []
    for p in props:                                   # documents and charts the camera must keep in the shot
        if p.get("frame") and p["name"] in live:
            pr = live[p["name"]]
            sc.show.append((p["frame"][0], p["frame"][1], pr.x - pr.w / 2, pr.x + pr.w / 2, pr.y, pr.y + pr.h))
    profile = scene.get("timing", "explainer")
    for a in actors.values():
        a.timing = PROFILES.get(profile)
    pers = {c["name"]: PERSONALITIES.get(c.get("personality", "kind")) for c in scene.get("cast", [])}
    sc.actors += list(live.values()) + list(actors.values())
    sc.narration = []
    stuff = None                                      # animals, objects and scenery the script named

    def things():
        nonlocal stuff
        if stuff is None:
            from .storyboard import _Stuff
            stuff = _Stuff(sc, w)
            for n, p in live.items():
                if p.kind == "shape" and n not in {a["name"] for a in scene.get("animals", [])}:
                    stuff.things[n] = p
        return stuff
    here = next((a.hips_x(0.0) for a in actors.values()), anchor)
    for an in scene.get("animals", []):
        if an["name"] in live:                        # still here from the last shot (and still holding...)
            things().animals[an["name"]] = live[an["name"]]
            for p in live.values():
                if p.data.get("held_by_animal") == an["name"]:
                    things().held[an["name"]] = p
        else:
            things().animal(an["name"], an.get("desc", an["name"]), here, 0.0, an.get("landing", False))
    if scene.get("things"):
        things().place(SimpleNamespace(things=scene["things"]), here, 0.0, actors)
    aux: dict = {}                                    # the script director's own props (balls, crates, signs)
    if scene.get("focus"):
        sc.focus = [(0.0, 1e9, list(scene["focus"]))]
    t = 0.0
    notes = []
    sc.voiced = {}                                    # caption start -> spoken seconds (for the subtitle check)
    for st in scene.get("steps", []):
        st = dict(st)
        when = st.get("t", "+0.2")
        t0 = t + float(when) if isinstance(when, str) and when[:1] in "+-" else float(when)   # "+0.2" / "-1": relative
        a = actors.get(st.get("who", ""))
        do = st["do"]
        end = t0
        if do == "walk":
            end = a.walk(t0, st["to"], st.get("speed", 1.2))
        elif do == "run":
            end = a.run(t0, st["to"], st.get("speed", 3.6))
        elif do == "turn":
            a.turn(t0, st.get("facing", -a._facing_at_build(t0)))
            end = t0 + 0.3
        elif do == "jump":
            end = M.jump(a, t0, st.get("dist", 1.0), st.get("height", 0.45), st.get("land", 0.0))
        elif do == "climb":
            end = M.climb(a, t0, st["wall"], st["top"])
        elif do == "sit":
            end = M.sit(a, t0, st.get("seat", 0.45), st.get("hold", 2.0))
        elif do == "crawl":
            end = M.crawl(a, t0, st.get("dist", 1.5))
        elif do == "trip":
            end = M.trip_roll(a, t0)
        elif do == "pick_up":
            end = M.pick_up(a, t0, live[st["what"]])
        elif do == "put_down":
            end = M.put_down(a, t0, live[st["what"]], on=st.get("on", 0.0))
        elif do == "throw":
            to = actors[st["to"]]
            end = M.throw(a, t0, live[st["what"]], lambda tt, to=to: M.chest(to, tt), st.get("flight", 0.9))
            M.catch(to, end, live[st["what"]], st.get("hold", 1.5))
        elif do == "push":
            end = M.push(a, t0, live[st["what"]], st["dist"], st.get("speed", 0.75))
        elif do == "act":                              # a verb the script director understands, with its target
            from . import storyboard as SB
            act = {"who": st["who"], "verb": st["verb"], "target": st.get("target", ""), "emotion": "",
                   "line": st.get("line", "")}
            beat = SimpleNamespace(things=st.get("things", scene.get("things", [])))
            if st["who"] in things().animals:
                end = things().animal_do(act, t0, actors, beat)
            elif a is not None and things().handles(act, a, actors, beat):
                end = things().actor_do(act, a, t0, actors, beat)
            elif a is not None:
                end = SB._do(sc, w, a, actors.get(act["target"]), act, t0, actors, aux)
        elif do == "enter":                            # walks in from out of shot to stand by someone
            near = actors.get(st.get("near", "")) or next((x for n, x in actors.items() if n != st["who"]), None)
            dest = (near.hips_x(t0) + 1.6) if near is not None else a.hips_x(t0) - 5.0
            end = a.walk(t0, dest, st.get("speed", 1.3))
            if near is not None:
                a.look_at(end - 0.6, end + 1.5, near)
        elif do == "metaphor":
            from . import storyboard as SB
            aux["_subject_x"] = a.hips_x(t0) if a is not None else here
            SB._metaphor(sc, w, st["kind"], t0, t0 + st.get("dur", 5.0), aux)
            end = t0
        elif do == "move":                             # a prop (a car drives, a dog trots): wheels and legs follow
            pr = live[st["what"]]
            x_now = pr.pos(t0)[0]
            dur = st.get("dur") or abs(st["to"] - x_now) / st.get("speed", 1.5)
            pr.move(t0, t0 + dur, st["to"], st.get("y", pr.pos(t0)[1]), 0.0, st.get("ease", "inout"))
            end = t0 + dur
        elif do == "comfort":
            end = M.comfort(a, t0, actors[st["to"]], st.get("dur", 2.0))
        elif do == "step_back":
            end = M.step_back(a, t0, st.get("dist", 0.35))
        elif do == "nod":
            end = a.nod(t0, st.get("dur", 0.7), st.get("kind", "yes"))
        elif do == "posture":
            a.posture(t0, t0 + st.get("dur", 2.0), st.get("lean", 0.0), st.get("crouch", 0.0))
            end = t0 + st.get("dur", 2.0)
        elif do == "symbol":
            a.say_symbol(t0, t0 + st.get("dur", 1.0), st["text"])
            end = t0 + st.get("dur", 1.0)
        elif do == "point":
            end = M.point_at(a, t0, tuple(st["at"]), st.get("dur", 1.6))
        elif do == "gesture":
            end = a.gesture(t0, st["name"], st.get("dur", 1.5))
        elif do == "feel":
            end = a.feel(t0, t0 + st.get("dur", 1.5), st["emotion"])
        elif do == "express":
            a.loco.express(t0, st["face"], st.get("blend", 0.25))
        elif do == "look":
            target = actors.get(st["at"]) or live.get(st["at"]) or tuple(st["at"])
            end = a.look_at(t0, t0 + st.get("dur", 1.5), target)
        elif do == "say":
            off = st.get("offset", 0.0)
            dur = st.get("dur", max(1.6, 0.075 * len(st["text"]) / st.get("pace", 1.0) + 0.8))
            end = a.say_line(t0 + off, t0 + off + dur, st["text"], st.get("face")) - off
        elif do == "line":
            end, _ = PF.perform(st["lines"], actors, pers, t0, profile)
        elif do == "pose":
            end = a.act(t0, [(k[0], k[1], k[2] if len(k) > 2 else "inout") for k in st["keys"]], st.get("name", "pose"))
        elif do in ("double_take", "slow_burn"):
            fn = getattr(C, do)
            target = actors.get(st.get("at")) or live.get(st.get("at")) or (0.0, 1.4)
            end = fn(a, t0, target, sc=sc) if do == "double_take" else fn(a, t0, target, st.get("dur", 3.0), sc=sc)
        elif do in ("deadpan", "pratfall", "take", "button"):
            end = getattr(C, do)(a, t0, sc=sc) if do != "take" else C.take(a, t0)
        elif do == "visual":                           # visual reasoning: how to show this line, honestly
            from . import visual_reasoning as VR
            plan = VR.reason(st["text"], st.get("sources"))
            dur = st.get("dur", 6.0)
            if st.get("voice"):
                wav, secs = narrate(st["voice"])
                sc.narration.append((t0 + 0.15, str(wav)))
                dur = max(dur, secs + 0.55)
                sc.voiced[round(t0, 3)] = secs
            VR.stage(sc, plan, t0, t0 + dur, x=a.hips_x(t0) + st.get("x", 3.2) if a is not None and st.get("near")
                     else st.get("x", 3.2))
            sc.visual_plans = getattr(sc, "visual_plans", []) + [plan]
            if st.get("caption", True):
                notes.append((t0, t0 + dur, st["text"]))
            end = t0 + dur
        elif do == "caption":                          # narration on screen; hold=True waits for it to be read
            dur = st.get("dur") or max(2.6, 0.062 * len(st["text"]) + 1.0)
            if st.get("voice"):                       # ... and spoken: the line lasts as long as the voice
                wav, secs = narrate(st["voice"])
                sc.narration.append((t0 + 0.15, str(wav)))
                dur = max(st.get("dur") or 0.0, secs + 0.55)
                sc.voiced[round(t0, 3)] = secs
            notes.append((t0, t0 + dur, st["text"]))
            from . import visual_reasoning as VR      # narration is audited too: facts need sources
            sc.visual_plans = getattr(sc, "visual_plans", []) + [VR.reason(st["text"], st.get("sources"))]
            end = t0 + dur if st.get("hold") else t0
        elif do == "wait":
            end = t0 + st.get("dur", 1.0)
        elif do == "wait_notes":                       # until the narration on screen has been read / spoken
            end = max([n[1] for n in notes] + [t0])
        if st.get("wait", True):
            t = max(t, end)
    seconds = scene.get("seconds") or t + 0.8
    if layers.get("mood"):
        sc.moods = [(0.0, seconds, layers["mood"])]
    if layers.get("tag"):
        sc.tags = [(0.0, seconds, layers["tag"])]
    sc.overlay = _caption(layers.get("caption", scene.get("name", "")), notes)
    sc.subtitles = [(a_, b_, text, sc.voiced.get(round(a_, 3))) for a_, b_, text in notes]
    cam = scene.get("camera", {})
    if cam.get("keys"):
        from .scene2d import CamKey
        sc.cams = [CamKey(k[0], k[1], k[2], k[3]) for k in cam["keys"]]
    sc.style = cam.get("style", "explainer")
    sc.asset_log = stuff.assets if stuff is not None else []
    sc.decisions = stuff.log if stuff is not None else []
    if stuff is not None:                             # the animals and objects the script named are part of the
        for p in list(stuff.animals.values()) + list(stuff.things.values()):      # world from now on
            live.setdefault(p.name, p)
    return sc, seconds, actors, live


NARRATION_CACHE = Path(os.environ.get("CF_NARRATION_CACHE", Path(tempfile.gettempdir()) / "cf_narration"))


def narrate(voice: dict) -> tuple[Path, float]:
    """A narration line as speech (espeak-ng: offline, English and Hindi - Hinglish is Devanagari Hindi with English
    words, which the Hindi voice reads in English). voice: {"say": text, "lang": "en|hi", "rate", "pitch"}.
    Cached by content; returns (wav, seconds)."""
    from . import speech
    NARRATION_CACHE.mkdir(parents=True, exist_ok=True)
    key = _hash(voice)
    wav = NARRATION_CACHE / f"{key}.wav"
    if not wav.exists():
        speech.say(voice["say"], wav, lang=voice.get("lang", "en"), voice=voice.get("voice", ""),
                   rate=voice.get("rate", 150), pitch=voice.get("pitch", 48))
    return wav, speech.wav_seconds(wav)


def _mix_narration(track: Path, clips: list, out: Path) -> Path:
    """Lays the narration over the scene's soundtrack, ducking the effects and ambience under the voice."""
    import wave

    import numpy as np
    with wave.open(str(track)) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        bed = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32).reshape(-1, ch) / 32768.0
    gain = np.ones(len(bed), dtype=np.float32)
    voice = np.zeros(len(bed), dtype=np.float32)
    for start, path in clips:
        with wave.open(str(path)) as w:
            vr, vn = w.getframerate(), w.getnframes()
            v = np.frombuffer(w.readframes(vn), dtype="<i2").astype(np.float32) / 32768.0
        v = np.interp(np.arange(0, len(v), vr / sr), np.arange(len(v)), v)        # to the track's rate
        i0 = int(start * sr)
        i1 = min(len(bed), i0 + len(v))
        if i1 <= i0:
            continue
        voice[i0:i1] += v[:i1 - i0] * 0.95
        fade = int(0.15 * sr)
        lo, hi = max(0, i0 - fade), min(len(bed), i1 + fade)
        gain[lo:hi] = np.minimum(gain[lo:hi], 0.45)
    mixed = bed * gain[:, None] + voice[:, None]
    peak = max(1e-6, float(np.abs(mixed).max()))
    mixed = mixed * min(1.0, 0.95 / peak)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((mixed * 32767).astype("<i2").tobytes())
    return out


def _hash(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(json.dumps(p, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


class _Footage:
    """Stands in for a QC report on a real-footage scene (nothing animated to check)."""
    defects: list = []

    def __init__(self, seconds):
        self.seconds = seconds

    def summary(self) -> str:
        return f"real footage ({self.seconds:.1f} s, not animated)"


def plan_states(doc: dict, quality: str = "preview"):
    """Stages every scene in order and returns per scene: (start state, end state, seconds, qc report,
    continuity issues with the previous scene, corrections, incoming state)."""
    state = worldstate.WorldState()
    out = []
    for i, scene in enumerate(doc["scenes"]):
        if scene.get("footage"):                       # a cut to real footage: the world state passes through
            T = float(scene.get("dur") or _probe_seconds(scene["footage"]) - scene.get("start", 0.0))
            out.append((state, state, T, _Footage(T), [], [], state))
            continue
        sc, T, actors, live = stage_scene(scene, state, QUALITY[quality]["fps"], quality)
        R = qc.record(sc, T)
        rep = qc.inspect(R)
        fixes = qc.corrections(R, rep)
        acts, props = list(actors.values()), list(live.values())
        sc0, _, a0, l0 = stage_scene(scene, state, QUALITY[quality]["fps"], quality)
        for a in a0.values():
            a.step(0.0, 1 / 30)
        start = worldstate.capture(list(a0.values()), list(l0.values()), 0.0, scene["id"])
        end = worldstate.capture(acts, props, T - 1 / R.fps, scene["id"])
        issues = worldstate.check(out[-1][1], start, cut=scene.get("cut", True)) if out else []
        out.append((start, end, T, rep, issues, fixes, state))
        state = end
    return out


def _probe_seconds(path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\u2019").replace(":", "\\:").replace("%", "\\%")


def _render_footage(scene: dict, quality: str, out: str) -> str:
    """Real footage framed for 16:9 (a blurred fill behind portrait material), credited on screen for its whole
    length, at the production's size and frame rate, with its own sound or silence."""
    from .props_draw import BOLD
    Q = QUALITY[quality]
    W, H = Q["width"], Q["height"]
    start, dur = scene.get("start", 0.0), float(scene.get("dur") or _probe_seconds(scene["footage"]) - scene.get("start", 0.0))
    fs = max(12, H // 36)
    label, credit = _esc(scene.get("label", "REAL FOOTAGE")), _esc(scene.get("credit", ""))
    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=20:2,eq=brightness=-0.12[bg];"
          f"[0:v]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,"
          f"drawbox=x={W // 32}:y={H - H // 6}:w={W // 2}:h={H // 9}:color=black@0.62:t=fill,"
          f"drawtext=fontfile={BOLD}:text='{label}':x={W // 32 + fs}:y={H - H // 6 + fs // 2}:fontsize={fs}:fontcolor=white,"
          f"drawtext=fontfile={BOLD}:text='{credit}':x={W // 32 + fs}:y={H - H // 6 + int(fs * 1.9)}:fontsize={int(fs * 0.8)}:"
          f"fontcolor=0xdddddd,fps={Q['fps']},format=yuv420p[v]")
    has_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                                           scene["footage"]], capture_output=True, text=True).stdout
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", f"{dur:.3f}", "-i", scene["footage"]]
    if not has_audio:
        cmd += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    cmd += ["-filter_complex", vf, "-map", "[v]", "-map", "0:a" if has_audio else "1:a", "-c:v", "libx264", "-crf", "16",
            "-preset", "medium", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", out]
    subprocess.run(cmd, check=True)
    return out


def _render_one(args):
    doc_scene, state_json, quality, out, fixes = args
    if doc_scene.get("footage"):
        return _render_footage(doc_scene, quality, out)
    from . import sound
    state = worldstate.WorldState(**{**state_json, "entities": {k: worldstate.Entity(**v)
                                                                for k, v in state_json["entities"].items()}})
    def build():
        s, T_, _, _ = stage_scene(doc_scene, state, QUALITY[quality]["fps"], quality)
        return s, T_
    sc, T = build()
    framing, passes = [], 0
    if sc.cams:                                       # the editor set the camera by hand: keep it
        qc.apply(sc, fixes)
    else:                                             # directed, then checked: anyone's head (or a speaker's
        sc, T, _, framing, passes, fixes = qc.refine(build, style=sc.style, tries=3)   # bubble) out of the safe
    wav = sound.soundtrack(build, fixes, sc, T, doc_scene.get("place", "studio"), Path(out).with_suffix(".wav"))
    if getattr(sc, "narration", None):
        wav = _mix_narration(wav, sc.narration, Path(out).with_suffix(".voice.wav"))
    sc.render(Path(out), T, audio_wav=wav)            # area widens the shot and directs again
    Path(out).with_suffix(".camera.json").write_text(json.dumps({"passes": passes, "framing": [
        [d.kind, d.who, d.t0, d.t1] for d in framing]}))
    return out


def render(doc: dict, out: Path, quality: str = "preview", workers: int = 1, cache_dir: Path | None = None) -> dict:
    """Renders the production. Returns a report: per-scene QC, continuity, cache hits and timings."""
    from dataclasses import asdict
    out = Path(out)
    cache = Path(cache_dir or out.parent / "scene_cache")
    cache.mkdir(parents=True, exist_ok=True)
    states = plan_states(doc, quality)
    jobs, files, report = [], [], {"scenes": []}
    for scene, (start, end, T, rep, issues, fixes, incoming) in zip(doc["scenes"], states):
        key = _hash(scene, asdict(incoming), quality, fixes, _code_version())
        f = cache / f"{scene['id']}-{key}.mp4"
        files.append(f)
        hit = f.exists()
        report["scenes"].append({"id": scene["id"], "seconds": round(T, 2), "qc": rep.summary(),
                                 "corrections": fixes, "continuity": [asdict(i) for i in issues], "cached": hit})
        if not hit:
            jobs.append((scene, asdict(incoming), quality, str(f), fixes))
    t0 = time.time()
    if workers > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(workers) as ex:
            list(ex.map(_render_one, jobs))
    else:
        for j in jobs:
            _render_one(j)
    report["render_seconds"] = round(time.time() - t0, 1)
    for s_, f in zip(report["scenes"], files):         # camera passes and any framing left after them
        cj = f.with_suffix(".camera.json")
        if cj.exists():
            s_["camera"] = json.loads(cj.read_text())
    fps = QUALITY[quality]["fps"]
    frames = sum(int(round(st[2] * fps)) for st in states)        # what each scene render writes
    lst = cache / f"{out.stem}_list.txt"
    lst.write_text("".join(f"file '{f.resolve()}'\n" for f in files))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "libx264",
                    "-preset", "medium", "-crf", "16" if quality == "final" else "22", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-t", f"{(frames - 0.5) / fps:.6f}", "-movflags", "+faststart",
                    str(out)], check=True)
    android = out.with_name(out.stem + "_android.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "libx264", "-profile:v", "main", "-level",
                    "4.0", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-movflags", "+faststart",
                    str(android)], check=True)
    report["video"] = qc.check_video(out, frames / fps, fps)
    report["delivery"] = qc.check_delivery(out, QUALITY[quality]["width"], QUALITY[quality]["height"], fps)
    subs, t_off = [], 0.0
    for scene, st in zip(doc["scenes"], states):     # subtitles: readable speed, on screen while spoken
        if not scene.get("footage"):
            sc_, _, _, _ = stage_scene(scene, st[6], fps, quality)
            for a_, b_, text, spoken in getattr(sc_, "subtitles", []):
                cps = len(text) / max(0.1, b_ - a_)
                issue = "too fast to read" if cps > 20 else ("shorter than its voice" if spoken and spoken > b_ - a_
                                                              else "")
                subs.append({"scene": scene["id"], "t": round(t_off + a_, 2), "seconds": round(b_ - a_, 2),
                             "cps": round(cps, 1), "spoken": round(spoken, 2) if spoken else None, "issue": issue})
        t_off += st[2]
    report["subtitles"] = {"count": len(subs), "issues": [x for x in subs if x["issue"]],
                           "max_cps": max([x["cps"] for x in subs] or [0])}
    report["files"] = {"master": str(out), "android": str(android)}
    return report


def _code_version() -> str:
    """Scenes re-render when the engine changes (a hash of the animation package's source)."""
    h = hashlib.sha256()
    for f in sorted(Path(__file__).parent.glob("*.py")):
        h.update(f.read_bytes())
    return h.hexdigest()[:12]
