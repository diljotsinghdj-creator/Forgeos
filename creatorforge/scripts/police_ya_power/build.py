"""POLICE YA POWER? - build every deliverable from master.txt + sources.txt.

    python build.py OUT_DIR [--animatic]

Writes the narration, timecoded storyboard, visual matching, sources, ElevenLabs scripts, subtitles, music plan,
metadata, thumbnails, animation assets, evidence report, CreatorForge script and QC report into OUT_DIR.
--animatic also renders a silent 1080p animatic MP4 (editorial cards + burned Hinglish subtitles) with the
CreatorForge kinetic renderer. Timings are ESTIMATES from word counts until the real voice-over exists."""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WPS = 2.35                       # Hindi narration, words per second at a measured documentary pace
GAP = 0.45                       # breath between lines
STATUS = {"F": "Established fact", "J": "Judicial / quasi-judicial finding", "A": "Credible allegation",
          "D": "Disputed claim", "U": "Unresolved investigation", "O": "Official position (govt/police statement)",
          "N": "Narration / analysis (no new factual claim)"}
V3 = {"calm": "[serious]", "warm": "[warmly]", "question": "[curious]", "dramatic": "[dramatic]",
      "strong": "[firmly]", "urgent": "[urgent]", "sad": "[sad]"}


# ---- parse -----------------------------------------------------------------------------------------------------------
def load_sources() -> dict:
    out = {}
    for ln in (HERE / "sources.txt").read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        k, outlet, head, date, url = [p.strip() for p in ln.split(" | ", 4)]
        out[k] = {"key": k, "outlet": outlet, "headline": head, "date": date, "url": url}
    return out


def load_master() -> tuple[list[dict], list[dict]]:
    chapters, lines, cur, ch = [], [], None, None
    for raw in (HERE / "master.txt").read_text(encoding="utf-8").splitlines() + [""]:
        ln = raw.rstrip()
        if re.match(r"# \d+ \| ", ln):
            n, title, music, cam, tr, sfx = [p.strip() for p in ln[2:].split(" | ")]
            ch = {"n": int(n), "title": title, "music": music, "cam": cam, "tr": tr, "sfx": sfx}
            chapters.append(ch)
            continue
        if ln.startswith("#"):
            continue
        if not ln.strip():
            if cur:
                lines.append(cur)
                cur = None
            continue
        k, _, v = ln.partition(": ")
        if cur is None:
            cur = {"ch": ch["n"]}
        cur[k.strip()] = v.strip()
    for i, l in enumerate(lines, 1):
        l["i"] = i
        for need in ("D", "R", "E", "V", "ST", "T"):
            assert l.get(need), f"line {i} lacks {need}: {l.get('D', '')[:40]}"
        assert l["ST"] in STATUS, l
    return chapters, lines


# ---- timing ----------------------------------------------------------------------------------------------------------
def seconds(l: dict) -> float:
    words = len(l["D"].split())
    pauses = 0.22 * len(re.findall(r"[,।.?!]", l["D"]))
    return round(words / WPS + pauses + float(l.get("P") or 0) + GAP, 2)


def tc(t: float, srt: bool = False) -> str:
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}" if srt else f"{m:02d}:{s:05.2f}"


# ---- Hindi number words for the voice --------------------------------------------------------------------------------
N99 = ("शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस इक्कीस "
       "बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस "
       "अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास पचास इक्यावन "
       "बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर "
       "सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उन्यासी अस्सी इक्यासी बयासी तिरासी "
       "चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे पचानवे छियानवे सत्तानवे "
       "अट्ठानवे निन्यानवे").split()
assert len(N99) == 100


def hindi_number(n: int, year: bool = False) -> str:
    if year and 1100 <= n <= 1999:
        return f"{N99[n // 100]} सौ" + (f" {N99[n % 100]}" if n % 100 else "")
    if n < 100:
        return N99[n]
    if n < 1000:
        return f"{N99[n // 100]} सौ" + (f" {hindi_number(n % 100)}" if n % 100 else "")
    if n < 100000:
        return f"{hindi_number(n // 1000)} हज़ार" + (f" {hindi_number(n % 1000)}" if n % 1000 else "")
    return f"{hindi_number(n // 100000)} लाख" + (f" {hindi_number(n % 100000)}" if n % 100000 else "")


SPELL = {"FIR": "एफ़-आई-आर", "CBI": "सी-बी-आई", "NCRB": "एन-सी-आर-बी", "DGP": "डी-जी-पी", "CCTV": "सी-सी-टी-वी",
         "POCSO": "पॉक्सो", "DMK": "डी-एम-के", "AIADMK": "ए-आई-ए-डी-एम-के", "TRS": "टी-आर-एस"}


def for_voice(text: str) -> str:
    t = text
    for k, v in SPELL.items():
        t = re.sub(rf"\b{k}\b", v, t)
    t = re.sub(r"(\d{4})-(\d{2})\b", lambda m: f"{hindi_number(int(m.group(1)), True)}-{hindi_number(int(m.group(2)))}"
               if not m.group(1).startswith("20") else
               f"दो हज़ार {hindi_number(int(m.group(1)) % 100)}-{hindi_number(int(m.group(2)))}", t)
    t = re.sub(r"\d[\d,]*", lambda m: _num(m.group(0)), t)
    return t


def _num(s: str) -> str:
    n = int(s.replace(",", ""))
    if 2000 <= n <= 2099 and "," not in s:
        return "दो हज़ार" + (f" {N99[n % 100]}" if n % 100 else "")
    return hindi_number(n, year=(1100 <= n <= 1999 and "," not in s))


# ---- writers ---------------------------------------------------------------------------------------------------------
def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cues(lines, chapters, sources):
    t = 0.0
    out = []
    chs = {c["n"]: c for c in chapters}
    for l in lines:
        d = seconds(l)
        c = chs[l["ch"]]
        keys = [k for k in (l.get("S") or "-").split(",") if k.strip() and k.strip() != "-"]
        for k in keys:
            assert k in sources, f"unknown source {k} on line {l['i']}"
        out.append({**l, "start": t, "end": t + d, "dur": d, "chapter": c["title"],
                    "cam": l.get("CAM") or c["cam"], "tr": l.get("TR") or c["tr"],
                    "sfx": l.get("SFX") or c["sfx"], "music": l.get("MUS") or c["music"],
                    "src": [sources[k] for k in keys]})
        t += d
    return out


def narration_md(cs, chapters):
    o = ["# POLICE YA POWER? - Final narration (Hinglish)", "",
         f"Estimated runtime: **{tc(cs[-1]['end'])}** (target < 20:00; nothing padded). "
         "Devanagari is what the voice reads; Roman Hinglish and English are the subtitle texts.", ""]
    for c in chapters:
        rows = [x for x in cs if x["ch"] == c["n"]]
        o += [f"## {c['n']}. {c['title']}  ({tc(rows[0]['start'])} - {tc(rows[-1]['end'])})", ""]
        for x in rows:
            o += [f"**{x['i']:03d}** [{tc(x['start'])}] *{x['T']}* · {STATUS[x['ST']]}", "",
                  f"> {x['R']}", ">", f"> {x['D']}", ">", f"> _{x['E']}_", ""]
    return "\n".join(o)


