# The weekly system: 2 new books + marketing every day

Time for you: about 30-45 min a day. Claude does the writing, building, checking and ad-making.

## Book production (2 books a week)
| Day | You | Claude |
|---|---|---|
| **Mon** | Say "new week". Pick 2 ideas or let Claude pick (one for girls, one for boys works well). | Writes both stories, the ChatGPT picture prompts, cover prompts and KDP listings. |
| **Tue-Wed** | Make the pictures in ChatGPT (2 x 32 images + 2 covers). Send the zips. | Sorts, cleans, builds both books, checks every page, sends the 2 inside PDFs + 2 cover PDFs + KDP answers. |
| **Thu** | Upload both books to KDP (your friend's account). Own free ISBN for each book. Same author name as the other books. | Fixes anything KDP complains about. |
| **Fri-Sun** | KDP review (up to 72 h). When live, send Claude the amazon.com/dp/... links. | Makes the full ad pack (below) into `campaigns/<book>/`, fills its CAMPAIGN.md, adds the book to THIS-WEEK.md, Linktree note, memory file. |

## The ad pack every book gets (same every time)
- 3 Pinterest pins + 1 square ad (`images/`)
- 3 carousels: story, "2", gift (`carousel*/`), each also as a Reel video
- 4-5 coloring videos (TikTok/Reels version + YouTube "Link in bio" version)
- 1-2 slideshows with voiceover + soft music
- All captions ready to paste in CAMPAIGN.md (TikTok, YouTube, Instagram, Facebook, Pinterest)

## Daily marketing
**See `WORKPLAN.md`** (from the ad research): TikTok 2 videos/day, YouTube 2 Shorts/day, Instagram + Facebook 1 Reel/day,
carousels Mon/Thu/Sat, Pinterest 1 pin/day, Stories with a link after every IG/FB post.
Times (Czech): Mon-Fri 19:00-21:00, Sat-Sun 15:00-16:00. Nico gets 2 of every 3 posts until Dec 10; new books get a launch week.
Every video gets voiceover + soft music (`tools/add_voice.py`, `tools/make_slideshow.py`). Each day's files are in `campaigns/<date>/`.

## Sunday check (15 min)
1. KDP Reports > units sold per book. Write it in each CAMPAIGN.md Results table (or send Claude a screenshot).
2. The 3 best posts of the week (views/saves). Claude makes more in that format.
3. Claude writes next week's THIS-WEEK.md.

## Money rules
- Organic (free) first. Paid ads only after a book has sales or reviews: $5/day tests, the friend's card.
- Stop any ad after $30 with clicks but no sales.
- Amazon Ads (Sponsored Products, auto, $5/day) 2-3 weeks after a book goes live.
