"""The Brain Log (channels/BRAIN_LOG.md): every correction from the owner becomes a [BRAIN_LOG_PATCH] appended to
the log, and every film's engine, hook and metaphors go into the used-mechanics table so the next film on that
channel can't repeat them.

    python -m creatorforge_worker.studio.brainlog patch "<title>" "<mistake>" "<new rule>" "<retire>" "<winning pattern>"
    python -m creatorforge_worker.studio.brainlog used "<channel>" "<film>" "<engine>" "<hook>" "<metaphors>" "<status>"
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[3] / "channels" / "BRAIN_LOG.md"


def patch_block(title: str, mistake: str, rule: str, retire: str = "n/a", win: str = "", day: str = "") -> str:
    """The copy-pasteable [BRAIN_LOG_PATCH] block, as the showrunner directive asks for at the bottom of a reply."""
    day = day or _dt.date.today().isoformat()
    return (f"### {day}: {title.strip()}\n- **Mistake Logged:** {mistake.strip()}\n- **New Permanent Rule:** {rule.strip()}\n"
            f"- **Used Mechanics to Retire:** {retire.strip() or 'n/a'}\n- **Winning Pattern:** {win.strip() or 'n/a'}\n")


def append_patch(title: str, mistake: str, rule: str, retire: str = "n/a", win: str = "", path: Path | str = DEFAULT, day: str = "") -> str:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    block = patch_block(title, mistake, rule, retire, win, day)
    if block.split("\n", 1)[1] in text:          # the same patch twice is one patch
        return block
    p.write_text(text.rstrip("\n") + "\n\n" + block, encoding="utf-8")
    return block


def _cell(x: str) -> str:
    return str(x).replace("|", "/").replace("\n", " ").strip()


def record_used(channel: str, film: str, engine: str, hook: str, metaphors, status: str = "", path: Path | str = DEFAULT) -> None:
    """Adds (or updates, by channel and film) a row of the used-mechanics table."""
    p = Path(path)
    lines = p.read_text(encoding="utf-8").split("\n")
    mets = "; ".join(metaphors) if isinstance(metaphors, (list, tuple)) else str(metaphors)
    row = "| " + " | ".join(_cell(x) for x in (channel, film, engine, hook, mets, status)) + " |"
    head = next(i for i, ln in enumerate(lines) if ln.startswith("| Channel | Film"))
    end = head + 2
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    key = re.escape(f"| {_cell(channel)} | {_cell(film)} |")
    for i in range(head + 2, end):
        if re.match(key, lines[i]):
            lines[i] = row
            break
    else:
        lines.insert(end, row)
    p.write_text("\n".join(lines), encoding="utf-8")


def used(path: Path | str = DEFAULT) -> list[dict]:
    """The used-mechanics table as studio history rows (oldest first), for writer.novelty and writer.pitch."""
    out = []
    for ln in Path(path).read_text(encoding="utf-8").split("\n"):
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) == 6 and ln.startswith("|") and c[0] not in ("Channel", "---") and not set(c[0]) <= {"-"}:
            out.append({"channel": c[0].lower().replace(" ", "-"), "id": c[1], "engine": c[2].lower().replace(" ", "-"),
                        "hook_mechanism": c[3], "metaphors": [m.strip() for m in re.split(r"[;]", c[4]) if m.strip()], "status": c[5]})
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 4 and a[0] == "patch":
        print(append_patch(*a[1:6]))
    elif len(a) >= 6 and a[0] == "used":
        record_used(*a[1:7])
    else:
        print(__doc__)
        sys.exit(2)
