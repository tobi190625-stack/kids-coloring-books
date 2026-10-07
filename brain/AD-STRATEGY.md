# Little Crayon Tales: ad strategy (Oct 2026)

Built from 10 earlier research reports (`marketing/ad-research/`) + a new research round on Oct 7 (sources at the bottom).
This file wins over older plans when they disagree.

## 1. The truth about sales
- A sale needs two things: **the right person sees us** (parent or grandparent of a 3-6 year old) and **the Amazon page
  convinces them** (price, cover, reviews, look inside). Views from anyone else don't sell books.
- For coloring/activity books, **Amazon search + Amazon Ads usually sell the most**. Social media is our engine to get
  the first sales, reviews and a brand, and the place where we can win for free.
- So we measure **clicks and sales, not views** (Amazon Attribution, section 7).

## 2. Our angle (say it in every ad)
**"Color the story, then read it."** One big picture + one short sentence per page, ages 3-6.
Every hook speaks to one of three parent motives:
1. **Screen-free calm**: "30 minutes. Zero screens." / "Instead of the tablet..."
2. **Learning to read**: "Can your 4-year-old read this?"
3. **Gift**: "Stocking stuffer that isn't candy" / "Birthday gift for a monster-truck kid"

## 3. Three content engines (every week has all three)
| Engine | What | Why it works | Our formats |
|---|---|---|---|
| **A. Story series** | The book told as a faceless animated story, in parts | Animated story moments are the top format for kids' book accounts in 2026: watch time often 90%+ because people want to know what happens next. Parts make people follow | Bedtime story part 1/2/3, "Color with me: page 1 of 29" |
| **B. Play-along challenge** | The viewer does something | Comments and rewatches push reach | Guess the colors, Find Bella, Can your 4-year-old read this?, Which page would your kid color first? |
| **C. Parent problem / gift** | Talks straight to the buyer | Brings link clicks, not just views | Zero screens, stocking stuffer, gift carousel, "what's inside" |
Mix: about 40% A, 40% B, 20% C. Pinterest and carousels repurpose all three.

## 4. Creative rules for every video (checked before posting)
1. **Frame 1 = the hook.** Moving picture + big caption + spoken line, all saying the same thing, visible from frame one. No logo, no cover splash, no slow fade-in.
2. **Word-by-word subtitles** (our renderer does this). Many viewers watch muted; the caption is the real hook.
3. **Something changes every 2-4 seconds** (new page, color sweep, zoom, new line).
4. **Payoff before the end** (colored page, answer, twist), then the cover + "Color it. Read it." for 2 s max.
5. **Length:** challenges 8-15 s, coloring 15-20 s, story parts 25-35 s.
6. **Ending gives a reason to act:** comment an answer, follow for part 2, or link in bio.
7. **Real book colors only**, kid-safe, no real children's faces, no brand characters.
8. Turn on the platform's **"AI-generated" label** (the art and voice are AI-made). TikTok says the label does not reduce reach; undisclosed AI content gets downranked.

## 5. Platform roles
| Platform | Role | Rule |
|---|---|---|
| TikTok | Discovery + testing hooks fast | 2 videos/day, pin a question comment |
| YouTube Shorts | Discovery, long tail (Shorts keep getting views for weeks) | 2/day, "not made for kids", link in description |
| Instagram | Parents, shares ("send this to a mom...") | 1-2 Reels/day; from 200 followers on a professional account use **Trial Reels** (shown to non-followers first) to test hooks, publish only the winners |
| Facebook | Grandparents + clickable links | Same Reels + link in caption |
| Pinterest | Evergreen search traffic to Amazon; parents plan gifts there | 1 pin/day, search-style titles, video pins of the coloring |
| YouTube long-form (from November) | 5-10 min "bedtime read-along" per book | Parents search these; Shorts feed them |

## 6. How Claude gets very good at making our ads
1. **Every video is a script** (`campaigns/<book>/scripts/*.json` → `tools/render_script.py`): hook, scenes, voice lines.
   Winners get copied and varied, not reinvented.
2. **Hook bank with results** (`marketing/HOOKS.md`): every hook + its 3-day views, watch %, shares, link clicks.
   Claude writes new hooks only as variations of top hooks + 1 wild test per week.
3. **One test per post**: change one variable (hook, format, length, sound, book), write the question in the schedule.
4. **Weekly post-mortem (Sunday)**: top 3 and bottom 3 posts, why (first 2 s, payoff, length), what we change.
5. **Study winners outside our account**: weekly look at outlier videos in kids' coloring/storybook niches
   (vidIQ outliers, TikTok Creative Center); transcribe them (Whisper) and copy the *structure*, never the content.
