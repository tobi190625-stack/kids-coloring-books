#!/usr/bin/env python3
"""Still posts that go with the fresh ads: Pinterest pins (2:3) and an Instagram/Facebook swipe carousel (4:5).

Usage: python tools/fresh_stills.py   -> campaigns/fresh/stills/*.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from fresh_ads import (INK, NAVY, OUT, POSY_ROUNDS, Page, book_dir, card, comic, font, gradient,  # noqa: E402
                       groups_from_map, ring)
from make_video import find_cover  # noqa: E402

S = OUT / "stills"


def canvas(w, h, c1, c2):
    return gradient(c1, c2).resize((w, h))


def centered(d, text, y, size, fill=NAVY, w=1000, max_w=900):
    while d.textlength(text, font=font(size)) > max_w:
        size -= 2
    d.text(((w - d.textlength(text, font=font(size))) / 2, y), text, font=font(size), fill=fill)


def rocco_pages():
    changes = [("red", [165]), ("red", [163]), ("blue", [48])]
    g = groups_from_map("rocco", 26)
    return Page("rocco", 26, g, changes=changes), changes, len(g)


def rocco_pin(page, changes, n):
    im = canvas(1000, 1500, "#EAF6FF", "#CFE8F7")
    d = ImageDraw.Draw(im)
    comic(d, "Spot 3 Differences!", 500, 80, 84)
    centered(d, "Monster truck activity for kids 3-6", 140, 44)
    s = 600
    card(im, page.picture([1] * n, s), 200, 210)
    card(im, page.picture([1] * n, s, changed=True), 200, 835)
    d = ImageDraw.Draw(im)
    centered(d, "Rocco the Little Monster Truck's Big Jump  •  color & read book", 1455, 30)
    im.convert("RGB").save(S / "pin-rocco-spot-difference.png")


def rocco_carousel(page, changes, n):
    s = 540
    for slide in (1, 2):
        im = canvas(1080, 1350, "#EAF6FF", "#CFE8F7")
        d = ImageDraw.Draw(im)
        comic(d, "Spot 3 differences!" if slide == 1 else "Answers:", 540, 80, 80)
        x = (1080 - s) / 2
        card(im, page.picture([1] * n, s), x, 150)
        card(im, page.picture([1] * n, s, changed=True), x, 715)
        d = ImageDraw.Draw(im)
        if slide == 2:
            sc = s / page.shape[1]
            for _, ids in changes:
                cx, cy, rr = page.where(ids)
                for y in (150, 715):
                    ring(d, x + cx * sc, y + cy * sc, min(rr * sc, 105), width=9)
        else:
            centered(d, "swipe for the answers >>", 1282, 42, w=1080)
        im.convert("RGB").save(S / f"carousel-rocco-{slide}.png")
    im = canvas(1080, 1350, "#EAF6FF", "#CFE8F7")
    d = ImageDraw.Draw(im)
    comic(d, "Color it. Read it.", 540, 110, 96)
    card(im, find_cover(book_dir("rocco")).resize((760, 760)), 160, 230)
    d = ImageDraw.Draw(im)
    centered(d, "One big picture + one easy sentence on every page", 1040, 42, w=1080, max_w=980)
    centered(d, "Ages 3-6  •  find it on Amazon (link in bio)", 1110, 42, w=1080, max_w=980)
    im.convert("RGB").save(S / "carousel-rocco-3.png")


def posy_pin():
    p, g, q, sentence = POSY_ROUNDS[0]
    page = Page("posy", p, g)
    im = canvas(1000, 1500, "#FFEAF4", "#EADCFF")
    d = ImageDraw.Draw(im)
    comic(d, "Learn Colors with Posy!", 500, 80, 80, fill="#FFD95A")
    centered(d, "Unicorn coloring page for kids 3-6", 140, 44)
    s = 600
    card(im, page.picture([0] * len(g), s), 200, 210)
    card(im, page.picture([1] * len(g), s), 200, 835)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([330, 790, 670, 840], 25, fill=NAVY)
    centered(d, sentence.split("!")[0] + "!", 795, 36, fill="white")
    centered(d, "Posy the Little Unicorn's Rainbow Birthday  •  color & read", 1455, 30)
    im.convert("RGB").save(S / "pin-posy-learn-colors.png")


if __name__ == "__main__":
    S.mkdir(parents=True, exist_ok=True)
    page, changes, n = rocco_pages()
    rocco_pin(page, changes, n)
    rocco_carousel(page, changes, n)
    posy_pin()
    print("✓", *sorted(p.name for p in S.iterdir()))
