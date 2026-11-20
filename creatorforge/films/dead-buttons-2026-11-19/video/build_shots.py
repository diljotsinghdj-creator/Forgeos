#!/usr/bin/env python3
"""Writes video/shots.json for "The Buttons That Do Nothing" (owner's go, 2026-11-20).
One or more shots per SCRIPT_TABLE.md row, in order; `vo` is the approved wording, `say` only respells numbers and initials for
Kokoro. The viewer trap's three waits are timed from the END of the spoken line (measured on the voice file): lamp 1 at +3.5 s,
lamp 2 at +4.0 s, lamp 3 at +1.2 s, the same times the reveal (16_reveal) prints on its tape. Run it again after --voice-only
so the waits are tuned to the real voice files:  python3 video/build_shots.py"""
import json
import math
import wave
from pathlib import Path

V = Path(__file__).resolve().parent
S = []
LOCK = lambda z, x, y: (z, x, y, z, x, y)


def sh(id, beat, vo, page, t, cam, **kw):
    d = {"id": id, "beat": beat, "vo": vo, "page": page, "t": list(t), "cam": list(cam)}
    d.update(kw); S.append(d)


def audible(n):
    """(length, audible end) of voice file n, or None before the first --voice-only run."""
    f = V / "audio" / f"{n:03d}.wav"
    if not f.is_file():
        return None
    import array
    with wave.open(str(f)) as w:
        sr, a = w.getframerate(), array.array("h", w.readframes(w.getnframes()))
    step = w.getnchannels() if False else 1
    peak = max(1, max(abs(x) for x in a)); last = len(a) - 1
    while last > 0 and abs(a[last]) < peak * 0.02:
        last -= 1
    return len(a) / sr, (last + 1) / sr


def wait(n_line, target, t0, t1, cue, tail=0.5):
    """For the silent shot after spoken shot n_line: the lamp's cue must land `target` seconds after the voice stops.
    Returns (post for the spoken shot, hold and build for the silent shot)."""
    m = audible(n_line)
    if m is None:
        k = round(target * 12); post = 0.0
    else:
        length, end = m
        best = None
        for extra in range(0, 4):                       # whole frames of post on the spoken shot
            dur = (math.ceil(length * 24 - 1e-6) + extra) / 24
            gap = dur - end                             # silence already heard before the silent shot starts
            k = round((target - gap) * 12)
            err = abs(gap + k / 12 - target)
            if best is None or err < best[0] - 1e-9:
                best = (err, extra, k, dur - length)
        _, extra, k, post = best
    build = (k - 0.5) / 12 * (t1 - t0) / (cue - t0)      # the timeline crosses the cue on step k exactly
    return round(post, 4), round(k / 12 + tail, 4), round(build, 4)


