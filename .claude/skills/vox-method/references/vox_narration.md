# Narration: voice, delivery and writing for the ear

How the narration sounds and how its sentences are built. Read this at the script stage and before recording.
CreatorForge: Print Facts uses the owner's own ElevenLabs voice (only with permission); Kokoro is for drafts and
timing only.

Labels: [V] source-backed (sources.md P#, case_studies/) · [I] interpretation · [O] our rule.

---

## 1. What the studied craft shows

- [V] One producer owns a video from pitch to delivery (P6, P9, P42; P1 and P24 snippet only). One senior producer
  voices his own script once it is locked (P9). [I] The voice that explains is the voice that researched it, which
  is why it sounds like explaining rather than reading. No source confirmed that producers always narrate their own
  films (sources.md §I).
- [V] "Look at this": naming the evidence and then showing it grabs attention, and is underused in explainers (P16).
- [V] Different formats change the voice: analyst-narrated short explainers for fast news; a travelling host for
  field series; presenter authority for a policy piece; a host who joins the experiment in long-form series
  (PATTERNS: politics §8, history/geography §8, econ/tech §9).
- [V] Long-form series allow breathers, reflection and emotional moments, not just cramming facts (P18).
- [V] First-hand guides explain their own reasoning in their own words, and say what is still unknown
  (PATTERNS sci/culture §5).
- [V] The narration names its own limits: one producer publicly named the flaw in her setup (P3).

- [V] **Measured (case_studies/TRANSCRIPT_STUDY.md and the four watch-based case studies):**
  - narration runs at about **167 words a minute** (147–190 on sampled segments; about 2.8 words a second);
  - sentences in punctuated transcripts run a median of **15–16 words** (range 7–35), with short punches mixed in;
  - expert voices enter as soundbites, not long interviews;
  - field sound is sometimes played *as* evidence ("this is what it usually sounds like").

## 2. Narrator personality [O]

- **The curious expert friend:** has done the reading, is still a bit amazed, explains without condescending.
- **First person sparingly and honestly:** "I went through the filings" only if someone did. A faceless channel's
  "we" is the studio.
- **Stance:** confident where the evidence is strong, explicit where it is uncertain ("we don't know", "the records
  stop here").
- **Never** salesy, breathless or doom-laden. No "buckle up", no "you won't believe".

## 3. Sentence construction (writing for the ear) [O]

- **Sentences of about 15 words on average** (measured median 15–16), varied hard: short punches (5–8 words) after
  reveals, an occasional long one (25+) that carries a list or a build.
- **One idea per sentence; one number per sentence.**
- **Subject–verb early:** "The canal lifts ships 26 metres," not "Lifting ships some 26 metres is what the canal…".
- **Concrete nouns and active verbs** that can be pictured.
- **Spoken numbers:** round as the source allows ("almost a third", "about 2 million"), with the exact figure on
  screen.
- **Signposts the ear needs:** "Here's the thing." "But." "So." "Which raises a question." Used, not overused.
- **Questions to the viewer** at chapter turns, not every paragraph.
- **Banned phrases** (CreatorForge `BANNED_PHRASES`): delve, testament, moreover, "in a world where", "it's important
  to remember", "let's unpack", "buckle up", game-changer, tapestry…
- **Read every line aloud before locking it.** If you stumble, rewrite it.

## 4. Information density [O]

- Explanatory runs: one new idea every 10–15 seconds (about 25–40 words).
- Evidence and human beats: half that density, more holds.
- Never introduce a new term and a new number in the same sentence.
- Repetition is a feature: restate the central question at each act turn in new words.

## 5. Delivery direction (for the recording script) [O]

Mark up `script_narration.md`:
- `/` short pause (~0.3 s) · `//` long pause (~0.8 s) · `[beat]` 1–1.5 s hold
- **bold** = stressed word (usually the new information, often the number)
- `{pron: …}` pronunciation for names and places, checked against an authoritative source
- `(warmer)`, `(flatter)`, `(slower)` mood notes per paragraph, sparingly
- Pace target: about 160–175 words per minute (about 2.8 words/s, the measured Vox median) overall; slower for
  evidence and human beats, faster for lists.

## 6. Recording and checking [O]

- Draft timing with a free TTS voice; real narration only with permission (ElevenLabs credits).
- After recording, re-time the blueprint from the real audio. Never estimate after audio exists.
- Check: no mispronunciations, consistent level, breaths trimmed but not removed (natural), no mouth clicks.

## 7. Failure modes

| Failure | Fix |
|---|---|
| Reads like an essay | Shorter sentences, active verbs, signposts, read aloud |
| A wall of numbers | One per sentence; the rest on screen or cut |
| Monotone authority | Mood notes; stress the new information; pauses after reveals |
| Fake first person | Only claim what was done |
| Hype vocabulary | Plain words; banned-phrase check |
