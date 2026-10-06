#!/usr/bin/env python3
"""Make a book picture come alive: a short AI video clip from one page (open-source Wan 2.2 model).

Usage: python3 tools/animate.py books/005-rocco-monster-truck 10 "the monster truck bounces in the mud" [--secs 4] [--seed 7]
Writes campaigns/<slug>/videos/alive-p<N>.mp4 (about 3-5 s, no sound). Add voice + music with add_voice.py.

Runs free on Hugging Face's GPUs (our laptop GPU is too small), so it needs internet and can be
slow or busy at peak times. Free use is limited to a few clips per day; if it says "quota", try
again tomorrow. ALWAYS look at the frames before posting: AI can warp faces and wheels. Pick another
--seed if it looks wrong. Posting AI video: tick the "AI-generated" label on TikTok/YouTube/Meta.
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from gradio_client import Client, handle_file
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
# Wan 2.2 image-to-video 14B (Apache 2.0, github.com/Wan-Video/Wan2.2), fast "Lightning" build.
SPACES = ["zerogpu-aoti/wan2-2-fp8da-aoti-faster", "r3gm/wan2-2-fp8da-aoti-preview"]
STYLE = ("black and white coloring book line art, thick clean black outlines on white, "
         "cute cartoon for kids, gentle smooth motion, the drawing style stays exactly the same. ")
NEGATIVE = ("color, colored, gray shading, realistic, photo, blurry, distorted face, extra wheels, "
            "extra limbs, deformed, flicker, text, watermark, static image, camera shake")


def picture(book_dir, page):
    """The page's line art (art/NN.png), shrunk to 832 px so the upload is small."""
    src = book_dir / "art" / f"{int(page):02d}.png"
    if not src.exists():
        sys.exit(f"No picture {src}")
    img = Image.open(src).convert("RGB")
    img.thumbnail((832, 832))
    tmp = Path(tempfile.mkdtemp()) / src.name
    img.save(tmp)
    return tmp


def generate(image, prompt, secs, seed):
    last = None
    for space in SPACES:
        try:
            print(f"Asking {space} (can take 1-3 min)...")
            client = Client(space, verbose=False)
            if space.startswith("r3gm"):
                out = client.predict(handle_file(image), None, STYLE + prompt, 6, NEGATIVE, secs,
                                     1, 1, max(seed, 0), seed < 0, api_name="/generate_video")
                video = out[1] or out[0]["video"]
            else:
                out = client.predict(handle_file(image), STYLE + prompt, 6, NEGATIVE, secs,
                                     1, 1, max(seed, 0), seed < 0, api_name="/generate_video")
                video = out[0]["video"] if isinstance(out[0], dict) else out[0]
            return video, out[-1]
        except Exception as e:  # busy / quota / Space down: try the next one
            last = e
            print(f"  failed: {str(e)[:200]}")
    sys.exit(f"All Spaces failed. Last error: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book")
    ap.add_argument("page", type=int)
    ap.add_argument("prompt", help="what moves, e.g. 'the bear waves and smiles'")
    ap.add_argument("--secs", type=float, default=4.0)
    ap.add_argument("--seed", type=int, default=-1, help="-1 = random; reuse a seed to repeat a good result")
    a = ap.parse_args()

    book_dir = (ROOT / a.book).resolve()
    slug = book_dir.name.split("-", 1)[1].split("-")[0]  # 005-rocco-monster-truck -> rocco
    out_dir = ROOT / "campaigns" / slug / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    video, seed = generate(picture(book_dir, a.page), a.prompt, a.secs, a.seed)
    out = out_dir / f"alive-p{a.page}.mp4"
    shutil.copy(video, out)
    print(f"Wrote {out.relative_to(ROOT)}  (seed {int(seed)})")


if __name__ == "__main__":
    main()