# ================= 1 · Hook and question (the trap is set)
p1, h1, b1 = wait(1, 3.5, .30, .84, .82)
p2, h2, b2 = wait(4, 4.0, .25, .80, .78)
p3, h3, b3 = wait(7, 1.2, .53, .64, .62)
sh("1.01", 1, "Before anything else, a small test.", "01_press_v", (0, .06), LOCK(1.0, .5, .5))
sh("1.02", 1, "This is your button. When you're ready, press it. In your head.", "01_press_v", (.06, .30), (1.0, .5, .5, 1.1, .5, .52), post=p1)
sh("1.03", 1, "", "01_press_v", (.30, .84), LOCK(1.12, .5, .52), hold=h1, build=b1, post=0)                      # [WAIT 3.5 s] lamp 1
sh("1.04", 1, "There. It heard you.", "01_press_v", (.84, .90), (1.2, .58, .5, 1.25, .6, .5), build=.15, post=.6)
sh("1.05", 1, "Again. Take your time. Whenever you like.", "02_again_v", (0, .25), (1.1, .46, .5, 1.1, .53, .5), post=p2)
sh("1.06", 1, "", "02_again_v", (.25, .80), LOCK(1.16, .5, .5), hold=h2, build=b2, post=0)                      # [WAIT 4.0 s] lamp 2
sh("1.07", 1, "Lovely. Very responsive, this button.", "02_again_v", (.80, .95), (1.2, .56, .46, 1.26, .58, .46), post=.6)
sh("1.08", 1, "One last time. Press it… now.", "03_now_v", (0, .53), (1.1, .5, .5, 1.2, .5, .5), post=p3)
sh("1.09", 1, "", "03_now_v", (.53, .64), LOCK(1.26, .5, .47), hold=h3, build=b3, post=0)                        # [WAIT 1.2 s] lamp 3
sh("1.10", 1, "Hold on to that feeling. We're coming back for it.", "03_now_v", (.64, .90), (1.15, .54, .5, 1.25, .6, .52))
sh("1.11", 1, "Because that button lives on a panel. And look what else is on it.", "04_panel", (0, .62), (1.0, .5, .5, 1.03, .5, .5))
sh("1.12", 1, "A crosswalk button in New York.", "04_panel", (.62, .665), (1.0, .5, .5, 1.5, .13, .5))
sh("1.13", 1, "The \"door close\" button in a lift.", "04_panel", (.665, .705), (1.5, .13, .5, 1.6, .31, .48))
sh("1.14", 1, "The thermostat on the office wall that everyone fights over.", "04_panel", (.705, .78), (1.6, .6, .4, 1.7, .87, .27))
sh("1.15", 1, "Each one makes the same promise: press me, and the world will do what you want.", "04_panel", (.78, .79), (1.45, .87, .3, 1.0, .5, .5))
sh("1.16", 1, "So how many of them are actually wired to anything?", "04_panel", (.79, .92), (1.0, .5, .5, 1.12, .56, .42), post=.6)
sh("1.17", 1, "And if some aren't, why does pressing them still feel so good?", "04_panel", (.92, .93), (1.5, .87, .7, 2.2, .875, .79), post=.6)
sh("1.18", 1, "I went back to the reports, the regulations and the original studies.", "04_panel", (.93, .94), (1.4, .57, .3, 1.7, .57, .3))
sh("1.19a", 1, "Some of these buttons do nothing.", "24_recap", (0, .01), (1.8, .12, .4, 2.0, .12, .62))
sh("1.19b", 1, "Some do something very specific.", "24_recap", (.01, .02), (2.0, .31, .36, 2.0, .31, .56))
sh("1.19c", 1, "And your brain can't tell which.", "24_recap", (.02, .04), (1.35, .5, .5, 1.0, .5, .5))
sh("1.20", 1, "", "05_title", (0, .75), (1.0, .5, .5, 1.04, .5, .5), hold=2.1, build=1.5, post=0)

# ================= 2 · Map and history (where the dead buttons are)
sh("2.01", 2, "Start with the crosswalk box. Look closely at its face.", "06_crosswalk", (0, .045), (1.0, .5, .5, 1.6, .15, .34))
sh("2.02", 2, "In February 2004, the New York Times went counting these.", "06_crosswalk", (.045, .56), (1.0, .5, .5, 1.2, .62, .62),
   say="In February two thousand and four, the New York Times went counting these.")
sh("2.03", 2, "City figures said about 3,250 walk buttons were left on the streets.", "07_count", (0, .44), (1.0, .5, .5, 1.12, .58, .42),
   say="City figures said about three thousand two hundred and fifty walk buttons were left on the streets.")
sh("2.04", 2, "More than 2,500 of them did nothing at all.", "07_count", (.44, .72), (1.3, .74, .4, 1.6, .7, .5), post=.6,
   say="More than twenty-five hundred of them did nothing at all.")
sh("2.05", 2, "The paper's phrase for them: \"mechanical placebos\".", "08_placebo", (0, .30), (1.0, .5, .5, 1.5, .6, .25), post=.6)
sh("2.06", 2, "Which is a sugar pill, bolted to a lamppost.", "08_placebo", (.54, .60), (1.32, .24, .34, 1.42, .24, .33), cut=True, build=.25)
sh("2.07", 2, "So why were they there at all?", "08_placebo", (.60, .62), (1.25, .62, .3, 1.25, .52, .3))
sh("2.08", 2, "A city traffic official said they went in when traffic was much lighter.", "08_placebo", (.62, .72), (1.3, .6, .48, 1.55, .6, .53))
sh("2.09", 2, "Then the signals moved onto central, computer-controlled timing.", "08_placebo", (.72, .81), (1.45, .66, .62, 1.55, .68, .66))
sh("2.10", 2, "The buttons stayed on the poles, connected to nothing.", "08_placebo", (.81, .95), (1.3, .5, .64, 1.8, .26, .63), post=.6)
sh("2.11", 2, "About 750 still worked. So a press was worse than a one-in-four bet.", "07_count", (.72, .90), (1.4, .3, .5, 1.8, .75, .8),
   say="About seven hundred and fifty still worked. So a press was worse than a one-in-four bet.")
