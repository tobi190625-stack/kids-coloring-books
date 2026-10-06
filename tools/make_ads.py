#!/usr/bin/env python3
"""Ad formats from the Oct 2026 ad research (marketing/ad-research/SUMMARY.md).

Usage:
  python tools/make_ads.py guess  <book_dir> <page> "<hook>" <out.mp4> [--yt]
      "Guess the colors" timelapse: the page colors itself (paint map), ends on the cover.
  python tools/make_ads.py three  <book_dir> <page> "<hook line 1>|<hook line 2>" <out.mp4> [--yt]
      "Same page, 3 ways": the page colors itself in 3 color styles at once, "Comment 1, 2 or 3!".
  python tools/make_ads.py readit <book_dir> <page1,page2,...> "<hook>" <out.mp4> [--yt]
      "Can your 4-year-old read this page?": read-along with a parent hook.
  python tools/make_ads.py pin    <book_dir> <page> "<line 1>|<line 2>" <out.png>
      Pinterest 2:3 pin: blank page vs colored page + "Color it. Then read it."
All videos are 1080x1920, 30 fps, no sound (add a Commercial Music Library sound in the app);
text stays inside the safe zone. Pages need a paint map (marketing/paint/<slug>-p<N>.json).
"""
import colorsys
import shutil
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import paint  # noqa: E402
from make_marketing import NAVY, centered, font, paste_card, pill  # noqa: E402
from make_video import FPS, H, W, end_card, find_cover, painted_video  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
THEME = {"benny": ("#FFF6E0", "#FFE3B8"), "nico": ("#EEF7FF", "#D3E9FB")}
RAINBOW = ["#E5484D", "#F59A3D", "#FFD95A", "#6CBF4B", "#5AA7E6", "#B48AD8", "#F7AFC3", "#4FBFB0"]


def book_title(book_dir):
    import json
    for d in (book_dir, book_dir.parent):
        f = d / "book.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))["title"]


def background(slug):
    top, bot = (tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in THEME.get(slug, THEME["benny"]))
    bg = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return bg, "#{:02X}{:02X}{:02X}".format(*top)


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

    def fade_to(self, img, frames=12):
        a0, a1 = self.last.astype(float), np.asarray(img.convert("RGB")).astype(float)
        for t in range(1, frames + 1):
            self.w.send((a0 + (a1 - a0) * t / frames).astype(np.uint8).tobytes())
        self.last = a1.astype(np.uint8)

    def close(self):
        self.w.close()


def guess(book_dir, page, hook, out, yt=False):
    """Reuse the realistic painted timelapse with our own hook, saved under the given name."""
    tmp = Path(tempfile.mkdtemp())
    painted_video(book_dir, page, hook, yt, book_title(book_dir), tmp)
    shutil.move(str(next(tmp.glob("*.mp4"))), out)
    print("✓", out)


def recolor(groups, style):
    out = []
    for k, (rgb, ids) in enumerate(groups):
        if style == "rainbow":
            h = RAINBOW[k % len(RAINBOW)]
            out.append((tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)), ids))
        else:  # "magic": same picture, every color moved around the color wheel
            hh, ll, ss = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
            r, g, b = colorsys.hls_to_rgb((hh + 0.45) % 1, ll, min(1, ss * 1.1))
            out.append(((round(r * 255), round(g * 255), round(b * 255)), ids))
    return out


