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


FONT_FILES = {}


def register_font(font_path=None, name="BookFont"):
    path = Path(font_path) if font_path else DEFAULT_FONT
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        path = DEFAULT_FONT if DEFAULT_FONT.exists() else Path(FALLBACK_FONT)
        if font_path:
            print(f"! font {font_path} not found, using {path.name}")
    pdfmetrics.registerFont(TTFont(name, str(path)))
    FONT_FILES[name] = path
    return name


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


# never end a line on these: they belong with the word after them (weighted double)
ARTICLES = {"a", "an", "the", "his", "her", "my", "their", "your", "our", "its"}
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
            weak = sum((2 if e.lower() in ARTICLES else 1) for e in ends if e.lower() in WEAK_ENDINGS)
            mid_sentence = sum(len(re.findall(r"[.!?] +\S", line)) for line in lines)
            # a word alone on its line is fine only if it is a whole sentence ("Whee!", "Hello!")
            lonely = sum(" " not in line and not (line.endswith(("!", "?", "."))
                                                 and (k == 0 or lines[k - 1].endswith(("!", "?", "."))))
                         for k, line in enumerate(lines))
            ragged = max(widths) - min(widths)
            score = ragged + size * (4 * weak + 8 * mid_sentence + 3 * lonely + 3 * (n - fewest))
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


# --- full-bleed layout ------------------------------------------------------
#
# The drawing covers the whole page (KDP "bleed"), and the words sit right on
# the picture in solid black. A white knockout hugging the letters clears the
# line art behind them, so the text reads cleanly without a box or border.

BLEED = 0.125 * inch
SAFE = 0.45 * inch          # text stays this far inside the trim (KDP minimum 0.375in with bleed)
SAFE_GUTTER = 0.6 * inch    # ...and this far from the spine (KDP minimum 0.375in)
LEADING = 1.12
HALO = 0.30                 # knockout around the letters, as a fraction of the type size
FACE_WEIGHT = 1.0           # covering a face costs as much as covering solid black ink
BODY_WEIGHT = 0.4           # a body under a face is worth keeping clear too, but less so

# "bubble" text style (the default): the words sit in a white rounded bubble with a thin
# outline, like a label placed on the picture.
BUBBLE_SAFE = 0.375 * inch          # bubble edge stays this far inside the trim...
BUBBLE_SAFE_GUTTER = 0.5 * inch     # ...and from the spine; the words sit further in still
BUBBLE_PAD_X = 0.32 * inch          # room between the words and the bubble's edge
BUBBLE_PAD_Y = 0.2 * inch
BUBBLE_LINE = 3.0                   # outline weight, matched to the drawings' lines
BUBBLE_RADIUS = 0.5 * inch
PART_GAP = 0.16 * inch              # between a title and its subtitle, words and a name line


def ink_extent(font):
    """How far the letters' ink reaches above and below the baseline, per point of size."""
    from PIL import ImageFont
    f = ImageFont.truetype(str(FONT_FILES[font]), 200)
    return -f.getbbox("bdfhklBDHT!", anchor="ls")[1] / 200, f.getbbox("gjpqy,", anchor="ls")[3] / 200


def cap_height(font):
    """Height of the capitals above the baseline, per point of size (for optical centering)."""
    from PIL import ImageFont
    f = ImageFont.truetype(str(FONT_FILES[font]), 200)
    return -f.getbbox("HBEN", anchor="ls")[1] / 200


