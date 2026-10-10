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

# Director Mode looks. Applied to every scene image and carried into the animation prompt.
STYLE_PRESETS: dict[str, tuple[str, str]] = {
    "hyperreal": ("Hyper-realistic", "hyper-realistic photograph, 8k detail, natural skin texture, real-world lighting, "
                  "shot on a full-frame camera, 50mm lens, true-to-life colors"),
    "cinematic": ("Cinematic film", "cinematic film still, anamorphic lens, dramatic volumetric lighting, film grain, "
                  "teal and orange grade, shallow depth of field"),
    "documentary": ("Documentary", "documentary photography, natural available light, candid, realistic textures, "
                    "handheld feel, muted natural colors"),
    "animated_3d": ("3D animated", "high-end 3D animated feature film style, expressive stylized characters, soft global "
                    "illumination, subsurface scattering, vibrant colors"),
    "anime": ("Anime", "anime key visual, cel shading, crisp line art, vivid colors, detailed painted background"),
    "claymation": ("Claymation", "stop-motion claymation style, handmade clay figures, visible fingerprints, miniature "
                   "set, soft studio lighting"),
    "watercolor": ("Watercolor", "watercolor illustration, soft washes, paper texture, gentle hand-drawn lines"),
    "comic": ("Comic book", "comic book art, bold ink outlines, halftone shading, dynamic composition, saturated colors"),
    "explainer_2d": ("2D explainer", "flat 2D vector explainer animation style, clean geometric shapes, simple friendly "
                     "characters, bold flat colors, minimal shading, uncluttered background"),
    "doodle": ("Doodle / whiteboard", "hand-drawn whiteboard doodle, black marker line art on white, simple sketchy "
               "characters, one accent color"),
    "painterly": ("Hand-painted animation", "hand-painted 2D animated film style, lush painterly backgrounds, soft "
                  "natural light, gentle colors, whimsical detail"),
    "noir_graphic": ("Noir graphic novel", "black and white graphic novel art, heavy ink shadows, high contrast, a single "
                     "red accent color, gritty noir mood"),
    "paper_cutout": ("Paper cut-out", "layered paper cut-out craft style, cardboard and colored paper textures, soft "
                     "shadows between layers, handmade diorama"),
    "isometric": ("Isometric 3D", "isometric 3D illustration, miniature diorama, clean soft lighting, tidy detailed "
                  "objects, pastel palette"),
    "low_poly": ("Low-poly 3D", "low-poly 3D render, faceted geometric shapes, soft pastel lighting, clean minimal scene"),
    "retro_cartoon": ("Retro cartoon", "1950s retro cartoon style, rubber-hose animation, warm vintage colors, grainy "
                      "print texture, playful exaggeration"),
    "pixel_art": ("Pixel art", "detailed 16-bit pixel art, limited palette, crisp pixels, retro video game scene"),
    "neon": ("Neon synthwave", "neon synthwave illustration, glowing magenta and cyan lights, dark night scene, "
             "retro-futuristic, reflective surfaces"),
    "editorial": ("Editorial collage", "editorial explainer collage, cut-out archival photographs on off-white textured "
                  "paper, bold flat shapes in mustard yellow and black, halftone dots, torn paper edges, clean graphic "
                  "layout with lots of negative space"),
    "investigative": ("Investigative desk", "investigative documentary desk collage, archival photographs and documents "
                      "taped onto an old desk and a paper map, red string and pins, hand-drawn red circles and arrows, "
                      "warm desk lamp light, film grain"),
    "collage": ("Mixed-media collage", "mixed-media collage, cut-out vintage photographs, torn paper, halftone textures, "
                "bold graphic shapes"),
}
# Editorial explainer looks, built like a video essay: every picture is one clear subject that the worker cuts out
# and lays on paper (or a desk) itself, with highlighter callouts, animated charts and sliding cuts.
EDITORIAL_STYLES = {"editorial", "investigative", "collage"}
# What each explainer look asks the image model for. It leads the prompt (SDXL only reads ~77 tokens, so a look
# placed after a long description is cut off): one subject on a plain background, so it cuts out cleanly.
EDITORIAL_LEADS = {
    "editorial": "vintage halftone press photograph, one clear subject, isolated on a plain light grey background",
    "collage": "vintage halftone press photograph, one clear subject, isolated on a plain light grey background",
    "investigative": "old sepia archival photograph, one clear subject, isolated on a plain light background",
}
EDITORIAL_NEGATIVE = (", collage, multiple images, grid, panels, busy background, torn paper, picture frame, border, "
                      "painting, drawing, illustration, portrait, close-up of a face")
# Drawn / animated looks: characters may show faces even in AI video (cartoon faces don't turn uncanny), and the
# worker renders them with its illustration model when one is installed (the photoreal model suits the rest).
ANIMATED_STYLES = {"animated_3d", "anime", "claymation", "watercolor", "comic", "explainer_2d", "doodle", "painterly",
                   "noir_graphic", "paper_cutout", "isometric", "low_poly", "retro_cartoon", "pixel_art", "neon"}