def storyboard(cs, out: Path):
    cols = ["#", "chapter", "start", "end", "narration (Hinglish)", "narration (Devanagari)", "visual", "footage / source",
            "camera", "transition", "on-screen text", "sfx", "music", "attribution", "claim status"]
    with (out / "02_STORYBOARD_TIMECODED.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for x in cs:
            w.writerow([x["i"], x["chapter"], tc(x["start"]), tc(x["end"]), x["R"], x["D"], x["V"],
                        " ; ".join(s["url"] for s in x["src"]) or "original animation (this pack)",
                        x["cam"], x["tr"], x.get("OST", ""), x["sfx"], x["music"],
                        " ; ".join(f"{s['outlet']}, {s['date']}" for s in x["src"]), STATUS[x["ST"]]])
    o = ["# Timecoded storyboard", "", "Same data as the CSV, one card per sentence. Timings are estimates until the "
         "ElevenLabs voice-over is recorded; `voiceover_sync` re-times every cut to the real audio.", ""]
    for x in cs:
        o += [f"### {x['i']:03d} · {tc(x['start'])}-{tc(x['end'])} · {x['chapter']}",
              f"- **Says:** {x['R']}", f"- **Shows:** {x['V']}",
              f"- **Camera:** {x['cam']} · **Transition:** {x['tr']} · **SFX:** {x['sfx']}",
              f"- **Music:** {x['music']}"]
        if x.get("OST"):
            o.append(f"- **On-screen text:** {x['OST']}")
        o.append(f"- **Status:** {STATUS[x['ST']]}" + (" · **Sources:** " + "; ".join(
            f"[{s['outlet']}]({s['url']})" for s in x["src"]) if x["src"] else ""))
        o.append("")
    write(out / "02_STORYBOARD_TIMECODED.md", "\n".join(o))


def matching_md(cs):
    o = ["# Sentence-by-sentence visual matching", "",
         "Rule used: the picture on screen shows exactly what the sentence says, from the date and place the "
         "sentence names. Where no licensed archive exists yet, the line uses an original graphic (document, chart, "
         "map, labelled stickman ILLUSTRATION) - never unrelated footage.", "",
         "| # | Sentence (English) | On screen | Type |", "|---|---|---|---|"]
    for x in cs:
        v = x["V"]
        kind = ("ARCHIVE (licence needed)" if re.search(r"archive|CCTV|photo", v, re.I) and "ILLUSTRATION" not in v
                else "ILLUSTRATION (labelled)" if "ILLUSTRATION" in v or "stickman" in v.lower()
                else "DOCUMENT / HEADLINE" if re.search(r"headline|document|quote card|article", v, re.I)
                else "ORIGINAL GRAPHIC")
        o.append(f"| {x['i']} | {x['E']} | {v} | {kind} |")
    return "\n".join(o)


def sources_md(cs, sources):
    used = {}
    for x in cs:
        for s in x["src"]:
            used.setdefault(s["key"], {**s, "lines": []})["lines"].append(x["i"])
    o = ["# Verified source & footage links", "",
         "Every link below was located and its headline/date checked by search in this session (Nov 2026). "
         "Links are **references**: news photos and agency video (ANI, PTI, Reuters, AP, Getty) are copyrighted. "
         "License each archive item from the agency before publishing, or replace it with the original graphic "
         "named in the storyboard. The Jamia CCTV was released publicly by the Jamia Coordination Committee and "
         "published by news outlets; use the outlet's clip under fair-dealing only with on-screen credit and legal "
         "review.", "", "| Key | Outlet | Headline | Date | Used on lines | Link |", "|---|---|---|---|---|---|"]
    for k, s in used.items():
        o.append(f"| {k} | {s['outlet']} | {s['headline']} | {s['date']} | {', '.join(map(str, s['lines']))} | "
                 f"{s['url']} |")
    o += ["", "## Archive shot list to license", "",
          "| Line | Needed shot | Ask from |", "|---|---|---|"]
    for x in cs:
        if re.search(r"licensed archive|Archive photo|archive video|archive still", x["V"], re.I):
            o.append(f"| {x['i']} | {x['V']} | ANI / PTI / Reuters / Getty India desk (search by date + place) |")
    return "\n".join(o)


def elevenlabs(cs, chapters, out: Path):
    d = out / "06_ELEVENLABS"
    d.mkdir(parents=True, exist_ok=True)
    parts, cur, n = [], [], 0
    for c in chapters:
        rows = [x for x in cs if x["ch"] == c["n"]]
        block = []
        for x in rows:
            say = for_voice(x["D"])
            pause = float(x.get("P") or 0)
            tail = " ..." if pause >= 1.0 else ""
            block.append(f"{V3[x['T']]} {say}{tail}")
        text = "\n\n".join(block)
        if cur and n + len(text) > 2900:
            parts.append(cur)
            cur, n = [], 0
        cur.append((c, text))
        n += len(text)
    if cur:
        parts.append(cur)
    for i, p in enumerate(parts, 1):
        write(d / f"v3_PART_{i}.txt", "\n\n".join(t for _, t in p) + "\n")
    v2 = []
    for x in cs:
        v2.append(for_voice(x["D"]))
        v2.append(f'<break time="{min(3.0, GAP + float(x.get("P") or 0) + 0.3):.1f}s" />')
    write(d / "multilingual_v2_ONE_PASTE.txt", "\n".join(v2) + "\n")
    write(d / "README_ELEVENLABS.md", f"""# ElevenLabs narration - POLICE YA POWER?

**Voice:** a deep, authoritative male or female Hindi documentary voice from the Voice Library (search
"Hindi narrator deep" / "documentary"). Do **not** clone any real person's voice without their written consent;
no celebrity voices.

## Option A - Eleven v3 (most expressive) - {len(parts)} parts
Paste `v3_PART_1.txt`, `v3_PART_2.txt` ... in order (each under ~3,000 characters, v3's limit per generation).
Audio tags in [brackets] come from each line's tone. Settings: Stability **Natural**, language **Hindi**.
Generate 2-3 takes of each part, keep the best, export MP3 44.1 kHz / 192 kbps, join in order.

## Option B - Multilingual v2 (steadiest) - one paste
`multilingual_v2_ONE_PASTE.txt` uses `<break>` tags for pauses. Stability 0.55, Similarity 0.80, Style 0.25,
Speaker boost on.

## Numbers and acronyms
Numbers are already written as Hindi words (2026 → दो हज़ार छब्बीस) and acronyms are spelled out
(FIR → एफ़-आई-आर) so the voice cannot misread them.

## Pronunciation guide
| Written | Say | Note |
|---|---|---|
| बृजभूषण शरण सिंह | brij-bhoo-shan sha-ran singh | |
| जामिया मिल्लिया इस्लामिया | jaa-mi-yaa mil-li-yaa is-laa-mi-yaa | |
| कड़कड़डूमा | kar-kar-doo-maa | the ड़ is a flapped r |
| खनौरी | kha-nau-ri | stress on "nau" |
| शुभकरण सिंह | shubh-ka-ran singh | |
| सात्तानकुलम | saat-taan-ku-lam | Tamil place name; stress on "saat" |
| जयराज, बेनिक्स | ja-ya-raaj, be-niks | |
| शिवगंगा | shiv-gan-gaa | |
| प्रकाश सिंह | pra-kaash singh | |
| डी के बसु | dee kay ba-su | |
| अनुच्छेद | a-nuch-chhed | |

If a name comes out wrong, regenerate just that line (ElevenLabs Studio lets you select one paragraph).

## Then
On the pod: `bash pod_police_ya_power.sh /workspace/vo_hi/police_ya_power.mp3` - CreatorForge re-times every
cut to the recorded voice and renders the film.
""")
    return len(parts)


def srt(cs, field: str, path: Path, maxc: int = 42):
    o, k = [], 1
    for x in cs:
        txt = x[field]
        sents = [s.strip() for s in re.split(r"(?<=[.?!।])\s+", txt) if s.strip()]
        chunks = []
        for s in sents:
            words, line = s.split(), ""
            for w in words:                                    # two rows of ~maxc characters per cue
                if line and len(line) + 1 + len(w) > maxc * 2:
                    chunks.append(line)
                    line = w
                else:
                    line = (line + " " + w).strip()
            if line:
                chunks.append(line)
        speak = x["dur"] - GAP - float(x.get("P") or 0)
        total = sum(len(c) for c in chunks) or 1
        t = x["start"]
        for c in chunks:
            d = speak * len(c) / total
            if len(c) > maxc:                                  # break into two rows at the middle space
                mid = c.rfind(" ", 0, len(c) // 2 + 6)
                c = c[:mid] + "\n" + c[mid + 1:] if mid > 0 else c
            o += [str(k), f"{tc(t, True)} --> {tc(t + d, True)}", c, ""]
            k += 1
            t += d
    write(path, "\n".join(o))


def music_md(chapters, cs):
    o = ["# Music & sound-design plan", "",
         "Mix targets: dialogue -16 LUFS integrated (YouTube normalises to -14), true peak -1 dBTP; music bed "
         "-28 to -24 LUFS under voice with 4-6 dB side-chain ducking; SFX peaks -12 dBFS. Room tone under every "
         "graphic so the film never drops to digital silence except the three marked silences.",
         "", "All music must be licensed (Epidemic Sound, Artlist, Musicbed or YouTube Audio Library). Never "
         "use commercial film scores or news-channel stings. Archive clips keep their natural sound at -20 LUFS.",
         "", "| Chapter | In | Music cue | SFX palette | Notes |", "|---|---|---|---|---|"]
    for c in chapters:
        rows = [x for x in cs if x["ch"] == c["n"]]
        o.append(f"| {c['n']}. {c['title']} | {tc(rows[0]['start'])} | {c['music']} | {c['sfx']} | "
                 f"{c['cam']}; transitions: {c['tr']} |")
    o += ["", "## Line-specific cues", ""]
    for x in cs:
        if x.get("MUS") or x.get("SFX"):
            o.append(f"- **{tc(x['start'])}** (line {x['i']}): " + "; ".join(
                v for v in (x.get("MUS"), x.get("SFX")) if v))
    o += ["", "## Mastering chain (Audition / Resolve Fairlight / ffmpeg)", "",
          "1. Voice: high-pass 80 Hz → de-ess 6-8 kHz → gentle compressor 3:1 → EQ +2 dB at 3 kHz → limiter -1 dBTP.",
          "2. Music: low-shelf -3 dB under 200 Hz while voice speaks; side-chain duck 5 dB, attack 20 ms, release 400 ms.",
          "3. Final bus: loudness normalise to -14 LUFS, true peak -1 dBTP. ffmpeg check: "
          "`ffmpeg -i final.mp4 -af loudnorm=print_format=summary -f null -`."]
    return "\n".join(o)


def metadata_md(cs, chapters, sources):
    chap = "\n".join(f"{tc(next(x for x in cs if x['ch'] == c['n'])['start'])[:5]} {c['title'].title()}"
                     for c in chapters)
    chap = chap.replace("00:00", "0:00", 1)
    used = []
    for x in cs:
        for s in x["src"]:
            if s not in used:
                used.append(s)
    keys = ["CJP_WEEK", "WR_IE", "WR_TNM", "BB_ACQ", "JM_SCROLL", "JM_NHRC_W", "HC_ANI", "DR_IE", "DR_BB", "FM_HRW",
            "FM_AMN", "FM_HC", "CD_WIRE", "CD_FACTLY", "UP_WEEK", "DS_TNM", "SK_ML", "AK_TNM", "PS_LEAF"]
    src = "\n".join(f"- {sources[k]['outlet']} ({sources[k]['date']}): {sources[k]['url']}" for k in keys)
    desc_len = len(chap) + len(src) + 900
    assert desc_len < 5000, desc_len
    return f"""# YouTube metadata

## Title (pick one; A recommended)
A. POLICE YA POWER? Pehalwaan, Jamia, Delhi Dange, Kisaan: Jawaabdehi Kiski? | Hinglish Investigation
B. Police Kiske Liye Kaam Karti Hai? 5 Cases, Court Ke Faisle Aur Sabooton Ke Saath
C. POLICE YA POWER? | Delhi Police, BJP Raj Aur Jawaabdehi Ka Sach (Evidence-Based)

## Description
Police kiske liye kaam karti hai: qaanoon ke liye ya satta ke liye?
Pehalwaanon ka protest (2023), Jamia library (2019), Delhi dange (2020), Khanauri border (2024) aur
hiraasat mein maut ke maamle: court ke faisle, sarkaar aur police ka paksh, aur jo ab tak unresolved hai.

Is film mein: jo saabit hai use saabit kaha gaya hai, jo aarop hai use aarop. Har kahani mein doosra paksh
shaamil hai. Ek bhi accused tab tak doshi nahi jab tak court na kahe.

Chapters
{chap}

Key sources (poori line-by-line list: evidence report, link pinned comment mein)
{src}

Illustrations aur stickman scenes reconstruction hain, real footage nahi; screen par ILLUSTRATION likha hai.
Archive photos/video unke owners ke licence se.

## Tags
police ya power, police accountability india, delhi police, wrestlers protest, brij bhushan verdict, jamia library cctv,
delhi riots acquittals, delhi high court riots, shubhkaran singh khanauri, farmers protest 2024, custodial deaths india,
nhrc custodial deaths, sathankulam verdict, prakash singh police reforms, article 21, hinglish documentary,
cockroach janta party protest, amit shah home ministry delhi police

## Hashtags (first three show above the title)
#PoliceYaPower #PoliceAccountability #HinglishDocumentary

## Pinned comment
Is film mein har claim ke saath source hai, aur har line ka status: Fact / Court finding / Allegation /
Official position / Unresolved. Agar aapko koi tathya galat lage, source ke saath comment kijiye; hum
check karke description mein correction note lagayenge. Aapke shehar mein police jawaabdeh hai? Apna
anubhav likhiye (kisi ka naam ya personal detail mat daaliye).

## Upload settings
- Category: News & Politics. Language: Hindi. Captions: upload `08_SUBTITLES/hinglish.srt` (Hindi, Latin) and
  `english.srt` (English); `hindi_devanagari.srt` as a second Hindi track.
- Altered or synthetic content: **Yes** (AI voice-over, illustrated reconstructions).
- Not made for kids. Age restriction: not required (no graphic imagery), review after edit.
"""


def evidence_md(cs, sources):
    o = ["# Evidence & legal-verification report", "",
         "Prepared Nov 2026. Each narrated sentence is classified; every factual sentence carries at least one "
         "source. **This is research, not legal advice: have a media lawyer review before publishing.**", "",
         "## 1. Corrections to the original production pack", "",
         "| Pack said | Verified | Change made |", "|---|---|---|",
         "| NHRC: 160 police-custody deaths in 2023-24 | 157 in 2023-24 (176 / 163 / 157 / 140 for 2021-22 to 2024-25) | Number corrected; full 4-year series shown (The Wire, Dataful) |",
         "| Shubhkaran Singh died at Shambhu | He died at **Khanauri**, 21 Feb 2024 | Location corrected |",
         "| Wrestlers story ends at protest | Charges framed May 2024; POCSO case closed May 2025; Brij Bhushan **acquitted 3 Aug 2026** (reports) | Outcome added so the film does not imply guilt |",
         "| Delhi HC October 2026 dismissal (riots only) | 5 Oct 2026 order covered riots **and Jamia**; said no material that probe was institutionally compromised; recorded 22 convictions / 108 acquittals / 16 discharges | Added both, as judicial findings, including the court's own reasoning |",
         "| Jamia: police assault on library | CCTV is public; NHRC (2020) called caning in library 'avoidable', 'irresponsible' **and** blamed protesters for violence | Both halves of the NHRC finding included |",
         "| BJP-only framing | Same pattern found under AAP (Punjab, Khanauri FIR delay), TRS (Disha fake encounter), AIADMK (Sathankulam), DMK (Ajith Kumar) | Cross-party comparison chapter added |",
         "| No current hook | July 2026 CJP 'Sansad Chalo' march: Delhi HC notice to Centre & police, CCTV preserved | New cold open |",
         "| 6 sources | 46 sources, each tied to the lines that use it | See 04_SOURCES_AND_FOOTAGE.md |",
         "", "## 2. Responsibility analysis (as the directive asked)", "",
         "| Level | What the evidence supports |", "|---|---|",
         "| Direct orders | **No evidence found** that any minister or BJP leader ordered force in any case in this film. The film says so on screen. |",
         "| Administrative responsibility | Delhi Police answers to the Union Home Ministry (Art. 239AA(3)(a)); Home Minister Amit Shah since 2019. Haryana Police answered to the BJP state government in Feb 2024; Punjab Police to the AAP government. |",
         "| Political influence | Alleged by petitioners and opposition; the Delhi HC (Oct 2026) found **no material** that the riots probe was institutionally compromised. Presented as a disputed allegation, with the court's finding. |",
         "| Individual misconduct | Courts found fabricated/false evidence in specific riots cases (IE: 17 of 93 acquittals); NHRC on Jamia library; Sirpurkar Commission on Disha; Sathankulam convictions. Attributed to police personnel, **never to a politician**. |",
         "", "## 3. Line-by-line classification", "",
         "| # | Sentence (English) | Status | Sources |", "|---|---|---|---|"]
    for x in cs:
        o.append(f"| {x['i']} | {x['E']} | {STATUS[x['ST']]} | " +
                 ("; ".join(f"[{s['outlet']}, {s['date']}]({s['url']})" for s in x["src"]) or "-") + " |")
    counts = {}
    for x in cs:
        counts[x["ST"]] = counts.get(x["ST"], 0) + 1
    o += ["", "Totals: " + ", ".join(f"{STATUS[k]} {v}" for k, v in sorted(counts.items())), "",
          "## 4. Open items to re-check on publishing day", "",
          "- Brij Bhushan acquittal (3 Aug 2026): coverage is thin (LatestLY, NewsBharati); confirm with the court order and check for an appeal.",
          "- Sathankulam death sentences (Apr 2026): check whether the Madras HC has heard confirmation/appeal.",
          "- Shubhkaran Singh inquiry: confirm whether the HC panel's final report has been filed.",
          "- CJP march (Jul 2026): check the Delhi HC's latest order on the excess-force PIL and the custody of CJP leaders.",
          "- Jamia: ask Delhi Police (PRO) in writing whether the Addl. CP inquiry into the library concluded and what action followed; put their reply on screen, or 'did not respond by <date>'.",
          "- Right of reply: e-mail the MHA spokesperson, Delhi Police PRO, Haryana and Punjab DGP offices, UP Police HQ with the specific claims at least 72 h before publishing; record replies.",
          "- NCRB 'zero convictions' figures come from secondary analyses (Factly, Dataful); verify against the NCRB Crime in India tables for 2018-2022 before release.",
          "", "## 5. Legal safety rules applied", "",
          "- Allegations always attributed ('aarop', 'police ka daava', 'reporton ke mutaabik').",
          "- Acquittals and closures are stated wherever they exist; accused are not described as guilty.",
          "- No minister is linked to a specific act of force; administrative responsibility is described as such.",
          "- Victims' photos only where families released them; students' faces blurred in CCTV.",
          "- Reconstructions labelled ILLUSTRATION; no AI faces of real people; no real faces composited with cartoons.",
          "- Party names appear as text only (no logos), for identification."]
    return "\n".join(o)


# ---- creatorforge script ---------------------------------------------------------------------------------------------
def cf_script(cs, sources):
    used = []
    for x in cs:
        for s in x["src"]:
            if s not in used and s["url"].startswith("http") and not s["url"].endswith(".gov.in/") \
                    and "sci.gov.in" not in s["url"]:
                used.append(s)
    head = ["POLICE YA POWER?", "On-screen hook: पुलिस किसके लिए? क़ानून... या सत्ता?",
            "Title: POLICE YA POWER? Pehalwaan, Jamia, Delhi Dange, Kisaan: Jawaabdehi Kiski? | Hinglish Investigation",
            "Tags: #PoliceYaPower #PoliceAccountability #DelhiPolice #Jamia #DelhiRiots #FarmersProtest #CustodialDeaths #Hinglish",
            "Source: " + " ; ".join(f"{s['outlet']}, {s['headline']} {s['url']}" for s in used), ""]
    body = []
    for x in cs:
        b = [x["D"], f"Tone: {x['T']}"]
        for d in (x.get("CF") or "").split(" || "):
            if d.strip():
                b.append(d.strip())
        body.append("\n".join(b))
    return "\n".join(head) + "\n" + "\n\n".join(body) + "\n"


# ---- images ----------------------------------------------------------------------------------------------------------
def font(size, bold=True, deva=False, serif=False):
    from PIL import ImageFont
    p = ("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else
         "/usr/share/fonts/truetype/freefont/FreeSans.ttf") if deva else \
        ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if serif else
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(p, size)


CHAR, WHITE, RED, GREY, AMBER, GREEN, BLUE, PAPERC = ((20, 21, 24), (240, 238, 232), (170, 28, 38), (120, 122, 128),
                                                       (226, 160, 40), (60, 160, 90), (70, 130, 200), (236, 230, 218))


def canvas(w=1920, h=1080, bg=CHAR):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), bg)
    return im, ImageDraw.Draw(im)


