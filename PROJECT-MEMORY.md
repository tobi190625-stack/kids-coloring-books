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
| 4 | books/005-rocco-monster-truck (copied into main 2026-10-04) | Rocco the Little Monster Truck's Big Jump | 8.5x8.5 | BUILT 2026-10-04, check_kdp passed; final files out/Rocco-INSIDE-manuscript.pdf + out/Rocco-COVER.pdf | LIVE (Oct 6, $8.99) | https://www.amazon.com/dp/B0HLZWLS5J |
| 5 | books/006-posy-the-unicorn (copied into main 2026-10-04) | Posy the Little Unicorn's Rainbow Birthday | 8.5x8.5 | BUILT 2026-10-04, check_kdp passed; final files out/Posy-INSIDE-manuscript.pdf + out/Posy-COVER.pdf (front v2, back v2) | LIVE (Oct 6, $8.99) | https://www.amazon.com/dp/B0HLZF8NMX |
Book 001-leo-the-lion is an old SVG test book, ignore.

## Accounts / links
- Linktree: linktr.ee/littlecrayontalles (note the double L in the username; fix or use exactly).
  Should show the 2 book links FIRST (big "featured" cards), socials below.
- Socials: TikTok, Instagram, YouTube, Pinterest, Facebook Page "Little Crayon Tales" (handles assumed
  @littlecrayontales; confirm exact handles with the owner before using them in links).
- Amazon Author Central: not set up yet.
- Author name (checked 2026-10-04): Nico = "František Chobot" (correct), Benny = "Františkek Chobot" (TYPO).
  Paperback author field locks 72 h after publishing, so the fix is a KDP Support typo request from the
  friend's KDP account (not a new edition). Use exactly "František Chobot" for every future book.
- Own landing page (Netlify-ready): `site/` (drag the folder onto app.netlify.com/drop). Social URLs in it are guesses.

## Ad research verdict (Oct 2026): `marketing/ad-research/SUMMARY.md` (10 platform reports next to it)
- Post Mon-Fri 19:00-21:00 Czech time (= US afternoon), Sat-Sun 15:00-16:00. Nico 2 of every 3 posts until Dec 10.
- Formats: `tools/make_ads.py` guess (coloring timelapse + question), three (same page 3 ways, 1/2/3), readit
  ("Can your 4-year-old read this?"), pin (2:3 before/after with keyword title). Daily packs go in `campaigns/<date>/<platform>/`.
- Amazon showed Benny and Nico at $12.00 (plan $8.99): the owner should check the KDP price. Series: "Little Crayon Tales: Color & Read Story Books".
- **Coloring videos use REAL book colors only** (paint maps). The owner rejected random / 2-crayon / rainbow colors on Oct 5:
  never again ("three" mode = 3 ways is retired).
- Nico bedtime story series: IG+FB got part 1 Mon Oct 5, part 2 Tue; TikTok + YT run 1 day behind (part 1 Tue, part 2 Wed).
  Each part = 4 pages via `tools/make_slideshow.py nico-storyN`; part 3 = next pages (18+), needs new paint maps.

## Owner's Windows laptop (local Claude Code session, since 2026-10-04)
- Project at `C:\Users\tobi1\Documents\GitHub\kids-coloring-books`, a git clone of github.com/tobi190625-stack/kids-coloring-books
  (Git at `C:\Program Files\Git\cmd\git.exe`, sign-in saved). Commit + push to main after work. Online-store branch copy in `..\kids-coloring-books-branches\`.
- Kokoro voice model in `C:\Users\tobi1\kokoro` (tools/voice.py finds it; cloud sessions use /root/kokoro).
- Python: `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` (not on PATH). Always set `PYTHONUTF8=1` first,
  or the tools crash reading book.json (Windows cp1252).
- Claude in Chrome works: Claude can open ChatGPT in its own tab and paste the prompts, then download the images via
  ChatGPT's backend (files in order: title, belongs, pages 1-29, end, then covers).
  Don't poll /backend-api/conversation often: ChatGPT returns 429 "Too many requests"; watch the page text instead.
  ChatGPT often makes 2 versions of a cover; compare them side by side and pick.

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
- `campaigns/WORKPLAN.md` = how many posts where (TikTok 2 videos/day, YT 2 Shorts/day, IG+FB 1 Reel/day, carousels Mon/Thu/Sat, Pinterest 1 pin/day). Daily packs in `campaigns/<date>/` (one folder per platform + CAPTIONS.md); owner says "pack for tomorrow". All videos get voice + soft music: `tools/add_voice.py <video> <music> <out> "0.2:line" ...`.
- **Weekly sheet:** `campaigns/AD-SCHEDULE.xlsx` (one row per post: thumbnail, clickable file link, caption, status). Built by `python3 tools/build_week.py` (edit WEEK in it), which also copies each day's files into `campaigns/<date>/` in posting order + POST-TODAY.md. Owner flow on laptop: pull → open sheet → click file → upload.
- Nico bedtime story series: part 1 (IG/FB Mon, TT/YT Tue), part 2 (IG/FB Tue, TT/YT Wed), part 3 = the end (IG/FB Wed, TT/YT Thu). Configs nico-story1/2/3 in make_slideshow.py.
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
- `animate.py` AI "page comes alive" clips (3-5 s, B&W line art moves): open-source Wan 2.2 on free Hugging Face
  GPUs via gradio_client (laptop GPU = GTX 1050 2 GB, too small to run it locally; no Node.js installed). Chosen Oct 6 over
  Higgsfield-style paid apps / HyperFrames / Remotion (our Python pipeline already does code-made video). Free quota = a few
  clips/day. First test: campaigns/rocco/videos/alive-p10.mp4 (seed 718782066), looked clean. Check frames; label as AI when posting.
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
- Rocco + Posy are LIVE (links above, both on Linktree): make their campaigns (tools/new_campaign.py + ad pack); launch week = 1 video a day each.
- KDP fix list for Benny/Nico (price $8.99, series, Author Central, A+, keywords): see marketing/ad-research/SUMMARY.md.
- Author Central page; fix Linktree username; confirm social handles.
- Possible upgrades: Claude Code on desktop + "Claude in Chrome" extension (browser access); Whisper for
  speech-to-text in reels; owner can export Instagram "Saved" via Accounts Center → Download your information.
- Fable 5.1 subagents fail: the account has no usage credits for it.
