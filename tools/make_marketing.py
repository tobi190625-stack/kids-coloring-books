#!/usr/bin/env python3
"""Build the Pinterest pins and the square ad for a book (same look as campaigns/benny).

Usage: python3 tools/make_marketing.py books/003-nico-the-reindeer
Needs in book.json: "marketing": {"title", "pin1_head", "pin2_pages": [4 art files],
"pin3_pages": [2 art files], "colors": {"pin1","pin2","pin3","ad"}} and cover/front.png.
Writes campaigns/<slug>/images/{pin1-cover,pin2-pages,pin3-gift,ad-square}.png
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = str(ROOT / "fonts" / "Grandstander-ExtraBold.ttf")
NAVY = "#3B4A63"


def font(size):
    return ImageFont.truetype(FONT, size)


def rounded(img, radius):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(m)
    return out


def paste_card(canvas, img, xy, size, radius=40):
    img = img.convert("RGB").resize(size, Image.LANCZOS)
    card = rounded(img, radius)
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [xy[0], xy[1] + 14, xy[0] + size[0], xy[1] + size[1] + 14], radius, fill=(40, 50, 80, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(card, xy)


def centered(d, text, y, size, fill=NAVY, width=1000, max_w=None):
    f = font(size)
    while max_w and d.textlength(text, font=f) > max_w:
        size -= 2
        f = font(size)
    d.text(((width - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def pill(d, text, y, width=1000, size=54, pad=64):
    f = font(size)
    while d.textlength(text, font=f) + 2 * pad > width - 100:
        size -= 2
        f = font(size)
    w = d.textlength(text, font=f) + 2 * pad
    x0 = (width - w) / 2
    d.rounded_rectangle([x0, y, x0 + w, y + size + 62], (size + 62) // 2, fill=NAVY)
    d.text((x0 + pad, y + 24), text, font=f, fill="white")


def art(book_dir, name):
    img = Image.open(book_dir / name).convert("L")
    return img.resize((800, 800), Image.LANCZOS)


def fit(img, box):
    """Scale img to fit inside box (w, h) keeping its shape; returns the image."""
    s = min(box[0] / img.width, box[1] / img.height)
    return img.convert("RGB").resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)


def card_in_box(canvas, img, box_xy, box_wh, radius=36):
    """Paste img as a rounded card centered in a box, keeping its shape."""
    im = fit(img, box_wh)
    xy = (box_xy[0] + (box_wh[0] - im.width) // 2, box_xy[1] + (box_wh[1] - im.height) // 2)
    paste_card(canvas, im, xy, im.size, radius)


def page_art(book_dir, name):
    return Image.open(book_dir / name).convert("L").resize((700, 1050), Image.LANCZOS)


def main_portrait(book_dir, book, out):
    """Same four images for a tall (portrait) book: tall cover and tall pages."""
    m = book["marketing"]
    cover = Image.open(book_dir / "cover" / "front.png").convert("RGB")
    title = m["title"]

    c = Image.new("RGBA", (1000, 1500), m["colors"]["pin1"])
    d = ImageDraw.Draw(c)
    centered(d, m["pin1_head"][0], 60, 112)
    centered(d, m["pin1_head"][1], 165, 112)
    card_in_box(c, cover, (90, 330), (820, 870), 40)
    pill(d, "Find it on Amazon", 1230)
    centered(d, title, 1380, 50, max_w=880)
    c.convert("RGB").save(out / "pin1-cover.png")

    c = Image.new("RGBA", (1000, 1500), m["colors"]["pin2"])
    d = ImageDraw.Draw(c)
    centered(d, "Color the story.", 60, 112)
    centered(d, "Learn to read.", 165, 112)
    for i, name in enumerate(m["pin2_pages"][:6]):
        card_in_box(c, page_art(book_dir, name), (40 + (i % 3) * 315, 330 + (i // 3) * 455), (290, 435), 28)
    pill(d, "Big words. Big pictures.", 1250)
    centered(d, "Ages 3-6  \u2022  On Amazon", 1390, 50)
    c.convert("RGB").save(out / "pin2-pages.png")

    c = Image.new("RGBA", (1000, 1500), m["colors"]["pin3"])
    d = ImageDraw.Draw(c)
    centered(d, m["pin3_head"][0], 60, 104, max_w=900)
    centered(d, m["pin3_head"][1], 165, 104, max_w=900)
    card_in_box(c, cover, (50, 340), (580, 860), 36)
    card_in_box(c, page_art(book_dir, m["pin3_pages"][0]), (670, 340), (290, 425), 28)
    card_in_box(c, page_art(book_dir, m["pin3_pages"][1]), (670, 775), (290, 425), 28)
    pill(d, m["pin3_pill"], 1230)
    centered(d, title, 1380, 50, max_w=880)
    c.convert("RGB").save(out / "pin3-gift.png")

    c = Image.new("RGBA", (1080, 1080), m["colors"]["ad"])
    d = ImageDraw.Draw(c)
    centered(d, "Screen-free fun", 30, 84, width=1080)
    card_in_box(c, page_art(book_dir, m["pin3_pages"][0]), (50, 330), (250, 380), 28)
    card_in_box(c, page_art(book_dir, m["pin3_pages"][1]), (780, 330), (250, 380), 28)
    card_in_box(c, cover, (290, 140), (500, 740), 32)
    pill(d, "Color it. Read it. Love it.", 915, width=1080, size=52)
    c.convert("RGB").save(out / "ad-square.png")


def main(book_dir):
    book_dir = Path(book_dir).resolve()
    book = json.loads((book_dir / "book.json").read_text())
    m = book["marketing"]
    out = ROOT / "campaigns" / m["slug"] / "images"
    out.mkdir(parents=True, exist_ok=True)
    cover = Image.open(book_dir / "cover" / "front.png").convert("RGB")
    title = m["title"]
    if m.get("layout") == "portrait":
        main_portrait(book_dir, book, out)
        print("\u2713", out)
        return

    # pin 1: the cover
    c = Image.new("RGBA", (1000, 1500), m["colors"]["pin1"])
    d = ImageDraw.Draw(c)
    centered(d, m["pin1_head"][0], 60, 112)
    centered(d, m["pin1_head"][1], 165, 112)
    paste_card(c, cover, (90, 340), (820, 820))
    pill(d, "Find it on Amazon", 1230)
    centered(d, title, 1380, 50, max_w=880)
    c.convert("RGB").save(out / "pin1-cover.png")

    # pin 2: four pages
    c = Image.new("RGBA", (1000, 1500), m["colors"]["pin2"])
    d = ImageDraw.Draw(c)
    centered(d, "Color the story.", 60, 112)
    centered(d, "Learn to read.", 165, 112)
    for i, name in enumerate(m["pin2_pages"]):
        paste_card(c, art(book_dir, name), (70 + (i % 2) * 440, 340 + (i // 2) * 450), (420, 420), 36)
    pill(d, "Big words. Big pictures.", 1250)
    centered(d, "Ages 3-6  •  On Amazon", 1390, 50)
    c.convert("RGB").save(out / "pin2-pages.png")

    # pin 3: gift
    c = Image.new("RGBA", (1000, 1500), m["colors"]["pin3"])
    d = ImageDraw.Draw(c)
    centered(d, m["pin3_head"][0], 60, 104, max_w=900)
    centered(d, m["pin3_head"][1], 165, 104, max_w=900)
    paste_card(c, cover, (50, 400), (700, 700))
    paste_card(c, art(book_dir, m["pin3_pages"][0]), (570, 330), (400, 400), 36)
    paste_card(c, art(book_dir, m["pin3_pages"][1]), (570, 760), (400, 400), 36)
    pill(d, m["pin3_pill"], 1230)
    centered(d, title, 1380, 50, max_w=880)
    c.convert("RGB").save(out / "pin3-gift.png")

    # square ad
    c = Image.new("RGBA", (1080, 1080), m["colors"]["ad"])
    d = ImageDraw.Draw(c)
    centered(d, "Screen-free fun", 30, 84, width=1080)
    paste_card(c, cover, (190, 170), (700, 700))
    pill(d, "Color it. Read it. Love it.", 900, width=1080, size=52)
    c.convert("RGB").save(out / "ad-square.png")
    print("✓", out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
