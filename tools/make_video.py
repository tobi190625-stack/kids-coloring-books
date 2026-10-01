#!/usr/bin/env python3
"""Make a vertical 9:16 "watch it get colored" video (TikTok / Reels / Shorts) from a book page.

Usage: python3 tools/make_video.py books/004-dex-the-dinosaur 22 "Watch Dex come to life"
The page is rendered from out/interior.pdf, its white areas get filled with crayon colors one by
one, then the cover appears with the title. No sound: add a sound in the app.
Writes marketing/<slug>/videos/color-page-<N>.mp4
"""
import json
import random
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pymupdf as fitz
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
from make_marketing import NAVY, card_in_box, centered, font, pill  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
PALETTE = ["#FF8A80", "#FFB74D", "#FFE066", "#9BE15D", "#5ED3B8", "#6EC6FF", "#8C9EFF",
           "#C792EA", "#FF9CCF", "#A1887F", "#FFD180", "#81D4FA", "#AED581", "#F48FB1"]


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def main(book_dir, page_no, hook):
    book_dir = Path(book_dir).resolve()
    book = json.loads((book_dir / "book.json").read_text())
    slug = book.get("marketing", {}).get("slug") or book_dir.name.split("-")[1]
    if book_dir.name.startswith("kdp-"):
        slug = book_dir.parent.name.split("-")[1]
    title = book["title"]
    out_dir = ROOT / "marketing" / slug / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    page = fitz.open(book_dir / "out" / "interior.pdf")[page_no - 1]
    bubbles = [d["rect"] for d in page.get_drawings()
               if d.get("fill") == (1.0, 1.0, 1.0) and d.get("color") == (0.0, 0.0, 0.0)]
    pw = 1000
    zoom = pw / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]
    ph = pix.height
    white = img.mean(axis=2) > 200
    # close small gaps in the lines so a character is not one area with the sky
    core = ndimage.binary_erosion(white, iterations=3)
    labels, n = ndimage.label(core)
    _, (iy, ix) = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    labels = np.where(white, labels[iy, ix], 0)
    sizes = ndimage.sum(np.ones_like(labels), labels, index=np.arange(n + 1))
    border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])))
    keep = np.zeros(n + 1, bool)
    for i in range(1, n + 1):
        if sizes[i] >= 150 and i not in border:
            keep[i] = True
    for r in bubbles:  # leave the text bubbles white
        x0, y0, x1, y1 = (int(v * zoom) for v in (r.x0, r.y0, r.x1, r.y1))
        for i in np.unique(labels[max(0, y0):y1, max(0, x0):x1]):
            keep[i] = False
    regions = [i for i in range(1, n + 1) if keep[i]]
    rng = random.Random(page_no)
    color = {i: hexrgb(rng.choice(PALETTE)) for i in regions}
    cy = ndimage.center_of_mass(np.ones_like(labels), labels, regions)
    regions = [r for _, r in sorted(zip([c[0] + rng.uniform(-120, 120) for c in cy], regions))]

    # frame layout: hook on top, page card in the middle, title below
    base = Image.new("RGB", (W, H), "#FFF6DA")
    d = ImageDraw.Draw(base)
    centered(d, hook, 120, 76, width=W, max_w=980)
    centered(d, "Color & Read Story Book  •  Ages 3-6", 230, 40, width=W)
    px, py = (W - pw) // 2, max(330, (H - ph) // 2 - 40)
    d.rounded_rectangle([px - 12, py - 12, px + pw + 12, py + ph + 12], 30, fill="white")
    centered(d, title, py + ph + 45, 46, width=W, max_w=1000)
    canvas = img.copy()

    writer = imageio_ffmpeg.write_frames(str(out_dir / f"color-page-{page_no}.mp4"), (W, H), fps=FPS,
                                         codec="libx264", quality=8, macro_block_size=8,
                                         output_params=["-pix_fmt", "yuv420p"])
    writer.send(None)

    def frame(page_arr):
        f = base.copy()
        f.paste(Image.fromarray(page_arr), (px, py))
        writer.send(np.asarray(f).tobytes())

    for _ in range(int(1.5 * FPS)):  # show the empty page first
        frame(canvas)
    steps = int(9 * FPS)
    done = 0
    for s in range(steps):
        upto = round(len(regions) * (s + 1) / steps)
        for i in regions[done:upto]:
            canvas[labels == i] = color[i]
        done = upto
        frame(canvas)
    for _ in range(int(1.5 * FPS)):
        frame(canvas)

    # end card: cover + call to action
    covers = [book_dir / "out" / "front-cover-no-watermark.png", book_dir / "cover" / "front.png",
              book_dir.parent / "out" / "front-cover-no-watermark.png", book_dir.parent / "cover" / "front.png"]
    cover = Image.open(next(c for c in covers if c.exists())).convert("RGB")
    end = Image.new("RGBA", (W, H), "#FFF6DA")
    e = ImageDraw.Draw(end)
    centered(e, "Color it. Read it.", 150, 90, width=W)
    card_in_box(end, cover, (110, 330), (860, 1150), 40)
    pill(e, "Find it on Amazon", 1560, width=W, size=64)
    centered(e, "Link in bio", 1730, 50, width=W)
    end = np.asarray(end.convert("RGB"))
    lastf = base.copy(); lastf.paste(Image.fromarray(canvas), (px, py)); last = np.asarray(lastf).astype(float)
    for t in range(12):  # quick crossfade
        a = (t + 1) / 12
        writer.send((last * (1 - a) + end * a).astype(np.uint8).tobytes())
    for _ in range(int(3 * FPS)):
        writer.send(end.tobytes())
    writer.close()
    print("✓", out_dir / f"color-page-{page_no}.mp4", f"({len(regions)} areas colored)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
