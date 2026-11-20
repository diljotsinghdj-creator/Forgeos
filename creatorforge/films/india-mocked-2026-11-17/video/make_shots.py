"""Writes video/shots.json for "Disgust Pays" (script draft 3.1). One or more shots per script row, in order.
Camera centres are given in page pixels (1920x1080) and converted. `vo` is the approved wording; `say` only respells numbers."""
import json
import re
from pathlib import Path

V = Path(__file__).resolve().parent
S = []
SAY = [  # (pattern, spoken) applied in order to make "say"; meaning never changes
    ("138.54 million", "one hundred and thirty-eight point five four million"), ("128 posts", "one hundred and twenty-eight posts"),
    ("1.4 billion", "one point four billion"), ("in 1600", "in sixteen hundred"), ("1690", "sixteen ninety"), ("1858", "eighteen fifty-eight"),
    ("1927", "nineteen twenty-seven"), ("1952", "nineteen fifty-two"), ("₹269 a gigabyte in 2014", "two hundred and sixty-nine rupees a gigabyte in twenty fourteen"),
    ("In 2016", "In twenty sixteen"), ("4G", "four G"), ("239 million", "two hundred and thirty-nine million"), ("776 million", "seven hundred and seventy-six million"),
    ("A 2021 study of 2.73 million", "A twenty twenty-one study of two point seven three million"), ("67%", "sixty-seven percent"),
    ("From 2017", "From twenty seventeen"), ("end of 2020", "end of twenty twenty"), ("October 2024", "October twenty twenty-four"),
    ("January 2025", "January twenty twenty-five"), ("542,360", "five hundred and forty-two thousand, three hundred and sixty"),
    ("45%", "Forty-five percent"), ("30%", "thirty percent"), ("4chan", "four chan"), ("171%", "one hundred and seventy-one percent"),
    ("December 2024", "December twenty twenty-four"), ("July 2025", "July twenty twenty-five"),
    ("167, 196,", "one hundred and sixty-seven, one hundred and ninety-six,"), ("279, 324,", "two hundred and seventy-nine, three hundred and twenty-four,"),
    ("483", "four hundred and eighty-three"), ("49%", "forty-nine percent"), ("from 2019", "from twenty nineteen"),
    ("2018 and 2020", "twenty eighteen and twenty twenty"), ("125 were", "one hundred and twenty-five were"),
    ("19%", "Nineteen percent"), ("6th of 143", "sixth of one hundred and forty-three"), ("69%", "sixty-nine percent"),
    ("in 2023", "in twenty twenty-three"), ("1997", "nineteen ninety-seven"), ("world's 36", "world's thirty-six"), (" X ", " ex "), (" X,", " ex,"), (" X.", " ex.")]


def sh(beat, page, t, cam, vo="", **k):
    z0, x0, y0, z1, x1, y1 = cam
    s = {"id": f"{beat}.{len([q for q in S if q['beat'] == beat]) + 1:02d}", "beat": beat, "vo": vo, "page": page, "t": list(t),
         "cam": [z0, round(x0 / 1920, 4), round(y0 / 1080, 4), z1, round(x1 / 1920, 4), round(y1 / 1080, 4)]}
    say = vo
    for a, b in SAY:
        say = say.replace(a, b)
    if say != vo:
        s["say"] = say
    s.update(k); S.append(s)


