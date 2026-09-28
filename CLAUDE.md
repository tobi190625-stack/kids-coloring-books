# Kids Color & Read Books – instructions for Claude

This folder produces Amazon KDP paperback coloring/story books. Read `README.md` and
`kdp/specs.md` before changing anything.

## "Make a new book about X"
1. Create `books/NNN-short-slug/` (next number after the highest existing one).
2. Write the story: 8-20 pages, **one or two short sentences per page** (max ~12 words),
   simple words for ages 3-6, a small problem → trying → success arc, a cozy ending.
   No trademarked characters.
3. Art, per page, in `art/`:
   - Default: draw SVG line art (white fills, `stroke="#000" stroke-width="8"`, round caps,
     big simple shapes, no gray/shading, 800x600 viewBox). Use only basic shapes/paths;
     for text inside SVGs use `font-family="Helvetica" font-weight="bold" fill="#000"`
     (svglib can't render stroked text or special glyphs).
   - If the user wants richer art: write per-page prompts using `prompts/line-art.md`
     and use the Canva `generate-image` tool when available, or give the user the prompts.
4. Write `book.json` (copy the shape of `books/001-leo-the-lion/book.json`), including
   the cover blurb and colors.
5. Build and check:
   ```bash
   python3 tools/build_book.py books/NNN-slug/book.json
   python3 tools/build_cover.py books/NNN-slug/book.json
   ```
   Render a few pages to PNG (pymupdf) and look at them before calling it done.
6. Fill a listing in `kdp/listing-template.md` style as `books/NNN-slug/listing.md`
   and 3 ad hooks as `books/NNN-slug/ads.md`.

## Rules
- Never change the KDP math in the tools (margins, spine per page, bleed) without
  checking KDP's current help pages.
- Keep interiors black & white; color only on the cover.
