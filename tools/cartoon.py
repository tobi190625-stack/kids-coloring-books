#!/usr/bin/env python3
"""Real cartoon videos made only with code (no AI): the book character is cut out of its colored page
and animated frame by frame (drive, jump, squash, splat), on a scene drawn in the book's style.

Usage: python3 tools/cartoon.py rocco-jump          -> campaigns/rocco/videos/cartoon-big-jump.mp4
       python3 tools/cartoon.py sprites rocco-jump  -> just the cut-out characters (to check them)

A character pose = a book page with a paint map (marketing/paint/<slug>-p<N>.json, see paint.py).
Everything in the map except the "sky" group is the character; the cut-out keeps its own black outline.
Sound: Kokoro voice + music (make_music.py) + cartoon sound effects synthesized here.
"""
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
import paint  # noqa: E402
import voice  # noqa: E402
from make_marketing import NAVY, font  # noqa: E402
from make_video import end_card, find_cover  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
ASR = 44100  # sound effects sample rate
INK = (30, 30, 30)
LINE = 9


# ---------- characters ----------
def sprite(book_dir, page, width):
    """The colored character cut out of a painted page, as an RGBA image `width` px wide.

    Cut from the original picture (art/NN.png, no text bubble hiding anything), colored with the
    colors of the painted book page (the paint map works on the PDF page, so we map one onto the other)."""
    img, labels, ids, _ = paint.regions(book_dir, page)
    data = json.loads((ROOT / "marketing" / "paint" / f"{paint.slug_of(book_dir)}-p{page}.json").read_text())
    back = {i for name, l in data["groups"] if name == "sky" for i in l} | set(data.get("scenery", []))
    body = ({i for name, l in data["groups"] if name != "sky" for i in l} | set(data.get("white", []))) - back
    colored = paint.paint_full(img, labels, paint.load_map(book_dir, page))
    # the clean picture exactly as it is placed on the PDF page (the text bubble is drawn on top of it)
    import pymupdf as fitz
    doc = fitz.open(book_dir / "out" / "interior.pdf")
    pg = doc[page - 1]
    info = pg.get_image_info(xrefs=True)[0]
    zoom = img.shape[1] / pg.rect.width
    px0, py0, px1, py1 = (int(round(v * zoom)) for v in info["bbox"])
    pix = fitz.Pixmap(doc, info["xref"])
    if pix.alpha:
        pix = fitz.Pixmap(pix, 0)
    if pix.n != 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    art = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
    a = np.asarray(art.resize((px1 - px0, py1 - py0), Image.LANCZOS)).astype(np.uint8)
    lab_p, col_p = labels[py0:py1, px0:px1], colored[py0:py1, px0:px1]
    # areas of the clean picture, each colored like the matching painted area
    white = ndimage.binary_erosion(a > 200, iterations=2)
    al, an = ndimage.label(white)
    _, (iy, ix) = ndimage.distance_transform_edt(al == 0, return_indices=True)
    al = np.where(a > 60, al[iy, ix], 0)  # grow areas into the soft gray edge of the lines
    out = np.repeat(a[..., None], 3, 2).astype(float)
    is_body = np.zeros(an + 1, bool)
    known_ids = np.array(sorted(set(ids) | body | back))  # real areas (not the text bubble)
    g = paint.grain(a.shape + (3,)) * paint.shade(np.repeat(a[..., None], 3, 2))
    for i, sl in enumerate(ndimage.find_objects(al), 1):
        if sl is None:
            continue
        m = al[sl] == i
        under = lab_p[sl][m]
        known = under[np.isin(under, known_ids)]  # ignore text-bubble and line pixels
        if not len(known):
            continue
        owner = np.bincount(known).argmax()
        is_body[i] = owner not in back  # anything that isn't sky or scenery belongs to the character
        if owner in back:
            continue
        cols = col_p[sl][m][under == owner]
        rgb = np.median(cols, axis=0) if len(cols) else np.array([255, 255, 255.])
        if rgb.mean() > 245:  # paper white: leave as is
            continue
        region = out[sl]
        region[m] = rgb * g[sl][m][:, None] * (a[sl][m][:, None] / 255.0)
    m = is_body[al]
    lines = a < 150
    mask = m | (lines & ndimage.binary_dilation(m, iterations=10))
    mask = ndimage.binary_fill_holes(ndimage.binary_closing(mask, iterations=2))
    colored = np.clip(out, 0, 255).astype(np.uint8)
    lab, n = ndimage.label(mask)
    if n > 1:  # keep the character, drop loose bits (a cloud edge, a speed line)
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        mask = lab == (1 + int(np.argmax(sizes)))
    ys, xs = np.nonzero(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([colored, (mask * 255).astype(np.uint8)])[y0:y1, x0:x1]
    im = Image.fromarray(rgba, "RGBA")
    im.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(0.8)))
    return im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)


