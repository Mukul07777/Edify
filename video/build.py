"""Everything the video page needs, made from the filmed screens and the recorded voice.

    python build.py            (after capture.mjs, measure.mjs and voice.py)

Writes:
  assets/*.jpg        the filmed screens at 1.5x, and the landing page's live demo as stabilised frames
  data.js             the timeline (every scene and caption timed from the voice clips), screen sizes, card positions
  audio/<voice>.wav   the finished sound track for each voice: the lines in place over a quiet pad

A scene lasts as long as its lines take in the slower of the two voices, so one picture fits both sound tracks.
"""
import json
import re
import wave
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SR = 48000
FPS = 30
LEAD, GAP, TAIL, XF = 0.35, 0.2, 0.3, 0.45      # seconds: before a scene's first line, between lines, after the last, crossfade
END_HOLD = 2.4                                  # the closing card stays up
VOICES = ("male", "female")
PAGE_W = 2160                                   # filmed at 2880 (2x of 1440); 1.5x is plenty and loads faster


# ------------------------------------------------------------------ pictures
def pictures() -> dict:
    out = HERE / "assets"
    out.mkdir(exist_ok=True)
    meta = json.loads((HERE / "shots" / "shots.json").read_text())
    for name, m in meta.items():
        if name in ("hero", "v_trace", "landing"):
            continue
        for suffix in ("", "_tall"):
            src = HERE / "shots" / f"{name}{suffix}.png"
            dst = out / f"{name}{suffix}.jpg"
            if not src.exists() or (dst.exists() and dst.stat().st_mtime > src.stat().st_mtime):
                continue
            im = Image.open(src).convert("RGB")
            w = PAGE_W if m["w"] == 1440 else im.width
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(dst, quality=91)
    # the landing page's live demo: each frame cut around the board, so the page's own small shifts don't show
    hero, scale = meta["hero"], 1.25
    (out / "hero").mkdir(exist_ok=True)
    kept = []
    for i in range(hero["frames"]):
        im = Image.open(HERE / "shots" / "hero" / f"{i:03d}.jpg").convert("RGB")
        col = np.asarray(im)[:, int(520 * scale), :].mean(axis=1)
        dark = np.flatnonzero(col[int(350 * scale):] < 70)
        if not len(dark):
            continue
        top = int(350 * scale) + int(dark[0]) - int(72 * scale)
        im.crop((int(120 * scale), top, int(1320 * scale), top + int(550 * scale))).save(out / "hero" / f"{len(kept):03d}.jpg", quality=90)
        kept.append(hero["times"][i] / 1000)
    meta["hero"] = {"times": kept, "w": 1200, "h": 550}
    return meta


# ------------------------------------------------------------------ timeline
def chunks(caption: str, limit: int = 74) -> list[str]:
    """A caption in pieces short enough for one or two lines on screen, split at sentence ends, then at commas."""
    parts = [p.strip() for p in re.split(r"(?<=[.?!:])\s+", caption) if p.strip()]
    out: list[str] = []
    for part in parts:
        while len(part) > limit and ", " in part:
            cut = part.rfind(", ", 0, limit)
            if cut <= 0:
                cut = part.find(", ")
            out.append(part[:cut + 1]); part = part[cut + 2:]
        if out and len(out[-1]) + len(part) + 1 <= limit and not out[-1].endswith(","):
            out[-1] += " " + part
        else:
            out.append(part)
    return out


def timeline() -> dict:
    scenes = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))["scenes"]
    durs = {v: json.loads((HERE / "audio" / v / "durations.json").read_text()) for v in VOICES}
    t, out = 0.0, []
    for n, scene in enumerate(scenes):
        start, local, lines = t, LEAD + (0.35 if n == 0 else 0), []
        for i, line in enumerate(scene["lines"]):
            key = f"{scene['id']}_{i}"
            dur = max(durs[v][key] for v in VOICES)
            pieces, total = chunks(line["cap"]), sum(len(c) for c in chunks(line["cap"]))
            caps, c0 = [], local
            for piece in pieces:
                c1 = c0 + dur * len(piece) / total
                caps.append({"t0": round(c0, 3), "t1": round(c1, 3), "text": piece})
                c0 = c1
            lines.append({"key": key, "t0": round(local, 3), "dur": round(dur, 3), "caps": caps})
            local += dur + GAP
        dur_scene = local - GAP + TAIL + (END_HOLD if n == len(scenes) - 1 else 0)
        out.append({"id": scene["id"], "start": round(start, 3), "dur": round(dur_scene, 3), "lines": lines})
        t += dur_scene
    return {"fps": FPS, "xf": XF, "total": round(t, 3), "scenes": out}


# ------------------------------------------------------------------ sound
def read(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767


def pad(seconds: float) -> np.ndarray:
    """A quiet, slow chord pad under the voice: four bars that repeat, soft enough to sit far behind speech."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]  # Am F C G
    bar = 4.8
    out = np.zeros(n, dtype=np.float32)
    for k in range(int(seconds / bar) + 1):
        a, b = int(k * bar * SR), min(n, int((k + 1) * bar * SR) + int(0.6 * SR))
        if a >= n:
            break
        tt = t[a:b] - k * bar
        env = np.clip(tt / 1.4, 0, 1) * np.clip((bar + 0.6 - tt) / 1.6, 0, 1)
        for f in chords[k % 4]:
            for mult, gain in ((1, 1.0), (2, 0.22), (0.5, 0.5)):
                out[a:b] += (gain * env * np.sin(2 * np.pi * f * mult * tt + 0.3 * np.sin(2 * np.pi * 0.21 * tt))).astype(np.float32)
    out /= np.abs(out).max() + 1e-9
    fade = np.clip(t / 1.5, 0, 1) * np.clip((seconds - t) / 2.5, 0, 1)
    return out * fade


def sound(tl: dict) -> None:
    n = int((tl["total"] + 0.2) * SR)
    bed = pad(tl["total"] + 0.2)[:n] * 0.045
    for voice in VOICES:
        mix = np.zeros(n, dtype=np.float32)
        for scene in tl["scenes"]:
            for line in scene["lines"]:
                clip = read(HERE / "audio" / voice / f"{line['key']}.wav")
                a = int((scene["start"] + line["t0"]) * SR)
                mix[a:a + len(clip)] += clip[: n - a]
        mix *= 0.9 / (np.abs(mix).max() + 1e-9)
        for name, track in ((voice, mix + bed), (f"{voice}_nomusic", mix)):
            with wave.open(str(HERE / "audio" / f"{name}.wav"), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
                w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    meta = pictures()
    tl = timeline()
    rects = json.loads((HERE / "shots" / "rects.json").read_text())
    (HERE / "data.js").write_text("window.DATA = " + json.dumps({**tl, "shots": meta, "rects": rects}, ensure_ascii=False) + ";\n", encoding="utf-8")
    sound(tl)
    print(f"total {tl['total']:.1f}s, {int(tl['total'] * FPS)} frames")
    for s in tl["scenes"]:
        print(f"  {s['start']:6.1f}  {s['id']:8} {s['dur']:5.1f}s  " + " | ".join(str(len(l['caps'])) for l in s["lines"]))
