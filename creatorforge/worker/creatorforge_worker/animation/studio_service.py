"""The animation editor as a service: production documents on disk, edited through whitelisted Editor operations
(with undo/redo that survives a restart), saved versions, background renders and the asset library.

    store = AnimationStore(root)
    doc_id = store.create(doc)
    store.apply(doc_id, "update_step", {"sid": "s1", "index": 0, "to": 2.0})
    store.undo(doc_id); store.redo(doc_id)
    store.render(doc_id, "preview")      -> starts a background render; store.status(doc_id) reports it

Every write is validated by staging the document (plan_states) before it is kept, so a broken edit is refused with
the reason instead of failing later at render time."""
from __future__ import annotations

import json
import re
import threading
import traceback
import uuid
from pathlib import Path

from . import asset_lib
from .production import Editor, plan_states, render

OPS = {"add_scene", "move_scene", "delete_scene", "insert_step", "update_step", "delete_step", "set_pose",
       "set_expression", "shift_lipsync", "set_camera", "set_layer", "set_cast", "replace_asset"}
ID = re.compile(r"^[a-f0-9]{12}$")


class AnimationStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self.assets = asset_lib.Library(self.root / "assets")
        for k in asset_lib.Library.STOCK:
            if k not in self.assets.items:
                self.assets.items[k] = asset_lib.Library.default().get(k)

    def _dir(self, doc_id: str) -> Path:
        if not ID.match(doc_id or ""):
            raise KeyError(doc_id)
        d = self.root / doc_id
        if not (d / "doc.json").exists():
            raise KeyError(doc_id)
        return d

    def _editor(self, doc_id: str) -> Editor:
        d = self._dir(doc_id)
        ed = Editor(json.loads((d / "doc.json").read_text()), d / "versions")
        stacks = json.loads((d / "stacks.json").read_text()) if (d / "stacks.json").exists() else {}
        ed._undo = [tuple(x) for x in stacks.get("undo", [])]
        ed._redo = [tuple(x) for x in stacks.get("redo", [])]
        return ed

    def _save(self, doc_id: str, ed: Editor) -> None:
        d = self.root / doc_id
        (d / "doc.json").write_text(json.dumps(ed.doc, indent=1))
        (d / "stacks.json").write_text(json.dumps({"undo": ed._undo[-50:], "redo": ed._redo[-50:]}))

    @staticmethod
    def check(doc: dict) -> dict:
        """Stages the whole document; returns per-scene QC and continuity, or raises ValueError with the reason."""
        if not isinstance(doc, dict) or not isinstance(doc.get("scenes"), list):
            raise ValueError("a production needs a list of scenes")
        try:
            states = plan_states(doc)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError, StopIteration) as e:
            raise ValueError(f"the document does not stage: {type(e).__name__}: {e}") from None
        return {"scenes": [{"id": s["id"], "seconds": round(st[2], 2), "qc": st[3].summary(),
                            "continuity": [i.__dict__ for i in st[4]]} for s, st in zip(doc["scenes"], states)]}

    def create(self, doc: dict) -> dict:
        report = self.check(doc)
        doc_id = uuid.uuid4().hex[:12]
        d = self.root / doc_id
        d.mkdir()
        self._save(doc_id, Editor(doc))
        return {"id": doc_id, "doc": doc, "check": report}

    def list(self) -> list[dict]:
        out = []
        for d in sorted(self.root.iterdir()):
            if (d / "doc.json").exists():
                doc = json.loads((d / "doc.json").read_text())
                out.append({"id": d.name, "title": doc.get("title", ""), "scenes": len(doc.get("scenes", []))})
        return out

    def get(self, doc_id: str) -> dict:
        ed = self._editor(doc_id)
        return {"id": doc_id, "doc": ed.doc, "history": ed.history(), "can_redo": bool(ed._redo),
                "render": self._jobs.get(doc_id, {})}

    def apply(self, doc_id: str, op: str, args: dict) -> dict:
        if op not in OPS:
            raise ValueError(f"unknown operation {op!r}; allowed: {', '.join(sorted(OPS))}")
        with self._lock:
            ed = self._editor(doc_id)
            args = dict(args)
            try:
                getattr(ed, op)(**args)
            except (KeyError, IndexError, StopIteration, TypeError, ValueError) as e:
                raise ValueError(f"{op} failed: {type(e).__name__}: {e}") from None
            report = self.check(ed.doc)                 # refuse an edit that breaks the film
            self._save(doc_id, ed)
        return {**self.get(doc_id), "check": report}

    def undo(self, doc_id: str) -> dict:
        with self._lock:
            ed = self._editor(doc_id)
            label = ed.undo()
            self._save(doc_id, ed)
        return {**self.get(doc_id), "undone": label}

    def redo(self, doc_id: str) -> dict:
        with self._lock:
            ed = self._editor(doc_id)
            label = ed.redo()
            self._save(doc_id, ed)
        return {**self.get(doc_id), "redone": label}

    def save_version(self, doc_id: str, message: str) -> dict:
        ed = self._editor(doc_id)
        return {"version": ed.save_version(message[:200] or "saved"), "versions": ed.versions()}

    def versions(self, doc_id: str) -> list[dict]:
        return self._editor(doc_id).versions()

    def restore(self, doc_id: str, vid: str) -> dict:
        if not re.match(r"^[\w-]{8,40}$", vid):
            raise ValueError("bad version id")
        with self._lock:
            ed = self._editor(doc_id)
            try:
                ed.restore(vid)
            except FileNotFoundError:
                raise KeyError(vid) from None
            self._save(doc_id, ed)
        return self.get(doc_id)

    # ---- rendering ----
    def render(self, doc_id: str, quality: str = "preview") -> dict:
        if quality not in ("preview", "final"):
            raise ValueError("quality is preview or final")
        d = self._dir(doc_id)
        job = self._jobs.get(doc_id)
        if job and job.get("state") == "running":
            return job
        doc = json.loads((d / "doc.json").read_text())
        job = {"state": "running", "quality": quality}
        self._jobs[doc_id] = job

        def run():
            try:
                rep = render(doc, d / f"{quality}.mp4", quality, cache_dir=self.root / "scene_cache")
                job.update(state="done", report={k: v for k, v in rep.items() if k != "files"})
            except Exception as e:                     # reported to the client, never swallowed
                job.update(state="failed", error=f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-2000:])
        threading.Thread(target=run, daemon=True, name=f"anim-{doc_id}").start()
        return job

    def status(self, doc_id: str) -> dict:
        self._dir(doc_id)
        return self._jobs.get(doc_id, {"state": "idle"})

    def file(self, doc_id: str, name: str) -> Path:
        if name not in ("preview.mp4", "final.mp4", "preview_android.mp4", "final_android.mp4"):
            raise KeyError(name)
        p = self._dir(doc_id) / name
        if not p.is_file():
            raise KeyError(name)
        return p

    # ---- assets ----
    def asset_list(self, kind: str | None = None, use: str | None = None) -> list[dict]:
        return [{"id": a["id"], "kind": a["kind"], "name": a["name"], "w": a["w"], "h": a["h"],
                 "uses": a.get("uses", []), "source": a.get("source", ""), "warnings": a.get("warnings", [])}
                for a in self.assets.find(kind, use)]

    def asset_generate(self, description: str) -> dict:
        aid, how = self.assets.obtain(description[:120])
        a = self.assets.get(aid)
        return {"id": aid, "how": how, "kind": a["kind"], "w": a["w"], "h": a["h"],
                "compatible": {u: asset_lib.compatible(a, u)[0] for u in ("carry", "sit", "stand_on", "ride", "walk", "3d")},
                "warnings": a.get("warnings", [])}

    def asset_thumbnail(self, aid: str) -> Path:
        a = self.assets.get(aid)
        thumbs = self.root / "assets" / "thumbs"
        thumbs.mkdir(parents=True, exist_ok=True)
        p = thumbs / f"{re.sub(r'[^\w-]', '_', aid)}.png"
        if not p.exists():
            asset_lib.render_png(a, p, 256)
        return p