sh("2.12", 2, "Worse than a coin toss. With extra walking.", "07_count", (.90, 1), (2.2, .72, .82, 2.3, .72, .82), cut=True, post=.6)
sh("2.13", 2, "And it isn't just New York. Follow the wire across the Atlantic.", "09_london", (0, .5), (1.9, .2, .48, 1.9, .29, .56))
sh("2.14", 2, "TfL told the BBC in 2013: at most London junctions, the button does control the green man.", "09_london", (.5, .5), (1.3, .75, .3, 1.6, .86, .24),
   say="T F L told the B B C in twenty thirteen: at most London junctions, the button does control the green man.")
sh("2.15", 2, "If nobody presses, the lights skip the walking part.", "09_london", (.5, .5), (1.5, .66, .36, 1.75, .645, .38))
sh("2.16a", 2, "But at busy junctions, the Department for Transport said,", "09_london", (.5, .64), (1.2, .7, .66, 1.45, .76, .74))
sh("2.16b", 2, "the green man may come up every time anyway.", "09_london", (.64, .65), (1.8, .76, .78, 1.9, .78, .8))
sh("2.17", 2, "Like a waiter who brings the bill regardless.", "09_london", (.86, .90), (1.8, .28, .86, 1.9, .28, .86), cut=True, build=.25)
sh("2.18", 2, "Then, in 2020, Sydney did something unusual. It admitted it.", "10_sydney", (0, .5), (1.9, .2, .5, 1.9, .29, .56), post=.6,
   say="Then, in twenty twenty, Sydney did something unusual. It admitted it.")
sh("2.19a", 2, "So nobody had to touch the buttons during COVID,", "10_sydney", (.5, .5), (1.5, .69, .28, 1.3, .69, .32))
sh("2.19b", 2, "central Sydney's crossings were switched to automatic.", "10_sydney", (.5, .6), (1.4, .73, .66, 1.6, .73, .7))
sh("2.20a", 2, "Some buttons even got covers.", "10_sydney", (.6, .69), (1.9, .69, .29, 2.1, .69, .29))
sh("2.20b", 2, "Given the afternoon off, indefinitely.", "10_sydney", (.69, .75), (1.7, .9, .48, 1.85, .9, .48), cut=True, build=.25, post=.6)
sh("2.21a", 2, "Slide right, to the lift. Here's \"door close\".", "11_lift", (0, .28), (2.0, .15, .3, 2.0, .15, .62))
sh("2.21b", 2, "Everyone has pressed it. With feeling.", "11_lift", (.28, .68), (2.4, .14, .64, 2.6, .14, .64))
sh("2.22", 2, "In 1990, the United States passed the Americans with Disabilities Act.", "11_lift", (.68, .68), (1.3, .7, .2, 1.55, .73, .17),
   say="In nineteen ninety, the United States passed the Americans with Disabilities Act.")
sh("2.23", 2, "Its accessibility standards put a floor under how long lift doors stay open.", "11_lift", (.68, .69), (1.35, .72, .3, 1.35, .74, .42))
sh("2.24", 2, "Read this line. The doors stay fully open for at least three seconds.", "11_lift", (.69, .69), (1.5, .74, .4, 1.95, .7, .46))
sh("2.25", 2, "And your button isn't allowed to cut that short.", "11_lift", (.69, .78), (1.4, .75, .7, 1.5, .76, .76), post=.6)
sh("2.26a", 2, "In 2016 the lift trade group told the Times", "12_lift_split", (0, .19), (1.3, .2, .35, 1.5, .25, .35),
   say="In twenty sixteen the lift trade group told the Times")
