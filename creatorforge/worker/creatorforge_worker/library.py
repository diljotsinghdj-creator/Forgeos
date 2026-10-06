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
