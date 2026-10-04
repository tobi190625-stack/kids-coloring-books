# 09 – Snapchat Ads Gallery + X Ads Repository + Parent Language

Research date: 2026-10-04. Read-only. No logins and no downloads.

---

## 1) TL;DR (5 lines)

1. **Snapchat: we found zero coloring-book or kids-activity-book ads.** We checked about 77 advertiser names through Snap's official Ads Library API. Crayola, Melissa & Doug, Lovevery, Usborne, Scholastic, Bobbie Goods, Yoto and tonies had **no Snap ads at all**. Toy sellers (Smyths, Ravensburger, LEGO) advertise toys to 18+ adults, not books.
2. **X (Twitter): the library cannot be searched by keyword.** You pick 1 advertiser + 1 EU country + dates, and X makes a CSV file. Kids' books are a weak fit for X anyway: about 63-64% of users are male and the platform is about news and opinion, not parenting.
3. **Verdict: skip Snapchat and X for now.** That nobody advertises coloring books there is a signal: these are not places where parents shop for kids' books. Keep TikTok, Pinterest, IG/FB Reels and YouTube Shorts.
4. **Reddit was blocked for our tools** (browser, fetch and search all refused reddit.com). We collected real parent language from Mumsnet threads, Amazon reviews and "Customers say" summaries, and parenting/teacher blogs instead.
5. **The strongest parent words for us:** "big, simple pictures", "not too detailed", "screen-free", "keeps them busy", "fine motor skills", "learning to read", "something to do at restaurants/travel", and "not tat" for gifts. The biggest objections: thin paper or bleed-through, too-hard pictures that frustrate small kids, "it's just scribbles anyway", and cheap-feeling AI/KDP books.

---

## 2) Snapchat ads found (Snap Ads Gallery / EU ads library)

**How the tool works:** adsgallery.snap.com only searches by **exact paying-advertiser name** ("must be exact spelling"). There is **no keyword search**, so we could not type "coloring book". It only shows ads delivered in the **EU and some other places in the last 12 months**. We used the same public API the page uses (`adsapi.snapchat.com/v1/ads_library/ads/search`), with a delay between requests (it rate-limits).

**Names we checked that had ZERO Snap ads:** Crayola, Crayola LLC, Crayola Europe, Melissa & Doug, Lovevery/LOVEVERY, Usborne, Usborne Publishing, Scholastic, Bobbie Goods, Yoto, tonies, Toniebox, Faber-Castell, Staedtler, STABILO, Vertbaudet, Lingokids, ABCmouse, Djeco, Orchard Toys, Penguin Random House, HarperCollins, Wonderbly, Hooray Heroes, Librio, Kidly, JoJo Maman Bebe, Galt Toys, Water Wow, Aqua Doodle, Tombow, Carioca, Giotto, Play-Doh, Fisher-Price, VTech, LeapFrog, Janod, Learning Resources, Little Passports, KiwiCo, and others.

**Advertisers that DO run Snap ads (first page of 10 ads checked):**

| Advertiser (paying name) | What they advertise on Snap | Format | Dates seen | Reach (impressions) | Kids' coloring/books? |
|---|---|---|---|---|---|
| Ravensburger (Poland, via Empik) | GraviTrax marble runs; "Small bricks. Big possibilities." | Video + photo Snap ads, web-view | May 2026 and Sep 2026 | 23k to 1.96M per ad | No (toys and STEM, aimed at older kids/teens) |
| Smyths Toys | LEGO Disney WALL-E, LEGO One Piece, Super Mario, Monster High, Topps | Video Snap ads | Dec 2025 to Aug 2026 | Up to 4.5M per ad | No. Targets **18+ / 20+ / 25+** (adults, collectors, gift buyers) |
| LEGO ("Lego") | Fall shopper campaign (FR/BE), "Rejoignez-nous!" | Video, web-view | Oct 2025 | about 322k | No |
| Disney | ESPN/UEFA tune-in and similar | Video | 2025 | about 92k | No |
| Panini (DE) | Sticker albums ("now in stores") | Story video ads | May-Jun 2026 | 0.18M to 2.8M | No (stickers, football fans) |
| Mattel | UNO card game | Video | 2026 | n/a | No |
| Cultura (FR) | "Books to enjoy over the holidays" for **adults** at Christmas | Image | Dec 2025 | about 10k | Books, but adult, not kids |
| bol.com (NL) | "You can learn to concentrate!" back-to-school/study | Story ads | Aug-Sep 2026 | 0.2M to 0.93M | No (students) |
| Storytel / BookBeat | Audiobook free trials, UGC-style creator videos | UGC video | 2026 | 6 to 36k (small) | Books, but adult audiobooks |
| Montessori-Spiele (small shop) | "-60% on plush toy" (Spanish) | Single image/video website ad | Dec 2025 | **2,038** (tiny) | Kids' toy, but almost no reach |
| Amazon, Etsy, Temu, AliExpress, Thalia, Fnac, Audible | General shopping/brand ads | Mixed | 2025-26 | various | None about kids' coloring books in the first 10 ads |

