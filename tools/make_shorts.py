#!/usr/bin/env python3
"""Make vertical 9:16 shorts (TikTok / Reels / YouTube Shorts) for a book: a flip-through
and a "3 reasons parents love this book" video.

Usage: python3 tools/make_shorts.py benny     (or: nico)
Writes marketing/<slug>/videos/flip-through.mp4 and 3-reasons.mp4. No sound: add one in the app.
All text stays inside the safe zone (x 60-940, y 120-1520) so the app buttons don't cover it.
"""
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pymupdf as fitz
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from make_carousel import wrap  # noqa: E402
from make_marketing import NAVY, card_in_box, centered, font, paste_card  # noqa: E402
from make_video import FPS, H, W, end_card, find_cover  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BOOKS = {
    "benny": dict(dir="books/002-benny-the-bear/kdp-8.5x8.5", bg="#CDEBF8",
                  title="Benny the Bear’s Cozy Day", reason_pages=[5, 14, 27]),
    "nico": dict(dir="books/003-nico-the-reindeer", bg="#FFE1E1",
                 title="Nico the Little Reindeer’s Snowy Day", reason_pages=[11, 17, 31]),
}
REASONS = ["Kids color the story AND learn to read it",
           "One short sentence in BIG, easy letters on every page",
           "Bold, thick lines that little hands can color"]


def pages(pdf, width):
    doc = fitz.open(pdf)
    out = []
    for p in doc:
        z = width / p.rect.width
        pix = p.get_pixmap(matrix=fitz.Matrix(z, z))
        out.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    return out


class Video:
    def __init__(self, path):
        self.w = imageio_ffmpeg.write_frames(str(path), (W, H), fps=FPS, codec="libx264", quality=8,
                                             macro_block_size=8, output_params=["-pix_fmt", "yuv420p"])
        self.w.send(None)
        self.last = None

    def add(self, img, frames=1):
        arr = np.asarray(img.convert("RGB"))
        for _ in range(frames):
            self.w.send(arr.tobytes())
        self.last = arr

    def fade_to(self, img, frames=8):
        a0, a1 = self.last.astype(float), np.asarray(img.convert("RGB")).astype(float)
        for t in range(1, frames + 1):
            self.w.send((a0 + (a1 - a0) * t / frames).astype(np.uint8).tobytes())
        self.last = a1.astype(np.uint8)

    def close(self):
        self.w.close()


def flip_through(slug, cfg, out):
    book_dir = ROOT / cfg["dir"]
    pw = 860
    imgs = pages(book_dir / "out" / "interior.pdf", pw)
    ph = imgs[0].height
    base = Image.new("RGBA", (W, H), cfg["bg"])
    d = ImageDraw.Draw(base)
    centered(d, "Flip through the whole book", 130, 74, width=W, max_w=880)
    centered(d, cfg["title"], 235, 44, width=W, max_w=880)
    y = max(330, (H - ph) // 2 - 20)
    x = (W - pw) // 2
    centered(d, f"{len(imgs)} pages  •  Ages 3-6", min(y + ph + 40, 1460), 44, width=W)

    def scene(cards):
        f = base.copy()
        for im, cx in cards:
            paste_card(f, im, (cx, y), im.size, 28)
        return f

    v = Video(out)
    v.add(scene([(imgs[0], x)]), 20)
    for i in range(1, len(imgs)):
        for t in range(1, 7):  # new page slides in from the right over the old one
            e = 1 - (1 - t / 6) ** 3
            v.add(scene([(imgs[i - 1], x - round(e * 120)), (imgs[i], x + round((1 - e) * W))]))
        v.add(scene([(imgs[i], x)]), 9)
    v.fade_to(end_card(book_dir, cfg["bg"]), 10)
    v.add(end_card(book_dir, cfg["bg"]), 85)
    v.close()


def three_reasons(slug, cfg, out):
    book_dir = ROOT / cfg["dir"]
    imgs = pages(book_dir / "out" / "interior.pdf", 760)
    bg = cfg["bg"]

    title = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(title)
    for k, ln in enumerate(["3 reasons", "parents love", "this book"]):
        centered(d, ln, 150 + k * 120, 104, width=W)
    card_in_box(title, find_cover(book_dir), (210, 560), (660, 660), 36)
    centered(d, cfg["title"], 1300, 46, width=W, max_w=880)

    v = Video(out)
    v.add(title, 75)
    for n, (reason, pg) in enumerate(zip(REASONS, cfg["reason_pages"]), start=1):
        c = Image.new("RGBA", (W, H), bg)
        d = ImageDraw.Draw(c)
        d.ellipse([W // 2 - 70, 120, W // 2 + 70, 260], fill=NAVY)
        f = font(96)
        d.text((W // 2 - d.textlength(str(n), font=f) / 2, 128), str(n), font=f, fill="white")
        lines = wrap(d, reason, 66, 860)
        ty = 300
        for ln in lines:
            centered(d, ln, ty, 66, width=W)
            ty += 80
        im = imgs[pg - 1]
        card_in_box(c, im, (100, ty + 30), (880, 1500 - ty - 30), 30)
        v.fade_to(c, 8)
        v.add(c, 82)
    v.fade_to(end_card(book_dir, bg), 8)
    v.add(end_card(book_dir, bg), 85)
    v.close()


def main(slug):
    cfg = BOOKS[slug]
    out = ROOT / "marketing" / slug / "videos"
    out.mkdir(parents=True, exist_ok=True)
    flip_through(slug, cfg, out / "flip-through.mp4")
    three_reasons(slug, cfg, out / "3-reasons.mp4")
    print("✓", out / "flip-through.mp4", "and 3-reasons.mp4")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in BOOKS:
        sys.exit(__doc__)
    main(sys.argv[1])
