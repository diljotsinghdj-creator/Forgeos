"""AI Director + ScriptForge + PromptForge.

The LLM writes the script and shot list; PromptForge then deterministically turns each shot
into an image prompt using the template style, Director Mode controls and the character
library, so visual style stays consistent across scenes."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from .providers.base import ProviderError
from .templates import PACING, TEMPLATES, WORDS_PER_SECOND, Template

NEGATIVE = ("text, watermark, logo, caption, subtitles, letters, signature, blurry, low quality, "
            "jpeg artifacts, deformed, distorted face, extra fingers, extra limbs")


@dataclass
class Character:
    name: str
    description: str


@dataclass
class ProductionSpec:
    idea: str
    duration_s: int = 45
    aspect: str = ""  # empty -> template default
    template: str = "shorts_cinematic"
    voice: str = ""
    style: str = ""  # Director Mode overrides
    pacing: str = "medium"
    mood: str = ""
    camera: str = ""
    characters: list[Character] = field(default_factory=list)
    music: bool = True
    captions: bool = True
    motion: str = "stills"  # "stills" (camera motion on images) | "ai_video" (image-to-video clips)
    review: bool = False  # pause after scene visuals so the storyboard can be edited/approved

    @staticmethod
    def from_dict(d: dict) -> "ProductionSpec":
        chars = [Character(str(c.get("name", "")).strip(), str(c.get("description", "")).strip())
                 for c in d.get("characters") or [] if isinstance(c, dict)]
        spec = ProductionSpec(
            idea=str(d.get("idea", "")).strip(),
            duration_s=int(d.get("duration_s", 45)),
            aspect=str(d.get("aspect", "") or ""),
            template=str(d.get("template", "") or "shorts_cinematic"),
            voice=str(d.get("voice", "") or ""),
            style=str(d.get("style", "") or "").strip(),
            pacing=str(d.get("pacing", "") or "medium"),
            mood=str(d.get("mood", "") or "").strip(),
            camera=str(d.get("camera", "") or "").strip(),
            characters=[c for c in chars if c.name and c.description],
            music=bool(d.get("music", True)),
            captions=bool(d.get("captions", True)),
            motion=str(d.get("motion", "") or "stills"),
            review=bool(d.get("review", False)),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if len(self.idea) < 5:
            raise ValueError("idea must be at least 5 characters")
        if len(self.idea) > 4000:
            raise ValueError("idea is too long (max 4000 characters)")
        if not 10 <= self.duration_s <= 900:
            raise ValueError("duration_s must be between 10 and 900")
        if self.template not in TEMPLATES:
            raise ValueError(f"unknown template '{self.template}'")
        if not self.aspect:
            self.aspect = TEMPLATES[self.template].aspect
        if self.aspect not in ("9:16", "16:9", "1:1"):
            raise ValueError("aspect must be 9:16, 16:9 or 1:1")
        if self.pacing not in PACING:
            raise ValueError("pacing must be slow, medium or fast")
        if self.motion not in ("stills", "ai_video"):
            raise ValueError("motion must be stills or ai_video")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ShotPlan:
    narration: str
    visual: str
    shot: str = ""
    camera: str = ""
    mood: str = ""
    overlay: str = ""
    prompt: str = ""
    negative: str = ""


@dataclass
class ProductionPlan:
    title: str
    hook: str
    cta: str
    music_mood: str
    scenes: list[ShotPlan]

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "ProductionPlan":
        return ProductionPlan(d["title"], d.get("hook", ""), d.get("cta", ""), d.get("music_mood", ""),
                              [ShotPlan(**s) for s in d["scenes"]])


def target_scene_count(spec: ProductionSpec) -> int:
    t = TEMPLATES[spec.template]
    seconds = t.scene_seconds * PACING[spec.pacing]
    return max(3, min(40, round(spec.duration_s / seconds)))


SYSTEM = """You are CreatorForge's AI Director and ScriptForge. You turn one idea into a complete,
production-ready short video plan: a scroll-stopping hook, a tight narrated script split into
scenes, a shot list and a call to action. Narration is spoken by a voice-over; visuals are
generated as still images, so every 'visual' must describe ONE concrete, filmable image
(subject, setting, action, lighting) with no on-screen text. Respond with JSON only."""


def _user_prompt(spec: ProductionSpec, t: Template, n: int) -> str:
    words = int(spec.duration_s * WORDS_PER_SECOND)
    chars = "\n".join(f"- {c.name}: {c.description}" for c in spec.characters) or "(none)"
    return f"""IDEA: {spec.idea}
