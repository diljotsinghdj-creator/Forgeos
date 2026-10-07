"""Generation queue: runs productions one at a time (GPU-friendly), supports cancel,
retry and resume after a worker restart."""
from __future__ import annotations

import threading
from collections import deque

import shutil
import uuid
from pathlib import Path

from . import director
from .media import ff, render, verify
from .pipeline import Pipeline
from .store import STAGES, TERMINAL, JobStore


class Runner:
    def __init__(self, pipeline: Pipeline, store: JobStore):
        self.pipeline = pipeline
        self.store = store
        self._queue: deque[str] = deque()
        self._cancel: dict[str, threading.Event] = {}
        self._cv = threading.Condition()
        self._current: str | None = None
        self._thread = threading.Thread(target=self._loop, name="creatorforge-runner", daemon=True)

    def start(self) -> None:
        # Resume anything interrupted by a worker restart.
        for job in reversed(self.store.all()):
            if job["status"] in ("QUEUED", "RUNNING"):
                for s in job["stages"].values():
                    if s["state"] == "RUNNING":
                        s["state"] = "PENDING"
                job.update(status="QUEUED", message="Resuming after worker restart")
                self.store.save(job)
                self._queue.append(job["id"])
        self._thread.start()

    def submit(self, job_id: str) -> None:
        with self._cv:
            if job_id not in self._queue and job_id != self._current:
                self._queue.append(job_id)
            self._cv.notify()

    def cancel(self, job_id: str) -> dict:
        with self._cv:
            job = self.store.load(job_id)
            if job["status"] in TERMINAL:
                return job
            if job["status"] == "REVIEW":
                job.update(status="CANCELLED", message="Cancelled during storyboard review")
                self.store.save(job)
                return job
            if job_id in self._queue:
                self._queue.remove(job_id)
                job.update(status="CANCELLED", message="Cancelled before start")
                self.store.save(job)
                return job
            ev = self._cancel.get(job_id)
            if ev:
                ev.set()
            job["message"] = "Cancelling..."
            return job

    def retry(self, job_id: str, from_stage: str | None = None) -> dict:
        job = self.store.load(job_id)
        if job["status"] in ("QUEUED", "RUNNING"):
            return job
        reset = False
        for s in STAGES:
            st = job["stages"][s]
            if s == from_stage:
                reset = True
            if reset or st["state"] in ("FAILED", "PENDING", "RUNNING"):
                reset = True
                st.update(state="PENDING", error=None)
        for sc in job["scenes"]:
            for k in ("image_state", "voice_state", "clip_state"):
                if sc.get(k) in ("FAILED", "GENERATING"):
                    sc[k] = "QUEUED"
        job.update(status="QUEUED", error=None, message="Queued for retry", result=None)
        self.store.save(job)
        self.submit(job_id)
        return job

    def regenerate_scene(self, job_id: str, index: int) -> dict:
        """Regenerates one scene's visual without touching the rest of the production."""
        job = self.store.load(job_id)
        if job["status"] in ("QUEUED", "RUNNING"):
            raise ValueError("production is busy")
        if not 0 <= index < len(job["scenes"]):
            raise ValueError("no such scene")
        sc = job["scenes"][index]
        sc.update(image_state="QUEUED", error=None, reroll=sc.get("reroll", 0) + 1)
        if sc.get("clip_source") != "asset":
            sc["clip_state"] = "QUEUED"
        job["plan"]["scenes"][index]["prompt"] += f" (variation {sc['reroll']})"
        self._reset(job, "images", "clips", "assembly", "verify")
        job.update(status="QUEUED", message=f"Regenerating scene {index + 1}", result=None)
        self.store.save(job)
        self.submit(job_id)
        return job

    def redraw_scenes(self, job_id: str, indices: list[int]) -> dict:
        """Swipe Storyboard: new visuals for the rejected scenes, then pause for review again."""
        job = self.store.load(job_id)
        if job["status"] in ("QUEUED", "RUNNING"):
            raise ValueError("production is busy")
        if not job.get("plan"):
            raise ValueError("production has no storyboard yet")
        picked = sorted({int(i) for i in indices})
        if not picked or not all(0 <= i < len(job["scenes"]) for i in picked):
            raise ValueError("pick at least one existing scene")
        for i in picked:
            sc = job["scenes"][i]
            sc.update(image_state="QUEUED", error=None, reroll=sc.get("reroll", 0) + 1, image_source="generated")
            if sc.get("clip_source") != "asset":
                sc["clip_state"] = "QUEUED"
            job["plan"]["scenes"][i]["prompt"] += f" (variation {sc['reroll']})"
        self._reset(job, "images", "review", "clips", "assembly", "verify")
        job["approved"] = not job["spec"].get("review", False)  # review-mode productions stop at the storyboard again
        job.update(status="QUEUED", message=f"Redrawing {len(picked)} scene(s)", result=None)
        self.store.save(job)
        self.submit(job_id)
        return job

    @staticmethod
    def _reset(job: dict, *stages: str) -> None:
        for s in stages:
            if job["stages"][s]["state"] != "SKIPPED" or s in ("assembly", "verify"):
                job["stages"][s].update(state="PENDING", error=None)

    def edit_scene(self, job_id: str, index: int, narration: str | None, visual: str | None) -> dict:
        """Storyboard editing: changes one scene and invalidates only the assets that depend on it."""
        job = self.store.load(job_id)
        if job["status"] in ("QUEUED", "RUNNING"):
            raise ValueError("production is busy")
        if not job.get("plan") or not 0 <= index < len(job["scenes"]):
            raise ValueError("no such scene")
        shot, sc = job["plan"]["scenes"][index], job["scenes"][index]
        changed = False
        if narration is not None and narration.strip() and narration.strip() != shot["narration"]:
            shot["narration"] = narration.strip()[:1000]
            sc.update(voice_state="QUEUED", voice_source="generated")
            if sc.get("clip_source") != "asset":
                sc["clip_state"] = "QUEUED"
            self._reset(job, "narration", "clips", "captions", "assembly", "verify")
            changed = True
        if visual is not None and visual.strip() and visual.strip() != shot["visual"]:
            shot["visual"] = visual.strip()[:1000]
            plan = director.ProductionPlan.from_dict(job["plan"])
            director.prompt_forge(plan, director.ProductionSpec.from_dict(job["spec"]), only=index)
            job["plan"] = plan.to_dict()
            sc.update(image_state="QUEUED", clip_state="QUEUED", clip_source="generated")
            self._reset(job, "images", "clips", "assembly", "verify")
            changed = True
        if changed:
            sc["error"] = None
            job.update(status="REVIEW", result=None, message=f"Scene {index + 1} edited - approve to render")
            self.store.save(job)
        return job

    def use_asset(self, job_id: str, index: int, asset_path: Path, kind: str, name: str) -> dict:
        """Puts an imported image, clip or voice-over into one scene; nothing else is regenerated."""
        job = self.store.load(job_id)
        if job["status"] in ("QUEUED", "RUNNING"):
            raise ValueError("production is busy")
        if not job.get("plan") or not 0 <= index < len(job["scenes"]):
            raise ValueError("no such scene")
        jdir = self.store.dir(job_id)
        sc = job["scenes"][index]
        tag = uuid.uuid4().hex[:8]
        ai_video = job["spec"].get("motion") == "ai_video"
        if kind == "image":
            dst = jdir / f"scene_{index + 1:02d}_asset_{tag}{asset_path.suffix.lower()}"
            shutil.copyfile(asset_path, dst)
            self._drop(jdir, sc.get("image"))
            sc.update(image=dst.name, image_state="READY", image_source="asset")
            if sc.get("clip_source") == "asset":
                self._drop(jdir, sc.get("clip"))
                sc.update(clip=None, clip_source="generated")
            sc["clip_state"] = "QUEUED"
            self._reset(job, "clips", "assembly", "verify")
        elif kind == "video":
            clip = jdir / f"scene_{index + 1:02d}_asset_{tag}.mp4"
            ff.run(["-i", str(asset_path), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip)])
            still = jdir / f"scene_{index + 1:02d}_asset_{tag}.png"
            ff.run(["-i", str(clip), "-frames:v", "1", str(still)])
            self._drop(jdir, sc.get("clip"))
            self._drop(jdir, sc.get("image"))
            sc.update(clip=clip.name, clip_state="READY", clip_source="asset", image=still.name,
                      image_state="READY", image_source="asset")
            self._reset(job, "assembly", "verify")
        elif kind == "audio":
            wav = jdir / f"scene_{index + 1:02d}_asset_{tag}.wav"
            render.to_pcm(asset_path, wav)
            self._drop(jdir, sc.get("narration"))
            sc.update(narration=wav.name, narration_s=round(verify.wav(wav), 3), voice_state="READY", voice_source="asset")
            if ai_video and sc.get("clip_source") != "asset":
                sc["clip_state"] = "QUEUED"
            self._reset(job, "clips", "captions", "assembly", "verify")
        else:
            raise ValueError(f"a {kind} asset can't be placed in a scene (use image, video or audio)")
        sc["error"] = None
        job.update(status="REVIEW", result=None, message=f"Scene {index + 1} now uses '{name}' - approve to render")
        self.store.save(job)
        return job

    @staticmethod
    def _drop(jdir: Path, name: str | None) -> None:
        if name:
            (jdir / name).unlink(missing_ok=True)

    def edit_timeline(self, job_id: str, body: dict) -> dict:
        """Timeline editor: reorder or remove scenes, set scene lengths and transitions, edit the
        hook, callouts and CTA. Only timing-dependent work (captions, render) is redone."""
        job = self.store.load(job_id)
        if job["status"] in ("QUEUED", "RUNNING"):
            raise ValueError("production is busy")
        if not job.get("plan") or not job["scenes"] or any(sc.get("narration_s") is None for sc in job["scenes"]):
            raise ValueError("the timeline can be edited once narration exists for every scene")
        entries = body.get("scenes")
        if not isinstance(entries, list) or not entries:
            raise ValueError("'scenes' must list at least one scene")
        old_scenes, old_shots = job["scenes"], job["plan"]["scenes"]
        seen: set[int] = set()
        new_scenes, new_shots = [], []
        ai_video = job["spec"].get("motion") == "ai_video"
        retime = False
        for e in entries:
            i = int(e.get("index", -1))
            if not 0 <= i < len(old_scenes) or i in seen:
                raise ValueError(f"invalid or repeated scene index {i}")
            seen.add(i)
            sc, shot = dict(old_scenes[i]), dict(old_shots[i])
            if "duration_s" in e:
                d = e["duration_s"]
                new = None if d in (None, "") else round(min(60.0, max(float(d), sc["narration_s"] + 0.1)), 2)
                if new != sc.get("duration_override"):
                    sc["duration_override"] = new
                    retime = True
                    if ai_video and sc.get("clip_source") != "asset":
                        sc["clip_state"] = "QUEUED"
            if e.get("transition"):
                if e["transition"] not in render.TRANSITIONS:
                    raise ValueError(f"unknown transition '{e['transition']}'")
                shot.update(transition=e["transition"], transition_locked=True)
            if "overlay" in e:
                shot["overlay"] = str(e["overlay"] or "").strip()[:60]
            new_scenes.append(sc)
            new_shots.append(shot)
        if [int(e["index"]) for e in entries] != list(range(len(old_scenes))):
            retime = True
        jdir = self.store.dir(job_id)
        for i, sc in enumerate(old_scenes):
            if i not in seen:
                for k in ("image", "narration", "clip"):
                    self._drop(jdir, sc.get(k))
        for n, sc in enumerate(new_scenes):
            sc["index"] = n
        job["scenes"], job["plan"]["scenes"] = new_scenes, new_shots
        for k in ("hook", "cta"):
            if k in body:
                job["plan"][k] = str(body[k] or "").strip()[:80]
        self._reset(job, *(["clips", "captions"] if retime else []), "assembly", "verify")
        job.update(status="REVIEW", result=None, message="Timeline edited - approve to render")
        self.store.save(job)
        return job

    def rename(self, job_id: str, title: str) -> dict:
        job = self.store.load(job_id)
        title = title.strip()[:100]
        if not title:
            raise ValueError("title can't be empty")
        job["title"] = title
        self.store.save(job)
        return job

    def purge(self, job_id: str) -> None:
        with self._cv:
            job = self.store.load(job_id)
            if job["status"] in ("QUEUED", "RUNNING") or job_id == self._current:
                raise ValueError("cancel the production before deleting it")
            shutil.rmtree(self.store.dir(job_id))

    def approve(self, job_id: str) -> dict:
        job = self.store.load(job_id)
        if job["status"] in ("QUEUED", "RUNNING"):
            return job
        job["approved"] = True
        job.update(status="QUEUED", error=None, message="Approved - rendering", result=None)
        self.store.save(job)
        self.submit(job_id)
        return job

    def _loop(self) -> None:
        while True:
            with self._cv:
                while not self._queue:
                    self._cv.wait()
                job_id = self._queue.popleft()
                self._current = job_id
                ev = self._cancel[job_id] = threading.Event()
            try:
                self.pipeline.run(job_id, ev)
            finally:
                with self._cv:
                    self._cancel.pop(job_id, None)
                    self._current = None
