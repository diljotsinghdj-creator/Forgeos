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
    faces: str = "show"  # "show": expressive faces | "faceless": people from behind / silhouettes / hands / wide shots
    fast_cuts: bool = True  # split scenes into phrase-level beats (new picture every 1-2 s)
    film_grade: bool = True  # one consistent look: contrast, vignette, fine grain
    voice_speed: float = 1.0  # narration tempo (pitch kept); 1.1 is the common Shorts pace
    hook_text: str = ""  # on-screen hook, e.g. from a writer's "On-screen hook:" line
    visual_direction: str = ""  # the look of the whole video, e.g. "black-and-white 1950s lab footage"
    roles: list = field(default_factory=list)  # writer's story roles per line: [["TWIST", "Every single one..."]]
    publish: dict = field(default_factory=dict)  # title / cover / hashtags / source from the writer
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
        d = _script_pasted_as_idea(d)
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
            faces=str(d.get("faces", "show") or "show"),
            fast_cuts=bool(d.get("fast_cuts", True)),
            film_grade=bool(d.get("film_grade", True)),
            voice_speed=min(1.4, max(0.8, float(d.get("voice_speed", 1.0) or 1.0))),
            auto_edit=bool(d.get("auto_edit", True)),
            character_ids=[str(x) for x in d.get("character_ids") or []][:10],
            script=clean_script(parse_script(str(d.get("script", "") or ""))[0]),
            music_asset_id=str(d.get("music_asset_id", "") or ""),
            sfx=bool(d.get("sfx", True)),
            brand=clean_brand(d.get("brand")),
        )
        meta = parse_script(str(d.get("script", "") or ""))[1] if d.get("script") else {}
        if spec.script and not d.get("idea"):
            spec.idea = meta.get("title") or script_heading(parse_script(str(d.get("script", "")))[0]) or spec.idea
        spec.hook_text = str(d.get("hook_text") or meta.get("hook_text") or "").strip()[:80]
        spec.visual_direction = str(d.get("visual_direction") or meta.get("visual_direction") or "").strip()[:400]
        spec.roles = [list(r)[:2] for r in (d.get("roles") or meta.get("roles") or []) if len(r) >= 2][:60]
        spec.publish = d.get("publish") if isinstance(d.get("publish"), dict) else \
            {k: meta[k] for k in ("title", "cover", "hashtags", "source") if k in meta}
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
    emotion: str = ""  # the feeling on screen: shock, fear, suspicion, disgust, awe...
    # Fast cuts: the narration split into 2-4 phrases, each with its own picture, so the visual changes every
    # 1-2 seconds and always shows what is being said right then. [{"text","visual","emotion","prompt","negative"}]
    beats: list = field(default_factory=list)


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
      "motion": "what physically moves during the shot, e.g. 'robot arm lifts a crate, workers walk past, dust in light beams'",
      "emotion": "the feeling on screen, e.g. shock, fear, suspicion, disgust, awe, relief",
      "beats": {BEATS_SHAPE}}}
  ]}}
