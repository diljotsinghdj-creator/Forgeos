"""CreatorForge worker HTTP API.

Legacy (RC10 app): GET /health, POST /v1/images/generate, POST /v1/voice/generate,
                    /v1/video/jobs (501 until video models land).
One-button production: POST /v1/productions and friends (see README)."""
from __future__ import annotations

import hashlib
import hmac
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from . import __version__, providers
from .config import Config
from .director import Character, ProductionSpec
from .library import ASSET_KINDS, Library
from .media import ff
from .media import verify
from .media.ff import MediaError
from .pipeline import Pipeline
from .providers.base import NotConfigured, ProviderError
from .runner import Runner
from .store import JobStore
from .templates import ASPECTS, STYLE_PRESETS, TEMPLATES


def create_app(cfg: Config | None = None, start_runner: bool = True) -> FastAPI:
    cfg = cfg or Config.from_env()
    store = JobStore(cfg.jobs_dir)
    library = Library(cfg.data_dir / "library", cfg.allow_mock)
    pipeline = Pipeline(cfg, store, library)
    runner = Runner(pipeline, store)
    characters = library.characters

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if start_runner:
            runner.start()
        yield

    app = FastAPI(title="CreatorForge Worker", version=__version__, lifespan=lifespan)
    app.state.cfg, app.state.store, app.state.runner = cfg, store, runner

    def auth(request: Request) -> None:
        if not cfg.token:
            return
        header = request.headers.get("authorization", "")
        if not hmac.compare_digest(header.encode(), f"Bearer {cfg.token}".encode()):
            raise HTTPException(401, "missing or invalid worker token")

    def provider_status() -> dict:
        status = {}
        for name, build in [("llm", lambda: providers.build_llm(cfg)), ("image", lambda: providers.build_image(cfg)),
                            ("voice", lambda: providers.build_voice(cfg, providers.voice_profile(cfg, None, pipeline.library_voices()))),
                            ("video", lambda: providers.build_video(cfg))]:
            try:
                status[name] = {"ready": True, "id": build().id}
            except NotConfigured as e:
                status[name] = {"ready": False, "error": str(e)}
        status["captions"] = {"ready": True, "id": "whisper" if cfg.asr_provider == "whisper" else "estimated"}
        try:
            gen = providers.build_music(cfg)
            status["music"] = {"ready": True, "id": gen.id if gen else (f"library:{cfg.music_dir}" if cfg.music_dir else "none")}
        except NotConfigured as e:
            status["music"] = {"ready": False, "error": str(e)}
        return status

    def job_or_404(job_id: str) -> dict:
        try:
            return store.load(job_id)
        except KeyError:
            raise HTTPException(404, "production not found") from None

    def public(job: dict) -> dict:
        j = {k: v for k, v in job.items() if k not in ("music_track", "render")}
        if j.get("result"):
            j["result"] = {**j["result"], "video_url": f"/v1/productions/{job['id']}/video"}
        return j

    @app.get("/health")
    def health() -> dict:
        st = provider_status()
        return {"ok": True, "version": __version__, "auth_required": bool(cfg.token),
                "production_ready": all(v["ready"] for k, v in st.items() if k != "video"),
                "ai_video_ready": st["video"]["ready"], "providers": st,
                "mock": cfg.allow_mock}

    @app.get("/v1/capabilities", dependencies=[Depends(auth)])
    def capabilities() -> dict:
        return {"templates": [{"id": t.id, "name": t.name, "aspect": t.aspect} for t in TEMPLATES.values()],
                "aspects": list(ASPECTS), "pacing": ["slow", "medium", "fast"],
                "motion": ["stills"] + (["ai_video"] if cfg.video_provider else []),
                "styles": [{"id": k, "name": v[0]} for k, v in STYLE_PRESETS.items()],
                "voices": [{"id": v.id, "name": v.name, "provider": v.provider} for v in cfg.voices + pipeline.library_voices()],
                "providers": provider_status()}

    # ---- one-button production -----------------------------------------------------------
    @app.post("/v1/productions", status_code=202, dependencies=[Depends(auth)])
    async def create_production(request: Request) -> dict:
        try:
            spec = ProductionSpec.from_dict(await request.json())
            # Snapshot library characters so later library edits never change a production mid-flight.
            known = {c.name.lower() for c in spec.characters}
            for c in characters.get_many(spec.character_ids):
                if c["name"].lower() not in known:
                    spec.characters.append(Character(c["name"], c["description"]))
        except (ValueError, TypeError) as e:
            raise HTTPException(422, str(e)) from None
        job = store.create(spec.to_dict())
        runner.submit(job["id"])
        return public(job)

    @app.get("/v1/productions", dependencies=[Depends(auth)])
    def list_productions() -> list[dict]:
        return [{"id": j["id"], "status": j["status"], "progress": j["progress"], "message": j["message"],
                 "title": j.get("title") or (j.get("plan") or {}).get("title") or j["spec"]["idea"][:60],
                 "created_at": j["created_at"]} for j in store.all()]

    @app.get("/v1/productions/{job_id}", dependencies=[Depends(auth)])
    def get_production(job_id: str) -> dict:
        return public(job_or_404(job_id))

    @app.delete("/v1/productions/{job_id}", dependencies=[Depends(auth)])
    def cancel_production(job_id: str, purge: bool = False):
        job_or_404(job_id)
        if purge:
            try:
                runner.purge(job_id)
            except ValueError as e:
                raise HTTPException(409, str(e)) from None
            return Response(status_code=204)
        return public(runner.cancel(job_id))

    @app.post("/v1/productions/{job_id}/retry", dependencies=[Depends(auth)])
    def retry_production(job_id: str, from_stage: str | None = None) -> dict:
        job_or_404(job_id)
        return public(runner.retry(job_id, from_stage))

    @app.post("/v1/productions/{job_id}/scenes/{index}/regenerate", dependencies=[Depends(auth)])
    def regenerate_scene(job_id: str, index: int) -> dict:
        job_or_404(job_id)
        try:
            return public(runner.regenerate_scene(job_id, index))
        except ValueError as e:
            raise HTTPException(409, str(e)) from None

    @app.patch("/v1/productions/{job_id}/scenes/{index}", dependencies=[Depends(auth)])
    async def edit_scene(job_id: str, index: int, request: Request) -> dict:
        job_or_404(job_id)
        body = await request.json()
        try:
            if body.get("asset_id"):
                path, kind, name = resolve_asset(str(body["asset_id"]))
                return public(runner.use_asset(job_id, index, path, kind, name))
            return public(runner.edit_scene(job_id, index, body.get("narration"), body.get("visual")))
        except KeyError:
            raise HTTPException(404, "asset not found") from None
        except (ValueError, MediaError) as e:
            raise HTTPException(409, str(e)) from None

    @app.patch("/v1/productions/{job_id}", dependencies=[Depends(auth)])
    async def rename_production(job_id: str, request: Request) -> dict:
        job_or_404(job_id)
        try:
            return public(runner.rename(job_id, str((await request.json()).get("title", ""))))
        except ValueError as e:
            raise HTTPException(422, str(e)) from None

    @app.patch("/v1/productions/{job_id}/timeline", dependencies=[Depends(auth)])
    async def edit_timeline(job_id: str, request: Request) -> dict:
        job_or_404(job_id)
        try:
            return public(runner.edit_timeline(job_id, await request.json()))
        except (ValueError, TypeError) as e:
            raise HTTPException(409, str(e)) from None

    @app.get("/v1/productions/{job_id}/files/{name}", dependencies=[Depends(auth)])
    def production_file(job_id: str, name: str):
        job_or_404(job_id)
        if "/" in name or "\\" in name or name.startswith(".") or not name.startswith("scene_"):
            raise HTTPException(404, "file not found")
        path = store.dir(job_id) / name
        if not path.is_file():
            raise HTTPException(404, "file not found")
        return FileResponse(path, media_type=_media_type(path))

    @app.post("/v1/productions/{job_id}/approve", dependencies=[Depends(auth)])
    def approve_production(job_id: str) -> dict:
        job_or_404(job_id)
        return public(runner.approve(job_id))

    @app.get("/v1/productions/{job_id}/video", dependencies=[Depends(auth)])
    def production_video(job_id: str):
        job = job_or_404(job_id)
        if job["status"] != "READY" or not job.get("result"):
            raise HTTPException(409, "video is not ready")
        return FileResponse(store.dir(job_id) / job["result"]["file"], media_type="video/mp4",
                            filename=f"creatorforge_{job_id}.mp4")

    @app.get("/v1/productions/{job_id}/scenes/{index}/image", dependencies=[Depends(auth)])
    def scene_image(job_id: str, index: int):
        job = job_or_404(job_id)
        if not 0 <= index < len(job["scenes"]) or not job["scenes"][index].get("image"):
            raise HTTPException(404, "scene image not ready")
        return FileResponse(store.dir(job_id) / job["scenes"][index]["image"], media_type="image/png")

    # ---- libraries -----------------------------------------------------------------------
    @app.get("/v1/library/characters", dependencies=[Depends(auth)])
    def list_characters() -> list[dict]:
        return characters.list()

    @app.post("/v1/library/characters", status_code=201, dependencies=[Depends(auth)])
    async def create_character(request: Request) -> dict:
        try:
            return characters.create(await request.json())
        except ValueError as e:
            raise HTTPException(422, str(e)) from None

    @app.put("/v1/library/characters/{cid}", dependencies=[Depends(auth)])
    async def update_character(cid: str, request: Request) -> dict:
        try:
            return characters.update(cid, await request.json())
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        except KeyError:
            raise HTTPException(404, "character not found") from None

    @app.delete("/v1/library/characters/{cid}", status_code=204, dependencies=[Depends(auth)])
    def delete_character(cid: str) -> Response:
        try:
            characters.delete(cid)
        except KeyError:
            raise HTTPException(404, "character not found") from None
        return Response(status_code=204)

    # Voice Profiles -----------------------------------------------------------------------
    @app.get("/v1/library/voices", dependencies=[Depends(auth)])
    def list_voices() -> list[dict]:
        builtin = [{"id": v.id, "name": v.name, "provider": v.provider, "voice": v.voice, "speed": v.speed,
                    "builtin": True} for v in cfg.voices]
        return builtin + [{**v, "builtin": False} for v in library.voices.list()]

    @app.post("/v1/library/voices", status_code=201, dependencies=[Depends(auth)])
    async def create_voice(request: Request) -> dict:
        try:
            return library.voices.create(await request.json(), {v.id for v in cfg.voices})
        except ValueError as e:
            raise HTTPException(422, str(e)) from None

    @app.put("/v1/library/voices/{vid}", dependencies=[Depends(auth)])
    async def update_voice(vid: str, request: Request) -> dict:
        try:
            return library.voices.update(vid, await request.json())
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        except KeyError:
            raise HTTPException(404, "voice not found (built-in voices are set on the worker)") from None

    @app.delete("/v1/library/voices/{vid}", status_code=204, dependencies=[Depends(auth)])
    def delete_voice(vid: str) -> Response:
        try:
            library.voices.delete(vid)
        except KeyError:
            raise HTTPException(404, "voice not found (built-in voices are set on the worker)") from None
        return Response(status_code=204)

    @app.post("/v1/library/voices/{vid}/preview", dependencies=[Depends(auth)])
    async def preview_voice(vid: str, request: Request):
        try:
            body = await request.json()
        except ValueError:
            body = {}
        text = str(body.get("text") or "This is how I sound narrating your CreatorForge video.")[:300]
        try:
            voice = providers.build_voice(cfg, providers.voice_profile(cfg, vid, pipeline.library_voices()))
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "preview.wav"
                voice.synthesize(text, out)
                verify.wav(out)
                return Response(out.read_bytes(), media_type="audio/wav")
        except NotConfigured as e:
            raise HTTPException(404, str(e)) from None
        except (ProviderError, MediaError) as e:
            raise HTTPException(502, str(e)) from None

    # Asset Library ------------------------------------------------------------------------
    def resolve_asset(asset_id: str) -> tuple[Path, str, str]:
        """Library uploads by id, or generated scene files as 'gen~<production>~<file>'."""
        if asset_id.startswith("gen~"):
            _, jid, name = asset_id.split("~", 2)
            if "/" in name or not name.startswith("scene_"):
                raise KeyError(asset_id)
            path = store.dir(jid) / name
            if not path.is_file():
                raise KeyError(asset_id)
            kind = {".png": "image", ".jpg": "image", ".jpeg": "image", ".mp4": "video"}.get(path.suffix.lower(), "audio")
            return path, kind, name
        a = library.assets.get(asset_id)
        kind = "audio" if a["kind"] in ("music", "sfx") else a["kind"]
        return library.assets.path(a), kind, a["name"]

    @app.get("/v1/library/assets", dependencies=[Depends(auth)])
    def list_assets(kind: str | None = None, generated: bool = False) -> list[dict]:
        out = [{**a, "source": "upload", "file_url": f"/v1/library/assets/{a['id']}/file"} for a in library.assets.list(kind)]
        if generated:
            for j in store.all():
                title = j.get("title") or (j.get("plan") or {}).get("title") or j["spec"]["idea"][:40]
                for sc in j.get("scenes", []):
                    for key, k in (("image", "image"), ("clip", "video"), ("narration", "audio")):
                        name = sc.get(key)
                        if not name or (kind and kind != k) or not (store.dir(j["id"]) / name).is_file():
                            continue
                        out.append({"id": f"gen~{j['id']}~{name}", "kind": k, "source": "generated",
                                    "name": f"{title[:40]} - scene {sc['index'] + 1} {k}", "created_at": j["created_at"],
                                    "file_url": f"/v1/productions/{j['id']}/files/{name}"})
        return out

    @app.post("/v1/library/assets", status_code=201, dependencies=[Depends(auth)])
    async def upload_asset(request: Request, kind: str, name: str = "") -> dict:
        if kind not in ASSET_KINDS:
            raise HTTPException(422, f"kind must be one of: {', '.join(ASSET_KINDS)}")
        ext = Path(name).suffix.lower()[:6] or {"image": ".png", "video": ".mp4"}.get(kind, ".wav")
        tmpdir = Path(tempfile.mkdtemp(dir=library.assets.root))
        tmp = tmpdir / f"upload{ext}"
        size = 0
        try:
            with tmp.open("wb") as f:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 300 * 1024 * 1024:
                        raise HTTPException(413, "asset larger than 300 MB")
                    f.write(chunk)
            return library.assets.add(kind, name, tmp, ext, lambda p: _check_asset(kind, p))
        except (MediaError, ValueError) as e:
            raise HTTPException(422, f"not a usable {kind}: {e}") from None
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @app.patch("/v1/library/assets/{aid}", dependencies=[Depends(auth)])
    async def rename_asset(aid: str, request: Request) -> dict:
        try:
            return library.assets.rename(aid, str((await request.json()).get("name", "")))
        except KeyError:
            raise HTTPException(404, "asset not found") from None

    @app.delete("/v1/library/assets/{aid}", status_code=204, dependencies=[Depends(auth)])
    def delete_asset(aid: str) -> Response:
        try:
            library.assets.delete(aid)
        except KeyError:
            raise HTTPException(404, "asset not found") from None
        return Response(status_code=204)

    @app.get("/v1/library/assets/{aid}/file", dependencies=[Depends(auth)])
    def asset_file(aid: str):
        try:
            a = library.assets.get(aid)
        except KeyError:
            raise HTTPException(404, "asset not found") from None
        path = library.assets.path(a)
        return FileResponse(path, media_type=_media_type(path), filename=a["name"])

    @app.get("/v1/library/videos", dependencies=[Depends(auth)])
    def list_videos() -> list[dict]:
        """Media Library: every finished, verified production."""
        out = []
        for j in store.all():
            if j["status"] == "READY" and j.get("result"):
                v = j["result"]["verification"]
                out.append({"id": j["id"], "title": j.get("title") or j["result"].get("title") or j["spec"]["idea"][:60],
                            "aspect": j["spec"]["aspect"], "template": j["spec"]["template"],
                            "duration_s": v["duration_s"], "bytes": v["bytes"], "created_at": j["created_at"],
                            "video_url": f"/v1/productions/{j['id']}/video",
                            "thumbnail_url": f"/v1/productions/{j['id']}/scenes/0/image"})
        return out

    # ---- legacy single-asset endpoints used by CreatorForge RC10 ---------------------------
    @app.post("/v1/images/generate", dependencies=[Depends(auth)])
    async def legacy_image(request: Request):
        body = await request.json()
        prompt = str(body.get("prompt", "")).strip()
        aspect = str(body.get("aspect_ratio", "9:16"))
        if not prompt or aspect not in ASPECTS:
            raise HTTPException(422, "prompt and a valid aspect_ratio are required")
        (w, h), _ = ASPECTS[aspect]
        try:
            img = providers.build_image(cfg)
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "image.png"
                img.generate(prompt, "", w, h, int(body.get("seed", 0)) or int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16), out)
                verify.image(out)
                return Response(out.read_bytes(), media_type="image/png")
        except (ProviderError, MediaError) as e:
            raise HTTPException(502, str(e)) from None

    @app.post("/v1/voice/generate", dependencies=[Depends(auth)])
    async def legacy_voice(request: Request):
        body = await request.json()
        text = str(body.get("text", "")).strip()
        if not text:
            raise HTTPException(422, "text is required")
        try:
            voice = providers.build_voice(cfg, providers.voice_profile(cfg, body.get("voice") or None))
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "voice.wav"
                voice.synthesize(text, out)
                verify.wav(out)
                return Response(out.read_bytes(), media_type="audio/wav")
        except (ProviderError, MediaError) as e:
            raise HTTPException(502, str(e)) from None

    @app.api_route("/v1/video/jobs{rest:path}", methods=["GET", "POST", "DELETE"], dependencies=[Depends(auth)])
    def video_jobs(rest: str):
        return JSONResponse({"error": "AI video clip generation is not enabled on this worker yet"}, status_code=501)

    return app


def _media_type(path: Path) -> str:
    return {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
            ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm", ".wav": "audio/wav",
            ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".aac": "audio/aac", ".ogg": "audio/ogg",
            ".flac": "audio/flac"}.get(path.suffix.lower(), "application/octet-stream")


def _check_asset(kind: str, path: Path) -> dict:
    """Fail-closed import check: the file must really be the kind it claims to be."""
    if kind == "image":
        return verify.image(path)
    info = ff.probe(path)
    streams = info["streams"]
    duration = float(info["format"].get("duration") or 0)
    if kind == "video":
        v = [s for s in streams if s.get("codec_type") == "video"]
        if not v or duration < 0.5:
            raise MediaError("no playable video stream")
        return {"duration_s": round(duration, 2), "width": int(v[0]["width"]), "height": int(v[0]["height"])}
    if not [s for s in streams if s.get("codec_type") == "audio"]:
        raise MediaError("no audio stream")
    if duration < (0.05 if kind == "sfx" else 0.5):
        raise MediaError("audio too short")
    return {"duration_s": round(duration, 2)}