C = (960, 540)
# ---- 1 · hook and question -----------------------------------------------------------------------------------------------
P = "02_receipt"
sh(1, P, (.56, .70), (2.4, 1356, 683, 2.4, 1356, 683), "Look closely at this number.", post=.6)
sh(1, P, (.70, .70), (2.4, 1356, 683, 2.1, 1380, 670), "138.54 million views,")
sh(1, P, (.70, .70), (2.1, 1560, 610, 1.9, 1450, 640), "for 128 posts on X,")
sh(1, P, (.70, .70), (1.9, 1450, 640, 1.6, 1250, 650), "all aimed at one group of people: Indians.")
sh(1, P, (.70, .72), (1.6, 1250, 650, 1.25, 800, 480), "Somebody counted them. A research group,")
sh(1, P, (.72, .74), (1.5, 620, 300, 1.0, *C), "the Center for the Study of Organized Hate, in January 2025.")
P = "01_feed"
sh(1, P, (0, .08), (1.0, *C, 1.3, 960, 500), "And if those posts were your only window on India…")
sh(1, P, (.08, .22), (1.3, 960, 500, 1.45, 960, 540), "…you'd think a country of about 1.4 billion people was four clips on a loop:")
sh(1, P, (.22, .42), (1.45, 1010, 520, 1.3, 1120, 470), "a traffic jam, a crowded train, a street stall,")
sh(1, P, (.42, .6), (1.3, 1120, 470, 1.5, 980, 520), "and then the traffic jam again, in case you missed it.")
sh(1, P, (.6, .6), (1.7, 960, 480, 1.7, 960, 480), "That's not a country.", cut=True)
sh(1, P, (.6, .8), (1.2, 620, 560, 1.0, *C), "That's a highlight reel edited by someone who hates you.", post=.6)
P = "03_otherfeed"
sh(1, P, (0, .24), (1.25, 520, 380, 1.0, *C), "But follow the phone's edge, off the feed, and the desk is covered in things that never trend.")
sh(1, P, (.24, .3), (1.5, 420, 500, 1.55, 400, 520), "A Moon landing.")
sh(1, P, (.3, .46), (1.5, 960, 540, 1.55, 980, 560), "Billions of payments in one month.")
sh(1, P, (.46, .88), (1.4, 1540, 560, 1.5, 1560, 600), "Three-quarters of the world's wild tigers.")
sh(1, P, (.88, .92), (1.0, *C, 1.2, 1250, 420), "None of it went viral.")
P = "03b_tiger"
sh(1, P, (0, .38), (1.0, *C, 1.15, 1050, 520), "Apparently a tiger is less engaging than a traffic jam.")
sh(1, P, (.38, .85), (1.35, 1200, 440, 1.1, 1250, 600), "Which, if you've ever met a tiger, is a bold editorial choice.", cut=True, post=.6)
sh(1, "04_title", (.1, .8), (1.0, *C, 1.15, 960, 520), "So why does the internet keep showing you the worst of India?", post=.6)

