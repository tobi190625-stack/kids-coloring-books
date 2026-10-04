#!/usr/bin/env python3
"""Build a 6-slide Instagram/Facebook/Threads carousel (1080x1350) for a book.

Usage: python3 tools/make_carousel.py campaigns/dex/carousel.json
Config keys: slug, title, cover, art_dir, bg, headline [2 lines], pages [art files],
texts {art file: caption}, benefits [4-5 lines], ages.
Writes campaigns/<slug>/carousel/slide1..6.png
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from make_marketing import NAVY, card_in_box, centered, font, pill  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1350


def wrap(d, text, size, max_w):
    f = font(size)
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if d.textlength(test, font=f) <= max_w:
            line = test
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def page_img(path):
    im = Image.open(path).convert("L")
    s = 1400 / max(im.size)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


def main(cfg_file):
    cfg_file = Path(cfg_file).resolve()
    cfg = json.loads(cfg_file.read_text())
    out = cfg_file.parent / cfg.get("out", "carousel")
    out.mkdir(exist_ok=True)
    cover = Image.open(ROOT / cfg["cover"]).convert("RGB")
    bg, title = cfg["bg"], cfg["title"]
    art_dir = ROOT / cfg["art_dir"]

    def canvas():
        c = Image.new("RGBA", (W, H), bg)
        return c, ImageDraw.Draw(c)

    # 1: cover + hook
    c, d = canvas()
    centered(d, cfg["headline"][0], 50, 108, width=W, max_w=980)
    centered(d, cfg["headline"][1], 165, 108, width=W, max_w=980)
    card_in_box(c, cover, (60, 310), (960, 880), 44)
    pill(d, "Swipe to peek inside  >>", 1215, width=W, size=46)
    c.convert("RGB").save(out / "slide1.png")

    # 2-4: pages with their story sentence
    for n, name in enumerate(cfg["pages"][:3], start=2):
        c, d = canvas()
        lines = wrap(d, cfg["texts"][name], 66, 940)
        y = 45 + (190 - len(lines) * 78) // 2
        for ln in lines:
            centered(d, ln, y, 66, width=W)
            y += 78
        card_in_box(c, page_img(art_dir / name), (70, 250), (940, 960), 40)
        centered(d, title, 1260, 40, width=W, max_w=960)
        c.convert("RGB").save(out / f"slide{n}.png")

    # 5: what's inside
    c, d = canvas()
    centered(d, cfg.get("inside_title", "What’s inside"), 70, 120, width=W, max_w=980)
    y = 300
    for line in cfg["benefits"]:
        d.ellipse([90, y, 90 + 90, y + 90], fill=NAVY)
        d.line([(112, y + 47), (133, y + 68), (164, y + 24)], fill="white", width=11, joint="curve")
        lines = wrap(d, line, 58, 780)
        ty = y + 45 - len(lines) * 36
        for ln in lines:
            d.text((215, ty), ln, font=font(58), fill=NAVY)
            ty += 72
        y += 190
    c.convert("RGB").save(out / "slide5.png")

    # 6: call to action
    c, d = canvas()
    centered(d, cfg.get("cta_title", "Ready to color?"), 60, 116, width=W, max_w=980)
    card_in_box(c, cover, (190, 260), (700, 680), 40)
    pill(d, "Find it on Amazon", 985, width=W, size=64)
    centered(d, "Link in bio  •  " + cfg["ages"], 1200, 48, width=W)
    centered(d, title, 1270, 40, width=W, max_w=960)
    c.convert("RGB").save(out / "slide6.png")
    print("✓", out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