def place(canvas, spr, cx, bottom, angle=0.0, sx=1.0, sy=1.0):
    """Paste a sprite with its bottom-center at (cx, bottom); squash/stretch and tilt around that point."""
    s = spr.resize((max(1, int(spr.width * sx)), max(1, int(spr.height * sy))), Image.BICUBIC)
    if angle:
        s = s.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(s, (int(cx - s.width / 2), int(bottom - s.height)))


# ---------- scenery, drawn in the book's style (thick black outlines) ----------
def cloud(d, x, y, s=1.0):
    bumps = [(-90, 10, 55), (-35, -30, 70), (35, -20, 62), (90, 12, 50), (0, 20, 60)]
    for bx, by, r in bumps:  # outline first, then white on top = one cloud shape with an outline
        r2 = r * s + LINE
        d.ellipse([x + bx * s - r2, y + by * s - r2, x + bx * s + r2, y + by * s + r2], fill=INK)
    for bx, by, r in bumps:
        d.ellipse([x + bx * s - r * s, y + by * s - r * s, x + bx * s + r * s, y + by * s + r * s], fill="white")


def flag(d, x, y, color):
    d.line([x, y, x, y - 130], fill=INK, width=LINE)
    d.polygon([(x, y - 130), (x + 80, y - 105), (x, y - 80)], fill=color, outline=INK, width=6)


