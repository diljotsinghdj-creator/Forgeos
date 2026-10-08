"""Auto-placed sound effects: whooshes on moving transitions, hits on hard cuts and the hook,
pops on on-screen callouts and the CTA. Sounds come from your own SFX folder or Asset Library;
files are matched to roles by name (e.g. whoosh_01.wav, impact_deep.mp3, pop.wav)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from .render import AUDIO_EXT

ROLES = {
    "whoosh": ("whoosh", "swoosh", "swish", "woosh", "swipe", "transition"),
    "hit": ("hit", "impact", "boom", "thud", "punch", "slam"),
    "pop": ("pop", "click", "ding", "blip", "tick", "notification"),
    "riser": ("riser", "rise", "build", "tension", "swell"),
}
TRANSITION_ROLE = {"whip": "whoosh", "slide": "whoosh", "wipe": "whoosh", "zoom": "whoosh", "reveal": "whoosh",
                   "cut": "hit", "flash": "hit"}
GAIN = {"whoosh": 0.55, "hit": 0.6, "pop": 0.45, "riser": 0.4}
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

    def pick(self, role: str, seed: str) -> Path | None:
        options = self.sounds.get(role) or []
        if not options:
            return None
        return options[int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(options)]


def place(bank: SfxBank, transitions: list[str], timings: list[float], overlays: list[tuple[float, str]],
          seed: str) -> list[tuple[Path, float, float]]:
    """Returns (sound, start seconds, gain). transitions[i] is the edit INTO scene i."""
    hits: list[tuple[Path, float, float]] = []
    if not bank.any():
        return hits
    offset = 0.0
    for i, d in enumerate(timings):
        if i > 0:
            role = TRANSITION_ROLE.get(transitions[i])
            sound = bank.pick(role, f"{seed}:t{i}") if role else None
            if sound:
                lead = 0.25 if role == "whoosh" else 0.0  # whooshes swell into the cut
                hits.append((sound, max(0.0, offset - lead), GAIN[role]))
            riser = bank.pick("riser", f"{seed}:r{i}") if transitions[i] in REVEALS else None
            if riser and offset >= 1.6:
                hits.append((riser, offset - 1.55, GAIN["riser"]))
        offset += d
    for n, (start, style) in enumerate(overlays):
        role = {"Hook": "hit", "Callout": "pop", "CTA": "pop"}.get(style)
        sound = bank.pick(role, f"{seed}:o{n}") if role else None
        if sound:
            hits.append((sound, max(0.0, start + (0.05 if style == "Hook" else 0.0)), GAIN[role]))
    return sorted(hits, key=lambda h: h[1])
