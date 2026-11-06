"""BJP IT CELL KA SACH - build the CreatorForge script, a ONE-part ElevenLabs file, SEO metadata and the evidence table.

    python gen.py OUT_DIR
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("pyp_build", HERE.parent / "police_ya_power" / "build.py")
pyp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pyp)                      # reuse the number-to-Hindi-words voice converter and timecodes
STATUS = {"F": "Established fact (sourced)", "A": "Allegation / reported claim (attributed)", "D": "Disputed", "J": "Court / judicial finding",
          "O": "Official position / denial", "N": "Narration or analysis"}
TITLE = "BJP IT Cell Ka Sach: 'Sach Ho Ya Jhooth, Viral Kar Denge' | WhatsApp, Trolls Aur Crore Ke Ads"


def load():
    src = {}
    for ln in (HERE / "sources.txt").read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            k, outlet, head, date, url = [p.strip() for p in ln.split(" | ", 4)]
            src[k] = {"key": k, "outlet": outlet, "headline": head, "date": date, "url": url}
    blocks, cur, ch = [], None, ""
    for raw in (HERE / "master.txt").read_text(encoding="utf-8").splitlines() + [""]:
        ln = raw.rstrip()
        m = re.match(r"# \d+ \| (.+)", ln)
        if m:
            ch = m.group(1)
            continue
        if ln.startswith("#"):
            continue
        if not ln.strip():
            if cur:
                blocks.append(cur)
            cur = None
            continue
        k, _, v = ln.partition(": ")
        cur = cur or {"chapter": ch}
        cur[k] = v.strip()
    for i, b in enumerate(blocks, 1):
        b["i"] = i
        assert b.get("D") and b.get("T") in pyp.V3 and b.get("ST") in STATUS, b
        b["src"] = [src[k] for k in (b.get("S") or "").split(",") if k.strip()]
        if b["ST"] in "FAODJ":
            assert b["src"], f"line {i} makes a claim without a source"
    return src, blocks


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    src, blocks = load()
    t = 0.0
    for b in blocks:
        b["start"] = t
        t += pyp.seconds({"D": b["D"], "P": b.get("P")})
    total = t

    used = []
    for b in blocks:
        for s in b["src"]:
            if s not in used:
                used.append(s)
    head = ["BJP IT Cell Ka Sach",
            "On-screen hook: सच्चा हो या झूठा, वायरल कर देंगे।",
            f"Title: {TITLE}",
            "Tags: #BJPITCell #FakeNews #WhatsApp #AmitMalviya #Propaganda #PoliticalAds #Hinglish #FactCheck",
            "Source: " + " ; ".join(f"{s['outlet']}, {s['headline']} {s['url']}" for s in used), ""]
    body = []
    for b in blocks:
        lines = [b["D"], f"Tone: {b['T']}"] + [d.strip() for d in (b.get("CF") or "").split(" || ") if d.strip()]
        body.append("\n".join(lines))
    cf = "\n".join(head) + "\n" + "\n\n".join(body) + "\n"
    (out / "BJP_IT_CELL_CreatorForge_Script.txt").write_text(cf, encoding="utf-8")
    (HERE / "bjp_it_cell_creatorforge.txt").write_text(cf, encoding="utf-8")

    voice = []
    for b in blocks:
        voice.append(pyp.for_voice(b["D"]))
        if float(b.get("P") or 0) > 0:
            voice.append(f'<break time="{float(b["P"]) + 0.4:.1f}s" />')
    el = "\n".join(voice) + "\n"
    assert len(el) <= 10_000, f"ElevenLabs file is {len(el)} characters - over the 10,000 limit"
    (out / "BJP_IT_CELL_ElevenLabs_ONE_PART.txt").write_text(el, encoding="utf-8")

    chapters, seen = [], set()
    for b in blocks:
        if b["chapter"] not in seen:
            seen.add(b["chapter"])
            m, s = divmod(int(b["start"]), 60)
            chapters.append(f"{m}:{s:02d} {b['chapter'].title()}")
    keys = ["SHAH_QUINT", "ROW", "TW_PRINT", "SB_NL", "SWAMY", "MHASKEY", "TROLL_BF", "GUPTA", "TNM_GOOGLE",
            "RC_SCROLL", "NL_ADS", "WSJ_AJ", "BJP_AJ", "BBC_PRINT", "BBC_IT", "X_8000", "FCU", "DORSEY", "OII", "TEKFOG"]
    meta = f"""# YouTube metadata (SEO)

