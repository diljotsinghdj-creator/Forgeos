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
# Faceless channels: show people without showing faces - also avoids the uncanny, smeared faces image models make.
FACELESS = ("faceless framing: person seen from behind or in silhouette, face hidden or out of frame, "
            "hands and objects in focus, or a wide shot where people are small")
FACELESS_NEGATIVE = ", visible face, facial close-up, portrait, looking at camera"


_PEOPLE = re.compile(r"\b(person|people|man|men|woman|women|boy|girl|child|children|kid|kids|teen\w*|student\w*|"
                     r"crowd|worker\w*|scientist\w*|researcher\w*|someone|couple|friend\w*|guy|lady|soldier\w*|"
                     r"king|queen|doctor|nurse|teacher|mother|father|parent\w*|he|she|they|his|her|face\w*|"
                     r"portrait|character|figure|astronaut|detective|officer|audience|family|baby|old\s+\w+|young\s+\w+)\b",
                     re.I)


def _has_people(text: str) -> bool:
    return bool(_PEOPLE.search(text))


def _clip_words(text: str, n: int) -> str:
    words = text.split()
    return " ".join(words[:n]) + ("…" if len(words) > n else "")


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
    faces: str = "faceless"  # "faceless": people from behind / silhouettes / hands / wide shots | "show"
    video_quality: str = ""  # AI clip speed: "fast" | "balanced" | "best" ("" = the worker's default)
    ai_video_scenes: object = "all"  # with motion=ai_video: "all", "hook" (first scene) or a list of scene numbers (1-based)
    auto_edit: bool = True  # let the Director choose transitions, caption emphasis and dramatic holds
    character_ids: list[str] = field(default_factory=list)  # resolved from the Character Library at submit
    music_asset_id: str = ""  # use a track from the Asset Library as the score
    sfx: bool = True  # auto-place sound effects when an SFX folder or SFX assets exist
    script: str = ""  # script mode: the user's exact narration; the Director only plans visuals and the edit
    brand: dict = field(default_factory=dict)  # brand kit: logo, caption colours, intro/outro text

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
            video_quality=str(d.get("video_quality", "") or ""),
            faces=str(d.get("faces", "faceless") or "faceless"),
            auto_edit=bool(d.get("auto_edit", True)),
            character_ids=[str(x) for x in d.get("character_ids") or []][:10],
            script=clean_script(str(d.get("script", "") or "")),
            music_asset_id=str(d.get("music_asset_id", "") or ""),
            sfx=bool(d.get("sfx", True)),
            brand=clean_brand(d.get("brand")),
        )
        if spec.script and not d.get("idea"):
            spec.idea = script_heading(str(d.get("script", ""))) or spec.idea
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
        if self.faces not in ("faceless", "show"):
            raise ValueError("faces must be faceless or show")
        if self.video_quality not in ("", "fast", "balanced", "best"):
            raise ValueError("video_quality must be fast, balanced or best")
        if isinstance(self.ai_video_scenes, list):
            if not self.ai_video_scenes or not all(isinstance(n, int) and n >= 1 for n in self.ai_video_scenes):
                raise ValueError("ai_video_scenes must list scene numbers starting at 1")
        elif self.ai_video_scenes not in ("all", "hook"):
            raise ValueError("ai_video_scenes must be 'all', 'hook' or a list of scene numbers")

    def to_dict(self) -> dict:
        return asdict(self)


_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
LOGO_POSITIONS = ("top-right", "top-left", "bottom-right", "bottom-left")


def clean_brand(b) -> dict:
    """Brand kit: everything optional; bad values are rejected rather than silently rendered wrong."""
    if not b:
        return {}
    if not isinstance(b, dict):
        raise ValueError("brand must be an object")
    out: dict = {}
    for k in ("caption_color", "highlight_color"):
        if b.get(k):
            if not _HEX.match(str(b[k])):
                raise ValueError(f"brand.{k} must look like #FFD400")
            out[k] = str(b[k]).upper()
    if b.get("logo_asset_id"):
        out["logo_asset_id"] = str(b["logo_asset_id"])[:40]
        pos = str(b.get("logo_position") or "top-right")
        if pos not in LOGO_POSITIONS:
            raise ValueError(f"brand.logo_position must be one of {', '.join(LOGO_POSITIONS)}")
        out["logo_position"] = pos
        try:
            out["logo_opacity"] = min(1.0, max(0.2, float(b.get("logo_opacity", 0.85))))
        except (TypeError, ValueError):
            raise ValueError("brand.logo_opacity must be a number") from None
    for k, n in (("intro_text", 40), ("outro_text", 50), ("name", 60)):
        if str(b.get(k, "")).strip():
            out[k] = str(b[k]).strip()[:n]
    return out


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


RETENTION = """RETENTION RULES (viewers must watch to the end and replay):
- Second 1 is the hook: a curiosity gap, bold claim or tension. Never a greeting, intro or "in this video".
- Short spoken sentences (mostly under 12 words). One idea per sentence. No filler, no throat-clearing.
- Open loops: tease what's coming ("but that wasn't the strange part"), escalate every 2-3 sentences, save the payoff for the end.
- Concrete and visual: every sentence names something the viewer can SEE (a person, place, object, action).
- Videos of 60 seconds or less end with a LOOP: the last line flows straight back into the first line so the replay feels
  seamless. No "like and subscribe" at the end of a short; for longer videos a one-line CTA is fine."""

