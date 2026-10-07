#!/usr/bin/env python3
"""Daily ad formats built on what performed (Oct 7 numbers): story trailers with the colorful cover on frame 1
(like the Rocco/Posy launch Reels, best on Facebook), guess-the-colors (best on YouTube) and reading challenges.
Uses the engine in fresh_ads.py (natural voice, word-synced captions, real book colors).

Usage: python tools/day_ads.py <name> [<name> ...]   (names: see ADS at the bottom, or "all")
Writes campaigns/fresh/<name>.mp4
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from fresh_ads import (INK, NAVY, OUT, PIC, PY, Ad, Page, W, book_dir, card, comic, countdown, ease,  # noqa: E402
                       end_card, font, groups_from_map, pill, rgb, s_crayon, s_ding, s_pop, s_swish, s_tada,
                       s_tick, show)
from make_video import find_cover  # noqa: E402


def pdf_page(key, page, size=900):
    """A real page of the book (picture + its sentence bubble), as printed."""
    import pymupdf
    pg = pymupdf.open(book_dir(key) / "out" / "interior.pdf")[page - 1]
    pix = pg.get_pixmap(dpi=150)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples).resize((size, size), Image.LANCZOS)


def hook_frame(im, key, lt, line1, line2):
    """Frame 1: the colorful cover pops in (slight tilt, bounce) under a big hook. Visible from the first frame."""
    d = ImageDraw.Draw(im)
    s = 0.92 + 0.08 * ease(lt / 0.35) + 0.015 * math.sin(lt * 5)
    c = find_cover(book_dir(key)).resize((int(820 * s), int(820 * s)))
    m = Image.new("L", c.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, c.width, c.height], 36, fill=255)
    c = c.convert("RGBA")
    c.putalpha(m)
    c = c.rotate(-3 + 2 * math.sin(lt * 2), resample=Image.BICUBIC, expand=True)
    im.alpha_composite(c, (int((W - c.width) / 2), int(360 - (c.height - 820) / 2)))
    comic(d, line1, W / 2, 150, 92, fill="#FFD95A")
    comic(d, line2, W / 2, 262, 66, fill="white")


def story_trailer(key, hook, pages, cliff, end_say, voice="ava"):
    """hook = (line1, line2, spoken). pages = [(pdf page, sentence the voice reads)]. cliff = (text, spoken)."""
    ad = Ad(key, voice=voice, music="soft-music-box", music_vol=0.10)
    imgs = [pdf_page(key, p) for p, _ in pages]

    def h(im, lt, dur, k):
        hook_frame(im, key, lt, hook[0], hook[1])
    ad.beat(h, hook[2], lead=0.05, tail=0.25, sounds=[(0.0, s_ding())])

    for i, ((p, sentence), img) in enumerate(zip(pages, imgs)):
        def page_beat(im, lt, dur, k, i=i, img=img):
            slide = ease(lt / 0.3)
            if i:
                card(im, imgs[i - 1].resize((PIC, PIC)), PX0(), PY)
            z = 1.0 + 0.035 * k
            s = int(PIC * z)
            layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
            card(layer, img.resize((s, s)), (W - s) / 2, PY - (s - PIC) / 2)
            im.alpha_composite(layer.transform(im.size, Image.AFFINE, (1, 0, -int((1 - slide) * W), 0, 1, 0)))
            d = ImageDraw.Draw(im)
            pill(d, f"{i + 1} / {len(pages)}", 205, 40)
            return True  # the page shows the sentence itself
        ad.beat(page_beat, sentence, lead=0.3, tail=0.35, rate="-6%", sounds=[(0.0, s_swish())])

    def c(im, lt, dur, k):
        card(im, imgs[-1].resize((PIC, PIC)), PX0(), PY)
        fade = Image.new("RGBA", im.size, (20, 30, 50, int(150 * ease(lt / 0.4))))
        im.alpha_composite(fade)
        d = ImageDraw.Draw(im)
        comic(d, cliff[0], W / 2, 760, 96, fill="#FFD95A")
    ad.beat(c, cliff[1], lead=0.1, tail=0.3, sounds=[(0.0, s_pop())])

    def e(im, lt, dur, k):
        end_card(im, key)
    ad.beat(e, end_say, tail=0.7, sounds=[(0.0, s_ding())])
    return ad


def PX0():
    return (W - PIC) / 2


def guess_colors(key, page_no, hook, mid_say, ask_say, end_say, voice="ava", seconds=9.0):
    """B&W page, 'guess the colors before the end', a crayon colors it group by group with crayon sounds,
    then the full page + 'did you guess right?'."""
    ad = Ad(key, voice=voice, music="soft-music-box", music_vol=0.08)
    groups = groups_from_map(key, page_no)
    page = Page(key, page_no, groups)
    n = len(groups)
    areas = np.array([max(1, (page.gidx == k).sum()) for k in range(n)], float)
    share = np.sqrt(areas) / np.sqrt(areas).sum()
    starts = np.concatenate([[0], np.cumsum(share)])

    def progress(kk):
        return [min(1, max(0, (kk - starts[i]) / (starts[i + 1] - starts[i]))) for i in range(n)]

    def h(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        show(im, page, [0] * n, k)
        comic(d, hook[0], W / 2, 150, 104, fill="#FFD95A")
        comic(d, hook[1], W / 2, 262, 62, fill="white")
    ad.beat(h, hook[2], lead=0.05, tail=0.2, sounds=[(0.0, s_ding())])

    def color(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        kk = min(1, lt / (dur - 0.4))
        x, y, sc = show(im, page, progress(kk), 0)
        i = min(int(np.searchsorted(starts, kk, side="right") - 1), n - 1)
        local = (kk - starts[i]) / (starts[i + 1] - starts[i])
        if kk < 1:
            cx, cy = page.tip(i, min(1, local))
            cx, cy = x + cx * sc, y + cy * sc
            wob = 9 * math.sin(lt * 30)
            col = rgb(groups[i][0])
            d.polygon([(cx, cy), (cx + 40 + wob, cy - 110), (cx + 90 + wob, cy - 80)], fill=col, outline=INK, width=5)
            d.polygon([(cx + 40 + wob, cy - 110), (cx + 90 + wob, cy - 80), (cx + 250 + wob, cy - 330),
                       (cx + 200 + wob, cy - 360)], fill=col, outline=INK, width=5)
        comic(d, hook[0], W / 2, 150, 104, fill="#FFD95A")
    fr = int(seconds * 30)
    ad.beat(color, mid_say, min=seconds, lead=1.2,
            sounds=[(0.0, 0.6 * s_crayon([1.0 if f < fr - 12 else 0.0 for f in range(fr)]))])

    def ask(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        show(im, page, [1] * n, k, zoom=0.05)
        comic(d, "Did you guess right?", W / 2, 180, 92, fill="#FFD95A")
    ad.beat(ask, ask_say, lead=0.05, tail=0.4, sounds=[(0.0, s_tada())])

    def e(im, lt, dur, k):
        end_card(im, key)
    ad.beat(e, end_say, tail=0.7)
    return ad


def big_sentence(im, words, t, y=1180, size=76, shown=False):
    """The book sentence in big letters; the word being read lights up (karaoke)."""
    d = ImageDraw.Draw(im)
    f = font(size)
    lines, cur = [], []
    for i in range(len(words)):
        if cur and d.textlength(" ".join(words[j][0] for j in cur + [i]), font=f) > 960:
            lines.append(cur)
            cur = []
        cur.append(i)
    lines.append(cur)
    now = None if shown else next((i for i, (_, a, b) in enumerate(words) if a <= t < b + 0.05), None)
    done_all = (not shown) and t >= words[-1][2]
    for li, idx in enumerate(lines):
        x = (W - d.textlength(" ".join(words[j][0] for j in idx), font=f)) / 2
        yy = y + li * (size + 30)
        for j in idx:
            wd = d.textlength(words[j][0], font=f)
            if j == now:
                d.rounded_rectangle([x - 12, yy - 6, x + wd + 12, yy + size + 18], 20, fill="#FFD95A")
            lit = (now is not None and j <= now) or done_all
            d.text((x, yy), words[j][0], font=f, fill=NAVY if lit else "#9AA6BA")
            x += wd + d.textlength(" ", font=f)


def read_challenge(key, items, hook, end_say, voice="emma"):
    """items = [(pdf page, sentence)]. Each round: picture + sentence in gray, 3-2-1 for the kid to read,
    then the voice reads it and the words light up."""
    ad = Ad(key, voice=voice, music="soft-music-box", music_vol=0.08)
    pics = [pdf_page_art(key, p) for p, _ in items]

    def h(im, lt, dur, k):
        hook_frame(im, key, lt, hook[0], hook[1])
    ad.beat(h, hook[2], lead=0.05, tail=0.2, sounds=[(0.0, s_ding())])
    for r, ((p, sentence), pic) in enumerate(zip(items, pics)):
        words_gray = [(w, 9e9, 9e9) for w in sentence.split()]

        def try_(im, lt, dur, k, pic=pic, wg=words_gray, r=r):
            d = ImageDraw.Draw(im)
            card(im, pic, (W - pic.width) / 2, 300)
            pill(d, f"Sentence {r + 1} of {len(items)}: your turn!", 205, 44)
            big_sentence(im, wg, 0, shown=True)
            countdown(d, W / 2, 1600, 1 - k, 3 - min(2, int(k * 3)), r=80)
            return True
        ad.beat(try_, None, min=2.4, sounds=[(0.0, s_tick()), (0.8, s_tick()), (1.6, s_tick())])

        def read(im, lt, dur, k, pic=pic, r=r):
            d = ImageDraw.Draw(im)
            card(im, pic, (W - pic.width) / 2, 300)
            pill(d, f"Sentence {r + 1} of {len(items)}", 205, 44)
            big_sentence(im, ad_words[r], ad_t0[r] + lt)
            return True
        ad.beat(read, sentence, lead=0.15, tail=0.5, rate="-12%")

    def ask(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        for i, pic in enumerate(pics):
            card(im, pic.resize((320, 320)), 30 + i * 345, 560)
        comic(d, "How many could they read?", W / 2, 260, 84, fill="#FFD95A")
        comic(d, "1, 2 or all 3?", W / 2, 1020, 80, fill="white")
    ad.beat(ask, "How many could your little one read? One, two, or all three? Tell me in the comments!",
            sounds=[(0.0, s_tada())])

    def e(im, lt, dur, k):
        end_card(im, key)
    ad.beat(e, end_say, tail=0.7)

    # the karaoke needs each read-beat's own word times: render() fills them in through this hook
    ad_words, ad_t0 = [], []
    orig = ad.render

    def render(name):
        import tts
        for p, sentence in items:
            _, ws = tts.say(sentence, ad.voice, rate="-12%")
            toks = sentence.split()  # keep the book's own words + punctuation, take only the times from the voice
            if len(toks) == len(ws):
                ws = [(tok, s, e2) for tok, (_, s, e2) in zip(toks, ws)]
            ad_words.append([(w, s + 0.15, e2 + 0.15) for w, s, e2 in ws])
            ad_t0.append(0.0)
        return orig(name)
    ad.render = render
    return ad


def pdf_page_art(key, page, size=760):
    """The page picture without its sentence bubble (the sentence is shown big below it)."""
    pg = Page(key, page, [])
    return pg.picture([], size)


ADS = {
    "nico-story": lambda: story_trailer(
        "nico", ("Got a little one", "who LOVES snow?", "Got a little one who loves snow? Watch this."),
        [(7, "Whoosh! The door opens to a snowy world."), (8, "Nico makes his very first snow angel."),
         (11, "Whee! They zoom down the big hill."), (12, "Bump! They tumble into the soft snow.")],
        ("Who's hiding in the trees?", "But wait... who is hiding in the trees?"),
        "Nico's Snowy Day. Your child colors every page, and reads it too. Find it on Amazon!"),
    "benny-story": lambda: story_trailer(
        "benny", ("Rainy day", "and no screens?", "Rainy day, and no screens? Here's a cozy story."),
        [(10, "Oh no, it starts to rain!"), (11, "Benny and Bella meet Ollie the owl."),
         (12, "Ollie reads them a story."), (13, "Ducks swim by. Quack, quack!")],
        ("Who do they meet next?", "And guess who they meet next..."),
        "Benny the Bear's Cozy Day. They color it, then they read it. Find it on Amazon!", voice="emma"),
    "rocco-story": lambda: story_trailer(
        "rocco", ("Monster truck kid?", "This one's for them", "Got a monster truck kid? This one's for them."),
        [(7, "The big trucks are SO tall. Rocco is small."), (8, "Zoom! A big truck flies over the ramp."),
         (19, "Oh no! Gus is stuck in the deep mud."), (20, "Rocco pushes with his big tires. Push, push!")],
        ("Can tiny Rocco save him?", "Can tiny Rocco save his friend?"),
        "Rocco's Big Jump. Kids color it, then read it. Find it on Amazon!", voice="andrew"),
    "posy-story": lambda: story_trailer(
        "posy", ("Little unicorn fan?", "A rainbow needs help", "Got a little unicorn fan? A rainbow needs help."),
        [(15, "Oops! Mochi trips on a little rock."), (16, "Posy helps Mochi up. Friends help friends."),
         (19, "A mermaid waves from the sparkly lake."), (24, "They climb the tall rainbow hill.")],
        ("Will the rainbow be back?", "Will the rainbow be back in time for her party?"),
        "Posy's Rainbow Birthday. They color it, then read it. Find it on Amazon!"),
    "nico-guess": lambda: guess_colors(
        "nico", 31, ("GUESS THE COLORS", "before Nico falls asleep", "Guess the colors before Nico falls asleep!"),
        "Shh... it's bedtime.", "Did you guess right? Tell me the color of Nico's blanket!",
        "Nico's Snowy Day. Color it, then read it. Find it on Amazon!"),
    "benny-guess": lambda: guess_colors(
        "benny", 21, ("GUESS THE COLORS", "before the end!", "Can you guess the colors before the end?"),
        "Whee! Benny rolls down the hill.", "Did you guess right? Comment the color you picked!",
        "Benny the Bear's Cozy Day. Color it, then read it. Find it on Amazon!", voice="emma"),
    "rocco-guess": lambda: guess_colors(
        "rocco", 25, ("GUESS THE COLORS", "before he lands!", "Guess Rocco's colors before he lands!"),
        "He flies high up in the sky!", "Did you guess right? Red, blue, or something else?",
        "Rocco's Big Jump. Color it, then read it. Find it on Amazon!", voice="andrew"),
    "posy-read": lambda: read_challenge(
        "posy", [(3, "Posy the unicorn wakes up. It is her birthday!"), (6, "Mochi the kitten brings a cupcake."),
                 (28, "Posy wears her sparkly crown.")],
        ("Can your 4-year-old", "read these?", "Can your four year old read these? Let's try!"),
        "Posy's Rainbow Birthday. One big picture and one easy sentence on every page. Find it on Amazon!"),
}

if __name__ == "__main__":
    names = sys.argv[1:] or sys.exit(__doc__)
    if names == ["all"]:
        names = list(ADS)
    for nm in names:
        ADS[nm]().render(nm)