# ---- 2 · map and history -------------------------------------------------------------------------------------------------
P = "05_map"
sh(2, P, (0, .1), (1.3, 960, 420, 1.0, *C), "The answer starts with a company.")
sh(2, P, (.1, .26), (1.5, 380, 300, 1.35, 620, 360), "Follow this red line, out of London, in 1600:")
sh(2, P, (.26, .72), (1.35, 620, 360, 1.15, 1150, 580), "a royal charter to trade with the East.")
sh(2, "globe_a", (0, 0), (1.0, *C, 1.25, 1250, 520), "The ships didn't go straight.")
sh(2, "globe_b", (0, 0), (1.3, 1275, 480, 1.5, 1380, 760), "Look how far south they had to swing.")
sh(2, "globe_c", (0, 0), (1.45, 1150, 760, 1.35, 1380, 500), "Round Africa,")
sh(2, "ship_a", (0, 0), (1.25, 1100, 600, 1.4, 1250, 720), "across the Indian Ocean,")
sh(2, "ship_b", (0, 0), (1.35, 1420, 880, 1.5, 1600, 640), "and here, at the top of the Bay of Bengal,")
sh(2, "ship_c", (0, 0), (1.4, 1600, 560, 1.6, 1620, 400), "a settlement in 1690.")
sh(2, "ship_c", (0, 0), (1.8, 1560, 330, 1.7, 1480, 330), "The settlement was called Calcutta.", post=.6)
sh(2, "ship_c", (0, 0), (1.7, 480, 880, 1.6, 520, 860), "Its mission statement was \"trade\". Approximately.", cut=True)
sh(2, "globe_c", (0, 0), (1.5, 520, 860, 1.2, 800, 700), "By 1858 the Crown ran the place directly,")
sh(2, "ship_c", (0, 0), (1.3, 1300, 520, 1.0, *C), "and running someone else's country needs a story about why it's a favour.")
P = "06_macaulay"
sh(2, P, (0, .3), (1.0, *C, 1.25, 640, 340), "Here's one of the stories, in the author's own handwriting.")
sh(2, P, (.3, .35), (1.5, 620, 290, 1.5, 820, 310), "Read this line: \"a single shelf of a good European library")
sh(2, P, (.35, .4), (1.5, 820, 310, 1.35, 700, 340), "was worth the whole native literature of India and Arabia.\"")
sh(2, P, (.4, .5), (1.6, 680, 320, 1.6, 600, 400), "A confident review. Now drop down two lines.", post=.6)
sh(2, "z06_smash", (.5, .72), (1.0, *C, 1.06, 620, 500), "\"I have no knowledge of either Sanscrit or Arabic.\"", cut=True)
sh(2, P, (.7, .8), (1.3, 700, 620, 1.0, *C), "A one-star review of a library, by a reviewer who can't read the books.", post=.6)
P = "07_drain"
sh(2, P, (0, .14), (1.0, *C, 1.2, 560, 540), "And that kind of review sold.")
sh(2, P, (.14, .2), (1.5, 400, 480, 1.4, 440, 560), "In 1927 an American writer, Katherine Mayo, published Mother India,")
sh(2, P, (.2, .26), (1.4, 440, 560, 1.15, 640, 560), "a bestseller about everything wrong with the country.")
sh(2, P, (.26, .48), (1.0, *C, 1.2, 1180, 540), "Look at what Gandhi wrote back.")
sh(2, P, (.48, .5), (1.5, 1300, 400, 1.5, 1440, 420), "\"The report of a drain inspector,")
sh(2, P, (.5, .5), (1.5, 1440, 420, 1.3, 1340, 460), "sent out with the one purpose of opening and examining the drains of the country.\"", post=.6)
sh(2, P, (.5, .5), (1.9, 1260, 370, 1.9, 1260, 370), "A drain inspector.", cut=True)
sh(2, P, (.5, .62), (1.5, 1500, 300, 1.4, 1450, 260), "Remember that phrase.")
sh(2, P, (.62, .9), (1.3, 1340, 800, 1.15, 1200, 700), "He named the genre ninety-eight years before the algorithm monetised it.")
sh(2, P, (.9, .9), (1.15, 1200, 700, 1.0, *C), "But the vocabulary still needed an update.")
P = "08_worlds"
sh(2, P, (0, .14), (1.25, 560, 320, 1.15, 640, 340), "And in 1952 it got one.")
sh(2, P, (.14, .24), (1.3, 560, 320, 1.3, 1000, 320), "Follow the three columns. First World, Second World,")
sh(2, P, (.24, .4), (1.3, 1000, 320, 1.4, 1480, 340), "and the Third World: countries aligned with neither Cold War bloc.")
sh(2, P, (.4, .72), (1.3, 1480, 420, 1.25, 1340, 620), "That's all it meant. Then Western usage quietly changed it to mean \"poor\".", post=.6)
sh(2, P, (.72, .92), (1.5, 1100, 800, 1.35, 1100, 740), "A definition, updated without notice.", cut=True)