class Scene:
    """A wide world the camera moves along: sky (fixed), hills (move at half speed), the dirt track
    with a mud puddle and a BIG ramp, and the landing zone on the far side. Positions in world px."""
    WORLD = 2900
    GROUND = 1360
    RAMP = (760, 1480)         # ramp foot x, lip x
    RAMP_TOP = 780             # y of the ramp's lip
    MUD = (330, 640)           # mud puddle x range (before the ramp)

    def __init__(self):
        g = self.GROUND
        sky = np.linspace(0, 1, H)[:, None, None]
        a, b = np.array([120, 196, 240.]), np.array([205, 236, 250.])
        self.sky = Image.fromarray(np.broadcast_to(a * (1 - sky) + b * sky, (H, W, 3)).astype(np.uint8)).convert("RGBA")
        d = ImageDraw.Draw(self.sky)
        d.ellipse([830, 330, 1000, 500], fill="#FFD95A", outline=INK, width=LINE)
        for k in range(10):
            ang = k * math.pi / 5
            d.line([915 + 115 * math.cos(ang), 415 + 115 * math.sin(ang),
                    915 + 150 * math.cos(ang), 415 + 150 * math.sin(ang)], fill=INK, width=LINE)
        cloud(d, 200, 520, 0.85)
        cloud(d, 600, 700, 0.6)
        # hills, half speed
        hw = W + self.WORLD // 2
        self.hills = Image.new("RGBA", (hw, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.hills)
        for k, x in enumerate(range(-300, hw, 700)):
            d.ellipse([x, g - 210 - 40 * (k % 2), x + 1000, g + 260], fill="#8ACB5C" if k % 2 else "#6CBF4B",
                      outline=INK, width=LINE)
        # track layer, full speed
        self.track = Image.new("RGBA", (self.WORLD, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.track)
        for x, c in ((90, "#E5484D"), (2050, "#5AA7E6"), (2650, "#E5484D")):
            flag(d, x, g - 30, c)
        d.rectangle([0, g, self.WORLD, H], fill="#D8A878")
        d.line([0, g, self.WORLD, g], fill=INK, width=LINE)
        rng = np.random.default_rng(3)
        for _ in range(70):
            x, y = rng.uniform(0, self.WORLD), rng.uniform(g + 60, H - 80)
            w = rng.uniform(40, 110)
            d.arc([x, y, x + w, y + 24], 200, 340, fill=INK, width=6)
        fx, tx, ty = self.RAMP[0], self.RAMP[1], self.RAMP_TOP
        # support tower under the lip, then the wooden slope
        d.rectangle([tx - 30, ty, tx + 30, g], fill="#B7835A", outline=INK, width=LINE)
        for y in range(ty + 80, g, 110):
            d.line([tx - 220, y + 60, tx - 30, y], fill=INK, width=6)
        d.polygon([(fx, g), (tx, ty), (tx + 30, ty + 10), (tx + 30, ty + 60), (fx + 120, g)],
                  fill="#C9965F", outline=INK, width=LINE)
        for k in range(1, 9):  # planks
            t = k / 9
            x, y = fx + (tx - fx) * t, g + (ty - g) * t
            d.line([x, y, x + 120 * (1 - t) + 10, y + 40 + 10 * (1 - t)], fill=INK, width=5)
        d.line([fx, g, tx, ty], fill=INK, width=LINE + 4)
        flag(d, tx + 10, ty, "#FFD95A")
        mx0, mx1 = self.MUD
        d.ellipse([mx0, g + 15, mx1, g + 125], fill="#8B5A3C", outline=INK, width=LINE)
        d.ellipse([mx0 + 60, g + 40, mx0 + 130, g + 70], fill="#A8714A")
        # finish banner on the landing side
        d.line([2380, g, 2380, g - 420], fill=INK, width=LINE)
        d.line([2780, g, 2780, g - 420], fill=INK, width=LINE)
        d.rectangle([2370, g - 470, 2790, g - 360], fill="white", outline=INK, width=LINE)
        for k in range(14):
            if k % 2 == 0:
                d.rectangle([2370 + k * 30, g - 470, 2400 + k * 30, g - 415], fill=INK)
            else:
                d.rectangle([2370 + k * 30, g - 415, 2400 + k * 30, g - 360], fill=INK)

    def ramp_y(self, x):
        fx, tx = self.RAMP
        t = min(max((x - fx) / (tx - fx), 0), 1)
        return self.GROUND + (self.RAMP_TOP - self.GROUND) * t

    def frame(self, cam):
        """The background for camera position cam (world x at the left edge of the screen)."""
        im = self.sky.copy()
        im.alpha_composite(self.hills.crop((int(cam / 2), 0, int(cam / 2) + W, H)))
        im.alpha_composite(self.track.crop((int(cam), 0, int(cam) + W, H)))
        return im


# ---------- little helpers ----------
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def comic(d, text, cx, cy, size, fill="#FFD95A", angle=0):
    """Big comic word (BUMP!, SPLAT!) with a thick dark outline."""
    f = font(size)
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, cy - size / 2), text, font=f, fill=fill, stroke_width=max(6, size // 12), stroke_fill=INK)


def badge(d, text, y=150):
    size = 74
    while d.textlength(text, font=font(size)) > 900:
        size -= 2
    w = d.textlength(text, font=font(size))
    d.rounded_rectangle([W / 2 - w / 2 - 50, y, W / 2 + w / 2 + 50, y + size + 50], (size + 50) // 2,
                        fill=NAVY, outline="white", width=5)
    d.text((W / 2 - w / 2, y + 20), text, font=font(size), fill="white")


def blobs(d, cx, cy, t, n, color, spread, seed, up=1.0):
    """A burst of mud / dust blobs flying out and falling (t = seconds since the burst)."""
    if t < 0 or t > 1.4:
        return
    rng = np.random.default_rng(seed)
    for _ in range(n):
        ang = rng.uniform(math.pi * 1.05, math.pi * 1.95)
        sp = rng.uniform(0.5, 1.0) * spread
        x = cx + math.cos(ang) * sp * t * 2.2
        y = cy + math.sin(ang) * sp * t * 2.2 * up + 900 * t * t
        r = rng.uniform(14, 30) * (1 - t / 1.6)
        if r > 2:
            d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=INK, width=4)


def speed_lines(d, x, y, length=220):
    for k, dy in enumerate((-90, -20, 50)):
        d.line([x - 80 - length - k * 30, y + dy, x - 80, y + dy + 30], fill=INK, width=7)


def subtitle(img, text, t0, t1, t, y=1560, size=56):
    """Short line of text at the bottom while the voice says it (big, easy to read with sound off)."""
    if not (t0 <= t < t1) or not text:
        return
    d = ImageDraw.Draw(img)
    f = font(size)
    w = d.textlength(text, font=f)
    while w > 960:
        size -= 2
        f = font(size)
        w = d.textlength(text, font=f)
    d.rounded_rectangle([W / 2 - w / 2 - 30, y - 16, W / 2 + w / 2 + 30, y + size + 26], 34, fill=(255, 255, 255, 235))
    d.text((W / 2 - w / 2, y), text, font=f, fill=NAVY)


# ---------- sound effects (synthesized) ----------
def sfx_whoosh(dur=0.7):
    t = np.arange(int(dur * ASR)) / ASR
    noise = np.random.default_rng(1).normal(0, 1, len(t))
    # band of noise sweeping upward
    out, lp = np.zeros_like(noise), 0.0
    for i, x in enumerate(noise):
        a = 0.02 + 0.25 * (i / len(noise))
        lp += a * (x - lp)
        out[i] = lp
    return 0.5 * out / np.abs(out).max() * np.sin(np.pi * t / dur)


def sfx_splat(dur=0.5):
    t = np.arange(int(dur * ASR)) / ASR
    noise = ndimage.uniform_filter1d(np.random.default_rng(2).normal(0, 1, len(t)), 14)
    thump = np.sin(2 * np.pi * (120 - 160 * t) * t)
    return (0.8 * noise / np.abs(noise).max() + 0.6 * thump) * np.exp(-t * 9)


def sfx_boing(dur=0.6):
    t = np.arange(int(dur * ASR)) / ASR
    f = 180 + 140 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 3)
    return 0.45 * np.sin(2 * np.pi * np.cumsum(f) / ASR) * np.exp(-t * 4)