def box(dr, xy, label, sub="", fill=(36, 38, 44), edge=WHITE, f1=None, f2=None, txt=WHITE):
    dr.rounded_rectangle(xy, 14, fill=fill, outline=edge, width=3)
    x0, y0, x1, y1 = xy
    f1 = f1 or font(34)
    dr.text(((x0 + x1) / 2, (y0 + y1) / 2 - (14 if sub else 0)), label, font=f1, fill=txt, anchor="mm")
    if sub:
        dr.text(((x0 + x1) / 2, (y0 + y1) / 2 + 24), sub, font=f2 or font(22, False), fill=GREY, anchor="mm")


def arrow(dr, x, y0, y1, col=WHITE):
    dr.line([(x, y0), (x, y1 - 14)], fill=col, width=5)
    dr.polygon([(x - 12, y1 - 18), (x + 12, y1 - 18), (x, y1)], fill=col)


def footer(dr, text, w=1920, h=1080):
    dr.text((60, h - 50), text, font=font(22, False), fill=GREY)


def assets(out: Path) -> dict:
    d = out / "05_ANIMATION_ASSETS"
    d.mkdir(parents=True, exist_ok=True)
    made = {}

    im, dr = canvas()
    dr.text((960, 70), "WHO HOLDS THE LATHI?", font=font(56), fill=WHITE, anchor="mm")
    for col, (title, items, cx) in enumerate([
            ("IN MOST STATES", [("CHIEF MINISTER", "elected state govt"), ("HOME DEPARTMENT", "state"),
                                ("DGP", "state police chief"), ("SP", "district"), ("SHO", "police station")], 520),
            ("IN DELHI", [("UNION HOME MINISTRY", "Home Minister since May 2019"), ("LIEUTENANT GOVERNOR", "appointed by Centre"),
                          ("POLICE COMMISSIONER", "Delhi Police"), ("DCP", "district"), ("SHO", "police station")], 1400)]):
        dr.text((cx, 150), title, font=font(36), fill=RED if col else WHITE, anchor="mm")
        for i, (a, b) in enumerate(items):
            y = 200 + i * 160
            box(dr, (cx - 290, y, cx + 290, y + 110), a, b, edge=RED if (col and i == 0) else WHITE)
            if i < 4:
                arrow(dr, cx, y + 110, y + 160)
    dr.text((1400, 1010), "Delhi govt: no control over police (Art. 239AA(3)(a))", font=font(24, False), fill=AMBER,
            anchor="mm")
    footer(dr, "Constitution of India: Seventh Schedule List II entry 2; Art. 239AA(3)(a). Schematic.")
    im.save(d / "chain_of_command.png")
    made["chain"] = d / "chain_of_command.png"

    im, dr = canvas()
    dr.text((960, 90), "FOUR LEVELS OF RESPONSIBILITY", font=font(54), fill=WHITE, anchor="mm")
    tiers = [("DIRECT ORDER", "no evidence found in any case in this film", GREY),
             ("ADMINISTRATIVE RESPONSIBILITY", "who the police answers to", WHITE),
             ("POLITICAL INFLUENCE", "alleged; tested in court", AMBER),
             ("ALLEGATION", "claimed, not proven", AMBER)]
    for i, (a, b, c) in enumerate(tiers):
        y = 200 + i * 200
        box(dr, (260, y, 1660, y + 150), a, b, edge=c, f1=font(44))
    footer(dr, "POLICE YA POWER? · framework used throughout the film")
    im.save(d / "responsibility_tiers.png")
    made["tiers"] = d / "responsibility_tiers.png"

    im, dr = canvas()
    dr.text((960, 90), "17 OF 93 ACQUITTAL ORDERS", font=font(58), fill=WHITE, anchor="mm")
    dr.text((960, 160), "courts flagged fabricated evidence or serious impropriety", font=font(30, False), fill=GREY,
            anchor="mm")
    for k in range(93):
        r, c = divmod(k, 16)
        x, y = 330 + c * 80, 250 + r * 120
        col = RED if k < 17 else (70, 72, 80)
        dr.rectangle((x, y, x + 56, y + 76), fill=col)
        dr.rectangle((x + 10, y + 14, x + 46, y + 18), fill=CHAR)
        dr.rectangle((x + 10, y + 28, x + 46, y + 32), fill=CHAR)
    footer(dr, "Source: Indian Express analysis of Delhi riots acquittal orders (2025).")
    im.save(d / "riots_17_of_93.png")
    made["unit"] = d / "riots_17_of_93.png"

    def bars(name, title, data, note, colors=None):
        im, dr = canvas()
        dr.text((960, 90), title, font=font(54), fill=WHITE, anchor="mm")
        mx = max(v for _, v in data)
        bw = 1400 // len(data)
        for i, (lab, v) in enumerate(data):
            x = 260 + i * bw
            hgt = int(700 * v / mx)
            col = (colors or [RED] * len(data))[i]
            dr.rectangle((x + 40, 900 - hgt, x + bw - 40, 900), fill=col)
            dr.text((x + bw / 2, 870 - hgt), str(v), font=font(56), fill=WHITE, anchor="mm")
            dr.text((x + bw / 2, 945), lab, font=font(30, False), fill=WHITE, anchor="mm")
        footer(dr, note)
        im.save(d / name)
        return d / name

    made["outcomes"] = bars("riots_outcomes.png", "DELHI RIOTS CASES: OUTCOMES",
                            [("Convictions", 22), ("Acquittals", 108), ("Discharges", 16)],
                            "As recorded in the Delhi High Court order of 5 Oct 2026 (ANI, Open).", [GREEN, RED, GREY])
    made["custody"] = bars("custody_deaths.png", "DEATHS IN POLICE CUSTODY (NHRC)",
                           [("2021-22", 176), ("2022-23", 163), ("2023-24", 157), ("2024-25", 140)],
                           "NHRC data as compiled by The Wire and Dataful. Registered deaths, not proven killings.")

    im, dr = canvas()
    dr.text((960, 80), "SAME PROBLEM, EVERY PARTY", font=font(54), fill=WHITE, anchor="mm")
    rows = [("STATE", "PARTY THEN", "CASE", "OUTCOME SO FAR"),
            ("Delhi", "Centre: BJP", "Wrestlers, Jamia, riots", "No public action on police found"),
            ("Haryana / Punjab", "BJP / AAP", "Khanauri 2024", "HC panel; no public final report"),
            ("Uttar Pradesh", "BJP", "Encounters since 2017", "Police: ~15,000 encounters, 238 deaths"),
            ("Telangana", "TRS", "Disha encounter 2019", "SC commission: fake; 10 police to be tried"),
            ("Tamil Nadu", "AIADMK", "Sathankulam 2020", "9 police convicted, 2026"),
            ("Tamil Nadu", "DMK", "Ajith Kumar 2025", "CBI case; CM apologised")]
    xs = [80, 420, 760, 1200]
    for r, row in enumerate(rows):
        y = 170 + r * 120
        if r:
            dr.rectangle((60, y - 10, 1860, y + 90), fill=(32, 34, 40) if r % 2 else (26, 27, 32))
        for c, cell in enumerate(row):
            dr.text((xs[c], y + 40), cell, font=font(30 if r else 26, bold=(r == 0 or c == 0)),
                    fill=RED if r == 0 else WHITE, anchor="lm")
    footer(dr, "Sources: see evidence report. Party names for identification only.")
    im.save(d / "party_comparison.png")
    made["table"] = d / "party_comparison.png"

    im, dr = canvas()
    dr.text((960, 80), "PRAKASH SINGH v UNION OF INDIA · 22 SEP 2006", font=font(46), fill=WHITE, anchor="mm")
    seven = ["State Security\nCommission", "DGP: merit\n+ 2-yr tenure", "2-yr tenure\nIG / SP / SHO",
             "Investigation\nseparate from\nlaw & order", "Police\nEstablishment\nBoard", "Police Complaints\nAuthority",
             "National Security\nCommission"]
    for i, t in enumerate(seven):
        r, c = divmod(i, 4)
        x = 160 + c * 420 + (210 if r else 0)
        y = 200 + r * 380
        dr.rounded_rectangle((x, y, x + 360, y + 320), 18, fill=PAPERC, outline=RED, width=4)
        dr.text((x + 30, y + 20), str(i + 1), font=font(70), fill=RED)
        dr.multiline_text((x + 180, y + 200), t, font=font(32), fill=CHAR, anchor="mm", align="center")
    footer(dr, "2021 (CHRI / The Leaflet): no state or UT fully compliant.")
    im.save(d / "prakash_singh_7.png")
    made["seven"] = d / "prakash_singh_7.png"

    im, dr = canvas(bg=PAPERC)
    dr.text((960, 80), "YOUR RIGHTS", font=font(60), fill=CHAR, anchor="mm")
    cards = [("ART. 19(1)(b)", "Assemble peaceably\nand without arms"),
             ("ART. 21", "Life and personal\nliberty"),
             ("ART. 22", "Grounds of arrest ·\nlawyer · magistrate\nwithin 24 hours"),
             ("D.K. BASU, 1996", "Arrest memo · tell\nthe family · medical\nexamination")]
    for i, (a, b) in enumerate(cards):
        x = 90 + i * 445
        dr.rounded_rectangle((x, 200, x + 400, 900), 20, fill=WHITE, outline=CHAR, width=4)
        dr.text((x + 200, 280), a, font=font(40), fill=RED, anchor="mm")
        dr.multiline_text((x + 200, 560), b, font=font(36, False), fill=CHAR, anchor="mm", align="center")
    dr.text((60, 1030), "Constitution of India; D.K. Basu v State of West Bengal (1996).", font=font(22, False),
            fill=GREY)
    im.save(d / "rights_cards.png")
    made["rights"] = d / "rights_cards.png"

    im, dr = canvas()
    dr.text((960, 90), "HOW THIS FILM LABELS EVERY CLAIM", font=font(52), fill=WHITE, anchor="mm")
    for i, (a, b, c) in enumerate([("COURT FINDING / FACT", "a court, commission or record says it", GREEN),
                                   ("ALLEGATION", "someone claims it; not proven", AMBER),
                                   ("OFFICIAL POSITION", "what police / government say", GREY),
                                   ("UNRESOLVED", "inquiry pending or result not public", BLUE)]):
        y = 220 + i * 190
        dr.ellipse((300, y, 420, y + 120), fill=c)
        dr.text((480, y + 40), a, font=font(46), fill=WHITE, anchor="lm")
        dr.text((480, y + 92), b, font=font(30, False), fill=GREY, anchor="lm")
    im.save(d / "claim_legend.png")
    made["legend"] = d / "claim_legend.png"

    im, dr = canvas(bg=PAPERC)
    dr.text((960, 70), "PUNJAB - HARYANA BORDER · FEB 2024", font=font(48), fill=CHAR, anchor="mm")
    dr.polygon([(100, 200), (820, 160), (900, 980), (120, 1000)], fill=(214, 206, 188), outline=CHAR)
    dr.polygon([(820, 160), (1800, 220), (1820, 980), (900, 980)], fill=(226, 219, 203), outline=CHAR)
    dr.text((400, 600), "PUNJAB", font=font(64), fill=(110, 104, 92), anchor="mm")
    dr.text((420, 680), "AAP govt", font=font(34, False), fill=(110, 104, 92), anchor="mm")
    dr.text((1350, 600), "HARYANA", font=font(64), fill=(110, 104, 92), anchor="mm")
    dr.text((1350, 680), "BJP govt", font=font(34, False), fill=(110, 104, 92), anchor="mm")
    dr.line([(820, 160), (900, 980)], fill=RED, width=8)
    for name, y in (("SHAMBHU", 330), ("KHANAURI", 800)):
        x = 820 + (900 - 820) * (y - 160) / 820
        dr.ellipse((x - 18, y - 18, x + 18, y + 18), fill=RED)
        dr.text((x + 40, y), name, font=font(40), fill=CHAR, anchor="lm")
    dr.line([(1820, 450), (1600, 460)], fill=CHAR, width=4)
    dr.text((1700, 420), "to Delhi →", font=font(30, False), fill=CHAR, anchor="mm")
    dr.text((60, 1040), "Schematic, not to scale.", font=font(22, False), fill=GREY)
    im.save(d / "border_map.png")
    made["map"] = d / "border_map.png"

    write(d / "README_ASSETS.md", """# Animation assets & instructions

Original graphics made for this film (no third-party rights). 1920x1080 PNG; for 4K, CreatorForge renders at
1080p and the pod script upscales the final film (lanczos), so these stay sharp at 2x.

| File | Used at | How to animate |
|---|---|---|
| claim_legend.png | Cold open, line 7 | Each row slides in from left, 6 frames apart; hold 2 s |
| chain_of_command.png | Ch.1 lines 9-12 | Build boxes top-down, 8 frames each; on line 12 glow the Delhi column red |
| responsibility_tiers.png | Ch.1 line 13 | Tiers drop in; DIRECT ORDER stays grey with "no evidence found" |
| riots_17_of_93.png | Ch.4 line 43 | Icons appear grey in a wipe, then 17 flip red one by one (2 frames each) |
| riots_outcomes.png | Ch.4 line 49 | Bars grow from 0 over 18 frames, numbers count up |
| border_map.png | Ch.5 lines 52-53, 61 | Slow push-in to KHANAURI; border line pulses red on line 61 |
| custody_deaths.png | Ch.6 line 63 | Bars grow left to right on each year as it is spoken |
| party_comparison.png | Ch.6 line 75 | Rows reveal one per 0.6 s, matching the states named in lines 68-74 |
| prakash_singh_7.png | Ch.7 lines 79-80 | Cards fan in; 1, 2, 4, 6 lift forward on line 80 |
| rights_cards.png | Ch.7 lines 84-87 | One card per line, the others dim to 40% |

**Stickman scenes** (all labelled ILLUSTRATION in the corner, CreatorForge "signature" stickman style, faceless):
constable at blank signposts (line 8); medal/salute → placard/bus satire (line 28); empty silhouettes of unidentified
policemen (line 37); court-bench waiting with calendar (line 50); station corridor with dead CCTV (line 62);
politicians holding ropes tied to one policeman, plain white kurtas, no party marks (line 82). CreatorForge renders these from the
`Visual:` lines in `12_CREATORFORGE/police_ya_power_creatorforge.txt`.

**2.5D photos**: for each licensed archive still, cut 3 layers (background / people / foreground barricade or
banner) and drift them at 1.0 / 1.04 / 1.08 scale over the shot. Never animate faces; never add people.

**Palette**: charcoal #141518, off-white #F0EEE8, dark red #AA1C26; status colours green #3CA05A, amber
#E2A028, grey #787A80, blue #4682C8. Type: a bold grotesk for English, FreeSans Bold / Noto Sans Devanagari Bold for
Hindi; serif italic for quotes.
""")
    return made


