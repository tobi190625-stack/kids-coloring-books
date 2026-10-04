#!/usr/bin/env python3
"""Web pictures and the free printable for the online store (store/ builds site/).

    python3 tools/make_store_assets.py          # every book in store/assets.json + brand icons + free PDF
    python3 tools/make_store_assets.py dex      # one book (plus the free PDF)

store/assets.json says which pages each book shows. Everything is written into store/public/:
  img/books/<id>/cover.webp (+ -480), back.webp, inside-<n>.webp (+ -480),
  color-<n>.webp (+ -480, pages with a marketing/paint map), og.jpg (link previews), pin.jpg
  img/brand/  logo + favicons, made from marketing/profile-picture-round-transparent.png
  downloads/  the free coloring pages PDF
Then rebuild the site:  node store/build.mjs
"""
import json
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "store"
PUBLIC = STORE / "public"
FONT = str(ROOT / "fonts" / "Grandstander-ExtraBold.ttf")
INK = (47, 59, 82)
BIG, SMALL = 960, 480


def save_webp(im, path, width, quality=82):
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "WEBP", quality=quality, method=6)


def save_pair(im, folder, name, quality=80):
    save_webp(im, folder / f"{name}.webp", BIG, quality)
    for w in (720, SMALL):
        save_webp(im, folder / f"{name}-{w}.webp", w, quality)


def render_page(pdf, n, width=1400):
    page = pdf[n - 1]
    zoom = width / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def colored_page(paint_dir, n):
    sys.path.insert(0, str(ROOT / "tools"))
    import paint  # needs numpy + scipy (only for pages with a paint map)

    groups = paint.load_map(paint_dir, n)
    if groups is None:
        return None
    img, labels, _, _ = paint.regions(paint_dir, n)
    return Image.fromarray(paint.paint_full(img, labels, groups))


def rounded(im, radius):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    return lines + [line]


def og_image(cover, title, tint, logo, out):
    """1200x630 link preview: cover on the left, title on the right, brand at the bottom."""
    W, H = 1200, 630
    bg = Image.new("RGB", (W, H), hex_rgb(tint))
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-200, -300, 900, 700], fill=90)
    bg = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), bg, glow.filter(ImageFilter.GaussianBlur(120)))
    box_w, box_h = 470, 520
    c = cover.copy()
    c.thumbnail((box_w, box_h), Image.LANCZOS)
    c = rounded(c, 26)
    x, y = 70 + (box_w - c.width) // 2, (H - c.height) // 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([x + 6, y + 16, x + c.width + 6, y + c.height + 16], 26, fill=(47, 59, 82, 70))
    bg = Image.alpha_composite(bg.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(18)))
    bg.alpha_composite(c, (x, y))
    d = ImageDraw.Draw(bg)
    tx, tw = 600, 540
    for size in (68, 62, 56, 50, 46):
        font = ImageFont.truetype(FONT, size)
        lines = wrap(d, title, font, tw)
        if len(lines) <= 3:
            break
    while tw > 200 and len(wrap(d, title, font, tw - 10)) == len(lines):  # balance the lines
        tw -= 10
    lines = wrap(d, title, font, tw)
    lh = int(size * 1.12)
    ty = 150 if len(lines) == 3 else 180
    for i, line in enumerate(lines):
        d.text((tx, ty + i * lh), line, font=font, fill=INK)
    sub = ImageFont.truetype(FONT, 30)
    d.text((tx, ty + len(lines) * lh + 22), "Color & Read Story Book, ages 3-6", font=sub, fill=(91, 103, 128))
    lg = logo.copy()
    lg.thumbnail((84, 84), Image.LANCZOS)
    bg.alpha_composite(lg, (tx, H - 130))
    d.text((tx + 100, H - 108), "Little Crayon Tales", font=ImageFont.truetype(FONT, 34), fill=INK)
    out.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(out, "JPEG", quality=86, optimize=True, progressive=True)


