# Brain log

Permanent lessons from the owner's corrections, rejections and analytics. Read before pitching or writing anything.
Newest entries go at the bottom. Rules here are binding for both channels unless an entry names one.

## Used mechanics (never repeat back-to-back on the same channel)

| Channel | Film | Engine | Hook mechanism | Visual metaphors | Status |
|---|---|---|---|---|---|
| Print Facts | The BJP IT Cell (draft plan) | not pitched yet | the party president's own words ("true or false") over a black screen | message arcs across India; org chart on string; evidence board with red string | research done |
| Dragon Psychology | Phone scam / "Phantom Authority" (owner's draft v1) | explainer (before the engines existed) | a counter freezing at a number, then the smart victim | two-track brain grid; compliance staircase; balance scale; protocol card | under revision |

---

## Patches

### 2026-11-07: The two channels
- **Mistake Logged:** The storyteller character (Dastango) was being applied to every video.
- **New Permanent Rule:** Print Facts has no mascot and no Dastango. Dragon Psychology is the animation channel. (Superseded 2026-11-10: no mascot or character on either channel.)
- **Used Mechanics to Retire:** n/a
- **Winning Pattern:** Separate brand kits per channel.

### 2026-11-08: No video until "go"
- **Mistake Logged:** A draft render was started before the owner asked for one.
- **New Permanent Rule:** Build capability and scripts; produce video only when the owner says go.
- **Used Mechanics to Retire:** n/a
- **Winning Pattern:** Scripts and storyboards for review first.

### 2026-11-10: Scam script v1 review (Dragon Psychology)
- **Mistake Logged:** The draft carried invented precision as fact:
  - 4.20 s;
  - a 138-IQ victim who lost $242,000 in 18 minutes;
  - an IQ "hockey stick" curve;
  - cortisol at 300%;
  - "starves the prefrontal cortex of glucose";
  - System 1 and 2 timings.

  It also called sharing a two-factor code "harmless".
- **New Permanent Rule:**
  - Every number on screen comes from the dossier or wears an ILLUSTRATIVE tag.
  - Neuroscience lines are checked against a primary paper (e.g. Arnsten 2009) before animating.
  - Safety advice must never normalise a step real scams depend on: never read out a one-time code.
- **Used Mechanics to Retire:** the counter-freeze hook; the two-track brain grid; the compliance staircase; the
  balance scale. Used in v1, so don't reuse them in the *next* Dragon Psychology film.
- **Winning Pattern:** A five-act structure with open loops at every act end; a screenshot-ready protocol card as the
  payoff; a strict three-colour palette with 12 fps cut-outs over a smooth camera.

### 2026-11-10: The showrunner directive
- **Mistake Logged:** Films risked sharing one formula: the same hook type, act shape and metaphors.
- **New Permanent Rule:**
  - Pitch three narrative engines (Reverse Autopsy, Live Viewer Trap, Trojan Horse, Historical Echo) and wait for the pick.
  - Visual-first beats.
  - Banned phrases.
  - A pattern interrupt at least every 20 s.
  - A retention and mistake audit on every draft.
  - A Brain Log patch after every correction.

  Enforced in `studio/writer.py` (`check`, `novelty`).
- **Used Mechanics to Retire:** n/a
- **Winning Pattern:** Micro-moment first, then the system.

### 2026-11-10: Simplify CreatorForge
- **Mistake Logged:** The app carried tools for a different kind of channel: trend-chasing Shorts, autopilot plans, hook tests, a clipper, a posting calendar, analytics, a safety screen, lip-sync.
- **New Permanent Rule:** CreatorForge serves two channels only: Print Facts (researched documentaries) and Dragon Psychology (animated psychology). New features must serve one of them. Removed: Trends + Autopilot, Hook Lab, Templates, Shorts Clipper, Publish Calendar, Analytics, Safety Check, talking-mascot lip-sync. Kept: Director, Scripts, Generate, Library, Brand Kits, Cloud Studio, AI images, preset voices, stickman looks.
- **Used Mechanics to Retire:** n/a
- **Winning Pattern:** Topics come from research and the owner, not trend feeds; publishing goes through Uplika.

### 2026-11-10: No mascot
- **Mistake Logged:** A rigged dragon mascot was built for Dragon Psychology. The owner never asked for one: it was
  Claude's own assumption, written into MASTER_DIRECTIVES as if it were the owner's rule, and the owner had already
  rejected the dragon drawing on 2026-11-08.
- **New Permanent Rule:** Neither channel has a mascot or a recurring character. Both are faceless; Dragon
  Psychology's identity is its look (palette, cut-outs, type) and the narrator's voice.
- **Also permanent:** Only the owner's own words go into MASTER_DIRECTIVES. Claude's suggestions stay marked as
  suggestions until the owner says yes, and nothing is built from them before that.
- **Used Mechanics to Retire:** the dragon character, in thumbnails and scenes.
- **Winning Pattern:** Evidence and diagrams carry the film, not a character.

### 2026-11-10: Evolution sample in Hindi
- **Mistake Logged:** The owner asked for "a 10 second video on evolution", naming no language and no channel. Claude
  assumed Hindi, wrote the narration in Hindi script and spent about 330 ElevenLabs credits on it.
- **New Permanent Rule:** When a request doesn't name the language and the channel, ask before writing a script or
  spending credits (ElevenLabs, image or video models). Never guess them from an earlier film.
- **Used Mechanics to Retire:** n/a
- **Winning Pattern:** n/a

### 2026-11-10: English, and no images without asking
- **Mistake Logged:** Storyboard stills and mock-up images were made without asking; the evolution sample was in Hindi.
- **New Permanent Rule:** All videos, on both channels, are in English. No images (stills, storyboards, mock-ups, AI
  images) are created without asking the owner first.
- **Used Mechanics to Retire:** n/a
- **Winning Pattern:** n/a

### 2026-11-11: Use judgment, not the nearest template
- **Mistake Logged:** The owner kept having to point out basics:
  - logos left out of shots that name a platform;
  - a flat pin map where the globe fly-in existed;
  - a number counter where the subject (planets) should have been drawn;
  - "people standing on bars" for planets;
  - overlaps and cut-off words;
  - a mascot and Hindi narration nobody asked for.

  The pattern: the quickest available graphic was used, then shown before it was judged.
- **New Permanent Rule:** Before showing the owner anything:
  1. For every shot, ask what a Vox or Johnny Harris editor would put on screen for this exact subject. If the
     engine can't draw it, build it, or say so plainly. Never settle for a generic stand-in.
  2. Watch every frame and fix what a viewer would notice.
  3. Check the work against every patch in this log.
  4. Only then show it, and list what's still weak.
- **Used Mechanics to Retire:** generic stand-ins (counter for a subject, desk globe for planets, flat map for a place)
- **Winning Pattern:** Subject-native visuals (3D planets, the globe dive to the city, the evidence on the desk).

### 2026-11-11: Samples that look like the last ones
- **Mistake Logged:** The BJP IT cell sample repeated what the owner had already seen:
  - its shots were lifted from the BJP storyboard shown on 2026-11-10 (the family-group forward hook, the chain flowchart, 687 vs 15, the smartphone headline, the news card);
  - four of the five samples used the same narrative approach (trojan-horse) and the same voice (am_michael);
  - every sample shared one look: cream paper, grain, vignette, black title box, mono tags, one sentence per shot held 5-10 s, hard cuts.
  The variation check passed it because it compared only finished films, not samples or storyboards, and never compared the look itself.
- **New Permanent Rule:** Every sample is a film for the anti-repetition rules. Before anything is drawn:
  1. List what the owner has already seen on this subject and in the last three samples: hook, approach, shot list, look, voice, pacing.
  2. Change all of them that the 20/80 rule calls variable: approach, hook, lead technique, palette, background and texture, typography treatment, cut rhythm, transition family, opening shot.
  3. A storyboard shown to the owner counts as used: its hook and shots are not reused in a sample unless the owner asks for them.
  4. Rotate the stand-in voice when the owner's voice is not used.
- **Used Mechanics to Retire:** the family-group forward hook; one sentence per shot on cream paper; trojan-horse for samples; am_michael as the default stand-in voice
- **Winning Pattern:** The Antarctica landmarks and the 687-squares unit chart: subject-native visuals that were new to the owner.
