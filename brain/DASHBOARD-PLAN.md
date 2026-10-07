# Dashboard plan: every platform + Amazon in one place

Goal: every Sunday, answer three questions in 10 minutes:
1. Which **formats and hooks** bring views AND link clicks? → make more of them.
2. Which posts flopped? → stop that format after 3 tries.
3. Are any of the views turning into **book sales**?

## The one rule
Views alone lie. Track the chain: **views → watch time / completion → profile visits → link clicks → Amazon sales.**
A video with 300 views and 6 link clicks beats one with 3,000 views and 0 clicks.

## Data we need, per post
| Field | Where it comes from |
|---|---|
| date, time, platform, book, format, hook (first words), file, caption | we already have it in AD-SCHEDULE.xlsx |
| views / plays | each platform's analytics |
| avg. watch time + % watched to the end | TikTok Studio, YouTube Studio, Instagram insights |
| likes, comments, shares/sends, saves | all platforms |
| profile visits | TikTok, Instagram |
| link clicks | Linktree analytics (per book link), Facebook link clicks, Pinterest outbound clicks |
| sales | KDP Reports (units per book per day) |

## Where the numbers come from (from easiest to hardest)
1. **Manual weekly export (start here, free, works today).** Every Sunday, download or screenshot:
   - TikTok Studio > Analytics (export works on desktop)
   - YouTube Studio > Analytics > Advanced > Export
   - Meta Business Suite > Insights > Content (export CSV)
   - Pinterest Analytics > Export
   - Linktree > Analytics
   - KDP > Reports > Orders
   Claude reads the files/screenshots and fills `data/posts.csv` + `data/sales.csv`.
2. **One free tool that collects everything:** a social media manager like **Metricool** (has a free tier; check the
   current limits) connects TikTok, Instagram, Facebook, YouTube and Pinterest, schedules posts AND shows analytics in
   one place, with CSV export. This would also fix our scheduling problems (Business Suite on desktop, YouTube morning post).
3. **Amazon Attribution** (free Amazon Ads tool, available to KDP authors in the US marketplace — check it is enabled
   on the account): gives a tracking link per platform, so we see clicks → Amazon page views → **sales per platform**.
   This is the only way to know which platform actually sells books. Put these links in Linktree and Facebook/YouTube captions.
4. **Official APIs (later, only if 1-3 are not enough):** YouTube Analytics API, Meta Graph API (Instagram/Facebook
   insights), TikTok Display/Research API, Pinterest API. Needs developer apps and keys from an adult account. Not worth it yet.

## The dashboard itself
- `data/posts.csv` (one row per post per platform) + `data/sales.csv` (one row per book per day).
- `tools/build_dashboard.py` → `dashboard.html` (a single page that opens in any browser, no server):
  - Top: this week vs last week: views, link clicks, sales, followers.
  - **Format leaderboard**: average views, completion %, link clicks per 1,000 views, by format (guess colors, story part, read-along, screen-free, carousel...).
  - **Hook leaderboard**: same, by first line / on-screen hook.
  - Per book: posts, clicks, sales (Nico vs Benny vs Rocco vs Posy).
  - Per platform: where clicks come from.
  - "Winners" list (2x the median views) → re-post with a new hook in 7 days. "Losers" list → retire after 3 tries.
- Later: the same data as a page in Obsidian (Dataview table), see OBSIDIAN.md.

## Decision rules (write them down now, so we don't guess later)
- Judge a post after **3 days**, a format after **3 posts per platform**, a platform after **4 weeks**.
- Winner: ≥ 2× median views OR ≥ 2× median link clicks per 1,000 views → make 3 more like it this week.
- Loser: < 0.5× median 3 times in a row → retire the format on that platform.
- Watch time < 50% on a 15-20 s video → the hook or the first 2 seconds are wrong; change only the hook and re-test.
- Paid ads only on a post that already won organically, and only after the book has sales or reviews.

## Build order
1. Now: add columns to AD-SCHEDULE.xlsx: views (3 days), watch %, shares, saves, profile visits, link clicks.
2. Week 2: `data/*.csv` + `tools/build_dashboard.py` → `dashboard.html`.
3. Week 3: Metricool (or similar) + Amazon Attribution links.
4. Month 2+: APIs only if needed.
