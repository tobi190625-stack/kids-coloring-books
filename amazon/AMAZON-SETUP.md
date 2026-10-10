# Amazon setup: make the 4 books sell better (do this on the KDP account)

Claude can't log into KDP. Everything below is ready to copy. Pictures are in `amazon/aplus/<book>/`.
Order: **1 → 6**. Steps 1-3 take about 30 minutes, A+ about 15 minutes per book.

| Book | Amazon |
|---|---|
| Nico the Little Reindeer's Snowy Day | https://www.amazon.com/dp/B0HLVTTK7T |
| Benny the Bear's Cozy Day | https://www.amazon.com/dp/B0HLVSLXK7 |
| Rocco the Little Monster Truck's Big Jump | https://www.amazon.com/dp/B0HLZWLS5J |
| Posy the Little Unicorn's Rainbow Birthday | https://www.amazon.com/dp/B0HLZF8NMX |

---

## 1. Fix Benny's author name FIRST (blocks the series)
A series needs **the exact same author name** on every book. Benny says "Františkek Chobot" (typo), the others "František Chobot".
KDP → **Help → Contact Us → Paperback → Making changes to your book → Update author name**. Paste:
```
Hello, my paperback "Benny the Bear's Cozy Day" (ASIN B0HLVSLXK7) was published with a typo in the author name: "Františkek Chobot". The correct name is "František Chobot", the same as on my other books (ASIN B0HLVTTK7T, B0HLZWLS5J, B0HLZF8NMX). Could you please correct it so all my books link to the same author? Thank you.
```
Until it's fixed, create the series with Nico, Rocco and Posy, and add Benny when support confirms.

## 2. Create the series
KDP **Bookshelf** → next to **Nico** click **⋯** → **Add to series** → **Create new series**:
- **Series title:**
```
Little Crayon Tales: Color & Read Story Books
```
- **Reading order:** choose **Unordered** (the books are separate stories; any one can be read first)
- **Language:** English
- **Series description:**
```
Little Crayon Tales are story books your child colors AND reads. Every page has one big, bold picture with thick, easy lines and one short sentence in BIG letters, so kids ages 3-6 color the story while they learn to read it.

Meet the friends:
• Nico the Little Reindeer: a snowy Christmas adventure with a snowman, a sled and a cozy bedtime
• Benny the Bear: a cozy day of pancakes, a kite, hide and seek and a bedtime story
• Rocco the Little Monster Truck: the smallest truck at the show learns to be brave and makes the biggest jump
• Posy the Little Unicorn: the rainbow lost its colors on Posy's birthday, and her friends help bring it back

Perfect for preschool and kindergarten, quiet time, car rides, birthdays, Christmas stockings and Easter baskets. Best with crayons and colored pencils.
```
Then on **Rocco** and **Posy** (and Benny after the fix): **⋯** → **Add to series** → pick the series. Click **Publish series**. The series page shows up in a few days.

## 3. Price + keywords + categories (each book: ⋯ → Edit paperback details / rights & pricing)
**Price:** US **$8.99** for all four (Amazon showed $12.00 for Nico and Benny). Nico can be $7.99 until Christmas ("under $10").

**Keywords (7 boxes) — Nico**
```
christmas coloring book for kids ages 3-5
reindeer coloring book for toddlers
stocking stuffers for kids 3-6
winter coloring book preschool
learn to read christmas book for kids
color and read story book
christmas activity book kindergarten
```
**Keywords — Benny**
```
bear coloring book for kids ages 3-5
cute animal coloring book toddlers
easter basket stuffers for kids 3-6
bedtime story book for preschoolers
learn to read coloring book kindergarten
color and read story book
quiet time activity book for toddlers
```
Rocco and Posy already have good keywords (in their `listing.md`).

**Categories (3 per book):**
- Nico: Coloring · Holidays & Celebrations › Christmas & Advent · Animals › Deer
- Benny: Coloring · Animals › Bears · Bedtime & Dreams
- Rocco: Coloring · Cars, Trains & Things That Go › Trucks · Growing Up › Friendship
- Posy: Coloring · Fairy Tales, Folk Tales & Myths (Unicorns if offered) · Holidays & Celebrations › Birthdays

## 4. Author Central (author.amazon.com, log in with the KDP account)
1. **Claim the books:** Books → Add more books → search each title → "Yes, this is my book".
2. **Biography** (one person's name is on the books, so write it as the brand):
```
František Chobot writes Little Crayon Tales, color-and-read story books for children ages 3-6. Each book tells a simple, cozy story with one big picture and one short sentence on every page, so little ones can color the story and read it at the same time. The stories are about friendship, being brave and helping others: a snowy Christmas with Nico the reindeer, a cozy day with Benny the bear, a big jump with Rocco the monster truck and a rainbow birthday with Posy the unicorn.
```
3. **Photo:** use `marketing/profile-picture.png` (the brand picture) if no author photo.
4. **Editorial reviews:** later, when real reviewers or teachers send quotes. Never invent them.

## 5. A+ Content (KDP → Marketing → A+ Content Manager → Start creating A+ content)
Make one A+ document per book, with these 4 modules, in this order. Images: `amazon/aplus/<book>/`.

**Module 1 — "Standard Image Header With Text"**: image `1-header-970x600.png`
- Headline: `Color it. Then read it.`
- Body:
```
Every page has one big, bold picture to color and one short sentence in BIG, easy letters. Your child colors the story and reads it at the same time. Made for ages 3-6.
```

**Module 2 — "Standard Three Images & Text"**: images `2-step1-color`, `2-step2-read`, `2-step3-series`
- 1: Headline `1. Color the big picture` · Body `Thick, easy lines made for little hands. Best with crayons and colored pencils.`
- 2: Headline `2. Read the sentence` · Body `One short sentence per page in big letters, perfect for early readers.`
- 3: Headline `3. Collect the series` · Body `Nico the Reindeer, Benny the Bear, Rocco the Monster Truck and Posy the Unicorn.`

**Module 3 — "Standard Image & Light Text Overlay"** (or "Standard Image Header" if not offered): image `3-banner-970x300.png`
- Headline: `What's inside` · Body: `Big pages · easy thick lines · one sentence per page · a "This book belongs to" page`

**Module 4 — "Standard Comparison Chart"** (cross-sells the other 3 books):
- Columns (product = ASIN, image = `4-compare-<book>-150x300.png`): Nico B0HLVTTK7T · Benny B0HLVSLXK7 · Rocco B0HLZWLS5J · Posy B0HLZF8NMX. Mark the current book as "highlighted".
- Rows:

| Row | Nico | Benny | Rocco | Posy |
|---|---|---|---|---|
| Story | Snowy Christmas day | Cozy day with a friend | Brave little monster truck | Rainbow birthday |
| Best for | Christmas, stocking stuffer | Bedtime, Easter, any day | Truck and car fans | Unicorn and rainbow fans |
| Pages to color | 29 | 27 | 29 | 29 |
| Ages | 3-6 | 3-6 | 3-6 | 3-6 |

Applicable ASINs: the book itself. Submit → Amazon reviews it in up to 7 days.

## 6. Reviews (the biggest sales lever after the page itself)
- Give copies to real parents (family, friends of family, a preschool teacher) and ask for an **honest** review.
- Never buy reviews, never review your own book, no family members with the same address (Amazon removes those).
- Put a small "If your little one enjoyed this book, a review helps us a lot" line on the last page of the next print update.

## After all this: Amazon Ads (only once a book has reviews)
Sponsored Products, auto campaign, $5/day per book, bids $0.20-0.40, "dynamic bids - down only". After 14 days move the search terms that sold into a manual exact campaign.
