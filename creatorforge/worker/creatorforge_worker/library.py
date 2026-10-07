"""Character Library: reusable characters whose descriptions are injected into every prompt
they appear in, keeping visual identity consistent across scenes and productions."""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path


class CharacterStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read(self) -> list[dict]:
        if not self.path.is_file():
            return []
        return json.loads(self.path.read_text())

    def _write(self, items: list[dict]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, indent=1))
        os.replace(tmp, self.path)

    @staticmethod
    def _clean(d: dict) -> tuple[str, str]:
        name, desc = str(d.get("name", "")).strip()[:60], str(d.get("description", "")).strip()[:600]
        if not name or len(desc) < 5:
            raise ValueError("a character needs a name and a description of at least 5 characters")
        return name, desc

    def list(self) -> list[dict]:
        with self._lock:
            return self._read()

    def get_many(self, ids: list[str]) -> list[dict]:
        items = {c["id"]: c for c in self.list()}
        missing = [i for i in ids if i not in items]
        if missing:
            raise ValueError(f"unknown character id(s): {', '.join(missing)}")
        return [items[i] for i in ids]

    def create(self, d: dict) -> dict:
        name, desc = self._clean(d)
        with self._lock:
            items = self._read()
            if any(c["name"].lower() == name.lower() for c in items):
                raise ValueError(f"a character named '{name}' already exists")
            c = {"id": uuid.uuid4().hex[:12], "name": name, "description": desc, "created_at": time.time()}
            items.append(c)
            self._write(items)
            return c

    def update(self, cid: str, d: dict) -> dict:
        name, desc = self._clean(d)
        with self._lock:
            items = self._read()
            for c in items:
                if c["id"] == cid:
                    if any(o["id"] != cid and o["name"].lower() == name.lower() for o in items):
                        raise ValueError(f"a character named '{name}' already exists")
                    c.update(name=name, description=desc)
                    self._write(items)
                    return c
        raise KeyError(cid)

    def delete(self, cid: str) -> None:
        with self._lock:
            items = self._read()
            kept = [c for c in items if c["id"] != cid]
            if len(kept) == len(items):
                raise KeyError(cid)
            self._write(kept)


class VoiceStore:
    """Voice Profiles saved from the app (in addition to read-only ones from CF_VOICES)."""
    PROVIDERS = ("piper", "kokoro", "chatterbox")

    def __init__(self, path: Path, allow_mock: bool = False):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.allow_mock = allow_mock

    def _read(self) -> list[dict]:
        return json.loads(self.path.read_text()) if self.path.is_file() else []

    def _write(self, items: list[dict]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, indent=1))
        os.replace(tmp, self.path)

    def _clean(self, d: dict) -> dict:
        name = str(d.get("name", "")).strip()[:60]
        provider = str(d.get("provider", "")).strip()
        voice = str(d.get("voice", "")).strip()[:300]
        try:
            speed = float(d.get("speed", 1.0))
        except (TypeError, ValueError):
            raise ValueError("speed must be a number") from None
        allowed = self.PROVIDERS + (("mock",) if self.allow_mock else ())
        if not name:
            raise ValueError("a voice profile needs a name")
        if provider not in allowed:
            raise ValueError(f"provider must be one of: {', '.join(allowed)}")
        if provider != "mock" and not voice:
            raise ValueError("voice is required (Piper: path to a .onnx model on the worker; Kokoro: a voice id like af_heart)")
        if provider == "piper" and not Path(voice).is_file():
            raise ValueError(f"Piper model not found on the worker: {voice}")
        if provider == "chatterbox" and not (voice == "default" or voice.startswith(("kokoro:", "asset:"))):
            raise ValueError("Chatterbox voice must be 'default', 'kokoro:<voice id>' or 'asset:<voice sample id>'")
        style = str(d.get("style", "") or "")
        if style not in ("", "documentary", "natural", "calm", "energetic"):
            raise ValueError("style must be documentary, natural, calm or energetic")
        if not 0.5 <= speed <= 2.0:
            raise ValueError("speed must be between 0.5 and 2.0")
        return {"name": name, "provider": provider, "voice": voice, "speed": round(speed, 2),
                "lang": str(d.get("lang", "a") or "a")[:5], "style": style}

    def list(self) -> list[dict]:
        with self._lock:
            return self._read()

    def create(self, d: dict, reserved: set[str]) -> dict:
        clean = self._clean(d)
        with self._lock:
            items = self._read()
            v = {"id": "v-" + uuid.uuid4().hex[:8], **clean, "created_at": time.time()}
            if v["id"] in reserved:
                raise ValueError("id clash, try again")
            items.append(v)
            self._write(items)
            return v

    def update(self, vid: str, d: dict) -> dict:
        clean = self._clean(d)
        with self._lock:
            items = self._read()
            for v in items:
                if v["id"] == vid:
                    v.update(clean)
                    self._write(items)
                    return v
        raise KeyError(vid)

    def delete(self, vid: str) -> None:
        with self._lock:
            items = self._read()
            kept = [v for v in items if v["id"] != vid]
            if len(kept) == len(items):
                raise KeyError(vid)
            self._write(kept)


ASSET_KINDS = ("image", "video", "audio", "music", "sfx")


class AssetStore:
    """Asset Library: files you import (images, clips, voice-overs, music, sound effects)."""

    def __init__(self, root: Path):
        self.root = root
        self.files = root / "files"
        self.files.mkdir(parents=True, exist_ok=True)
        self.index = root / "assets.json"
        self._lock = threading.Lock()

    def _read(self) -> list[dict]:
        return json.loads(self.index.read_text()) if self.index.is_file() else []

    def _write(self, items: list[dict]) -> None:
        tmp = self.index.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, indent=1))
        os.replace(tmp, self.index)

    def list(self, kind: str | None = None) -> list[dict]:
        with self._lock:
            items = self._read()
        return [a for a in items if not kind or a["kind"] == kind]

    def get(self, aid: str) -> dict:
        for a in self.list():
            if a["id"] == aid:
                return a
        raise KeyError(aid)

    def path(self, a: dict) -> Path:
        return self.files / a["file"]

    def add(self, kind: str, name: str, tmp: Path, ext: str, check) -> dict:
        if kind not in ASSET_KINDS:
            raise ValueError(f"kind must be one of: {', '.join(ASSET_KINDS)}")
        info = check(tmp)  # raises MediaError on bad input
        aid = uuid.uuid4().hex[:12]
        dst = self.files / f"{aid}{ext}"
        os.replace(tmp, dst)
        a = {"id": aid, "kind": kind, "name": (name or f"{kind} {aid[:4]}")[:80], "file": dst.name,
             "bytes": dst.stat().st_size, "created_at": time.time(), **info}
        with self._lock:
            items = self._read()
            items.append(a)
            self._write(items)
        return a

    def rename(self, aid: str, name: str) -> dict:
        with self._lock:
            items = self._read()
            for a in items:
                if a["id"] == aid:
                    a["name"] = name.strip()[:80] or a["name"]
                    self._write(items)
                    return a
        raise KeyError(aid)

    def delete(self, aid: str) -> None:
        with self._lock:
            items = self._read()
            target = next((a for a in items if a["id"] == aid), None)
            if target is None:
                raise KeyError(aid)
            self._write([a for a in items if a["id"] != aid])
        (self.files / target["file"]).unlink(missing_ok=True)


class Library:
    def __init__(self, root: Path, allow_mock: bool = False):
        self.characters = CharacterStore(root / "characters.json")
        self.voices = VoiceStore(root / "voices.json", allow_mock)
        self.assets = AssetStore(root / "assets")