The scenes array must contain exactly {n} scenes. Scene 1 narration must open with the hook idea.
{BEATS_RULE}"""


BEATS_SHAPE = ('[{"text": "the exact words of this scene\'s narration for this beat (in order, together they cover the whole '
               'narration)", "visual": "one concrete image of exactly what those words say", '
               '"emotion": "facial expression / body language in this beat"}]')
BEATS_RULE = ("BEATS: split every scene's narration into 2-4 beats of about 3-7 spoken words (1-2 seconds each). Each beat gets "
              "its own picture showing exactly what those words say - a new subject, angle or close-up - so the video cuts "
              "every 1-2 seconds like a top Shorts edit. Same characters and place across beats. Put strong, readable "
              "emotion on faces when people appear (shock, fear, suspicion, disgust, awe).")


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
    if not 2 <= len(scenes) <= max(60, n * 3):   # the planned count is a guide; a good story may need more cuts
        raise ValueError(f"expected about {n} scenes, got {len(scenes)}")
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
                            motion=str(s.get("motion", "") or "").strip()[:300],
                            emotion=str(s.get("emotion", "") or "").strip()[:60], beats=_clean_beats(s.get("beats"))))
    return ProductionPlan(str(d.get("title", "")).strip()[:100] or "Untitled", str(d.get("hook", "")).strip()[:80],
                          str(d.get("cta", "")).strip()[:60], str(d.get("music_mood", "")).strip()[:60], out)


def _clean_beats(raw) -> list[dict]:
    """Keeps 2-4 well-formed beats; anything else means the scene stays one shot."""
    out = []
    for b in raw if isinstance(raw, list) else []:
        if isinstance(b, dict) and str(b.get("text", "")).strip() and str(b.get("visual", "")).strip():
            out.append({"text": str(b["text"]).strip()[:300], "visual": str(b["visual"]).strip()[:400],
                        "emotion": str(b.get("emotion", "") or "").strip()[:60]})
    return out[:8] if len(out) >= 2 else []


BEAT_WORDS = 5   # ~2 seconds of speech at 2.5 words/second: the longest a picture stays on screen


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _phrases(text: str, limit: int = BEAT_WORDS) -> list[str]:
    """Narration cut into spoken phrases of at most `limit` words, preferring breaks at punctuation."""
    out, cur = [], []
    for tok in text.split():
        cur.append(tok)
        if len(cur) >= limit or (len(cur) >= 3 and re.search(r"[.!?,;:\u2014\u2026]$", tok)):
            out.append(" ".join(cur))
            cur = []
    if cur:
        if out and len(cur) <= 2:
            out[-1] += " " + " ".join(cur)
        else:
            out.append(" ".join(cur))
    return out


BEATS_SYSTEM = """You are the picture editor of a viral faceless video. You get ONE scene's narration. Split it into
beats of 3-5 consecutive words (copy the words exactly, in order, covering every word). For each beat describe ONE
concrete image that literally shows what THOSE words say - the subject and action the viewer hears at that moment -
in the scene's setting with the same characters. Add the emotion on screen (facial expression or atmosphere).
Respond with JSON only: {"beats": [{"text": "...", "visual": "...", "emotion": "..."}]}"""


def _beats_match(beats: list[dict], narration: str) -> bool:
    import difflib
    said = _words(narration)
    planned = [w for b in beats for w in _words(b["text"])]
    return bool(said) and difflib.SequenceMatcher(None, said, planned).ratio() >= 0.85


def plan_beats(llm, plan: ProductionPlan, spec: ProductionSpec) -> None:
    """Fast cuts for every scene: a new picture at most every ~2 s, each showing exactly what is being said.
    Uses the Director's beats when they fit; otherwise asks the LLM one scene at a time (small models do this
    well); if that fails too, cuts the narration into phrases and illustrates each phrase directly."""
    chars = "\n".join(f"- {c.name}: {c.description}" for c in spec.characters) or "(none)"
    for s in plan.scenes:
        if len(_words(s.narration)) <= BEAT_WORDS + 1:
            s.beats = []            # a short line is already a quick shot
            continue
        ok = (s.beats and _beats_match(s.beats, s.narration)
              and all(len(_words(b["text"])) <= BEAT_WORDS + 2 for b in s.beats))
        if not ok and llm is not None:
            try:
                user = (f"SCENE SETTING: {s.visual}\nEMOTION: {s.emotion or 'what fits'}\nRECURRING CHARACTERS:\n{chars}\n"
                        f"NARRATION: {s.narration}")
                beats = _clean_beats(_extract_json(llm.complete_json(BEATS_SYSTEM, user)).get("beats"))
                if beats and _beats_match(beats, s.narration) and all(len(_words(b["text"])) <= BEAT_WORDS + 2 for b in beats):
                    s.beats, ok = beats, True
            except Exception:  # noqa: BLE001 - fall through to the phrase split
                pass
        if not ok:
            s.beats = [{"text": p, "visual": f"{p.strip(' .,!?')} - {s.visual}", "emotion": s.emotion}
                       for p in _phrases(s.narration)][:8]


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


def _image_prompt(visual: str, emotion: str, s: "ShotPlan", spec: ProductionSpec, style: str,
                  shot_size: str = "") -> tuple[str, str]:
    # SDXL reads only ~77 tokens: keep the subject short and put framing, emotion + quality early so they aren't cut.
    parts = [_clip_words(visual.rstrip("."), 30 if spec.visual_direction else 40)]
    if spec.visual_direction:
        parts.append(_clip_words(spec.visual_direction.split(",")[0], 8))   # the look, e.g. "black-and-white 1950s lab footage"
    people = _has_people(f"{visual} {s.shot}")
    faceless = spec.faces == "faceless" and people
    if faceless:
        parts.append(FACELESS)
        if emotion:
            parts.append(f"body language showing {emotion}")
    elif emotion and people:
        parts.append(f"face clearly showing {emotion}, intense expressive eyes, emotional")
    elif emotion:
        parts.append(f"{emotion} atmosphere")
    parts.append("sharp focus, highly detailed")
    shot = ", ".join(x for x in [f"{shot_size or s.shot} shot" if (shot_size or s.shot) else "", spec.camera or s.camera,
                                 f"{spec.mood or s.mood} mood" if (spec.mood or s.mood) else ""] if x)
    if shot:
        parts.append(shot)
    text = f"{visual} {s.narration}".lower()
    for c in spec.characters:
        if c.name.lower() in text:
            parts.append(f"{c.name}: {c.description}")
    parts.append(style)
    return ". ".join(parts), NEGATIVE + (FACELESS_NEGATIVE if faceless else ", blank expression, dead eyes")


def prompt_forge(plan: ProductionPlan, spec: ProductionSpec, only: int | None = None) -> None:
    """Builds each scene's generation prompt from the shot, Director Mode and characters."""
    t = TEMPLATES[spec.template]
    style = STYLE_PRESETS[spec.style][1] if spec.style in STYLE_PRESETS else (spec.style or t.style)
    for i, s in enumerate(plan.scenes):
        if only is not None and i != only:
            continue
        s.prompt, s.negative = _image_prompt(s.visual, s.emotion, s, spec, style)
        if not spec.fast_cuts:
            s.beats = []
        for k, b in enumerate(s.beats):
            # Alternate shot sizes so consecutive beats feel like real coverage, not the same frame twice.
            size = ("close-up", "medium", "extreme close-up", "wide")[(i + k) % 4] if k else (s.shot or "medium")
            b["prompt"], b["negative"] = _image_prompt(b["visual"], b.get("emotion") or s.emotion, s, spec, style, size)
        if s.beats:
            s.prompt, s.negative = s.beats[0]["prompt"], s.beats[0]["negative"]
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


