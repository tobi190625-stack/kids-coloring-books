#!/usr/bin/env python3
"""Interactive ad videos (9:16) for all books: color quiz, I spy, spot the difference, crayon ASMR,
"which book would your kid pick?". Natural neural voice (tools/tts.py) with captions synced word by word,
real book colors only (paint maps), synthesized sounds (ticks, pops, crayon scribbles), no AI video.

Usage: python tools/fresh_ads.py <name> [<name> ...]     names: see ADS at the bottom (or "all")
Writes campaigns/fresh/<name>.mp4 (+ .txt transcript).
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
import paint  # noqa: E402
import tts  # noqa: E402
from make_marketing import NAVY, font  # noqa: E402
from make_video import find_cover  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
SR = 44100
INK = (30, 30, 30)
OUT = ROOT / "campaigns" / "fresh"
BOOKS = {"nico": "books/003-nico-the-reindeer", "benny": "books/002-benny-the-bear/kdp-8.5x8.5",
         "rocco": "books/005-rocco-monster-truck", "posy": "books/006-posy-the-unicorn"}
TITLES = {"nico": "Nico the Little Reindeer's Snowy Day", "benny": "Benny the Bear's Cozy Day",
          "rocco": "Rocco the Little Monster Truck's Big Jump", "posy": "Posy the Little Unicorn's Rainbow Birthday"}
THEME = {"nico": ("#E6F4FF", "#C6E3F7"), "benny": ("#FFF6DA", "#FFE3B0"), "rocco": ("#EAF6FF", "#CFE8F7"),
         "posy": ("#FFEAF4", "#EADCFF"), "all": ("#FFF6DA", "#FFE9B8")}


def rgb(h):
    h = paint.COLORS.get(h, h)
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def book_dir(key):
    d = ROOT / BOOKS[key]
    return d if (d / "out" / "interior.pdf").exists() else d.parent


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def gradient(c1, c2):
    a, b = np.array(rgb(c1), float), np.array(rgb(c2), float)
    t = np.linspace(0, 1, H)[:, None, None]
    return Image.fromarray(np.broadcast_to(a * (1 - t) + b * t, (H, W, 3)).astype(np.uint8)).convert("RGBA")


# ---------------- a book picture without its text bubble, colorable group by group ----------------
class Page:
    """Clean picture of a book page (the art as placed in the PDF, no text bubble), colored with
    paint groups [(color name, [area ids])] whose ids come from paint.py on that PDF page."""

    def __init__(self, key, page, groups, changes=None):
        bd = book_dir(key)
        img, labels, ids, _ = paint.regions(bd, page)
        import pymupdf as fitz
        doc = fitz.open(bd / "out" / "interior.pdf")
        pg = doc[page - 1]
        info = pg.get_image_info(xrefs=True)[0]
        zoom = img.shape[1] / pg.rect.width
        x0, y0, x1, y1 = (int(round(v * zoom)) for v in info["bbox"])
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, img.shape[1]), min(y1, img.shape[0])
        pix = fitz.Pixmap(doc, info["xref"])
        if pix.alpha:
            pix = fitz.Pixmap(pix, 0)
        if pix.n != 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        art = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
        # the image box may run past the page edge: keep the part that is on the page
        bx0, by0, bx1, by1 = (v * zoom for v in info["bbox"])
        sx, sy = art.width / (bx1 - bx0), art.height / (by1 - by0)
        art = art.crop((int((x0 - bx0) * sx), int((y0 - by0) * sy), int((x1 - bx0) * sx), int((y1 - by0) * sy)))
        a = np.asarray(art.resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.uint8)
        lab_p = labels[y0:y1, x0:x1]
        white = ndimage.binary_erosion(a > 200, iterations=2)
        al, an = ndimage.label(white)
        _, (iy, ix) = ndimage.distance_transform_edt(al == 0, return_indices=True)
        al = np.where(a > 60, al[iy, ix], 0)
        known = np.array(sorted(ids))
        owner = np.zeros(an + 1, int)
        for i, sl in enumerate(ndimage.find_objects(al), 1):
            if sl is None:
                continue
            under = lab_p[sl][al[sl] == i]
            under = under[np.isin(under, known)]
            if len(under):
                owner[i] = np.bincount(under).argmax()
        self.pdf_owner = owner[al]                     # PDF area id under every clean pixel
        self.a = a
        g = paint.grain(a.shape) * paint.shade(np.repeat(a[..., None], 3, 2))
        self.tex = g[..., None] * (a[..., None] / 255.0)
        self.bw = np.repeat(a[..., None], 3, 2).astype(np.uint8)
        self.groups = []
        self.gidx = np.full(a.shape, -1, int)
        col = self.bw.astype(float)
        for k, grp in enumerate(groups):
            name, gids = grp[0], grp[1]
            m = np.isin(self.pdf_owner, gids)
            if len(grp) > 2:  # (name, ids, (cx, cy, r)): only inside this circle (PDF page px), for an
                cx, cy, r = grp[2]  # area that leaks into the sky through a gap in the line
                yy0, xx0 = np.mgrid[0:a.shape[0], 0:a.shape[1]]
                m &= (xx0 + x0 - cx) ** 2 + (yy0 + y0 - cy) ** 2 <= r * r
            self.gidx[m] = k
            col[m] = np.array(rgb(name), float) * self.tex[m]
            self.groups.append((name, gids))
        self.col = np.clip(col, 0, 255).astype(np.uint8)
        self.changed = None
        if changes:  # spot the difference: same picture with a few areas recolored
            ch = col.copy()
            for name, gids in changes:
                m = np.isin(self.pdf_owner, gids)
                ch[m] = self.bw[m] if name == "paper" else np.array(rgb(name), float) * self.tex[m]
            self.changed = np.clip(ch, 0, 255).astype(np.uint8)
        # crayon sweep order inside each group (top-left to bottom-right)
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        proj = (xx * 0.8 + yy * 0.6).astype(float)
        self.projn = np.zeros(a.shape)
        self.order = []
        for k in range(len(groups)):
            m = self.gidx == k
            if m.any():
                p = proj[m]
                self.projn[m] = (p - p.min()) / (p.max() - p.min() + 1)
                o = np.argsort(self.projn[m])
                self.order.append((yy[m][o], xx[m][o]))
            else:
                self.order.append((np.array([0]), np.array([0])))

    def picture(self, progress, size, changed=False):
        """progress: list of 0..1 per group (how far the crayon got). Returns an RGB PIL image."""
        prog = np.append(np.asarray(progress, float), 0.0)
        on = (self.gidx >= 0) & (prog[self.gidx] > self.projn)
        src = self.changed if changed else self.col
        out = np.where(on[..., None], src, self.bw)
        return Image.fromarray(out).resize((size, int(size * out.shape[0] / out.shape[1])), Image.LANCZOS)

    def tip(self, k, p):
        """Picture px of the crayon tip for group k at progress p."""
        ys, xs = self.order[k]
        i = min(int(p * (len(ys) - 1)), len(ys) - 1)
        return int(xs[i]), int(ys[i])

    def where(self, gids):
        """Center and radius (picture px) of some areas, for circling them."""
        m = np.isin(self.pdf_owner, gids)
        ys, xs = np.nonzero(m)
        return xs.mean(), ys.mean(), max(np.ptp(xs), np.ptp(ys)) / 2 + 30

    def spots(self, gids, most=3):
        """Circles around the separate things in these areas (e.g. a red scarf AND a red hat)."""
        m = ndimage.binary_dilation(np.isin(self.pdf_owner, gids), iterations=12)
        lab, n = ndimage.label(m)
        if n == 0:
            return []
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        out = []
        for i in np.argsort(sizes)[::-1][:most]:
            if sizes[i] < 0.15 * sizes.max():
                break
            ys, xs = np.nonzero(lab == i + 1)
            out.append((xs.mean(), ys.mean(), max(np.ptp(xs), np.ptp(ys)) / 2 + 20))
        return out

    @property
    def shape(self):
        return self.a.shape


def groups_from_map(key, page):
    """Named groups of a paint map, completed like paint.load_map does it: the "rest" color for the bigger
    unlisted areas (grass, sky) and small gaps joined to the color around them."""
    data = json.loads((ROOT / "marketing" / "paint" / f"{key}-p{page}.json").read_text())
    names = [n for n, _ in data["groups"]] + ([data["rest"]] if data.get("rest") else [])
    full = paint.load_map(book_dir(key), page)
    return [(n, ids) for n, (_, ids) in zip(names, full)]


# ---------------- drawing helpers ----------------
def card(im, pic, x, y, radius=36, shadow=True):
    if shadow:
        sh = Image.new("RGBA", (pic.width + 50, pic.height + 50), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([25, 32, pic.width + 25, pic.height + 32], radius, fill=(40, 60, 90, 70))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (int(x) - 25, int(y) - 25))
    m = Image.new("L", pic.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, pic.width, pic.height], radius, fill=255)
    layer = Image.new("RGBA", pic.size, (0, 0, 0, 0))
    layer.paste(pic.convert("RGB"), (0, 0), m)
    im.alpha_composite(layer, (int(x), int(y)))


def comic(d, text, cx, cy, size, fill="#FFD95A", max_w=980):
    while d.textlength(text, font=font(size)) > max_w and size > 30:
        size -= 2
    f = font(size)
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, cy - size / 2), text, font=f, fill=fill, stroke_width=max(5, size // 11), stroke_fill=INK)


def pill(d, text, cy, size=60, fill=NAVY, color="white", max_w=940):
    while d.textlength(text, font=font(size)) > max_w and size > 30:
        size -= 2
    w = d.textlength(text, font=font(size))
    d.rounded_rectangle([W / 2 - w / 2 - 44, cy - size / 2 - 24, W / 2 + w / 2 + 44, cy + size / 2 + 28],
                        (size + 52) // 2, fill=fill)
    d.text((W / 2 - w / 2, cy - size / 2 - 2), text, font=font(size), fill=color)


def ring(d, cx, cy, r, color="#E5484D", width=12):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="white", width=width + 8)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=width)


def countdown(d, cx, cy, frac, number, r=95):
    """Timer circle: the colored arc shrinks as time runs out, the number in the middle."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white", outline=INK, width=8)
    d.arc([cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14], -90, -90 + 360 * frac, fill="#E5484D", width=22)
    comic(d, str(number), cx, cy - 4, 110, fill="#FFD95A")


