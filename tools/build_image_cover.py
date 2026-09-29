#!/usr/bin/env python3
"""Build a KDP wrap-around cover PDF from ready-made front and back images.

Usage:
    python3 tools/build_image_cover.py books/002-benny-the-bear/book.json

book.json "cover" needs "front_image" and "back_image" (square or portrait art,
e.g. from ChatGPT). The script:
  - upscales the art to 300+ DPI at print size,
  - fills each panel edge to edge when the art has the book's shape (square art on a
    square book), or extends it to a taller shape like 8.5x11 without cropping,
  - optionally paints out a corner watermark box ("erase": [x0, y0, x1, y1] in source px),
  - adds the spine, the back blurb and a clear barcode area.
Output: <book folder>/out/cover.pdf
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).parent))
from build_book import FALLBACK_FONT, ROOT, final_page_count, register_font  # noqa: E402

DPI = 300
BLEED = 0.125
SPINE_PER_PAGE = {"white": 0.002252, "cream": 0.0025}


def px(inches):
    return round(inches * DPI)


def erase_box(img, box):
    """Paint over a rectangle by blending the columns just left and right of it."""
    x0, y0, x1, y1 = box
    src = img.load()
    for y in range(y0, y1):
        left, right = src[x0 - 3, y], src[x1 + 3, y]
        for x in range(x0, x1):
            t = (x - x0) / (x1 - x0)
            src[x, y] = tuple(round(l + (r - l) * t) for l, r in zip(left, right))
    patch = img.crop((x0 - 4, y0 - 4, x1 + 4, y1 + 4)).filter(ImageFilter.GaussianBlur(3))
    img.paste(patch, (x0 - 4, y0 - 4))


def panel(art_path, width_px, height_px, top_px, erase=None):
    """One cover panel from the art.

    When the art is (nearly) the panel's shape, e.g. square art on an 8.5x8.5 book, it is
    scaled to fill the panel edge to edge and center-cropped (only the bleed is lost).
    When the panel is much taller, e.g. square art on 8.5x11, the art keeps its full width,
    sits top_px from the top, and its own top and bottom edges are extended to fill.
    """
    art = Image.open(art_path).convert("RGB")
    if erase:
        for box in (erase if isinstance(erase[0], list) else [erase]):
            erase_box(art, box)
    if art.height * width_px / art.width >= 0.97 * height_px:
        scale = max(width_px / art.width, height_px / art.height)
        art = art.resize((round(art.width * scale), round(art.height * scale)), Image.LANCZOS)
        x0, y0 = (art.width - width_px) // 2, (art.height - height_px) // 2
        return art.crop((x0, y0, x0 + width_px, y0 + height_px))
    scale = width_px / art.width
    art = art.resize((width_px, round(art.height * scale)), Image.LANCZOS)

    # Extend with the art's own top and bottom edges, smoothed sideways, so the
    # sky continues upward and the meadow downward without cropping anything.
    bg = Image.new("RGB", (width_px, height_px))
    strip = px(0.15)
    if top_px > 0:
        top = art.crop((0, 0, width_px, strip)).resize((10, 1), Image.BOX)
        bg.paste(top.resize((width_px, top_px + px(0.4)), Image.BICUBIC), (0, 0))
    below = height_px - top_px - art.height
    if below > 0:
        bottom = art.crop((0, art.height - strip, width_px, art.height)).resize((10, 1), Image.BOX)
        bg.paste(bottom.resize((width_px, below + px(0.4)), Image.BICUBIC), (0, height_px - below - px(0.4)))
    mask = Image.new("L", art.size, 255)
    feather = px(0.35)
    draw = ImageDraw.Draw(mask)
    for i in range(feather):
        a = round(255 * i / feather)
        if top_px > 0:
            draw.line([(0, i), (art.width, i)], fill=a)
        if top_px + art.height < height_px:
            draw.line([(0, art.height - 1 - i), (art.width, art.height - 1 - i)], fill=a)
    bg.paste(art, (0, top_px), mask)
    return bg


def build(book_file):
    book_file = Path(book_file).resolve()
    book_dir = book_file.parent
    book = json.loads(book_file.read_text())
    cover = book["cover"]

    pages = final_page_count(book)
    trim_w, trim_h = (float(v) for v in book.get("trim", "8.5x11").split("x"))
    spine = pages * SPINE_PER_PAGE[book.get("paper", "white")]
    panel_w = px(trim_w + BLEED)
    full_h = px(trim_h + 2 * BLEED)
    spine_w = px(spine)
    full_w = panel_w * 2 + spine_w

    front = panel(book_dir / cover["front_image"], panel_w, full_h,
                  px(cover.get("front_top", 1.0)), cover.get("front_erase"))
    back_art_h = panel_w  # square art
    back = panel(book_dir / cover["back_image"], panel_w, full_h,
                 full_h - back_art_h, cover.get("back_erase"))

    sheet = Image.new("RGB", (full_w, full_h), "white")
    sheet.paste(back, (0, 0))
    # Spine: the front's inner edge stretched across, so it blends with the front.
    sheet.paste(front.crop((0, 0, 4, full_h)).resize((spine_w, full_h)), (panel_w, 0))
    sheet.paste(front, (panel_w + spine_w, 0))

    draw = ImageDraw.Draw(sheet)
    font_path = cover.get("font") or book.get("font")
    font_path = ROOT / font_path if font_path else None
    if not font_path or not font_path.exists():
        font_path = FALLBACK_FONT
    color = cover.get("text_color", "#4A3526")

    # Back blurb in the sky area, kept 0.5 in inside the trim.
    left = px(BLEED + 0.6)
    max_w = px(trim_w - 1.2)
    y = px(BLEED + 0.7)
    for i, para in enumerate(cover.get("blurb", "").split("\n\n")):
        size = px(0.32) if i == 0 else px(0.2)
        font = ImageFont.truetype(str(font_path), size)
        lines = []
        for row in para.split("\n"):
            line = ""
            for word in row.split():
                test = f"{line} {word}".strip()
                if draw.textlength(test, font=font) <= max_w:
                    line = test
                else:
                    lines.append(line)
                    line = word
            lines.append(line)
        for ln in lines:
            draw.text((left, y), ln, font=font, fill=color)
            y += round(size * 1.35)
        y += round(size * 0.7)

    # Barcode area: KDP prints it bottom-right of the back cover (2 x 1.2 in).
    bx1 = px(BLEED + trim_w - 0.25)
    by1 = px(BLEED + trim_h - 0.25)
    draw.rounded_rectangle([bx1 - px(2.2), by1 - px(1.35), bx1, by1], radius=px(0.1), fill="white")

    out = book_dir / "out" / "cover.pdf"
    out.parent.mkdir(exist_ok=True)
    jpg = book_dir / "out" / "cover-preview.jpg"
    sheet.save(jpg, quality=92, dpi=(DPI, DPI))
    # Page size exactly per KDP's formula; the pixel sheet is off by a rounding hair, so
    # it is drawn stretched to fit (a change of about 0.01%).
    exact_w = (2 * (trim_w + BLEED) + spine) * inch
    exact_h = (trim_h + 2 * BLEED) * inch
    # The cover is one flat image; start the page in an embeddable font, or the PDF library
    # declares its default Helvetica, which KDP can flag as a font that isn't embedded.
    c = canvas.Canvas(str(out), pagesize=(exact_w, exact_h),
                      initialFontName=register_font(book.get("font")))
    c.drawImage(str(jpg), 0, 0, exact_w, exact_h)
    c.save()

    interior = book_dir / "out" / "interior.pdf"
    note = ""
    if not interior.exists():
        note = " (interior not built yet: rebuild the cover if the page count changes)"
    print(f"✓ {out}")
    print(f"  {exact_w/inch:.4f} x {exact_h/inch:.4f} in, spine {spine:.4f} in for {pages} pages{note}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
