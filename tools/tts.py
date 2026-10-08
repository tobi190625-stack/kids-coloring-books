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


def warm_path(text, exaggeration=0.6, cfg=0.35, seed=7):
    import hashlib
    from pathlib import Path
    cache = Path(__file__).resolve().parent.parent / "campaigns" / "fresh" / ".voicecache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache / (hashlib.md5(f"{text}|{exaggeration}|{cfg}|{seed}".encode()).hexdigest() + ".wav")


def warm_batch(texts, exaggeration=0.6, cfg=0.35, seed=7):
    """Make every missing line in one run of the local Chatterbox (tools/cb_batch.py in its own Python)."""
    import json
    import os
    import tempfile
    from pathlib import Path
    jobs = {str(warm_path(t, exaggeration, cfg, seed)): {"text": t, "exaggeration": exaggeration, "cfg": cfg, "seed": seed}
            for t in dict.fromkeys(texts) if not warm_path(t, exaggeration, cfg, seed).exists()}
    if not jobs:
        return
    jf = Path(tempfile.mkdtemp()) / "jobs.json"
    jf.write_text(json.dumps(jobs), encoding="utf-8")
    py = os.environ.get("CB_PYTHON", str(Path.home() / "cbvenv" / "Scripts" / "python.exe"))
    subprocess.run([py, str(Path(__file__).parent / "cb_batch.py"), str(jf)], check=True)


def warm(text, exaggeration=0.6, cfg=0.35, seed=7):
    """Emotional voice: Chatterbox (open source, MIT) through its free Hugging Face demo, built-in warm female
    voice. Results are cached in campaigns/fresh/.voicecache so re-renders don't use the free GPU quota again.
    Chatterbox gives no word times, so captions get times spread over the spoken part by word length."""
    import hashlib
    import shutil
    from pathlib import Path
    import soundfile as sf
    cache = Path(__file__).resolve().parent.parent / "campaigns" / "fresh" / ".voicecache"
    cache.mkdir(parents=True, exist_ok=True)
    f = warm_path(text, exaggeration, cfg, seed)
    if not f.exists():
        warm_batch([text], exaggeration, cfg, seed)
    a, sr = sf.read(f, dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    if sr != SR:
        a = np.interp(np.arange(int(len(a) * SR / sr)) / SR, np.arange(len(a)) / sr, a).astype(np.float32)
    loud = np.nonzero(np.abs(a) > 0.02)[0]
    s0, s1 = (loud[0] / SR, loud[-1] / SR) if len(loud) else (0, len(a) / SR)
    toks = text.split()
    wts = [len(t) + 2 + (4 if t[-1] in ".!?," else 0) for t in toks]  # a little pause after punctuation
    t, words = s0, []
    for tok, w in zip(toks, wts):
        d = (s1 - s0) * w / sum(wts)
        words.append((tok.strip(".,!?\"'"), t, t + d * 0.85))
        t += d
    return a, words


def say(text, voice="ava", rate="+0%", pitch="+0Hz", tries=3):
    if voice == "warm":
        return warm(text)
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
