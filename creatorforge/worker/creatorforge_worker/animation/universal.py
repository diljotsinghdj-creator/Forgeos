"""Universal studio demonstrations: five short films in five genres and styles, plus delivery-format checks.

    python -m creatorforge_worker.animation.universal <out_dir> [quality] [film ...]

1. history   "The Courier"            cinematic historical adventure - graphic novel, ancient world, desert
2. comedy    "Walkies"                humorous cartoon - a robot, a girl, a dog and a cat in the city
3. science   "The Body's Defenders"   science explainer - made by the automatic director from a plain script
4. drama     "The Letter"             dramatic story - painterly present, a remembered past in selective colour
5. wild      "Wild Worlds"            wildlife and fantasy - savanna, ocean, forest and a dragon

Every film is an editable production document (written next to the video as <name>.doc.json). The people and
stories are invented; the historical film is a fictional story in a historical setting, and it says so."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SKIN = {"a": [226, 186, 150], "b": [196, 140, 100], "c": [150, 100, 70], "d": [244, 214, 186]}


def history() -> dict:
    nef = {"name": "Neferu", "skin": SKIN["b"], "hair": "ponytail", "hair_color": [20, 16, 14],
           "shirt": [236, 226, 200], "skirt": [236, 226, 200], "pants": [150, 110, 70], "height": 1.66}
    elder = {"name": "Elder", "skin": SKIN["c"], "beard": True, "hair_color": [220, 220, 220], "shirt": [240, 236, 220],
             "skirt": [210, 190, 120], "height": 1.7, "hunch": 0.3, "cane": True}
    return {"title": "The Courier", "style": {"name": "graphic_novel"}, "fps": 24, "scenes": [
        {"id": "h1", "layers": {"world": "ancient", "light": [[0.0, "dawn"]]}, "timing": "drama",
         "cast": [{**nef, "x": -3.0, "facing": 1}, {**elder, "x": 1.2, "facing": -1}],
         "props": [{"name": "table", "asset": "table", "x": 0.75},
                   {"name": "scroll", "kind": "box", "x": 0.75, "y": 0.79, "w": 0.32, "h": 0.1,
                    "color": [236, 220, 170]}],
         "steps": [
             {"t": 0.2, "do": "fx", "kind": "caption", "text": "Egypt, the age of the pyramids. An invented story.",
              "dur": 3.2},
             {"t": 0.4, "who": "Neferu", "do": "walk", "to": 0.2},
             {"t": "+0.1", "who": "Elder", "do": "say", "text": "The river is rising. Warn the southern temple."},
             {"t": "+0.1", "who": "Neferu", "do": "nod"},
             {"t": "+0.1", "who": "Neferu", "do": "pick_up", "what": "scroll"},
             {"t": "+0.2", "who": "Neferu", "do": "say", "text": "I will be there by nightfall."},
             {"t": "+0.1", "who": "Neferu", "do": "turn", "facing": -1},
             {"t": "+0.1", "who": "Neferu", "do": "run", "to": -9.0}]},
        {"id": "h2", "layers": {"world": "desert", "light": [[0.0, "day"], [6.0, "dusk"]], "wind": 0.5},
         "cut": True, "timing": "drama",
         "cast": [{**nef, "x": -6.0, "facing": 1}],
         "creatures": [{"name": "Jackal", "species": "wolf", "x": 9.0, "facing": -1, "colour": [196, 160, 110]},
                       {"name": "Falcon", "species": "eagle", "x": -14.0, "y": 4.5, "scale": 0.6}],
         "props": [{"name": "rock", "asset": "rock", "x": 1.4}],
         "steps": [
             {"t": 0.2, "do": "fx", "kind": "caption", "text": "Across the desert, all day.", "dur": 2.6},
             {"t": 0.2, "do": "move", "what": "Falcon", "to": 10.0, "y": 5.2, "dur": 6.0, "ease": "linear",
              "wait": False},
             {"t": 0.3, "who": "Neferu", "do": "run", "to": 0.2, "speed": 3.8},
             {"t": "+0.0", "who": "Neferu", "do": "jump", "dist": 1.6, "height": 0.5},
             {"t": "+0.0", "do": "move", "what": "Jackal", "to": 4.0, "dur": 1.6, "wait": False},
             {"t": "+0.4", "do": "animal", "what": "Jackal", "act": "roar", "dur": 1.4, "wait": False},
             {"t": "+0.0", "do": "fx", "kind": "sfx", "text": "GRRR!", "at": "Jackal", "dur": 1.2, "color": [240, 160, 60]},
             {"t": "+0.0", "who": "Neferu", "do": "feel", "emotion": "frightened", "dur": 1.2},
             {"t": "+0.0", "who": "Neferu", "do": "step_back", "dist": 0.3},
             {"t": "+0.2", "who": "Neferu", "do": "gesture", "name": "shake_fist", "dur": 1.2},
             {"t": "+0.0", "do": "move", "what": "Jackal", "to": 12.0, "dur": 1.6, "wait": False},
             {"t": "+0.4", "who": "Neferu", "do": "run", "to": 9.0, "speed": 3.8}]},
        {"id": "h3", "layers": {"world": "ancient:rome", "light": [[0.0, "dusk"]]},
         "cut": True, "timing": "drama",
         "cast": [{**nef, "x": -4.5, "facing": 1},
                  {"name": "Priest", "skin": SKIN["a"], "shirt": [250, 250, 245], "skirt": [250, 250, 245],
                   "height": 1.74, "x": 1.5, "facing": -1},
                  {"name": "Crowd", "crowd": 4, "x": 3.4, "facing": -1, "spacing": 0.6}],
         "steps": [
             {"t": 0.2, "who": "Neferu", "do": "run", "to": -0.3, "speed": 3.4},
             {"t": "+0.0", "who": "Neferu", "do": "gesture", "name": "point", "dur": 1.0},
             {"t": "+0.0", "who": "Neferu", "do": "say", "text": "The flood is coming! Move to the high ground!"},
             {"t": "+0.1", "who": "Priest", "do": "feel", "emotion": "shocked", "dur": 1.2},
             {"t": "+0.0", "who": "Priest", "do": "say", "text": "Ring the bells. Everyone up the hill."},
             {"t": "+0.2", "who": "Crowd", "do": "gesture", "name": "cheer", "dur": 1.6},
             {"t": "+0.0", "do": "fx", "kind": "caption", "text": "The message arrived in time.", "dur": 3.0,
              "wait": True}]},
    ]}


def comedy() -> dict:
    bolt = {"name": "Bolt", "species": "robot", "height": 1.7}
    mia = {"name": "Mia", "skin": SKIN["d"], "hair": "ponytail", "hair_color": [190, 80, 40], "shirt": [250, 200, 60],
           "pants": [60, 90, 160], "height": 1.25, "girth": 0.9, "head": 1.25}
    return {"title": "Walkies", "style": {"name": "cartoon"}, "fps": 24, "scenes": [
        {"id": "c1", "layers": {"world": "city"}, "timing": "comedy",
         "cast": [{**mia, "x": -1.6, "facing": 1}, {**bolt, "x": 0.4, "facing": -1}],
         "creatures": [{"name": "Biscuit", "species": "dog", "x": -0.6, "facing": 1}],
         "steps": [
             {"t": 0.3, "who": "Mia", "do": "say", "text": "Bolt, take Biscuit for a walk. Gently!"},
             {"t": "+0.1", "who": "Bolt", "do": "say", "text": "WALK PROTOCOL ENGAGED."},
             {"t": "+0.0", "do": "animal", "what": "Biscuit", "act": "wag", "dur": 2.0, "wait": False},
             {"t": "+0.0", "who": "Bolt", "do": "gesture", "name": "wave", "dur": 1.2},
             {"t": "+0.2", "who": "Bolt", "do": "turn", "facing": 1},
             {"t": "+0.0", "who": "Bolt", "do": "walk", "to": 6.0, "speed": 1.0, "wait": False},
             {"t": "+0.0", "do": "move", "what": "Biscuit", "to": 6.6, "dur": 5.6}]},
        {"id": "c2", "layers": {"world": "city"}, "cut": True, "timing": "comedy",
         "cast": [{**bolt, "x": -3.0, "facing": 1}],
         "creatures": [{"name": "Biscuit", "species": "dog", "x": -2.3, "facing": 1},
                       {"name": "Cat", "species": "cat", "x": 6.0, "facing": -1}],
         "steps": [
             {"t": 0.3, "who": "Bolt", "do": "walk", "to": -1.0, "speed": 1.0, "wait": False},
             {"t": 0.3, "do": "move", "what": "Biscuit", "to": -0.3, "dur": 2.0},
             {"t": "+0.1", "do": "move", "what": "Cat", "to": 3.5, "dur": 1.5},
             {"t": "+0.0", "do": "animal", "what": "Biscuit", "act": "roar", "dur": 0.9, "wait": False},
             {"t": "+0.0", "do": "fx", "kind": "impact", "text": "WOOF!", "at": "Biscuit", "dur": 1.0},
             {"t": "+0.0", "do": "move", "what": "Cat", "to": 14.0, "dur": 1.6, "wait": False},
             {"t": "+0.1", "do": "move", "what": "Biscuit", "to": 13.0, "dur": 2.0, "wait": False},
             {"t": "+0.1", "who": "Bolt", "do": "feel", "emotion": "shocked", "dur": 0.6},
             {"t": "+0.0", "do": "fx", "kind": "speedlines", "at": "Bolt", "dur": 1.6, "wait": False},
             {"t": "+0.0", "who": "Bolt", "do": "run", "to": 4.0, "speed": 3.6},
             {"t": "+0.4", "do": "fx", "kind": "impact", "text": "CLANK!", "at": [5.3, 0.5], "dur": 1.0,
              "color": [120, 200, 255], "wait": False},
             {"t": "+0.0", "who": "Bolt", "do": "pratfall"},
             {"t": "+0.1", "who": "Bolt", "do": "say", "text": "ERROR. DOG NOT FOUND."}]},
        {"id": "c3", "layers": {"world": "city"}, "cut": True, "timing": "comedy",
         "cast": [{**mia, "x": 2.3, "facing": -1}, {**bolt, "x": -1.3, "facing": 1}],
         "creatures": [{"name": "Biscuit", "species": "dog", "x": 0.2, "facing": 1},
                       {"name": "Cat", "species": "cat", "x": 0.85, "facing": -1}],
         "steps": [
             {"t": 0.2, "do": "animal", "what": "Biscuit", "act": "sit", "dur": 7.0, "wait": False},
             {"t": 0.2, "do": "animal", "what": "Cat", "act": "sit", "dur": 7.0, "wait": False},
             {"t": 0.4, "who": "Mia", "do": "double_take", "at": "Biscuit"},
             {"t": "+0.0", "who": "Mia", "do": "say", "text": "They're... friends now?"},
             {"t": "+0.1", "who": "Bolt", "do": "say", "text": "MISSION SUCCESS. CELEBRATION MODE."},
             {"t": "+0.0", "who": "Bolt", "do": "dance", "beats": 8, "bpm": 120, "wait": False},
             {"t": "+0.4", "who": "Mia", "do": "gesture", "name": "facepalm", "dur": 1.6},
             {"t": "+0.0", "do": "fx", "kind": "sfx", "text": "TA-DA!", "sx": 0.5, "sy": 0.22, "dur": 1.4,
              "wait": True}]},
    ]}


SCIENCE_SCRIPT = ("Dr. Lena teaches her class about the immune system. Inside the body, white blood cells patrol "
                  "the bloodstream. A virus enters the body and starts copying itself. The white cells find the "
                  "virus and surround it. Antibodies stick to the virus so it cannot spread. Afterwards the body "
                  "remembers the virus, so the next defence is faster. Dr. Lena smiles at the class.")


def drama() -> dict:
    arun = {"name": "Arun", "skin": SKIN["b"], "hair": "short", "hair_color": [200, 200, 200], "mustache": True,
            "hunch": 0.45, "cane": True, "shirt": [120, 110, 100], "pants": [70, 66, 60], "height": 1.68}
    young = {"name": "Arun", "skin": SKIN["b"], "hair": "short", "hair_color": [30, 24, 20], "mustache": True,
             "shirt": [110, 120, 140], "pants": [50, 50, 60], "height": 1.74}
    priya = {"name": "Priya", "skin": SKIN["b"], "hair": "long", "hair_color": [24, 18, 16], "shirt": [200, 40, 50],
             "pants": [60, 50, 60], "height": 1.62}
    girl = {**priya, "height": 1.15, "head": 1.3, "girth": 0.88}
    return {"title": "The Letter", "fps": 24, "scenes": [
        {"id": "d1", "style": {"name": "painterly"}, "layers": {"world": "interior:home",
                                                                "light": [[0.0, "dusk"]]}, "timing": "drama",
         "cast": [{**arun, "x": 0.0, "facing": 1}],
         "props": [{"name": "table", "asset": "table", "x": 0.6},
                   {"name": "letter", "kind": "box", "x": 0.6, "y": 0.79, "w": 0.24, "h": 0.05,
                    "color": [250, 246, 236]}],
         "steps": [
             {"t": 0.2, "do": "fx", "kind": "caption", "text": "Thirty years without a word.", "dur": 3.0},
             {"t": 0.4, "who": "Arun", "do": "pick_up", "what": "letter"},
             {"t": "+0.2", "who": "Arun", "do": "posture", "lean": 0.25, "dur": 2.6},
             {"t": "+0.0", "who": "Arun", "do": "feel", "emotion": "sad", "dur": 2.4},
             {"t": "+0.2", "who": "Arun", "do": "say", "text": "\"Papa, I have a daughter now. Will you come?\""}]},
        {"id": "d2", "style": {"name": "noir", "key_hue": 355}, "layers": {"world": "city"}, "timing": "drama",
         "transition": {"kind": "dissolve", "dur": 0.8},
         "cast": [{**young, "x": -1.4, "facing": 1}, {**priya, "x": 1.4, "facing": -1}],
         "steps": [
             {"t": 0.2, "do": "fx", "kind": "caption", "text": "He remembered the night she left.", "dur": 2.8},
             {"t": 0.6, "who": "Priya", "do": "say", "text": "I'm going, Papa. With or without your blessing."},
             {"t": "+0.1", "who": "Arun", "do": "feel", "emotion": "angry", "dur": 1.4},
             {"t": "+0.0", "who": "Arun", "do": "gesture", "name": "cross_arms", "dur": 2.4},
             {"t": "+0.0", "who": "Arun", "do": "turn", "facing": -1},
             {"t": "+0.4", "who": "Priya", "do": "feel", "emotion": "crying", "dur": 1.8},
             {"t": "+0.0", "who": "Priya", "do": "turn", "facing": 1},
             {"t": "+0.0", "who": "Priya", "do": "walk", "to": 7.0, "speed": 1.1}]},
        {"id": "d3", "style": {"name": "painterly"},
         "layers": {"world": "city:night", "weather": [[0.0, 99.0, "rain", 0.8]], "wind": 0.2},
         "transition": {"kind": "dissolve", "dur": 0.8}, "timing": "drama",
         "cast": [{**arun, "x": -5.0, "facing": 1}, {**priya, "x": 2.2, "facing": -1, "shirt": [190, 60, 70]},
                  {**girl, "name": "Asha", "x": 3.0, "facing": -1}],
         "steps": [
             {"t": 0.2, "who": "Arun", "do": "walk", "to": 0.9, "speed": 0.7},
             {"t": "+0.1", "who": "Priya", "do": "feel", "emotion": "surprised", "dur": 1.2},
             {"t": "+0.0", "who": "Priya", "do": "say", "text": "Papa... you came."},
             {"t": "+0.2", "who": "Arun", "do": "say", "text": "I was wrong. I'm sorry."},
             {"t": "+0.2", "who": "Priya", "do": "comfort", "to": "Arun", "dur": 2.4},
             {"t": "+0.0", "who": "Arun", "do": "feel", "emotion": "crying", "dur": 2.0, "wait": False},
             {"t": "+0.3", "who": "Asha", "do": "gesture", "name": "wave", "dur": 1.4},
             {"t": "+0.0", "who": "Arun", "do": "feel", "emotion": "happy", "dur": 2.4},
             {"t": "+0.0", "do": "fx", "kind": "caption", "text": "Some letters take thirty years to answer.",
              "dur": 3.2, "wait": True}]},
    ]}


def wild() -> dict:
    voice = {"lang": "en", "rate": 150}
    return {"title": "Wild Worlds", "style": {"name": "painterly"}, "fps": 24, "scenes": [
        {"id": "w1", "layers": {"world": "savanna", "light": [[0.0, "dawn"], [5.0, "day"]]}, "timing": "explainer",
         "creatures": [{"name": "Elephant", "species": "elephant", "x": -9.0, "facing": 1},
                       {"name": "Calf", "species": "elephant", "x": -12.0, "facing": 1, "scale": 0.5},
                       {"name": "Lion", "species": "lion", "x": 5.0, "facing": -1, "acts": [[0.0, 99.0, "lie"]]},
                       {"name": "Bird1", "species": "bird", "x": -16.0, "y": 5.0, "colour": [40, 40, 50]}],
         "steps": [
             {"t": 0.2, "do": "caption", "text": "At dawn on the savanna, an elephant leads her calf to water.",
              "voice": {**voice, "say": "At dawn on the savanna, an elephant leads her calf to water."}, "wait": False},
             {"t": 0.3, "do": "move", "what": "Elephant", "to": 0.5, "dur": 7.0, "ease": "linear", "wait": False},
             {"t": 0.3, "do": "move", "what": "Calf", "to": -3.0, "dur": 7.0, "ease": "linear", "wait": False},
             {"t": 0.5, "do": "move", "what": "Bird1", "to": 12.0, "y": 6.0, "dur": 5.0, "ease": "linear",
              "wait": False},
             {"t": 4.0, "do": "animal", "what": "Lion", "act": "roar", "dur": 1.6, "wait": False},
             {"t": 7.6, "do": "wait", "dur": 0.4}]},
        {"id": "w2", "layers": {"world": "underwater"}, "cut": True, "timing": "explainer",
         "transition": {"kind": "dissolve", "dur": 0.7},
         "creatures": [{"name": "Whale", "species": "whale", "x": -14.0, "y": 2.0, "scale": 0.45, "facing": 1},
                       {"name": "Dolphin", "species": "dolphin", "x": 6.0, "y": 1.2, "facing": -1, "scale": 0.8},
                       {"name": "Fish1", "species": "fish", "x": -2.0, "y": 0.6},
                       {"name": "Fish2", "species": "fish", "x": -2.6, "y": 0.9, "colour": [250, 210, 60]},
                       {"name": "Fish3", "species": "fish", "x": -3.1, "y": 0.5}],
         "steps": [
             {"t": 0.2, "do": "caption", "text": "Under the sea, a whale glides past while dolphins play.",
              "voice": {**voice, "say": "Under the sea, a whale glides past while dolphins play."}, "wait": False},
             {"t": 0.2, "do": "move", "what": "Whale", "to": 2.0, "y": 2.4, "dur": 7.5, "ease": "linear", "wait": False},
             {"t": 0.4, "do": "move", "what": "Dolphin", "to": -4.0, "y": 2.4, "dur": 3.0, "wait": False},
             {"t": 3.5, "do": "move", "what": "Dolphin", "to": 3.0, "y": 0.8, "dur": 3.0, "wait": False},
             {"t": 0.3, "do": "move", "what": "Fish1", "to": 4.0, "y": 0.8, "dur": 7.0, "wait": False},
             {"t": 0.3, "do": "move", "what": "Fish2", "to": 3.4, "y": 1.1, "dur": 7.0, "wait": False},
             {"t": 0.3, "do": "move", "what": "Fish3", "to": 2.9, "y": 0.6, "dur": 7.0, "wait": False},
             {"t": 7.8, "do": "wait", "dur": 0.2}]},
        {"id": "w3", "layers": {"world": "forest", "light": [[0.0, "day"]]}, "cut": True, "timing": "explainer",
         "transition": {"kind": "dissolve", "dur": 0.7},
         "creatures": [{"name": "Deer", "species": "deer", "x": 0.0, "facing": 1, "acts": [[0.0, 3.0, "eat"]]},
                       {"name": "Wolf1", "species": "wolf", "x": -11.0, "facing": 1},
                       {"name": "Wolf2", "species": "wolf", "x": -12.5, "facing": 1},
                       {"name": "Fox", "species": "fox", "x": 4.0, "facing": -1, "acts": [[0.0, 9.0, "sit"]]}],
         "steps": [
             {"t": 0.2, "do": "caption", "text": "In the forest, a deer grazes. The wolves are hunting.",
              "voice": {**voice, "say": "In the forest, a deer grazes. The wolves are hunting."}, "wait": False},
             {"t": 1.2, "do": "move", "what": "Wolf1", "to": -4.0, "dur": 3.0, "wait": False},
             {"t": 1.3, "do": "move", "what": "Wolf2", "to": -5.5, "dur": 3.0, "wait": False},
             {"t": 3.6, "do": "move", "what": "Deer", "to": 16.0, "dur": 2.2, "ease": "linear", "wait": False},
             {"t": 4.2, "do": "move", "what": "Wolf1", "to": 14.0, "dur": 2.6, "ease": "linear", "wait": False},
             {"t": 4.3, "do": "move", "what": "Wolf2", "to": 12.0, "dur": 2.7, "ease": "linear", "wait": False},
             {"t": 7.5, "do": "wait", "dur": 0.3}]},
        {"id": "w4", "style": {"name": "anime"}, "layers": {"world": "castle"}, "cut": True,
         "transition": {"kind": "dissolve", "dur": 0.7}, "timing": "explainer",
         "creatures": [{"name": "Dragon", "species": "dragon", "x": -16.0, "y": 6.0, "scale": 0.6, "facing": 1},
                       {"name": "Unicorn", "species": "unicorn", "x": 3.0, "facing": -1, "acts": [[0.0, 3.0, "eat"]]}],
         "steps": [
             {"t": 0.2, "do": "caption", "text": "And in the stories we tell, a dragon comes home.", "voice": {**voice, "say": "And in the stories we tell, a dragon comes home."},
              "wait": False},
             {"t": 0.3, "do": "move", "what": "Dragon", "to": -2.0, "y": 2.5, "dur": 4.0, "wait": False},
             {"t": 3.3, "do": "animal", "what": "Unicorn", "act": "rear", "dur": 1.4, "wait": False},
             {"t": 4.4, "do": "animal", "what": "Dragon", "act": "breathe_fire", "dur": 1.6, "wait": False},
             {"t": 4.5, "do": "fx", "kind": "sfx", "text": "FWOOSH!", "at": "Dragon", "dur": 1.4},
             {"t": 6.2, "do": "move", "what": "Dragon", "to": -2.0, "y": 0.0, "dur": 1.4, "wait": False},
             {"t": 6.4, "do": "move", "what": "Unicorn", "to": 12.0, "dur": 1.6, "ease": "in", "wait": False},
             {"t": 8.2, "do": "wait", "dur": 0.4}]},
    ]}


DOCS = {"history": history, "comedy": comedy, "drama": drama, "wild": wild}


def run(out_dir: Path, quality: str = "final:1280x720@24", only: list | None = None, workers: int = 2) -> dict:
    from . import production, studio
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in ["history", "comedy", "science", "drama", "wild"]:
        if only and name not in only:
            continue
        t0 = time.time()
        out = out_dir / f"{name}.mp4"
        if name == "science":                          # the automatic director: script in, film out
            rep = studio.film(SCIENCE_SCRIPT, out, "The Body's Defenders", voice={"lang": "en", "rate": 150},
                              quality=quality, workers=workers, force=True)
            doc = json.loads(out.with_suffix(".doc.json").read_text())
        else:
            doc = DOCS[name]()
            out.with_suffix(".doc.json").write_text(json.dumps(doc, indent=1))
            rep = production.render(doc, out, quality, workers=workers)
            out.with_suffix(".report.json").write_text(json.dumps(rep, indent=1, default=str))
        results[name] = {"seconds_render": round(time.time() - t0, 1), "video": rep.get("video"),
                         "delivery": rep.get("delivery"), "subtitles": rep.get("subtitles"),
                         "styles": sorted({json.dumps(s_.get("style", doc.get("style"))) for s_ in doc["scenes"]}),
                         "worlds": [s_.get("layers", {}).get("world") for s_ in doc["scenes"]],
                         "decisions": (rep.get("notes") or {}).get("decisions", [])[:12]}
        (out_dir / "universal.json").write_text(json.dumps(results, indent=1, default=str))
    return results


FORMATS = [("16x9_1080p30", {"aspect": "16:9", "fps": 30}), ("9x16_1080x1920_30", {"aspect": "9:16", "fps": 30}),
           ("1x1_1080_24", {"aspect": "1:1", "fps": 24}), ("16x9_1080p60", {"aspect": "16:9", "fps": 60}),
           ("4k_2160p24", {"aspect": "4k", "fps": 24})]


def formats(out_dir: Path) -> dict:
    """The same short styled scene delivered in every format; each output's size, frame rate, codec and A/V sync
    are measured from the file."""
    from . import production
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scene = comedy()["scenes"][2]
    res = {}
    for name, fmt in FORMATS:
        doc = {"title": name, "style": {"name": "cartoon"}, "format": fmt,
               "scenes": [{**scene, "steps": scene["steps"][:4] + [{"t": "+0.5", "do": "wait", "dur": 0.1}]}]}
        t0 = time.time()
        rep = production.render(doc, out_dir / f"{name}.mp4", "final", workers=1)
        res[name] = {"delivery": rep["delivery"], "video": rep["video"], "seconds_render": round(time.time() - t0, 1)}
        (out_dir / "formats.json").write_text(json.dumps(res, indent=1, default=str))
    return res


if __name__ == "__main__":
    d = Path(sys.argv[1])
    q = sys.argv[2] if len(sys.argv) > 2 else "final:1280x720@24"
    if q == "formats":
        print(json.dumps(formats(d), indent=1, default=str))
    else:
        print(json.dumps(run(d, q, sys.argv[3:] or None), indent=1, default=str))