sh("2.26b", 2, "working close buttons were phased out after the law.", "12_lift_split", (.19, .34), (2.0, .45, .36, 2.2, .47, .4))
sh("2.27", 2, "But here's the other side, from the same industry.", "12_lift_split", (.34, .35), (1.2, .6, .3, 1.35, .66, .24))
sh("2.28", 2, "Later, the same group said it isn't merely a placebo: it works, after the legal wait.", "12_lift_split", (.35, .82), (1.6, .78, .38, 1.9, .8, .42))
sh("2.29a", 2, "So the honest answer is: it depends on the building.", "12_lift_split", (.82, .84), (1.0, .5, .5, 1.15, .6, .45))
sh("2.29b", 2, "Owners choose how the button behaves.", "12_lift_split", (.84, .90), (1.6, .68, .76, 1.75, .68, .78))
sh("2.30a", 2, "Pan down to the thermostat.", "13_office", (0, .10), (1.3, .3, .2, 1.3, .3, .44))
sh("2.30b", 2, "In January 2003, the Wall Street Journal reported many office thermostats are fakes.", "13_office", (.10, .29), (1.2, .28, .55, 1.4, .27, .7),
   say="In January two thousand and three, the Wall Street Journal reported many office thermostats are fakes.")
sh("2.31", 2, "Plastic boxes on the wall, so people feel they've changed the temperature.", "13_office", (.29, .295), (1.6, .59, .32, 1.9, .59, .3), post=.6)
sh("2.32", 2, "A heating trade magazine, ACHR News, ran an informal web poll of its readers that year.", "13_office", (.295, .42), (1.3, .8, .35, 1.5, .84, .3),
   say="A heating trade magazine, A C H R News, ran an informal web poll of its readers that year.")
sh("2.33", 2, "Seventy replied. Fifty-one said yes, they had installed dummy thermostats.", "13_office", (.42, .60), (1.7, .84, .36, 1.95, .84, .38))
sh("2.34a", 2, "Its own description: comfort for occupants,", "13_office", (.60, .74), (1.5, .82, .7, 1.7, .82, .71))
sh("2.34b", 2, "without giving them a direct interface to the mechanical system.", "13_office", (.74, .75), (2.0, .8, .71, 2.2, .84, .72), post=.6)
sh("2.35", 2, "Which is also how you'd describe a toddler's toy steering wheel.", "13_office", (.75, .76), (2.5, .56, .3, 2.6, .56, .3), cut=True)
sh("2.36", 2, "To be fair, that's seventy people who clicked, not a census.", "13_office", (.86, .90), (2.2, .65, .9, 2.4, .65, .9), build=.3, post=.6)

# ================= 3 · Mechanics (the reveal, and why it works)
sh("3.01a", 3, "Psychologists named that feeling in 1975,", "14_langer", (0, .05), (1.0, .5, .5, 1.1, .42, .42),
   say="Psychologists named that feeling in nineteen seventy-five,")
