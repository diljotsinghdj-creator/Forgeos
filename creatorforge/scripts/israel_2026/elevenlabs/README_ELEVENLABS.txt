ELEVENLABS NARRATION - Israel 2026 (Hinglish and English)

FILES
  Hinglish_R1 ... R6_ElevenLabs.txt   Hindi/Hinglish narration (Devanagari; numbers written as Hindi words)
  English_R1 ... R6_ElevenLabs.txt    English narration
  One file per CreatorForge render part. Each has the spoken lines only, in order, with <break> pauses:
  0.6 s normal, 0.7 s after a question, 0.8 s after a strong line, 1.0 s after a dramatic one, 1.5 s before a chapter.
  The text is identical to what CreatorForge speaks, so voiceover_sync can match it line for line.

ELEVENLABS SETTINGS
  Model: Eleven Multilingual v2 (reads Hindi + English words together well and honours <break> tags).
    If you use a newer model and it reads the tags aloud or ignores them, delete the <break .../> lines; the
    full stops still give natural pauses.
  Voice: Hinglish = a Hindi-capable voice (Indian male or female news/documentary voice from the Voice Library with a
    commercial licence, or your own voice). English = a calm documentary voice. No cloned real person or known anchor.
  Stability 55-60 | Similarity 75 | Style 10-15 (0 for Part 4 / R3) | Speaker boost ON | Speed 1.0 (Hinglish), 0.95 (English)
  Output: MP3 44.1 kHz 192 kbps.
  Use the SAME voice and settings for every chunk and part.

HOW TO GENERATE
  Option A (easiest): ElevenLabs Studio / Projects -> new project -> paste a whole R file (without the # and ===== lines)
    -> convert -> export one MP3. Name it R1.mp3 ... R6.mp3.
  Option B (Text to Speech): paste each CHUNK separately (chunks are under 2,800 characters), download each, name them
    R1_1.mp3, R1_2.mp3, ... then join them on the pod (below).
  Listen to chunk 1 first: check names (Eisenkot, Knesset, Netanyahu) and numbers. Regenerate a chunk if a word is wrong.

JOIN CHUNKS ON THE POD (Option B), after uploading the MP3s to /workspace/vo_hi (or /workspace/vo for English)
  cd /workspace/vo_hi
  for n in 1 2 3 4 5 6; do ls R${n}_*.mp3 | sort -V | sed "s/.*/file '&'/" > l.txt; ffmpeg -y -loglevel error -f concat -safe 0 -i l.txt -c:a libmp3lame -b:a 192k R$n.mp3; done

PUT IT ON THE VIDEO
  Hinglish:  bash israel_hi.sh /workspace/vo_hi     (renders R1-R6, syncs each part to your R<n>.mp3, joins the film)
  English:   bash israel.sh /workspace/vo
  Already rendered a part in the app? python -m creatorforge_worker.voiceover_sync <job id> /workspace/vo_hi/R1.mp3

IF YOU CHANGE THE SCRIPT
  Edit the script lines, run the build scripts, then: python3 make_elevenlabs.py   (re-makes these files)