def book_assets(book_id, cfg):
    folder = PUBLIC / "img" / "books" / book_id
    cover = Image.open(ROOT / cfg["cover"]).convert("RGB")
    save_pair(cover, folder, "cover")
    if cfg.get("back"):
        save_webp(Image.open(ROOT / cfg["back"]).convert("RGB"), folder / "back.webp", BIG)
    pdf = pymupdf.open(ROOT / cfg["interior"])
    for n in cfg.get("inside", []):
        save_pair(render_page(pdf, n), folder, f"inside-{n}", quality=80)
    for n in cfg.get("colored", []):
        im = colored_page(ROOT / cfg["paint_dir"], n)
        if im is None:
            print(f"  {book_id} p{n}: no marketing/paint map, skipped")
            continue
        save_pair(im, folder, f"color-{n}")
    if cfg.get("pin"):
        pin = Image.open(ROOT / cfg["pin"]).convert("RGB")
        pin.save(folder / "pin.jpg", "JPEG", quality=84, optimize=True, progressive=True)
    content = json.loads((STORE / "content" / "books" / f"{book_id}.json").read_text())
    og_image(cover, content["title"], cfg.get("tint", "#FFF4DE"), brand_logo(), folder / "og.jpg")
    print(f"  {book_id}: {len(list(folder.iterdir()))} files in {folder.relative_to(ROOT)}")


def brand_logo():
    return Image.open(ROOT / "marketing" / "profile-picture-round-transparent.png").convert("RGBA")


