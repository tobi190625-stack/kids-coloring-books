#!/usr/bin/env python3
"""Render a video from a script file, frame by frame.

Usage: python3 tools/render_script.py campaigns/nico/scripts/snowman-steps.json

1. Reads the script (JSON): scenes with a picture, on-screen text and the voice line ("say").
2. Makes the voice for every scene first (Kokoro TTS), so each scene lasts exactly as long as its line.
3. Draws every frame as a PNG (30 per second): gentle zoom, text fading in, pages that color themselves
   with a crayon sweep, and subtitles that light up word by word.
   Scene types: title (cover), page (colors itself, needs a paint map), bwpage (black-and-white page),
   clip (an AI "comes alive" video from tools/animate.py: "video": path), read (the picture + its
   sentence in big letters that light up as the voice reads it: "say" = the sentence), flip (fast
   flip-through: "pages": [book pages]), end (cover + link). Any picture scene can have a "step" badge on top.
   Cartoon motion made in code (no AI) for page/bwpage scenes: "motion": ["bounce", "wobble"]
   (bounce = the page hops with squash and stretch, wobble = hand-drawn lines that gently wiggle).
4. Merges the frames into an MP4 (ffmpeg), adds the voice + soft music.
5. Writes the transcript: <out>.srt (subtitles with times) and <out>.txt (plain text).
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import paint  # noqa: E402
import voice  # noqa: E402
from make_marketing import NAVY, card_in_box, centered, font  # noqa: E402
from make_video import FPS, H, W, end_card, find_cover  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LEAD, TAIL = 0.35, 0.55  # silence before / after each voice line (seconds)
SUB_Y = 1330  # subtitles: inside the safe zone (y 120-1520), above the app buttons


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(c1, c2):
    a, b = np.array(hex_rgb(c1), float), np.array(hex_rgb(c2), float)
    t = np.linspace(0, 1, H)[:, None, None]
    return Image.fromarray(np.broadcast_to(a * (1 - t) + b * t, (H, W, 3)).astype(np.uint8))


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def words_timed(text, start, dur):
    """Split a line into words with times, spread by word length (good enough for subtitles)."""
    words = text.split()
    weights = [len(w) + 2 for w in words]
    total, t, out = sum(weights), start, []
    for w, k in zip(words, weights):
        d = dur * k / total
        out.append((w, t, t + d))
        t += d
    return out


def subtitle(img, words, t, y=SUB_Y, size=62):
    """Three-to-five word chunk around the word being spoken; the current word is highlighted."""
    cur = next((i for i, (_, a, b) in enumerate(words) if a <= t < b), None)
    if cur is None:
        return img
    start = cur - cur % 4
    chunk = words[start:start + 4]
    d = ImageDraw.Draw(img)
    f = font(size)
    SUB = y
    widths = [d.textlength(w + " ", font=f) for w, _, _ in chunk]
    x = (W - sum(widths)) / 2
    box = [x - 30, SUB - 18, x + sum(widths) + 14, SUB + size + 30]
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(box, 36, fill=(255, 255, 255, 230))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    d = ImageDraw.Draw(img)
    for (w, _, _), wd, i in zip(chunk, widths, range(start, start + len(chunk))):
        if i == cur:
            d.rounded_rectangle([x - 8, SUB - 6, x + wd - 6, SUB + size + 18], 18, fill="#FFD95A")
        d.text((x, SUB), w, font=f, fill=NAVY)
        x += wd
    return img


def badge(d, text, y=140):
    """Navy pill with white text on top of the frame; shrinks long hooks to fit the safe zone."""
    size = 80
    while d.textlength(text, font=font(size)) > 900 and size > 44:
        size -= 2
    half = max(210, int(d.textlength(text, font=font(size))) // 2 + 60)
    d.rounded_rectangle([W // 2 - half, y, W // 2 + half, y + size + 50], (size + 50) // 2, fill=NAVY)
    centered(d, text, y + 20, size, width=W, fill="white")


def paste_card(im, page, y=320):
    """A picture as a rounded card with a soft shadow, centered at height y."""
    shadow = Image.new("RGBA", (page.width + 40, page.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([20, 26, page.width + 20, page.height + 26], 40,
                                             fill=(40, 60, 90, 60))
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)), ((W - page.width) // 2 - 20, y - 20))
    card = Image.new("RGBA", page.size, (0, 0, 0, 0))
    m = Image.new("L", page.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, page.width, page.height], 40, fill=255)
    card.paste(page.convert("RGB"), (0, 0), m)
    im.alpha_composite(card, ((W - page.width) // 2, y))


def clip_frames(path, size=900):
    reader = imageio_ffmpeg.read_frames(str(ROOT / path))
    meta = reader.__next__()
    w, h = meta["size"]
    return [Image.frombytes("RGB", (w, h), fr).resize((size, size), Image.LANCZOS) for fr in reader]


def big_sentence(im, words, t, y=1110, size=78):
    """The book sentence in big letters; the word being read lights up (karaoke style)."""
    d = ImageDraw.Draw(im)
    f = font(size)
    lines, cur = [], []
    for i in range(len(words)):
        if cur and d.textlength(" ".join(words[j][0] for j in cur + [i]), font=f) > 940:
            lines.append(cur)
            cur = []
        cur.append(i)
    lines.append(cur)
    now = next((i for i, (_, a, b) in enumerate(words) if a <= t < b), None)
    for li, idx in enumerate(lines):
        x = (W - d.textlength(" ".join(words[j][0] for j in idx), font=f)) / 2
        yy = y + li * (size + 34)
        for j in idx:
            wd = d.textlength(words[j][0], font=f)
            if j == now:
                d.rounded_rectangle([x - 12, yy - 6, x + wd + 12, yy + size + 18], 20, fill="#FFD95A")
            done = (now is not None and j <= now) or t >= words[-1][2]
            d.text((x, yy), words[j][0], font=f, fill=NAVY if done else "#8A97AD")
            x += wd + d.textlength(" ", font=f)


def wobble_frames(img, n=3, amp=2.6, seed=7):
    """n copies of a picture with its lines nudged by smooth random noise; cycling them looks hand-drawn."""
    from scipy import ndimage
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = []
    for _ in range(n):
        dx, dy = (np.asarray(Image.fromarray(rng.uniform(-1, 1, (10, 10)).astype(np.float32)).resize((w, h), Image.BICUBIC))
                  * amp for _ in range(2))
        warped = np.stack([ndimage.map_coordinates(a[..., c], [yy + dy, xx + dx], order=1, mode="nearest")
                           for c in range(3)], -1)
        out.append(Image.fromarray(warped.clip(0, 255).astype(np.uint8)))
    return out


def bounce(t, period=0.9, height=45):
    """Hop height and squash for time t: up in an arc, squash a little on landing."""
    ph = (t % period) / period
    hop = np.sin(np.pi * ph) * height
    squash = max(0.0, 1 - ph / 0.12) * 0.07 + max(0.0, (ph - 0.9) / 0.1) * 0.05
    return hop, squash


def page_images(book_dir, page):
    """Black-and-white page and the same page in the book's real colors."""
    img, labels, _, _ = paint.regions(book_dir, page)
    col = paint.paint_full(img, labels, paint.load_map(book_dir, page))
    bw = Image.fromarray(img if img.ndim == 3 else np.stack([img] * 3, -1)).convert("RGB")
    return bw, Image.fromarray(col).convert("RGB")


