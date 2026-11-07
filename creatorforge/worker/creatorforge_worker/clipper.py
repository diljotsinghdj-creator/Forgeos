"""Shorts Clipper: turns a long video (a finished production or an uploaded video) into vertical Shorts.

It reads the transcript, picks the strongest self-contained moments (the AI picks when a script model is
configured, otherwise a simple scorer), cuts them, reframes 16:9 to 9:16 with a blurred fill, burns in
captions, and verifies every clip."""
from __future__ import annotations

import json
import math
import re
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .media import captions as cap
from .media import ff, verify
from .providers.base import ProviderError, Word

SYSTEM = """You pick the best moments of a long video to post as YouTube Shorts / TikToks. SHORTS_CLIPPER
Each moment must make sense on its own, open with a strong line (a question, a surprising fact, a bold claim)
and end on a complete thought. Prefer moments with numbers, conflict, surprise or a clear payoff.
Return JSON only: {"clips":[{"start":3,"end":9,"title":"short catchy title","hook":"why it grabs attention"}]}
start and end are SENTENCE NUMBERS from the list (inclusive)."""


@dataclass
class Sentence:
    text: str
    start: float
    end: float


def sentences(words: list[Word]) -> list[Sentence]:
    out: list[Sentence] = []
    buf: list[Word] = []
    for i, w in enumerate(words):
        buf.append(w)
        gap = words[i + 1].start - w.end if i + 1 < len(words) else 9.0
        if re.search(r"[.!?]$", w.text) or gap > 0.8 or len(buf) >= 40:
            out.append(Sentence(" ".join(x.text for x in buf), buf[0].start, buf[-1].end))
            buf = []
    return out


def _score(s: list[Sentence]) -> float:
    text = " ".join(x.text for x in s).lower()
    return (2.0 * text.count("?") + 1.5 * len(re.findall(r"\d", text)) ** 0.5 +
            sum(text.count(w) for w in ("secret", "never", "nobody", "truth", "why", "how", "biggest", "first", "only")))


def pick(sents: list[Sentence], count: int, seconds: float, llm=None) -> list[dict]:
    """Returns [{start, end, title, hook}] in seconds."""
    if not sents:
        raise ValueError("the video has no speech to clip")
    total = sents[-1].end
    if llm is not None:
        listing = "\n".join(f"{i + 1}. [{s.start:.1f}-{s.end:.1f}s] {s.text}" for i, s in enumerate(sents))[:24000]
        user = f"TARGET: {count} clips, each about {seconds:.0f} seconds (15-60s)\nSENTENCES:\n{listing}"
        error = ""
        for _ in range(2):
            raw = llm.complete_json(SYSTEM, user if not error else f"{user}\n\nYour previous answer was invalid: {error}. JSON only.")
            try:
                m = re.search(r"\{.*\}", raw, re.S)
                picks = []
                for c in json.loads(m.group(0) if m else "{}").get("clips") or []:
                    a, b = int(c["start"]) - 1, int(c["end"]) - 1
                    if not (0 <= a <= b < len(sents)):
                        continue
                    st, en = sents[a].start, sents[b].end
                    if en - st < 8 or en - st > 75:
                        continue
                    picks.append({"start": round(st, 2), "end": round(en, 2), "title": str(c.get("title", ""))[:80],
                                  "hook": str(c.get("hook", ""))[:160]})
                if not picks:
                    raise ValueError("no usable clips")
                return _no_overlap(picks)[:count]
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
                error = str(e)
        raise ProviderError(f"the script model picked no usable clips twice: {error}")
    # No AI: windows that start on a sentence, scored by curiosity signals, spread over the video.
    windows = []
    for i in range(len(sents)):
        j = i
        while j + 1 < len(sents) and sents[j + 1].end - sents[i].start <= seconds:
            j += 1
        if sents[j].end - sents[i].start >= min(10.0, total * 0.5):
            windows.append((_score(sents[i:j + 1]) - 0.01 * i, i, j))
    windows.sort(reverse=True)
    picks = _no_overlap([{"start": round(sents[i].start, 2), "end": round(sents[j].end, 2),
                          "title": sents[i].text[:60], "hook": "auto-picked"} for _, i, j in windows])
    return sorted(picks[:count], key=lambda p: p["start"])