def brand_assets():
    folder = PUBLIC / "img" / "brand"
    folder.mkdir(parents=True, exist_ok=True)
    logo = brand_logo()
    for px in (96, 192, 320):
        im = logo.resize((px, px), Image.LANCZOS)
        im.save(folder / f"logo-{px}.webp", "WEBP", quality=90, method=6)
    # small sizes: the middle of the logo (the dinosaur) reads better than the whole badge
    w = logo.width
    face = logo.crop((int(w * .30), int(w * .26), int(w * .70), int(w * .66)))
    cream = (255, 248, 236, 255)
    tile = Image.new("RGBA", face.size, cream)
    tile.alpha_composite(face)
    tile = rounded(tile, face.width // 4)
    tile.resize((32, 32), Image.LANCZOS).save(folder / "favicon-32.png")
    tile.save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # app icons need a solid background (iOS paints transparency black)
    for px, name in ((180, "apple-touch-icon.png"), (512, "icon-512.png"), (192, "icon-192.png")):
        canvas = Image.new("RGBA", (px, px), cream)
        inner = logo.resize((int(px * .86), int(px * .86)), Image.LANCZOS)
        canvas.alpha_composite(inner, ((px - inner.width) // 2, (px - inner.height) // 2))
        canvas.convert("RGB").save(folder / name, optimize=True)
    canvas = Image.new("RGBA", (512, 512), cream)  # maskable: keep the art inside the 80% safe circle
    inner = logo.resize((380, 380), Image.LANCZOS)
    canvas.alpha_composite(inner, (66, 66))
    canvas.convert("RGB").save(folder / "icon-maskable-512.png", optimize=True)
    og = ROOT / "site" / "img" / "og.jpg"
    if og.exists() and not (folder / "og.jpg").exists():
        (folder / "og.jpg").write_bytes(og.read_bytes())
    print(f"  brand: {len(list(folder.iterdir()))} files in {folder.relative_to(ROOT)}")


def free_pdf(cfg, books):
    """Letter-size printable: a welcome page, then one real page from each book."""
    out = PUBLIC / cfg["file"]
    out.parent.mkdir(parents=True, exist_ok=True)
    W, H = 612, 792  # US Letter in points; prints fine on A4 with "fit to page"
    doc = pymupdf.open()
    titles = {b: json.loads((STORE / "content" / "books" / f"{b}.json").read_text())["title"] for b, _ in cfg["pages"]}

    page = doc.new_page(width=W, height=H)
    page.insert_font(fontname="gs", fontfile=FONT)
    logo = PUBLIC / "img" / "brand" / "logo-320.webp"
    if logo.exists():
        tmp = out.parent / ".logo.png"
        Image.open(logo).save(tmp)
        page.insert_image(pymupdf.Rect(W / 2 - 45, 56, W / 2 + 45, 146), filename=str(tmp))
        tmp.unlink()
    page.insert_textbox(pymupdf.Rect(40, 166, W - 40, 246), "Free coloring pages", fontname="gs", fontsize=42, align=1)
    page.insert_textbox(pymupdf.Rect(40, 230, W - 40, 262), f"{len(cfg['pages'])} real pages from our Color & Read story books",
                        fontname="gs", fontsize=16, align=1)
    n = len(cfg["pages"])
    gap, box_h = 22, 236
    col_w = (W - 2 * 54 - gap * (n - 1)) / n
    for i, (b, _) in enumerate(cfg["pages"]):
        cover = Image.open(PUBLIC / "img" / "books" / b / "cover-480.webp").convert("RGB")
        s_ = min(col_w / cover.width, box_h / cover.height)
        w, h = cover.width * s_, cover.height * s_
        x = 54 + i * (col_w + gap) + (col_w - w) / 2
        y = 300 + (box_h - h)
        tmp = out.parent / f".{b}-cover.jpg"
        cover.save(tmp, "JPEG", quality=85)
        page.insert_image(pymupdf.Rect(x, y, x + w, y + h), filename=str(tmp))
        tmp.unlink()
        page.insert_textbox(pymupdf.Rect(54 + i * (col_w + gap), 300 + box_h + 12, 54 + i * (col_w + gap) + col_w, 300 + box_h + 70),
                            titles[b], fontname="gs", fontsize=12.5, align=1)
    lines = ["Print as many copies as you like for your family or classroom.",
             "Color the picture, then read the sentence together.",
             "Find the whole stories on Amazon: search for Little Crayon Tales."]
    for i, line in enumerate(lines):
        page.insert_textbox(pymupdf.Rect(54, 650 + i * 22, W - 54, 672 + i * 22), line, fontname="helv", fontsize=12, align=1)

    for b, n in cfg["pages"]:
        src = pymupdf.open(ROOT / books[b]["interior"])
        r = src[n - 1].rect
        box_w, box_h = W - 2 * 40, H - 36 - 130
        s = min(box_w / r.width, box_h / r.height)
        w, h = r.width * s, r.height * s
        x0, y0 = (W - w) / 2, max(36, (H - h - 84) / 2)
        page = doc.new_page(width=W, height=H)
        page.show_pdf_page(pymupdf.Rect(x0, y0, x0 + w, y0 + h), src, n - 1)
        page.insert_font(fontname="gs", fontfile=FONT)
        fy = y0 + h + 34
        page.insert_text((x0 + 24, fy), "This page is from", fontname="helv", fontsize=11)
        page.insert_text((x0 + 24, fy + 24), titles[b], fontname="gs", fontsize=17)
        page.insert_text((x0 + 24, fy + 44), "A Color & Read Story Book by Little Crayon Tales. Find it on Amazon.", fontname="helv", fontsize=11)
    doc.set_metadata({"title": "Free coloring pages - Little Crayon Tales", "author": "Little Crayon Tales"})
    doc.save(out, garbage=4, deflate=True)
    print(f"  free PDF: {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB, {len(doc)} pages)")


def main():
    cfg = json.loads((STORE / "assets.json").read_text())
    wanted = sys.argv[1:] or list(cfg["books"])
    for book_id in wanted:
        book_assets(book_id, cfg["books"][book_id])
    if not sys.argv[1:]:
        brand_assets()
    free_pdf(cfg["free_pdf"], cfg["books"])


if __name__ == "__main__":
    main()
