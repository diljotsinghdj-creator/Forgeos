"""Writes video/shots.json for the render engine (channels/design_kits/film_video.py) from the approved script rows.
Run from the film folder:  python3 video/build_shots.py
The voiceover text comes straight from script_table.py (the approved wording); each row is split into shots here and the
script asserts that the pieces of a row join back to the row's exact wording. Cameras are written in page pixels (1920x1080)."""
import json
import re
import sys
from pathlib import Path

D = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(D))
import script_table as ST  # noqa: E402

ROWS = [(int(b), re.sub(r"\s*⚠", "", vo).strip(), cam) for _, rows in ST.ACTS for b, vo, _, cam, _ in rows]

# Spoken respellings for Kokoro (meaning unchanged; captions keep the approved spelling).
SAY = {
    "dominio absoluto y perpetuo": "doh-meen-yo ahb-so-loo-toh ee pair-pet-woe",
    "a perpetuidad": "ah pair-pet-wee-dahd",
    "irrenunciable e imprescriptible": "ee-ray-noon-see-ah-blay eh eem-press-creep-tee-blay",
    "Día del Mar": "dee-ah del mar", "Topáter": "toh-pah-tair", "Abaroa": "ah-bah-roh-ah", "Antofagasta": "antofa-gasta",
    "Titicaca": "titi-kahka", "Tiquina": "tee-kee-nah", "Ancón": "ahn-cone", "Arica's": "ah-ree-kah's", "Arica": "ah-ree-kah",
    "Ilo": "ee-loh", "La Paz": "lah pahss", "Litoral": "lee-toh-rahl",
    "1963": "nineteen sixty-three", "1904": "nineteen oh four", "1884": "eighteen eighty-four", "1879": "eighteen seventy-nine",
    "1878": "eighteen seventy-eight", "1874": "eighteen seventy-four", "1883": "eighteen eighty-three", "1913": "nineteen thirteen",
    "1992": "nineteen ninety-two", "2013": "twenty thirteen", "2015": "twenty fifteen", "2018": "twenty eighteen", "2009": "two thousand nine",
}
GUIDE = {k: v for k, v in SAY.items() if not k[0].isdigit()}