# ---- writer's scripts: "0:05 SETUP A student thinks...", "On-screen hook: ...", "Visuals: ...", "Post: ..." ----------
_META_KEYS = ("on-screen hook", "on screen hook", "onscreen hook", "hook text", "visuals", "visual", "visual style",
              "b-roll", "broll", "post", "title", "cover", "thumbnail", "caption", "description", "hashtags", "tags",
              "source", "sources", "music", "sfx")
_META = re.compile(r"(?i)(?:^|(?<=[\s.]))(" + "|".join(re.escape(k) for k in sorted(_META_KEYS, key=len, reverse=True)) +
                   r")\s*:\s*")
_STAMP = re.compile(r"^\s*(?:[-\u2022*]\s*)?\(?(?:\d{0,2}:\d{2})(?:\s*[-\u2013]\s*\d{0,2}:\d{2})?\)?\s*")
_ROLE = re.compile(r"^\[?([A-Z][A-Z]+(?:[- ][A-Z]{2,})?)\]?\s*[:\-\u2013\u2014]?\s+(?=\S)")
# Story roles a writer tags lines with -> the feeling on screen and the cut into that moment.
ROLE_EDIT = {"HOOK": ("intrigue", "flash"), "STAKES": ("unease", ""), "SETUP": ("curiosity", ""),
             "GAP": ("suspense", ""), "TWIST": ("shock", "flash"), "REVEAL": ("shock", "flash"),
             "TURN": ("tension", "whip"), "PROOF": ("confident", ""), "NUMBER": ("surprise", "zoom"),
             "RE-HOOK": ("intrigue", "zoom"), "TAKEAWAY": ("calm resolve", "dissolve"), "PAYOFF": ("awe", "flash"),
             "LOOP": ("suspense", "dip"), "CTA": ("warm", "")}


