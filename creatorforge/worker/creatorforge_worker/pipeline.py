"""ONE-BUTTON PRODUCTION: idea -> director plan -> PromptForge -> images -> narration ->
captions -> music -> assembly (transitions, overlays) -> render -> verify.

Every stage persists its output, so a crash, cancel or failure resumes from the first
unfinished stage instead of regenerating finished assets. Nothing reports success unless
the stage's output was verified."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import threading
from pathlib import Path

from . import director, providers
from .providers import speech
from .config import Config, VoiceProfile
from .library import Library
from .media import captions as cap
from .media import cards, charts, globe, layout, maps, match, objects, quality, render, sfx, verify
from .media import ff
from .media.ff import Cancelled, MediaError
from .providers.base import NotConfigured, ProviderError, Word
from .store import STAGES, JobStore
from .templates import (ASPECTS, CALLOUT_LOOKS, CUTOUT_LOOKS, DESK_STYLES, EDITORIAL_LEADS, EDITORIAL_STYLES,
                        MIX_STYLE, TEMPLATES)

SCENE_GAP_S = 0.12   # breath between scenes - longer gaps lose viewers
MIN_SCENE_S = 1.5
MAX_HOLD_S = 0.5     # cap on the Director's dramatic pauses
REVEAL_PAUSE_S = 0.3
FAST_PICTURES = 60           # more pictures than this: the image model's fast pass (long videos)
ENDING_HOLD_S = (1.5, 2.5)   # seconds the last picture holds after the final word: Shorts, long videos
REVEAL_EMOTIONS = {"shock", "surprise", "awe"}
SHOCK_EMOTIONS = {"shock", "surprise", "fear", "horror", "disgust", "terror"}



def _covered(beat: dict) -> bool:
    """True when a full-frame graphic (chart, map, steps, chapter or quote card) replaces the beat's picture."""
    extra = beat.get("extra") or {}
    return bool(beat.get("chart") or any(extra.get(k) for k in director.FULL_FRAME))

class StageFailed(Exception):
    pass


class ReviewPause(Exception):
    pass


def _key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:32]


def _beat_lengths(texts: list[str], word_starts: list[float], total: float, spoken: float | None = None,
                  shortest: float = 0.3) -> list[float]:
    """Screen time per beat. With Whisper's word timings each cut lands on the first word of its phrase;
    without them, the spoken part (not the pause or ending hold after it) is shared in proportion to the words,
    and the last beat keeps the picture through the pause."""
    counts = [max(1, len(t.split())) for t in texts]
    n = sum(counts)
    talk = min(total, spoken) if spoken else total
    cuts, seen = [0.0], 0
    for c in counts[:-1]:
        seen += c
        if len(word_starts) >= 2:
            cuts.append(word_starts[min(len(word_starts) - 1, round(seen * len(word_starts) / n))])
        else:
            cuts.append(talk * seen / n)
    cuts.append(total)
    if len(texts) * shortest > total:
        return [total * c / n for c in counts]
    # Whisper can merge or drop words: a beat squeezed under a visible moment borrows from its neighbours
    # instead of throwing every cut away.
    for i in range(1, len(cuts) - 1):
        cuts[i] = max(cuts[i], cuts[i - 1] + shortest)
    for i in range(len(cuts) - 2, 0, -1):
        cuts[i] = min(cuts[i], cuts[i + 1] - shortest)
    return [b - a for a, b in zip(cuts, cuts[1:])]


# Stock searches about people and places in the story's country: a "protest" or "police" clip must be from there
# (Pexels/Pixabay/Unsplash would otherwise return a protest in Paris for a line about Delhi).
_LOCAL = re.compile(r"\b(protest|demonstrat|rally|march|crowd|police|street|market|city|village|farmer|student|voter|"
                    r"queue|parliament|court|office|slum|traffic|train|station|hospital|school|people|worker|women|men\b|"
                    r"youth|famil|shop|road|election|polling|booth|politic|minister|leader|journalist|press)", re.I)
_PLACE_WORDS = {"India": ("india", "indian", "delhi", "mumbai", "kolkata", "bengaluru", "bangalore", "chennai",
                          "hyderabad", "punjab", "kerala", "rajasthan", "bihar", "gujarat", "varanasi", "jaipur",
                          "lucknow", "kashmir", "assam", "maharashtra", "uttar pradesh", "bengal", "hindu", "sikh",
                          "sari", "saree", "rickshaw")}


def _place_words(country: str, city: str = "") -> tuple[str, ...]:
    if not country:
        return ()
    return tuple(dict.fromkeys([*(w.lower() for w in (city,) if w), *_PLACE_WORDS.get(country, (country.lower(),))]))


def stock_queries(query: str, country: str, city: str = "") -> tuple[list[str], tuple[str, ...]]:
    """The searches for a stock line, and the place words a result must mention: "protest march" in a story
    about Delhi searches "protest march Delhi" / "protest march India" and needs a Delhi/India result."""
    words = _place_words(country, city)
    if not words or not _LOCAL.search(query) or any(w in query.lower() for w in words):
        return [query], ()
    return list(dict.fromkeys(q for q in (f"{query} {city}" if city else "", f"{query} {country}") if q)), words


def stock_fits(found: dict, query: str, place: tuple[str, ...], checked: bool) -> bool:
    """A library result is only used when its own description says it shows the line (and, for local scenes,
    the story's country). Without the picture check, a result with no description is never trusted."""
    if str(found.get("url", "")).startswith("mock://"):
        return True
    about = str(found.get("about") or "").lower()
    if place and about and not any(re.search(rf"\b{re.escape(w)}", about) for w in place):
        return False                # a protest somewhere else
    if checked:
        return True                 # the picture check looks at the frame itself
    from .providers.stock_video import relevant
    bare = " ".join(w for w in query.split() if w.lower() not in place)
    return bool(about) and relevant(bare or query, about) and (not place or any(re.search(rf"\b{re.escape(w)}", about)
                                                                                 for w in place))


