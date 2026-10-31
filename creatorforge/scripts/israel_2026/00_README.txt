ISRAEL 2026: THE ELECTION THAT SETTLED NOTHING - CreatorForge production package
Long-form investigative satire documentary, English, ~44 min at voice speed 1.0 / ~48 min at 0.9. Research cut-off 31 Oct 2026.

FILES
  A_Script_Israel_2026_The_Election_That_Settled_Nothing.txt   full word-for-word script in CreatorForge format
                                                               (8 chapters, 334 pictures, graphics, citations, tone per line)
  render/R1 ... R6                                             the same script split into six CreatorForge render parts
                                                               (CreatorForge renders up to 20,000 characters / 15 min at a time)
  B_Storyboard_Timestamped.txt                                 every line with start time, pictures and graphics
  C_Asset_Manifest.txt                                         every asset type, source and licence; hard rules
  D_Character_and_Animation_Directions.txt                     the 8 animated gags, motifs, comedy rules
  E_Voiceover_Direction.txt                                    voice, pace, ElevenLabs settings, pronunciation guide
  F_Evidence_Register.txt                                      106 claims: source URL, date, evidence, status, contradictions
  G_Editing_Plan.txt                                           structure, workflow, pacing, sound, export, corrections
  H_YouTube_Package.txt                                        5 titles, 3 thumbnails, SEO description, chapters, tags, pinned comment
  I_Pre_Upload_Checklist.txt                                   what to re-check on upload day (coalition talks will move)
  pod_israel_longform.sh                                       renders all six parts on the pod and joins them
  parts/                                                       source parts + build.py (rebuilds A, render/, B after edits)

MAKE IT (pod terminal; never share the terminal link)
  curl -fsSL https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/israel_2026/pod_israel_longform.sh -o israel.sh
  bash israel.sh                       # CreatorForge narration
  bash israel.sh /workspace/vo         # with your ElevenLabs files R1.mp3 ... R6.mp3 (one per render part)

FROM THE APP INSTEAD
  Generate -> Script, paste one render part at a time (R1 ... R6), 16:9, YouTube Documentary, Investigative desk,
  Faceless, Fast cuts (OFF for R3), voice pace 0.9x, captions on, music off.

EDITING THE SCRIPT
  Edit parts/p1-p5.txt (or parts/inserts.py), then from creatorforge/worker:  python ../scripts/israel_2026/parts/build.py
  It rebuilds A, render/ and B, and checks each part fits CreatorForge's limits.

BEFORE UPLOAD: work through I_Pre_Upload_Checklist.txt. Seat numbers, the mandate and the casualty figures will change.