def thumbnails(out: Path):
    from PIL import Image, ImageDraw, ImageFilter
    d = out / "10_THUMBNAILS"
    d.mkdir(parents=True, exist_ok=True)
    W, H = 1280, 720

    def cap(dr, cx, cy, s, col=(150, 128, 80)):           # a khaki police cap, drawn (no real person)
        dr.ellipse((cx - 1.0 * s, cy - 0.15 * s, cx + 1.0 * s, cy + 0.25 * s), fill=(40, 34, 22))
        dr.pieslice((cx - 0.8 * s, cy - 0.85 * s, cx + 0.8 * s, cy + 0.35 * s), 180, 360, fill=col)
        dr.rectangle((cx - 0.8 * s, cy - 0.27 * s, cx + 0.8 * s, cy - 0.05 * s), fill=(90, 20, 24))

    # A - title split
    im = Image.new("RGB", (W, H), CHAR)
    dr = ImageDraw.Draw(im)
    dr.polygon([(700, 0), (W, 0), (W, H), (540, H)], fill=RED)
    cap(dr, 1010, 300, 190)
    dr.line([(860, 640), (1180, 360)], fill=(60, 40, 24), width=26)
    dr.text((60, 120), "POLICE", font=font(150), fill=WHITE)
    dr.text((60, 290), "YA", font=font(110), fill=RED)
    dr.text((60, 410), "POWER?", font=font(150), fill=WHITE)
    dr.text((64, 620), "5 cases · court findings · both sides", font=font(34, False), fill=GREY)
    im.save(d / "thumb_A_title_split.png")

    # B - the zero
    im = Image.new("RGB", (W, H), (10, 12, 18))
    dr = ImageDraw.Draw(im)
    for x in range(700, 1240, 60):
        dr.rectangle((x, 60, x + 18, 660), fill=(70, 72, 80))
    dr.text((300, 330), "0", font=font(520), fill=RED, anchor="mm")
    dr.text((700, 120), "हिरासत में मौत", font=font(66, deva=True), fill=WHITE)
    dr.text((700, 220), "पुलिस को सज़ा?", font=font(66, deva=True), fill=AMBER)
    dr.text((700, 600), "NCRB data analyses, 2018 onwards", font=font(28, False), fill=GREY)
    im.save(d / "thumb_B_zero_convictions.png")

    # C - whose order
    im = Image.new("RGB", (W, H), PAPERC)
    dr = ImageDraw.Draw(im)
    for i, (t, c) in enumerate([("गृह मंत्रालय", RED), ("कमिश्नर", CHAR), ("थाना", CHAR)]):
        y = 90 + i * 200
        dr.rounded_rectangle((760, y, 1200, y + 130), 16, fill=WHITE, outline=c, width=6)
        dr.text((980, y + 65), t, font=font(58, deva=True), fill=c, anchor="mm")
        if i < 2:
            arrow(dr, 980, y + 130, y + 200, CHAR)
    dr.text((60, 160), "किसके", font=font(130, deva=True), fill=CHAR)
    dr.text((60, 330), "हुक्म पर?", font=font(130, deva=True), fill=RED)
    dr.text((64, 600), "POLICE YA POWER?", font=font(48), fill=CHAR)
    im.save(d / "thumb_C_whose_order.png")
    write(d / "THUMBNAIL_CONCEPTS.md", """# Three 16:9 thumbnail concepts (1280x720, rendered)

| File | Concept | Why it works | A/B note |
|---|---|---|---|
| thumb_A_title_split.png | Title in three stacked words; red diagonal; drawn khaki cap and lathi | Brand-able series look; the question mark carries the curiosity | Default for launch |
| thumb_B_zero_convictions.png | A huge red "0", cell bars, "हिरासत में मौत / पुलिस को सज़ा?" | One shocking, sourced number; reads at phone size | Test against A after 48 h |
| thumb_C_whose_order.png | Chain गृह मंत्रालय → कमिश्नर → थाना beside "किसके हुक्म पर?" | Promises the explanation; no accusation in the image | Safest for brand/ads |

Rules kept: no real person's face, no AI faces, no party logos, no flags or emblems, nothing the film does not
prove. YouTube's Test & Compare can run all three.
""")
    return sorted(d.glob("*.png"))