def parse_script(raw: str) -> tuple[str, dict]:
    """Splits a writer's script into the words to speak and the direction around them: per-line story roles
    (HOOK, TWIST, ...), the on-screen hook, visual direction and posting details. Timestamps are dropped."""
    meta: dict = {"roles": []}
    spoken = []
    for line in raw.replace("\r", "").splitlines():
        parts = _META.split(line)
        body, pairs = parts[0], list(zip(parts[1::2], parts[2::2]))
        for key, value in pairs:
            k, v = key.lower().replace("on screen", "on-screen").replace("onscreen", "on-screen"), value.strip().rstrip(".")
            if k in ("on-screen hook", "hook text", "cover", "thumbnail"):
                meta.setdefault("hook_text" if "hook" in k else "cover", re.sub(r"#\w+", "", v).strip(" .")[:80])
            elif k in ("visuals", "visual", "visual style", "b-roll", "broll"):
                meta["visual_direction"] = (meta.get("visual_direction", "") + " " + v).strip()[:400]
            elif k in ("post", "title"):
                meta.setdefault("title", v[:100])
            elif k in ("hashtags", "tags"):
                meta["hashtags"] = re.findall(r"#\w+", v) or v.split()
            elif k in ("source", "sources"):
                meta["source"] = v[:200]
        tags = re.findall(r"#\w+", body + " ".join(v for _, v in pairs))
        if tags:
            meta["hashtags"] = list(dict.fromkeys(meta.get("hashtags", []) + tags))
        body = re.sub(r"#\w+", "", body)
        stamped = bool(_STAMP.match(body))
        body = _STAMP.sub("", body)
        m = _ROLE.match(body)
        if m and (stamped or m.group(1).replace(" ", "-") in ROLE_EDIT):
            body = body[m.end():]
            meta["roles"].append((m.group(1).replace(" ", "-"), body.strip()))
        if body.strip() and re.search(r"[A-Za-z]", body):
            spoken.append(body.strip())
    return "\n".join(spoken), meta


def apply_roles(plan: "ProductionPlan", roles: list) -> None:
    """Gives each scene the emotion and cut of the writer's role for the line it opens with."""
    for s in plan.scenes:
        said = _words(s.narration)
        for role, text in roles:
            head = _words(text)[:4]
            if head and " ".join(head) in " ".join(said[:12]):
                emotion, cut = ROLE_EDIT.get(role, ("", ""))
                s.emotion = s.emotion or emotion
                if cut:
                    s.transition = cut
                break


def _looks_like_script(text: str) -> bool:
    """A finished script pasted into the idea box: writer tags/timestamps/direction lines, or simply long prose."""
    if not text.strip():
        return False
    spoken, meta = parse_script(text)
    if meta["roles"] or meta.get("hook_text") or meta.get("visual_direction") or _STAMP.search(text):
        return True
    return len(_words(spoken)) >= 60 and len(split_sentences(spoken)) >= 5


def _script_pasted_as_idea(d: dict) -> dict:
    if not str(d.get("script", "") or "").strip() and _looks_like_script(str(d.get("idea", "") or "")):
        d = {**d, "script": d["idea"], "idea": ""}
    return d


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
        _apply_writer(plan, spec)
        prompt_forge(plan, spec)
        return plan
    t = TEMPLATES[spec.template]
    numbered = "\n".join(f"{i + 1}. {seg}" for i, seg in enumerate(segments))
    chars = "\n".join(f"- {c.name}: {c.description}" for c in spec.characters) or "(none)"
    direction = ""
    if spec.visual_direction:
        direction += f"VISUAL DIRECTION (the look of every shot - follow it): {spec.visual_direction}\n"
    if spec.roles:
        direction += "WRITER'S STORY ROLES (match the image and emotion to each role):\n" + \
            "\n".join(f"- {r}: {txt}" for r, txt in spec.roles) + "\n"
    user = f"""{direction}FORMAT: {t.name}, aspect {spec.aspect}
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
              "motion": "what physically moves during the shot",
              "emotion": "the feeling on screen, e.g. shock, fear, suspicion, disgust, awe",
              "beats": {BEATS_SHAPE}}}]}}
{BEATS_RULE} Beat texts must be copied word for word from that scene's narration."""
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
    _apply_writer(plan, spec)
    prompt_forge(plan, spec)
    return plan


def _apply_writer(plan: "ProductionPlan", spec: ProductionSpec) -> None:
    """The writer's own choices win: on-screen hook, title and per-role emotion and cuts."""
    if spec.roles:
        apply_roles(plan, spec.roles)
    if spec.hook_text:
        plan.hook = spec.hook_text
    if spec.publish.get("title"):
        plan.title = spec.publish["title"][:100]


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
