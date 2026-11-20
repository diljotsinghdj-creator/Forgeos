"""Hosted-ready accounts: the worker owner (CF_WORKER_TOKEN) can hand out keys to creators and clients.

Each account has a role, a credit balance and usage. Productions remember their owner and accounts only
see their own work. Payments are not built in: the owner adds credits (for example after someone pays)."""
from __future__ import annotations

import contextvars
import json
import math
import os
import secrets
import threading
import time
from pathlib import Path

ROLES = ("creator", "client")
current: contextvars.ContextVar[dict | None] = contextvars.ContextVar("cf_account", default=None)


def cost(spec: dict) -> int:
    """Credits for one production: 1 per started 30 seconds of video, x2 with an AI-animated hook, x4 all-AI video."""
    if spec.get("script"):
        seconds = max(10, len(str(spec["script"]).split()) / 2.5)
    else:
        seconds = float(spec.get("duration_s") or 45)
    mult = 1
    if spec.get("motion") == "ai_video":
        mult = 4 if spec.get("ai_video_scenes", "all") == "all" else 2
    return max(1, math.ceil(seconds / 30)) * mult


class AccountStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read(self) -> list[dict]:
        return json.loads(self.path.read_text()) if self.path.is_file() else []

    def _write(self, items: list[dict]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, indent=1))
        os.replace(tmp, self.path)

    def any(self) -> bool:
        return bool(self._read())

    def list(self) -> list[dict]:
        with self._lock:
            return self._read()

    def by_key(self, key: str) -> dict | None:
        if not key:
            return None
        for a in self.list():
            if secrets.compare_digest(a["key"], key):
                return a
        return None

    def create(self, name: str, role: str, credits: int) -> dict:
        name = name.strip()[:60]
        if len(name) < 2:
            raise ValueError("give the account a name")
        if role not in ROLES:
            raise ValueError("role must be creator or client")
        a = {"id": secrets.token_hex(6), "name": name, "role": role, "key": "cfk_" + secrets.token_urlsafe(24),
             "credits": max(0, int(credits)), "used": 0, "created_at": time.time()}
        with self._lock:
            items = self._read()
            items.append(a)
            self._write(items)
        return a

    def update(self, aid: str, credits_delta: int = 0, name: str = "", role: str = "") -> dict:
        with self._lock:
            items = self._read()
            for a in items:
                if a["id"] == aid:
                    a["credits"] = max(0, a["credits"] + int(credits_delta))
                    if name.strip():
                        a["name"] = name.strip()[:60]
                    if role:
                        if role not in ROLES:
                            raise ValueError("role must be creator or client")
                        a["role"] = role
                    self._write(items)
                    return a
        raise KeyError(aid)

    def charge(self, aid: str, amount: int) -> dict:
        with self._lock:
            items = self._read()
            for a in items:
                if a["id"] == aid:
                    if a["credits"] < amount:
                        raise PermissionError(f"not enough credits: this needs {amount}, you have {a['credits']}")
                    a["credits"] -= amount
                    a["used"] += amount
                    self._write(items)
                    return a
        raise KeyError(aid)

    def delete(self, aid: str) -> None:
        with self._lock:
            items = self._read()
            kept = [a for a in items if a["id"] != aid]
            if len(kept) == len(items):
                raise KeyError(aid)
            self._write(kept)


def public(a: dict, with_key: bool = False) -> dict:
    out = {k: a[k] for k in ("id", "name", "role", "credits", "used", "created_at")}
    if with_key:
        out["key"] = a["key"]
    return out


REVIEW_PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review: {title}</title><style>
body{{margin:0;background:#0b0b0b;color:#eee;font-family:system-ui,sans-serif}}main{{max-width:560px;margin:auto;padding:16px}}
h1{{color:#d4af37;font-size:20px}}video{{width:100%;border-radius:12px;background:#000}}textarea{{width:100%;min-height:90px;
background:#151515;color:#eee;border:1px solid #333;border-radius:8px;padding:8px;box-sizing:border-box}}
button{{padding:12px 18px;border:0;border-radius:10px;font-weight:700;margin:8px 8px 0 0;font-size:15px}}
.ok{{background:#d4af37;color:#000}}.no{{background:#2a2a2a;color:#eee}}.st{{color:#9e9e9e;font-size:13px}}li{{margin:6px 0}}
</style></head><body><main><h1>{title}</h1><p class="st">Status: <b>{status}</b></p>
<video src="/review/{token}/video" controls playsinline preload="metadata"></video>
<form method="post" action="/review/{token}"><textarea name="comment" placeholder="Notes for the creator (optional)"></textarea>
<button class="ok" name="decision" value="approved">Approve</button><button class="no" name="decision" value="changes">Request changes</button></form>
<ul>{comments}</ul><p class="st">Made with CreatorForge</p></main></body></html>"""