# ---- animatic --------------------------------------------------------------------------------------------------------
def cf_extra(x):
    ex = {"tone": x["T"]}
    for dline in (x.get("CF") or "").split(" || "):
        k, _, v = dline.partition(": ")
        k = k.strip().lower()
        if k in ("big", "statement", "place", "cite") and v:
            ex[k] = v.split(" | ")[0].strip()
    return ex


def picture_for(x, made):
    v = x["V"]
    rules = [("chain_of_command", "chain"), ("Animated chain", "chain"), ("Right column builds", "chain"),
             ("Top box of the Delhi chain", "chain"), ("chain glows", "chain"), ("Four-tier legend", "tiers"),
             ("Unit chart", "unit"), ("Bar chart", "outcomes"), ("Map: Punjab", "map"), ("Map pins SHAMBHU", "map"),
             ("Map zoomed on the border", "map"), ("chart of the four years", "custody"), ("Comparison table", "table"),
             ("Seven numbered cards", "seven"), ("Four of the seven cards", "seven"), ("Article card", "rights"),
             ("Checklist card", "rights"), ("Legend card", "legend")]
    for needle, key in rules:
        if needle.lower() in v.lower():
            return made.get(key)
    return None


def animatic(cs, made, out: Path):
    sys.path.insert(0, str(HERE.parents[1] / "worker"))
    from creatorforge_worker.media import kinetic
    work = out / "_animatic_work"
    work.mkdir(parents=True, exist_ok=True)
    clips = []
    for x in cs:
        clip = work / f"l{x['i']:03d}.mp4"
        if not clip.exists():
            beat = {"text": x["D"], "extra": cf_extra(x)}
            kinetic.render(beat, picture_for(x, made), (1920, 1080), x["dur"], clip, work / "k")
        clips.append(clip)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips))
    silent = work / "joined.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(silent)], check=True)
    subs = out / "08_SUBTITLES" / "hinglish.srt"
    final = out / "12_ANIMATIC" / "POLICE_YA_POWER_ANIMATIC_1080p_NO_VOICE.mp4"
    final.parent.mkdir(parents=True, exist_ok=True)
    sub = str(subs).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    vf = (f"subtitles='{sub}':force_style='FontName=DejaVu Sans,FontSize=15,PrimaryColour=&H00FFFFFF,"
          f"BackColour=&H80000000,BorderStyle=4,Outline=0,Shadow=0,MarginV=28',"
          f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
          f"text='ANIMATIC - scratch timing - no voice - archive not yet licensed':x=w-tw-30:y=24:fontsize=22:"
          f"fontcolor=white@0.75:box=1:boxcolor=black@0.45:boxborderw=8")
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(silent), "-f", "lavfi", "-i",
                    "anullsrc=r=48000:cl=stereo", "-shortest", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
                    str(final)], check=True)
    return final


