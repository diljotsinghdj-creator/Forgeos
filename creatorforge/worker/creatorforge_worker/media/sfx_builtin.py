"""Built-in sound design, synthesised with ffmpeg on first use - nothing to download, nothing to license.
Whooshes for moving cuts, deep hits for hard cuts and reveals, a riser that builds into a twist, a soft pop
for callouts. Your own SFX folder / Asset Library sounds are used alongside these."""
from __future__ import annotations

import threading
from pathlib import Path

from . import ff

SOUNDS = {
    # name: lavfi graph producing mono 48 kHz audio
    "whoosh_air": "anoisesrc=d=0.65:c=pink:a=0.9:r=48000,highpass=f=500,lowpass=f=4000,"
                  "afade=t=in:d=0.42:curve=exp,afade=t=out:st=0.42:d=0.23,volume=1.2",
    "whoosh_low": "anoisesrc=d=0.55:c=brown:a=0.9:r=48000,lowpass=f=900,"
                  "afade=t=in:d=0.35:curve=exp,afade=t=out:st=0.35:d=0.2,volume=2.2",
    "impact_deep": "aevalsrc='0.9*sin(2*PI*(48+30*exp(-t*14))*t)*exp(-t*3.2)':d=1.1:s=48000,"
                   "lowpass=f=220,volume=0.85",
    "impact_punch": "aevalsrc='0.8*sin(2*PI*(70+90*exp(-t*30))*t)*exp(-t*7)+0.35*(random(0)-0.5)*exp(-t*40)':d=0.6:s=48000,"
                    "lowpass=f=1800",
    "riser_tension": "aevalsrc='0.35*sin(2*PI*(110+520*t*t/2.4)*t)*(t/1.6)+0.12*(random(0)-0.5)*(t/1.6)':d=1.6:s=48000,"
                     "highpass=f=90,afade=t=out:st=1.5:d=0.1",
    "pop_soft": "aevalsrc='0.6*sin(2*PI*(900-500*t/0.09)*t)*exp(-t*38)':d=0.12:s=48000",
}
_lock = threading.Lock()


def ensure(folder: Path) -> list[Path]:
    """Creates the built-in sounds once; returns their paths."""
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    with _lock:
        for name, graph in SOUNDS.items():
            p = folder / f"{name}.wav"
            if not p.is_file() or p.stat().st_size < 1000:
                tmp = p.with_suffix(".tmp.wav")
                ff.run(["-f", "lavfi", "-i", graph, "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(tmp)])
                tmp.replace(p)
            out.append(p)
    return out