def captions(im, words, t, y=1395, size=68):
    """TikTok-style captions: 1-4 words at a time, the spoken word in yellow, white text with a dark edge."""
    cur = next((i for i, (_, a, b) in enumerate(words) if a <= t < b + 0.12), None)
    if cur is None:
        return
    # chunk = run of up to 4 words that belong together in time
    start = cur
    while start > 0 and cur - start < 3 and words[start][1] - words[start - 1][2] < 0.35 and (cur - start + 1) % 4:
        start -= 1
    start = cur - (cur - start) % 4
    chunk = words[start:start + 4]
    d = ImageDraw.Draw(im)
    f = font(size)
    text = " ".join(w for w, _, _ in chunk)
    while d.textlength(text, font=f) > 960:
        size -= 3
        f = font(size)
    x = (W - d.textlength(text, font=f)) / 2
    for i, (w, _, _) in enumerate(chunk):
        d.text((x, y), w, font=f, fill="#FFD95A" if start + i == cur else "white",
               stroke_width=7, stroke_fill=INK)
        x += d.textlength(w + " ", font=f)


def end_card(im, key, d=None):
    d = d or ImageDraw.Draw(im)
    keys = ["nico", "benny", "rocco", "posy"] if key == "all" else [key]
    if len(keys) == 1:
        c = find_cover(book_dir(key)).resize((700, 700))
        card(im, c, (W - 700) / 2, 330)
    else:
        for i, k in enumerate(keys):
            c = find_cover(book_dir(k)).resize((420, 420))
            card(im, c, 90 + (i % 2) * 480, 300 + (i // 2) * 470)
    comic(d, "Color it. Read it.", W / 2, 190, 96)
    pill(d, "Find it on Amazon", 1150 if len(keys) == 1 else 1290, 64)
    t = "tap the link  •  link in bio  •  link in description"
    d.text(((W - d.textlength(t, font=font(40))) / 2, (1245 if len(keys) == 1 else 1385)), t, font=font(40), fill=NAVY)


# ---------------- sounds (synthesized, copyright-free) ----------------
def tone(f, dur, decay=6, vol=0.3):
    t = np.arange(int(dur * SR)) / SR
    return vol * np.sin(2 * np.pi * f * t) * np.exp(-t * decay)


def s_tick():
    t = np.arange(int(0.06 * SR)) / SR
    return 0.35 * np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90)


def s_pop():
    t = np.arange(int(0.25 * SR)) / SR
    return 0.45 * np.sin(2 * np.pi * (500 + 900 * t / 0.25) * t) * np.exp(-t * 18)


def s_ding():
    return tone(1318, 0.9, 5, 0.25) + tone(1976, 0.9, 6, 0.12)


def s_tada():
    out = np.zeros(int(1.2 * SR))
    for k, f in enumerate((523, 659, 784, 1046)):
        s = tone(f, 0.8, 4, 0.18)
        i = int(k * 0.09 * SR)
        out[i:i + len(s)] += s[:len(out) - i]
    return out


def s_swish():
    t = np.arange(int(0.45 * SR)) / SR
    n = np.random.default_rng(4).normal(0, 1, len(t))
    n = ndimage.uniform_filter1d(n, 3) - ndimage.uniform_filter1d(n, 40)
    return 0.4 * n / np.abs(n).max() * np.sin(np.pi * t / 0.45) ** 2


def s_crayon(active, fps=FPS, seed=9):
    """Crayon-on-paper scribbles while `active` frames are on: bursts of rough noise in quick strokes."""
    total = len(active) / fps
    n = int(total * SR)
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, n)
    rough = ndimage.uniform_filter1d(noise, 2) - ndimage.uniform_filter1d(noise, 25)  # papery hiss
    grit = (rng.random(n) < 0.004) * rng.normal(0, 3, n)                              # tiny wax crackles
    t = np.arange(n) / SR
    rate = 5.5 + 1.5 * np.sin(2 * np.pi * 0.31 * t)                                   # strokes per second
    stroke = np.abs(np.sin(np.pi * np.cumsum(rate) / SR)) ** 0.6
    env = np.repeat(np.asarray(active, float), int(SR / fps) + 1)[:n]
    env = ndimage.uniform_filter1d(env, int(0.05 * SR))
    s = (rough + 0.5 * grit) * stroke * env
    return 0.55 * s / (np.abs(s).max() + 1e-9)


