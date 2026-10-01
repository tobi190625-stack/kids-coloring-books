#!/usr/bin/env python3
"""Make a vertical 9:16 "watch it get colored" video (TikTok / Reels / Shorts) from a book page.

Usage: python3 tools/make_video.py books/004-dex-the-dinosaur 22 "Watch Dex come to life"
The page is rendered from out/interior.pdf, its white areas get filled with crayon colors one by
one, then the cover appears with the title. No sound: add a sound in the app.
Writes marketing/<slug>/videos/color-page-<N>.mp4 (add --yt for the YouTube end card: yt-color-page-<N>.mp4)
"""
import json
import random
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pymupdf as fitz
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
from make_marketing import NAVY, card_in_box, centered, font, pill  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
PALETTE = ["#FF8A80", "#FFB74D", "#FFE066", "#9BE15D", "#5ED3B8", "#6EC6FF", "#8C9EFF",
           "#C792EA", "#FF9CCF", "#A1887F", "#FFD180", "#81D4FA", "#AED581", "#F48FB1"]


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def find_cover(book_dir):
    covers = [book_dir / "out" / "front-cover-no-watermark.png", book_dir / "cover" / "front.png",
              book_dir.parent / "out" / "front-cover-no-watermark.png", book_dir.parent / "cover" / "front.png"]
    return Image.open(next(c for c in covers if c.exists())).convert("RGB")


def end_card(book_dir, bg="#FFF6DA", yt=False):
    """Cover + 'Find it on Amazon', all inside the safe zone (x 60-940, y 120-1520)."""
    end = Image.new("RGBA", (W, H), bg)
    e = ImageDraw.Draw(end)
    centered(e, "Color it. Read it.", 150, 90, width=W)
    card_in_box(end, find_cover(book_dir), (160, 300), (760, 860), 40)
    if yt:  # YouTube: say clearly where the link is
        pill(e, "Link in bio", 1200, width=W, size=78)
        centered(e, "Find it on Amazon  \u2022  link also in the description", 1345, 40, width=W, max_w=880)
    else:
        pill(e, "Find it on Amazon", 1215, width=W, size=64)
        centered(e, "Link in bio", 1360, 54, width=W)
    return end


def prepare_coloring(book_dir, page_no, pw):
    """Render a page pw px wide and find its closed white areas.
    Returns (page image array, area labels, ordered area ids, {area id: rgb})."""
    page = fitz.open(book_dir / "out" / "interior.pdf")[page_no - 1]
    bubbles = [d["rect"] for d in page.get_drawings()
               if d.get("fill") == (1.0, 1.0, 1.0) and d.get("color") == (0.0, 0.0, 0.0)]
    zoom = pw / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]
    white = img.mean(axis=2) > 200
    # close small gaps in the lines so a character is not one area with the sky
    core = ndimage.binary_erosion(white, iterations=3)
    labels, n = ndimage.label(core)
    _, (iy, ix) = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    labels = np.where(white, labels[iy, ix], 0)
    sizes = ndimage.sum(np.ones_like(labels), labels, index=np.arange(n + 1))
    border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])))
    keep = np.zeros(n + 1, bool)
    for i in range(1, n + 1):
        if sizes[i] >= 150 and i not in border:
            keep[i] = True
    for r in bubbles:  # leave the text bubbles white
        x0, y0, x1, y1 = (int(v * zoom) for v in (r.x0, r.y0, r.x1, r.y1))
        for i in np.unique(labels[max(0, y0):y1, max(0, x0):x1]):
            keep[i] = False
    regions = [i for i in range(1, n + 1) if keep[i]]
    rng = random.Random(page_no)
    color = {i: hexrgb(rng.choice(PALETTE)) for i in regions}
    cy = ndimage.center_of_mass(np.ones_like(labels), labels, regions)
    regions = [r for _, r in sorted(zip([c[0] + rng.uniform(-120, 120) for c in cy], regions))]

    return img, labels, regions, color


def colored(img, labels, regions, color):
    out = img.copy()
    for i in regions:
        out[labels == i] = color[i]
    return out


