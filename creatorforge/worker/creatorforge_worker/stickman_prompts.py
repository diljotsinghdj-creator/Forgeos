"""Stickman video prompt pack: a script becomes ready-to-paste prompts for an AI video model (Gemini / Veo, or any
text-to-video tool), one per ~8-second shot, every prompt carrying the same character sheet and look so the stickman
stays the same from shot to shot.

    python -m creatorforge_worker.stickman_prompts script.txt --look stick_cozy [--aspect 9:16] [--character "..."]

The script can be a CreatorForge script (spoken lines with Visual:/Animate:/Text: directions) or plain text, in any
language: the voiceover stays in the script's own words, the directions to the video model are in English."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .director import ProductionSpec, parse_script
from .templates import STICKMAN_LOOKS

DEFAULT_LOOK = "stick_cozy"
CAMERAS = ["slow push in", "static wide shot", "gentle pan right", "medium shot, slight handheld drift",
           "slow pull back", "close-up, then a small zoom out"]
FRAMING = {"16:9": "16:9 landscape (YouTube)", "9:16": "9:16 vertical (Shorts / Reels)", "1:1": "1:1 square"}
WORDS_PER_S = 2.4          # Hindi and English narration both land near this pace
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def _lines(script: str) -> list[dict]:
    """The spoken lines with the writer's directions (visual, action, on-screen text) for each."""
    spoken, meta = parse_script(script)
    shots = meta.get("shots") or []
    out: list[dict] = []
    if shots:
        for line, visual, text, _stock, _chart, _draw, _bubble, extra in ((list(x) + [""] * 7 + [{}])[:8] for x in shots):
            extra = extra if isinstance(extra, dict) else {}
            out.append({"text": str(line).strip(), "visual": str(visual or ""), "action": str(extra.get("animate") or ""),
                        "on_screen": str(text or extra.get("big") or extra.get("statement") or "").replace("*", "")})
    else:
        clean = ProductionSpec.from_dict({"script": script}).script
        for line in [l.strip() for l in clean.splitlines() if l.strip()]:
            out.append({"text": line, "visual": "", "action": "", "on_screen": ""})
    # the script's heading (its name on the first line) is not narration
    clean = ProductionSpec.from_dict({"script": script}).script
    if out and spoken and spoken.splitlines()[0].strip() not in clean:
        head = spoken.splitlines()[0].strip()
        if out[0]["text"].startswith(head):
            out[0]["text"] = out[0]["text"][len(head):].strip()
    for x in out:          # writer labels ("ILLUSTRATION", "FICTIONAL") are for the edit, not for the video model
        if re.fullmatch(r"[\W_]*(illustration|fictional|example|representative|symbolic)[\W_]*", x["on_screen"], re.I):
            x["on_screen"] = ""
    return [x for x in out if x["text"]]


def _group(lines: list[dict], shot_seconds: float) -> list[list[dict]]:
    """Consecutive lines packed into shots of about shot_seconds of speech (a long line gets a shot of its own)."""
    groups, cur, n = [], [], 0.0
    for ln in lines:
        s = len(ln["text"].split()) / WORDS_PER_S
        if cur and n + s > shot_seconds:
            groups.append(cur)
            cur, n = [], 0.0
        cur.append(ln)
        n += s
    if cur:
        groups.append(cur)
    return groups


def build(script: str, look: str = DEFAULT_LOOK, aspect: str = "16:9", character: str = "",
          shot_seconds: float = 8.0, max_shots: int = 150) -> dict:
    look = look if look in STICKMAN_LOOKS else DEFAULT_LOOK
    name, style = STICKMAN_LOOKS[look]
    shot_seconds = max(4.0, min(10.0, float(shot_seconds or 8.0)))
    hero = (character or "").strip() or "the stickman exactly as described in the LOOK line"
    lines = _lines(script)
    if not lines:
        raise ValueError("the script has no spoken lines")
    groups = _group(lines, shot_seconds)[:max_shots]
    language = "Hindi" if _DEVANAGARI.search(" ".join(x["text"] for x in lines)) else "the script's language"
    sheet = (f"CHARACTER (identical in every shot): {hero}. Same proportions, same clothes, same colours, same line "
             f"style in every shot. No real people, no real faces, no logos or brand names.")
    look_line = (f"LOOK: {style}. Use this world, palette and drawing style whenever the scene doesn't name another "
                 f"place. {FRAMING.get(aspect, FRAMING['16:9'])}.")
    shots = []
    for i, g in enumerate(groups):
        said = " ".join(x["text"] for x in g)
        seconds = round(max(4.0, min(10.0, len(said.split()) / WORDS_PER_S + 0.6)), 1)
        visual = next((x["visual"] for x in g if x["visual"] and not _DEVANAGARI.search(x["visual"])), "")
        action = next((x["action"] for x in g if x["action"]), "")
        on_screen = next((x["on_screen"] for x in g if x["on_screen"]), "")
        scene = action or visual or f"the stickman acts out, clearly and simply, what the voiceover says"
        camera = CAMERAS[i % len(CAMERAS)]
        prompt = "\n".join(p for p in [
            f"SHOT {i + 1} of {len(groups)} - {seconds} seconds.",
            look_line,
            sheet,
            f"SCENE: {scene}. Every person in the scene is drawn as a stickman in this same style.",
            f"CAMERA: {camera}. Smooth, simple animation; expressive body language and eyebrows.",
            f"ON-SCREEN TEXT: \"{on_screen}\" (large, clean, readable)" if on_screen else "",
            f"VOICEOVER ({language}, spoken calmly and clearly, lip movement not needed): \"{said}\"",
            "Keep the character exactly as in the previous shots. No subtitles unless asked above.",
        ] if p)
        shots.append({"n": i + 1, "seconds": seconds, "voiceover": said, "scene": scene, "camera": camera,
                      "on_screen": on_screen, "prompt": prompt})
    total = round(sum(s["seconds"] for s in shots))
    head = (f"STICKMAN VIDEO PROMPT PACK - {name}\n{len(shots)} shots, about {total // 60}:{total % 60:02d} in total, "
            f"{FRAMING.get(aspect, FRAMING['16:9'])}.\nPaste one shot at a time into your video model (Gemini / Veo or "
            f"another). Generate shot 1 first; if the model can take a reference image, give it a still of shot 1 "
            f"for every later shot so the stickman stays the same.\n\n{sheet}\n{look_line}\n")
    text = head + "\n\n".join(f"===== SHOT {s['n']} =====\n{s['prompt']}" for s in shots) + "\n"
    return {"look": look, "look_name": name, "aspect": aspect, "character": hero, "seconds": total,
            "shots": shots, "text": text}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("script")
    ap.add_argument("--look", default=DEFAULT_LOOK, choices=sorted(STICKMAN_LOOKS))
    ap.add_argument("--aspect", default="16:9", choices=sorted(FRAMING))
    ap.add_argument("--character", default="")
    ap.add_argument("--shot-seconds", type=float, default=8.0)
    a = ap.parse_args(argv)
    pack = build(Path(a.script).read_text(encoding="utf-8"), a.look, a.aspect, a.character, a.shot_seconds)
    sys.stdout.write(pack["text"])


if __name__ == "__main__":
    main()