sh("3.01b", 3, "when Ellen Langer published a paper called \"The Illusion of Control\".", "14_langer", (.05, .18), (1.4, .27, .27, 1.7, .27, .27))
sh("3.02a", 3, "Her definition, right here:", "14_langer", (.18, .36), (1.2, .66, .42, 1.4, .7, .42))
sh("3.02b", 3, "an expectancy of personal success inappropriately higher than the objective probability would warrant.", "14_langer", (.36, .37), (1.6, .7, .42, 1.9, .72, .44))
sh("3.03", 3, "In plain English: feeling in charge of things that are luck.", "14_langer", (.37, .62), (1.5, .66, .74, 1.7, .66, .8), build=.5)
sh("3.04a", 3, "Look at her lottery.", "15_lottery", (0, .10), (1.0, .5, .5, 1.1, .5, .45))
sh("3.04b", 3, "Office workers were offered a one-dollar ticket, printed with a football player.", "15_lottery", (.10, .19), (1.6, .2, .8, 1.9, .16, .8))
sh("3.05", 3, "Twenty-seven people chose their own card. Twenty-six were handed one.", "15_lottery", (.19, .195), (1.7, .3, .42, 2.0, .26, .46))
sh("3.06", 3, "Same price. Same odds. Same draw.", "15_lottery", (.195, .20), (1.45, .33, .34, 1.6, .33, .36), post=.6)
sh("3.07", 3, "Then, before the draw, she asked: what would you sell your ticket back for?", "15_lottery", (.20, .21), (1.2, .46, .42, 1.5, .34, .3))
sh("3.08", 3, "People who'd been handed a ticket asked, on average, about two dollars.", "15_lottery", (.21, .43), (1.3, .62, .45, 1.5, .6, .5))
sh("3.09", 3, "People who'd picked their own asked for about eight sixty-seven.", "15_lottery", (.43, .73), (1.5, .66, .45, 1.6, .7, .36), post=.6)
sh("3.10", 3, "Four times the price. For having pointed.", "15_lottery", (.84, .90), (1.8, .7, .42, 1.9, .7, .42), cut=True, build=.25)
sh("3.11", 3, "Langer's argument: luck borrows the costume of skill.", "14_langer", (.62, .90), (1.5, .22, .56, 1.7, .2, .58))
sh("3.12", 3, "You'd never pay extra for pointing, of course. Back to your button.", "16_reveal", (0, .04), (1.0, .5, .5, 1.15, .5, .52))
sh("3.13", 3, "Here's what was behind the panel.", "16_reveal", (.04, .30), (1.0, .5, .5, 1.04, .5, .5), build=1.2, post=.6)           # [TRAP REVEAL]
sh("3.14a", 3, "The button was never connected.", "16_reveal", (.30, .62), (1.0, .5, .5, 1.12, .56, .46))
sh("3.14b", 3, "Look: no wire.", "16_reveal", (.62, .76), (2.0, .49, .54, 2.1, .49, .53), build=.6, post=.6)
sh("3.15a", 3, "The lamps were on a timer.", "16_reveal", (.76, .76), (1.6, .5, .7, 1.8, .5, .76))
sh("3.15b", 3, "Lamp one lit three and a half seconds after I asked.", "16_reveal", (.76, .80), (1.7, .86, .5, 1.9, .86, .48), build=.5)
sh("3.16", 3, "Lamp two lit four seconds after \"whenever you like\".", "16_reveal", (.80, .87), (1.9, .86, .54, 1.9, .86, .6), build=.5)
sh("3.17", 3, "And lamp three lit just after \"now\", because I'm the one who said when.", "16_reveal", (.87, .95), (1.9, .86, .64, 2.1, .86, .7), build=.5, post=.6)
sh("3.18", 3, "Every lamp would have lit if you'd been making a sandwich.", "17_sandwich", (0, .78), (1.0, .5, .5, 1.08, .5, .5), cut=True)
sh("3.19", 3, "And yet, for a second, it felt like it answered you.", "17_sandwich", (.78, .80), (1.5, .72, .35, 1.8, .72, .32))
sh("3.20", 3, "That isn't gullibility. It's a well-documented habit.", "17_sandwich", (.80, .81), (1.25, .7, .55, 1.35, .7, .6), post=.6)
sh("3.21a", 3, "Run Langer's list over it. Choice: you decided when, mostly.", "14_langer", (.90, 1), (2.0, .11, .55, 2.2, .11, .55))
sh("3.21b", 3, "Involvement: your thumb did something.", "14_langer", (1, 1), (2.3, .13, .62, 2.5, .13, .62))
sh("3.22", 3, "Then the world does what it was going to do anyway, right on schedule.", "16_reveal", (.95, 1), (1.8, .5, .72, 2.0, .5, .76))
sh("3.23", 3, "Meet your brain, in its role as middle manager.", "18_manager", (0, .22), (1.0, .5, .5, 1.1, .45, .5), post=.6)
sh("3.24", 3, "It sees an action, then a result, and signs off: \"Great work, team.\"", "18_manager", (.22, .47), (1.4, .72, .3, 1.4, .66, .5))
sh("3.25", 3, "It doesn't check the wiring. It checks the timing, and it takes the credit.", "18_manager", (.47, .68), (1.5, .76, .6, 1.7, .78, .6))
sh("3.26", 3, "Which is most of corporate history, honestly, but in a skull.", "18_manager", (.83, .90), (1.5, .78, .72, 1.6, .78, .73), cut=True, build=.25, post=.6)

