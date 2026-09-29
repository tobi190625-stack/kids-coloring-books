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
   Render a few pages to PNG (pymupdf) and look at them before calling it done, then run
   the pre-flight check, which must pass before the user uploads anything:
   `python3 tools/check_kdp.py books/NNN-slug/book.json`
   For AI (PNG) art, first run `python3 tools/clean_art.py books/NNN-slug` on `art/raw/`, and
   use `tools/build_image_cover.py` when the cover comes as front/back images.
6. Fill a listing in `kdp/listing-template.md` style as `books/NNN-slug/listing.md`
   and 3 ad hooks as `books/NNN-slug/ads.md`.

## Full-page books (`"layout": "fullbleed"`, see `books/002-benny-the-bear/book.json`)
- Square art → `"trim": "8.5x8.5"`; also set `title_art`, `belongs_art`, `end_art`.
- Each sentence goes in a white bubble (default `"text_style": "bubble"`), one type size
  for the whole book (`"text_size"` pins it; Benny uses 41).
- The builder places each bubble automatically (least drawing covered, faces avoided).
  Look at every page, and wherever a bubble hides what the sentence is about (the kite,
  the mushroom, the boots), render the other spots side by side and pick by eye. Steer
  per page: `"text_pos": "top" | "bottom"`, `"text_align": "center" | "left" | "right"`,
  `"text_offset": <inches from that edge>`, `"text_width": <0-1, share of the page width
  for a corner bubble>`, or split the words into separate bubbles with
  `"blocks": [{"text": ..., "text_pos": ...}, ...]`. Title and end pages: `"title_zone"`,
  `"end_align"`, `"end_zone"`, `"end_size"`.
- Keep phrases together with a no-break space (`\u00a0`), e.g. `Mama\u00a0Bear`,
  `little\u00a0house`, so lines break at natural phrases for early readers.
- If a sentence can't sit anywhere without covering the picture, shorten it and tell the user.

## Rules
- Never change the KDP math in the tools (margins, spine per page, bleed) without
  checking KDP's current help pages.
- Keep interiors black & white; color only on the cover.
