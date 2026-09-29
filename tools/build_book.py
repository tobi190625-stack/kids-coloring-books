#!/usr/bin/env python3
"""Build a KDP-ready coloring/story book interior PDF from a book.json file.

Usage:
    python3 tools/build_book.py books/002-benny-the-bear/book.json

Storybook layout: each drawing sits in a rounded frame, and its sentence is set
in colorable bubble letters inside a cloud that overlaps the top of the frame,
so the words become part of the picture. Art can be SVG (drawn by Claude) or
PNG/JPG (from an AI image generator).
Output: <book folder>/out/interior.pdf
"""

import json
import math
import re
import sys
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parent.parent
# Grandstander (SIL OFL): chunky and round, with the single-story a and g kids learn to write.
DEFAULT_FONT = ROOT / "fonts" / "Grandstander-ExtraBold.ttf"
FALLBACK_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# KDP no-bleed margins. Inside (gutter) margin grows with page count.
OUTSIDE_MARGIN = 0.5 * inch

# One line weight for everything drawn, matched to the AI line art (~3pt at print size).
LINE = 3.2
PANEL = 6.9 * inch        # square frame around each drawing
CLOUD_H = 3.2 * inch      # cloud that holds the sentence
OVERLAP = 0.3 * inch      # how far the cloud sits over the top of the frame
TEXT_OUTLINE = 2.4        # outline around the bubble letters


def gutter_for(page_count):
    if page_count <= 150:
        return 0.375 * inch + 0.25 * inch  # KDP minimum + comfort
    if page_count <= 300:
        return 0.5 * inch + 0.25 * inch
    return 0.625 * inch + 0.25 * inch


def active_pages(book):
    """Story pages to print; pages marked "skip" (art not ready yet) are left out."""
    return [p for p in book["pages"] if not p.get("skip")]


def final_page_count(book):
    """Pages in the finished interior: front matter, story pages, The End, padded."""
    per_story = 2 if book.get("blank_backs", True) else 1
    n = max(2 + len(active_pages(book)) * per_story + 1, 24)  # KDP minimum is 24
    return n + n % 2


def register_font(font_path=None):
    path = Path(font_path) if font_path else DEFAULT_FONT
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        path = DEFAULT_FONT if DEFAULT_FONT.exists() else Path(FALLBACK_FONT)
        if font_path:
            print(f"! font {font_path} not found, using {path.name}")
    pdfmetrics.registerFont(TTFont("BookFont", str(path)))
    return "BookFont"


# --- text -------------------------------------------------------------------

