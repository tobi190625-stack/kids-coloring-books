#!/usr/bin/env python3
"""Natural voiceover with Microsoft's neural voices (edge-tts, free, needs internet) + exact word times.

    from tts import say
    audio, words = say("Can you find something red?", voice="ava")   # 24 kHz float32, [(word, start, end)]

Voices: ava (warm, expressive, default), emma (cheerful), andrew (warm male), brian (casual male).
Command line test: python tools/tts.py ava "Hello there!"  -> writes hello.wav next to you.
"""
import asyncio
import subprocess
import sys

import imageio_ffmpeg
import numpy as np

SR = 24000
VOICES = {"ava": "en-US-AvaMultilingualNeural", "emma": "en-US-EmmaMultilingualNeural",
          "andrew": "en-US-AndrewMultilingualNeural", "brian": "en-US-BrianMultilingualNeural"}


async def _stream(text, voice, rate, pitch):
    import edge_tts
    com = edge_tts.Communicate(text, VOICES.get(voice, voice), rate=rate, pitch=pitch, boundary="WordBoundary")
    mp3, words = bytearray(), []
    async for chunk in com.stream():
        if chunk["type"] == "audio":
            mp3 += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            s = chunk["offset"] / 1e7
            words.append((chunk["text"], s, s + chunk["duration"] / 1e7))
    return bytes(mp3), words


def say(text, voice="ava", rate="+0%", pitch="+0Hz", tries=3):
    for k in range(tries):
        try:
            mp3, words = asyncio.run(_stream(text, voice, rate, pitch))
            break
        except Exception:
            if k == tries - 1:
                raise
    pcm = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", "pipe:0", "-f", "f32le",
                          "-ac", "1", "-ar", str(SR), "pipe:1"], input=mp3, capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32).copy(), words


if __name__ == "__main__":
    import soundfile as sf
    a, w = say(sys.argv[2], sys.argv[1])
    sf.write("hello.wav", a, SR)
    print(len(a) / SR, "s", w)
