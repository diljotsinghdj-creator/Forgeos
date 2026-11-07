"""Project files for free desktop editors, written into the CreatorForge export zip next to the media they point at.

    shotcut_project.mlt   opens in Shotcut (and Kdenlive / any MLT editor): the scenes in order on V1 at their
                          timeline lengths, the voice-over on A1, the music on A2 at -18 dB
    openshot_import.edl   CMX3600 EDL for OpenShot (File > Import > EDL), DaVinci Resolve and Premiere: the same cut

Paths are relative to the unzipped folder, so the project opens wherever the zip is extracted."""
from __future__ import annotations

from xml.sax.saxutils import escape


def _frames(seconds: float, fps: int) -> int:
    return max(1, int(round(seconds * fps)))


def _attr(s: str) -> str:
    return escape(str(s), {'"': "&quot;"})


def mlt(title: str, items: list[dict], voice: str | None, music: str | None, width: int, height: int,
        fps: int = 30, voice_s: float | None = None) -> str:
    """items: [{"file": "media/01_scene.png", "seconds": 4.2, "image": True}] in timeline order."""
    from math import gcd
    g = gcd(width, height)
    total = sum(_frames(i["seconds"], fps) for i in items if i.get("file"))
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           f'<mlt LC_NUMERIC="C" version="7.0.0" title="{_attr(title)}" producer="main_bin">',
           f'  <profile description="CreatorForge {width}x{height} {fps}fps" width="{width}" height="{height}" '
           f'progressive="1" sample_aspect_num="1" sample_aspect_den="1" display_aspect_num="{width // g}" '
           f'display_aspect_den="{height // g}" frame_rate_num="{fps}" frame_rate_den="1" colorspace="709"/>',
           '  <playlist id="main_bin"><property name="xml_retain">1</property></playlist>',
           f'  <producer id="black" in="0" out="{max(0, total - 1)}"><property name="length">{total}</property>'
           '<property name="resource">0</property><property name="mlt_service">color</property></producer>',
           f'  <playlist id="background"><entry producer="black" in="0" out="{max(0, total - 1)}"/></playlist>']
    entries = []
    for n, it in enumerate(i for i in items if i.get("file")):
        f = _frames(it["seconds"], fps)
        svc = "qimage" if it.get("image") else "avformat-novalidate"
        extra = '<property name="ttl">1</property>' if it.get("image") else ""
        out.append(f'  <producer id="scene{n}" in="0" out="{f - 1}"><property name="length">{f}</property>'
                   f'<property name="resource">{_attr(it["file"])}</property><property name="mlt_service">{svc}</property>'
                   f'{extra}<property name="shotcut:caption">{_attr(it["file"].rsplit("/", 1)[-1])}</property></producer>')
        entries.append(f'    <entry producer="scene{n}" in="0" out="{f - 1}"/>')
    out += ['  <playlist id="v1"><property name="shotcut:video">1</property><property name="shotcut:name">V1</property>',
            *entries, '  </playlist>']
    tracks = ['    <track producer="background"/>', '    <track producer="v1"/>']
    audio_n = 0
    for pid, res, gain, name in (("voice", voice, None, "A1 voice-over"), ("music", music, -18, "A2 music")):
        if not res:
            continue
        length = _frames(voice_s, fps) if (pid == "voice" and voice_s) else total
        filt = (f'<filter><property name="mlt_service">volume</property><property name="level">{gain}</property></filter>'
                if gain is not None else "")
        out.append(f'  <producer id="{pid}" in="0" out="{length - 1}"><property name="length">{length}</property>'
                   f'<property name="resource">{_attr(res)}</property><property name="mlt_service">avformat-novalidate'
                   f'</property>{filt}</producer>')
        out.append(f'  <playlist id="pl_{pid}"><property name="shotcut:audio">1</property>'
                   f'<property name="shotcut:name">{name}</property>'
                   f'<entry producer="{pid}" in="0" out="{min(length, total) - 1}"/></playlist>')
        tracks.append(f'    <track producer="pl_{pid}" hide="video"/>')
        audio_n += 1
    out.append(f'  <tractor id="tractor0" title="{_attr(title)}" in="0" out="{max(0, total - 1)}">'
               '<property name="shotcut">1</property>')
    out += tracks
    out.append('    <transition><property name="a_track">0</property><property name="b_track">1</property>'
               '<property name="mlt_service">qtblend</property><property name="always_active">1</property></transition>')
    for k in range(audio_n + 1):                    # every track's sound reaches the output
        out.append(f'    <transition><property name="a_track">0</property><property name="b_track">{k + 1}</property>'
                   '<property name="mlt_service">mix</property><property name="always_active">1</property>'
                   '<property name="sum">1</property></transition>')
    out += ['  </tractor>', '</mlt>', '']
    return "\n".join(out)


def _tc(frames: int, fps: int) -> str:
    s, f = divmod(frames, fps)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}:{f:02d}"


def edl(title: str, items: list[dict], voice: str | None, fps: int = 30, voice_s: float | None = None) -> str:
    """CMX3600: one video event per scene on the record timeline, plus the voice-over on audio 1."""
    lines = [f"TITLE: {title[:60]}", "FCM: NON-DROP FRAME", ""]
    rec, n = 0, 0
    for it in items:
        if not it.get("file"):
            continue
        f = _frames(it["seconds"], fps)
        n += 1
        lines += [f"{n:03d}  AX       V     C        {_tc(0, fps)} {_tc(f, fps)} {_tc(rec, fps)} {_tc(rec + f, fps)}",
                  f"* FROM CLIP NAME: {it['file']}", ""]
        rec += f
    if voice:
        f = _frames(voice_s, fps) if voice_s else rec
        n += 1
        lines += [f"{n:03d}  AX       A     C        {_tc(0, fps)} {_tc(f, fps)} {_tc(0, fps)} {_tc(f, fps)}",
                  f"* FROM CLIP NAME: {voice}", ""]
    return "\n".join(lines)
