#!/usr/bin/env python3
"""Original, copyright-free upbeat background track: warm marimba melody, soft bass, light shaker.

Usage: python tools/make_music2.py marketing/music/marimba-sunny.wav 40 [bpm]
"""
import sys

import numpy as np
import soundfile as sf

SR = 44100


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def marimba(f, dur, vel):
    t = np.arange(int(dur * SR)) / SR
    body = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 30)
    return vel * body * np.exp(-t * 5.5) * (1 - np.exp(-t * 800))


def bass(f, dur, vel):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return vel * s * np.exp(-t * 2.5) * (1 - np.exp(-t * 200))


def shaker(dur, vel, rng):
    n = rng.normal(0, 1, int(dur * SR))
    n = n - np.convolve(n, np.ones(8) / 8, "same")  # keep the hiss
    t = np.arange(len(n)) / SR
    return vel * n * np.exp(-t * 45)


def main(out, seconds, bpm=112):
    seconds, beat = float(seconds), 60 / float(bpm)
    rng = np.random.default_rng(3)
    total = np.zeros(int((seconds + 3) * SR))

    def add(s, at):
        i = int(at * SR)
        total[i:i + len(s)] += s[:len(total) - i]
    # F - C - Dm - Bb (I V vi IV in F), a bouncy original melody in eighth notes
    chords = [[53, 57, 60], [48, 52, 55], [50, 53, 57], [46, 50, 53]]
    mel = [[72, 74, 77, 74, 72, None, 69, None], [67, 69, 72, None, 76, 74, 72, None],
           [69, 72, 74, 77, 76, None, 74, 72], [70, None, 74, 72, 69, None, 65, None]]
    bar, t0 = 0, 0.0
    while t0 < seconds:
        ch, m = chords[bar % 4], mel[bar % 4]
        add(bass(hz(ch[0] - 12), beat * 1.9, 0.30), t0)
        add(bass(hz(ch[0] - 12), beat * 1.9, 0.24), t0 + 2 * beat)
        for k in range(8):
            at = t0 + k * beat / 2
            add(marimba(hz(ch[k % 3] + 12), 0.6, 0.10), at)          # soft broken chord
            if m[k]:
                add(marimba(hz(m[k]), 0.9, 0.24 if k % 2 == 0 else 0.18), at)
            add(shaker(0.12, 0.05 if k % 2 else 0.03, rng), at)
        t0 += 4 * beat
        bar += 1
    total = total[: int(seconds * SR)]
    fade = int(1.5 * SR)
    total[-fade:] *= np.linspace(1, 0, fade)
    total[: int(0.2 * SR)] *= np.linspace(0, 1, int(0.2 * SR))
    rev = np.zeros_like(total)
    for d, g in [(0.029, 0.25), (0.047, 0.18), (0.071, 0.12), (0.11, 0.08)]:
        k = int(d * SR)
        rev[k:] += g * total[:-k]
    total = total + rev
    total = 0.7 * total / np.max(np.abs(total))
    sf.write(out, np.stack([total, total], 1), SR)
    print("✓", out)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