FORMAT: {t.name}, aspect {spec.aspect}, about {spec.duration_s} seconds
SCENE_COUNT: {n}
TOTAL NARRATION: about {words} words across all scenes (spoken at ~{WORDS_PER_SECOND} words/second)
TONE: {t.tone}
MOOD: {spec.mood or 'choose what fits the idea'}
RECURRING CHARACTERS (use their names in visuals when they appear):
{chars}

Return exactly this JSON shape:
{{"title": "short video title",
  "hook": "on-screen hook text, max 7 words",
  "cta": "on-screen call to action, max 6 words",
  "music_mood": "2-4 words describing background music",
  "scenes": [
    {{"narration": "what the voice-over says in this scene (1-3 sentences)",
      "visual": "one concrete image description, no text in image",
      "shot": "wide | medium | close-up | extreme close-up | aerial | over-the-shoulder",
      "camera": "e.g. slow push in, pan left, static, low angle",
      "mood": "e.g. tense, hopeful, awe",
      "overlay": "optional short on-screen callout (max 5 words) or empty string"}}
  ]}}
The scenes array must contain exactly {n} scenes. Scene 1 narration must open with the hook idea."""


def _extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start:end + 1])


def _validate(d: dict, n: int) -> ProductionPlan:
    scenes = d.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("'scenes' must be a non-empty list")
    if abs(len(scenes) - n) > max(2, n // 3):
        raise ValueError(f"expected {n} scenes, got {len(scenes)}")
    out = []
    for i, s in enumerate(scenes, 1):
        if not isinstance(s, dict):
            raise ValueError(f"scene {i} is not an object")
        narration, visual = str(s.get("narration", "")).strip(), str(s.get("visual", "")).strip()
        if not narration or not visual:
            raise ValueError(f"scene {i} needs both narration and visual")
        out.append(ShotPlan(narration, visual, str(s.get("shot", "")).strip(), str(s.get("camera", "")).strip(),
                            str(s.get("mood", "")).strip(), str(s.get("overlay", "") or "").strip()[:60]))
    return ProductionPlan(str(d.get("title", "")).strip()[:100] or "Untitled", str(d.get("hook", "")).strip()[:80],
                          str(d.get("cta", "")).strip()[:60], str(d.get("music_mood", "")).strip()[:60], out)


def direct(llm, spec: ProductionSpec) -> ProductionPlan:
    """Runs the AI Director. Retries once with the validation error; then fails closed."""
    t = TEMPLATES[spec.template]
    n = target_scene_count(spec)
    user = _user_prompt(spec, t, n)
    error = ""
    for _ in range(2):
        raw = llm.complete_json(SYSTEM, user if not error else
                                f"{user}\n\nYour previous answer was invalid: {error}. Return corrected JSON only.")
        try:
            plan = _validate(_extract_json(raw), n)
            break
        except (ValueError, json.JSONDecodeError) as e:
            error = str(e)
    else:
        raise ProviderError(f"AI Director returned an invalid plan twice: {error}")
    prompt_forge(plan, spec)
    return plan


def prompt_forge(plan: ProductionPlan, spec: ProductionSpec, only: int | None = None) -> None:
    """Builds each scene's generation prompt from the shot, Director Mode and characters."""
    t = TEMPLATES[spec.template]
    style = spec.style or t.style
    for i, s in enumerate(plan.scenes):
        if only is not None and i != only:
            continue
        parts = [s.visual.rstrip(".")]
        shot = ", ".join(x for x in [f"{s.shot} shot" if s.shot else "", spec.camera or s.camera,
                                     f"{spec.mood or s.mood} mood" if (spec.mood or s.mood) else ""] if x)
        if shot:
            parts.append(shot)
        text = f"{s.visual} {s.narration}".lower()
        for c in spec.characters:
            if c.name.lower() in text:
                parts.append(f"{c.name}: {c.description}")
        parts.append(style)
        s.prompt = ". ".join(parts)
        s.negative = NEGATIVE
