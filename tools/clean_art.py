#!/usr/bin/env python3
"""Turn AI coloring-page images into crisp, print-ready black & white line art.

Usage:
    python3 tools/clean_art.py books/002-benny-the-bear

Reads   <book>/art/raw/NN.<png|jpg|webp>
Writes  <book>/art/NN.png  (upscaled 3x, pure black/white, 1-bit)

Upscaling then snapping every pixel to black or white turns soft, low-res edges
into sharp lines and removes any light gray the generator slipped in.
"""

import sys
from pathlib import Path

from PIL import Image, ImageFilter

SCALE = 3
THRESHOLD = 160  # 0-255; lower keeps only darker lines


def clean(src, dst):
    img = Image.open(src).convert("L")
    grays = sum(img.histogram()[60:200]) / (img.width * img.height)
    img = img.resize((img.width * SCALE, img.height * SCALE), Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    img.point(lambda v: 255 if v > THRESHOLD else 0).convert("1").save(dst, optimize=True)
    return img.size, grays


def main(book_dir):
    book_dir = Path(book_dir)
    raw = sorted(p for p in (book_dir / "art" / "raw").iterdir()
                 if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    for src in raw:
        dst = book_dir / "art" / f"{src.stem}.png"
        size, grays = clean(src, dst)
        flag = "  ! lots of gray - check this page" if grays > 0.08 else ""
        print(f"✓ {dst.name}  {size[0]}x{size[1]}{flag}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