# ================= 4 · Stakes (we check the science)
sh("4.01", 4, "But this channel checks the science. So: check Langer.", "19_replication", (0, .14), (1.0, .5, .5, 1.4, .2, .3))
sh("4.02", 4, "Her lottery was small. Fifty-three office workers, back in the 1970s.", "19_replication", (.14, .145), (1.9, .18, .3, 2.2, .16, .36),
   say="Her lottery was small. Fifty-three office workers, back in the nineteen seventies.")
sh("4.03a", 4, "In 2021, a team ran seventeen experiments, nearly eleven thousand people:", "19_replication", (.145, .46), (1.4, .5, .3, 1.7, .5, .3),
   say="In twenty twenty-one, a team ran seventeen experiments, nearly eleven thousand people:")
sh("4.03b", 4, "does choosing make you think you'll win?", "19_replication", (.46, .47), (1.2, .5, .36, 1.25, .52, .4))
sh("4.04", 4, "Mostly, no. Choice rarely made people feel luckier, unless it really did improve their odds.", "19_replication", (.47, .53), (1.3, .5, .55, 1.5, .51, .6), build=.4, post=.6)
sh("4.05", 4, "And a 2013 review pooling many studies says the illusion is real, on average.", "19_replication", (.58, .81), (1.6, .83, .36, 1.9, .83, .38),
   say="And a twenty thirteen review pooling many studies says the illusion is real, on average.")
sh("4.06", 4, "So the feeling is real. Just smaller, and pickier, than the textbook story.", "19_replication", (.81, .97), (1.4, .5, .7, 1.0, .5, .5), post=.6)
sh("4.07a", 4, "Is a fake button bad for you, though?", "20_glass", (0, .12), (1.0, .5, .5, 1.1, .4, .45))
sh("4.07b", 4, "In 1972, Glass and Singer blasted people with unpredictable noise.", "20_glass", (.12, .29), (1.5, .28, .38, 1.3, .5, .4),
   say="In nineteen seventy-two, Glass and Singer blasted people with unpredictable noise.")
sh("4.08", 4, "Some were given a button that could stop the noise, and asked not to press it.", "20_glass", (.29, .33), (2.0, .3, .45, 2.4, .31, .46), build=.8)
sh("4.09a", 4, "Almost nobody pressed it.", "20_glass", (.33, .34), (1.3, .7, .3, 1.5, .72, .28))
sh("4.09b", 4, "And afterwards, they did better on the next tasks than people with no button.", "20_glass", (.34, .62), (1.6, .66, .5, 1.8, .64, .52))
sh("4.10a", 4, "A button nobody used, working purely by existing.", "20_glass", (.62, .63), (1.6, .26, .42, 1.6, .33, .44))
sh("4.10b", 4, "Which is the crosswalk business model.", "06_crosswalk", (0, 0), (2.2, .125, .66, 2.4, .125, .68), cut=True, post=.6)
sh("4.11", 4, "The other side: later experiments with formal consent procedures failed to replicate those after-effects.", "20_glass", (.70, .80), (1.3, .7, .7, 1.5, .72, .78), build=.5)
sh("4.12", 4, "Then 1976, a nursing home in Connecticut. Ellen Langer again, with Judith Rodin.", "21_plant", (0, .20), (1.0, .5, .5, 1.25, .34, .34),
   say="Then nineteen seventy-six, a nursing home in Connecticut. Ellen Langer again, with Judith Rodin.")
