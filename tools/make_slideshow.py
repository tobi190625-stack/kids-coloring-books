#!/usr/bin/env python3
"""Vertical 9:16 slideshow short with a voiceover (Kokoro TTS): cover, colored story pages read
aloud, a "what's inside" card and the end card.

Usage: python3 tools/make_slideshow.py benny [voice]     (voice default af_heart)
Needs: kokoro-onnx + model files in /root/kokoro (see marketing/README), colored page maps in
marketing/paint/. Writes marketing/<slug>/videos/slideshow-voice.mp4
"""
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import paint  # noqa: E402
from make_carousel import wrap  # noqa: E402
from make_marketing import NAVY, card_in_box, centered, font, pill  # noqa: E402
from make_video import FPS, H, W, end_card, find_cover  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BOOKS = {
    "benny": dict(dir="books/002-benny-the-bear/kdp-8.5x8.5", bg=("#FFF6E0", "#FFE3B8"),
                  title="Benny the Bear’s Cozy Day",
                  intro=("Meet Benny the bear!", "Meet Benny the bear! A cozy story your kids color, and read."),
                  pages=[4, 20, 22, 29],
                  inside=("Big pictures. Big letters.", "Every page has one big picture to color, and one short "
                          "sentence in big, easy letters. Perfect for ages three to six."),
                  outro="Find Benny the Bear's Cozy Day on Amazon. Link in bio!"),
    "benny2": dict(dir="books/002-benny-the-bear/kdp-8.5x8.5", bg=("#FFF6E0", "#FFE3B8"), slug="benny",
                   out="slideshow2", music="benny-soft",
                   title="Benny the Bear\u2019s Cozy Day",
                   intro=("A day with Benny the bear", "Want to spend a cozy day with Benny the bear? Come on, "
                          "let's take a peek inside!"),
                   pages=[16, 21, 23],
                   reads={16: "Oh, look! A butterfly lands on Benny's nose. Hello!",
                          21: "Whee! Benny rolls down the grassy hill.",
                          23: "Found you! Bella hides behind a mushroom."},
                   inside=("Kids color it. Then read it.", "Your little one colors every page, and reads one short, "
                           "easy sentence. Perfect for ages three to six."),
                   outro="Benny the Bear's Cozy Day is on Amazon. Link in bio!"),
    "nico": dict(dir="books/003-nico-the-reindeer", bg=("#EEF7FF", "#D3E9FB"),
                 title="Nico the Little Reindeer\u2019s Snowy Day",
                 intro=("Meet Nico the reindeer!", "Meet Nico the little reindeer! A cozy Christmas story your "
                        "kids color, and read."),
                 pages=[8, 13, 17, 31],
                 inside=("The stocking stuffer that isn't candy", "Every page has one big picture to color, and one "
                         "short sentence in big, easy letters. The perfect stocking stuffer for ages three to six."),
                 outro="Find Nico the Little Reindeer's Snowy Day on Amazon. Link in bio!"),
}


def bg_img(c1, c2):
    a, b = paint_hex(c1), paint_hex(c2)
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return im