## Title options (A recommended; keyword first, under 100 characters)
A. {TITLE}
B. BJP IT Cell Exposed? Amit Shah Ka 'True Ya Fake' Bayan, WhatsApp Groups Aur Ghost Ads | Hinglish
C. BJP IT Cell Kaise Kaam Karta Hai? 32 Lakh WhatsApp Members, Trolls Aur ₹100 Crore Google Ads

## Description
"Sach ho ya jhooth, viral kar denge." BJP IT Cell kaise kaam karta hai? Amit Shah ka 2018 ka Kota bayan,
WhatsApp groups ka network, Amit Malviya ka 'manipulated media' tweet, 'I Am a Troll' ke aarop, Google aur
Facebook par crore ke ads, ghost advertisers, BBC documentary ka block, 30,000+ links ke blocking orders,\nX ke 8,000 accounts, trolling, aur platforms par uthe sawaal. Har claim source ke saath, har
aarop aarop ki tarah, aur BJP, Meta aur Facebook ka paksh bhi.

Chapters
{chr(10).join(chapters)}

Key sources
{chr(10).join(f"- {src[k]['outlet']} ({src[k]['date']}): {src[k]['url']}" for k in keys)}

Illustrations are labelled. Fake message ko forward karne se pehle check karein: Google Lens, Alt News, BOOM, Factly.

## Tags
bjp it cell, bjp it cell exposed, amit shah true or fake viral, amit malviya manipulated media, whatsapp propaganda india,
bbc documentary blocked india, india: the modi question, x accounts withheld india, twitter blocking orders,\nfake news india, i am a troll swati chaturvedi, bjp google ads spending, facebook ghost advertisers bjp,
ankhi das facebook bjp, political ads india 2024, how to spot fake news whatsapp, hinglish documentary, deepak mhaskey

## Hashtags
#BJPITCell #FakeNews #HinglishDocumentary

## Pinned comment
Is video mein har claim ka source description mein hai, aur har line par likha hai ki wo fact hai, aarop hai ya
official paksh. Koi galti dikhe to source ke saath comment kijiye, hum check karke correction lagayenge. Aapke
family group mein sabse zyada kaunsa fake message aata hai?

## Estimated runtime
{int(total // 60)}:{int(total % 60):02d} (with the ElevenLabs voice the real length will differ slightly)
"""
    assert len(meta.split("## Description")[1].split("## Tags")[0]) < 5000
    (out / "BJP_IT_CELL_YouTube_SEO.md").write_text(meta, encoding="utf-8")

    ev = ["# Evidence table - every line, its status and source", "",
          "| # | Narration | Status | Source |", "|---|---|---|---|"]
    for b in blocks:
        ev.append(f"| {b['i']} | {b['D']} | {STATUS[b['ST']]} | " +
                  ("; ".join(f"[{s['outlet']}, {s['date']}]({s['url']})" for s in b["src"]) or "-") + " |")
    ev += ["", "## Not used, on purpose", "",
           "- Tek Fog (The Wire, Jan 2022): taken down for review in Oct 2022; the film says so and does not use it as evidence.",
           "- '5 million WhatsApp groups': a single report, not independently verified; the film labels it a reported claim.",
           "", "## Before publishing", "",
           "- Open every Source link and confirm the headline used on Article: lines matches exactly.",
           "- Use real news photos only through the pod's Cite/Source pull (credited) or licensed agency images.",
           "- Right of reply: email the BJP national media cell with the specific claims 72 h before publishing."]
    (out / "BJP_IT_CELL_Evidence_Table.md").write_text("\n".join(ev) + "\n", encoding="utf-8")
    print(f"{len(blocks)} lines · estimated {int(total // 60)}:{int(total % 60):02d} · ElevenLabs {len(el)} chars")


if __name__ == "__main__":
    main()