def sfx_engine(dur=1.0, rev=False):
    t = np.arange(int(dur * ASR)) / ASR
    f = 55 + (70 * t / dur if rev else 10 * np.sin(2 * np.pi * 2 * t))
    ph = 2 * np.pi * np.cumsum(f) / ASR
    s = np.sign(np.sin(ph)) * 0.25 + 0.15 * np.sin(2 * ph)
    s = ndimage.uniform_filter1d(s, 30)
    return 0.35 * s * np.minimum(1, t / 0.08) * np.minimum(1, (dur - t) / 0.15)


def sfx_ding():
    t = np.arange(int(0.9 * ASR)) / ASR
    return 0.3 * (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t)) * np.exp(-t * 5)


def sfx_cheer(dur=1.6):
    t = np.arange(int(dur * ASR)) / ASR
    n = ndimage.uniform_filter1d(np.random.default_rng(5).normal(0, 1, len(t)), 6)
    return 0.35 * n / np.abs(n).max() * np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.6)


# ---------- the Rocco big-jump cartoon ----------
def rocco_jump(sprites_only=False):
    book = ROOT / "books" / "005-rocco-monster-truck"
    stand = sprite(book, 26, 560)   # book page 24: "Bump! Rocco lands on all four wheels."
    fly = sprite(book, 25, 600)     # book page 23: "He flies high up in the sky!"
    if sprites_only:
        out = Path(tempfile.gettempdir()) / "rocco-sprites.png"
        sheet = Image.new("RGBA", (stand.width + fly.width + 60, max(stand.height, fly.height) + 40), "#9ACDEB")
        sheet.alpha_composite(stand, (20, 20))
        sheet.alpha_composite(fly, (stand.width + 40, 20))
        sheet.save(out)
        print(out)
        return
    scene = Scene()
    cover = find_cover(book)
    G = Scene.GROUND
    fx, tx = Scene.RAMP
    SLOPE = math.degrees(math.atan2(G - Scene.RAMP_TOP, tx - fx))
    START, MUDX, LAND = 180, 485, 2330
    FOOT = G + 45  # sprite bottom (dust under the wheels sits on the track)

    # timeline (seconds) -- voice lines, captions and sounds hang off these marks
    T_STOP, T_LOOK, T_TRY1, T_SPLAT = 2.0, 2.3, 4.8, 6.6
    T_BACK, T_TRY2, T_LIFT, T_LAND = 10.4, 11.8, 13.4, 15.6
    T_TITLE, T_CARD, T_TOTAL = 18.8, 23.8, 27.6

    lines = [  # (start, voice line, short caption)
        (0.3, "This is Rocco, the little monster truck.", "This is Rocco!"),
        (2.4, "He wants to make the big jump!", "He wants to make the BIG jump!"),
        (4.9, "Vroom! Oh no...", "Vroom! Oh no..."),
        (6.9, "Splat! Right in the mud. But Rocco doesn't give up!", "Splat! But he doesn't give up!"),
        (10.5, "He tries again.", "He tries again..."),
        (12.6, "Up, up, up, he flies!", "Up, up, up!"),
        (15.8, "Bump! He did it!", "He did it!"),
        (19.0, "Rocco's Big Jump. A story book your child colors, and reads.", "Color it. Read it."),
        (24.0, "For ages three to six. Link in bio!", ""),
    ]
    sounds = [(0.0, sfx_engine(2.0)), (T_TRY1, sfx_engine(1.6, rev=True)), (T_SPLAT, sfx_splat()),
              (T_TRY2, sfx_engine(1.6, rev=True)), (T_LIFT, sfx_whoosh(1.0)), (T_LAND, sfx_boing()),
              (T_LAND + 0.2, sfx_cheer()), (T_TITLE + 0.1, sfx_ding())]

    track = voice.place([(t, s) for t, s, _ in lines], T_TOTAL)
    caps = []
    for k, (t, s, c) in enumerate(lines):
        nxt = lines[k + 1][0] if k + 1 < len(lines) else T_TOTAL
        caps.append((t, nxt - 0.1, c))

    def follow(x):
        return min(max(x - 430, 0), Scene.WORLD - W)

    frames_dir = Path(tempfile.mkdtemp(prefix="cartoon-"))
    n_frames = int(T_TOTAL * FPS)
    for f in range(n_frames):
        t = f / FPS
        if t >= T_CARD:
            im = end_card(book, "#EAF6FF").convert("RGBA")
        elif t >= T_TITLE:  # cover + "Color it. Read it."
            k = (t - T_TITLE) / (T_CARD - T_TITLE)
            im = Image.new("RGBA", (W, H), "#EAF6FF")
            d = ImageDraw.Draw(im)
            comic(d, "Color it.", W / 2, 250, 130, fill="#E5484D")
            comic(d, "Read it.", W / 2, 410, 130, fill="#5AA7E6")
            z = 1.0 + 0.05 * k
            c = cover.resize((int(800 * z), int(800 * z)))
            im.alpha_composite(c.convert("RGBA"), ((W - c.width) // 2, 560 - int(15 * z)))
        else:
            # ---- where is Rocco (world coords) and how does he look? ----
            spr, ang, sx, sy = stand, 0.0, 1.0, 1.0
            bob = 5 * math.sin(t * 22)  # engine wobble
            dust = False
            if t < T_STOP:  # drive in from the left
                cx, bottom, dust = lerp(-350, START, ease(t / T_STOP)), FOOT + bob, True
            elif t < T_TRY1:  # waits and looks at the ramp (camera pans to show how big it is)
                cx, bottom = START, FOOT + bob * 0.4
                sy = 1 + 0.03 * math.sin(t * 6)
            elif t < T_SPLAT:  # try 1: up the ramp, too slow, slides back into the mud
                k = (t - T_TRY1) / (T_SPLAT - T_TRY1)
                if k < 0.6:
                    cx = lerp(START, 1080, ease(k / 0.6))
                    dust = True
                else:
                    kk = (k - 0.6) / 0.4
                    cx = lerp(1080, MUDX, kk * kk)
                bottom = scene.ramp_y(cx) + 45
                ang = SLOPE * 0.8 * min(1, max(0, (cx - fx) / 120))
                if k >= 0.6:
                    ang += 8 * math.sin(k * 40)
            elif t < T_BACK:  # stuck in the mud, sinks a little, wiggles
                k = t - T_SPLAT
                cx, bottom = MUDX, FOOT + 40 + 15 * min(1, k * 3)
                ang = 3 * math.sin(t * 8)
                if k < 0.18:
                    sx, sy = 1.12, 0.86
            elif t < T_TRY2:  # backs up for a run-up
                k = ease((t - T_BACK) / (T_TRY2 - T_BACK))
                cx, bottom = lerp(MUDX, START - 60, k), FOOT + bob * 0.5
            elif t < T_LIFT:  # try 2: fast all the way up
                k = (t - T_TRY2) / (T_LIFT - T_TRY2)
                cx = lerp(START - 60, tx, k ** 1.7)
                bottom = scene.ramp_y(cx) + 45
                ang = SLOPE * 0.8 * min(1, max(0, (cx - fx) / 120))
                dust = True
            elif t < T_LAND:  # flying in a big arc, pose changes to the flying picture
                k = (t - T_LIFT) / (T_LAND - T_LIFT)
                spr = fly
                cx = lerp(tx + 40, LAND, k)
                bottom = lerp(Scene.RAMP_TOP + 60, FOOT, k * k) - 330 * 4 * k * (1 - k)
                ang = lerp(18, -8, k)
                sx = sy = 1 + 0.12 * math.sin(math.pi * k)
            else:  # landed: squash, then happy bounces
                k = t - T_LAND
                cx = LAND
                sq = 0.2 * math.exp(-k * 6) * math.cos(k * 20)
                sx, sy = 1 + sq, 1 - sq
                bottom = FOOT - abs(45 * math.sin(k * 6)) * math.exp(-k * 1.0)

            # camera
            if T_LOOK <= t < T_TRY1:  # pan over to show the big ramp, then back
                k = (t - T_LOOK) / (T_TRY1 - T_LOOK)
                cam = 700 * math.sin(math.pi * ease(k))
            else:
                cam = follow(cx)
            shake = 0
            for ts_, amp in ((T_SPLAT, 16), (T_LAND, 20)):
                if ts_ <= t < ts_ + 0.45:
                    shake = amp * math.sin(t * 90) * (1 - (t - ts_) / 0.45)
            cam = min(max(cam + shake, 0), Scene.WORLD - W)  # camera shake on impacts
            im = scene.frame(cam)
            d = ImageDraw.Draw(im)
            X = cx - cam  # Rocco on screen

            if dust:
                blobs(d, X - 250, G + 30, (t % 0.45), 3, "#E9D3B0", 240, int(t / 0.45), up=0.3)
            if T_SPLAT <= t < T_SPLAT + 1.4:
                blobs(d, MUDX - cam, G + 30, t - T_SPLAT, 18, "#8B5A3C", 560, 11)
            if T_LAND <= t < T_LAND + 1.4:
                blobs(d, LAND - cam, G + 30, t - T_LAND, 16, "#E9D3B0", 600, 12)
            if T_TRY2 + 0.4 <= t < T_LAND:
                speed_lines(d, X - 220, bottom - 220, 300)
            if T_LIFT + 0.4 <= t < T_LAND - 0.4:
                for j, (ox, oy) in enumerate(((-380, -560), (360, -640), (420, -250), (-420, -200))):
                    star(d, X + ox, bottom + oy, 30 + 10 * math.sin(t * 10 + j))
            place(im, spr, X, bottom, ang, sx, sy)
            d = ImageDraw.Draw(im)
            if T_SPLAT <= t < T_SPLAT + 1.8:
                comic(d, "SPLAT!", W / 2, 700, int(lerp(60, 190, ease((t - T_SPLAT) / 0.25))), fill="#A8714A")
            if T_LAND <= t < T_LAND + 2.2:
                comic(d, "BUMP!", W / 2, 640, int(lerp(60, 190, ease((t - T_LAND) / 0.25))))
            if t >= T_LAND + 0.7:
                comic(d, "He did it!", W / 2, 820, 110, fill="white")
            if t < T_TRY1:
                badge(d, "Can little Rocco make the BIG jump?")
            elif t < T_TRY2:
                badge(d, "Try #1")
            elif t < T_LIFT:
                badge(d, "Try #2")
        for t0, t1, c in caps:
            if t < T_CARD:
                subtitle(im, c, t0, t1, t)
        im.convert("RGB").save(frames_dir / f"f_{f:05d}.png")
    print(f"drew {n_frames} frames ({T_TOTAL:.1f} s)")

    out = ROOT / "campaigns" / "rocco" / "videos" / "cartoon-big-jump.mp4"
    render(frames_dir, track, sounds, T_TOTAL, out, ROOT / "marketing" / "music" / "rocco-upbeat.wav")
    srt = "".join(f"{i}\n{ts(a)} --> {ts(b)}\n{s}\n\n" for i, ((a, s, _), (_, b, _)) in
                  enumerate(zip(lines, caps), 1))
    out.with_suffix(".srt").write_text(srt, encoding="utf-8")
    out.with_suffix(".txt").write_text("Rocco's Big Jump (cartoon)\n\n" + "\n".join(s for _, s, _ in lines) + "\n",
                                       encoding="utf-8")


def star(d, x, y, r):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.polygon(pts, fill="#FFD95A", outline=INK, width=5)


def ts(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def render(frames_dir, voice_track, sounds, total, out, music):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    silent = frames_dir / "video.mp4"
    subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(frames_dir / "f_%05d.png"),
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(silent)], check=True)
    raw, warm = frames_dir / "voice.raw.wav", frames_dir / "voice.wav"
    sf.write(raw, voice_track, voice.SR)
    voice.warm(raw, warm)
    fx = np.zeros(int(total * ASR) + ASR)
    for t, s in sounds:
        i = int(t * ASR)
        fx[i:i + len(s)] += s[: len(fx) - i]
    fxw = frames_dir / "sfx.wav"
    sf.write(fxw, np.clip(fx[: int(total * ASR)], -1, 1), ASR)
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", str(silent), "-i", str(warm), "-i", str(fxw),
                    "-stream_loop", "-1", "-i", str(music), "-filter_complex",
                    f"[1:a]volume=1.6[v];[2:a]volume=0.55[s];[3:a]atrim=0:{total:.2f},volume=0.16,afade=t=in:d=0.4,"
                    f"afade=t=out:st={total - 1.5:.2f}:d=1.5[m];[v][s][m]amix=inputs=3:duration=first:normalize=0,"
                    "alimiter=limit=0.95[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("✓", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["sprites", "rocco-jump"]:
        rocco_jump(sprites_only=True)
    elif args == ["rocco-jump"]:
        rocco_jump()
    else:
        sys.exit(__doc__)