6. **Upgrade the renderer step by step**: crayon sound effect, character "bounce" on the colored page, page-turn
   transition, end-card animation, then Remotion/HyperFrames for more polish.
7. **Color maps for Rocco + Posy** (5-6 pages each), so all 4 books get colored videos.

## 7. Measurement (what decides everything)
- **Amazon Attribution** (free for KDP authors, advertising.amazon.com → Measurement & Reporting): one tracking link
  per platform per book → we see which platform sells. Put them in Linktree buttons and Facebook/YouTube captions.
  (Pinterest strips Amazon affiliate links, so use plain or Attribution links there.)
- Linktree clicks per book + KDP daily sales.
- Per post: views, % watched, shares/sends, profile visits, link clicks (see DASHBOARD-PLAN.md).
- Rules: judge a post at 3 days, a format after 3 posts per platform. Winner = 2× median → 5 variations next week.
  Loser 3× in a row → retire on that platform.

## 8. The Amazon side (the ads only work if the page converts)
- $8.99, series "Little Crayon Tales" linking all 4 books, A+ content showing "color it → read it", search-phrase keywords.
- **Reviews first**: real parents with free copies, honest reviews only.
- **Amazon Ads** once a book has reviews: auto campaign, bids $0.20-0.40, "dynamic bids – down only", $5/day per book.
  After 14 days, take the search terms that sold → manual exact campaign. Long, specific keywords
  ("monster truck coloring book for kids 3-5"), not "coloring book".

## 9. Amplifiers (fastest way to first sales)
1. **Micro-influencer moms** (10k-50k followers, toddler/preschool/homeschool content): send a free copy, personal
   message referencing one of their posts, ask for an honest Reel/TikTok. Parenting creators, not book reviewers
   (our book stands out there). Goal: 10 creators per month. Needs the KDP account owner to order author copies.
2. **Free printable page** (lead magnet) on Pinterest + bio: "Free Christmas coloring page: Nico's snow angel."
3. **Facebook groups** for preschool/homeschool parents: give value, follow the rules, no spam.

## 10. Next 30 days
| Week | Focus | Target |
|---|---|---|
| Oct 7-11 | Post the planned week; fix IG bio link, YouTube 0-view Shorts; Rocco/Posy links into Linktree | Every post logged with numbers |
| Oct 12-18 | Amazon Attribution links; Rocco/Posy color maps + guess/story videos; first Sunday post-mortem | First 50 link clicks; know top 2 formats |
| Oct 19-25 | 5 variations of each winner; 10 creator pitches; free printable live; Amazon Ads for Nico if it has reviews | First sales attributed to a platform |
| Oct 26-Nov 1 | Double down on the best platform + format; first YouTube long read-along (Nico) | Weekly sales growing; Christmas push ready |

## Sources (Oct 7 research round)
- Kids' book formats, posting cadence: https://animatemystorybook.com/blog/how-to-go-viral-on-tiktok-with-childrens-book.html · https://thekidlitlab.substack.com/p/your-childrens-book-author-guide
- Hooks/retention: https://ugccopilot.ai/blog/viral-hooks-that-convert/ · https://kineclip.com/blog/how-to-write-viral-hooks-short-form-2026/ · https://shortzly.com/blog/short-form-video-retention-strategies
- Bobbie Goods trend: https://knowyourmeme.com/memes/bobbie-goods-coloring-book-tiktok-trend-color-book-challenge
- Pinterest for kids' books: https://janefriedman.com/pinterest-market-childrens-books/ · https://bookbolt.io/how-to-market-low-content-and-no-content-books-to-kids/
- Amazon Attribution: https://aifictionlab.substack.com/p/amazon-attribution-a-no-nonsense · https://indieauthormagazine.com/the-art-of-amazon-attribution/
- Amazon Ads for KDP: https://bookbolt.io/amazon-ads-for-kdp/ · https://www.kdpeasy.com/blog/amazon-ads-kdp-strategy
- Instagram Trial Reels: https://www.inro.social/blog/what-is-a-reel-trial-and-how-does-it-work · https://brandid.app/blog/instagram-trial-reels/
- AI labels: https://shortgen.io/blog/tiktok-ai-content-rules-2026 · https://frameos.studio/blog/ai-content-disclosure-labels
- Creator gifting: https://www.momfluence.co/blog/micro-influencer-moms-the-complete-2026-guide-for-brands · https://www.athomeauthor.com/post/influencers-for-marketing
