#!/usr/bin/env python3
"""Amazon A+ content images for every book (KDP > Marketing > A+ Content Manager).

Usage: python3 tools/make_aplus.py        -> amazon/aplus/<slug>/*.png
Per book:
  1-header-970x600.png      Standard Image Header With Text: "Color it. Then read it." + before/after page
  2-step1/2/3-300x300.png   Standard Three Images & Text: color it / read it / collect the series
  3-banner-970x300.png      Standard Image & Light Text Overlay: the 4 promises
  4-compare-<slug>-150x300.png  Standard Comparison Chart: one column image per book (same set for all books)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import paint  # noqa: E402
from make_marketing import NAVY, font  # noqa: E402
from make_video import find_cover  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "amazon" / "aplus"
BOOKS = {
    "nico": dict(dir="books/003-nico-the-reindeer", page=17, bg="#EAF4FD", accent="#D9483B",
                 title="Nico the Little Reindeer"),
    "benny": dict(dir="books/002-benny-the-bear/kdp-8.5x8.5", page=20, pages=27, bg="#FFF4E0", accent="#E58A2E",
                  title="Benny the Bear"),
    "rocco": dict(dir="books/005-rocco-monster-truck", page=25, bg="#EAF6FF", accent="#2F7FD1",
                  title="Rocco the Monster Truck"),
    "posy": dict(dir="books/006-posy-the-unicorn", page=31, bg="#FDEEF6", accent="#C25BB0",
                 title="Posy the Unicorn"),
}


def card(img, size, radius=18, border=0):
    img = img.convert("RGB").resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), m)
    if border:
        ImageDraw.Draw(out).rounded_rectangle([0, 0, size - 1, size - 1], radius, outline="white", width=border)
    return out


def text_center(d, txt, cx, y, size, fill=NAVY):
    f = font(size)
    w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill)


def pages(cfg):
    book_dir = ROOT / cfg["dir"]
    img, labels, _, _ = paint.regions(book_dir, cfg["page"])
    col = paint.paint_full(img, labels, paint.load_map(book_dir, cfg["page"]))
    bw = Image.fromarray(img if img.ndim == 3 else np.stack([img] * 3, -1))
    return bw, Image.fromarray(col), find_cover(book_dir)


def header(cfg, bw, col, out):
    im = Image.new("RGBA", (970, 600), cfg["bg"])
    d = ImageDraw.Draw(im)
    d.text((40, 70), "Color it.", font=font(56), fill=NAVY)
    d.text((40, 140), "Then read it.", font=font(56), fill=cfg["accent"])
    for i, line in enumerate(["One big picture to color", "+ one short sentence", "in BIG letters on every", "page. Ages 3-6."]):
        d.text((44, 235 + i * 36), line, font=font(26), fill=NAVY)
    d.rounded_rectangle([40, 410, 340, 466], 28, fill=NAVY)
    text_center(d, "Color & Read Story Book", 190, 424, 23, fill="white")
    # before -> after
    im.alpha_composite(card(bw, 260, border=6), (410, 170))
    im.alpha_composite(card(col, 300, border=6), (640, 150))
    d.polygon([(678, 300), (650, 285), (650, 315)], fill=cfg["accent"])
    text_center(d, "before", 540, 445, 26)
    text_center(d, "after", 790, 465, 26)
    im.convert("RGB").save(out)


def steps(cfg, bw, col, covers, outdir):
    # 1: the page to color
    a = Image.new("RGBA", (300, 300), cfg["bg"])
    a.alpha_composite(card(bw, 280, border=4), (10, 10))
    a.convert("RGB").save(outdir / "2-step1-color-300x300.png")
    # 2: the colored page with its sentence
    b = Image.new("RGBA", (300, 300), cfg["bg"])
    b.alpha_composite(card(col, 280, border=4), (10, 10))
    b.convert("RGB").save(outdir / "2-step2-read-300x300.png")
    # 3: the whole series
    c = Image.new("RGBA", (300, 300), "#FFFFFF")
    for i, cv in enumerate(covers):
        c.alpha_composite(card(cv, 140, radius=10), (8 + (i % 2) * 146, 8 + (i // 2) * 146))
    c.convert("RGB").save(outdir / "2-step3-series-300x300.png")


def banner(cfg, out):
    im = Image.new("RGB", (970, 300), cfg["accent"])
    d = ImageDraw.Draw(im)
    items = [f"{cfg.get('pages', 29)} big pages", "Easy thick lines", "1 sentence a page", "Ages 3-6"]
    for i, t in enumerate(items):
        cx = 121 + i * 242
        d.ellipse([cx - 34, 70, cx + 34, 138], fill="white")
        d.line([(cx - 15, 104), (cx - 3, 117), (cx + 17, 89)], fill=cfg["accent"], width=8)
        text_center(d, t, cx, 165, 24, fill="white")
    text_center(d, "Best with crayons and colored pencils", 485, 235, 24, fill="white")
    im.save(out)


def compare_column(cover, out):
    im = Image.new("RGB", (150, 300), "white")
    c = cover.convert("RGB").resize((150, 150), Image.LANCZOS)
    im.paste(c, (0, 75))
    im.save(out)


def main():
    data = {k: (cfg, *pages(cfg)) for k, cfg in BOOKS.items()}
    covers = [data[k][3] for k in BOOKS]
    for slug, (cfg, bw, col, cover) in data.items():
        outdir = OUT / slug
        outdir.mkdir(parents=True, exist_ok=True)
        header(cfg, bw, col, outdir / "1-header-970x600.png")
        steps(cfg, bw, col, covers, outdir)
        banner(cfg, outdir / "3-banner-970x300.png")
        for s2, (_, _, _, cv) in data.items():
            compare_column(cv, outdir / f"4-compare-{s2}-150x300.png")
        print("✓", outdir)


if __name__ == "__main__":
    main()
