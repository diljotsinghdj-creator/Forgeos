"""Visual match check: scores how well a picture shows what its line describes, with CLIP (ViT-B/32, ONNX, run by
onnxruntime - no PyTorch needed). The pipeline regenerates a picture that scores low and rejects stock footage or
photos that don't show the search. Models live in <data>/models/clip (downloaded in the background by setup);
without them every check passes, so a production never waits on this."""
from __future__ import annotations

import gzip
import html
import re
import threading
from functools import lru_cache
from pathlib import Path

MODEL_BASE = ("https://clip-as-service.s3.us-east-2.amazonaws.com/models-436c69702d61732d53657276696365/onnx/"
              "ViT-B-32")
VOCAB_URL = "https://raw.githubusercontent.com/openai/CLIP/main/clip/bpe_simple_vocab_16e6.txt.gz"
FILES = ("visual.onnx", "textual.onnx", "bpe_simple_vocab_16e6.txt.gz")

# Cosine similarity between a picture and its description, calibrated on a real render: pictures that showed their
# line scored 0.27-0.38 (coins stacked on a calendar, a hand past a wallet, a statement circled in red pen); ones that
# drifted scored 0.18-0.25 (a woman's face for "a map of Britain with coins", a woman for "a thumb over a phone").
GOOD = 0.26          # below: the picture is regenerated (best of up to three is kept)
POOR = 0.22          # below: stock footage/photos are rejected (an AI picture is used instead)

_MEAN = (0.48145466, 0.4578275, 0.40821073)
_STD = (0.26862954, 0.26130258, 0.27577711)


def available(models: Path) -> bool:
    return all((models / f).is_file() and (models / f).stat().st_size > 0 for f in FILES)


def _bytes_to_unicode() -> dict[int, str]:
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, (chr(c) for c in cs)))


class _Tokenizer:
    """CLIP's byte-level BPE (the open-source reference tokenizer, with the standard-library regex)."""

    _PAT = re.compile(r"<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|[^\W\d_]+|\d|[^\s\w]+|_", re.I)

    def __init__(self, vocab: Path):
        self.byte_encoder = _bytes_to_unicode()
        merges = gzip.open(vocab).read().decode("utf-8").split("\n")[1:49152 - 256 - 2 + 1]
        merges = [tuple(m.split()) for m in merges]
        words = list(self.byte_encoder.values())
        words += [w + "</w>" for w in words] + ["".join(m) for m in merges] + ["<|startoftext|>", "<|endoftext|>"]
        self.encoder = {w: i for i, w in enumerate(words)}
        self.ranks = {m: i for i, m in enumerate(merges)}
        self.sot, self.eot = self.encoder["<|startoftext|>"], self.encoder["<|endoftext|>"]

    @lru_cache(maxsize=4096)  # noqa: B019 - one tokenizer per process
    def _bpe(self, token: str) -> tuple[str, ...]:
        word = tuple(token[:-1]) + (token[-1] + "</w>",)
        while len(word) > 1:
            pairs = {(word[i], word[i + 1]) for i in range(len(word) - 1)}
            best = min(pairs, key=lambda p: self.ranks.get(p, 1e10))
            if best not in self.ranks:
                break
            out, i = [], 0
            while i < len(word):
                if i < len(word) - 1 and (word[i], word[i + 1]) == best:
                    out.append(word[i] + word[i + 1])
                    i += 2
                else:
                    out.append(word[i])
                    i += 1
            word = tuple(out)
        return word

    def encode(self, text: str, length: int = 77) -> list[int]:
        text = re.sub(r"\s+", " ", html.unescape(html.unescape(text))).strip().lower()
        ids = []
        for tok in self._PAT.findall(text):
            tok = "".join(self.byte_encoder[b] for b in tok.encode("utf-8"))
            ids += [self.encoder[t] for t in self._bpe(tok) if t in self.encoder]
        return [self.sot] + ids[: length - 2] + [self.eot]


class Matcher:
    def __init__(self, models: Path):
        import onnxruntime as ort
        gpu = [p for p in ("CUDAExecutionProvider",) if p in ort.get_available_providers()]
        providers = gpu + ["CPUExecutionProvider"]
        self.visual = ort.InferenceSession(str(models / "visual.onnx"), providers=providers)
        self.textual = ort.InferenceSession(str(models / "textual.onnx"), providers=providers)
        self.tok = _Tokenizer(models / "bpe_simple_vocab_16e6.txt.gz")
        self.lock = threading.Lock()

    def _image(self, path: Path):
        import numpy as np
        from PIL import Image
        with Image.open(path) as im:
            im = im.convert("RGB")
            w, h = im.size
            s = 224 / min(w, h)
            im = im.resize((max(224, round(w * s)), max(224, round(h * s))), Image.BICUBIC)
            w, h = im.size
            im = im.crop(((w - 224) // 2, (h - 224) // 2, (w - 224) // 2 + 224, (h - 224) // 2 + 224))
        x = (np.asarray(im, dtype=np.float32) / 255.0 - np.array(_MEAN, np.float32)) / np.array(_STD, np.float32)
        return x.transpose(2, 0, 1)[None]

    def score(self, image: Path, text: str) -> float:
        """Cosine similarity between the picture and the description (roughly 0.1 unrelated .. 0.35 exact)."""
        import numpy as np
        ids = self.tok.encode(text)
        input_ids = np.zeros((1, 77), np.int32)
        input_ids[0, : len(ids)] = ids
        mask = (input_ids != 0).astype(np.int32)
        with self.lock:
            v = self.visual.run(None, {"pixel_values": self._image(image)})[0][0]
            t = self.textual.run(None, {"input_ids": input_ids, "attention_mask": mask})[0][0]
        return float(np.dot(v, t) / (np.linalg.norm(v) * np.linalg.norm(t) + 1e-9))


_matchers: dict[str, Matcher] = {}
_build_lock = threading.Lock()


def matcher(models: Path) -> Matcher | None:
    """The shared matcher, or None when the models aren't on this machine (every check then passes)."""
    if not available(models):
        return None
    with _build_lock:
        if str(models) not in _matchers:
            try:
                _matchers[str(models)] = Matcher(models)
            except Exception:  # noqa: BLE001 - no onnxruntime / bad download: skip the check rather than fail
                return None
        return _matchers[str(models)]


def describe(visual: str) -> str:
    """The part of a Visual: line CLIP can judge: the subject, without camera words or our own style labels."""
    v = re.sub(r"\b(close[- ]?up|wide shot|medium shot|top[- ]down|overhead|slow(ly)?|camera|push(es)? in|pans?|"
               r"zoom(s|ing)?( in| out)?|text unreadable|unreadable|illustration|fictional)\b", "", visual, flags=re.I)
    return re.sub(r"\s+", " ", v).strip(" ,.")[:300] or visual[:300]
