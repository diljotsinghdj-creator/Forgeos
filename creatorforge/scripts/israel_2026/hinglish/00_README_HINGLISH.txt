ISRAEL 2026: WOH CHUNAV JISNE KUCH TAY NAHIN KIYA - Hinglish version
~48 min (CreatorForge timing). Research cut-off 31 Oct 2026.

Narration: everyday Hindi in Devanagari with English words where Hindi news anchors use them (coalition, majority,
caretaker, ceasefire, red line, Knesset...). Titles, description and pinned comment in Roman Hinglish.
Every spoken line matches the English script line for line (164 lines), with the SAME pictures, graphics, on-screen
text and citations - so the English evidence register and production files apply unchanged.

FILES (this folder)
  A_Hinglish_Script_Israel_2026.txt     full script, CreatorForge format
  render/R1 ... R6                      six render parts (CreatorForge limit: 20,000 characters / 15 min each)
  B_Hinglish_Storyboard.txt             every line with start time, pictures and graphics
  H_Hinglish_YouTube_Package.txt        5 Hinglish titles, 3 thumbnails, description, chapters, tags, pinned comment
  pod_israel_hinglish.sh                renders all six parts on the pod and joins them
  lines_1.txt, lines_2.txt              the Hinglish lines (edit here), build_hinglish.py rebuilds everything

SHARED WITH THE ENGLISH VERSION (one folder up): C asset manifest, D animation directions + comedy rules,
F evidence register (106 claims), G editing plan, I pre-upload checklist. Use them as they are.

VOICE (Hinglish version of E)
  CreatorForge: pick the Hindi news-anchor voice in the app (Gemini Hindi voices read mixed Hindi-English best).
    On the pod: export CF_VOICE=<that voice's id> before running the script, or leave it for the pod default.
  ElevenLabs: a Hindi-capable voice you own or have a commercial licence for (multilingual model), Stability ~60,
    Style ~15; one MP3 per render part, named R1.mp3 ... R6.mp3. No cloned voice of a real person or a known anchor.
  Delivery: conversational, like explaining to a friend; deadpan on the jokes; Part 4 (Gaza / West Bank) serious,
    slow, no smile in the voice. Names as in E_Voiceover_Direction.txt (Eisenkot = आइज़नकोट, Knesset = क्नेसेट).

MAKE IT (pod terminal; never share the terminal link)
  curl -fsSL https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/israel_2026/hinglish/pod_israel_hinglish.sh -o israel_hi.sh
  bash israel_hi.sh                    # CreatorForge Hindi narration
  bash israel_hi.sh /workspace/vo_hi   # with your ElevenLabs R1.mp3 ... R6.mp3
  Output: /workspace/creatorforge/israel_2026_hinglish/Israel_2026_Hinglish_full.mp4

FROM THE APP: Generate -> Script, paste R1 ... R6 one at a time, 16:9, YouTube Documentary, Investigative desk,
  Faceless, Fast cuts (OFF for R3), Hindi voice, pace 1.0x, captions on, music off.

BEFORE UPLOAD: ../I_Pre_Upload_Checklist.txt. If a fact changes, edit BOTH the English line (parts/) and the matching
Hinglish line (same number in lines_*.txt), then run parts/build.py and hinglish/build_hinglish.py.
