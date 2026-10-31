"""Acceptance benchmarks: whole productions built as editable documents, rendered, and reported on.

    python -m creatorforge_worker.animation.benchmarks <name|all> <out_dir> [preview|final]

    comedy       ~60 s  stickman comedy: one samosa, two very polite people, and a dog
    political    ~90 s  political explainer on how India's election commissioners are chosen - every fact from a
                        named source (Constitution, Supreme Court judgment, the 2023 Act, a credited news report),
                        both sides given, the satire beat labelled
    psychology   ~3 min psychology explainer on the worry loop - general, hedged, no statistics, ends with where
                        to get help
    documentary  ~5 min hybrid documentary on the Election Commission: animation, real photos and a real news
                        screenshot (credited), real footage (credited), diagrams, an attributed allegation shown as
                        a sourced evidence chain, never acted out
    unfamiliar   a script the engine has never seen, with characters and places it has no assets for, through the
                        script-to-animation path; assets it can build are generated, the rest are labelled
                        placeholders (reported, not hidden)

Each run writes <name>/: the production document (doc.json - open it in the editor), the MP4 (+ Android copy),
storyboard.png (a frame from every scene), assets.json (what was used, generated or placeheld, with validation
warnings), report.json (per-scene QC, critic notes, continuity, sourcing audit, render check, timings).
A clean report is not the same as a good film: the reports say what was measured, and REPORT.md says what was
looked at and what is still weak."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from . import asset_lib, critic, production, qc, visual_reasoning as VR

REAL = Path(__file__).parent / "assets"

# ---- document helpers ---------------------------------------------------------------------------------------------------
SKIN = [226, 186, 150]
ORANGE, GREEN, PURPLE, BLUE, RED, TEAL = [235, 115, 30], [52, 160, 78], [130, 80, 170], [45, 105, 205], [200, 60, 60], \
    [40, 150, 150]


def cast(name, body, x, facing=1, faceless=True, personality="kind", height=1.75):
    c = {"name": name, "body": body, "x": x, "facing": facing, "faceless": faceless, "personality": personality,
         "height": height}
    if not faceless:
        c["skin"] = SKIN
    return c


def step(do, who=None, t="+0.2", **kw):
    s = {"t": t, "do": do, **kw}
    if who:
        s["who"] = who
    return s


def cap(text, t="+0.1", hold=True, dur=None, sources=None):
    s = {"t": t, "do": "caption", "text": text, "hold": hold}
    if dur:
        s["dur"] = dur
    if sources:
        s["sources"] = sources
    return s


def narrate(text, who=None, gesture=None, t="+0.15", dur=None, sources=None):
    """A narration line read on screen while the presenter performs a gesture under it; factual lines carry their
    sources (the audit flags figures and allegations without one)."""
    out = []
    if who and gesture:
        out.append(step("gesture", who, t=t, name=gesture, dur=min(2.4, max(1.2, 0.04 * len(text))), wait=False))
    out.append(cap(text, t=t, dur=dur, sources=sources))
    return out


def scene(sid, name, cast_, props, steps, place="studio", cut=True, timing="explainer", layers=None, camera=None,
          world=None):
    s = {"id": sid, "name": name, "place": place, "cut": cut, "timing": timing, "cast": cast_, "props": props,
         "steps": [x for st in steps for x in (st if isinstance(st, list) else [st])]}
    if layers:
        s["layers"] = layers
    if camera:
        s["camera"] = camera
    if world:
        s["world"] = world
    return s


def bars(t0, values, gap=0.5):
    """Keyed bar values that grow one after another from t0."""
    return {f"v{i}": [[t0 + gap * i, 0.0, "linear"], [t0 + gap * i + 0.6, float(v), "back"]] for i, v in enumerate(values)}


def chart(name, x, title, labels, values, colors, source, t0, frame=None, w=2.8, h=2.0):
    p = {"name": name, "kind": "chart", "x": x, "y": 0.45, "w": w, "h": h,       # above the subtitle band
         "data": {"title": title, "bars": [[l_, c] for l_, c in zip(labels, colors)], "max": max(values) * 1.4,
                  "source": source, **bars(t0, values)}}
    if frame:
        p["frame"] = frame
    return p


def photo(name, x, y, w, h, image, credit, frame=None, highlight=None, hl=None):
    p = {"name": name, "kind": "photo", "x": x, "y": y, "w": w, "h": h, "data": {"image": str(REAL / image),
                                                                                 "credit": credit}}
    if highlight:
        p["data"]["highlight"] = highlight
        p["data"]["hl"] = hl
    if frame:
        p["frame"] = frame
    return p


def sign(name, x, y, w, h, text, color=None, frame=None):
    p = {"name": name, "kind": "sign", "x": x, "y": y, "w": w, "h": h, "label": text}
    if color:
        p["color"] = color
    if frame:
        p["frame"] = frame
    return p


# ---- sources (each is a public document; the claims are paraphrased from it) -----------------------------------------
SRC = {
    "art324_1": {"claim": "Article 324(1): the superintendence, direction and control of elections to Parliament, the "
                          "state legislatures and the offices of President and Vice-President is vested in the "
                          "Election Commission", "source": "Constitution of India, Art. 324(1)"},
    "art324_2": {"claim": "Article 324(2): the President appoints the election commissioners, subject to any law made "
                          "by Parliament", "source": "Constitution of India, Art. 324(2)"},
    "baranwal": {"claim": "Until Parliament makes a law, the commissioners are appointed on the advice of a panel of "
                          "the Prime Minister, the Leader of the Opposition and the Chief Justice of India",
                 "source": "Anoop Baranwal v. Union of India, Supreme Court, 2 March 2023"},
    "act_s7": {"claim": "Selection committee: the Prime Minister, a Union Cabinet Minister nominated by the Prime "
                        "Minister, and the Leader of Opposition in the Lok Sabha",
               "source": "CEC and Other ECs (Appointment...) Act, 2023, s.7(1)"},
    "act_s6": {"claim": "A search committee headed by the Law Minister prepares a panel of five names",
               "source": "CEC and Other ECs (Appointment...) Act, 2023, s.6"},
    "scroll": {"claim": "Gyanesh Kumar was appointed chief election commissioner hours after Opposition leader Rahul "
                        "Gandhi submitted a dissent note at the selection meeting",
               "source": "Scroll.in, 18 Feb 2025"},
    "scroll_defer": {"claim": "The Congress had asked the Union government to defer the appointment until the Supreme "
                              "Court decides the plea challenging the selection process",
                     "source": "Scroll.in, 18 Feb 2025"},
    "lawcomm": {"claim": "The Law Commission recommended that the commissioners be appointed on the advice of a "
                         "three-member collegium of the Prime Minister, the Leader of the Opposition and the Chief "
                         "Justice", "source": "Law Commission of India, 255th Report, 2015"},
    "petitions": {"claim": "Petitions alleged the new selection panel could compromise the independence of the "
                           "Election Commission",
                  "source": "Petitions challenging the 2023 Act, Supreme Court (as reported, March 2024)"},
    "nostay": {"claim": "The Supreme Court declined to stay the appointments of the two election commissioners "
                        "made under the new law", "source": "Supreme Court, March 2024 (as reported)"},
    "eci_history": {"claim": "The Election Commission was established on 25 January 1950; it was a single-member "
                             "body until October 1989, became multi-member in 1989, single-member again in January "
                             "1990, and has been multi-member since October 1993",
                    "source": "Election Commission of India, About ECI"},
    "rolls": {"claim": "Draft electoral rolls are published so that people can check them and file claims and "
                       "objections", "source": "Registration of Electors Rules, 1960"},
    "nolaw": {"claim": "For decades Parliament made no law on the appointment; commissioners were appointed by the "
                       "President on the advice of the government",
              "source": "Anoop Baranwal v. Union of India, Supreme Court, 2 March 2023"},
    "mcc": {"claim": "The Model Code of Conduct sets out what parties, candidates and governments may and may not do "
                     "during the campaign, from the announcement of elections",
            "source": "Election Commission of India, Model Code of Conduct"},
    "ink": {"claim": "A voter's name is checked against the electoral roll and a finger is marked with indelible ink "
                     "before voting", "source": "Conduct of Election Rules, 1961, r.49K"},
    "mar2024": {"claim": "Gyanesh Kumar and Sukhbir Singh Sandhu were appointed election commissioners in March 2024, "
                         "the first appointments under the new law", "source": "Notification of 14 March 2024 (as reported)"},
}


def _presenters(doc: dict) -> dict:
    """The Guide presents: gestures along with the narration when not doing anything else."""
    for sc in doc["scenes"]:
        if any(c.get("name") == "Guide" for c in sc.get("cast", [])):
            sc["presenter"] = "Guide"
    return doc


# ---- 1. comedy ------------------------------------------------------------------------------------------------------------
def _samosa(x, y):
    tri = asset_lib.poly("samosa", [(-0.11, 0.0), (0.11, 0.0), (0.0, 0.14)], (222, 160, 70))
    return {"name": "samosa", "kind": "shape", "x": x, "y": y, "w": 0.22, "h": 0.14, "data": {"parts": [tri]}}


def comedy() -> dict:
    raj = lambda x, f=1: cast("Raj", BLUE, x, f, faceless=False, personality="energetic")   # noqa: E731
    ivy = lambda x, f=-1: cast("Ivy", PURPLE, x, f, faceless=False, personality="calm", height=1.68)  # noqa: E731
    top = 0.78
    scenery = [{"name": "tree", "asset": "tree", "x": -6.5}, {"name": "lamp", "asset": "lamp", "x": 5.5}]
    s1 = scene("c1", "One samosa", [raj(-5.0), ivy(5.5)],
               scenery + [{"name": "table", "asset": "table", "x": 0.0}, _samosa(0.0, top)], [
                   step("walk", "Raj", t=0.3, to=-1.05, speed=1.4),
                   step("double_take", "Raj", at="samosa"),
                   step("express", "Raj", t="+0.0", face="happy"),
                   step("walk", "Ivy", t="+0.1", to=1.05, speed=1.2),
                   step("look", "Ivy", at="samosa", dur=1.0),
                   step("look", "Raj", t="+0.0", at="Ivy", dur=1.2, wait=False),
                   step("look", "Ivy", t="+0.0", at="Raj", dur=1.2),
               ], place="outdoors", timing="comedy")
    s2 = scene("c2", "After you", [raj(-1.05), ivy(1.05)], [], [
        step("line", t=0.3, lines=[
            {"who": "Raj", "text": "You have it.", "to": "Ivy"},
            {"who": "Ivy", "text": "No, no. You have it.", "to": "Raj"},
            {"who": "Raj", "text": "I insist!", "to": "Ivy"}]),
        step("deadpan", "Ivy", dur=1.4),
    ], place="outdoors", cut=False, timing="comedy")
    reach = [[0.32, {"lean": 0.35, "au": 1.35, "al": 1.45}, "out"], [0.5, {"lean": 0.0, "au": 0.3, "al": 0.6}, "inout"]]
    s3 = scene("c3", "Three tries", [raj(-1.05), ivy(1.05)], [], [
        step("pose", "Raj", t=0.4, keys=reach, name="reach"),
        step("symbol", "Ivy", t="-0.6", text="ahem", dur=0.9),
        step("gesture", "Raj", t="+0.1", name="scratch_head", dur=1.0),
        step("pose", "Raj", t="+0.5", keys=reach, name="reach"),
        step("symbol", "Ivy", t="-0.6", text="AHEM", dur=0.9),
        step("gesture", "Ivy", t="+0.0", name="cross_arms", dur=1.4, wait=False),
        step("gesture", "Raj", t="+0.1", name="facepalm", dur=1.1),
        step("turn", "Raj", t="+0.4", facing=-1),
        step("walk", "Raj", t="+0.1", to=-1.9, speed=0.9),
        step("pratfall", "Raj", t="+0.0"),
    ], place="outdoors", cut=False, timing="comedy")
    s4 = scene("c4", "Slow burn", [cast("Raj", BLUE, -3.3, 1, faceless=False, personality="energetic"), ivy(1.05)], [], [
        step("turn", "Raj", t=0.2, facing=1),
        step("walk", "Raj", t="+0.1", to=-1.1, speed=1.2),
        step("pick_up", "Ivy", t="+0.2", what="samosa"),
        step("say", "Ivy", t="+0.1", text="Thank you!"),
        step("slow_burn", "Raj", t="+0.0", at="Ivy", dur=2.6),
    ], place="outdoors", cut=False, timing="comedy")
    s5 = scene("c5", "Sharing", [raj(-1.1), ivy(1.05)], [{"name": "dog", "asset": "a small brown dog", "x": 8.0}], [
        step("put_down", "Ivy", t=0.4, what="samosa", on=top),
        step("line", t="+0.1", lines=[{"who": "Ivy", "text": "Fine. We split it.", "to": "Raj"},
                                      {"who": "Raj", "text": "Deal!", "to": "Ivy"}]),
        step("move", t="+0.1", what="dog", to=0.55, speed=3.0),
        step("move", t="+0.05", what="samosa", to=0.9, y=0.42, dur=0.25, wait=False),
        step("move", t="+0.3", what="samosa", to=8.4, y=0.42, dur=2.6, ease="in", wait=False),
        step("move", t="+0.0", what="dog", to=8.0, dur=2.6, ease="in"),
        step("double_take", "Raj", t="-2.4", at="dog", wait=False),
        step("double_take", "Ivy", t="+0.0", at="dog"),
    ], place="outdoors", cut=False, timing="comedy")
    s6 = scene("c6", "Button", [raj(-1.1), ivy(1.05)], [], [
        step("look", "Raj", t=0.2, at="Ivy", dur=1.4, wait=False),
        step("look", "Ivy", t="+0.0", at="Raj", dur=1.4),
        step("button", "Raj", t="+0.1"),
        step("gesture", "Ivy", t="+0.0", name="laugh", dur=1.8, wait=False),
        step("express", "Ivy", t="+0.0", face="laughing"),
        step("gesture", "Raj", t="+0.4", name="laugh", dur=1.8),
        cap("THE END", t="+0.2", dur=2.0),
    ], place="outdoors", cut=False, timing="comedy")
    return {"title": "The Last Samosa", "fps": 24, "scenes": [s1, s2, s3, s4, s5, s6]}


# ---- 2. political explainer -----------------------------------------------------------------------------------------------
GOV, OPP, JUD = [200, 90, 50], [60, 110, 200], [110, 110, 120]


def political() -> dict:
    G = lambda x, f=1: cast("Guide", ORANGE, x, f)   # noqa: E731
    p1 = scene("p1", "The referee", [G(-4.0)], [], [
        step("walk", "Guide", t=0.3, to=-2.2, speed=1.3),
        step("visual", t="+0.1", text="India's Election Commission runs elections to Parliament and the state "
             "legislatures.", sources=[SRC["art324_1"]], dur=5.5, x=1.6),
        narrate("Like a referee, it is meant to be neutral. So who chooses the referee?", "Guide", "think"),
    ])
    p2 = scene("p2", "The Constitution", [G(-2.2)], [], [
        step("visual", t=0.3, text="Under Article 324(2), the President appoints the election commissioners, subject "
             "to any law made by Parliament.", sources=[SRC["art324_2"]], dur=6.5, x=1.2),
        step("point", "Guide", t="-5.6", at=[1.0, 1.6], dur=1.6, wait=False),
        step("visual", t="+0.2", text="For 73 years Parliament made no such law, so in practice the government of the "
             "day decided.", sources=[SRC["nolaw"]], dur=6.0, x=1.6),
    ])
    p3 = scene("p3", "The Court steps in", [G(-2.2)],
               [chart("court", 1.4, "Panel ordered by the Supreme Court (2023)", ["Prime Minister", "Leader of Opp.",
                      "Chief Justice"], [1, 1, 1], [GOV, OPP, JUD], SRC["baranwal"]["source"], 0.6, frame=[0.4, 12])], [
        step("point", "Guide", t=0.5, at=[1.4, 1.2], dur=1.6, wait=False),
        narrate("In March 2023 the Supreme Court said: until Parliament makes a law, a panel of the Prime Minister, "
                "the Leader of the Opposition and the Chief Justice will choose.", t="+0.3", sources=[SRC["baranwal"]]),
    ])
    p4 = scene("p4", "Parliament's law", [G(-2.6)],
               [chart("act", 0.4, "Panel under the 2023 Act", ["Prime Minister", "Minister picked by PM",
                      "Leader of Opp."], [1, 1, 1], [GOV, GOV, OPP], SRC["act_s7"]["source"], 0.5, frame=[0.3, 14]),
                {"name": "balance", "kind": "scale", "x": 3.4, "y": 0.0, "w": 1.8, "h": 1.35, "label": "Illustration",
                 "data": {"left_label": "Government", "right_label": "Opposition", "left_n": 2, "right_n": 1,
                          "left_color": GOV, "right_color": OPP, "tilt": [[3.0, 0.0, "linear"], [4.2, 1.0, "back"]]},
                 "frame": [2.5, 14]}], [
        step("point", "Guide", t=0.4, at=[0.4, 1.2], dur=1.6, wait=False),
        narrate("In December 2023 Parliament passed that law - and replaced the Chief Justice with a Union Cabinet "
                "Minister chosen by the Prime Minister.", t="+0.3", sources=[SRC["act_s7"]]),
        narrate("So the government side now holds two of the three seats.", "Guide", "explain", sources=[SRC["act_s7"]]),
    ])
    p5 = scene("p5", "Two views", [cast("Mira", GREEN, -1.4, 1, faceless=False, personality="energetic"),
                                   cast("Dev", PURPLE, 1.4, -1, faceless=False, personality="calm")], [], [
        step("line", t=0.4, lines=[
            {"who": "Mira", "text": "Critics: can one side pick the referee?", "to": "Dev"},
            {"who": "Dev", "text": "Supporters: the Court's panel was only until Parliament made a law.", "to": "Mira"}]),
        cap("Both positions paraphrased from the public debate", t="+0.2", dur=2.4),
    ], layers={"tag": "Positions paraphrased"})
    p6 = scene("p6", "February 2025", [G(-2.4)],
               [photo("scroll", 0.6, 0.15, 2.04, 2.4, "scroll_headline.png", "Real screenshot: Scroll.in, 18 Feb 2025",
                      frame=[0.3, 14], highlight=(0.24, 0.255, 0.77, 0.36), hl=[[1.0, 0.0, "linear"],
                                                                                 [2.6, 1.0, "inout"]])], [
        step("point", "Guide", t=0.6, at=[0.4, 1.9], dur=1.8, wait=False),
        narrate("17 February 2025: Gyanesh Kumar was named Chief Election Commissioner.", t="+0.4", sources=[SRC["scroll"]]),
        narrate("Leader of Opposition Rahul Gandhi had submitted a dissent note; the Congress had asked for a delay "
                "until the Supreme Court ruled.", "Guide", "explain", sources=[SRC["scroll"], SRC["scroll_defer"]]),
    ])
    p7 = scene("p7", "Satire", [cast("Captain A", RED, -2.0, 1), cast("Captain B", BLUE, 2.0, -1),
                                cast("Ref", [40, 40, 44], 0.0, 1, height=1.7)], [], [
        step("say", "Captain A", t=0.4, text="We picked the ref!"),
        step("say", "Captain B", t="+0.1", text="Parliament said you could?"),
        step("gesture", "Ref", t="+0.1", name="shrug", dur=1.2),
        step("say", "Captain A", t="+0.1", text="Exactly!"),
        step("gesture", "Captain B", t="+0.0", name="facepalm", dur=1.3),
    ], timing="satire", layers={"tag": "Satire - an exaggeration of the critics' view"})
    p8 = scene("p8", "Where it stands", [G(-0.6)], [], [
        narrate("As reported in February 2025, challenges to the law were pending before the Supreme Court.", "Guide",
                "explain", t=0.4, sources=[SRC["scroll_defer"]]),
        narrate("Sources: Constitution Art. 324; Anoop Baranwal v. Union of India (2023); the 2023 Act; Scroll.in.",
                "Guide", "wave", dur=7.0),
    ])
    doc = {"title": "Who Picks the Referee?", "fps": 24, "scenes": [p1, p2, p3, p4, p5, p6, p7, p8]}
    return _presenters(doc)


# ---- 2b. the political explainer in Hinglish (Stickman Universe 2.0, Test 1) ----------------------------------------
HINGLISH = {   # English line -> (Roman Hinglish subtitle, Devanagari + English words for the Hindi voice)
    "India's Election Commission runs elections to Parliament and the state legislatures.":
        ("India ka Election Commission Parliament aur rajyon ki vidhan sabhaon ke chunav karata hai.",
         "India का Election Commission Parliament और राज्यों की विधानसभाओं के चुनाव कराता है।"),
    "Like a referee, it is meant to be neutral. So who chooses the referee?":
        ("Ek referee ki tarah, ise nishpaksh rehna hai. To referee chunta kaun hai?",
         "एक referee की तरह, इसे निष्पक्ष रहना है। तो referee चुनता कौन है?"),
    "Under Article 324(2), the President appoints the election commissioners, subject to any law made by Parliament.":
        ("Article 324(2) ke tahat President election commissioners ko appoint karte hain - Parliament ke kisi bhi "
         "kanoon ke adheen.",
         "Article 324(2) के तहत President election commissioners को appoint करते हैं, Parliament के किसी भी क़ानून के "
         "अधीन।"),
    "For 73 years Parliament made no such law, so in practice the government of the day decided.":
        ("73 saal tak Parliament ne aisa koi kanoon nahin banaya, isliye asal mein us waqt ki sarkar faisla karti thi.",
         "तिहत्तर साल तक Parliament ने ऐसा कोई क़ानून नहीं बनाया, इसलिए असल में उस वक़्त की सरकार फ़ैसला करती थी।"),
    "In March 2023 the Supreme Court said: until Parliament makes a law, a panel of the Prime Minister, the Leader of "
    "the Opposition and the Chief Justice will choose.":
        ("March 2023 mein Supreme Court ne kaha: jab tak Parliament kanoon nahin banati, Prime Minister, Leader of "
         "Opposition aur Chief Justice ka panel chunega.",
         "March दो हज़ार तेईस में Supreme Court ने कहा: जब तक Parliament क़ानून नहीं बनाती, Prime Minister, Leader of "
         "Opposition और Chief Justice का panel चुनेगा।"),
    "In December 2023 Parliament passed that law - and replaced the Chief Justice with a Union Cabinet Minister chosen "
    "by the Prime Minister.":
        ("December 2023 mein Parliament ne woh kanoon paas kiya - aur Chief Justice ki jagah Prime Minister ka chuna "
         "hua ek Union Cabinet Minister rakh diya.",
         "December दो हज़ार तेईस में Parliament ने वो क़ानून पास किया, और Chief Justice की जगह Prime Minister का चुना "
         "हुआ एक Union Cabinet Minister रख दिया।"),
    "So the government side now holds two of the three seats.":
        ("Yaani ab teen mein se do seats sarkar ki taraf hain.", "यानी अब तीन में से दो seats सरकार की तरफ़ हैं।"),
    "Both positions paraphrased from the public debate":
        ("Dono paksh public debate se paraphrase kiye gaye hain", "दोनों पक्ष public debate से लिए गए हैं।"),
    "17 February 2025: Gyanesh Kumar was named Chief Election Commissioner.":
        ("17 February 2025: Gyanesh Kumar ko Chief Election Commissioner banaya gaya.",
         "सत्रह February दो हज़ार पच्चीस: Gyanesh Kumar को Chief Election Commissioner बनाया गया।"),
    "Leader of Opposition Rahul Gandhi had submitted a dissent note; the Congress had asked for a delay until the "
    "Supreme Court ruled.":
        ("Leader of Opposition Rahul Gandhi ne dissent note diya tha; Congress ne Supreme Court ke faisle tak rukne ko "
         "kaha tha.",
         "Leader of Opposition Rahul Gandhi ने dissent note दिया था; Congress ने Supreme Court के फ़ैसले तक रुकने को "
         "कहा था।"),
    "As reported in February 2025, challenges to the law were pending before the Supreme Court.":
        ("February 2025 ki report ke mutabik, is kanoon ke khilaaf yachikayein Supreme Court mein lambit thin.",
         "February दो हज़ार पच्चीस की report के मुताबिक़, इस क़ानून के ख़िलाफ़ याचिकाएँ Supreme Court में लंबित थीं।"),
    "Sources: Constitution Art. 324; Anoop Baranwal v. Union of India (2023); the 2023 Act; Scroll.in.":
        ("Sources: Constitution Art. 324; Anoop Baranwal v. Union of India (2023); 2023 ka Act; Scroll.in.",
         "स्रोत: Constitution का Article 324, Anoop Baranwal case, 2023 का Act, और Scroll."),
}
HINGLISH_BUBBLES = {"Critics: can one side pick the referee?": "Critics: kya ek team referee chun sakti hai?",
                    "Supporters: the Court's panel was only until Parliament made a law.":
                        "Supporters: Court ka panel sirf tab tak tha jab tak Parliament kanoon na banaye.",
                    "We picked the ref!": "Ref humne chuna!", "Parliament said you could?": "Parliament ne ijaazat di?",
                    "Exactly!": "Bilkul!"}


def political_hinglish() -> dict:
    """Test 1: the political explainer narrated in Hinglish (Hindi voice reading Devanagari with English terms;
    Roman-script subtitles), sources cited per line, the headline pushed into and dissolved into real footage."""
    import copy as _copy
    doc = _copy.deepcopy(political())
    doc["title"] = "Referee kaun chunta hai?"
    missing = []
    for sc in doc["scenes"]:
        for st in sc["steps"]:
            if st["do"] in ("caption", "visual"):
                hi = HINGLISH.get(st["text"])
                if not hi:
                    missing.append(st["text"])
                    continue
                if not st["text"].startswith("Sources:"):     # the source list is read on screen, not aloud
                    st["voice"] = {"lang": "hi", "say": hi[1], "rate": 168}
                if st["do"] == "visual":
                    st["subtitle"] = hi[0]                     # reasoning stays on the English line
                else:
                    st["reason_text"], st["text"] = st["text"], hi[0]
                if st.get("sources"):
                    st["cite"] = True
            elif st["do"] == "say":
                st["text"] = HINGLISH_BUBBLES.get(st["text"], st["text"])
            elif st["do"] == "line":
                for ln in st["lines"]:
                    ln["text"] = HINGLISH_BUBBLES.get(ln["text"], ln["text"])
    if missing:
        raise ValueError(f"no Hinglish for: {missing}")
    doc["scenes"] = [s_ for s_ in doc["scenes"] if s_["id"] != "p7"]      # Test 1 asks for no satire beat
    p6 = next(s_ for s_ in doc["scenes"] if s_["id"] == "p6")
    p6["outro"] = {"push_into": "scroll", "dur": 1.4}
    i = doc["scenes"].index(p6)
    doc["scenes"].insert(i + 1, {"id": "p6f", "name": "Real footage", "footage": str(REAL / "footage_portrait.mp4"),
                                 "start": 0.0, "dur": 5.5, "credit": "from the Print Facts report on the CEC appointment",
                                 "transition": {"kind": "dissolve", "dur": 0.6}})
    doc["scenes"][i + 2]["transition"] = {"kind": "dissolve", "dur": 0.5}
    return doc


def voice_all(doc: dict, lang: str = "en", rate: int = 150) -> dict:
    """Narrates every caption that has no voice yet (the same words as the subtitle)."""
    for sc in doc["scenes"]:
        for st in sc.get("steps", []):
            if st.get("do") in ("caption", "visual") and not st.get("voice") and st.get("caption", True) is not False:
                st["voice"] = {"lang": lang, "say": st.get("subtitle", st["text"]), "rate": rate}
    return doc


# ---- 3. psychology explainer ----------------------------------------------------------------------------------------------
def psychology() -> dict:
    noor = lambda x, f=1: cast("Noor", TEAL, x, f, faceless=False, personality="timid", height=1.65)   # noqa: E731
    sam = lambda x, f=-1: cast("Sam", ORANGE, x, f, faceless=False, personality="kind")   # noqa: E731
    room = [{"name": "lamp", "asset": "lamp", "x": -4.0}, {"name": "desk", "asset": "table", "x": 1.6, "z": 1.3},
            {"name": "chair", "asset": "chair", "x": 0.6, "z": 1.3}]
    S = []
    S.append(scene("w1", "The worry loop", [noor(-3.0)], room, [
        step("walk", "Noor", t=0.4, to=-0.6, speed=1.0),
        step("express", "Noor", t="+0.0", face="neutral"),
        narrate("This is Noor. It's late, and one small worry has started to grow.", t="+0.2"),
        step("gesture", "Noor", t="+0.0", name="think", dur=2.0),
    ], place="indoors", layers={"paper": [236, 232, 244]}))
    S.append(scene("w2", "It grows", [noor(-0.6)], room, [
        step("visual", t=0.3, text="Anxiety can make a small worry feel overwhelming.", dur=6.0, x=2.2),
        step("express", "Noor", t="-5.2", face="nervous", wait=False),
        step("feel", "Noor", t="+0.0", emotion="scared", dur=4.0, wait=False),
        step("gesture", "Noor", t="+0.0", name="cover_face", dur=1.8),
    ], place="indoors", cut=False))
    S.append(scene("w3", "Round and round", [noor(-0.6)], room, [
        narrate("Worry often runs in loops: the same 'what if' replayed again and again.", t=0.3, dur=7.0),
        step("walk", "Noor", t="-6.6", to=1.4, speed=0.9),
        step("turn", "Noor", t="+0.1", facing=-1),
        step("walk", "Noor", t="+0.1", to=-1.2, speed=0.9),
        step("turn", "Noor", t="+0.1", facing=1),
        step("walk", "Noor", t="+0.1", to=0.4, speed=0.9),
        step("symbol", "Noor", t="+0.0", text="what if...?", dur=1.6),
    ], place="indoors", cut=False, layers={"mood": "anxious"}))
    S.append(scene("w4", "The body joins in", [noor(0.4)], room, [
        narrate("The body joins in: a faster heartbeat, tight shoulders, quick shallow breaths.", t=0.3, dur=6.0),
        step("posture", "Noor", t="-5.6", lean=0.18, crouch=0.08, dur=5.0, wait=False),
        step("express", "Noor", t="+0.0", face="nervous"),
    ], place="indoors", cut=False, layers={"mood": "anxious"}))
    S.append(scene("w5", "Avoiding it", [noor(0.4)], room + [sign("email", 3.2, 0.9, 1.4, 0.6, "Reply to boss",
                                                              [90, 100, 120], frame=[0.3, 9])], [
        step("look", "Noor", t=0.3, at="email", dur=1.2),
        step("step_back", "Noor", t="+0.0", dist=0.5),
        step("turn", "Noor", t="+0.1", facing=-1),
        narrate("Avoiding what we fear brings quick relief - but it can teach the brain the fear was right.", t="+0.2"),
    ], place="indoors", cut=False, layers={"mood": "anxious", "tag": "Illustration"}))
    breathe = [[1.6, {"squash": 1.04, "head": -0.12, "au": 0.42}, "inout"], [2.4, {"squash": 0.98, "head": 0.06,
                                                                                    "au": 0.28}, "inout"]]
    S.append(scene("w6", "Breathe out longer", [noor(-0.1, -1)], room, [
        step("turn", "Noor", t=0.2, facing=1),
        narrate("Something many people find helpful: slow breathing, with the breath out longer than the breath in.",
                t="+0.2", dur=6.5),
        step("pose", "Noor", t="-6.0", keys=breathe + breathe, name="breathe"),
        step("express", "Noor", t="+0.0", face="neutral", blend=1.0),
    ], place="indoors", cut=False, layers={"mood": "calm"}))
    S.append(scene("w7", "Name it", [noor(-0.1)], room + [sign("worry", 2.2, 1.0, 1.9, 0.6, "What if I mess up?",
                                                               [150, 70, 70], frame=[0.3, 9])], [
        step("point", "Noor", t=0.4, at=[2.2, 1.3], dur=1.4, wait=False),
        narrate("Naming the worry - even writing it down - can make it easier to look at.", t="+0.2"),
        step("gesture", "Noor", t="+0.0", name="think", dur=1.4),
    ], place="indoors", cut=False))
    S.append(scene("w8", "Weigh it", [noor(-0.1)], room + [
        {"name": "weigh", "kind": "scale", "x": 2.4, "y": 0.0, "w": 1.8, "h": 1.35, "label": "Illustration",
         "data": {"left_label": "Fear", "right_label": "Facts", "left_n": 2, "right_n": 3, "left_color": [150, 70, 70],
                  "right_color": [60, 140, 90], "tilt": [[1.5, 0.6, "linear"], [5.5, -0.8, "inout"]]},
         "frame": [0.3, 12]}], [
        narrate("Then ask: what is the evidence? What would I tell a friend who had this worry?", "Noor", "think",
                t=0.3, dur=6.5),
        step("nod", "Noor", t="+0.0", dur=0.9),
    ], place="indoors", cut=False))
    S.append(scene("w9", "A friend", [noor(-0.1), sam(4.5)], room, [
        step("walk", "Sam", t=0.3, to=1.1, speed=1.2),
        step("line", t="+0.1", lines=[
            {"who": "Sam", "text": "Hey. You look worried.", "to": "Noor"},
            {"who": "Noor", "text": "I keep thinking I'll mess up tomorrow.", "to": "Sam", "emotion": "sad"},
            {"who": "Sam", "text": "Want to talk it through?", "to": "Noor"}]),
        step("comfort", "Sam", t="+0.1", to="Noor", dur=2.0),
    ], place="indoors", cut=False))
    S.append(scene("w10", "Talking helps", [noor(-0.1), sam(1.1)], room, [
        narrate("Talking a worry through with someone we trust often makes it feel smaller.", t=0.3),
        step("nod", "Noor", t="-3.0", dur=0.9, wait=False),
        step("express", "Noor", t="+0.0", face="happy", blend=0.8),
    ], place="indoors", cut=False, layers={"mood": "calm"}))
    S.append(scene("w11", "One small step", [noor(-0.1), sam(1.1)], room + [sign("email", 3.2, 0.9, 1.4, 0.6,
                                                                                 "Reply to boss", [90, 100, 120],
                                                                                 frame=[0.3, 12])], [
        narrate("Then one small step toward the thing we were avoiding.", t=0.3),
        step("walk", "Noor", t="+0.0", to=2.2, speed=1.0),
        step("point", "Noor", t="+0.1", at=[3.2, 1.2], dur=1.2),
        step("gesture", "Sam", t="+0.0", name="clap", dur=1.2),
    ], place="indoors", cut=False, layers={"tag": "Illustration"}))
    S.append(scene("w12a", "Worry or problem?", [noor(2.2, -1), sam(1.1)], room + [
        sign("plan", -1.6, 1.1, 2.2, 0.6, "Next step: draft the reply", [60, 120, 90], frame=[0.3, 12])], [
        narrate("If a worry is a real problem, turn it into a plan with one next step.", "Noor", "explain", t=0.3),
        step("point", "Noor", t="+0.0", at=[-1.6, 1.4], dur=1.2),
        narrate("If it isn't something you can act on, practise noticing it - and letting it pass.", t="+0.2"),
    ], place="indoors", cut=False))
    S.append(scene("w12b", "Back to the room", [noor(2.2, -1), sam(1.1)], room, [
        narrate("When thoughts race, come back to the room: five things you can see, four you can hear, three you "
                "can touch.", t=0.3, dur=7.5),
        step("look", "Noor", t="-7.0", at="lamp", dur=1.6),
        step("look", "Noor", t="+0.2", at="desk", dur=1.6),
        step("look", "Noor", t="+0.2", at="Sam", dur=1.6),
        step("express", "Noor", t="+0.0", face="neutral", blend=0.8),
    ], place="indoors", cut=False, layers={"mood": "calm"}))
    S.append(scene("w12c", "At night", [noor(2.2, -1), sam(1.1)], room, [
        narrate("Worries often feel louder at night, when we're tired and nothing else holds our attention.", "Noor",
                "think", t=0.3),
        narrate("A regular wind-down - screens away, the same bedtime - helps many people.", t="+0.2"),
        step("gesture", "Sam", t="-2.5", name="wave", dur=1.4, wait=False),
        step("walk", "Sam", t="+0.0", to=5.5, speed=1.2),
    ], place="indoors", cut=False, layers={"paper": [214, 216, 232]}))
    S.append(scene("w12d", "Be kind", [noor(2.2, -1)], room, [
        narrate("And talk to yourself the way you would talk to a friend. Worrying is not a weakness - it is a brain "
                "trying to protect you.", "Noor", "shrug", t=0.3),
        step("nod", "Noor", t="+0.0", dur=0.9),
    ], place="indoors", cut=False, layers={"mood": "calm"}))
    S.append(scene("w12", "Quieter", [noor(2.2, -1)], room, [
        narrate("Worry doesn't vanish for good - but it gets quieter when we stop running from it.", "Noor", "think",
                t=0.3),
        cap("If worry is taking over your days, talk to a doctor or a mental-health professional.", t="+0.2",
            dur=5.0),
    ], place="indoors", cut=False, layers={"mood": "calm"}))
    return {"title": "The Worry Loop", "fps": 24, "scenes": S}


# ---- 4. hybrid documentary ------------------------------------------------------------------------------------------------
def documentary() -> dict:
    G = lambda x, f=1: cast("Guide", ORANGE, x, f)   # noqa: E731
    T = "explainer"
    D = []
    D.append(scene("d1", "The Referee", [G(-4.0)],
                   [photo("ec", 1.4, 0.5, 3.0, 2.0, "ec_photo.png", "Real photo: Election Commission of India",
                          frame=[0.3, 14])], [
        step("walk", "Guide", t=0.3, to=-2.0, speed=1.2),
        step("point", "Guide", t="+0.1", at=[1.0, 1.6], dur=1.6, wait=False),
        narrate("Every Indian election - for Parliament and the states - is run by one body: the Election "
                "Commission of India.", t="+0.2", sources=[SRC["art324_1"]]),
    ], timing=T))
    D.append(scene("d2", "Founded 1950", [G(-2.0)],
                   [{"name": "timeline", "kind": "diagram", "x": 1.2, "y": 1.2, "w": 6.0, "h": 0.6, "frame": [0.3, 14],
                     "data": {"boxes": ["1950 founded", "1989 three", "1990 one", "1993 three"],
                              "colors": [[90, 110, 140], [60, 120, 190], [150, 90, 90], [60, 120, 190]],
                              "reveal": [[0.6, 0.0, "linear"], [3.0, 1.0, "linear"]]}}], [
        narrate("It was set up on 25 January 1950 - the day before India became a republic.", "Guide", "explain",
                t=0.4, sources=[SRC["eci_history"]]),
        narrate("For its first 39 years it had a single commissioner. Two more were added in 1989, removed in "
                "1990, and added again in 1993.", t="+0.2", sources=[SRC["eci_history"]]),
    ], timing=T))
    D.append(scene("d3", "What it does", [G(-3.0), cast("Voter 1", GREEN, 4.6, -1), cast("Voter 2", PURPLE, 5.4, -1),
                                          cast("Voter 3", TEAL, 6.2, -1, height=1.62)], [], [
        step("visual", t=0.3, text="It runs elections to Parliament, the state legislatures, and the offices of "
             "President and Vice-President.", sources=[SRC["art324_1"]], dur=7.0, x=0.6),
        step("walk", "Voter 1", t="-6.4", to=1.3, speed=1.0, wait=False),
        step("walk", "Voter 2", t="+0.0", to=2.1, speed=1.0, wait=False),
        step("walk", "Voter 3", t="+0.0", to=2.9, speed=1.0, wait=False),
        step("gesture", "Guide", t="+0.0", name="explain", dur=1.6),
    ], timing=T))
    D.append(scene("d4", "The voter list", [G(-2.6), cast("Voter 1", GREEN, -0.2, 1)],
                   [photo("rolls", 2.2, 0.2, 3.0, 1.55, "voters_lists.png", "Real photo: voters checking draft lists",
                          frame=[0.3, 14])], [
        step("point", "Voter 1", t=0.5, at=[2.0, 1.0], dur=1.5, wait=False),
        narrate("It keeps the electoral rolls - the list of who can vote. Draft rolls are published so people can "
                "check them and object.", "Guide", "explain", t="+0.2", sources=[SRC["rolls"]]),
        step("nod", "Voter 1", t="+0.0"),
    ], timing=T))
    D.append(scene("d5", "Who appoints?", [G(-2.4)], [], [
        step("visual", t=0.3, text="Under Article 324(2), the President appoints the election commissioners, subject "
             "to any law made by Parliament.", sources=[SRC["art324_2"]], dur=7.0, x=1.2),
        step("point", "Guide", t="-6.2", at=[1.0, 1.6], dur=1.6, wait=False),
    ], timing=T))
    D.append(scene("d6", "Decades of practice", [G(-2.4)], [], [
        narrate("For decades Parliament made no such law, so commissioners were appointed on the government's advice.",
                "Guide", "explain", t=0.3, sources=[SRC["nolaw"]]),
        step("walk", "Guide", t="+0.0", to=0.4, speed=1.0),
        narrate("Reformers asked for a wider panel. In 2015 the Law Commission recommended the Prime Minister, the "
                "Leader of the Opposition and the Chief Justice.", "Guide", "point", t="+0.1", sources=[SRC["lawcomm"]]),
    ], timing=T))
    D.append(scene("d7", "The 2023 judgment", [G(-2.2)],
                   [chart("court", 1.4, "Panel ordered by the Supreme Court (2023)", ["Prime Minister",
                          "Leader of Opp.", "Chief Justice"], [1, 1, 1], [GOV, OPP, JUD], SRC["baranwal"]["source"],
                          0.6, frame=[0.4, 14])], [
        step("point", "Guide", t=0.5, at=[1.4, 1.2], dur=1.6, wait=False),
        narrate("On 2 March 2023 the Supreme Court ordered that, until Parliament makes a law, a panel of the Prime Minister, "
                "the Leader of the Opposition and the Chief Justice of India appoints the commissioners.", t="+0.3", sources=[SRC["baranwal"]]),
    ], timing=T))
    D.append(scene("d8", "The 2023 Act", [G(-2.6)],
                   [chart("act", 0.4, "Panel under the 2023 Act", ["Prime Minister", "Minister picked by PM",
                          "Leader of Opp."], [1, 1, 1], [GOV, GOV, OPP], SRC["act_s7"]["source"], 0.5, frame=[0.3, 14]),
                    {"name": "balance", "kind": "scale", "x": 3.4, "y": 0.0, "w": 1.8, "h": 1.35, "label": "Illustration",
                     "data": {"left_label": "Government", "right_label": "Opposition", "left_n": 2, "right_n": 1,
                              "left_color": GOV, "right_color": OPP, "tilt": [[3.0, 0.0, "linear"], [4.2, 1.0, "back"]]},
                     "frame": [2.5, 14]}], [
        step("point", "Guide", t=0.4, at=[0.4, 1.2], dur=1.6, wait=False),
        narrate("In December 2023 Parliament made that law: the Chief Justice was replaced by a Union Cabinet "
                "Minister nominated by the Prime Minister.", t="+0.3", sources=[SRC["act_s7"]]),
    ], timing=T))
    D.append(scene("d9", "Search and selection", [G(-3.4)],
                   [{"name": "flow", "kind": "diagram", "x": 0.6, "y": 1.6, "w": 6.4, "h": 0.62, "frame": [0.3, 14],
                     "data": {"boxes": ["Search committee: 5 names", "Selection committee picks", "President appoints"],
                              "colors": [[90, 110, 140], [60, 120, 190], [200, 140, 40]],
                              "reveal": [[0.8, 0.0, "linear"], [3.2, 1.0, "linear"]]}}], [
        step("point", "Guide", t=0.6, at=[-1.5, 1.9], dur=1.4, wait=False),
        narrate("A search committee headed by the Law Minister shortlists five names; the selection committee then "
                "chooses.", t="+0.2", sources=[SRC["act_s6"]]),
    ], timing=T))
    D.append(scene("d10", "March 2024", [G(-2.2)],
                   [{"name": "card", "kind": "stat", "x": 1.4, "y": 0.9, "w": 2.6, "h": 1.1, "label": "2 appointed",
                     "data": {"sub": "the first under the new law", "source": "March 2024",
                              "pop": [[0.6, 0.0, "linear"], [1.1, 1.0, "back"]]}, "frame": [0.4, 12]}], [
        narrate("In March 2024 two election commissioners, Gyanesh Kumar and Sukhbir Singh Sandhu, were the first "
                "appointed under the new law.", "Guide", "explain", t=0.4, sources=[SRC["mar2024"]]),
    ], timing=T))
    D.append(scene("d11", "The challenge", [G(-3.0)], [], [
        step("visual", t=0.3, text="Petitioners alleged that the new selection panel could compromise the "
             "independence of the Election Commission; the Supreme Court declined to stay the appointments.",
             sources=[SRC["petitions"], SRC["nostay"]], dur=9.0, x=0.8),
        step("gesture", "Guide", t="-8.0", name="think", dur=1.6),
    ], timing=T))
    D.append(scene("d12", "February 2025", [G(-2.4)],
                   [photo("scroll", 0.6, 0.15, 2.04, 2.4, "scroll_headline.png", "Real screenshot: Scroll.in, 18 Feb 2025",
                          frame=[0.3, 16], highlight=(0.24, 0.255, 0.77, 0.36), hl=[[1.0, 0.0, "linear"],
                                                                                    [2.6, 1.0, "inout"]])], [
        step("point", "Guide", t=0.6, at=[0.4, 1.9], dur=1.8, wait=False),
        narrate("On 17 February 2025 Gyanesh Kumar was named Chief Election Commissioner.", t="+0.4", sources=[SRC["scroll"]]),
        narrate("Rahul Gandhi, Leader of the Opposition, had submitted a dissent note; the Congress asked for a delay "
                "until the Supreme Court ruled.", "Guide", "explain", sources=[SRC["scroll"], SRC["scroll_defer"]]),
    ], timing=T))
    D.append({"id": "d13", "name": "Real footage", "footage": str(REAL / "footage_portrait.mp4"), "start": 0.0,
              "dur": 6.5, "credit": "from the Print Facts report on the CEC appointment"})
    D.append(scene("d14", "Two views", [cast("Mira", GREEN, -1.4, 1, faceless=False, personality="energetic"),
                                        cast("Dev", PURPLE, 1.4, -1, faceless=False, personality="calm")], [], [
        step("line", t=0.4, lines=[
            {"who": "Mira", "text": "Critics: two of three seats are the government's.", "to": "Dev"},
            {"who": "Dev", "text": "Supporters: the Court said its panel lasts only until Parliament acts.",
             "to": "Mira"},
            {"who": "Mira", "text": "So the question is whether that law is fair.", "to": "Dev"},
            {"who": "Dev", "text": "And that is for the Supreme Court to decide.", "to": "Mira"}]),
    ], timing=T, layers={"tag": "Positions paraphrased from the public debate"}))
    D.append(scene("d15", "Why it matters", [G(-3.6), cast("Voter 1", GREEN, 5.0, -1), cast("Voter 2", PURPLE, 5.8, -1)],
                   [{"name": "box", "kind": "crate", "x": 1.0, "y": 0.0, "w": 0.6, "h": 0.6, "label": "VOTES"}], [
        step("walk", "Voter 1", t=0.3, to=1.6, speed=1.0, wait=False),
        step("walk", "Voter 2", t="+0.0", to=2.4, speed=1.0, wait=False),
        narrate("A referee is only useful if both teams trust the whistle.", "Guide", "explain", t="+0.2"),
        narrate("That trust - more than any one appointment - is what the debate is about.", t="+0.2"),
    ], timing=T, layers={"tag": "Illustration"}))
    D.append(scene("d16", "Where it stands", [G(-0.6)], [], [
        narrate("As reported in February 2025, challenges to the 2023 law were pending before the Supreme Court.",
                "Guide", "explain", t=0.4, sources=[SRC["scroll_defer"]]),
        narrate("Sources: Constitution Art. 324; Law Commission Report 255 (2015); Anoop Baranwal v. Union of India "
                "(2023); the 2023 Act; Scroll.in (2025).", "Guide", "wave", dur=6.0),
    ], timing=T))
    D.append(scene("dA", "The rules of the game", [G(-2.6)],
                   [sign("mcc", 1.2, 1.0, 2.8, 0.7, "Model Code of Conduct", [60, 90, 140], frame=[0.3, 14])], [
        step("point", "Guide", t=0.4, at=[1.0, 1.35], dur=1.4, wait=False),
        narrate("When elections are announced, a Model Code of Conduct sets out what parties, candidates and "
                "governments may and may not do during the campaign.", t="+0.2", sources=[SRC["mcc"]]),
    ], timing=T))
    D.append(scene("dB", "Polling day", [G(-3.4), cast("Voter 1", GREEN, 5.0, -1), cast("Voter 2", PURPLE, 5.8, -1),
                                        cast("Voter 3", TEAL, 6.6, -1, height=1.62)],
                   [{"name": "box", "kind": "crate", "x": 0.6, "y": 0.0, "w": 0.6, "h": 0.6, "label": "VOTES"}], [
        step("walk", "Voter 1", t=0.3, to=1.2, speed=0.9, wait=False),
        step("walk", "Voter 2", t="+0.0", to=2.0, speed=0.9, wait=False),
        step("walk", "Voter 3", t="+0.0", to=2.8, speed=0.9, wait=False),
        narrate("On polling day each voter's name is checked against the roll, and a finger is marked with "
                "indelible ink so no one votes twice.", "Guide", "explain", t="+0.4", sources=[SRC["ink"]]),
        step("point", "Voter 1", t="+0.0", at=[0.6, 0.5], dur=1.2),
    ], timing=T))
    D.append(scene("dC", "Three members", [G(-2.2)],
                   [{"name": "card", "kind": "stat", "x": 1.4, "y": 0.9, "w": 2.6, "h": 1.1, "label": "1 + 2",
                     "data": {"sub": "Chief Election Commissioner + two Election Commissioners",
                              "source": "ECI, About ECI", "pop": [[0.6, 0.0, "linear"], [1.1, 1.0, "back"]]},
                     "frame": [0.4, 12]}], [
        narrate("Today the Commission has three members: a Chief Election Commissioner and two Election "
                "Commissioners.", "Guide", "explain", t=0.4, sources=[SRC["eci_history"]]),
        narrate("So how they are chosen matters.", "Guide", "think", t="+0.2"),
    ], timing=T))
    D.append(scene("dD", "Side by side", [G(-4.2)],
                   [chart("court2", -1.4, "Court's panel (2023)", ["PM", "Leader of Opp.", "Chief Justice"], [1, 1, 1],
                          [GOV, OPP, JUD], SRC["baranwal"]["source"], 0.5, frame=[0.3, 14], w=2.4, h=1.8),
                    chart("act2", 1.6, "2023 Act", ["PM", "Minister", "Leader of Opp."], [1, 1, 1], [GOV, GOV, OPP],
                          SRC["act_s7"]["source"], 1.6, frame=[0.3, 14], w=2.4, h=1.8)], [
        narrate("Side by side: the Court's panel had one member from the government, one from the opposition and "
                "one judge; the Act's panel has two from the government and one from the opposition.", "Guide",
                "explain", t=0.4, dur=7.5, sources=[SRC["baranwal"], SRC["act_s7"]]),
    ], timing=T))
    D.append(scene("dE", "Common ground", [cast("Mira", GREEN, -1.4, 1, faceless=False, personality="energetic"),
                                          cast("Dev", PURPLE, 1.4, -1, faceless=False, personality="calm")], [], [
        narrate("Both sides say the Commission must be independent. They disagree about how to choose the people "
                "who run it.", t=0.4),
        step("nod", "Mira", t="-2.0", dur=0.8, wait=False),
        step("nod", "Dev", t="+0.0", dur=0.8),
    ], timing=T, layers={"tag": "Summary of the debate"}))
    D.append(scene("dF", "Your part", [G(-2.6), cast("Voter 1", GREEN, -0.4, 1)],
                   [photo("rolls2", 2.2, 0.2, 3.0, 1.55, "voters_lists.png", "Real photo: voters checking draft lists",
                          frame=[0.3, 12])], [
        narrate("Whoever runs it, the roll is yours to check: any eligible citizen can look up their name and apply "
                "to add or correct it.", "Guide", "explain", t=0.4, sources=[SRC["rolls"]]),
        step("point", "Voter 1", t="+0.0", at=[2.0, 1.0], dur=1.2),
    ], timing=T))
    order = ["d1", "d2", "dC", "d3", "dA", "d4", "dB", "d5", "d6", "d7", "d8", "d9", "dD", "d10", "d11", "d12", "d13",
             "d14", "dE", "d15", "dF", "d16"]
    by = {s_["id"]: s_ for s_ in D}
    D = [by[k] for k in order]
    return _presenters({"title": "The Referee", "fps": 24, "scenes": D})


# ---- 6. unfamiliar script ---------------------------------------------------------------------------------------------------
UNFAMILIAR = ("Old Tomas the fisherman rows his boat to the harbour at dawn. A cheeky pelican lands next to him and "
              "steals a fish. Tomas chases the pelican past the lighthouse and the market stalls. The pelican drops "
              "the fish into a little girl's basket. Tomas laughs and gives her the fish.")

DOCS = {"comedy": comedy, "political": political, "psychology": psychology, "documentary": documentary,
        "test1_political_hinglish": political_hinglish, "film_b": lambda: film_b(), "film_a": lambda: film_a(),
        "test3_psychology_narrated": lambda: voice_all(psychology(), "en")}


# ---- running and reporting --------------------------------------------------------------------------------------------------
def _storyboard(video: Path, doc: dict, seconds: list[float], out: Path) -> Path:
    from PIL import Image, ImageDraw
    from .props_draw import font
    tiles, t = [], 0.0
    tmp = out.parent / "_frames"
    tmp.mkdir(exist_ok=True)
    for k, (sc, T) in enumerate(zip(doc["scenes"], seconds)):
        f = tmp / f"{k:02d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t + T * 0.6:.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=400:-2", str(f)], check=True)
        im = Image.open(f).convert("RGB") if f.exists() else Image.new("RGB", (400, 225), (60, 20, 20))
        tiles.append((im, f"{k + 1}. {sc.get('name', sc['id'])}  ({T:.1f} s)" + ("" if f.exists() else " NO FRAME")))
        t += T
    cols = 4
    w, h = tiles[0][0].size
    sheet = Image.new("RGB", (cols * w, ((len(tiles) + cols - 1) // cols) * (h + 28)), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, (im, label) in enumerate(tiles):
        x, y = (i % cols) * w, (i // cols) * (h + 28)
        sheet.paste(im, (x, y + 28))
        d.text((x + 6, y + 6), label, font=font(15), fill=(20, 20, 24))
    sheet.save(out)
    for f in list(tmp.iterdir()):
        f.unlink()
    tmp.rmdir()
    return out


def _assets_used(doc: dict) -> list[dict]:
    lib = asset_lib.Library.default()
    out = []
    for sc in doc["scenes"]:
        for p in sc.get("props", []):
            if p.get("asset"):
                aid = p["asset"] if p["asset"] in lib.items else lib.obtain(p["asset"])[0]
                a = lib.get(aid)
                out.append({"scene": sc["id"], "prop": p["name"], "asset": aid, "source": a.get("source", ""),
                            "warnings": [w["detail"] for w in a.get("warnings", [])]})
            elif p.get("kind") == "photo":
                out.append({"scene": sc["id"], "prop": p["name"], "asset": Path(p["data"]["image"]).name,
                            "source": "real image: " + p["data"]["credit"]})
            elif p.get("kind") == "shape":
                issues = asset_lib.validate({"kind": "prop", "name": p["name"], "w": p["w"], "h": p["h"],
                                             "parts": p["data"]["parts"]})
                out.append({"scene": sc["id"], "prop": p["name"], "asset": "inline shape", "source": "document",
                            "warnings": [i.detail for i in issues]})
        if sc.get("footage"):
            out.append({"scene": sc["id"], "prop": "footage", "asset": Path(sc["footage"]).name,
                        "source": "real footage: " + sc.get("credit", "")})
    return out


def run(name: str, out_dir: Path, quality: str = "preview", workers: int = 2) -> dict:
    out = Path(out_dir) / name
    out.mkdir(parents=True, exist_ok=True)
    if name == "unfamiliar":
        return run_unfamiliar(out)
    if name == "test5_universal":
        return run_universal(out)
    doc = DOCS[name]()
    (out / "doc.json").write_text(json.dumps(doc, indent=1))
    t0 = time.time()
    states = production.plan_states(doc, quality)
    reviews, plans = [], []
    for sc_doc, (start, end, T, rep, issues, fixes, incoming) in zip(doc["scenes"], states):
        if sc_doc.get("footage"):
            reviews.append({"scene": sc_doc["id"], "notes": []})
            continue
        sc, T, _, _ = production.stage_scene(sc_doc, incoming, production.QUALITY[quality]["fps"], quality)
        R = qc.record(sc, T)
        rv = critic.review(R, sc)
        reviews.append({"scene": sc_doc["id"], **rv.to_dict()})
        plans += getattr(sc, "visual_plans", [])
    stage_s = time.time() - t0
    rep = production.render(doc, out / f"{name}.mp4", quality, workers=workers, cache_dir=out.parent / "scene_cache")
    seconds = [s["seconds"] for s in rep["scenes"]]
    _storyboard(out / f"{name}.mp4", doc, seconds, out / "storyboard.png")
    assets = _assets_used(doc)
    (out / "assets.json").write_text(json.dumps(assets, indent=1))
    report = {
        "benchmark": name, "title": doc["title"], "quality": quality, "seconds": round(sum(seconds), 1),
        "scenes": rep["scenes"], "critic": reviews,
        "sourcing": {"plans": [{"sentence": p.sentence, "mode": p.mode, "label": p.label, "sourced": p.sourced,
                                "note": p.note} for p in plans], "audit": VR.audit(plans)},
        "video": rep["video"], "delivery": rep.get("delivery"), "subtitles": rep.get("subtitles"), "files": rep["files"],
        "timing": {"staging_and_review_s": round(stage_s, 1), "render_s": rep["render_seconds"]},
        "qc_clean_scenes": sum(1 for s in rep["scenes"] if s["qc"].startswith(("clean", "real footage"))),
        "continuity_issues": sum(len(s["continuity"]) for s in rep["scenes"]),
    }
    (out / "report.json").write_text(json.dumps(report, indent=1, default=str))
    return report


FLOUR = ("Grandma Rosa bakes bread in her tiny kitchen. Her cat jumps onto the table and knocks over the flour. Rosa "
         "sneezes, and white flour covers everything. The cat hides under a chair. Rosa laughs, picks up the cat, and "
         "they share a warm slice by the window.")


def run_universal(out: Path) -> dict:
    """Test 5: two scripts the studio was not written for, straight through the director, narrated."""
    from . import studio
    res = {}
    for name, script, title in (("flour", FLOUR, "Flour"), ("pelican", UNFAMILIAR, "The Pelican")):
        t0 = time.time()
        rep = studio.film(script, out / f"{name}.mp4", title, voice={"lang": "en", "rate": 150}, quality="preview")
        doc = json.loads((out / f"{name}.doc.json").read_text())
        _storyboard(out / f"{name}.mp4", doc, [s["seconds"] for s in rep["scenes"]], out / f"{name}_storyboard.png")
        res[name] = {"script": script, "seconds": round(sum(s["seconds"] for s in rep["scenes"]), 1),
                     "qc": [s["qc"] for s in rep["scenes"]], "continuity": sum(len(s["continuity"]) for s in rep["scenes"]),
                     "framing": [s.get("camera", {}).get("framing") for s in rep["scenes"]],
                     "notes": rep["notes"], "assets": rep["assets"], "video": rep["video"], "delivery": rep["delivery"],
                     "subtitles": rep["subtitles"], "render_s": round(time.time() - t0, 1)}
    (out / "report.json").write_text(json.dumps(res, indent=1, default=str))
    return res


def run_unfamiliar(out: Path) -> dict:
    """The unfamiliar script through the director (studio.film), narrated."""
    from . import studio
    t0 = time.time()
    rep = studio.film(UNFAMILIAR, out / "unfamiliar.mp4", "The Pelican", voice={"lang": "en", "rate": 150},
                      quality="preview")
    doc = json.loads((out / "unfamiliar.doc.json").read_text())
    _storyboard(out / "unfamiliar.mp4", doc, [s["seconds"] for s in rep["scenes"]], out / "storyboard.png")
    report = {"benchmark": "unfamiliar", "script": UNFAMILIAR, "seconds": round(sum(s["seconds"] for s in
                                                                                  rep["scenes"]), 1),
              "scenes": rep["scenes"], "notes": rep["notes"], "assets": rep["assets"], "critic": rep["critic"],
              "video": rep["video"], "timing": {"total_s": round(time.time() - t0, 1),
                                                "render_s": rep["render_seconds"]},
              "qc_clean_scenes": sum(1 for s in rep["scenes"] if s["qc"].startswith("clean")),
              "continuity_issues": sum(len(s["continuity"]) for s in rep["scenes"])}
    (out / "report.json").write_text(json.dumps(report, indent=1, default=str))
    return report

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("benchmarks_out")
    q = sys.argv[3] if len(sys.argv) > 3 else "preview"
    for n in (list(DOCS) + ["unfamiliar"]) if which == "all" else which.split(","):
        r = run(n, dest, q)
        print(n, json.dumps({k: r.get(k) for k in ("seconds", "qc_clean_scenes", "continuity_issues", "video",
                                                    "timing", "qc")}, default=str), flush=True)


# ---- Film B: "Bus Stop" (3 minutes) ----------------------------------------------------------------------------------
def _bus_in(what, stop, t="+0.0"):
    """A bus cruises in and brakes to a stop (two moves: steady, then easing out)."""
    return [step("move", t=t, what=what, to=stop - 4.0, speed=7.0, ease="linear"),
            step("move", t="+0.0", what=what, to=stop, dur=1.2, ease="out")]


def film_b() -> dict:
    """An original stickman story: a bus stop, a dog, two missed buses, rain, a crowded awning, a pratfall and a
    friendship. One continuous world: the bench, the shop, the lamp and the dog persist from scene to scene."""
    raj = lambda x, f=1: cast("Raj", BLUE, x, f, faceless=False, personality="energetic")      # noqa: E731
    ivy = lambda x, f=-1: cast("Ivy", PURPLE, x, f, faceless=False, personality="calm", height=1.68)  # noqa: E731
    BX = 0.0                                                    # the bus stop bench
    street = [{"name": "shop", "asset": "shop", "x": -6.2}, {"name": "lamp", "asset": "lamp", "x": 3.2, "z": 1.3},
              {"name": "tree", "asset": "tree", "x": 8.5}, {"name": "house", "asset": "house", "x": -15.0},
              {"name": "stop", "asset": "sign", "x": BX - 1.25, "z": 1.12, "data": {"text": "BUS STOP"}},
              {"name": "seat", "kind": "bench", "x": BX, "y": 0.0, "w": 1.3, "h": 0.9, "data": {"seat": 0.45, "back": 1}}]
    on_bench = {"platforms": [[BX - 0.6, BX + 0.6, 0.45]]}    # only while someone stands on the bench
    S = []
    S.append(scene("b0", "Morning", [raj(-24.0), {"name": "Walkers", "crowd": 2, "x": -10.0, "facing": 1,
                                                 "spacing": 1.4}], street, [
        step("walk", "Walkers", t=0.3, to=12.0, speed=1.2, spacing=1.6, wait=False),
        step("run", "Raj", t="+2.5", to=-12.0, speed=3.0),
        step("gesture", "Raj", t="+0.0", name="phone", dur=1.2),
        step("symbol", "Raj", t="+0.0", text="7:59!", dur=1.2),
    ], place="outdoors", timing="comedy", layers={"light": [[0, "dawn"], [8, "day"]]}))
    S.append(scene("b1", "Late again", [raj(-12.0)], [], [
        step("run", "Raj", t=0.2, to=BX + 0.35, speed=3.2),       # sits back onto the bench
        step("express", "Raj", t="+0.0", face="nervous"),
        step("say", "Raj", t="+0.1", text="Made it! ...right?"),
        step("look", "Raj", t="+0.1", at=[9.0, 1.2], dur=1.6),
        step("sit", "Raj", t="+0.2", seat=0.45, hold=3.0),
        step("gesture", "Raj", t="-2.6", name="phone", dur=2.2, wait=False),
        step("walk", "Raj", t="+0.2", to=BX - 0.9, speed=0.8),   # up, a restless step away from the bench
    ], place="outdoors", cut=False, timing="comedy", layers={"light": [[0, "day"]]}))
    S.append(scene("b2", "A dog", [raj(BX - 0.9), ivy(10.0)], [{"name": "dog", "asset": "a small brown dog", "x": 11.2}],
                   [
        step("walk", "Ivy", t=0.3, to=2.2, speed=1.2, wait=False),
        step("move", t="+0.0", what="dog", to=0.9, speed=1.4),
        step("look", "Raj", t="-1.2", at="dog", dur=1.6),
        step("double_take", "Raj", t="+0.0", at="dog"),
        step("express", "Raj", t="+0.0", face="scared"),
        step("jump", "Raj", t="+0.1", dist=0.9, height=0.35, land=0.45),     # up onto the seat
        step("symbol", "Raj", t="+0.0", text="!!", dur=1.0),
        step("move", t="-0.4", what="dog", to=0.2, dur=0.8),
        step("say", "Ivy", t="+0.2", text="He's friendly!"),
        step("gesture", "Ivy", t="+0.0", name="laugh", dur=1.6, wait=False),
        step("say", "Raj", t="+0.1", text="That's what they all say!"),
    ], place="outdoors", cut=False, timing="comedy", world=on_bench))
    S.append(scene("b3", "Friends", [raj(BX + 0.05), ivy(2.2)], [], [
        step("say", "Ivy", t=0.3, text="Sit, Biscuit."),
        step("move", t="+0.0", what="dog", to=1.5, dur=1.0),
        step("turn", "Raj", t="+0.3", facing=-1),
        step("jump", "Raj", t="+0.15", dist=0.75, height=0.2, land=-0.45),
        step("turn", "Raj", t="+0.1", facing=1),
        step("express", "Raj", t="+0.0", face="embarrassed"),
        step("gesture", "Raj", t="+0.0", name="scratch_head", dur=1.4),
        step("line", t="+0.2", lines=[
            {"who": "Raj", "text": "I'm Raj. I'm usually braver.", "to": "Ivy"},
            {"who": "Ivy", "text": "Ivy. And this is Biscuit.", "to": "Raj"},
            {"who": "Raj", "text": "Hello, Biscuit... sir.", "to": "Ivy"}]),
        step("nod", "Ivy", t="+0.1"),
    ], place="outdoors", cut=False, timing="comedy", world=on_bench))
    S.append(scene("b3b", "Waiting", [raj(BX - 0.7), ivy(2.2)],
                   [{"name": "ball", "kind": "ball", "x": 2.6, "y": 0.0, "w": 0.18, "h": 0.18, "color": [230, 80, 60],
                     "data": {"friction": 12.0}}], [
        step("gesture", "Raj", t=0.3, name="phone", dur=1.2),
        step("look", "Raj", t="+0.1", at=[9.0, 1.2], dur=1.0),
        step("gesture", "Raj", t="+0.3", name="phone", dur=1.2),
        step("look", "Raj", t="+0.1", at=[9.0, 1.2], dur=1.0),
        step("gesture", "Raj", t="+0.3", name="phone", dur=1.0),
        step("slow_burn", "Raj", t="+0.1", at=[9.0, 1.2], dur=2.0),
        step("turn", "Ivy", t="-1.4", facing=1),
        step("pick_up", "Ivy", t="+0.1", what="ball"),
        step("throw", "Ivy", t="+0.2", what="ball", at=[6.4, 0.09], flight=0.9, bounce=0.2),
        step("move", t="+0.0", what="dog", to=6.1, speed=3.2),
        step("move", t="+0.3", what="dog", to=2.9, speed=2.4, wait=False),
        step("move", t="+0.0", what="ball", to=3.3, y=0.25, speed=2.4),
        step("say", "Ivy", t="+0.1", text="Good boy!"),
        step("gesture", "Raj", t="+0.0", name="clap", dur=1.2),
        step("express", "Raj", t="+0.0", face="happy"),
    ], place="outdoors", cut=False, timing="comedy"))
    S.append(scene("b4", "The first bus", [raj(BX - 0.7), ivy(2.2)], [{"name": "bus", "asset": "a blue bus", "x": -14.0}],
                   [*_bus_in("bus", 9.5, t=0.3),
        step("say", "Raj", t="-2.2", text="Bus!"),
        step("run", "Raj", t="+0.1", to=7.6, speed=3.4, wait=False),
        step("run", "Ivy", t="+0.15", to=6.8, speed=3.0, wait=False),
        step("move", t="+0.2", what="dog", to=6.2, speed=2.8),
        step("move", t="+1.4", what="bus", to=40.0, speed=6.0, ease="in"),
        step("double_take", "Raj", t="-3.0", at="bus"),
        step("slow_burn", "Raj", t="+0.1", at="bus", dur=2.4),
    ], place="outdoors", cut=False, timing="comedy"))
    S.append(scene("b5", "Rain", [raj(7.6, -1), ivy(6.8, -1)], [], [
        step("look", "Ivy", t=0.2, at=[6.8, 4.0], dur=1.2),
        step("say", "Ivy", t="+0.1", text="Uh-oh."),
        step("run", "Raj", t="+0.2", to=-5.2, speed=3.4, wait=False),
        step("run", "Ivy", t="+0.15", to=-6.0, speed=3.2, wait=False),
        step("move", t="+0.1", what="dog", to=-6.9, speed=3.0),
        step("gesture", "Raj", t="+0.2", name="cover_face", dur=1.2),
        step("say", "Raj", t="+0.1", text="Of course it's raining."),
    ], place="outdoors", cut=False, timing="comedy",
        layers={"light": [[0, "day"], [1.0, "storm"]], "weather": [[0.8, 999, "rain", 1.0]], "wind": 0.3}))
    S.append(scene("b6", "Under the awning", [raj(-5.2, -1), ivy(-6.0, 1),
                                              {"name": "Crowd", "crowd": 3, "x": 6.0, "facing": -1}], [], [
        step("run", "Crowd", t=0.3, to=-3.6, speed=3.0, spacing=0.55),
        step("step_back", "Raj", t="+0.1", dist=0.3),
        step("symbol", "Raj", t="+0.0", text="squeeze", dur=1.2),
        step("gesture", "Ivy", t="+0.1", name="laugh", dur=1.4),
        step("move", t="+0.3", what="dog", to=-6.6, dur=0.15, wait=False),
        step("move", t="+0.15", what="dog", to=-7.0, dur=0.15, wait=False),
        step("move", t="+0.15", what="dog", to=-6.6, dur=0.15, wait=False),
        step("move", t="+0.15", what="dog", to=-6.9, dur=0.15),
        step("symbol", "Ivy", t="-0.4", text="*shake shake*", dur=1.4),
        step("gesture", "Crowd", t="+0.1", name="cover_face", dur=1.4),
        step("gesture", "Raj", t="+0.0", name="cover_face", dur=1.4),
        step("say", "Raj", t="+0.3", text="Thanks, Biscuit."),
    ], place="outdoors", cut=False, timing="comedy",
        layers={"light": [[0, "storm"]], "weather": [[0, 999, "rain", 1.0]], "wind": 0.3}))
    S.append(scene("b6b", "Rain talk", [raj(-5.5, -1), ivy(-6.0, 1),
                                        {"name": "Crowd", "crowd": 3, "x": -3.6, "facing": -1, "spacing": 0.55}], [], [
        step("line", t=0.4, lines=[
            {"who": "Ivy", "text": "Where were you going, anyway?", "to": "Raj"},
            {"who": "Raj", "text": "A job interview. At nine.", "to": "Ivy", "emotion": "sad"},
            {"who": "Ivy", "text": "It's 9:15.", "to": "Raj"},
            {"who": "Raj", "text": "...I know.", "to": "Ivy"}]),
        step("comfort", "Ivy", t="+0.2", to="Raj", dur=1.6),
        step("say", "Ivy", t="+0.1", text="They'll wait. Interviewers always run late."),
        step("nod", "Raj", t="+0.1"),
        step("express", "Raj", t="+0.0", face="happy", blend=0.8),
    ], place="outdoors", cut=False, timing="drama",
        layers={"light": [[0, "storm"]], "weather": [[0, 999, "rain", 0.7]], "wind": 0.2}))
    S.append(scene("b7", "The second bus", [raj(-5.5, 1), ivy(-6.0, 1), {"name": "Crowd", "crowd": 3, "x": -3.6,
                                                                        "facing": 1, "spacing": 0.55}],
                   [{"name": "bus2", "asset": "a blue bus", "x": -16.0}], [
        step("look", "Ivy", t=0.3, at=[0.0, 4.0], dur=1.0),
        step("say", "Ivy", t="+0.1", text="It stopped!"),
        *_bus_in("bus2", 4.5, t="+0.3"),
        step("run", "Crowd", t="+0.1", to=3.6, speed=3.2, spacing=0.6),
        step("run", "Raj", t="-1.6", to=-0.9, speed=3.4, wait=False),
        step("trip", "Raj", t="+0.5"),
        step("express", "Raj", t="+0.0", face="embarrassed"),
        step("walk", "Ivy", t="-0.6", to=-0.2, speed=1.6),
        step("comfort", "Ivy", t="+0.1", to="Raj", dur=1.6),
        step("walk", "Crowd", t="+0.2", to=12.0, speed=1.4, spacing=0.6, wait=False),
        step("move", t="+0.0", what="bus2", to=40.0, speed=6.0, ease="in"),     # gone before the scene ends
    ], place="outdoors", cut=False, timing="comedy",
        layers={"light": [[0, "storm"], [1.0, "dusk"]], "weather": [[0, 1.2, "rain", 1.0]]}))
    S.append(scene("b8", "Missed it again", [raj(1.0, 1), ivy(-0.2, 1)], [], [
        step("look", "Raj", t=0.3, at=[30.0, 1.2], dur=1.6, wait=False),
        step("look", "Ivy", t="+0.0", at=[30.0, 1.2], dur=1.6),
        step("turn", "Raj", t="+0.1", facing=-1),
        step("deadpan", "Raj", t="+0.1", dur=1.6),
        step("line", t="+0.2", lines=[
            {"who": "Ivy", "text": "Walk?", "to": "Raj"},
            {"who": "Raj", "text": "...Walk.", "to": "Ivy"}]),
        step("gesture", "Raj", t="+0.1", name="laugh", dur=1.6, wait=False),
        step("gesture", "Ivy", t="+0.1", name="laugh", dur=1.6),
        step("symbol", "Ivy", t="+0.0", text="Woof!", dur=1.0),
        step("walk", "Raj", t="+0.3", to=-12.0, speed=1.0, wait=False),
        step("walk", "Ivy", t="+0.25", to=-11.2, speed=1.0, wait=False),
        step("move", t="+0.1", what="dog", to=-10.4, speed=1.0),
        cap("THE END", t="+0.4", dur=3.0),
    ], place="outdoors", cut=False, timing="comedy", layers={"light": [[0, "dusk"], [6.0, "night"]]}))
    return {"title": "Bus Stop", "fps": 24, "scenes": S}


# ---- Film A: "Referee kaun chunta hai?" (3 minutes, Hinglish) --------------------------------------------------------
HINGLISH.update({
    "It was set up on 25 January 1950 - the day before India became a republic.":
        ("Iski sthapna 25 January 1950 ko hui - India ke republic banne se ek din pehle.",
         "इसकी स्थापना पच्चीस January उन्नीस सौ पचास को हुई, India के republic बनने से एक दिन पहले।"),
    "For its first 39 years it had a single commissioner. Two more were added in 1989, removed in 1990, and added "
    "again in 1993.":
        ("Pehle 39 saal tak isme ek hi commissioner the. 1989 mein do aur jode gaye, 1990 mein hata diye gaye, aur "
         "1993 mein phir se jode gaye.",
         "पहले उनतालीस साल तक इसमें एक ही commissioner थे। उन्नीस सौ नवासी में दो और जोड़े गए, उन्नीस सौ नब्बे में हटा दिए "
         "गए, और उन्नीस सौ तिरानवे में फिर से जोड़े गए।"),
    "Today the Commission has three members: a Chief Election Commissioner and two Election Commissioners.":
        ("Aaj Commission ke teen sadasya hain: ek Chief Election Commissioner aur do Election Commissioners.",
         "आज Commission के तीन सदस्य हैं: एक Chief Election Commissioner और दो Election Commissioners।"),
    "So how they are chosen matters.":
        ("Isliye unhe kaise chuna jaata hai, yeh maayne rakhta hai.", "इसलिए उन्हें कैसे चुना जाता है, यह मायने रखता है।"),
    "On polling day each voter's name is checked against the roll, and a finger is marked with indelible ink so no "
    "one votes twice.":
        ("Matdaan ke din har voter ka naam list se milaaya jaata hai, aur ungli par syahi lagaayi jaati hai taaki koi "
         "do baar vote na de.",
         "मतदान के दिन हर voter का नाम list से मिलाया जाता है, और उंगली पर स्याही लगाई जाती है ताकि कोई दो बार vote न दे।"),
    "A search committee headed by the Law Minister shortlists five names; the selection committee then chooses.":
        ("Law Minister ki adhyakshata mein ek search committee paanch naam shortlist karti hai; phir selection "
         "committee chunti hai.",
         "Law Minister की अध्यक्षता में एक search committee पाँच नाम shortlist करती है; फिर selection committee चुनती है।"),
    "Side by side: the Court's panel had one member from the government, one from the opposition and one judge; the "
    "Act's panel has two from the government and one from the opposition.":
        ("Saath rakh kar dekhiye: Court ke panel mein ek sarkar se, ek opposition se aur ek judge tha; Act ke panel "
         "mein do sarkar se aur ek opposition se hain.",
         "साथ रख कर देखिए: Court के panel में एक सरकार से, एक opposition से और एक judge था; Act के panel में दो सरकार से "
         "और एक opposition से हैं।"),
    "In March 2024 two election commissioners, Gyanesh Kumar and Sukhbir Singh Sandhu, were the first appointed "
    "under the new law.":
        ("March 2024 mein do election commissioners, Gyanesh Kumar aur Sukhbir Singh Sandhu, naye kanoon ke tahat "
         "pehli baar appoint hue.",
         "March दो हज़ार चौबीस में दो election commissioners, Gyanesh Kumar और Sukhbir Singh Sandhu, नए क़ानून के तहत "
         "पहली बार appoint हुए।"),
    "Petitioners alleged that the new selection panel could compromise the independence of the Election Commission; "
    "the Supreme Court declined to stay the appointments.":
        ("Yachikakartaon ne aarop lagaaya ki naya selection panel Election Commission ki swatantrata par asar daal "
         "sakta hai; Supreme Court ne appointments par rok lagaane se inkaar kiya.",
         "याचिकाकर्ताओं ने आरोप लगाया कि नया selection panel Election Commission की स्वतंत्रता पर असर डाल सकता है; Supreme "
         "Court ने appointments पर रोक लगाने से इनकार किया।"),
    "A referee is only useful if both teams trust the whistle.":
        ("Referee tabhi kaam ka hai jab dono teams uski seeti par bharosa karein.",
         "Referee तभी काम का है जब दोनों teams उसकी सीटी पर भरोसा करें।"),
    "That trust - more than any one appointment - is what the debate is about.":
        ("Yahi bharosa - kisi ek appointment se zyada - is behas ka asli mudda hai.",
         "यही भरोसा, किसी एक appointment से ज़्यादा, इस बहस का असली मुद्दा है।"),
    "Every Indian election - for Parliament and the states - is run by one body: the Election Commission of India.":
        ("Bharat ka har chunav - Parliament ho ya rajya - ek hi sanstha karaati hai: Election Commission of India.",
         "भारत का हर चुनाव, Parliament हो या राज्य, एक ही संस्था कराती है: Election Commission of India।"),
})


def _hinglish(doc: dict) -> dict:
    """Narration in Hinglish: the Hindi voice reads Devanagari with English terms; subtitles in Roman script; the
    reasoning (diagrams, source matching) stays on the English line; sources are cited per line."""
    for sc in doc["scenes"]:
        for st in sc.get("steps", []):
            if st.get("do") in ("caption", "visual"):
                hi = HINGLISH.get(st.get("reason_text", st["text"])) or HINGLISH.get(st["text"])
                if not hi:
                    raise ValueError(f"no Hinglish for: {st['text']}")
                if not st["text"].startswith("Sources:"):
                    st["voice"] = {"lang": "hi", "say": hi[1], "rate": 168}
                if st["do"] == "visual":
                    st["subtitle"] = hi[0]
                elif "reason_text" not in st:
                    st["reason_text"], st["text"] = st["text"], hi[0]
                if st.get("sources"):
                    st["cite"] = True
            elif st.get("do") == "say":
                st["text"] = HINGLISH_BUBBLES.get(st["text"], st["text"])
            elif st.get("do") == "line":
                for ln in st["lines"]:
                    ln["text"] = HINGLISH_BUBBLES.get(ln["text"], ln["text"])
    return doc


def film_a() -> dict:
    """Film A: the documentary and the explainer as one 3-minute Hinglish film, in story order."""
    import copy as _copy
    pol = {s_["id"]: s_ for s_ in political_hinglish()["scenes"]}
    doc = {s_["id"]: s_ for s_ in documentary()["scenes"]}
    order = [pol["p1"], doc["d2"], doc["dC"], doc["dB"], pol["p2"], pol["p3"], pol["p4"], doc["d9"],
             doc["d10"], doc["d11"], pol["p6"], pol["p6f"], pol["p5"], doc["d15"], pol["p8"]]
    scenes = [_copy.deepcopy(s_) for s_ in order]
    for s_ in scenes:
        s_.pop("transition", None)
    nxt = {"p6f": {"kind": "dissolve", "dur": 0.6}, "p5": {"kind": "dissolve", "dur": 0.5},
           "d2": {"kind": "fade", "dur": 0.4}, "p2": {"kind": "fade", "dur": 0.4}, "d10": {"kind": "fade", "dur": 0.4},
           "d15": {"kind": "fade", "dur": 0.5}}
    for s_ in scenes:
        if s_["id"] in nxt:
            s_["transition"] = nxt[s_["id"]]
    film = {"title": "Referee kaun chunta hai? (Film A)", "fps": 24, "scenes": scenes}
    return _hinglish(_presenters(film))
