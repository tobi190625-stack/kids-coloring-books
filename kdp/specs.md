# KDP paperback specs (what the tools already follow)

Verify against KDP's current help pages before each upload; KDP changes these occasionally.

## Interior
- **Trim size:** 8.5 x 11 in (most popular for coloring books). 8.5 x 8.5 also works for toddlers.
- **Bleed:** "No bleed" – drawings stay inside margins, so upload with *No bleed* selected.
- **Margins:** outside/top/bottom ≥ 0.25 in, inside (gutter) ≥ 0.375 in for 24-150 pages.
  The builder uses 0.5 in outside and 0.625 in inside.
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

## Upload checklist
1. KDP Bookshelf → *Create* → *Paperback*.
2. Details: title, subtitle, author (pen name), description, 7 keywords, 3 categories
   (see `listing-template.md`). Tick **"Low-content book"** only if it has no story; our
   story books are regular books, so leave it unticked and take the free KDP ISBN.
3. **AI content question:** answer honestly (text and/or images AI-generated).
4. Content: upload `out/interior.pdf` (No bleed, 8.5x11, white paper, B&W) and `out/cover.pdf`.
5. Launch Previewer → fix any flagged issues → order a **printed proof copy** before going live.
6. Pricing: check the royalty calculator; $6.99–$9.99 is typical for 24–60 page kids books.
