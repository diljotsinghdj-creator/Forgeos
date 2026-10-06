# CreatorForge v1.0 RC12 (Android controller)

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
- **Settings**: worker URL and worker token (stored encrypted). Plain `http://` is allowed so a
  worker on your home network works. Use `https://` anywhere else.
- **Create / Projects / Studio**: the RC10 manual workflow (per-scene generation and on-device
  MP4 export). It still works offline from the worker's render pipeline.
