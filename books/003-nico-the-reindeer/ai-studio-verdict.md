# Verdict

Winner: B (system instructions + one scene per message), with pieces borrowed from C.

## Scores (1-10)
| Criterion | A | B | C |
|---|---|---|---|
| Clean / short on a phone | 6 | 8 | 5 |
| Likely 32 separate consistent B/W images | 3 | 7 | 7 |
| Robustness / recovery | 5 | 8 | 7 |
| Honesty about unverified | 8 | 8 | 9 |
| Completeness | 8 | 8 | 8 |
| Overall | 4 | 8 | 6 |

## Why B
A asks for all 32 images in one message, which repeats the ChatGPT failure (long list, many images per turn, collage/early stop; Gemini is documented as not reliably returning an exact count). C is the most careful on consistency (character sheet) but needs 6 chats, each with an attach step, plus a multi-figure sheet image (itself a collage-type request), and gives no scarf control, so scene 15 ("his scarf") has no earlier scarf. B keeps the rules once in the system box, each message is one short scene, it has a 1-minute test plus a Plan B if the box is ignored, and a reference-image step per chat. Borrowed from C: the border, "something missing", and top/bottom-third recovery messages, the "Change nothing else" wording, and the "(line-art outline, no color)" scarf note. Borrowed nothing from A except the idea of an explicit "chatty answer" recovery (B already had it).

## Programmatic check (check.py word-diff of each entry against book.json)
All three contain 32 scenes in the right order: title, name, 29 story, end. None dropped, merged or reordered.
Discrepancies:
- A: name page lost "little reindeer" (harmless). Story 19 "Nico and Willow the fawn holding out a big red apple" makes Nico co-holder (book: Willow holds it). Labels "TITLE PAGE / NAME PAGE / THE END PAGE" in the list may leak into images. Scarf: only "when the scene says so"; scenes 6-16 give Nico no scarf though scene 15 has him take it off his neck (soft story inconsistency, admitted in its own note).
- B: story 3 (kitchen, after scarf is put on) lacks "Scarf on" (own rule broken); story 7 dropped Tilly's description (system box covers it); story 25 "snow cloud puff" became "puff of breath"; story 19 same Nico+Willow apple ambiguity; some "the penguin/fawn" tags dropped (covered by system box); adds "No scarf on Nico" to 15 scene tags (consistent with book: scarf on snowman from story 15, so end page "snowman wears it" is an inference). Extra Picture 0 test is not a book scene (declared).
- C: scenes are verbatim. Scarf only in stories 2 and 15, so Nico has no scarf in stories 3-14 although he must be wearing it in 15 ("his scarf"); its own note admits this. Same Nico+Willow apple ambiguity (story 19). Says "33 images" in one place (sheet + 32), fine.
Fixed in the final file: kitchen scene now "Scarf on"; Tilly's description restored in story 7; "snow cloud puff" restored; apple scene reworded so Willow holds it, Nico beside her; the end page no longer claims the snowman wears the scarf; "No scarf" tags removed (system box says otherwise none); "Nico himself has no scarf now" on story 15; "Willow ... white spots / no antlers" kept; system text trimmed.