def _no_overlap(picks: list[dict]) -> list[dict]:
    kept: list[dict] = []
    for p in picks:
        if all(p["end"] <= k["start"] or p["start"] >= k["end"] for k in kept):
            kept.append(p)
    return kept


def render_clip(src: Path, start: float, end: float, words: list[Word], out: Path, work: Path,
                caption_color: str = "", highlight_color: str = "", cancel: threading.Event | None = None) -> dict:
    """Cuts [start, end] into a 1080x1920 Short: the video fitted to the width over a blurred, filled copy."""
    w, h = 1080, 1920
    dur = end - start
    inside = [Word(x.text, x.start - start, x.end - start) for x in words if x.start >= start - 0.05 and x.end <= end + 0.05]
    ass = work / f"{out.stem}.ass"
    cap.write_ass(ass, w, h, 0.05, 0.72, cap.group(inside, 3), [], set(), caption_color, highlight_color)
    graph = (f"[0:v]split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=24:2,"
             f"eq=brightness=-0.08[bg];[b]scale={w}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,"
             f"subtitles=filename={ass.name},format=yuv420p[v]")
    ff.run(["-ss", f"{start:.3f}", "-i", str(src), "-t", f"{dur:.3f}", "-filter_complex", graph, "-map", "[v]",
            "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-c:a", "aac",
            "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", str(out)], cancel, cwd=work)
    return verify.mp4(out, w, h, dur)


class ClipJobs:
    """Clip jobs run one at a time in the background and are stored as JSON next to their files."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def dir(self, cid: str) -> Path:
        if not cid.isalnum():
            raise KeyError(cid)
        return self.root / cid

    def load(self, cid: str) -> dict:
        p = self.dir(cid) / "clip.json"
        if not p.is_file():
            raise KeyError(cid)
        return json.loads(p.read_text())

    def save(self, job: dict) -> None:
        with self._lock:
            p = self.dir(job["id"]) / "clip.json"
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps(job, indent=1))
            tmp.replace(p)

    def all(self) -> list[dict]:
        out = []
        for p in sorted(self.root.glob("*/clip.json"), key=lambda p: -p.stat().st_mtime):
            try:
                out.append(json.loads(p.read_text()))
            except ValueError:
                continue
        return out

    def create(self, source: dict, count: int, seconds: float, brand: dict, owner: str = "") -> dict:
        cid = uuid.uuid4().hex[:12]
        self.dir(cid).mkdir(parents=True)
        job = {"id": cid, "created_at": time.time(), "status": "QUEUED", "message": "Queued", "error": None,
               "source": source, "count": count, "seconds": seconds, "brand": brand, "clips": [], "owner": owner}
        self.save(job)
        return job

    def run(self, cid: str, src: Path, words: list[Word], llm) -> None:
        job = self.load(cid)
        work = self.dir(cid)
        try:
            job.update(status="RUNNING", message="Choosing the best moments")
            self.save(job)
            picks = pick(sentences(words), job["count"], job["seconds"], llm)
            for n, p in enumerate(picks, 1):
                job["message"] = f"Cutting Short {n} of {len(picks)}"
                self.save(job)
                out = work / f"short_{n:02d}.mp4"
                report = render_clip(src, p["start"], p["end"], words, out, work,
                                     job["brand"].get("caption_color", ""), job["brand"].get("highlight_color", ""))
                job["clips"].append(dict(p, file=out.name, duration_s=report["duration_s"], index=n))
                self.save(job)
            job.update(status="READY", message=f"{len(picks)} Shorts ready")
        except Exception as e:  # noqa: BLE001 - a clip job never stays RUNNING
            job.update(status="FAILED", error=str(e), message="Failed")
        self.save(job)
