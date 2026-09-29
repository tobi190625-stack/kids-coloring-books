# KDP paperback specs (what the tools already follow)

Verify against KDP's current help pages before each upload; KDP changes these occasionally.

## Interior
- **Trim size:** 8.5 x 11 in (framed layout) or 8.5 x 8.5 in (full-page layout, square art).
- **Bleed:**
  - Framed layout: *No bleed*; drawings stay inside the margins.
  - Full-page layout: *Bleed (PDF only)*. Pages are trim + 0.125 in wide and + 0.25 in tall
    (8.625 x 8.75 in for 8.5 x 8.5), and the drawings run off every outside edge.
- **Margins:** no bleed: outside/top/bottom ≥ 0.25 in; with bleed: ≥ 0.375 in. Inside
  (gutter) ≥ 0.375 in for 24-150 pages. The builder keeps text 0.45 in from the outside
  edges and 0.6 in from the spine.
- **Page count:** minimum 24, must be even. The builder pads with blank pages.
- **Blank backs:** each drawing is followed by a blank page so markers don't bleed through.
  Set `"blank_backs": false` in `book.json` to print on both sides.
- **Ink:** black & white interior on white paper = cheapest print cost.
- **Images:** 300 DPI at print size. The builder warns on low-DPI PNG/JPG. SVG art is vector (always sharp).
- **Fonts:** embedded automatically by the builder.

## Cover
- **Size:** bleed + back + spine + front + bleed wide, trim height + 0.25 in tall.
  The builder calculates it from the interior page count.
- **Spine width (white paper):** pages x 0.002252 in.
- **Spine text:** only allowed when the book has **more than 79 pages**.
- **Barcode:** KDP prints it in the bottom-right of the back cover (2 x 1.2 in).
  The builder leaves that area white.
- Keep text 0.25 in inside the trim line (builder does this).

## Previewer errors we have hit
- **"This image is outside the margins"** on every even page: the full-page art reached past
  the page edge on the spine side (invisible, but KDP counts it). The builder now crops every
  picture to exactly the page; `tools/check_kdp.py` catches it.
- **Pages show up tall with white bands above and below:** the KDP trim size setting doesn't
  match the PDF (e.g. still 8.5 x 11 for a square 8.5 x 8.5 book). Fix the trim size in KDP
  (Paperback Content → Print Options → Trim Size), then re-upload interior and cover.

## Upload checklist
1. KDP Bookshelf → *Create* → *Paperback*.
2. Details: title, subtitle, author (pen name), description, 7 keywords, 3 categories
   (see `listing-template.md`). Tick **"Low-content book"** only if it has no story; our
   story books are regular books, so leave it unticked and take the free KDP ISBN.
3. **AI content question:** answer honestly (text and/or images AI-generated).
4. Content: upload `out/interior.pdf` and `out/cover.pdf`. Match the book's settings: trim
   size (8.5x11 or 8.5x8.5), bleed (No bleed or Bleed), white paper, black & white interior.
5. Launch Previewer → fix any flagged issues → order a **printed proof copy** before going live.
6. Pricing: check the royalty calculator; $6.99–$9.99 is typical for 24–60 page kids books.
