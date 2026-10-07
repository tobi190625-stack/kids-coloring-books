# Handoff: state of the work (Oct 7, 2026)

## Books
| Book | Status | Amazon |
|---|---|---|
| Nico the Little Reindeer's Snowy Day | live | https://www.amazon.com/dp/B0HLVTTK7T |
| Benny the Bear's Cozy Day | live | https://www.amazon.com/dp/B0HLVSLXK7 |
| Rocco the Little Monster Truck's Big Jump | published Oct 5-6 | **link not in the repo yet: get it from KDP Bookshelf > View on Amazon** |
| Posy the Little Unicorn's Rainbow Birthday | published Oct 5-6 | **link not in the repo yet** |
| Dex the Little Dinosaur | built, NOT for sale | - |

## What exists on main (all pushed)
- `campaigns/AD-SCHEDULE.xlsx` — whole week Oct 5-11: one row per post, thumbnail, clickable file link, caption, status.
  Built by `python3 tools/build_week.py`, which also copies each day's files into `campaigns/<date>/` + POST-TODAY.md.
- `campaigns/WORKPLAN.md` — posting rules (TikTok 2/day, YT 2/day, IG+FB 2 Reels/day, carousels Mon/Thu/Sat, 1 pin/day).
- `marketing/ad-research/` — 10 research reports + SUMMARY.md (formats, hooks, times, Amazon fixes).
- Video tools: `make_ads.py` (guess-the-colors, read-along), `make_slideshow.py` (bedtime story parts 1-3, screen-free),
  `add_voice.py` (voice + music on any video), `render_script.py` (**video from a JSON script, frame by frame, with
  word-by-word subtitles + .srt/.txt transcript**). Scripts live in `campaigns/<book>/scripts/*.json`.
- New this week: Nico bedtime story parts 1-3, 5 guess-the-colors videos, Benny read-along, Nico story carousel,
  "How Nico builds a snowman" (script video), launch videos for Rocco and Posy (`campaigns/rocco|posy/videos/new-book.mp4`).

## Open problems (fix these first)
1. Rocco + Posy Amazon links: put them in PROJECT-MEMORY.md, Linktree, and the Oct 6 captions (placeholders ROCCO-LINK / POSY-LINK).
2. Instagram: Linktree link is typed in the bio text (not clickable) → move it to Edit profile > Links.
   Nico "guess the colors" Reel posted twice on Oct 5 → archive one. The phone app is a **beta build** → leave the beta / reinstall from Play Store.
3. YouTube: 6 Shorts from Oct 4 have 0 views → check Visibility (Public) + Audience ("not made for kids").
   Duplicates: "Found You, Bella!" and "Watch Nico the Reindeer Come to Life!" uploaded twice.
   Scheduling: the Oct 5 Nico Short went public in the morning instead of 19:00.
4. Meta Business Suite failed on desktop browser, works on mobile app.
5. Amazon showed $12.00 instead of $8.99; series "Little Crayon Tales: Color & Read Story Books" to create; Benny's author name typo (KDP support).
6. The GitHub repo is public: make it private (Settings > General > Danger zone > Change visibility).

## First numbers (Oct 4-6, tiny new accounts)
- YouTube: Nico guess-the-colors Short 266 views (best), Benny can-they-read 103.
- Instagram: Reels 5-31 plays each, 1 follower.
Too early to judge formats: need ~2 weeks of data (see DASHBOARD-PLAN.md).
