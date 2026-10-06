"""Reusable production styles (Shorts / Reels / TikTok / YouTube)."""
from __future__ import annotations

from dataclasses import dataclass

ASPECTS = {
    # aspect: (generation size, output size)
    "9:16": ((768, 1344), (1080, 1920)),
    "16:9": ((1344, 768), (1920, 1080)),
    "1:1": ((1024, 1024), (1080, 1080)),
}


@dataclass(frozen=True)
class Template:
    id: str
    name: str
    aspect: str
    scene_seconds: float
    style: str
    tone: str
    transitions: tuple[str, ...]
    words_per_caption: int
    caption_scale: float  # caption font size as a fraction of output height
    caption_position: float  # vertical position of captions, fraction of height from top
    music_mood: str


TEMPLATES: dict[str, Template] = {t.id: t for t in [
    Template("shorts_cinematic", "Cinematic Short", "9:16", 5.0,
             "cinematic, photorealistic, dramatic lighting, shallow depth of field, 35mm film still, high detail",
             "punchy and curiosity-driven, short sentences, strong hook in the first line",
             ("fade", "whip", "zoom", "dissolve"), 3, 0.045, 0.70, "epic cinematic"),
    Template("reels_punchy", "Punchy Reel / TikTok", "9:16", 3.5,
             "vibrant, high contrast, bold saturated colors, dynamic composition, ultra detailed",
             "energetic and fast, conversational, every line delivers a new point",
             ("slide", "cut", "flash", "whip"), 2, 0.05, 0.62, "upbeat electronic"),
    Template("explainer", "Clear Explainer", "16:9", 7.0,
             "clean modern digital illustration, soft studio lighting, clear subject, high detail",
             "clear, friendly and educational, explain one idea per scene",
             ("fade", "dissolve"), 5, 0.04, 0.84, "light corporate"),
    Template("youtube_longform", "YouTube Documentary", "16:9", 10.0,
             "cinematic documentary photography, natural light, realistic textures, high detail",
             "engaging documentary narration with a clear story arc",
             ("fade", "dissolve", "dip"), 6, 0.036, 0.86, "ambient documentary"),
    Template("square_social", "Square Social Post", "1:1", 4.5,
             "bold editorial photography, striking composition, high detail",
             "direct and scroll-stopping, short sentences",
             ("fade", "slide", "dissolve"), 3, 0.05, 0.74, "modern upbeat"),
]}

PACING = {"slow": 1.3, "medium": 1.0, "fast": 0.75}
WORDS_PER_SECOND = 2.5
