"""Local narration server around Chatterbox TTS (Resemble AI, MIT licence): natural, expressive speech and
zero-shot voice cloning from a short reference clip.

Runs in its own Python environment (its pinned torch/diffusers versions clash with the worker's), started by
cloud/setup_gpu.sh and called by providers.tts.ChatterboxVoice over 127.0.0.1. Standard library only, apart
from Chatterbox itself.

    POST /tts  {"text", "out", "ref" (optional wav path), "exaggeration", "cfg_weight"} -> writes a WAV to "out"
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
_lock = threading.Lock()
_load_lock = threading.Lock()


def model():
    global _model
    with _load_lock:   # the background preload and the first request must not load it twice
        if _model is None:
            _model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
    return _model


def chunks(text: str, limit: int = 280) -> list[str]:
    """Chatterbox is best on short passages: sentence groups of up to ~280 characters."""
    out, cur = [], ""
    for s in re.split(r"(?<=[.!?…])\s+", " ".join(text.split())):
        if cur and len(cur) + len(s) + 1 > limit:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return [c for c in out if re.search(r"\w", c)]


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
        if self.path != "/tts":
            return self._send(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            text, out = str(body.get("text", "")), str(body.get("out", ""))
            if not text.strip() or not out:
                return self._send(422, {"error": "text and out are required"})
            ref = body.get("ref") or None
            ex, cw = float(body.get("exaggeration", 0.5)), float(body.get("cfg_weight", 0.5))
            with _lock:
                m = model()
                pause = np.zeros(int(m.sr * 0.15), dtype=np.float32)
                parts = []
                for c in chunks(text):
                    wav = m.generate(c, audio_prompt_path=ref, exaggeration=ex, cfg_weight=cw)
                    parts += [wav.squeeze(0).detach().cpu().numpy().astype(np.float32), pause]
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
