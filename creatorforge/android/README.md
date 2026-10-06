# CreatorForge v1.0 RC16 (Android controller)

Your phone runs the studio. The heavy AI generation runs on your self-hosted worker
(`../worker`).

- **Generate** tab, the one-button flow: type an idea, then choose length, format
  (9:16 / 16:9 / 1:1), template, voice and pacing. Optionally set Director Mode: style, mood,
  camera and recurring characters. Tap **GENERATE VIDEO**.
  - While it runs you see each stage live: Director → PromptForge → visuals → narration →
    captions → music → edit/render → verify.
  - A storyboard appears as each scene's image arrives, and you can regenerate any single scene.
  - **Review storyboard before render** pauses after the scene images: edit any scene's narration
    or visual (only that scene is regenerated), then tap **APPROVE & RENDER**.
  - **AI video clips** turns every scene image into a generated video clip. This needs a video
    model on the worker; when the worker has none, the switch is disabled.
  - **Cancel** keeps finished assets. **Retry / Resume** continues from the failed stage.
  - When the production is ready, the verified MP4 downloads and you can **Play**, **Share** or
    **Save** it to `Movies/CreatorForge`.
- **Generate** also has **Auto Edit** (the AI picks transitions, highlighted caption words and
  dramatic pauses) and lets you pick saved characters from the library.
- **Library** tab: every finished video on the worker (Play / Share / Save) and the
  **Character Library**. Save a character's look once; every scene that names that character
  uses the same description.
- **Settings**: worker URL and worker token (stored encrypted). Plain `http://` is allowed so a
  worker on your home network works. Use `https://` anywhere else.
- **Make on this phone (no worker)**: in **Create**, paste a script and it's split into scenes.
  In **Projects**, tap **MAKE ON THIS PHONE**: each scene gets narration from Android's built-in
  voice (free, offline) and a styled title card. Then **Studio → EXPORT MP4** renders the video on
  the phone with burned-in captions.
- **Create / Projects / Studio**: the RC10 manual workflow (per-scene generation and on-device
  MP4 export). It still works offline from the worker's render pipeline.