# ---------------- the timeline machine ----------------
class Ad:
    """Beats one after another. A beat lasts as long as its voice line (plus a little air) or `min`."""

    def __init__(self, key, voice="ava", music="soft-music-box", music_vol=0.11):
        self.key, self.voice, self.music, self.music_vol = key, voice, music, music_vol
        self.beats, self.sfx, self.lines = [], [], []

    def beat(self, draw, say=None, min=0.0, lead=0.2, tail=0.35, rate="+0%", sounds=()):
        self.beats.append(dict(draw=draw, say=say, min=min, lead=lead, tail=tail, rate=rate, sounds=sounds))

    def render(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        t0, words, voice = 0.0, [], []
        for b in self.beats:
            dur = b["min"]
            if b["say"]:
                a, ws = tts.say(b["say"], self.voice, rate=b["rate"])
                voice.append((t0 + b["lead"], a))
                words += [(w, t0 + b["lead"] + s, t0 + b["lead"] + e) for w, s, e in ws]
                self.lines.append(b["say"])
                dur = max(dur, b["lead"] + len(a) / tts.SR + b["tail"])
            b["start"], b["dur"] = t0, dur
            for st, snd in b["sounds"]:
                self.sfx.append((t0 + (st if st >= 0 else dur + st), snd))
            t0 += dur
        total = t0
        n = int(total * FPS)
        # audio tracks
        vt = np.zeros(int(total * tts.SR) + tts.SR, np.float32)
        for st, a in voice:
            i = int(st * tts.SR)
            vt[i:i + len(a)] += a[:len(vt) - i]
        vt = vt / (np.abs(vt).max() + 1e-9) * 0.9
        fx = np.zeros(int(total * SR) + SR)
        for st, s in self.sfx:
            i = int(st * SR)
            fx[i:i + len(s)] += s[:len(fx) - i]
        tmp = OUT / f".{name}"
        tmp.mkdir(exist_ok=True)
        sf.write(tmp / "voice.wav", vt[:int(total * tts.SR)], tts.SR)
        sf.write(tmp / "fx.wav", np.clip(fx[:int(total * SR)], -1, 1), SR)
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        inputs = ["-i", str(tmp / "voice.wav"), "-i", str(tmp / "fx.wav")]
        mix = "[1:a]volume=1.0[v];[2:a]volume=0.8[s];"
        if self.music:
            inputs += ["-stream_loop", "-1", "-i", str(ROOT / "marketing" / "music" / f"{self.music}.wav")]
            mix += (f"[3:a]atrim=0:{total:.2f},volume={self.music_vol},afade=t=in:d=0.3,"
                    f"afade=t=out:st={total - 1.2:.2f}:d=1.2[m];[v][s][m]amix=inputs=3:duration=first:normalize=0,")
        else:
            mix += "[v][s]amix=inputs=2:duration=first:normalize=0,"
        mix += "alimiter=limit=0.95[a]"
        out = OUT / f"{name}.mp4"
        proc = subprocess.Popen([ff, "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                 "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"] + inputs +
                                ["-filter_complex", mix, "-map", "0:v", "-map", "[a]", "-c:v", "libx264",
                                 "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
                                 "-b:a", "192k", "-t", f"{total:.2f}", "-movflags", "+faststart", str(out)],
                                stdin=subprocess.PIPE)
        bg = gradient(*THEME[self.key])
        bi = 0
        for f in range(n):
            t = f / FPS
            while bi + 1 < len(self.beats) and t >= self.beats[bi + 1]["start"]:
                bi += 1
            b = self.beats[bi]
            lt = t - b["start"]
            im = bg.copy()
            hide_caps = b["draw"](im, lt, b["dur"], lt / b["dur"])
            if not hide_caps:
                captions(im, words, t)
            proc.stdin.write(im.convert("RGB").tobytes())
        proc.stdin.close()
        proc.wait()
        for p in tmp.iterdir():
            p.unlink()
        tmp.rmdir()
        (OUT / f"{name}.txt").write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        print(f"✓ {out.relative_to(ROOT)}  {total:.1f} s")
        return out


# ---------------- formats ----------------
PIC = 900          # picture width on screen
PX, PY = (W - PIC) // 2, 330


def show(im, page, progress, k=0.0, y=PY, size=PIC, changed=False, zoom=0.03):
    s = int(size * (1 + zoom * k))
    pic = page.picture(progress, s, changed)
    card(im, pic, (W - s) / 2, y - (s - size) / 2)
    return (W - s) / 2, y - (s - size) / 2, s / page.shape[1]


def color_quiz(key, rounds, hook, outro, end_line):
    """rounds: [(pdf page, groups, question, reveal sentence)]. Clean B&W picture, question, 3-2-1, the
    object colors itself while the voice reads the book's own sentence (shown big, word by word)."""
    ad = Ad(key, voice="ava")
    pages = [Page(key, p, g) for p, g, _, _ in rounds]
    first = pages[0]

    def hook_draw(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        show(im, first, [0] * len(first.groups), k)
        comic(d, hook[0], W / 2, 150, 104, fill="#FFD95A")
        comic(d, hook[1], W / 2, 262, 58, fill="white")
    ad.beat(hook_draw, "Color quiz! Can your little one get all three?", lead=0.05,
            sounds=[(0.0, s_ding())])

    for r, ((p, g, q, sentence), page) in enumerate(zip(rounds, pages)):
        none = [0] * len(page.groups)

        def ask(im, lt, dur, k, page=page, q=q, r=r, none=none):
            d = ImageDraw.Draw(im)
            show(im, page, none, k)
            pill(d, f"Question {r + 1} of {len(rounds)}", 160, 46)
            comic(d, q, W / 2, 262, 78, fill="white")
        ad.beat(ask, q, lead=0.1, tail=0.15)

        def count(im, lt, dur, k, page=page, q=q, none=none):
            d = ImageDraw.Draw(im)
            show(im, page, none, 1)
            comic(d, q, W / 2, 262, 78, fill="white")
            countdown(d, W / 2, 1390, 1 - k, 3 - min(2, int(k * 3)))
            return True
        ad.beat(count, None, min=2.4, sounds=[(0.0, s_tick()), (0.8, s_tick()), (1.6, s_tick())])

        def reveal(im, lt, dur, k, page=page, sentence=sentence):
            d = ImageDraw.Draw(im)
            prog = [ease(lt / 1.2)] * len(page.groups)
            x, y, sc = show(im, page, prog, k)
            if lt < 1.2:  # crayon on the sweep front
                cx, cy = page.tip(0, ease(lt / 1.2))
                d.ellipse([x + cx * sc - 26, y + cy * sc - 26, x + cx * sc + 26, y + cy * sc + 26],
                          fill=rgb(page.groups[0][0]), outline=INK, width=6)
            comic(d, sentence.split("!")[0] + "!", W / 2, 230, 96, fill=rgb(page.groups[0][0]))
        ad.beat(reveal, sentence, lead=0.05, tail=0.3, sounds=[(0.0, s_swish()), (0.05, s_tada())])

    def score(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        for i, pg in enumerate(pages):
            pic = pg.picture([1] * len(pg.groups), 320)
            card(im, pic, 30 + i * 345, 520)
            comic(d, str(i + 1), 30 + i * 345 + 160, 470, 80)
        comic(d, outro[0], W / 2, 250, 100, fill="#FFD95A")
        comic(d, outro[1], W / 2, 1020, 70, fill="white")
    ad.beat(score, "How many did they get? Tell me in the comments!")

    def end(im, lt, dur, k):
        end_card(im, key)
    ad.beat(end, end_line, tail=0.8, sounds=[(0.0, s_ding())])
    return ad


def i_spy(key, page_no, rounds, hook_say, end_line, voice="ava"):
    """rounds: [(group names, clue, answer)]. Whole page B&W; each found thing colors in and gets circled;
    at the end the whole page colors itself."""
    ad = Ad(key, voice=voice, music="soft-music-box")
    groups = groups_from_map(key, page_no)
    page = Page(key, page_no, groups)
    n = len(groups)

    def hook(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        show(im, page, [0] * n, k)
        comic(d, "I SPY...", W / 2, 150, 120)
        comic(d, "can your kid find it first?", W / 2, 262, 60, fill="white")
    ad.beat(hook, hook_say, lead=0.1, sounds=[(0.0, s_ding())])

    for r, (names, clue, answer) in enumerate(rounds):
        already = [nm for prev, _, _ in rounds[:r] for nm in prev]

        def base(already=already):
            return [1.0 if g[0] in already else 0.0 for g in groups]

        def ask(im, lt, dur, k, clue=clue, base=base, r=r):
            d = ImageDraw.Draw(im)
            show(im, page, base(), 0)
            pill(d, f"Round {r + 1} of {len(rounds)}", 160, 46)
            comic(d, clue, W / 2, 262, 78, fill="white")
        ad.beat(ask, f"I spy, with my little eye... {clue}", lead=0.1, tail=0.15)

        def count(im, lt, dur, k, clue=clue, base=base):
            d = ImageDraw.Draw(im)
            show(im, page, base(), 0)
            comic(d, clue, W / 2, 262, 78, fill="white")
            countdown(d, W / 2, 1390, 1 - k, 3 - min(2, int(k * 3)))
            return True
        ad.beat(count, None, min=2.4, sounds=[(0.0, s_tick()), (0.8, s_tick()), (1.6, s_tick())])

        ids = [i for g in groups if g[0] in names for i in g[1]]

        def reveal(im, lt, dur, k, names=names, answer=answer, base=base, ids=ids):
            d = ImageDraw.Draw(im)
            p = base()
            p = [ease(lt / 0.9) if g[0] in names else v for g, v in zip(groups, p)]
            x, y, sc = show(im, page, p, 0)
            pulse = 1 + 0.06 * math.sin(lt * 10)
            for cx, cy, rr in page.spots(ids):
                ring(d, x + cx * sc, y + cy * sc, min(rr * sc, 230) * pulse)
            comic(d, answer, W / 2, 230, 90, fill="#FFD95A")
        ad.beat(reveal, answer, lead=0.05, tail=0.5, sounds=[(0.0, s_pop()), (0.1, s_tada())])

    def full(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        show(im, page, [min(1, ease(lt / (dur * 0.8)))] * n, k)
        comic(d, "Now the whole page!", W / 2, 230, 84, fill="white")
    ad.beat(full, "And now, the whole page!",
            sounds=[(0.0, s_swish())])

    def end(im, lt, dur, k):
        end_card(im, key)
    ad.beat(end, end_line, tail=0.8, sounds=[(0.0, s_ding())])
    return ad


def spot_difference(key, page_no, changes, answers, end_line, voice="andrew"):
    """Two copies of a colored page, the lower one with 3 changes. Timer, then the circles pop in."""
    ad = Ad(key, voice=voice, music="rocco-upbeat", music_vol=0.09)
    groups = groups_from_map(key, page_no)
    page = Page(key, page_no, groups, changes=[(c, ids) for c, ids in changes])
    n = len(groups)
    S = 640
    top, bot = 300, 980
    full = [1] * n

    def both(im):
        pa = page.picture(full, S)
        pb = page.picture(full, S, changed=True)
        card(im, pa, (W - S) / 2, top)
        card(im, pb, (W - S) / 2, bot)
        return S / page.shape[1]

    def hook(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        both(im)
        comic(d, "SPOT 3 DIFFERENCES", W / 2, 140, 92)
        comic(d, "can your kid find them all?", W / 2, 235, 54, fill="white")
        return True
    ad.beat(hook, "Spot the difference! There are three. Can your kid find them all? Ready... go!", lead=0.1,
            sounds=[(0.0, s_ding())])
    T = 8

    def timer(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        both(im)
        comic(d, "SPOT 3 DIFFERENCES", W / 2, 140, 92)
        x0, x1 = 120, W - 120
        d.rounded_rectangle([x0, 950, x1, 975], 12, fill="white", outline=INK, width=4)
        d.rounded_rectangle([x0, 950, x0 + (x1 - x0) * (1 - k), 975], 12, fill="#E5484D")
        comic(d, str(max(1, math.ceil(T - lt))), W / 2, 1720, 110)
        return True
    ad.beat(timer, None, min=T, sounds=[(float(i), s_tick()) for i in range(T)])

    for j, ((c, ids), ans) in enumerate(zip(changes, answers)):
        def reveal(im, lt, dur, k, upto=j, ans=ans):
            d = ImageDraw.Draw(im)
            sc = both(im)
            for i in range(upto + 1):
                cx, cy, rr = page.where(changes[i][1])
                r = min(rr * sc, 120) * (ease(lt / 0.25) if i == upto else 1)
                for yy in (top, bot):
                    ring(d, (W - S) / 2 + cx * sc, yy + cy * sc, max(r, 2), width=10)
            comic(d, ans, W / 2, 1720, 76, fill="#FFD95A")
            return True
        ad.beat(reveal, ans, lead=0.1, tail=0.4, sounds=[(0.0, s_pop())])

    def ask(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        sc = both(im)
        for i in range(len(changes)):
            cx, cy, rr = page.where(changes[i][1])
            for yy in (top, bot):
                ring(d, (W - S) / 2 + cx * sc, yy + cy * sc, min(rr * sc, 120), width=10)
        comic(d, "How many did you find?", W / 2, 150, 84)
        return True
    ad.beat(ask, "How many did you find? Tell me in the comments!", sounds=[(0.0, s_tada())])

    def end(im, lt, dur, k):
        end_card(im, key)
    ad.beat(end, end_line, tail=0.8)
    return ad


def asmr(key, page_no, title, seconds=17):
    """No talking: the page colors itself with a crayon, crayon-on-paper sounds, soft ding at the end."""
    ad = Ad(key, voice="ava", music=None)
    groups = groups_from_map(key, page_no)
    page = Page(key, page_no, groups)
    n = len(groups)
    areas = np.array([max(1, (page.gidx == k).sum()) for k in range(n)], float)
    share = np.sqrt(areas) / np.sqrt(areas).sum()
    starts = np.concatenate([[0], np.cumsum(share)])
    gap = 0.12  # crayon lifts between colors (silence in the sound)

    def progress(k):
        out = []
        for i in range(n):
            a, b = starts[i], starts[i + 1]
            span = (b - a)
            out.append(min(1, max(0, (k - a) / (span * (1 - gap)))) if k > a else 0)
        return out

    def which(k):
        i = int(np.searchsorted(starts, k, side="right") - 1)
        i = min(max(i, 0), n - 1)
        local = (k - starts[i]) / (starts[i + 1] - starts[i])
        return i, local

    def draw(im, lt, dur, k):
        d = ImageDraw.Draw(im)
        kk = min(1, lt / (dur - 1.2))
        x, y, sc = show(im, page, progress(kk), 0)
        i, local = which(kk)
        if kk < 1 and local < 1 - gap:
            p = min(1, local / (1 - gap))
            cx, cy = page.tip(i, p)
            cx, cy = x + cx * sc, y + cy * sc
            wob = 10 * math.sin(lt * 34)
            col = rgb(groups[i][0])
            d.polygon([(cx, cy), (cx + 40 + wob, cy - 110), (cx + 90 + wob, cy - 80)], fill=col, outline=INK, width=5)
            d.polygon([(cx + 40 + wob, cy - 110), (cx + 90 + wob, cy - 80), (cx + 250 + wob, cy - 330),
                       (cx + 200 + wob, cy - 360)], fill=col, outline=INK, width=5)
            d.line([(cx + 70 + wob, cy - 150), (cx + 120 + wob, cy - 120)], fill=INK, width=4)
        comic(d, "Crayon ASMR", W / 2, 150, 100)
        comic(d, "sound on", W / 2, 250, 56, fill="white")
        t = title
        d.text(((W - d.textlength(t, font=font(42))) / 2, 1290), t, font=font(42), fill=NAVY)
        return True

    # crayon sound follows the drawing
    fr = int(seconds * FPS)
    act = []
    for f in range(fr):
        kk = min(1, (f / FPS) / (seconds - 1.2))
        i, local = which(kk)
        act.append(1.0 if kk < 1 and local < 1 - gap else 0.0)
    ad.beat(draw, None, min=seconds, sounds=[(0.0, s_crayon(act)), (seconds - 1.1, s_ding())])

    def end(im, lt, dur, k):
        end_card(im, key)
        return True
    ad.beat(end, None, min=3.2)
    return ad


def which_book():
    """All 4 covers: 'Which one would your kid pick? Comment 1, 2, 3 or 4'."""
    ad = Ad("all", voice="emma", music="soft-music-box")
    keys = ["nico", "benny", "rocco", "posy"]
    covers = [find_cover(book_dir(k)).resize((440, 440)) for k in keys]
    pages = {"nico": ("nico", 17), "benny": ("benny", 20), "rocco": ("rocco", 26)}
    pics = {}
    for k, (kk, p) in pages.items():
        pg = Page(kk, p, groups_from_map(kk, p))
        pics[k] = pg.picture([1] * len(pg.groups), 860)
    pics["posy"] = find_cover(book_dir("posy")).resize((860, 860))

    def grid(im, lt, pop=True):
        d = ImageDraw.Draw(im)
        for i, c in enumerate(covers):
            s = ease((lt - i * 0.15) / 0.3) if pop else 1
            if s <= 0:
                continue
            cs = c.resize((max(1, int(440 * s)), max(1, int(440 * s))))
            x = 80 + (i % 2) * 480 + (440 - cs.width) / 2
            y = 420 + (i // 2) * 500 + (440 - cs.height) / 2
            card(im, cs, x, y)
            comic(d, str(i + 1), 80 + (i % 2) * 480 + 40, 420 + (i // 2) * 500 + 30, 100)
        return d

    def hook(im, lt, dur, k):
        d = grid(im, lt)
        comic(d, "Which one would", W / 2, 150, 100)
        comic(d, "your kid pick?", W / 2, 265, 100)
        return True
    ad.beat(hook, "Which one would your kid pick? One, two, three, or four?", lead=0.1, sounds=[(0.0, s_ding())])
    lines = {"nico": "Number one. Nico the little reindeer, and a snowy Christmas day.",
             "benny": "Two. Benny the bear, and the coziest day ever.",
             "rocco": "Three. Rocco, the little monster truck, and his big jump!",
             "posy": "Four. Posy the unicorn, and a rainbow birthday."}
    for i, k in enumerate(keys):
        def one(im, lt, dur, kk, k=k, i=i):
            d = ImageDraw.Draw(im)
            card(im, pics[k], (W - 860) / 2, 330)
            comic(d, f"{i + 1}", 150, 230, 140)
            comic(d, TITLES[k].split("'")[0], W / 2 + 60, 230, 70, fill="white", max_w=760)
        ad.beat(one, lines[k], sounds=[(0.0, s_swish())])

    def ask(im, lt, dur, k):
        d = grid(im, 0, pop=False)
        comic(d, "Comment your number!", W / 2, 200, 90)
        return True
    ad.beat(ask, "Every page, they color it, and then they read it. Comment your number!",
            sounds=[(0.0, s_tada())])

    def end(im, lt, dur, k):
        end_card(im, "all")
        return True
    ad.beat(end, "All four are on Amazon. Link in bio!", tail=0.8)
    return ad


# ---------------- tomorrow's ads ----------------
POSY_ROUNDS = [
    (10, [("red", [175]), ("green", [169, 170]), ("yellow", [186, 178, 192, 198, 202, 209, 211, 214, 216])],
     "What color are strawberries?", "Red strawberries! Swish! Red for the rainbow!"),
    (14, [("yellow", [71, 78, 82, 95, 116, 151, 170, 162, 185, 177, 189, 182, 201, 176, 163, 153, 127, 104]),
          ("brown", [2], (676, 489, 136))],
     "What color are sunflowers?", "Yellow sunflowers! Swish! Yellow for the rainbow!"),
    (22, [("purple", [305, 348, 344, 364, 359, 375, 367, 347, 374, 388, 379, 397, 392]), ("green", [323])],
     "What color are grapes?", "Purple grapes! Swish! Purple for the rainbow!"),
]

ADS = {
    "posy-color-quiz": lambda: color_quiz(
        "posy", POSY_ROUNDS, ("COLOR QUIZ", "3 questions for your little one"),
        ("How many did they get?", "1, 2 or all 3? Comment!"),
        "Posy's Rainbow Birthday. They color it, then they read it. Link in bio!"),
    "nico-i-spy": lambda: i_spy(
        "nico", 17, [(["carrot"], "something orange!", "The carrot nose!"),
                     (["red"], "something red and stripy!", "Nico's red scarf!"),
                     (["fur", "tan", "darkbrown"], "someone with antlers!", "Nico the reindeer!")],
        "Let's play I spy! Find it before I count to three.",
        "Nico's Snowy Day. A Christmas book they color, and read. Link in bio!"),
    "benny-i-spy": lambda: i_spy(
        "benny", 16, [(["lavender"], "something purple!", "The purple flower!"),
                      (["orange"], "something orange, with wings!", "The butterfly!"),
                      (["brown", "tan", "beige"], "a fuzzy brown bear!", "Benny!")],
        "I spy time! Can your toddler find it before I count to three?",
        "Benny the Bear's Cozy Day. A book they color, and read. Link in bio!", voice="emma"),
    "rocco-spot-difference": lambda: spot_difference(
        "rocco", 26, [("red", [165]), ("red", [163]), ("blue", [48])],
        ["The lightning bolt!", "The mud on his face!", "A blue light!"],
        "Rocco the Little Monster Truck's Big Jump. Color it, then read it. Link in bio!"),
    "nico-asmr": lambda: asmr("nico", 15, "Nico's Snowy Day  •  color & read"),
    "benny-asmr": lambda: asmr("benny", 20, "Benny the Bear's Cozy Day  •  color & read"),
    "which-book": which_book,
}

if __name__ == "__main__":
    names = sys.argv[1:] or sys.exit(__doc__)
    if names == ["all"]:
        names = list(ADS)
    for nm in names:
        ADS[nm]().render(nm)