**Warning about name matches:** exact-name search finds *any* account with that name. "Edding" returned a casino bonus ad, "Pelikan" a student offer, and "Action"/"Hape" were unrelated companies. Snap results by brand name are not always that brand.

**What this tells us:**
- On Snap, **even big kids' brands (Crayola, Melissa & Doug, Lovevery, Usborne) do not advertise.** Toy retailers that do advertise target **adults 18-25+**, so they sell to collectors, teens and gift-buyers, not parents of 3-year-olds.
- EU law (the DSA) blocks profiling-based ads to minors, so kids' brands talk to adults on Snap. Snap's adults skew very young (most users are under 35, the biggest group is 18-24), which mostly means people *without* preschoolers.
- The only tiny kids' shop we saw (Montessori-Spiele) got about 2k impressions. No real activity.

---

## 3) X (Twitter) ads found (X Ads Repository, EU DSA library)

**How the tool works:** ads.twitter.com/ads-repository needs you to choose **one advertiser account** (from a dropdown), **one EU country** (no "all EU"), and a date range. Then "Create report" makes a **.csv download**. There is **no keyword search** and nothing shows on the page, so we could not search "coloring book". There is also a giant "Commercial Communications CSV" of the full dataset.

| Advertiser | Result |
|---|---|
| @Crayola | Account exists in the advertiser dropdown. We did **not** make the CSV report, because downloading files was outside our read-only rules. |
| Keyword search ("coloring book", "kids activity", "toddler", "Bobbie Goods", "Christmas gift kids") | **Not possible.** The repository has no keyword search. |

**What we know about X from other sources:**
- About 63-64% of X's ad audience is male, and about 70% of users are 18-34. Teens are about 2%.
- X is used for news, sports, politics and tech. It is not a "shopping for my toddler" place.
- In other parts of this research (Meta, TikTok, Google), kids' coloring-book sellers advertise on Meta, TikTok, Pinterest and Amazon. **Nobody in this niche is known for X ads.**
- The EU has criticized X's ad repository for being hard to use and incomplete. That fits what we saw.

**X ads found for our niche: none we could verify (0).**

---

## 4) Are these platforms worth it for us?

**Snapchat: NO (for now).**
- No competitors are there, and that's not because the space is "free". It's because the audience is wrong: mostly 13-24, and our buyer is a 25-40-year-old parent (mostly moms) or a grandparent.
- Snap needs vertical video **with faces/people** to work. We cannot film kids or hands.
- Snap Ads send people to a website. We sell on Amazon, so every click goes Snap → Amazon. Small budgets get almost no learning (see the 2k-impression shop).
- One small exception for later: Snap could reach **young aunts/uncles/older siblings** buying a cheap Christmas gift. It's not worth testing before TikTok and Pinterest are working.

**X: NO.**
- Male-heavy, news-focused, and almost no parent-shopping behavior. Its library is so hard to use that we can't even learn from competitors.
- Organic posting on X is also low value for a picture-book brand. Pinterest beats it by far.

**Where to put the effort instead:** Pinterest (moms search "toddler coloring pages", "Christmas activities for kids"), TikTok/IG Reels (flip-throughs, "color with me", page reveals), YouTube Shorts, and Amazon itself.

---

## 5) Parent language: top 20 phrases, desires and pain points

Sources: Mumsnet threads (colouring ages, "colouring books are no good?", restaurants/planes, toddlers and screens, stocking fillers, "not tat"), Amazon reviews and Amazon "Customers say" summaries for 12 top kids' coloring books (Christmas, monster truck, unicorn, toddler, Kumon), the "color and read" emergent-reader teacher blog, and parent buying guides. Reddit itself was blocked. Short direct quotes are in quotation marks. Everything else is paraphrased.

