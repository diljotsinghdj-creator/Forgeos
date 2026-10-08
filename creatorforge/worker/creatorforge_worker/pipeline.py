"""ONE-BUTTON PRODUCTION: idea -> director plan -> PromptForge -> images -> narration ->
captions -> music -> assembly (transitions, overlays) -> render -> verify.

Every stage persists its output, so a crash, cancel or failure resumes from the first
unfinished stage instead of regenerating finished assets. Nothing reports success unless
the stage's output was verified."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import threading
from pathlib import Path

from . import director, providers
from .config import Config, VoiceProfile
from .library import Library
from .media import captions as cap
from .media import render, sfx, verify
from .media import ff
from .media.ff import Cancelled, MediaError
from .providers.base import NotConfigured, ProviderError, Word
from .store import STAGES, JobStore
from .templates import ASPECTS, TEMPLATES

SCENE_GAP_S = 0.12   # breath between scenes - longer gaps lose viewers
MIN_SCENE_S = 1.5
MAX_HOLD_S = 0.5     # cap on the Director's dramatic pauses


class StageFailed(Exception):
    pass


class ReviewPause(Exception):
    pass


def _key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:32]


def _beat_lengths(texts: list[str], word_starts: list[float], total: float) -> list[float]:
    """Screen time per beat. With Whisper's word timings each cut lands on the first word of its phrase;
    without them, time is shared in proportion to the words."""
    counts = [max(1, len(t.split())) for t in texts]
    n = sum(counts)
    proportional = [total * c / n for c in counts]
    if len(word_starts) < 2:
        return proportional
    cuts, seen = [0.0], 0
    for c in counts[:-1]:
        seen += c
        cuts.append(word_starts[min(len(word_starts) - 1, round(seen * len(word_starts) / n))])
    cuts.append(total)
    lengths = [b - a for a, b in zip(cuts, cuts[1:])]
    # Whisper can merge or drop words; if the timings don't give every beat a visible moment, share evenly.
    return lengths if all(x >= 0.3 for x in lengths) else proportional


class Pipeline:
    def __init__(self, cfg: Config, store: JobStore, library: Library | None = None):
        self.cfg = cfg
        self.store = store
        self.library = library or Library(cfg.data_dir / "library", cfg.allow_mock)

    def library_voices(self) -> list[VoiceProfile]:
        return [VoiceProfile(v["id"], v["name"], v["provider"], v["voice"], v.get("speed", 1.0), v.get("lang", "a"),
                             v.get("style", ""))
                for v in self.library.voices.list()]

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

    @staticmethod
    def _replace_file(jdir: Path, old: str | None, new_name: str, src: Path) -> Path:
        """Scene files carry a content key in their name, so reordering scenes can never make two
        scenes share or overwrite a file."""
        dst = jdir / new_name
        shutil.copyfile(src, dst)
        if old and old != new_name:
            (jdir / old).unlink(missing_ok=True)
        return dst

    def _stage(self, job: dict, name: str, state: str, **extra) -> None:
        job["stages"][name].update(state=state, **extra)
        if state == "RUNNING":
            job["message"] = {"director": "AI Director writing script and shot list",
                              "prompts": "PromptForge building generation prompts",
                              "images": "Generating scene visuals", "review": "Waiting for storyboard approval",
                              "narration": "Recording narration", "clips": "Animating scenes into video clips",
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
        except ReviewPause:
            job.update(status="REVIEW", message="Storyboard ready - edit any scene, then approve to render")
        except Cancelled:
            for s in job["stages"].values():
                if s["state"] == "RUNNING":
                    s["state"] = "PENDING"
            for sc in job["scenes"]:
                for k in ("image_state", "voice_state", "clip_state"):
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
        if spec.script:
            try:
                llm = providers.director_llm(self.cfg, job["id"])
            except NotConfigured:
                llm = None
            plan = director.direct_script(llm, spec)
            job["providers"]["llm"] = f"{llm.id} (script mode)" if llm else "none (script mode: visuals from your words)"
        else:
            llm = providers.director_llm(self.cfg, job["id"])
            plan = director.direct(llm, spec)
            job["providers"]["llm"] = llm.id
        if spec.fast_cuts:
            director.plan_beats(llm, plan, spec)
        job["plan"] = plan.to_dict()
        job["scenes"] = [{"index": i, "image_state": "PLANNED", "voice_state": "PLANNED", "clip_state": "PLANNED",
                          "image": None, "narration": None, "narration_s": None, "clip": None, "error": None}
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
                dst = self._replace_file(jdir, sc.get("image"), f"scene_{sc['index'] + 1:02d}_{key[:8]}.png", src)
                sc.update(image_state="READY", image=dst.name, image_source="generated")
            except (ProviderError, MediaError) as e:
                sc.update(image_state="FAILED", error=f"image: {e}")
                failures.append(f"scene {sc['index'] + 1}: {e}")
            self.store.save(job)
        self._stage(job, "images", "RUNNING", done=sum(1 for s in scenes if s["image_state"] == "READY"))
        self._beat_images(job, img, gen, seed_base, cancel)
        if failures:
            raise StageFailed(f"{len(failures)} scene image(s) failed - {failures[0]}")

    def _beat_images(self, job: dict, img, gen, seed_base: int, cancel) -> None:
        """Fast cuts: one extra picture per beat after the first (beat 1 uses the scene image). A beat image that
        fails is skipped - the scene simply holds its previous picture longer."""
        jdir = self.store.dir(job["id"])
        for sc, shot in zip(job["scenes"], job["plan"]["scenes"]):
            beats = shot.get("beats") or []
            if len(beats) < 2 or sc.get("image_source") == "asset":
                continue
            names = list(sc.get("beat_images") or [])[: len(beats) - 1]
            names += [None] * (len(beats) - 1 - len(names))
            for k, b in enumerate(beats[1:]):
                if names[k] and (jdir / names[k]).is_file():
                    continue
                if cancel.is_set():
                    raise Cancelled()
                seed = (seed_base + sc["index"] * 7919 + (k + 1) * 104729) % 2**31
                key = _key(img.id, b.get("prompt", ""), b.get("negative", ""), gen, seed)
                try:
                    src = self._cached("images", key, ".png",
                                       lambda p, b=b, seed=seed: img.generate(b["prompt"], b["negative"], gen[0], gen[1], seed, p),
                                       verify.image)
                    dst = jdir / f"scene_{sc['index'] + 1:02d}_beat{k + 2}_{key[:8]}.png"
                    if not dst.is_file():
                        shutil.copyfile(src, dst)
                    names[k] = dst.name
                except (ProviderError, MediaError):
                    names[k] = None
                sc["beat_images"] = names
                self.store.save(job)

    def _review(self, job: dict, cancel) -> None:
        if not self._spec(job).review:
            self._stage(job, "review", "SKIPPED")
        elif not job.get("approved"):
            self._stage(job, "review", "WAITING")
            raise ReviewPause()

    def _clips(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        if spec.motion != "ai_video":
            job["providers"]["clips"] = "off (camera motion on stills)"
            self._stage(job, "clips", "SKIPPED")
            return
        video = providers.build_video(self.cfg)
        if hasattr(video, "set_quality"):
            video.set_quality(spec.video_quality or self.cfg.video_quality)
        chosen = self._mark_video_scenes(job)
        job["providers"]["clips"] = f"{video.id} ({len(chosen)}/{len(job['scenes'])} scenes)"
        gen, _ = ASPECTS[spec.aspect]
        jdir = self.store.dir(job["id"])
        scenes, shots = job["scenes"], job["plan"]["scenes"]
        for sc, shot, slot in zip(scenes, shots, self._timings(job)):
            if not sc.get("ai_video"):
                if sc.get("clip_source") != "asset":
                    sc["clip_state"] = "SKIPPED"
                continue
            self._stage(job, "clips", "RUNNING", done=sum(1 for s in scenes if s.get("ai_video") and s.get("clip_state") == "READY"),
                        total=len(chosen))
            if sc.get("clip_state") == "READY" and sc.get("clip") and (jdir / sc["clip"]).is_file():
                continue
            if cancel.is_set():
                raise Cancelled()
            sc.update(clip_state="GENERATING")
            self.store.save(job)
            image = jdir / sc["image"]
            seconds = round(slot + render.TRANSITION_S, 2)
            seed = (int(job["id"][:8], 16) + sc["index"] * 104729) % 2**31
            vprompt = shot.get("video_prompt") or shot["prompt"]
            vneg = shot.get("video_negative") or director.VIDEO_NEGATIVE
            key = _key(video.id, hashlib.sha256(image.read_bytes()).hexdigest(), vprompt, seconds, gen, seed)
            try:
                src = self._cached("clips", key, ".mp4",
                                   lambda p: video.generate(image, vprompt, vneg, seconds, gen[0], gen[1], seed, p),
                                   verify.clip)
                dst = self._replace_file(jdir, sc.get("clip"), f"scene_{sc['index'] + 1:02d}_{key[:8]}.mp4", src)
                sc.update(clip_state="READY", clip=dst.name, clip_source="generated")
            except (ProviderError, MediaError) as e:
                sc.update(clip_state="FAILED", error=f"clip: {e}")
                self.store.save(job)
                raise StageFailed(f"scene {sc['index'] + 1} video clip failed - {e}") from e
            self.store.save(job)

    def _mark_video_scenes(self, job: dict) -> list[int]:
        """Decides once which scenes get AI video (saved per scene, so timeline edits keep the choice)."""
        scenes = job["scenes"]
        if not any("ai_video" in sc for sc in scenes):
            sel = self._spec(job).ai_video_scenes
            wanted = (set(range(len(scenes))) if sel == "all" else {0} if sel == "hook"
                      else {n - 1 for n in sel if 1 <= n <= len(scenes)})
            for i, sc in enumerate(scenes):
                sc["ai_video"] = i in wanted
        return [i for i, sc in enumerate(scenes) if sc.get("ai_video")]

    def _narration(self, job: dict, cancel) -> None:
        spec = self._spec(job)
        profile = providers.voice_profile(self.cfg, spec.voice, self.library_voices())
        voice = providers.build_voice(self.cfg, profile)
        note = ""
        if profile.provider == "chatterbox":
            # The human-like engine installs in the background after a pod start and is the newest part of the
            # pod; if it isn't up or can't speak, use the matching Kokoro voice so the video still finishes.
            problem = "" if providers.chatterbox_ready(self.cfg) else "still installing"
            if not problem and not any(s.get("voice_state") == "READY" for s in job["scenes"]):
                try:
                    with tempfile.TemporaryDirectory() as d:
                        voice.synthesize("Testing.", Path(d) / "probe.wav")
                except Exception as e:  # noqa: BLE001
                    problem = f"failed ({str(e)[:160]})"
            if problem:
                fallback = profile.voice.split(":", 1)[1] if profile.voice.startswith("kokoro:") else "af_heart"
                voice = providers.build_voice(self.cfg, VoiceProfile(profile.id, profile.name, "kokoro", fallback, 1.0,
                                                                     fallback[0] if fallback[:1] in tuple("abefhijpz") else "a"))
                note = f" - human-like engine {problem}; used its standard voice instead"
        job["providers"]["voice"] = f"{profile.id} ({voice.id}){note}"
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
                dst = jdir / f"scene_{sc['index'] + 1:02d}_{key[:8]}.wav"
                if sc.get("narration") and sc["narration"] != dst.name:
                    (jdir / sc["narration"]).unlink(missing_ok=True)
                render.to_pcm(src, dst, cancel)
                sc.update(voice_state="READY", narration=dst.name, narration_s=round(verify.wav(dst), 3))
            except (ProviderError, MediaError) as e:
                sc.update(voice_state="FAILED", error=f"narration: {e}")
                self.store.save(job)
                raise StageFailed(f"scene {sc['index'] + 1} narration failed - {e}") from e
            self.store.save(job)

    def _timings(self, job: dict) -> list[float]:
        auto = self._spec(job).auto_edit
        out = []
        for sc, shot in zip(job["scenes"], job["plan"]["scenes"]):
            natural = max(MIN_SCENE_S, sc["narration_s"] + SCENE_GAP_S + (min(MAX_HOLD_S, shot.get("hold", 0.0)) if auto else 0.0))
            override = sc.get("duration_override")
            # A timeline-edited length wins, but can never cut the narration short.
            out.append(max(float(override), sc["narration_s"] + 0.1) if override else natural)
        return out

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
                sc["word_starts"] = [round(w.start, 3) for w in ws]   # fast cuts land exactly on these
            else:
                est = cap.estimate_words(shot["narration"], start, sc["narration_s"])
                words += est
                sc["word_starts"] = [round(w.start - start, 3) for w in est]
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
        if spec.music_asset_id:
            try:
                a = self.library.assets.get(spec.music_asset_id)
            except KeyError:
                raise StageFailed("the chosen music track was deleted from the Asset Library") from None
            job["providers"]["music"] = f"asset: {a['name']}"
            job["music_track"] = str(self.library.assets.path(a))
            return
        gen = providers.build_music(self.cfg)
        if gen is not None:
            # Generated score: one bed per production (looped under longer videos), cached by mood + length.
            total = sum(self._timings(job)) + render.TRANSITION_S
            seconds = round(min(total, gen.max_seconds), 1)
            prompt = f"{mood}, instrumental background score for a short video, no vocals, steady, mixable"
            seed = int(job["id"][:8], 16) % 2**31
            src = self._cached("music", _key(gen.id, prompt, seconds, seed), ".wav",
                               lambda p: gen.generate(prompt, seconds, seed, p), verify.audio)
            dst = self.store.dir(job["id"]) / "music.wav"
            shutil.copyfile(src, dst)
            job["providers"]["music"] = f"{gen.id} ({mood})"
            job["music_track"] = str(dst)
            return
        track = render.pick_music(self.cfg.music_dir, mood, job["id"])
        job["providers"]["music"] = track.name if track else "none (no music library or model configured)"
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

        use_video = spec.motion == "ai_video"

        def transition(i: int, shot: dict) -> str:
            chosen = shot.get("transition", "")
            if chosen in render.TRANSITIONS and (spec.auto_edit or shot.get("transition_locked")):
                return chosen
            return t.transitions[i % len(t.transitions)]

        def clip_for(sc: dict) -> Path | None:
            # Imported clips are always used; generated clips only in AI video mode.
            if sc.get("clip") and ((use_video and sc.get("ai_video", True)) or sc.get("clip_source") == "asset"):
                return jdir / sc["clip"]
            return None

        clips, firsts = [], []   # firsts[i]: index in clips of scene i's opening shot
        for i, (sc, shot, d) in enumerate(zip(job["scenes"], shots, timings)):
            firsts.append(len(clips))
            video = clip_for(sc)
            beats = [b for b in (shot.get("beats") or [])] if spec.fast_cuts and video is None else []
            extra = list(sc.get("beat_images") or [])
            if len(beats) >= 2 and sc.get("image_source") != "asset" and any(n and (jdir / n).is_file() for n in extra):
                # Cut on the beat: each phrase gets screen time in proportion to its words, so the picture
                # changes exactly when the narration moves on.
                images = [jdir / sc["image"]] + [jdir / n if n and (jdir / n).is_file() else None for n in extra]
                lengths = _beat_lengths([b["text"] for b in beats], sc.get("word_starts") or [], d)
                cams = ["slow push in", "pull back", "pan left", "pan right"]
                for k, length in enumerate(lengths):
                    if k and images[k] is None:      # failed beat image: previous picture holds instead
                        clips[-1].duration += length
                        continue
                    clips.append(render.Clip(images[k], length,
                                             shot.get("camera", "") if k == 0 else cams[(i + k) % 4],
                                             transition(i, shot) if k == 0 else "cut"))
            else:
                clips.append(render.Clip(jdir / sc["image"], d, shot.get("camera", ""), transition(i, shot), video))
        for c in clips:
            if c.video is not None:
                c.video_duration = ff.duration(c.video)

        heads = [clips[j] for j in firsts]   # one per scene, for scene-level bookkeeping below
        if use_video and any(c.video is None and sc.get("ai_video", True) for c, sc in zip(heads, job["scenes"])):
            raise StageFailed("AI video mode but a chosen scene has no clip")

        plan = job["plan"]
        overlays, start = [], 0.0
        if plan.get("hook"):
            overlays.append(cap.Overlay(0.0, min(3.0, timings[0]), plan["hook"], "Hook"))
        for i, (shot, slot) in enumerate(zip(shots, timings)):
            if shot.get("overlay") and i > 0:
                overlays.append(cap.Overlay(start + 0.3, start + slot - 0.2, shot["overlay"], "Callout"))
            start += slot
        brand = spec.brand or {}
        cta = brand.get("outro_text") or plan.get("cta")
        if cta:
            overlays.append(cap.Overlay(max(0.0, total - 3.0), total, cta, "CTA"))
        if brand.get("intro_text"):
            overlays.append(cap.Overlay(0.0, min(2.5, total), brand["intro_text"], "Brand"))

        sfx_hits: list[tuple[Path, float, float]] = []
        if spec.sfx:
            bank = sfx.SfxBank.load(self.cfg.sfx_dir, [self.library.assets.path(a) for a in self.library.assets.list("sfx")])
            sfx_hits = sfx.place(bank, [c.transition for c in heads], timings,
                                 [(o.start, o.style) for o in overlays if spec.captions], job["id"])
            job["providers"]["sfx"] = f"{len(sfx_hits)} cues from {bank.describe()}" if bank.any() else "none (no SFX folder or SFX assets)"
        else:
            job["providers"]["sfx"] = "off"

        narr = work / "narration.wav"
        render.narration_track([jdir / sc["narration"] for sc in job["scenes"]], timings, tail, narr)
        music = Path(job["music_track"]) if job.get("music_track") else None
        if music is not None and not music.is_file():
            raise StageFailed(f"music track disappeared: {music}")
        mixed = work / "audio.wav"
        render.mix_audio(narr, music, total, mixed, cancel, sfx_hits)

        ass = None
        if spec.captions:
            words = [Word(**d) for d in json.loads((jdir / "words.json").read_text())]
            cues = cap.group(words, t.words_per_caption)
            ass = work / "captions.ass"
            emphasis = {wd for s in shots for wd in s.get("emphasis", [])} if spec.auto_edit else set()
            cap.write_ass(ass, w, h, t.caption_scale, t.caption_position, cues, overlays, emphasis,
                          brand.get("caption_color", ""), brand.get("highlight_color", ""))

        job["edit"] = {"auto_edit": spec.auto_edit, "transitions": [c.transition for c in heads[1:]],
                       "shots": len(clips),
                       "durations": [round(d, 2) for d in timings],
                       "sfx": [{"file": p.name, "at": round(at, 2)} for p, at, _ in sfx_hits],
                       "clip_stretch": [round(min(1.6, (d + render.TRANSITION_S) / c.video_duration), 2)
                                        if c.video_duration and c.video_duration < d + render.TRANSITION_S else 1.0
                                        for c, d in zip(heads, timings)]}
        out = jdir / "work" / "render.mp4"
        logo = None
        if brand.get("logo_asset_id"):
            try:
                a = self.library.assets.get(brand["logo_asset_id"])
            except KeyError:
                raise StageFailed("the brand logo was deleted from the Asset Library") from None
            if a["kind"] != "image":
                raise StageFailed("the brand logo must be an image asset")
            logo = (self.library.assets.path(a), brand.get("logo_position", "top-right"), brand.get("logo_opacity", 0.85))
            job["providers"]["brand"] = f"logo {a['name']} ({logo[1]})"
        expected = render.render_video(clips, mixed, ass, w, h, out, work, cancel, logo)
        job["render"] = {"file": "work/render.mp4", "expected_s": round(expected, 3), "width": w, "height": h}

    def _verify(self, job: dict, cancel) -> None:
        jdir = self.store.dir(job["id"])
        r = job.get("render") or {}
        src = jdir / r.get("file", "work/render.mp4")
        report = verify.mp4(src, r["width"], r["height"], r["expected_s"])
        final = jdir / "creatorforge.mp4"
        src.replace(final)
        job["result"] = {"file": final.name, "verification": report, "title": job["plan"]["title"]}
