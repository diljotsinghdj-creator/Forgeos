"""A talking mascot: LatentSync (ByteDance, Apache-2.0 code) re-draws the character's mouth so it speaks the
narration, frame by frame, on the line the writer marks "Talk: <name>".

LatentSync lives in its own folder and Python environment on the pod (/workspace/latentsync, set up by the pod setup
only when CF_LIPSYNC=1 - the model is a ~6 GB download and needs a GPU). It works on a video of a face; a still
picture is first turned into a gently moving clip at its 25 frames a second. When it cannot find a face (very
abstract drawings) or anything else goes wrong, the line keeps its normal picture."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .ff import MediaError

HOME = Path(os.environ.get("CF_LATENTSYNC_DIR", "/workspace/latentsync"))
PYTHON = Path(os.environ.get("CF_LATENTSYNC_PYTHON", str(HOME / "venv" / "bin" / "python")))
CONFIG = os.environ.get("CF_LATENTSYNC_CONFIG", "configs/unet/stage2.yaml")
CKPT = os.environ.get("CF_LATENTSYNC_CKPT", "checkpoints/latentsync_unet.pt")


def available() -> bool:
    return (os.environ.get("CF_LIPSYNC", "0") == "1" and PYTHON.is_file() and (HOME / CKPT).is_file()
            and (HOME / "scripts").is_dir())


def command(video: Path, audio: Path, out: Path, steps: int = 20, guidance: float = 1.5) -> list[str]:
    return [str(PYTHON), "-m", "scripts.inference", "--unet_config_path", CONFIG, "--inference_ckpt_path", CKPT,
            "--inference_steps", str(steps), "--guidance_scale", str(guidance), "--video_path", str(video),
            "--audio_path", str(audio), "--video_out_path", str(out)]


def still_video(image: Path, seconds: float, out: Path, width: int, height: int) -> Path:
    """A still as a 25 fps clip with a slow push-in (LatentSync needs a video, and a face that holds still)."""
    frames = max(2, int(seconds * 25))
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-loop", "1", "-i", str(image), "-vf",
                    f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                    f"zoompan=z='1+0.04*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:"
                    f"s={width}x{height}:fps=25,format=yuv420p", "-t", f"{seconds:.2f}", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "17", str(out)], check=True)
    return out


def talk(picture: Path, audio: Path, out: Path, width: int, height: int, seconds: float,
         timeout: float = 3600) -> Path:
    """The character in `picture` (a still or a clip) speaking `audio`. Raises MediaError when it can't."""
    if not available():
        raise MediaError("lip-sync not installed (set CF_LIPSYNC=1 and run the pod setup)")
    out.parent.mkdir(parents=True, exist_ok=True)
    src = picture
    if picture.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
        src = still_video(picture, seconds, out.with_suffix(".base.mp4"), width, height)
    r = subprocess.run(command(src, audio, out), cwd=HOME, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not out.is_file() or out.stat().st_size < 1000:
        raise MediaError(f"lip-sync failed: {(r.stderr or r.stdout)[-300:]}")
    return out
