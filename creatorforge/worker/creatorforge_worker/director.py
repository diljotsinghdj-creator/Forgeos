"""AI Director + ScriptForge + PromptForge.

The LLM writes the script and shot list; PromptForge then deterministically turns each shot
into an image prompt using the template style, Director Mode controls and the character
library, so visual style stays consistent across scenes."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from .providers.base import ProviderError
from .media.render import TRANSITIONS
from .templates import PACING, STYLE_PRESETS, TEMPLATES, WORDS_PER_SECOND, Template

NEGATIVE = ("text, watermark, logo, caption, subtitles, letters, signature, blurry, low quality, "
            "jpeg artifacts, deformed, distorted face, extra fingers, extra limbs")
VIDEO_NEGATIVE = ("static, frozen frame, flicker, jitter, morphing, warped face, melting, extra limbs, distorted hands, "
                  "text, watermark, low quality, blurry, overexposed, cartoonish artifacts")


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
    ai_video_scenes: object = "all"  # with motion=ai_video: "all", "hook" (first scene) or a list of scene numbers (1-based)
    auto_edit: bool = True  # let the Director choose transitions, caption emphasis and dramatic holds
    character_ids: list[str] = field(default_factory=list)  # resolved from the Character Library at submit
    music_asset_id: str = ""  # use a track from the Asset Library as the score
    sfx: bool = True  # auto-place sound effects when an SFX folder or SFX assets exist
    script: str = ""  # script mode: the user's exact narration; the Director only plans visuals and the edit

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
            ai_video_scenes=d.get("ai_video_scenes", "all") or "all",
            auto_edit=bool(d.get("auto_edit", True)),
            character_ids=[str(x) for x in d.get("character_ids") or []][:10],
            script=str(d.get("script", "") or "").strip(),
            music_asset_id=str(d.get("music_asset_id", "") or ""),
            sfx=bool(d.get("sfx", True)),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if self.script:
            if len(self.script) < 10:
                raise ValueError("script must be at least 10 characters")
            if len(self.script) > 20000:
                raise ValueError("script is too long (max 20000 characters)")
            if not split_sentences(self.script):
                raise ValueError("script has no speakable sentences")
            if not self.idea:
                self.idea = script_title(self.script)
            self.duration_s = max(10, min(900, round(len(self.script.split()) / WORDS_PER_SECOND)))
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
        if isinstance(self.ai_video_scenes, list):
            if not self.ai_video_scenes or not all(isinstance(n, int) and n >= 1 for n in self.ai_video_scenes):
                raise ValueError("ai_video_scenes must list scene numbers starting at 1")
        elif self.ai_video_scenes not in ("all", "hook"):
            raise ValueError("ai_video_scenes must be 'all', 'hook' or a list of scene numbers")

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
    transition: str = ""  # Auto Edit: transition INTO this scene
    emphasis: list[str] = field(default_factory=list)  # Auto Edit: words highlighted in captions
    hold: float = 0.0  # Auto Edit: extra seconds to let a moment land
    motion: str = ""  # what moves in the shot (people, objects, environment) for AI video
    video_prompt: str = ""
    video_negative: str = ""


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
      "overlay": "optional short on-screen callout (max 5 words) or empty string",
      "transition": "edit INTO this scene: {' | '.join(TRANSITIONS)}",
      "emphasis": ["1-3 key words from this scene's narration to highlight in captions"],
      "hold": "seconds (0 to 1.5) to pause after the line for impact; usually 0",
      "motion": "what physically moves during the shot, e.g. 'robot arm lifts a crate, workers walk past, dust in light beams'"}}
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
        transition = str(s.get("transition", "") or "").strip().lower()
        emphasis = s.get("emphasis") or []
        if isinstance(emphasis, str):
            emphasis = [emphasis]
        try:
            hold = min(1.5, max(0.0, float(s.get("hold") or 0)))
        except (TypeError, ValueError):
            hold = 0.0
        out.append(ShotPlan(narration, visual, str(s.get("shot", "")).strip(), str(s.get("camera", "")).strip(),
                            str(s.get("mood", "")).strip(), str(s.get("overlay", "") or "").strip()[:60],
                            transition=transition if transition in TRANSITIONS else "",
                            emphasis=[str(w).strip()[:30] for w in emphasis if str(w).strip()][:3], hold=hold,
                            motion=str(s.get("motion", "") or "").strip()[:300]))
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
    style = STYLE_PRESETS[spec.style][1] if spec.style in STYLE_PRESETS else (spec.style or t.style)
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
        # The animation prompt leads with motion: image-to-video models already see the still.
        camera = spec.camera or s.camera or "slow cinematic camera move"
        motion = s.motion or f"subtle natural movement in the scene: {s.visual.rstrip('.')}"
        s.video_prompt = (f"{motion}. Camera: {camera}. {s.visual.rstrip('.')}. {style}. "
                          "Smooth realistic motion, natural physics, consistent identity, stable details")
        s.video_negative = VIDEO_NEGATIVE


# ---- script mode ---------------------------------------------------------------------------
_ABBREV = re.compile(r"(?:\b(?:Mr|Mrs|Ms|Dr|Jr|Sr|St|vs|etc|No|Inc|Ltd)\.|\b(?:[A-Z]\.){2,})$")
_SYMBOLS = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]")


def split_sentences(text: str) -> list[str]:
    """Sentence split that keeps abbreviations like "U.S." and "Dr." inside their sentence."""
    text = _SYMBOLS.sub(" ", text)
    out: list[str] = []
    for block in re.split(r"\n+", text):
        pieces = re.split(r"(?<=[.!?\u2026])\s+", block.strip())
        buf = ""
        for p in pieces:
            buf = f"{buf} {p}".strip() if buf else p.strip()
            if not _ABBREV.search(buf):
                out.append(buf)
                buf = ""
        if buf:
            out.append(buf)
    return [re.sub(r"\s+", " ", s).strip() for s in out if any(ch.isalnum() for ch in s)]


def script_title(text: str) -> str:
    first = (split_sentences(text) or ["Untitled"])[0]
    return first[:60].rstrip(" ,.") or "Untitled"


def split_script(spec: ProductionSpec) -> list[str]:
    """Groups the script's sentences into scenes of roughly the template's scene length."""
    sentences = split_sentences(spec.script)
    words = sum(len(s.split()) for s in sentences)
    seconds = TEMPLATES[spec.template].scene_seconds * PACING[spec.pacing]
    n = max(1, min(len(sentences), 40, round(words / WORDS_PER_SECOND / seconds) or 1))
    target = words / n
    groups: list[list[str]] = [[]]
    count = 0
    for i, sent in enumerate(sentences):
        if groups[-1] and len(groups) < n and (count >= target * len(groups) or len(sentences) - i <= n - len(groups)):
            groups.append([])
        groups[-1].append(sent)
        count += len(sent.split())
    return [" ".join(g) for g in groups if g]


SCRIPT_SYSTEM = """You are CreatorForge's AI Director. The narration script is FINAL and already split into
scenes; never change, add or remove words. For each scene, design ONE concrete filmable image (subject,
setting, action, lighting; no on-screen text) that illustrates what is being said, plus the edit.
Respond with JSON only."""


def direct_script(llm, spec: ProductionSpec) -> ProductionPlan:
    """Script mode: exact narration from the user; the LLM (if configured) plans visuals and the edit.
    Without an LLM, each scene's visual is derived from its own words."""
    segments = split_script(spec)
    if llm is None:
        plan = ProductionPlan(script_title(spec.script), "", "", "", [ShotPlan(seg, seg) for seg in segments])
        prompt_forge(plan, spec)
        return plan
    t = TEMPLATES[spec.template]
    numbered = "\n".join(f"{i + 1}. {seg}" for i, seg in enumerate(segments))
    chars = "\n".join(f"- {c.name}: {c.description}" for c in spec.characters) or "(none)"
    user = f"""FORMAT: {t.name}, aspect {spec.aspect}
TONE: {t.tone}
MOOD: {spec.mood or 'choose what fits'}
RECURRING CHARACTERS:
{chars}
SCENES (narration, final):
{numbered}

Return exactly this JSON shape with exactly {len(segments)} scenes in the same order:
{{"title": "short video title", "hook": "on-screen hook text, max 7 words", "cta": "on-screen call to action, max 6 words",
  "music_mood": "2-4 words",
  "scenes": [{{"visual": "...", "shot": "...", "camera": "...", "mood": "...", "overlay": "optional max 5 words or empty",
              "transition": "{' | '.join(TRANSITIONS)}", "emphasis": ["1-3 key words from this scene"], "hold": 0,
              "motion": "what physically moves during the shot"}}]}}"""
    error = ""
    for _ in range(2):
        raw = llm.complete_json(SCRIPT_SYSTEM, user if not error else f"{user}\n\nYour previous answer was invalid: {error}. Return corrected JSON only.")
        try:
            d = _extract_json(raw)
            scenes = d.get("scenes")
            if not isinstance(scenes, list) or len(scenes) != len(segments):
                raise ValueError(f"expected exactly {len(segments)} scenes")
            for sc, seg in zip(scenes, segments):
                if not isinstance(sc, dict):
                    raise ValueError("each scene must be an object")
                sc["narration"] = seg  # the user's words are authoritative
            plan = _validate(d, len(segments))
            break
        except (ValueError, json.JSONDecodeError) as e:
            error = str(e)
    else:
        raise ProviderError(f"AI Director returned an invalid shot list twice: {error}")
    prompt_forge(plan, spec)
    return plan
