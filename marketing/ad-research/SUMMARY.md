# The verdict: what marketing works for Little Crayon Tales (from 10 ad-research reports, Oct 4-5, 2026)

Read this first. Details and proof are in reports 01-10 in this folder.

## The 7 big lessons
1. **Our niche has almost no paid competition.** Nobody advertises "color & read" story books (Meta, TikTok, Google, Snapchat and X all came up empty or nearly so). Bobbie Goods and Coco Wyo grew with **free videos**, not ads. → We win with organic posting first, then boost what already works. (01, 02, 04, 05, 09)
2. **The #1 hook is the parent's problem, not the book.** "Screen-free", "quiet time", "no tablet at the restaurant" and "learning to read" beat "cute coloring book" everywhere. Name the age: "If you have a 3-6 year old…". (01, 02, 03, 10)
3. **The #1 video format is a 15-30 s coloring timelapse that loops.** The page fills with color, ends on the finished page and the cover. Numbered series ("Color with me pg. 3") build followers. No faces or hands needed. (03, 06, 10)
4. **Comment-bait multiplies reach.** "Guess the colors", "Same page, 3 ways: 1, 2 or 3?", "Can your 4-year-old read this?". Comments push the video to more people. (03, 10)
5. **Christmas has already started.** Big brands switched to Christmas ads Sept 15 to Oct 1, and Pinterest needs 45-60 days to warm up. → **Nico gets 2 of every 3 posts until Dec 10.** (01, 02, 06, 10)
6. **Post later.** 15:00-17:00 Czech time is 9-11 AM in the US (parents are at work). → **Post Mon-Fri 19:00-21:00 Czech time, Sat-Sun 15:00-16:00.** (10)
7. **Fix Amazon before paying for ads.** Our books show **$12.00** (plan: $8.99), have 0 reviews, no A+ content and no series, and Benny's author name has a typo. Paid clicks are wasted until this is fixed. The small searches ("reindeer coloring book", "bear coloring book kids", "color and read book") are wide open. (07)

## Formats ranked (what we make from now on)
| Rank | Format | Length | Where | Tool |
|---|---|---|---|---|
| 1 | Coloring timelapse with a question hook ("Guess the colors before the end") | 15-20 s | TikTok, Reels, Shorts, **Pinterest video pin** | `tools/make_ads.py guess` |
| 2 | Same page, 3 ways → "Comment 1, 2 or 3!" | 15 s | TikTok, Reels, Shorts | `tools/make_ads.py three` |
| 3 | Learning-to-read hook: "Can your 4-year-old read this?" (words light up) | 20-30 s | Shorts, Reels, TikTok | `tools/make_ads.py readit` |
| 4 | Carousel: cover + inside pages + "Color it. Read it." (book authors keep these running for months on Meta) | 6 slides | IG, FB (with link), TikTok photo mode | `tools/make_carousel.py` |
| 5 | Pinterest before/after pin with a keyword title | 2:3 image | Pinterest | `tools/make_ads.py pin` |
| 6 | Narrated story slideshow ("bedtime story, part 1") | 30-45 s | TikTok, Reels | `tools/make_slideshow.py` (needs the voice model) |

## Captions
- First line = the search phrase + the hook: "Christmas coloring book for kids: guess the colors before the end".
- Talk like a parent, not a brand. End with "Link in bio" (TikTok/IG), the real Amazon link on Facebook and in the YouTube description, and the Destination link on Pinterest.
- 3-5 hashtags only: mix one parent tag (#screenfree #toddleractivities #learningtoread), one coloring tag (#coloringbook #colorwithme #satisfying), and one season tag (#christmascoloring #stockingstuffers). No #fyp.
- Always say "best with crayons and colored pencils" (paper is printed on both sides). Don't show markers.

## Pinterest titles (keyword formula: subject + "coloring page/book" + "for kids" + age)
- Nico: "Cute Reindeer Christmas Coloring Book for Kids 3-6", "Easy Christmas Coloring Pages for Kids: Color + Read", "Stocking Stuffer for Toddlers: Reindeer Coloring Story Book"
- Benny: "Cute Bear Coloring Pages for Kids 3-6", "Quiet Time Activity Before Bed: Bear Coloring Story Book"
- Rocco: "Easy Monster Truck Coloring Book for Kids 3-6". Posy: "Unicorn Coloring Book for Girls 3-6"

## Paid ads (later, only after the fixes + first reviews)
- **Amazon Sponsored Products** first: $5/day per book, bids $0.25-0.45, long-tail keywords + competitor ASINs (list in 07). Nico from Oct 20-25 until Dec 18-20.
- **Boost the best organic video** (TikTok Promote / Spark Ads, Meta boost): target adults 18+ only, send people to Amazon.
- Skip Snapchat, X and Google ads for now.

## Don'ts
No real kids or kids "saying" they love it · no realistic AI people · no songs outside TikTok's Commercial Music Library · no brand characters · no fake discounts · no asking friends or family for Amazon reviews (Amazon removes them) · no text near the bottom or right edge of videos.

## Fix list for the adult on the KDP account (free, do this week)
1. Check the US list price of Benny and Nico in KDP. Amazon shows **$12.00**. Set **$8.99** (Nico could be $7.99 for Christmas "under $10").
2. Benny's author name typo: the KDP Support request (see PROJECT-MEMORY.md).
3. Create the series **"Little Crayon Tales: Color & Read Story Books"** and add all 4 books.
4. Author Central: claim the books, add a photo and a short bio.
5. A+ content (free): 3 modules showing "Color it → Read it", inside pages, ages 3-6.
6. Add Benny/Nico search phrases to their 7 keyword boxes ("reindeer coloring book for kids", "christmas coloring book for toddlers", "bear coloring book for kids"...).
7. Idea for the next books: single-sided pages (no bleed-through, the page count looks bigger, and the print cost is the same for 24-108 pages). Check the KDP calculator first.
