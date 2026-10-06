"""Generation queue: runs productions one at a time (GPU-friendly), supports cancel,
retry and resume after a worker restart."""
from __future__ import annotations

import threading
from collections import deque

from . import director
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
        sc.update(image_state="QUEUED", image=None, clip_state="QUEUED", clip=None, error=None,
                  reroll=sc.get("reroll", 0) + 1)
        job["plan"]["scenes"][index]["prompt"] += f" (variation {sc['reroll']})"
        self._reset(job, "images", "clips", "assembly", "verify")
        job.update(status="QUEUED", message=f"Regenerating scene {index + 1}", result=None)
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
            sc.update(voice_state="QUEUED", narration=None, narration_s=None, clip_state="QUEUED", clip=None)
            self._reset(job, "narration", "clips", "captions", "assembly", "verify")
            changed = True
        if visual is not None and visual.strip() and visual.strip() != shot["visual"]:
            shot["visual"] = visual.strip()[:1000]
            plan = director.ProductionPlan.from_dict(job["plan"])
            director.prompt_forge(plan, director.ProductionSpec.from_dict(job["spec"]), only=index)
            job["plan"] = plan.to_dict()
            sc.update(image_state="QUEUED", image=None, clip_state="QUEUED", clip=None)
            self._reset(job, "images", "clips", "assembly", "verify")
            changed = True
        if changed:
            sc["error"] = None
            job.update(status="REVIEW", result=None, message=f"Scene {index + 1} edited - approve to render")
            self.store.save(job)
        return job

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
