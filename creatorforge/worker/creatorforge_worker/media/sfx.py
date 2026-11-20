"""Auto-placed sound effects: whooshes on moving transitions, hits on hard cuts and the hook,
pops on on-screen callouts and the CTA. Sounds come from your own SFX folder or Asset Library;
files are matched to roles by name (e.g. whoosh_01.wav, impact_deep.mp3, pop.wav)."""
from __future__ import annotations

import functools
import hashlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .render import AUDIO_EXT

ROLES = {
    "projector": ("projector",),          # its own role, checked first: "click_projector" is not a callout pop
    "whoosh": ("whoosh", "swoosh", "swish", "woosh", "swipe", "transition"),
    "hit": ("hit", "impact", "boom", "thud", "punch", "slam"),
    "pop": ("pop", "click", "ding", "blip", "tick", "notification"),
    "riser": ("riser", "rise", "build", "tension", "swell"),
    "scribble": ("scribble", "pen", "marker", "pencil", "draw", "scratch"),
}
TRANSITION_ROLE = {"dive": "whoosh", "page": "whoosh", "push": "whoosh", "drop": "hit", "squeeze": "whoosh",
                   "whip": "whoosh", "blur": "whoosh", "slide": "whoosh", "wipe": "whoosh", "zoom": "whoosh", "reveal": "whoosh",
                   "cut": "hit", "flash": "hit", "dipcut": "hit"}
# which way a moving cut's whoosh travels: slides and wipes go the way the picture goes
SWEEP = {"slide": "rl", "wipe": "lr", "push": "rl", "whip": "rl"}
GAIN = {"projector": 0.5, "whoosh": 0.55, "hit": 0.6, "pop": 0.45, "riser": 0.4, "scribble": 0.5}
REVEALS = {"flash", "zoom"}   # twists / reveals: a riser builds into the cut, a deep hit lands on it


@dataclass
class SfxBank:
    sounds: dict[str, list[Path]] = field(default_factory=dict)

    @staticmethod
    def load(folder: str, extra: list[Path]) -> "SfxBank":
        files = list(extra)
        if folder and Path(folder).is_dir():
            files += [p for p in Path(folder).rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXT]
        bank = SfxBank({r: [] for r in ROLES})
        for p in sorted(set(files)):
            name = p.stem.lower()
            for role, words in ROLES.items():
                if any(w in name for w in words):
                    bank.sounds[role].append(p)
                    break
        return bank

    def any(self) -> bool:
        return any(self.sounds.values())

    def describe(self) -> str:
        return ", ".join(f"{len(v)} {k}" for k, v in self.sounds.items() if v)

    def pick(self, role: str, seed: str, avoid: Path | None = None) -> Path | None:
        """A take for this role; with two or more takes, never the one just used (the same whoosh on every cut is
        the most common tell of a template)."""
        options = self.sounds.get(role) or []
        if not options:
            return None
        i = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(options)
        if avoid is not None and len(options) > 1 and options[i] == avoid:
            i = (i + 1) % len(options)
        return options[i]


FRAME = 1 / 30          # an effect's peak lands one frame after its picture: light arrives before sound


