#!/usr/bin/env python3
"""Generate a soft, original music-box background track (copyright-free, made from scratch).

Usage: python3 tools/make_music.py OUT.wav SECONDS [bpm]
"""
import sys

import numpy as np
import soundfile as sf

SR = 44100


def note_freq(n):  # MIDI note -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


def bell(freq, dur, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 3.2) * (1 - np.exp(-t * 400))
    tone = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t * 4)
            + 0.12 * np.sin(2 * np.pi * 3.01 * freq * t) * np.exp(-t * 7))
    return vel * env * tone


def pad(freqs, dur):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.6)
    s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 1.003 * t) for f in freqs)
    return 0.05 * env * s / len(freqs)


def main(out, seconds, bpm=84):
    seconds = float(seconds)
    beat = 60 / bpm
    # C - G - Am - F, gentle broken chords + a simple original melody on top
    chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
    melody = [[72, None, 74, 76, 74, None, 72, None], [71, None, 72, 74, 71, None, 67, None],
              [69, None, 71, 72, 76, None, 74, None], [72, None, 69, 72, 71, None, None, None]]
    total = np.zeros(int((seconds + 4) * SR))
    t0 = 0.0
    bar = 0
    while t0 < seconds:
        ch = chords[bar % 4]
        mel = melody[bar % 4] if (bar // 4) % 2 == 0 else [m - 12 if m else None for m in melody[(bar + 2) % 4]][::-1]
        seg = pad([note_freq(n - 12) for n in ch], 4 * beat + 0.6)
        i = int(t0 * SR); total[i:i + len(seg)] += seg[: len(total) - i]
        for k in range(8):  # eighth-note arpeggio
            n = ch[[0, 1, 2, 1, 0, 1, 2, 1][k]]
            s = bell(note_freq(n), 2.0, 0.18)
            j = int((t0 + k * beat / 2) * SR); total[j:j + len(s)] += s[: len(total) - j]
            if mel[k]:
                s = bell(note_freq(mel[k]), 2.5, 0.32)
                total[j:j + len(s)] += s[: len(total) - j]
        t0 += 4 * beat
        bar += 1
    total = total[: int(seconds * SR)]
    fade = int(1.5 * SR)
    total[-fade:] *= np.linspace(1, 0, fade)
    total[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    # soft room reverb
    rev = np.zeros_like(total)
    for d, g in [(0.031, 0.35), (0.053, 0.28), (0.079, 0.22), (0.113, 0.16), (0.167, 0.1)]:
        k = int(d * SR); rev[k:] += g * total[:-k]
    total = total + rev
    total = 0.7 * total / np.max(np.abs(total))
    sf.write(out, np.stack([total, total], 1), SR)
    print("✓", out)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], *(float(x) for x in sys.argv[3:]))