def painted_video(book_dir, page_no, hook, yt, title, out_dir):
    """Realistic hand-picked colors (marketing/paint/<slug>-p<N>.json), filled object by object
    with a crayon sweeping across, on a soft background."""
    import paint
    groups = paint.load_map(book_dir, page_no)
    img, labels, _, _ = paint.regions(book_dir, page_no, paint.PW)
    pw, ph = img.shape[1], img.shape[0]
    slug = paint.slug_of(book_dir)
    theme = {"benny": ("#FFF6E0", "#FFE3B8", "#E9A35E"), "nico": ("#EEF7FF", "#D3E9FB", "#7FB6E6")}
    c_top, c_bot, accent = (hexrgb(x) for x in theme.get(slug, theme["benny"]))
    base = Image.new("RGBA", (W, H))
    bd = ImageDraw.Draw(base)
    for y in range(H):
        t = y / H
        bd.line([(0, y), (W, y)], fill=tuple(round(c_top[i] + (c_bot[i] - c_top[i]) * t) for i in range(3)))
    # soft decorative circles
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    for cx, cy, r in [(90, 300, 120), (1010, 420, 90), (60, 1580, 140), (1000, 1700, 160), (980, 120, 60)]:
        dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent + (40,))
    base.alpha_composite(deco)
    bd = ImageDraw.Draw(base)
    f = font(84)
    tw = bd.textlength(hook, font=f)
    while tw > 960:
        f = font(f.size - 4)
        tw = bd.textlength(hook, font=f)
    bd.text(((W - tw) / 2, 148), hook, font=f, fill=NAVY)
    sub = "Color & Read Story Book  \u2022  Ages 3-6"
    sf = font(40)
    sw = bd.textlength(sub, font=sf) + 60
    bd.rounded_rectangle([(W - sw) / 2, 268, (W + sw) / 2, 330], 31, fill="white")
    bd.text(((W - sw) / 2 + 30, 276), sub, font=sf, fill=NAVY)
    px, py = (W - pw) // 2, 390
    centered(bd, title, py + ph + 55, 48, width=W, max_w=960)
    name = f"{'yt-' if yt else ''}color-page-{page_no}.mp4"
    writer = imageio_ffmpeg.write_frames(str(out_dir / name), (W, H), fps=FPS, codec="libx264", quality=8,
                                         macro_block_size=8, output_params=["-pix_fmt", "yuv420p"])
    writer.send(None)
    from make_marketing import paste_card
    tips = {}

    def compose(arr, cr=None, tip=None):
        f = base.copy()
        paste_card(f, Image.fromarray(arr), (px, py), (pw, ph), 30)
        if cr is not None:
            key = id(cr)
            if key not in tips:
                tips[key] = paint.crayon_tip(cr)
            tx, ty = tips[key]
            f.alpha_composite(cr, (max(0, px + tip[0] - tx), max(0, py + tip[1] - ty)))
        return f.convert("RGB")

    blank = compose(img)
    for _ in range(int(1.2 * FPS)):
        writer.send(np.asarray(blank).tobytes())
    last = blank
    for arr, cr, tip in paint.animate(img, labels, groups, 10.5, FPS):
        last = compose(arr, cr, tip)
        writer.send(np.asarray(last).tobytes())
    for _ in range(int(1.6 * FPS)):
        writer.send(np.asarray(last).tobytes())
    endbg = "#{:02X}{:02X}{:02X}".format(*c_top)
    end = np.asarray(end_card(book_dir, endbg, yt=yt).convert("RGB")).astype(float)
    la = np.asarray(last).astype(float)
    for k in range(14):
        a = (k + 1) / 14
        writer.send((la * (1 - a) + end * a).astype(np.uint8).tobytes())
    for _ in range(int(3 * FPS)):
        writer.send(end.astype(np.uint8).tobytes())
    writer.close()
    print("\u2713", out_dir / name, "(painted)")


def main(book_dir, page_no, hook, yt=False):
    book_dir = Path(book_dir).resolve()
    book = json.loads((book_dir / "book.json").read_text())
    slug = book.get("marketing", {}).get("slug") or book_dir.name.split("-")[1]
    if book_dir.name.startswith("kdp-"):
        slug = book_dir.parent.name.split("-")[1]
    title = book["title"]
    out_dir = ROOT / "marketing" / slug / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    import paint
    if paint.load_map(book_dir, page_no):
        painted_video(book_dir, page_no, hook, yt, title, out_dir)
        return
    pw = 1000
    img, labels, regions, color = prepare_coloring(book_dir, page_no, pw)
    ph = img.shape[0]

    # frame layout: hook on top, page card in the middle, title below
    base = Image.new("RGB", (W, H), "#FFF6DA")
    d = ImageDraw.Draw(base)
    centered(d, hook, 120, 76, width=W, max_w=980)
    centered(d, "Color & Read Story Book  •  Ages 3-6", 230, 40, width=W)
    px, py = (W - pw) // 2, max(330, (H - ph) // 2 - 40)
    d.rounded_rectangle([px - 12, py - 12, px + pw + 12, py + ph + 12], 30, fill="white")
    centered(d, title, py + ph + 45, 46, width=W, max_w=1000)
    canvas = img.copy()

    writer = imageio_ffmpeg.write_frames(str(out_dir / f"{'yt-' if yt else ''}color-page-{page_no}.mp4"), (W, H), fps=FPS,
                                         codec="libx264", quality=8, macro_block_size=8,
                                         output_params=["-pix_fmt", "yuv420p"])
    writer.send(None)

    def frame(page_arr):
        f = base.copy()
        f.paste(Image.fromarray(page_arr), (px, py))
        writer.send(np.asarray(f).tobytes())

    for _ in range(int(1.5 * FPS)):  # show the empty page first
        frame(canvas)
    steps = int(9 * FPS)
    done = 0
    for s in range(steps):
        upto = round(len(regions) * (s + 1) / steps)
        for i in regions[done:upto]:
            canvas[labels == i] = color[i]
        done = upto
        frame(canvas)
    for _ in range(int(1.5 * FPS)):
        frame(canvas)

    # end card: cover + call to action (kept above the app buttons at the bottom)
    end = np.asarray(end_card(book_dir, yt=yt).convert("RGB"))
    lastf = base.copy(); lastf.paste(Image.fromarray(canvas), (px, py)); last = np.asarray(lastf).astype(float)
    for t in range(12):  # quick crossfade
        a = (t + 1) / 12
        writer.send((last * (1 - a) + end * a).astype(np.uint8).tobytes())
    for _ in range(int(3 * FPS)):
        writer.send(end.tobytes())
    writer.close()
    print("✓", out_dir / f"{'yt-' if yt else ''}color-page-{page_no}.mp4", f"({len(regions)} areas colored)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--yt"]
    if len(args) != 3:
        sys.exit(__doc__)
    main(args[0], int(args[1]), args[2], yt="--yt" in sys.argv)