# ---- 3 · mechanics -------------------------------------------------------------------------------------------------------
P = "08b_data"
sh(3, P, (0, .14), (1.25, 480, 320, 1.05, 860, 480), "And that's when the phones arrived.")
sh(3, P, (.14, .3), (1.2, 900, 620, 1.4, 860, 560), "Look at the first bar: ₹269 a gigabyte in 2014.")
sh(3, P, (.3, .68), (1.25, 1050, 640, 1.15, 1250, 660), "Now watch it fall.", post=1.4, build=2.6)
sh(3, P, (.68, .68), (1.5, 1220, 460, 1.6, 1300, 400), "In 2016 a new 4G network, Jio, launched with free data.", post=.6)
sh(3, P, (.68, .72), (1.3, 560, 600, 1.4, 500, 640), "Internet subscribers went from 239 million")
sh(3, P, (.72, .87), (1.6, 480, 650, 1.7, 520, 660), "to 776 million.", post=.5, build=1.6)
sh(3, P, (.87, .88), (1.0, *C, 1.1, 900, 560), "Hundreds of millions of people, filming their own lives.")
sh(3, P, (.88, .92), (1.3, 1300, 330, 1.5, 1400, 260), "And the regulator gave its slide a modest title.")
sh(3, P, (.92, .92), (1.6, 1400, 250, 1.5, 1380, 270), "Fair title. The rest of the internet chose a different one.", cut=True, post=.6)
P = "09_dial"
sh(3, P, (0, .3), (1.0, *C, 1.25, 660, 500), "Look at this dial. It measures what the feed actually rewards.")
sh(3, P, (.3, .5), (1.2, 900, 460, 1.35, 1460, 380), "A 2021 study of 2.73 million posts found that")
sh(3, P, (.5, .5), (1.5, 1470, 400, 1.7, 1420, 480), "every word about the \"other side\" raised the odds of a share by about 67%.")
sh(3, P, (.5, .85), (1.25, 1200, 640, 1.0, *C), "Outrage isn't a bug in the feed. It's the fuel.", cut=True, post=.6)
P = "10_angry"
sh(3, P, (0, .5), (1.0, *C, 1.3, 1150, 760), "And for years one platform priced it. Look at these two stacks.")
sh(3, P, (.5, .6), (1.45, 1340, 740, 1.5, 1400, 680), "From 2017, Facebook's feed counted an angry reaction as worth five likes,")
sh(3, P, (.6, .9), (1.25, 700, 680, 1.15, 620, 720), "according to its own documents, reported by the Washington Post.")
sh(3, P, (.9, .9), (1.6, 460, 640, 1.5, 520, 650), "The weight was cut, and reached zero by the end of 2020.")
sh(3, P, (.9, .9), (1.0, *C, 1.12, 1000, 640), "Critics note \"angry\" was the least-used reaction.")
sh(3, P, (.9, .9), (1.8, 1290, 800, 1.8, 1290, 800), "Least used. Best paid.", cut=True, post=.6)
P = "11_repost"
sh(3, P, (0, .15), (1.0, *C, 1.25, 520, 540), "Now follow one video. Here, on the left, an ordinary market street,")
sh(3, P, (.15, .18), (1.5, 430, 460, 1.4, 430, 600), "posted by the person who filmed it.")
sh(3, P, (.18, .36), (1.3, 700, 500, 1.3, 1020, 500), "Follow the arrow. Someone else reposts it")
sh(3, P, (.36, .5), (1.5, 1200, 480, 1.7, 1200, 380), "with a caption we've blacked out.")
sh(3, P, (.5, .66), (1.3, 1480, 520, 1.45, 1580, 470), "Since October 2024, X has paid creators")
sh(3, P, (.66, .86), (1.5, 1600, 560, 1.4, 1560, 620), "by engagement from its Premium subscribers.")
P = "11b_slot"
sh(3, P, (0, .58), (1.0, *C, 1.25, 1320, 600), "Picture it: the original gets a few hundred views.")
sh(3, P, (.58, .86), (1.2, 560, 560, 1.08, 700, 560), "The insult gets a salary.", cut=True, post=.9, build=1.8)
P = "16_fakes"
sh(3, P, (0, .1), (1.5, 660, 200, 1.25, 800, 320), "And look closely: some of this \"proof\" isn't even real.")
sh(3, P, (.1, .3), (1.3, 620, 500, 1.5, 380, 500), "Fact-checkers stamped them: AI-generated.")
sh(3, P, (.3, .5), (1.5, 950, 500, 1.55, 950, 500), "Scripted.", post=.4)
sh(3, P, (.5, .7), (1.5, 1540, 500, 1.0, *C), "Not filmed in India at all.", post=.6)