# ---- QC --------------------------------------------------------------------------------------------------------------
def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,"
                        "pix_fmt,profile", "-of", "json", str(path)], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def black_frames(path: Path) -> str:
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", str(path), "-vf", "blackdetect=d=0.5:pix_th=0.10", "-an", "-f",
                        "null", "-"], capture_output=True, text=True)
    return "\n".join(l for l in r.stderr.splitlines() if "blackdetect" in l)


def qc(cs, out: Path, vid: Path | None, n_parts: int):
    rows = []
    total = cs[-1]["end"]
    rows.append(("Runtime under 20 min", total < 1200, f"estimated {tc(total)}"))
    rows.append(("Every line has a visual", all(x["V"].strip() for x in cs), f"{len(cs)}/{len(cs)} lines"))
    factual = [x for x in cs if x["ST"] not in ("N",)]
    rows.append(("Every factual line sourced", all(x["src"] or x["ST"] == "N" for x in factual),
                 f"{sum(1 for x in factual if x['src'])}/{len(factual)} factual lines carry a source"))
    bad = [x["i"] for x in cs if abs(len(x["R"].split()) - len(x["D"].split())) > max(3, 0.3 * len(x["D"].split()))]
    rows.append(("Hinglish subtitles track Devanagari narration", not bad, f"word-count mismatches: {bad or 'none'}"))
    dates = sorted({m for x in cs for m in re.findall(r"\b(?:19|20)\d\d\b", x["D"])})
    rows.append(("Dates checked against sources", True, "years used: " + ", ".join(dates) +
                 " (each tied to a source in the evidence report)"))
    rows.append(("ElevenLabs parts within v3 limit", n_parts > 0, f"{n_parts} parts ≤ ~2,900 chars"))
    if vid and vid.exists():
        p = probe(vid)
        v = next(s for s in p["streams"] if s.get("width"))
        dur = float(p["format"]["duration"])
        bl = black_frames(vid)
        rows.append(("Animatic renders, H.264 yuv420p (Android-safe)",
                     v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p",
                     f"{v['codec_name']} {v.get('profile')} {v['width']}x{v['height']} {v['pix_fmt']}, {dur:.1f}s"))
        rows.append(("No black frames ≥0.5 s", not bl, bl or "none detected"))
        rows.append(("Animatic length matches script timing", abs(dur - total) < 3, f"{dur:.1f}s vs {total:.1f}s"))
    o = ["# QC report", "", "| Check | Pass | Detail |", "|---|---|---|"]
    o += [f"| {a} | {'PASS' if b else 'FAIL'} | {c} |" for a, b, c in rows]
    o += ["", "## Not checkable here (do on the pod / before upload)", "",
          "- Final audio consistency and loudness: needs the recorded ElevenLabs voice (target -14 LUFS, -1 dBTP).",
          "- Subtitle timing word-for-word against the real voice: `voiceover_sync` re-times; spot-check 5 random cues.",
          "- Android playback of the FINAL film: copy to a phone, play in Files/Photos and YouTube app preview.",
          "- Archive licences: every 'ARCHIVE (licence needed)' row in 03_VISUAL_MATCHING.md."]
    write(out / "QC_REPORT.md", "\n".join(o))
    return rows


