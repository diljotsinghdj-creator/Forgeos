# ElevenLabs narration - POLICE YA POWER?

**Voice:** a deep, authoritative male or female Hindi documentary voice from the Voice Library (search
"Hindi narrator deep" / "documentary"). Do **not** clone any real person's voice without their written consent;
no celebrity voices.

## Option A - Eleven v3 (most expressive) - 4 parts
Paste `v3_PART_1.txt`, `v3_PART_2.txt` ... in order (each under ~3,000 characters, v3's limit per generation).
Audio tags in [brackets] come from each line's tone. Settings: Stability **Natural**, language **Hindi**.
Generate 2-3 takes of each part, keep the best, export MP3 44.1 kHz / 192 kbps, join in order.

## Option B - Multilingual v2 (steadiest) - one paste
`multilingual_v2_ONE_PASTE.txt` uses `<break>` tags for pauses. Stability 0.55, Similarity 0.80, Style 0.25,
Speaker boost on.

## Numbers and acronyms
Numbers are already written as Hindi words (2026 → दो हज़ार छब्बीस) and acronyms are spelled out
(FIR → एफ़-आई-आर) so the voice cannot misread them.

## Pronunciation guide
| Written | Say | Note |
|---|---|---|
| बृजभूषण शरण सिंह | brij-bhoo-shan sha-ran singh | |
| जामिया मिल्लिया इस्लामिया | jaa-mi-yaa mil-li-yaa is-laa-mi-yaa | |
| कड़कड़डूमा | kar-kar-doo-maa | the ड़ is a flapped r |
| खनौरी | kha-nau-ri | stress on "nau" |
| शुभकरण सिंह | shubh-ka-ran singh | |
| सात्तानकुलम | saat-taan-ku-lam | Tamil place name; stress on "saat" |
| जयराज, बेनिक्स | ja-ya-raaj, be-niks | |
| शिवगंगा | shiv-gan-gaa | |
| प्रकाश सिंह | pra-kaash singh | |
| डी के बसु | dee kay ba-su | |
| अनुच्छेद | a-nuch-chhed | |

If a name comes out wrong, regenerate just that line (ElevenLabs Studio lets you select one paragraph).

## Then
On the pod: `bash pod_police_ya_power.sh /workspace/vo_hi/police_ya_power.mp3` - CreatorForge re-times every
cut to the recorded voice and renders the film.
