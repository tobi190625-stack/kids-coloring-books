# Project memory: Little Crayon Tales (read this first, every session)

Last updated: 2026-10-04. Keep this file current: add decisions, links and lessons as they happen.

## Who / how to work
- Owner: a teenager in the Czech Republic (not 18 yet). Non-technical, often on a phone, sometimes a laptop.
  Plain English, short steps, copy-paste boxes. Send files (PDF, PNG, MP4) instead of explaining.
  Hates long prompts and being told "it should work": **check everything yourself before sending**
  (render pages, look at frames, run tools/check_kdp.py). Do the whole job to the end.
- The KDP account belongs to an adult friend (18). Anything needing ID, a card or tax forms is the friend's.
  Tax: Czech rodne cislo on W-8BEN; royalties are the friend's income (see notes in chat history: ask the
  financni urad / an accountant once money comes in).
- Business: Amazon KDP paperback "color & read" story books for kids 3-6 (one big B&W picture + one short
  big-letter sentence per page), marketed organically on TikTok, YouTube Shorts, Instagram, Facebook, Pinterest.
  Goal: **2 new books per week + daily marketing**.
- Brand: **Little Crayon Tales**. Profile picture `marketing/profile-picture.png`, Facebook cover
  `marketing/facebook-cover.png`, YouTube banner `marketing/youtube-banner.png`.

## Books
| # | Folder | Title | Trim | Status | Amazon |
|---|---|---|---|---|---|
| 1 | books/002-benny-the-bear (final files in kdp-8.5x8.5/) | Benny the Bear's Cozy Day | 8.5x8.5 no bleed | LIVE | https://www.amazon.com/dp/B0HLVSLXK7 |
| 2 | books/003-nico-the-reindeer | Nico the Little Reindeer's Snowy Day | 8.5x8.5 no bleed | LIVE | https://www.amazon.com/dp/B0HLVTTK7T |
| 3 | books/004-dex-the-dinosaur | Dex the Little Dinosaur's Big Day | 8.5x11 no bleed | built; owner said NOT to post/market it | - |
| 4 | books/005-rocco-monster-truck (branch books/rocco-and-posy) | Rocco the Little Monster Truck's Big Jump | 8.5x8.5 | prompts ready, waiting for art | - |
| 5 | books/006-posy-the-unicorn (branch books/rocco-and-posy) | Posy the Little Unicorn's Rainbow Birthday | 8.5x8.5 | prompts ready, waiting for art | - |
Book 001-leo-the-lion is an old SVG test book, ignore.

## Accounts / links
- Linktree: linktr.ee/littlecrayontalles (note the double L in the username; fix or use exactly).
  Should show the 2 book links FIRST (big "featured" cards), socials below.
- Socials: TikTok, Instagram, YouTube, Pinterest, Facebook Page "Little Crayon Tales" (handles assumed
  @littlecrayontales; confirm exact handles with the owner before using them in links).
- Amazon Author Central: not set up yet (books may show different author names; check "by ..." on both pages).
- Own landing page (Netlify-ready): `site/` (drag the folder onto app.netlify.com/drop). Social URLs in it are guesses.

## How we make a book (proven pipeline)
1. Story + prompts: book.json (29 story pages + title/belongs/end art = 32 pictures), `chatgpt-prompts.md`
   (4 prompts x 8 images, one image per generation, square 1:1), `cover-prompts.md`, `listing.md`.
2. Owner generates art in ChatGPT, sends zips. Sort by contact sheet → `art/raw/NN.png`,
   `python3 tools/clean_art.py <book>`, `python3 tools/build_book.py <book>/book.json`,
   cover: `python3 tools/build_image_cover.py <book>/book.json`, then `python3 tools/check_kdp.py <book>/book.json`.
3. Look at every page (bubble over faces/key objects → per-page overrides in book.json).
4. Send `X-INSIDE-manuscript.pdf` + `X-COVER.pdf` + the KDP answers from listing.md.

## KDP lessons (do not repeat mistakes)
- KDP "No bleed" needs pictures inside margins (0.25 in outside/top/bottom, 0.375 in at spine) → `"bleed": false`.
- The KDP trim size setting must match the PDF exactly. Cover width = 2*(trim+0.125)+pages*0.002252.
- Even page count, min 24. Fonts embedded (initialFontName fix), no transparency, 300+ DPI.
- Every book has its OWN ISBN (free KDP ISBN). Books are linked on Amazon by the AUTHOR NAME, not the ISBN.
- No trademarked characters/brands (no brainrot characters, Monster Jam, CAT look, My Little Pony, Kittycorn...).

## Campaign system (the weekly routine)
- `campaigns/<slug>/CAMPAIGN.md` = everything for one book: link, every ad file + its caption per platform, posting log, Sunday results.
- `campaigns/WEEKLY-SYSTEM.md` = the repeatable week (Mon stories+prompts, Tue-Wed art, Thu KDP upload, Fri-Sun ad pack; daily: 1 video to TikTok/YT/IG/FB + 1 pin + story; carousels Tue+Sat; Sunday check).
- `campaigns/THIS-WEEK.md` = day-by-day plan for the current week. **Rewrite it every Sunday.**
- New book: `python3 tools/new_campaign.py books/<NNN-book> [amazon link]`, then make the ad pack into campaigns/<slug>/.
- When the owner says "posted X", tick it in that book's posting log.

## Marketing toolkit (all in tools/, ad outputs in campaigns/<slug>/, shared stuff in marketing/)
- `make_marketing.py` pins + square ad · `make_carousel.py` 6-slide 4:5 carousels
- `paint.py` hand-picked realistic coloring maps (marketing/paint/<slug>-p<N>.json) · `make_video.py` coloring videos
  (`--yt` = "Link in bio" end card) · `make_shorts.py` flip-through, 3 reasons, read-along, before/after, which-page, gift
- `make_slideshow.py` colored pages + voiceover · `voice.py` Kokoro TTS (natural pauses, warm EQ; model in /root/kokoro,
  re-download from github.com/thewh1teagle/kokoro-onnx releases if missing) · `make_music.py` original copyright-free
  music box (marketing/music/) · `carousel_video.py` carousel → Reel
- Video frames are checked by extracting frames with ffmpeg (imageio_ffmpeg) and looking at them.
- Rules learned: TikTok business account (Commercial music only), YouTube Shorts "not made for kids", post at
  15:00-17:00 Czech time, English only, no location tag, captions say "link in bio". Pixabay music is free.
  Facebook links are clickable, Instagram/TikTok captions are not. Pinterest: link goes in the Destination field.
  Paid ads only after first sales/reviews ($5/day tests, the adult friend's card).

## What has been posted (update this!)
- YouTube Shorts: Nico x3 (song-only snowman, voiceover, slideshow) + Benny x3.
- TikTok: Nico slideshow (+ more in progress). Instagram/Facebook: Reels in progress (4 videos + 2 carousels).
- Pinterest: 3 Nico pins prepared (free pins, Amazon link in Destination field).

## Open tasks
- Rocco + Posy art (owner generates) → build → publish → campaigns.
- Author Central page; fix Linktree username; confirm social handles.
- Possible upgrades: Claude Code on desktop + "Claude in Chrome" extension (browser access); Whisper for
  speech-to-text in reels; owner can export Instagram "Saved" via Accounts Center → Download your information.
- Fable 5.1 subagents fail: the account has no usage credits for it.