@functools.lru_cache(maxsize=512)
def peak(path: Path) -> float:
    """Seconds from a sound's start to its loudest moment (within its first 3 s); 0 when it can't be read."""
    try:
        raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-t", "3", "-i", str(path), "-ac", "1", "-ar", "8000",
                              "-f", "s16le", "-"], capture_output=True, timeout=60).stdout
    except Exception:  # noqa: BLE001
        return 0.0
    if len(raw) < 4:
        return 0.0
    import array
    a = array.array("h", raw[: len(raw) // 2 * 2])
    best = max(range(len(a)), key=lambda k: abs(a[k]))
    return best / 8000.0


def place(bank: SfxBank, transitions: list[str], timings: list[float], overlays: list[tuple[float, str]],
          seed: str) -> list[tuple[Path, float, float]]:
    """Returns (sound, start seconds, gain). transitions[i] is the edit INTO scene i."""
    hits: list[tuple[Path, float, float]] = []
    if not bank.any():
        return hits
    offset = 0.0
    last: dict[str, Path] = {}
    for i, d in enumerate(timings):
        if i > 0:
            role = TRANSITION_ROLE.get(transitions[i])
            sound = bank.pick(role, f"{seed}:t{i}", last.get(role)) if role else None
            if sound:
                last[role] = sound
                # the sound's loudest moment lands on the cut (a whoosh swells into it), a hit one frame after it
                lead = peak(sound) - (0.0 if role == "whoosh" else FRAME)
                # stereo: a whoosh travels across the picture the way the cut does (alternating sides), a hit is centred
                pan = SWEEP.get(transitions[i], "lr" if i % 2 else "rl") if role == "whoosh" else 0.0
                hits.append((sound, max(0.0, offset - lead), GAIN[role], pan))
            riser = bank.pick("riser", f"{seed}:r{i}") if transitions[i] in REVEALS else None
            if riser and offset >= 1.6:
                hits.append((riser, offset - 1.55, GAIN["riser"]))
        offset += d
    for n, (start, style) in enumerate(overlays):
        role = {"Hook": "hit", "Callout": "pop", "CTA": "pop", "Draw": "scribble", "Bubble": "pop",
                "Think": "pop", "Big": "hit"}.get(style)
        sound = bank.pick(role, f"{seed}:o{n}", last.get(role)) if role else None
        if sound:
            last[role] = sound
            hits.append((sound, max(0.0, start + (0.05 if style == "Hook" else 0.0) + FRAME - peak(sound)), GAIN[role]))
    return sorted(hits, key=lambda h: h[1])


# Full-frame graphics get their own sound: the beat before a chapter or a big statement builds, the reveal lands.
GRAPHIC_CUES = {
    "chapter": (("riser", 1.5), ("hit", 0.0)), "statement": (("riser", 1.5), ("hit", 0.05)),
    "globe": (("whoosh", -0.1),), "map": (("whoosh", -0.1),),
    "chart": (("hit", 0.55),), "icons": (("pop", 0.2),), "timeline": (("pop", 0.25),),
    "steps": (("pop", 0.25),), "screen": (("whoosh", 0.45),), "document": (("whoosh", 0.25),),
    "quote": (("scribble", 0.6),), "split": (("whoosh", -0.1),),
    "object": (("whoosh", 0.0), ("pop", 1.2)), "article": (("whoosh", 0.25),),
    "slide": (("projector", 0.0),), "chat": (("pop", 0.25),), "search": (("pop", 0.15),), "pie": (("pop", 0.2),),
    "squares": (("pop", 0.25),), "timer": (("riser", -0.2),), "receipt": (("scribble", 0.2),),
}


def graphic_cues(bank: SfxBank, graphics: list[tuple[float, str]], seed: str) -> list[tuple[Path, float, float]]:
    """(sound, start, gain) for each full-frame graphic: a riser that ends as it appears, a hit or pop as it lands."""
    hits: list[tuple[Path, float, float]] = []
    last: dict[str, Path] = {}
    last_riser = -99.0
    for n, (at, kind) in enumerate(graphics):
        for role, lead in GRAPHIC_CUES.get(kind, ()):
            if role == "riser":
                if at < 1.6 or at - last_riser < 8:
                    continue                      # risers stay special: never back to back
                last_riser = at
                start = at - lead
            else:
                start = at + lead
            if role == "projector":
                named = bank.sounds.get("projector") or []
                sound = named[0] if named else bank.pick("pop", f"{seed}:g{n}:pop")
                if sound:
                    hits.append((sound, max(0.0, start), 0.5))
                continue
            sound = bank.pick(role, f"{seed}:g{n}:{role}", last.get(role))
            if sound:
                last[role] = sound
                if role != "riser":
                    start += FRAME - peak(sound)          # the hit's peak one frame after the picture lands
                hits.append((sound, max(0.0, start), GAIN[role] * (1.15 if kind in ("chapter", "statement") else 1.0)))
    return hits