def wrap(text, font, size, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words, line = [w for w in paragraph.split(" ") if w], ""
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


WEAK_ENDINGS = {"a", "an", "the", "and", "of", "to", "with", "it", "is",
                "in", "on", "at", "by", "his", "her", "my", "their"}


def balanced_wrap(text, font, size, max_width, max_lines=3):
    """Even lines that fit, avoiding a dangling "the"/"and" and sentence breaks mid-line.

    Words joined by a no-break space (e.g. "Mama\u00a0Bear") always stay together.
    """
    words = [w for w in text.split(" ") if w]
    fewest = len(wrap(text, font, size, max_width))
    best, best_score = None, None
    for n in range(fewest, max(fewest, max_lines) + 1):
        for breaks in _break_sets(len(words), n):
            lines = [" ".join(words[a:b]) for a, b in zip((0,) + breaks, breaks + (len(words),))]
            widths = [pdfmetrics.stringWidth(line, font, size) for line in lines]
            if max(widths) > max_width:
                continue
            ends = [line.split(" ")[-1] for line in lines[:-1]]
            weak = sum(e.lower() in WEAK_ENDINGS for e in ends)  # no punctuation = mid-phrase
            mid_sentence = sum(len(re.findall(r"[.!?] +\S", line)) for line in lines)
            lonely = sum(" " not in line and not line.endswith(("!", "?", ".")) for line in lines)
            ragged = max(widths) - min(widths)
            score = ragged + size * (4 * weak + 6 * mid_sentence + 3 * lonely + 3 * (n - fewest))
            if best_score is None or score < best_score:
                best, best_score = lines, score
    return best or wrap(text, font, size, max_width)


def _break_sets(n_words, n_lines):
    """Every way to split n_words into n_lines non-empty lines (fine for short sentences)."""
    from itertools import combinations
    if n_lines <= 1 or n_words <= 1:
        return [()]
    return list(combinations(range(1, n_words), min(n_lines, n_words) - 1))


def story_lines(text, font, size, max_width):
    return balanced_wrap(text, font, size, max_width)


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
    """Plain solid text, centered in a box (used by the cover builder)."""
    size, lines = fit_text(text, font, max_size, width, height)
    leading = size * 1.2
    block_h = len(lines) * leading
    y = y_top - (height - block_h) / 2 - size
    c.setFont(font, size)
    for line in lines:
        c.drawCentredString(x + width / 2, y, line)
        y -= leading


def block_height(font, size, n_lines, leading=1.08):
    ascent, descent = pdfmetrics.getAscentDescent(font, size)
    return (n_lines - 1) * size * leading + (ascent - descent)


def bubble_text(c, lines, font, size, cx, cy, outline=TEXT_OUTLINE, leading=1.08):
    """Colorable letters: white inside, black outline drawn only outside the glyphs."""
    ascent, _ = pdfmetrics.getAscentDescent(font, size)
    top = cy + block_height(font, size, len(lines), leading) / 2 - ascent
    baselines = [top - i * size * leading for i in range(len(lines))]
    c.saveState()
    c.setFont(font, size)  # set before beginText, or the text object starts in unembedded Helvetica
    c.setLineJoin(1)
    c.setLineCap(1)
    c.setStrokeColor(black)
    c.setLineWidth(outline * 2)
    for mode, colour in ((1, black), (0, white)):  # doubled stroke first, white fill on top
        c.setFillColor(colour)
        for line, base in zip(lines, baselines):
            t = c.beginText()
            t.setTextRenderMode(mode)
            t.setFont(font, size)
            t.setTextOrigin(cx - pdfmetrics.stringWidth(line, font, size) / 2, base)
            t.textOut(line)
            c.drawText(t)
    c.restoreState()


def solid_text(c, text, font, size, cx, y):
    c.setFillColor(black)
    c.setFont(font, size)
    c.drawCentredString(cx, y, text)


# --- shapes -----------------------------------------------------------------

def _union(c, shapes, line=LINE):
    """Outline several overlapping shapes as one: dilated black first, white on top."""
    c.saveState()
    c.setLineJoin(1)
    c.setStrokeColor(black)
    for fill, stroke in ((black, 2 * line), (white, 0)):
        c.setFillColor(fill)
        c.setLineWidth(stroke or 0.1)
        for kind, *args in shapes:
            if kind == "circle":
                c.circle(*args, stroke=1 if stroke else 0, fill=1)
            else:
                c.roundRect(*args, stroke=1 if stroke else 0, fill=1)
    c.restoreState()


def cloud(c, x, y, w, h):
    """A puffy cloud filling the box (x, y, w, h), bumps a little uneven like the art's clouds."""
    body_y, body_h = y + 0.12 * h, 0.66 * h
    shapes = [("rect", x, body_y, w, body_h, body_h / 2)]
    top = body_y + body_h
    for i, rr in enumerate([0.30, 0.37, 0.29, 0.35, 0.27, 0.33]):
        r = rr * h * 0.6
        shapes.append(("circle", x + w * (0.14 + 0.72 * i / 5), top - r * 0.3, r))
    for i, rr in enumerate([0.17, 0.21, 0.16, 0.2, 0.17]):
        r = rr * h * 0.6
        shapes.append(("circle", x + w * (0.2 + 0.6 * i / 4), body_y + r * 0.15, r))
    _union(c, shapes)


def star(c, cx, cy, r, line=LINE):
    p = c.beginPath()
    for i in range(10):
        a = math.pi / 2 + math.pi * i / 5
        rr = r if i % 2 == 0 else r * 0.5
        (p.moveTo if i == 0 else p.lineTo)(cx + rr * math.cos(a), cy + rr * math.sin(a))
    p.close()
    c.saveState()
    c.setLineJoin(1)
    c.setLineWidth(line)
    c.setFillColor(white)
    c.drawPath(p, stroke=1, fill=1)
    c.restoreState()


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


def framed_art(c, art_path, x, y, size, warnings, radius=0.42 * inch):
    """Drawing clipped to a rounded window, then the frame drawn over its edge."""
    c.saveState()
    clip = c.beginPath()
    clip.roundRect(x, y, size, size, radius)
    c.clipPath(clip, stroke=0, fill=0)
    bleed = 0.08 * inch  # pushes the image's hard cut-off edges under the frame
    draw_art(c, art_path, x - bleed, y - bleed, size + 2 * bleed, size + 2 * bleed, warnings)
    c.restoreState()
    c.saveState()
    c.setLineWidth(LINE)
    c.roundRect(x, y, size, size, radius, stroke=1, fill=0)
    c.restoreState()


def page_badge(c, cx, cy, number, font):
    c.saveState()
    c.setLineWidth(LINE * 0.8)
    c.setFillColor(white)
    c.circle(cx, cy, 0.24 * inch, stroke=1, fill=1)
    c.setFillColor(black)
    c.setFont(font, 14)
    ascent, descent = pdfmetrics.getAscentDescent(font, 14)
    c.drawCentredString(cx, cy - (ascent + descent) / 2, str(number))
    c.restoreState()


# --- book -------------------------------------------------------------------

def story_type_size(texts, font, max_width, max_height, max_size=56, min_size=30, wrapper=None):
    """One size for the whole book: the largest at which every sentence fits its cloud."""
    wrapper = wrapper or story_lines
    for size in range(max_size, min_size - 1, -1):
        if all(block_height(font, size, len(wrapper(t, font, size, max_width))) <= max_height
               for t in texts):
            return size
    return min_size


def clean_title_size(title, font, max_width, max_height, max_size=66, min_size=36):
    """Largest size where the title fits and breaks cleanly (no dangling "the", no lone word)."""
    for size in range(max_size, min_size - 1, -1):
        lines = balanced_wrap(title, font, size, max_width)
        clean = all(line.split(" ")[-1].lower() not in WEAK_ENDINGS for line in lines[:-1])
        clean = clean and (len(lines) == 1 or all(" " in line for line in lines))
        if clean and block_height(font, size, len(lines)) <= max_height:
            return size
    return min_size


def build(book_file):
    book_file = Path(book_file).resolve()
    book_dir = book_file.parent
    book = json.loads(book_file.read_text())

    trim_w, trim_h = (float(v) * inch for v in book.get("trim", "8.5x11").split("x"))
    font = register_font(book.get("font"))
    blank_backs = book.get("blank_backs", True)

    pages = active_pages(book)
    gutter = gutter_for(final_page_count(book))

    out_dir = book_dir / "out"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "interior.pdf"
    c = canvas.Canvas(str(out), pagesize=(trim_w, trim_h), initialFontName=font)
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

    x, y, w, h = box()
    cloud_w = PANEL + 0.3 * inch  # a touch wider than the frame, so the cloud breaks it
    text_w = cloud_w - 1.0 * inch
    text_h = CLOUD_H * 0.62
    size = story_type_size([p["text"] for p in pages], font, text_w, text_h)

    # Title page: title in a tall cloud, subtitle, and a framed drawing to color.
    x, y, w, h = box()
    cx = x + w / 2
    title_cloud_h = 4.0 * inch
    title_size = clean_title_size(book["title"], font, text_w, title_cloud_h * 0.6)
    title_cloud_y = y + h - title_cloud_h
    cloud(c, cx - cloud_w / 2, title_cloud_y, cloud_w, title_cloud_h)
    bubble_text(c, balanced_wrap(book["title"], font, title_size, text_w), font, title_size,
                cx, title_cloud_y + title_cloud_h * 0.46, outline=TEXT_OUTLINE * 1.3)
    sub_lines = balanced_wrap(book.get("subtitle", ""), font, 17, w * 0.8) if book.get("subtitle") else []
    for i, line in enumerate(sub_lines):
        solid_text(c, line, font, 17, cx, title_cloud_y - 0.3 * inch - i * 22)
    art_top = title_cloud_y - 0.45 * inch - len(sub_lines) * 22
    art_size = min(5.4 * inch, art_top - y - 0.1 * inch)
    if book.get("title_art"):
        framed_art(c, book_dir / book["title_art"], cx - art_size / 2, art_top - art_size, art_size, warnings)
    if book.get("author"):
        solid_text(c, book["author"], font, 20, cx, y + 0.05 * inch)
    finish()

    # "This book belongs to" page: cloud, a name plate to write in, stars to color.
    x, y, w, h = box()
    cx = x + w / 2
    plate_w, plate_h = PANEL, 2.0 * inch
    plate_y = y + h * 0.36
    cloud_y = plate_y + plate_h + 0.35 * inch
    cloud(c, cx - cloud_w / 2, cloud_y, cloud_w, CLOUD_H)
    bubble_text(c, balanced_wrap("This book belongs to:", font, 50, text_w), font, 50,
                cx, cloud_y + CLOUD_H * 0.47)
    c.saveState()
    c.setLineWidth(LINE)
    c.roundRect(cx - plate_w / 2, plate_y, plate_w, plate_h, 0.4 * inch, stroke=1, fill=0)
    c.setDash(1, 8)
    c.setLineCap(1)
    c.setLineWidth(LINE * 0.8)
    c.line(cx - plate_w / 2 + 0.55 * inch, plate_y + 0.6 * inch,
           cx + plate_w / 2 - 0.55 * inch, plate_y + 0.6 * inch)
    c.restoreState()
    for i, r in enumerate([0.34, 0.46, 0.6, 0.46, 0.34]):
        star(c, cx + (i - 2) * 1.35 * inch, y + h * 0.17, r * inch)
    finish()

    for page in pages:
        x, y, w, h = box()
        cx = x + w / 2
        group_h = PANEL + CLOUD_H - OVERLAP
        panel_y = y + max(0.2 * inch, (h - group_h) / 2)  # leaves room for the page number
        framed_art(c, book_dir / page["art"], cx - PANEL / 2, panel_y, PANEL, warnings)
        cloud_y = panel_y + PANEL - OVERLAP
        cloud(c, cx - cloud_w / 2, cloud_y, cloud_w, CLOUD_H)
        bubble_text(c, story_lines(page["text"], font, size, text_w), font, size,
                    cx, cloud_y + CLOUD_H * 0.46)
        page_badge(c, cx, panel_y, state["n"] + 1, font)
        finish()
        if blank_backs:
            finish()  # blank back so markers don't bleed through

    # The End: big bubble letters in a cloud, stars around it.
    x, y, w, h = box()
    cx, cy = x + w / 2, y + h / 2
    end_h = CLOUD_H * 1.15
    cloud(c, cx - cloud_w / 2, cy - end_h * 0.47, cloud_w, end_h)
    bubble_text(c, [book.get("ending", "The End")], font, 92, cx, cy)
    for sx, sy, r in [(-2.5, 2.6, 0.5), (0.3, 3.4, 0.36), (2.5, 2.5, 0.62),
                      (-2.4, -2.6, 0.62), (0.2, -3.3, 0.42), (2.6, -2.4, 0.46)]:
        star(c, cx + sx * inch, cy + sy * inch, r * inch)
    finish()
    while state["n"] < 24 or state["n"] % 2:
        finish()  # KDP paperback minimum is 24 pages

    c.save()
    print(f"✓ {out}  ({state['n']} pages, {trim_w/inch:g}x{trim_h/inch:g} in, story text {size}pt)")
    for wmsg in warnings:
        print(f"! {wmsg}")
    return out, state["n"]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