sh("4.13a", 4, "One floor heard a talk about taking charge,", "21_plant", (.20, .205), (1.7, .25, .3, 1.8, .27, .33))
sh("4.13b", 4, "and each resident chose a plant to look after.", "21_plant", (.205, .21), (1.6, .8, .42, 2.0, .82, .42))
sh("4.14", 4, "The comparison floor got plants too, cared for by the staff.", "21_plant", (.21, .22), (1.35, .62, .4, 1.35, .5, .42))
sh("4.15", 4, "Eighteen months later, a follow-up reported fewer deaths in the take-charge group.", "21_plant", (.22, .44), (1.4, .26, .6, 1.7, .25, .64), post=.6)
sh("4.16a", 4, "The two floors got different speeches from the administrator,", "21_plant", (.44, .64), (1.4, .78, .6, 1.7, .79, .63))
sh("4.16b", 4, "so you can't pin the result on a plant.", "21_plant", (.64, .65), (1.9, .82, .4, 1.6, .82, .42))
sh("4.17a", 4, "And the authors warned that more control isn't automatically better.", "21_plant", (.65, .66), (1.2, .6, .55, 1.35, .7, .6))
sh("4.17b", 4, "Too much responsibility can hurt.", "21_plant", (.66, .67), (2.0, .79, .66, 2.2, .79, .68))
sh("4.18", 4, "Nobody should be prescribing ferns.", "21_plant", (.84, .88), (1.8, .82, .25, 1.9, .82, .25), cut=True, build=.25, post=.6)
sh("4.19a", 4, "But across these studies, a sense of control seems to matter for stress.", "19_replication", (.97, 1), (1.0, .5, .5, 1.14, .5, .34))
sh("4.19b", 4, "Even a borrowed one.", "20_glass", (.80, .82), (2.0, .3, .45, 2.3, .3, .45))
sh("4.20a", 4, "That's the honest case for a placebo button.", "08_placebo", (.95, 1), (1.5, .24, .3, 1.65, .24, .32))
sh("4.20b", 4, "Here's the honest case against.", "08_placebo", (1, 1), (1.6, .24, .56, 2.0, .22, .63))
sh("4.21a", 4, "If you can't see the signal, a dead button isn't a placebo.", "06_crosswalk", (.56, .60), (1.5, .46, .4, 1.8, .46, .4))
sh("4.21b", 4, "It's a locked door.", "06_crosswalk", (.60, .60), (2.4, .125, .68, 2.6, .125, .68), post=.6)
sh("4.22a", 4, "In 2020, a federal judge in New York ruled", "22_court", (0, .20), (1.0, .5, .5, 1.2, .6, .4),
   say="In twenty twenty, a federal judge in New York ruled")
sh("4.22b", 4, "that the city's crosswalks broke the disability law.", "22_court", (.20, .24), (1.5, .76, .18, 1.7, .76, .17))
sh("4.23a", 4, "At more than 95% of signalled intersections,", "22_court", (.24, .50), (1.9, .28, .5, 2.1, .26, .43),
   say="At more than ninety-five percent of signalled intersections,")
sh("4.23b", 4, "there was nothing to tell a blind pedestrian when to walk.", "22_court", (.50, .56), (2.3, .25, .44, 1.9, .28, .5))
sh("4.24", 4, "The order that followed: accessible signals at about ten thousand intersections by the early 2030s.", "22_court", (.56, .57), (1.5, .72, .46, 1.8, .72, .46),
   say="The order that followed: accessible signals at about ten thousand intersections by the early twenty thirties.")
sh("4.25a", 4, "These buttons do something.", "22_court", (.57, .572), (1.6, .9, .75, 1.8, .92, .78))
sh("4.25b", 4, "Press one, and it tells you, in sound and vibration, when to cross.", "22_court", (.572, .575), (2.2, .935, .78, 2.6, .935, .78))
sh("4.26", 4, "In 2024 alone, the city reported fitting them at 855 intersections.", "22_court", (.575, .82), (1.5, .73, .74, 1.7, .73, .76),
   say="In twenty twenty-four alone, the city reported fitting them at eight hundred and fifty-five intersections.")
sh("4.27", 4, "New York's working buttons are being built for the people the dead ones failed.", "22_court", (.82, .95), (1.6, .73, .7, 1.0, .5, .5), post=.6)
sh("4.28", 4, "And the lift's \"door close\"? It has one more job.", "23_fire", (0, .04), (1.3, .25, .6, 1.6, .22, .66))
sh("4.29a", 4, "In fire-service mode, the lift code makes firefighters", "23_fire", (.04, .30), (1.2, .7, .3, 1.4, .73, .3))
sh("4.29b", 4, "hold that button down to close the doors.", "23_fire", (.30, .40), (1.7, .17, .7, 1.9, .17, .72))
sh("4.30", 4, "The most ignored button in the building has an emergency contract.", "23_fire", (.78, .84), (1.5, .7, .6, 1.6, .7, .61), cut=True, build=.25, post=.6)

