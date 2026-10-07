# Ad playbook: how we get very good at ads

Being "good at ads" is not about one genius video. It's a loop: **make → post → measure → keep the winners → make variations of the winners.** The team that runs the loop fastest wins.

## 1. Every post is a test with ONE question
Before making a video, write one line in the schedule: *"Testing: does a question hook beat a statement hook?"*
Change one thing at a time:
| Variable | Options to test |
|---|---|
| Hook (first 1-2 s, text + voice) | question ("Can you guess...?"), parent pain ("30 minutes. Zero screens."), age call-out ("If you have a 4-year-old..."), challenge ("Find Bella before the end"), cliffhanger ("part 1") |
| Format | coloring timelapse, story in parts, read-along, slideshow, carousel, before/after |
| Length | 8-12 s vs 15-20 s vs 30 s |
| Sound | voice + music vs music only vs trending sound |
| Book / season | Christmas (Nico) vs all-year (Benny, Rocco, Posy) |
| Ending | "Link in bio" vs question to comment vs "part 2 tomorrow" |

## 2. Score every video BEFORE posting (5 checks, 0-2 points each, post only 7+)
1. **First second**: something moves or a question appears immediately (no logo, no slow intro).
2. **Hook**: names the parent's problem or the kid's age, or asks a question.
3. **Payoff**: the finished colored page / the answer / the twist comes before the end.
4. **Book visible**: the cover and "color it, read it" appear, and the subtitles say what the book is.
5. **Next step**: comment, follow for part 2, or link in bio.

## 3. The hook bank (grows every week)
Keep `marketing/HOOKS.md`: every hook we used + its 3-day views, watch % and clicks. Reuse the winners with new pages.
Starting list from the research:
- "Guess the colors before the end" · "Can your 4-year-old read this?" · "30 minutes. Zero screens."
- "Bedtime story, part 1" · "Can you find Bella?" · "Stocking stuffer that isn't candy"
- "If you have a 3-6 year old, try this instead of the tablet" · "Which one would your kid pick?"

## 4. Formats ranked (update every Sunday from the dashboard)
Current ranking is research-based (not our data yet):
1. Coloring timelapse with a question hook
2. Story in parts (cliffhanger → follows)
3. Read-along ("can your 4-year-old read this?")
4. Parent-problem slideshow ("zero screens")
5. Carousel (gift angle) + carousel video
After 2 weeks, replace this list with OUR numbers.

## 5. Make variations, not new ideas
When a video wins: keep the format and change ONE thing: a new page, a new book, a new hook wording, or a new length.
One winner → 5 variations → spread over 5 days and 4 platforms. This is how small accounts grow.

## 6. Production speed (so 4 books × 4 platforms stays doable)
- Every video is a **script file** (`campaigns/<book>/scripts/*.json`) rendered by `tools/render_script.py`.
  New ad = copy a winning script, change pages/lines, render. Minutes, not hours.
- One page with a color map (`marketing/paint/`) → guess-the-colors video + read-along + pin + carousel slide.
  **Make color maps for 5-6 pages of Rocco and Posy** so they get colored videos too.
- Batch on Sunday: Claude renders the whole week (`tools/build_week.py`), the owner schedules in one sitting.

## 7. Don'ts (protect the accounts)
No real kids' faces, no fake reviews or fake "my kid loves it", no brand characters/trademarks, no copyrighted songs
outside platform libraries, no buying followers, no identical video posted twice on the same platform.
