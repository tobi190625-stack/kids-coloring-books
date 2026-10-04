# Campaigns: one folder per book, everything for its ads in one place

```
campaigns/
  README.md            <- you are here (how the system works)
  WEEKLY-SYSTEM.md     <- the repeatable week: 2 new books + marketing every day
  THIS-WEEK.md         <- the actual day-by-day plan for the current week (what to post, which file, which caption)
  _TEMPLATE/CAMPAIGN.md  <- copied for every new book (tools/new_campaign.py does it)
  benny/               <- Benny the Bear (LIVE)
    CAMPAIGN.md        <- links, every ad file + its ready-to-paste caption, posting log, results
    images/            <- pins (1000x1500) + square ad
    carousel/ carousel-2/ carousel-gift/   <- 6-slide carousels (4:5)
    videos/            <- coloring videos, slideshows, Reels (yt-... = YouTube version with "Link in bio")
  nico/                <- Nico the Reindeer (LIVE, Christmas book: push until Dec 15)
  dex/                 <- Dex the Dinosaur (ON HOLD: owner said do not post it)
```

Shared things stay in `marketing/`: brand pictures (profile picture, Facebook cover, YouTube banner),
`music/`, `paint/` (color maps for the coloring videos), `MASTER-PLAN.md` (how each account was set up),
`ad-scripts.md` (video ideas).

## The 3 rules
1. **Every ad file has its caption next to it** in that book's CAMPAIGN.md. Copy, paste, post.
2. **After posting, tick it in the posting log** (or just tell Claude "posted X on TikTok" and Claude ticks it).
3. **Every Sunday, write the numbers** (views, sales) in the Results table. More of what works, stop what doesn't.

## Commands Claude runs for a new book (owner never needs to)
```
python3 tools/new_campaign.py books/<NNN-book>          # makes campaigns/<slug>/ + CAMPAIGN.md from the template
python3 tools/make_marketing.py books/<NNN-book>        # pins + square ad
python3 tools/make_carousel.py campaigns/<slug>/carousel.json
python3 tools/make_video.py books/<NNN-book> <page> [--yt]   # coloring video (needs marketing/paint/<slug>-p<N>.json)
python3 tools/make_slideshow.py <config>                # colored pages + voiceover + music
python3 tools/carousel_video.py campaigns/<slug>/carousel <music.wav> campaigns/<slug>/videos/carousel-reel.mp4
```
