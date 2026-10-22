"""Narration said in full (numbers, rupees, acronyms), long sentences split for the voice, and picture cuts that
stay on the words."""
import importlib.util
import sys
from pathlib import Path

from creatorforge_worker.pipeline import _beat_lengths
from creatorforge_worker.providers.speech import number_words, speakable


def test_numbers_rupees_and_acronyms_are_said_in_full():
    assert speakable("The ED found ₹13 crore in 2024.") == "The E D found thirteen crore rupees in twenty twenty-four."
    assert speakable("40% of MPs said NO") == "forty percent of M Ps said NO"
    assert speakable("6,060 cases, CBI and PMLA") == "six thousand and sixty cases, C B I and P M L A"
    assert speakable("NEET and the INDIA bloc") == "NEET and the INDIA bloc"


def test_hindi_numbers_and_acronyms():
    assert speakable("ED ने ₹13 करोड़ जब्त किए", "hi") == "ई डी ने तेरह करोड़ रुपये जब्त किए"
    assert speakable("13.3 करोड़ नाम, 40% वोटर", "hi") == "तेरह दशमलव तीन करोड़ नाम, चालीस प्रतिशत वोटर"
    assert number_words("2000", "hi") == "दो हज़ार"
    assert speakable("Hola 13", "es") == "Hola 13"           # other languages left to the voice


def _server_chunks():
    path = Path(__file__).parents[1] / "creatorforge_worker" / "chatterbox_server.py"
    src = path.read_text()
    code = src[src.index("def _pieces("):src.index("def unload(")]
    ns = {"re": __import__("re")}
    exec(code, ns)
    return ns["chunks"]


def test_long_sentences_are_split_for_the_voice():
    chunks = _server_chunks()
    long_hi = "ईडी ने बताया कि घोटाले में करीब ₹13 करोड़ की रकम, कई फर्जी कंपनियों, बैंक खातों और बिचौलियों के जरिए, " * 6
    parts = chunks(long_hi)
    assert len(parts) > 2 and all(len(p) <= 220 for p in parts)
    assert " ".join(parts).split() == long_hi.split()            # nothing lost
    assert chunks("पहला वाक्य।दूसरा वाक्य।", limit=12) == ["पहला वाक्य।", "दूसरा वाक्य।"]


def test_cuts_follow_the_words_not_the_ending_hold():
    texts = ["The ED raided", "five", "offices in Delhi and Mumbai on Friday morning", "and found cash"]
    # no word timings: the 4.8 s of speech is shared, the hold after it stays on the last picture
    lengths = _beat_lengths(texts, [], 7.32, spoken=4.8)
    assert abs(sum(lengths) - 7.32) < 1e-6
    assert abs(sum(lengths[:3]) - 4.8 * 12 / 15) < 1e-6
    # Whisper gave the one-word beat almost no time: it borrows, the other cuts stay on their words
    starts = [0, 0.3, 0.6, 0.85, 0.95, 1.1, 1.4, 1.7, 2.0, 2.3, 2.6, 2.9, 3.2, 3.5, 3.8, 4.1]
    lengths = _beat_lengths(texts, starts, 7.32, spoken=4.4)
    assert all(x >= 0.3 for x in lengths) and abs(sum(lengths) - 7.32) < 1e-6
    assert abs(lengths[0] - 0.85) < 1e-6
