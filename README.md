# Kids Color & Read Books (Amazon KDP side hustle)

Kids' coloring books with a simple story in BIG letters on every page, sold as
paperbacks through Amazon KDP (print on demand), promoted with short-form video
on TikTok, Instagram/Facebook Reels and YouTube Shorts.

## What's in this folder

| Path | What it is |
|---|---|
| `tools/build_book.py` | Turns `book.json` + drawings into a KDP-ready **interior PDF** |
| `tools/build_cover.py` | Builds the wrap-around **cover PDF** (back + spine + front) sized to the page count |
| `books/001-leo-the-lion/` | Finished sample book: story, 8 drawings, `out/interior.pdf`, `out/cover.pdf` |
| `kdp/specs.md` | KDP print rules (sizes, margins, spine, DPI, AI disclosure) |
| `kdp/listing-template.md` | Title / subtitle / keywords / description template for the Amazon listing |
| `marketing/ad-scripts.md` | Ready-to-film TikTok / Reels / Shorts scripts and hooks |
| `prompts/line-art.md` | Prompts for AI image generators that give clean coloring-page line art |
| `CLAUDE.md` | Instructions Claude follows when you say "make a new book about ..." |

## Make a book (3 commands)

```bash
pip install -r requirements.txt
python3 tools/build_book.py books/001-leo-the-lion/book.json    # -> out/interior.pdf
python3 tools/build_cover.py books/001-leo-the-lion/book.json   # -> out/cover.pdf
```

Or just ask Claude: **"Make a new book about a dinosaur who is scared of the dark."**
Claude writes the story, draws or prompts the art, builds both PDFs.

Optional: drop a rounded kid-style font at `fonts/kids.ttf` (free: *Fredoka*,
*Baloo 2* or *Andika* from Google Fonts). Without it the builder uses DejaVu Sans Bold.

## Best Claude tools for this

Already connected to your account:

- **Canva** – `generate-image` for colorful cover art, `create-design` + `export-design`
  for covers, ad images and thumbnails. Best option for the colored cover.
- **vidIQ** – finds viral TikTok/Instagram/YouTube kids-content outliers, keyword research,
  script, voiceover and short-video generation for ads.
- **HyperFrames (HeyGen)** – programmable video ads (flip-through / "watch me color" style).
- **pdf skill** (built in) – checks, merges and previews the PDFs.

Worth installing (from the Anthropic plugin directory):

- **image-generation** – prompting guide for Midjourney / Ideogram / GPT Image / Flux etc.
  Makes AI line art come out clean (thick outlines, no shading) on the first try.

How the art gets made: Claude can draw simple SVG line art directly (like the sample book),
which is 100% print-sharp at any size. For richer illustrations use an AI image
generator with the prompts in `prompts/line-art.md`, save PNGs into the book's `art/`
folder at 2400 px or wider, and the builder handles the rest.

## Honest money math

- KDP pays **60% of list price minus print cost**. A 24-page 8.5x11 black-ink paperback
  costs about **$2.30** to print (US), so at **$7.99** you keep about **$2.50 per sale**.
  Check exact numbers with KDP's royalty calculator before pricing.
- Royalties are paid ~60 days after the end of the month of the sale.
- Kids' coloring books are a crowded category. What moves the needle: a specific
  niche (e.g. "trucks for toddlers", "first words + coloring"), a strong cover,
  and publishing a **series** so one buyer buys 3-5 books. Plan on 10+ books, not 1.
- KDP requires you to **disclose AI-generated content** (text and/or images) when you
  publish. Don't use characters you don't own (no Disney, Bluey, Pokémon etc.) or the
  book gets pulled and the account can be banned.
