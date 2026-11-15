"""The voice-over, one clip per narration line, in each voice.

    python voice.py                (needs: pip install edge-tts imageio-ffmpeg numpy)

Reads narration.json, writes audio/<voice>/<scene>_<n>.wav (silence trimmed) and audio/<voice>/durations.json.
The voices are Microsoft's neural Hindi voices (through the edge-tts package), which read Hinglish naturally when
Hindi words are in Devanagari. RATE is a little faster than their default, the pace of someone explaining to a friend.
"""
import asyncio
import json
import subprocess
import wave
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np

HERE = Path(__file__).resolve().parent
VOICES = {"male": "hi-IN-MadhurNeural", "female": "hi-IN-SwaraNeural"}
RATE = "+22%"
SR = 48000
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def trim(samples: np.ndarray, pad: float = 0.05) -> np.ndarray:
    """Cut the silence the voice service leaves at both ends, keeping a short breath."""
    loud = np.flatnonzero(np.abs(samples) > 0.012)
    if not len(loud):
        return samples
    a, b = max(0, loud[0] - int(pad * SR)), min(len(samples), loud[-1] + int((pad + 0.04) * SR))
    return samples[a:b]


async def say(text: str, voice: str, out: Path) -> float:
    mp3 = out.with_suffix(".mp3")
    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, voice, rate=RATE).save(str(mp3))
            break
        except Exception as exc:  # the service drops a connection now and then
            if attempt == 3:
                raise
            print("  retry:", exc)
            await asyncio.sleep(2)
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(mp3), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    samples = trim(np.frombuffer(raw, dtype=np.float32))
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
    mp3.unlink()
    return len(samples) / SR


async def main() -> None:
    scenes = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))["scenes"]
    for name, voice in VOICES.items():
        folder = HERE / "audio" / name
        folder.mkdir(parents=True, exist_ok=True)
        durations, total = {}, 0.0
        for scene in scenes:
            for i, line in enumerate(scene["lines"]):
                key = f"{scene['id']}_{i}"
                durations[key] = round(await say(line["say"], voice, folder / f"{key}.wav"), 3)
                total += durations[key]
        (folder / "durations.json").write_text(json.dumps(durations, indent=1))
        print(f"{name} ({voice}): {len(durations)} lines, {total:.1f}s of speech")


asyncio.run(main())
