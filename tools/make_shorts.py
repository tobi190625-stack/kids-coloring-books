#!/usr/bin/env python3
"""Make vertical 9:16 shorts (TikTok / Reels / YouTube Shorts) for a book.

Usage: python3 tools/make_shorts.py benny          flip-through + 3 reasons
       python3 tools/make_shorts.py nico batch2   the second batch (read-along, before/after,
                                                   which page, gift idea; plus YouTube versions)
Writes marketing/<slug>/videos/*.mp4 (YouTube versions start with "yt-" and end on "Link in bio").
No sound: add one in the app.
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
from make_marketing import NAVY, card_in_box, centered, font, paste_card, pill  # noqa: E402
from make_video import FPS, H, W, colored, end_card, find_cover, prepare_coloring  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BOOKS = {
    "benny": dict(dir="books/002-benny-the-bear/kdp-8.5x8.5", bg="#CDEBF8",
                  title="Benny the Bear’s Cozy Day", reason_pages=[5, 14, 27], hero="Benny",
                  gift=["Birthday gift idea", "for kids 3-6", "A story they color AND read"],
                  gift_pages="Peek inside",
                  batch2=dict(read=[3, 4, 5, 6, 7], before_after=17, which=[6, 12, 20], gift_pages=[5, 14, 23],
                              yt=[("before_after", 27), ("read", [15, 16, 17, 18])])),
    "nico": dict(dir="books/003-nico-the-reindeer", bg="#FFE1E1",
                 title="Nico the Little Reindeer’s Snowy Day", reason_pages=[11, 17, 31], hero="Nico",
                 gift=["Stocking stuffer idea", "that isn’t candy", "A snowy story kids color AND read"],
                 gift_pages="Peek inside",
                 batch2=dict(read=[3, 4, 5, 6, 7], before_after=11, which=[9, 14, 21], gift_pages=[8, 17, 27],
                             yt=[("gift", [5, 11, 31])])),
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


def ease(t):
    return 1 - (1 - t) ** 3


def page_text(pdf, n):
    return " ".join(fitz.open(pdf)[n - 1].get_text().split())


def read_along(cfg, out, page_nos, yt=False):
    """Pages one by one; the sentence underneath lights up word by word, like reading together."""
    book_dir = ROOT / cfg["dir"]
    pdf = book_dir / "out" / "interior.pdf"
    imgs = pages(pdf, 820)
    bg = cfg["bg"]
    v = Video(out)
    for k, n in enumerate(page_nos):
        im = imgs[n - 1]
        words = page_text(pdf, n).split()
        base = Image.new("RGBA", (W, H), bg)
        d = ImageDraw.Draw(base)
        centered(d, "Read along with " + cfg["hero"], 125, 74, width=W, max_w=880)
        centered(d, cfg["title"], 228, 42, width=W, max_w=880)
        paste_card(base, im, ((W - im.width) // 2, 320), im.size, 28)
        ty0 = 320 + im.height + 45
        f = font(62)
        lines = wrap(d, " ".join(words), 62, 860)

        def caption(lit):
            c = base.copy()
            cd = ImageDraw.Draw(c)
            idx, ty = 0, ty0
            for ln in lines:
                lw = ln.split()
                x = (W - cd.textlength(ln, font=f)) / 2
                for w_ in lw:
                    col = NAVY if idx < lit else "#9AA8BD"
                    if idx == lit - 1:
                        ww = cd.textlength(w_, font=f)
                        cd.rounded_rectangle([x - 10, ty - 4, x + ww + 10, ty + 78], 18, fill="#FFE066")
                    cd.text((x, ty), w_, font=f, fill=col)
                    x += cd.textlength(w_ + " ", font=f)
                    idx += 1
                ty += 84
            return c

        if k == 0:
            v.add(caption(0), 15)
        else:
            v.fade_to(caption(0), 6)
        for lit in range(1, len(words) + 1):
            v.add(caption(lit), 11)
        v.add(caption(len(words)), 14)
    v.fade_to(end_card(book_dir, bg, yt), 10)
    v.add(end_card(book_dir, bg, yt), 90)
    v.close()


def before_after(cfg, out, page_no, yt=False):
    """The blank page, then a wipe reveals the colored page."""
    book_dir = ROOT / cfg["dir"]
    pw = 900
    img, labels, regions, color = prepare_coloring(book_dir, page_no, pw)
    done = colored(img, labels, regions, color)
    ph = img.shape[0]
    bg = cfg["bg"]
    base = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(base)
    centered(d, "Before & After", 125, 92, width=W)
    centered(d, "Same page, a little crayon magic", 245, 44, width=W, max_w=880)
    px, py = (W - pw) // 2, 340
    centered(d, cfg["title"], py + ph + 40, 44, width=W, max_w=880)

    def frame(xcut, tag):
        arr = img.copy()
        if xcut > 0:
            arr[:, :xcut] = done[:, :xcut]
        f = base.copy()
        paste_card(f, Image.fromarray(arr), (px, py), (pw, ph), 28)
        fd = ImageDraw.Draw(f)
        if 0 < xcut < pw:
            fd.rectangle([px + xcut - 4, py, px + xcut + 4, py + ph], fill="white")
        tf = font(48)
        tw = fd.textlength(tag, font=tf) + 50
        fd.rounded_rectangle([px + 20, py + ph - 95, px + 20 + tw, py + ph - 20], 36, fill=NAVY)
        fd.text((px + 45, py + ph - 88), tag, font=tf, fill="white")
        return f

    v = Video(out)
    v.add(frame(0, "BEFORE"), 50)
    for t in range(60):
        v.add(frame(round(ease((t + 1) / 60) * pw), "AFTER" if t > 30 else "BEFORE"))
    v.add(frame(pw, "AFTER"), 60)
    for t in range(30):  # peek back
        v.add(frame(round((1 - ease((t + 1) / 30) * 0.5) * pw), "AFTER"))
    for t in range(20):
        v.add(frame(round((0.5 + ease((t + 1) / 20) * 0.5) * pw), "AFTER"))
    v.add(frame(pw, "AFTER"), 30)
    v.fade_to(end_card(book_dir, bg, yt), 10)
    v.add(end_card(book_dir, bg, yt), 90)
    v.close()


def which_page(cfg, out, page_nos, yt=False):
    """Three pages pop in with numbers: 'Which page would your kid color first?'"""
    book_dir = ROOT / cfg["dir"]
    imgs = pages(book_dir / "out" / "interior.pdf", 430)
    bg = cfg["bg"]
    spots = [(70, 420), (580, 420), (325, 900)]
    base = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(base)
    centered(d, "Which page would your", 120, 72, width=W, max_w=900)
    centered(d, "kid color first?", 210, 72, width=W, max_w=900)
    centered(d, cfg["title"], 320, 40, width=W, max_w=880)

    def frame(shown, scale_last=1.0, prompt=False):
        f = base.copy()
        for k in range(shown):
            im = imgs[page_nos[k] - 1]
            s = scale_last if k == shown - 1 else 1.0
            iw, ih = round(im.width * s), round(im.height * s)
            x, y = spots[k][0] + (im.width - iw) // 2, spots[k][1] + (im.height - ih) // 2
            paste_card(f, im.resize((iw, ih)), (x, y), (iw, ih), 24)
            fd = ImageDraw.Draw(f)
            cx, cy = x + 10, y + 10
            fd.ellipse([cx, cy, cx + 90, cy + 90], fill=NAVY)
            nf = font(64)
            fd.text((cx + 45 - fd.textlength(str(k + 1), font=nf) / 2, cy + 6), str(k + 1), font=nf, fill="white")
        if prompt:
            fd = ImageDraw.Draw(f)
            pill(fd, "Comment 1, 2 or 3!", 1390, width=W, size=60)
        return f

    v = Video(out)
    v.add(frame(0), 20)
    for k in range(1, 4):
        for t in range(8):
            v.add(frame(k, 0.6 + 0.4 * ease((t + 1) / 8)))
        v.add(frame(k), 25)
    v.add(frame(3, prompt=True), 120)
    v.fade_to(end_card(book_dir, bg, yt), 10)
    v.add(end_card(book_dir, bg, yt), 90)
    v.close()


def gift_idea(cfg, out, page_nos, yt=False):
    """Slow zoom on the cover with the gift idea lines, then a few pages, then the end card."""
    book_dir = ROOT / cfg["dir"]
    cover = find_cover(book_dir)
    imgs = pages(book_dir / "out" / "interior.pdf", 760)
    bg = cfg["bg"]
    lines = cfg["gift"]
    v = Video(out)
    n = 150
    for t in range(n):
        f = Image.new("RGBA", (W, H), bg)
        d = ImageDraw.Draw(f)
        for k, ln in enumerate(lines):
            appear = 10 + k * 30
            if t >= appear:
                centered(d, ln, 130 + k * 100, 76 if k < 2 else 54, width=W, max_w=900)
        s = 1.0 + 0.08 * t / n
        size = round(780 * s)
        card_in_box(f, cover, ((W - size) // 2, 470 + (780 - size) // 2), (size, size), 40)
        v.add(f)
    for k, n_ in enumerate(page_nos):
        f = Image.new("RGBA", (W, H), bg)
        d = ImageDraw.Draw(f)
        centered(d, cfg["gift_pages"], 140, 70, width=W, max_w=900)
        card_in_box(f, imgs[n_ - 1], (160, 300), (760, 1100), 28)
        v.fade_to(f, 6)
        v.add(f, 34)
    v.fade_to(end_card(book_dir, bg, yt), 10)
    v.add(end_card(book_dir, bg, yt), 90)
    v.close()


def batch2(slug, cfg, out):
    b = cfg["batch2"]
    read_along(cfg, out / "read-along.mp4", b["read"])
    before_after(cfg, out / "before-after.mp4", b["before_after"])
    which_page(cfg, out / "which-page.mp4", b["which"])
    gift_idea(cfg, out / "gift-idea.mp4", b["gift_pages"])
    for kind, arg in b["yt"]:
        name = {"read": "read-along", "before_after": "before-after", "which": "which-page",
                "gift": "gift-idea"}[kind]
        fn = {"read": read_along, "before_after": before_after, "which": which_page,
              "gift": gift_idea}[kind]
        fn(cfg, out / f"yt-{name}.mp4", arg, yt=True)


def main(slug, which="batch1"):
    cfg = BOOKS[slug]
    out = ROOT / "marketing" / slug / "videos"
    out.mkdir(parents=True, exist_ok=True)
    if which == "batch2":
        batch2(slug, cfg, out)
        print("✓", out, "batch 2")
        return
    flip_through(slug, cfg, out / "flip-through.mp4")
    three_reasons(slug, cfg, out / "3-reasons.mp4")
    print("✓", out / "flip-through.mp4", "and 3-reasons.mp4")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in BOOKS:
        sys.exit(__doc__)
    main(*sys.argv[1:])
