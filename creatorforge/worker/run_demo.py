"""Start a worker in DEMO mode so the CreatorForge app can be tested end to end without any AI
models. The script, images, narration and music are placeholders; everything else is real:
the editing, transitions, captions, MP4 render and verification. Every production clearly
reports `mock` providers.

    python run_demo.py            # then in the app: Settings -> Worker URL -> http://<this-PC-IP>:8765
"""
import os
import socket

os.environ.setdefault("CF_ALLOW_MOCK", "1")
os.environ.setdefault("CF_LLM_URL", "mock")
os.environ.setdefault("CF_IMAGE_PROVIDER", "mock")
os.environ.setdefault("CF_VIDEO_PROVIDER", "mock")
os.environ.setdefault("CF_MUSIC_PROVIDER", "mock")
os.environ.setdefault("CF_VOICES", '[{"id": "demo", "name": "Demo narrator (tone)", "provider": "mock", "voice": ""}]')
os.environ.setdefault("CF_DATA_DIR", "./creatorforge-demo-data")

if __name__ == "__main__":
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except OSError:
        ip = "<this-computer's-IP>"
    print(f"\n  CreatorForge DEMO worker -> in the app set Worker URL to:  http://{ip}:8765\n")
    from creatorforge_worker.__main__ import main
    main()
