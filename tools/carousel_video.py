#!/usr/bin/env python3
"""Turn a carousel (6 slides, 4:5) into a 9:16 Reel/Short: slides one after another with a soft zoom,
crossfades and background music.

Usage: python3 tools/carousel_video.py marketing/nico/carousel-gift marketing/music/nico-soft.wav OUT.mp4 [bg]
"""
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

W, H, FPS = 1080, 1920, 30


def main(folder, music, out, bg="#FFF6E0", secs=2.8):
    slides = sorted(Path(folder).glob("slide*.png"))
    base = Image.new("RGB", (W, H), bg)
    tmp = Path(out).with_suffix(".tmp.mp4")
    w = imageio_ffmpeg.write_frames(str(tmp), (W, H), fps=FPS, codec="libx264", quality=8,
                                    macro_block_size=8, output_params=["-pix_fmt", "yuv420p"])
    w.send(None)
    prev = None
    for s in slides:
        sl = Image.open(s).convert("RGB")
        n = int(secs * FPS)
        for f in range(n):
            z = 1.0 + 0.035 * f / n
            im = sl.resize((round(1000 * z), round(1250 * z)), Image.BILINEAR)
            fr = base.copy()
            fr.paste(im, ((W - im.width) // 2, 230 - (im.height - 1250) // 2))
            a = np.asarray(fr).astype(float)
            if prev is not None and f < 8:
                a = prev * (1 - (f + 1) / 8) + a * ((f + 1) / 8)
            w.send(a.astype(np.uint8).tobytes())
        prev = a
    w.close()
    dur = len(slides) * secs
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", str(tmp), "-i", str(music), "-filter_complex",
                    f"[1:a]atrim=0:{dur:.2f},volume=0.6,afade=t=in:d=0.4,afade=t=out:st={dur - 1.5:.2f}:d=1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    tmp.unlink()
    print("✓", out)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