def say(vo):
    out = vo
    for k, v in sorted(SAY.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(rf"(?<!\w){re.escape(k)}(?!\w)", v, out)
    return out.replace('"', "")


SHOTS, _row = [], {}


def S(row, vo, page, t0, t1, cam, **kw):
    z0, x0, y0, z1, x1, y1 = cam
    _row.setdefault(row, []).append(vo)
    n = len(_row[row])
    s = {"id": f"{ROWS[row][0]}.{row + 1:02d}{'abcd'[n - 1]}", "beat": ROWS[row][0], "vo": vo, "page": page, "t": [t0, t1],
         "cam": [z0, round(x0 / 1920, 4), round(y0 / 1080, 4), z1, round(x1 / 1920, 4), round(y1 / 1080, 4)]}
    sp = say(vo)
    if sp != vo:
        s["say"] = sp
    s.update(kw)
    SHOTS.append(s)


H = {"post": 0.6}          # [HOLD 0.6s]
C = {"cut": True}          # [CUT]
CH = {"cut": True, "post": 0.6}

# ---- 1 · hook ---------------------------------------------------------------------------------------------------------
S(0, "This is a navy.", "01_navy", 0, .12, (1.2, 760, 640, 1.25, 770, 640), pre=.5)
S(1, "Look at the altitude.", "01_navy", .12, .85, (1.25, 1300, 640, 1.25, 1400, 420), build=1.9, **H)
S(2, "Most navies measure depth.", "01_navy", .85, .86, (1.12, 960, 620, 1.16, 1000, 640))
S(2, "This one mostly measures height.", "01_navy", .86, .95, (1.3, 1400, 600, 1.36, 1420, 610), **C)
S(3, "Navies need a sea.", "01_navy", .95, 1, (1.2, 900, 660, 1.0, 960, 540))
S(3, "So I went looking for this one's, and I found its autopsy report instead.", "02_receipt", 0, .2, (1.0, 960, 540, 1.05, 960, 560))
S(4, "Look closely at this line.", "02_receipt", .2, .45, (1.06, 900, 540, 1.18, 840, 560))
S(4, 'The coast belongs to Chile, it says, with "dominio absoluto y perpetuo".', "02_receipt", .45, .8, (1.3, 738, 580, 1.33, 720, 590), **H)
S(5, "Absolute. And perpetual. Treaty writers don't hedge.", "02_receipt", .8, .92, (1.2, 700, 600, 1.24, 700, 610), **C)
S(6, "Lake Titicaca sits about three thousand eight hundred metres up,", "03_lighttable", 0, .42, (1.5, 800, 430, 1.2, 860, 480))
S(6, "the highest lake on Earth that big ships can sail.", "03_lighttable", .42, .7, (1.1, 1200, 620, 1.25, 1380, 680))
S(7, "Follow this line west.", "03_lighttable", .7, 1, (1.3, 1150, 480, 1.3, 760, 520))
S(7, "The country that owns this navy has no coast at all, and that treaty is why.", "04_nocoast", 0, .42, (1.15, 1300, 480, 1.15, 900, 600), **H)
S(8, "So why does a country with no sea", "04_nocoast", .42, .66, (1.0, 960, 540, 1.3, 960, 850))
S(8, "keep a navy on a lake in the clouds?", "04_nocoast", .66, .9, (1.12, 700, 520, 1.04, 860, 540))
S(9, "To answer that, I'm going to run this backwards.", "05_title", 0, .3, (1.0, 960, 540, 1.06, 960, 520))
S(9, "Date by date, to the day the coast went missing.", "05_title", .3, .8, (1.12, 700, 450, 1.04, 900, 520), **H)
# ---- 2 · the rewind ---------------------------------------------------------------------------------------------------
S(10, "The stamp stops at January 1963.", "06_1963", 0, .06, (1.6, 300, 200, 1.5, 340, 220))
S(10, "That's when Bolivia set up a River and Lake Force.", "06_1963", .06, .3, (1.1, 700, 520, 1.18, 660, 540))
S(11, "Follow its name. River and lake. Not sea.", "06_1963", .3, .82, (1.05, 960, 480, 1.3, 980, 440), **H)
S(12, "So the navy is younger than the problem. Keep rewinding.", "06_1963", .82, 1, (1.25, 1300, 700, 1.25, 1000, 640))
S(13, "October 1904.", "07_1904", 0, .1, (1.5, 360, 240, 1.4, 400, 260))
S(13, "The treaty we just read is signed in Santiago, twenty years after the shooting stopped.", "07_1904", .1, .6, (1.0, 960, 540, 1.14, 1000, 470))
S(14, "It didn't take the coast. It made a loss that had already happened permanent.", "07_1904", .6, .9, (1.2, 1250, 620, 1.3, 1380, 700), **H)
S(15, "Rewind again. April 1884.", "08_1884", 0, .16, (1.4, 400, 300, 1.3, 420, 330))
S(15, "A truce: the fighting stops, and Chile keeps running the coast it holds.", "08_1884", .16, .5, (1.1, 800, 500, 1.25, 900, 520))
S(16, "That truce lasted twenty years,", "08_1884", .5, .6, (1.5, 1020, 500, 1.55, 1040, 520))
S(16, 'which is a long time to leave something on "pending".', "08_1884", .6, .9, (1.3, 1250, 700, 1.36, 1300, 740), **CH)
S(17, "Keep going. The stamp slows down,", "09_1879", 0, .1, (1.5, 380, 250, 1.4, 420, 280))
S(17, "because this is where the coast actually leaves.", "09_1879", .1, .12, (1.0, 960, 540, 1.2, 1000, 560))
S(18, "Fourteenth of February, 1879.", "09_1879", .12, .2, (1.3, 500, 330, 1.2, 560, 380))
S(18, "Chilean troops land at the port of Antofagasta. There's no resistance.", "09_1879", .2, .5, (1.2, 500, 480, 1.2, 1050, 640))
S(19, "And that's the day the coast started to come off the map.", "09_1879", .5, .8, (1.0, 960, 540, 1.25, 800, 600), **H)
S(20, "But why? Rewind one more year, to a tax.", "10_1878", 0, .16, (1.3, 1300, 400, 1.2, 640, 460))
S(21, "In 1878 Bolivia's assembly approves a tax of ten centavos", "10_1878", .16, .2, (1.3, 560, 440, 1.5, 520, 450))
S(21, "on every quintal of nitrate a Chilean company ships out.", "10_1878", .2, .4, (1.1, 1100, 420, 1.15, 1250, 400))
S(22, "A quintal is about forty-six kilos. Ten centavos.", "10_1878", .4, .72, (1.32, 1200, 620, 1.4, 1280, 660))
S(23, "The most expensive ten cents in South American history.", "10_1878", .72, .9, (1.15, 1100, 700, 1.22, 1160, 760), **CH)
S(24, "Here's Chile's side.", "11_sides", 0, .1, (1.0, 960, 540, 1.08, 800, 500))
S(24, "A treaty in 1874 had promised no new taxes on Chilean companies there for twenty-five years.", "11_sides", .1, .4, (1.15, 640, 500, 1.3, 600, 520))
S(25, "Here's Bolivia's. This was Bolivian soil, and a sovereign country taxes its own soil.", "11_sides", .4, .7, (1.15, 1200, 500, 1.3, 1300, 520), **H)
S(26, "The company refused to pay.", "12_trigger", 0, .2, (1.1, 500, 420, 1.25, 460, 400))
S(26, "Bolivia moved to seize and auction its property, on the fourteenth of February.", "12_trigger", .2, .4, (1.45, 500, 440, 1.3, 440, 360))
S(27, "The same day Chile's troops landed.", "12_trigger", .4, .62, (1.08, 900, 520, 1.15, 960, 540))
S(27, "Historians list deeper causes: nitrate wealth, a secret alliance, a vague border.", "12_trigger", .62, .8, (1.3, 500, 800, 1.36, 520, 800))
S(27, "But the trigger was an auction.", "12_trigger", .8, 1, (1.35, 480, 330, 1.45, 460, 300), **H)
# ---- 3 · forward again ------------------------------------------------------------------------------------------------
S(28, "So I pressed play.", "13_topater", 0, .06, (1.5, 340, 230, 1.5, 520, 260))
S(29, "Twenty-third of March, 1879.", "13_topater", .06, .12, (1.3, 600, 360, 1.2, 700, 420))
S(29, "Near Calama, a small Bolivian force holds a bridge at a place called Topáter.", "13_topater", .12, .28, (1.05, 1000, 540, 1.15, 1040, 560))
S(30, "Its best-known defender, a civilian named Eduardo Abaroa, is killed there.", "13_topater", .28, .3, (1.3, 1100, 560, 1.3, 980, 600))
S(30, "It's the first battle of the war.", "13_topater", .3, .5, (1.15, 600, 640, 1.2, 540, 680), **H)
S(31, "Remember that date. Twenty-third of March. It comes back.", "13_topater", .5, .75, (1.3, 1000, 400, 1.6, 1070, 340))
S(32, "Peru joins on Bolivia's side.", "14_peel_v", 0, .05, (1.4, 820, 520, 1.3, 860, 560))
S(32, "The war runs until 1884, and when it ends, look at the map.", "14_peel_v", .05, .15, (1.3, 860, 560, 1.0, 960, 540))
S(33, "Peru loses a province. Bolivia loses all of its coast: the department of Litoral.", "14_peel_v", .15, .52, (1.15, 900, 640, 1.3, 760, 560), **H)
S(34, "Bolivia's government puts it at about four hundred kilometres of shore,", "14_peel_v", .52, .62, (1.5, 400, 360, 1.6, 340, 330))
S(34, "and some hundred and twenty thousand square kilometres of land.", "14_peel_v", .62, .62, (1.5, 360, 340, 1.35, 560, 520))
S(35, "Bolivia had a beach. Now it has a lake. A very high one.", "14_peel_v", .62, .68, (1.2, 700, 620, 1.3, 640, 680), **CH)
S(36, "Peru signs its peace with Chile at Ancón on the twentieth of October, 1883.", "14_peel_v", .68, .79, (1.25, 1400, 420, 1.4, 1560, 380))
S(37, "Bolivia's treaty, twenty-one years later, is signed on the twentieth of October too.", "14_peel_v", .79, .88, (1.4, 1560, 500, 1.45, 1600, 600))
S(37, "Same date. Different decade.", "14_peel_v", .88, .95, (1.6, 1620, 720, 1.7, 1620, 740), **CH)
S(38, "Which brings us back to the 1904 treaty.", "15_railway", 0, .1, (1.5, 360, 240, 1.3, 420, 300))
S(38, "Because it isn't only about what Bolivia gave up.", "15_railway", .1, .13, (1.2, 500, 360, 1.3, 440, 330))
S(39, "Follow the tabs.", "15_railway", .13, .13, (1.5, 380, 310, 1.6, 380, 310))
S(39, "Article three: Chile builds a railway from the port of Arica up to La Paz,", "15_railway", .13, .6, (1.3, 900, 640, 1.3, 1250, 400))
S(39, "at its own expense.", "15_railway", .6, .6, (1.7, 330, 360, 1.8, 300, 390))
S(40, "Fifteen years after it's finished, the Bolivian section is handed to Bolivia.", "15_railway", .6, .7, (1.3, 1300, 700, 1.4, 1350, 780))
S(41, "Article four: three hundred thousand pounds sterling, in two payments.", "15_railway", .7, .92, (1.5, 400, 740, 1.6, 360, 750))
S(42, "Article six. And look at this phrase.", "16_forever", 0, .27, (1.15, 1100, 440, 1.4, 1390, 400))
S(43, 'Chile grants Bolivia, "a perpetuidad",', "16_forever", .27, .27, (1.6, 1500, 400, 1.75, 1530, 380))
S(43, "the widest and freest right of commercial transit through its territory and ports.", "16_forever", .27, .27, (1.45, 1390, 430, 1.35, 1390, 460), **H)
S(44, "So the treaty uses forever twice.", "16_forever", .27, .4, (1.35, 1390, 460, 1.0, 960, 540))
S(44, "Once for Chile's land, and once for Bolivia's passage across it.", "16_forever", .4, .82, (1.12, 700, 480, 1.12, 1220, 520))
S(45, "It's like selling your house and getting, in writing, eternal rights to the hallway.", "17_hallway", 0, .78, (1.0, 960, 540, 1.1, 1000, 560), **CH)
S(46, "Article seven adds Bolivian customs agents in the ports.", "15_railway", 1, 1, (1.4, 1250, 400, 1.4, 960, 640))
S(46, "And to be fair to the hallway, it's a busy one.", "17_hallway", .78, 1, (1.25, 1050, 720, 1.3, 1100, 760))
S(47, "The railway opened in 1913.", "18_arica", 0, .2, (1.2, 700, 330, 1.25, 1000, 300))
S(47, "Today, about three-quarters of the cargo moving through Arica's port is Bolivian.", "18_arica", .2, .62, (1.3, 480, 520, 1.4, 440, 540))
S(48, "So Bolivia trades through the sea every day.", "18_arica", .62, .62, (1.0, 960, 540, 1.4, 1400, 700))
S(48, "It just can't put a flag on any of it.", "18_arica", .62, .92, (1.5, 400, 820, 1.6, 380, 860), **CH)
S(49, "And Chile's view of all this is simple:", "19_positions", 0, .12, (1.1, 700, 440, 1.2, 560, 420))
S(49, "a treaty signed two decades after the war, ratified by both, and honoured.", "19_positions", .12, .32, (1.4, 520, 400, 1.5, 500, 420))
S(50, "Bolivia's view:", "19_positions", .32, .52, (1.1, 1300, 460, 1.2, 1400, 440))
S(50, "a treaty signed by a country that had already lost a war, on terms it couldn't refuse.", "19_positions", .52, .72, (1.4, 1420, 440, 1.5, 1420, 460), **H)
S(51, "Both sides have also argued, for years, over whether Chile's port rules respect that article six.", "19_positions", .72, .92, (1.0, 960, 540, 1.25, 960, 700))
S(51, "Chile says it does.", "19_positions", .92, 1, (1.7, 480, 470, 1.8, 470, 480))
S(52, "Which is where the navy comes in.", "19_positions", 1, 1, (1.2, 960, 560, 1.0, 960, 540))
S(52, "Because the treaty settled the coast. It didn't settle the feeling.", "03_lighttable", 1, 1, (1.3, 900, 500, 1.0, 960, 540), **H)
# ---- 4 · stakes -------------------------------------------------------------------------------------------------------
S(53, "So what does a landlocked navy actually do all day?", "20_rivers", 0, .05, (1.3, 1300, 400, 1.5, 560, 620))
S(53, "Quite a lot, it turns out.", "20_rivers", .05, .1, (1.2, 700, 560, 1.1, 860, 540))
S(54, "Follow the water out of the mountains.", "20_rivers", .1, .2, (1.3, 760, 560, 1.3, 1000, 460))
S(54, "Bolivia's rivers run east, down into the Amazon basin.", "20_rivers", .2, .3, (1.15, 1000, 420, 1.15, 1300, 380))
S(55, "The navy patrols the lake and those rivers.", "20_rivers", .3, .36, (1.4, 1150, 340, 1.5, 1180, 320))
S(55, "It chases smugglers, carries supplies to remote towns,", "20_rivers", .36, .44, (1.5, 1200, 440, 1.6, 1220, 480))
S(55, "and pulls people out of floods.", "20_rivers", .44, .55, (1.5, 1140, 620, 1.6, 1120, 650))
S(56, "Reports put it at around five thousand people, with its main lake base at Tiquina.", "20_rivers", .55, .66, (1.2, 700, 700, 1.45, 480, 740))
S(57, "And some of its officers do get to sea, by training on other countries' ships.", "20_rivers", .66, .81, (1.25, 700, 640, 1.25, 1400, 740))
S(58, "Which is the naval version of learning to swim at a friend's house.", "20_rivers", .81, .92, (1.4, 1560, 700, 1.5, 1600, 700), **CH)
S(59, "But the navy also has a second job.", "20_rivers", .92, 1, (1.2, 600, 620, 1.1, 800, 560))
S(59, "And for that, look at the calendar.", "21_diadelmar", 0, .14, (1.5, 1500, 330, 1.7, 1640, 290))
S(60, "Every twenty-third of March, the date Abaroa died,", "21_diadelmar", .14, .16, (1.9, 1680, 270, 2.0, 1700, 250))
S(60, "Bolivia marks the Día del Mar. The Day of the Sea.", "21_diadelmar", .16, .3, (1.15, 500, 560, 1.3, 420, 600), **H)
S(61, "There are speeches, wreaths, and parades. And marching through them, the navy.", "21_diadelmar", .3, .3, (1.5, 400, 760, 1.5, 1000, 740))
S(62, "A ceremony with one guest of honour who can never attend.", "21_diadelmar", .3, .85, (1.3, 1300, 700, 1.4, 1360, 740), **CH)
S(63, "And it isn't only ceremony. It's in the constitution.", "22_art267", 0, .14, (1.0, 960, 540, 1.1, 700, 500))
S(63, "Look at article two six seven, from 2009.", "22_art267", .14, .25, (1.2, 560, 440, 1.4, 560, 440))
S(64, "Bolivia declares its right to the territory that gives it access to the Pacific", "22_art267", .25, .25, (1.5, 560, 560, 1.5, 640, 600))
S(64, '"irrenunciable e imprescriptible".', "22_art267", .25, .55, (1.1, 960, 480, 1.15, 1100, 440), **H)
S(65, "Which is the 1904 treaty's forever, answered with a forever of its own.", "22_art267", .55, .92, (1.2, 1300, 560, 1.35, 1440, 660))
S(66, "There was another attempt, from the other neighbour.", "23_boliviamar", 0, .12, (1.2, 1200, 560, 1.1, 900, 520))
S(66, "In 1992, Peru granted Bolivia a strip of beach near the port of Ilo.", "23_boliviamar", .12, .44, (1.3, 480, 460, 1.4, 440, 520))
S(67, "A free zone was promised. Decades later, reports say, it's still mostly sand.", "23_boliviamar", .44, .44, (1.5, 1100, 660, 1.5, 1500, 700))
S(68, "Five kilometres of coast, for ninety-nine years.", "23_boliviamar", .44, .44, (1.5, 440, 720, 1.6, 440, 730))
S(68, "So far, the main tenant is the sand.", "23_boliviamar", .44, .9, (1.3, 1400, 360, 1.4, 1400, 320), **CH)
S(69, "So in 2013 Bolivia tried a court.", "24a_filing", 0, .06, (1.5, 360, 240, 1.4, 420, 280))
S(69, "It asked the International Court of Justice to say that Chile must negotiate sea access.", "24a_filing", .06, .2, (1.1, 640, 460, 1.25, 560, 440))
S(70, "Not hand over the coast. Just negotiate.", "24a_filing", .2, .2, (1.7, 450, 440, 1.8, 440, 450))
S(70, "The argument was that decades of talks had created a duty to keep talking.", "24a_filing", .2, .52, (1.2, 1250, 360, 1.3, 1300, 340))
S(71, "Chile argued the court couldn't even hear it, because the 1904 treaty had already settled the matter.", "24a_filing", .52, .68, (1.15, 1200, 640, 1.3, 1340, 720))
S(72, "In 2015 the court disagreed on that point, and said it would hear the case.", "24a_filing", .68, .86, (1.4, 1340, 720, 1.5, 1380, 760))
S(73, "First of October, 2018. The judgment comes back.", "24_icj_v", .1, .24, (1.2, 600, 400, 1.1, 640, 420), build=.8, **H)
S(74, "By twelve votes to three,", "24_icj_v", .24, .4, (1.6, 480, 360, 1.7, 440, 350))
S(74, "the court finds Chile did not take on a legal obligation to negotiate.", "24_icj_v", .4, .6, (1.25, 1300, 440, 1.35, 1340, 420), **H)
S(75, "That's Chile's side, confirmed by the court.", "24_icj_v", .6, .6, (1.4, 560, 400, 1.4, 560, 440))
S(75, "And then, near the end, the judges add a paragraph.", "24_icj_v", .6, .6, (1.4, 560, 440, 2.0, 500, 510))
S(76, "Their finding, they say, shouldn't stop the two countries continuing their dialogue,", "24_icj_v", .6, .6, (2.0, 440, 510, 2.0, 560, 515))
S(76, "in a spirit of good neighbourliness.", "24_icj_v", .6, .6, (2.4, 620, 530, 2.5, 630, 530), **H)
S(77, "Nobody has to talk. But everyone is welcome to.", "24_icj_v", .6, .72, (1.3, 1020, 800, 1.4, 1020, 860), **C)
S(78, "Bolivia's government pointed to that paragraph as a reason to keep talking.", "24_icj_v", .72, .94, (1.6, 1220, 730, 1.7, 1240, 738))
S(79, "Chile's government said it was open to dialogue, but not about its sovereignty.", "24_icj_v", .94, 1, (1.45, 1360, 790, 1.35, 1300, 700), **H)
# ---- 5 · synthesis ----------------------------------------------------------------------------------------------------
S(80, "So, back to the lake. Why does landlocked Bolivia have a navy?", "25_answer", 0, .1, (1.0, 960, 540, 1.2, 900, 400))
S(81, "Part of the answer is plain geography.", "25_answer", .1, .2, (1.25, 1300, 360, 1.3, 1400, 330))
S(81, "A big lake and a lot of river need boats and people who can run them.", "25_answer", .2, .3, (1.4, 900, 420, 1.4, 1250, 500))
S(82, "The other part is paperwork.", "25_answer", .3, .3, (1.8, 1700, 260, 1.9, 1740, 270))
S(82, "A tax of ten centavos, an auction, a war, and a treaty that says forever twice.", "25_answer", .3, .6, (1.5, 400, 840, 1.5, 1150, 840))
S(83, "None of which changes the law. The treaty is in force, and the court has ruled.", "25_answer", .6, .74, (1.5, 1300, 820, 1.6, 1500, 840))
S(84, "In my reading, the navy is a sentence in the constitution that learned to march.", "25_answer", .74, .88, (1.3, 1500, 480, 1.5, 1700, 500), **H)
S(85, "Chile holds the coast, and the court agreed it doesn't have to negotiate.", "24_icj_v", 1, 1, (1.2, 800, 420, 1.3, 900, 420))
S(85, "Bolivia holds a claim it says can't expire.", "22_art267", .55, .55, (1.3, 1300, 400, 1.4, 1420, 320))
S(86, "And a navy on a lake", "01_navy", .12, .12, (1.0, 960, 540, 1.5, 860, 700))
S(86, "is how you keep a claim like that from gathering dust.", "01_navy", .12, .12, (1.9, 860, 680, 1.7, 800, 640), **H)
S(87, "Look at the altitude again.", "26_end", 0, .12, (1.3, 1500, 560, 1.3, 1500, 330))
S(88, "Three thousand eight hundred metres up. And zero kilometres of coast.", "26_end", .12, .38, (1.6, 1640, 300, 1.7, 1660, 380))
S(89, "Most navies measure depth.", "26_end", .38, .56, (1.15, 760, 400, 1.2, 700, 380))
S(89, "This one measures how long a country can remember.", "26_end", .56, .85, (1.15, 640, 600, 1.2, 600, 640), **CH)
S(90, "Every twenty-third of March, it gets measured again.", "26_end", .85, 1, (1.5, 1560, 660, 1.0, 960, 540), **H)

# every row's shots must join back to the approved wording, in order, with nothing added or dropped
assert sorted(_row) == list(range(len(ROWS))), [i for i in range(len(ROWS)) if i not in _row]
order = [int(s["id"].split(".")[1][:2]) for s in SHOTS]
assert order == sorted(order)
for i, (_, vo, _) in enumerate(ROWS):
    assert " ".join(_row[i]) == vo, (i, " ".join(_row[i]), vo)
SHOTS.append({"id": "5.end", "beat": 5, "vo": "", "hold": 2.0, "post": 0.0, "page": "26_end", "t": [1, 1], "cam": [1.0, .5, .5, 1.0, .5, .5]})

old = json.loads((D / "video" / "shots.json").read_text()) if (D / "video" / "shots.json").is_file() else {}
cfg = {"slug": "bolivia-navy", "title": "Why does landlocked Bolivia have a navy?", "channel": "printfacts", "voice": "am_eric", "speed": 1.0,
       "treatment": "pulse",
       "evidence_waiver": "owner told 2026-11-19/20; treaty page is a labelled reconstruction, scan still to be sourced",
       "guide": GUIDE, "reload_pages": old.get("reload_pages", []), "shots": SHOTS}
(D / "video" / "shots.json").write_text(json.dumps(cfg, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{len(SHOTS)} shots, {len(ROWS)} rows, {len({s['page'] for s in SHOTS})} pages")
