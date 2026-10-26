"""Local narration server around Chatterbox TTS (Resemble AI, MIT licence): natural, expressive speech and
zero-shot voice cloning from a short reference clip.

Runs in its own Python environment (its pinned torch/diffusers versions clash with the worker's), started by
cloud/setup_gpu.sh and called by providers.tts.ChatterboxVoice over 127.0.0.1. Standard library only, apart
from Chatterbox itself.

    POST /tts  {"text", "out", "ref" (optional wav path), "exaggeration", "cfg_weight", "lang"} -> writes a WAV
               to "out". "lang" other than "en" (e.g. "hi" for Hindi) uses Chatterbox Multilingual (23 languages).
    GET  /health
"""
from __future__ import annotations

import json
import re
import sys
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import torch

try:  # Chatterbox's watermark helper (resemble-perth) is None when its optional deps don't load; that makes
    import perth  # ChatterboxTTS crash with "'NoneType' object is not callable". Fall back to a no-op watermark.
    if getattr(perth, "PerthImplicitWatermarker", None) is None:
        class _NoWatermark:
            def apply_watermark(self, wav, sample_rate=None, **_):
                return wav
        perth.PerthImplicitWatermarker = getattr(perth, "DummyWatermarker", None) or _NoWatermark
except ImportError:
    pass

from chatterbox.tts import ChatterboxTTS  # noqa: E402

_model = None
_mtl = None
_lock = threading.Lock()
_load_lock = threading.Lock()


def model():
    global _model
    with _load_lock:   # the background preload and the first request must not load it twice
        if _model is None:
            _model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
    return _model


def multilingual():
    """Chatterbox Multilingual, loaded the first time a non-English line is asked for (Hindi, Spanish, ...)."""
    global _mtl
    with _load_lock:
        if _mtl is None:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            _mtl = ChatterboxMultilingualTTS.from_pretrained(device=torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    return _mtl


def _pieces(s: str, limit: int) -> list[str]:
    """One sentence cut to fit: at commas/semicolons first, then at word boundaries (Chatterbox stops generating
    after ~40 s, so an over-long sentence would otherwise be cut off mid-word)."""
    if len(s) <= limit:
        return [s]
    out, cur = [], ""
    for part in re.split(r"(?<=[,;:])\s*", s):
        words = part.split() if len(part) > limit else [part]
        for w in words:
            if cur and len(cur) + len(w) + 1 > limit:
                out.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


def chunks(text: str, limit: int = 220) -> list[str]:
    """One piece per sentence (so each gets its own breath after it - longer after a question or a "..."), and an
    over-long sentence cut at commas or words: Chatterbox stops generating after ~40 s."""
    out = []
    # after ! ? … and a danda, even with no space; after a full stop only at a word gap and never inside "..."
    # or a number ("13.3", "U.S.")
    for sent in re.split(r"(?<=[!?…।॥])\s*|(?<=\.)(?!\.)\s+", " ".join(text.split())):
        out += _pieces(sent, limit)
    return [c for c in out if re.search(r"\w", c)]


def breath(chunk: str) -> float:
    """The pause after a piece, the way a narrator breathes: longer after a question or a trailing "...", a full
    stop (or danda) a natural beat, a comma-cut piece only a short one."""
    end = chunk.rstrip(" \"'”’)")
    if end.endswith(("...", "…")):
        return 0.6
    if end.endswith("?"):
        return 0.4
    if end.endswith("!"):
        return 0.32
    if end.endswith((".", "।", "॥")):
        return 0.26
    return 0.12


def unload() -> None:
    """Free the voice models' GPU memory so the image/video models get it (they reload on the next line)."""
    global _model, _mtl
    with _lock, _load_lock:
        _model = _mtl = None
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send(200, {"ok": True, "loaded": _model is not None})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if self.path == "/unload":
            unload()
            return self._send(200, {"ok": True})
        if self.path != "/tts":
            return self._send(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            text, out = str(body.get("text", "")), str(body.get("out", ""))
            if not text.strip() or not out:
                return self._send(422, {"error": "text and out are required"})
            ref = body.get("ref") or None
            ex, cw = float(body.get("exaggeration", 0.5)), float(body.get("cfg_weight", 0.5))
            lang = str(body.get("lang") or "en").lower()
            segs = body.get("segments") or [{"text": text, "exaggeration": ex, "cfg_weight": cw, "pause": 0.0}]
            with _lock:
                m = model() if lang == "en" else multilingual()
                parts = []
                for seg in segs:
                    sex = float(seg.get("exaggeration", ex))
                    scw = float(seg.get("cfg_weight", cw))
                    for c in chunks(str(seg.get("text", ""))):
                        if lang == "en":
                            wav = m.generate(c, audio_prompt_path=ref, exaggeration=sex, cfg_weight=scw)
                        else:
                            wav = m.generate(c, language_id=lang, audio_prompt_path=ref, exaggeration=sex, cfg_weight=scw)
                        parts += [wav.squeeze(0).detach().cpu().numpy().astype(np.float32),
                                  np.zeros(int(m.sr * breath(c)), dtype=np.float32)]
                    extra = min(1.5, max(0.0, float(seg.get("pause", 0.0))))
                    if extra:
                        parts.append(np.zeros(int(m.sr * extra), dtype=np.float32))
            if not parts:
                return self._send(422, {"error": "nothing to say"})
            pcm = (np.clip(np.concatenate(parts), -1, 1) * 32767).astype("<i2").tobytes()
            with wave.open(out, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(m.sr)
                w.writeframes(pcm)
            self._send(200, {"ok": True})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {e}"})

    def log_message(self, *args):  # keep the log quiet
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
    threading.Thread(target=model, daemon=True).start()   # load in the background so the first video isn't slow
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