# ---- 4 · stakes ----------------------------------------------------------------------------------------------------------
P = "12_count"
sh(4, P, (0, .2), (1.3, 620, 300, 1.2, 600, 280), "So how big did it get? CSOH kept counting.")
sh(4, P, (.2, .27), (1.6, 520, 250, 1.5, 560, 270), "About 542,360")
sh(4, P, (.27, .28), (1.4, 640, 300, 1.3, 700, 330), "anti-South Asian posts on X")
sh(4, P, (.28, .72), (1.2, 760, 400, 1.2, 760, 700), "in eighteen months. Read the three lines underneath.")
sh(4, P, (.72, .72), (1.5, 620, 500, 1.5, 860, 510), "45% call South Asians \"invaders\" or \"job thieves\".")
sh(4, P, (.72, .72), (1.5, 640, 670, 1.5, 880, 680), "About 30% use a single slur, one that CNN traces back to 4chan.")
sh(4, P, (.72, .82), (1.3, 760, 780, 1.6, 600, 830), "And the fastest-growing kind of insult, up 171%, is about hygiene.", post=.6)
sh(4, "13b_inspector", (0, .78), (1.0, *C, 1.15, 1150, 500), "The drain inspector has gone digital. With a blue tick.", cut=True, post=.6, build=3.0)
P = "13_timing"
sh(4, P, (0, .16), (1.2, 960, 380, 1.0, *C), "But posts are just posts. Unless you follow the timeline off the screen.")
sh(4, P, (.16, .29), (1.4, 480, 460, 1.5, 400, 520), "December 2024, the visa fight on X.")
sh(4, P, (.29, .33), (1.5, 400, 600, 1.35, 520, 580), "Arguing about visas isn't racism; the slurs that rode along with it were.")
sh(4, P, (.33, .46), (1.5, 900, 380, 1.5, 1040, 420), "July 2025, Tallaght, in Dublin:")
sh(4, P, (.46, .48), (1.7, 1060, 430, 1.4, 1000, 460), "police record an assault on an Indian man as racially motivated.")
sh(4, P, (.48, .64), (1.3, 1300, 680, 1.4, 1500, 740), "August, Australia: rally flyers single out Indian migration.")
sh(4, P, (.64, .8), (1.4, 520, 400, 1.6, 380, 330), "And here, in Canada, the police numbers.")
P = "bars_c"
sh(4, P, (0, 0), (1.5, 1200, 620, 1.5, 1330, 600), "Hate crimes against South Asians: 167, 196,")
sh(4, P, (0, 0), (1.5, 1400, 560, 1.6, 1520, 520), "279, 324,")
sh(4, P, (0, 0), (1.7, 1640, 480, 1.9, 1670, 440), "and then 483.", post=.6)
sh(4, P, (0, 0), (1.4, 760, 300, 1.25, 800, 340), "Up 49% in one year.")
sh(4, P, (0, 0), (1.7, 420, 680, 1.55, 480, 660), "To be precise: no study shows a post caused an attack.")
sh(4, P, (0, 0), (1.25, 900, 560, 1.0, *C), "What lines up is the timing.")
P = "14_classifier"
sh(4, P, (0, .3), (1.0, *C, 1.3, 700, 420), "So who was supposed to stop it? Look at this page from 2019.")
sh(4, P, (.3, .3), (1.5, 560, 360, 1.5, 800, 390), "A test account in Kerala, flooded in three weeks with hate,")
sh(4, P, (.3, .3), (1.5, 800, 390, 1.6, 900, 420), "most of it aimed at other Indians, and much of it never flagged:")
sh(4, P, (.3, .3), (1.7, 760, 460, 1.6, 700, 450), "no classifiers for Hindi or Bengali.")
sh(4, P, (.3, .58), (1.5, 700, 520, 1.3, 1420, 700), "Facebook says it added them in 2018 and 2020. Then check the corner.", post=.6)
sh(4, P, (.58, .6), (1.6, 1480, 690, 1.5, 1470, 700), "Of the 128 posts CSOH logged,", cut=True)
sh(4, P, (.6, .8), (1.5, 1470, 700, 1.0, *C), "125 were still up.", post=.8, build=1.6)
P = "15_drains"
sh(4, P, (0, .1), (1.6, 480, 300, 1.5, 520, 320), "But there's a catch, and we have to say it.")
sh(4, P, (.1, .2), (1.5, 520, 320, 1.35, 600, 400), "The problems in those clips are real.")
sh(4, P, (.2, .345), (1.4, 1000, 300, 1.6, 1000, 270), "19% of households had no toilet in the last national survey.")
sh(4, P, (.345, .47), (1.5, 1560, 270, 1.6, 1580, 270), "India ranks 6th of 143 for polluted air.")
sh(4, P, (.47, .62), (1.5, 1000, 620, 1.6, 1010, 630), "About one food sample in five failed a standard.")
sh(4, P, (.62, .76), (1.25, 1280, 560, 1.5, 1560, 640), "And scam call centres exist. Indian police raid them,")
sh(4, P, (.76, .76), (1.75, 1500, 620, 1.6, 1560, 640), "and Indians get the most scam calls of anyone surveyed: 69%.", post=.6)
sh(4, P, (.76, .97), (1.4, 480, 760, 1.25, 560, 720), "So yes, the drains exist. The feed just never shows anything else.", cut=True)

