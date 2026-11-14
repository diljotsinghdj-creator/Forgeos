"""Exact word timings with WhisperX (BSD-2-Clause): Whisper's word times are refined by forced alignment against a
wav2vec2 model of the language, so every caption word lights up on the syllable it is spoken.

WhisperX lives in its own Python environment (default /workspace/whisperx, or CF_WHISPERX_PYTHON) so its pinned
torch versions never touch the worker's image and video models. It runs as one subprocess for the whole video
(the alignment model loads once). Anything that goes wrong leaves Whisper's own timings in place."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from .base import Word

ALIGN_SCRIPT = r'''
import json, sys
import whisperx
job = json.load(open(sys.argv[1], encoding="utf-8"))
device = job.get("device") or "cuda"
models = {}
out = []
for item in job["items"]:
    lang = item["lang"]
    if lang not in models:
        try:
            models[lang] = whisperx.load_align_model(language_code=lang, device=device)
        except Exception:
            device = "cpu"
            models[lang] = whisperx.load_align_model(language_code=lang, device=device)
    model, meta = models[lang]
    audio = whisperx.load_audio(item["wav"])
    seg = [{"start": item["start"], "end": item["end"], "text": item["text"]}]
    try:
        r = whisperx.align(seg, model, meta, audio, device, return_char_alignments=False)
        words = [{"text": w.get("word", ""), "start": w.get("start"), "end": w.get("end")}
                 for s in r.get("segments", []) for w in s.get("words", [])]
    except Exception as e:
        words = {"error": str(e)[:200]}
    out.append(words)
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"))
'''


def python() -> str | None:
    for p in (os.environ.get("CF_WHISPERX_PYTHON", ""), "/workspace/whisperx/bin/python"):
        if p and Path(p).is_file():
            return p
    return None


def available() -> bool:
    return os.environ.get("CF_ALIGN", "1") != "0" and python() is not None


def lang_of(text: str) -> str:
    return "hi" if re.search(r"[ऀ-ॿ]", text) else "en"


def merge(original: list[Word], aligned) -> list[Word]:
    """Takes WhisperX's start/end for each word when it returned the same words in the same order; a word it could
    not place (no timestamp) keeps Whisper's. A mismatch keeps everything as it was."""
    if not isinstance(aligned, list) or len(aligned) != len(original):
        return original
    out = []
    for w, a in zip(original, aligned):
        s, e = a.get("start"), a.get("end")
        if isinstance(s, (int, float)) and isinstance(e, (int, float)) and e >= s:
            out.append(Word(w.text, float(s), float(e)))
        else:
            out.append(w)
    for i in range(1, len(out)):                        # never let a word start before the previous one
        if out[i].start < out[i - 1].start:
            return original
    return out


def refine(items: list[tuple[Path, list[Word]]], timeout: float = 1800) -> tuple[list[list[Word]], str]:
    """items: (scene audio, Whisper's words for it). Returns the refined words per scene and a short status."""
    py = python()
    if not py or not items:
        return [w for _, w in items], "whisper"
    jobs = [{"wav": str(wav), "lang": lang_of(" ".join(w.text for w in ws)), "text": " ".join(w.text for w in ws),
             "start": ws[0].start if ws else 0.0, "end": ws[-1].end if ws else 0.0} for wav, ws in items]
    with tempfile.TemporaryDirectory(prefix="cf_align_") as tmp:
        src, dst, script = Path(tmp) / "in.json", Path(tmp) / "out.json", Path(tmp) / "align.py"
        src.write_text(json.dumps({"items": jobs, "device": os.environ.get("CF_WHISPERX_DEVICE", "cuda")}),
                       encoding="utf-8")
        script.write_text(ALIGN_SCRIPT, encoding="utf-8")
        try:
            r = subprocess.run([py, str(script), str(src), str(dst)], capture_output=True, text=True, timeout=timeout)
            if r.returncode != 0 or not dst.is_file():
                return [w for _, w in items], f"whisper (WhisperX failed: {(r.stderr or '')[-160:]})"
            aligned = json.loads(dst.read_text(encoding="utf-8"))
        except (OSError, subprocess.TimeoutExpired, ValueError) as e:
            return [w for _, w in items], f"whisper (WhisperX failed: {str(e)[:120]})"
    out = [merge(ws, a) for (_, ws), a in zip(items, aligned)]
    n = sum(1 for (_, ws), o in zip(items, out) if o is not ws)
    return out, f"whisperx-aligned ({n}/{len(items)} scenes)"