class InkMap:
    """What the words would hide: line-art density, plus a heavy price for faces.

    In this art style every character has solid black eyes, so eyes (and noses) are the
    blobs left after thin lines are eroded away. Each one marks a head-sized zone
    (reaching up over the ears) that the text should stay off.
    """

    def __init__(self, art_path, placement, reduce=6):
        from PIL import Image, ImageDraw, ImageFilter
        im = Image.open(art_path).convert("L")
        self.im = im.resize((max(1, im.width // reduce), max(1, im.height // reduce)), Image.BOX)
        self.x, self.y, self.w, self.h = placement
        px_per_in = 630 / (self.w / inch)
        small = im.resize((630, 630), Image.BOX)
        eroded = small.filter(ImageFilter.MaxFilter(7)).resize((126, 126), Image.BOX)
        self.faces = Image.new("L", (126, 126), 0)   # heads, full price
        self.bodies = Image.new("L", (126, 126), 0)  # the body below each head, lighter price
        faces, bodies = ImageDraw.Draw(self.faces), ImageDraw.Draw(self.bodies)
        unit = px_per_in / 5
        r, lift = 1.45 * unit, 0.4 * unit
        for y in range(126):
            for x in range(126):
                if eroded.getpixel((x, y)) < 110:
                    faces.ellipse((x - r, y - lift - r, x + r, y - lift + r), fill=255)
                    bodies.ellipse((x - 1.1 * unit, y + 0.9 * unit, x + 1.1 * unit, y + 3.3 * unit), fill=255)

    def _box(self, rect, size):
        x0, y0, x1, y1 = rect
        width, height = size
        px0 = max(0, int((x0 - self.x) / self.w * width))
        px1 = min(width, int((x1 - self.x) / self.w * width))
        py0 = max(0, int((self.y + self.h - y1) / self.h * height))
        py1 = min(height, int((self.y + self.h - y0) / self.h * height))
        return px0, py0, px1, py1

    occupied = ()

    def cost(self, rects):
        from PIL import ImageStat
        total = 0.0
        for rect in rects:
            for ox0, oy0, ox1, oy1 in self.occupied:  # never overlap another text block
                if rect[0] < ox1 and ox0 < rect[2] and rect[1] < oy1 and oy0 < rect[3]:
                    total += 1e9
            px0, py0, px1, py1 = self._box(rect, self.im.size)
            if px1 <= px0 or py1 <= py0:
                continue
            area = (px1 - px0) * (py1 - py0)
            ink = (255 - ImageStat.Stat(self.im.crop((px0, py0, px1, py1))).mean[0]) / 255
            fx0, fy0, fx1, fy1 = self._box(rect, self.faces.size)
            face = body = 0.0
            if fx1 > fx0 and fy1 > fy0:
                face = ImageStat.Stat(self.faces.crop((fx0, fy0, fx1, fy1))).mean[0] / 255
                body = ImageStat.Stat(self.bodies.crop((fx0, fy0, fx1, fy1))).mean[0] / 255
            total += area * (ink + FACE_WEIGHT * face + BODY_WEIGHT * max(0.0, body - face))
        return total


def text_part(lines, size, halo=None):
    return {"kind": "text", "lines": lines, "size": size, "halo": halo or max(6, size * HALO)}


def layout_block(parts, font, cx, top):
    """Stack text lines and name plates downward from `top`: drawable items + knockout rects.

    A plate with "wrap": True becomes one clean white panel behind the whole block (words
    and writing line together), so no stray bits of drawing show between them.
    """
    asc, desc = ink_extent(font)
    wrapping = any(p["kind"] == "plate" and p.get("wrap") for p in parts)
    items, rects, y = [], [], top - (0.24 * inch if wrapping else 0)
    for i, part in enumerate(parts):
        gap = 0.16 * inch if i < len(parts) - 1 else 0
        if part["kind"] == "text":
            size, halo = part["size"], part["halo"]
            base = y
            for j, line in enumerate(part["lines"]):
                base = y - asc * size - j * size * LEADING
                width = pdfmetrics.stringWidth(line, font, size)
                items.append(("text", line, size, cx - width / 2, base, halo))
                rects.append((cx - width / 2 - halo, base - desc * size - halo,
                              cx + width / 2 + halo, base + asc * size + halo))
            y = base - desc * size - gap
        else:  # a white plate to write a name on
            w, h = part["w"], part["h"]
            plate_top = top if part.get("wrap") else y
            items.append(("plate", cx - w / 2, y - h, w, h, plate_top))
            rects.append((cx - w / 2, y - h, cx + w / 2, plate_top))
            y -= h + gap
    return items, rects, top - y


def layout_bubble(parts, font, cx, top):
    """Words (and a name line to write on) inside one white bubble whose top edge is `top`.

    Lines are centered on the band from the capitals' tops to the baseline, so a line
    without descenders doesn't look like it floats high in its bubble.
    """
    cap = cap_height(font)
    items, widths = [], []
    # padding grows with big type (title, The End) so large letters never crowd the edge
    big = max((p["size"] for p in parts if p["kind"] == "text"), default=0)
    pad_x, pad_y = max(BUBBLE_PAD_X, 0.3 * big), max(BUBBLE_PAD_Y, 0.22 * big)
    y = top - pad_y
    for i, part in enumerate(parts):
        if part["kind"] == "text":
            size = part["size"]
            base = y
            for j, line in enumerate(part["lines"]):
                base = y - cap * size - j * size * LEADING
                width = pdfmetrics.stringWidth(line, font, size)
                items.append(("text", line, size, cx - width / 2, base, 0))
                widths.append(width)
            y = base - 0.1 * size
        else:  # room to write a name, with a dotted line at the bottom
            w, h = part["w"], part["h"]
            items.append(("plate", cx - w / 2, y - h, w, h, y))
            widths.append(w)
            y -= h
        if i < len(parts) - 1:
            y -= PART_GAP
    half = max(widths) / 2 + pad_x
    rect = (cx - half, y - pad_y, cx + half, top)
    return [("bubble", rect)] + items, [rect], top - rect[1]


def draw_bubble(c, parts, font, cx, top):
    items, _, _ = layout_bubble(parts, font, cx, top)
    c.saveState()
    c.setFont(font, 12)  # never let a text object fall back to unembedded Helvetica
    for item in items:
        if item[0] == "bubble":
            x0, y0, x1, y1 = item[1]
            c.setLineWidth(BUBBLE_LINE)
            c.setLineJoin(1)
            c.setStrokeColor(black)
            c.setFillColor(white)
            c.roundRect(x0, y0, x1 - x0, y1 - y0, min((y1 - y0) / 2, BUBBLE_RADIUS), stroke=1, fill=1)
    c.setFillColor(black)
    for item in items:
        if item[0] == "text":
            _, line, size, x, base, _ = item
            c.setFont(font, size)
            c.drawString(x, base, line)
        elif item[0] == "plate":
            _, px, py, w, h, _ = item
            c.setLineWidth(2.4)
            c.setLineCap(1)
            c.setDash(1, 7)
            c.line(px, py + 0.22 * inch, px + w, py + 0.22 * inch)
            c.setDash()
    c.restoreState()


def place_block(variants, font, safe, ink, zone="auto", offset=None, layout=layout_block):
    """Pick the layout and spot that hide the least drawing (and no faces).

    `variants` maps an anchor ("center", "left", "right") to the block's parts; each is tried
    near the top and the bottom of the page. Returns (parts, cx, top).
    """
    x0, y0, x1, y1 = safe
    step, travel = 0.05 * inch, 1.8 * inch
    candidates = []
    for anchor, parts in variants.items():
        _, rects, height = layout(parts, font, 0, 0)
        left, right = min(r[0] for r in rects), max(r[2] for r in rects)
        # knockout halos may reach past the safe line; a bubble's edge may not
        inset = max(p.get("halo", 0) for p in parts) if layout is layout_block else 0
        cx = {"center": (x0 + x1) / 2, "left": x0 - left - inset, "right": x1 - right + inset}[anchor]
        if offset is not None:  # manual override: inches down from the top / up from the bottom
            top = y1 - offset * inch if zone != "bottom" else y0 + height + offset * inch
            candidates.append((0, len(candidates), parts, cx, top))
            continue
        for where in ("top", "bottom"):
            if zone not in ("auto", where):
                continue
            for k in range(int(travel / step) + 1):
                top = y1 - k * step if where == "top" else y0 + height + k * step
                if top > y1 + 0.01 or top - height < y0 - 0.01:
                    break
                shifted = [(a + cx, b + top, c_ + cx, d + top) for a, b, c_, d in rects]
                cost = ink.cost(shifted) if ink else 0
                cost += k * step / inch * 250            # hug the edge of the page
                cost *= 1.0 if where == "top" else 1.12  # read from the top, all else equal
                cost *= 1.0 if anchor == "center" else 1.25
                candidates.append((cost, len(candidates), parts, cx, top))
    _, _, parts, cx, top = min(candidates, key=lambda c_: (c_[0], c_[1]))
    return parts, cx, top


def draw_block(c, parts, font, cx, top):
    items, _, _ = layout_block(parts, font, cx, top)
    c.saveState()
    c.setFont(font, 12)  # never let a text object fall back to unembedded Helvetica
    # 1) knockouts: clear the drawing behind the words. Wrapped in its own q/Q because the
    #    text render mode and stroke width are sticky graphics state in PDF.
    c.saveState()
    c.setLineJoin(1)
    c.setLineCap(1)
    c.setStrokeColor(white)
    c.setFillColor(white)
    for item in items:
        if item[0] == "text":
            _, line, size, x, base, halo = item
            width = pdfmetrics.stringWidth(line, font, size)
            c.setLineWidth(size * 0.7)  # bridge letters and word spaces into one smooth shape
            c.line(x + size * 0.3, base + size * 0.33, x + width - size * 0.3, base + size * 0.33)
            c.setLineWidth(2 * halo)
            t = c.beginText()
            t.setTextRenderMode(2)
            t.setFont(font, size)
            t.setTextOrigin(x, base)
            t.textOut(line)
            c.drawText(t)
        else:
            _, px, py, w, h, plate_top = item
            c.roundRect(px, py, w, plate_top - py, min((plate_top - py) / 2, 0.45 * inch),
                        stroke=0, fill=1)
    c.restoreState()
    # 2) the words themselves, solid black
    c.setFillColor(black)
    c.setStrokeColor(black)
    for item in items:
        if item[0] == "text":
            _, line, size, x, base, _ = item
            c.setFont(font, size)
            c.drawString(x, base, line)
        else:
            _, px, py, w, h, _ = item
            c.setLineWidth(2.4)
            c.setLineCap(1)
            c.setDash(1, 7)
            c.line(px + 0.45 * inch, py + h * 0.3, px + w - 0.45 * inch, py + h * 0.3)
            c.setDash()
    c.restoreState()


def full_page_art(c, art_path, rect, warnings, center_x=None):
    """Fill `rect` = (x, y, w, h) with the art, center-cropped, embedded cropped to exactly it.

    Returns the placement of the uncropped, scaled art (for the text-placement map). Cropping
    before embedding matters: KDP's checker reports any image reaching past its allowed area.
    """
    from PIL import Image
    src = Image.open(art_path)
    iw, ih = src.size
    rx, ry, rw, rh = rect
    scale = max(rw / iw, rh / ih)
    w, h = iw * scale, ih * scale
    cx = rx + rw / 2 if center_x is None else center_x
    x, y = cx - w / 2, ry + (rh - h) / 2
    if iw / (w / inch) < 300:
        warnings.append(f"{Path(art_path).name}: only {iw / (w / inch):.0f} DPI at print size")
    left, right = round((rx - x) / scale), round((rx + rw - x) / scale)
    top, bottom = round((y + h - (ry + rh)) / scale), round((y + h - ry) / scale)
    crop = src.crop((max(0, left), max(0, top), min(iw, right), min(ih, bottom)))
    c.drawImage(ImageReader(crop.convert("L")), rx, ry, rw, rh)
    return x, y, w, h


def story_fit_size(texts, font, inner_width, max_lines=2, max_size=54, min_size=28):
    """One type size for the whole book: the largest where every sentence fits in max_lines.

    `inner_width(size)` is the room the words get at that size.
    """
    for size in range(max_size, min_size - 1, -1):
        w = inner_width(size)
        if all(len(balanced_wrap(t, font, size, w, max_lines=max_lines)) <= max_lines for t in texts):
            return size
    return min_size


def build_fullbleed(book, book_dir, font, out, warnings):
    trim_w, trim_h = (float(v) * inch for v in book["trim"].split("x"))
    bleed = book.get("bleed", True)
    # No-bleed books (KDP's default): the picture must stay inside KDP's margins, which the
    # Previewer measures at about 0.25 in outside and 0.375 in at the spine. We keep clear
    # of both with room to spare, so the picture fills the page except for a thin white edge.
    art_out, art_gutter = book.get("art_margin", 0.3) * inch, book.get("art_gutter", 0.5) * inch
    page_w, page_h = (trim_w + BLEED, trim_h + 2 * BLEED) if bleed else (trim_w, trim_h)
    c = canvas.Canvas(str(out), pagesize=(page_w, page_h), initialFontName=font)
    c.setTitle(book["title"])
    c.setAuthor(book.get("author", ""))
    pages = active_pages(book)
    state = {"n": 0}
    bubble = book.get("text_style", "bubble") == "bubble"
    layout, draw = (layout_bubble, draw_bubble) if bubble else (layout_block, draw_block)
    edge, spine_edge = (BUBBLE_SAFE, BUBBLE_SAFE_GUTTER) if bubble else (SAFE, SAFE_GUTTER)

    def art_rect():
        """Where the picture goes on the current page (odd pages: spine on the left)."""
        if bleed:
            return (0, 0, page_w, page_h)
        right_hand = state["n"] % 2 == 0
        x0 = art_gutter if right_hand else art_out
        x1 = trim_w - (art_out if right_hand else art_gutter)
        return (x0, art_out, x1 - x0, trim_h - 2 * art_out)

    def frame():
        """Trim center and the safe area for the current page (odd pages: spine on the left)."""
        right_hand = state["n"] % 2 == 0
        if not bleed:
            x, y, w, h = art_rect()
            inset = 0.12 * inch  # the bubble stays a little inside the picture
            return trim_w / 2, (x + inset, y + inset, x + w - inset, y + h - inset)
        trim_x0 = 0 if right_hand else BLEED
        x0 = trim_x0 + (spine_edge if right_hand else edge)
        x1 = trim_x0 + trim_w - (edge if right_hand else spine_edge)
        safe = (x0, BLEED + edge, x1, BLEED + trim_h - edge)
        return trim_x0 + trim_w / 2, safe

    def page(art, blocks):
        """blocks: [(variants, zone, offset)], placed in order; later ones avoid earlier ones."""
        trim_cx, safe = frame()
        placement = full_page_art(c, book_dir / art, art_rect(), warnings,
                                  center_x=trim_cx if bleed else None)
        ink = InkMap(book_dir / art, placement)
        placed = []
        for variants, zone, offset in blocks:
            parts, cx, top = place_block(variants, font, safe, ink, zone, offset, layout)
            ink.occupied = tuple(ink.occupied) + tuple(layout(parts, font, cx, top)[1])
            placed.append((parts, cx, top))
        for parts, cx, top in placed:
            draw(c, parts, font, cx, top)
        c.showPage()
        state["n"] += 1

    _, safe = frame()
    safe_w = safe[2] - safe[0]

    def inner(width, size):
        """Room for the words in a block `width` wide (minus bubble padding or halo)."""
        return width - 2 * (BUBBLE_PAD_X if bubble else max(6, size * HALO))

    # one size for every page: pinned in book.json, or the largest that fits two lines
    size = book.get("text_size") or story_fit_size([p["text"] for p in pages], font,
                                                   lambda s_: inner(safe_w, s_))
    text_w = inner(safe_w, size)
    side_w = inner(safe_w * 0.62, size)  # narrower block that can tuck into a corner

    # Title page
    title_w = inner(safe_w, 66)
    title_size = clean_title_size(book["title"], font, title_w, 2.6 * inch, max_size=74)
    parts = [text_part(balanced_wrap(book["title"], font, title_size, title_w), title_size)]
    tagline = book.get("title_page_subtitle", book.get("subtitle"))
    if tagline:
        parts.append(text_part(balanced_wrap(tagline, font, 28, title_w * 0.8), 28))
    if book.get("author"):
        parts.append(text_part([book["author"]], 22))
    page(book["title_art"], [({"center": parts}, book.get("title_zone", "top"), None)])

    # This book belongs to
    if bubble:
        writing = {"kind": "plate", "w": text_w, "h": 0.95 * inch}
    else:
        writing = {"kind": "plate", "w": safe_w * 0.92, "h": 1.05 * inch, "wrap": True}
    page(book["belongs_art"], [({"center": [text_part(["This book belongs to:"], 44), writing]},
                                book.get("belongs_zone", "auto"), None)])

    def story_variants(text, align, width=None):
        centered = [text_part(balanced_wrap(text, font, size, text_w), size)]
        forced = align in ("left", "right")
        corner_w = inner(safe_w * width, size) if width else side_w
        side_lines = balanced_wrap(text, font, size, corner_w, max_lines=4 if forced else 3)
        side_ok = (len(side_lines) <= 3
                   and max(pdfmetrics.stringWidth(l, font, size) for l in side_lines) <= corner_w
                   and not any(re.search(r"[.!?] +\S", l) for l in side_lines)
                   and not any(l.split(" ")[-1].lower() in WEAK_ENDINGS for l in side_lines[:-1])
                   and not any(" " not in l and not l.endswith(("!", "?")) for l in side_lines))
        side = [text_part(side_lines, size)]
        if forced:
            return {align: side}
        if align == "center" or not side_ok:
            return {"center": centered}
        return {"center": centered, "left": side, "right": side}

    for p in pages:
        # A page can split its words into separate blocks (e.g. a sound effect near the ducks).
        blocks = p.get("blocks") or [p]
        page(p["art"], [(story_variants(b["text"], b.get("text_align"), b.get("text_width")),
                         b.get("text_pos", "auto"), b.get("text_offset")) for b in blocks])

    end_parts = [text_part([book.get("ending", "The End")], book.get("end_size", 110))]
    page(book["end_art"], [({book.get("end_align", "center"): end_parts},
                             book.get("end_zone", "auto"), None)])
    while state["n"] < 24 or state["n"] % 2:
        c.showPage()
        state["n"] += 1
    c.save()
    return state["n"], size


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
    warnings = []
    if book.get("layout") == "fullbleed":
        count, size = build_fullbleed(book, book_dir, font, out, warnings)
        print(f"✓ {out}  ({count} pages, {trim_w/inch:g}x{trim_h/inch:g} in + bleed, "
              f"story text {size}pt)")
        for wmsg in warnings:
            print(f"! {wmsg}")
        return out, count

    c = canvas.Canvas(str(out), pagesize=(trim_w, trim_h), initialFontName=font)
    c.setTitle(book["title"])
    c.setAuthor(book.get("author", ""))

    state = {"n": 0}

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
