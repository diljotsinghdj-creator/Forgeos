---
name: collage-explainer
description: >
  Make a Vox-style paper-collage documentary (or a collage shot inside a studio film) for Print Facts or Dragon
  Psychology: an approved beat map, a locked theme chosen by bake-off, layered collage-poster keyframes made with
  AI image models, living paper motion with Gemini Omni Flash or Seedance, then narration, music and paper foley.
  All generation runs on the ElevenLabs creative flows (Nano Banana 2, GPT Image 2, Seedream, Omni Flash,
  Seedance, background removal, SFX, music). Use whenever the owner asks for the "collage", "motion collage",
  "paper collage", "torn-paper", "living poster" or "Vox-style AI" look, or for AI plates for a film.
---

# Collage explainer (adapted for CreatorForge)

Adapted on 2026-11-13 from the owner-supplied skill "vox-explainer" (Advibly). The original is kept verbatim in
`references/original/`. Its method is unchanged here; three things differ: the tools (ElevenLabs flows instead of
the Advibly MCP), the purpose (documentary, not product ads) and the house rules, which win wherever they meet.

Read before any work: `creatorforge/channels/MASTER_DIRECTIVES.md` (section 6 hard rules, section 8 AI plates),
`creatorforge/channels/STYLE_REFERENCES.md`, `creatorforge/channels/PRODUCTION_SHEET_TEMPLATE.md`, and the four
reference files here: `beat-layer.md` (STORY), `prompt-guide.md` (LOOK), `motion-collage.md` (dramatic moves),
`models-and-gotchas.md` (failure modes).

## The core idea (from the original)
1. The look is born in the IMAGE step: each shot is a finished, clearly layered collage poster (torn edges,
   cut-outs with their own shadows, halftone, one bold flat colour, a short baked headline).
2. The motion is added after: the video model animates the poster into a living collage (parallax, bob, flutter,
   or the assemble-from-empty build). The more distinct the layers, the better the motion.
3. One element stays REAL. In the Advibly original it was the product photo. **Here it is the evidence:** a real
   archival photo, document, satellite image or a real public figure's credited photograph, composited unchanged
   into the paper world ("the real photograph, unchanged, composited into the collage with its own soft contact
   shadow"). Everything else is printed paper and labelled ILLUSTRATION.

## House rules that override the original
- **Faces of real people are never generated or redrawn.** The original's section 4 ("real-person posters are fine
  to generate", "route to kling-v3 for celebrities") does NOT apply. A real person appears only from a real,
  credited photograph passed as a reference and described "unchanged, photoreal"; if a model redraws the face, the
  take is rejected. Do not use Kling or any model to animate a recognisable real person. Private people's eyes are
  covered (white strip), as in the owner's references.
- **No pick, no script (gate 1).** Phase 2's beat map and Phase 3's theme are pitched; the owner picks (or says
  "free hand"). Nothing is generated before that.
- **Evidence first (gate 3, Print Facts):** the first picture beat composites a real piece of evidence.
- **Every fact sourced:** each narration line's numbers go into the film's dossier.json with sources before any
  image is made. Comparisons are computed.
- **Pacing (gate 4):** shots of 4-6 s as the original says, but a still-like shot never holds past 4.5 s.
- **Credits:** image and video generation spends the owner's ElevenLabs credits. Bake-offs use one image per
  theme; re-roll images (cheap) before clips (dear). Never repeat a generation call to retry. Confirm with the
  owner before any run of more than about 12 clips.
- **Labels:** every AI plate or clip is logged in `creatorforge-data/assets/ledger.json` as AI-generated with model
  and prompt, and the film shows ILLUSTRATION on it. PRESHOW lists every AI shot.
- **Colour:** the theme's palette drives the film; the signature #FFDD33 stays the signal (highlighter, key number).
- **No em dashes** in any copy (from the original, also the house style).

## Tool mapping (Advibly -> ElevenLabs creative flows)
| Original | Here |
|---|---|
| `advibly_generate_image` model `nano-banana-2`, 2K | `creative_generate_image`, model `gemini-3.1-flash-image` (Nano Banana 2), resolution 2K. Fallbacks: `gpt-image-2` (dense headline text), `bytedance-seedream-5-pro` (type-heavy) |
| `reference_image_urls` (the product photo) | put the evidence photo on the flow (`creative_attach_reference_file` or upload) and connect it as the image node's reference input |
| `advibly_generate_video` `gemini-omni-flash` | `creative_generate_video`, model `gemini-omni-flash` (or `gemini-omni-1.2-flash`), start frame = the poster; 9:16 or 16:9; 4-10 s |
| Seedance `end_image_url` (hard assemble-from-empty) | `bytedance-seedance-v2` or `-v2-fast` with start_frame = empty plate, end_frame = finished poster |
| background-remover recipe | `birefnet-v2-bg-removal` image model (a real remover; prefer it to the isolate-prompt trick) |
| `advibly_generate_voiceover` | the studio's own narration (Kokoro, or the owner's ElevenLabs voice when allowed) |
| `advibly_generate_music` | `creative_generate_in_flow` music node (`eleven_music_v2_5`, instrumental) or the studio score |
| paper foley | ElevenLabs SFX node (`eleven_text_to_sound_v2`) or the studio's SFX bank and SFX_LOG |
| `advibly_render_composition` | the CreatorForge studio edit (`python -m creatorforge_worker.studio`), so every gate, PRESHOW and SFX_LOG still run |

Before the first generation each session: load the ElevenLabs tools, call `creative_get_flow_node_types`, and
`creative_get_model_guide` for any model not used before. Create one flow per film and keep every node on it.

## Phases (as in the original, with the gates)
1. **Intake:** topic, channel, length (30 s = 6-8 shots, 60 s = 10-12), aspect (9:16 or 16:9), the one question.
2. **Beat map** (`beat-layer.md`): arc, hook in under 3 s, two shots per beat (wide with headline, detail without),
   varied camera moves (no two adjacent beats alike, `static` for the payoff), rich element motion per shot.
   Narration about 2.5-3 words a second. Shown to the owner as JSON; owner approves.
3. **Theme bake-off** (`prompt-guide.md` section 5): 3-4 presets that fit the topic (or a custom mix), beat 1's
   wide poster once per theme, the owner picks by eye; that theme and image model are locked for the film. Never
   the last film's theme (SEEN.json).
4. **Keyframes:** the 5-part image prompt, style block verbatim on every poster, the real evidence composited on
   evidence beats only. Check each poster is truly layered and the real photo was not redrawn; re-roll misses.
5. **Motion:** one verbatim MOTION BLOCK (camera family, amplitude, paper physics, audio rule) shared by every clip
   so all cuts move alike, plus the per-shot element motion; the 5-axis motion prompt, positive phrasing only for Omni Flash, SFX-only audio (no spoken words),
   dramatic moves (assemble-from-empty, fly-in, scatter, impact kick, whip) only on hook, reveal and payoff.
6. **Assembly:** the clips become the film's scenes in the studio (Footage lines), narration and score on top,
   blue-box word captions, gates, PRESHOW and SFX_LOG, then sent to the owner PRESHOW first.