**What parents WANT (desires):**
1. **"Big, simple pictures"** with thick, bold lines. This shows up in nearly every positive review.
2. Pictures "easy to color within the lines", so the kid feels proud, not frustrated.
3. Things the kid **recognizes**: animals, trucks, unicorns, Christmas, everyday stuff. "Easy to identify."
4. **"Keeps them busy" / "entertained for a long time"**: quiet time that actually works.
5. **Screen-free** time without guilt. Parents feel judged about iPads. One Mumsnet parent warned that a "bit of quiet time" turns into addiction.
6. **Restaurant/plane/waiting-room** activity. Parents pack sticker books, Water Wow and coloring for eating out.
7. **Fine motor skills / pencil grip.** Parents and teachers say coloring "really help[s] pencil grip".
8. **Learning while coloring**: words to repeat, first reading. One Amazon parent liked that "it also has words for them to repeat".
9. Coloring **together** with mom/dad/siblings. A Mumsnet parent said kids enjoy it most "if I'm colouring with them".
10. A **sense of accomplishment**: finishing a page, showing it off.
11. **Worth the price / good value.** Parents compare with cheap shop books.
12. **Gifts that aren't "tat"**: stocking fillers and Easter-basket add-ins they "will need anyway" or "enjoy and play with lots".
13. **"Not babyish"** for older kids (4-6). Monster-truck buyers praise this.
14. Kids get **excited for each new page** (story order and suspense help).

**What ANNOYS parents (pain points):**
15. **Too detailed / tiny pictures.** A Mumsnet parent said "small pictures just frustrate him". Kids under 5 give up.
16. **Thin paper, bleed-through, seeing the picture from the back.** One Amazon parent said pages are "THIN" and "markers will bleed through".
17. **Cheap feel / damaged on arrival / bent pages.**
18. **"It's mostly scribbles anyway"**: some parents think a 2-3-year-old doesn't need a "real" book, and the cheapest one is fine.
19. **Kid loses interest fast**: attention span is short and new things beat old things.
20. **Coloring vs creativity**: some parents say coloring books "stifle creativity" and prefer blank paper.

Bonus insight on the "color & read" idea: teachers already use **color-and-read emergent readers** (one picture + one predictable sentence with sight words). A teacher-blog parent said her daughter was "almost giddy" coloring her reader. Phonics-book parents (BOB Books) love it when a 4-year-old "can read a whole book". But some say kids get bored with plain readers. **Our book = a fun reader + coloring, and that fixes the "boring reader" problem.**

---

## 6) Objections and how our ads should answer them

