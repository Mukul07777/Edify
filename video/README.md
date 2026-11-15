# The demo video

A Hinglish walkthrough of Edify under three minutes, made from the real app: every screen in it is filmed from a
running Edify with the demo accounts.

To rebuild it (the app on `http://127.0.0.1:8011`, `seed_demo.py` and `warm_chains.py` already run):

```
pip install edge-tts imageio-ffmpeg numpy pillow
cd backend && python ../video/setup_account.py     # a throwaway demo account for filming the trace
cd ../video
node capture.mjs        # films the screens into shots/
node measure.mjs        # where the cards the video points at sit
python voice.py         # the voice-over, a male and a female voice (narration.json)
python build.py         # pictures, timeline and sound tracks
node render.mjs         # every frame, then out/edify-demo-<voice>-voice.mp4   (set FFMPEG to an ffmpeg binary)
```

`video.html?t=42` shows one moment in a browser; `?play=1` plays it without sound. To change what is said, edit
`narration.json` and run `voice.py`, `build.py` and `render.mjs` again: every scene is timed from the recorded lines.
