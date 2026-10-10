# From video to Amazon: the conversion funnel (Oct 10, 2026)

## What the numbers say
- People watch **2-3 seconds** on average → the book and the hook must be on frame 1.
- Best so far: Facebook Reels with **the cover on frame 1 + "Got a little one who loves X?"** (Posy 262, Rocco 201 views).
- TikTok: **0 views on every post** → the account has a problem; posting more there does nothing until fixed.
- Every extra tap loses about half the people: video → profile → Linktree → book → Amazon = 4 taps = almost nobody.
  **Goal: 1 tap from the video to the Amazon page.**

## The path per platform (best first)
| Platform | How people reach Amazon | Taps |
|---|---|---|
| **Instagram + Facebook Reels** (Meta Verified) | **Reel link = the book's own Amazon link** (not Linktree). Facebook: the link also in the caption | **1** |
| IG/FB Stories | Share every Reel to Story with the **Link sticker** → the book's Amazon link | 1 |
| Comments | "Comment ROCCO and we'll send you the link" → reply in DM with the link (by hand now; later ManyChat comment-to-DM, check its free plan). Comments also push reach | 1 (DM) |
| Pinterest | Pin Destination = **the book's Amazon link** (not Linktree) for new pins | 1 |
| YouTube Shorts | Links in Shorts descriptions aren't tappable on phones → end card says **"Search Amazon: Rocco Little Monster Truck"**; description still has the link for desktop | search |
| Linktree (bio) | Buttons named by character with the cover as thumbnail, **today's book first** | 2-3 |
| TikTok | Fix first: Settings → Account → **Account status** (any violation?), business account, no copyrighted sounds, AI label on. Until fixed: 1 post/day max | - |

## What every conversion ad must have
1. Frame 1: the **book cover** + **"Got a little one who loves ___?"** (the parent's kid, not the book).
2. Seconds 3-10: **proof**: the real book opening, real pages, one page colored (what the kid will do).
3. Second 9: the 3 reasons in chips: Color it · Read it · Ages 3-6.
4. Seconds 11-15: **"Tap the link"** + arrow toward where the Reel link sits, voice says it too.
5. Under 16 seconds.
6. One book per ad, and the link goes to **that** book.

## The Amazon page (where the sale happens)
Price $8.99, series, A+ content, reviews: see `amazon/AMAZON-SETUP.md` and the to-do board.

## Measuring it
- Amazon Attribution: one tracking link per book per platform (free, advertising.amazon.com). Use them as the Reel links.
- Every Sunday: Reel link clicks (Meta insights), Linktree clicks, KDP orders per day.

## New renderer (Oct 10): `tools/render_html_ad.py`
Ads are now web pages with CSS 3D + keyframe animations (a 3D book that opens and turns its real pages, a page that
colors itself, chips, CTA), rendered frame by frame in headless Chromium (Playwright), then ffmpeg + Kokoro voice + music.
`python3 tools/render_html_ad.py rocco out.mp4 [--yt]`. New books: add an entry to BOOKS (pages, colored page, hook).
