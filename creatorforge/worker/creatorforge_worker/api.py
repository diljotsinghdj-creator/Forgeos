"""CreatorForge worker HTTP API.

Legacy (RC10 app): GET /health, POST /v1/images/generate, POST /v1/voice/generate,
                    /v1/video/jobs (501 until video models land).
One-button production: POST /v1/productions and friends (see README)."""
from __future__ import annotations

import hashlib
import hmac
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from . import __version__, providers
from .config import Config
from .director import ProductionSpec
from .media import verify
from .media.ff import MediaError
from .pipeline import Pipeline
from .providers.base import NotConfigured, ProviderError
from .runner import Runner
from .store import JobStore
from .templates import ASPECTS, TEMPLATES


def create_app(cfg: Config | None = None, start_runner: bool = True) -> FastAPI:
    cfg = cfg or Config.from_env()
    store = JobStore(cfg.jobs_dir)
    pipeline = Pipeline(cfg, store)
    runner = Runner(pipeline, store)

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
                            ("voice", lambda: providers.build_voice(cfg, providers.voice_profile(cfg, None)))]:
            try:
                status[name] = {"ready": True, "id": build().id}
            except NotConfigured as e:
                status[name] = {"ready": False, "error": str(e)}
        status["captions"] = {"ready": True, "id": "whisper" if cfg.asr_provider == "whisper" else "estimated"}
        status["music"] = {"ready": True, "id": cfg.music_dir or "none"}
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
                "production_ready": all(v["ready"] for v in st.values()), "providers": st,
                "mock": cfg.allow_mock}

    @app.get("/v1/capabilities", dependencies=[Depends(auth)])
    def capabilities() -> dict:
        return {"templates": [{"id": t.id, "name": t.name, "aspect": t.aspect} for t in TEMPLATES.values()],
                "aspects": list(ASPECTS), "pacing": ["slow", "medium", "fast"],
                "voices": [{"id": v.id, "name": v.name, "provider": v.provider} for v in cfg.voices],
                "providers": provider_status()}

    # ---- one-button production -----------------------------------------------------------
    @app.post("/v1/productions", status_code=202, dependencies=[Depends(auth)])
    async def create_production(request: Request) -> dict:
        try:
            spec = ProductionSpec.from_dict(await request.json())
        except (ValueError, TypeError) as e:
            raise HTTPException(422, str(e)) from None
        job = store.create(spec.to_dict())
        runner.submit(job["id"])
        return public(job)

    @app.get("/v1/productions", dependencies=[Depends(auth)])
    def list_productions() -> list[dict]:
        return [{"id": j["id"], "status": j["status"], "progress": j["progress"], "message": j["message"],
                 "title": (j.get("plan") or {}).get("title") or j["spec"]["idea"][:60],
                 "created_at": j["created_at"]} for j in store.all()]

    @app.get("/v1/productions/{job_id}", dependencies=[Depends(auth)])
    def get_production(job_id: str) -> dict:
        return public(job_or_404(job_id))

    @app.delete("/v1/productions/{job_id}", dependencies=[Depends(auth)])
    def cancel_production(job_id: str) -> dict:
        job_or_404(job_id)
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
