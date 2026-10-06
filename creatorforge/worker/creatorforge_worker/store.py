"""Durable production records: one directory per production with an atomically written job.json."""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path

STAGES = ["director", "prompts", "images", "review", "narration", "clips", "captions", "music", "assembly", "verify"]
WEIGHTS = {"director": .08, "prompts": .02, "images": .30, "review": 0.0, "narration": .15, "clips": .20,
           "captions": .04, "music": .02, "assembly": .15, "verify": .04}
TERMINAL = {"READY", "FAILED", "CANCELLED"}


class JobStore:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def dir(self, job_id: str) -> Path:
        if not job_id.replace("-", "").isalnum():
            raise KeyError(job_id)
        return self.root / job_id

    def create(self, spec: dict) -> dict:
        job_id = uuid.uuid4().hex[:16]
        now = time.time()
        job = {"id": job_id, "created_at": now, "updated_at": now, "status": "QUEUED", "message": "Queued",
               "error": None, "progress": 0.0, "spec": spec, "plan": None, "scenes": [],
               "stages": {s: {"state": "PENDING", "error": None} for s in STAGES},
               "providers": {}, "result": None}
        self.dir(job_id).mkdir(parents=True)
        self.save(job)
        return job

    def load(self, job_id: str) -> dict:
        with self._lock:
            p = self.dir(job_id) / "job.json"
            if not p.is_file():
                raise KeyError(job_id)
            job = json.loads(p.read_text())
            for s in STAGES:  # productions created before a stage existed simply skip it
                job["stages"].setdefault(s, {"state": "SKIPPED", "error": None})
            return job

    def save(self, job: dict) -> None:
        with self._lock:
            job["updated_at"] = time.time()
            job["progress"] = round(progress(job), 4)
            p = self.dir(job["id"]) / "job.json"
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps(job, indent=1))
            os.replace(tmp, p)

    def all(self) -> list[dict]:
        out = []
        for d in self.root.iterdir():
            if (d / "job.json").is_file():
                try:
                    out.append(self.load(d.name))
                except (KeyError, ValueError):
                    continue
        return sorted(out, key=lambda j: j["created_at"], reverse=True)


def progress(job: dict) -> float:
    if job["status"] == "READY":
        return 1.0
    total = 0.0
    for s in STAGES:
        st = job["stages"][s]
        if st["state"] in ("READY", "SKIPPED"):
            total += WEIGHTS[s]
        elif st["state"] == "RUNNING" and st.get("total"):
            total += WEIGHTS[s] * st.get("done", 0) / st["total"]
    return min(total, 0.99)
