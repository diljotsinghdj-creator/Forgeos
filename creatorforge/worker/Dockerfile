FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY creatorforge_worker ./creatorforge_worker
# Default backends: Piper narration + Whisper captions (both run on CPU).
# Add GPU/extra backends with e.g. --build-arg EXTRAS=whisper,kokoro,diffusers
ARG EXTRAS=whisper
RUN pip install --no-cache-dir ".[${EXTRAS}]" piper-tts
ENV CF_DATA_DIR=/data CF_PORT=8765
VOLUME /data
EXPOSE 8765
CMD ["creatorforge-worker"]