# ---- 5 · synthesis -------------------------------------------------------------------------------------------------------
sh(5, "17_sowhat", (0, .78), (1.25, 640, 520, 1.0, *C), "So if the feed only shows the drains, here's what it leaves out.", post=.6)
P = "18_softpower"
sh(5, P, (0, .2), (1.2, 1000, 480, 1.0, *C), "First, look at what's sitting just outside the frame.")
sh(5, P, (.2, .3), (1.5, 660, 400, 1.6, 640, 410), "\"Naatu Naatu\" won an Oscar in 2023.")
sh(5, P, (.3, .5), (1.4, 1280, 440, 1.6, 1440, 430), "India's payments system handles billions of transactions a month.")
sh(5, "08b_data", (.95, .95), (1.7, 1400, 250, 1.6, 1390, 260), "Extraordinary achievements, as the regulator would say.", cut=True)
sh(5, P, (.5, .82), (1.0, *C, 1.2, 1100, 680), "Modestly.", post=.7, build=1.0)
P = "18b_achievers"
sh(5, P, (0, .14), (1.4, 420, 220, 1.1, 800, 420), "Look at these names.")
sh(5, P, (.14, .27), (1.5, 760, 540, 1.6, 750, 620), "Kalpana Chawla, the first Indian-born woman in space, 1997.")
sh(5, P, (.27, .4), (1.5, 1190, 540, 1.6, 1200, 620), "Sunita Williams, who commanded the space station.")
sh(5, P, (.4, .9), (1.25, 820, 300, 1.1, 960, 380), "Named. Not viral.", cut=True, post=.8, build=1.5)
P = "18c_faces"
sh(5, P, (0, .5), (1.0, *C, 1.1, 960, 520), "And look at the people. Twelve Indians:")
sh(5, P, (.5, .8), (1.3, 720, 760, 1.3, 1240, 760), "an officer, a scientist, a singer, a student.")
sh(5, P, (.8, .86), (1.1, 960, 560, 1.0, *C), "None of them went viral.")
sh(5, P, (.86, .9), (1.5, 1500, 240, 1.3, 1380, 320), "The algorithm looked at them and saw nothing to be angry about.", post=.6)
P = "rivers"
sh(5, P, (0, .3), (1.25, 520, 360, 1.25, 760, 460), "Now follow this river down from the Himalaya.")
sh(5, P, (.3, .5), (1.4, 640, 420, 1.4, 1060, 520), "Past the Yamuna, past the Gandak,")
sh(5, P, (.5, .85), (1.3, 1200, 640, 1.5, 1500, 780), "to the Sundarbans, the largest mangrove forest on Earth.")
sh(5, "relief_a", (0, 0), (1.35, 900, 620, 1.0, *C), "And pull back:")
sh(5, "relief_c", (0, 0), (1.0, *C, 1.2, 1000, 560), "four of the world's 36 biodiversity hotspots.", post=.6)
sh(5, "relief_b", (0, 0), (1.2, 1100, 520, 1.0, *C), "That's the country.")
P = "19_notinterested"
sh(5, P, (0, .28), (1.0, *C, 1.3, 560, 500), "Here's the feed. And this part's on us.")
sh(5, P, (.28, .62), (1.6, 540, 330, 1.75, 540, 380), "Right here, in the corner: three dots. \"Not interested.\"")
sh(5, "19b_button", (0, .9), (1.2, 1500, 500, 1.0, *C), "The cheapest act of good manners on the internet.", post=.8, build=3.0)
P = "20b_edit"
sh(5, P, (0, .4), (1.0, *C, 1.1, 900, 540), "India isn't a caricature. It's about 1.4 billion people,")
sh(5, P, (.4, .92), (1.1, 900, 540, 1.3, 860, 520), "and the feed keeps editing them down to one drain.", post=.6)
P = "20_end"
sh(5, P, (0, .5), (1.25, 700, 320, 1.0, *C), "And laughing at that edit? That review was written in 1927.", cut=True)
sh(5, P, (.5, .8), (1.25, 860, 640, 1.1, 960, 640), "It's had a very long run for a one-star book.")
sh(5, P, (.8, .9), (1.1, 960, 640, 1.0, *C), "", hold=2.6)

cfg = {"slug": "disgust-pays", "title": "Disgust Pays", "channel": "printfacts", "voice": "af_heart", "speed": 1.1, "treatment": "pulse",
       "guide": {"CSOH": "C S O H", "Jio": "Jee-oh", "Tallaght": "Talla", "Naatu": "Nah-too", "Chawla": "Chow-la", "Sanscrit": "Sanskrit",
                 "Sundarbans": "Soon-dar-bunns", "Gandak": "Gun-duck", "Yamuna": "Yum-oo-na"},
       "reload_pages": json.loads((V / "reload_pages.json").read_text()) if (V / "reload_pages.json").is_file() else [],
       "shots": S}
(V / "shots.json").write_text(json.dumps(cfg, indent=1, ensure_ascii=False))
print(len(S), "shots")
