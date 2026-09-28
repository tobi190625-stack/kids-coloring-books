#!/usr/bin/env python3
"""Build a KDP-ready coloring/story book interior PDF from a book.json file.

Usage:
    python3 tools/build_book.py books/001-leo-the-lion/book.json

Each page in book.json has big story text on top and a line drawing below.
Art can be SVG (drawn by Claude) or PNG/JPG (from an AI image generator).
Output: <book folder>/out/interior.pdf
"""

import json
import sys
from pathlib import Path

from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

ROOT = Path(__file__).resolve().parent.parent
FALLBACK_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# KDP no-bleed margins. Inside (gutter) margin grows with page count.
OUTSIDE_MARGIN = 0.5 * inch


def gutter_for(page_count):
    if page_count <= 150:
        return 0.375 * inch + 0.25 * inch  # KDP minimum + comfort
    if page_count <= 300:
        return 0.5 * inch + 0.25 * inch
    return 0.625 * inch + 0.25 * inch


def register_font(font_path):
    path = Path(font_path) if font_path else None
    if path and not path.is_absolute():
        path = ROOT / path
    if not path or not path.exists():
        if font_path:
            print(f"! font {font_path} not found, using DejaVu Sans Bold")
        path = Path(FALLBACK_FONT)
    pdfmetrics.registerFont(TTFont("BookFont", str(path)))
    return "BookFont"


def wrap(text, font, size, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words, line = paragraph.split(), ""
        for word in words:
            test = f"{line} {word}".strip()
            if pdfmetrics.stringWidth(test, font, size) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


def fit_text(text, font, max_size, max_width, max_height):
    """Largest font size (down to 20pt) whose wrapped text fits the box."""
    size = max_size
    while size > 20:
        lines = wrap(text, font, size, max_width)
        if len(lines) * size * 1.2 <= max_height:
            return size, lines
        size -= 2
    return size, wrap(text, font, size, max_width)


def draw_text_block(c, text, font, max_size, x, y_top, width, height):
    size, lines = fit_text(text, font, max_size, width, height)
    leading = size * 1.2
    block_h = len(lines) * leading
    y = y_top - (height - block_h) / 2 - size
    c.setFont(font, size)
    for line in lines:
        c.drawCentredString(x + width / 2, y, line)
        y -= leading


def draw_art(c, art_path, x, y, w, h, warnings):
    path = Path(art_path)
    if not path.exists():
        warnings.append(f"missing art: {art_path}")
        c.setDash(6, 6)
        c.rect(x, y, w, h)
        c.setDash()
        return
    if path.suffix.lower() == ".svg":
        drawing = svg2rlg(str(path))
        scale = min(w / drawing.width, h / drawing.height)
        drawing.scale(scale, scale)
        dx = x + (w - drawing.width * scale) / 2
        dy = y + (h - drawing.height * scale) / 2
        renderPDF.draw(drawing, c, dx, dy)
        return
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    dpi = iw / (dw / inch)
    if dpi < 300:
        warnings.append(f"{path.name}: only {dpi:.0f} DPI at print size (KDP wants 300)")
    c.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, mask="auto")


def build(book_file):
    book_file = Path(book_file).resolve()
    book_dir = book_file.parent
    book = json.loads(book_file.read_text())

    trim_w, trim_h = (float(v) * inch for v in book.get("trim", "8.5x11").split("x"))
    font = register_font(book.get("font"))
    blank_backs = book.get("blank_backs", True)
    text_size = book.get("text_size", 54)

    pages = book["pages"]
    # title + belongs-to + (story pages, maybe with blank backs) + the end
    per_story = 2 if blank_backs else 1
    page_count = 2 + len(pages) * per_story + (2 if blank_backs else 1)
    if page_count % 2:
        page_count += 1
    gutter = gutter_for(page_count)

    out_dir = book_dir / "out"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "interior.pdf"
    c = canvas.Canvas(str(out), pagesize=(trim_w, trim_h))
    c.setTitle(book["title"])
    c.setAuthor(book.get("author", ""))

    state = {"n": 0}
    warnings = []

    def box():
        # Right-hand (odd) pages have the gutter on the left.
        odd = state["n"] % 2 == 0
        left = gutter if odd else OUTSIDE_MARGIN
        right = OUTSIDE_MARGIN if odd else gutter
        return left, OUTSIDE_MARGIN, trim_w - left - right, trim_h - 2 * OUTSIDE_MARGIN

    def finish():
        c.showPage()
        state["n"] += 1

    # Title page
    x, y, w, h = box()
    draw_text_block(c, book["title"], font, 64, x, y + h * 0.75, w, h * 0.3)
    if book.get("subtitle"):
        draw_text_block(c, book["subtitle"], font, 28, x, y + h * 0.45, w, h * 0.15)
    if book.get("author"):
        draw_text_block(c, book["author"], font, 24, x, y + h * 0.2, w, h * 0.1)
    finish()

    # "This book belongs to" page
    x, y, w, h = box()
    draw_text_block(c, "This book belongs to:", font, 44, x, y + h * 0.65, w, h * 0.15)
    c.setLineWidth(3)
    c.line(x + w * 0.1, y + h * 0.45, x + w * 0.9, y + h * 0.45)
    finish()

    for page in pages:
        x, y, w, h = box()
        text_h = h * page.get("text_ratio", 0.22)
        draw_text_block(c, page["text"], font, page.get("text_size", text_size), x, y + h, w, text_h)
        gap = 0.2 * inch
        draw_art(c, book_dir / page["art"], x, y, w, h - text_h - gap, warnings)
        finish()
        if blank_backs:
            finish()  # blank back so markers don't bleed through

    # The End
    x, y, w, h = box()
    draw_text_block(c, book.get("ending", "The End"), font, 72, x, y + h * 0.6, w, h * 0.2)
    finish()
    while state["n"] < 24 or state["n"] % 2:
        finish()  # KDP paperback minimum is 24 pages

    c.save()
    print(f"✓ {out}  ({state['n']} pages, {trim_w/inch:g}x{trim_h/inch:g} in)")
    for wmsg in warnings:
        print(f"! {wmsg}")
    return out, state["n"]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
