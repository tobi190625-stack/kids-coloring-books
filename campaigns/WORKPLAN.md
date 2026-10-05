# Workplan: how many posts, where, every day

Based on the ad research (`marketing/ad-research/10-organic-shortform.md`, `06-pinterest.md`):
1 video a day on every platform is the base, TikTok and Shorts can take 2, carousels 3x a week, Pinterest 1 pin a day.
Being consistent (same time, every day) matters more than posting a lot.

## Every day (about 45 min)
| Platform | Videos | Carousels | Extra |
|---|---|---|---|
| **TikTok** | **2** (19:00 and 21:00) | **+1 photo carousel** on Mon, Thu, Sat | pin a question comment under video 1 |
| **YouTube Shorts** | **2** (the `yt-` files) | YouTube has no carousels. A few times a week one of the 2 Shorts is a carousel **video** (`carousel-...-voice.mp4`), never a 3rd | - |
| **Instagram** | **2 Reels**: one per live book (19:00 + 21:00) | **+1 carousel post** on Mon, Thu, Sat (20:00) | Story with Link sticker after every post |
| **Facebook** | **2 Reels** (the same 2 as Instagram) | **+1 carousel post** on Mon, Thu, Sat | post via Meta Business Suite = IG + FB in one go; Story with link |
| **Pinterest** | **1 pin** (video pin or image pin) | - | Destination link = Amazon |

**Times (Czech):** Mon-Fri 19:00-21:00 · Sat-Sun 15:00-16:00 (= when US parents are on their phones).

## Per week
| | TikTok | YouTube Shorts | Instagram | Facebook | Pinterest |
|---|---|---|---|---|---|
| Videos | 14 | 14 | 14 Reels | 14 Reels | - |
| Carousels | 3 (photo posts) | 2-3 (as video, inside the 14) | 3 | 3 | - |
| Pins | - | - | - | - | 7 |

## Which book?
- **Nico (Christmas) gets 2 of every 3 posts until Dec 10.** Benny gets the rest.
- A book that just went live (Rocco, Posy) gets **1 video a day for its first 7 days** (it takes the 2nd TikTok/Shorts slot).
- Dex: on hold.

## What "video" and "carousel" mean here
- **Video** = a 12-25 s vertical video with voice + soft music (guess the colors, same page 3 ways, can they read this, 30 minutes zero screens, story slideshow).
- **Carousel (photo)** = 6 slides posted as a photo post (Instagram/Facebook carousel, TikTok photo mode). Swipe = more time on the post = more reach.
- **Carousel video** = the same 6 slides turned into a video with voice (`carousel-...-voice.mp4`). Post it as a Short / Reel on another day than the photo version.

## Rule: real book colors only
Every coloring video uses the page's color map (`marketing/paint/<book>-p<N>.json`), so it looks like the cover and the book.
No random, rainbow or "2-crayon" colors (tested Oct 5, the owner said it looks bad). "Same page, 3 ways" is retired for that reason.

## Formats to rotate (from the research, best first)
1. Guess the colors before the end (coloring timelapse)
2. Story slideshow in parts (bedtime story part 1, 2, 3...: "follow for part 2")
3. Can your 4-year-old read this? (read-along)
4. Parent problem hook: "30 minutes. Zero screens." (slideshow + voice)
5. Carousel / carousel video (gift angle for Nico)
6. Story slideshow read aloud
Never the same format twice in a row on the same platform.

## How the packs get made
Every evening (or in the morning) tell Claude **"pack for tomorrow"**. Claude makes `campaigns/<date>/` with one folder per
platform, the files numbered in posting order, and a CAPTIONS.md in each. You post, then say "posted".
