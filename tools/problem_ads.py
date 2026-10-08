#!/usr/bin/env python3
"""Problem-solving ads (direct response): a parent's problem -> the book as the answer -> proof (a real page colors
itself, then its sentence is read) -> what they get -> tap the link. Warm emotional voice (Chatterbox, tts.warm).

Usage: python tools/problem_ads.py <name> [<name> ...]   (names: see ADS, or "all")  -> campaigns/fresh/<name>.mp4
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from day_ads import pdf_page  # noqa: E402
from fresh_ads import (INK, NAVY, PIC, PY, THEME, Ad, Page, W, book_dir, card, comic, ease, end_card,  # noqa: E402
                       font, gradient, groups_from_map, s_ding, s_pop, s_swish, s_tada, show)
from fresh_ads import POSY_ROUNDS  # noqa: E402
from make_video import find_cover  # noqa: E402

H = 1920
NIGHT = gradient("#2B3550", "#1B2236")


def dark(im):
    im.alpha_composite(NIGHT)


def tablet(d, cx, cy, w, t, crossed):
    """A glowing tablet that wobbles (the screen), optionally crossed out."""
    a = math.radians(4 * math.sin(t * 9))
    h = w * 1.35
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    rot = [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in pts]
    d.polygon(rot, fill="#11151F", outline="#5A6378", width=10)
    inner = [(cx + x * 0.86 * math.cos(a) - y * 0.86 * math.sin(a), cy + x * 0.86 * math.sin(a) + y * 0.86 * math.cos(a))
             for x, y in pts]
    glow = ["#5AA7E6", "#B48AD8", "#F59A3D"][int(t * 3) % 3]  # flashing cartoon screen
    d.polygon(inner, fill=glow)
    if crossed:
        r = w * 0.95
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#E5484D", width=34)
        d.line([cx - r * 0.7, cy - r * 0.7, cx + r * 0.7, cy + r * 0.7], fill="#E5484D", width=34)


def moon(d, cx, cy, r, t):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#FFE08A")
    d.ellipse([cx - r * 0.55, cy - r * 1.05, cx + r * 1.35, cy + r * 0.75], fill="#2A3450")
    for k, (x, y) in enumerate(((-330, -220), (300, -300), (360, 160), (-380, 200), (120, -420))):
        s = 22 + 8 * math.sin(t * 4 + k)
        d.polygon([(cx + x, cy + y - s), (cx + x + s * .3, cy + y - s * .3), (cx + x + s, cy + y),
                   (cx + x + s * .3, cy + y + s * .3), (cx + x, cy + y + s), (cx + x - s * .3, cy + y + s * .3),
                   (cx + x - s, cy + y), (cx + x - s * .3, cy + y - s * .3)], fill="#FFE08A")


def gift(d, cx, cy, w, t):
    b = 12 * abs(math.sin(t * 5))
    d.rectangle([cx - w / 2, cy - w / 2 + 60 - b, cx + w / 2, cy + w / 2 - b], fill="#E5484D", outline=INK, width=8)
    d.rectangle([cx - w / 2 - 25, cy - w / 2 - b, cx + w / 2 + 25, cy - w / 2 + 70 - b], fill="#F06A6F", outline=INK, width=8)
    d.rectangle([cx - 30, cy - w / 2 - b, cx + 30, cy + w / 2 - b], fill="#FFD95A", outline=INK, width=6)
    d.ellipse([cx - 110, cy - w / 2 - 90 - b, cx - 5, cy - w / 2 + 5 - b], outline="#FFD95A", width=26)
    d.ellipse([cx + 5, cy - w / 2 - 90 - b, cx + 110, cy - w / 2 + 5 - b], outline="#FFD95A", width=26)
    comic(d, "?", cx, cy + 40 - b, 160, fill="white")


ICONS = {"tablet": lambda d, t, crossed=False: tablet(d, W / 2, 900, 360, t, crossed),
         "moon": lambda d, t, crossed=False: moon(d, W / 2, 880, 170, t),
         "gift": lambda d, t, crossed=False: gift(d, W / 2, 900, 420, t)}


def check(d, x, y, s, color="#2E9E4F"):
    d.ellipse([x, y, x + s, y + s], fill=color)
    d.line([x + s * .25, y + s * .52, x + s * .43, y + s * .70, x + s * .76, y + s * .32], fill="white", width=max(6, s // 7))


def problem_ad(key, hook, agitate, solution, page_no, groups, proof_color, sentence, benefits, cta, icon="tablet"):
    """hook/agitate = (line1, line2, spoken). solution/proof_color/cta = spoken lines. sentence = the page's text."""
    ad = Ad(key, voice="warm", music="soft-music-box", music_vol=0.07)
    page = Page(key, page_no, groups)
    n = len(groups)
    book_pdf = pdf_page(key, page_no)
    cover = find_cover(book_dir(key))

    def h(im, lt, dur, k):
        dark(im)
        d = ImageDraw.Draw(im)
        ICONS[icon](d, lt)
        comic(d, hook[0], W / 2, 220, 104, fill="#FFD95A")
        comic(d, hook[1], W / 2, 345, 84, fill="white")
    ad.beat(h, hook[2], lead=0.05, tail=0.25)

    def a(im, lt, dur, k):
        dark(im)
        d = ImageDraw.Draw(im)
        ICONS[icon](d, lt + 3, crossed=lt > dur * 0.55)
        comic(d, agitate[0], W / 2, 220, 92, fill="white")
        comic(d, agitate[1], W / 2, 335, 72, fill="#FFD95A")
    ad.beat(a, agitate[2], lead=0.05, tail=0.25, sounds=[(1.2, s_pop())])

    def s(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        pop = ease(lt / 0.35)
        sz = int(760 * (0.6 + 0.4 * pop) * (1 + 0.03 * k))
        c = cover.resize((sz, sz))
        card(im, c, (W - sz) / 2, 330 + (760 - sz) / 2)
        comic(d, "Try this instead", W / 2, 200, 100, fill="#E5484D")
    ad.beat(s, solution, lead=0.1, tail=0.3, sounds=[(0.0, s_swish()), (0.05, s_ding())])

    def pc(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        show(im, page, [ease(min(1, lt / (dur * 0.8)))] * n, k)
        comic(d, "1. They color it", W / 2, 200, 96, fill="#FFD95A")
    ad.beat(pc, proof_color, lead=0.15, tail=0.3, sounds=[(0.0, s_swish())])

    def pr(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        z = 1 + 0.03 * k
        sz = int(PIC * z)
        card(im, book_pdf.resize((sz, sz)), (W - sz) / 2, PY - (sz - PIC) / 2)
        comic(d, "2. They read it", W / 2, 200, 96, fill="#FFD95A")
        return False
    ad.beat(pr, sentence, lead=0.2, tail=0.4)

    def b(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        card(im, cover.resize((300, 300)), (W - 300) / 2, 150)
        for i, txt in enumerate(benefits):
            appear = ease((lt - 0.35 * i) / 0.25)
            if appear <= 0:
                continue
            y = 560 + i * 165
            x = 150 - int(60 * (1 - appear))
            check(d, x, y, 100)
            d.text((x + 135, y + 10), txt, font=font(70), fill=NAVY)
        return True
    ad.beat(b, "No screens. Big, easy pictures. And a little reading practice on every page.", lead=0.1, tail=0.3,
            sounds=[(0.35 * i, s_pop()) for i in range(len(benefits))])

    def e(im, lt, dur, k):
        end_card(im, key)
    ad.beat(e, cta, tail=0.8, sounds=[(0.0, s_tada())])
    return ad


def four_books(hook, agitate, cta):
    """One problem, all four books."""
    ad = Ad("all", voice="warm", music="soft-music-box", music_vol=0.07)
    keys = ["nico", "benny", "rocco", "posy"]
    covers = [find_cover(book_dir(k)) for k in keys]

    def h(im, lt, dur, k):
        dark(im)
        d = ImageDraw.Draw(im)
        tablet(d, W / 2, 900, 360, lt, False)
        comic(d, hook[0], W / 2, 220, 100, fill="#FFD95A")
        comic(d, hook[1], W / 2, 340, 80, fill="white")
    ad.beat(h, hook[2], lead=0.05, tail=0.25)

    def a(im, lt, dur, k):
        dark(im)
        d = ImageDraw.Draw(im)
        tablet(d, W / 2, 900, 360, lt + 3, lt > dur * 0.5)
        comic(d, agitate[0], W / 2, 220, 92, fill="white")
        comic(d, agitate[1], W / 2, 335, 72, fill="#FFD95A")
    ad.beat(a, agitate[2], lead=0.05, tail=0.25, sounds=[(1.0, s_pop())])
    lines = ["For the snow lover: Nico the little reindeer.", "For the cuddly one: Benny the bear.",
             "For the monster truck fan: Rocco.", "And for the unicorn dreamer: Posy."]
    for i, (key, c, line) in enumerate(zip(keys, covers, lines)):
        def one(im, lt, dur, kk, i=i, c=c):
            d = ImageDraw.Draw(im)
            for j in range(i):  # earlier covers stay small at the top
                card(im, covers[j].resize((200, 200)), 70 + j * 240, 150)
            pop = ease(lt / 0.3)
            sz = int(720 * (0.6 + 0.4 * pop))
            card(im, c.resize((sz, sz)), (W - sz) / 2, 470 + (720 - sz) / 2)
        ad.beat(one, line, lead=0.1, tail=0.2, sounds=[(0.0, s_swish())])

    def b(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        for j, c in enumerate(covers):
            card(im, c.resize((420, 420)), 90 + (j % 2) * 480, 300 + (j // 2) * 470)
        comic(d, "Color it. Read it.", W / 2, 180, 100, fill="#FFD95A")
    ad.beat(b, "Every page: one big picture to color, and one easy sentence to read.", lead=0.1, tail=0.3)

    def e(im, lt, dur, k):
        end_card(im, "all")
        return True
    ad.beat(e, cta, tail=0.8, sounds=[(0.0, s_tada())])
    return ad


def crayon_bg(im, t):
    """Bright paper with thick crayon scribbles drifting at the edges (the hook frame of the all-books ad)."""
    im.alpha_composite(gradient("#FFF8EC", "#FFE9C7"))
    d = ImageDraw.Draw(im)
    cols = ["#E5484D", "#F59A3D", "#FFD95A", "#6CBF4B", "#5AA7E6", "#B48AD8"]
    for k, c in enumerate(cols):
        y = 1500 + k * 70
        pts = [(x, y + 26 * math.sin(x / 90 + t * 2 + k)) for x in range(-40, W + 60, 30)]
        d.line(pts, fill=c, width=38, joint="curve")
        y2 = 22 + k * 24
        pts = [(x, y2 + 10 * math.sin(x / 110 - t * 2 + k)) for x in range(-40, W + 60, 30)]
        d.line(pts, fill=c, width=16, joint="curve")


def all_books_ad(hook, promise, lines, cta, music="marimba-sunny", music_vol=0.09):
    """Problem -> all four books together -> each book's goodnight page colors itself -> color it, read it -> link."""
    ad = Ad("all", voice="warm", music=music, music_vol=music_vol)
    keys = ["nico", "benny", "rocco", "posy"]
    covers = [find_cover(book_dir(k)) for k in keys]
    pages = {"nico": 31, "benny": 29, "rocco": 31, "posy": 31}
    pg = {k: Page(k, p, groups_from_map(k, p)) for k, p in pages.items()}

    def fan(im, lt, y0=560, size=430):
        for j, c in enumerate(covers):  # the four covers drop in one after another
            a = ease((lt - 0.12 * j) / 0.35)
            if a <= 0:
                continue
            cs = c.resize((size, size)).convert("RGBA").rotate([-8, -3, 3, 8][j], resample=Image.BICUBIC, expand=True)
            x = 40 + (j % 2) * 500 + (j // 2) * 0
            y = y0 + (j // 2) * 430 - int(200 * (1 - a))
            im.alpha_composite(cs, (int(x), int(y)))

    def h(im, lt, dur, k):
        crayon_bg(im, lt)
        d = ImageDraw.Draw(im)
        comic(d, hook[0], W / 2, 300, 104, fill="#E5484D")
        comic(d, hook[1], W / 2, 420, 84, fill="#3B4A63")
        fan(im, lt, y0=600)
        return True
    ad.beat(h, hook[2], lead=0.05, tail=0.25, sounds=[(0.0, s_ding()), (0.15, s_pop()), (0.4, s_pop())])

    def pr(im, lt, dur, k):
        crayon_bg(im, lt)
        d = ImageDraw.Draw(im)
        comic(d, promise[0], W / 2, 300, 100, fill="#3B4A63")
        comic(d, promise[1], W / 2, 415, 84, fill="#E5484D")
        fan(im, 5, y0=600)
        return True
    ad.beat(pr, promise[2], lead=0.05, tail=0.25)

    for i, (key, line) in enumerate(zip(keys, lines)):
        def one(im, lt, dur, kk, i=i, key=key, line=line):
            d = ImageDraw.Draw(im)
            page = pg[key]
            show(im, page, [ease(min(1, lt / (dur * 0.85)))] * len(page.groups), kk)
            card(im, covers[i].resize((230, 230)), W - 290, 1100)
            comic(d, line[0], W / 2, 200, 92, fill="#FFD95A")
        ad.beat(one, line[1], lead=0.1, tail=0.25, sounds=[(0.0, s_swish())])

    def b(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        comic(d, "Color it. Read it.", W / 2, 200, 100, fill="#FFD95A")
        for j, txt in enumerate(["No screens", "Big, easy pictures", "One easy sentence", "Ages 3-6"]):
            if ease((lt - 0.3 * j) / 0.25) <= 0:
                continue
            y = 420 + j * 165
            check(d, 130, y, 100)
            d.text((265, y + 10), txt, font=font(66), fill=NAVY)
        return True
    ad.beat(b, "No screens. Big, easy pictures. And one little sentence to read on every page.",
            lead=0.1, tail=0.3, sounds=[(0.3 * j, s_pop()) for j in range(4)])

    def e(im, lt, dur, k):
        end_card(im, "all")
        return True
    ad.beat(e, cta, tail=0.8, sounds=[(0.0, s_tada())])
    return ad


BEN = ["No screens", "Big, easy pictures", "Reading practice", "Ages 3-6"]
ADS = {
    "posy-quiet": lambda: problem_ad(
        "posy", ("Need 30 quiet", "minutes?", "Need thirty quiet minutes... without handing over the tablet?"),
        ("Cartoons on", "repeat again?", "Same cartoons on repeat again? I know that feeling."),
        "Try this instead. Posy the little unicorn, and her rainbow birthday.",
        10, POSY_ROUNDS[0][1], "First, they color the picture.", "Red strawberries! Swish! Red for the rainbow!",
        BEN, "Tap the link, and grab it on Amazon."),
    "nico-gift": lambda: problem_ad(
        "nico", ("Stocking stuffer", "that isn't candy?", "Looking for a stocking stuffer that isn't more candy?"),
        ("Or more plastic", "that breaks by noon?", "Or more plastic that breaks by lunchtime?"),
        "Try this instead. Nico the little reindeer, and his snowy day.",
        16, groups_from_map("nico", 16), "They color the whole story, page by page.", "Tilly adds two shiny button eyes.",
        ["Screen-free gift", "Big, easy pictures", "Reading practice", "Ages 3-6"],
        "Tap the link, and grab it on Amazon before Christmas.", icon="gift"),
    "benny-bedtime": lambda: problem_ad(
        "benny", ("Bedtime battles", "every night?", "Bedtime battles, every single night?"),
        ("Screens make it", "even harder", "And screens before bed only make it harder."),
        "Try this instead. Benny the bear, and his cozy day.",
        29, groups_from_map("benny", 29), "A calm page to color, right before bed.", "Goodnight, Benny. Sweet dreams!",
        BEN, "Tap the link, and grab it on Amazon.", icon="moon"),
    "rocco-reading": lambda: problem_ad(
        "rocco", ("Truck videos", "all day long?", "Monster truck videos, all day long?"),
        ("Won't sit still", "for a book?", "And he won't sit still for a book?"),
        "Try this one. Rocco, the little monster truck, and his big jump.",
        26, groups_from_map("rocco", 26), "First, he colors his favorite truck.", "Bump! Rocco lands on all four wheels.",
        BEN, "Tap the link, and grab it on Amazon."),
    "rocco-bedtime": lambda: problem_ad(
        "rocco", ("Bedtime battles", "every night?", "Bedtime battles, every single night?"),
        ("Screens make it", "even harder", "And screens before bed only make it harder."),
        "Try this instead. Rocco, the little monster truck, and his big day.",
        31, groups_from_map("rocco", 31), "A calm page to color, right before bed.", "Goodnight, Rocco. Sweet dreams!",
        BEN, "Tap the link, and grab it on Amazon.", icon="moon"),
    "posy-bedtime": lambda: problem_ad(
        "posy", ("Bedtime battles", "every night?", "Bedtime battles, every single night?"),
        ("Screens make it", "even harder", "And screens before bed only make it harder."),
        "Try this instead. Posy the little unicorn, and her rainbow birthday.",
        31, groups_from_map("posy", 31), "A calm page to color, right before bed.", "Goodnight, Posy. Sweet dreams!",
        BEN, "Tap the link, and grab it on Amazon.", icon="moon"),
    "all-books-screens": lambda: all_books_ad(
        ("Always asking", "for the tablet?", "Always asking for the tablet?"),
        ("Hand them a story", "they color AND read", "Hand them a story instead. One they color, and read."),
        [("Snow lovers", "For snow lovers: Nico the little reindeer."),
         ("Cuddly ones", "For the cuddly ones: Benny the bear."),
         ("Truck fans", "For monster truck fans: Rocco."),
         ("Unicorn dreamers", "And for unicorn dreamers: Posy.")],
        "Pick the one your kid will love. Tap the link, and find all four on Amazon."),
    "four-car-ride": lambda: four_books(
        ("Long car ride", "coming up?", "Long car ride coming up?"),
        ("Don't hand them", "the phone", "Don't hand them the phone. Hand them a story."),
        "Pick the one your kid will love. Tap the link, and find all four on Amazon."),
}

if __name__ == "__main__":
    names = sys.argv[1:] or sys.exit(__doc__)
    if names == ["all"]:
        names = list(ADS)
    import tts
    ads = {nm: ADS[nm]() for nm in names}
    tts.warm_batch([b["say"] for ad in ads.values() for b in ad.beats if b["say"]])  # one model load for all lines
    for nm, ad in ads.items():
        ad.render(nm)