def three(book_dir, page, hook, out, yt=False):
    slug = paint.slug_of(book_dir)
    groups = paint.load_map(book_dir, page)
    img, labels, _, _ = paint.regions(book_dir, page, paint.PW)
    styles = [groups, recolor(groups, "magic"), recolor(groups, "rainbow")]
    S = 470
    spots = [(55, 400), (555, 400), (305, 905)]
    base, endbg = background(slug)
    d = ImageDraw.Draw(base)
    l1, l2 = (hook.split("|") + [""])[:2]
    centered(d, l1, 130, 76, width=W, max_w=960)
    if l2:
        centered(d, l2, 228, 60, width=W, max_w=960)
    centered(d, book_title(book_dir), 318, 38, width=W, max_w=940)

    def frame(arrs, prompt=False):
        f = base.copy()
        for k, (arr, (x, y)) in enumerate(zip(arrs, spots)):
            paste_card(f, Image.fromarray(arr).resize((S, S), Image.LANCZOS), (x, y), (S, S), 26)
            fd = ImageDraw.Draw(f)
            fd.ellipse([x + 12, y + 12, x + 102, y + 102], fill=NAVY)
            nf = font(64)
            fd.text((x + 57 - fd.textlength(str(k + 1), font=nf) / 2, y + 18), str(k + 1), font=nf, fill="white")
        if prompt:
            pill(ImageDraw.Draw(f), "Comment 1, 2 or 3!", 1420, width=W, size=62)
        return f

    v = Video(out)
    v.add(frame([img] * 3), int(1.0 * FPS))
    gens = [paint.animate(img, labels, g, 8.0, FPS) for g in styles]
    last = None
    for trio in zip(*gens):
        last = [t[0].copy() for t in trio]
        v.add(frame(last))
    final = [paint.paint_full(img, labels, g) for g in styles]
    v.add(frame(final), 10)
    v.add(frame(final, prompt=True), int(2.6 * FPS))
    end = end_card(book_dir, endbg, yt=yt)
    v.fade_to(end, 12)
    v.add(end, int(2.6 * FPS))
    v.close()
    print("✓", out)


def readit(book_dir, pages, hook, out, yt=False):
    import make_shorts
    slug = paint.slug_of(book_dir)
    cfg = dict(make_shorts.BOOKS[slug])
    cfg["dir"] = str(book_dir.relative_to(ROOT))
    make_shorts.read_along(cfg, Path(out), pages, yt=yt, header=hook)
    print("✓", out)


def pin(book_dir, page, lines, out):
    PWID, PHT = 1000, 1500
    slug = paint.slug_of(book_dir)
    groups = paint.load_map(book_dir, page)
    img, labels, _, _ = paint.regions(book_dir, page, paint.PW)
    done = paint.paint_full(img, labels, groups)
    top, bot = THEME.get(slug, THEME["benny"])
    c = Image.new("RGBA", (PWID, PHT), top)
    d = ImageDraw.Draw(c)
    l1, l2 = (lines.split("|") + [""])[:2]
    centered(d, l1, 60, 64, width=PWID, max_w=920)
    if l2:
        centered(d, l2, 145, 50, width=PWID, max_w=920)
    S = 455
    for k, (arr, tag) in enumerate([(img, "BEFORE"), (done, "AFTER")]):
        x = 30 + k * (S + 30)
        paste_card(c, Image.fromarray(arr).resize((S, S), Image.LANCZOS), (x, 240), (S, S), 24)
        tf = font(36)  # label under the picture, so it never covers the page's sentence
        tw = d.textlength(tag, font=tf) + 40
        lx = x + (S - tw) / 2
        d.rounded_rectangle([lx, 240 + S + 14, lx + tw, 240 + S + 66], 26, fill=NAVY)
        d.text((lx + 20, 240 + S + 18), tag, font=tf, fill="white")
    pill(d, "Color it. Then read it.", 800, width=PWID, size=52)
    cover = find_cover(book_dir)
    cw = 440
    paste_card(c, cover, ((PWID - cw) // 2, 920), (cw, cw), 30)
    centered(d, "Ages 3-6  •  Big pictures, big letters", 1400, 38, width=PWID, max_w=920)
    c.convert("RGB").save(out, quality=92)
    print("✓", out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--yt"]
    yt = "--yt" in sys.argv
    if len(args) != 5:
        sys.exit(__doc__)
    mode, bdir, pg, text, outp = args
    bdir = (ROOT / bdir).resolve()
    if mode == "guess":
        guess(bdir, int(pg), text, outp, yt)
    elif mode == "three":
        three(bdir, int(pg), text, outp, yt)
    elif mode == "readit":
        readit(bdir, [int(x) for x in pg.split(",")], text, outp, yt)
    elif mode == "pin":
        pin(bdir, int(pg), text, outp)
    else:
        sys.exit(__doc__)
