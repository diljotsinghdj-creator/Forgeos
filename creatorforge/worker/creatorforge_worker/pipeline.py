"""ONE-BUTTON PRODUCTION: idea -> director plan -> PromptForge -> images -> narration ->
captions -> music -> assembly (transitions, overlays) -> render -> verify.

Every stage persists its output, so a crash, cancel or failure resumes from the first
unfinished stage instead of regenerating finished assets. Nothing reports success unless
the stage's output was verified."""
from __future__ import annotations

import hashlib
import json
import shutil
import threading
from pathlib import Path

from . import director, providers
from .config import Config
from .media import captions as cap
from .media import render, verify
from .media.ff import Cancelled, MediaError
from .providers.base import ProviderError, Word
from .store import STAGES, JobStore
from .templates import ASPECTS, TEMPLATES

SCENE_GAP_S = 0.35
MIN_SCENE_S = 2.0


class StageFailed(Exception):
    pass


def _key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:32]


class Pipeline:
    def __init__(self, cfg: Config, store: JobStore):
        self.cfg = cfg
        self.store = store

    # -- helpers ---------------------------------------------------------------------------
    def _cached(self, kind: str, key: str, suffix: str, make, check) -> Path:
        """Content-addressed cache: identical requests never regenerate expensive assets."""
        d = self.cfg.cache_dir / kind
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{key}{suffix}"
        if path.is_file():
            try:
                check(path)
                return path
            except MediaError:
                path.unlink()
        tmp = d / f"{key}.partial{suffix}"
        try:
            make(tmp)
            check(tmp)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
        tmp.replace(path)
        return path

    def _stage(self, job: dict, name: str, state: str, **extra) -> None:
        job["stages"][name].update(state=state, **extra)
        if state == "RUNNING":
            job["message"] = {"director": "AI Director writing script and shot list",
                              "prompts": "PromptForge building generation prompts",
                              "images": "Generating scene visuals", "narration": "Recording narration",
                              "captions": "Synchronizing captions", "music": "Scoring music",
                              "assembly": "Assembling timeline, transitions and overlays",
                              "verify": "Verifying the exported MP4"}[name]
        self.store.save(job)

    # -- run -------------------------------------------------------------------------------
    def run(self, job_id: str, cancel: threading.Event) -> None:
        job = self.store.load(job_id)
        job.update(status="RUNNING", error=None)
        self.store.save(job)
        try:
            for name in STAGES:
                if job["stages"][name]["state"] in ("READY", "SKIPPED"):
                    continue
                if cancel.is_set():
                    raise Cancelled()
                self._stage(job, name, "RUNNING", error=None)
                try:
                    getattr(self, f"_{name}")(job, cancel)
                except (ProviderError, MediaError, StageFailed, ValueError, OSError) as e:
                    self._stage(job, name, "FAILED", error=str(e))
                    raise StageFailed(f"{name}: {e}") from e
                if job["stages"][name]["state"] == "RUNNING":
                    self._stage(job, name, "READY")
            job.update(status="READY", message="Finished: verified MP4 ready")
        except Cancelled:
            for s in job["stages"].values():
                if s["state"] == "RUNNING":
                    s["state"] = "PENDING"
            for sc in job["scenes"]:
                for k in ("image_state", "voice_state"):
                    if sc.get(k) == "GENERATING":
                        sc[k] = "QUEUED"
            job.update(status="CANCELLED", message="Cancelled - finished assets are kept; retry resumes")
        except StageFailed as e:
            job.update(status="FAILED", error=str(e), message=f"Failed at {str(e).split(':')[0]} - retry resumes here")
        except Exception as e:  # noqa: BLE001 - never leave a job stuck in RUNNING
            job.update(status="FAILED", error=f"internal error: {e}", message="Failed")
        self.store.save(job)

    # -- stages ----------------------------------------------------------------------------
    def _spec(self, job: dict) -> director.ProductionSpec:
        return director.ProductionSpec.from_dict(job["spec"])

    def _director(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        llm = providers.build_llm(self.cfg)
        job["providers"]["llm"] = llm.id
        plan = director.direct(llm, spec)
        job["plan"] = plan.to_dict()
        job["scenes"] = [{"index": i, "image_state": "PLANNED", "voice_state": "PLANNED", "image": None,
                          "narration": None, "narration_s": None, "error": None}
                         for i in range(len(plan.scenes))]

    def _prompts(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        plan = director.ProductionPlan.from_dict(job["plan"])
        director.prompt_forge(plan, spec)
        job["plan"] = plan.to_dict()
        for sc in job["scenes"]:
            if sc["image_state"] == "PLANNED":
                sc["image_state"] = "QUEUED"
            if sc["voice_state"] == "PLANNED":
                sc["voice_state"] = "QUEUED"

    def _images(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        gen, _ = ASPECTS[spec.aspect]
        img = providers.build_image(self.cfg)
        job["providers"]["image"] = img.id
        jdir = self.store.dir(job["id"])
        seed_base = int(job["id"][:8], 16)
        scenes, shots = job["scenes"], job["plan"]["scenes"]
        failures = []
        for sc, shot in zip(scenes, shots):
            done = sum(1 for s in scenes if s["image_state"] == "READY")
            self._stage(job, "images", "RUNNING", done=done, total=len(scenes))
            if sc["image_state"] == "READY" and sc["image"] and (jdir / sc["image"]).is_file():
                continue
            if cancel.is_set():
                raise Cancelled()
            sc.update(image_state="GENERATING", error=None)
            self.store.save(job)
            seed = (seed_base + sc["index"] * 7919) % 2**31
            key = _key(img.id, shot["prompt"], shot["negative"], gen, seed)
            try:
                src = self._cached("images", key, ".png",
                                   lambda p: img.generate(shot["prompt"], shot["negative"], gen[0], gen[1], seed, p),
                                   verify.image)
                dst = jdir / f"scene_{sc['index'] + 1:02d}.png"
                shutil.copyfile(src, dst)
                sc.update(image_state="READY", image=dst.name)
            except (ProviderError, MediaError) as e:
                sc.update(image_state="FAILED", error=f"image: {e}")
                failures.append(f"scene {sc['index'] + 1}: {e}")
            self.store.save(job)
        self._stage(job, "images", "RUNNING", done=sum(1 for s in scenes if s["image_state"] == "READY"))
        if failures:
            raise StageFailed(f"{len(failures)} scene image(s) failed - {failures[0]}")

    def _narration(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        profile = providers.voice_profile(self.cfg, spec.voice)
        voice = providers.build_voice(self.cfg, profile)
        job["providers"]["voice"] = f"{profile.id} ({voice.id})"
        jdir = self.store.dir(job["id"])
        scenes, shots = job["scenes"], job["plan"]["scenes"]
        for sc, shot in zip(scenes, shots):
            self._stage(job, "narration", "RUNNING", done=sum(1 for s in scenes if s["voice_state"] == "READY"),
                        total=len(scenes))
            if sc["voice_state"] == "READY" and sc["narration"] and (jdir / sc["narration"]).is_file():
                continue
            if cancel.is_set():
                raise Cancelled()
            sc.update(voice_state="GENERATING")
            self.store.save(job)
            key = _key(voice.id, profile.speed, shot["narration"])
            try:
                src = self._cached("voice", key, ".wav", lambda p: voice.synthesize(shot["narration"], p), verify.wav)
                dst = jdir / f"scene_{sc['index'] + 1:02d}.wav"
                render.to_pcm(src, dst, cancel)
                sc.update(voice_state="READY", narration=dst.name, narration_s=round(verify.wav(dst), 3))
            except (ProviderError, MediaError) as e:
                sc.update(voice_state="FAILED", error=f"narration: {e}")
                self.store.save(job)
                raise StageFailed(f"scene {sc['index'] + 1} narration failed - {e}") from e
            self.store.save(job)

    def _timings(self, job: dict) -> list[float]:
        return [max(MIN_SCENE_S, sc["narration_s"] + SCENE_GAP_S) for sc in job["scenes"]]

    def _captions(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        if not spec.captions:
            job["providers"]["captions"] = "off"
            self._stage(job, "captions", "SKIPPED")
            return
        asr = providers.build_asr(self.cfg)
        jdir = self.store.dir(job["id"])
        words: list[Word] = []
        start = 0.0
        for sc, shot, slot in zip(job["scenes"], job["plan"]["scenes"], self._timings(job)):
            if cancel.is_set():
                raise Cancelled()
            if asr is not None:
                ws = asr.words(jdir / sc["narration"])
                if not ws:
                    raise StageFailed(f"Whisper heard no words in scene {sc['index'] + 1}")
                words += [Word(w.text, start + w.start, start + w.end) for w in ws]
            else:
                words += cap.estimate_words(shot["narration"], start, sc["narration_s"])
            start += slot
        job["providers"]["captions"] = asr.id if asr else "estimated (Whisper not configured)"
        (jdir / "words.json").write_text(json.dumps([w.__dict__ for w in words]))

    def _music(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        if not spec.music:
            job["providers"]["music"] = "off"
            self._stage(job, "music", "SKIPPED")
            return
        mood = job["plan"].get("music_mood") or TEMPLATES[spec.template].music_mood
        track = render.pick_music(self.cfg.music_dir, mood, job["id"])
        job["providers"]["music"] = track.name if track else "none (no music library configured)"
        job["music_track"] = str(track) if track else None

    def _assembly(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        t = TEMPLATES[spec.template]
        _, (w, h) = ASPECTS[spec.aspect]
        jdir = self.store.dir(job["id"])
        work = jdir / "work"
        work.mkdir(exist_ok=True)
        timings = self._timings(job)
        shots = job["plan"]["scenes"]
        tail = render.TRANSITION_S if len(timings) > 1 else 0.0
        total = sum(timings) + tail

        narr = work / "narration.wav"
        render.narration_track([jdir / sc["narration"] for sc in job["scenes"]], timings, tail, narr)
        music = Path(job["music_track"]) if job.get("music_track") else None
        if music is not None and not music.is_file():
            raise StageFailed(f"music track disappeared: {music}")
        mixed = work / "audio.wav"
        render.mix_audio(narr, music, total, mixed, cancel)

        ass = None
        if spec.captions:
            words = [Word(**d) for d in json.loads((jdir / "words.json").read_text())]
            cues = cap.group(words, t.words_per_caption)
            overlays, start = [], 0.0
            plan = job["plan"]
            if plan.get("hook"):
                overlays.append(cap.Overlay(0.0, min(3.0, timings[0]), plan["hook"], "Hook"))
            for i, (shot, slot) in enumerate(zip(shots, timings)):
                if shot.get("overlay") and i > 0:
                    overlays.append(cap.Overlay(start + 0.3, start + slot - 0.2, shot["overlay"], "Callout"))
                start += slot
            if plan.get("cta"):
                overlays.append(cap.Overlay(max(0.0, total - 3.0), total, plan["cta"], "CTA"))
            ass = work / "captions.ass"
            cap.write_ass(ass, w, h, t.caption_scale, t.caption_position, cues, overlays)

        clips = [render.Clip(jdir / sc["image"], d, shot.get("camera", ""), t.transitions[i % len(t.transitions)])
                 for i, (sc, shot, d) in enumerate(zip(job["scenes"], shots, timings))]
        out = jdir / "work" / "render.mp4"
        expected = render.render_video(clips, mixed, ass, w, h, out, work, cancel)
        job["render"] = {"file": "work/render.mp4", "expected_s": round(expected, 3), "width": w, "height": h}

    def _verify(self, job: dict, cancel) -> None:
        jdir = self.store.dir(job["id"])
        r = job.get("render") or {}
        src = jdir / r.get("file", "work/render.mp4")
        report = verify.mp4(src, r["width"], r["height"], r["expected_s"])
        final = jdir / "creatorforge.mp4"
        src.replace(final)
        job["result"] = {"file": final.name, "verification": report, "title": job["plan"]["title"]}