VISUAL_RULES = """VISUAL RULES (the picture must match the words):
- Each visual shows exactly what that scene's narration is saying - its key subject and action, literally.
- Keep the same main character, place, era and look across scenes (repeat the same descriptors every time).
- Vary the shot size scene to scene (wide, medium, close-up) so the edit feels alive.
- No text, captions, logos or signs in images."""

SYSTEM = """You are CreatorForge's AI Director and ScriptForge. You turn one idea into a complete,
production-ready short video plan: a scroll-stopping hook, a tight narrated script split into
scenes, a shot list and a call to action. Narration is spoken by a voice-over; visuals are
generated as still images, so every 'visual' must describe ONE concrete, filmable image
(subject, setting, action, lighting) with no on-screen text. Respond with JSON only.

""" + RETENTION + "\n\n" + VISUAL_RULES


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
      "hold": "seconds (0 to 0.5) to pause after the line for impact; almost always 0 - pauses lose viewers",
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
            hold = min(0.5, max(0.0, float(s.get("hold") or 0)))
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
        # SDXL reads only ~77 tokens: keep the subject short and put framing + quality early so they aren't cut.
        parts = [_clip_words(s.visual.rstrip("."), 40)]
        faceless = spec.faces == "faceless" and _has_people(f"{s.visual} {s.shot}")
        if faceless:
            parts.append(FACELESS)
        parts.append("sharp focus, highly detailed")
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
        s.negative = NEGATIVE + (FACELESS_NEGATIVE if faceless else "")
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


_LABEL = re.compile(r"^\s*(?:\*\*|__)?(?:voice\s*-?\s*over|vo|v\.o\.|narrator|narration|script|hook|cta|outro|intro)"
                    r"(?:\s*\([^)]*\))?\s*(?:\*\*|__)?\s*[:\-\u2013\u2014]\s*(?:\*\*|__)?", re.I)
_DIRECTION = re.compile(r"^\s*(?:\*\*|__)?(?:visuals?|on[- ]screen(?: text)?|text overlay|b-?roll|shot|camera|sfx|music|"
                        r"scene\s*\d*|title|caption|thumbnail|duration|\d+\s*[-\u2013]\s*\d+\s*s(?:ec)?)\b[^:]{0,30}:", re.I)


def _is_heading(line: str) -> bool:
    """A short line with no sentence punctuation, e.g. "Nobody Noticed (Brain Glitch)" or "# Episode 3"."""
    t = line.strip().strip("#*_ ").strip()
    return bool(t) and len(t.split()) <= 10 and not re.search(r"[.!?…]", t)


def script_heading(text: str) -> str:
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) > 1 and _is_heading(lines[0]) and not _LABEL.match(lines[0]):
        return lines[0].strip().strip("#*_ ").strip()[:80]
    return ""


def clean_script(text: str) -> str:
    """Keeps only the words to be spoken: drops a title line, "Voiceover:"-style labels, stage directions
    ("Visual: ...", "[cut to black]", "(beat)") and markdown, so pasted scripts aren't read out literally."""
    lines = [l for l in text.replace("\r", "").splitlines() if l.strip()]
    if script_heading(text):
        lines = lines[1:]
    out = []
    for line in lines:
        if _DIRECTION.match(line) and not _LABEL.match(line):
            continue
        line = _LABEL.sub("", line)
        line = re.sub(r"\[[^\]]*\]", " ", line)
        line = re.sub(r"^\s*\([^)]*\)\s*$", " ", line)
        line = re.sub(r"[*_#>`]+", "", line)
        line = re.sub(r"^\s*[-\u2022]\s+", "", line)
        line = re.sub(r"\s+", " ", line).strip().strip('"\u201c\u201d').strip()
        if line:
            out.append(line)
    return "\n".join(out).strip()


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
Respond with JSON only.

""" + VISUAL_RULES


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
    error, best = "", {}
    for _ in range(2):
        raw = llm.complete_json(SCRIPT_SYSTEM, user if not error else f"{user}\n\nYour previous answer was invalid: {error}. Return corrected JSON only.")
        try:
            d = _extract_json(raw)
            if isinstance(d, dict) and isinstance(d.get("scenes"), list):
                best = d
            scenes = d.get("scenes")
            if not isinstance(scenes, list) or len(scenes) != len(segments):
                raise ValueError(f"expected exactly {len(segments)} scenes, got {len(scenes) if isinstance(scenes, list) else 0}")
            for sc, seg in zip(scenes, segments):
                if not isinstance(sc, dict):
                    raise ValueError("each scene must be an object")
                sc["narration"] = seg  # the user's words are authoritative
            plan = _validate(d, len(segments))
            break
        except (ValueError, json.JSONDecodeError) as e:
            error = str(e)
    else:
        # Small local models often miscount long scripts. Never fail the video over it: keep the scenes it did
        # plan (in order) and give any missing ones a visual drawn from their own narration.
        plan = _repair(best, segments)
    prompt_forge(plan, spec)
    return plan


def _repair(d: dict, segments: list[str]) -> "ProductionPlan":
    got = [sc for sc in (d.get("scenes") or []) if isinstance(sc, dict)]
    scenes = []
    for i, seg in enumerate(segments):
        sc = dict(got[i]) if i < len(got) else {}
        if not str(sc.get("visual", "")).strip():
            sc["visual"] = seg
        sc["narration"] = seg
        scenes.append(sc)
    fixed = {**{k: v for k, v in d.items() if k != "scenes"}, "scenes": scenes}
    try:
        return _validate(fixed, len(segments))
    except ValueError:
        return ProductionPlan(script_title(" ".join(segments)), "", "", "", [ShotPlan(seg, seg) for seg in segments])
