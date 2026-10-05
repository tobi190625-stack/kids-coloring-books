#!/usr/bin/env python3
"""Put a timed voiceover + soft music on a finished (silent) video.

Usage: python3 tools/add_voice.py <video.mp4> <music name|path> <out.mp4> "0:First line." "7.5:Second line." ...
Each line starts at its time in seconds (or right after the previous line if that one is still talking).
Music name = a file in marketing/music/ without .wav (e.g. nico-soft).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import voice  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main(video, music, out, *lines):
    m = Path(music) if music.endswith(".wav") else ROOT / "marketing" / "music" / f"{music}.wav"
    parsed = [(float(t), txt) for t, txt in (ln.split(":", 1) for ln in lines)]
    import re
    import subprocess
    import imageio_ffmpeg
    info = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(video)], capture_output=True, text=True).stderr
    h, mi, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info).groups()
    dur = int(h) * 3600 + int(mi) * 60 + float(s)
    track = voice.place(parsed, dur)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    voice.mix_into_video(video, track, m, out)
    print("✓", out)


if __name__ == "__main__":
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