# Pictures of paperwork: a cited article's real page shows these better than any drawing
_PAPERWORK = re.compile(r"\b(newspapers?|front[- ]pages?|headlines?|mastheads?|articles?|reports?|documents?|"
                        r"files?|clippings?|chargesheets?|orders?|judg(e)?ments?|notices?|press releases?|"
                        r"manifestos?|transcripts?|records?|registers?)\b", re.I)


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
        # The script model on the pod (Ollama) shares the GPU with the picture/video models. If they are still loaded
        # from the last video it starts half on the CPU and can take over ten minutes, so make room first and hand
        # the GPU back as soon as the plan is written.
        if self.cfg.llm_url and providers.is_local_url(self.cfg.llm_url):
            providers.release_gpu()
        try:
            if spec.script:
                try:
                    llm = providers.director_llm(self.cfg, job["id"])
                except NotConfigured:
                    llm = None
                plan, llm = self._with_gpu_room(lambda m: director.direct_script(m, spec), llm, optional=True)
                job["providers"]["llm"] = f"{llm.id} (script mode)" if llm else "none (script mode: visuals from your words)"
            else:
                llm = providers.director_llm(self.cfg, job["id"])
                plan, llm = self._with_gpu_room(lambda m: director.direct(m, spec), llm)
                job["providers"]["llm"] = llm.id
            if spec.fast_cuts:
                self._with_gpu_room(lambda m: director.plan_beats(m, plan, spec), llm, optional=True)
        finally:
            providers.unload_local_llm(self.cfg)
        job["plan"] = plan.to_dict()
        job["scenes"] = [{"index": i, "image_state": "PLANNED", "voice_state": "PLANNED", "clip_state": "PLANNED",
                          "image": None, "narration": None, "narration_s": None, "clip": None, "error": None}
                         for i in range(len(plan.scenes))]

    def _with_gpu_room(self, step, llm, optional: bool = False):
        """Runs a script-model step. If the GPU is full (the image/video models from an earlier video are still
        loaded), frees them and tries again. A script-mode video carries on without the script model whenever it
        fails (out of memory, unreachable, too slow, or a server error such as Ollama's "token repeat limit
        reached"), because its pictures come from the writer's own Visual lines."""
        try:
            return step(llm), llm
        except ProviderError as e:
            if llm is None:
                raise
            if "memory" not in str(e).lower():
                if optional:
                    return step(None), None
                raise
        providers.release_gpu()
        try:
            return step(llm), llm
        except ProviderError:
            if not optional:
                raise
        return step(None), None

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
        img = providers.build_image(self.cfg, spec.style)
        scenes, shots = job["scenes"], job["plan"]["scenes"]
        # A long video has well over a hundred pictures: draw them in one faster pass so it doesn't take hours
        pictures = sum(max(1, len(s.get("beats") or [])) for s in shots)
        if hasattr(img, "fast"):
            img.fast = pictures > FAST_PICTURES
        job["providers"]["image"] = img.id + (" (fast pass: long video)" if getattr(img, "fast", False) else "")
        jdir = self.store.dir(job["id"])
        seed_base = int(job["id"][:8], 16)
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
            face = self._face_lock(img, job, jdir, shot["visual"])
            try:
                beats0 = shot.get("beats") or []
                named = (beats0[0].get("named") if beats0 else shot.get("named")) or {}
                real = None
                first = beats0[0] if beats0 else {"text": shot.get("narration", ""), "visual": shot["visual"], "extra": {}}
                if not (beats0 and _covered(beats0[0])):
                    real = self._source_shot(job, first, self._out_size(job))  # a newspaper line: the real page
                if real is None and not (beats0 and _covered(beats0[0])) and (not named or named.get("movement")):
                    real = self._news_photo(job, first, self._out_size(job))   # the cited article's own photo
                if real is None and named and not (beats0 and _covered(beats0[0])):
                    real = self._named_photo(job, named, self._out_size(job))  # the person/party/place named
                # a full-frame graphic covers the scene's first picture: keep the real photos for pictures people see
                if real is None and not (beats0 and _covered(beats0[0])):
                    real = self._real_photo(
                        job, shot.get("stock") or "", shot["visual"],
                        str(((beats0[0].get("extra") or {}) if beats0 else {}).get("archive") or ""),
                        where=str((beats0[0].get("country") if beats0 else "") or ""))
                if real is not None:
                    dst = self._replace_file(jdir, sc.get("image"), f"scene_{sc['index'] + 1:02d}_photo{real.suffix}", real)
                    sc.update(image_state="READY", image=dst.name, image_source="photo")
                    self.store.save(job)
                    continue
                src, key = self._matched_image(job, img, shot["prompt"], shot["negative"], gen, seed, face,
                                               shot["visual"])
                dst = self._replace_file(jdir, sc.get("image"), f"scene_{sc['index'] + 1:02d}_{key[:8]}.png", src)
                sc.update(image_state="READY", image=dst.name, image_source="generated")
                self._remember_face(job, dst, shot["visual"])
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
        self._asset_clips(job, jdir)
        stock = providers.stock_sources(job["id"], self.cfg)
        photos = providers.photo_sources(job["id"], self.cfg)
        portrait = self._spec(job).aspect == "9:16"
        for sc, shot in zip(job["scenes"], job["plan"]["scenes"]):
            beats = shot.get("beats") or []
            if len(beats) < 2 or sc.get("image_source") == "asset":
                continue
            if stock:
                self._stock_clips(job, sc, beats, stock, jdir)
            clips = sc.get("beat_clips") or []
            names = list(sc.get("beat_images") or [])[: len(beats) - 1]
            names += [None] * (len(beats) - 1 - len(names))
            for k, b in enumerate(beats[1:]):
                if names[k] and (jdir / names[k]).is_file():
                    continue
                if k + 1 < len(clips) and clips[k + 1]:
                    continue                 # real footage covers this beat - no AI image needed
                if _covered(b):
                    continue                 # a chart, map or card fills the frame - no picture needed
                if cancel.is_set():
                    raise Cancelled()
                if photos and b.get("stock") and not b.get("named"):
                    names[k] = self._stock_photo(job, sc, k + 2, b["stock"], photos, portrait, jdir, b.get("visual", ""))
                    if names[k]:
                        sc["beat_images"] = names
                        self.store.save(job)
                        continue     # a real photo covers this beat - no AI image needed
                real = self._source_shot(job, b, self._out_size(job))
                if real is None and (not b.get("named") or b["named"].get("movement")):
                    real = self._news_photo(job, b, self._out_size(job))
                if real is None and b.get("named"):
                    real = self._named_photo(job, b["named"], self._out_size(job))
                real = real or self._real_photo(job, b.get("stock") or "", b.get("visual", ""),
                                                str((b.get("extra") or {}).get("archive") or ""),
                                                where=str(b.get("country") or ""))
                if real is not None:
                    dst = jdir / f"scene_{sc['index'] + 1:02d}_beat{k + 2}_photo{real.suffix}"
                    shutil.copyfile(real, dst)
                    names[k] = dst.name
                    sc["beat_images"] = names
                    self.store.save(job)
                    continue
                seed = (seed_base + sc["index"] * 7919 + (k + 1) * 104729) % 2**31
                face = self._face_lock(img, job, jdir, b["visual"])
                try:
                    src, key = self._matched_image(job, img, b.get("prompt", ""), b.get("negative", ""), gen, seed,
                                                   face, b.get("visual", ""))
                    dst = jdir / f"scene_{sc['index'] + 1:02d}_beat{k + 2}_{key[:8]}.png"
                    if not dst.is_file():
                        shutil.copyfile(src, dst)
                    names[k] = dst.name
                except (ProviderError, MediaError):
                    names[k] = None
                sc["beat_images"] = names
                self.store.save(job)

    def _matcher(self):
        return match.matcher(self.cfg.data_dir / "models" / "clip")

    def _note_match(self, job: dict, **counts) -> None:
        m = job.setdefault("match", {"checked": 0, "regenerated": 0, "stock_rejected": 0, "low": 0})
        for k, v in counts.items():
            m[k] = m.get(k, 0) + v
        job["providers"]["match"] = (f"visual match check: {m['checked']} pictures, {m.get('real_photos', 0)} real photos, "
                                     f"{m.get('named', 0)} named people/places, "
                                     f"{m['regenerated']} regenerated, {m['stock_rejected']} off-topic stock skipped"
                                     + (f", {m['low']} still weak" if m["low"] else ""))

    def _matched_image(self, job: dict, img, prompt: str, negative: str, gen, seed: int, face: str,
                       visual: str) -> tuple[Path, str]:
        """Generates the picture and checks it shows what the line describes; a picture that drifted (a face where
        the line asks for a map) is redrawn with new seeds and the closest of up to three is kept."""
        checker = self._matcher() if visual else None
        best: tuple[float, Path, str] | None = None
        lead = EDITORIAL_LEADS.get(self._spec(job).style, "photograph")
        tries = (2 if getattr(img, "fast", False) else 3) if checker else 1
        for attempt in range(tries):
            s = (seed + attempt * 15485863) % 2**31
            # Last try: a plain prompt with just the subject - models get compound or metaphorical scenes wrong,
            # but rarely miss "old paper map Britain".
            # the subject put first, keeping the forged prompt's look, setting and colour (never the old-print lead)
            p_text = prompt if attempt == 0 or attempt < tries - 1 else f"{match.subject(visual, 6)}, {prompt}"
            key = _key(img.id, p_text, negative, gen, s, face)
            src = self._cached("images", key, ".png",
                               lambda p, s=s, t=p_text: img.generate(t, negative, gen[0], gen[1], s, p), verify.image)
            if checker is None:
                return src, key
            score = checker.score(src, match.describe(visual))
            if match.is_flat(src):
                score -= 0.5                  # a blank screen or page shows nothing: never kept over a real picture
            score -= match.text_penalty(checker, src, visual)   # garbled fake writing: draw it again
            if best is None or score > best[0]:
                best = (score, src, key)
            if score >= match.GOOD:
                break
        self._note_match(job, checked=1, regenerated=1 if attempt else 0, low=1 if best[0] < match.GOOD else 0)
        return best[1], best[2]

    def _out_size(self, job: dict) -> tuple[int, int]:
        """The finished video's frame size: real photos are framed at this size, not the smaller drawing size."""
        return ASPECTS[self._spec(job).aspect][1]

    def _gen(self, job: dict) -> tuple[int, int]:
        return ASPECTS[self._spec(job).aspect][0]

    def _news_links(self, job: dict) -> list[dict]:
        from .providers import news_media
        return news_media.source_links(str((self._spec(job).publish or {}).get("source") or ""))

    def _fresh_print(self, job: dict | None, image: Path, owner: str, within: int = 8) -> bool:
        """False when this picture looks like one already used in the video by something else (two article pages
        rendering the same consent wall, a site's generic share image on every article)."""
        if job is None:
            return True
        fp = match.fingerprint(image)
        if fp is None:
            return True
        prints = job.setdefault("print_owner", {})
        for other, who in prints.items():
            if who != owner and match.seen_before(fp, [json.loads(other)], within):
                return False
        prints[json.dumps(fp)] = owner
        return True

    def _source_shot(self, job: dict, beat: dict, gen) -> Path | None:
        """A line whose picture is a newspaper, report or document gets the real thing when the script cites it:
        a screenshot of the matching Source: article (each article once per video). None: the line keeps its
        other pictures."""
        if not self.cfg.free_stock or not _PAPERWORK.search(str(beat.get("visual") or "")):
            return None
        links = self._news_links(job)
        if not links:
            return None
        from .providers import news_media
        cite = str((beat.get("extra") or {}).get("cite") or "")
        used = set((job.get("shot_for") or {}).values())
        link = news_media.find_link(f"{beat.get('text') or ''} {cite}", links, cite.split(",")[0].strip(),
                                    min_overlap=2, skip=used)
        if link is None:
            return None
        shot = news_media.screenshot(link["url"], self.cfg.cache_dir / "news")
        if shot is None or not self._fresh_print(job, shot, link["url"], within=2):
            return None
        job.setdefault("shot_for", {})[f"line:{beat.get('text')}"] = link["url"]
        label = news_media.host_label(link)
        out = news_media.framed(shot, self.cfg.cache_dir / "news" / f"page_{shot.stem}_{gen[0]}x{gen[1]}.png",
                                gen[0], gen[1], label)
        credit = f"Screenshot: {label} ({link['url']})"
        credits = job.setdefault("stock_credits", [])
        if credit not in credits:
            credits.append(credit)
        return out

    def _news_photo(self, job: dict, beat: dict, gen) -> Path | None:
        """The cited article's own lead photo, for a line about the events it reports (a protest, an arrest, a
        court hearing): the real picture from the news, credited "Photo via <publisher>". Each article's photo is
        used at most twice and never on two lines in a row."""
        if not self.cfg.free_stock:
            return None
        text = str(beat.get("text") or "")
        cite = str((beat.get("extra") or {}).get("cite") or "")
        if not cite and not _EVENT.search(f"{text} {beat.get('visual') or ''}"):
            return None
        links = self._news_links(job)
        if not links:
            return None
        from .providers import news_media
        publisher = cite.split(",")[0].split("/")[0].strip()
        link = news_media.find_link(f"{text} {cite}", links, publisher)
        if link is None:
            return None
        uses = job.setdefault("news_used", {})
        if uses.get(link["url"], 0) >= 2 or job.get("news_last") == link["url"]:
            return None
        cache = self.cfg.cache_dir / "news"
        try:
            src = news_media.lead_photo(link["url"], cache)
        except Exception:  # noqa: BLE001 - a news site that blocks us: the line keeps its other pictures
            src = None
        if src is None or match.is_flat(src) or not self._fresh_print(job, src, link["url"]):
            return None
        out = news_media.frame_photo(src, cache / f"framed_{src.stem}_{gen[0]}x{gen[1]}.jpg", gen[0], gen[1])
        uses[link["url"]] = uses.get(link["url"], 0) + 1
        job["news_last"] = link["url"]
        credit = f"Photo via {news_media.host_label(link)} ({link['url']})"
        credits = job.setdefault("stock_credits", [])
        if credit not in credits:
            credits.append(credit)
        self._note_match(job, checked=1, real_photos=1, named=1)
        return out

    def _named_photo(self, job: dict, named: dict, gen) -> Path | None:
        """A real picture of the person, party, institution or place the words name: the party symbol when the
        line says "the BJP", the politician when it says "Rahul Gandhi", the building when it says "Parliament".
        Found by name on Wikipedia/Commons; a repeat mention gets a different photo where one exists. Faces are
        allowed here - they are the public figures the line is about. Nothing found: the line keeps its picture."""
        name = str(named.get("name") or "").strip()
        if not name or not self.cfg.free_stock:
            return None
        from .providers import wiki_image
        cache = job.setdefault("named_cache", {})
        if name not in cache and len(cache) >= 40:
            return None                   # a cap on lookups per video
        try:
            if name not in cache:
                page = wiki_image.resolve(name, named.get("context", ""), named.get("topic") or [],
                                          named.get("city", ""))
                if page:
                    cache[name] = {"title": page["title"], "pics": wiki_image.pictures(page)}
                elif len(name.split()) >= 2:
                    # no Wikipedia page (a new movement's founder): Commons photos that name them in full
                    cache[name] = {"title": name, "pics": wiki_image.search_by_name(name)}
                else:
                    cache[name] = {}
            entry = cache[name]
        except ProviderError:
            cache[name] = {}          # Wikipedia unreachable: don't retry this name (20 s each) on every line
            return None
        used = job.setdefault("used_photos", [])
        pics = entry.get("pics") or []
        # the first unused picture; when all were shown, the subject's lead picture again (a symbol can repeat)
        # each photo once; only a party symbol or logo may come back (a person's photo on repeat looks broken)
        again = [p for p in pics[:1] if p.get("logo")]
        for pic in [p for p in pics if p["url"] not in used] + again:
            try:
                src = wiki_image.fetch_framed(pic, self.cfg.cache_dir / "named_photos", gen)
            except (ProviderError, OSError):
                continue
            if not pic.get("logo") and match.is_flat(src):
                continue
            if not pic.get("logo") and _greyscale(src) and any(p["url"] not in used and p is not pic for p in pics):
                continue                      # a black-and-white photo only when there's no colour one left
            if not pic.get("logo"):
                fp = match.fingerprint(src)
                if match.seen_before(fp, job.setdefault("used_fingerprints", [])):
                    used.append(pic["url"])
                    continue                  # the same photo under another address
                if fp is not None:
                    job["used_fingerprints"].append(fp)
            used.append(pic["url"])
            credits = job.setdefault("stock_credits", [])
            if pic["credit"] not in credits:
                credits.append(pic["credit"])
            self._note_match(job, checked=1, real_photos=1, named=1)
            return src
        return None

    def _archive_photo(self, job: dict, visual: str, era: str) -> Path | None:
        """A history line: a real period photograph from Wikimedia Commons (public domain / open licence) when one
        clearly shows what the line describes; credited in the post description."""
        checker = self._matcher()
        if checker is None or not visual or not self.cfg.free_stock:
            return None
        from .providers import archive_photo, stock_photo
        want = match.describe(visual)
        used = job.setdefault("used_photos", [])
        m = re.search(r"\b(1[5-9]\d\d|20\d\d)s?\b", era)
        decade = m.group(0) if m else ""
        for q in dict.fromkeys(x for x in (f"{match.subject(visual)} {decade}".strip(), match.subject(visual, 3)) if x):
            try:
                found_all = archive_photo.search(q)
            except ProviderError:
                return None
            for found in found_all[:5]:
                if found["url"] in used:
                    continue
                try:
                    src = stock_photo.fetch(found, self.cfg.cache_dir / "archive_photos")
                except (ProviderError, OSError):
                    continue
                if checker.score(src, want) < match.GOOD - 0.02 or match.shows_face(checker, src, visual):
                    continue
                fp = match.fingerprint(src)
                if match.seen_before(fp, job.setdefault("used_fingerprints", [])):
                    continue
                used.append(found["url"])
                if fp is not None:
                    job["used_fingerprints"].append(fp)
                credits = job.setdefault("stock_credits", [])
                if found["credit"] not in credits:
                    credits.append(found["credit"])
                self._note_match(job, checked=1, real_photos=1)
                return src
        return None

    def _real_photo(self, job: dict, query: str, visual: str, era: str = "", where: str = "") -> Path | None:
        """Explainer looks: a real photograph of what the line shows (archive/stock), when one clearly matches -
        the way a video essay is built. Needs the match check to judge it; otherwise the line gets an AI picture."""
        spec = self._spec(job)
        if era and spec.style in EDITORIAL_STYLES:
            found = self._archive_photo(job, visual, era)
            if found is not None:
                return found
        checker = self._matcher()
        photos = providers.photo_sources(job["id"], self.cfg)
        if spec.style not in EDITORIAL_STYLES or not visual or checker is None or not photos:
            return None
        from .providers import stock_photo
        want = match.describe(visual)
        used = job.setdefault("used_photos", [])        # one photo is shown once per video, never on repeat
        base = [x for x in (query, match.subject(visual)) if x]
        # a story set in India looks for Indian courts and streets first, not whatever comes up
        tries = ([f"{x} {where}" for x in base if where.lower() not in x.lower()] if where else []) + base
        for q in dict.fromkeys(tries):
            for found in stock_photo.search_any(photos, q, spec.aspect == "9:16")[:4]:
                if found.get("url") in used:
                    continue
                try:
                    src = stock_photo.fetch(found, self.cfg.cache_dir / "stock_photos")
                except (ProviderError, OSError):
                    continue
                if checker.score(src, want) < match.GOOD or match.shows_face(checker, src, visual) or match.is_flat(src):
                    continue
                fp = match.fingerprint(src)
                if match.seen_before(fp, job.setdefault("used_fingerprints", [])):
                    continue                     # the same photo again (another library, another address)
                used.append(found.get("url"))
                if fp is not None:
                    job["used_fingerprints"].append(fp)
                credits = job.setdefault("stock_credits", [])
                if found["credit"] not in credits:
                    credits.append(found["credit"])
                self._note_match(job, checked=1, real_photos=1)
                return src
        return None

    def _on_topic(self, job: dict, media: Path, query: str, visual: str) -> bool:
        """Real footage/photos must show what the line is about; an off-topic result is skipped."""
        checker = self._matcher()
        if checker is None:
            return True       # callers only pass keyed-library media when there is no checker
        frame = media
        if media.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            frame = self.cfg.cache_dir / "match" / f"{media.stem}_{media.stat().st_size}.jpg"
            if not frame.is_file():
                frame.parent.mkdir(parents=True, exist_ok=True)
                try:
                    at = min(1.0, max(0.0, ff.duration(media) / 3))
                    ff.run(["-ss", f"{at:.2f}", "-i", str(media), "-frames:v", "1", "-q:v", "3", str(frame)])
                except (MediaError, OSError):
                    return True
        line = checker.score(frame, match.describe(visual)) if visual else checker.score(frame, query)
        score = max(checker.score(frame, query), line)
        # it must show this line, not merely the 2-word search ("crowd" footage on any line about people)
        if score < match.POOR or (visual and line < match.POOR) or match.shows_face(checker, frame, visual) \
                or match.is_flat(frame):
            # off-topic, a face, or a clip that shows nothing (a dark or blank frame)
            # off-topic, or a face close-up the line didn't ask for (the channel is faceless)
            self._note_match(job, stock_rejected=1)
            return False
        return True

    def _face_lock(self, img, job: dict, jdir: Path, visual: str) -> str:
        """Points the image model at the video's character reference for shots with people; returns a cache tag."""
        if not hasattr(img, "reference"):
            return ""
        ref = job.get("character_ref")
        people = director._has_people(visual)
        if self._spec(job).consistent_character and ref and people and (jdir / ref).is_file():
            img.reference, img.ref_strength = jdir / ref, 0.6
            return f"face:{ref}:0.6"
        img.reference, img.ref_strength = None, 0.0
        return ""

    def _remember_face(self, job: dict, image: Path, visual: str) -> None:
        """The first generated shot showing people becomes the character reference for the rest of the video."""
        if self._spec(job).consistent_character and not job.get("character_ref") and director._has_people(visual):
            job["character_ref"] = image.name

    def _story_place(self, job: dict) -> tuple[str, str]:
        """The story's country and city (from the whole script), worked out once per video."""
        if "story_place" not in job:
            from .media import literal
            text = " ".join(str(sh.get("narration", "")) for sh in (job.get("plan") or {}).get("scenes", []))
            job["story_place"] = [literal.context_country(text), literal.context_city(text)]
        return tuple(job["story_place"])

    def _stock_photo(self, job: dict, sc: dict, beat: int, query: str, photos: list, portrait: bool,
                     jdir: Path, visual: str = "") -> str | None:
        """A real photo for a beat no footage covered (best effort; None -> the beat gets an AI image)."""
        from .providers import stock_photo
        if self._matcher() is None:
            photos = [p for p in photos if p[1] or p[0] == "mock"]   # keyless libraries only with the picture check
        queries, place = stock_queries(query, *self._story_place(job))
        checked = self._matcher() is not None
        found_all = []
        for q in queries:
            found_all = [f for f in stock_photo.search_any(photos, q, portrait) if stock_fits(f, query, place, checked)]
            if found_all:
                break
        for found in found_all[:3]:
            try:
                src = stock_photo.fetch(found, self.cfg.cache_dir / "stock_photos")
            except (ProviderError, OSError):
                continue
            if found.get("url") in job.setdefault("used_photos", []) or not self._on_topic(job, src, query, visual):
                continue
            checker = self._matcher()
            if checker is not None and match.shows_face(checker, src, visual):
                continue
            fp = match.fingerprint(src)
            if match.seen_before(fp, job.setdefault("used_fingerprints", [])):
                continue
            job["used_photos"].append(found.get("url"))
            if fp is not None:
                job["used_fingerprints"].append(fp)
            dst = jdir / f"scene_{sc['index'] + 1:02d}_beat{beat}_photo.jpg"
            shutil.copyfile(src, dst)
            credits = job.setdefault("stock_credits", [])
            if found["credit"] not in credits:
                credits.append(found["credit"])
            return dst.name
        return None

    def _asset_clips(self, job: dict, jdir: Path) -> None:
        """The writer's "Clip:" lines: their own Asset Library clips, each played on its line (sound removed).
        "Clip: delhi march" finds the video asset by name; "Clip: delhi march @ 0:12" starts 12 s in. A name that
        isn't in the library is reported and the line keeps its normal picture."""
        missing = []
        for sc, shot in zip(job["scenes"], job["plan"]["scenes"]):
            beats = shot.get("beats") or []
            want = [str((b.get("extra") or {}).get("clip") or "").strip() for b in beats]
            if not any(want):
                continue
            clips = (list(sc.get("beat_clips") or []) + [None] * len(beats))[: len(beats)]
            for k, ref in enumerate(want):
                if not ref or (clips[k] and (jdir / clips[k]).is_file()):
                    continue
                name, start = clip_ref(ref)
                asset = find_asset(self.library.assets.list("video"), name)
                if asset is None:
                    missing.append(name)
                    continue
                src = self.library.assets.path(asset)
                try:
                    length = ff.duration(src)
                except (MediaError, OSError, KeyError, ValueError):
                    missing.append(f"{name} (not a readable video)")
                    continue
                if start >= length - 0.5:
                    start = max(0.0, length - 1.0)    # a start time past the clip's end: play its last second
                dst = jdir / f"scene_{sc['index'] + 1:02d}_clip{k + 1}_{asset['id']}_{int(start)}.mp4"
                if not dst.is_file():
                    try:
                        ff.run(["-ss", f"{start:.2f}", "-i", str(src), "-t", "30", "-an", "-c:v", "libx264",
                                "-preset", "veryfast", "-pix_fmt", "yuv420p", str(dst)])
                        if ff.duration(dst) <= 0:
                            raise MediaError("no video in the cut")
                    except (MediaError, OSError, KeyError, ValueError) as e:
                        dst.unlink(missing_ok=True)       # never keep a broken cut: the next try starts clean
                        missing.append(f"{name} ({e})")
                        continue
                clips[k] = dst.name
            sc["beat_clips"] = clips
        if missing:
            job.setdefault("warnings", []).append(
                "Clip not found in your Asset Library (line keeps its picture): " + ", ".join(dict.fromkeys(missing)))
        used = sum(1 for sc in job["scenes"] for n in (sc.get("beat_clips") or []) if n and "_clip" in n)
        if used:
            job["providers"]["clips_own"] = f"{used} of your own clip{'s' if used != 1 else ''}"
        self.store.save(job)

    def _stock_clips(self, job: dict, sc: dict, beats: list, stock: list[tuple[str, str]], jdir: Path) -> None:
        """Real footage for beats the planner marked with a stock search (best effort, cached)."""
        from .providers import stock_video
        clips = list(sc.get("beat_clips") or [])[: len(beats)]
        clips += [None] * (len(beats) - len(clips))
        portrait = self._spec(job).aspect == "9:16"
        used = job.setdefault("used_clips", [])
        keyed = [x for x in stock if x[1]]
        checked = self._matcher() is not None
        for k, b in enumerate(beats):
            if clips[k] and (jdir / clips[k]).is_file() or not b.get("stock"):
                continue
            if b.get("named") and not b["named"].get("movement"):
                continue     # a line about a named person or party shows them, never a stock look-alike
            history = bool((b.get("extra") or {}).get("archive"))
            # keyless libraries rank loosely: without the picture check they are not trusted at all
            sources = list(stock if checked else keyed) + (providers.archive_sources(self.cfg) if history else [])
            queries, place = stock_queries(b["stock"], *self._story_place(job)) if not history else ([b["stock"]], ())
            candidates = []
            for q in queries:
                candidates = [f for f in stock_video.search_any(sources, q, portrait)
                              if stock_fits(f, b["stock"], place, checked)]
                if candidates:
                    break
            for found in candidates[:4]:
                if found["url"] in used:
                    continue     # never the same footage on two lines
                try:
                    src = stock_video.fetch(found, self.cfg.cache_dir / "stock")
                except (ProviderError, MediaError, OSError):
                    continue     # try the next candidate; none left -> this beat gets an AI image as usual
                if not self._on_topic(job, src, b["stock"], b.get("visual", "")):
                    continue     # footage that doesn't show the line: try the next one
                frame = self.cfg.cache_dir / "match" / f"{src.stem}_{src.stat().st_size}.jpg"
                if not history and frame.is_file() and _greyscale(frame):
                    continue     # black-and-white film on a line about today
                fp = match.fingerprint(frame) if frame.is_file() else None
                if match.seen_before(fp, job.setdefault("used_fingerprints", [])):
                    continue
                used.append(found["url"])
                if fp is not None:
                    job["used_fingerprints"].append(fp)
                dst = jdir / f"scene_{sc['index'] + 1:02d}_stock{k + 1}{src.suffix}"
                if not dst.is_file():
                    shutil.copyfile(src, dst)
                clips[k] = dst.name
                job.setdefault("stock_credits", [])
                if found["credit"] not in job["stock_credits"]:
                    job["stock_credits"].append(found["credit"])
                break
        sc["beat_clips"] = clips
        used = sum(1 for c in job.get("scenes", []) for n in (c.get("beat_clips") or []) if n)
        job["providers"]["stock"] = f"{', '.join(p for p, _ in stock)} ({used} real clip{'s' if used != 1 else ''} so far)"
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
        per_line = [i for i in chosen if spec.fast_cuts and len(shots[i].get("beats") or []) >= 2
                    and scenes[i].get("clip_source") != "asset"]
        if per_line:
            # One clip per spoken line: the picture moves exactly while its line is spoken.
            self._line_clips(job, video, per_line, gen, cancel)
        for sc, shot, slot in zip(scenes, shots, self._timings(job)):
            if not sc.get("ai_video") or sc["index"] in per_line:
                if not sc.get("ai_video") and sc.get("clip_source") != "asset":
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

    def _line_clips(self, job: dict, video, indices: list[int], gen: tuple[int, int], cancel) -> None:
        """AI video for every spoken line of the chosen scenes. Each beat's still (scene image for the first line,
        beat images after) is animated for about as long as its line is spoken, so clips never need to loop.
        Lines with real stock footage keep it. A line whose clip fails keeps its still with a smooth camera move;
        only if every clip fails does the stage fail (the video model is broken, not one prompt)."""
        jdir = self.store.dir(job["id"])
        scenes, shots = job["scenes"], job["plan"]["scenes"]
        if hasattr(video, "max_frames") and hasattr(video, "_model_limits"):
            video.max_frames = video._model_limits[1]          # lines can run a little past the preset's clip length
        todo = [(i, k) for i in indices for k in range(len(shots[i]["beats"]))]
        done = failed = 0
        last_error = ""
        for i in indices:
            sc, shot = scenes[i], shots[i]
            beats = shot["beats"]
            names = (list(sc.get("beat_videos") or []) + [None] * len(beats))[: len(beats)]
            stock = (list(sc.get("beat_clips") or []) + [None] * len(beats))[: len(beats)]
            stills = [sc.get("image")] + list(sc.get("beat_images") or [])
            words = [max(1, len(b["text"].split())) for b in beats]
            speech = sc.get("narration_s") or sum(words) / 2.6
            for k, b in enumerate(beats):
                self._stage(job, "clips", "RUNNING", done=done, total=len(todo))
                done += 1
                if (names[k] and (jdir / names[k]).is_file()) or (stock[k] and (jdir / stock[k]).is_file()):
                    continue
                still = stills[k] if k < len(stills) else None
                if not still or not (jdir / still).is_file():
                    continue                                    # no picture for this line: it holds the previous one
                if cancel.is_set():
                    raise Cancelled()
                seconds = round(min(6.0, max(1.6, speech * words[k] / sum(words) + 0.5)), 2)
                seed = (int(job["id"][:8], 16) + i * 104729 + (k + 1) * 7919) % 2**31
                vprompt = b.get("video_prompt") or shot.get("video_prompt") or shot["prompt"]
                vneg = shot.get("video_negative") or director.VIDEO_NEGATIVE
                image = jdir / still
                key = _key(video.id, hashlib.sha256(image.read_bytes()).hexdigest(), vprompt, seconds, gen, seed)
                try:
                    src = self._cached("clips", key, ".mp4",
                                       lambda p: video.generate(image, vprompt, vneg, seconds, gen[0], gen[1], seed, p),
                                       verify.clip)
                    dst = jdir / f"scene_{i + 1:02d}_line{k + 1}_{key[:8]}.mp4"
                    if not dst.is_file():
                        shutil.copyfile(src, dst)
                    names[k] = dst.name
                except (ProviderError, MediaError) as e:
                    failed += 1
                    last_error = str(e)
                    names[k] = None
                sc["beat_videos"] = names
                sc.update(clip_state="READY" if any(names) else "GENERATING")
                self.store.save(job)
            sc["clip_state"] = "READY"
        made = sum(1 for i in indices for n in scenes[i].get("beat_videos") or [] if n)
        if failed and not made:
            raise StageFailed(f"AI video clips failed - {last_error}")
        if failed:
            job.setdefault("warnings", []).append(f"{failed} line clip(s) failed and use a moving still instead")
        job["providers"]["clips"] = (job["providers"].get("clips", video.id).rstrip(")") +
                                     f", {made} line clips{f', {failed} failed' if failed else ''})")
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
                speaks = getattr(voice, "lang", "en")
                if speaks != "en":
                    # a Hindi (or other language) narrator: the standard voice of that language
                    fallback = {"hi": "hm_omega" if fallback[1:2] == "m" else "hf_alpha"}.get(speaks, fallback)
                elif fallback[:1] not in ("a", "b"):
                    # a timbre borrowed from another language (Indian English from a Hindi voice): the standard voice
                    # must still speak English
                    fallback = "am_onyx" if fallback[1:2] == "m" else "af_heart"
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
            mood = shot.get("emotion", "")
            if hasattr(voice, "mood"):
                voice.mood = mood          # human-like voice: more intensity on shocks, calmer on set-up
            said = director.spoken_text(shot["narration"], spec.pronounce)   # the creator's pronunciation list
            if profile.provider == "chatterbox":
                said = speech.speakable(said, getattr(voice, "lang", "en"))   # ₹13 crore, 40%, ED said in full
            key = _key(voice.id, profile.speed, said, mood if hasattr(voice, "mood") else "")
            try:
                src = self._cached("voice", key, ".wav", lambda p: voice.synthesize(said, p), verify.wav)
                dst = jdir / f"scene_{sc['index'] + 1:02d}_{_key(key, spec.voice_speed)[:8]}.wav"
                if sc.get("narration") and sc["narration"] != dst.name:
                    (jdir / sc["narration"]).unlink(missing_ok=True)
                render.to_pcm(src, dst, cancel, speed=spec.voice_speed)
                sc.update(voice_state="READY", narration=dst.name, narration_s=round(verify.wav(dst), 3))
            except (ProviderError, MediaError) as e:
                sc.update(voice_state="FAILED", error=f"narration: {e}")
                self.store.save(job)
                raise StageFailed(f"scene {sc['index'] + 1} narration failed - {e}") from e
            self.store.save(job)
        if profile.provider == "chatterbox":
            providers.unload_voice(self.cfg.chatterbox_url)   # its GPU memory goes back to the picture models

    def _timings(self, job: dict) -> list[float]:
        auto = self._spec(job).auto_edit
        out = []
        shots = job["plan"]["scenes"]
        for i, (sc, shot) in enumerate(zip(job["scenes"], shots)):
            natural = max(MIN_SCENE_S, sc["narration_s"] + SCENE_GAP_S + (min(MAX_HOLD_S, shot.get("hold", 0.0)) if auto else 0.0))
            if auto and i + 1 < len(shots) and shots[i + 1].get("emotion") in REVEAL_EMOTIONS:
                natural += REVEAL_PAUSE_S   # a beat of silence before the twist lands
            if i == len(shots) - 1:
                # let the last line land: the closing picture holds after the final word, then the video fades out
                natural += ENDING_HOLD_S[0] if self._spec(job).aspect == "9:16" else ENDING_HOLD_S[1]
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
                if sc.get("voice_source") != "asset":
                    # Captions show the script's own words and spelling (names, respelled words, numbers);
                    # Whisper only supplies the timing. How closely it heard the script is kept for the final check.
                    ws, sc["asr_match"] = cap.script_spelling(ws, shot["narration"])
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
            if not (chosen in render.TRANSITIONS and (spec.auto_edit or shot.get("transition_locked"))):
                chosen = t.transitions[i % len(t.transitions)]
            if spec.style in EDITORIAL_STYLES and not shot.get("transition_locked"):
                # Paper cut-outs slide and wipe; they don't dissolve.
                chosen = {"fade": "slide", "dissolve": "wipe", "dip": "cut", "zoom": "wipe", "reveal": "wipe",
                          "flash": "whip"}.get(chosen, chosen)
            return chosen

        def line_videos(sc: dict) -> list:
            if not (use_video and sc.get("ai_video", True) and spec.fast_cuts):
                return []
            return [jdir / n if n and (jdir / n).is_file() else None for n in sc.get("beat_videos") or []]

        def clip_for(sc: dict) -> Path | None:
            # Imported clips are always used; generated clips only in AI video mode.
            if sc.get("clip_source") != "asset" and any(line_videos(sc)):
                return None                                      # per-line clips are cut on the beats below
            if sc.get("clip") and ((use_video and sc.get("ai_video", True)) or sc.get("clip_source") == "asset"):
                return jdir / sc["clip"]
            return None

        clips, firsts = [], []   # firsts[i]: index in clips of scene i's opening shot
        charted: set[tuple[int, int]] = set()   # (scene, beat) shown as an animated chart
        stepped_files: set[Path] = set()         # drawn graphics, played "on twos" (12 fps) like hand-made animation
        chart_files: set[Path] = set()
        for i, (sc, shot, d) in enumerate(zip(job["scenes"], shots, timings)):
            firsts.append(len(clips))
            video = clip_for(sc)
            beats = [b for b in (shot.get("beats") or [])] if spec.fast_cuts and video is None else []
            extra = list(sc.get("beat_images") or [])
            stock_clips = [jdir / n if n and (jdir / n).is_file() else None for n in (sc.get("beat_clips") or [])]
            stock_clips += [None] * (len(beats) - len(stock_clips))
            for k, v in enumerate(line_videos(sc)[: len(beats)]):
                stock_clips[k] = stock_clips[k] or v          # real footage first, else the line's AI clip
            graphic = any(b.get("chart") or b.get("draw") or b.get("bubble") or b.get("extra") for b in beats)
            if beats and sc.get("image_source") != "asset" and (graphic or len(beats) >= 2 and (
                    any(n and (jdir / n).is_file() for n in extra) or any(stock_clips))):
                # Cut on the beat: each phrase gets screen time in proportion to its words, so the picture
                # changes exactly when the narration moves on.
                images = [jdir / sc["image"]] + [jdir / n if n and (jdir / n).is_file() else None for n in extra]
                images += [None] * (len(beats) - len(images))
                lengths = _beat_lengths([b["text"] for b in beats], sc.get("word_starts") or [], d, sc.get("narration_s"))
                for k, length in enumerate(lengths):
                    chart = self._chart_clip(spec, beats[k], length, (w, h), work, job)
                    if chart is not None:
                        stock_clips[k] = chart          # the animated graphic shows the number instead of a picture
                        charted.add((i, k))
                        stepped_files.add(chart)
                        chart_files.add(chart)
                cams = ["slow push in", "pull back", "pan left", "pan right"]
                merged = set()
                for k, length in enumerate(lengths):
                    if k in merged:
                        continue
                    if k and images[k] is None and stock_clips[k] is None:   # nothing for this beat: hold the last shot
                        clips[-1].duration += length
                        continue
                    cam = shot.get("camera", "") if k == 0 else cams[(i + k) % 4]
                    if spec.auto_edit and (beats[k].get("emotion") or shot.get("emotion", "")).lower() in SHOCK_EMOTIONS:
                        cam = "punch"   # a smooth zoom that lands - never a shaky camera
                    extra_k = beats[k].get("extra") or {}
                    still, video_k = images[k] or images[0], stock_clips[k]
                    if extra_k.get("split") and k + 1 < len(beats) and video_k is None and stock_clips[k + 1] is None \
                            and images[k + 1] is not None:
                        # split screen: this picture and the next side by side, held for both phrases
                        left_l, _, right_l = str(extra_k["split"]).partition("|")
                        try:
                            still = layout.split(still, images[k + 1], (left_l, right_l),
                                                 "desk" if spec.style in DESK_STYLES else "paper", w, h, work / "layout")
                            length += lengths[k + 1]
                            merged.add(k + 1)
                            cam = "static"
                        except (MediaError, OSError):
                            pass
                    clip = render.Clip(still, length, cam, transition(i, shot) if k == 0 else "cut", video_k)
                    clip.beat, clip.beat_data, clip.beat_len = (i, k), beats[k], length
                    chosen_t = str(extra_k.get("transition") or "").strip().lower()
                    if chosen_t in render.TRANSITIONS:
                        clip.transition = chosen_t                    # the writer's chosen cut into this line
                    elif extra_k.get("chapter") and spec.style in EDITORIAL_STYLES:
                        clip.transition = "tear"                      # a new part tears the page away
                    elif extra_k.get("statement"):
                        clip.transition = "dip"                       # cut to dark for the big line
                    if extra_k.get("archive"):
                        clip.grade = "archive"          # a history line: old-film look
                    clips.append(clip)
            else:
                cam = shot.get("camera", "")
                if spec.auto_edit and video is None and shot.get("emotion", "").lower() in SHOCK_EMOTIONS:
                    cam = "punch"
                clips.append(render.Clip(jdir / sc["image"], d, cam, transition(i, shot), video))
        for c in clips:
            if c.video is not None and c.video in stepped_files and spec.style in EDITORIAL_STYLES:
                c.stepped = True
        end_s = 0.0
        brand_kit = spec.brand or {}
        if w > h and total > 90 and spec.style in EDITORIAL_STYLES:
            # YouTube end screen: the last 12 s laid out for its "next video" and subscribe elements
            end_s = 12.0
            line = brand_kit.get("outro_text") or "What should we explain next?"
            try:
                card = cards.render("endscreen", f"{brand_kit.get('name', '')} | {line}",
                                    "investigative" if spec.style in DESK_STYLES else "editorial", w, h,
                                    end_s + render.TRANSITION_S, work / "endscreen.mp4", work)
                clips.append(render.Clip(clips[-1].image, end_s, "static", "fade", card))
                timings = list(timings)
                total += end_s
            except MediaError:
                end_s = 0.0
        # Drawn looks: whiteboard shots are drawn on one by one; line-art styles open each scene as a sketch.
        if spec.style == "doodle":
            for c in clips:
                c.reveal = "draw"
        elif spec.style in ("explainer_2d", "comic", "noir_graphic"):
            for j in firsts:
                clips[j].reveal = "sketch"
        for c in clips:
            if c.video is not None:
                c.video_duration = ff.duration(c.video)
        if spec.style in EDITORIAL_STYLES:
            self._lay_out(clips, chart_files, spec.style, w, h, work, cancel, firsts)
        tracked = self._attach_marks(clips, spec, t, w, h, work) if spec.fast_cuts else set()

        heads = [clips[j] for j in firsts]   # one per scene, for scene-level bookkeeping below
        if use_video and any(c.video is None and sc.get("ai_video", True) and not sc.get("beat_videos")
                             for c, sc in zip(heads, job["scenes"])):
            raise StageFailed("AI video mode but a chosen scene has no clip")

        plan = job["plan"]
        overlays, start = [], 0.0
        graphics: list[tuple[float, str]] = []   # (start, kind) of each full-frame graphic, for sound design
        if plan.get("hook"):
            overlays.append(cap.Overlay(0.0, min(3.0, timings[0]), plan["hook"], "Hook"))
        for i, (shot, slot) in enumerate(zip(shots, timings)):
            if shot.get("overlay") and i > 0:
                overlays.append(cap.Overlay(start + 0.3, start + slot - 0.2, shot["overlay"], "Callout"))
            beats = shot.get("beats") or []
            if spec.fast_cuts and any(b.get("overlay") or b.get("draw") or b.get("bubble") or b.get("extra") or b.get("chart")
                                      for b in beats):
                # The writer's on-screen text appears exactly while its line is spoken.
                at = start
                for k, (b, length) in enumerate(zip(beats, _beat_lengths([b["text"] for b in beats],
                                                                         job["scenes"][i].get("word_starts") or [], slot,
                                                                         job["scenes"][i].get("narration_s")))):
                    begin = at + 0.1
                    if plan.get("hook") and begin < min(3.0, timings[0]):
                        begin = min(3.0, timings[0])           # after the opening hook text, not on top of it
                    if b.get("overlay") and begin < at + length - 0.4 and (i, k) not in charted:
                        overlays.append(cap.Overlay(begin, at + max(0.6, length - 0.1), b["overlay"], "Callout"))
                    extras = b.get("extra") or {}
                    if (i, k) in charted:
                        graphics.append((at, next((g for g in director.FULL_FRAME if extras.get(g)), "chart")))
                    elif extras.get("split"):
                        graphics.append((at, "split"))
                    if extras.get("big") and (i, k) not in charted and length > 0.5:
                        overlays.append(cap.Overlay(at + 0.08, at + min(length, 1.8) - 0.05, extras["big"], "Big"))
                    if extras.get("cite") and length > 0.6:
                        overlays.append(cap.Overlay(at + 0.3, at + length - 0.05, extras["cite"], "Cite"))
                    if extras.get("place") and (i, k) not in charted and length > 0.8:
                        overlays.append(cap.Overlay(at + 0.2, at + min(length, 4.0) - 0.05, extras["place"], "Place"))
                    if (i, k) not in charted and (i, k) not in tracked and length > 0.8:
                        # The writer's pen marks and bubbles: drawn on once the picture has landed.
                        if b.get("draw"):
                            overlays.append(cap.Overlay(at + 0.25, at + length - 0.05, b["draw"], "Draw"))
                        if b.get("bubble"):
                            kind, _, said = b["bubble"].partition(":")
                            overlays.append(cap.Overlay(at + 0.15, at + length - 0.05, said,
                                                        "Think" if kind == "think" else "Bubble"))
                    at += length
            start += slot
        brand = spec.brand or {}
        cta = brand.get("outro_text") or plan.get("cta")
        if not brand.get("outro_text") and re.fullmatch(r"\W*(stay informed|learn more|subscribe( now)?|like and subscribe|"
                                                       r"follow( for more)?|watch more|find out more)\W*", cta or "", re.I):
            # a generic call to action adds nothing: name the channel, or leave the last picture clean
            cta = f"Follow {brand['name']}" if brand.get("name") else ""
        if cta:
            overlays.append(cap.Overlay(max(0.0, total - end_s - 3.0), total - end_s, cta, "CTA"))
        if brand.get("intro_text"):
            overlays.append(cap.Overlay(0.0, min(2.5, total), brand["intro_text"], "Brand"))
        if brand.get("name") and spec.style in EDITORIAL_STYLES and total > 8:
            overlays.append(cap.Overlay(max(0.0, total - end_s - 3.2), total - end_s, brand["name"], "Sting"))   # sign-off

        at_c = 0.0
        for c in clips:
            if c.camera == "slidein":
                graphics.append((at_c, "slide"))
            at_c += c.duration
        graphics.sort()
        sfx_hits: list[tuple[Path, float, float]] = []
        if spec.sfx:
            from .media import sfx_builtin
            bank = sfx.SfxBank.load(self.cfg.sfx_dir, [self.library.assets.path(a) for a in self.library.assets.list("sfx")]
                                    + sfx_builtin.ensure(self.cfg.data_dir / "sfx_builtin"))
            sfx_hits = sfx.place(bank, [c.transition for c in heads], timings,
                                 [(o.start, o.style) for o in overlays if spec.captions], job["id"])
            sfx_hits = sorted(sfx_hits + sfx.graphic_cues(bank, graphics, job["id"]), key=lambda x: x[1])
            job["providers"]["sfx"] = f"{len(sfx_hits)} cues from {bank.describe()}" if bank.any() else "none (no SFX folder or SFX assets)"
        else:
            job["providers"]["sfx"] = "off"

        narr = work / "narration.wav"
        render.narration_track([jdir / sc["narration"] for sc in job["scenes"]], timings, tail, narr)
        music = Path(job["music_track"]) if job.get("music_track") else None
        if music is not None and not music.is_file():
            raise StageFailed(f"music track disappeared: {music}")
        chapters = [at for at, kind in graphics if kind == "chapter"]
        if music is not None and len(chapters) >= 2 and str(music).startswith(str(self.cfg.music_dir or "\0")):
            # Long form: each part gets its own track from the library, crossfading at the chapter card, so the
            # score moves with the story instead of one loop under twenty minutes.
            mood = job["plan"].get("music_mood") or TEMPLATES[spec.template].music_mood
            tracks = [music]
            for n in range(1, len(chapters) + 8):
                if len(tracks) > len(chapters):
                    break
                pick = render.pick_music(self.cfg.music_dir, mood, f"{job['id']}:part{n}")
                if pick is not None and pick not in tracks:
                    tracks.append(pick)
            if len(tracks) >= 2:
                scored = work / "music_parts.wav"
                render.chapter_music(tracks, chapters, total, scored, cancel)
                music = scored
                job["providers"]["music"] = f"{len(tracks)} tracks, changing at chapters"
        mixed = work / "audio.wav"
        # the music steps back under chapter cards and big statements (a beat of near-silence before the next part)
        dips = [(at - 0.1, at + 1.4) for at, kind in graphics if kind in ("chapter", "statement")]
        render.mix_audio(narr, music, total, mixed, cancel, sfx_hits, dips)

        ass = None
        if spec.captions:
            words = [Word(**d) for d in json.loads((jdir / "words.json").read_text())]
            cues = cap.group(words, min(3, t.words_per_caption))   # 1-3 words at a time: easy to read at a glance
            ass = work / "captions.ass"
            emphasis = {wd for s in shots for wd in s.get("emphasis", [])} if spec.auto_edit else set()
            cap.write_ass(ass, w, h, t.caption_scale, t.caption_position, cues, overlays, emphasis,
                          brand.get("caption_color", ""), brand.get("highlight_color", ""),
                          CALLOUT_LOOKS.get(spec.style, ""))

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
                a = None   # e.g. a new pod: the logo lived on the old one. Render without it rather than fail.
                job["providers"]["brand"] = "no logo (not on this pod - upload it again and pick it in Brand kit)"
            if a is not None and a["kind"] != "image":
                raise StageFailed("the brand logo must be an image asset")
            if a is not None:
                logo = (self.library.assets.path(a), brand.get("logo_position", "top-right"), brand.get("logo_opacity", 0.85))
                job["providers"]["brand"] = f"logo {a['name']} ({logo[1]})"
        look = re.sub(r"[^a-z]", "", spec.visual_direction.lower())
        grade = ("bw" if "blackandwhite" in look or "monochrome" in look else "film") if spec.film_grade else ""
        if spec.film_grade and spec.style in EDITORIAL_STYLES and spec.style != MIX_STYLE:
            grade = "paper"     # Studio mix keeps the film grade: most of its pictures fill the frame
        expected = render.render_video(clips, mixed, ass, w, h, out, work, cancel, logo, grade=grade)
        job["render"] = {"file": "work/render.mp4", "expected_s": round(expected, 3), "width": w, "height": h}

    def _lay_out(self, clips: list, chart_files: set, style: str, w: int, h: int, work: Path, cancel,
                 firsts: list[int] | None = None) -> None:
        """Explainer looks: each still becomes a finished frame - its subject cut out with a white sticker edge on
        paper (or a desk), or a tilted bordered print when it is a whole scene - and footage plays framed on the
        same backdrop. Charts already are full-frame graphics."""
        kind = "desk" if style in DESK_STYLES else "paper"
        mix = style == MIX_STYLE        # Studio mix: only the lines given a cut-out look are laid out; footage fills the frame
        lay = work / "layout"
        backdrop = layout.backdrop(kind, w, h, lay, cancel)
        model = self.cfg.data_dir / "models" / "isnet-general-use.onnx"   # downloaded in the background by setup
        for c in clips:
            if c.video is not None and c.video not in chart_files and not mix:
                c.backdrop = backdrop
        # Scenes are laid out in parallel; inside a scene the stills build up like photos on a desk: each new one
        # lands left or right of the last and partly covers it (widescreen), then the pile starts again.
        bounds = sorted(set([0] + list(firsts or []))) + [len(clips)]
        groups = [list(range(a, b)) for a, b in zip(bounds, bounds[1:]) if b > a]
        wide = w > h
        slots = ("center", "left", "right")

        def lay_scene(idxs: list[int]) -> list[tuple[int, Path]]:
            out, under, depth = [], None, 0
            for n, idx in enumerate(idxs):
                c = clips[idx]
                if c.video is not None or c.image.name.startswith("split_"):
                    under, depth = None, 0           # footage, a graphic or a split screen clears the desk
                    continue
                c_kind = kind
                if mix:
                    beat_look = str((getattr(c, "beat_data", None) or {}).get("look") or "")
                    if beat_look not in CUTOUT_LOOKS:
                        under, depth = None, 0       # a full-frame photo look: the picture stays as it is
                        continue
                    c_kind = "desk" if beat_look == "investigative" else "paper"
                if cancel.is_set():
                    raise Cancelled()
                slot = slots[depth % 3] if (wide and depth) else ("center" if not n % 2 else ("left", "right")[n // 2 % 2])
                cut = layout.cutout(c.image, lay, model)
                look = str(((getattr(c, "beat_data", None) or {}).get("extra") or {}).get("treat") or "")
                src_img = c.image
                if look:
                    # the writer's print look: duotone or halftone, applied to the cut-out (or the whole picture)
                    if cut is not None:
                        cut = layout.treat(cut, look, c_kind, lay)
                    else:
                        src_img = layout.treat(c.image, look, c_kind, lay)
                frame = layout.compose(src_img, c_kind, idx, w, h, lay, cut, cancel,
                                       under=under if wide and depth else None, slot=slot)
                if c.camera != "punch":
                    # the first photo of a scene slides in Johnny Harris-style; the rest land and drift
                    c.camera = "slidein" if n == 0 and cut is not None else "settle"
                c.layers = layout.layers(frame)      # 2.5D: the cut-out moves over the desk
                out.append((idx, frame))
                under, depth = (frame, depth + 1) if depth < 2 else (None, 0)
            return out

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            for laid in pool.map(lay_scene, groups):
                for idx, frame in laid:
                    clips[idx].image = frame

    def _attach_marks(self, clips: list, spec, t, w: int, h: int, work: Path) -> set:
        """Pen marks and bubbles are drawn on the shot itself (not over the finished video), so they move with the
        picture: through a cut-out's push-in, or along with the footage's own motion. Returns the beats handled."""
        done: set = set()
        look = CALLOUT_LOOKS.get(spec.style, "")
        for c in clips:
            b, length = getattr(c, "beat_data", None), getattr(c, "beat_len", 0.0)
            if not b or length <= 0.8 or not (b.get("draw") or b.get("bubble")) or _covered(b):
                continue
            if b.get("draw") and b.get("overlay"):
                continue             # the pen circles the line's Text: box - drawn with the captions, which know where
            items = []
            if b.get("draw"):
                # a circle or arrow needs a subject in a known place: a cut-out on paper, or a real photo of the named
                # person, framed centrally. On anything else it would circle a random spot - keep only verdict marks
                subject = bool(getattr(c, "layers", None)) or "_photo" in str(getattr(c, "image", "") or "")
                kinds = [k.strip() for k in b["draw"].replace("+", ",").split(",") if k.strip()]
                if not subject:
                    kinds = [k for k in kinds if k not in ("circle", "box", "underline", "arrow")]
                if kinds:
                    items.append(cap.Overlay(0.25, length - 0.05, "subject:" + ", ".join(kinds), "Draw"))
                elif not b.get("bubble"):
                    done.add(c.beat)
                    continue
            if b.get("bubble"):
                kind, _, said = b["bubble"].partition(":")
                items.append(cap.Overlay(0.15, length - 0.05, said, "Think" if kind == "think" else "Bubble"))
            ass = work / f"marks_{hashlib.sha256(repr([(o.start, o.end, o.text, o.style) for o in items]).encode() + str((w, h, look)).encode()).hexdigest()[:16]}.ass"
            if not ass.is_file():
                cap.write_ass(ass, w, h, t.caption_scale, t.caption_position, [], items, set(), "", "", look)
            if c.video is not None:
                box = layout.video_box(w, h) if c.backdrop is not None else (w, h)
                c.track = render.track_motion(c.video, length, box)
            c.marks = ass
            done.add(c.beat)
        return done

    def _article_shot(self, spec, beat: dict, size: tuple[int, int], seconds: float, work: Path, job: dict | None):
        """An Article: line as the real web page: a screenshot of the cited article (matched to the headline in
        the script's Source: links), held up with a SOURCE tag and a slow push-in. None: draw the headline card."""
        if not self.cfg.free_stock:
            return None
        from .providers import news_media
        headline, _, source = str((beat.get("extra") or {}).get("article") or "").partition("|")
        publisher = source.split(",")[0].strip()
        links = news_media.source_links(str((spec.publish or {}).get("source") or ""))
        mine = (job or {}).setdefault("shot_for", {}) if job is not None else {}
        others = {u for h, u in mine.items() if h != headline.strip()}
        # the headline must really be that article's (most of its words in the link), and each page is shown once
        link = news_media.find_link(headline, links, publisher, min_share=0.4, skip=others) if headline.strip() else None
        if link is None:
            return None
        shot = news_media.screenshot(link["url"], self.cfg.cache_dir / "news")
        if shot is None or not self._fresh_print(job, shot, link["url"], within=2):
            return None
        if job is not None:
            mine[headline.strip()] = link["url"]
        key = hashlib.sha256(f"{link['url']}|{size}|{seconds}".encode()).hexdigest()[:16]
        try:
            frame = news_media.framed(shot, work / f"article_{key}.png", size[0], size[1], publisher or news_media.host_label(link))
            clip = news_media.still_clip(frame, work / f"article_{key}.mp4", size[0], size[1], seconds)
        except (MediaError, OSError):
            return None
        if job is not None:
            credit = f"Screenshot: {publisher or news_media.host_label(link)} ({link['url']})"
            credits = job.setdefault("stock_credits", [])
            if credit not in credits:
                credits.append(credit)
        return clip

    def _chart_clip(self, spec, beat: dict, length: float, size: tuple[int, int], work: Path,
                    job: dict | None = None) -> Path | None:
        """An animated number graphic for a beat: the writer's Chart: line, or - in the editorial looks - a Text:
        line that compares figures ("£12 → £720", "48% vs 22%"). None when the beat has no chart."""
        theme = "investigative" if spec.style in DESK_STYLES else "editorial"
        seconds = round(length + render.TRANSITION_S + 0.2, 2)
        extra = beat.get("extra") or {}
        if not beat.get("chart"):
            # The writer's full-frame graphics: an animated map, a chapter card, a highlighted quote.
            if extra.get("article"):
                real = self._article_shot(spec, beat, size, seconds, work, job)
                if real is not None:
                    return real                     # the real web page; otherwise the drawn headline card below
            for kind in director.FULL_FRAME:
                if extra.get(kind):
                    out = work / f"{kind}_{hashlib.sha256(f'{extra[kind]}|{theme}|{size}|{seconds}'.encode()).hexdigest()[:16]}.mp4"
                    if out.is_file():
                        return out
                    try:
                        if kind == "object":
                            plan = objects.parse(extra[kind])
                            if plan is None:
                                continue
                            return objects.render(plan, theme, size[0], size[1], seconds, out, work)
                        if kind == "shade":
                            plan = maps.parse_shade(extra[kind])
                            if plan is None:
                                continue
                            return maps.render(plan, theme, size[0], size[1], seconds, out, work)
                        if kind in ("map", "globe"):
                            plan = maps.parse(extra[kind])
                            if plan is None:
                                continue          # a place the map doesn't know: keep the picture
                            if kind == "globe":
                                return globe.render(plan, theme, size[0], size[1], seconds, out, work)
                            return maps.render(plan, theme, size[0], size[1], seconds, out, work)
                        return cards.render(kind, extra[kind], theme, size[0], size[1], seconds, out, work,
                                            brand=(spec.brand or {}).get("name", ""))
                    except MediaError:
                        continue
        src = beat.get("chart") or ""
        auto = beat.get("overlay") or ""
        if not src and spec.style in EDITORIAL_STYLES and re.search(r"→|->|=|\bvs\b", auto, re.I):
            src = auto
        plan = charts.parse(src) if src else None
        if plan is None:
            return None
        out = work / f"chart_{hashlib.sha256(f'{src}|{theme}|{size}|{seconds}'.encode()).hexdigest()[:16]}.mp4"
        if not out.is_file():
            try:
                charts.render(plan, theme, size[0], size[1], seconds, out, work)
            except MediaError:
                return None                      # a chart that can't be drawn falls back to the picture
        return out

    def _verify(self, job: dict, cancel) -> None:
        jdir = self.store.dir(job["id"])
        r = job.get("render") or {}
        src = jdir / r.get("file", "work/render.mp4")
        report = verify.mp4(src, r["width"], r["height"], r["expected_s"])
        final = jdir / "creatorforge.mp4"
        src.replace(final)
        job["result"] = {"file": final.name, "verification": report, "title": job["plan"]["title"]}
        try:   # what a viewer would notice - reported, never blocking
            matches = [s["asr_match"] for s in job["scenes"] if isinstance(s.get("asr_match"), (int, float))]
            job["result"]["quality"] = quality.check(final, r["expected_s"], matches, render.TARGET_LUFS)
        except Exception as e:  # noqa: BLE001
            job["result"]["quality"] = {"passed": None, "checks": [], "warnings": [f"quality check skipped: {e}"]}


def clip_ref(ref: str) -> tuple[str, float]:
    """"delhi march @ 1:05" -> ("delhi march", 65.0). No time -> start at 0."""
    name, _, at = ref.partition("@")
    start = 0.0
    m = re.fullmatch(r"\s*(?:(\d+):)?(\d+(?:\.\d+)?)\s*s?\s*", at) if at else None
    if m:
        start = int(m.group(1) or 0) * 60 + float(m.group(2))
    return name.strip(), start


def find_asset(assets: list[dict], name: str) -> dict | None:
    """The video asset the writer named: exact name first (with or without its extension, any case), then one whose
    name contains every word they wrote."""
    def norm(t: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", re.sub(r"\.(mp4|mov|webm|mkv|m4v|avi)$", "", t.strip().lower())).strip()
    want = norm(name)
    if not want:
        return None
    for a in assets:
        if norm(a.get("name", "")) == want:
            return a
    words = want.split()
    hits = [a for a in assets if all(w in norm(a.get("name", "")).split() for w in words)]
    return hits[0] if len(hits) == 1 else None


def _greyscale(path: Path) -> bool:
    """A black-and-white (or sepia) photo: almost no colour saturation."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            hsv = im.convert("RGB").resize((64, 64)).convert("HSV")
            sat = [px[1] for px in hsv.getdata()]
        return sum(sat) / len(sat) < 22
    except (OSError, ValueError):
        return False


# Lines about news events: these get the cited article's own photo when one matches
_EVENT = re.compile(r"\b(protest\w*|march\w*|rall(?:y|ies)|demonstrat\w*|detain\w*|detention\w*|arrest\w*|crackdown|"
                    r"police|barricade\w*|court|hearing|verdict|bail|jail|custody|raid\w*|election|vote\w*|voter\w*|"
                    r"campaign\w*|speech|addressed|press conference|parliament|minister|leader\w*|founder|activist\w*|"
                    r"journalist\w*|reporter\w*|shutdown|internet)\b", re.I)