def paint_hex(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def main(slug, voice="af_heart"):
    cfg = BOOKS[slug]
    book_dir = ROOT / cfg["dir"]
    import pymupdf as fitz
    pdf = fitz.open(book_dir / "out" / "interior.pdf")

    import voice as vmod

    def say(text):
        return vmod.speak(text, voice, seed=len(text)), vmod.SR

    slides = []  # (image, audio)
    base = bg_img(*cfg["bg"])
    # 1: cover
    im = base.copy(); d = ImageDraw.Draw(im)
    centered(d, cfg["intro"][0], 150, 84, width=W, max_w=960)
    centered(d, "A story kids color AND read", 265, 50, width=W, max_w=960)
    card_in_box(im, find_cover(book_dir), (110, 380), (860, 900), 40)
    slides.append((im, say(cfg["intro"][1])))
    # story pages, colored, read aloud
    for n in cfg["pages"]:
        img, labels, _, _ = paint.regions(book_dir, n)
        col = paint.paint_full(img, labels, paint.load_map(book_dir, n))
        text = cfg.get("reads", {}).get(n) or " ".join(pdf[n - 1].get_text().split())
        im = base.copy(); d = ImageDraw.Draw(im)
        centered(d, cfg["title"], 170, 48, width=W, max_w=960)
        card_in_box(im, Image.fromarray(col), (60, 290), (960, 960), 34)
        slides.append((im, say(text)))
    # what's inside
    im = base.copy(); d = ImageDraw.Draw(im)
    centered(d, cfg["inside"][0], 160, 76, width=W, max_w=960)
    ty = 330
    for line in ["One big picture on every page", "One short sentence in BIG letters",
                 "Kids color the story AND read it", "Perfect for ages 3-6"]:
        d.ellipse([110, ty, 190, ty + 80], fill=NAVY)
        d.line([(130, ty + 42), (148, ty + 60), (174, ty + 22)], fill="white", width=10)
        for k2, ln in enumerate(wrap(d, line, 58, 760)):
            d.text((220, ty + 8 + k2 * 70), ln, font=font(58), fill=NAVY)
        ty += 190
    slides.append((im, say(cfg["inside"][1])))
    # end
    slides.append((end_card(book_dir, cfg["bg"][0], yt=True), say(cfg["outro"])))

    sr = slides[0][1][1]
    name = cfg.get("out", "slideshow")
    out = ROOT / "marketing" / cfg.get("slug", slug) / "videos" / f"{name}-voice.mp4"
    tmp_v = out.with_suffix(".tmp.mp4")
    w = imageio_ffmpeg.write_frames(str(tmp_v), (W, H), fps=FPS, codec="libx264", quality=8,
                                    macro_block_size=8, output_params=["-pix_fmt", "yuv420p"])
    w.send(None)
    audio = []
    prev = None
    for idx, (im, (a, _)) in enumerate(slides):
        dur = len(a) / sr + 0.7
        n = int(dur * FPS)
        arr = np.asarray(im.convert("RGB")).astype(float)
        for f in range(n):
            s = 1.0 + 0.04 * f / n  # gentle zoom
            z = Image.fromarray(arr.astype(np.uint8)).resize((round(W * s), round(H * s)), Image.BILINEAR)
            x0, y0 = (z.width - W) // 2, (z.height - H) // 2
            fr = np.asarray(z.crop((x0, y0, x0 + W, y0 + H))).astype(float)
            if prev is not None and f < 8:
                fr = prev * (1 - (f + 1) / 8) + fr * ((f + 1) / 8)
            w.send(fr.astype(np.uint8).tobytes())
        prev = fr
        pad = np.zeros(int(n / FPS * sr) - len(a), np.float32)
        lead = np.zeros(int(0.25 * sr), np.float32)
        seg = np.concatenate([lead, a, pad])[: int(n / FPS * sr)]
        audio.append(seg)
    w.close()
    wav = out.with_suffix(".wav")
    sf.write(wav.with_suffix(".raw.wav"), np.concatenate(audio), sr)
    vmod.warm(wav.with_suffix(".raw.wav"), wav)
    wav.with_suffix(".raw.wav").unlink()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", str(tmp_v), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "volume=1.5,alimiter=limit=0.95",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)
    tmp_v.unlink(); wav.unlink()
    music = ROOT / "marketing" / "music" / f"{cfg.get('music', slug + '-soft')}.wav"
    if music.exists():  # soft background music under the voice
        final = out.with_name(f"{name}-voice-music.mp4")
        subprocess.run([ff, "-loglevel", "error", "-y", "-i", str(out), "-i", str(music), "-filter_complex",
                        "[1:a]volume=0.2,afade=t=in:d=0.4[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", str(final)], check=True)
        print("\u2713", final)
    print("✓", out)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in BOOKS:
        sys.exit(__doc__)
    main(*sys.argv[1:])
