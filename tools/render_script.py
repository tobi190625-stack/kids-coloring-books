#!/usr/bin/env python3
"""Render a video from a script file, frame by frame.

Usage: python3 tools/render_script.py campaigns/nico/scripts/snowman-steps.json

1. Reads the script (JSON): scenes with a picture, on-screen text and the voice line ("say").
2. Makes the voice for every scene first (Kokoro TTS), so each scene lasts exactly as long as its line.
3. Draws every frame as a PNG (30 per second): gentle zoom, text fading in, pages that color themselves
   with a crayon sweep, and subtitles that light up word by word.
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


def page_images(book_dir, page):
    """Black-and-white page and the same page in the book's real colors."""
    img, labels, _, _ = paint.regions(book_dir, page)
    col = paint.paint_full(img, labels, paint.load_map(book_dir, page))
    bw = Image.fromarray(img if img.ndim == 3 else np.stack([img] * 3, -1)).convert("RGB")
    return bw, Image.fromarray(col).convert("RGB")


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
        if s["type"] == "page":
            bw, col = page_images(book_dir, s["page"])
            bw, col = bw.resize((900, 900)), col.resize((900, 900))
            # soft crayon edge for the color sweep
            ramp = np.clip((np.arange(900)[None, :] - np.arange(900)[:, None] * 0.25), 0, None)
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
            elif s["type"] == "page":
                # step badge
                d.rounded_rectangle([W // 2 - 210, 140, W // 2 + 210, 270], 65, fill=NAVY)
                centered(d, s["step"], 160, 80, width=W, fill="white")
                # the page colors itself with a diagonal crayon sweep (first 70% of the scene)
                p = ease(k / 0.7) * 1250
                mask = Image.fromarray(np.clip((p - ramp) * 6, 0, 255).astype(np.uint8))
                page = Image.composite(col, bw, mask)
                z = 1.0 + 0.04 * k
                page = page.resize((int(900 * z), int(900 * z)))
                shadow = Image.new("RGBA", (page.width + 40, page.height + 40), (0, 0, 0, 0))
                ImageDraw.Draw(shadow).rounded_rectangle([20, 26, page.width + 20, page.height + 26], 40,
                                                         fill=(40, 60, 90, 60))
                im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)),
                                   ((W - page.width) // 2 - 20, 320 - 20))
                card = Image.new("RGBA", page.size, (0, 0, 0, 0))
                m = Image.new("L", page.size, 0)
                ImageDraw.Draw(m).rounded_rectangle([0, 0, page.width, page.height], 40, fill=255)
                card.paste(page, (0, 0), m)
                im.alpha_composite(card, ((W - page.width) // 2, 320))
            else:  # end card
                im = end_card(book_dir, sc["background"][0]).convert("RGBA")
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
    music = ROOT / "marketing" / "music" / f"{sc['music']}.wav"
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
