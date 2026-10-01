#!/usr/bin/env python3
"""Hand-picked, realistic coloring for book pages (the bear brown, the snow white, ...).

1. python3 tools/paint.py ids books/003-nico-the-reindeer 17
   -> scratch image with every closed area numbered, to decide the colors.
2. Write marketing/paint/<slug>-p<N>.json:
     {"groups": [["brown", [12, 15, 40]], ["sky", [1]], ...]}
   Groups are painted in this order (like a person: one character, then the next, then the
   background). Areas not listed stay white paper (snow, clouds, white fur).
3. python3 tools/paint.py preview books/003-nico-the-reindeer 17   -> colored page png to check.
make_video.py and make_shorts.py use the map automatically when it exists.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
PW = 1000

# soft crayon colors
COLORS = {
    "brown": "#A8714A", "darkbrown": "#7A4E31", "tan": "#D8A878", "beige": "#F2D9B8",
    "cream": "#FBEBCF", "fur": "#C98A55", "honey": "#F2B33D", "yellow": "#FFD95A",
    "orange": "#F59A3D", "red": "#E5484D", "darkred": "#B83236", "pink": "#F7AFC3",
    "lightpink": "#FCD5DF", "rose": "#EE7FA0", "purple": "#B48AD8", "lavender": "#D8C4F0",
    "blue": "#5AA7E6", "lightblue": "#A9D6F5", "sky": "#CDEBFA", "navy": "#3F5E99",
    "teal": "#4FBFB0", "mint": "#A8E6CF", "green": "#6CBF4B", "darkgreen": "#3E8E41",
    "lightgreen": "#B5E08C", "grass": "#8ACB5C", "gray": "#AEB5BD", "lightgray": "#D9DEE3",
    "darkgray": "#6E757C", "black": "#3A3A3A", "white": "#FFFFFF", "ice": "#E3F3FC",
    "wood": "#B7835A", "lightwood": "#D9B287", "carrot": "#F28C28", "gold": "#E8B931",
    "peach": "#FFC9A3", "snowshadow": "#EAF2FA",
}


def find_dir(book):
    p = Path(book)
    return (p if p.is_absolute() else ROOT / p).resolve()


def slug_of(book_dir):
    d = book_dir.parent if book_dir.name.startswith("kdp-") else book_dir
    return d.name.split("-")[1]


def regions(book_dir, page_no, pw=PW):
    """Page image, area labels, area ids (bubbles excluded), and a point inside each area."""
    page = fitz.open(book_dir / "out" / "interior.pdf")[page_no - 1]
    bubbles = [d["rect"] for d in page.get_drawings()
               if d.get("fill") == (1.0, 1.0, 1.0) and d.get("color") == (0.0, 0.0, 0.0)]
    zoom = pw / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3].copy()
    white = img.mean(axis=2) > 200
    # close the picture at its own edge (lines run off the art), and drop the page margin
    dark = ~white
    ys, xs = np.nonzero(dark)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    white[y0:y0 + 3, x0:x1 + 1] = white[y1 - 2:y1 + 1, x0:x1 + 1] = False
    white[y0:y1 + 1, x0:x0 + 3] = white[y0:y1 + 1, x1 - 2:x1 + 1] = False
    white[:y0], white[y1 + 1:], white[:, :x0], white[:, x1 + 1:] = False, False, False, False
    core = ndimage.binary_erosion(white, iterations=3)
    labels, n = ndimage.label(core)
    _, (iy, ix) = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    labels = np.where(white, labels[iy, ix], 0)
    sizes = ndimage.sum(np.ones_like(labels), labels, index=np.arange(n + 1))
    keep = sizes >= 15
    keep[0] = False
    inside = np.zeros(labels.shape, bool)
    for r in bubbles:
        x0, y0, x1, y1 = (int(v * zoom) for v in (r.x0, r.y0, r.x1, r.y1))
        inside[max(0, y0):y1, max(0, x0):x1] = True
    # an area mostly inside a text bubble is the bubble itself (or a letter hole): keep it white
    frac = ndimage.sum(inside, labels, index=np.arange(n + 1)) / np.maximum(sizes, 1)
    keep &= frac < 0.6
    # tiny white specks (gaps between claws, ...) take the color around them
    small = white & (labels == 0)
    sl, sn = ndimage.label(small)
    ssz = ndimage.sum(np.ones_like(sl), sl, index=np.arange(sn + 1))
    tiny = (ssz < 60)[sl] & small
    d2, (ky, kx) = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    labels = np.where(tiny & (d2 <= 6), labels[ky, kx], labels)
    # reach into the soft gray edge pixels next to the lines (painted with multiply, so lines stay)
    dist, (jy, jx) = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    soft = (img.mean(axis=2) > 40) & (dist <= 4)
    labels = np.where((labels == 0) & soft, labels[jy, jx], labels)
    ids = [int(i) for i in np.nonzero(keep)[0]]
    seeds = {}
    for i, sl in zip(range(1, n + 1), ndimage.find_objects(labels)):
        if i in ids and sl is not None:
            m = labels[sl] == i
            dist = ndimage.distance_transform_edt(m)
            y, x = np.unravel_index(np.argmax(dist), dist.shape)
            seeds[i] = (sl[0].start + int(y), sl[1].start + int(x))
    return img, labels, ids, seeds


def load_map(book_dir, page_no):
    f = ROOT / "marketing" / "paint" / f"{slug_of(book_dir)}-p{page_no}.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text())
    groups = list(data["groups"])
    img, labels, ids, _ = regions(book_dir, page_no)
    whites = {int(i) for i in data.get("white", [])}
    owner = {int(i): g for g, (_, l) in enumerate(groups) for i in l}
    sizes = ndimage.sum(np.ones_like(labels), labels, index=np.arange(labels.max() + 1))
    free = [i for i in ids if i not in owner and i not in whites]
    if data.get("rest"):  # bigger unlisted areas get the background color (painted last)
        groups.append([data["rest"], [i for i in free if sizes[i] >= 300]])
        for i in groups[-1][1]:
            owner[i] = len(groups) - 1
    # small unlisted areas (grass blade insides, gaps) take the color around them
    for sl_i in [i for i in free if i not in owner]:
        sl = ndimage.find_objects((labels == sl_i).astype(int))[0]
        y0, y1 = max(0, sl[0].start - 12), sl[0].stop + 12
        x0, x1 = max(0, sl[1].start - 12), sl[1].stop + 12
        m = labels[y0:y1, x0:x1] == sl_i
        ring = ndimage.binary_dilation(m, iterations=10) & ~m
        votes = {}
        for j in labels[y0:y1, x0:x1][ring]:
            if j and j != sl_i:
                key = "w" if (j in whites or j not in owner) else owner[j]
                votes[key] = votes.get(key, 0) + 1
        if votes:
            best = max(votes, key=votes.get)
            if best != "w":
                groups[best] = [groups[best][0], list(groups[best][1]) + [sl_i]]
    out = []
    for name, idlist in groups:
        h = COLORS.get(name, name)
        out.append((tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)), [int(i) for i in idlist]))
    return out


def grain(shape, seed=7):
    """Soft paper/crayon texture: multiply factor around 1.0."""
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (shape[0] // 3 + 1, shape[1] // 3 + 1))
    n = ndimage.gaussian_filter(n, 1.2)
    n = np.kron(n, np.ones((3, 3)))[:shape[0], :shape[1]]
    fine = ndimage.gaussian_filter(rng.normal(0, 1, shape[:2]), 0.6)
    return 1.0 + 0.012 * n / (n.std() + 1e-6) + 0.008 * fine / (fine.std() + 1e-6)


def shade(img):
    """Darken a little next to the black lines, like real crayon that piles up at the edges."""
    white = img.mean(axis=2) > 200
    d = ndimage.distance_transform_edt(white)
    return 1.0 - 0.10 * np.exp(-d / 6.0)


def paint_full(img, labels, groups):
    out = img.astype(float)
    g = grain(img.shape) * shade(img)
    for col, idlist in groups:
        m = np.isin(labels, idlist)
        out[m] = np.array(col, float) * g[m][:, None] * (img[m].astype(float) / 255.0)
    return np.clip(out, 0, 255).astype(np.uint8)


def crayon_tip(im):
    a = np.array(im)[..., 3] > 0
    ys, xs = np.nonzero(a)
    k = np.argmax(ys - xs)
    return int(xs[k]), int(ys[k])


def crayon(rgb, length=300, width=60):
    """A crayon picture pointing down-left, tip at (0, h)."""
    im = Image.new("RGBA", (width + 20, length + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dark = tuple(max(0, int(c * 0.72)) for c in rgb)
    x0, x1 = 10, 10 + width
    d.polygon([(x0 + width / 2, length + 10), (x0 + 6, length - 40), (x1 - 6, length - 40)], fill=dark)
    d.rounded_rectangle([x0, 10, x1, length - 36], 10, fill=rgb + (255,), outline=dark + (255,), width=3)
    d.rectangle([x0, 60, x1, 90], fill=dark + (255,))
    d.rectangle([x0, length - 90, x1, length - 70], fill=dark + (255,))
    d.rectangle([x0 + 7, 16, x0 + 13, length - 44], fill=(255, 255, 255, 90))
    return im.rotate(-35, expand=True, resample=Image.BICUBIC)


def animate(img, labels, groups, seconds, fps=30):
    """Frames of the page being colored group by group with a crayon sweeping across.
    Yields (page array, crayon image or None, crayon tip (x, y) in page px)."""
    full = paint_full(img, labels, groups)
    canvas = img.copy()
    areas = [max(1, int(np.isin(labels, ids).sum())) for _, ids in groups]
    w = np.sqrt(areas)
    total = int(seconds * fps)
    frames_per = [max(8, int(total * x / w.sum())) for x in w]
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    for (col, ids), nf in zip(groups, frames_per):
        m = np.isin(labels, ids)
        if not m.any():
            continue
        proj = (xx[m] * 0.8 + yy[m] * 0.6).astype(float)
        lo, hi = proj.min(), proj.max() + 1
        proj = (proj - lo) / (hi - lo)
        ys, xs = yy[m], xx[m]
        cr = crayon(col)
        for f in range(nf):
            p = (f + 1) / nf
            sel = proj <= p
            canvas[ys[sel], xs[sel]] = full[ys[sel], xs[sel]]
            front = np.abs(proj - p) < 0.04
            if front.any():
                k = np.nonzero(front)[0]
                k = k[len(k) // 2]
                tip = (int(xs[k]), int(ys[k]))
            else:
                tip = None
            yield canvas, (cr if tip else None), tip
    yield full, None, None


def ids_image(book_dir, page_no, path):
    img, labels, ids, seeds = regions(book_dir, page_no)
    big = 2
    im = Image.fromarray(img).resize((img.shape[1] * big, img.shape[0] * big)).convert("RGB")
    # tint each area lightly so neighbours are distinguishable
    rng = np.random.default_rng(1)
    tint = np.array(im).astype(float)
    lab2 = np.kron(labels, np.ones((big, big), int))
    for i in ids:
        tint[lab2 == i] = tint[lab2 == i] * 0.55 + rng.integers(120, 255, 3) * 0.45
    im = Image.fromarray(tint.astype(np.uint8))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(ROOT / "fonts" / "Grandstander-ExtraBold.ttf"), 22)
    for i in ids:
        y, x = seeds[i]
        t = str(i)
        w = d.textlength(t, font=f)
        d.rectangle([x * big - w / 2 - 3, y * big - 13, x * big + w / 2 + 3, y * big + 13], fill="white")
        d.text((x * big - w / 2, y * big - 13), t, font=f, fill="black")
    im.save(path)
    print(path, len(ids), "areas")


if __name__ == "__main__":
    mode, book, n = sys.argv[1], find_dir(sys.argv[2]), int(sys.argv[3])
    S = Path("/tmp/claude-0/-home-user-emil-kowalski/dad0fc95-c17a-51fc-b393-54fe27ba2afa/scratchpad/paint")
    S.mkdir(parents=True, exist_ok=True)
    if mode == "ids":
        ids_image(book, n, S / f"{slug_of(book)}-p{n}-ids.png")
    else:
        img, labels, ids, seeds = regions(book, n)
        groups = load_map(book, n)
        listed = {i for _, l in groups for i in l}
        print("not listed (stay white):", [i for i in ids if i not in listed])
        Image.fromarray(paint_full(img, labels, groups)).save(S / f"{slug_of(book)}-p{n}-preview.png")
        print(S / f"{slug_of(book)}-p{n}-preview.png")
