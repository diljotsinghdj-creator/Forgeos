# Master Vox motion and sandbox system (owner, 2026-11-12)

The owner's standing rules for every interactive Artifact (charts, simulations, stages for screen recording),
recorded verbatim. They bind every session. Where they differ from the film pipeline's rules, they apply to
Artifacts only.

## 1. Sandbox and security rules (strict, never violate)

- **Zero external network calls in Artifacts:** never use fetch(), XMLHttpRequest, WebSockets or external API
  URLs inside generated Artifacts. Hardcode all numbers, study citations and datasets directly inside the script.
- **Zero external CDNs or fonts:** never include `<script src="https://...">`,
  `<link href="https://fonts.googleapis.com/...">` or external JS/CSS libraries (no D3, Chart.js, Rough.js,
  Lucide CDN or Tailwind CDN). Write 100% self-contained vanilla HTML, CSS and JavaScript. Use native system
  editorial fonts (Georgia, 'Times New Roman', -apple-system, 'SF Mono', Menlo, Consolas, monospace).
- **Zero remote images:** never use `<img src="https://...">` URLs. Draw all maps, portraits, icons, arrows,
  torn-paper edges and grain textures using pure inline `<svg>` or CSS gradients/data-URIs.
- **Safe state:** keep all state in JS variables. Never use document.cookie or blocked auto-downloads.

## 2. Brand palette and editorial aesthetic

- **Colours:**
  - Canvas #F4F1EA (warm editorial paper)
  - Card inset #E8E2D5
  - Ink #1C1C1C (never pure black)
  - Slate #7A7770
  - Vox Yellow #F4D03F (always use mix-blend-mode: multiply on highlights)
  - Alert Coral #D9534F
  - Psych Teal #2E86AB
- **Stage spec:**
  - a responsive 16:9 stage (1920x1080 / 1280x720);
  - subtle paper grain (opacity 0.08);
  - warm directional desk shadows (rgba(45, 38, 25, 0.2));
  - stepped overshoot easing on card pop-ins (0 → 1.03 → 1);
  - 12 fps stepped motion (steps(2)) on hand-drawn SVG arrows, circles and underlines.
- **Journalistic receipts:** always include a small bottom-left monospace source citation (e.g. "Source: Study /
  Lab, Year") on data visuals.
- **Recording controls:** every Artifact must include a clean top-right floating control bar with "Play / Replay"
  and "Hide UI (Clean Screen)" buttons, plus a Spacebar shortcut to replay, for OBS screen recording.

## 3. Director shortcut commands

- **[SIMULATE]:** build an interactive 10-second first-person "Viewer Brain Trap" experiment (e.g. selective
  attention, anchoring, the Stroop effect) that tricks the viewer live on screen first, then reveals the
  psychological mechanism.
- **[3D_STAGE]:**
  - Use CSS 3D perspective (perspective: 1200px; transform-style: preserve-3d).
  - Stack three Z-depth layers:
    - the background map at translateZ(-200px);
    - the mid-ground torn-paper receipt at translateZ(0px);
    - the foreground cut-out or arrow at translateZ(80px).
  - Add a smooth virtual camera dolly and rack-focus blur between the layers.
- **[SFX_LOG]:** below any visual or script response, output a compact timestamped Foley and music cue table
  (e.g. [00:02.4] Low-passed felt marker wipe -22dB | [00:05.0] Cut music stem to bass pulse, sync -2 frames
  early).

## Notes (Claude's, for the owner to confirm)

- The film signature yellow in MASTER_DIRECTIVES is #FFDD33; this system sets #F4D03F for Artifacts. Until the
  owner says otherwise: #F4D03F in Artifacts, #FFDD33 in rendered films.
