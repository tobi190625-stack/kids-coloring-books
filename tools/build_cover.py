#!/usr/bin/env python3
"""Build a KDP paperback wrap-around cover (back + spine + front) PDF.

Usage:
    python3 tools/build_cover.py books/001-leo-the-lion/book.json

Needs out/interior.pdf to exist first (page count sets the spine width).
Output: <book folder>/out/cover.pdf
"""

import json
import re
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).parent))
from build_book import draw_art, draw_text_block, register_font, wrap  # noqa: E402

BLEED = 0.125 * inch
SAFE = 0.25 * inch  # keep text this far inside the trim line
SPINE_PER_PAGE = {"white": 0.002252, "cream": 0.0025}  # inches, KDP B&W paper


def build(book_file):
    book_file = Path(book_file).resolve()
    book_dir = book_file.parent
    book = json.loads(book_file.read_text())
    cover = book.get("cover", {})

    interior = book_dir / "out" / "interior.pdf"
    if not interior.exists():
        sys.exit("Build the interior first: python3 tools/build_book.py " + str(book_file))
    pages = len(re.findall(rb"/Type /Page\b", interior.read_bytes()))

    trim_w, trim_h = (float(v) * inch for v in book.get("trim", "8.5x11").split("x"))
    spine = pages * SPINE_PER_PAGE[book.get("paper", "white")] * inch
    full_w = BLEED + trim_w + spine + trim_w + BLEED
    full_h = BLEED + trim_h + BLEED

    font = register_font(book.get("font"))
    bg = HexColor(cover.get("color", "#FFB703"))
    accent = HexColor(cover.get("accent", "#023047"))

    out = book_dir / "out" / "cover.pdf"
    c = canvas.Canvas(str(out), pagesize=(full_w, full_h))
    c.setFillColor(bg)
    c.rect(0, 0, full_w, full_h, stroke=0, fill=1)

    back_x = BLEED
    spine_x = BLEED + trim_w
    front_x = spine_x + spine
    base_y = BLEED

    # Front: title band, then white panel with the cover art
    fx, fy = front_x + SAFE, base_y + SAFE
    fw, fh = trim_w - 2 * SAFE, trim_h - 2 * SAFE
    c.setFillColor(accent)
    draw_text_block(c, book["title"], font, 72, fx, fy + fh, fw, fh * 0.24)
    if book.get("subtitle"):
        draw_text_block(c, book["subtitle"], font, 28, fx, fy + fh * 0.76, fw, fh * 0.08)
    panel_y, panel_h = fy + fh * 0.1, fh * 0.56
    c.setFillColor(white)
    c.roundRect(fx + 0.2 * inch, panel_y, fw - 0.4 * inch, panel_h, 0.4 * inch, stroke=0, fill=1)
    warnings = []
    if cover.get("art"):
        pad = 0.4 * inch
        draw_art(c, book_dir / cover["art"], fx + pad, panel_y + pad,
                 fw - 2 * pad, panel_h - 2 * pad, warnings)
    if book.get("author"):
        c.setFillColor(accent)
        draw_text_block(c, book["author"], font, 26, fx, fy + fh * 0.08, fw, fh * 0.08)

    # Back: blurb, leaving KDP's barcode area (bottom right) clear
    bx, by = back_x + SAFE + 0.25 * inch, base_y + SAFE
    bw, bh = trim_w - 2 * SAFE - 0.5 * inch, trim_h - 2 * SAFE
    c.setFillColor(accent)
    blurb = cover.get("blurb", "")
    size = 22
    y = by + bh - 0.6 * inch
    c.setFont(font, size)
    for para in blurb.split("\n\n"):
        for line in wrap(para, font, size, bw):
            c.drawString(bx, y, line)
            y -= size * 1.35
        y -= size * 0.6
    barcode_w, barcode_h = 2.0 * inch, 1.2 * inch
    c.setFillColor(white)
    c.rect(back_x + trim_w - SAFE - barcode_w, base_y + SAFE, barcode_w, barcode_h, stroke=0, fill=1)

    # Spine text only allowed by KDP when the book has more than 79 pages
    if pages > 79:
        c.saveState()
        c.setFillColor(accent)
        c.translate(spine_x + spine / 2, base_y + trim_h / 2)
        c.rotate(-90)
        spine_size = min(18, spine * 0.55)
        c.setFont(font, spine_size)
        c.drawCentredString(0, -spine_size / 3, book["title"])
        c.restoreState()

    c.save()
    print(f"✓ {out}")
    print(f"  full size {full_w/inch:.3f} x {full_h/inch:.3f} in, spine {spine/inch:.3f} in, {pages} pages")
    if pages <= 79:
        print("  (no spine text: KDP only allows it above 79 pages)")
    for wmsg in warnings:
        print(f"! {wmsg}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