# ================= 5 · Synthesis (the payoff)
sh("5.01", 5, "So pull back out. Here's the whole panel again.", "24_recap", (.04, .045), (1.6, .5, .5, 1.0, .5, .5))
sh("5.02a", 5, "Crosswalk: in 2004 New York, mostly dead.", "24_recap", (.045, .13), (1.5, .13, .35, 1.8, .13, .32),
   say="Crosswalk: in two thousand and four New York, mostly dead.")
sh("5.02b", 5, "In London, mostly live. In central Sydney, off duty by day.", "24_recap", (.13, .28), (1.9, .13, .38, 1.9, .13, .45))
sh("5.03", 5, "Lift: working, but only once the law has had its seconds.", "24_recap", (.28, .38), (1.6, .31, .6, 2.4, .32, .9))
sh("5.04", 5, "Thermostat: by one informal poll, plenty of installers admit to fitting dummies.", "24_recap", (.38, .48), (1.5, .85, .3, 1.7, .87, .36))
sh("5.05", 5, "And the middle manager signs off on all of them the same way.", "18_manager", (1, 1), (1.3, .32, .5, 1.5, .72, .6))
sh("5.06", 5, "Its wiring went in when traffic was much lighter, too.", "08_placebo", (1, 1), (2.2, .6, .54, 2.4, .6, .54), cut=True)
sh("5.07", 5, "So here's one useful habit. Before you press, ask what it's wired to.", "24_recap", (.48, .84), (1.0, .5, .5, 1.3, .58, .46))
sh("5.08a", 5, "A timer? A sensor? A person?", "24_recap", (.84, .90), (1.8, .57, .5, 1.8, .6, .52))
sh("5.08b", 5, "Or a facilities team hoping you'll stop emailing?", "24_recap", (.90, 1), (2.4, .68, .52, 2.6, .68, .52), cut=True)
sh("5.09a", 5, "And when it's real, use it.", "22_court", (.95, 1), (2.0, .93, .78, 2.2, .93, .78))
sh("5.09b", 5, "In central Sydney, crossings run automatically from six a.m. to ten p.m.", "10_sydney", (.75, 1), (1.3, .74, .68, 1.5, .74, .7),
   say="In central Sydney, crossings run automatically from six A M to ten P M.")
sh("5.10", 5, "After that, the button's back on duty. Press it.", "04_panel", (1, 1), (2.3, .12, .68, 2.6, .12, .7))
sh("5.11", 5, "Which leaves one last thing. Your button.", "25_last_v", (0, .02), (1.0, .5, .5, 1.3, .5, .52))
sh("5.12", 5, "Press it one more time. Whenever you're ready.", "25_last_v", (.02, .30), LOCK(1.0, .5, .5), post=0)
sh("5.13", 5, "", "25_last_v", (.30, .60), LOCK(1.12, .5, .5), hold=4.0, post=0)                                                    # [WAIT 4.0 s] no lamp
sh("5.14", 5, "Nothing. No lamp. Slightly offended? Notice that.", "25_last_v", (.60, .90), (1.0, .5, .5, 1.1, .45, .52), post=.6)
sh("5.15", 5, "That little sting is the illusion leaving the room.", "16_reveal", (1, 1), (1.5, .5, .5, 2.0, .5, .76))
sh("5.16", 5, "To be fair, one button in this film worked every single time.", "26_pause", (0, .28), (1.2, .5, .4, 1.0, .5, .5))
sh("5.17", 5, "It's down here, in the corner of your screen. The pause button.", "26_pause", (.28, .60), (1.0, .5, .5, 1.8, .1, .85), post=.6)
sh("5.18", 5, "That one was always connected. To you.", "26_pause", (.60, 1), (1.0, .5, .5, 1.08, .5, .52), cut=True, post=1.4)

cfg = {"slug": "the-buttons-that-do-nothing", "title": "The Buttons That Do Nothing", "channel": "dragonpsych", "voice": "bm_daniel", "speed": 1.0,
       "treatment": "pulse", "guide": {"Langer": "Langer"}, "reload_pages": ["16_reveal"], "shots": S}
(V / "shots.json").write_text(json.dumps(cfg, indent=1, ensure_ascii=False))
print(len(S), "shots", "| trap:", (p1, h1, b1), (p2, h2, b2), (p3, h3, b3))