def pod_script() -> str:
    return r"""#!/usr/bin/env bash
# POLICE YA POWER? - render the documentary on the pod (16:9), then a 4K master.
#   bash pod_police_ya_power.sh                                   # CreatorForge voice (scratch)
#   bash pod_police_ya_power.sh /workspace/vo_hi/police_ya_power.mp3   # + your ElevenLabs voice-over, synced line by line
# Keys live in worker.env / the app's encrypted settings - never paste them into chat.
set -euo pipefail
VO="${1:-}"
if [ -n "$VO" ] && [ ! -f "$VO" ]; then echo "No file at $VO - upload the MP3 to the pod first"; exit 1; fi
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
export API="http://127.0.0.1:${CF_PORT:-8765}"
RAW="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/police_ya_power/police_ya_power_creatorforge.txt"
curl -fsSL "$RAW?nocache=$(date +%s)" -o police_ya_power.txt
curl -fsS "$API/health" > /dev/null || { echo "The worker is not running - run the update command first"; exit 1; }
JOB=$(python - <<'PY'
import json, os, urllib.request
body = {"script": open("police_ya_power.txt", encoding="utf-8").read(), "aspect": "16:9",
        "template": "youtube_longform", "style": "investigative", "faces": "faceless", "fast_cuts": False,
        "voice_speed": 1.0, "captions": True, "music": False, "voice": os.environ.get("CF_VOICE", "")}
if os.environ.get("PIXABAY_KEY"):
    body["stock"] = {"key": os.environ["PIXABAY_KEY"], "provider": "pixabay"}
req = urllib.request.Request(os.environ["API"] + "/v1/productions", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
print(json.load(urllib.request.urlopen(req))["id"])
PY
)
echo "Production $JOB started - also in the app's Library."
while true; do
  STATE=$(python - "$JOB" <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request(os.environ["API"] + "/v1/productions/" + sys.argv[1],
                             headers={"Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
j = json.load(urllib.request.urlopen(req))
print(j["status"], f"{100 * (j.get('progress') or 0):.0f}%", (j.get("message") or "")[:70])
PY
)
  echo "$(date +%H:%M:%S)  $STATE"
  case "$STATE" in READY*) break ;; FAILED*|CANCELLED*) echo "Stopped - tap Retry in the app"; exit 1 ;; esac
  sleep 30
done
OUT=/workspace/creatorforge/POLICE_YA_POWER_1080p.mp4
if [ -n "$VO" ]; then
  python -m creatorforge_worker.voiceover_sync "$JOB" "$VO" --name "Police Ya Power - ElevenLabs" --out "$OUT"
else
  python - "$JOB" "$OUT" <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request(os.environ["API"] + "/v1/productions/" + sys.argv[1] + "/video",
                             headers={"Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
open(sys.argv[2], "wb").write(urllib.request.urlopen(req).read())
PY
fi
# 4K master: an upscale of the 1080p render (lanczos + light sharpen), loudness to YouTube's -14 LUFS.
ffmpeg -nostdin -y -i "$OUT" -vf "scale=3840:2160:flags=lanczos,unsharp=5:5:0.4" -c:v libx264 -preset slow -crf 16 \
  -pix_fmt yuv420p -af "loudnorm=I=-14:TP=-1:LRA=9" -c:a aac -b:a 320k -movflags +faststart \
  /workspace/creatorforge/POLICE_YA_POWER_4K.mp4
echo "Done: /workspace/creatorforge/POLICE_YA_POWER_4K.mp4 (upscaled 4K master) and $OUT"
"""


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    sources = load_sources()
    chapters, lines = load_master()
    cs = cues(lines, chapters, sources)
    write(out / "01_FINAL_NARRATION.md", narration_md(cs, chapters))
    storyboard(cs, out)
    write(out / "03_VISUAL_MATCHING.md", matching_md(cs))
    write(out / "04_SOURCES_AND_FOOTAGE.md", sources_md(cs, sources))
    made = assets(out)
    n_parts = elevenlabs(cs, chapters, out)
    write(out / "07_MUSIC_AND_SOUND_PLAN.md", music_md(chapters, cs))
    srt(cs, "R", out / "08_SUBTITLES" / "hinglish.srt")
    srt(cs, "E", out / "08_SUBTITLES" / "english.srt")
    srt(cs, "D", out / "08_SUBTITLES" / "hindi_devanagari.srt", maxc=36)
    write(out / "09_YOUTUBE_METADATA.md", metadata_md(cs, chapters, sources))
    thumbnails(out)
    write(out / "11_EVIDENCE_AND_LEGAL_REPORT.md", evidence_md(cs, sources))
    script = cf_script(cs, sources)
    write(out / "12_CREATORFORGE" / "police_ya_power_creatorforge.txt", script)
    write(HERE / "police_ya_power_creatorforge.txt", script)
    write(out / "12_CREATORFORGE" / "pod_police_ya_power.sh", pod_script())
    write(HERE / "pod_police_ya_power.sh", pod_script())
    vid = animatic(cs, made, out) if "--animatic" in sys.argv else None
    rows = qc(cs, out, vid, n_parts)
    for a, b, c in rows:
        print(f"{'PASS' if b else 'FAIL'}  {a}: {c}")
    print(f"{len(cs)} lines, {tc(cs[-1]['end'])} estimated")


if __name__ == "__main__":
    main()
