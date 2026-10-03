# Next two books: START HERE

Branch: `books/rocco-and-posy`. Everything for both books is ready; only the pictures are missing.

| | Book 5 (boys) | Book 6 (girls) |
|---|---|---|
| Folder | `books/005-rocco-monster-truck/` | `books/006-posy-the-unicorn/` |
| Title | Rocco the Little Monster Truck's Big Jump | Posy the Little Unicorn's Rainbow Birthday |
| Characters | Rocco (little monster truck), Dot (digger), Gus (garbage truck) | Posy (baby unicorn), Mochi (kitten), Bibi (butterfly with a magic paintbrush) |
| Size | 8.5 x 8.5, No bleed, 32 pages | 8.5 x 8.5, No bleed, 32 pages |

## Steps (same as Benny and Nico)
1. Open `chatgpt-prompts.md` of the book. One new ChatGPT chat per book. Send Prompt 1-4 (8 pictures each = 32).
2. In the same chat, send the 2 prompts from `cover-prompts.md` (front + back).
3. Send all pictures to Claude as zips (or drop them in `art/inbox/`). Claude sorts them, cleans the line art, builds `out/interior.pdf` and `out/cover.pdf`, runs `tools/check_kdp.py`.
4. Copy the KDP answers from `listing.md` (title, subtitle, description, keywords, categories, settings).
5. Marketing: `marketing/rocco/plan.md` and `marketing/posy/plan.md` (Claude makes pins, carousels and realistic coloring videos once the art is in).

## Why these two themes (research, Oct 2026)
- 4 research agents (Amazon data + kid appeal/virality for each book).
- Boys: construction has the steadiest Amazon demand and low trademark risk; monster trucks have the most hype with 3-5 year olds and the best video appeal. Combined: a monster-truck hero with a digger and a garbage-truck friend.
- Girls: both researchers picked unicorn (most-searched girls' theme, top under-6 party theme). Kitten sidekick for the huge cat audience online; a mermaid and fairy appear for "unicorn mermaid fairy" searches. Very few unicorn books tell a story, which is our edge.
- Trademark rules are at the bottom of each `listing.md`. Read them before publishing.
