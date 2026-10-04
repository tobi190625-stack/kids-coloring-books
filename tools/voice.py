#!/usr/bin/env python3
"""More human-sounding voiceover with Kokoro TTS: talks sentence by sentence with natural pauses,
slight speed variation and a little room warmth. Model files live in /root/kokoro."""
import random
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf

_K = None
SR = 24000


def kokoro():
    global _K
    if _K is None:
        from kokoro_onnx import Kokoro
        _K = Kokoro("/root/kokoro/kokoro-v1.0.int8.onnx", "/root/kokoro/voices-v1.0.bin")
    return _K


def speak(text, voice="af_heart", seed=1):
    """One line of speech, split into sentences with short natural pauses."""
    rng = random.Random(seed)
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()]
    out = []
    for i, p in enumerate(parts):
        a, _ = kokoro().create(p, voice=voice, speed=rng.uniform(0.93, 0.99), lang="en-us")
        a = a.astype(np.float32)
        # trim silence at the ends so the pauses we add are the real ones
        nz = np.nonzero(np.abs(a) > 0.01)[0]
        if len(nz):
            a = a[max(0, nz[0] - 600): nz[-1] + 1200]
        out.append(a)
        if i < len(parts) - 1:
            out.append(np.zeros(int(SR * rng.uniform(0.28, 0.45)), np.float32))
    return np.concatenate(out)


def place(lines, total_seconds, voice="af_heart"):
    """lines: [(start_seconds, text)]; each starts at its time or right after the previous one."""
    track = np.zeros(int(total_seconds * SR), np.float32)
    pos = 0
    for k, (start, text) in enumerate(lines):
        a = speak(text, voice, seed=k + 3)
        i = max(int(start * SR), pos)
        track[i:i + len(a)] += a[: max(0, len(track) - i)]
        pos = i + len(a) + int(0.25 * SR)
    return track


def warm(in_wav, out_wav):
    """Gentle EQ + tiny room so the voice sounds recorded, not synthetic."""
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", str(in_wav), "-af",
                    "highpass=f=80,equalizer=f=200:t=q:w=1:g=2,equalizer=f=6500:t=q:w=1:g=-2,"
                    "aecho=0.8:0.6:28|47:0.12|0.07,acompressor=threshold=0.15:ratio=2.5:attack=8:release=120,"
                    "aresample=44100", str(out_wav)], check=True)


def mix_into_video(video, voice_track, music_wav, out, music_vol=0.2):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    info = subprocess.run([ff, "-i", str(video)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info).groups()
    dur = int(h) * 3600 + int(m) * 60 + float(s)
    tmp = Path(out).with_suffix(".vo.wav")
    raw = Path(out).with_suffix(".raw.wav")
    sf.write(raw, voice_track, SR)
    warm(raw, tmp)
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", str(video), "-i", str(tmp), "-i", str(music_wav),
                    "-filter_complex",
                    f"[1:a]volume=1.5[v];[2:a]atrim=0:{dur:.2f},volume={music_vol},afade=t=in:d=0.4,afade=t=out:st={dur-1.6:.2f}:d=1.6[m];[v][m]amix=inputs=2:duration=longest:normalize=0,"
                    "alimiter=limit=0.95[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "22", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                    str(out)], check=True)
    tmp.unlink(); raw.unlink()
