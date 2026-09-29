#!/usr/bin/env python3
"""Pre-flight check a built book against KDP's print rules before uploading.

Usage:
    python3 tools/check_kdp.py books/002-benny-the-bear/book.json

Checks out/interior.pdf and out/cover.pdf: page count and size (with or without bleed),
fonts embedded, no transparency, every image inside its page and at 300+ DPI, text
inside the safe margins, words inside their bubbles, the story text matching book.json,
and the cover's exact size for this page count. Exits 1 if anything fails.
"""

import json
import re
import sys
from pathlib import Path

import pymupdf as fitz

sys.path.insert(0, str(Path(__file__).parent))
from build_book import ROOT, active_pages, final_page_count  # noqa: E402

IN = 72
BLEED = 0.125
SPINE_PER_PAGE = {"white": 0.002252, "cream": 0.0025}


def spans(page):
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                if span["text"].strip():
                    yield span


def main(book_file):
    book_file = Path(book_file).resolve()
    book_dir = book_file.parent
    book = json.loads(book_file.read_text())
    trim_w, trim_h = (float(v) for v in book.get("trim", "8.5x11").split("x"))
    bleed = book.get("layout") == "fullbleed" and book.get("bleed", True)
    fullpage = book.get("layout") == "fullbleed"
    problems = []

    def check(ok, message):
        if not ok:
            problems.append(message)

    fitz.TOOLS.reset_mupdf_warnings()
    d = fitz.open(book_dir / "out" / "interior.pdf")
    want_pages = final_page_count(book)
    check(len(d) == want_pages, f"interior has {len(d)} pages, expected {want_pages}")
    check(len(d) >= 24 and len(d) % 2 == 0, "KDP needs an even page count of at least 24")
    page_w = trim_w + (BLEED if bleed else 0)
    page_h = trim_h + (2 * BLEED if bleed else 0)
    margin = 0.375 if bleed else 0.25

    for i, p in enumerate(d):
        n = i + 1
        check(abs(p.rect.width / IN - page_w) < 1e-3 and abs(p.rect.height / IN - page_h) < 1e-3,
              f"page {n}: size {p.rect.width/IN:.3f}x{p.rect.height/IN:.3f} in, "
              f"expected {page_w:.3f}x{page_h:.3f}")
        for f in p.get_fonts():
            check(f[1] != "n/a" and "+" in f[3], f"page {n}: font {f[3]} is not embedded")
        for im in p.get_images(full=True):
            check(not im[1], f"page {n}: image has transparency")
        recto_ = i % 2 == 0
        for info in p.get_image_info():
            r = fitz.Rect(info["bbox"])
            check(r.x0 > -0.5 and r.y0 > -0.5 and r.x1 < p.rect.width + 0.5 and r.y1 < p.rect.height + 0.5,
                  f"page {n}: an image reaches past the page edge (KDP: 'image outside the margins')")
            if not bleed:
                # KDP's No-bleed rule: pictures stay inside the margins (0.25 in outside and
                # top/bottom, 0.375 in at the spine, measured on the Previewer's guides)
                lo = fitz.Rect(0.25 * IN, 0.25 * IN, p.rect.width - 0.25 * IN, p.rect.height - 0.25 * IN)
                lo.x0, lo.x1 = ((0.375 * IN, lo.x1) if recto_ else (lo.x0, p.rect.width - 0.375 * IN))
                check(r.x0 >= lo.x0 - 0.5 and r.x1 <= lo.x1 + 0.5 and r.y0 >= lo.y0 - 0.5 and r.y1 <= lo.y1 + 0.5,
                      f"page {n}: picture reaches into the margins "
                      f"(left {r.x0/IN:.2f}, right {(p.rect.width-r.x1)/IN:.2f}, "
                      f"top {r.y0/IN:.2f}, bottom {(p.rect.height-r.y1)/IN:.2f} in)")
            if r.width > 1:
                check(info["width"] / (r.width / IN) >= 299,
                      f"page {n}: image is only {info['width'] / (r.width / IN):.0f} DPI")
        # trim box: bleed goes on the outside edge (right on odd pages, left on even pages)
        recto = i % 2 == 0
        tx0 = 0 if (recto or not bleed) else BLEED * IN
        tx1 = tx0 + trim_w * IN
        ty0 = BLEED * IN if bleed else 0
        ty1 = ty0 + trim_h * IN
        if not bleed:
            tx0, tx1 = 0, trim_w * IN
        bubbles = [dr["rect"] for dr in p.get_drawings()
                   if dr.get("fill") == (1.0, 1.0, 1.0) and dr.get("color") == (0.0, 0.0, 0.0)]
        for s in spans(p):
            r = fitz.Rect(s["bbox"])
            m = min(r.x0 - tx0, tx1 - r.x1, r.y0 - ty0, ty1 - r.y1) / IN
            check(m >= margin, f"page {n}: text '{s['text'][:25]}' is {m:.3f} in from the trim "
                               f"(KDP needs {margin})")
            if fullpage and book.get("text_style", "bubble") == "bubble":
                check(any(b.contains(r) for b in bubbles),
                      f"page {n}: text '{s['text'][:25]}' spills out of its bubble")

    # the words on the pages match the story
    norm = lambda t: re.sub(r"\s+", " ", t.replace(" ", " ")).strip()
    if fullpage:
        expected = [None, None]  # title and name pages vary; the story pages must match
        for pg in active_pages(book):
            text = " ".join(b["text"] for b in pg["blocks"]) if pg.get("blocks") else pg["text"]
            expected.append(norm(text))
        for n, want in enumerate(expected, start=1):
            if want is None or n > len(d):
                continue
            got = norm(" ".join(s["text"] for s in spans(d[n - 1])))
            check(got == want, f"page {n}: text reads '{got}', expected '{want}'")

    warnings = fitz.TOOLS.mupdf_warnings()
    check(not warnings, f"PDF structure warnings: {warnings}")

    cover_file = book_dir / "out" / "cover.pdf"
    if cover_file.exists():
        c = fitz.open(cover_file)
        spine = len(d) * SPINE_PER_PAGE[book.get("paper", "white")]
        want_w, want_h = 2 * (trim_w + BLEED) + spine, trim_h + 2 * BLEED
        cw, ch = c[0].rect.width / IN, c[0].rect.height / IN
        check(abs(cw - want_w) < 0.005 and abs(ch - want_h) < 0.005,
              f"cover is {cw:.4f}x{ch:.4f} in, KDP expects {want_w:.4f}x{want_h:.4f} for {len(d)} pages")
        for f in c[0].get_fonts():
            check(f[1] != "n/a" and "+" in f[3], f"cover: font {f[3]} is not embedded")
        for info in c[0].get_image_info():
            r = fitz.Rect(info["bbox"])
            check(r.x0 > -0.5 and r.y0 > -0.5 and r.x1 < c[0].rect.width + 0.5 and r.y1 < c[0].rect.height + 0.5,
                  "cover: an image reaches past the page edge")
            check(info["width"] / (r.width / IN) >= 299, "cover: image under 300 DPI")
    else:
        problems.append("out/cover.pdf is missing")

    print(f"{book['title']}: {len(d)} pages, {page_w:.3f} x {page_h:.3f} in "
          f"({'bleed' if bleed else 'no bleed'}), KDP trim size {trim_w:g} x {trim_h:g} in")
    if problems:
        print(f"✗ {len(problems)} problem(s):")
        for msg in problems:
            print(f"  - {msg}")
        return 1
    print("✓ ready for KDP (still check the Previewer and order a proof copy)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