def pdf_page(book_dir, page):
    import pymupdf
    pg = pymupdf.open(book_dir / "out" / "interior.pdf")[page - 1]
    pix = pg.get_pixmap(dpi=120)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def render(script_path):
    sc = json.loads(Path(script_path).read_text())
    book_dir = ROOT / sc["book"]
    out = ROOT / sc["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    bg = gradient(*sc["background"])
    frames_dir = Path(tempfile.mkdtemp(prefix="frames-"))

    # 1) voice first: every scene lasts as long as its line
    lines, audio, t0 = [], [], 0.0
    for s in sc["scenes"]:
        a = voice.speak(s["say"], sc.get("voice", "af_heart"), seed=len(s["say"]))
        dur = LEAD + len(a) / voice.SR + TAIL
        seg = np.zeros(int(dur * voice.SR), np.float32)
        seg[int(LEAD * voice.SR):int(LEAD * voice.SR) + len(a)] = a
        audio.append(seg)
        s["_start"], s["_dur"] = t0, dur
        s["_words"] = words_timed(s["say"], t0 + LEAD, len(a) / voice.SR)
        lines.append((t0 + LEAD, t0 + LEAD + len(a) / voice.SR, s["say"]))
        t0 += dur
    total = t0

    # 2) frame by frame
    cover = find_cover(book_dir)
    n = 0
    for s in sc["scenes"]:
        if s["type"] in ("page", "bwpage"):
            if s["type"] == "page":
                bw, col = page_images(book_dir, s["page"])
            else:  # no color map yet: show the black-and-white page kids will color
                bw = col = pdf_page(book_dir, s["page"])
            bw, col = bw.resize((900, 900)), col.resize((900, 900))
            # soft crayon edge for the color sweep
            ramp = np.clip((np.arange(900)[None, :] - np.arange(900)[:, None] * 0.25), 0, None)
            motion = s.get("motion", [])
            if "wobble" in motion:
                bws, cols = wobble_frames(bw), wobble_frames(col)
        elif s["type"] == "clip":
            clip = clip_frames(s["video"])
        elif s["type"] == "read":
            art = Image.open(book_dir / "art" / f"{s['page']:02d}.png").convert("RGB").resize((760, 760), Image.LANCZOS)
        elif s["type"] == "flip":  # book page N is PDF page N + 2 (title + "belongs to" come first)
            flips = [pdf_page(book_dir, p + 2).resize((900, 900), Image.LANCZOS) for p in s["pages"]]
        frames = int(round(s["_dur"] * FPS))
        for f in range(frames):
            t = s["_start"] + f / FPS
            k = f / max(frames - 1, 1)
            im = bg.copy().convert("RGBA")
            d = ImageDraw.Draw(im)
            if s["type"] == "title":
                a = ease(f / 12)
                centered(d, s["text"], 170, 86, width=W, max_w=960, fill=NAVY)
                centered(d, s.get("small", ""), 300, 56, width=W, fill=NAVY)
                z = 1.0 + 0.06 * k
                c = cover.resize((int(760 * z), int(760 * z)))
                im.alpha_composite(c.convert("RGBA"), ((W - c.width) // 2, 420 - int(20 * z)))
                if a < 1:  # fade in from the background
                    im = Image.blend(bg.convert("RGBA"), im, a)
            elif s["type"] == "clip":  # the AI clip, stretched to the length of the voice line
                fr = clip[min(int(k * len(clip)), len(clip) - 1)]
                z = 1.0 + 0.03 * k
                paste_card(im, fr.resize((int(900 * z), int(900 * z))), 320)
                if s.get("step"):
                    badge(d, s["step"])
            elif s["type"] == "read":
                paste_card(im, art, 310)
                if s.get("step"):
                    badge(d, s["step"])
                # "text" (optional) = a sentence shown gray while the voice says something else (the hook)
                big_sentence(im, [(w, 1e9, 1e9) for w in s["text"].split()] if s.get("text") else s["_words"], t)
            elif s["type"] == "flip":  # pages slide in from the right, one after another
                share = 1 / len(flips)
                i = min(int(k / share), len(flips) - 1)
                slide = ease((k - i * share) / share / 0.3) if i else 1.0
                if i:
                    paste_card(im, flips[i - 1], 320)
                layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
                paste_card(layer, flips[i], 320)
                im.alpha_composite(layer.transform(im.size, Image.AFFINE, (1, 0, -int((1 - slide) * W), 0, 1, 0)))
                if s.get("step"):
                    badge(ImageDraw.Draw(im), s["step"])
            elif s["type"] in ("page", "bwpage"):
                # the page colors itself with a diagonal crayon sweep (first 70% of the scene)
                p = ease(k / 0.7) * 1250
                mask = Image.fromarray(np.clip((p - ramp) * 6, 0, 255).astype(np.uint8))
                if "wobble" in motion:  # new line drawing 8 times a second, like a cartoon
                    w = (f // 4) % len(bws)
                    page = Image.composite(cols[w], bws[w], mask)
                else:
                    page = Image.composite(col, bw, mask)
                z = 1.0 + 0.04 * k
                if "bounce" in motion:
                    hop, sq = bounce(t - s["_start"])
                    pw, ph = int(900 * z * (1 + sq)), int(900 * z * (1 - sq))
                    paste_card(im, page.resize((pw, ph)), int(320 + 900 * z - ph - hop))
                else:
                    paste_card(im, page.resize((int(900 * z), int(900 * z))), 320)
                if s.get("step"):  # badge on top (after the page, so a bouncing page never covers it)
                    badge(d, s["step"])
            else:  # end card
                im = end_card(book_dir, sc["background"][0]).convert("RGBA")
            if s["type"] != "read":  # read scenes already show the words big
                im = subtitle(im, s["_words"], t, *((1440, 54) if s["type"] == "end" else (SUB_Y, 62)))
            im.convert("RGB").save(frames_dir / f"frame_{n:05d}.png")
            n += 1
    print(f"drew {n} frames ({total:.1f} s)")

    # 3) merge frames into a video
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    silent = frames_dir / "video.mp4"
    subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(frames_dir / "frame_%05d.png"),
                    "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p", str(silent)], check=True)

    # 4) voice + soft music
    raw, warm = frames_dir / "voice.raw.wav", frames_dir / "voice.wav"
    sf.write(raw, np.concatenate(audio), voice.SR)
    voice.warm(raw, warm)
    music = ROOT / "marketing" / "music" / f"{sc.get('music', 'soft-music-box')}.wav"
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", str(silent), "-i", str(warm), "-stream_loop", "-1", "-i",
                    str(music), "-filter_complex",
                    f"[1:a]volume=1.5[v];[2:a]atrim=0:{total:.2f},volume=0.18,afade=t=in:d=0.5,"
                    f"afade=t=out:st={total - 1.5:.2f}:d=1.5[m];[v][m]amix=inputs=2:duration=first:normalize=0,"
                    "alimiter=limit=0.95[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out.with_suffix(".mp4"))], check=True)

    # 5) transcript
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    srt = "".join(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n" for i, (a, b, txt) in enumerate(lines, 1))
    out.with_suffix(".srt").write_text(srt)
    out.with_suffix(".txt").write_text(f"{sc['title']}\n\n" + "\n".join(txt for _, _, txt in lines) + "\n")
    shutil.rmtree(frames_dir)
    print("✓", out.with_suffix(".mp4"), "+ .srt + .txt")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    render(sys.argv[1])