| Parent objection (in their words) | How our ad answers it (show, don't tell) |
|---|---|
| "Pictures are too detailed, he gets frustrated." | Show a full page: ONE big picture, thick lines, lots of white space. Text: "One big picture per page. No tiny details." |
| "Thin paper, markers bleed through." | Be honest: say **"crayon & colored-pencil friendly"** and "single-sided pictures" (if true for our layout) or "put a sheet behind for markers". Never promise "thick paper", because KDP paperback paper is standard. |
| "She just scribbles anyway, any cheap book is fine." | "Scribbling IS the start of writing." Show the **story + words**: it's not just coloring, it's their first book they can 'read'. |
| "Coloring books kill creativity." | "Color it your way: Benny can be purple." Show 2-3 different "kid-style" colored versions of the same page (made digitally, no hands). |
| "Kids lose interest after 2 pages." | "Every page is the next part of the story": what happens next? Show the page-to-page story flow. |
| "I don't want more tat for the stocking." | "A gift they'll color, read and keep." Show it next to a cocoa mug/stocking (flat-lay, no hands). Price $8.99 = stocking-filler price. |
| "Is it AI junk / low quality?" | Show real, consistent characters (Benny, Nico) across pages, a named series, and a real story arc. Avoid the "100 random pages" look. |
| "Is it the right age?" | Always say **"Ages 3-6"** + "big easy words for first readers". Kids under 3 are fine for coloring only. |
| "Screens are easier." | "15 quiet minutes, no screen needed." Never shame parents; make it an easy win. |

---

## 7) 10 hook lines in real parent language

1. "If your 3-year-old gives up on 'real' coloring books… look at this page."
2. "One big picture. One easy sentence. That's the whole page, and it's why kids finish it."
3. "The restaurant trick that isn't a phone."
4. "Coloring book or first reading book? Yes."
5. "POV: your preschooler just 'read' a whole book by herself." *(show text only, no kids)*
6. "Stocking filler that isn't tat: a story they color AND read."
7. "No tiny details. No frustrated tears. Just Benny's cozy day."
8. "Screen-free quiet time that actually lasts more than 5 minutes."
9. "Big pictures for little hands. Big words for first readers."
10. "Nico the little reindeer needs colors before Christmas. Can your kid help?" *(seasonal, Oct-Dec)*

Matching later books: "For the truck-obsessed 4-year-old: Rocco's monster truck day" / "Unicorn-crazy? Posy's sparkly story is waiting for colors." Keep the tone soft, not "for boys/for girls only", because many parents dislike strict gender labels.

---

## 8) What to avoid

- **Don't spend money on Snapchat or X ads** right now. Wrong audience, no competitor proof, and our creative limits (no faces/hands) hurt most on Snap.
- **Don't promise "thick paper" / "no bleed-through".** KDP paper is standard and reviews punish overpromises hard.
- **Don't show crowded or detailed pages**, even in the background. Parents of 3-5-year-olds reject "too detailed" right away.
- **Don't shame screen-time parents.** Say "screen-free win", not "stop giving them iPads".
- **Don't say "educational" in a school/worksheet way.** Parents want fun first ("learning without noticing").
- **Don't look like generic AI low-content.** No "100 pages of random animals"; push characters and story.
- **Don't target or speak to children directly in paid ads** (platform rules and DSA). Speak to parents and grandparents.
- **Don't use real kids or fake "kid hands"**, and no AI-generated "real child" images. Use flat digital coloring animations and page flips.
- **Don't make very gendered claims** ("for boys only"). Use the theme instead (trucks, unicorns).

---

## 9) Confidence & gaps

| Area | Confidence | Why / gaps |
|---|---|---|
| Snapchat: "no coloring-book advertisers" | **Medium-high** | 77 names checked via the official API. But search is **exact advertiser name only**, EU (plus a few countries), last 12 months. Small unknown KDP sellers can't be found without knowing their exact name. We only read the first page (10 ads) for big advertisers. A second batch (Ladybird, Carlsen, Nathan, Auzou, Toca Boca, Sago Mini, "Coloring Book", "Malbuch"...) was queued but **not finished** because time ran out. |
| X: no niche ads | **Medium** | No keyword search exists. We did not create or download any CSV reports (read-only rule). The verdict leans on audience data plus the fact that this niche isn't found on X in other research. Next step if wanted: owner manually creates a report for @Crayola / @MelissaAndDoug in one EU country. |
| Snap/X US ads | **Low** | Neither library shows normal US commercial ads. US activity is unknown, but the audience argument still holds. |
| Parent language | **Medium** | **Reddit was blocked** for every tool we have (browser said "not allowed", and fetch and search both refused). We replaced it with Mumsnet (UK moms), Amazon reviews and "Customers say" summaries (US), and teacher/parent blogs. The words match closely, but US Reddit wording ("busy book", "quiet time", "Target dollar spot") is under-represented. Next step: the owner can read r/Mommit, r/toddlers and r/KDP manually and add 10 phrases. |
| Low-star Amazon reviews | **Low-medium** | Product pages mostly show 5-star top reviews. We found only a few critical ones (thin paper/bleed, damaged pages). The full critical-review filter needs login. |

Sources used: adsgallery.snap.com + adsapi.snapchat.com ads_library search; ads.twitter.com/ads-repository; help.x.com ads transparency; Mumsnet threads ("What age of child likes colouring books?", "To think colouring books are no good…", "Keeping toddler entertained in restaurant or on plane", "hard to watch very young kids addicted to screens", "Stocking filler ideas for 3 year old", "Stocking fillers – what is fun that isn't chocolate or tat"); Amazon product pages (Creative Toddler's First Coloring Book, Christmas/monster truck/unicorn/Kumon coloring books); thisreadingmama.com color-and-read emergent readers; magicmoonbooks.com buying guide; coloringbutterfly.com paper-quality complaints; Snapchat and X demographic stat pages (backlinko, wisernotify and similar).
